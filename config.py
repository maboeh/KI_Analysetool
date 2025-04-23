import configparser
import os

CURRENT_API_KEY = None

def check_api_key_exists():

    global CURRENT_API_KEY
    """Prüft, ob ein API-Key in der Konfigurationsdatei oder als Umgebungsvariable existiert."""
    # Prüfen auf Umgebungsvariable
    if 'OPENAI_API_KEY' in os.environ and os.environ['OPENAI_API_KEY']:
        CURRENT_API_KEY = os.environ['OPENAI_API_KEY']
        return True

    # Prüfen auf Konfigurationsdatei
    config = configparser.ConfigParser()
    if os.path.exists('config.ini'):
        config.read('config.ini')
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
    config_path = os.path.abspath('config.ini')

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

def get_api_key():
    """Liest den API-Key aus der Konfigurationsdatei oder Umgebungsvariable."""
    # Prüfen auf Umgebungsvariable
    if 'OPENAI_API_KEY' in os.environ:
        return os.environ['OPENAI_API_KEY']

    # Prüfen auf Konfigurationsdatei
    config = configparser.ConfigParser()
    if os.path.exists('config.ini'):
        config.read('config.ini')
        if 'API' in config and 'OpenAI_Key' in config['API']:
            return config['API']['OpenAI_Key']

    return None



