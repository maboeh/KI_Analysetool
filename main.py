import tkinter as tk
import PyPDF2
import os
import re
from tkinter import filedialog, ttk, scrolledtext
from tkinter import messagebox
from tkinter import ttk

from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from youtube_transcript_api import YouTubeTranscriptApi
from bs4 import BeautifulSoup
import requests
from openai import OpenAI

from APIKeyManager import APIKeyManager

from markdown_formatter import configure_markdown_tags, markdown_to_tkinter_text

notes = []
analyseResult = ""
analysePath = ""

#TODO alle funktionen auf ihre funktionalität iund bessere identifikation überprüfen und refactoren
#TODO Gui auslagern als eigene klasse


#Funktionen
def pdf_file_choose():
    file_path = filedialog.askopenfilename(filetypes=[("PDF-Dateien", "*.pdf")])
    if file_path:
        pdf_entry.delete(0, tk.END)
        pdf_entry.insert(0, file_path)
        pdf_path_var.set(file_path)  # Update the path label


def is_pdf_file(filepath):
    _, fileextension = os.path.splitext(filepath)
    return fileextension.lower() == ".pdf"

def extract_transkript(youtubelink):
    if youtubelink.startswith("https://www.youtube.com/watch?v="):
        video_id = youtubelink.split("v=")[1]
    elif youtubelink.startswith("https://youtu.be/"):
        video_id = youtubelink.split("be/")[1]
    transkript = YouTubeTranscriptApi.get_transcript(video_id, languages=['de', 'en'])
    text = ""
    for satz in transkript:
        text += satz["text"] + " "
    return text

def extract_text_from_website(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text()
    return text

#TODO eigene funktionen für text und pdf <-- sieht wohl so aus dass ich das dringend benötig eund den gesamtflow neu denken muss!!!!!
def text_extraction(filePath):
    try:

        if "youtu" in filePath.lower():  # Erkennt verschiedene YouTube-URL-Formate
            transkript = extract_transkript(filePath)
            return transkript
        #website analyse
        elif "http" in filePath.lower():  # Erkennt verschiedene URL-Formate
            text = extract_text_from_website(filePath)
            return text
        else:
            try:
                with open(filePath, "r", encoding="utf-8") as file:
                    filePath_string = file.read()
                    return filePath_string
            except UnicodeDecodeError:
                # Versuche andere Kodierungen, wenn UTF-8 fehlschlägt
                with open(filePath, "r", encoding="latin-1") as file:
                    filePath_string = file.read()
                    return filePath_string
    except FileNotFoundError:
        return "Fehler: Datei konnte nicht gefunden werden"
    except Exception as e:
        return f"Ein Fehler ist aufgetreten: {str(e)}"

def start_analyse():

    global analyseResult
    global analysePath
    # Get path from the currently selected tab
    tab_id = input_tabs.select()
    tab_index = input_tabs.index(tab_id)



    if tab_index == 0:  # Website tab
        analysePath = website_url.get()
        analyseResult = text_extraction(analysePath)
        return analyseResult,analysePath
    elif tab_index == 1:  # YouTube tab
        analysePath = youtube_url.get()
        analyseResult = text_extraction(analysePath)
        return analyseResult,analysePath
    elif tab_index == 2:  # PDF tab
        analysePath = pdf_url.get()
        analyseResult = pdf_path_var.get()
        return analyseResult


def get_prompt(content):


    value = combobox.get()
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
        question_prompt = question_text.get(1.0, tk.END).strip()
        # Format the custom prompt with the content
        prompt_template = f"{question_prompt} {{text}}".format(text=content)
        return prompt_template




def send_question():
    start_analyse() #texte oder pdf_url extrahieren
    content = analyseResult #ergebnis der extraktion in content speichern
    prompt = get_prompt(content)

    if "http" in analysePath.lower() or "youtu" in analysePath.lower():
        combined_text = prompt.format(text=content)
        result_analysis = real_ai_analyse_fortext(combined_text)
        print(result_analysis)
    else:
        result_analysis = real_ai_analyse_forpdf(content, prompt)
        print(result_analysis)

    output_text.config(state=tk.NORMAL)
    output_text.delete(1.0, tk.END)
    markdown_to_tkinter_text(result_analysis, output_text)
    output_text.config(state=tk.DISABLED)

def real_ai_analyse_fortext(text):
    try:
        #TODO: OpenAI API Key input through user and login - include database then

        api_manager = APIKeyManager(app_name="KI_Analysetool")

        api_key = api_manager.get_api_key()
        client = OpenAI(api_key=api_key)


        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user",
                "content": text}]
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Fehler bei der KI-Analyse: {str(e)}"

