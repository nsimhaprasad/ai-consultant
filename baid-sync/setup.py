#!/usr/bin/env python3
"""
Setup script for BAID-Sync package
"""

import os
from setuptools import setup, find_packages

# Read the contents of README.md for the long description
readme_path = os.path.join(os.path.dirname(__file__), "README.md")
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as fh:
        long_description = fh.read()
else:
    long_description = "BAID-Sync: Directory synchronization tool for Google Cloud Storage"

# Read version from the package
about = {}
with open(os.path.join("baid_sync", "__init__.py"), encoding="utf-8") as f:
    exec(f.read(), about)

setup(
    name="baid-sync",
    version=about["__version__"],
    author=about["__author__"],
    author_email=about["__email__"],
    description="Directory synchronization tool for Google Cloud Storage via BAID.dev",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/beskar-ai/baid-sync",
    project_urls={
        "Bug Tracker": "https://github.com/beskar-ai/baid-sync/issues",
        "Documentation": "https://docs.baid.dev/",
        "Source Code": "https://github.com/beskar-ai/baid-sync",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Software Development :: Build Tools",
        "Topic :: System :: Archiving :: Backup",
        "Topic :: Internet :: File Transfer Protocol (FTP)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
        "urllib3>=1.26.0",
        "cryptography>=36.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.12.0",
            "black>=21.5b2",
            "isort>=5.9.1",
            "flake8>=3.9.2",
            "mypy>=0.812",
            "pyinstaller>=5.0.0",
            "build>=0.7.0",
            "twine>=3.4.1",
        ],
    },
    entry_points={
        "console_scripts": [
            "baid-sync=baid_sync.cli:main",
        ],
    },
)