import os
import time
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from urllib.parse import urlparse, parse_qs

from openai import OpenAI
from openai import RateLimitError, APIConnectionError, APITimeoutError, APIError

from config import get_api_key

logger = logging.getLogger(__name__)


AVAILABLE_MODELS = {
    "gpt-4o": {"name": "GPT-4o", "max_tokens": 128000, "cost_per_1k_input": 0.0025, "cost_per_1k_output": 0.01},
    "gpt-4o-mini": {"name": "GPT-4o mini", "max_tokens": 128000, "cost_per_1k_input": 0.00015, "cost_per_1k_output": 0.0006},
    "gpt-4-turbo": {"name": "GPT-4 Turbo", "max_tokens": 128000, "cost_per_1k_input": 0.01, "cost_per_1k_output": 0.03},
}

DEFAULT_MODEL = "gpt-4o"


class AnalysisErrorCode(Enum):
    MISSING_API_KEY = "missing_api_key"
    CONTENT_TOO_LONG = "content_too_long"
    RATE_LIMITED = "rate_limited"
    CONNECTION_FAILED = "connection_failed"
    TIMED_OUT = "timed_out"
    INVALID_INPUT = "invalid_input"
    PROVIDER_ERROR = "provider_error"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class AnalysisError:
    code: AnalysisErrorCode
    user_message: str
    retryable: bool = False


class AnalysisFailure(Exception):
    def __init__(self, error: AnalysisError):
        super().__init__(error.user_message)
        self.error = error


@dataclass(frozen=True)
class AnalysisOutcome:
    content: str = ""
    error: Optional[AnalysisError] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def success(self) -> bool:
        return self.error is None

    def to_legacy_text(self) -> str:
        return self.content if self.success else f"Fehler: {self.error.user_message}"


class AnalysisSession:
    """
    Encapsulates per-session analysis state: chosen model, token usage and cost.
    Replaces the previous module-level global variables so the code is testable
    and thread-state is explicit.
    """

    def __init__(self, model: str = DEFAULT_MODEL):
        self._model = model if model in AVAILABLE_MODELS else DEFAULT_MODEL
        self.total_tokens_used = 0
        self.total_cost_estimate = 0.0

    @property
    def current_model(self) -> str:
        return self._model

    def set_model(self, model: str):
        if model in AVAILABLE_MODELS:
            self._model = model
            logger.info("Modell gewechselt auf: %s", model)
        else:
            logger.warning("Unbekanntes Modell: %s, behalte %s", model, self._model)

    def get_model(self) -> str:
        return self._model

    def get_usage_stats(self) -> dict:
        return {
            "total_tokens": self.total_tokens_used,
            "total_cost": round(self.total_cost_estimate, 4),
            "model": self._model,
        }

    def reset_usage_stats(self):
        self.total_tokens_used = 0
        self.total_cost_estimate = 0.0

    def record_usage(self, prompt_tokens: int, completion_tokens: int):
        self.total_tokens_used += prompt_tokens + completion_tokens
        model_info = AVAILABLE_MODELS.get(self._model, AVAILABLE_MODELS[DEFAULT_MODEL])
        self.total_cost_estimate += (
            prompt_tokens * model_info["cost_per_1k_input"] / 1000 +
            completion_tokens * model_info["cost_per_1k_output"] / 1000
        )


# Default session for backward-compatible module-level functions.
_default_session = AnalysisSession()


def set_model(model: str):
    """Setzt das aktuell verwendete Modell."""
    _default_session.set_model(model)


def get_model() -> str:
    """Gibt das aktuell verwendete Modell zurück."""
    return _default_session.get_model()


def get_usage_stats() -> dict:
    """Gibt Token/Cost-Tracking-Daten zurück."""
    return _default_session.get_usage_stats()


def reset_usage_stats():
    """Setzt Token/Cost-Tracking zurück."""
    _default_session.reset_usage_stats()


