
import os
from functools import lru_cache

from config import get_api_key
from security import validate_url, SecurityException
from urllib.parse import urljoin

def is_pdf_file(filepath):
    _, fileextension = os.path.splitext(filepath)
    return fileextension.lower() == ".pdf"

@lru_cache(maxsize=32)

def extract_transkript(youtubelink):
    from youtube_transcript_api import YouTubeTranscriptApi
    if youtubelink.startswith("https://www.youtube.com/watch?v="):
        video_id = youtubelink.split("v=")[1]
    elif youtubelink.startswith("https://youtu.be/"):
        video_id = youtubelink.split("be/")[1]
    transkript = YouTubeTranscriptApi.get_transcript(video_id, languages=['de', 'en'])
    # Optimization: Use join for O(n) performance instead of O(n^2) loop concatenation
    if not transkript:
        return ""
    return " ".join(satz["text"] for satz in transkript) + " "


def extract_text_from_website(url):
    """
    Extracts text from a website, following redirects securely.
    """
    session = requests.Session()
    # Initial validation
    try:
        validate_url(url)
    except SecurityException as e:
        return f"Security Error: {str(e)}"

    try:
        response = session.get(url, allow_redirects=False, timeout=10)
    except requests.exceptions.RequestException as e:
        return f"Error fetching URL: {str(e)}"

    redirects = 0
    max_redirects = 5

    while response.is_redirect and redirects < max_redirects:
        redirect_url = response.headers.get('Location')
        if not redirect_url:
            break

        # Handle relative redirects
        redirect_url = urljoin(url, redirect_url)

        # Validate the redirect target
        try:
            validate_url(redirect_url)
        except SecurityException as e:
            return f"Security Error on redirect: {str(e)}"

        try:
            response = session.get(redirect_url, allow_redirects=False, timeout=10)
        except requests.exceptions.RequestException as e:
             return f"Error fetching redirect URL: {str(e)}"

        redirects += 1
        url = redirect_url

    if redirects >= max_redirects:
        return "Error: Too many redirects"

    # Now we have the final response
    if response.status_code != 200:
        return f"Error: Failed to retrieve content (Status code: {response.status_code})"

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text()
    return text

# TODO eigene funktionen für text und pdf <-- sieht wohl so aus dass ich d


def text_extraction_youtube_website(filePath):
    try:

        if "youtu" in filePath.lower():  # Erkennt verschiedene YouTube-URL-Formate
            transkript = extract_transkript(filePath)
            return transkript
        # website analyse
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
        from openai import OpenAI
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
        from openai import OpenAI
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
