"""Dialoge für Projekte, Rezepte und Ergebnis-Versionen (M6).

Alle Dialoge sind bewusst schlicht gehalten und greifen über die Manager-
Klassen (`ProjectManager`, `RecipeManager`, `ResultsManager`) auf die
Persistenz zu. Sie blockieren nicht modal – der Aufrufer erhält über
Callbacks bzw. direkte Rückgaben Rückmeldung.
"""

import os
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, simpledialog, ttk
from tkinter import scrolledtext
from typing import Optional


class ProjectsDialog(tk.Toplevel):
    """Projektliste mit Erstellen, Archivieren, Löschen und Zuordnen."""

    def __init__(self, parent, project_manager, results_manager,
                 current_result_id: Optional[str] = None,
                 on_change=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.results_manager = results_manager
        self.current_result_id = current_result_id
        self.on_change = on_change
        self.title("Projekte verwalten")
        self.geometry("560x420")
        self.transient(parent)

        frame = ttk.Frame(self, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        self.show_archived_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame, text="Archivierte anzeigen",
            variable=self.show_archived_var,
            command=self._refresh
        ).pack(anchor=tk.W)

        columns = ("name", "results", "archived")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=10)
        self.tree.heading("name", text="Name")
        self.tree.heading("results", text="Ergebnisse")
        self.tree.heading("archived", text="Archiviert")
        self.tree.column("name", width=240)
        self.tree.column("results", width=90, anchor=tk.CENTER)
        self.tree.column("archived", width=80, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=5)

        btns = ttk.Frame(frame)
        btns.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(btns, text="Neu", command=self._create).pack(side=tk.LEFT)
        ttk.Button(btns, text="Umbenennen", command=self._rename).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Archivieren/Wiederherstellen",
                   command=self._toggle_archive).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Löschen", command=self._delete).pack(side=tk.LEFT, padx=4)
        if current_result_id:
            ttk.Button(btns, text="Aktuelles Ergebnis zuordnen",
                       command=self._assign_current).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Schließen", command=self.destroy).pack(side=tk.RIGHT)

        self._refresh()
        self.bind("<Escape>", lambda _e: self.destroy())

    def _selected_project(self):
        selection = self.tree.selection()
        if not selection:
            return None
        return self.project_manager.get_project(selection[0])

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        for project in self.project_manager.list_projects(
                include_archived=self.show_archived_var.get()):
            count = len(self.project_manager.get_project_result_ids(project.id))
            self.tree.insert("", tk.END, iid=project.id, values=(
                project.name, count, "ja" if project.archived else "–"
            ))

    def _create(self):
        name = simpledialog.askstring("Neues Projekt", "Projektname:", parent=self)
        if not name:
            return
        try:
            self.project_manager.create_project(name)
            self._refresh()
        except ValueError as exc:
            messagebox.showerror("Fehler", str(exc), parent=self)

    def _rename(self):
        project = self._selected_project()
        if not project:
            return
        name = simpledialog.askstring("Umbenennen", "Neuer Name:",
                                      initialvalue=project.name, parent=self)
        if name and name != project.name:
            try:
                self.project_manager.update_project(project.id, name=name)
                self._refresh()
            except ValueError as exc:
                messagebox.showerror("Fehler", str(exc), parent=self)

    def _toggle_archive(self):
        project = self._selected_project()
        if project:
            self.project_manager.set_archived(project.id, not project.archived)
            self._refresh()

    def _delete(self):
        project = self._selected_project()
        if not project:
            return
        if messagebox.askyesno(
                "Projekt löschen",
                f"Projekt '{project.name}' löschen?\n"
                "Zugeordnete Ergebnisse bleiben erhalten.", parent=self):
            self.project_manager.delete_project(project.id)
            self._refresh()
            if self.on_change:
                self.on_change()

    def _assign_current(self):
        project = self._selected_project()
        if project and self.current_result_id:
            self.project_manager.assign_result(self.current_result_id, project.id)
            self._refresh()
            if self.on_change:
                self.on_change()
            messagebox.showinfo("Zugeordnet",
                                f"Ergebnis wurde '{project.name}' zugeordnet.",
                                parent=self)


