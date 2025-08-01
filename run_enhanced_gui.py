#!/usr/bin/env python3
"""
Enhanced Cert Me Boi GUI Launcher
Launches the professional lightning-themed interface with content recording
"""

import sys
import os
import subprocess
import logging
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def setup_logging():
    """Setup logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/gui.log'),
            logging.StreamHandler()
        ]
    )

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'streamlit',
        'plotly',
        'pandas',
        'numpy',
        'playwright',
        'asyncio'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("⚠️  Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Install missing packages with:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True

def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        'data/certificates',
        'data/screenshots', 
        'data/knowledge_base',
        'logs',
        'tmp'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def main():
    """Main launcher function"""
    print("⚡ Cert Me Boi - Enhanced Lightning GUI")
    print("=" * 50)
    
    # Setup
    setup_logging()
    ensure_directories()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Launch enhanced Streamlit app
    print("🚀 Launching enhanced GUI with lightning animations...")
    print("🌟 Features included:")
    print("   ⚡ Lightning bolt animations")
    print("   ⭐ Constellation background")
    print("   📚 Content recording system") 
    print("   🎯 Interactive knowledge base")
    print("   📊 Advanced analytics")
    print("   🎮 Gamification elements")
    print("\n🌐 Open your browser to: http://localhost:8501")
    
    # Run Streamlit app
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "src/gui/enhanced_streamlit_app.py",
            "--server.port=8501",
            "--server.address=localhost",
            "--theme.base=dark",
            "--theme.primaryColor=#FFD700",
            "--theme.backgroundColor=#0a0a23",
            "--theme.secondaryBackgroundColor=#1a1a3e"
        ])
    except KeyboardInterrupt:
        print("\n⚡ Lightning automation stopped!")
        print("💫 Thanks for using Cert Me Boi!")
    except Exception as e:
        logging.error(f"Failed to launch GUI: {e}")
        print(f"❌ Error launching GUI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 