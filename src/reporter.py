#!/usr/bin/env python3
"""
ASMO-01 Daily Reporter

Analyzes the last 24h of health data and generates an intelligent report
with trends, correlations, and recommendations.

This script is designed to be called by Claude Code for advanced analysis.
"""

import sys
import json
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.storage import HealthStorage


def setup_logging(log_file: str, verbose: bool = False) -> logging.Logger:
    """Setup logging configuration"""
    log_level = logging.DEBUG if verbose else logging.INFO
    
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
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
        # Return default config
        return {
            "paths": {
                "history_file": str(Path(__file__).parent.parent / "data" / "health_history.json"),
                "log_file": str(Path(__file__).parent.parent / "logs" / "asmo.log")
            },
            "reporting": {
                "top_memory_containers": 5,
                "top_cpu_containers": 5,
                "max_errors_in_report": 10
            }
        }


def analyze_24h_trends(history: List[Dict]) -> Dict:
    """
    Analyze trends over the last 24 hours
    
    Args:
        history: List of historical entries
        
    Returns:
        Dictionary with trend analysis
    """
    if not history:
        return {'error': 'No data available'}
    
    # Extract time series data
    cpu_values = [h.get('cpu_percent', 0) for h in history]
    ram_values = [h.get('ram_percent', 0) for h in history]
    
    # Calculate statistics
    trends = {
        'cpu': {
            'avg': round(sum(cpu_values) / len(cpu_values), 2) if cpu_values else 0,
            'min': round(min(cpu_values), 2) if cpu_values else 0,
            'max': round(max(cpu_values), 2) if cpu_values else 0,
            'current': round(cpu_values[-1], 2) if cpu_values else 0,
        },
        'ram': {
            'avg': round(sum(ram_values) / len(ram_values), 2) if ram_values else 0,
            'min': round(min(ram_values), 2) if ram_values else 0,
            'max': round(max(ram_values), 2) if ram_values else 0,
            'current': round(ram_values[-1], 2) if ram_values else 0,
        },
        'data_points': len(history),
        'time_span_hours': 24,
    }
    
    return trends


def analyze_container_health(history: List[Dict], config: Dict) -> Dict:
    """
    Analyze container health patterns over 24h
    
    Args:
        history: List of historical entries
        config: Configuration dictionary
        
    Returns:
        Dictionary with container analysis
    """
    # Aggregate container stats
    container_stats = {}
    
    for entry in history:
        for container in entry.get('containers', []):
            name = container['name']
            
            if name not in container_stats:
                container_stats[name] = {
                    'name': name,
                    'uptime_checks': 0,
                    'down_checks': 0,
                    'total_restarts': 0,
                    'errors': [],
                    'mem_values': [],
                    'cpu_values': [],
                }
            
            stats = container_stats[name]
            
            # Count uptime
            if container['status'] == 'running':
                stats['uptime_checks'] += 1
            else:
                stats['down_checks'] += 1
            
            # Track restarts
            stats['total_restarts'] = max(stats['total_restarts'], container.get('restarts', 0))
            
            # Collect resource usage
            if container.get('mem_mb'):
                stats['mem_values'].append(container['mem_mb'])
            if container.get('cpu_percent'):
                stats['cpu_values'].append(container['cpu_percent'])
            
            # Collect unique errors
            for error in container.get('errors', []):
                if error not in stats['errors']:
                    stats['errors'].append(error)
    
    # Calculate averages and uptime percentages
    for name, stats in container_stats.items():
        total_checks = stats['uptime_checks'] + stats['down_checks']
        stats['uptime_percent'] = round((stats['uptime_checks'] / total_checks) * 100, 2) if total_checks > 0 else 0
        
        if stats['mem_values']:
            stats['avg_mem_mb'] = round(sum(stats['mem_values']) / len(stats['mem_values']), 2)
            stats['max_mem_mb'] = round(max(stats['mem_values']), 2)
        else:
            stats['avg_mem_mb'] = 0
            stats['max_mem_mb'] = 0
        
        if stats['cpu_values']:
            stats['avg_cpu_percent'] = round(sum(stats['cpu_values']) / len(stats['cpu_values']), 2)
            stats['max_cpu_percent'] = round(max(stats['cpu_values']), 2)
        else:
            stats['avg_cpu_percent'] = 0
            stats['max_cpu_percent'] = 0
        
        # Keep only first N errors
        stats['errors'] = stats['errors'][:config['reporting'].get('max_errors_in_report', 10)]
    
    return container_stats


