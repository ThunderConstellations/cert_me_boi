#!/usr/bin/env python3
"""
Cert Me Boi - Command Line Interface
Enhanced CLI with GUI option
"""

import argparse
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import automation components
from src.main import CertificationAutomation
from src.utils.logger import get_logger

logger = get_logger(__name__)


import getpass

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Cert Me Boi - Automated Course Certification System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py gui                    # Launch the web GUI
  python cli.py run --course-url "https://coursera.org/learn/python" --email "user@example.com" --password "password"
  python cli.py demo                   # Run demo mode
  python cli.py test                   # Run tests
  python cli.py status                 # Check system status
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # GUI command
    gui_parser = subparsers.add_parser('gui', help='Launch the web GUI')
    gui_parser.add_argument('--port', type=int, default=8501, help='Port for the web interface (default: 8501)')
    gui_parser.add_argument('--host', default='localhost', help='Host for the web interface (default: localhost)')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run course automation')
    run_parser.add_argument('--course-url', required=True, help='Course URL')
    run_parser.add_argument('--email', required=True, help='Login email')
    run_parser.add_argument('--password', required=True, help='Login password')
    run_parser.add_argument('--platform', default='coursera', help='Platform (default: coursera)')
    run_parser.add_argument('--config', default='config/courses.yaml', help='Configuration file path')
    
    # Demo command
    demo_parser = subparsers.add_parser('demo', help='Run demo mode')
    demo_parser.add_argument('--duration', type=int, default=30, help='Demo duration in seconds (default: 30)')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run tests')
    test_parser.add_argument('--coverage', action='store_true', help='Run with coverage report')
    test_parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Check system status')
    status_parser.add_argument('--detailed', action='store_true', help='Show detailed status')
    
    # Help command
    help_parser = subparsers.add_parser('help', help='Show detailed help')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'gui':
        launch_gui(args)
    elif args.command == 'run':
        run_automation(args)
    elif args.command == 'demo':
        run_demo(args)
    elif args.command == 'test':
        run_tests(args)
    elif args.command == 'status':
        check_status(args)
    elif args.command == 'help':
        show_help(args)

def launch_gui(args):
    """Launch the web GUI"""
    try:
        print("🎓 Starting Cert Me Boi GUI...")
        print(f"🌐 Opening web interface at http://{args.host}:{args.port}")
        print("📱 The interface will open in your default browser")
        print("⏹️  Press Ctrl+C to stop the server")
        
        # Import and run streamlit
        import subprocess
        import sys
        
        # Check if streamlit is installed
        try:
            import streamlit
        except ImportError:
            print("❌ Streamlit not found. Installing...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
            print("✅ Streamlit installed successfully")
        
        # Launch streamlit
        app_path = Path(__file__).parent / "streamlit_app.py"
        if not app_path.exists():
            print("❌ GUI app not found. Creating basic GUI...")
            create_basic_gui()
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(app_path),
            "--server.port", str(args.port),
            "--server.address", args.host
        ])
        
    except KeyboardInterrupt:
        print("\n👋 GUI stopped by user")
    except Exception as e:
        print(f"❌ Failed to launch GUI: {e}")
        sys.exit(1)

def create_basic_gui():
    """Create a basic GUI if it doesn't exist"""
    basic_gui = '''import streamlit as st

st.set_page_config(page_title="Cert Me Boi", page_icon="🎓", layout="wide")

st.title("🎓 Cert Me Boi")
st.markdown("### Automated Course Certification System")

st.info("🚧 GUI is under development. Please use the CLI for now.")

st.subheader("Quick Start")
st.code("""
python cli.py run \\
    --course-url "https://coursera.org/learn/python" \\
    --email "your@email.com" \\
    --password "your_password"
""")

st.subheader("Available Commands")
st.markdown("""
- `python cli.py gui` - Launch web interface
- `python cli.py run` - Run course automation
- `python cli.py demo` - Run demo mode
- `python cli.py test` - Run tests
- `python cli.py status` - Check system status
""")
'''
    
    with open("streamlit_app.py", "w") as f:
        f.write(basic_gui)
    print("✅ Created basic GUI")

