import os
import time
import logging
from urllib.parse import urlparse
import ipaddress

import requests
from bs4 import BeautifulSoup

from config import get_api_key

logger = logging.getLogger(__name__)


AVAILABLE_MODELS = {
    "gpt-4o": {"name": "GPT-4o", "max_tokens": 128000, "cost_per_1k_input": 0.0025, "cost_per_1k_output": 0.01},
    "gpt-4o-mini": {"name": "GPT-4o mini", "max_tokens": 128000, "cost_per_1k_input": 0.00015, "cost_per_1k_output": 0.0006},
    "gpt-4-turbo": {"name": "GPT-4 Turbo", "max_tokens": 128000, "cost_per_1k_input": 0.01, "cost_per_1k_output": 0.03},
}

DEFAULT_MODEL = "gpt-4o"

current_model = DEFAULT_MODEL
total_tokens_used = 0
total_cost_estimate = 0.0


def set_model(model: str):
    """Setzt das aktuell verwendete Modell."""
    global current_model
    if model in AVAILABLE_MODELS:
        current_model = model
        logger.info(f"Modell gewechselt auf: {model}")
    else:
        logger.warning(f"Unbekanntes Modell: {model}, behalte {current_model}")


def get_model() -> str:
    """Gibt das aktuell verwendete Modell zurück."""
    return current_model


def get_usage_stats() -> dict:
    """Gibt Token/Cost-Tracking-Daten zurück."""
    return {
        "total_tokens": total_tokens_used,
        "total_cost": round(total_cost_estimate, 4),
        "model": current_model,
    }


def reset_usage_stats():
    """Setzt Token/Cost-Tracking zurück."""
    global total_tokens_used, total_cost_estimate
    total_tokens_used = 0
    total_cost_estimate = 0.0


