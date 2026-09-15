"""Zentrales Befehlsregister für Menüs, Tastenkürzel und die Befehlspalette.

Befehle werden einmal als :class:`Command` registriert und von dort für
Menüaufbau, globale Shortcuts und die Befehlspalette (Suche) genutzt.
Shortcuts werden kanonisch als ``"Ctrl+Shift+E"`` notiert (immer ``Ctrl``);
``tk_binding`` bildet sie auf plattformspezifische Tk-Sequenzen ab
(auf macOS zusätzlich die ⌘-Variante), ``accelerator_label`` erzeugt die
Anzeigeform für Menüeinträge.
"""

import sys
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass(frozen=True)
class Command:
    """Ein registrierbarer Anwendungsbefehl.

    id:            eindeutige ID, z. B. ``"results.manage"``
    label:         sichtbarer Menütext
    category:      z. B. "Ergebnisse", "Export", "Arbeitsbereich",
                   "Qualität", "Hilfe", "Ansicht", "Analyse"
    callback:      auszuführende Aktion ohne Argumente
    shortcut:      kanonisch "Ctrl+Shift+E" (Mapping auf ⌘ macht die GUI)
    requires_result: nur sinnvoll, wenn ein aktuelles Ergebnis existiert
    keywords:      zusätzliche Suchbegriffe für die Befehlspalette
    """
    id: str
    label: str
    category: str
    callback: Callable[[], None]
    shortcut: Optional[str] = None
    requires_result: bool = False
    keywords: tuple = ()


class CommandRegistry:
    """Registriert Befehle und liefert sie für Menüs, Shortcuts und Suche."""

    def __init__(self):
        self._commands = {}
        self._order = []

    def register(self, command: Command) -> None:
        """Registriert einen Befehl; ValueError bei doppelter ID."""
        if command.id in self._commands:
            raise ValueError(f"Befehl bereits registriert: {command.id}")
        self._commands[command.id] = command
        self._order.append(command.id)

    def get(self, command_id: str) -> Optional[Command]:
        return self._commands.get(command_id)

    def all(self) -> list:
        """Alle Befehle in stabiler Registrierungsreihenfolge."""
        return [self._commands[command_id] for command_id in self._order]

    def by_category(self) -> dict:
        """Befehle gruppiert nach Kategorie (Reihenfolge = erste Nutzung)."""
        grouped = {}
        for command in self.all():
            grouped.setdefault(command.category, []).append(command)
        return grouped

    def search(self, query: str, limit: int = 12) -> list:
        """Durchsucht Befehle fuzzy nach Label, Kategorie und Keywords.

        Leerer Query liefert alle Befehle (bis limit). Scoring:
        Substring im Label = 100 (+ Prefix-Bonus), Treffer in Keywords
        oder Kategorie = 60, Subsequenz über das Label = 30 minus
        Spread-Strafe. Score 0 fliegt raus. Sortiert nach Score,
        dann Registrierungsreihenfolge.
        """
        query = (query or "").strip()
        if not query:
            return self.all()[:limit]
        needle = query.casefold()
        scored = []
        for position, command in enumerate(self.all()):
            score = self._score(command, needle)
            if score > 0:
                scored.append((score, position, command))
        scored.sort(key=lambda item: (-item[0], item[1]))
        return [command for _score, _pos, command in scored[:limit]]

    @staticmethod
    def _score(command: Command, needle: str) -> int:
        label = command.label.casefold()
        score = 0
        if needle in label:
            score = 100
            if label.startswith(needle):
                score += 20
            elif any(word.startswith(needle) for word in label.split()):
                score += 10
        haystacks = [command.category.casefold()]
        haystacks.extend(keyword.casefold() for keyword in command.keywords)
        if any(needle in haystack for haystack in haystacks):
            score = max(score, 60)
        subsequence = CommandRegistry._subsequence_score(label, needle)
        return max(score, subsequence)

    @staticmethod
    def _subsequence_score(label: str, needle: str) -> int:
        """Subsequenz-Match: alle Query-Zeichen in Reihenfolge im Label.

        Score 30 minus Spread-Strafe (Abstand zwischen erstem und letztem
        Treffer relativ zur Query-Länge), mindestens 1. 0 bei keinem Match.
        """
        position = -1
        first = -1
        for char in needle:
            position = label.find(char, position + 1)
            if position == -1:
                return 0
            if first == -1:
                first = position
        spread = (position - first + 1) - len(needle)
        return max(30 - spread, 1)


