# Contributing to QuantFi

Thank you for your interest in QuantFi! This document provides guidelines and conventions for the project.

## ⚠️ Early Stage Project

**Important**: QuantFi is currently in **early development** (Phase 1). Contributions will be **rarely accepted** at this stage as the project is still being actively shaped and core architecture is being established.

We appreciate your interest, but we're focusing on:
- Core architecture and data model stability
- API integration and data ingestion
- Foundation for future features

If you have suggestions, bug reports, or feature ideas, please open an issue to discuss them first. Major contributions may be better suited once the project reaches a more stable foundation.

## 🚀 Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Run tests: `pytest`
5. Ensure code quality: `black src tests && ruff check src tests`
6. Commit your changes: `git commit -m "Add feature"`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Open a Pull Request

## 📋 Code Style

### Formatting and Linting

- **Formatter**: Black (automatic formatting)
- **Linter**: Ruff (fast, modern Python linter)
- **Type Checking**: mypy (static type analysis)

```bash
# Format code
black src tests

# Lint code
ruff check src tests

# Type check
mypy src
```

### Python Style

- **Python Version**: Python 3.11
- Follow PEP 8 style guidelines
- Use type hints for function signatures
- Write descriptive docstrings for public functions/classes

## 🧪 Testing

### Test Requirements

- **Coverage Target**: Minimum 90% line coverage
- **Test Framework**: pytest
- **Test Structure**: Mirror `src/` structure in `tests/`

### Writing Tests

```python
# tests/unit/models/test_account.py
import pytest
from src.models import Account

def test_account_creation():
    """Test account creation"""
    account = Account(database=db, id="U1234567", name="Test")
    assert account.id == "U1234567"
    assert account.name == "Test"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/models/test_account.py
```

## 💾 Database Conventions

### Schema Management

- **Migrations**: Use Alembic for all schema changes
- **Database File**: Always use `portfolio.db` (never `flex.db`)
- **Table Names**: Use plural, snake_case (e.g., `accounts`, `executions`)

### Currency Handling

**CRITICAL**: Currency amounts must use INTEGER (micro-dollars), never float/REAL.

```python
# ✅ CORRECT: Use INTEGER for currency
from decimal import Decimal

MICRO_DOLLARS = 1_000_000  # 6 decimal places

def currency_to_int(amount: Decimal) -> int:
    """Convert Decimal to micro-dollars (INTEGER)."""
    return int(amount * MICRO_DOLLARS)

# ❌ WRONG: Never use float/REAL for currency
price = float(api_data['price'])  # Precision loss!
```

### Creating Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Review the generated migration file
# Apply migrations
alembic upgrade head
```

## 🔒 Security Guidelines

### Environment Variables

- **Never commit `.env` files** - They're in `.gitignore`
- **Use `.env.example`** as a template
- **Never hardcode secrets** in code
- **Use placeholders** in examples: `"your-secure-key-here"`, `"U1234567"`

### Secrets Prevention

Git hooks automatically prevent committing secrets:
- Pre-commit hook scans staged files
- Pre-push hook performs final check

If you see a false positive, verify it's safe before using `--no-verify`.

### Database Encryption

- SQLCipher provides database-level encryption
- Encryption key must be in `.env` (never in code)
- Database files are encrypted at rest

## 📝 Documentation

### Documentation Standards

- **Terminology**: Use "Web API" (not "Flex" or "Flex Web Service")
- **Naming**: Use "Client Portal Gateway" (not just "Gateway")
- **Database**: Always reference `portfolio.db` (not `flex.db`)

### Writing Documentation

- Start with a Purpose section
- Include References section with cross-links
- Use consistent heading hierarchy
- Include code examples in appropriate language blocks

### Documentation Files

- User-facing docs: `docs/`
- API documentation: Inline docstrings
- README: Project overview and quick start
- This file: Contributing guidelines

## 🛠️ Technology Preferences

While these are preferences (not hard requirements), we encourage consistency:

### Core Technologies

- **Environment**: Conda/Miniconda (conda-forge channel)
- **Database**: SQLite with SQLCipher
- **Analytics**: DuckDB + Parquet
- **UI**: Jupyter Lab (primary), Flask (future)
- **Visualization**: Plotly

### Tools

- **HTTP Client**: requests
- **CLI Framework**: Click
- **Retry Logic**: tenacity

### Why These Choices?

- **Conda**: Better dependency management for scientific Python packages
- **SQLite**: Local-first, no external dependencies
- **Plotly**: Interactive visualizations work better in notebooks
- **Ruff**: Faster and more modern than flake8

## 🔄 API Integration Patterns

### IBKR Client Portal Web API

- **Base URL**: `https://localhost:5000/v1/api`
- **Session Management**: Use cookie jar for session persistence
- **Error Handling**: Retry with exponential backoff
- **Data Normalization**: Convert API responses to standardized format

