#!/usr/bin/env python3
"""
Setup script for Cert Me Boi
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="cert-me-boi",
    version="1.0.0",
    author="ThunderConstellations",
    author_email="your.email@example.com",
    description="Automated Course Certification System powered by AI",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/ThunderConstellations/cert_me_boi",
    project_urls={
        "Bug Tracker": "https://github.com/ThunderConstellations/cert_me_boi/issues",
        "Documentation": "https://github.com/ThunderConstellations/cert_me_boi/wiki",
        "Source Code": "https://github.com/ThunderConstellations/cert_me_boi",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.13",
        "Topic :: Education",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.13",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "cert-me-boi=cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json"],
    },
    keywords="automation, education, ai, certification, courses, learning",
    license="MIT",
    platforms=["Windows", "Linux", "macOS"],
) 