def real_ai_analyse_forpdf(pdf_path, prompt):
    try:
        api_manager = APIKeyManager(app_name="KI_Analysetool")
        api_key = api_manager.get_api_key()
        client = OpenAI(api_key=api_key)

        # For PDFs:
        with open(pdf_path, "rb") as file_object:
            file = client.files.create(
                file=file_object,
                purpose="assistants"
            )

        # Create an assistant
        assistant = client.beta.assistants.create(
            model="gpt-4o",
            instructions="Analyze the provided PDF document",
            tools=[{"type": "file_search"}]
        )

        # Create a thread
        thread = client.beta.threads.create()

        # Create message with the PDF attached
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=[{
                "type": "text",
                "text": prompt
            }],
            attachments=[{
                "file_id": file.id,
                "tools": [{"type": "file_search"}]
            }]
        )

        # Run the assistant
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id
        )

        # Wait for completion
        while run.status not in ["completed", "failed"]:
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run.status == "failed":
                return f"Error: {run.last_error}"
            import time
            time.sleep(1)

        # Get the response
        messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )

        # Return the assistant's response
        for message in messages.data:
            if message.role == "assistant":
                return message.content[0].text.value

        return "No response received"

    except Exception as e:
        return f"Error analyzing PDF: {str(e)}"






def save_note():
    global notes
    note = output_text.get(1.0, tk.END).strip()

    if note:
        notes = [note]
        status_var.set("Notiz gespeichert")
    else:
        status_var.set("Kein Text zum Speichern gefunden")
    print(notes)

def export_notes_as_pdf():
    save_note()
    file_path = filedialog.asksaveasfilename(filetypes=[("PDF-Dateien", "*.pdf")])

    if not file_path:
        return
    pdf = SimpleDocTemplate(file_path, pagesize=letter)
    styles=getSampleStyleSheet()
    story = []

    title = Paragraph("Notizen", styles["Heading1"])
    story.append(title)
    story.append(Spacer(1, 0.25*inch))

    for i, note in enumerate(notes, 1):
        note_text = f"{i}. {note}"
        wrapped_text = Paragraph(note_text, styles["Normal"])
        story.append(wrapped_text)
        story.append(Spacer(1, 0.1*inch))

    pdf.build(story)
    # Inform user
    tk.messagebox.showinfo("Export erfolgreich", "Notizen wurden als PDF exportiert!")


def copy_notes_as_text():
    save_note()
    window.clipboard_clear()
    window.clipboard_append("\n\n".join(notes))
    window.update()
    tk.messagebox.showinfo("Export erfolgreich", "Notizen wurden in die Zwischenablage kopiert!")



#Gui

window = tk.Tk()
window.title("KI Analysetool")
window.geometry("800x1000")
window.minsize(700, 900)

#Main Container
main_frame = ttk.Frame(window,padding=15)
main_frame.pack(fill="both", expand=True)

#Header
header_label = ttk.Label(main_frame,text="KI-Analysetool" ,style="Header.TLabel")
header_label.pack(pady=(0,15))

#Input-Source Frame
sources_frame = ttk.LabelFrame(main_frame,text="Inhaltsquellen",padding=15)
sources_frame.pack(fill=tk.X,pady=(0,15))
sources_frame.columnconfigure(0, weight=1)

# Tabs for different input types
input_tabs = ttk.Notebook(sources_frame)
input_tabs.grid(row=0, column=0, sticky=tk.W+tk.E)

# Website tab
website_tab = ttk.Frame(input_tabs, padding=10)
input_tabs.add(website_tab, text="Webseite")

ttk.Label(website_tab, text="Webseiten-URL:").pack(anchor=tk.W, pady=(0, 5))

website_frame = ttk.Frame(website_tab)
website_frame.pack(fill=tk.X)

