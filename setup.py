#!/usr/bin/env python3
"""Setup script for ADWS Testing Framework."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    long_description = readme_path.read_text()

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = [
        line.strip()
        for line in requirements_path.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="adws-testing",
    version="0.1.0",
    author="ADWS Testing Team",
    description="Testing harness for standard-configuration project",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/adws-testing",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "adws-test=cli:cli",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="testing automation claude ai llm",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/adws-testing/issues",
        "Source": "https://github.com/yourusername/adws-testing",
    },
)