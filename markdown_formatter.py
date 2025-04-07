
import tkinter as tk
from tkinter import ttk


#defining the tags
def configure_markdown_tags(text_widget):
    text_widget.tag_config("bold", font=("Helvetica", 12, "bold"))
    text_widget.tag_config("italic", font=("Helvetica", 12, "italic"))
    text_widget.tag_config("underline", font=("Helvetica", 12, "underline"))
    text_widget.tag_config("strikethrough", font=("Helvetica", 12, "overstrike"))
    text_widget.tag_config("h1", font=("Helvetica", 24, "bold"))
    text_widget.tag_config("h2", font=("Helvetica", 20, "bold"))
    text_widget.tag_config("h3", font=("Helvetica", 16, "bold"))
    text_widget.tag_config("h4", font=("Helvetica", 14, "bold"))
    text_widget.tag_config("h5", font=("Helvetica", 12, "bold"))
    text_widget.tag_config("h6", font=("Helvetica", 10, "bold"))
    text_widget.tag_config("code", font=("Courier", 12, "normal"))
    text_widget.tag_config("blockquote", font=("Helvetica", 12, "italic"))
    text_widget.tag_config("link", font=("Helvetica", 12, "underline"))
#TODO funtkionen fertigstellen mit allen ausgaben

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
    # This would be similar to bold processing

    # Insert any remaining text
    if current_pos < len(line):
        text_widget.insert(tk.END, line[current_pos:])

