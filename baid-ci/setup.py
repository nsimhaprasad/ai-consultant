#!/usr/bin/env python3
"""
Setup script for BAID-CI package
"""

import os
from setuptools import setup, find_packages

# Read the contents of README.md for the long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read version from the package
about = {}
with open(os.path.join("baid_ci", "__init__.py"), encoding="utf-8") as f:
    exec(f.read(), about)

setup(
    name="baid-ci",
    version=about["__version__"],
    author=about["__author__"],
    author_email=about["__email__"],
    description="A CI error analyzer tool using BAID.dev AI services",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/beskar-ai/baid-ci",
    project_urls={
        "Bug Tracker": "https://github.com/beskar-ai/baid-ci/issues",
        "Documentation": "https://docs.baid.dev/",
        "Source Code": "https://github.com/beskar-ai/baid-ci",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Quality Assurance",
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
            "pyarmor>=6.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "baid-ci=baid_ci.cli:main",
        ],
    },
)