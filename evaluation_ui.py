"""Dialog für die Evaluationssuite (M13).

Drei Spalten: Suites (links), Testfälle (Mitte), Varianten & Ergebnisse
(rechts). Ein Lauf führt sequenziell Variante × Testfall im Worker-Thread
aus und bewertet die Ausgaben lokal-deterministisch (kein LLM-as-Judge).
"""

import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, simpledialog, ttk
from typing import Optional

from evaluation import (
    CaseResult,
    EvalCase,
    EvalRun,
    EvalSuite,
    EvaluationStore,
    _new_id,
    _now_iso,
    parse_variant_lines,
    render_markdown_report,
    run_evaluation,
)


# ---------------------------------------------------------------------------
# Erwartungs-Syntax des Case-Editors (zeilenweise, testbare Modulfunktionen)
# ---------------------------------------------------------------------------

EXPECTATIONS_HINT = (
    "Erwartungen – eine pro Zeile:\n"
    "enthält: Begriff        · muss im Output vorkommen\n"
    "enthält nicht: Begriff  · darf nicht vorkommen\n"
    "regex: Ausdruck          · muss matchen\n"
    "max_zeichen: 800         · Maximallänge des Outputs\n"
    "json                     · Output muss gültiges JSON sein"
)


def parse_expectations(text: str) -> dict:
    """Parst die Erwartungs-Zeilensyntax in ein Erwartungs-Dict.

    Unbekannte oder ungültige Zeilen lösen ValueError aus.
    """
    result = {
        "must_contain": [],
        "must_not_contain": [],
        "regex": [],
        "max_output_chars": None,
        "expect_json": False,
    }
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        lowered = line.casefold()
        if lowered.startswith("enthält nicht:"):
            value = line.split(":", 1)[1].strip()
            if not value:
                raise ValueError(f"Leere Erwartung: {line}")
            result["must_not_contain"].append(value)
        elif lowered.startswith("enthält:"):
            value = line.split(":", 1)[1].strip()
            if not value:
                raise ValueError(f"Leere Erwartung: {line}")
            result["must_contain"].append(value)
        elif lowered.startswith("regex:"):
            value = line.split(":", 1)[1].strip()
            if not value:
                raise ValueError(f"Leere Erwartung: {line}")
            result["regex"].append(value)
        elif lowered.startswith("max_zeichen:"):
            value = line.split(":", 1)[1].strip()
            try:
                result["max_output_chars"] = int(value)
            except ValueError:
                raise ValueError(f"Ungültige Zeichenzahl: {line}")
        elif lowered == "json":
            result["expect_json"] = True
        else:
            raise ValueError(f"Unbekannte Erwartung: {line}")
    return result


def format_expectations(case: EvalCase) -> str:
    """Serialisiert die Erwartungen eines Cases zurück in die Zeilensyntax."""
    lines = [f"enthält: {item}" for item in case.must_contain]
    lines += [f"enthält nicht: {item}" for item in case.must_not_contain]
    lines += [f"regex: {pattern}" for pattern in case.regex]
    if case.max_output_chars is not None:
        lines.append(f"max_zeichen: {case.max_output_chars}")
    if case.expect_json:
        lines.append("json")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Case-Editor
# ---------------------------------------------------------------------------