class RecipesDialog(tk.Toplevel):
    """Rezeptliste mit Erstellen-aus-aktueller-Eingabe, Anwenden und Löschen."""

    def __init__(self, parent, recipe_manager, on_apply=None,
                 current_prompt: str = "", current_model: str = ""):
        super().__init__(parent)
        self.recipe_manager = recipe_manager
        self.on_apply = on_apply
        self.current_prompt = current_prompt
        self.current_model = current_model
        self.title("Analyse-Rezepte")
        self.geometry("600x420")
        self.transient(parent)

        frame = ttk.Frame(self, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        columns = ("name", "source", "model")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=10)
        self.tree.heading("name", text="Name")
        self.tree.heading("source", text="Quelltyp")
        self.tree.heading("model", text="Modell")
        self.tree.column("name", width=260)
        self.tree.column("source", width=110)
        self.tree.column("model", width=130)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=5)
        self.tree.bind("<Double-1>", lambda _e: self._apply())

        detail = ttk.Label(frame, text="", wraplength=560, justify=tk.LEFT)
        detail.pack(fill=tk.X, pady=4)
        self._detail = detail
        self.tree.bind("<<TreeviewSelect>>", self._show_detail)

        btns = ttk.Frame(frame)
        btns.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(btns, text="Aus aktuellem Prompt erstellen",
                   command=self._create_from_current).pack(side=tk.LEFT)
        ttk.Button(btns, text="Anwenden", command=self._apply).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Löschen", command=self._delete).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Schließen", command=self.destroy).pack(side=tk.RIGHT)

        self._refresh()
        self.bind("<Escape>", lambda _e: self.destroy())

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        for recipe in self.recipe_manager.list_recipes():
            self.tree.insert("", tk.END, iid=recipe.id, values=(
                recipe.name, recipe.source_type, recipe.model or "Standard"
            ))

    def _selected_recipe(self):
        selection = self.tree.selection()
        if not selection:
            return None
        return self.recipe_manager.get_recipe(selection[0])

    def _show_detail(self, _event=None):
        recipe = self._selected_recipe()
        if not recipe:
            return
        text = recipe.prompt_template[:200]
        if len(recipe.prompt_template) > 200:
            text += "…"
        extra = []
        if recipe.follow_up_actions:
            extra.append(f"Folgeaktionen: {', '.join(recipe.follow_up_actions)}")
        if recipe.export_format:
            extra.append(f"Export: {recipe.export_format}")
        self._detail.config(text=f"{text}\n{' | '.join(extra)}".strip())

    def _create_from_current(self):
        if not self.current_prompt.strip():
            messagebox.showinfo(
                "Kein Prompt",
                "Bitte zuerst einen eigenen Prompt im Prompt-Feld eingeben.",
                parent=self)
            return
        name = simpledialog.askstring("Rezept speichern", "Rezeptname:", parent=self)
        if not name:
            return
        try:
            self.recipe_manager.create_recipe(
                name=name,
                prompt_template=self.current_prompt.strip(),
                model=self.current_model or None,
            )
            self._refresh()
        except ValueError as exc:
            messagebox.showerror("Fehler", str(exc), parent=self)

    def _apply(self):
        recipe = self._selected_recipe()
        if recipe and self.on_apply:
            self.on_apply(recipe)
            self.destroy()

    def _delete(self):
        recipe = self._selected_recipe()
        if recipe and messagebox.askyesno(
                "Rezept löschen", f"Rezept '{recipe.name}' löschen?", parent=self):
            self.recipe_manager.delete_recipe(recipe.id)
            self._refresh()


