import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
from tkinter import messagebox
import os
import threading
import cProfile

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Spacer,Paragraph
from markdown_formatter import configure_markdown_tags, markdown_to_tkinter_text


from analysis import (extract_transkript, extract_text_from_website,
                     text_extraction_youtube_website, real_ai_analyse_fortext,
                     real_ai_analyse_forpdf, AVAILABLE_MODELS, set_model, get_model,
                     get_usage_stats, reset_usage_stats, estimate_tokens,
                     validate_content_length)
from config import check_api_key_exists, save_api_key, get_api_key


class Gui():
    def __init__(self,window):
        self.window = window
        self.window.title("KI Analysetool")
        self.window.geometry("800x1000")
        self.window.minsize(700, 900)


        if not check_api_key_exists():
            self.show_api_key_dialog()

        self.notes = []
        self.analyseResult = ""
        self.analysePath = ""
        self.processing_thread = None
        self.dark_mode = False
        self.font_size = 12

        self.setupGui()
        self._setup_shortcuts()
        self._setup_menu()

    def show_api_key_dialog(self):
        """Zeigt einen Dialog zur Eingabe des API-Keys an."""
        dialog = tk.Toplevel(self.window)
        dialog.title("API-Key Eingabe")
        dialog.geometry("400x150")
        dialog.resizable(False, False)

        # Dialog modal machen (Hauptfenster blockieren)
        dialog.transient(self.window)
        dialog.grab_set()

        # Erklärungstext
        ttk.Label(
            dialog,
            text="Bitte gib deinen OpenAI API-Key ein.\nDieser wird für die KI-Funktionen benötigt.",
            wraplength=380
        ).pack(pady=(20, 10))

        # Eingabefeld
        api_key_var = tk.StringVar()
        entry = ttk.Entry(dialog, textvariable=api_key_var, width=50, show="*")
        entry.pack(padx=20, pady=5)

        # Bestätigungsbutton
        def save_and_close():
            key = api_key_var.get().strip()
            if key:
                save_api_key(key)
                dialog.destroy()
            else:
                messagebox.showerror("Fehler", "Bitte gib einen API-Key ein.")

        ttk.Button(dialog, text="Speichern", command=save_and_close).pack(pady=10)

        # Sicherstellen, dass der Dialog geschlossen wird, bevor die App weiterläuft
        self.window.wait_window(dialog)

    def setupGui(self):
        # Main Container
        self.main_frame = ttk.Frame(self.window, padding=15)
        self.main_frame.pack(fill="both", expand=True)

        # Header
        self.header_label = ttk.Label(self.main_frame, text="KI-Analysetool", style="Header.TLabel")
        self.header_label.pack(pady=(0, 15))

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Bereit")
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, pady=(15, 0))

        self.setupSourcesFrame()
        self.analysis_Frame()


    def setupSourcesFrame(self):
        # Input-Source Frame
        self.sources_frame = ttk.LabelFrame(self.main_frame, text="Inhaltsquellen", padding=15)
        self.sources_frame.pack(fill=tk.X, pady=(0, 15))
        self.sources_frame.columnconfigure(0, weight=1)

        # Tabs for different input types
        self.input_tabs = ttk.Notebook(self.sources_frame)
        self.input_tabs.grid(row=0, column=0, sticky=tk.W + tk.E)

        self.setupWebsiteTab()
        self.setupYoutubeTab()
        self.setupPdfTab()
    def setupWebsiteTab(self):
        # Website tab
        website_tab = ttk.Frame(self.input_tabs, padding=10)
        self.input_tabs.add(website_tab, text="Webseite")

        ttk.Label(website_tab, text="Webseiten-URL:").pack(anchor=tk.W, pady=(0, 5))

        website_frame = ttk.Frame(website_tab)
        website_frame.pack(fill=tk.X)

        self.website_url = tk.StringVar()
        website_entry = ttk.Entry(website_frame, textvariable=self.website_url)
        website_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
    def setupYoutubeTab(self):
        # YouTube tab
        youtube_tab = ttk.Frame(self.input_tabs, padding=10)
        self.input_tabs.add(youtube_tab, text="YouTube")

        ttk.Label(youtube_tab, text="YouTube-Link:").pack(anchor=tk.W, pady=(0, 5))

        youtube_frame = ttk.Frame(youtube_tab)
        youtube_frame.pack(fill=tk.X)

        self.youtube_url = tk.StringVar()
        youtube_entry = ttk.Entry(youtube_frame, textvariable=self.youtube_url)
        youtube_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
    def setupPdfTab(self):
        # PDF tab
        pdf_tab = ttk.Frame(self.input_tabs, padding=10)
        self.input_tabs.add(pdf_tab, text="PDF")

        ttk.Label(pdf_tab, text="PDF-URL:").pack(anchor=tk.W, pady=(0, 5))

        pdf_url_frame = ttk.Frame(pdf_tab)
        pdf_url_frame.pack(fill=tk.X, pady=(0, 10))

        self.pdf_url = tk.StringVar()
        self.pdf_entry = ttk.Entry(pdf_url_frame, textvariable=self.pdf_url)
        self.pdf_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        ttk.Label(pdf_tab, text="oder").pack(pady=5)

        pdf_upload_button = ttk.Button(pdf_tab, text="PDF hochladen", command=self.pdf_file_choose)
        pdf_upload_button.pack(pady=5)

        self.pdf_path_var = tk.StringVar()
        self.pdf_path_label = ttk.Label(pdf_tab, textvariable=self.pdf_path_var, wraplength=350)
        self.pdf_path_label.pack(pady=5)

    # ----------------------------------------------------------------------------------------------------------------------------
    def analysis_Frame(self):
        # Analysis and results frame
        self.analysis_frame = ttk.LabelFrame(self.main_frame, text="Analyse & Ergebnisse", padding=10)
        self.analysis_frame.pack(fill=tk.BOTH, expand=True)
        self.analysis_frame.rowconfigure(5, weight=1)
        self.analysis_frame.columnconfigure(0, weight=1)

        self.promptFrame()
        self.outPutArea()
    def promptFrame(self):
        # Question input
        ttk.Label(self.analysis_frame, text="Erstelle einen Prompt zu dem Inhalt:").grid(row=0, column=0, sticky=tk.W)

        self.question_text = scrolledtext.ScrolledText(self.analysis_frame, height=4)
        self.question_text.grid(row=1, column=0, sticky=tk.W + tk.E, pady=(0, 15))

        self.combobox = ttk.Combobox(self.analysis_frame,
                                values=["Prompt senden", "Zusammenfassung", "Keyword-Extraktion", "Sentiment Analyse",
                                        "Themen-Erkennung"])
        self.combobox.current(1)
        self.combobox.grid(row=2, column=0, sticky=tk.W + tk.E, pady=(0, 15))

        question_button = ttk.Button(self.analysis_frame, text="Frage senden", command=self.send_question)
        question_button.grid(row=3, column=0, sticky=tk.W + tk.E, pady=(0, 15))

        # Separator
        separator = ttk.Separator(self.analysis_frame, orient=tk.HORIZONTAL)
        separator.grid(row=4, column=0, sticky=tk.W + tk.E, pady=10)
    def outPutArea(self):
        # Output area
        ttk.Label(self.analysis_frame, text="Ergebnisse:").grid(row=5, column=0, sticky=tk.W)

        self.output_text = scrolledtext.ScrolledText(self.analysis_frame, height=10)
        self.output_text.grid(row=6, column=0, sticky=tk.W + tk.E + tk.N + tk.S, pady=(0, 10))
        self.output_text.config(state=tk.DISABLED)

        configure_markdown_tags(self.output_text)
        self._setup_output_placeholder()

        # Note management buttons
        buttons_frame = ttk.Frame(self.analysis_frame)
        buttons_frame.grid(row=7, column=0, sticky=tk.W + tk.E, pady=(0, 10))

        export_button = ttk.Button(buttons_frame, text="Notiz exportieren", command=self.export_notes_as_pdf)
        export_button.grid(row=0, column=0)

        clipboard_button = ttk.Button(buttons_frame, text="In Zwischenablage", command=self.copy_notes_as_text)
        clipboard_button.grid(row=0, column=2)

    # Funktionen

    def profile_function(self):
        profiler = cProfile.Profile()
        profiler.enable()
        self.send_question()
        profiler.disable()
        profile_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'profile.txt')
        profiler.dump_stats(profile_path)
        messagebox.showinfo("Profiling", f"Profil gespeichert unter: {profile_path}")

    def pdf_file_choose(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF-Dateien", "*.pdf")])
        if file_path:
            self.pdf_entry.delete(0, tk.END)
            self.pdf_entry.insert(0, file_path)
            self.pdf_path_var.set(file_path)  # Update the path label

    def start_analyse(self):
        """Setzt nur den Pfad/URL basierend auf dem aktiven Tab. Content-Extraktion erfolgt im Background-Thread."""
        tab_id = self.input_tabs.select()
        tab_index = self.input_tabs.index(tab_id)

        if tab_index == 0:  # Website tab
            self.analysePath = self.website_url.get()
            self.analyseResult = None
            return self.analysePath, tab_index
        elif tab_index == 1:  # YouTube tab
            self.analysePath = self.youtube_url.get()
            self.analyseResult = None
            return self.analysePath, tab_index
        elif tab_index == 2:  # PDF tab
            pdf_url = self.pdf_url.get().strip()
            pdf_local = self.pdf_path_var.get().strip()
            if pdf_local:
                self.analysePath = pdf_local
            elif pdf_url:
                self.analysePath = pdf_url
            self.analyseResult = self.analysePath
            return self.analysePath, tab_index

    def get_prompt(self, content=None):
        value = self.combobox.get()
        if value == "Zusammenfassung":
            return "Fasse den Text zusammen: {text}"
        elif value == "Keyword-Extraktion":
            return "Extrahiere Schlüsselwörter aus diesem Text: {text}"
        elif value == "Sentiment Analyse":
            return "Analysiere die Stimmung und den Tonfall dieses Textes: {text}"
        elif value == "Themen-Erkennung":
            return "Erkenne die Hauptthemen des nachfolgenden Textes: {text}"
        else:
            question_prompt = self.question_text.get(1.0, tk.END).strip()
            if not question_prompt:
                return "Analysiere den folgenden Text: {text}"
            return f"{question_prompt} {{text}}"

    def _setup_menu(self):
        self.menubar = tk.Menu(self.window)
        self.window.config(menu=self.menubar)

        settings_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Einstellungen", menu=settings_menu)

        self.model_var = tk.StringVar(value=get_model())
        model_menu = tk.Menu(settings_menu, tearoff=0)
        settings_menu.add_cascade(label="Modell", menu=model_menu)
        for model_key, info in AVAILABLE_MODELS.items():
            model_menu.add_radiobutton(
                label=info["name"],
                value=model_key,
                variable=self.model_var,
                command=lambda mk=model_key: self._change_model(mk)
            )

        settings_menu.add_separator()
        settings_menu.add_command(label="API-Key ändern", command=self.show_api_key_dialog)
        settings_menu.add_command(label="Verbrauchsstatistik", command=self._show_usage_stats)
        settings_menu.add_command(label="Verbrauch zurücksetzen", command=self._reset_usage)

        view_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Ansicht", menu=view_menu)
        view_menu.add_command(label="Dark Mode umschalten", command=self._toggle_dark_mode)
        view_menu.add_separator()
        self.font_var = tk.IntVar(value=self.font_size)
        font_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Schriftgröße", menu=font_menu)
        for size in [10, 12, 14, 16, 18]:
            font_menu.add_radiobutton(
                label=f"{size} pt",
                value=size,
                variable=self.font_var,
                command=lambda s=size: self._change_font_size(s)
            )

        tools_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Werkzeuge", menu=tools_menu)
        tools_menu.add_command(label="Notizen verwalten", command=self._show_notes_manager)
        tools_menu.add_command(label="Profiling ausführen", command=self.profile_function)

    def _change_model(self, model_key):
        set_model(model_key)
        self.status_var.set(f"Modell: {AVAILABLE_MODELS[model_key]['name']}")

    def _show_usage_stats(self):
        stats = get_usage_stats()
        msg = (f"Verbrauchsstatistik\n\n"
               f"Modell: {stats['model']}\n"
               f"Tokens gesamt: {stats['total_tokens']}\n"
               f"Geschätzte Kosten: ${stats['total_cost']:.4f}")
        messagebox.showinfo("Verbrauchsstatistik", msg)

    def _reset_usage(self):
        reset_usage_stats()
        self.status_var.set("Verbrauchsstatistik zurückgesetzt")

    def _toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.window.tk.call("tk_setPalette", background="#2b2b2b", foreground="#ffffff",
                                activeBackground="#3b3b3b", activeForeground="#ffffff",
                                disabledForeground="#888888")
            bg, fg, ib = "#1e1e1e", "#d4d4d4", "#ffffff"
        else:
            self.window.tk.call("tk_setPalette", background="#f0f0f0", foreground="#000000",
                                activeBackground="#e0e0e0", activeForeground="#000000",
                                disabledForeground="#a0a0a0")
            bg, fg, ib = "#ffffff", "#000000", "#000000"

        self.output_text.config(bg=bg, fg=fg, insertbackground=ib)
        self.question_text.config(bg=bg, fg=fg, insertbackground=ib)

        if hasattr(self, 'results_display') and hasattr(self.results_display, 'text_widget'):
            self.results_display.text_widget.config(bg=bg, fg=fg, insertbackground=ib)

        self.status_var.set(f"Dark Mode: {'AN' if self.dark_mode else 'AUS'}")

    def _change_font_size(self, size):
        self.font_size = size
        font_tuple = ("Helvetica", size)
        self.output_text.config(font=font_tuple)
        self.question_text.config(font=font_tuple)
        configure_markdown_tags(self.output_text, font_size=size)
        self.status_var.set(f"Schriftgröße: {size} pt")

    def _show_notes_manager(self):
        dialog = tk.Toplevel(self.window)
        dialog.title("Notizen verwalten")
        dialog.geometry("600x400")
        dialog.transient(self.window)
        dialog.grab_set()

        list_frame = ttk.Frame(dialog, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(list_frame, text=f"{len(self.notes)} Notiz(en) gespeichert:", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(0, 10))

        notes_listbox = tk.Listbox(list_frame, height=15)
        notes_listbox.pack(fill=tk.BOTH, expand=True)

        for i, note in enumerate(self.notes):
            preview = note[:80].replace("\n", " ") + ("..." if len(note) > 80 else "")
            notes_listbox.insert(tk.END, f"{i+1}. {preview}")

        btn_frame = ttk.Frame(dialog, padding=10)
        btn_frame.pack(fill=tk.X)

        def delete_selected():
            sel = notes_listbox.curselection()
            if sel:
                idx = sel[0]
                self.notes.pop(idx)
                notes_listbox.delete(idx)
                for i in range(idx, len(self.notes)):
                    note = self.notes[i]
                    preview = note[:80].replace("\n", " ") + ("..." if len(note) > 80 else "")
                    notes_listbox.delete(i)
                    notes_listbox.insert(i, f"{i+1}. {preview}")

        def view_selected():
            sel = notes_listbox.curselection()
            if sel:
                idx = sel[0]
                view_win = tk.Toplevel(dialog)
                view_win.title(f"Notiz {idx+1}")
                view_win.geometry("500x400")
                text_widget = scrolledtext.ScrolledText(view_win, wrap=tk.WORD)
                text_widget.pack(fill=tk.BOTH, expand=True)
                text_widget.insert(tk.END, self.notes[idx])
                text_widget.config(state=tk.DISABLED)

        def clear_all():
            if messagebox.askyesno("Bestätigen", "Alle Notizen wirklich löschen?"):
                self.notes.clear()
                notes_listbox.delete(0, tk.END)

        ttk.Button(btn_frame, text="Anzeigen", command=view_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Löschen", command=delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Alle löschen", command=clear_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Schließen", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

    def _setup_shortcuts(self):
        self.window.bind("<Control-Return>", lambda e: self.send_question())
        self.window.bind("<Control-s>", lambda e: self.export_notes_as_pdf())
        self.window.bind("<Control-Shift-c>", lambda e: self.copy_notes_as_text())

    def _setup_output_placeholder(self):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, "Das Ergebnis wird hier angezeigt...", "placeholder")
        self.output_text.tag_config("placeholder", foreground="gray")
        self.output_text.config(state=tk.DISABLED)

    def _clear_output_placeholder(self):
        current = self.output_text.get(1.0, tk.END).strip()
        if current == "Das Ergebnis wird hier angezeigt...":
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete(1.0, tk.END)
            self.output_text.config(state=tk.DISABLED)

    def _validate_input(self):
        tab_id = self.input_tabs.select()
        tab_index = self.input_tabs.index(tab_id)

        if tab_index == 0:
            url = self.website_url.get().strip()
            if not url:
                messagebox.showwarning("Eingabe fehlt", "Bitte gib eine Webseiten-URL ein.")
                return False
        elif tab_index == 1:
            url = self.youtube_url.get().strip()
            if not url:
                messagebox.showwarning("Eingabe fehlt", "Bitte gib einen YouTube-Link ein.")
                return False
        elif tab_index == 2:
            pdf_url = self.pdf_url.get().strip()
            pdf_local = self.pdf_path_var.get().strip()
            if not pdf_url and not pdf_local:
                messagebox.showwarning("Eingabe fehlt", "Bitte gib eine PDF-URL ein oder lade eine PDF hoch.")
                return False
        return True

    def send_question(self):
        if self.processing_thread and self.processing_thread.is_alive():
            messagebox.showinfo("Analyse läuft", "Eine Analyse wird bereits durchgeführt. Bitte warte einen Moment.")
            return

        if not self._validate_input():
            return

        source_path, tab_index = self.start_analyse()
        prompt_template = self.get_prompt()

        self.status_var.set("Analyse wird durchgeführt...")
        self._clear_output_placeholder()

        self.processing_thread = threading.Thread(
            target=self._run_analysis,
            args=(source_path, prompt_template, tab_index),
            daemon=True
        )
        self.processing_thread.start()

    def _run_analysis(self, source_path, prompt_template, tab_index):
        try:
            if tab_index == 2:
                prompt = prompt_template.replace("{text}", "")
                result_analysis = real_ai_analyse_forpdf(source_path, prompt)
            else:
                content = text_extraction_youtube_website(source_path)
                combined_text = prompt_template.replace("{text}", content)
                result_analysis = real_ai_analyse_fortext(combined_text)

            self.window.after(0, lambda: self._display_result(result_analysis))
        except Exception as e:
            error_msg = f"Ein Fehler ist aufgetreten: {str(e)}"
            self.window.after(0, lambda: self._display_error(error_msg))

    def _display_result(self, result_analysis):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        markdown_to_tkinter_text(result_analysis, self.output_text)
        self.output_text.config(state=tk.DISABLED)
        self.status_var.set("Analyse abgeschlossen")

    def _display_error(self, error_msg):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, error_msg)
        self.output_text.config(state=tk.DISABLED)
        self.status_var.set("Fehler bei der Analyse")
        messagebox.showerror("Fehler bei der Analyse", error_msg)

    def save_note(self):
        note = self.output_text.get(1.0, tk.END).strip()

        if note and note != "Das Ergebnis wird hier angezeigt...":
            self.notes.append(note)
            self.status_var.set("Notiz gespeichert")
        elif note == "Das Ergebnis wird hier angezeigt...":
            self.status_var.set("Kein Ergebnis zum Speichern vorhanden")
        else:
            self.status_var.set("Kein Text zum Speichern gefunden")


    def export_notes_as_pdf(self):
        self.save_note()
        file_path = filedialog.asksaveasfilename(filetypes=[("PDF-Dateien", "*.pdf")])

        if not file_path:
            return
        pdf = SimpleDocTemplate(file_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        title = Paragraph("Notizen", styles["Heading1"])
        story.append(title)
        story.append(Spacer(1, 0.25 * inch))

        for i, note in enumerate(self.notes, 1):
            note_text = f"{i}. {note}"
            wrapped_text = Paragraph(note_text, styles["Normal"])
            story.append(wrapped_text)
            story.append(Spacer(1, 0.1 * inch))

        pdf.build(story)
        # Inform user
        messagebox.showinfo("Export erfolgreich", "Notizen wurden als PDF exportiert!")

    def copy_notes_as_text(self):
        self.save_note()
        self.window.clipboard_clear()
        self.window.clipboard_append("\n\n".join(self.notes))
        self.window.update()
        messagebox.showinfo("Export erfolgreich", "Notizen wurden in die Zwischenablage kopiert!")
