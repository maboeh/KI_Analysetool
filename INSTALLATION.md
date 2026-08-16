# Installation Guide - KI Analysetool

## System Requirements

- Python 3.8 or higher
- Operating System: Windows, macOS, or Linux
- Tesseract OCR engine (for image text extraction)

## Quick Setup

For a complete automated setup, run:

```bash
# Clone or download the project
# Navigate to the project directory
cd KI_Analysetool

# Run the automated setup script
python setup.py
```

This will install all dependencies, configure the environment, and validate the setup.

## Manual Installation Steps

### 1. Python Environment Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 2. Install Python Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

### 3. Install Tesseract OCR Engine

#### Windows
1. Download Tesseract installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer and follow the setup wizard
3. Add Tesseract to your PATH or note the installation directory

#### macOS
```bash
# Using Homebrew
brew install tesseract

# Using MacPorts
sudo port install tesseract3
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install tesseract-ocr
sudo apt install libtesseract-dev
```

#### Linux (CentOS/RHEL/Fedora)
```bash
# CentOS/RHEL
sudo yum install tesseract
sudo yum install tesseract-devel

# Fedora
sudo dnf install tesseract
sudo dnf install tesseract-devel
```

### 4. Configure API Keys

1. Create a `config.ini` file in the project root:
```ini
[API]
openai_api_key = your_openai_api_key_here
```

2. Or set environment variable:
```bash
export OPENAI_API_KEY=your_openai_api_key_here
```

### 5. Configure Environment

```bash
# Configure matplotlib for Tkinter integration
python configure_matplotlib.py
```

### 6. Verify Installation

Run the setup validation scripts:
```bash
# Check system requirements
python system_requirements_check.py

# Validate complete setup
python setup_validation.py
```

## Troubleshooting

### Common Issues

#### Tesseract Not Found
If you get "tesseract not found" errors:
1. Ensure Tesseract is installed
2. Add Tesseract to your system PATH
3. On Windows, you may need to specify the path in your code

#### Import Errors
If you get import errors for new packages:
```bash
# Upgrade pip first
pip install --upgrade pip

# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

#### matplotlib Backend Issues
If matplotlib charts don't display properly:
```bash
# Install tkinter backend support
pip install matplotlib[tk]
```

### Platform-Specific Notes

#### Windows
- Ensure Visual C++ redistributables are installed for some packages
- Use Command Prompt or PowerShell as Administrator if needed

#### macOS
- Xcode command line tools may be required: `xcode-select --install`
- Some packages may require Homebrew dependencies

#### Linux
- Development headers may be needed: `sudo apt install python3-dev`
- For GUI applications, ensure X11 forwarding is enabled if using SSH

## Package Versions

The application has been tested with the following package versions:

### Core Dependencies
- openai: 1.0.0+
- youtube-transcript-api: 0.6.0+
- beautifulsoup4: 4.12.0+
- requests: 2.31.0+
- reportlab: 4.0.0+

### Data Processing
- pandas: 2.0.0+
- openpyxl: 3.1.0+

### Image Processing
- pytesseract: 0.3.10+
- Pillow: 10.0.0+

### Visualization
- matplotlib: 3.7.0+
- seaborn: 0.12.0+

## Performance Recommendations

### For Large File Processing
- Ensure sufficient RAM (8GB+ recommended)
- SSD storage for better I/O performance
- Close other applications when processing large datasets

### For OCR Operations
- Higher resolution images provide better OCR accuracy
- Preprocessing images (contrast, brightness) can improve results
- Consider batch processing for multiple images

## Security Notes

- Keep your OpenAI API key secure and never commit it to version control
- The application processes data locally by default
- Ensure proper file permissions for configuration files