class EditResultDialog(tk.Toplevel):
    """Ergebnis bearbeiten – Speichern legt automatisch eine Vorversion an."""

    def __init__(self, parent, results_manager, result_id: str, on_saved=None):
        super().__init__(parent)
        self.results_manager = results_manager
        self.result_id = result_id
        self.on_saved = on_saved
        self.title("Ergebnis bearbeiten")
        self.geometry("700x500")
        self.transient(parent)

        result = results_manager.load_result(result_id)
        if result is None:
            messagebox.showerror("Fehler", "Ergebnis nicht gefunden.", parent=parent)
            self.destroy()
            return

        frame = ttk.Frame(self, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="Inhalt (Änderungen werden als neue Version gespeichert):"
                  ).pack(anchor=tk.W)
        self.editor = scrolledtext.ScrolledText(frame, wrap=tk.WORD)
        self.editor.pack(fill=tk.BOTH, expand=True, pady=5)
        self.editor.insert("1.0", result.content)

        btns = ttk.Frame(frame)
        btns.pack(fill=tk.X)
        ttk.Button(btns, text="Speichern", command=self._save).pack(side=tk.LEFT)
        ttk.Button(btns, text="Abbrechen", command=self.destroy).pack(side=tk.RIGHT)
        self.bind("<Escape>", lambda _e: self.destroy())

    def _save(self):
        new_content = self.editor.get("1.0", tk.END).rstrip("\n")
        if self.results_manager.update_result_content(self.result_id, new_content):
            if self.on_saved:
                self.on_saved()
            self.destroy()
        else:
            messagebox.showerror("Fehler", "Ergebnis konnte nicht gespeichert werden.",
                                 parent=self)


class VersionsDialog(tk.Toplevel):
    """Versionsverlauf eines Ergebnisses mit Diff-Ansicht und Rollback."""

    def __init__(self, parent, results_manager, result_id: str, on_change=None):
        super().__init__(parent)
        self.results_manager = results_manager
        self.result_id = result_id
        self.on_change = on_change
        self.title("Versionsverlauf")
        self.geometry("640x480")
        self.transient(parent)

        frame = ttk.Frame(self, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        columns = ("version", "created", "note", "size")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=8)
        self.tree.heading("version", text="Version")
        self.tree.heading("created", text="Erstellt")
        self.tree.heading("note", text="Notiz")
        self.tree.heading("size", text="Größe")
        self.tree.column("version", width=70, anchor=tk.CENTER)
        self.tree.column("created", width=150)
        self.tree.column("note", width=220)
        self.tree.column("size", width=80, anchor=tk.E)
        self.tree.pack(fill=tk.X, pady=5)

        self.diff_text = scrolledtext.ScrolledText(frame, wrap=tk.NONE, height=14)
        self.diff_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.diff_text.config(state=tk.DISABLED)

        btns = ttk.Frame(frame)
        btns.pack(fill=tk.X)
        ttk.Button(btns, text="Diff zu aktuell",
                   command=self._diff_current).pack(side=tk.LEFT)
        ttk.Button(btns, text="Wiederherstellen",
                   command=self._rollback).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Schließen", command=self.destroy).pack(side=tk.RIGHT)

        self._refresh()
        self.bind("<Escape>", lambda _e: self.destroy())

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        for version in self.results_manager.list_versions(self.result_id):
            self.tree.insert("", tk.END, iid=version["id"], values=(
                f"v{version['version_no']}", version["created_at"][:19],
                version["note"], f"{version['size']} Z."
            ))

    def _selected_version(self):
        selection = self.tree.selection()
        return selection[0] if selection else None

    def _show_diff(self, diff: Optional[str]):
        self.diff_text.config(state=tk.NORMAL)
        self.diff_text.delete("1.0", tk.END)
        self.diff_text.insert("1.0", diff or "Kein Diff verfügbar.")
        self.diff_text.config(state=tk.DISABLED)

    def _diff_current(self):
        version_id = self._selected_version()
        if not version_id:
            return
        self._show_diff(self.results_manager.diff_versions(
            self.result_id, version_id, "current"))

    def _rollback(self):
        version_id = self._selected_version()
        if not version_id:
            return
        if not messagebox.askyesno(
                "Wiederherstellen",
                "Diese Version wiederherstellen?\n"
                "Der aktuelle Inhalt wird vorher als Version gesichert.",
                parent=self):
            return
        if self.results_manager.rollback_to_version(self.result_id, version_id):
            self._refresh()
            if self.on_change:
                self.on_change()
            messagebox.showinfo("Wiederhergestellt",
                                "Die Version wurde wiederhergestellt.", parent=self)