### Example API Client Pattern

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class IBKRAPIClient:
    def __init__(self):
        self.base_url = "https://localhost:5000/v1/api"
        self.session = requests.Session()
        self.session.verify = False  # Self-signed cert
    
    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_positions(self, account_id: str):
        """Get positions with retry logic"""
        response = self.session.get(f"{self.base_url}/portfolio/{account_id}/positions")
        response.raise_for_status()
        return normalize_positions(response.json())
```

## ✅ Data Quality

### Validation Rules

- **Balance Reconciliation**: Cash + positions ≈ account value (within tolerance)
- **Position Consistency**: Negative quantities only for short positions
- **Trade Validation**: Quantity > 0, side in {BUY, SELL}, price > 0
- **Date Validation**: No future dates, monotonic execution times

### Data Normalization

All API responses should be normalized to consistent formats:
- Currency codes: Uppercase ISO 4217 codes
- Dates: ISO 8601 format
- Amounts: INTEGER (micro-dollars for USD)

## 📦 Pull Request Process

### Before Submitting

**Please note**: Due to the early stage of this project, PRs may not be accepted. Please open an issue first to discuss your contribution.

1. ✅ Open an issue to discuss your proposed changes
2. ✅ Wait for maintainer feedback before implementing
3. ✅ All tests pass
4. ✅ Code formatted with Black
5. ✅ No linting errors (Ruff)
6. ✅ Type checking passes (mypy)
7. ✅ Documentation updated (if needed)
8. ✅ No secrets in code (hooks will catch)

### PR Checklist

- [ ] Issue opened and discussed with maintainers
- [ ] Tests added/updated for new functionality
- [ ] Documentation updated
- [ ] Code follows style guidelines
- [ ] No breaking changes (or documented)
- [ ] Migration created (if schema changes)

### Review Process

- **Early Stage**: PRs may not be accepted during Phase 1 development
- **Discussion First**: Always open an issue before submitting a PR
- **Timeline**: Response times may vary as this is a personal project
- **Focus**: PRs should be small, focused, and align with project goals

## 🐛 Reporting Issues

### Bug Reports

Include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (Python version, OS, etc.)
- Relevant logs or error messages

### Feature Requests

Include:
- Use case description
- Proposed solution (if you have one)
- Benefits to the project

## 📚 Additional Resources

- **Architecture**: `docs/initial_plan.md`
- **Data Model**: `docs/data_model.md`
- **Tech Stack**: `docs/tech_stack.md`
- **API Integration**: `docs/ib_web_api.md`
- **Security**: `docs/security_measures.md`

## 🙏 Thank You!

While we're in early development and may not accept contributions right now, we appreciate your interest in QuantFi! 

- **Suggestions**: Open an issue to share ideas
- **Bug Reports**: Always welcome - please include details
- **Future Contributions**: We'll update this document when we're ready for broader contributions

Thank you for your understanding as we build the foundation for QuantFi!

