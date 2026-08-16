#!/usr/bin/env python3
"""
Matplotlib Configuration for KI Analysetool
Configures matplotlib to work properly with Tkinter GUI.
"""

import matplotlib
import os
import sys
from pathlib import Path

def configure_matplotlib_for_tkinter():
    """Configure matplotlib to use TkAgg backend for Tkinter integration."""
    print("🔧 Configuring matplotlib for Tkinter integration...")
    
    try:
        # Set the backend to TkAgg for Tkinter compatibility
        matplotlib.use('TkAgg')
        
        # Import pyplot to test the configuration
        import matplotlib.pyplot as plt
        
        # Configure default settings for better integration
        plt.rcParams['figure.figsize'] = (8, 6)
        plt.rcParams['figure.dpi'] = 100
        plt.rcParams['savefig.dpi'] = 150
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.titlesize'] = 12
        plt.rcParams['axes.labelsize'] = 10
        plt.rcParams['xtick.labelsize'] = 9
        plt.rcParams['ytick.labelsize'] = 9
        plt.rcParams['legend.fontsize'] = 9
        
        # Set style for better appearance
        plt.style.use('default')
        
        print("✅ matplotlib configured successfully for Tkinter")
        return True
        
    except Exception as e:
        print(f"❌ Failed to configure matplotlib: {e}")
        return False

def create_matplotlib_config():
    """Create matplotlib configuration file if needed."""
    try:
        import matplotlib
        config_dir = matplotlib.get_configdir()
        config_file = Path(config_dir) / "matplotlibrc"
        
        print(f"📁 matplotlib config directory: {config_dir}")
        
        if not config_file.exists():
            print("📝 Creating matplotlib configuration file...")
            config_content = """
# matplotlib configuration for KI Analysetool
backend: TkAgg
figure.figsize: 8, 6
figure.dpi: 100
savefig.dpi: 150
font.size: 10
axes.titlesize: 12
axes.labelsize: 10
xtick.labelsize: 9
ytick.labelsize: 9
legend.fontsize: 9
"""
            config_file.write_text(config_content.strip())
            print("✅ matplotlib configuration file created")
        else:
            print("ℹ️  matplotlib configuration file already exists")
            
        return True
        
    except Exception as e:
        print(f"❌ Failed to create matplotlib config: {e}")
        return False

def test_matplotlib_tkinter():
    """Test matplotlib with Tkinter backend."""
    print("🧪 Testing matplotlib with Tkinter...")
    
    try:
        import matplotlib
        matplotlib.use('TkAgg')
        import matplotlib.pyplot as plt
        import numpy as np
        
        # Create a simple test plot
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        
        fig, ax = plt.subplots()
        ax.plot(x, y)
        ax.set_title('Test Plot')
        ax.set_xlabel('X axis')
        ax.set_ylabel('Y axis')
        
        # Don't show the plot, just test that it can be created
        plt.close(fig)
        
        print("✅ matplotlib Tkinter test passed")
        return True
        
    except Exception as e:
        print(f"❌ matplotlib Tkinter test failed: {e}")
        return False

def main():
    """Main configuration function."""
    print("🚀 matplotlib Configuration for KI Analysetool")
    print("=" * 50)
    
    success = True
    
    # Configure matplotlib
    if not configure_matplotlib_for_tkinter():
        success = False
    
    # Create config file
    if not create_matplotlib_config():
        success = False
    
    # Test the configuration
    if not test_matplotlib_tkinter():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 matplotlib configuration completed successfully!")
        print("✅ Ready for use with Tkinter GUI")
    else:
        print("❌ matplotlib configuration failed")
        print("🔧 Please check the error messages above")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())