class BatchDialog(tk.Toplevel):
    """Batch-Queue: Jobs anlegen, starten, pausieren, abbrechen, verfolgen."""

    def __init__(self, parent, batch_queue, on_result_saved=None):
        super().__init__(parent)
        self.batch_queue = batch_queue
        self.on_result_saved = on_result_saved
        self.title("Batch-Verarbeitung")
        self.geometry("720x520")
        self.transient(parent)

        frame = ttk.Frame(self, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Neuer Job
        create_frame = ttk.LabelFrame(frame, text="Neuer Batch-Job", padding=8)
        create_frame.pack(fill=tk.X)

        ttk.Label(create_frame, text="Prompt (Platzhalter {text} optional):"
                  ).grid(row=0, column=0, sticky=tk.W)
        self.prompt_text = tk.Text(create_frame, height=3, wrap=tk.WORD)
        self.prompt_text.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=4)
        self.prompt_text.insert("1.0", "Fasse den Inhalt zusammen: {text}")

        self.files_var = tk.StringVar(value="Keine Dateien gewählt")
        ttk.Label(create_frame, textvariable=self.files_var).grid(
            row=2, column=0, sticky=tk.W)
        ttk.Button(create_frame, text="Dateien wählen…",
                   command=self._pick_files).grid(row=2, column=1, padx=4)
        ttk.Label(create_frame, text="Parallel:").grid(row=2, column=2, sticky=tk.E)
        self.concurrency_var = tk.Spinbox(create_frame, from_=1, to=4, width=3)
        self.concurrency_var.grid(row=2, column=3, padx=4)
        ttk.Button(create_frame, text="Job erstellen & starten",
                   command=self._create_job).grid(row=3, column=0, sticky=tk.W, pady=4)
        create_frame.columnconfigure(0, weight=1)
        self._selected_files = []

        # Jobliste
        list_frame = ttk.LabelFrame(frame, text="Jobs", padding=8)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=8)

        columns = ("name", "status", "progress", "cost")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)
        for col, label, width in (("name", "Name", 220), ("status", "Status", 100),
                                  ("progress", "Fortschritt", 160),
                                  ("cost", "Kosten", 90)):
            self.tree.heading(col, text=label)
            self.tree.column(col, width=width)
        self.tree.pack(fill=tk.BOTH, expand=True)

        btns = ttk.Frame(list_frame)
        btns.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(btns, text="Start/Fortsetzen", command=self._start).pack(side=tk.LEFT)
        ttk.Button(btns, text="Pause", command=self._pause).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Abbrechen", command=self._cancel).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Löschen", command=self._delete).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Schließen", command=self.destroy).pack(side=tk.RIGHT)

        self._refresh()
        self.bind("<Escape>", lambda _e: self.destroy())

    def _pick_files(self):
        from tkinter import filedialog as fd
        files = fd.askopenfilenames(parent=self, title="Dateien für Batch wählen")
        if files:
            self._selected_files = list(files)
            self.files_var.set(f"{len(files)} Datei(en) gewählt")

    def _create_job(self):
        if not self._selected_files:
            messagebox.showinfo("Keine Dateien",
                                "Bitte zuerst Dateien wählen.", parent=self)
            return
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showinfo("Kein Prompt", "Bitte einen Prompt eingeben.",
                                parent=self)
            return

        # Kombinierte Übertragungsbestätigung für den Batch-Prompt.
        from transfer_confirmation import confirm_transfer
        decision = confirm_transfer(
            self, prompt, source_type="file",
        )
        if not decision.proceed:
            return

        items = []
        for path in self._selected_files:
            ext = os.path.splitext(path)[1].lower()
            items.append({
                "source": path,
                "source_type": "pdf" if ext == ".pdf" else "file",
            })
        try:
            job_id = self.batch_queue.create_job(
                name=f"Batch {datetime.now().strftime('%d.%m. %H:%M')}",
                prompt=decision.content,
                items=items,
                concurrency=int(self.concurrency_var.get() or 1),
            )
        except ValueError as exc:
            messagebox.showerror("Fehler", str(exc), parent=self)
            return
        self.batch_queue.start_job(job_id, on_progress=self._on_progress)
        self._refresh()

    def _selected_job(self):
        selection = self.tree.selection()
        return selection[0] if selection else None

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        for job in self.batch_queue.list_jobs():
            progress = self.batch_queue.get_job_progress(job.id)
            total = progress["total"]
            done = progress["done"] + progress["skipped"]
            failed = progress["failed"] + progress["cancelled"]
            text = f"{done}/{total} fertig"
            if failed:
                text += f", {failed} fehlgeschlagen"
            self.tree.insert("", tk.END, iid=job.id, values=(
                job.name, job.status, text, f"${progress['cost']:.4f}"))

    def _on_progress(self, _job_id):
        try:
            self.after(0, self._refresh)
        except tk.TclError:
            pass
        if self.on_result_saved:
            try:
                self.after(0, self.on_result_saved)
            except tk.TclError:
                pass

    def _start(self):
        job_id = self._selected_job()
        if job_id:
            self.batch_queue.resume_job(job_id, on_progress=self._on_progress)
            self._refresh()

    def _pause(self):
        job_id = self._selected_job()
        if job_id:
            self.batch_queue.pause_job(job_id)
            self._refresh()

    def _cancel(self):
        job_id = self._selected_job()
        if job_id and messagebox.askyesno(
                "Batch abbrechen", "Offene Items werden abgebrochen. Fortfahren?",
                parent=self):
            self.batch_queue.cancel_job(job_id)
            self._refresh()

    def _delete(self):
        job_id = self._selected_job()
        if job_id and messagebox.askyesno(
                "Job löschen", "Job und Item-Historie löschen?", parent=self):
            self.batch_queue.delete_job(job_id)
            self._refresh()


