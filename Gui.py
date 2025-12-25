import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
from tkinter import messagebox
import os
import cProfile
import threading

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Spacer, Paragraph
from markdown_formatter import configure_markdown_tags, markdown_to_tkinter_text


from analysis import (extract_transkript, extract_text_from_website,
                      text_extraction_youtube_website, real_ai_analyse_fortext,
                      real_ai_analyse_forpdf)
from config import check_api_key_exists, save_api_key, get_api_key


class Gui():
    def __init__(self, window):
        self.window = window
        self.window.title("KI Analysetool")
        self.window.geometry("800x1000")
        self.window.minsize(700, 900)

        if not check_api_key_exists():
            self.show_api_key_dialog()

        self.notes = []
        self.analyseResult = ""
        self.analysePath = ""

        self.setupGui()

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
        entry = ttk.Entry(dialog, textvariable=api_key_var, width=50)
        entry.pack(padx=20, pady=5)

        # Bestätigungsbutton
        def save_and_close():
            key = api_key_var.get().strip()
            if key:
                save_api_key(key)
                dialog.destroy()
            else:
                messagebox.showerror("Fehler", "Bitte gib einen API-Key ein.")

        ttk.Button(dialog, text="Speichern",
                   command=save_and_close).pack(pady=10)

        # Sicherstellen, dass der Dialog geschlossen wird, bevor die App weiterläuft
        self.window.wait_window(dialog)

    def setupGui(self):
        # Main Container
        self.main_frame = ttk.Frame(self.window, padding=15)
        self.main_frame.pack(fill="both", expand=True)

        # Header
        self.header_label = ttk.Label(
            self.main_frame, text="KI-Analysetool", style="Header.TLabel")
        self.header_label.pack(pady=(0, 15))

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Bereit")
        self.status_bar = ttk.Label(
            self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, pady=(15, 0))

        self.setupSourcesFrame()
        self.analysis_Frame()

    def setupSourcesFrame(self):
        # Input-Source Frame
        self.sources_frame = ttk.LabelFrame(
            self.main_frame, text="Inhaltsquellen", padding=15)
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

        pdf_upload_button = ttk.Button(
            pdf_tab, text="PDF hochladen", command=self.pdf_file_choose)
        pdf_upload_button.pack(pady=5)

        self.pdf_path_var = tk.StringVar()
        self.pdf_path_label = ttk.Label(
            pdf_tab, textvariable=self.pdf_path_var, wraplength=350)
        self.pdf_path_label.pack(pady=5)

    # ----------------------------------------------------------------------------------------------------------------------------
    def analysis_Frame(self):
        # Analysis and results frame
        self.analysis_frame = ttk.LabelFrame(
            self.main_frame, text="Analyse & Ergebnisse", padding=10)
        self.analysis_frame.pack(fill=tk.BOTH, expand=True)
        self.analysis_frame.rowconfigure(5, weight=1)
        self.analysis_frame.columnconfigure(0, weight=1)

        self.promptFrame()
        self.outPutArea()

    def promptFrame(self):
        # Question input
        ttk.Label(self.analysis_frame, text="Erstelle einen Prompt zu dem Inhalt:").grid(
            row=0, column=0, sticky=tk.W)

        self.question_text = scrolledtext.ScrolledText(
            self.analysis_frame, height=4)
        self.question_text.grid(
            row=1, column=0, sticky=tk.W + tk.E, pady=(0, 15))

        self.combobox = ttk.Combobox(self.analysis_frame,
                                     values=["Prompt senden", "Zusammenfassung", "Keyword-Extraktion", "Sentiment Analyse",
                                             "Themen-Erkennung"])
        self.combobox.current(0)
        self.combobox.grid(row=2, column=0, sticky=tk.W + tk.E, pady=(0, 15))

        self.question_button = ttk.Button(
            self.analysis_frame, text="Frage senden", command=self.send_question)
        self.question_button.grid(
            row=3, column=0, sticky=tk.W + tk.E, pady=(0, 15))

        # Separator
        separator = ttk.Separator(self.analysis_frame, orient=tk.HORIZONTAL)
        separator.grid(row=4, column=0, sticky=tk.W + tk.E, pady=10)

    def outPutArea(self):
        # Output area
        ttk.Label(self.analysis_frame, text="Ergebnisse:").grid(
            row=5, column=0, sticky=tk.W)

        self.output_text = scrolledtext.ScrolledText(
            self.analysis_frame, height=10)
        self.output_text.grid(row=6, column=0, sticky=tk.W +
                              tk.E + tk.N + tk.S, pady=(0, 10))
        self.output_text.insert(tk.END, "Das Ergebnis wird hier angezeigt...")
        self.output_text.config(state=tk.DISABLED)

        configure_markdown_tags(self.output_text)

        # Note management buttons
        buttons_frame = ttk.Frame(self.analysis_frame)
        buttons_frame.grid(row=7, column=0, sticky=tk.W + tk.E, pady=(0, 10))

        export_button = ttk.Button(
            buttons_frame, text="Notiz exportieren", command=self.export_notes_as_pdf)
        export_button.grid(row=0, column=0)

        clipboard_button = ttk.Button(
            buttons_frame, text="In Zwischenablage", command=self.copy_notes_as_text)
        clipboard_button.grid(row=0, column=2)

    # Funktionen

    def profile_function(self):
        cProfile.run('self.send_question()', os.path.join(
            os.getcwd(), 'profile.txt'), sortby='time')

    def pdf_file_choose(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("PDF-Dateien", "*.pdf")])
        if file_path:
            self.pdf_entry.delete(0, tk.END)
            self.pdf_entry.insert(0, file_path)
            self.pdf_path_var.set(file_path)  # Update the path label

    def start_analyse(self):

        # Get path from the currently selected tab
        tab_id = self.input_tabs.select()
        tab_index = self.input_tabs.index(tab_id)

        if tab_index == 0:  # Website tab
            self.analysePath = self.website_url.get()
            self.analyseResult = text_extraction_youtube_website(
                self.analysePath)
            return self.analyseResult, self.analysePath
        elif tab_index == 1:  # YouTube tab
            self.analysePath = self.youtube_url.get()
            self.analyseResult = text_extraction_youtube_website(
                self.analysePath)
            return self.analyseResult, self.analysePath
        elif tab_index == 2:  # PDF tab
            self.analysePath = self.pdf_url.get()
            self.analyseResult = self.pdf_path_var.get()
            return self.analyseResult

    def get_prompt(self, content):

        value = self.combobox.get()
        if value == "Zusammenfassung":
            question = "Fasse den Text zusammen:{text}"
            return question
        elif value == "Keyword-Extraktion":
            question = "Extrahiere Schlüsselwörter aus diesem Text: {text}".format(
                text=content)
            return question
        elif value == "Sentiment Analyse":
            question = "Analysiere die Stimmung und den Tonfall dieses Textes: {text}".format(
                text=content)
            return question
        elif value == "Themen-Erkennung":
            question = "Erkenne die Hauptthemen des nachfolgendes Textes: {text}".format(
                text=content)
            return question
        else:
            question_prompt = self.question_text.get(1.0, tk.END).strip()
            # Format the custom prompt with the content
            prompt_template = f"{question_prompt} {{text}}".format(
                text=content)
            return prompt_template

    def send_question(self):
        # UI Input Gathering and Validation
        tab_id = self.input_tabs.select()
        tab_index = self.input_tabs.index(tab_id)

        input_path = ""
        is_pdf_upload = False

        if tab_index == 0:  # Website
            input_path = self.website_url.get().strip()
        elif tab_index == 1:  # YouTube
            input_path = self.youtube_url.get().strip()
        elif tab_index == 2:  # PDF
            # Check URL first, then file path
            url_val = self.pdf_url.get().strip()
            path_val = self.pdf_path_var.get().strip()
            if url_val:
                input_path = url_val
            elif path_val:
                input_path = path_val
                is_pdf_upload = True

        if not input_path:
            messagebox.showwarning(
                "Fehlende Eingabe", "Bitte gib eine URL ein oder wähle eine Datei aus.")
            return

        # Prepare for background work
        self.question_button.config(state=tk.DISABLED, text="Verarbeite...")
        self.status_var.set("Analyse läuft...")
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, "Analyse läuft, bitte warten...\n")
        self.output_text.config(state=tk.DISABLED)

        # Get prompt params before threading
        prompt_value = self.combobox.get()
        custom_prompt_text = self.question_text.get(1.0, tk.END).strip()

        # Run analysis in a separate thread
        thread = threading.Thread(
            target=self.run_analysis_thread,
            args=(input_path, tab_index, is_pdf_upload,
                  prompt_value, custom_prompt_text)
        )
        thread.daemon = True
        thread.start()

    def run_analysis_thread(self, input_path, tab_index, is_pdf_upload, prompt_value, custom_prompt_text):
        try:
            content = ""
            self.analysePath = input_path  # Maintain compatibility

            # Step 1: Extraction
            if tab_index in [0, 1]:  # Website or YouTube
                content = text_extraction_youtube_website(input_path)
                self.analyseResult = content
            elif tab_index == 2:  # PDF
                if is_pdf_upload:
                    content = input_path  # It's the file path
                else:
                    content = input_path
                self.analyseResult = content

            # Step 2: Prompt Generation
            prompt = ""
            if prompt_value == "Zusammenfassung":
                prompt = "Fasse den Text zusammen:{text}"
            elif prompt_value == "Keyword-Extraktion":
                prompt = "Extrahiere Schlüsselwörter aus diesem Text: {text}".format(
                    text=content)
            elif prompt_value == "Sentiment Analyse":
                prompt = "Analysiere die Stimmung und den Tonfall dieses Textes: {text}".format(
                    text=content)
            elif prompt_value == "Themen-Erkennung":
                prompt = "Erkenne die Hauptthemen des nachfolgendes Textes: {text}".format(
                    text=content)
            else:
                prompt = f"{custom_prompt_text} {{text}}".format(text=content)

            # Step 3: AI Analysis
            result_analysis = ""
            if "http" in input_path.lower() or "youtu" in input_path.lower():
                try:
                    combined_text = prompt.format(text=content)
                except Exception:
                    combined_text = prompt
                result_analysis = real_ai_analyse_fortext(combined_text)
            else:
                result_analysis = real_ai_analyse_forpdf(content, prompt)

            # Schedule UI Update
            self.window.after(0, self.analysis_complete, result_analysis)

        except Exception as e:
            error_msg = f"Ein Fehler ist aufgetreten:\n{str(e)}"
            self.window.after(0, self.analysis_complete, error_msg)

    def analysis_complete(self, result_text):
        try:
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete(1.0, tk.END)
            markdown_to_tkinter_text(result_text, self.output_text)
            self.output_text.config(state=tk.DISABLED)
            self.status_var.set("Analyse abgeschlossen.")
        except Exception as e:
            messagebox.showerror(
                "Fehler", f"Ein Fehler ist aufgetreten: {str(e)}")
            self.status_var.set("Fehler bei der Analyse.")
        finally:
            self.window.config(cursor="")
            self.question_button.config(state=tk.NORMAL)
            self.question_button.config(text="Frage senden")

    def save_note(self):
        self.notes
        note = self.output_text.get(1.0, tk.END).strip()

        if note:
            self.notes = [note]
            self.status_var.set("Notiz gespeichert")
        else:
            self.status_var.set("Kein Text zum Speichern gefunden")

    def export_notes_as_pdf(self):
        self.save_note()
        file_path = filedialog.asksaveasfilename(
            filetypes=[("PDF-Dateien", "*.pdf")])

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
        tk.messagebox.showinfo("Export erfolgreich",
                               "Notizen wurden als PDF exportiert!")

    def copy_notes_as_text(self):
        self.save_note()
        self.window.clipboard_clear()
        self.window.clipboard_append("\n\n".join(self.notes))
        self.window.update()
        tk.messagebox.showinfo("Export erfolgreich",
                               "Notizen wurden in die Zwischenablage kopiert!")
