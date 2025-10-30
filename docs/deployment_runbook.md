# Deployment Runbook (macOS-local)

Purpose: Operational procedures for deploying and maintaining the IBKR Client Portal Web API integration on macOS, including gateway management, application deployment, and monitoring.

## Overview

- **Environment**: macOS localhost-only deployment
- **Components**: Client Portal Gateway, Python application, SQLite database
- **Access**: Single user, local machine only
- **Dependencies**: Java 8u192+, Python 3.11+

## Prerequisites

### System Requirements
- **macOS**: 10.15+ (Catalina or later)
- **Java**: JRE 11 or later
- **Python**: 3.11 or later
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 1GB free space for application and data

### Software Dependencies
- **Client Portal Gateway**: Standard Release from IBKR
- **Python packages**: See `requirements.txt`
- **Database**: SQLCipher-enabled SQLite
- **Notebook**: Jupyter Lab or Jupyter Notebook

## Pre-Deployment Checklist

### Environment Setup
- [ ] Java 11+ installed and verified (`java -version`)
- [ ] Python 3.11+ installed and verified
- [ ] Client Portal Gateway downloaded and extracted
- [ ] Project directory created and configured
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)

### Security Configuration
- [ ] macOS firewall enabled
- [ ] Screen lock configured (5-minute timeout)
- [ ] Antivirus software installed and updated
- [ ] Backup location configured and tested
- [ ] Database encryption key secured

### IBKR Account Setup
- [ ] IBKR account active and accessible
- [ ] 2FA enabled and working
- [ ] API access permissions confirmed
- [ ] Account ID noted for configuration

## Deployment Procedures

### 1. Gateway Deployment

#### Initial Setup
```bash
# Navigate to gateway directory
cd /path/to/client-portal-gateway

# Verify Java installation
java -version

# Start gateway
./bin/run.sh root/conf.yaml
```

#### Configuration
- **Port**: Default 5000 (configurable in `root/conf.yaml`)
- **TLS**: Self-signed certificate for localhost
- **Access**: localhost only, no external exposure

#### Verification
```bash
# Test gateway connectivity
curl -k https://localhost:5000/v1/api/tickle

# Expected response: {"status":"ok"}
```

### 2. Application Deployment

#### Project Structure
```
quantfi/
├── src/
│   ├── api_client.py
│   ├── data_normalization.py
│   ├── database.py
│   └── validation.py
├── notebooks/
│   ├── data_import.ipynb
│   ├── portfolio_tracking.ipynb
│   └── research_analytics.ipynb
├── data/
│   ├── logs/
│   ├── raw/
│   └── processed/
├── tests/
├── docs/
└── requirements.txt
```

#### Installation Steps
```bash
# Clone or extract project
cd /Users/username/quantfi

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -m src.database init

# Run tests
pytest tests/
```

### 3. Database Setup

#### SQLCipher Configuration
```bash
# Install SQLCipher
pip install pysqlcipher3

# Initialize encrypted database
python -c "
from src.database import init_database
init_database('data/portfolio.db', 'your_encryption_key')
"
```

#### Schema Migration
```bash
# Apply migrations
alembic upgrade head

# Verify schema
python -c "
from src.database import verify_schema
verify_schema()
"
```

### 4. Configuration

#### Environment Variables
Create `.env` file:
```bash
# Database
DB_PATH=data/portfolio.db
DB_ENCRYPTION_KEY=your_encryption_key

# Gateway
GATEWAY_URL=https://localhost:5000
GATEWAY_VERIFY_SSL=false

# Logging
LOG_LEVEL=INFO
LOG_DIR=data/logs

# Backup
BACKUP_DIR=~/Library/Application Support/QuantFi/backups
```

#### Account Configuration
```bash
# Set account ID
export IBKR_ACCOUNT_ID=U1234567

# Or add to .env
echo "IBKR_ACCOUNT_ID=U1234567" >> .env
```

## Operational Procedures

### Daily Operations

#### Gateway Management
```bash
# Start gateway
cd /path/to/client-portal-gateway
./bin/run.sh root/conf.yaml

# Check status
curl -k https://localhost:5000/v1/api/tickle

# Stop gateway (Ctrl+C or kill process)
```

#### Data Synchronization
```bash
# Manual sync
python -m src.cli sync --from 2024-01-01 --to 2024-12-31

# Check status
python -m src.cli status

# Validate data
python -m src.cli validate
```

#### Notebook Operations
```bash
# Start Jupyter
jupyter lab

# Or start specific notebook
jupyter notebook notebooks/data_import.ipynb
```

### Monitoring

#### Health Checks
```bash
# Gateway health
curl -k https://localhost:5000/v1/api/tickle

# Application health
python -m src.cli status

# Database health
python -c "
from src.database import check_health
check_health()
"
```

#### Log Monitoring
```bash
# View recent logs
tail -f data/logs/application.log

# Check error logs
grep ERROR data/logs/application.log

# Monitor sync logs
grep "sync" data/logs/application.log
```

### Backup Procedures

#### Automated Backup (launchd)
Create `~/Library/LaunchAgents/com.quantfi.backup.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.quantfi.backup</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/username/quantfi/scripts/backup.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>2</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</dict>
</plist>
```

