# Contributing to ParseStudio

Welcome to ParseStudio! This guide will help you get started with contributing to the project.

## 🚀 Quick Start

### 1. Development Environment Setup

```bash
# Clone the repository
git clone https://github.com/chatclimate-ai/ParseStudio.git
cd ParseStudio

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Set up development environment
uv sync --dev

# Install pre-commit hooks
uv run pre-commit install
```

### 2. Verify Your Setup

```bash
# Run all quality checks
make all-checks

# Or run individual checks
make format     # Format code with Black & isort
make lint       # Run ruff linter  
make type-check # Run mypy type checker
make test       # Run pytest
```

## 🛠️ Development Tools

### Code Quality Tools

| Tool | Purpose | Command |
|------|---------|---------|
| **Black** | Code formatting | `uv run black parsestudio/` |
| **isort** | Import sorting | `uv run isort parsestudio/` |
| **Ruff** | Fast Python linter | `uv run ruff check parsestudio/` |
| **mypy** | Static type checking | `uv run mypy parsestudio/` |
| **pre-commit** | Git hooks | `uv run pre-commit run --all-files` |

### Available Make Commands

```bash
make help           # Show all available commands
make dev-setup      # Complete development setup
make check          # Quick checks (format + lint + type-check)
make all-checks     # Run all quality checks
make ci-checks      # Run CI-style checks (no formatting)
make test-cov       # Run tests with coverage report
make clean          # Clean build artifacts
```

## 📝 Development Workflow

### 1. Before You Start

- Create a new branch from `main`
- Ensure your development environment is set up
- Run `make dev-setup` if this is your first time

### 2. Making Changes

1. **Write your code** following the existing patterns
2. **Add tests** for new functionality
3. **Update documentation** if needed
4. **Run quality checks**: `make check`

### 3. Committing Changes

Pre-commit hooks will automatically run when you commit:

```bash
git add .
git commit -m "feat: add new parser functionality"
# Pre-commit hooks run automatically:
# ✅ ruff (linting)
# ✅ black (formatting)
# ✅ isort (import sorting)
# ✅ mypy (type checking)
# ✅ trailing-whitespace
# ✅ end-of-file-fixer
```

### 4. Before Submitting PR

```bash
# Ensure all checks pass
make all-checks

# Run tests with coverage
make test-cov

# Check that build works
make build
```

## 🎯 Code Standards

### Code Style

- **Line length**: 88 characters (Black default)
- **Import order**: stdlib → third-party → first-party → local
- **Type hints**: Use modern Python type hints (`list[str]` not `List[str]`)
- **Docstrings**: Google-style docstrings for all public functions

### Example Code Style

```python
from collections.abc import Generator
from typing import Any

import pandas as pd
from anthropic import Anthropic

from ..logging_config import get_logger
from .schemas import ParserOutput, TextElement

logger = get_logger("parsers.example")


class ExampleParser:
    """
    Example parser demonstrating code standards.

    Args:
        options: Configuration options for the parser

    Raises:
        ValueError: If options are invalid
    """

    def __init__(self, options: dict[str, Any] | None = None) -> None:
        self.options = options or {}

    def parse(self, paths: str | list[str]) -> list[ParserOutput]:
        """
        Parse PDF files and return structured output.

        Args:
            paths: Path or list of paths to PDF files

        Returns:
            List of parsed outputs

        Examples:
            >>> parser = ExampleParser()
            >>> results = parser.parse("document.pdf")
            >>> print(len(results))
            1
        """
        if isinstance(paths, str):
            paths = [paths]

        outputs = []
        for path in paths:
            logger.info("Processing file", extra={"file_path": path})
            # Processing logic here...

        return outputs
```

### Testing Standards

- **Test coverage**: Aim for >90% coverage
- **Test naming**: `test_<function_name>_<scenario>`
- **Fixtures**: Use pytest fixtures for common setup
- **Mocking**: Mock external APIs and file operations

```python
import pytest
from unittest.mock import Mock, patch

def test_parser_initialization_with_valid_options():
    """Test parser initializes correctly with valid options."""
    parser = ExampleParser({"model": "gpt-4"})
    assert parser.options["model"] == "gpt-4"

def test_parser_handles_invalid_file_path():
    """Test parser raises appropriate error for invalid path."""
    parser = ExampleParser()
    with pytest.raises(FileNotFoundError):
        parser.parse("nonexistent.pdf")
```

## 🔧 Configuration Details

### Pre-commit Configuration

Pre-commit runs these tools automatically:

- **ruff**: Linting and auto-fixes
- **black**: Code formatting
- **isort**: Import sorting  
- **mypy**: Type checking
- **General**: Whitespace, file endings, JSON formatting

### Ruff Rules

We use a comprehensive set of ruff rules:

- **E/W**: pycodestyle errors and warnings
- **F**: pyflakes
- **I**: isort
- **B**: flake8-bugbear
- **UP**: pyupgrade
- **S**: bandit security checks
- **And more...**

See `pyproject.toml` for the complete configuration.

## 🚨 Troubleshooting

### Common Issues

#### Pre-commit hooks failing

```bash
# Update pre-commit hooks
uv run pre-commit autoupdate

# Run manually to see detailed errors
uv run pre-commit run --all-files
```

#### Import errors during development

```bash
# Reinstall in development mode
uv sync --dev

# Check your PYTHONPATH
python -c "import sys; print('\\n'.join(sys.path))"
```

#### Type checking errors

```bash
# Run mypy with verbose output
uv run mypy --show-error-codes parsestudio/

# Install missing type stubs
uv add --dev types-requests types-pillow
```

### Getting Help

- **Documentation**: Check existing docstrings and examples
- **Issues**: Search [GitHub issues](https://github.com/chatclimate-ai/ParseStudio/issues)
- **Code Review**: Learn from existing code patterns

## 📋 Checklist Before PR

- [ ] Code follows style guidelines (ruff, black, isort pass)
- [ ] Type hints are added where appropriate
- [ ] Tests are added for new functionality
- [ ] All tests pass (`make test`)
- [ ] Documentation is updated if needed
- [ ] Pre-commit hooks are passing
- [ ] Build succeeds (`make build`)

## 🎉 Thank You!

Thank you for contributing to ParseStudio! Your contributions help make PDF parsing better for everyone.

---

**Questions?** Feel free to open an issue or reach out to the maintainers.
