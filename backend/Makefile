.PHONY: help test type-check lint format format-check quality quality-fix

help:
	@echo "Float Backend Quality Assurance Targets"
	@echo "========================================"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  test         Run pytest tests with coverage"
	@echo "  type-check   Run mypy type checking"
	@echo "  lint         Run ruff linting checks"
	@echo "  format       Format code with black"
	@echo "  format-check Check if code needs formatting"
	@echo "  quality      Run all quality checks (test → type-check → lint → format-check)"
	@echo "  quality-fix  Auto-fix issues (ruff --fix + black)"
	@echo "  help         Show this help message"
	@echo ""

test:
	@echo "Running pytest..."
	pytest tests/ -v

type-check:
	@echo "Running mypy type checker..."
	mypy src/ --show-error-codes

lint:
	@echo "Running ruff linter..."
	ruff check src/ tests/

format:
	@echo "Formatting code with black..."
	black src/ tests/

format-check:
	@echo "Checking if code needs formatting..."
	black --check src/ tests/

quality: test type-check lint format-check
	@echo ""
	@echo "✓ All quality checks passed!"

quality-fix:
	@echo "Auto-fixing code issues..."
	ruff check src/ tests/ --fix --unsafe-fixes
	black src/ tests/
	@echo "✓ Auto-fixes complete. Run 'make quality' to verify."

.DEFAULT_GOAL := help
