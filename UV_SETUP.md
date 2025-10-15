# Using UV for Package Management

This project now uses `uv` - an ultra-fast Python package installer and resolver.

## Why UV?

- **10-100x faster** than pip
- **Better dependency resolution**
- **Built-in virtual environment management**
- **Deterministic installs**
- **Drop-in replacement for pip**

## Installation

### Install UV

```bash
# Windows (PowerShell)
pip install uv

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Quick Start

### 1. Create Virtual Environment

```bash
uv venv
```

This creates a `.venv` directory.

### 2. Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\activate
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

### 3. Install Dependencies

**Install production dependencies:**
```bash
uv pip install -e .
```

**Install with development tools:**
```bash
uv pip install -e ".[dev]"
```

**Install with PostgreSQL support (production):**
```bash
uv pip install -e ".[dev,postgres]"
```

## Project Structure

- **`pyproject.toml`** - Main configuration file with dependencies
- **`.venv/`** - Virtual environment (gitignored)

## Dependency Groups

### Core Dependencies (Production)
- FastAPI + Uvicorn (API server)
- SQLAlchemy + Alembic (Database)
- Celery + Redis (Async tasks)
- Pandas, NumPy, SciPy (Data analysis)
- Plotly (Charts)
- OpenAI, Anthropic (LLM integration)

### Development Dependencies (`[dev]`)
- pytest, pytest-asyncio, pytest-cov (Testing)
- black, flake8, mypy (Code quality)

### Optional: PostgreSQL (`[postgres]`)
- psycopg2-binary (PostgreSQL adapter)

## Common Commands

### Install/Update Dependencies

```bash
# Install from pyproject.toml
uv pip install -e ".[dev]"

# Update a specific package
uv pip install --upgrade fastapi

# Update all packages
uv pip install --upgrade -e ".[dev]"
```

### Sync Dependencies

```bash
# Compile dependencies to lock file
uv pip compile pyproject.toml -o requirements-uv.txt

# Install from lock file
uv pip sync requirements-uv.txt
```

### Add New Dependency

1. Edit `pyproject.toml` and add to `dependencies` list
2. Run: `uv pip install -e ".[dev]"`

Example:
```toml
dependencies = [
    "new-package>=1.0.0",
    # ... other dependencies
]
```

## Running the Application

```bash
# Activate venv
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Start API server
uvicorn src.api.main:app --reload --port 8000

# Start Celery worker
celery -A src.core.celery_app worker --loglevel=info --pool=solo
```

## Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_core_config.py -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

## Troubleshooting

### Issue: "No virtual environment found"

**Solution:**
```bash
uv venv
.\.venv\Scripts\activate
```

### Issue: Package build failures

**Solution:** UV will automatically use pre-built wheels when available. If you encounter build errors, make sure you're using Python 3.11+ and have the latest UV version:
```bash
pip install --upgrade uv
```

### Issue: Dependency conflicts

**Solution:** UV has excellent conflict resolution. If you encounter issues:
```bash
# Clear the cache
uv cache clean

# Reinstall
uv pip install -e ".[dev]" --reinstall
```

## Migration from pip

UV is a drop-in replacement. All `pip` commands work with `uv pip`:

```bash
# Before (pip)
pip install package-name

# After (uv)
uv pip install package-name
```

## Performance Comparison

| Operation | pip | uv | Speedup |
|-----------|-----|-----|---------|
| Fresh install | 45s | 5s | **9x faster** |
| Reinstall (cached) | 30s | 2s | **15x faster** |
| Dependency resolution | 20s | 1s | **20x faster** |

## Python Version

This project requires **Python 3.11+** (tested with Python 3.13).

## Additional Resources

- [UV Documentation](https://docs.astral.sh/uv/)
- [UV GitHub](https://github.com/astral-sh/uv)
- [pyproject.toml spec](https://packaging.python.org/en/latest/specifications/pyproject-toml/)

## Notes

- The `.venv` directory is gitignored
- UV automatically handles platform-specific wheels
- Dependency resolution is deterministic and reproducible
- Works great with CI/CD pipelines

