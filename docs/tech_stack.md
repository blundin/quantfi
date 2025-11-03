# Technology Stack

Purpose: Document all technology choices for the IBKR Client Portal Web API integration project. This serves as the authoritative reference for what technologies are approved and why.

References:
- Architecture plan: `docs/initial_plan.md`
- Data model: `docs/data_model.md`
- Implementation checklist: `docs/implementation_checklist.md`

## Core Technologies

### Programming Language
- **Python 3.11**
  - **Rationale**: Optimal for data processing, financial analytics, and Jupyter notebook workflows
  - **Locked**: Python 3.11 (not 3.12+, not 3.10-)
  - **Why this version**: Balance of modern features, stability, and library compatibility

### Environment Management
- **Conda/Miniconda**
  - **Rationale**: Handles Python + scientific packages + system dependencies (especially for SQLCipher)
  - **Channel**: `conda-forge` (primary)
  - **Alternative not used**: venv/pip (insufficient for native dependencies)

## User Interface

### Primary UI
- **Jupyter Lab**
  - **Rationale**: Interactive data exploration, reproducible research workflows, ideal for Phase 1
  - **Notebooks**:
    - `data_import.ipynb`: Data import controls and monitoring
    - `portfolio_tracking.ipynb`: Portfolio overview and metrics
    - `research_analytics.ipynb`: Research workflows
    - `data_exploration.ipynb`: Ad-hoc analysis
  - **Future (Phase 6)**: Flask app for read-only dashboards/APIs (optional)

### Visualization
- **Plotly**
  - **Rationale**: Interactive visualizations in Jupyter, better for financial time-series data
  - **Not used**: Matplotlib (static plots, more verbose API)
  - **Does not sit on top of**: Matplotlib (independent libraries)

## Storage & Database

### Primary Database
- **SQLite (SQLCipher)**
  - **Rationale**: Local-first, single-file, encrypted, no server needed
  - **File**: `data/portfolio.db`
  - **Encryption**: SQLCipher for database-level encryption at rest
  - **Data types**: INTEGER (not BIGINT) for currency amounts in micro-dollars
  - **Why not PostgreSQL**: No server management needed for single-user local app

### Analytics Engine
- **DuckDB**
  - **Rationale**: Fast SQL analytics over Parquet and attached SQLite
  - **Use case**: Ad-hoc queries joining ledger (SQLite) with research lake (Parquet)

### Research Data Lake
- **Parquet**
  - **Rationale**: Columnar format, compressed, efficient for analytics queries
  - **Storage**: `data/lake/` partitioned by dataset and date
  - **Why not CSV**: 10-100x smaller, faster columnar reads
  - **Why not HDF5**: Less standard, more complex

## Data Processing

### Core Libraries
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical operations
- **pyarrow**: Parquet I/O

### Data Quality
- **great-expectations**: Data quality validation
- **pandas-profiling**: Data profiling (referenced in plan)

## Database Migration & ORM

- **Alembic**: Database schema migrations
- **SQLAlchemy**: ORM/query builder (optional, for Alembic migrations)

## HTTP Client

- **requests**: HTTP client for IBKR Web API calls
- **urllib3**: HTTP library (dependency of requests)
- **certifi**: SSL certificates

## CLI Framework

- **Click**: Command-line interface framework
- **Commands**: `python -m src.cli sync|status|validate`

## Retry & Error Handling

- **tenacity**: Retry logic with exponential backoff

## Configuration

- **python-dotenv**: Environment variable management (`.env` files)

## Terminal UI

- **rich**: Enhanced terminal output and formatting
- **tqdm**: Progress bars

## Testing

- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **requests-mock**: HTTP request mocking for tests

## Code Quality

### Formatting
- **Black**: Code formatter (opinionated, zero config)

### Linting
- **Ruff**: Linter (replaces flake8, isort, and more)
  - **Rationale**: 10-100x faster than flake8, modern, actively maintained
  - **Not used**: flake8 (replaced by Ruff)

### Type Checking
- **mypy**: Static type checking

## Development Environment

### IDE/Editor
- **Cursor** (VS Code-based): Primary development environment
- **VS Code Extensions Required**:
  - Python (`ms-python.python`)
  - Black Formatter (`ms-python.black-formatter`)
  - Ruff (`charliermarsh.ruff`)

### Configuration
- **`.vscode/settings.json`**: Project-specific VS Code settings
  - Black: format-on-save enabled
  - Ruff: linting and import organization enabled

## External Dependencies

### IBKR Gateway
- **Client Portal Gateway**: Java-based local gateway for Web API
  - **Java**: JRE 11+ required
  - **Port**: 5000 (localhost)
  - **TLS**: Self-signed certificate

### System Dependencies
- **SQLCipher**: C library for database encryption (via Homebrew)
- **Java 11+**: For Client Portal Gateway

## Future Components (Phase 6+)

### Web Framework (Optional)
- **Flask**: Lightweight web framework for future read-only dashboards/APIs
- **Not decided**: FastAPI (could be alternative, decision deferred)

## Package Management

### Environment File
- **File**: `environment.yml` (Conda environment definition)
- **Installation**: `conda env create -f environment.yml`
- **Updates**: `conda env update -f environment.yml --prune`

### Special Cases
- **pysqlcipher3**: Installed via pip (not available on conda-forge)
  - Requires system SQLCipher via Homebrew
  - Installation process documented separately

## Technology Decisions Summary

### Approved & Locked
- ✅ Python 3.11
- ✅ Jupyter Lab
- ✅ Conda/Miniconda
- ✅ SQLite (SQLCipher)
- ✅ DuckDB + Parquet
- ✅ Alembic + SQLAlchemy
- ✅ requests (HTTP client)
- ✅ Click (CLI)
- ✅ Black (formatter)
- ✅ Ruff (linter)
- ✅ Plotly (visualization)
- ✅ pytest (testing)
- ✅ Flask (future, Phase 6)

### Not Approved / Not Used
- ❌ PostgreSQL (server overhead unnecessary)
- ❌ MongoDB (wrong data model)
- ❌ Matplotlib (static plots, more verbose)
- ❌ flake8 (replaced by Ruff)
- ❌ venv/pip (can't handle native dependencies)
- ❌ FastAPI (Flask chosen for Phase 6)
- ❌ Docker (local-only deployment)

## Version Constraints

- **Python**: 3.11 (exact version in environment.yml)
- **Java**: 11+ (JRE or JDK)
- **macOS**: 10.15+ (Catalina or later)

## Updates & Maintenance

- **Dependencies**: Update via `conda env update -f environment.yml --prune`
- **Python packages**: Update via `conda update <package>` or `pip install --upgrade <package>`
- **Security**: Regularly update packages for security patches

