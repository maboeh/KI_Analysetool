"""
Learning path system for KI Analysetool.

Defines a sequence of discoverable steps that guide a beginner from the first
analysis to advanced workflows. Progress is persisted through UserProfile.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Callable, Any

from user_profile import UserProfileManager


@dataclass
class LearningStep:
    """A single step in the learning path."""

    id: str
    title: str
    description: str
    help_text: str
    condition: Optional[Callable[[], bool]] = None
    next_step_id: Optional[str] = None


# Default learning path. Steps are designed to be completed in order.
DEFAULT_LEARNING_STEPS: List[LearningStep] = [
    LearningStep(
        id="first_analysis",
        title="Erste Analyse durchführen",
        description="Führe eine beliebige Analyse durch, um das Tool kennenzulernen.",
        help_text=(
            "Wähle den Tab 'Text', gib einen kurzen Text ein, wähle 'Zusammenfassung' "
            "und klicke auf 'Frage senden'."
        ),
        next_step_id="try_follow_up"
    ),
    LearningStep(
        id="try_follow_up",
        title="Eine Folgeaktion ausprobieren",
        description="Nutze eine Folgeaktion wie 'Zusammenfassen' oder 'Vertiefen'.",
        help_text=(
            "Nach der ersten Analyse erscheinen rechts Buttons wie 'Zusammenfassen' oder 'Vertiefen'. "
            "Klicke auf einen davon, um das Ergebnis weiter zu verarbeiten."
        ),
        next_step_id="analyze_file"
    ),
    LearningStep(
        id="analyze_file",
        title="Eine Datei analysieren",
        description="Lade ein PDF, Excel, CSV oder Bild hoch und analysiere es.",
        help_text=(
            "Wähle einen der erweiterten Tabs (Excel, Bild/PDF, CSV/Text oder Multi-Datei), "
            "lade eine Datei hoch und starte die Analyse."
        ),
        next_step_id="extract_data"
    ),
    LearningStep(
        id="extract_data",
        title="Daten extrahieren",
        description="Extrahiere strukturierte Daten aus einem Analyseergebnis.",
        help_text=(
            "Wenn das Ergebnis Zahlen oder Tabellen enthält, klicke auf 'Daten extrahieren' "
            "oder verwende das Kontextmenü."
        ),
        next_step_id="visualize"
    ),
    LearningStep(
        id="visualize",
        title="Eine Visualisierung erstellen",
        description="Erstelle ein Diagramm aus den extrahierten Daten.",
        help_text=(
            "Wechsle zum Tab 'Visualisierung', wähle einen Diagrammtyp und klicke auf 'Erstellen'. "
            "Du kannst das Diagramm anschließend exportieren."
        ),
        next_step_id="export_excel"
    ),
    LearningStep(
        id="export_excel",
        title="Ergebnis als Excel exportieren",
        description="Exportiere die extrahierten Daten in eine Excel-Datei.",
        help_text=(
            "Wechsle zum Tab 'Datenexport' und klicke auf 'Excel exportieren'. "
            "Wähle einen Speicherort und speichere die Datei."
        ),
        next_step_id="save_result"
    ),
    LearningStep(
        id="save_result",
        title="Ergebnis mit Tags speichern",
        description="Speichere ein Ergebnis und versehe es mit Tags.",
        help_text=(
            "Nutze 'Ergebnisse verwalten' oder das Menü 'Tags verwalten', um ein Ergebnis "
            "mit aussagekräftigen Tags zu versehen."
        ),
        next_step_id="compare_results"
    ),
    LearningStep(
        id="compare_results",
        title="Mehrere Ergebnisse vergleichen",
        description="Vergleiche zwei oder mehr gespeicherte Ergebnisse.",
        help_text=(
            "Öffne den 'Ergebnisverlauf', wähle mehrere Einträge aus und nutze die rechte Maustaste "
            "zum Vergleichen."
        ),
        next_step_id="custom_prompt"
    ),
    LearningStep(
        id="custom_prompt",
        title="Eigenen Prompt schreiben",
        description="Nutze die Prompt-Vorlagen oder schreibe eine eigene Anfrage.",
        help_text=(
            "Wähle im Dropdown 'Prompt senden' und gib im Prompt-Feld eine eigene Frage ein. "
            "Nutze {text} als Platzhalter für den Inhalt."
        ),
        next_step_id=None
    ),
]


class LearningPath:
    """Manages the learning path state and progression."""

    def __init__(self, steps: List[LearningStep] = None,
                 profile_manager: UserProfileManager = None):
        self.steps = steps or DEFAULT_LEARNING_STEPS
        self._profile_manager = profile_manager or UserProfileManager()
        self._step_map = {step.id: step for step in self.steps}

    @property
    def completed_steps(self) -> List[str]:
        return self._profile_manager.profile.completed_tutorial_steps

    def is_completed(self, step_id: str) -> bool:
        return step_id in self.completed_steps

    def complete(self, step_id: str):
        if step_id not in self._step_map:
            raise ValueError(f"Unbekannter Lernpfad-Schritt: {step_id}")
        if not self.is_completed(step_id):
            self._profile_manager.complete_step(step_id)

    def get_step(self, step_id: str) -> Optional[LearningStep]:
        return self._step_map.get(step_id)

    def current_step(self) -> Optional[LearningStep]:
        """Return the first step that is not yet completed."""
        for step in self.steps:
            if not self.is_completed(step.id):
                return step
        return None

    def progress(self) -> Dict[str, Any]:
        total = len(self.steps)
        completed = len(self.completed_steps)
        current = self.current_step()
        return {
            "total": total,
            "completed": completed,
            "percent": int((completed / total) * 100) if total else 0,
            "current_step": current,
            "all_done": current is None
        }

    def reset(self):
        self._profile_manager.profile.completed_tutorial_steps.clear()
        self._profile_manager.save()

    def to_ui_items(self) -> List[Dict[str, Any]]:
        """Return a list of dicts suitable for rendering a checklist UI."""
        items = []
        for step in self.steps:
            items.append({
                "id": step.id,
                "title": step.title,
                "description": step.description,
                "help_text": step.help_text,
                "completed": self.is_completed(step.id),
                "next_step_id": step.next_step_id
            })
        return items
