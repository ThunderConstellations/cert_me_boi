#!/usr/bin/env python3
"""
Certification Automation Demo

Demonstration script showcasing the core functionality of the project.
"""

import sys
from pathlib import Path
import time

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.main import CertificationAutomation
from src.monitor.screen_monitor import ScreenMonitor
from src.ai.model_handler import ModelHandler
from src.automation.browser import Browser
from src.utils.logger import get_logger

logger = get_logger(__name__)


def demo_components():
    """Demonstrate individual components."""
    print("🎯 Component Demo")
    print("=" * 50)
    
    # Screen Monitor Demo
    print("\n📸 Screen Monitor Demo:")
    try:
        monitor = ScreenMonitor()
        screenshot_path = monitor.save_screenshot("demo_screenshot")
        print(f"  ✅ Screenshot saved: {screenshot_path}")
        
        motion_detected = monitor.detect_motion()
        print(f"  ✅ Motion detection: {'Yes' if motion_detected else 'No'}")
        
        progress = monitor.detect_progress_bar()
        print(f"  ✅ Progress detection: {progress}%")
        
    except Exception as e:
        print(f"  ❌ Screen monitor error: {e}")
    
    # AI Model Handler Demo
    print("\n🤖 AI Model Handler Demo:")
    try:
        ai = ModelHandler()
        ai.load_model()
        print("  ✅ AI model loaded successfully")
        
        # Test simple question
        question = "What is the capital of France?"
        answer = ai.answer_quiz_question(question)
        print(f"  ✅ Quiz answer: {answer}")
        
    except Exception as e:
        print(f"  ❌ AI model error: {e}")
    
    # Browser Demo
    print("\n🌐 Browser Demo:")
    try:
        browser = Browser()
        browser.start()
        print("  ✅ Browser started successfully")
        
        # Navigate to a test page
        browser.navigate("https://example.com")
        print("  ✅ Navigation successful")
        
        browser.cleanup()
        print("  ✅ Browser cleanup successful")
        
    except Exception as e:
        print(f"  ❌ Browser error: {e}")


def demo_full_automation():
    """Demonstrate full automation workflow."""
    print("\n🚀 Full Automation Demo")
    print("=" * 50)
    
    try:
        automation = CertificationAutomation()
        automation.initialize_components()
        print("  ✅ Components initialized")
        
        # Demo credentials (not real)
        credentials = {
            "email": "demo@example.com",
            "password": "demo_password"
        }
        
        # Demo course URL
        course_url = "https://coursera.org/learn/python-programming"
        
        print(f"  📚 Course URL: {course_url}")
        print(f"  👤 Email: {credentials['email']}")
        print("  🔒 Password: [hidden]")
        
        # Note: This is a demo, so we won't actually run the automation
        print("  ⚠️  Demo mode - automation not actually executed")
        print("  ✅ Demo completed successfully")
        
    except Exception as e:
        print(f"  ❌ Full automation error: {e}")


def demo_cli():
    """Demonstrate CLI functionality."""
    print("\n💻 CLI Demo")
    print("=" * 50)
    
    try:
        import subprocess
        
        # Test status command
        print("  📊 Testing status command:")
        result = subprocess.run([sys.executable, "cli.py", "status"], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("  ✅ Status command works")
        else:
            print(f"  ❌ Status command failed: {result.stderr}")
        
        # Test help command
        print("  📖 Testing help command:")
        result = subprocess.run([sys.executable, "cli.py", "help"], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("  ✅ Help command works")
        else:
            print(f"  ❌ Help command failed: {result.stderr}")
            
    except Exception as e:
        print(f"  ❌ CLI demo error: {e}")


def main():
    """Main demo function."""
    print("🎓 Certification Automation System - Demo")
    print("=" * 60)
    print("This demo showcases the core functionality of the system.")
    print("Note: This is a demonstration and does not perform actual automation.")
    print()
    
    # Run component demos
    demo_components()
    
    # Run full automation demo
    demo_full_automation()
    
    # Run CLI demo
    demo_cli()
    
    print("\n" + "=" * 60)
    print("🎉 Demo completed successfully!")
    print("\nTo run actual automation:")
    print("  python cli.py run --course-url <URL> --email <EMAIL> --password <PASSWORD>")
    print("\nFor more information:")
    print("  python cli.py help")


if __name__ == "__main__":
    main() 