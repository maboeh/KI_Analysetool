import os
import time
import logging
import threading
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
    FILE_NOT_FOUND = "file_not_found"
    UNSUPPORTED_FORMAT = "unsupported_format"
    UNSAFE_URL = "unsafe_url"
    EXTRACTION_FAILED = "extraction_failed"
    CANCELLED = "cancelled"
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


@dataclass(frozen=True)
class ExtractionOutcome:
    content: str = ""
    source_type: str = "unknown"
    source: str = ""
    error: Optional[AnalysisError] = None

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
        self._lock = threading.Lock()
        self.total_tokens_used = 0
        self.total_cost_estimate = 0.0
        self._budget_usd: Optional[float] = None

    @property
    def current_model(self) -> str:
        with self._lock:
            return self._model

    def set_model(self, model: str):
        with self._lock:
            if model in AVAILABLE_MODELS:
                self._model = model
                logger.info("Modell gewechselt auf: %s", model)
            else:
                logger.warning("Unbekanntes Modell: %s, behalte %s", model, self._model)

    def get_model(self) -> str:
        return self.current_model

    def get_usage_stats(self) -> dict:
        with self._lock:
            return {
                "total_tokens": self.total_tokens_used,
                "total_cost": round(self.total_cost_estimate, 4),
                "model": self._model,
            }

    def reset_usage_stats(self):
        with self._lock:
            self.total_tokens_used = 0
            self.total_cost_estimate = 0.0

    def record_usage(self, prompt_tokens: int, completion_tokens: int):
        with self._lock:
            self.total_tokens_used += prompt_tokens + completion_tokens
            model_info = AVAILABLE_MODELS.get(self._model, AVAILABLE_MODELS[DEFAULT_MODEL])
            self.total_cost_estimate += (
                prompt_tokens * model_info["cost_per_1k_input"] / 1000 +
                completion_tokens * model_info["cost_per_1k_output"] / 1000
            )

    def set_budget(self, limit_usd: Optional[float]):
        """Setzt ein optionales Sitzungsbudget in USD (None = unbegrenzt)."""
        with self._lock:
            if limit_usd is None or (isinstance(limit_usd, (int, float)) and limit_usd <= 0):
                self._budget_usd = None
            else:
                self._budget_usd = float(limit_usd)

    def get_budget_status(self) -> dict:
        """Budgetstatus der Sitzung: limit, spent, remaining, fraction, warn/exceeded."""
        with self._lock:
            spent = self.total_cost_estimate
            limit = self._budget_usd
        if not limit:
            return {
                "limit": None, "spent": round(spent, 4),
                "remaining": None, "fraction": 0.0,
                "warning": False, "exceeded": False,
            }
        fraction = spent / limit
        return {
            "limit": round(limit, 4),
            "spent": round(spent, 4),
            "remaining": round(max(0.0, limit - spent), 4),
            "fraction": round(fraction, 3),
            "warning": fraction >= 0.8,
            "exceeded": fraction >= 1.0,
        }


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


def set_session_budget(limit_usd: Optional[float]):
    """Setzt ein optionales Sitzungsbudget in USD (None oder <= 0 = unbegrenzt)."""
    _default_session.set_budget(limit_usd)


def get_budget_status() -> dict:
    """Gibt den Budgetstatus der Standardsession zurück."""
    return _default_session.get_budget_status()


def estimate_request_cost(text: str, model: Optional[str] = None,
                          expected_output_tokens: int = 1024) -> dict:
    """Schätzt die Kosten einer Analyse vor dem API-Request.

    Args:
        text: Der an den Anbieter gesendete Gesamttext (Prompt + Inhalt).
        model: Optionaler Modellname; Standard ist das aktive Modell.
        expected_output_tokens: Annahme für die Antwortlänge.

    Returns:
        Dict mit input_tokens, output_tokens, estimated_cost und model.
    """
    model = model or _default_session.current_model
    info = AVAILABLE_MODELS.get(model, AVAILABLE_MODELS[DEFAULT_MODEL])
    input_tokens = estimate_tokens(text or "")
    cost = (
        input_tokens * info["cost_per_1k_input"] / 1000 +
        expected_output_tokens * info["cost_per_1k_output"] / 1000
    )
    return {
        "input_tokens": input_tokens,
        "output_tokens": expected_output_tokens,
        "estimated_cost": round(cost, 6),
        "model": model,
    }


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


