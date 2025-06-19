# BAID-Sync

Directory synchronization tool for Google Cloud Storage via BAID.dev backend services.

## Features

- **Continuous Sync**: Automatically sync your directories to Google Cloud Storage every 5 minutes (configurable)
- **One-time Sync**: Perform manual synchronization on demand
- **Smart Change Detection**: Only uploads when files have changed
- **Compression**: Creates compressed archives before upload to minimize transfer time
- **Authentication**: Supports both OAuth and API key authentication
- **Configurable Ignore Patterns**: Exclude files and directories from synchronization

## Installation

```bash
pip install -e .
```

## Usage

### Authentication

Before using baid-sync, you need to authenticate:

```bash
# Interactive OAuth login
baid-sync login

# Or use API key
baid-sync login --api-key YOUR_API_KEY
```

### Continuous Synchronization

Start continuous sync (default: every 5 minutes):

```bash
# Sync current directory
baid-sync start

# Sync specific directory
baid-sync start /path/to/project

# Custom sync interval (in minutes)
baid-sync start --interval 10

# With custom ignore patterns
baid-sync start --ignore "*.log" --ignore "temp/"
```

### One-time Synchronization

Perform a single sync:

```bash
# Sync current directory
baid-sync sync

# Sync specific directory
baid-sync sync /path/to/project
```

### Other Commands

```bash
# Show version
baid-sync version

# Logout
baid-sync logout
```

## Default Ignore Patterns

The following files and directories are ignored by default:

- `.git`
- `.gitignore`
- `__pycache__`
- `*.pyc`
- `.DS_Store`
- `node_modules`
- `.env`, `.venv`, `venv`
- `.pytest_cache`
- `.coverage`
- `dist`, `build`
- `*.egg-info`
- `.mypy_cache`
- `.idea`, `.vscode`

## Backend API

The tool expects the backend server to provide:

- `POST /api/sync/signed-url` - Get signed URL for Google Cloud Storage upload
- Standard authentication endpoints compatible with baid-ci

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Code formatting
black baid_sync/
isort baid_sync/
```

## License

Licensed for individual use only. Copyright 2025 Beskar AI Technologies.