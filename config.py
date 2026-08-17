import configparser
import os
import sys
import logging

logger = logging.getLogger(__name__)

CURRENT_API_KEY = None

try:
    import keyring
    KEYRING_AVAILABLE = True
    KEYRING_SERVICE = "KI_Analysetool"
    KEYRING_USERNAME = "openai_api_key"
except ImportError:
    KEYRING_AVAILABLE = False

def get_config_path():
    """Gibt den absoluten Pfad zur Konfigurationsdatei zurück (relativ zu dieser Datei)."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')

def check_api_key_exists():
    """Prüft, ob ein API-Key im Keyring, in der Umgebungsvariable oder Konfigurationsdatei existiert."""
    global CURRENT_API_KEY

    if KEYRING_AVAILABLE:
        key = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
        if key:
            CURRENT_API_KEY = key
            return True

    if 'OPENAI_API_KEY' in os.environ and os.environ['OPENAI_API_KEY']:
        CURRENT_API_KEY = os.environ['OPENAI_API_KEY']
        return True

    config_path = get_config_path()
    if os.path.exists(config_path):
        config = configparser.ConfigParser()
        config.read(config_path)
        if 'API' in config and 'OpenAI_Key' in config['API'] and config['API']['OpenAI_Key']:
            CURRENT_API_KEY = config['API']['OpenAI_Key']
            return True

    return False

def save_api_key(key):
    """Speichert den API-Key sicher im OS-Keyring mit Fallback auf config.ini."""
    global CURRENT_API_KEY

    CURRENT_API_KEY = key

    if KEYRING_AVAILABLE:
        try:
            keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, key)
            _migrate_key_from_config_ini()
            return
        except Exception as e:
            logger.warning(f"Keyring-Speicherung fehlgeschlagen, falle auf config.ini zurück: {e}")

    config = configparser.ConfigParser()
    config_path = get_config_path()

    if os.path.exists(config_path):
        config.read(config_path)

    if 'API' not in config:
        config['API'] = {}

    config['API']['OpenAI_Key'] = key

    with open(config_path, 'w') as configfile:
        config.write(configfile)
        configfile.flush()
        os.fsync(configfile.fileno())
    os.chmod(config_path, 0o600)

def get_api_key():
    """Liest den API-Key aus der Konfigurationsdatei oder Umgebungsvariable."""
    global CURRENT_API_KEY

    # Falls schon im Speicher, direkt zurückgeben
    if CURRENT_API_KEY:
        return CURRENT_API_KEY

    # Sonst versuchen zu laden
    if check_api_key_exists():
        return CURRENT_API_KEY

    # Interaktive Abfrage nur im CLI-Modus
    if not sys.stdin.isatty():
        return None

    print("Kein API-Schlüssel gefunden.")
    choice = input("Möchtest du einen API-Schlüssel eingeben? (j/n): ")

    if choice.lower() in ["j", "ja", "y", "yes"]:
        from getpass import getpass
        api_key = getpass("Gib deinen OpenAI API-Schlüssel ein: ")
        save = input("Schlüssel für zukünftige Verwendung speichern? (j/n): ")

        if save.lower() in ["j", "ja", "y", "yes"]:
            save_api_key(api_key)
        else:
            CURRENT_API_KEY = api_key

        return api_key

    return None


def _migrate_key_from_config_ini():
    """Entfernt den API-Key aus config.ini, wenn er erfolgreich im Keyring gespeichert wurde."""
    config_path = get_config_path()
    if not os.path.exists(config_path):
        return

    config = configparser.ConfigParser()
    config.read(config_path)

    if 'API' in config and 'OpenAI_Key' in config['API']:
        del config['API']['OpenAI_Key']
        if not config['API']:
            del config['API']
        with open(config_path, 'w') as configfile:
            config.write(configfile)
