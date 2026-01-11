#!/usr/bin/env python3
"""
ASMO-01 Health Monitor (Hourly)

Collects system and container metrics every hour and stores them in history.
Can also detect critical issues and trigger immediate alerts.
"""

import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.docker_client import DockerMonitor
from utils.metrics import get_all_system_metrics, SystemMetrics
from utils.storage import HealthStorage


def setup_logging(log_file: str, verbose: bool = False) -> logging.Logger:
    """Setup logging configuration"""
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Ensure log directory exists
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def load_config(config_path: str = None) -> dict:
    """Load configuration from JSON file"""
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.json"
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️  Config file not found: {config_path}")
        print("📝 Using default configuration. Run with --create-config to generate one.")
        
        # Return default config
        return {
            "paths": {
                "history_file": str(Path(__file__).parent.parent / "data" / "health_history.json"),
                "log_file": str(Path(__file__).parent.parent / "logs" / "asmo.log")
            },
            "monitoring": {
                "history_retention_days": 7,
                "error_log_lines_to_check": 50
            },
            "thresholds": {
                "cpu_warning": 80,
                "cpu_critical": 95,
                "ram_warning": 85,
                "ram_critical": 95,
                "disk_warning": 80,
                "disk_critical": 90
            },
            "docker": {
                "socket": "unix:///var/run/docker.sock",
                "containers_to_ignore": []
            },
            "alerts": {
                "critical_immediate": True
            }
        }


def collect_metrics(config: dict, logger: logging.Logger) -> dict:
    """
    Collect all metrics (system + Docker)
    
    Args:
        config: Configuration dictionary
        logger: Logger instance
        
    Returns:
        Dictionary with all collected metrics
    """
    logger.info("🔍 Starting metrics collection...")
    
    # Collect system metrics
    logger.debug("Collecting system metrics...")
    system_metrics = get_all_system_metrics()
    
    # Flatten system metrics for easier access
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'cpu_percent': system_metrics['cpu']['cpu_percent'],
        'cpu_count': system_metrics['cpu']['cpu_count'],
        'ram_total_gb': system_metrics['memory']['ram_total_gb'],
        'ram_used_gb': system_metrics['memory']['ram_used_gb'],
        'ram_percent': system_metrics['memory']['ram_percent'],
        'swap_total_gb': system_metrics['memory']['swap_total_gb'],
        'swap_used_gb': system_metrics['memory']['swap_used_gb'],
        'disks': system_metrics['disks'],
        'uptime': system_metrics['uptime']['uptime_human'],
        'load_average': system_metrics['load_average'],
    }
    
    # Collect Docker metrics
    logger.debug("Collecting Docker metrics...")
    try:
        docker_client = DockerMonitor(config['docker']['socket'])
        
        # Get container info
        containers = docker_client.get_all_containers(
            ignore_list=config['docker'].get('containers_to_ignore', [])
        )
        
        metrics['containers'] = containers
        metrics['containers_total'] = len(containers)
        metrics['containers_running'] = len([c for c in containers if c['status'] == 'running'])
        metrics['containers_stopped'] = len([c for c in containers if c['status'] != 'running'])
        metrics['containers_unhealthy'] = len([c for c in containers if c.get('health') == 'unhealthy'])
        
        # Get Docker system info
        docker_info = docker_client.get_docker_info()
        metrics['docker_info'] = docker_info
        
        docker_client.close()
        
    except Exception as e:
        logger.error(f"❌ Error collecting Docker metrics: {e}")
        metrics['containers'] = []
        metrics['docker_error'] = str(e)
    
    logger.info(f"✅ Metrics collected: {metrics['containers_total']} containers, CPU {metrics['cpu_percent']}%, RAM {metrics['ram_percent']}%")
    
    return metrics