class EvidenceDialog(tk.Toplevel):
    """Prüft Zitate und Referenzen eines Ergebnisses gegen die Quelle (M8).

    `source_loader` ist ein Callable ohne Argumente, das den Quelltext
    (oder None) zurückgibt. So bleibt der Dialog frei von Extraktionslogik.
    """

    _STATUS_LABELS = {
        "verified": "Verifiziert",
        "unverified": "Nicht gefunden",
        "plausible": "Plausibel",
        "not_checkable": "Nicht prüfbar",
    }

    def __init__(self, parent, result_text: str, source_loader, source_name: str = ""):
        super().__init__(parent)
        self.title("Quellenbelege prüfen")
        self.geometry("680x460")
        self.transient(parent)
        self._result_text = result_text
        self._source_loader = source_loader
        self._source_name = source_name

        frame = ttk.Frame(self, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        self.summary_var = tk.StringVar(value="Prüfe Belege …")
        ttk.Label(frame, textvariable=self.summary_var).pack(anchor=tk.W)

        columns = ("kind", "status", "text")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=10)
        self.tree.heading("kind", text="Art")
        self.tree.heading("status", text="Status")
        self.tree.heading("text", text="Beleg")
        self.tree.column("kind", width=80)
        self.tree.column("status", width=110)
        self.tree.column("text", width=430)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=5)
        self.tree.bind("<<TreeviewSelect>>", self._show_excerpt)

        self.excerpt = scrolledtext.ScrolledText(frame, height=8, wrap=tk.WORD)
        self.excerpt.pack(fill=tk.BOTH, expand=False)
        self.excerpt.configure(state=tk.DISABLED)

        ttk.Button(frame, text="Schließen", command=self.destroy).pack(
            anchor=tk.E, pady=(6, 0))

        self._report = None
        self._start_loading()

    def _start_loading(self):
        """Quell-Laden (OCR/Netzwerk) im Hintergrund-Thread ausführen."""
        import threading
        self.summary_var.set("Quelle wird geladen und geprüft …")
        threading.Thread(target=self._run_check, daemon=True).start()

    def _run_check(self):
        from evidence import validate_evidence
        try:
            source = self._source_loader() if self._source_loader else None
        except Exception:
            source = None
        self._report = validate_evidence(self._result_text, source)
        self.after(0, self._populate, source)

    def _populate(self, source):
        report = self._report
        if report is None:
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        if not report.citations:
            self.summary_var.set("Keine Zitate oder Referenzen im Ergebnis gefunden.")
            return
        if not report.source_available:
            hint = (f"Quelle '{self._source_name}' ist nicht mehr verfügbar – "
                    "Belege können nicht verifiziert werden.")
        else:
            hint = (f"{report.verified_count} verifiziert, "
                    f"{report.unverified_count} nicht gefunden, "
                    f"{report.plausible_count} plausibel, "
                    f"{report.not_checkable_count} nicht prüfbar.")
        self.summary_var.set(hint)
        for index, citation in enumerate(report.citations):
            self.tree.insert(
                "", tk.END, iid=str(index),
                values=(citation.kind,
                        self._STATUS_LABELS.get(citation.status, citation.status),
                        citation.text[:120]))

    def _show_excerpt(self, _event=None):
        selection = self.tree.selection()
        if not selection or self._report is None:
            return
        citation = self._report.citations[int(selection[0])]
        self.excerpt.configure(state=tk.NORMAL)
        self.excerpt.delete("1.0", tk.END)
        if citation.source_excerpt:
            self.excerpt.insert("1.0",
                f"Quelltext-Auszug:\n\n{citation.source_excerpt}")
        elif citation.status == "unverified":
            self.excerpt.insert("1.0",
                "Diese Angabe wurde in der Quelle nicht gefunden.\n"
                "Mögliche Ursachen: Umformulierung durch das Modell oder "
                "frei erfundener Beleg – bitte manuell nachprüfen.")
        elif citation.status == "plausible":
            self.excerpt.insert("1.0",
                "Diese Referenz existiert strukturell in der Quelle "
                "(z. B. Seite oder Zeitpunkt), der Inhalt wurde aber nicht "
                "gegengeprüft – bitte stichprobenartig verifizieren.")
        else:
            self.excerpt.insert("1.0",
                "Diese Angabe ist ohne die Original-Quellstruktur nicht "
                "automatisch prüfbar (z. B. Seiten- oder Zeitangabe).")
        self.excerpt.configure(state=tk.DISABLED)


