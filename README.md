# Cert Me Boi - Automated Course Certification System

An intelligent automation system that helps complete online certification courses using browser automation, screen monitoring, and AI assistance.

## Features

- **Browser Automation**: Uses Playwright for reliable and stealth browser control
- **Screen Monitoring**: Real-time screen analysis for video progress and interactive elements
- **AI Integration**: 
  - Local AI models for text generation and analysis
  - OpenRouter API support for advanced language models
  - OCR capabilities for text extraction from images
- **Multi-Platform Support**: 
  - Coursera
  - More platforms coming soon
- **Intelligent Automation**:
  - Automatic video progress tracking
  - Quiz and assignment completion
  - Smart navigation between course sections
- **Robust Logging**: Comprehensive logging system with rotation for debugging and monitoring

## Requirements

- Python 3.8+
- CUDA-compatible GPU (optional, for faster AI processing)
- Windows 10/11 or Linux

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/cert_me_boi.git
cd cert_me_boi
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:
```bash
playwright install
```

## Configuration

1. Copy the example configuration:
```bash
cp config/courses.example.yaml config/courses.yaml
```

2. Edit `config/courses.yaml` to configure:
- Browser settings
- AI model preferences
- Platform-specific selectors
- Screen monitoring regions
- Logging preferences

3. (Optional) Set up OpenRouter API:
- Get an API key from [OpenRouter](https://openrouter.ai)
- Add the key to the configuration file

## Usage

1. Basic usage:
```python
from src.main import CertificationAutomation

credentials = {
    "email": "your_email@example.com",
    "password": "your_password"
}

with CertificationAutomation() as automation:
    automation.start_automation("coursera", credentials)
```

2. Custom configuration:
```python
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

## Disclaimer

This project is for educational purposes only. Please respect the terms of service of educational platforms and use responsibly.

## License

MIT License - see LICENSE file for details 