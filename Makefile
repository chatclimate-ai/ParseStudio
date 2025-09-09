.PHONY: help install install-dev format lint type-check test test-cov clean pre-commit-install pre-commit-run all-checks

# Default Python interpreter
PYTHON := python

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e .

install-dev: ## Install development dependencies
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"

format: ## Format code with black and isort
	@echo "🔧 Formatting code with Black..."
	black parsestudio/ tests/
	@echo "🔧 Sorting imports with isort..."
	isort parsestudio/ tests/
	@echo "✅ Code formatting complete!"

lint: ## Run linting with ruff
	@echo "🔍 Running ruff linter..."
	ruff check parsestudio/ tests/
	@echo "✅ Linting complete!"

lint-fix: ## Run ruff linter with auto-fix
	@echo "🔧 Running ruff linter with auto-fix..."
	ruff check --fix parsestudio/ tests/
	@echo "✅ Linting with fixes complete!"

type-check: ## Run type checking with mypy
	@echo "🔍 Running mypy type checker..."
	mypy parsestudio/
	@echo "✅ Type checking complete!"

test: ## Run tests
	@echo "🧪 Running tests..."
	pytest
	@echo "✅ Tests complete!"

test-cov: ## Run tests with coverage
	@echo "🧪 Running tests with coverage..."
	pytest --cov=parsestudio --cov-report=html --cov-report=term-missing
	@echo "✅ Tests with coverage complete! Check htmlcov/ directory."

clean: ## Clean up build artifacts and cache
	@echo "🧹 Cleaning up..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	@echo "✅ Cleanup complete!"

pre-commit-install: ## Install pre-commit hooks
	@echo "🔗 Installing pre-commit hooks..."
	pre-commit install
	@echo "✅ Pre-commit hooks installed!"

pre-commit-run: ## Run pre-commit hooks on all files
	@echo "🔗 Running pre-commit hooks..."
	pre-commit run --all-files
	@echo "✅ Pre-commit hooks complete!"

all-checks: format lint type-check test ## Run all code quality checks
	@echo "🎉 All checks completed successfully!"

ci-checks: lint type-check test ## Run CI checks (no formatting to avoid changes)
	@echo "🎉 CI checks completed successfully!"

build: ## Build distribution packages
	@echo "📦 Building distribution packages..."
	$(PYTHON) -m pip install --upgrade build
	$(PYTHON) -m build
	@echo "✅ Build complete! Check dist/ directory."

# Development workflow helpers
dev-setup: install-dev pre-commit-install ## Complete development environment setup
	@echo "🎉 Development environment setup complete!"
	@echo "💡 Run 'make help' to see available commands"

check: format lint type-check ## Quick development checks (format + lint + type-check)
	@echo "✅ Quick checks complete!"
