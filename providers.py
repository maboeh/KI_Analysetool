"""Provider-Abstraktion für KI-Analysen (M9).

Unterstützt neben der OpenAI-Cloud lokale bzw. OpenAI-kompatible Server
(z. B. Ollama, LM Studio, LocalAI). Ob Daten das Gerät verlassen, wird aus
dem Host der Base-URL abgeleitet – `localhost`/`127.0.0.1`/`::1` gelten als
lokal, alles andere als externe Übertragung.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", "0.0.0.0"})


@dataclass(frozen=True)
class Provider:
    """Beschreibt einen Analyse-Anbieter."""

    id: str
    name: str
    base_url: Optional[str]          # None = OpenAI-Standard-Endpoint
    requires_api_key: bool
    hint: str = ""

    @property
    def is_local(self) -> bool:
        """True, wenn die Base-URL auf einen lokalen Host zeigt."""
        if not self.base_url:
            return False
        host = urlparse(self.base_url).hostname or ""
        return host in LOCAL_HOSTS

    @property
    def external_transfer(self) -> bool:
        """True, wenn Inhalte das Gerät verlassen."""
        return not self.is_local


PROVIDERS = {
    "openai": Provider(
        id="openai",
        name="OpenAI (Cloud)",
        base_url=None,
        requires_api_key=True,
        hint="Verarbeitung auf OpenAI-Servern; es fallen API-Kosten an.",
    ),
    "ollama": Provider(
        id="ollama",
        name="Ollama (lokal)",
        base_url="http://localhost:11434/v1",
        requires_api_key=False,
        hint="Lokale Verarbeitung; keine Cloud-Übertragung, keine API-Kosten.",
    ),
    "custom": Provider(
        id="custom",
        name="OpenAI-kompatibel (eigene URL)",
        base_url=None,               # wird per Konfiguration gesetzt
        requires_api_key=False,
        hint="Beliebiger OpenAI-kompatibler Server (z. B. LM Studio, LocalAI).",
    ),
}


def get_provider(provider_id: str,
                 base_url: Optional[str] = None) -> Optional[Provider]:
    """Liefert den Provider; bei 'custom' mit der konfigurierten Base-URL."""
    provider = PROVIDERS.get(provider_id)
    if provider is None:
        return None
    if provider_id == "custom":
        if not base_url:
            return None
        return Provider(
            id=provider.id, name=provider.name,
            base_url=base_url.rstrip("/"),
            requires_api_key=provider.requires_api_key,
            hint=provider.hint,
        )
    return provider


def list_providers() -> List[Provider]:
    return list(PROVIDERS.values())


def build_client(provider: Provider, api_key: Optional[str] = None):
    """Erzeugt einen OpenAI-kompatiblen Client für den Provider."""
    from openai import OpenAI
    if provider.id == "openai":
        if not api_key:
            raise ValueError("OpenAI benötigt einen API-Key.")
        return OpenAI(api_key=api_key)
    if not provider.base_url:
        raise ValueError("Provider benötigt eine Base-URL.")
    # Lokale Server brauchen keinen echten Key; das SDK verlangt aber einen Wert.
    return OpenAI(base_url=provider.base_url,
                  api_key=api_key or "local")


# Muster für Modellnamen, die typischerweise nur bei OpenAI existieren.
_CLOUD_MODEL_PREFIXES = (
    "gpt-", "o1", "o3", "o4", "chatgpt-", "dall-e", "whisper", "tts-",
    "text-embedding", "text-davinci", "text-curie", "text-babbage",
    "text-ada", "davinci", "curie", "babbage", "ada",
)


def looks_like_cloud_model(model: Optional[str]) -> bool:
    """True, wenn der Modellname wie ein OpenAI-Cloud-Modell aussieht.

    Heuristik: lokale Server (Ollama, LM Studio) verwenden eigene Namen
    wie `llama3:latest`. Ein Cloud-Name auf einem lokalen Provider
    schlägt dort meist fehl – die Warnung macht das früh sichtbar.
    """
    if not model:
        return False
    name = model.strip().lower()
    return name.startswith(_CLOUD_MODEL_PREFIXES)


def detect_models(provider: Provider, timeout: float = 5.0) -> List[str]:
    """Fragt die Modellliste eines OpenAI-kompatiblen Servers ab.

    Nutzt GET {base_url}/models. Fehler (Server nicht erreichbar etc.)
    liefern eine leere Liste.
    """
    if not provider.base_url:
        return []
    try:
        request = Request(
            f"{provider.base_url.rstrip('/')}/models",
            headers={"Accept": "application/json"},
        )
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return sorted(
            entry["id"] for entry in payload.get("data", []) if "id" in entry
        )
    except Exception:
        logger.info("Modellerkennung für %s fehlgeschlagen", provider.id,
                    exc_info=True)
        return []
