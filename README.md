# QuantFi - Local Portfolio Tracking & Research Platform

A local-first system for tracking portfolio activity and powering quantitative research workflows. Integrates with Interactive Brokers (IBKR) Client Portal Web API to ingest account data, positions, executions, and cash transactions into a local SQLite database for analysis and research.

## 🎯 Purpose

QuantFi provides a **local-first, offline-capable** solution for:
- **Portfolio Tracking**: Automated data ingestion from IBKR Client Portal Web API
- **Research Workflows**: Jupyter notebooks for portfolio analysis and quantitative research
- **Data Integrity**: Encrypted SQLite database with comprehensive validation and error handling
- **Analytics Ready**: DuckDB + Parquet for fast ad-hoc analysis

## ✨ Features

- 🔐 **Encrypted Storage**: SQLCipher-encrypted SQLite database for sensitive financial data
- 📊 **ActiveModel ORM**: ActiveRecord-style ORM for type-safe database operations
- 🔄 **Incremental Sync**: Smart sync with overlap handling and conflict resolution
- ✅ **Data Validation**: Comprehensive validation rules and quality checks
- 📈 **Analytics Ready**: DuckDB integration for fast queries over Parquet + SQLite
- 🧪 **Well Tested**: 90%+ test coverage with unit and integration tests
- 🔒 **Security First**: Git hooks prevent secrets from being committed
- 📝 **Schema Management**: Alembic migrations for database schema evolution

## 🛠️ Tech Stack

- **Language**: Python 3.11
- **Environment**: Conda/Miniconda (conda-forge channel)
- **Database**: SQLite with SQLCipher (encryption at rest)
- **ORM**: ActiveModel (ActiveRecord-style, custom implementation)
- **Migrations**: Alembic
- **Analytics**: DuckDB + Parquet
- **UI**: Jupyter Lab (primary), Flask (future Phase 6)
- **Visualization**: Plotly
- **HTTP Client**: requests
- **CLI Framework**: Click
- **Testing**: pytest
- **Code Quality**: Black (formatting), Ruff (linting), mypy (type checking)
- **Retry Logic**: tenacity

## 📋 Prerequisites

- **Python**: 3.11 (via Conda)
- **Java**: 11+ (for IBKR Client Portal Gateway)
- **IBKR Account**: Interactive Brokers account with Client Portal Gateway access
- **macOS**: Designed for macOS-local deployment (Phase 1)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Create and activate conda environment
conda env create -f environment.yml
conda activate quantfi

# Install SQLCipher (macOS)
brew install sqlcipher
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# IMPORTANT: Set DB_ENCRYPTION_KEY to a secure random key (min 32 chars)
# IMPORTANT: Set IBKR_ACCOUNT_ID to your actual account ID
```

Required environment variables:
- `DB_ENCRYPTION_KEY`: Secure random key for database encryption (min 32 characters)
- `IBKR_ACCOUNT_ID`: Your IBKR account ID (e.g., `U1234567`)
- `DB_PATH`: Path to portfolio database (default: `data/portfolio.db`)
- `GATEWAY_URL`: IBKR Gateway URL (default: `https://localhost:5000`)

### 3. Start IBKR Client Portal Gateway

```bash
# Download and extract Client Portal Gateway (Standard Release)
# Start gateway
./bin/run.sh root/conf.yaml

# Login in browser: https://localhost:5000/
# Complete 2FA authentication
```

### 4. Initialize Database

```bash
# Run Alembic migrations
alembic upgrade head
```

### 5. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

## 📖 Usage

### CLI Commands

```bash
# Sync data from IBKR API
python -m src.cli sync --from 2024-01-01 --to 2024-12-31

# Check sync status
python -m src.cli status

# Validate data quality
python -m src.cli validate
```

### Python API

```python
from src.database import Database
from src.models import Account

# Initialize database
db = Database("data/portfolio.db", encryption_key="your-key")

# Create account
account = Account(
    database=db,
    id="U1234567",
    name="Individual",
    base_currency="USD"
)
account.save()

# Query accounts
accounts = Account.find_all(db)
for account in accounts:
    print(account)
```

### Jupyter Notebooks

Launch Jupyter Lab and open notebooks in the `notebooks/` directory:

```bash
jupyter lab
```

Notebooks (planned):
- `data_import.ipynb`: Data import controls and sync status
- `portfolio_tracking.ipynb`: Portfolio overview and performance
- `research_analytics.ipynb`: Research workflows and analysis
- `data_exploration.ipynb`: Ad-hoc data exploration

## 📁 Project Structure

