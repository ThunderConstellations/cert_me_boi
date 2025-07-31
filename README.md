# Cert Me Boi - Automated Course Certification System

An intelligent automation system for completing free online certification courses using browser automation, screen monitoring, and AI assistance.

## Features

- **Browser Automation**: Uses Playwright for reliable browser control
- **Screen Monitoring**: Real-time screen capture and analysis for progress tracking
- **AI Integration**: Hugging Face models and OpenRouter for intelligent course interaction
- **Multi-Platform Support**: Coursera, edX, and extensible platform system
- **Progress Tracking**: Automated video progress detection and quiz/assignment solving
- **Certificate Download**: Automatic certificate retrieval upon completion
- **Error Recovery**: Robust error handling with automatic retry mechanisms
- **CLI Interface**: Easy-to-use command-line interface

## Prerequisites

- Python 3.8+
- Playwright browsers
- Free accounts on course platforms
- CUDA-compatible GPU (optional, for faster AI processing)
- Windows 10/11 or Linux

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/cert_me_boi.git
   cd cert_me_boi
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers**:
   ```bash
   playwright install
   ```

4. (Optional) Set up OpenRouter API:
   - Get an API key from [OpenRouter](https://openrouter.ai)
   - Add the key to the configuration file

## Usage

1. Basic usage:
   ```bash
   python cli.py run --course-url "https://coursera.org/learn/python" --email "user@example.com" --password "password"
   ```

2. Custom configuration:
   ```python
   from src.main import CertificationAutomation
   
   automation = CertificationAutomation("path/to/custom/config.yaml")
   ```

## Project Structure

```
cert_me_boi/
├── config/
│   └── courses.yaml       # Configuration file
├── data/
│   ├── certificates/      # Completed certificates
│   ├── courses/          # Course-specific data
│   ├── screenshots/      # Captured screenshots
│   └── templates/        # Image templates for matching
├── logs/                 # Application logs
└── src/
    ├── ai/              # AI model handling
    ├── automation/      # Browser automation
    ├── monitor/         # Screen monitoring
    └── utils/           # Utility functions
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for educational purposes only. Users are responsible for:
- Complying with course platform terms of service
- Ensuring they have permission to use automation tools
- Following academic integrity policies
- Respecting intellectual property rights

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs in `logs/` directory
3. Run `python cli.py status` for system diagnostics
4. Create an issue with detailed error information
