# Contributing

Contributions are welcome! Here's how to get started.

## Setup

1. Fork and clone the repository:

   ```bash
   git clone https://github.com/<your-username>/Lansweeper.Helpdesk-Python.git
   cd Lansweeper.Helpdesk-Python
   ```

2. Create a virtual environment and install dev dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # or .venv\Scripts\activate on Windows
   pip install -e ".[dev]"
   ```

## Development Workflow

### Running Tests

```bash
pytest --cov
```

All new features and bug fixes should include tests.

### Linting & Formatting

```bash
ruff check src/ tests/
ruff format src/ tests/
```

### Type Checking

```bash
mypy src/
```

## Submitting Changes

1. Create a feature branch from `main`.
2. Make your changes with clear, descriptive commits.
3. Ensure all tests pass, linting is clean, and type checking succeeds.
4. Open a pull request against `main`.

## Code Style

- Follow existing patterns in the codebase.
- Use type annotations on all public functions and methods.
- Use `logging` (never `print()`) for any debug or status output.
- Keep docstrings up to date when modifying public API methods.
