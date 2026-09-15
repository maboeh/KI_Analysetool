"""Evaluationssuite für das KI Analysetool (M13).

Gespeicherte Testfälle (EvalCase) werden gegen mehrere Prompt-/Modell-
Varianten (Variant) laufen gelassen und lokal sowie deterministisch
bewertet (score_output) – bewusst ohne LLM-as-Judge, damit keine
zusätzlichen Kosten entstehen und keine Daten an Dritte gehen.

EvaluationStore persistiert Suiten und Läufe in der Ergebnis-Datenbank
(Tabellen eval_suites/eval_runs, Schema-Migration 4).
"""

import json
import re
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Callable, List, Optional

import analysis
from privacy_scanner import scan_text


def _now_iso() -> str:
    return datetime.now().isoformat()


def _new_id() -> str:
    return uuid.uuid4().hex


# ---------------------------------------------------------------------------
# Datenmodell
# ---------------------------------------------------------------------------

@dataclass
class EvalCase:
    """Ein gespeicherter Testfall mit lokal prüfbaren Erwartungen."""
    id: str
    name: str
    input_text: str
    must_contain: List[str] = field(default_factory=list)
    must_not_contain: List[str] = field(default_factory=list)
    regex: List[str] = field(default_factory=list)
    max_output_chars: Optional[int] = None
    expect_json: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "EvalCase":
        return EvalCase(
            id=data["id"],
            name=data["name"],
            input_text=data.get("input_text", ""),
            must_contain=list(data.get("must_contain", [])),
            must_not_contain=list(data.get("must_not_contain", [])),
            regex=list(data.get("regex", [])),
            max_output_chars=data.get("max_output_chars"),
            expect_json=bool(data.get("expect_json", False)),
        )


