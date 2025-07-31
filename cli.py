#!/usr/bin/env python3
"""
Certification Automation CLI

Command-line interface for the automated course certification system.
"""

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.main import CertificationAutomation
from src.utils.logger import get_logger

logger = get_logger(__name__)


def run_automation(args):
    """Run course automation with provided credentials."""
    try:
        automation = CertificationAutomation()
        automation.initialize_components()
        
        credentials = {
            "email": args.email,
            "password": args.password
        }
        
        success = automation.run_course_automation(args.course_url, credentials)
        
        if success:
            print("✅ Course automation completed successfully!")
            return 0
        else:
            print("❌ Course automation failed")
            return 1
            
    except Exception as e:
        logger.error(f"Automation failed: {e}")
        print(f"❌ Error: {e}")
        return 1


def run_demo(args):
    """Run demonstration mode."""
    try:
        from demo import main as demo_main
        demo_main()
        return 0
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"❌ Demo error: {e}")
        return 1


def run_tests(args):
    """Run test suite."""
    try:
        import subprocess
        result = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"], 
                              capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        return result.returncode
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        print(f"❌ Test error: {e}")
        return 1


def show_status(args):
    """Show system status."""
    try:
        automation = CertificationAutomation()
        
        print("🔍 System Status Check")
        print("=" * 40)
        
        # Check configuration
        print("📋 Configuration:")
        if automation.config:
            print("  ✅ Configuration loaded")
            print(f"  📁 Config file: {automation.config_file}")
        else:
            print("  ❌ Configuration not loaded")
        
        # Check directories
        print("\n📁 Directories:")
        data_dir = Path("data")
        if data_dir.exists():
            print("  ✅ Data directory exists")
        else:
            print("  ❌ Data directory missing")
            
        logs_dir = Path("logs")
        if logs_dir.exists():
            print("  ✅ Logs directory exists")
        else:
            print("  ❌ Logs directory missing")
        
        # Check dependencies
        print("\n🔧 Dependencies:")
        try:
            import playwright
            print("  ✅ Playwright installed")
        except ImportError:
            print("  ❌ Playwright not installed")
            
        try:
            import opencv
            print("  ✅ OpenCV installed")
        except ImportError:
            print("  ❌ OpenCV not installed")
            
        try:
            import transformers
            print("  ✅ Transformers installed")
        except ImportError:
            print("  ❌ Transformers not installed")
        
        print("\n✅ Status check completed")
        return 0
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        print(f"❌ Status error: {e}")
        return 1


def show_help(args):
    """Show detailed help."""
    help_text = """
Certification Automation System - Detailed Help

COMMANDS:
  run      - Run course automation
  demo     - Run demonstration mode
  test     - Run test suite
  status   - Show system status
  help     - Show this help

EXAMPLES:

1. Run course automation:
   python cli.py run --course-url "https://coursera.org/learn/python" \\
                    --email "user@example.com" \\
                    --password "password123"

2. Run demo:
   python cli.py demo

3. Run tests:
   python cli.py test

4. Check system status:
   python cli.py status

CONFIGURATION:
  - Edit config/courses.yaml for course settings
  - Edit config/monitor.yaml for screen monitoring settings
  - Edit config/error_handling.yaml for error handling settings

TROUBLESHOOTING:
  - Check logs/ directory for detailed error logs
  - Run 'python cli.py status' to verify system setup
  - Ensure all dependencies are installed: pip install -r requirements.txt
  - Install Playwright browsers: playwright install

For more information, see README.md
"""
    print(help_text)
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Certification Automation CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py run --course-url "https://coursera.org/learn/python" --email "user@example.com" --password "password123"
  python cli.py demo
  python cli.py test
  python cli.py status
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run course automation')
    run_parser.add_argument('--course-url', required=True, help='Course URL')
    run_parser.add_argument('--email', required=True, help='Login email')
    run_parser.add_argument('--password', required=True, help='Login password')
    run_parser.set_defaults(func=run_automation)
    
    # Demo command
    demo_parser = subparsers.add_parser('demo', help='Run demonstration mode')
    demo_parser.set_defaults(func=run_demo)
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run test suite')
    test_parser.set_defaults(func=run_tests)
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show system status')
    status_parser.set_defaults(func=show_status)
    
    # Help command
    help_parser = subparsers.add_parser('help', help='Show detailed help')
    help_parser.set_defaults(func=show_help)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main()) 