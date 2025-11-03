# User Guide (macOS-local)

Purpose: Quick-start guide for operators to get the IBKR Client Portal Web API integration running on macOS, from installation to daily usage.

## Quick Start (5 minutes)

### 1. Install Prerequisites
```bash
# Install Java (if not already installed)
brew install openjdk@11

# Verify Java installation
java -version

# Install Python 3.11+ (if not already installed)
brew install python@3.11

# Verify Python installation
python3 --version
```

### 2. Download Client Portal Gateway
1. Go to [IBKR Client Portal Gateway](https://www.interactivebrokers.com/en/trading/client-portal-gateway.php)
2. Download "Standard Release" for macOS
3. Extract to `~/Downloads/client-portal-gateway/`

### 3. Start Gateway
```bash
# Navigate to gateway directory
cd ~/Downloads/client-portal-gateway

# Start gateway
./bin/run.sh root/conf.yaml
```

### 4. Authenticate
1. Open browser to `https://localhost:5000/`
2. Log in with your IBKR credentials (2FA required)
3. Verify success: `curl -k https://localhost:5000/v1/api/tickle`

### 5. Run Application
```bash
# Clone or download the application
cd ~/quantfi

# Install dependencies
pip install -r requirements.txt

# Run sync
python -m src.cli sync

# Open notebook
jupyter lab notebooks/data_import.ipynb
```

## Detailed Installation

### Prerequisites

#### Java Installation
**Option 1: Homebrew (Recommended)**
```bash
# Install Java 11
brew install openjdk@11

# Link to system Java
sudo ln -sfn /opt/homebrew/opt/openjdk@11/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk-11.jdk

# Verify installation
java -version
```

**Option 2: Oracle JDK**
1. Download from [Oracle JDK Downloads](https://www.oracle.com/java/technologies/downloads/)
2. Run the `.dmg` installer
3. Verify: `java -version`

#### Python Installation
**Option 1: Homebrew (Recommended)**
```bash
# Install Python 3.11
brew install python@3.11

# Verify installation
python3.11 --version
```

**Option 2: Python.org**
1. Download from [Python.org Downloads](https://www.python.org/downloads/)
2. Run the installer
3. Verify: `python3 --version`

#### Jupyter Installation
```bash
# Install Jupyter
pip install jupyterlab

# Or for classic Jupyter
pip install notebook

# Verify installation
jupyter --version
```

### Client Portal Gateway Setup

#### Download and Extract
1. Visit [IBKR Client Portal Gateway](https://www.interactivebrokers.com/en/trading/client-portal-gateway.php)
2. Download "Standard Release" for macOS
3. Extract to desired location (e.g., `~/client-portal-gateway/`)

#### Configuration
Edit `root/conf.yaml` if needed:
```yaml
# Default configuration
listenPort: 5000
logLevel: INFO
```

#### Start Gateway
```bash
# Navigate to gateway directory
cd ~/client-portal-gateway

# Start gateway
./bin/run.sh root/conf.yaml

# Gateway will start on https://localhost:5000
```

#### Verify Gateway
```bash
# Test connectivity
curl -k https://localhost:5000/v1/api/tickle

# Expected response: {"status":"ok"}
```

### Application Setup

#### Download Application
```bash
# Clone repository (if using git)
git clone <repository-url> ~/quantfi

# Or download and extract ZIP
cd ~/
# Extract downloaded ZIP to quantfi/
```

#### Install Dependencies
```bash
# Navigate to application directory
cd ~/quantfi

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Initialize Database
```bash
# Initialize encrypted database
python -m src.database init

# Set encryption key (first time only)
export DB_ENCRYPTION_KEY="your-secure-key-here"

# Create .env file
cat > .env << EOF
DB_PATH=data/portfolio.db
DB_ENCRYPTION_KEY=your-secure-key-here
GATEWAY_URL=https://localhost:5000
GATEWAY_VERIFY_SSL=false
IBKR_ACCOUNT_ID=U1234567
EOF
```

## Daily Usage

### Starting the System

#### 1. Start Gateway
```bash
# Navigate to gateway directory
cd ~/client-portal-gateway

# Start gateway
./bin/run.sh root/conf.yaml
```

#### 2. Authenticate (if needed)
1. Open browser to `https://localhost:5000/`
2. Log in with IBKR credentials
3. Complete 2FA if prompted

#### 3. Start Application
```bash
# Navigate to application directory
cd ~/quantfi

# Activate virtual environment
source venv/bin/activate

# Check status
python -m src.cli status
```

### Data Synchronization

#### Manual Sync
```bash
# Sync all data
python -m src.cli sync

# Sync specific date range
python -m src.cli sync --from 2024-01-01 --to 2024-12-31

# Sync specific entity
python -m src.cli sync --entity positions
```

#### Check Status
```bash
# Overall status
python -m src.cli status

# Last sync times
python -m src.cli status --verbose

# Data validation
python -m src.cli validate
```

### Using Notebooks

#### Start Jupyter
```bash
# Start Jupyter Lab
jupyter lab

# Or start Jupyter Notebook
jupyter notebook

# Open specific notebook
jupyter lab notebooks/data_import.ipynb
```

#### Notebook Workflow
1. **data_import.ipynb**: Check gateway status, run sync, monitor errors
2. **portfolio_tracking.ipynb**: View positions, P&L, performance
3. **research_analytics.ipynb**: Run analysis, create reports
4. **data_exploration.ipynb**: Ad-hoc data exploration

### Using CLI Commands

#### Available Commands
```bash
# Check system status
python -m src.cli status

# Sync data
python -m src.cli sync [options]

# Validate data
python -m src.cli validate

# Show help
python -m src.cli --help
```

#### Command Options
```bash
# Sync options
python -m src.cli sync --from 2024-01-01 --to 2024-12-31 --entity positions

# Status options
python -m src.cli status --verbose --json

# Validate options
python -m src.cli validate --fix --report
```

## Troubleshooting

### Common Issues

#### Gateway Won't Start
```bash
# Check Java version
java -version

# Check if port 5000 is available
lsof -i :5000

# Check gateway logs
tail -f ~/client-portal-gateway/logs/gateway.log
```

#### Authentication Issues
```bash
# Clear browser cache and cookies
# Re-authenticate at https://localhost:5000/
# Check session status
curl -k https://localhost:5000/v1/api/tickle
```

#### Application Errors
```bash
# Check application logs
tail -f data/logs/application.log

# Check database
python -c "from src.database import check_health; check_health()"

# Test API connection
python -c "from src.api_client import test_connection; test_connection()"
```

#### Sync Failures
```bash
# Check sync logs
grep "sync" data/logs/application.log

# Reset sync cursors
python -c "from src.database import reset_sync_cursors; reset_sync_cursors()"

# Test individual endpoints
python -c "from src.api_client import test_endpoints; test_endpoints()"
```

### Getting Help

#### Log Files
- **Gateway logs**: `~/client-portal-gateway/logs/gateway.log`
- **Application logs**: `data/logs/application.log`
- **Sync logs**: `data/logs/sync.log`

#### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
python -m src.cli sync --verbose

# Test individual components
python -c "from src.api_client import test_connection; test_connection()"
```

#### Support Resources
- **Documentation**: `docs/` directory
- **Error handling**: `docs/error_handling_retry.md`
- **Deployment guide**: `docs/deployment_runbook.md`
- **IBKR Support**: [IBKR Support Portal](https://www.interactivebrokers.com/en/support/)

## Best Practices

### Security
- Keep Java and Python updated
- Use strong encryption keys
- Don't share credentials
- Enable screen lock
- Regular backups

### Performance
- Close unused notebooks
- Monitor memory usage
- Clean old log files
- Regular database maintenance

### Data Management
- Regular sync operations
- Validate data quality
- Monitor sync logs
- Test backup/restore

### Maintenance
- Daily: Check logs and sync status
- Weekly: Review errors and clean logs
- Monthly: Update dependencies
- Quarterly: Full system check

## Advanced Usage

### Custom Configuration
```bash
# Custom gateway port
export GATEWAY_PORT=5001

# Custom database location
export DB_PATH=/custom/path/portfolio.db

# Custom log level
export LOG_LEVEL=DEBUG
```

### Automation
```bash
# Create alias for quick start
alias quantfi-start="cd ~/client-portal-gateway && ./bin/run.sh root/conf.yaml &"

# Create alias for sync
alias quantfi-sync="cd ~/quantfi && source venv/bin/activate && python -m src.cli sync"
```

### Integration
```bash
# Add to shell profile
echo 'export PATH="$HOME/quantfi/bin:$PATH"' >> ~/.zshrc

# Create symlink for CLI
ln -s ~/quantfi/src/cli.py /usr/local/bin/quantfi
```

## Quick Reference

### Essential Commands
```bash
# Start gateway
cd ~/client-portal-gateway && ./bin/run.sh root/conf.yaml

# Check gateway
curl -k https://localhost:5000/v1/api/tickle

# Start application
cd ~/quantfi && source venv/bin/activate

# Sync data
python -m src.cli sync

# Check status
python -m src.cli status

# Open notebook
jupyter lab
```

### Important Files
- **Gateway config**: `~/client-portal-gateway/root/conf.yaml`
- **Application config**: `.env`
- **Database**: `data/portfolio.db`
- **Logs**: `data/logs/application.log`

### Key URLs
- **Gateway**: `https://localhost:5000/`
- **Jupyter**: `http://localhost:8888/`
- **IBKR Support**: [IBKR Support Portal](https://www.interactivebrokers.com/en/support/)

## References
- Web API overview: `docs/ib_web_api.md`
- Authentication guide: `docs/ib_web_api_auth.md`
- Error handling: `docs/error_handling_retry.md`
- Security measures: `docs/security_measures.md`
- Deployment runbook: `docs/deployment_runbook.md`
- Testing plan: `docs/testing_plan.md`
