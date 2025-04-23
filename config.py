import configparser
import os

CURRENT_API_KEY = None

def get_config_path():
    """Gibt den absoluten Pfad zur Konfigurationsdatei zurück."""
    return os.path.abspath('config.ini')

def check_api_key_exists():

    global CURRENT_API_KEY
    """Prüft, ob ein API-Key in der Konfigurationsdatei oder als Umgebungsvariable existiert."""
    # Prüfen auf Umgebungsvariable
    if 'OPENAI_API_KEY' in os.environ and os.environ['OPENAI_API_KEY']:
        CURRENT_API_KEY = os.environ['OPENAI_API_KEY']
        return True

    # Prüfen auf Konfigurationsdatei
    config_path = get_config_path()
    if os.path.exists(config_path):
        config = configparser.ConfigParser()
        config.read(config_path)
        if 'API' in config and 'OpenAI_Key' in config['API'] and config['API']['OpenAI_Key']:
            CURRENT_API_KEY = config['API']['OpenAI_Key']
            os.environ['OPENAI_API_KEY'] = CURRENT_API_KEY
            return True

    return False

def save_api_key(key):
    """Speichert den API-Key in der Konfigurationsdatei."""
    global CURRENT_API_KEY

    CURRENT_API_KEY = key
    os.environ['OPENAI_API_KEY'] = key

    config = configparser.ConfigParser()

    # Absoluten Pfad zur Konfigurationsdatei verwenden
    config_path = get_config_path()

    # Existierende Konfiguration laden, falls vorhanden
    if os.path.exists(config_path):
        config.read(config_path)

    # API-Sektion erstellen, falls nicht vorhanden
    if 'API' not in config:
        config['API'] = {}

    # API-Key setzen
    config['API']['OpenAI_Key'] = key

    # In Datei schreiben
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
        configfile.flush()
        os.fsync(configfile.fileno())
    # Berechtigungen setzen (nur Benutzer darf lesen/schreiben)
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

    # Interaktive Abfrage als letzter Ausweg
    print("Kein API-Schlüssel gefunden.")
    choice = input("Möchtest du einen API-Schlüssel eingeben? (j/n): ")

    if choice.lower() in ["j", "ja", "y", "yes"]:
        from getpass import getpass
        api_key = getpass("Gib deinen OpenAI API-Schlüssel ein: ")
        save = input("Schlüssel für zukünftige Verwendung speichern? (j/n): ")

        if save.lower() in ["j", "ja", "y", "yes"]:
            save_api_key(api_key)
        else:
            # Nur für diese Sitzung speichern
            CURRENT_API_KEY = api_key
            os.environ['OPENAI_API_KEY'] = api_key

        return api_key

    return None



