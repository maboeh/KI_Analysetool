"""
Action Buttons Frame for KI Analysetool

This module provides an interactive action buttons frame that generates dynamic buttons
for follow-up actions based on result content, including Zusammenfassen, Vertiefen, 
Übersetzen, and other context-sensitive actions.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass
from enum import Enum
import re

try:
    from data_models import Action as DataAction
except ImportError:
    DataAction = None

from help_tooltip import add_help_indicator


class ActionType(Enum):
    """Enumeration of available action types"""
    ZUSAMMENFASSEN = "zusammenfassen"
    VERTIEFEN = "vertiefen"
    UEBERSETZEN = "uebersetzen"
    ANALYSIEREN = "analysieren"
    EXPORTIEREN = "exportieren"
    VISUALISIEREN = "visualisieren"
    VERGLEICHEN = "vergleichen"
    CUSTOM = "custom"


@dataclass
class ActionButton:
    """Represents an action button configuration"""
    action_type: ActionType
    label: str
    description: str
    icon: Optional[str] = None
    enabled: bool = True
    callback: Optional[Callable] = None
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


class ActionButtonsFrame(ttk.Frame):
    """
    Interactive action buttons frame for follow-up actions on analysis results.
    
    Features:
    - Dynamic button generation based on content analysis
    - Context-sensitive action suggestions
    - Customizable action handlers
    - Context menu for additional actions
    - Action history and undo functionality
    """
    
    def __init__(self, parent, on_action_callback: Optional[Callable] = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Configuration
        self.on_action_callback = on_action_callback
        self.current_content = ""
        self.content_type = "text"
        self.action_history: List[Dict] = []
        self.available_actions: List[ActionButton] = []
        
        # UI Components
        self.buttons_frame = None
        self.context_menu = None
        
        # Setup the frame
        self._setup_frame()
        self._create_default_actions()
    
    def _setup_frame(self):
        """Setup the main frame components"""
        # Title label with help
        title_frame = ttk.Frame(self)
        title_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.title_label = ttk.Label(title_frame, text="Folgeaktionen:", 
                                   font=("Segoe UI", 10, "bold"))
        self.title_label.pack(side=tk.LEFT)
        
        add_help_indicator(title_frame,
                          "Schnellzugriff auf weitere KI-Analysen. "
                          "Wählen Sie z. B. Zusammenfassen, Vertiefen, Übersetzen oder Analysieren. "
                          "Einige Aktionen sind erst nach einer durchgeführten Analyse verfügbar.")
        
        # Main buttons container (vertical stack)
        self.buttons_frame = ttk.Frame(self)
        self.buttons_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Bottom button bar for history and more actions
        bottom_bar = ttk.Frame(self)
        bottom_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))
        
        # History button
        history_frame = ttk.Frame(bottom_bar)
        history_frame.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        self.history_btn = ttk.Button(history_frame, text="Verlauf",
                                    command=self._show_history)
        self.history_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        add_help_indicator(history_frame,
                          "Zeigt den Verlauf der zuletzt ausgeführten Folgeaktionen an.")
        
        # Additional actions button
        more_frame = ttk.Frame(bottom_bar)
        more_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.more_actions_btn = ttk.Button(more_frame, text="Weitere Aktionen ▼",
                                         command=self._show_context_menu)
        self.more_actions_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        add_help_indicator(more_frame,
                          "Öffnet ein Menü mit weiteren Aktionen: Daten extrahieren, "
                          "Visualisierung erstellen, in Zwischenablage kopieren, als PDF exportieren, "
                          "ähnliche Inhalte finden und Tags hinzufügen.")
        
        # Create context menu
        self._create_context_menu()
    
    def _create_default_actions(self):
        """Create the default set of action buttons"""
        default_actions = [
            ActionButton(
                action_type=ActionType.ZUSAMMENFASSEN,
                label="Zusammenfassen",
                description="Erstelle eine prägnante Zusammenfassung des Inhalts",
                callback=self._handle_zusammenfassen
            ),
            ActionButton(
                action_type=ActionType.VERTIEFEN,
                label="Vertiefen",
                description="Analysiere den Inhalt detaillierter",
                callback=self._handle_vertiefen
            ),
            ActionButton(
                action_type=ActionType.UEBERSETZEN,
                label="Übersetzen",
                description="Übersetze den Inhalt in eine andere Sprache",
                callback=self._handle_uebersetzen
            ),
            ActionButton(
                action_type=ActionType.ANALYSIEREN,
                label="Analysieren",
                description="Führe eine spezifische Analyse durch",
                callback=self._handle_analysieren
            )
        ]
        
        self.available_actions = default_actions
    
    def _create_context_menu(self):
        """Create the context menu for additional actions"""
        self.context_menu = tk.Menu(self, tearoff=0)
        
        # Add context menu items
        self.context_menu.add_command(label="📊 Daten extrahieren",
                                    command=lambda: self._execute_action("extract_data"))
        self.context_menu.add_command(label="📈 Visualisierung erstellen",
                                    command=lambda: self._execute_action("create_visualization"))
        self.context_menu.add_command(label="📋 In Zwischenablage kopieren",
                                    command=lambda: self._execute_action("copy_to_clipboard"))
        self.context_menu.add_command(label="💾 Als PDF exportieren",
                                    command=lambda: self._execute_action("export_pdf"))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🔍 Ähnliche Inhalte finden",
                                    command=lambda: self._execute_action("find_similar"))
        self.context_menu.add_command(label="🏷️ Tags hinzufügen",
                                    command=lambda: self._execute_action("add_tags"))
    
    def update_content(self, content: str, content_type: str = "text"):
        """
        Update the current content and refresh available actions
        
        Args:
            content: The content to analyze for action suggestions
            content_type: Type of content (text, markdown, structured, etc.)
        """
        self.current_content = content
        self.content_type = content_type
        
        # Analyze content and update action availability
        self._analyze_content_for_actions()
        self._refresh_buttons()
    
    def update_actions(self, actions: List[Any]):
        """
        Merge additional actions into the default action set.
        Supports both action_buttons.ActionButton and data_models.Action objects.
        Default actions (Zusammenfassen, Vertiefen, Übersetzen, Analysieren)
        are preserved so the user always sees the primary options.
        """
        if not actions:
            self._refresh_buttons()
            return
        
        existing_types = {a.action_type for a in self.available_actions}
        
        for action in actions:
            if isinstance(action, ActionButton):
                if action.action_type not in existing_types:
                    self.available_actions.append(action)
                    existing_types.add(action.action_type)
            elif DataAction is not None and isinstance(action, DataAction):
                action_value = action.action_type.value if hasattr(action.action_type, 'value') else str(action.action_type)
                # Normalize umlaut variants (übersetzen -> uebersetzen) for this module
                action_value = action_value.replace("ü", "ue").replace("Ü", "Ue")
                
                try:
                    at = ActionType(action_value)
                except ValueError:
                    at = ActionType.CUSTOM
                
                if at not in existing_types:
                    self.available_actions.append(ActionButton(
                        action_type=at,
                        label=action.label,
                        description=action.description,
                        parameters=action.parameters,
                        enabled=action.enabled
                    ))
                    existing_types.add(at)
        
        self._refresh_buttons()
    
    def _analyze_content_for_actions(self):
        """Analyze current content to determine which actions should be available"""
        if not self.current_content:
            # Disable all actions if no content
            for action in self.available_actions:
                action.enabled = False
            return
        
        content_lower = self.current_content.lower()
        content_length = len(self.current_content)
        
        # Enable/disable actions based on content analysis
        for action in self.available_actions:
            if action.action_type == ActionType.ZUSAMMENFASSEN:
                # Enable if content is long enough to summarize
                action.enabled = content_length > 200
                
            elif action.action_type == ActionType.VERTIEFEN:
                # Enable if content seems to have topics that can be expanded
                action.enabled = self._has_expandable_topics(self.current_content)
                
            elif action.action_type == ActionType.UEBERSETZEN:
                # Always enable translation
                action.enabled = content_length > 10
                
            elif action.action_type == ActionType.ANALYSIEREN:
                # Enable if content has analyzable elements
                action.enabled = self._has_analyzable_content(self.current_content)
        
        # Add dynamic actions based on content
        self._add_dynamic_actions()
    
    def _has_expandable_topics(self, content: str) -> bool:
        """Check if content has topics that can be expanded upon"""
        # Look for keywords that suggest expandable topics (German and English)
        expandable_keywords = [
            "konzept", "concept", "theorie", "theory", "methode", "method", 
            "ansatz", "approach", "strategie", "strategy",
            "problem", "lösung", "solution", "herausforderung", "challenge", 
            "trend", "entwicklung", "development"
        ]
        
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in expandable_keywords)
    
    def _has_analyzable_content(self, content: str) -> bool:
        """Check if content has elements suitable for analysis"""
        # Look for numbers, dates, names, or structured data
        has_numbers = bool(re.search(r'\d+', content))
        has_dates = bool(re.search(r'\d{1,2}[./]\d{1,2}[./]\d{4}', content))
        has_lists = bool(re.search(r'^\s*[-*•]\s', content, re.MULTILINE))
        has_structure = bool(re.search(r'^#{1,6}\s', content, re.MULTILINE))
        
        return has_numbers or has_dates or has_lists or has_structure
    
    def _add_dynamic_actions(self):
        """Add dynamic actions based on content analysis"""
        # Remove existing dynamic actions
        self.available_actions = [a for a in self.available_actions 
                                if a.action_type != ActionType.CUSTOM]
        
        # Add content-specific actions
        if self._contains_numerical_data():
            self.available_actions.append(
                ActionButton(
                    action_type=ActionType.CUSTOM,
                    label="Daten analysieren",
                    description="Analysiere numerische Daten im Inhalt",
                    callback=lambda: self._execute_action("analyze_data")
                )
            )
        
        if self._contains_code():
            self.available_actions.append(
                ActionButton(
                    action_type=ActionType.CUSTOM,
                    label="Code erklären",
                    description="Erkläre den Code-Inhalt",
                    callback=lambda: self._execute_action("explain_code")
                )
            )
        
        if self._contains_references():
            self.available_actions.append(
                ActionButton(
                    action_type=ActionType.CUSTOM,
                    label="Quellen prüfen",
                    description="Überprüfe und erweitere Quellenangaben",
                    callback=lambda: self._execute_action("check_sources")
                )
            )
    
    def _contains_numerical_data(self) -> bool:
        """Check if content contains numerical data"""
        # Look for numbers, percentages, currencies
        patterns = [
            r'\d+[.,]\d+',  # Decimal numbers
            r'\d+%',        # Percentages
            r'€\s*\d+',     # Euro amounts
            r'\$\s*\d+',    # Dollar amounts
        ]
        
        return any(re.search(pattern, self.current_content) for pattern in patterns)
    
    def _contains_code(self) -> bool:
        """Check if content contains code snippets"""
        # Look for code indicators
        code_indicators = [
            r'```',                    # Code blocks
            r'`[^`]+`',               # Inline code
            r'def\s+\w+\s*\(',        # Python functions
            r'function\s+\w+\s*\(',   # JavaScript functions
            r'class\s+\w+',           # Class definitions
        ]
        
        return any(re.search(pattern, self.current_content) for pattern in code_indicators)
    
    def _contains_references(self) -> bool:
        """Check if content contains references or citations"""
        # Look for reference patterns
        ref_patterns = [
            r'\[\d+\]',               # Numbered references
            r'http[s]?://\S+',        # URLs
            r'doi:\s*\S+',            # DOI references
            r'\(\w+\s+et\s+al\.',     # Academic citations
        ]
        
        return any(re.search(pattern, self.current_content) for pattern in ref_patterns)
    
    def _refresh_buttons(self):
        """Refresh the display of action buttons"""
        # Clear existing buttons
        for widget in self.buttons_frame.winfo_children():
            widget.destroy()
        
        # Show the first available actions (up to 6) stacked vertically.
        # Even disabled actions are rendered so the user sees what is possible.
        main_actions = self.available_actions[:6]
        
        for i, action in enumerate(main_actions):
            btn = ttk.Button(
                self.buttons_frame,
                text=action.label,
                command=lambda a=action: self._execute_action_button(a),
                width=20
            )
            btn.grid(row=i, column=0, padx=2, pady=2, sticky=tk.EW)
            
            if not action.enabled:
                btn.config(state=tk.DISABLED)
            
            # Add tooltip with a clear help text
            tooltip_text = f"{action.label}: {action.description}"
            if not action.enabled:
                tooltip_text += " (aktuell nicht verfügbar - führen Sie zuerst eine Analyse durch)"
            self._create_tooltip(btn, tooltip_text)
        
        # Update "Weitere Aktionen" button visibility
        has_more_actions = len(self.available_actions) > 6
        if has_more_actions:
            self.more_actions_btn.config(state=tk.NORMAL)
        else:
            self.more_actions_btn.config(state=tk.DISABLED)
    
    def _create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = ttk.Label(tooltip, text=text, background="#ffffe0",
                            relief=tk.SOLID, borderwidth=1, wraplength=200)
            label.pack()
            
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def _execute_action_button(self, action: ActionButton):
        """Execute an action from a button click"""
        if action.callback:
            try:
                # Record action in history
                self._add_to_history(action.action_type.value, action.label)
                
                # Execute the action
                action.callback()
                
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Ausführen der Aktion: {str(e)}")
    
    def _execute_action(self, action_name: str):
        """Execute a named action"""
        try:
            # Record action in history
            self._add_to_history(action_name, action_name.replace("_", " ").title())
            
            # Call the main callback if provided
            if self.on_action_callback:
                self.on_action_callback(action_name, self.current_content, self.content_type)
            else:
                messagebox.showinfo("Aktion", f"Aktion '{action_name}' ausgeführt")
                
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Ausführen der Aktion: {str(e)}")
    
    def _add_to_history(self, action_type: str, action_label: str):
        """Add an action to the history"""
        import datetime
        
        history_entry = {
            "timestamp": datetime.datetime.now(),
            "action_type": action_type,
            "action_label": action_label,
            "content_preview": self.current_content[:100] + "..." if len(self.current_content) > 100 else self.current_content
        }
        
        self.action_history.append(history_entry)
        
        # Keep only last 20 actions
        if len(self.action_history) > 20:
            self.action_history = self.action_history[-20:]
    
    def _show_context_menu(self):
        """Show the context menu with additional actions"""
        try:
            # Get button position
            x = self.more_actions_btn.winfo_rootx()
            y = self.more_actions_btn.winfo_rooty() + self.more_actions_btn.winfo_height()
            
            self.context_menu.post(x, y)
        except tk.TclError:
            pass  # Menu might already be posted
    
    def _show_history(self):
        """Show action history in a dialog"""
        if not self.action_history:
            messagebox.showinfo("Verlauf", "Keine Aktionen im Verlauf vorhanden.")
            return
        
        # Create history dialog
        history_dialog = tk.Toplevel(self)
        history_dialog.title("Aktionsverlauf")
        history_dialog.geometry("500x400")
        history_dialog.transient(self)
        history_dialog.grab_set()
        
        # Create listbox with scrollbar
        frame = ttk.Frame(history_dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        listbox = tk.Listbox(frame)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        
        # Populate history
        for entry in reversed(self.action_history):  # Most recent first
            timestamp = entry["timestamp"].strftime("%H:%M:%S")
            text = f"{timestamp} - {entry['action_label']}: {entry['content_preview']}"
            listbox.insert(tk.END, text)
        
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Close button
        ttk.Button(history_dialog, text="Schließen",
                  command=history_dialog.destroy).pack(pady=10)
    
    # Action handlers
    def _handle_zusammenfassen(self):
        """Handle summarization action"""
        self._execute_action("zusammenfassen")
    
    def _handle_vertiefen(self):
        """Handle deepening analysis action"""
        self._execute_action("vertiefen")
    
    def _handle_uebersetzen(self):
        """Handle translation action"""
        # Show language selection dialog
        self._show_translation_dialog()
    
    def _handle_analysieren(self):
        """Handle analysis action"""
        # Show analysis type selection dialog
        self._show_analysis_dialog()
    
    def _show_translation_dialog(self):
        """Show dialog for translation language selection"""
        dialog = tk.Toplevel(self)
        dialog.title("Übersetzung")
        dialog.geometry("300x200")
        dialog.transient(self)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Zielsprache auswählen:").pack(pady=10)
        
        languages = ["Englisch", "Französisch", "Spanisch", "Italienisch", "Niederländisch"]
        language_var = tk.StringVar(value=languages[0])
        
        for lang in languages:
            ttk.Radiobutton(dialog, text=lang, variable=language_var, 
                          value=lang).pack(anchor=tk.W, padx=20)
        
        def execute_translation():
            selected_lang = language_var.get()
            dialog.destroy()
            self._execute_action(f"uebersetzen_{selected_lang.lower()}")
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Übersetzen", 
                  command=execute_translation).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Abbrechen", 
                  command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _show_analysis_dialog(self):
        """Show dialog for analysis type selection"""
        dialog = tk.Toplevel(self)
        dialog.title("Analyse-Typ")
        dialog.geometry("350x250")
        dialog.transient(self)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Analyse-Typ auswählen:").pack(pady=10)
        
        analysis_types = [
            "Sentiment-Analyse",
            "Keyword-Extraktion", 
            "Themen-Erkennung",
            "Struktur-Analyse",
            "Stil-Analyse"
        ]
        
        analysis_var = tk.StringVar(value=analysis_types[0])
        
        for analysis_type in analysis_types:
            ttk.Radiobutton(dialog, text=analysis_type, variable=analysis_var,
                          value=analysis_type).pack(anchor=tk.W, padx=20)
        
        def execute_analysis():
            selected_analysis = analysis_var.get()
            dialog.destroy()
            self._execute_action(f"analysieren_{selected_analysis.lower().replace('-', '_')}")
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Analysieren",
                  command=execute_analysis).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Abbrechen",
                  command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def get_action_history(self) -> List[Dict]:
        """Get the current action history"""
        return self.action_history.copy()
    
    def clear_history(self):
        """Clear the action history"""
        self.action_history.clear()
    
    def add_custom_action(self, action: ActionButton):
        """Add a custom action button"""
        self.available_actions.append(action)
        self._refresh_buttons()
    
    def remove_action(self, action_type: ActionType):
        """Remove an action by type"""
        self.available_actions = [a for a in self.available_actions 
                                if a.action_type != action_type]
        self._refresh_buttons()
    
    def set_action_enabled(self, action_type: ActionType, enabled: bool):
        """Enable or disable a specific action"""
        for action in self.available_actions:
            if action.action_type == action_type:
                action.enabled = enabled
        self._refresh_buttons()