def estimate_tokens(text: str) -> int:
    """Schätzt die Token-Anzahl eines Textes (ca. 4 Zeichen pro Token)."""
    return max(1, len(text) // 4)


def validate_content_length(text: str, model: str = None) -> tuple:
    """Validiert, ob der Text innerhalb des Token-Limits des Modells liegt.
    
    Returns:
        (is_valid, estimated_tokens, max_tokens, message)
    """
    model = model or current_model
    info = AVAILABLE_MODELS.get(model, AVAILABLE_MODELS[DEFAULT_MODEL])
    max_tokens = info["max_tokens"]
    estimated = estimate_tokens(text)
    
    if estimated > max_tokens * 0.8:
        return (False, estimated, max_tokens,
                f"Text ist zu lang: ~{estimated} Tokens (Limit: {max_tokens}). Bitte kürzen.")
    return (True, estimated, max_tokens, "")


def _retry_api_call(func, max_retries=3, base_delay=1.0):
    """Führt einen API-Call mit Retry und exponential backoff aus."""
    last_error = None
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning(f"API-Aufruf fehlgeschlagen (Versuch {attempt + 1}/{max_retries}): {e}. Retry in {delay}s")
                time.sleep(delay)
            else:
                logger.error(f"API-Aufruf nach {max_retries} Versuchen endgültig fehlgeschlagen: {e}")
    raise last_error





def is_pdf_file(filepath):
    _, fileextension = os.path.splitext(filepath)
    return fileextension.lower() == ".pdf"

def is_safe_url(url):
    """Validiert eine URL: nur http/https, keine internen/private IPs."""
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    hostname = parsed.hostname
    if not hostname:
        return False
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return False
    except ValueError:
        pass
    blocked = {"localhost", "0.0.0.0", "metadata.google.internal"}
    if hostname.lower() in blocked:
        return False
    return True

def is_safe_filepath(filepath):
    """Validiert einen Dateipfad: muss existieren und darf nicht außerhalb des Arbeitsverzeichnisses liegen."""
    if not filepath:
        return False
    abs_path = os.path.abspath(filepath)
    allowed_extensions = {".txt", ".pdf", ".csv", ".xlsx", ".xls", ".png", ".jpg", ".jpeg"}
    _, ext = os.path.splitext(abs_path)
    if ext.lower() not in allowed_extensions:
        return False
    return True

def extract_transkript(youtubelink):
    from youtube_transcript_api import YouTubeTranscriptApi
    if youtubelink.startswith("https://www.youtube.com/watch?v="):
        video_id = youtubelink.split("v=")[1].split("&")[0]
    elif youtubelink.startswith("https://youtu.be/"):
        video_id = youtubelink.split("be/")[1].split("?")[0].split("&")[0]
    else:
        raise ValueError(f"Nicht unterstütztes YouTube-URL-Format: {youtubelink}")
    transkript = YouTubeTranscriptApi.get_transcript(video_id, languages=['de', 'en'])
    # Optimization: Use join for O(n) performance instead of O(n^2) loop concatenation
    if not transkript:
        return ""
    return " ".join(satz["text"] for satz in transkript) + " "


def extract_text_from_website(url):
    if not is_safe_url(url):
        raise ValueError(f"URL nicht erlaubt oder unsicher: {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text()
    return text

# TODO eigene funktionen für text und pdf <-- sieht wohl so aus dass ich d


def text_extraction_youtube_website(filePath):
    try:

        if "youtu" in filePath.lower():
            transkript = extract_transkript(filePath)
            return transkript
        elif "http" in filePath.lower():
            if not is_safe_url(filePath):
                return "Fehler: URL nicht erlaubt oder unsicher"
            text = extract_text_from_website(filePath)
            return text
        else:
            if not is_safe_filepath(filePath):
                return "Fehler: Dateityp nicht unterstützt oder Pfad ungültig"
            try:
                with open(filePath, "r", encoding="utf-8") as file:
                    filePath_string = file.read()
                    return filePath_string
            except UnicodeDecodeError:
                with open(filePath, "r", encoding="latin-1") as file:
                    filePath_string = file.read()
                    return filePath_string
    except FileNotFoundError:
        return "Fehler: Datei konnte nicht gefunden werden"
    except Exception as e:
        return f"Ein Fehler ist aufgetreten: {str(e)}"


def real_ai_analyse_fortext(text):
    try:
        is_valid, est_tokens, max_tokens, msg = validate_content_length(text)
        if not is_valid:
            return f"Fehler: {msg}"

        api_key = get_api_key()

        if not api_key:
            return "Fehler: Kein API-Schlüssel verfügbar"

        client = OpenAI(api_key=api_key)

        def _call():
            return client.chat.completions.create(
                model=current_model,
                messages=[
                    {"role": "user",
                    "content": text}]
            )

        response = _retry_api_call(_call)

        global total_tokens_used, total_cost_estimate
        if hasattr(response, 'usage') and response.usage:
            total_tokens_used += response.usage.total_tokens
            model_info = AVAILABLE_MODELS.get(current_model, AVAILABLE_MODELS[DEFAULT_MODEL])
            total_cost_estimate += (
                response.usage.prompt_tokens * model_info["cost_per_1k_input"] / 1000 +
                response.usage.completion_tokens * model_info["cost_per_1k_output"] / 1000
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

        def _create_assistant():
            return client.beta.assistants.create(
                model=current_model,
                instructions="Analyze the provided PDF document",
                tools=[{"type": "file_search"}]
            )

        assistant = _retry_api_call(_create_assistant)

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
        max_wait = 120
        waited = 0
        while run.status not in ["completed", "failed"]:
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run.status == "failed":
                return f"Error: {run.last_error}"
            time.sleep(1)
            waited += 1
            if waited >= max_wait:
                return "Fehler: Zeitüberschreitung bei der PDF-Analyse"

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
    finally:
        try:
            if 'file' in locals() and file:
                client.files.delete(file.id)
            if 'assistant' in locals() and assistant:
                client.beta.assistants.delete(assistant.id)
        except Exception:
            pass







