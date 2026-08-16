"""
Enhanced Results Display Widget for KI Analysetool

This module provides an enhanced results display widget that extends the existing
output_text widget with improved formatting, syntax highlighting, collapsible sections,
and better readability features.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, font
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from markdown_formatter import configure_markdown_tags, markdown_to_tkinter_text


@dataclass
class DisplaySection:
    """Represents a collapsible section in the results display"""
    title: str
    content: str
    is_collapsed: bool = False
    start_index: str = "1.0"
    end_index: str = "1.0"


class ResultsDisplayWidget(ttk.Frame):
    """
    Enhanced results display widget with improved formatting capabilities.
    
    Features:
    - Syntax highlighting for different content types
    - Collapsible sections for better organization
    - Zoom and scroll enhancements
    - Structured content display
    """
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Configuration
        self.zoom_level = 1.0
        self.base_font_size = 10
        self.sections: List[DisplaySection] = []
        self.collapsed_sections: Dict[str, bool] = {}
        
        # Setup the widget
        self._setup_widget()
        self._configure_tags()
        self._bind_events()
    
    def _setup_widget(self):
        """Setup the main widget components"""
        # Create main frame with toolbar
        self.toolbar_frame = ttk.Frame(self)
        self.toolbar_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        # Zoom controls
        zoom_frame = ttk.Frame(self.toolbar_frame)
        zoom_frame.pack(side=tk.LEFT)
        
        ttk.Label(zoom_frame, text="Zoom:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.zoom_out_btn = ttk.Button(zoom_frame, text="-", width=3, 
                                      command=self.zoom_out)
        self.zoom_out_btn.pack(side=tk.LEFT, padx=2)
        
        self.zoom_label = ttk.Label(zoom_frame, text="100%", width=6)
        self.zoom_label.pack(side=tk.LEFT, padx=2)
        
        self.zoom_in_btn = ttk.Button(zoom_frame, text="+", width=3,
                                     command=self.zoom_in)
        self.zoom_in_btn.pack(side=tk.LEFT, padx=2)
        
        # Reset zoom button
        self.reset_zoom_btn = ttk.Button(zoom_frame, text="Reset", width=6,
                                        command=self.reset_zoom)
        self.reset_zoom_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # View options
        view_frame = ttk.Frame(self.toolbar_frame)
        view_frame.pack(side=tk.RIGHT)
        
        self.collapse_all_btn = ttk.Button(view_frame, text="Alle zuklappen",
                                          command=self.collapse_all_sections)
        self.collapse_all_btn.pack(side=tk.LEFT, padx=2)
        
        self.expand_all_btn = ttk.Button(view_frame, text="Alle aufklappen",
                                        command=self.expand_all_sections)
        self.expand_all_btn.pack(side=tk.LEFT, padx=2)
        
        # Main text widget with enhanced scrolling
        text_frame = ttk.Frame(self)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create text widget with custom scrollbar
        self.text_widget = tk.Text(text_frame, wrap=tk.WORD, state=tk.DISABLED,
                                  font=("Segoe UI", self.base_font_size),
                                  bg="#ffffff", fg="#000000",
                                  selectbackground="#0078d4",
                                  selectforeground="#ffffff")
        
        # Custom scrollbar with better styling
        self.scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL,
                                      command=self.text_widget.yview)
        self.text_widget.configure(yscrollcommand=self.scrollbar.set)
        
        # Horizontal scrollbar for wide content
        self.h_scrollbar = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL,
                                        command=self.text_widget.xview)
        self.text_widget.configure(xscrollcommand=self.h_scrollbar.set)
        
        # Pack scrollbars and text widget
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    def _configure_tags(self):
        """Configure text tags for syntax highlighting and formatting"""
        # Configure existing markdown tags
        configure_markdown_tags(self.text_widget)
        
        # Additional enhanced tags
        self.text_widget.tag_configure("section_header", 
                                      font=("Segoe UI", self.base_font_size + 2, "bold"),
                                      foreground="#0078d4",
                                      spacing1=10, spacing3=5)
        
        self.text_widget.tag_configure("section_toggle",
                                      font=("Segoe UI", self.base_font_size, "bold"),
                                      foreground="#666666",
                                      underline=True)
        
        self.text_widget.tag_configure("collapsed_indicator",
                                      foreground="#999999",
                                      font=("Segoe UI", self.base_font_size - 1))
        
        self.text_widget.tag_configure("highlight_data",
                                      background="#fff3cd",
                                      foreground="#856404")
        
        self.text_widget.tag_configure("highlight_number",
                                      foreground="#d63384",
                                      font=("Segoe UI", self.base_font_size, "bold"))
        
        self.text_widget.tag_configure("highlight_date",
                                      foreground="#6f42c1",
                                      font=("Segoe UI", self.base_font_size, "bold"))
        
        self.text_widget.tag_configure("code_block",
                                      font=("Consolas", self.base_font_size),
                                      background="#f8f9fa",
                                      foreground="#212529",
                                      lmargin1=20, lmargin2=20,
                                      spacing1=5, spacing3=5)
    
    def _bind_events(self):
        """Bind mouse and keyboard events"""
        # Mouse wheel scrolling with zoom
        self.text_widget.bind("<Control-MouseWheel>", self._on_zoom_scroll)
        self.text_widget.bind("<MouseWheel>", self._on_scroll)
        
        # Click events for collapsible sections
        self.text_widget.bind("<Button-1>", self._on_click)
        
        # Keyboard shortcuts
        self.text_widget.bind("<Control-plus>", lambda e: self.zoom_in())
        self.text_widget.bind("<Control-minus>", lambda e: self.zoom_out())
        self.text_widget.bind("<Control-0>", lambda e: self.reset_zoom())
    
    def display_content(self, content: str, content_type: str = "markdown"):
        """
        Display content with enhanced formatting
        
        Args:
            content: The content to display
            content_type: Type of content (markdown, plain, structured)
        """
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        
        if content_type == "markdown":
            self._display_markdown_content(content)
        elif content_type == "structured":
            self._display_structured_content(content)
        else:
            self._display_plain_content(content)
        
        self.text_widget.config(state=tk.DISABLED)
        self._update_font_sizes()
    
    def _display_markdown_content(self, content: str):
        """Display markdown content with enhanced formatting"""
        # Parse content into sections
        sections = self._parse_sections(content)
        
        if sections and len(sections) > 1:
            # Only use sections if we have multiple sections
            for section in sections:
                self._insert_collapsible_section(section)
        else:
            # Fallback to regular markdown rendering for single section or no sections
            markdown_to_tkinter_text(content, self.text_widget)
            self._apply_syntax_highlighting()
    
    def _display_structured_content(self, content: str):
        """Display structured content with automatic section detection"""
        # Auto-detect structure and create sections
        sections = self._auto_detect_sections(content)
        
        if sections:
            for section in sections:
                self._insert_collapsible_section(section)
        else:
            # Fallback to plain display if no sections detected
            self.text_widget.insert(tk.END, content)
        
        self._apply_syntax_highlighting()
    
    def _display_plain_content(self, content: str):
        """Display plain content with basic highlighting"""
        self.text_widget.insert(tk.END, content)
        self._apply_syntax_highlighting()
    
    def _parse_sections(self, content: str) -> List[DisplaySection]:
        """Parse markdown content into collapsible sections"""
        sections = []
        lines = content.split('\n')
        current_section = None
        current_content = []
        intro_content = []
        
        for line in lines:
            # Check for headers (## or ###)
            header_match = re.match(r'^(#{2,3})\s+(.+)$', line)
            if header_match:
                # Save previous section
                if current_section:
                    current_section.content = '\n'.join(current_content).strip()
                    sections.append(current_section)
                
                # Start new section
                level = len(header_match.group(1))
                title = header_match.group(2)
                current_section = DisplaySection(title=title, content="")
                current_content = []
            else:
                if current_section:
                    current_content.append(line)
                else:
                    # Content before first header
                    intro_content.append(line)
        
        # Add intro section if there's content before first header
        if intro_content and any(line.strip() for line in intro_content):
            intro_section = DisplaySection(title="Einleitung", 
                                         content='\n'.join(intro_content).strip())
            sections.insert(0, intro_section)
        
        # Add last section
        if current_section:
            current_section.content = '\n'.join(current_content).strip()
            sections.append(current_section)
        
        return sections
    
    def _auto_detect_sections(self, content: str) -> List[DisplaySection]:
        """Auto-detect sections in unstructured content"""
        sections = []
        
        # Split by double newlines (paragraphs)
        paragraphs = content.split('\n\n')
        
        for i, paragraph in enumerate(paragraphs):
            if len(paragraph.strip()) > 0:
                # Try to extract a title from the first line
                lines = paragraph.split('\n')
                if len(lines) > 1 and len(lines[0]) < 100:
                    title = lines[0][:50] + "..." if len(lines[0]) > 50 else lines[0]
                    content_text = '\n'.join(lines[1:])
                else:
                    title = f"Abschnitt {i + 1}"
                    content_text = paragraph
                
                sections.append(DisplaySection(title=title, content=content_text))
        
        return sections
    
    def _insert_collapsible_section(self, section: DisplaySection):
        """Insert a collapsible section into the text widget"""
        start_pos = self.text_widget.index(tk.INSERT)
        
        # Insert section header with toggle button
        toggle_symbol = "▼" if not section.is_collapsed else "▶"
        header_text = f"{toggle_symbol} {section.title}\n"
        
        self.text_widget.insert(tk.INSERT, header_text, "section_header")
        
        # Store section info
        section.start_index = start_pos
        
        if not section.is_collapsed:
            # Insert section content
            content_start = self.text_widget.index(tk.INSERT)
            markdown_to_tkinter_text(section.content, self.text_widget)
            self.text_widget.insert(tk.INSERT, "\n\n")
            section.end_index = self.text_widget.index(tk.INSERT)
        else:
            # Insert collapsed indicator
            self.text_widget.insert(tk.INSERT, "   [Inhalt eingeklappt]\n\n", "collapsed_indicator")
            section.end_index = self.text_widget.index(tk.INSERT)
        
        # Make header clickable
        header_end = self.text_widget.search('\n', start_pos, tk.END)
        self.text_widget.tag_add(f"toggle_{len(self.sections)}", start_pos, header_end)
        self.text_widget.tag_bind(f"toggle_{len(self.sections)}", "<Button-1>", 
                                 lambda e, s=section: self._toggle_section(s))
        
        self.sections.append(section)
    
    def _apply_syntax_highlighting(self):
        """Apply syntax highlighting to the current content"""
        content = self.text_widget.get(1.0, tk.END)
        
        # Highlight numbers
        for match in re.finditer(r'\b\d+(?:\.\d+)?\b', content):
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            self.text_widget.tag_add("highlight_number", start_idx, end_idx)
        
        # Highlight dates
        date_patterns = [
            r'\b\d{1,2}\.\d{1,2}\.\d{4}\b',  # DD.MM.YYYY
            r'\b\d{4}-\d{2}-\d{2}\b',        # YYYY-MM-DD
            r'\b\d{1,2}/\d{1,2}/\d{4}\b'     # MM/DD/YYYY
        ]
        
        for pattern in date_patterns:
            for match in re.finditer(pattern, content):
                start_idx = f"1.0+{match.start()}c"
                end_idx = f"1.0+{match.end()}c"
                self.text_widget.tag_add("highlight_date", start_idx, end_idx)
        
        # Highlight code blocks (content between ```)
        for match in re.finditer(r'```[\s\S]*?```', content):
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            self.text_widget.tag_add("code_block", start_idx, end_idx)
    
    def _toggle_section(self, section: DisplaySection):
        """Toggle the collapsed state of a section"""
        section.is_collapsed = not section.is_collapsed
        
        # Refresh the display by rebuilding sections
        self._refresh_display()
    
    def zoom_in(self):
        """Increase zoom level"""
        if self.zoom_level < 2.9:  # Use 2.9 to avoid floating point precision issues
            self.zoom_level += 0.1
            self._update_font_sizes()
            self._update_zoom_label()
    
    def zoom_out(self):
        """Decrease zoom level"""
        if self.zoom_level > 0.6:  # Use 0.6 to avoid floating point precision issues
            self.zoom_level -= 0.1
            self._update_font_sizes()
            self._update_zoom_label()
    
    def reset_zoom(self):
        """Reset zoom to 100%"""
        self.zoom_level = 1.0
        self._update_font_sizes()
        self._update_zoom_label()
    
    def _update_font_sizes(self):
        """Update font sizes based on zoom level"""
        new_size = int(self.base_font_size * self.zoom_level)
        
        # Update main font
        current_font = font.Font(font=self.text_widget['font'])
        current_font.configure(size=new_size)
        self.text_widget.configure(font=current_font)
        
        # Update tag fonts
        for tag in self.text_widget.tag_names():
            if tag.startswith(('section_', 'highlight_', 'code_')):
                tag_font = self.text_widget.tag_cget(tag, 'font')
                if tag_font:
                    try:
                        # Parse font tuple and update size
                        if isinstance(tag_font, tuple):
                            family, size, *style = tag_font
                            new_tag_size = int(size * self.zoom_level / 
                                             (self.base_font_size / int(size)))
                            self.text_widget.tag_configure(tag, 
                                                         font=(family, new_tag_size, *style))
                    except (ValueError, TypeError):
                        pass
    
    def _update_zoom_label(self):
        """Update the zoom percentage label"""
        percentage = int(self.zoom_level * 100)
        self.zoom_label.config(text=f"{percentage}%")
    
    def collapse_all_sections(self):
        """Collapse all sections"""
        for section in self.sections:
            section.is_collapsed = True
        
        self._refresh_display()
    
    def expand_all_sections(self):
        """Expand all sections"""
        for section in self.sections:
            section.is_collapsed = False
        
        self._refresh_display()
    
    def _refresh_display(self):
        """Refresh the display with current sections"""
        if not self.sections:
            return
        
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        
        # Store current sections to avoid modifying during iteration
        current_sections = self.sections.copy()
        self.sections.clear()
        
        for section in current_sections:
            self._insert_collapsible_section(section)
        
        self.text_widget.config(state=tk.DISABLED)
        self._apply_syntax_highlighting()
    
    def get_content(self) -> str:
        """Get the current content from the text widget"""
        return self.text_widget.get(1.0, tk.END).strip()
    
    def clear_content(self):
        """Clear all content from the widget"""
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.config(state=tk.DISABLED)
        self.sections.clear()
    
    def _on_zoom_scroll(self, event):
        """Handle Ctrl+MouseWheel for zooming"""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
        return "break"
    
    def _on_scroll(self, event):
        """Handle regular mouse wheel scrolling"""
        self.text_widget.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"
    
    def _on_click(self, event):
        """Handle click events for interactive elements"""
        # Get the index of the click
        click_index = self.text_widget.index(f"@{event.x},{event.y}")
        
        # Check if click is on a toggle button
        for tag in self.text_widget.tag_names(click_index):
            if tag.startswith("toggle_"):
                return "break"  # Let the tag binding handle it
        
        return None