```
quantfi/
├── alembic/                 # Database migrations
│   └── versions/            # Migration files
├── data/                    # Data directories
│   ├── logs/               # Application logs
│   ├── raw/                # Raw API responses
│   └── processed/          # Processed CSV files
├── docs/                    # Documentation
│   ├── initial_plan.md     # Architecture plan
│   ├── data_model.md       # Database schema
│   ├── tech_stack.md       # Technology stack
│   └── ...                 # Additional docs
├── notebooks/               # Jupyter notebooks
├── src/                     # Source code
│   ├── models/             # ActiveModel ORM
│   │   ├── active_model.py # Base ActiveModel class
│   │   └── account.py      # Account model
│   ├── database.py         # Database connection
│   ├── api_client.py       # IBKR API client
│   ├── cli.py              # CLI commands
│   └── ...
├── tests/                   # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── fixtures/           # Test fixtures
├── .cursor/                 # Cursor IDE rules
│   └── rules/              # Development rules
├── .git/hooks/              # Git hooks (pre-commit, pre-push)
├── .env.example             # Environment template
├── environment.yml          # Conda environment
├── alembic.ini              # Alembic configuration
└── pytest.ini               # Pytest configuration
```

## 🔧 Development

### Code Quality

```bash
# Format code
black src tests

# Lint code
ruff check src tests

# Type check
mypy src
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/models/test_account.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run integration tests only
pytest tests/integration/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Git Hooks

Pre-commit and pre-push hooks automatically scan for secrets:
- Pre-commit: Scans staged files before commit
- Pre-push: Final check before pushing to remote

Hooks are automatically installed and executable. They skip documentation files (`.md`, `.mdc`) and recognize common placeholder patterns.

## 🔒 Security

### Environment Variables

- **Never commit `.env`** - It's in `.gitignore` and protected by git hooks
- **Use `.env.example`** as a template for required variables
- **Rotate `DB_ENCRYPTION_KEY`** if accidentally exposed

### Database Encryption

- SQLCipher provides database-level encryption at rest
- Encryption key stored in `.env` (never in code)
- Database file itself is encrypted, not just individual fields

### Git Protection

- Pre-commit hook prevents committing secrets
- Pre-push hook blocks pushing secrets to GitHub
- Documentation files automatically exempted

### Security Rules

See `.cursor/rules/` for comprehensive security guidelines:
- `.cursor/rules/env_security.mdc` - Environment file access rules
- `.cursor/rules/repo_security.mdc` - Repository security and secrets prevention
- `.cursor/rules/security_compliance.mdc` - Security compliance standards

## 📚 Documentation

Comprehensive documentation in `docs/`:

- **Architecture**: `docs/initial_plan.md` - Overall system architecture
- **Data Model**: `docs/data_model.md` - Database schema and relationships
- **Tech Stack**: `docs/tech_stack.md` - Technology choices and rationale
- **API Integration**: `docs/ib_web_api.md` - IBKR Web API integration guide
- **User Guide**: `docs/user_guide.md` - End-user documentation
- **Deployment**: `docs/deployment_runbook.md` - Deployment procedures
- **Security**: `docs/security_measures.md` - Security measures and best practices

## 🧪 Testing

Test coverage targets:
- **Line coverage**: Minimum 90%
- **Branch coverage**: Minimum 80%
- **Function coverage**: 100%
- **Critical path coverage**: 100%

Test structure:
- **Unit tests**: `tests/unit/` - Model, validation, normalization
- **Integration tests**: `tests/integration/` - Database, API, workflows
- **Fixtures**: `tests/fixtures/` - Mock data and test utilities

## 🗺️ Roadmap

### Phase 1: Data Ingest (Current)
- ✅ Account model with ActiveModel ORM
- ✅ Database schema and migrations
- 🔄 IBKR API integration
- 🔄 Data normalization and validation
- 🔄 CLI sync commands

### Phase 2: Portfolio Tracking
- Portfolio overview notebooks
- Position tracking and P&L analysis
- Performance metrics

### Phase 3: Research Data Integration
- Price history ingestion
- ETF holdings data
- Options analytics

### Phase 4: Research Notebooks
- Research workflows
- Factor analysis
- Custom queries

### Phase 5: Target Research
- Target identification
- Research-driven decisions

### Phase 6: Flask App (Future)
- Read-only dashboards
- JSON APIs
- Web interface

## ⚠️ Important Notes

### Currency Handling

- **Phase 1**: USD-only
- All amounts stored as **INTEGER** (micro-dollars, 6 decimal places)
- Never use `float` or `REAL` for currency amounts
- Use `decimal.Decimal` for calculations

### Database Schema

- **Database file**: `portfolio.db` (never `flex.db`)
- **Table names**: `accounts`, `executions`, `cash_transactions`, etc.
- **Schema changes**: Always use Alembic migrations

### Technology Lock

- **Python 3.11 only** - No other versions
- **Conda environment** - No venv/pipenv
- **Plotly only** - No Matplotlib
- **Ruff only** - No flake8
- See `docs/tech_stack.md` for full list

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Code style guidelines
- Testing requirements
- Database conventions
- Security best practices
- Pull request process

Quick checklist:
- ✅ Follow code style: Black formatting, Ruff linting
- ✅ Write tests for new features (90%+ coverage target)
- ✅ Update documentation for API changes
- ✅ Never commit secrets (hooks will catch them)

## 📄 License

[Add your license here]

## 🙏 Acknowledgments

- Interactive Brokers for Client Portal Web API
- SQLCipher for database encryption
- Alembic for database migrations
- All open-source contributors

---

**Status**: Active Development (Phase 1)  
**Platform**: macOS-local  
**Currency**: USD-only (Phase 1)

