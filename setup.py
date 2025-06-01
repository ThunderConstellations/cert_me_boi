"""Setup script for cert_me_boi package"""

from setuptools import setup, find_packages

setup(
    name="cert_me_boi",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.7",
    install_requires=[
        "playwright>=1.52.0",
        "opencv-python>=4.11.0",
        "pytesseract>=0.3.10",
        "numpy>=2.2.6",
        "Pillow>=11.2.1",
        "requests>=2.32.3",
        "httpx>=0.28.1",
        "urllib3>=2.4.0",
        "transformers>=4.52.4",
        "torch>=2.7.0",
        "tokenizers>=0.21.1",
        "PyYAML>=6.0.2",
        "python-dotenv>=1.1.0",
        "pydantic>=2.11.5",
    ],
    extras_require={
        "dev": [
            "pytest>=8.3.5",
            "pytest-cov>=6.1.1",
            "black>=25.1.0",
            "flake8>=7.2.0",
            "mypy>=1.16.0",
            "isort>=6.0.1",
        ],
        "test": [
            "pytest>=8.3.5",
            "pytest-cov>=6.1.1",
        ],
    },
    entry_points={
        "console_scripts": [
            "cert-me-boi=src.main:main",
        ],
    },
    package_data={
        "cert_me_boi": [
            "config/*.yaml",
            "data/templates/*.png",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Education",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
) 