#!/usr/bin/env python3
"""
Setup Validation Script for KI Analysetool
Checks if all required dependencies and external tools are properly installed and configured.
"""

import sys
import subprocess
import importlib
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.11 or higher."""
    print("🔍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.11+")
        return False

def check_package_import(package_name, import_name=None):
    """Check if a Python package can be imported."""
    if import_name is None:
        import_name = package_name
    
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"✅ {package_name} ({version}) - OK")
        return True
    except ImportError as e:
        print(f"❌ {package_name} - Import failed: {e}")
        return False

def check_tesseract():
    """Check if Tesseract OCR is installed and accessible."""
    print("🔍 Checking Tesseract OCR...")
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ {version_line} - OK")
            return True
        else:
            print(f"❌ Tesseract command failed: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ Tesseract not found in PATH")
        print("   Install instructions:")
        print("   - macOS: brew install tesseract")
        print("   - Ubuntu: sudo apt install tesseract-ocr")
        print("   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        return False
    except subprocess.TimeoutExpired:
        print("❌ Tesseract command timed out")
        return False

def check_matplotlib_backend():
    """Check if matplotlib can use Tkinter backend."""
    print("🔍 Checking matplotlib Tkinter backend...")
    try:
        import matplotlib
        matplotlib.use('TkAgg')  # Set Tkinter backend
        import matplotlib.pyplot as plt
        print("✅ matplotlib Tkinter backend - OK")
        return True
    except Exception as e:
        print(f"❌ matplotlib Tkinter backend failed: {e}")
        print("   Try: pip install matplotlib[tk]")
        return False

def check_gui_instantiation():
    """Check if the enhanced GUI can be instantiated."""
    print("🔍 Checking GUI instantiation...")
    try:
        import tkinter as tk
        from enhanced_gui_integration_final import EnhancedGui
        root = tk.Tk()
        root.withdraw()
        app = EnhancedGui(root)
        root.destroy()
        print("✅ Enhanced GUI instantiation - OK")
        return True
    except Exception as e:
        print(f"❌ Enhanced GUI instantiation failed: {e}")
        return False


def check_config_file():
    """Check if configuration file exists."""
    print("🔍 Checking configuration...")
    config_path = Path("config.ini")
    if config_path.exists():
        print("✅ config.ini found - OK")
        return True
    else:
        print("⚠️  config.ini not found")
        print("   Create config.ini with your OpenAI API key:")
        print("   [API]")
        print("   openai_api_key = your_key_here")
        return False

def check_openai_api_key():
    """Check if OpenAI API key is configured."""
    print("🔍 Checking OpenAI API key...")
    
    # Check environment variable
    if os.getenv('OPENAI_API_KEY'):
        print("✅ OpenAI API key found in environment - OK")
        return True
    
    # Check config file
    try:
        import configparser
        config = configparser.ConfigParser()
        config.read('config.ini')
        if config.has_section('API') and config.has_option('API', 'openai_api_key'):
            key = config.get('API', 'openai_api_key')
            if key and key != 'your_openai_api_key_here':
                print("✅ OpenAI API key found in config.ini - OK")
                return True
    except Exception:
        pass
    
    print("⚠️  OpenAI API key not configured")
    print("   Set environment variable: export OPENAI_API_KEY=your_key")
    print("   Or add to config.ini: [API] openai_api_key = your_key")
    return False

def main():
    """Run all validation checks."""
    print("🚀 KI Analysetool Setup Validation")
    print("=" * 50)
    
    checks = []
    
    # Core Python checks
    checks.append(("Python Version", check_python_version))
    
    # Core dependencies
    print("\n📦 Checking core dependencies...")
    checks.append(("openai", lambda: check_package_import("openai")))
    checks.append(("youtube-transcript-api", lambda: check_package_import("youtube-transcript-api", "youtube_transcript_api")))
    checks.append(("beautifulsoup4", lambda: check_package_import("beautifulsoup4", "bs4")))
    checks.append(("requests", lambda: check_package_import("requests")))
    checks.append(("reportlab", lambda: check_package_import("reportlab")))
    
    # Data processing dependencies
    print("\n📊 Checking data processing dependencies...")
    checks.append(("pandas", lambda: check_package_import("pandas")))
    checks.append(("openpyxl", lambda: check_package_import("openpyxl")))
    
    # Image processing dependencies
    print("\n🖼️  Checking image processing dependencies...")
    checks.append(("pytesseract", lambda: check_package_import("pytesseract")))
    checks.append(("Pillow", lambda: check_package_import("Pillow", "PIL")))
    checks.append(("pdf2image", lambda: check_package_import("pdf2image")))

    # Text/CSV encoding detection
    print("\n🔤 Checking encoding detection...")
    checks.append(("chardet", lambda: check_package_import("chardet")))

    # Visualization dependencies
    print("\n📈 Checking visualization dependencies...")
    checks.append(("matplotlib", lambda: check_package_import("matplotlib")))
    checks.append(("seaborn", lambda: check_package_import("seaborn")))
    
    # Additional utilities
    print("\n🔧 Checking additional utilities...")
    checks.append(("python-dateutil", lambda: check_package_import("python-dateutil", "dateutil")))
    checks.append(("regex", lambda: check_package_import("regex")))
    checks.append(("keyring", lambda: check_package_import("keyring")))

    # Internal learning/help modules
    print("\n🎓 Checking learning and help modules...")
    checks.append(("user_profile", lambda: check_package_import("user_profile")))
    checks.append(("learning_path", lambda: check_package_import("learning_path")))
    checks.append(("prompt_library", lambda: check_package_import("prompt_library")))
    checks.append(("help_tooltip", lambda: check_package_import("help_tooltip")))

    # External dependencies
    print("\n🔧 Checking external dependencies...")
    checks.append(("Tesseract OCR", check_tesseract))
    checks.append(("matplotlib backend", check_matplotlib_backend))

    # GUI instantiation
    print("\n🖥️  Checking GUI instantiation...")
    checks.append(("Enhanced GUI", check_gui_instantiation))
    
    # Configuration
    print("\n⚙️  Checking configuration...")
    checks.append(("config.ini", check_config_file))
    checks.append(("OpenAI API key", check_openai_api_key))
    
    # Run all checks
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} - Unexpected error: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All checks passed! Your setup is ready.")
        return 0
    else:
        failed = total - passed
        print(f"❌ Failed: {failed}/{total}")
        print("\n🔧 Please fix the failed checks and run this script again.")
        return 1

if __name__ == "__main__":
    sys.exit(main())