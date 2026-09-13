"""Dialoge für Projekte, Rezepte und Ergebnis-Versionen (M6).

Alle Dialoge sind bewusst schlicht gehalten und greifen über die Manager-
Klassen (`ProjectManager`, `RecipeManager`, `ResultsManager`) auf die
Persistenz zu. Sie blockieren nicht modal – der Aufrufer erhält über
Callbacks bzw. direkte Rückgaben Rückmeldung.
"""

import tkinter as tk
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