def extract_content(file_path_or_url: str) -> ExtractionOutcome:
    if not isinstance(file_path_or_url, str) or not file_path_or_url.strip():
        return ExtractionOutcome(error=AnalysisError(
            AnalysisErrorCode.INVALID_INPUT,
            "Bitte geben Sie eine URL oder einen Dateipfad an."
        ))

    source = file_path_or_url.strip()
    if source.lower().startswith(("http://", "https://")):
        parsed = urlparse(source)
        hostname = (parsed.hostname or "").lower()
        if hostname in ("youtube.com", "www.youtube.com", "youtu.be"):
            try:
                content = extract_transkript(source)
                if not content.strip():
                    raise ValueError("Empty transcript")
                return ExtractionOutcome(content=content, source_type="youtube", source=source)
            except Exception:
                logger.exception("Fehler bei der YouTube-Transkriptextraktion")
                return ExtractionOutcome(source_type="youtube", source=source, error=AnalysisError(
                    AnalysisErrorCode.EXTRACTION_FAILED,
                    "Das YouTube-Transkript konnte nicht extrahiert werden. Prüfen Sie URL und Untertitel."
                ))

        try:
            content = extract_text_from_website(source)
            if not content.strip():
                raise ValueError("Empty website content")
            return ExtractionOutcome(content=content, source_type="website", source=source)
        except Exception as exc:
            from security import SecurityException
            if isinstance(exc, SecurityException):
                code = AnalysisErrorCode.UNSAFE_URL
                message = "Die URL ist nicht erlaubt oder verweist auf ein geschütztes Netzwerk."
            else:
                code = AnalysisErrorCode.EXTRACTION_FAILED
                message = "Der lesbare Inhalt der Webseite konnte nicht extrahiert werden."
            logger.exception("Fehler bei der Webseitenextraktion")
            return ExtractionOutcome(source_type="website", source=source, error=AnalysisError(code, message))

    # Local file path
    text_extensions = {".txt", ".md", ".csv", ".json", ".xml", ".html", ".htm", ".log", ".ini", ".py", ".js"}
    binary_extensions = {".pdf", ".xlsx", ".xls", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".doc", ".docx", ".ppt", ".pptx"}
    ext = os.path.splitext(source)[1].lower()
    if ext in binary_extensions or ext not in text_extensions:
        return ExtractionOutcome(source_type="file", source=source, error=AnalysisError(
            AnalysisErrorCode.UNSUPPORTED_FORMAT,
            f"Dateien vom Typ '{ext or 'unbekannt'}' müssen über den passenden Import-Tab geöffnet werden."
        ))
    if not os.path.isfile(source):
        return ExtractionOutcome(source_type="file", source=source, error=AnalysisError(
            AnalysisErrorCode.FILE_NOT_FOUND,
            "Die ausgewählte Datei wurde nicht gefunden."
        ))

    try:
        from security import validate_file_path
        safe_path = validate_file_path(source)
        try:
            with open(safe_path, "r", encoding="utf-8") as file:
                content = file.read()
        except UnicodeDecodeError:
            with open(safe_path, "r", encoding="latin-1") as file:
                content = file.read()
        return ExtractionOutcome(content=content, source_type="file", source=safe_path)
    except Exception:
        logger.exception("Fehler bei der lokalen Textextraktion")
        return ExtractionOutcome(source_type="file", source=source, error=AnalysisError(
            AnalysisErrorCode.EXTRACTION_FAILED,
            "Die Datei konnte nicht gelesen werden. Prüfen Sie Format und Zugriffsrechte."
        ))


def text_extraction_youtube_website(file_path_or_url):
    """Extrahiert Text aus YouTube-URLs, Webseiten-URLs oder lokalen Dateien."""
    return extract_content(file_path_or_url).to_legacy_text()


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


