# Changelog

All notable changes to the ASMO-01 Health Monitoring System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-11

### Added - Initial Release (Phase 1)
- **Monitoring System** (`monitor.py`)
  - Hourly system metrics collection (CPU, RAM, Disk)
  - Docker container health monitoring
  - Error log parsing and aggregation
  - Threshold-based alert detection
  - JSON history storage with 7-day retention
  
- **Reporting System** (`reporter.py`)
  - 24-hour trend analysis
  - Container uptime tracking
  - Resource usage aggregation
  - Problematic container identification
  - Discord embed generation
  
- **Utilities**
  - `docker_client.py`: Docker API wrapper with error detection
  - `metrics.py`: System metrics collection using psutil
  - `storage.py`: JSON-based history management
  
- **Documentation**
  - README.md: Complete project overview
  - QUICKSTART.md: 5-minute setup guide
  - CUSTOMIZATION.md: Personalization guide
  - CLAUDE_CODE_INTEGRATION.md: Phase 2 roadmap
  
- **Configuration**
  - config.example.json: Template configuration
  - Customizable thresholds for CPU, RAM, Disk
  - Docker container ignore list
  - Retention policies

- **Testing**
  - test_setup.py: Setup verification script
  - Test modes for both monitor and reporter

### Features
- ✅ Automated hourly monitoring
- ✅ Daily intelligent reports
- ✅ Discord webhook integration
- ✅ Error pattern detection
- ✅ Resource usage tracking
- ✅ Container health monitoring
- ✅ Historical data analysis

### System Requirements
- Python 3.8+
- Docker
- Ubuntu 24 (or compatible Linux)
- n8n for workflow automation

---

## [Unreleased] - Phase 2 (Planned)

### Planned - Claude Code Integration
- AI-powered root cause analysis
- Pattern correlation detection
- Predictive alerts
- Intelligent recommendations
- Enhanced Discord reports with AI insights

### Planned - Auto-remediation
- Automatic container restart on failure
- Cache/log cleanup automation
- Resource limit adjustments
- Rollback capabilities
- Action audit trail

---

## [Future] - Phase 3+ (Ideas)

### Ideas
- Grafana dashboard integration
- REST API endpoint
- Telegram/Email notifications
- ML-based anomaly detection
- Long-term trend analysis (30 days)
- Custom healthcheck plugins
- Multi-server support
- Web UI dashboard

---

## Version History

- **1.0.0** (2026-01-11): Initial release with core monitoring and reporting
- **0.9.0** (2026-01-11): Beta testing phase
- **0.1.0** (2026-01-11): Project inception

---

## Upgrade Notes

### From 0.x to 1.0.0
This is the first stable release. If you were using a development version:
1. Backup your `data/health_history.json`
2. Pull latest code
3. Run `pip3 install -r requirements.txt --break-system-packages`
4. Update your `config.json` (compare with `config.example.json`)
5. Test with `python3 src/test_setup.py`

---

## Contributing

Want to contribute? Check out:
- Open issues on GitHub
- Feature requests in discussions
- Pull requests are welcome!

---

*For detailed documentation, see README.md*
