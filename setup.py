#!/usr/bin/env python3
"""
Setup script for Req2Run Benchmark Framework
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Read requirements
requirements = []
with open("requirements.txt", "r") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#"):
            requirements.append(line)

setup(
    name="req2run",
    version="1.0.0",
    author="ITDo Inc. Japan",
    author_email="contact@itdo.jp",
    description="Requirements-to-Running Code Benchmark Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/itdojp/req2run-benchmark",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "req2run=req2run.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "req2run": [
            "templates/*.html",
            "templates/*.md",
            "schemas/*.json",
        ],
    },
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0",
            "black>=23.12.1",
            "mypy>=1.8.0",
            "pre-commit>=3.6.0",
        ],
        "cloud": [
            "boto3>=1.34.11",
            "google-cloud-storage>=2.13.0",
            "azure-storage-blob>=12.19.0",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/itdojp/req2run-benchmark/issues",
        "Source": "https://github.com/itdojp/req2run-benchmark",
        "Documentation": "https://req2run.readthedocs.io",
    },
)