class CaseEditorDialog(tk.Toplevel):
    """Editor für einen einzelnen Testfall (Name, Input, Erwartungen)."""

    def __init__(self, parent, case: Optional[EvalCase], on_save):
        super().__init__(parent)
        self.on_save = on_save
        self.title("Testfall bearbeiten" if case else "Neuer Testfall")
        self.geometry("560x560")
        self.transient(parent)

        frame = ttk.Frame(self, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Name:").pack(anchor=tk.W)
        self.name_var = tk.StringVar(value=case.name if case else "")
        ttk.Entry(frame, textvariable=self.name_var).pack(fill=tk.X, pady=(0, 8))

        ttk.Label(frame, text="Input (wird an die Analyse gesendet):").pack(anchor=tk.W)
        self.input_text = scrolledtext.ScrolledText(frame, height=8, wrap=tk.WORD)
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        if case:
            self.input_text.insert("1.0", case.input_text)

        ttk.Label(frame, text=EXPECTATIONS_HINT, justify=tk.LEFT,
                  foreground="#555555").pack(anchor=tk.W)
        self.expect_text = scrolledtext.ScrolledText(frame, height=7, wrap=tk.WORD)
        self.expect_text.pack(fill=tk.X, pady=(4, 8))
        if case:
            self.expect_text.insert("1.0", format_expectations(case))

        buttons = ttk.Frame(frame)
        buttons.pack(fill=tk.X)
        ttk.Button(buttons, text="Speichern",
                   command=self._save).pack(side=tk.RIGHT)
        ttk.Button(buttons, text="Abbrechen",
                   command=self.destroy).pack(side=tk.RIGHT, padx=6)

        self.bind("<Escape>", lambda _e: self.destroy())

    def _save(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Testfall", "Bitte einen Namen angeben.",
                                 parent=self)
            return
        try:
            expectations = parse_expectations(
                self.expect_text.get("1.0", tk.END))
        except ValueError as exc:
            messagebox.showerror("Erwartungen", str(exc), parent=self)
            return
        case = EvalCase(
            id=_new_id(),
            name=name,
            input_text=self.input_text.get("1.0", tk.END).strip(),
            **expectations,
        )
        self.on_save(case)
        self.destroy()


# ---------------------------------------------------------------------------
# Hauptdialog
# ---------------------------------------------------------------------------

_STATUS_LABELS = {
    "done": "fertig",
    "failed": "fehlgeschlagen",
    "privacy_blocked": "datenschutz-blockiert",
    "cancelled": "abgebrochen",
}


class EvaluationDialog(tk.Toplevel):
    """Evaluationssuite: gespeicherte Testfälle × Prompt-/Modell-Varianten."""

    def __init__(self, parent, store: EvaluationStore, models,
                 analyze_fn, default_model: str, privacy_check: bool = True):
        super().__init__(parent)
        self.store = store
        self.models = list(models)
        self.analyze_fn = analyze_fn
        self.default_model = default_model
        self.privacy_check = privacy_check

        self.suites = []
        self.selected_suite: Optional[EvalSuite] = None
        self._run: Optional[EvalRun] = None
        self._run_list = []
        self._result_index = {}
        self._worker: Optional[threading.Thread] = None
        self._cancel_event: Optional[threading.Event] = None
        self._ui_queue: "queue.Queue" = queue.Queue()
        self._ui_poll_active = False

        self.title("Evaluationssuite")
        self.geometry("1100x680")
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        pane = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        left = ttk.Frame(pane, padding=4)
        middle = ttk.Frame(pane, padding=4)
        right = ttk.Frame(pane, padding=4)
        pane.add(left, weight=1)
        pane.add(middle, weight=2)
        pane.add(right, weight=3)

        self._build_suites_column(left)
        self._build_cases_column(middle)
        self._build_run_column(right)

        self._reload_suites()
        self._schedule_ui_drain()

    def _schedule_ui_drain(self):
        """Startet das periodische Abarbeiten der Worker→UI-Queue."""
        if self._ui_poll_active:
            return
        self._ui_poll_active = True
        self._drain_ui_queue()

    def _post(self, callback, *args):
        """Worker-Thread legt hier UI-Callbacks ab (threadsicher)."""
        self._ui_queue.put((callback, args))

    def _drain_ui_queue(self):
        """Führt abgelegte UI-Callbacks auf dem Main-Thread aus."""
        try:
            while True:
                callback, args = self._ui_queue.get_nowait()
                callback(*args)
        except queue.Empty:
            pass
        try:
            self.after(50, self._drain_ui_queue)
        except tk.TclError:
            self._ui_poll_active = False

    # ----- Aufbau -----

    def _build_suites_column(self, parent):
        ttk.Label(parent, text="Suites",
                  font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
        self.suite_list = tk.Listbox(parent, exportselection=False)
        scroll = ttk.Scrollbar(parent, command=self.suite_list.yview)
        self.suite_list.configure(yscrollcommand=scroll.set)
        self.suite_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.LEFT, fill=tk.Y)
        self.suite_list.bind("<<ListboxSelect>>",
                             lambda _e: self._on_suite_selected())

        buttons = ttk.Frame(parent)
        buttons.pack(fill=tk.X, pady=(6, 0))
        for text, command in (
                ("Neu", self._new_suite),
                ("Umbenennen", self._rename_suite),
                ("Löschen", self._delete_suite),
                ("Importieren…", self._import_suite),
                ("Exportieren…", self._export_suite),
                ("Beispiel-Suite anlegen", self._create_sample_suite)):
            ttk.Button(buttons, text=text, command=command).pack(
                fill=tk.X, pady=1)

    def _build_cases_column(self, parent):
        ttk.Label(parent, text="Testfälle",
                  font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
        columns = ("name", "checks", "input_len")
        self.case_tree = ttk.Treeview(parent, columns=columns,
                                      show="headings", height=12)
        self.case_tree.heading("name", text="Name")
        self.case_tree.heading("checks", text="Checks")
        self.case_tree.heading("input_len", text="Input (Zeichen)")
        self.case_tree.column("name", width=180)
        self.case_tree.column("checks", width=60)
        self.case_tree.column("input_len", width=90)
        self.case_tree.pack(fill=tk.BOTH, expand=True, pady=4)

        buttons = ttk.Frame(parent)
        buttons.pack(fill=tk.X)
        ttk.Button(buttons, text="Neu",
                   command=self._new_case).pack(side=tk.LEFT)
        ttk.Button(buttons, text="Bearbeiten",
                   command=self._edit_case).pack(side=tk.LEFT, padx=4)
        ttk.Button(buttons, text="Löschen",
                   command=self._delete_case).pack(side=tk.LEFT)

    def _build_run_column(self, parent):
        ttk.Label(parent, text="Varianten (eine pro Zeile: Modell | Prompt)"
                  ).pack(anchor=tk.W)
        self.variant_text = scrolledtext.ScrolledText(parent, height=5,
                                                      wrap=tk.WORD)
        self.variant_text.pack(fill=tk.X, pady=4)
        self.variant_text.insert(
            "1.0",
            f"{self.default_model} | Fasse den Inhalt in drei Sätzen zusammen.")

        buttons = ttk.Frame(parent)
        buttons.pack(fill=tk.X)
        self.run_btn = ttk.Button(buttons, text="Lauf starten",
                                  command=self._start_run)
        self.run_btn.pack(side=tk.LEFT)
        self.cancel_btn = ttk.Button(buttons, text="Abbrechen",
                                     command=self._cancel_run,
                                     state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT, padx=4)
        ttk.Button(buttons, text="Bericht exportieren…",
                   command=self._export_report).pack(side=tk.LEFT, padx=4)

        history = ttk.Frame(parent)
        history.pack(fill=tk.X, pady=4)
        ttk.Label(history, text="Frühere Läufe:").pack(side=tk.LEFT)
        self.run_combo = ttk.Combobox(history, state="readonly", width=40)
        self.run_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        self.run_combo.bind("<<ComboboxSelected>>",
                            lambda _e: self._load_selected_run())

        self.status_var = tk.StringVar(value="Bereit")
        ttk.Label(parent, textvariable=self.status_var).pack(anchor=tk.W)

        self.result_tree = ttk.Treeview(parent, columns=("info",),
                                        show="tree headings", height=10)
        self.result_tree.heading("#0", text="Variante / Testfall")
        self.result_tree.heading("info", text="Ergebnis")
        self.result_tree.column("#0", width=220)
        self.result_tree.column("info", width=420)
        self.result_tree.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        self.result_tree.bind("<<TreeviewSelect>>",
                              lambda _e: self._on_result_selected())

        ttk.Label(parent, text="Detail:",
                  font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(4, 0))
        self.detail_text = scrolledtext.ScrolledText(parent, height=8,
                                                     wrap=tk.WORD)
        self.detail_text.pack(fill=tk.BOTH, expand=True)
        self.detail_text.configure(state=tk.DISABLED)

    # ----- Suite-CRUD -----

    def _reload_suites(self, select_id: Optional[str] = None):
        self.suites = self.store.list_suites()
        self.suite_list.delete(0, tk.END)
        for suite in self.suites:
            self.suite_list.insert(
                tk.END, f"{suite.name} ({len(suite.cases)} Fälle)")
        if select_id:
            for index, suite in enumerate(self.suites):
                if suite.id == select_id:
                    self.suite_list.selection_set(index)
                    self._on_suite_selected()
                    break

    def _current_suite(self) -> Optional[EvalSuite]:
        selection = self.suite_list.curselection()
        if not selection:
            return self.selected_suite
        self.selected_suite = self.suites[selection[0]]
        return self.selected_suite

    def _on_suite_selected(self):
        suite = self._current_suite()
        self._refresh_cases()
        self._reload_runs()

    def _new_suite(self):
        name = simpledialog.askstring("Neue Suite", "Name der Suite:",
                                      parent=self)
        if not name:
            return
        now = _now_iso()
        suite = EvalSuite(id=_new_id(), name=name.strip(),
                          created_at=now, updated_at=now)
        self.store.save_suite(suite)
        self._reload_suites(select_id=suite.id)

    def _rename_suite(self):
        suite = self._current_suite()
        if not suite:
            return
        name = simpledialog.askstring("Suite umbenennen", "Neuer Name:",
                                      initialvalue=suite.name, parent=self)
        if not name:
            return
        suite.name = name.strip()
        self.store.save_suite(suite)
        self._reload_suites(select_id=suite.id)

    def _delete_suite(self):
        suite = self._current_suite()
        if not suite:
            return
        if not messagebox.askyesno(
                "Suite löschen",
                f"Suite „{suite.name}“ samt aller Läufe löschen?",
                parent=self):
            return
        self.store.delete_suite(suite.id)
        self.selected_suite = None
        self._reload_suites()
        self._refresh_cases()
        self._reload_runs()

    def _import_suite(self):
        path = filedialog.askopenfilename(
            title="Suite importieren",
            filetypes=[("JSON", "*.json"), ("Alle Dateien", "*.*")],
            parent=self)
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as handle:
                suite = EvaluationStore.import_suite_json(handle.read())
        except (ValueError, OSError) as exc:
            messagebox.showerror("Import fehlgeschlagen", str(exc),
                                 parent=self)
            return
        self.store.save_suite(suite)
        self._reload_suites(select_id=suite.id)

    def _export_suite(self):
        suite = self._current_suite()
        if not suite:
            messagebox.showinfo("Export", "Bitte zuerst eine Suite wählen.",
                                parent=self)
            return
        path = filedialog.asksaveasfilename(
            title="Suite exportieren", defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile=f"eval_suite_{suite.name}.json", parent=self)
        if not path:
            return
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(EvaluationStore.export_suite_json(suite))
        self.status_var.set(f"Suite exportiert: {path}")

    def _create_sample_suite(self):
        """Legt eine Beispiel-Suite mit zwei deutschen Testfällen an."""
        now = _now_iso()
        text = ("Die Digitalisierung verändert die Arbeitswelt grundlegend. "
                "Künstliche Intelligenz und Automatisierung schaffen "
                "Effizienzgewinne, erfordern aber neue Kompetenzen und "
                "lebenslanges Lernen in allen Branchen.")
        suite = EvalSuite(
            id=_new_id(),
            name="Beispiel-Suite",
            description="Zwei Beispiel-Testfälle zum Ausprobieren.",
            cases=[
                EvalCase(
                    id=_new_id(), name="Zusammenfassung", input_text=text,
                    must_contain=["Digitalisierung"], max_output_chars=800),
                EvalCase(
                    id=_new_id(), name="Datenextraktion",
                    input_text=("Umsatz 2024: 1,2 Mio. EUR; Mitarbeitende: 45; "
                                "Standorte: Berlin, München"),
                    expect_json=True),
            ],
            created_at=now, updated_at=now)
        self.store.save_suite(suite)
        self._reload_suites(select_id=suite.id)

    # ----- Case-CRUD -----

    def _refresh_cases(self):
        for item in self.case_tree.get_children():
            self.case_tree.delete(item)
        suite = self.selected_suite
        if not suite:
            return
        for index, case in enumerate(suite.cases):
            check_count = (len(case.must_contain) + len(case.must_not_contain)
                           + len(case.regex)
                           + (1 if case.max_output_chars is not None else 0)
                           + (1 if case.expect_json else 0))
            self.case_tree.insert("", tk.END, iid=str(index), values=(
                case.name, check_count, len(case.input_text)))

    def _selected_case_index(self) -> Optional[int]:
        selection = self.case_tree.selection()
        if not selection or self.selected_suite is None:
            return None
        try:
            index = int(selection[0])
        except ValueError:
            return None
        if 0 <= index < len(self.selected_suite.cases):
            return index
        return None

    def _new_case(self):
        suite = self._current_suite()
        if not suite:
            messagebox.showinfo("Kein Suite",
                                "Bitte zuerst eine Suite auswählen oder anlegen.",
                                parent=self)
            return
        CaseEditorDialog(self, None, on_save=self._add_case)

    def _add_case(self, case: EvalCase):
        self.selected_suite.cases.append(case)
        self.store.save_suite(self.selected_suite)
        self._refresh_cases()

    def _edit_case(self):
        index = self._selected_case_index()
        if index is None:
            return
        old = self.selected_suite.cases[index]
        CaseEditorDialog(
            self, old,
            on_save=lambda case: self._replace_case(index, case))

    def _replace_case(self, index: int, case: EvalCase):
        self.selected_suite.cases[index] = case
        self.store.save_suite(self.selected_suite)
        self._refresh_cases()

    def _delete_case(self):
        index = self._selected_case_index()
        if index is None:
            return
        case = self.selected_suite.cases[index]
        if not messagebox.askyesno("Testfall löschen",
                                   f"Testfall „{case.name}“ löschen?",
                                   parent=self):
            return
        del self.selected_suite.cases[index]
        self.store.save_suite(self.selected_suite)
        self._refresh_cases()

    # ----- Lauf -----

    def _set_running(self, running: bool):
        self.run_btn.configure(state=tk.DISABLED if running else tk.NORMAL)
        self.cancel_btn.configure(state=tk.NORMAL if running else tk.DISABLED)

    def _start_run(self):
        suite = self._current_suite()
        if not suite or not suite.cases:
            messagebox.showinfo(
                "Keine Testfälle",
                "Bitte eine Suite mit mindestens einem Testfall wählen.",
                parent=self)
            return
        variants = parse_variant_lines(
            self.variant_text.get("1.0", tk.END), self.models,
            self.default_model)
        if not variants:
            messagebox.showinfo("Keine Varianten",
                                "Bitte mindestens eine Variante angeben.",
                                parent=self)
            return
        self._cancel_event = threading.Event()
        self._set_running(True)
        self.status_var.set("Lauf läuft …")
        self._worker = threading.Thread(
            target=self._run_worker, args=(suite, variants), daemon=True)
        self._worker.start()

    def _run_worker(self, suite, variants):
        def on_progress(done, total, result):
            self._post(self._on_run_progress, done, total, result)

        run = run_evaluation(suite, variants, self.analyze_fn,
                             on_progress=on_progress,
                             cancel_event=self._cancel_event,
                             privacy_check=self.privacy_check)
        try:
            self.store.save_run(run)
        except Exception as exc:
            self._post(self.status_var.set,
                       f"Lauf fertig, aber Speichern fehlgeschlagen: {exc}")
        self._post(self._on_run_finished, run)

    def _on_run_progress(self, done, total, result):
        case_name = result.case_id
        if self.selected_suite:
            for case in self.selected_suite.cases:
                if case.id == result.case_id:
                    case_name = case.name
                    break
        status = _STATUS_LABELS.get(result.status, result.status)
        self.status_var.set(
            f"{done}/{total}: {result.variant_label} · {case_name} → {status}")

    def _on_run_finished(self, run: EvalRun):
        self._set_running(False)
        self.status_var.set("Lauf abgeschlossen")
        self._show_run(run, self.selected_suite)
        self._reload_runs(select_run_id=run.id)

    def _cancel_run(self):
        if self._cancel_event is not None:
            self._cancel_event.set()
            self.status_var.set("Abbruch angefordert …")

    def _on_close(self):
        if self._worker is not None and self._worker.is_alive():
            if not messagebox.askyesno(
                    "Lauf läuft",
                    "Der Evaluationslauf läuft noch. Abbrechen und schließen?",
                    parent=self):
                return
            if self._cancel_event is not None:
                self._cancel_event.set()
        self.destroy()

    # ----- Ergebnis-Anzeige -----

    def _reload_runs(self, select_run_id: Optional[str] = None):
        self._run_list = []
        self.run_combo.configure(values=[])
        if not self.selected_suite:
            return
        self._run_list = self.store.list_runs(self.selected_suite.id)
        self.run_combo.configure(values=[
            f"{run.started_at[:19]} · {len(run.variants)} Variante(n)"
            for run in self._run_list])
        if select_run_id:
            for index, run in enumerate(self._run_list):
                if run.id == select_run_id:
                    self.run_combo.current(index)
                    break

    def _load_selected_run(self):
        index = self.run_combo.current()
        if index < 0 or index >= len(self._run_list):
            return
        run = self.store.get_run(self._run_list[index].id)
        if run:
            self._show_run(run, self.selected_suite)

    def _show_run(self, run: EvalRun, suite: Optional[EvalSuite]):
        self._run = run
        self._result_index.clear()
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        case_names = ({case.id: case.name for case in suite.cases}
                      if suite else {})
        summaries = {s.label: s for s in run.summary()}
        best = run.best_variant()
        for variant in run.variants:
            summary = summaries.get(variant.label)
            if summary is None:
                continue
            rate = (f"{summary.check_pass_rate:.0%}"
                    if summary.check_pass_rate is not None else "–")
            star = "★ " if variant.label == best else ""
            parent_iid = self.result_tree.insert(
                "", tk.END, text=f"{star}{variant.label}",
                values=(f"bestanden {summary.cases_passed}/"
                        f"{summary.cases_total} · Checks {rate} · "
                        f"{summary.total_tokens} Tokens · "
                        f"${summary.total_cost:.4f} · "
                        f"Ø {summary.avg_duration_s:.1f}s",))
            for result in run.results:
                if result.variant_label != variant.label:
                    continue
                case_name = case_names.get(result.case_id, result.case_id)
                status = _STATUS_LABELS.get(result.status, result.status)
                passed = sum(1 for c in result.checks if c.passed)
                iid = self.result_tree.insert(
                    parent_iid, tk.END, text=case_name,
                    values=(f"{status} · Checks {passed}/"
                            f"{len(result.checks)} · "
                            f"{result.prompt_tokens + result.completion_tokens}"
                            f" Tokens · {result.duration_s:.1f}s",))
                self._result_index[iid] = result
        for item in self.result_tree.get_children():
            self.result_tree.item(item, open=True)

    def _on_result_selected(self):
        selection = self.result_tree.selection()
        result = self._result_index.get(selection[0]) if selection else None
        self.detail_text.configure(state=tk.NORMAL)
        self.detail_text.delete("1.0", tk.END)
        if result is not None:
            self.detail_text.insert("1.0", self._detail_for(result))
        self.detail_text.configure(state=tk.DISABLED)

    @staticmethod
    def _detail_for(result: CaseResult) -> str:
        status = _STATUS_LABELS.get(result.status, result.status)
        lines = [f"Status: {status}"]
        if result.status == "privacy_blocked":
            lines.append(
                "Nicht gesendet: lokale Datenschutzprüfung hat sensible "
                "Daten erkannt.")
        if result.error_message and result.status != "privacy_blocked":
            lines.append(f"Fehler: {result.error_message}")
        if result.checks:
            lines.append("")
            lines.append("Checks:")
            for check in result.checks:
                mark = "✓" if check.passed else "✗"
                suffix = f" — {check.detail}" if check.detail else ""
                lines.append(f"{mark} {check.name}{suffix}")
        if result.content:
            lines.append("")
            lines.append("Output:")
            lines.append(result.content)
        return "\n".join(lines)

    # ----- Bericht -----

    def _export_report(self):
        if self._run is None:
            messagebox.showinfo("Bericht",
                                "Es liegt noch kein Lauf vor.", parent=self)
            return
        suite = self.selected_suite
        if suite is None or suite.id != self._run.suite_id:
            suite = self.store.get_suite(self._run.suite_id)
        if suite is None:
            messagebox.showerror("Bericht", "Suite zum Lauf nicht gefunden.",
                                 parent=self)
            return
        path = filedialog.asksaveasfilename(
            title="Bericht exportieren", defaultextension=".md",
            filetypes=[("Markdown", "*.md")],
            initialfile=f"eval_bericht_{self._run.id[:8]}.md", parent=self)
        if not path:
            return
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(render_markdown_report(self._run, suite))
        self.status_var.set(f"Bericht exportiert: {path}")
