import os
from pathlib import Path
import configparser
from getpass import getpass


class APIKeyManager:
    def __init__(self, app_name, config_dir=None):
        self.app_name = app_name
        
        # Priorität: Explizites Verzeichnis > Projektverzeichnis > Home-Verzeichnis
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Suche im Projektverzeichnis
            project_config = Path(__file__).parent / "config_dir"
            if project_config.exists():
                self.config_dir = project_config
            else:
                # Fallback auf versteckten Ordner im Home-Verzeichnis
                self.config_dir = Path.home() / f".{app_name}"
                
        self.config_file = self.config_dir / "config.ini"
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """Stelle sicher, dass das Konfigurationsverzeichnis existiert."""
        if not self.config_dir.exists():
            self.config_dir.mkdir()

    def get_api_key(self):
        """Hole den API-Schlüssel aus verschiedenen Quellen."""
        # 1. Prüfe Umgebungsvariable
        env_key = os.environ.get("OPENAI_API_KEY")
        if env_key:
            return env_key

        # 2. Prüfe Konfigurationsdatei
        if self.config_file.exists():
            print(f"Verwende Konfiguration aus: {self.config_file}")
            config = configparser.ConfigParser()
            config.read(self.config_file)
            try:
                # Versuche zuerst den neuen Pfad (API/OpenAI_Key)
                if "API" in config and "OpenAI_Key" in config["API"]:
                    return config["API"]["OpenAI_Key"]
                # Versuche dann den alten Pfad (openai/openai_key)
                elif "openai" in config and "openai_key" in config["openai"]:
                    return config["openai"]["openai_key"]
                # Versuche weitere bekannte Varianten
                elif "API" in config and "openai_key" in config["API"]:
                    return config["API"]["openai_key"]
            except (configparser.NoSectionError, configparser.NoOptionError):
                pass  # Wenn Abschnitt oder Schlüssel nicht gefunden, fahre fort

        # 3. Frage Benutzer nach Schlüssel
        print(f"Kein API-Schlüssel für {self.app_name} gefunden.")
        choice = input("Möchtest du einen API-Schlüssel eingeben? (j/n): ")

        if choice.lower() in ["j", "ja", "y", "yes"]:
            api_key = getpass("Gib deinen OpenAI API-Schlüssel ein: ")
            save = input("Schlüssel für zukünftige Verwendung speichern? (j/n): ")

            if save.lower() in ["j", "ja", "y", "yes"]:
                self.save_api_key(api_key)

            return api_key

        return None

    def save_api_key(self, api_key):
        """Speichere den API-Schlüssel in der Konfigurationsdatei."""
        config = configparser.ConfigParser()
        if self.config_file.exists():
            config.read(self.config_file)

        if "API" not in config:
            config["API"] = {}

        config["API"]["OpenAI_Key"] = api_key  # Match the key name in config.py

        with open(self.config_file, "w") as f:
            config.write(f)

        # Setze Dateiberechtigungen (nur für den Benutzer lesbar)
        self.config_file.chmod(0o600)

        print(f"API-Schlüssel wurde in {self.config_file} gespeichert.")
