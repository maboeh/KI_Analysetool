"""
Prompt library for KI Analysetool.

Provides reusable, well-tested prompt templates for common analysis tasks.
Beginners see an explanation with each prompt; experts see only the prompt text.
"""

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class PromptTemplate:
    """A single reusable prompt template."""

    id: str
    category: str
    title: str
    prompt: str
    description: str
    tags: List[str]
    difficulty: str  # "beginner", "intermediate", "expert"

    def format(self, content: str = "{text}") -> str:
        """Return the prompt with content inserted."""
        return self.prompt.format(text=content)


# Built-in prompt templates. The `{text}` placeholder is replaced with the actual content.
DEFAULT_PROMPTS: List[PromptTemplate] = [
    PromptTemplate(
        id="summary_short",
        category="Zusammenfassung",
        title="Kurze Zusammenfassung",
        prompt=(
            "Fasse den folgenden Text in maximal 3 Sätzen zusammen und nenne die wichtigsten "
            "Erkenntnisse:\n\n{text}"
        ),
        description=(
            "Gut für lange Texte oder Berichte. Die KI erstellt eine kurze, prägnante Zusammenfassung."
        ),
        tags=["zusammenfassung", "kurz"],
        difficulty="beginner"
    ),
    PromptTemplate(
        id="summary_detailed",
        category="Zusammenfassung",
        title="Detaillierte Zusammenfassung",
        prompt=(
            "Fasse den folgenden Text zusammen. Strukturiere das Ergebnis in: "
            "1. Hauptthese, 2. Wichtige Argumente, 3. Belege, 4. Fazit.\n\n{text}"
        ),
        description="Strukturierte, ausführliche Zusammenfassung für komplexe Inhalte.",
        tags=["zusammenfassung", "strukturiert"],
        difficulty="intermediate"
    ),
    PromptTemplate(
        id="keywords",
        category="Extraktion",
        title="Schlüsselwörter extrahieren",
        prompt=(
            "Extrahiere die 10 wichtigsten Schlüsselwörter und Fachbegriffe aus dem folgenden Text. "
            "Gib sie als nummerierte Liste mit einer kurzen Erklärung aus:\n\n{text}"
        ),
        description="Hilft, die zentralen Begriffe eines Textes schnell zu erfassen.",
        tags=["keywords", "begriffe"],
        difficulty="beginner"
    ),
    PromptTemplate(
        id="sentiment",
        category="Analyse",
        title="Sentiment-Analyse",
        prompt=(
            "Analysiere die emotionale Tonalität des folgenden Textes. "
            "Klassifiziere als positiv, neutral oder negativ und begründe deine Einschätzung:\n\n{text}"
        ),
       description="Prüft, ob ein Text eher positiv, neutral oder negativ klingt.",
        tags=["sentiment", "emotion"],
        difficulty="beginner"
    ),
    PromptTemplate(
        id="swot",
        category="Strategie",
        title="SWOT-Analyse",
        prompt=(
            "Führe eine SWOT-Analyse für den folgenden Text durch. "
            "Gib Stärken, Schwächen, Chancen und Risiken in einer übersichtlichen Tabelle aus:\n\n{text}"
        ),
        description="Strategische Analyse: Stärken, Schwächen, Chancen, Risiken.",
        tags=["swot", "strategie"],
        difficulty="intermediate"
    ),
    PromptTemplate(
        id="extract_numbers",
        category="Extraktion",
        title="Zahlen und Metriken extrahieren",
        prompt=(
            "Extrahiere alle Zahlen, Prozentsätze, Währungsbeträge und Metriken aus dem folgenden Text. "
            "Stelle sie in einer Tabelle mit Spalten 'Wert', 'Einheit', 'Kontext' dar:\n\n{text}"
        ),
        description="Nützlich, um aus Texten strukturierte Daten für Excel/Visualisierungen zu gewinnen.",
        tags=["daten", "zahlen", "metriken"],
        difficulty="intermediate"
    ),
    PromptTemplate(
        id="pros_cons",
        category="Analyse",
        title="Pro- und Contra-Analyse",
        prompt=(
            "Analysiere den folgenden Text und liste die wichtigsten Pro- und Contra-Argumente "
            "übersichtlich auf:\n\n{text}"
        ),
        description="Hilft bei der Entscheidungsfindung, indem Für und Wider gegeneinander abgewogen werden.",
        tags=["pro-contra", "entscheidung"],
        difficulty="beginner"
    ),
    PromptTemplate(
        id="explain_simple",
        category="Lernen",
        title="Einfach erklären",
        prompt=(
            "Erkläre den folgenden Text so, dass ein Anfänger ihn versteht. "
            "Vermeide Fachjargon oder erkläre ihn kurz:\n\n{text}"
        ),
        description="Macht komplexe Inhalte verständlich – ideal zum Lernen.",
        tags=["lernen", "einfach"],
        difficulty="beginner"
    ),
    PromptTemplate(
        id="action_items",
        category="Produktivität",
        title="Action Items extrahieren",
        prompt=(
            "Lies den folgenden Text und extrahiere konkrete Aufgaben, nächste Schritte oder "
            "Handlungsempfehlungen als Checkliste:\n\n{text}"
        ),
        description="Wandelt Besprechungsprotokolle oder Berichte in eine To-do-Liste um.",
        tags=["aufgaben", "todo", "next-steps"],
        difficulty="intermediate"
    ),
    PromptTemplate(
        id="compare_sources",
        category="Experten",
        title="Quellenvergleich",
        prompt=(
            "Vergleiche die in folgendem Text genannten Aussagen und Quellen miteinander. "
            "Hebe Übereinstimmungen, Widersprüche und offene Fragen hervor:\n\n{text}"
        ),
        description="Für Experten: Mehrere Quellen oder Argumente kritisch vergleichen.",
        tags=["vergleich", "quellen", "experte"],
        difficulty="expert"
    ),
]


class PromptLibrary:
    """Registry for prompt templates."""

    def __init__(self, templates: List[PromptTemplate] = None):
        self.templates = templates or DEFAULT_PROMPTS

    def all(self) -> List[PromptTemplate]:
        return self.templates

    def by_id(self, template_id: str) -> PromptTemplate:
        for template in self.templates:
            if template.id == template_id:
                return template
        raise KeyError(f"Prompt template '{template_id}' not found")

    def by_category(self) -> Dict[str, List[PromptTemplate]]:
        categories: Dict[str, List[PromptTemplate]] = {}
        for template in self.templates:
            categories.setdefault(template.category, []).append(template)
        return categories

    def for_difficulty(self, level: str) -> List[PromptTemplate]:
        """Return templates up to and including the given difficulty level."""
        order = {"beginner": 0, "intermediate": 1, "expert": 2}
        target = order.get(level, 0)
        return [t for t in self.templates if order.get(t.difficulty, 0) <= target]

    def to_menu_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        """Return prompts grouped by category for UI menus."""
        result: Dict[str, List[Dict[str, Any]]] = {}
        for category, templates in self.by_category().items():
            result[category] = [
                {"id": t.id, "title": t.title, "description": t.description, "difficulty": t.difficulty}
                for t in templates
            ]
        return result