@dataclass
class EvalSuite:
    """Eine benannte Sammlung von Testfällen."""
    id: str
    name: str
    description: str = ""
    cases: List[EvalCase] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "cases": [case.to_dict() for case in self.cases],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(data: dict) -> "EvalSuite":
        return EvalSuite(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            cases=[EvalCase.from_dict(c) for c in data.get("cases", [])],
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


@dataclass(frozen=True)
class Variant:
    """Eine Prompt-/Modell-Variante für einen Evaluationslauf."""
    label: str
    model: str
    prompt: str


@dataclass(frozen=True)
class CheckResult:
    """Ergebnis eines einzelnen deterministischen Checks."""
    name: str
    passed: bool
    detail: str = ""


@dataclass
class CaseResult:
    """Ergebnis einer Variante auf einem Testfall."""
    case_id: str
    variant_label: str
    status: str  # "done" | "failed" | "privacy_blocked" | "cancelled"
    content: str = ""
    checks: List[CheckResult] = field(default_factory=list)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost: float = 0.0
    duration_s: float = 0.0
    error_message: Optional[str] = None

    @property
    def passed(self) -> bool:
        """True, wenn die Analyse lief und alle Checks bestanden sind."""
        if self.status != "done":
            return False
        return all(check.passed for check in self.checks)

    @property
    def check_pass_rate(self) -> Optional[float]:
        """Anteil bestandener Checks; None wenn der Case keine Checks hat."""
        if not self.checks:
            return None
        return sum(1 for c in self.checks if c.passed) / len(self.checks)

    def to_dict(self) -> dict:
        data = asdict(self)
        return data

    @staticmethod
    def from_dict(data: dict) -> "CaseResult":
        return CaseResult(
            case_id=data["case_id"],
            variant_label=data["variant_label"],
            status=data["status"],
            content=data.get("content", ""),
            checks=[CheckResult(**c) for c in data.get("checks", [])],
            prompt_tokens=data.get("prompt_tokens", 0),
            completion_tokens=data.get("completion_tokens", 0),
            cost=data.get("cost", 0.0),
            duration_s=data.get("duration_s", 0.0),
            error_message=data.get("error_message"),
        )


@dataclass
class VariantSummary:
    """Aggregierte Kennzahlen einer Variante über alle Cases."""
    label: str
    model: str
    cases_total: int
    cases_passed: int
    check_pass_rate: Optional[float]
    total_tokens: int
    total_cost: float
    avg_duration_s: float
    blocked: int
    failed: int


@dataclass
class EvalRun:
    """Ein durchgeführter Evaluationslauf (Varianten × Cases)."""
    id: str
    suite_id: str
    started_at: str
    finished_at: Optional[str]
    variants: List[Variant] = field(default_factory=list)
    results: List[CaseResult] = field(default_factory=list)

    def summary(self) -> List[VariantSummary]:
        """Aggregiert die Ergebnisse pro Variante (Reihenfolge = variants)."""
        summaries = []
        for variant in self.variants:
            results = [r for r in self.results
                       if r.variant_label == variant.label]
            all_checks = [c for r in results for c in r.checks]
            check_rate = (sum(1 for c in all_checks if c.passed)
                          / len(all_checks)) if all_checks else None
            durations = [r.duration_s for r in results if r.status == "done"]
            summaries.append(VariantSummary(
                label=variant.label,
                model=variant.model,
                cases_total=len(results),
                cases_passed=sum(1 for r in results if r.passed),
                check_pass_rate=check_rate,
                total_tokens=sum(r.prompt_tokens + r.completion_tokens
                                 for r in results),
                total_cost=sum(r.cost for r in results),
                avg_duration_s=(sum(durations) / len(durations)
                                if durations else 0.0),
                blocked=sum(1 for r in results
                            if r.status == "privacy_blocked"),
                failed=sum(1 for r in results if r.status == "failed"),
            ))
        return summaries

    def best_variant(self) -> Optional[str]:
        """Beste Variante: meiste bestandene Cases, dann Check-Quote,
        dann weniger Tokens. None, wenn kein Case bestanden wurde."""
        candidates = [s for s in self.summary() if s.cases_passed > 0]
        if not candidates:
            return None
        best = max(
            candidates,
            key=lambda s: (
                s.cases_passed,
                s.check_pass_rate if s.check_pass_rate is not None else 1.0,
                -s.total_tokens,
            ),
        )
        return best.label

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "suite_id": self.suite_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "variants": [asdict(v) for v in self.variants],
            "results": [r.to_dict() for r in self.results],
        }

    @staticmethod
    def from_dict(data: dict) -> "EvalRun":
        return EvalRun(
            id=data["id"],
            suite_id=data["suite_id"],
            started_at=data.get("started_at", ""),
            finished_at=data.get("finished_at"),
            variants=[Variant(**v) for v in data.get("variants", [])],
            results=[CaseResult.from_dict(r) for r in data.get("results", [])],
        )


# ---------------------------------------------------------------------------
# Varianten-Parsing (wird auch vom Prompt-Playground genutzt)
# ---------------------------------------------------------------------------

def parse_variant_lines(text: str, known_models, default_model: str
                        ) -> List[Variant]:
    """Parst „Modell | Prompt"-Zeilen in Variant-Objekte.

    Zeilen ohne „|" verwenden das Default-Modell; leere Modell- oder
    Prompt-Teile fallen auf den Default zurück bzw. werden übersprungen.
    """
    variants = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        if "|" in line:
            model, prompt = (part.strip() for part in line.split("|", 1))
        else:
            model, prompt = "", line
        if not prompt:
            continue
        model = model or default_model or "gpt-4o-mini"
        variants.append(Variant(
            label=f"{len(variants) + 1}. {model}",
            model=model,
            prompt=prompt,
        ))
    return variants


# ---------------------------------------------------------------------------
# Lokale, deterministische Checks
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    """Whitespace-normalisiert und casefold für Toleranz-Checks."""
    return " ".join((text or "").split()).casefold()


_JSON_BLOCK_RE = re.compile(r"```json\s*(.*?)```", re.IGNORECASE | re.DOTALL)


