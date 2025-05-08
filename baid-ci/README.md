# BAID-CI

[![PyPI version](https://img.shields.io/pypi/v/baid-ci.svg)](https://pypi.org/project/baid-ci/)
[![Python Versions](https://img.shields.io/pypi/pyversions/baid-ci.svg)](https://pypi.org/project/baid-ci/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://github.com/beskar-ai/baid-ci/actions/workflows/build.yml/badge.svg)](https://github.com/beskar-ai/baid-ci/actions)

BAID-CI is a powerful tool for diagnosing and automatically fixing CI pipeline errors using AI.

## Features

- **Error Analysis**: Get detailed explanations of CI errors
- **Auto-Fix**: Automatically fix common CI issues with a single command
- **Simple Interface**: Easy-to-use command line tool
- **Secure Authentication**: OAuth-based authentication with BAID.dev services

## Installation

### From PyPI

```bash
pip install baid-ci
```

### From Source

```bash
git clone https://github.com/beskar-ai/baid-ci.git
cd baid-ci
pip install -e .
```

## Usage

### Authentication

Before using BAID-CI, you need to authenticate:

```bash
baid-ci login
```

This will open a browser for Google authentication and connect your account to BAID.dev services.

### Running Commands with Error Analysis

To run a command and analyze any errors:

```bash
baid-ci run "your-command"
```

For example:

```bash
baid-ci run "npm test"
```

If the command fails, BAID-CI will analyze the error and suggest a fix.

### Auto-Fixing Errors

To automatically attempt to fix errors:

```bash
baid-ci run --auto-fix "your-command"
```

For example:

```bash
baid-ci run --auto-fix "pip install -r requirements.txt"
```

### Other Commands

```bash
# View version information
baid-ci version

# Log out
baid-ci logout
```

## Examples

### Fixing Dependency Conflicts

```bash
$ baid-ci run --auto-fix "pip install -r requirements.txt"
Running command: pip install -r requirements.txt
ERROR: Could not install packages due to an EnvironmentError: [Errno 2] No such file or directory: 'requirements.txt'

Command failed with exit code 1

🔧 AUTO-FIX ATTEMPT

Attempt 1/5:
Analyzing error with BAID.dev AI...
📋 Trying suggested fix: `touch requirements.txt`
Running command: touch requirements.txt
✅ Fix command executed successfully!

🔄 Running original command again: `pip install -r requirements.txt`
Running command: pip install -r requirements.txt
Successfully installed pip-22.0.4

🎉 AUTO-FIX SUCCESSFUL
The issue was fixed by running: `touch requirements.txt`
```

### Fixing Command Typos

```bash
$ baid-ci run --auto-fix "gti status"
Running command: gti status
bash: gti: command not found

Command failed with exit code 127

🔧 AUTO-FIX ATTEMPT

Attempt 1/5:
Analyzing error with BAID.dev AI...
📋 Found corrected command: `git status`
🔄 Running corrected command: `git status`
Running command: git status
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean

🎉 AUTO-FIX SUCCESSFUL
The issue was a typo in the command. Use `git status` instead of `gti status`.
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For support, please contact support@beskar.tech or visit [baid.dev](https://baid.dev).