import configparser
import os
import sys
import logging

logger = logging.getLogger(__name__)

# Interner, kurzlebiger Cache für den API-Key. Wird niemals direkt exportiert
# oder geloggt; Zugriff nur über die definierten Funktionen.
_API_KEY_CACHE = None


try:
    import keyring
    KEYRING_AVAILABLE = True
    KEYRING_SERVICE = "KI_Analysetool"
    KEYRING_USERNAME = "openai_api_key"
except ImportError:
    KEYRING_AVAILABLE = False


class SecretFilter(logging.Filter):
    """Filtert sensible Werte wie OpenAI API-Keys aus Log-Ausgaben heraus."""

    # Heuristiken für Secrets, die niemals geloggt werden dürfen.
    _patterns = (
        r"\bsk-[a-zA-Z0-9]{20,}\b",
        r"\b(OPENAI_)?API[_-]?KEY\s*=\s*[^\s'\"]+",
        r"\b(openai_key|OpenAI_Key|openai_api_key)\s*=\s*[^\s'\"]+",
    )

    def filter(self, record):
        import re
        # Build the full formatted message regardless of printf-style or f-string args.
        msg = record.getMessage()
        for pattern in self._patterns:
            msg = re.sub(pattern, "***REDACTED***", msg, flags=re.IGNORECASE)
        record.msg = msg
        record.args = ()
        return True


def _mask(text):
    """Hilfsfunktion zum maskieren von Secrets in beliebigen Strings."""
    import re
    if not isinstance(text, str):
        return text
    for pattern in SecretFilter._patterns:
        text = re.sub(pattern, "***REDACTED***", text, flags=re.IGNORECASE)
    return text


def get_config_path():
    """Gibt den absoluten Pfad zur Konfigurationsdatei zurück.

    Im Frozen-Build liegt die Datei im schreibbaren Benutzer-Datenverzeichnis,
    in der Entwicklung neben dem Quellcode.
    """
    from app_paths import get_data_dir, is_frozen
    if is_frozen():
        return str(get_data_dir() / 'config.ini')
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')


def check_api_key_exists():
    """Prüft, ob ein API-Key im Keyring, in der Umgebungsvariable oder Konfigurationsdatei existiert."""
    global _API_KEY_CACHE

    if KEYRING_AVAILABLE:
        key = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
        if key:
            _API_KEY_CACHE = key
            return True

    env_key = os.environ.get('OPENAI_API_KEY', '')
    if env_key:
        _API_KEY_CACHE = env_key
        return True

    config_path = get_config_path()
    if os.path.exists(config_path):
        config = configparser.ConfigParser()
        config.read(config_path)
        if 'API' in config:
            # Akzeptiere alle historischen Key-Namen (openai_key, OpenAI_Key, openai_api_key)
            for key_name in ('OpenAI_Key', 'openai_key', 'openai_api_key'):
                value = config['API'].get(key_name)
                if value:
                    _API_KEY_CACHE = value
                    return True

    return False


def save_api_key(key):
    """Speichert den API-Key sicher im OS-Keyring mit Fallback auf config.ini."""
    global _API_KEY_CACHE

    if not isinstance(key, str) or not key.strip():
        raise ValueError("API-Key darf nicht leer sein.")

    key = key.strip()
    _API_KEY_CACHE = key

    if KEYRING_AVAILABLE:
        try:
            keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, key)
            _migrate_key_from_config_ini()
            return
        except Exception as e:
            # Vermeide, dass der Key selbst in der Exception landet
            logger.warning("Keyring-Speicherung fehlgeschlagen, falle auf config.ini zurück: %s", type(e).__name__)

    # Fallback: Klartext in config.ini (nur wenn Keyring nicht verfügbar).
    # Wir warnen explizit, da dies weniger sicher ist.
    logger.warning(
        "API-Key wird in config.ini gespeichert, weil kein OS-Keyring verfügbar ist. "
        "Bitte prüfen Sie die Zugriffsrechte auf diese Datei."
    )

    config = configparser.ConfigParser()
    config_path = get_config_path()

    if os.path.exists(config_path):
        config.read(config_path)

    if 'API' not in config:
        config['API'] = {}

    # Einheitlicher Key-Name; alte Varianten entfernen
    for old_name in ('OpenAI_Key', 'openai_api_key'):
        if old_name in config['API']:
            del config['API'][old_name]
    config['API']['openai_key'] = key

    with open(config_path, 'w') as configfile:
        config.write(configfile)
        configfile.flush()
        os.fsync(configfile.fileno())
    os.chmod(config_path, 0o600)


def get_api_key():
    """Liest den API-Key aus der Konfigurationsdatei oder Umgebungsvariable."""
    global _API_KEY_CACHE

    # Falls schon im Speicher, direkt zurückgeben
    if _API_KEY_CACHE:
        return _API_KEY_CACHE

    # Sonst versuchen zu laden
    if check_api_key_exists():
        return _API_KEY_CACHE

    # Interaktive Abfrage nur im CLI-Modus
    if not sys.stdin.isatty():
        return None

    print("Kein API-Schlüssel gefunden.")
    choice = input("Möchtest du einen API-Schlüssel eingeben? (j/n): ")

    if choice.lower() in ["j", "ja", "y", "yes"]:
        from getpass import getpass
        api_key = getpass("Gib deinen OpenAI API-Schlüssel ein: ")
        save_choice = input("Schlüssel für zukünftige Verwendung speichern? (j/n): ")

        if save_choice.lower() in ["j", "ja", "y", "yes"]:
            save_api_key(api_key)
        else:
            _API_KEY_CACHE = api_key

        return api_key

    return None


def clear_api_key_cache():
    """Löscht den internen API-Key-Cache. Nützlich für Tests oder beim Beenden der Anwendung."""
    global _API_KEY_CACHE
    _API_KEY_CACHE = None


def _migrate_key_from_config_ini():
    """Entfernt den API-Key aus config.ini, wenn er erfolgreich im Keyring gespeichert wurde."""
    config_path = get_config_path()
    if not os.path.exists(config_path):
        return

    config = configparser.ConfigParser()
    config.read(config_path)

    if 'API' in config:
        removed = False
        for key_name in ('OpenAI_Key', 'openai_key', 'openai_api_key'):
            if key_name in config['API']:
                del config['API'][key_name]
                removed = True
        if removed:
            if not config['API']:
                del config['API']
            with open(config_path, 'w') as configfile:
                config.write(configfile)