def analyze_with_prompt(content: str, prompt: str,
                        model: Optional[str] = None) -> AnalysisOutcome:
    """Analysiert Inhalt mit eigenem Prompt und optionalem Modell (Playground)."""
    if not isinstance(content, str) or not content.strip():
        return AnalysisOutcome(error=AnalysisError(
            AnalysisErrorCode.INVALID_INPUT,
            "Bitte geben Sie einen Inhalt für die Analyse ein."
        ))
    if not isinstance(prompt, str) or not prompt.strip():
        return AnalysisOutcome(error=AnalysisError(
            AnalysisErrorCode.INVALID_INPUT,
            "Bitte geben Sie einen Prompt für die Analyse ein."
        ))
    model_id = model if model in AVAILABLE_MODELS else get_model()

    is_valid, _est_tokens, _max_tokens, msg = validate_content_length(
        content, model=model_id)
    if not is_valid:
        return AnalysisOutcome(error=AnalysisError(
            AnalysisErrorCode.CONTENT_TOO_LONG, msg))

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
                model=model_id,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content},
                ]
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
        logger.exception("Providerfehler bei der KI-Analyse")
        return AnalysisOutcome(error=AnalysisError(
            AnalysisErrorCode.PROVIDER_ERROR,
            "Der Analyse-Dienst hat einen Fehler gemeldet. Bitte versuchen Sie es erneut.",
            retryable=True
        ))
    except Exception:
        logger.exception("Unbekannter Fehler bei der KI-Analyse")
        return AnalysisOutcome(error=AnalysisError(
            AnalysisErrorCode.UNKNOWN,
            "Die Analyse ist unerwartet fehlgeschlagen."
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


def analyze_pdf(pdf_path: str, prompt: str) -> AnalysisOutcome:
    file = None
    assistant = None
    thread = None
    client = None
    if not isinstance(pdf_path, str) or not pdf_path.strip():
        return AnalysisOutcome(error=AnalysisError(
            AnalysisErrorCode.INVALID_INPUT,
            "Bitte wählen Sie eine PDF-Datei aus."
        ))
    if not os.path.isfile(pdf_path):
        return AnalysisOutcome(error=AnalysisError(
            AnalysisErrorCode.FILE_NOT_FOUND,
            "Die PDF-Datei wurde nicht gefunden."
        ))
    if not is_pdf_file(pdf_path):
        return AnalysisOutcome(error=AnalysisError(
            AnalysisErrorCode.UNSUPPORTED_FORMAT,
            "Die ausgewählte Datei ist keine PDF-Datei."
        ))
    if not isinstance(prompt, str) or not prompt.strip():
        return AnalysisOutcome(error=AnalysisError(
            AnalysisErrorCode.INVALID_INPUT,
            "Bitte geben Sie einen Analyseauftrag für die PDF-Datei an."
        ))

    api_key = get_api_key()
    if not api_key:
        return AnalysisOutcome(error=AnalysisError(
            AnalysisErrorCode.MISSING_API_KEY,
            "Kein API-Schlüssel verfügbar. Bitte hinterlegen Sie einen OpenAI API-Key."
        ))

    try:
        client = OpenAI(api_key=api_key)

        # For PDFs:
        with open(pdf_path, "rb") as file_object:
            file = client.files.create(file=file_object, purpose="assistants")

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
        while run.status not in ["completed", "failed", "cancelled", "expired"]:
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            time.sleep(1)
            waited += 1
            if waited >= max_wait:
                return AnalysisOutcome(error=AnalysisError(
                    AnalysisErrorCode.TIMED_OUT,
                    "Die PDF-Analyse hat zu lange gedauert. Bitte versuchen Sie es erneut.",
                    retryable=True
                ))

        if run.status == "failed" or run.status == "expired":
            return AnalysisOutcome(error=AnalysisError(
                AnalysisErrorCode.PROVIDER_ERROR,
                "Der KI-Dienst konnte die PDF-Datei nicht verarbeiten."
            ))
        if run.status == "cancelled":
            return AnalysisOutcome(error=AnalysisError(
                AnalysisErrorCode.CANCELLED,
                "Die PDF-Analyse wurde abgebrochen."
            ))

        # Get the response
        messages = client.beta.threads.messages.list(thread_id=thread.id)

        # Return the assistant's response
        for message in messages.data:
            if message.role == "assistant" and message.content:
                content = message.content[0].text.value
                usage = getattr(run, "usage", None)
                prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
                completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
                if isinstance(prompt_tokens, int) and isinstance(completion_tokens, int):
                    _default_session.record_usage(prompt_tokens, completion_tokens)
                else:
                    prompt_tokens = completion_tokens = 0
                return AnalysisOutcome(
                    content=content,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens
                )

        return AnalysisOutcome(error=AnalysisError(
            AnalysisErrorCode.PROVIDER_ERROR,
            "Der KI-Dienst hat kein PDF-Analyseergebnis zurückgegeben."
        ))
    except RateLimitError:
        logger.exception("Rate-Limit bei der PDF-Analyse")
        return AnalysisOutcome(error=AnalysisError(
            AnalysisErrorCode.RATE_LIMITED,
            "Das API-Limit wurde erreicht. Bitte versuchen Sie es später erneut.",
            retryable=True
        ))
    except APITimeoutError:
        logger.exception("Zeitüberschreitung bei der PDF-Analyse")
        return AnalysisOutcome(error=AnalysisError(
            AnalysisErrorCode.TIMED_OUT,
            "Die PDF-Analyse hat zu lange gedauert. Bitte versuchen Sie es erneut.",
            retryable=True
        ))
    except APIConnectionError:
        logger.exception("Verbindungsfehler bei der PDF-Analyse")
        return AnalysisOutcome(error=AnalysisError(
            AnalysisErrorCode.CONNECTION_FAILED,
            "OpenAI ist derzeit nicht erreichbar. Bitte prüfen Sie die Verbindung.",
            retryable=True
        ))
    except APIError:
        logger.exception("API-Fehler bei der PDF-Analyse")
        return AnalysisOutcome(error=AnalysisError(
            AnalysisErrorCode.PROVIDER_ERROR,
            "Der KI-Dienst konnte die PDF-Anfrage nicht verarbeiten."
        ))
    except Exception:
        logger.exception("Unerwarteter Fehler bei der PDF-Analyse")
        return AnalysisOutcome(error=AnalysisError(
            AnalysisErrorCode.UNKNOWN,
            "Die PDF-Analyse konnte nicht abgeschlossen werden."
        ))
    finally:
        if client:
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


def real_ai_analyse_forpdf(pdf_path, prompt):
    return analyze_pdf(pdf_path, prompt).to_legacy_text()
