"""Persistente Batch-Queue für Multi-Datei-Analysen (M7).

Jobs und Items werden in SQLite gespeichert und überleben damit einen
Neustart der Anwendung. Beim Start werden unterbrochene „running"-Items
zurück auf „pending" gesetzt, sodass `resume_job` nahtlos fortsetzt.

Verhalten:
- begrenzte Parallelität pro Job (`concurrency`),
- Pause/Resume über ein Event,
- Abbruch markiert offene Items als `cancelled`,
- Fehler werden nur bei `retryable`-Fehlern erneut versucht,
- jedes fertige Item speichert sein Ergebnis sofort (Teilergebnisse),
- vor dem Versand wird extrahierter Inhalt lokal auf Secrets/PII geprüft –
  Items mit Funden werden als `skipped` markiert statt übertragen.
"""

import os
import sqlite3
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, List, Optional

from analysis import (
    AVAILABLE_MODELS,
    DEFAULT_MODEL,
    AnalysisErrorCode,
    analyze_pdf,
    analyze_text,
    extract_content,
)

JOB_STATUSES = ("pending", "running", "paused", "completed", "failed", "cancelled")
ITEM_STATUSES = ("pending", "running", "done", "failed", "skipped", "cancelled")
MAX_ATTEMPTS = 2  # 1 Initialversuch + 1 Retry für retryable Fehler


@dataclass(frozen=True)
class BatchItem:
    id: str
    job_id: str
    source: str
    source_type: str
    position: int
    status: str
    attempts: int
    error_code: Optional[str]
    error_message: Optional[str]
    result_id: Optional[str]
    prompt_tokens: int
    completion_tokens: int
    cost_estimate: float

    @staticmethod
    def _from_row(row) -> "BatchItem":
        return BatchItem(
            id=row[0], job_id=row[1], source=row[2], source_type=row[3],
            position=row[4], status=row[5], attempts=row[6],
            error_code=row[7], error_message=row[8], result_id=row[9],
            prompt_tokens=row[10], completion_tokens=row[11],
            cost_estimate=row[12] or 0.0,
        )


@dataclass(frozen=True)
class BatchJob:
    id: str
    name: str
    status: str
    prompt: str
    model: Optional[str]
    concurrency: int
    created_at: str
    updated_at: str

    @staticmethod
    def _from_row(row) -> "BatchJob":
        return BatchJob(
            id=row[0], name=row[1], status=row[2], prompt=row[3],
            model=row[4], concurrency=row[5], created_at=row[6],
            updated_at=row[7],
        )