def score_output(content: str, case: EvalCase) -> List[CheckResult]:
    """Prüft einen Output gegen alle Erwartungen eines Testfalls.

    Alles lokal und deterministisch: Substring (case-insensitiv,
    whitespace-normalisiert), Regex (IGNORECASE|MULTILINE), Maximallänge,
    JSON-Parse (gesamter Inhalt oder erster ```json-Block).
    """
    checks = []
    normalized_content = _normalize(content)

    for needle in case.must_contain:
        found = _normalize(needle) in normalized_content
        checks.append(CheckResult(
            name=f"enthält: {needle}",
            passed=found,
            detail="" if found else f"'{needle}' fehlt im Output",
        ))

    for needle in case.must_not_contain:
        absent = _normalize(needle) not in normalized_content
        checks.append(CheckResult(
            name=f"enthält nicht: {needle}",
            passed=absent,
            detail="" if absent else f"'{needle}' im Output gefunden",
        ))

    for pattern in case.regex:
        try:
            matched = bool(re.search(pattern, content or "",
                                     re.IGNORECASE | re.MULTILINE))
        except re.error:
            checks.append(CheckResult(
                name=f"regex: {pattern}", passed=False,
                detail="Ungültiger Ausdruck"))
            continue
        checks.append(CheckResult(
            name=f"regex: {pattern}",
            passed=matched,
            detail="" if matched else "Kein Treffer",
        ))

    if case.max_output_chars is not None:
        length = len(content or "")
        checks.append(CheckResult(
            name=f"max. Zeichen ≤ {case.max_output_chars}",
            passed=length <= case.max_output_chars,
            detail="" if length <= case.max_output_chars
            else f"{length} Zeichen",
        ))

    if case.expect_json:
        parsed = False
        detail = ""
        try:
            json.loads(content or "")
            parsed = True
        except (json.JSONDecodeError, TypeError) as exc:
            block = _JSON_BLOCK_RE.search(content or "")
            if block:
                try:
                    json.loads(block.group(1))
                    parsed = True
                except (json.JSONDecodeError, TypeError) as exc2:
                    detail = str(exc2)
            else:
                detail = str(exc)
        checks.append(CheckResult(
            name="gültiges JSON", passed=parsed,
            detail="" if parsed else detail,
        ))

    return checks


# ---------------------------------------------------------------------------
# Lauf
# ---------------------------------------------------------------------------

def run_evaluation(suite: EvalSuite, variants: List[Variant], analyze_fn,
                   on_progress: Optional[Callable] = None,
                   cancel_event=None,
                   privacy_check: bool = True) -> EvalRun:
    """Führt sequenziell Variante × Case aus.

    analyze_fn(content, prompt, model) -> AnalysisOutcome (wie Playground).
    Datenschutz: Bei Funden im Input und Nicht-lokalem Provider wird der
    Case als "privacy_blocked" markiert ohne analyze_fn aufzurufen; bei
    lokalem Provider wird trotz Funden gesendet (verlässt Gerät nicht).
    cancel_event (threading.Event) → verbleibende Kombinationen "cancelled".
    """
    run = EvalRun(id=_new_id(), suite_id=suite.id,
                  started_at=_now_iso(), finished_at=None,
                  variants=list(variants), results=[])
    total = len(run.variants) * len(suite.cases)
    done = 0
    local = analysis.is_local_provider()

    for variant in run.variants:
        for case in suite.cases:
            result = None
            if cancel_event is not None and cancel_event.is_set():
                result = CaseResult(case_id=case.id,
                                    variant_label=variant.label,
                                    status="cancelled")
            elif (privacy_check and not local
                  and scan_text(case.input_text).has_findings):
                result = CaseResult(case_id=case.id,
                                    variant_label=variant.label,
                                    status="privacy_blocked",
                                    error_message="Datenschutz-Fund im Input")
            else:
                started = time.time()
                outcome = None
                error_message = None
                try:
                    outcome = analyze_fn(case.input_text, variant.prompt,
                                         variant.model)
                except Exception as exc:  # analyze_fn sollte nicht werfen
                    error_message = str(exc)
                duration = time.time() - started

                if outcome is None:
                    result = CaseResult(case_id=case.id,
                                        variant_label=variant.label,
                                        status="failed",
                                        duration_s=duration,
                                        error_message=error_message)
                elif not outcome.success:
                    error_message = getattr(outcome.error, "user_message",
                                            str(outcome.error))
                    result = CaseResult(
                        case_id=case.id, variant_label=variant.label,
                        status="failed", duration_s=duration,
                        error_message=error_message,
                        prompt_tokens=outcome.prompt_tokens or 0,
                        completion_tokens=outcome.completion_tokens or 0)
                else:
                    content = outcome.content or ""
                    result = CaseResult(
                        case_id=case.id, variant_label=variant.label,
                        status="done", content=content,
                        checks=score_output(content, case),
                        prompt_tokens=outcome.prompt_tokens or 0,
                        completion_tokens=outcome.completion_tokens or 0,
                        cost=(0.0 if local else analysis.calculate_cost(
                            outcome.prompt_tokens or 0,
                            outcome.completion_tokens or 0,
                            variant.model)),
                        duration_s=duration)

            run.results.append(result)
            done += 1
            if on_progress is not None:
                on_progress(done, total, result)

    run.finished_at = _now_iso()
    return run


