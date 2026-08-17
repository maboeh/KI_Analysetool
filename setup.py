#!/usr/bin/env python3
"""
Complete Setup Script for KI Analysetool
Installs dependencies, configures the environment, and validates the setup.
"""

import sys
import subprocess
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and return success status."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"   stdout: {e.stdout}")
        if e.stderr:
            print(f"   stderr: {e.stderr}")
        return False

def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing Python Dependencies")
    print("-" * 40)
    
    # Upgrade pip first
    if not run_command(f"{sys.executable} -m pip install --upgrade pip", 
                      "Upgrading pip"):
        return False
    
    # Install from requirements.txt
    if not run_command(f"{sys.executable} -m pip install -r requirements.txt", 
                      "Installing requirements"):
        return False
    
    return True

def configure_environment():
    """Configure the environment."""
    print("\n⚙️  Configuring Environment")
    print("-" * 30)
    
    # Configure matplotlib
    if not run_command(f"{sys.executable} configure_matplotlib.py", 
                      "Configuring matplotlib"):
        return False
    
    return True

def validate_setup():
    """Validate the complete setup."""
    print("\n🧪 Validating Setup")
    print("-" * 20)
    
    # Run system requirements check
    if not run_command(f"{sys.executable} system_requirements_check.py", 
                      "System requirements check"):
        return False
    
    # Run setup validation
    print("\n🔍 Running comprehensive validation...")
    result = subprocess.run([sys.executable, "setup_validation.py"], 
                          capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    # Return True even if API key is not configured (that's user-specific)
    return result.returncode in [0, 1]  # 1 is expected if API key is missing

def create_sample_config():
    """Create a sample configuration file."""
    config_path = Path("config.ini")
    if not config_path.exists():
        print("📝 Creating sample configuration file...")
        sample_config = """[API]
# Replace with your actual OpenAI API key
openai_api_key = your_openai_api_key_here

[SETTINGS]
# Default analysis language
language = de

# Maximum file size for processing (in MB)
max_file_size = 100

# Default export format
export_format = pdf
"""
        config_path.write_text(sample_config)
        print("✅ Sample config.ini created")
        print("   Please edit config.ini and add your OpenAI API key")
    else:
        print("ℹ️  config.ini already exists")

def print_next_steps():
    """Print next steps for the user."""
    print("\n" + "=" * 50)
    print("🎉 SETUP COMPLETE!")
    print("=" * 50)
    
    print("\n📋 Next Steps:")
    print("1. 🔑 Configure your OpenAI API key:")
    print("   - Edit config.ini and replace 'your_openai_api_key_here'")
    print("   - Or set environment variable: export OPENAI_API_KEY=your_key")
    print()
    print("2. 🚀 Start the application:")
    print("   python main.py")
    print()
    print("3. 📚 Read the documentation:")
    print("   - INSTALLATION.md for detailed setup instructions")
    print("   - README.md for usage guide (if available)")
    print()
    print("4. 🧪 Test the setup:")
    print("   python setup_validation.py")
    print()
    print("💡 Troubleshooting:")
    print("   - Run system_requirements_check.py for system-level issues")
    print("   - Check INSTALLATION.md for common problems")
    print("   - Ensure all dependencies are installed correctly")

def main():
    """Main setup function."""
    print("🚀 KI Analysetool Complete Setup")
    print("=" * 50)
    print("This script will install dependencies and configure the environment.")
    print()
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return 1
    
    success = True
    
    # Install dependencies
    if not install_dependencies():
        success = False
    
    # Configure environment
    if success and not configure_environment():
        success = False
    
    # Create sample config
    create_sample_config()
    
    # Validate setup
    if success and not validate_setup():
        success = False
    
    # Print results
    if success:
        print_next_steps()
        return 0
    else:
        print("\n❌ Setup failed. Please check the error messages above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())