class BatchQueue:
    """Verwaltet persistente Batch-Jobs und ihre Ausführung."""

    _ITEM_COLUMNS = ("id, job_id, source, source_type, position, status, attempts,"
                     " error_code, error_message, result_id, prompt_tokens,"
                     " completion_tokens, cost_estimate")
    _JOB_COLUMNS = ("id, name, status, prompt, model, concurrency, created_at,"
                    " updated_at")

    def __init__(self, db_path: str = "results.db", results_manager=None):
        self.db_path = db_path
        self.results_manager = results_manager
        self._controls: Dict[str, Dict[str, threading.Event]] = {}
        self._threads: Dict[str, threading.Thread] = {}
        self._resume_interrupted_items()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # ------------------------------------------------------------------
    # Persistenz
    # ------------------------------------------------------------------

    def create_job(self, name: str, prompt: str,
                   items: List[Dict[str, str]],
                   model: Optional[str] = None,
                   concurrency: int = 1) -> str:
        """Legt einen Job mit Items an. items: [{'source', 'source_type'}]."""
        if not items:
            raise ValueError("Ein Batch-Job benötigt mindestens ein Item.")
        if not (prompt or "").strip():
            raise ValueError("Ein Batch-Job benötigt einen Prompt.")
        job_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO batch_jobs (id, name, status, prompt, model, concurrency,"
                " created_at, updated_at) VALUES (?, ?, 'pending', ?, ?, ?, ?, ?)",
                (job_id, name.strip() or "Batch", prompt, model,
                 max(1, int(concurrency)), now, now)
            )
            for position, item in enumerate(items):
                conn.execute(
                    "INSERT INTO batch_items (id, job_id, source, source_type, position)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), job_id, item["source"],
                     item.get("source_type", "file"), position)
                )
            conn.commit()
        return job_id

    def get_job(self, job_id: str) -> Optional[BatchJob]:
        with self._connect() as conn:
            row = conn.execute(
                f"SELECT {self._JOB_COLUMNS} FROM batch_jobs WHERE id = ?",
                (job_id,)
            ).fetchone()
        return BatchJob._from_row(row) if row else None

    def list_jobs(self) -> List[BatchJob]:
        with self._connect() as conn:
            return [BatchJob._from_row(row) for row in conn.execute(
                f"SELECT {self._JOB_COLUMNS} FROM batch_jobs ORDER BY created_at DESC"
            ).fetchall()]

    def get_items(self, job_id: str) -> List[BatchItem]:
        with self._connect() as conn:
            return [BatchItem._from_row(row) for row in conn.execute(
                f"SELECT {self._ITEM_COLUMNS} FROM batch_items"
                " WHERE job_id = ? ORDER BY position", (job_id,)
            ).fetchall()]

    def get_job_progress(self, job_id: str) -> Dict[str, int]:
        """Fortschritt: Anzahl Items je Status plus Gesamtkosten."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*), SUM(cost_estimate) FROM batch_items"
                " WHERE job_id = ? GROUP BY status", (job_id,)
            ).fetchall()
        progress = {status: 0 for status in ITEM_STATUSES}
        total_cost = 0.0
        for status, count, cost in rows:
            progress[status] = count
            total_cost += cost or 0.0
        progress["total"] = sum(progress[s] for s in ITEM_STATUSES)
        progress["cost"] = round(total_cost, 4)
        return progress

    def delete_job(self, job_id: str) -> bool:
        self.cancel_job(job_id)
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM batch_jobs WHERE id = ?", (job_id,))
            return cursor.rowcount > 0

    def _set_job_status(self, job_id: str, status: str):
        with self._connect() as conn:
            conn.execute(
                "UPDATE batch_jobs SET status = ?, updated_at = ? WHERE id = ?",
                (status, datetime.now().isoformat(), job_id)
            )
            conn.commit()

    def _set_item(self, item_id: str, **fields):
        if not fields:
            return
        fields.setdefault("finished_at", datetime.now().isoformat())
        assignments = ", ".join(f"{key} = ?" for key in fields)
        with self._connect() as conn:
            conn.execute(
                f"UPDATE batch_items SET {assignments} WHERE id = ?",
                (*fields.values(), item_id)
            )
            conn.commit()

    def _resume_interrupted_items(self):
        """Nach Neustart: running-Items zurück auf pending setzen."""
        try:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE batch_items SET status = 'pending' WHERE status = 'running'"
                )
                conn.execute(
                    "UPDATE batch_jobs SET status = 'paused', updated_at = ?"
                    " WHERE status = 'running'",
                    (datetime.now().isoformat(),)
                )
                conn.commit()
        except sqlite3.OperationalError:
            pass  # Tabellen existieren noch nicht (vor Migration)

    # ------------------------------------------------------------------
    # Steuerung
    # ------------------------------------------------------------------

    def _control(self, job_id: str) -> Dict[str, threading.Event]:
        return self._controls.setdefault(job_id, {
            "pause": threading.Event(),
            "cancel": threading.Event(),
        })

    def start_job(self, job_id: str, on_progress: Optional[Callable] = None) -> bool:
        """Startet oder setzt einen Job fort (Thread im Hintergrund)."""
        job = self.get_job(job_id)
        if job is None or job.status in ("completed", "cancelled", "failed"):
            return False
        thread = self._threads.get(job_id)
        if thread and thread.is_alive():
            return False
        controls = self._control(job_id)
        controls["pause"].clear()
        controls["cancel"].clear()
        self._set_job_status(job_id, "running")
        thread = threading.Thread(
            target=self._run_job, args=(job_id, on_progress), daemon=True)
        self._threads[job_id] = thread
        thread.start()
        return True

    def pause_job(self, job_id: str):
        self._control(job_id)["pause"].set()
        self._set_job_status(job_id, "paused")

    def resume_job(self, job_id: str, on_progress: Optional[Callable] = None) -> bool:
        job = self.get_job(job_id)
        if job is None:
            return False
        thread = self._threads.get(job_id)
        if thread and thread.is_alive():
            self._control(job_id)["pause"].clear()
            self._set_job_status(job_id, "running")
            return True
        return self.start_job(job_id, on_progress=on_progress)

    def cancel_job(self, job_id: str):
        self._control(job_id)["cancel"].set()
        with self._connect() as conn:
            conn.execute(
                "UPDATE batch_items SET status = 'cancelled',"
                " finished_at = ? WHERE job_id = ? AND status IN ('pending', 'running')",
                (datetime.now().isoformat(), job_id)
            )
            conn.execute(
                "UPDATE batch_jobs SET status = 'cancelled', updated_at = ? WHERE id = ?",
                (datetime.now().isoformat(), job_id)
            )
            conn.commit()

    # ------------------------------------------------------------------
    # Ausführung
    # ------------------------------------------------------------------

    def _run_job(self, job_id: str, on_progress: Optional[Callable]):
        job = self.get_job(job_id)
        if job is None:
            return
        controls = self._control(job_id)
        try:
            while True:
                if controls["cancel"].is_set():
                    return
                if controls["pause"].is_set():
                    return  # Thread endet; resume_job startet neuen Thread
                pending = [item for item in self.get_items(job_id)
                           if item.status == "pending"]
                if not pending:
                    break
                batch = pending[: max(1, job.concurrency)]
                if len(batch) == 1:
                    self._run_item(batch[0], job)
                else:
                    with ThreadPoolExecutor(max_workers=job.concurrency) as pool:
                        list(pool.map(lambda item: self._run_item(item, job), batch))
                if on_progress:
                    try:
                        on_progress(job_id)
                    except Exception:
                        pass
            # Abschlussstatus bestimmen
            progress = self.get_job_progress(job_id)
            if progress["done"] + progress["skipped"] == progress["total"] \
                    or progress["done"] > 0:
                self._set_job_status(job_id, "completed")
            elif progress["failed"] == progress["total"]:
                self._set_job_status(job_id, "failed")
            else:
                self._set_job_status(job_id, "completed")
        finally:
            if on_progress:
                try:
                    on_progress(job_id)
                except Exception:
                    pass

    def _run_item(self, item: BatchItem, job: BatchJob):
        if self._control(job.id)["cancel"].is_set():
            return
        self._set_item(item.id, status="running", attempts=item.attempts + 1,
                       started_at=datetime.now().isoformat())
        try:
            outcome = self._analyze_item(item, job)
        except Exception:
            outcome = None
        if outcome is None:
            self._finish_item(item, "failed", "unknown",
                              "Unerwarteter Fehler bei der Verarbeitung.")
            return
        if outcome.success:
            result_id = self._store_result(item, job, outcome.content)
            self._set_item(
                item.id, status="done", result_id=result_id,
                prompt_tokens=outcome.prompt_tokens,
                completion_tokens=outcome.completion_tokens,
                cost_estimate=self._item_cost(job, outcome),
            )
            return
        error = outcome.error
        retryable = error.retryable and item.attempts + 1 < MAX_ATTEMPTS
        self._finish_item(
            item,
            "pending" if retryable else "failed",
            error.code.value,
            error.user_message,
        )

    def _analyze_item(self, item: BatchItem, job: BatchJob):
        """Führt Extraktion, Datenschutz-Scan und Analyse für ein Item aus."""
        if item.source_type == "pdf":
            prompt = job.prompt.replace("{text}", item.source) \
                if "{text}" in job.prompt else job.prompt
            return analyze_pdf(item.source, prompt)

        if item.source_type == "text":
            content = item.source
        else:
            outcome = extract_content(item.source)
            if not outcome.success:
                from analysis import AnalysisOutcome
                return AnalysisOutcome(error=outcome.error)
            content = outcome.content

        # Lokaler Datenschutz-Scan des extrahierten Inhalts.
        from privacy_scanner import scan_text
        if scan_text(content).has_findings:
            from analysis import AnalysisOutcome, AnalysisError
            return AnalysisOutcome(error=AnalysisError(
                AnalysisErrorCode.INVALID_INPUT,
                "Übersprungen: lokale Datenschutzprüfung hat sensible Daten erkannt."
            ))

        prompt = job.prompt.replace("{text}", content) \
            if "{text}" in job.prompt else f"{job.prompt}\n\n{content}"
        return _analyze_with_model(job, prompt)

    def _item_cost(self, job: BatchJob, outcome) -> float:
        info = AVAILABLE_MODELS.get(job.model or DEFAULT_MODEL,
                                    AVAILABLE_MODELS[DEFAULT_MODEL])
        return (outcome.prompt_tokens * info["cost_per_1k_input"] +
                outcome.completion_tokens * info["cost_per_1k_output"]) / 1000

    def _store_result(self, item: BatchItem, job: BatchJob, content: str) -> Optional[str]:
        if self.results_manager is None:
            return None
        try:
            from results_processor import ResultsProcessor
            from analysis import AnalysisOutcome
            processor = ResultsProcessor()
            processed = processor.process_analysis_outcome(
                AnalysisOutcome(content=content), item.source, item.source_type)
            return self.results_manager.save_result(
                processed, f"{job.name}: {os.path.basename(item.source) or item.source_type}")
        except Exception:
            return None

    def _finish_item(self, item: BatchItem, status: str,
                     error_code: Optional[str], error_message: Optional[str]):
        # Datenschutz-Überspringe werden als 'skipped' markiert.
        if status == "failed" and error_code == AnalysisErrorCode.INVALID_INPUT.value:
            status = "skipped"
        self._set_item(item.id, status=status, error_code=error_code,
                       error_message=error_message)


def _analyze_with_model(job: BatchJob, prompt: str):
    """Analyse mit dem Job-Modell (fällt auf Session-Modell zurück)."""
    from analysis import _default_session
    previous = _default_session.current_model
    if job.model:
        _default_session.set_model(job.model)
    try:
        return analyze_text(prompt)
    finally:
        if job.model:
            _default_session.set_model(previous)