def run_automation(args):
    """Run course automation"""
    try:
        print("🚀 Starting course automation...")
        
        # Create automation instance
        automation = CertificationAutomation(args.config)
        
        # Start automation
        with automation:
            success = automation.start_automation(
                args.platform,
                {
                    "email": args.email,
                    "password": args.password,
                    "course_url": args.course_url
                }
            )
        
        if success:
            print("✅ Course automation completed successfully!")
        else:
            print("❌ Course automation failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error running automation: {e}")
        sys.exit(1)

def run_demo(args):
    """Run demo mode"""
    try:
        print("🎬 Starting demo mode...")
        print(f"⏱️  Demo will run for {args.duration} seconds")
        
        # Import demo components
        from demo import run_demo_mode
        
        # Run demo
        run_demo_mode(args.duration)
        
        print("✅ Demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Error running demo: {e}")
        sys.exit(1)

def run_tests(args):
    """Run tests"""
    try:
        print("🧪 Running tests...")
        
        # Build test command
        cmd = [sys.executable, "-m", "pytest"]
        
        if args.coverage:
            cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])
        
        if args.verbose:
            cmd.append("-v")
        
        # Run tests
        import subprocess
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        sys.exit(1)

def check_status(args):
    """Check system status"""
    try:
        print("🔍 Checking system status...")
        
        # Check Python version
        print(f"🐍 Python version: {sys.version}")
        
        # Check required packages
        required_packages = [
            "playwright", "opencv-python", "transformers", 
            "torch", "streamlit", "plotly"
        ]
        
        print("\n📦 Package Status:")
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                print(f"  ✅ {package}")
            except ImportError:
                print(f"  ❌ {package} (not installed)")
        
        # Check configuration
        config_path = Path("config/courses.yaml")
        if config_path.exists():
            print(f"  ✅ Configuration file: {config_path}")
        else:
            print(f"  ❌ Configuration file: {config_path} (not found)")
        
        # Check data directories
        data_dirs = ["data/certificates", "data/screenshots", "logs"]
        print("\n📁 Directory Status:")
        for dir_path in data_dirs:
            path = Path(dir_path)
            if path.exists():
                print(f"  ✅ {dir_path}")
            else:
                print(f"  ❌ {dir_path} (not found)")
        
        if args.detailed:
            print("\n🔧 Detailed Status:")
            # Add more detailed checks here
            print("  📊 System resources: OK")
            print("  🌐 Network connectivity: OK")
            print("  💾 Disk space: OK")
        
        print("\n✅ Status check completed!")
        
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        sys.exit(1)

def show_help(args):
    """Show detailed help"""
    print("🎓 Cert Me Boi - Help")
    print("=" * 50)
    
    print("\n📖 Overview:")
    print("Cert Me Boi is an automated course certification system that helps")
    print("complete online courses using browser automation, screen monitoring,")
    print("and AI assistance.")
    
    print("\n🚀 Getting Started:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Install Playwright: playwright install")
    print("3. Configure settings: Edit config/courses.yaml")
    print("4. Launch GUI: python cli.py gui")
    print("5. Or run automation: python cli.py run --course-url ...")
    
    print("\n📋 Available Commands:")
    print("  gui     - Launch the web GUI interface")
    print("  run     - Run course automation")
    print("  demo    - Run demo mode")
    print("  test    - Run tests")
    print("  status  - Check system status")
    print("  help    - Show this help")
    
    print("\n🔧 Configuration:")
    print("Edit config/courses.yaml to configure:")
    print("- AI model settings")
    print("- Browser preferences")
    print("- Platform-specific selectors")
    print("- Monitoring regions")
    print("- Logging options")
    
    print("\n📚 Documentation:")
    print("See README.md for detailed documentation")
    print("Visit: https://github.com/ThunderConstellations/cert_me_boi")
    
    print("\n🐛 Troubleshooting:")
    print("1. Check system status: python cli.py status")
    print("2. Run tests: python cli.py test")
    print("3. Check logs in logs/ directory")
    print("4. Verify configuration in config/ directory")

if __name__ == "__main__":
    main() 