_MODIFIER_NAMES = {
    "ctrl": "Control",
    "control": "Control",
    "shift": "Shift",
    "alt": "Alt",
    "option": "Alt",
    "cmd": "Command",
    "command": "Command",
    "meta": "Command",
}

_MODIFIER_DISPLAY = {
    "ctrl": "Ctrl",
    "control": "Ctrl",
    "shift": "Shift",
    "alt": "Alt",
    "option": "Alt",
    "cmd": "Cmd",
    "command": "Cmd",
    "meta": "Cmd",
}

_PUNCTUATION_KEYSYMS = {
    ",": "comma",
    ".": "period",
    "/": "slash",
    "\\": "backslash",
    ";": "semicolon",
    "'": "apostrophe",
    "`": "grave",
    "-": "minus",
    "=": "equal",
    "[": "bracketleft",
    "]": "bracketright",
    " ": "space",
    "<": "less",
    ">": "greater",
}

_MAC_KEY_LABELS = {
    "Return": "↩",
    "Enter": "↩",
    "Escape": "⎋",
    "Esc": "⎋",
    "Tab": "⇥",
    "BackSpace": "⌫",
    "Delete": "⌦",
    "Space": "␣",
}

_DISPLAY_KEY_LABELS = {
    "return": "Enter",
    "escape": "Esc",
    "esc": "Esc",
    "backspace": "Backspace",
    "space": "Leertaste",
}


def _split_shortcut(shortcut: str):
    """Zerlegt "Ctrl+Shift+E" in (["Ctrl", "Shift"], "E")."""
    parts = shortcut.split("+")
    if len(parts) < 2 or not parts[-1]:
        raise ValueError(f"Ungültiger Shortcut: {shortcut!r}")
    return parts[:-1], parts[-1]


def _keysym(key: str, shift: bool) -> str:
    """Bildet den Tk-Keysym: Shift → Großbuchstabe, sonst klein;
    benannte Tasten (Return, F1, ...) bleiben unverändert."""
    if len(key) > 1:
        return key
    mapped = _PUNCTUATION_KEYSYMS.get(key)
    if mapped is not None:
        return mapped
    if shift and key.isalpha():
        return key.upper()
    return key.lower()


def tk_binding(shortcut: str, platform: Optional[str] = None) -> list:
    """Wandelt einen kanonischen Shortcut in Tk-Bind-Sequenzen um.

    "Ctrl+K" → darwin: ["<Command-k>", "<Control-k>"],
    sonst ["<Control-k>"]. Auf macOS werden ⌘- und Ctrl-Variante
    gebunden, damit beide funktionieren.
    """
    if platform is None:
        platform = sys.platform
    modifiers, key = _split_shortcut(shortcut)
    tk_modifiers = [_MODIFIER_NAMES.get(mod.casefold(), mod) for mod in modifiers]
    keysym = _keysym(key, "Shift" in tk_modifiers)

    sequences = []
    if platform == "darwin" and "Control" in tk_modifiers:
        darwin_modifiers = [
            "Command" if mod == "Control" else mod for mod in tk_modifiers
        ]
        sequences.append("<" + "-".join(darwin_modifiers + [keysym]) + ">")
    sequences.append("<" + "-".join(tk_modifiers + [keysym]) + ">")
    return sequences


def accelerator_label(shortcut: str, platform: Optional[str] = None) -> str:
    """Liefert die Anzeigeform eines Shortcuts für Menüeinträge.

    darwin → "⌘K", "⇧⌘E", "⌘↩"; sonst "Ctrl+K", "Ctrl+Shift+E", "Ctrl+Enter".
    """
    if platform is None:
        platform = sys.platform
    modifiers, key = _split_shortcut(shortcut)
    lowered = {mod.casefold() for mod in modifiers}

    if platform == "darwin":
        symbols = ""
        if lowered & {"alt", "option"}:
            symbols += "⌥"
        if "shift" in lowered:
            symbols += "⇧"
        if lowered & {"ctrl", "control", "cmd", "command", "meta"}:
            symbols += "⌘"
        key_label = _MAC_KEY_LABELS.get(key, key if len(key) == 1 else key.upper())
        if len(key) == 1:
            key_label = key.upper()
        return symbols + key_label

    names = [_MODIFIER_DISPLAY.get(mod.casefold(), mod) for mod in modifiers]
    key_label = _DISPLAY_KEY_LABELS.get(
        key.casefold(), key.upper() if len(key) == 1 else key)
    return "+".join(names + [key_label])