def identify_problematic_containers(container_stats: Dict) -> List[Dict]:
    """
    Identify containers with issues
    
    Args:
        container_stats: Container statistics dictionary
        
    Returns:
        List of problematic containers with issues
    """
    problems = []
    
    for name, stats in container_stats.items():
        issues = []
        severity = 'info'
        
        # Check uptime
        if stats['uptime_percent'] < 100:
            issues.append(f"Uptime: {stats['uptime_percent']}%")
            severity = 'warning' if stats['uptime_percent'] > 90 else 'critical'
        
        # Check restarts
        if stats['total_restarts'] > 0:
            issues.append(f"{stats['total_restarts']} restarts")
            if stats['total_restarts'] >= 5:
                severity = 'critical'
            elif stats['total_restarts'] >= 3:
                severity = 'warning'
        
        # Check for errors
        if stats['errors']:
            issues.append(f"{len(stats['errors'])} error types")
            if severity == 'info':
                severity = 'warning'
        
        if issues:
            problems.append({
                'name': name,
                'severity': severity,
                'issues': issues,
                'errors': stats['errors'][:3],  # Top 3 errors
                'stats': {
                    'uptime_percent': stats['uptime_percent'],
                    'restarts': stats['total_restarts'],
                    'avg_mem_mb': stats['avg_mem_mb'],
                }
            })
    
    # Sort by severity
    severity_order = {'critical': 0, 'warning': 1, 'info': 2}
    problems.sort(key=lambda x: severity_order[x['severity']])
    
    return problems


def get_top_resource_consumers(container_stats: Dict, config: Dict) -> Dict:
    """
    Get containers using the most resources
    
    Args:
        container_stats: Container statistics
        config: Configuration
        
    Returns:
        Dictionary with top consumers
    """
    top_n = config['reporting'].get('top_memory_containers', 5)
    
    # Sort by memory
    by_memory = sorted(
        container_stats.values(),
        key=lambda x: x['avg_mem_mb'],
        reverse=True
    )[:top_n]
    
    # Sort by CPU
    by_cpu = sorted(
        container_stats.values(),
        key=lambda x: x['avg_cpu_percent'],
        reverse=True
    )[:top_n]
    
    return {
        'top_memory': [
            {
                'name': c['name'],
                'avg_mb': c['avg_mem_mb'],
                'max_mb': c['max_mem_mb'],
            }
            for c in by_memory
        ],
        'top_cpu': [
            {
                'name': c['name'],
                'avg_percent': c['avg_cpu_percent'],
                'max_percent': c['max_cpu_percent'],
            }
            for c in by_cpu
        ],
    }


