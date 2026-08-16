
import tkinter as tk
from tkinter import ttk


#defining the tags
def configure_markdown_tags(text_widget, font_size=12):
    text_widget.tag_config("bold", font=("Helvetica", font_size, "bold"))
    text_widget.tag_config("italic", font=("Helvetica", font_size, "italic"))
    text_widget.tag_config("underline", font=("Helvetica", font_size, "underline"))
    text_widget.tag_config("strikethrough", font=("Helvetica", font_size, "overstrike"))
    text_widget.tag_config("h1", font=("Helvetica", font_size + 12, "bold"))
    text_widget.tag_config("h2", font=("Helvetica", font_size + 8, "bold"))
    text_widget.tag_config("h3", font=("Helvetica", font_size + 4, "bold"))
    text_widget.tag_config("h4", font=("Helvetica", font_size + 2, "bold"))
    text_widget.tag_config("h5", font=("Helvetica", font_size, "bold"))
    text_widget.tag_config("h6", font=("Helvetica", max(8, font_size - 2), "bold"))
    text_widget.tag_config("code", font=("Courier", font_size, "normal"))
    text_widget.tag_config("blockquote", font=("Helvetica", font_size, "italic"))
    text_widget.tag_config("link", font=("Helvetica", font_size, "underline"))

def markdown_to_tkinter_text(mark_down_text, text_widget):
    text_widget.delete(1.0, tk.END)  # Clear existing content

    # Process line-based formatting
    lines = mark_down_text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # Handle headings
        if line.startswith("# "):
            text_widget.insert(tk.END, line[2:] + "\n", "h1")
        elif line.startswith("## "):
            text_widget.insert(tk.END, line[3:] + "\n", "h2")
        elif line.startswith("### "):
            text_widget.insert(tk.END, line[4:] + "\n", "h3")
        elif line.startswith("#### "):
            text_widget.insert(tk.END, line[5:] + "\n", "h4")
        elif line.startswith("##### "):
            text_widget.insert(tk.END, line[6:] + "\n", "h5")
        elif line.startswith("###### "):
            text_widget.insert(tk.END, line[7:] + "\n", "h6")
        # Handle code blocks
        elif line.startswith("```"):
            code_block = []
            i += 1  # Skip the opening ```

            # Collect all lines until closing ```
            while i < len(lines) and not lines[i].startswith("```"):
                code_block.append(lines[i])
                i += 1

            text_widget.insert(tk.END, "\n".join(code_block) + "\n", "code")
        # Handle blockquotes
        elif line.startswith("> "):
            text_widget.insert(tk.END, line[2:] + "\n", "blockquote")
    # Handle unordered list items
        elif line.startswith("- ") or line.startswith("* "):
            text_widget.insert(tk.END, "  \u2022 " + line[2:] + "\n")
        elif line.startswith("  - ") or line.startswith("  * "):
            text_widget.insert(tk.END, "    \u25e6 " + line[4:] + "\n")
        # Handle ordered list items
        elif len(line) > 2 and line[0].isdigit() and line[1] == ".":
            text_widget.insert(tk.END, line + "\n")
        # Handle horizontal rules
        elif line.strip() in ("---", "***", "___"):
            text_widget.insert(tk.END, "\u2500" * 50 + "\n")
        # Regular text
        else:
            # Process inline formatting
            process_inline_formatting(text_widget, line)
            text_widget.insert(tk.END, "\n")

        i += 1


def process_inline_formatting(text_widget, line):
    # Split the line into segments to handle different formatting
    current_pos = 0

    # Process bold (**text**)
    while "**" in line[current_pos:]:
        start = line.find("**", current_pos)
        if start == -1:
            break

        # Insert text before the bold marker
        text_widget.insert(tk.END, line[current_pos:start])

        # Find closing bold marker
        end = line.find("**", start + 2)
        if end == -1:
            # No closing marker, insert rest as regular text
            text_widget.insert(tk.END, line[start:])
            return

        # Insert the bold text with the bold tag
        text_widget.insert(tk.END, line[start + 2:end], "bold")
        current_pos = end + 2

    # Process italic (*text* or _text_)
    remaining = line[current_pos:]
    while remaining and ("*" in remaining or "_" in remaining):
        # Find single * or _ (not ** which is bold)
        single_star = remaining.find("*")
        single_underscore = remaining.find("_")

        markers = []
        if single_star != -1:
            markers.append((single_star, "*"))
        if single_underscore != -1:
            markers.append((single_underscore, "_"))

        if not markers:
            break

        markers.sort()
        marker_pos, marker_char = markers[0]

        # Insert text before the italic marker
        text_widget.insert(tk.END, remaining[:marker_pos])

        # Find closing marker
        close_pos = remaining.find(marker_char, marker_pos + 1)
        if close_pos == -1:
            text_widget.insert(tk.END, remaining[marker_pos:])
            return

        # Insert the italic text
        text_widget.insert(tk.END, remaining[marker_pos + 1:close_pos], "italic")
        remaining = remaining[close_pos + 1:]
        current_pos = 0

    # Insert any remaining text
    if remaining:
        text_widget.insert(tk.END, remaining)

