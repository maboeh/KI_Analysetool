# Technology Stack

## Core Technologies

- **Python 3.12**: Main programming language
- **Tkinter**: GUI framework for desktop interface
- **OpenAI API**: GPT-4o model for AI analysis

## Key Dependencies

- `openai`: OpenAI API client
- `youtube-transcript-api`: YouTube transcript extraction
- `beautifulsoup4`: Web scraping and HTML parsing
- `requests`: HTTP requests for web content
- `reportlab`: PDF generation for exports
- `configparser`: Configuration file management

## Development Environment

- **Virtual Environment**: `.venv` directory for isolated dependencies
- **IDE**: PyCharm (`.idea` folder present)
- **Version Control**: Git with `.gitignore` for sensitive files

## Common Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the application
python main.py

# Install dependencies (if requirements.txt exists)
pip install -r requirements.txt

# Common dependencies to install manually:
pip install openai youtube-transcript-api beautifulsoup4 requests reportlab
```

## Configuration

- API keys stored in `config.ini` (excluded from git)
- Environment variable `OPENAI_API_KEY` as fallback
- Configuration managed through `config.py` module