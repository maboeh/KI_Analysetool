import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
from tkinter import messagebox
import os
import cProfile

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Spacer,Paragraph
from markdown_formatter import configure_markdown_tags, markdown_to_tkinter_text
from help_tooltip import add_help_indicator


from analysis import (extract_transkript, extract_text_from_website,
                     text_extraction_youtube_website, real_ai_analyse_fortext,
                     real_ai_analyse_forpdf)
from config import check_api_key_exists, save_api_key, get_api_key


class Gui():
    def __init__(self,window):
        self.window = window
        self.window.title("KI Analysetool")
        self.window.geometry("1800x1000")
        self.window.minsize(1500, 850)


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

        ttk.Button(dialog, text="Speichern", command=save_and_close).pack(pady=10)

        # Sicherstellen, dass der Dialog geschlossen wird, bevor die App weiterläuft
        self.window.wait_window(dialog)

    def setupGui(self):
        # Main Container
        self.main_frame = ttk.Frame(self.window, padding=15)
        self.main_frame.pack(fill="both", expand=True)

        # Horizontal container for sources (left) and analysis (right)
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        self.setupSourcesFrame()
        self.analysis_Frame()

        # Status bar (bottom, full width)
        self.status_var = tk.StringVar()
        self.status_var.set("Bereit")
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, pady=(15, 0))


    def setupSourcesFrame(self):
        # Input-Source Frame (left side)
        self.sources_frame = ttk.LabelFrame(self.content_frame, text="Inhaltsquellen", padding=15)
        self.sources_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
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

        url_label_frame = ttk.Frame(website_tab)
        url_label_frame.pack(anchor=tk.W, pady=(0, 5))
        ttk.Label(url_label_frame, text="Webseiten-URL:").pack(side=tk.LEFT)
        add_help_indicator(url_label_frame,
                          "Geben Sie hier die URL der Webseite ein, die analysiert werden soll. "
                          "Der Text der Seite wird automatisch extrahiert.")

        website_frame = ttk.Frame(website_tab)
        website_frame.pack(fill=tk.X)

        self.website_url = tk.StringVar()
        website_entry = ttk.Entry(website_frame, textvariable=self.website_url)
        website_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
    def setupYoutubeTab(self):
        # YouTube tab
        youtube_tab = ttk.Frame(self.input_tabs, padding=10)
        self.input_tabs.add(youtube_tab, text="YouTube")

        yt_label_frame = ttk.Frame(youtube_tab)
        yt_label_frame.pack(anchor=tk.W, pady=(0, 5))
        ttk.Label(yt_label_frame, text="YouTube-Link:").pack(side=tk.LEFT)
        add_help_indicator(yt_label_frame,
                          "Fügen Sie hier den YouTube-Video-Link ein. "
                          "Das Transkript des Videos wird automatisch extrahiert und analysiert.")

        youtube_frame = ttk.Frame(youtube_tab)
        youtube_frame.pack(fill=tk.X)

        self.youtube_url = tk.StringVar()
        youtube_entry = ttk.Entry(youtube_frame, textvariable=self.youtube_url)
        youtube_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
    def setupPdfTab(self):
        # PDF tab
        pdf_tab = ttk.Frame(self.input_tabs, padding=10)
        self.input_tabs.add(pdf_tab, text="PDF")

        pdf_label_frame = ttk.Frame(pdf_tab)
        pdf_label_frame.pack(anchor=tk.W, pady=(0, 5))
        ttk.Label(pdf_label_frame, text="PDF-URL:").pack(side=tk.LEFT)
        add_help_indicator(pdf_label_frame,
                          "Geben Sie hier eine URL zu einer PDF-Datei ein oder laden Sie "
                          "alternativ eine lokale PDF-Datei über den Button hoch.")

        pdf_url_frame = ttk.Frame(pdf_tab)
        pdf_url_frame.pack(fill=tk.X, pady=(0, 10))

        self.pdf_url = tk.StringVar()
        self.pdf_entry = ttk.Entry(pdf_url_frame, textvariable=self.pdf_url)
        self.pdf_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        ttk.Label(pdf_tab, text="oder").pack(pady=5)

        pdf_upload_frame = ttk.Frame(pdf_tab)
        pdf_upload_frame.pack(pady=5)
        pdf_upload_button = ttk.Button(pdf_upload_frame, text="PDF hochladen", command=self.pdf_file_choose)
        pdf_upload_button.pack(side=tk.LEFT)
        add_help_indicator(pdf_upload_frame,
                          "Öffnet einen Datei-Dialog zum Auswählen einer lokalen PDF-Datei. "
                          "Der Text wird extrahiert und für die Analyse vorbereitet.")

        self.pdf_path_var = tk.StringVar()
        self.pdf_path_label = ttk.Label(pdf_tab, textvariable=self.pdf_path_var, wraplength=350)
        self.pdf_path_label.pack(pady=5)

    # ----------------------------------------------------------------------------------------------------------------------------
    def analysis_Frame(self):
        # Analysis and results frame (right side)
        self.analysis_frame = ttk.LabelFrame(self.content_frame, text="Analyse & Ergebnisse", padding=10)
        self.analysis_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.analysis_frame.rowconfigure(5, weight=0)
        self.analysis_frame.rowconfigure(6, weight=1)
        self.analysis_frame.columnconfigure(0, weight=1)

        self.promptFrame()
        self.outPutArea()
    def promptFrame(self):
        # Question input
        prompt_label_frame = ttk.Frame(self.analysis_frame)
        prompt_label_frame.grid(row=0, column=0, sticky=tk.W)
        ttk.Label(prompt_label_frame, text="Erstelle einen Prompt zu dem Inhalt:").pack(side=tk.LEFT)
        add_help_indicator(prompt_label_frame,
                          "Hier können Sie einen eigenen Prompt eingeben. Verwenden Sie {text} als Platzhalter "
                          "für den extrahierten Inhalt. Alternativ können Sie eine vordefinierte Analyse aus dem Dropdown wählen.")

        self.question_text = scrolledtext.ScrolledText(self.analysis_frame, height=4)
        self.question_text.grid(row=1, column=0, sticky=tk.W + tk.E, pady=(0, 15))

        combo_frame = ttk.Frame(self.analysis_frame)
        combo_frame.grid(row=2, column=0, sticky=tk.W + tk.E, pady=(0, 15))
        
        self.combobox = ttk.Combobox(combo_frame,
                                values=["Prompt senden", "Zusammenfassung", "Keyword-Extraktion", "Sentiment Analyse",
                                        "Themen-Erkennung"])
        self.combobox.current(0)
        self.combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        add_help_indicator(combo_frame,
                          "Wählen Sie eine vordefinierte Analysemethode: "
                          "Zusammenfassung, Keyword-Extraktion, Sentiment-Analyse oder Themen-Erkennung. "
                          "Bei 'Prompt senden' wird Ihr eigener Prompt verwendet.")

        question_btn_frame = ttk.Frame(self.analysis_frame)
        question_btn_frame.grid(row=3, column=0, sticky=tk.W + tk.E, pady=(0, 15))
        question_button = ttk.Button(question_btn_frame, text="Frage senden", command=self.send_question)
        question_button.pack(side=tk.LEFT)
        add_help_indicator(question_btn_frame,
                          "Sendet den Prompt zusammen mit dem extrahierten Inhalt an die KI und zeigt das Ergebnis an.")

        # Separator
        separator = ttk.Separator(self.analysis_frame, orient=tk.HORIZONTAL)
        separator.grid(row=4, column=0, sticky=tk.W + tk.E, pady=10)
    def outPutArea(self):
        # Output area
        ttk.Label(self.analysis_frame, text="Ergebnisse:").grid(row=5, column=0, sticky=tk.W)

        self.output_text = scrolledtext.ScrolledText(self.analysis_frame, height=10)
        self.output_text.grid(row=6, column=0, sticky=tk.W + tk.E + tk.N + tk.S, pady=(0, 10))
        self.output_text.insert(tk.END, "Das Ergebnis wird hier angezeigt...")
        self.output_text.config(state=tk.DISABLED)

        configure_markdown_tags(self.output_text)

        # Note management buttons
        self.note_buttons_frame = ttk.Frame(self.analysis_frame)
        self.note_buttons_frame.grid(row=7, column=0, sticky=tk.W + tk.E, pady=(0, 10))

        export_frame = ttk.Frame(self.note_buttons_frame)
        export_frame.grid(row=0, column=0)
        export_button = ttk.Button(export_frame, text="Notiz exportieren", command=self.export_notes_as_pdf)
        export_button.pack(side=tk.LEFT)
        add_help_indicator(export_frame,
                          "Exportiert die aktuelle Notiz als PDF-Datei.")

        clipboard_frame = ttk.Frame(self.note_buttons_frame)
        clipboard_frame.grid(row=0, column=2)
        clipboard_button = ttk.Button(clipboard_frame, text="In Zwischenablage", command=self.copy_notes_as_text)
        clipboard_button.pack(side=tk.LEFT)
        add_help_indicator(clipboard_frame,
                          "Kopiert die aktuelle Notiz in die Zwischenablage des Systems.")

    # Funktionen

    def profile_function(self):
        cProfile.run('self.send_question()', os.path.join(os.getcwd(), 'profile.txt'), sortby='time')

    def pdf_file_choose(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF-Dateien", "*.pdf")])
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
            self.analyseResult = text_extraction_youtube_website(self.analysePath)
            return self.analyseResult, self.analysePath
        elif tab_index == 1:  # YouTube tab
            self.analysePath = self.youtube_url.get()
            self.analyseResult = text_extraction_youtube_website(self.analysePath)
            return self.analyseResult, self.analysePath
        elif tab_index == 2:  # PDF tab
            self.analysePath = self.pdf_url.get()
            self.analyseResult = self.pdf_path_var.get()
            return self.analyseResult

    def get_prompt(self,content):

        value = self.combobox.get()
        if value == "Zusammenfassung":
            question = "Fasse den Text zusammen:{text}"
            return question
        elif value == "Keyword-Extraktion":
            question = "Extrahiere Schlüsselwörter aus diesem Text: {text}".format(text=content)
            return question
        elif value == "Sentiment Analyse":
            question = "Analysiere die Stimmung und den Tonfall dieses Textes: {text}".format(text=content)
            return question
        elif value == "Themen-Erkennung":
            question = "Erkenne die Hauptthemen des nachfolgendes Textes: {text}".format(text=content)
            return question
        else:
            question_prompt = self.question_text.get(1.0, tk.END).strip()
            # Format the custom prompt with the content
            prompt_template = f"{question_prompt} {{text}}".format(text=content)
            return prompt_template

    def send_question(self):
        self.start_analyse()  # texte oder pdf_url extrahieren
        content = self.analyseResult  # ergebnis der extraktion in content speichern
        prompt = self.get_prompt(content)

        if "http" in self.analysePath.lower() or "youtu" in self.analysePath.lower():
            combined_text = prompt.format(text=content)
            result_analysis = real_ai_analyse_fortext(combined_text)

        else:
            result_analysis = real_ai_analyse_forpdf(content, prompt)


        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        markdown_to_tkinter_text(result_analysis, self.output_text)
        self.output_text.config(state=tk.DISABLED)

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
        tk.messagebox.showinfo("Export erfolgreich", "Notizen wurden als PDF exportiert!")

    def copy_notes_as_text(self):
        self.save_note()
        self.window.clipboard_clear()
        self.window.clipboard_append("\n\n".join(self.notes))
        self.window.update()
        tk.messagebox.showinfo("Export erfolgreich", "Notizen wurden in die Zwischenablage kopiert!")