# ---------------------------------------------------------------------------
# Bericht
# ---------------------------------------------------------------------------

def render_markdown_report(run: EvalRun, suite: EvalSuite) -> str:
    """Markdown-Bericht: Zusammenfassungstabelle, beste Variante, Details.

    Aus Datenschutzgründen keine vollständigen Inhalte – nur die ersten
    200 Zeichen des Outputs je Case.
    """
    lines = [
        f"# Evaluationsbericht: {suite.name}",
        "",
        f"- Suite: {suite.name} ({len(suite.cases)} Testfälle)",
        f"- Datum: {run.finished_at or run.started_at}",
        f"- Varianten: {len(run.variants)}",
        "",
        "## Zusammenfassung",
        "",
        "| Variante | Modell | Bestanden | Check-Quote | Tokens | Kosten | Ø Dauer | Blockiert/Fehler |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for summary in run.summary():
        rate = (f"{summary.check_pass_rate:.0%}"
                if summary.check_pass_rate is not None else "–")
        lines.append(
            f"| {summary.label} | {summary.model} "
            f"| {summary.cases_passed}/{summary.cases_total} | {rate} "
            f"| {summary.total_tokens} | ${summary.total_cost:.4f} "
            f"| {summary.avg_duration_s:.1f}s "
            f"| {summary.blocked}/{summary.failed} |")

    best = run.best_variant()
    lines += ["", f"**Beste Variante:** {best or '—'}", "", "## Details", ""]

    case_names = {case.id: case.name for case in suite.cases}
    status_labels = {
        "done": "fertig",
        "failed": "fehlgeschlagen",
        "privacy_blocked": "datenschutz-blockiert",
        "cancelled": "abgebrochen",
    }
    for variant in run.variants:
        lines.append(f"### {variant.label}")
        lines.append("")
        for result in run.results:
            if result.variant_label != variant.label:
                continue
            case_name = case_names.get(result.case_id, result.case_id)
            status = status_labels.get(result.status, result.status)
            passed = sum(1 for c in result.checks if c.passed)
            lines.append(
                f"- **{case_name}**: {status} "
                f"({passed}/{len(result.checks)} Checks, "
                f"{result.duration_s:.1f}s)")
            for check in result.checks:
                mark = "✓" if check.passed else "✗"
                suffix = f" — {check.detail}" if check.detail else ""
                lines.append(f"  - {mark} {check.name}{suffix}")
            if result.error_message:
                lines.append(f"  - Fehler: {result.error_message}")
            if result.content:
                excerpt = result.content[:200]
                if len(result.content) > 200:
                    excerpt += "…"
                lines.append(f"  - Output-Auszug: {excerpt}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Persistenz
# ---------------------------------------------------------------------------

class EvaluationStore:
    """Speichert Eval-Suiten und -Läufe in der Ergebnis-Datenbank."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        from migrations import migrate
        migrate(self.db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # ----- Suiten -----

    def save_suite(self, suite: EvalSuite) -> None:
        suite.updated_at = _now_iso()
        if not suite.created_at:
            suite.created_at = suite.updated_at
        cases_json = json.dumps([c.to_dict() for c in suite.cases],
                                ensure_ascii=False)
        with self._connect() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO eval_suites
                    (id, name, description, cases_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (suite.id, suite.name, suite.description, cases_json,
                  suite.created_at, suite.updated_at))
            conn.commit()

    def get_suite(self, suite_id: str) -> Optional[EvalSuite]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, name, description, cases_json, created_at,"
                " updated_at FROM eval_suites WHERE id = ?",
                (suite_id,)).fetchone()
        if not row:
            return None
        suite = EvalSuite(
            id=row[0], name=row[1], description=row[2] or "",
            cases=[EvalCase.from_dict(c) for c in json.loads(row[3])],
            created_at=row[4] or "", updated_at=row[5] or "")
        return suite

    def list_suites(self) -> List[EvalSuite]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, name, description, cases_json, created_at,"
                " updated_at FROM eval_suites ORDER BY name").fetchall()
        return [
            EvalSuite(id=row[0], name=row[1], description=row[2] or "",
                      cases=[EvalCase.from_dict(c)
                             for c in json.loads(row[3])],
                      created_at=row[4] or "", updated_at=row[5] or "")
            for row in rows
        ]

    def delete_suite(self, suite_id: str) -> None:
        """Löscht die Suite samt Läufen (ON DELETE CASCADE)."""
        with self._connect() as conn:
            conn.execute("DELETE FROM eval_suites WHERE id = ?", (suite_id,))
            conn.commit()

    # ----- Läufe -----

    def save_run(self, run: EvalRun) -> None:
        summary_json = json.dumps(
            [asdict(s) for s in run.summary()], ensure_ascii=False)
        with self._connect() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO eval_runs
                    (id, suite_id, started_at, finished_at,
                     variants_json, results_json, summary_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (run.id, run.suite_id, run.started_at, run.finished_at,
                  json.dumps([asdict(v) for v in run.variants],
                             ensure_ascii=False),
                  json.dumps([r.to_dict() for r in run.results],
                             ensure_ascii=False),
                  summary_json))
            conn.commit()

    def get_run(self, run_id: str) -> Optional[EvalRun]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, suite_id, started_at, finished_at,"
                " variants_json, results_json FROM eval_runs WHERE id = ?",
                (run_id,)).fetchone()
        if not row:
            return None
        return self._run_from_row(row, include_results=True)

    def list_runs(self, suite_id: str) -> List[EvalRun]:
        """Läufe einer Suite, neueste zuerst (ohne results-Blob)."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, suite_id, started_at, finished_at,"
                " variants_json, NULL FROM eval_runs WHERE suite_id = ?"
                " ORDER BY started_at DESC", (suite_id,)).fetchall()
        return [self._run_from_row(row, include_results=False)
                for row in rows]

    def delete_run(self, run_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM eval_runs WHERE id = ?", (run_id,))
            conn.commit()

    @staticmethod
    def _run_from_row(row, include_results: bool) -> EvalRun:
        run = EvalRun(
            id=row[0], suite_id=row[1], started_at=row[2] or "",
            finished_at=row[3],
            variants=[Variant(**v) for v in json.loads(row[4] or "[]")],
            results=[])
        if include_results:
            run.results = [CaseResult.from_dict(r)
                           for r in json.loads(row[5] or "[]")]
        return run

    # ----- Import/Export -----

    @staticmethod
    def export_suite_json(suite: EvalSuite) -> str:
        return json.dumps(suite.to_dict(), ensure_ascii=False, indent=2)

    @staticmethod
    def import_suite_json(text: str) -> EvalSuite:
        """Parst eine exportierte Suite; vergibt eine neue ID.

        Validierung: name und mindestens ein Case sind Pflicht.
        """
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("Suite-JSON muss ein Objekt sein.")
        if not data.get("name"):
            raise ValueError("Suite benötigt einen Namen.")
        cases = [EvalCase.from_dict(c) for c in data.get("cases", [])]
        if not cases:
            raise ValueError("Suite benötigt mindestens einen Testfall.")
        now = _now_iso()
        return EvalSuite(
            id=_new_id(), name=data["name"],
            description=data.get("description", ""),
            cases=cases, created_at=now, updated_at=now)
