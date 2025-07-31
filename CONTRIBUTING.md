# Contributing to Cert Me Boi

Thank you for your interest in contributing to Cert Me Boi! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues
- Use the [GitHub Issues](https://github.com/yourusername/cert_me_boi/issues) page
- Include detailed information about the problem
- Provide steps to reproduce the issue
- Include system information and error logs

### Feature Requests
- Submit feature requests through [GitHub Issues](https://github.com/yourusername/cert_me_boi/issues)
- Describe the feature and its benefits
- Include use cases and examples

### Code Contributions
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Add tests for new functionality
5. Run the test suite: `python -m pytest tests/`
6. Commit your changes: `git commit -m 'Add amazing feature'`
7. Push to the branch: `git push origin feature/amazing-feature`
8. Open a Pull Request

## 🛠️ Development Setup

### Prerequisites
- Python 3.13+
- Git
- pip

### Local Development
```bash
# Clone the repository
git clone https://github.com/yourusername/cert_me_boi.git
cd cert_me_boi

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
python -m pytest tests/

# Run linting
python -m flake8 src/
python -m black src/
```

## 📝 Code Style

### Python
- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes
- Keep functions small and focused
- Use meaningful variable and function names

### Example
```python
from typing import Dict, List, Optional

def process_course_data(
    course_url: str,
    credentials: Dict[str, str],
    options: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Process course data and return success status.
    
    Args:
        course_url: The URL of the course to process
        credentials: Dictionary containing login credentials
        options: Optional configuration options
        
    Returns:
        bool: True if processing was successful, False otherwise
        
    Raises:
        ValueError: If course_url is invalid
        AuthenticationError: If credentials are invalid
    """
    # Implementation here
    pass
```

### Documentation
- Update README.md for user-facing changes
- Add docstrings for new functions and classes
- Update inline comments for complex logic
- Keep documentation up to date with code changes

## 🧪 Testing

### Writing Tests
- Write tests for all new functionality
- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies
- Aim for high test coverage

### Example Test
```python
import pytest
from unittest.mock import Mock, patch
from src.automation.course_automation import CourseAutomation

def test_course_automation_login_success():
    """Test successful course login."""
    automation = CourseAutomation()
    mock_browser = Mock()
    mock_browser.page.fill.return_value = None
    mock_browser.page.click.return_value = None
    
    with patch.object(automation, 'browser', mock_browser):
        result = automation.login_to_course(
            "https://coursera.org/learn/python",
            "test@example.com",
            "password123"
        )
        
    assert result is True
    mock_browser.page.fill.assert_called()
    mock_browser.page.click.assert_called()

def test_course_automation_login_failure():
    """Test failed course login."""
    automation = CourseAutomation()
    mock_browser = Mock()
    mock_browser.page.fill.side_effect = Exception("Login failed")
    
    with patch.object(automation, 'browser', mock_browser):
        result = automation.login_to_course(
            "https://coursera.org/learn/python",
            "test@example.com",
            "wrongpassword"
        )
        
    assert result is False
```

### Running Tests
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src

# Run specific test file
python -m pytest tests/test_automation.py

# Run with verbose output
python -m pytest -v
```

## 🔧 Configuration

### Adding New Platforms
1. Add platform configuration to `config/courses.yaml`
2. Implement platform-specific selectors in `src/automation/`
3. Add tests for the new platform
4. Update documentation

### Adding New AI Models
1. Add model configuration to `config/courses.yaml`
2. Implement model handling in `src/ai/model_handler.py`
3. Add tests for the new model
4. Update the GUI to include the new model

## 📋 Pull Request Checklist

Before submitting a pull request, ensure:

- [ ] Code follows the project's style guidelines
- [ ] All tests pass
- [ ] New functionality has tests
- [ ] Documentation is updated
- [ ] No sensitive data is included
- [ ] Commit messages are clear and descriptive
- [ ] Branch is up to date with main

## 🚀 Release Process

### Versioning
We use [Semantic Versioning](https://semver.org/):
- MAJOR version for incompatible API changes
- MINOR version for backwards-compatible functionality
- PATCH version for backwards-compatible bug fixes

### Release Steps
1. Update version in `setup.py` and `__init__.py`
2. Update CHANGELOG.md
3. Create a release tag
4. Update documentation if needed

## 🆘 Getting Help

- **Issues**: [GitHub Issues](https://github.com/yourusername/cert_me_boi/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/cert_me_boi/discussions)
- **Wiki**: [Project Wiki](https://github.com/yourusername/cert_me_boi/wiki)

## 📄 License

By contributing to Cert Me Boi, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Cert Me Boi! 🎓 