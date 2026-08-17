#!/usr/bin/env python3
"""
System Requirements Check for KI Analysetool
Checks system-level dependencies and provides installation guidance.
"""

import sys
import platform
import subprocess
import shutil
from pathlib import Path

def get_system_info():
    """Get system information."""
    print("🖥️  System Information")
    print("-" * 30)
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Python: {sys.version}")
    print()

def check_tesseract_installation():
    """Check Tesseract OCR installation and provide guidance."""
    print("🔍 Checking Tesseract OCR Installation...")
    
    # Check if tesseract is in PATH
    tesseract_path = shutil.which('tesseract')
    if tesseract_path:
        try:
            result = subprocess.run(['tesseract', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                print(f"✅ {version_line}")
                print(f"   Location: {tesseract_path}")
                return True
        except Exception as e:
            print(f"❌ Error running tesseract: {e}")
    
    print("❌ Tesseract OCR not found or not working")
    print_tesseract_installation_guide()
    return False

def print_tesseract_installation_guide():
    """Print installation guide for Tesseract based on OS."""
    system = platform.system().lower()
    
    print("\n📋 Tesseract Installation Guide:")
    print("-" * 40)
    
    if system == "darwin":  # macOS
        print("🍎 macOS Installation:")
        print("   Using Homebrew (recommended):")
        print("   brew install tesseract")
        print()
        print("   Using MacPorts:")
        print("   sudo port install tesseract3")
        print()
        print("   Manual installation:")
        print("   Download from: https://github.com/tesseract-ocr/tesseract/wiki")
        
    elif system == "linux":
        print("🐧 Linux Installation:")
        print("   Ubuntu/Debian:")
        print("   sudo apt update")
        print("   sudo apt install tesseract-ocr")
        print("   sudo apt install libtesseract-dev")
        print()
        print("   CentOS/RHEL:")
        print("   sudo yum install tesseract")
        print("   sudo yum install tesseract-devel")
        print()
        print("   Fedora:")
        print("   sudo dnf install tesseract")
        print("   sudo dnf install tesseract-devel")
        
    elif system == "windows":
        print("🪟 Windows Installation:")
        print("   1. Download installer from:")
        print("      https://github.com/UB-Mannheim/tesseract/wiki")
        print("   2. Run the installer as Administrator")
        print("   3. Add Tesseract to your PATH:")
        print("      - Default location: C:\\Program Files\\Tesseract-OCR")
        print("      - Add to System PATH in Environment Variables")
        print("   4. Restart Command Prompt/PowerShell")
    
    print()

def check_python_dev_tools():
    """Check if Python development tools are available."""
    print("🔍 Checking Python Development Tools...")
    
    # Check if pip is available
    pip_path = shutil.which('pip')
    if pip_path:
        print(f"✅ pip found at: {pip_path}")
    else:
        print("❌ pip not found")
        return False
    
    # Check if we can compile extensions (important for some packages)
    try:
        import distutils.util
        import distutils.spawn
        
        # Check for C compiler
        cc = distutils.spawn.find_executable('gcc') or distutils.spawn.find_executable('clang')
        if cc:
            print(f"✅ C compiler found: {cc}")
        else:
            print("⚠️  C compiler not found (may be needed for some packages)")
            print_dev_tools_guide()
    except Exception:
        print("⚠️  Could not check for development tools")
    
    return True

def print_dev_tools_guide():
    """Print development tools installation guide."""
    system = platform.system().lower()
    
    print("\n📋 Development Tools Installation:")
    print("-" * 40)
    
    if system == "darwin":  # macOS
        print("🍎 macOS:")
        print("   Install Xcode Command Line Tools:")
        print("   xcode-select --install")
        
    elif system == "linux":
        print("🐧 Linux:")
        print("   Ubuntu/Debian:")
        print("   sudo apt install build-essential python3-dev")
        print()
        print("   CentOS/RHEL/Fedora:")
        print("   sudo yum groupinstall 'Development Tools'")
        print("   sudo yum install python3-devel")
        
    elif system == "windows":
        print("🪟 Windows:")
        print("   Install Microsoft Visual C++ Build Tools:")
        print("   https://visualstudio.microsoft.com/visual-cpp-build-tools/")
    
    print()

def check_gui_support():
    """Check if GUI support is available."""
    print("🔍 Checking GUI Support...")
    
    try:
        import tkinter as tk
        # Try to create a root window (but don't show it)
        root = tk.Tk()
        root.withdraw()  # Hide the window
        root.destroy()
        print("✅ Tkinter GUI support available")
        return True
    except Exception as e:
        print(f"❌ Tkinter GUI support not available: {e}")
        print_gui_support_guide()
        return False

def print_gui_support_guide():
    """Print GUI support installation guide."""
    system = platform.system().lower()
    
    print("\n📋 GUI Support Installation:")
    print("-" * 35)
    
    if system == "linux":
        print("🐧 Linux:")
        print("   Ubuntu/Debian:")
        print("   sudo apt install python3-tk")
        print()
        print("   CentOS/RHEL:")
        print("   sudo yum install tkinter")
        print("   # or")
        print("   sudo yum install python3-tkinter")
        print()
        print("   For SSH/Remote access:")
        print("   ssh -X username@hostname")
        
    elif system == "darwin":
        print("🍎 macOS:")
        print("   Tkinter should be included with Python")
        print("   If not working, try reinstalling Python from python.org")
        
    elif system == "windows":
        print("🪟 Windows:")
        print("   Tkinter should be included with Python")
        print("   If not working, reinstall Python with 'tcl/tk and IDLE' option")
    
    print()

def check_memory_and_disk():
    """Check system resources."""
    print("🔍 Checking System Resources...")
    
    try:
        import psutil
        
        # Check memory
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        print(f"💾 Total RAM: {memory_gb:.1f} GB")
        
        if memory_gb >= 8:
            print("✅ Sufficient memory for large file processing")
        elif memory_gb >= 4:
            print("⚠️  Limited memory - may struggle with very large files")
        else:
            print("❌ Low memory - consider upgrading for better performance")
        
        # Check disk space
        disk = psutil.disk_usage('.')
        disk_gb = disk.free / (1024**3)
        print(f"💽 Available disk space: {disk_gb:.1f} GB")
        
        if disk_gb >= 10:
            print("✅ Sufficient disk space")
        else:
            print("⚠️  Low disk space - may need cleanup for large exports")
            
    except ImportError:
        print("ℹ️  psutil not available - cannot check system resources")
        print("   Install with: pip install psutil")
    except Exception as e:
        print(f"⚠️  Could not check system resources: {e}")

def main():
    """Main system requirements check."""
    print("🚀 KI Analysetool System Requirements Check")
    print("=" * 50)
    
    get_system_info()
    
    checks = []
    
    # Core system checks
    checks.append(("Tesseract OCR", check_tesseract_installation))
    checks.append(("Python Dev Tools", check_python_dev_tools))
    checks.append(("GUI Support", check_gui_support))
    
    # Run checks
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
            print()
        except Exception as e:
            print(f"❌ {name} - Unexpected error: {e}")
            results.append((name, False))
            print()
    
    # Additional system info
    check_memory_and_disk()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 SYSTEM CHECK SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 System requirements satisfied!")
        print("✅ Ready to run KI Analysetool")
    else:
        failed = total - passed
        print(f"❌ Failed: {failed}/{total}")
        print("🔧 Please install missing dependencies and run again")
    
    print("\n💡 Next steps:")
    print("   1. Run: python setup_validation.py")
    print("   2. Configure your OpenAI API key")
    print("   3. Start the application: python main.py")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())