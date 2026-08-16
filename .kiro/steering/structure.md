# Project Structure

## File Organization

```
├── main.py                 # Application entry point
├── Gui.py                  # Main GUI class and interface logic
├── analysis.py             # Content extraction and AI analysis functions
├── config.py               # Configuration and API key management
├── markdown_formatter.py   # Markdown rendering for Tkinter text widgets
├── config.ini             # Configuration file (gitignored)
├── .venv/                 # Python virtual environment
├── .kiro/                 # Kiro IDE configuration
└── __pycache__/           # Python bytecode cache
```

## Architecture Patterns

### MVC-like Structure
- **main.py**: Entry point, minimal bootstrap code
- **Gui.py**: View layer - handles all UI components and user interactions
- **analysis.py**: Model layer - business logic for content processing and AI analysis
- **config.py**: Configuration layer - handles settings and API key management

### Key Design Principles
- **Separation of concerns**: UI, business logic, and configuration are separated
- **Modular functions**: Each analysis type has dedicated functions
- **Error handling**: Try-catch blocks for API calls and file operations
- **German localization**: All user-facing text in German

## Code Conventions

### File Naming
- **PascalCase**: Class files (Gui.py)
- **snake_case**: Utility modules (analysis.py, config.py, markdown_formatter.py)
- **lowercase**: Entry point (main.py)

### Function Naming
- **snake_case**: All function names
- **German prefixes**: Some functions use German naming (e.g., `real_ai_analyse_fortext`)
- **Descriptive names**: Functions clearly indicate their purpose

### Class Structure
- **Single responsibility**: Each class handles one main concern
- **Method organization**: Setup methods, event handlers, utility functions grouped logically