def analyze_for_critical_alerts(metrics: dict, config: dict, logger: logging.Logger) -> dict:
    """
    Check for critical issues that need immediate attention
    
    Args:
        metrics: Collected metrics
        config: Configuration
        logger: Logger instance
        
    Returns:
        Dictionary with alert info
    """
    alert = {
        'has_critical': False,
        'critical_issues': [],
        'warnings': [],
    }
    
    thresholds = config['thresholds']
    
    # Check system thresholds
    violations = SystemMetrics.check_thresholds(metrics, thresholds)
    
    if violations['critical']:
        alert['has_critical'] = True
        alert['critical_issues'].extend(violations['critical'])
    
    alert['warnings'].extend(violations['warnings'])
    
    # Check for stopped containers
    stopped = metrics.get('containers_stopped', 0)
    if stopped > 0:
        alert['warnings'].append(f"{stopped} container(s) stopped")
    
    # Check for unhealthy containers
    unhealthy = metrics.get('containers_unhealthy', 0)
    if unhealthy > 0:
        alert['has_critical'] = True
        alert['critical_issues'].append(f"{unhealthy} container(s) unhealthy")
    
    # Check for containers with high restart counts
    for container in metrics.get('containers', []):
        restarts = container.get('restarts', 0)
        if restarts >= thresholds.get('container_restart_critical', 5):
            alert['has_critical'] = True
            alert['critical_issues'].append(f"{container['name']}: {restarts} restarts")
        elif restarts >= thresholds.get('container_restart_warning', 3):
            alert['warnings'].append(f"{container['name']}: {restarts} restarts")
    
    if alert['has_critical']:
        logger.warning(f"🚨 CRITICAL ALERT: {', '.join(alert['critical_issues'])}")
    elif alert['warnings']:
        logger.warning(f"⚠️  Warnings: {', '.join(alert['warnings'])}")
    else:
        logger.info("✅ All systems nominal")
    
    return alert


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='ASMO-01 Health Monitor')
    parser.add_argument('--config', type=str, help='Path to config file')
    parser.add_argument('--test', action='store_true', help='Test mode - print to stdout only')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')
    parser.add_argument('--create-config', action='store_true', help='Create default config.json')
    
    args = parser.parse_args()
    
    # Create config if requested
    if args.create_config:
        config_path = Path(__file__).parent.parent / "config.json"
        example_path = Path(__file__).parent.parent / "config.example.json"
        
        if config_path.exists():
            print(f"⚠️  Config already exists: {config_path}")
            return
        
        import shutil
        shutil.copy(example_path, config_path)
        print(f"✅ Created config file: {config_path}")
        print("📝 Edit it with your settings!")
        return
    
    # Load configuration
    config = load_config(args.config)
    
    # Setup logging
    logger = setup_logging(
        config['paths']['log_file'],
        verbose=args.verbose
    )
    
    logger.info("=" * 60)
    logger.info("🏥 ASMO-01 Health Monitor - Starting...")
    logger.info("=" * 60)
    
    try:
        # Collect metrics
        metrics = collect_metrics(config, logger)
        
        # Analyze for critical alerts
        alert_info = analyze_for_critical_alerts(metrics, config, logger)
        
        # Add alert info to metrics
        metrics['alert'] = alert_info
        
        # Store in history (unless test mode)
        if not args.test:
            storage = HealthStorage(
                config['paths']['history_file'],
                retention_days=config['monitoring']['history_retention_days']
            )
            storage.add_entry(metrics)
            logger.info(f"💾 Metrics saved to {config['paths']['history_file']}")
        
        # Output for n8n (JSON to stdout)
        output = {
            'success': True,
            'timestamp': metrics['timestamp'],
            'critical_alert': alert_info['has_critical'],
            'summary': {
                'cpu_percent': metrics['cpu_percent'],
                'ram_percent': metrics['ram_percent'],
                'containers_running': metrics['containers_running'],
                'containers_total': metrics['containers_total'],
                'critical_issues': alert_info['critical_issues'],
                'warnings': alert_info['warnings'],
            }
        }
        
        print("\n" + "=" * 60)
        print("📊 MONITOR OUTPUT (for n8n):")
        print("=" * 60)
        print(json.dumps(output, indent=2))
        
        logger.info("✅ Monitor completed successfully")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        
        # Output error for n8n
        error_output = {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        print(json.dumps(error_output, indent=2))
        
        return 1


if __name__ == '__main__':
    sys.exit(main())