#### Manual Backup
```bash
# Run backup script
./scripts/backup.sh

# Or manual backup
ditto /Users/username/quantfi/data ~/Library/Application\ Support/QuantFi/backups/$(date +%Y%m%d)
```

### Troubleshooting

#### Common Issues

**Gateway Won't Start**
```bash
# Check Java version
java -version

# Check port availability
lsof -i :5000

# Check gateway logs
tail -f /path/to/gateway/logs/gateway.log
```

**Authentication Failures**
```bash
# Clear browser cache and cookies
# Re-authenticate at https://localhost:5000/
# Check session status
curl -k https://localhost:5000/v1/api/tickle
```

**Database Errors**
```bash
# Check database file permissions
ls -la data/portfolio.db

# Verify encryption key
python -c "
from src.database import test_connection
test_connection()
"

# Check database integrity
sqlite3 data/portfolio.db "PRAGMA integrity_check;"
```

**Sync Failures**
```bash
# Check logs
grep ERROR data/logs/application.log

# Test individual endpoints
python -c "
from src.api_client import test_endpoints
test_endpoints()
"

# Reset sync cursors
python -c "
from src.database import reset_sync_cursors
reset_sync_cursors()
"
```

#### Performance Issues

**Slow Sync Operations**
```bash
# Check database size
du -h data/portfolio.db

# Analyze query performance
sqlite3 data/portfolio.db "EXPLAIN QUERY PLAN SELECT * FROM positions;"

# Check memory usage
top -p $(pgrep -f "python.*quantfi")
```

**High Memory Usage**
```bash
# Monitor memory
htop

# Check for memory leaks
python -c "
import tracemalloc
tracemalloc.start()
# Run operation
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)
"
```

### Maintenance

#### Regular Maintenance
- **Daily**: Check logs, verify sync status
- **Weekly**: Review backup integrity, clean old logs
- **Monthly**: Update dependencies, review security
- **Quarterly**: Full system health check

#### Log Rotation
```bash
# Configure logrotate
sudo vim /etc/logrotate.d/quantfi

# Or manual rotation
mv data/logs/application.log data/logs/application.log.old
touch data/logs/application.log
```

#### Database Maintenance
```bash
# Vacuum database
sqlite3 data/portfolio.db "VACUUM;"

# Analyze database
sqlite3 data/portfolio.db "ANALYZE;"

# Check database size
du -h data/portfolio.db
```

## Rollback Procedures

### Application Rollback
```bash
# Stop application
pkill -f "python.*quantfi"

# Restore from backup
cp ~/Library/Application\ Support/QuantFi/backups/YYYYMMDD/data/* data/

# Restart application
python -m src.cli sync
```

### Database Rollback
```bash
# Stop application
pkill -f "python.*quantfi"

# Backup current database
cp data/portfolio.db data/portfolio.db.backup

# Restore from backup
cp ~/Library/Application\ Support/QuantFi/backups/YYYYMMDD/flex.db data/

# Verify integrity
sqlite3 data/portfolio.db "PRAGMA integrity_check;"

# Restart application
python -m src.cli sync
```

### Gateway Rollback
```bash
# Stop gateway
pkill -f "run.sh"

# Restore gateway configuration
cp ~/Library/Application\ Support/QuantFi/backups/YYYYMMDD/gateway/conf.yaml /path/to/gateway/root/

# Restart gateway
cd /path/to/gateway
./bin/run.sh root/conf.yaml
```

## Emergency Procedures

### Critical Failures
1. **Database corruption**: Restore from latest backup
2. **Gateway failure**: Restart gateway, re-authenticate
3. **Data loss**: Restore from backup, re-sync data
4. **Security breach**: Stop all services, investigate logs

### Emergency Contacts
- **IBKR Support**: [IBKR Support Portal](https://www.interactivebrokers.com/en/support/)
- **System Administrator**: [Your contact information]
- **Security Team**: [Security contact information]

### Escalation Matrix
1. **Level 1**: Check logs, restart services
2. **Level 2**: Restore from backup, investigate root cause
3. **Level 3**: Contact IBKR support, escalate to management

## Post-Deployment Verification

### Functional Testing
- [ ] Gateway starts and responds to health checks
- [ ] Application connects to gateway successfully
- [ ] Data synchronization works correctly
- [ ] Notebooks load and display data
- [ ] CLI commands execute without errors

### Performance Testing
- [ ] Sync operations complete within expected time
- [ ] Memory usage stays within limits
- [ ] Database queries perform adequately
- [ ] Log files don't grow excessively

### Security Testing
- [ ] Database encryption working
- [ ] Logs don't contain sensitive data
- [ ] Access restricted to localhost only
- [ ] Backup encryption working

## Maintenance Schedule

### Daily
- Check application logs
- Verify sync status
- Monitor disk space
- Check backup status

### Weekly
- Review error logs
- Clean old log files
- Verify backup integrity
- Check system performance

### Monthly
- Update dependencies
- Review security logs
- Test backup/restore procedures
- Update documentation

### Quarterly
- Full system health check
- Security review
- Performance analysis
- Disaster recovery testing

## References
- Web API overview: `docs/ib_web_api.md`
- Authentication guide: `docs/ib_web_api_auth.md`
- Error handling: `docs/error_handling_retry.md`
- Security measures: `docs/security_measures.md`
- Testing plan: `docs/testing_plan.md`
- Implementation checklist: `docs/implementation_checklist.md`