def estimate_tokens(text: str) -> int:
    """Schätzt die Token-Anzahl eines Textes (ca. 4 Zeichen pro Token)."""
    return max(1, len(text) // 4)


def validate_content_length(text: str, model: str = None) -> tuple:
    """Validiert, ob der Text innerhalb des Token-Limits des Modells liegt.

    Returns:
        (is_valid, estimated_tokens, max_tokens, message)
    """
    model = model or _default_session.current_model
    info = AVAILABLE_MODELS.get(model, AVAILABLE_MODELS[DEFAULT_MODEL])
    max_tokens = info["max_tokens"]
    estimated = estimate_tokens(text)

    if estimated > max_tokens * 0.8:
        return (False, estimated, max_tokens,
                f"Text ist zu lang: ~{estimated} Tokens (Limit: {max_tokens}). Bitte kürzen.")
    return (True, estimated, max_tokens, "")


def _retry_api_call(func, max_retries=3, base_delay=1.0):
    """Führt einen API-Call mit Retry und exponential backoff aus.

    Retries werden nur für vorübergehende OpenAI-Fehler durchgeführt
    (RateLimit, Timeout, Verbindungsfehler). Andere Fehler werden sofort
    weitergegeben.
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            return func()
        except (RateLimitError, APIConnectionError, APITimeoutError) as e:
            last_error = e
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    "API-Aufruf fehlgeschlagen (Versuch %d/%d): %s. Retry in %.1fs",
                    attempt + 1, max_retries, type(e).__name__, delay
                )
                time.sleep(delay)
            else:
                logger.error(
                    "API-Aufruf nach %d Versuchen endgültig fehlgeschlagen: %s",
                    max_retries, type(e).__name__
                )
        except Exception:
            # Non-retryable errors are raised immediately.
            raise
    raise last_error


def is_pdf_file(filepath):
    if not filepath:
        return False
    _, fileextension = os.path.splitext(filepath)
    return fileextension.lower() == ".pdf"


def is_safe_url(url):
    """Validiert eine URL: nur http/https, keine internen/private IPs."""
    from security import validate_url, SecurityException
    try:
        validate_url(url)
        return True
    except SecurityException:
        return False
    except Exception:
        return False


def is_safe_filepath(filepath):
    """Validiert einen Dateipfad: erlaubte Erweiterung und existiert."""
    from security import validate_file_path, SecurityException
    if not filepath:
        return False
    try:
        validate_file_path(filepath)
    except SecurityException:
        return False

    allowed_extensions = {".txt", ".pdf", ".csv", ".xlsx", ".xls", ".png", ".jpg", ".jpeg"}
    _, ext = os.path.splitext(filepath)
    if ext.lower() not in allowed_extensions:
        return False
    if not os.path.isfile(filepath):
        return False
    return True


try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None


def extract_transkript(youtubelink):
    if YouTubeTranscriptApi is None:
        raise RuntimeError("YouTube-Transkript-API nicht verfügbar. Bitte youtube-transcript-api installieren.")

    parsed = urlparse(youtubelink)
    video_id = None

    if parsed.hostname and parsed.hostname.lower() in ("www.youtube.com", "youtube.com"):
        video_id = parse_qs(parsed.query).get("v", [None])[0]
    elif parsed.hostname and parsed.hostname.lower() == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0] if parsed.path else None

    if not video_id:
        raise ValueError(f"Nicht unterstütztes YouTube-URL-Format: {youtubelink}")

    transkript = YouTubeTranscriptApi.get_transcript(video_id, languages=['de', 'en'])
    # Optimization: Use join for O(n) performance instead of O(n^2) loop concatenation
    if not transkript:
        return ""
    return " ".join(satz["text"] for satz in transkript) + " "


def _extract_readable_text_from_html(html: str) -> str:
    """Reduziert HTML auf lesbaren Haupttext (Navigation, Script, Style entfernt)."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    # Remove non-content elements that often contain PII or noise.
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        tag.decompose()

    # Try to prefer the main article/content area.
    main = soup.find("main") or soup.find("article") or soup.find("div", role="main")
    if main:
        text = main.get_text(separator="\n", strip=True)
    else:
        text = soup.get_text(separator="\n", strip=True)

    # Collapse multiple blank lines.
    lines = [line for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def extract_text_from_website(url):
    from security import safe_requests_get, validate_url, SecurityException
    validate_url(url)
    response = safe_requests_get(url, timeout=15)
    return _extract_readable_text_from_html(response.text)


def text_extraction_youtube_website(file_path_or_url):
    """Extrahiert Text aus YouTube-URLs, Webseiten-URLs oder lokalen Dateien."""
    if not file_path_or_url:
        return "Fehler: Keine Eingabe angegeben."

    if isinstance(file_path_or_url, str) and file_path_or_url.strip().lower().startswith(("http://", "https://")):
        text = file_path_or_url.strip()
        if "youtu" in text.lower():
            try:
                return extract_transkript(text)
            except Exception as e:
                return f"Fehler beim Extrahieren des YouTube-Transkripts: {e}"

        if not is_safe_url(text):
            return "Fehler: URL nicht erlaubt oder unsicher"
        try:
            return extract_text_from_website(text)
        except Exception as e:
            return f"Fehler beim Extrahieren der Webseite: {e}"

    # Local file path
    text_extensions = {".txt", ".md", ".csv", ".json", ".xml", ".html", ".htm", ".log", ".ini", ".py", ".js"}
    binary_extensions = {".pdf", ".xlsx", ".xls", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".doc", ".docx", ".ppt", ".pptx"}
    ext = os.path.splitext(file_path_or_url)[1].lower()
    if ext in binary_extensions:
        return f"Fehler: Dateien vom Typ '{ext}' können hier nicht als Text gelesen werden. Bitte verwenden Sie den passenden Import-Tab (z. B. PDF, Excel, Bilder)."

    if not is_safe_filepath(file_path_or_url):
        return "Fehler: Dateityp nicht unterstützt oder Pfad ungültig"
    try:
        with open(file_path_or_url, "r", encoding="utf-8") as file:
            return file.read()
    except UnicodeDecodeError:
        with open(file_path_or_url, "r", encoding="latin-1") as file:
            return file.read()
    except FileNotFoundError:
        return "Fehler: Datei konnte nicht gefunden werden"
    except Exception as e:
        return f"Ein Fehler ist aufgetreten: {e}"


def analyze_text(text: str) -> AnalysisOutcome:
    if not isinstance(text, str) or not text.strip():
        return AnalysisOutcome(error=AnalysisError(
            AnalysisErrorCode.INVALID_INPUT,
            "Bitte geben Sie einen Inhalt für die Analyse ein."
        ))

    is_valid, _est_tokens, _max_tokens, msg = validate_content_length(text)
    if not is_valid:
        return AnalysisOutcome(error=AnalysisError(
            AnalysisErrorCode.CONTENT_TOO_LONG,
            msg
        ))

    api_key = get_api_key()
    if not api_key:
        return AnalysisOutcome(error=AnalysisError(
            AnalysisErrorCode.MISSING_API_KEY,
            "Kein API-Schlüssel verfügbar. Bitte hinterlegen Sie einen OpenAI API-Key."
        ))

    try:
        client = OpenAI(api_key=api_key)

        def _call():
            return client.chat.completions.create(
                model=_default_session.current_model,
                messages=[{"role": "user", "content": text}]
            )

        response = _retry_api_call(_call)
        prompt_tokens = 0
        completion_tokens = 0
        if hasattr(response, 'usage') and response.usage:
            raw_prompt_tokens = response.usage.prompt_tokens
            raw_completion_tokens = response.usage.completion_tokens
            if isinstance(raw_prompt_tokens, int) and isinstance(raw_completion_tokens, int):
                prompt_tokens = raw_prompt_tokens
                completion_tokens = raw_completion_tokens
                _default_session.record_usage(prompt_tokens, completion_tokens)

        return AnalysisOutcome(
            content=response.choices[0].message.content or "",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
    except RateLimitError:
        logger.exception("Rate-Limit bei der KI-Analyse")
        return AnalysisOutcome(error=AnalysisError(
            AnalysisErrorCode.RATE_LIMITED,
            "Das API-Limit wurde erreicht. Bitte versuchen Sie es später erneut.",
            retryable=True
        ))
    except APITimeoutError:
        logger.exception("Zeitüberschreitung bei der KI-Analyse")
        return AnalysisOutcome(error=AnalysisError(
            AnalysisErrorCode.TIMED_OUT,
            "Die Analyse hat zu lange gedauert. Bitte versuchen Sie es erneut.",
            retryable=True
        ))
    except APIConnectionError:
        logger.exception("Verbindungsfehler bei der KI-Analyse")
        return AnalysisOutcome(error=AnalysisError(
            AnalysisErrorCode.CONNECTION_FAILED,
            "OpenAI ist derzeit nicht erreichbar. Bitte prüfen Sie die Verbindung und versuchen Sie es erneut.",
            retryable=True
        ))
    except APIError:
        logger.exception("API-Fehler bei der KI-Analyse")
        return AnalysisOutcome(error=AnalysisError(
            AnalysisErrorCode.PROVIDER_ERROR,
            "Der KI-Dienst konnte die Anfrage nicht verarbeiten. Bitte prüfen Sie Eingabe und Modell."
        ))
    except Exception:
        logger.exception("Unerwarteter Fehler bei der KI-Analyse")
        return AnalysisOutcome(error=AnalysisError(
            AnalysisErrorCode.UNKNOWN,
            "Die Analyse konnte nicht abgeschlossen werden. Bitte versuchen Sie es erneut."
        ))


def outcome_from_legacy_text(text: str) -> AnalysisOutcome:
    if text.startswith("Fehler:") or text.startswith("Error:"):
        return AnalysisOutcome(error=AnalysisError(
            AnalysisErrorCode.UNKNOWN,
            "Die Analyse konnte nicht abgeschlossen werden. Bitte prüfen Sie die Eingabe und versuchen Sie es erneut."
        ))
    return AnalysisOutcome(content=text)


def real_ai_analyse_fortext(text):
    return analyze_text(text).to_legacy_text()


def real_ai_analyse_forpdf(pdf_path, prompt):
    file = None
    assistant = None
    thread = None
    client = None
    try:
        if not is_pdf_file(pdf_path):
            return "Fehler: Ungültiger PDF-Pfad. Bitte wählen Sie eine .pdf-Datei."
        if not os.path.isfile(pdf_path):
            return "Fehler: PDF-Datei nicht gefunden."

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
                model=_default_session.current_model,
                instructions="Analyze the provided PDF document",
                tools=[{"type": "file_search"}]
            )

        assistant = _retry_api_call(_create_assistant)

        # Create a thread
        thread = client.beta.threads.create()

        # Create message with the PDF attached
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=[{"type": "text", "text": prompt}],
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
        while run.status not in ["completed", "failed", "cancelled"]:
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run.status == "failed":
                return f"Error: {run.last_error}"
            if run.status == "cancelled":
                return "Error: PDF-Analyse wurde abgebrochen."
            time.sleep(1)
            waited += 1
            if waited >= max_wait:
                return "Fehler: Zeitüberschreitung bei der PDF-Analyse"

        # Get the response
        messages = client.beta.threads.messages.list(thread_id=thread.id)

        # Return the assistant's response
        for message in messages.data:
            if message.role == "assistant":
                return message.content[0].text.value

        return "No response received"

    except Exception as e:
        logger.exception("Error analyzing PDF")
        return f"Error analyzing PDF: {e}"
    finally:
        if not client:
            return
        try:
            if file:
                client.files.delete(file.id)
        except Exception:
            pass
        try:
            if assistant:
                client.beta.assistants.delete(assistant.id)
        except Exception:
            pass
        try:
            if thread:
                client.beta.threads.delete(thread.id)
        except Exception:
            pass
