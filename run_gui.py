#!/usr/bin/env python3
"""
Cert Me Boi GUI Launcher
Launches the Streamlit web interface
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Launch the Streamlit GUI"""
    print("🎓 Starting Cert Me Boi GUI...")
    
    # Check if streamlit is installed
    try:
        import streamlit
        print("✅ Streamlit is installed")
    except ImportError:
        print("❌ Streamlit not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
        print("✅ Streamlit installed successfully")
    
    # Launch the GUI
    app_path = Path(__file__).parent / "streamlit_app.py"
    
    if not app_path.exists():
        print(f"❌ GUI app not found at {app_path}")
        return
    
    print("🚀 Launching web interface...")
    print("📱 Open your browser to the URL shown below")
    print("🔗 The interface will be available at http://localhost:8501")
    
    # Run streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", 
        str(app_path),
        "--server.port", "8501",
        "--server.address", "localhost"
    ])

if __name__ == "__main__":
    main() 