def generate_discord_embed(analysis: Dict, latest_entry: Dict) -> Dict:
    """
    Generate a Discord embed from the analysis
    
    Args:
        analysis: Analysis results
        latest_entry: Most recent metrics entry
        
    Returns:
        Discord embed dictionary
    """
    trends = analysis['trends']
    problems = analysis['problems']
    top_resources = analysis['top_resources']
    
    # Determine overall status
    critical_count = len([p for p in problems if p['severity'] == 'critical'])
    warning_count = len([p for p in problems if p['severity'] == 'warning'])
    
    if critical_count > 0:
        status_emoji = "🔴"
        status_text = "Critical Issues"
    elif warning_count > 0:
        status_emoji = "⚠️"
        status_text = "Warnings"
    else:
        status_emoji = "✅"
        status_text = "All Systems Nominal"
    
    # Build embed
    embed = {
        "content": "",
        "embeds": [{
            "title": f"{status_emoji} ASMO-01 • 24h Health Report",
            "description": (
                f"**CPU**: Avg {trends['cpu']['avg']}% (peak {trends['cpu']['max']}%)  •  "
                f"**RAM**: Avg {trends['ram']['avg']}% (peak {trends['ram']['max']}%)  •  "
                f"**Status**: {status_text}"
            ),
            "fields": [],
            "footer": {
                "text": f"Analysis of {trends['data_points']} data points • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            },
            "color": 15158332 if critical_count > 0 else (16776960 if warning_count > 0 else 3066993)
        }]
    }
    
    # Add current system stats
    disks_text = " | ".join([
        f"{d['mount']}: {d['used_percent']}%" 
        for d in latest_entry.get('disks', [])
    ])
    
    embed["embeds"][0]["fields"].append({
        "name": "💾 Current State",
        "value": (
            f"**Containers**: {latest_entry.get('containers_running', 0)}/{latest_entry.get('containers_total', 0)} running\n"
            f"**Disks**: {disks_text or 'N/A'}\n"
            f"**Uptime**: {latest_entry.get('uptime', 'N/A')}"
        ),
        "inline": False
    })
    
    # Add problematic containers
    if problems:
        problems_text = ""
        for p in problems[:5]:  # Top 5 problems
            icon = "🔥" if p['severity'] == 'critical' else "⚠️"
            problems_text += f"{icon} **{p['name']}**: {', '.join(p['issues'])}\n"
        
        embed["embeds"][0]["fields"].append({
            "name": "🚨 Issues Detected",
            "value": problems_text or "None",
            "inline": False
        })
    
    # Add top memory consumers
    mem_text = "\n".join([
        f"• **{c['name']}**: {c['avg_mb']:.0f} MB avg (peak {c['max_mb']:.0f} MB)"
        for c in top_resources['top_memory'][:3]
    ])
    
    embed["embeds"][0]["fields"].append({
        "name": "📊 Top Memory Users",
        "value": mem_text or "N/A",
        "inline": True
    })
    
    # Add top CPU consumers
    cpu_text = "\n".join([
        f"• **{c['name']}**: {c['avg_percent']:.1f}% avg"
        for c in top_resources['top_cpu'][:3]
    ])
    
    embed["embeds"][0]["fields"].append({
        "name": "⚡ Top CPU Users",
        "value": cpu_text or "N/A",
        "inline": True
    })
    
    return embed


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='ASMO-01 Daily Reporter')
    parser.add_argument('--config', type=str, help='Path to config file')
    parser.add_argument('--test', action='store_true', help='Test mode')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')
    parser.add_argument('--debug', action='store_true', help='Debug mode with detailed output')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Setup logging
    logger = setup_logging(
        config['paths']['log_file'],
        verbose=args.verbose
    )
    
    logger.info("=" * 60)
    logger.info("📊 ASMO-01 Daily Reporter - Starting...")
    logger.info("=" * 60)
    
    try:
        # Load history
        storage = HealthStorage(
            config['paths']['history_file'],
            retention_days=7
        )
        
        history_24h = storage.get_last_24h()
        latest_entry = storage.get_latest_entry()
        
        if not history_24h:
            logger.error("❌ No data available for the last 24 hours")
            print(json.dumps({'error': 'No data available'}, indent=2))
            return 1
        
        logger.info(f"📚 Loaded {len(history_24h)} data points from last 24h")
        
        # Perform analysis
        logger.info("🔍 Analyzing trends...")
        trends = analyze_24h_trends(history_24h)
        
        logger.info("🐳 Analyzing container health...")
        container_stats = analyze_container_health(history_24h, config)
        
        logger.info("🚨 Identifying problems...")
        problems = identify_problematic_containers(container_stats)
        
        logger.info("📊 Getting top resource consumers...")
        top_resources = get_top_resource_consumers(container_stats, config)
        
        # Compile analysis results
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'trends': trends,
            'problems': problems,
            'top_resources': top_resources,
            'container_stats': container_stats,
        }
        
        # Generate Discord embed
        logger.info("📝 Generating Discord embed...")
        embed = generate_discord_embed(analysis, latest_entry)
        
        # Output results
        output = {
            'success': True,
            'analysis': analysis,
            'embed': embed,
        }
        
        if args.debug:
            print("\n" + "=" * 60)
            print("🔍 DETAILED ANALYSIS:")
            print("=" * 60)
            print(json.dumps(analysis, indent=2))
        
        print("\n" + "=" * 60)
        print("📊 DISCORD EMBED (for n8n):")
        print("=" * 60)
        print(json.dumps(embed, indent=2))
        
        logger.info("✅ Report generated successfully")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        
        error_output = {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        print(json.dumps(error_output, indent=2))
        
        return 1


if __name__ == '__main__':
    sys.exit(main())
