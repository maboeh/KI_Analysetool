"""
User profile and experience level management for KI Analysetool.

Stores per-user preferences (beginner/intermediate/expert mode, learning path
progress, onboarding state) in a platform-agnostic config directory.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any


@dataclass
class UserProfile:
    """Persistent user preferences and learning progress."""

    experience_level: str = "beginner"  # "beginner", "intermediate", "expert"
    onboarding_completed: bool = False
    onboarding_skipped: bool = False
    show_learning_panel: bool = True
    completed_tutorial_steps: List[str] = field(default_factory=list)
    completed_learning_event_ids: List[str] = field(default_factory=list)
    dismissed_help_ids: List[str] = field(default_factory=list)
    last_used_model: str = "gpt-4o"
    settings: Dict[str, Any] = field(default_factory=dict)

    def mark_onboarding_complete(self):
        self.onboarding_completed = True

    def complete_step(self, step_id: str):
        if step_id not in self.completed_tutorial_steps:
            self.completed_tutorial_steps.append(step_id)

    def is_step_completed(self, step_id: str) -> bool:
        return step_id in self.completed_tutorial_steps

    def dismiss_help(self, help_id: str):
        if help_id not in self.dismissed_help_ids:
            self.dismissed_help_ids.append(help_id)

    def is_help_dismissed(self, help_id: str) -> bool:
        return help_id in self.dismissed_help_ids

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserProfile":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class UserProfileManager:
    """Loads and saves the user profile to disk."""

    _instance: "UserProfileManager" = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_dir: Path = None):
        if self._initialized:
            return
        self._initialized = True

        if config_dir is None:
            config_dir = self._default_config_dir()
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.profile_path = self.config_dir / "user_profile.json"
        self._profile = self._load()

    @staticmethod
    def _default_config_dir() -> Path:
        """Return a platform-appropriate config directory."""
        if os.name == "nt":
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
            return base / "KI_Analysetool"
        if os.uname().sysname == "Darwin":
            return Path.home() / "Library" / "Application Support" / "KI_Analysetool"
        # Linux and other Unix
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        return base / "ki-analysetool"

    def _load(self) -> UserProfile:
        if not self.profile_path.exists():
            return UserProfile()
        try:
            with open(self.profile_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return UserProfile.from_dict(data)
        except (json.JSONDecodeError, OSError, TypeError):
            return UserProfile()

    def save(self):
        """Persist the current profile to disk."""
        try:
            with open(self.profile_path, "w", encoding="utf-8") as f:
                json.dump(self._profile.to_dict(), f, ensure_ascii=False, indent=2)
        except OSError as e:
            import logging
            logging.getLogger(__name__).warning("Konnte Benutzerprofil nicht speichern: %s", e)

    @property
    def profile(self) -> UserProfile:
        return self._profile

    def set_experience_level(self, level: str):
        if level not in ("beginner", "intermediate", "expert"):
            raise ValueError(f"Ungültiger Erfahrungsgrad: {level}")
        self._profile.experience_level = level
        self.save()

    def complete_onboarding(self):
        self._profile.mark_onboarding_complete()
        self._profile.onboarding_skipped = False
        self.save()

    def skip_onboarding(self):
        self._profile.onboarding_skipped = True
        self.save()

    def set_learning_panel_visibility(self, visible: bool):
        self._profile.show_learning_panel = bool(visible)
        self.save()

    def mark_learning_event_handled(self, event_id: str):
        if event_id not in self._profile.completed_learning_event_ids:
            self._profile.completed_learning_event_ids.append(event_id)
            self._profile.completed_learning_event_ids = self._profile.completed_learning_event_ids[-500:]
            self.save()

    def set_setting(self, key: str, value: Any):
        self._profile.settings[key] = value
        self.save()

    def get_setting(self, key: str, default: Any = None) -> Any:
        return self._profile.settings.get(key, default)

    def set_session_budget(self, limit_usd):
        """Persistiert ein optionales Sitzungsbudget in USD (None/0 = unbegrenzt)."""
        self.set_setting("session_budget_usd", limit_usd if limit_usd else None)

    def get_session_budget(self):
        """Gibt das gespeicherte Sitzungsbudget in USD zurück (oder None)."""
        value = self.get_setting("session_budget_usd")
        if isinstance(value, (int, float)) and value > 0:
            return float(value)
        return None

    def set_privacy_check_enabled(self, enabled: bool):
        self.set_setting("privacy_check_enabled", bool(enabled))

    def get_privacy_check_enabled(self) -> bool:
        """Datenschutzprüfung vor externer Übertragung (Standard: an)."""
        return bool(self.get_setting("privacy_check_enabled", True))

    def complete_step(self, step_id: str):
        self._profile.complete_step(step_id)
        self.save()

    def dismiss_help(self, help_id: str):
        self._profile.dismiss_help(help_id)
        self.save()


def get_user_profile() -> UserProfile:
    """Convenience accessor for the singleton profile manager."""
    return UserProfileManager().profile
