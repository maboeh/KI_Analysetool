
import os

from youtube_transcript_api import YouTubeTranscriptApi
from bs4 import BeautifulSoup
import requests
from openai import OpenAI
from config import get_api_key





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
def text_extraction_youtube_website(filePath):
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


def real_ai_analyse_fortext(text):
    try:



        api_key = get_api_key()

        if not api_key:
            return "Fehler: Kein API-Schlüssel verfügbar"

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

        api_key = get_api_key()
        if not api_key:
            return "Fehler: Kein API-Schlüssel verfügbar"
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