class EditDataDialog(tk.Toplevel):
    """JSON-Editor für die extrahierten strukturierten Daten eines Ergebnisses."""

    def __init__(self, parent, results_manager, result_id: str, on_saved=None):
        super().__init__(parent)
        import json
        self.results_manager = results_manager
        self.result_id = result_id
        self.on_saved = on_saved
        self.title("Extrahierte Daten bearbeiten")
        self.geometry("640x520")
        self.transient(parent)

        result = results_manager.load_result(result_id)
        if result is None:
            messagebox.showerror("Fehler", "Ergebnis konnte nicht geladen werden.",
                                 parent=self)
            self.destroy()
            return
        self._result = result

        frame = ttk.Frame(self, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(
            frame,
            text=("Strukturierte Daten als JSON bearbeiten. Das Format muss dem "
                  "Schema 'StructuredData' entsprechen (tables, entities, "
                  "numeric_values, temporal_data, relationships, categories)."),
            wraplength=600, justify=tk.LEFT,
        ).pack(anchor=tk.W)

        self.editor = scrolledtext.ScrolledText(frame, wrap=tk.NONE, undo=True)
        self.editor.pack(fill=tk.BOTH, expand=True, pady=6)
        self.editor.insert("1.0", json.dumps(
            result.extracted_data.to_dict(), indent=2, ensure_ascii=False))

        btns = ttk.Frame(frame)
        btns.pack(fill=tk.X)
        ttk.Button(btns, text="Speichern", command=self._save).pack(side=tk.RIGHT)
        ttk.Button(btns, text="Abbrechen", command=self.destroy).pack(
            side=tk.RIGHT, padx=6)
        ttk.Button(btns, text="Validieren", command=self._validate).pack(
            side=tk.LEFT)

    def _parse(self):
        import json
        from data_models import StructuredData
        raw = self.editor.get("1.0", tk.END).strip()
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Oberste Ebene muss ein JSON-Objekt sein.")
        return StructuredData.from_dict(data)

    def _validate(self):
        try:
            parsed = self._parse()
        except Exception as exc:
            messagebox.showerror("Ungültig", f"JSON ist nicht valide:\n{exc}",
                                 parent=self)
            return
        messagebox.showinfo(
            "Valide",
            f"Gültige Struktur: {len(parsed.tables)} Tabelle(n), "
            f"{len(parsed.entities)} Entität(en).",
            parent=self)

    def _save(self):
        try:
            self._result.extracted_data = self._parse()
        except Exception as exc:
            messagebox.showerror("Ungültig", f"JSON ist nicht valide:\n{exc}",
                                 parent=self)
            return
        if not messagebox.askyesno(
                "Speichern",
                "Daten speichern? Der bisherige Stand wird als Version "
                "im Versionsverlauf gesichert.", parent=self):
            return
        if self.results_manager.update_result(self._result):
            if self.on_saved:
                self.on_saved()
            self.destroy()
        else:
            messagebox.showerror("Fehler", "Speichern fehlgeschlagen.", parent=self)


class ChartSuggestionsDialog(tk.Toplevel):
    """Zeigt Spaltenrollen und begründete Diagrammvorschläge für eine Tabelle."""

    def __init__(self, parent, table, table_name: str = "Tabelle"):
        super().__init__(parent)
        from column_analysis import analyze_columns, suggest_charts
        self.title(f"Diagramm-Vorschläge – {table_name}")
        self.geometry("640x460")
        self.transient(parent)

        frame = ttk.Frame(self, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Spaltenanalyse",
                  font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W)
        col_tree = ttk.Treeview(
            frame, columns=("role", "missing", "unique"),
            show="headings", height=6)
        col_tree.heading("role", text="Rolle")
        col_tree.heading("missing", text="Fehlend")
        col_tree.heading("unique", text="Eindeutig")
        col_tree.column("role", width=110)
        col_tree.column("missing", width=90, anchor=tk.CENTER)
        col_tree.column("unique", width=90, anchor=tk.CENTER)
        col_tree["displaycolumns"] = ("role", "missing", "unique")
        # Header als erste Spalte via tags geht nicht – Text stattdessen:
        col_tree.pack(fill=tk.X, pady=(2, 10))
        for profile in analyze_columns(table):
            col_tree.insert("", tk.END, text=profile.header,
                            values=(profile.role,
                                    f"{profile.missing}/{profile.total}",
                                    profile.unique_count))
        # Header-Spalte sichtbar machen
        col_tree.configure(show="tree headings")
        col_tree.heading("#0", text="Spalte")
        col_tree.column("#0", width=160)

        ttk.Label(frame, text="Vorschläge",
                  font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W)
        sug_tree = ttk.Treeview(
            frame, columns=("chart", "reason"), show="headings", height=8)
        sug_tree.heading("chart", text="Diagramm")
        sug_tree.heading("reason", text="Begründung")
        sug_tree.column("chart", width=90)
        sug_tree.column("reason", width=520)
        sug_tree.pack(fill=tk.BOTH, expand=True, pady=2)

        suggestions = suggest_charts(table)
        if not suggestions:
            sug_tree.insert("", tk.END, values=(
                "–", "Keine geeignete Visualisierung für diese Tabelle gefunden."))
        for suggestion in suggestions:
            reason = suggestion.reason
            if suggestion.missing_value_hint:
                reason += f" {suggestion.missing_value_hint}"
            sug_tree.insert("", tk.END, values=(suggestion.chart_type, reason))

        ttk.Button(frame, text="Schließen", command=self.destroy).pack(
            anchor=tk.E, pady=(8, 0))


class PromptPlaygroundDialog(tk.Toplevel):
    """Vergleicht mehrere Prompt-/Modell-Varianten auf demselben Inhalt (M8).

    `analyze_fn` wird als analyze_fn(content, prompt, model) -> AnalysisOutcome
    aufgerufen und muss thread-sicher sein (ein Worker-Thread pro Lauf,
    Läufe sequenziell).
    """

    def __init__(self, parent, content: str, models, analyze_fn):
        super().__init__(parent)
        import threading
        self._threading = threading
        self.content = content
        self.models = list(models)
        self.analyze_fn = analyze_fn
        self._cancelled = False
        self._worker = None
        self._variants = []
        self.title("Prompt-Playground")
        self.geometry("860x560")
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        pane = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        left = ttk.Frame(pane, padding=4)
        right = ttk.Frame(pane, padding=4)
        pane.add(left, weight=1)
        pane.add(right, weight=2)

        ttk.Label(left, text="Varianten (eine pro Zeile: Modell | Prompt)",
                  wraplength=280).pack(anchor=tk.W)
        self.variant_entry = scrolledtext.ScrolledText(left, height=6, wrap=tk.WORD)
        self.variant_entry.pack(fill=tk.X, pady=4)
        default_model = self.models[0] if self.models else "gpt-4o-mini"
        self.variant_entry.insert("1.0",
            f"{default_model} | Fasse den Inhalt in drei Sätzen zusammen.\n"
            f"{default_model} | Liste die wichtigsten Aussagen als Stichpunkte.")

        self.run_btn = ttk.Button(left, text="Alle ausführen", command=self._run)
        self.run_btn.pack(anchor=tk.W)
        self.cancel_btn = ttk.Button(left, text="Abbrechen",
                                     command=self._cancel, state=tk.DISABLED)
        self.cancel_btn.pack(anchor=tk.W, pady=4)
        self.status_var = tk.StringVar(value="Bereit")
        ttk.Label(left, textvariable=self.status_var, wraplength=280).pack(
            anchor=tk.W, pady=4)

        self.results_nb = ttk.Notebook(right)
        self.results_nb.pack(fill=tk.BOTH, expand=True)

    def _parse_variants(self):
        """Parst „Modell | Prompt"-Zeilen über die gemeinsame Logik
        aus evaluation.parse_variant_lines; gibt (model, prompt)-Tupel."""
        from evaluation import parse_variant_lines
        default_model = self.models[0] if self.models else ""
        return [(v.model, v.prompt) for v in parse_variant_lines(
            self.variant_entry.get("1.0", tk.END), self.models,
            default_model)]

    def _run(self):
        variants = self._parse_variants()
        if not variants:
            messagebox.showinfo("Keine Varianten",
                                "Bitte mindestens eine Variante angeben.",
                                parent=self)
            return
        if not self.content.strip():
            messagebox.showinfo("Kein Inhalt",
                                "Es ist kein Inhalt für den Vergleich geladen.",
                                parent=self)
            return
        self._cancelled = False
        self.run_btn.configure(state=tk.DISABLED)
        self.cancel_btn.configure(state=tk.NORMAL)
        for tab in self.results_nb.tabs():
            self.results_nb.forget(tab)
        self._worker = self._threading.Thread(
            target=self._run_worker, args=(variants,), daemon=True)
        self._worker.start()

    def _run_worker(self, variants):
        import time
        for index, (model, prompt) in enumerate(variants):
            if self._cancelled:
                break
            self.after(0, self.status_var.set,
                       f"Variante {index + 1}/{len(variants)} läuft ({model}) …")
            started = time.time()
            try:
                outcome = self.analyze_fn(self.content, prompt, model)
                elapsed = time.time() - started
                if outcome.success:
                    total_tokens = ((outcome.prompt_tokens or 0)
                                    + (outcome.completion_tokens or 0))
                    text = (outcome.content or "")
                    meta = (f"Modell: {model}  |  Dauer: {elapsed:.1f}s  |  "
                            f"Tokens: {total_tokens or '–'}")
                else:
                    text = f"Fehler: {getattr(outcome.error, 'user_message', outcome.error)}"
                    meta = f"Modell: {model}  |  fehlgeschlagen nach {elapsed:.1f}s"
            except Exception as exc:
                text = f"Fehler: {exc}"
                meta = f"Modell: {model}  |  fehlgeschlagen"
            self.after(0, self._add_result_tab, index, model, prompt, meta, text)
        self.after(0, self._finish_run, len(variants))

    def _add_result_tab(self, index, model, prompt, meta, text):
        frame = ttk.Frame(self.results_nb, padding=6)
        ttk.Label(frame, text=meta).pack(anchor=tk.W)
        ttk.Label(frame, text=f"Prompt: {prompt}", wraplength=480,
                  foreground="#555").pack(anchor=tk.W)
        view = scrolledtext.ScrolledText(frame, wrap=tk.WORD)
        view.pack(fill=tk.BOTH, expand=True, pady=4)
        view.insert("1.0", text)
        view.configure(state=tk.DISABLED)
        self.results_nb.add(frame, text=f"{index + 1}. {model}")

    def _finish_run(self, total):
        self.run_btn.configure(state=tk.NORMAL)
        self.cancel_btn.configure(state=tk.DISABLED)
        self.status_var.set(
            "Abgebrochen." if self._cancelled else f"Fertig – {total} Variante(n).")

    def _cancel(self):
        self._cancelled = True
        self.status_var.set("Abbruch angefordert …")

    def _on_close(self):
        self._cancelled = True
        self.destroy()