website_url = tk.StringVar()
website_entry = ttk.Entry(website_frame, textvariable=website_url)
website_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))



# YouTube tab
youtube_tab = ttk.Frame(input_tabs, padding=10)
input_tabs.add(youtube_tab, text="YouTube")

ttk.Label(youtube_tab, text="YouTube-Link:").pack(anchor=tk.W, pady=(0, 5))

youtube_frame = ttk.Frame(youtube_tab)
youtube_frame.pack(fill=tk.X)

youtube_url = tk.StringVar()
youtube_entry = ttk.Entry(youtube_frame, textvariable=youtube_url)
youtube_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))



# PDF tab
pdf_tab = ttk.Frame(input_tabs, padding=10)
input_tabs.add(pdf_tab, text="PDF")

ttk.Label(pdf_tab, text="PDF-URL:").pack(anchor=tk.W, pady=(0, 5))

pdf_url_frame = ttk.Frame(pdf_tab)
pdf_url_frame.pack(fill=tk.X, pady=(0, 10))

pdf_url = tk.StringVar()
pdf_entry = ttk.Entry(pdf_url_frame, textvariable=pdf_url)
pdf_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))



ttk.Label(pdf_tab, text="oder").pack(pady=5)

pdf_upload_button = ttk.Button(pdf_tab, text="PDF hochladen", command=pdf_file_choose)
pdf_upload_button.pack(pady=5)

pdf_path_var = tk.StringVar()
pdf_path_label = ttk.Label(pdf_tab, textvariable=pdf_path_var, wraplength=350)
pdf_path_label.pack(pady=5)



#----------------------------------------------------------------------------------------------------------------------------
# Analysis and results frame
analysis_frame = ttk.LabelFrame(main_frame, text="Analyse & Ergebnisse", padding=10)
analysis_frame.pack(fill=tk.BOTH, expand=True)
analysis_frame.rowconfigure(5, weight=1)
analysis_frame.columnconfigure(0, weight=1)


# Question input
ttk.Label(analysis_frame, text="Erstelle einen Prompt zu dem Inhalt:").grid(row=0,column=0,sticky=tk.W)

question_text = scrolledtext.ScrolledText(analysis_frame, height=4)
question_text.grid(row=1,column=0,sticky=tk.W+tk.E,pady=(0,15))

combobox = ttk.Combobox(analysis_frame, values=["Prompt senden", "Zusammenfassung","Keyword-Extraktion","Sentiment Analyse","Themen-Erkennung"])
combobox.current(0)
combobox.grid(row=2,column=0,sticky=tk.W+tk.E,pady=(0,15))

question_button = ttk.Button(analysis_frame, text="Frage senden", command=send_question)
question_button.grid(row=3,column=0,sticky=tk.W+tk.E,pady=(0,15))




# Separator
separator = ttk.Separator(analysis_frame, orient=tk.HORIZONTAL)
separator.grid(row=4,column=0,sticky=tk.W+tk.E,pady=10)

# Output area
ttk.Label(analysis_frame, text="Ergebnisse:").grid(row=5, column=0, sticky=tk.W)

output_text = scrolledtext.ScrolledText(analysis_frame, height=10)
output_text.grid(row=6, column=0, sticky=tk.W+tk.E+tk.N+tk.S, pady=(0, 10))
output_text.insert(tk.END, "Das Ergebnis wird hier angezeigt...")
output_text.config(state=tk.DISABLED)

configure_markdown_tags(output_text)

# Note management buttons
buttons_frame = ttk.Frame(analysis_frame)
buttons_frame.grid(row=7, column=0, sticky=tk.W+tk.E, pady=(0, 10))



export_button = ttk.Button(buttons_frame, text="Notiz exportieren", command=export_notes_as_pdf)
export_button.grid(row=0, column=0)

clipboard_button = ttk.Button(buttons_frame, text="In Zwischenablage", command=copy_notes_as_text)
clipboard_button.grid(row=0, column=2)

# Status bar
status_var = tk.StringVar()
status_var.set("Bereit")
status_bar = ttk.Label(main_frame, textvariable=status_var, relief=tk.SUNKEN, anchor=tk.W)
status_bar.pack(fill=tk.X, pady=(15, 0))



window.mainloop()

