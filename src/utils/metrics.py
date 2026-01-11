"""
System metrics collection (CPU, RAM, Disk)
"""

import psutil
from typing import Dict, List
import subprocess


class SystemMetrics:
    """Collects system-level metrics (CPU, RAM, Disk)"""
    
    @staticmethod
    def get_cpu_stats() -> Dict:
        """
        Get CPU usage statistics
        
        Returns:
            Dictionary with CPU metrics
        """
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        return {
            'cpu_percent': round(cpu_percent, 2),
            'cpu_count': cpu_count,
            'cpu_freq_mhz': round(cpu_freq.current, 2) if cpu_freq else None,
        }
    
    @staticmethod
    def get_memory_stats() -> Dict:
        """
        Get RAM and swap usage
        
        Returns:
            Dictionary with memory metrics
        """
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            'ram_total_gb': round(mem.total / (1024**3), 2),
            'ram_used_gb': round(mem.used / (1024**3), 2),
            'ram_available_gb': round(mem.available / (1024**3), 2),
            'ram_percent': round(mem.percent, 2),
            'swap_total_gb': round(swap.total / (1024**3), 2),
            'swap_used_gb': round(swap.used / (1024**3), 2),
            'swap_percent': round(swap.percent, 2),
        }
    
    @staticmethod
    def get_disk_stats() -> List[Dict]:
        """
        Get disk usage for all mounted partitions
        
        Returns:
            List of dictionaries with disk metrics
        """
        disks = []
        
        for partition in psutil.disk_partitions(all=False):
            # Skip pseudo filesystems
            if partition.fstype in ['tmpfs', 'devtmpfs', 'squashfs']:
                continue
            
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                
                disks.append({
                    'mount': partition.mountpoint,
                    'device': partition.device,
                    'fstype': partition.fstype,
                    'total_gb': round(usage.total / (1024**3), 2),
                    'used_gb': round(usage.used / (1024**3), 2),
                    'free_gb': round(usage.free / (1024**3), 2),
                    'used_percent': round(usage.percent, 2),
                })
            except PermissionError:
                # Skip partitions we can't access
                continue
        
        return disks
    
    @staticmethod
    def get_network_stats() -> Dict:
        """
        Get network I/O statistics
        
        Returns:
            Dictionary with network metrics
        """
        net_io = psutil.net_io_counters()
        
        return {
            'bytes_sent_mb': round(net_io.bytes_sent / (1024**2), 2),
            'bytes_recv_mb': round(net_io.bytes_recv / (1024**2), 2),
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv,
            'errors_in': net_io.errin,
            'errors_out': net_io.errout,
        }
    
    @staticmethod
    def get_system_uptime() -> Dict:
        """
        Get system uptime
        
        Returns:
            Dictionary with uptime info
        """
        boot_time = psutil.boot_time()
        uptime_seconds = psutil.time.time() - boot_time
        
        # Convert to days, hours, minutes
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        
        return {
            'boot_timestamp': boot_time,
            'uptime_seconds': int(uptime_seconds),
            'uptime_human': f"{days}d {hours}h {minutes}m",
        }
    
    @staticmethod
    def get_load_average() -> List[float]:
        """
        Get system load average (1, 5, 15 minutes)
        
        Returns:
            List of load averages
        """
        try:
            return [round(x, 2) for x in psutil.getloadavg()]
        except AttributeError:
            # Windows doesn't have load average
            return [0.0, 0.0, 0.0]
    
    @staticmethod
    def check_thresholds(metrics: Dict, thresholds: Dict) -> Dict:
        """
        Check if metrics exceed configured thresholds
        
        Args:
            metrics: Dictionary of collected metrics
            thresholds: Dictionary of threshold values
            
        Returns:
            Dictionary with threshold violations
        """
        violations = {
            'warnings': [],
            'critical': [],
        }
        
        # Check CPU
        cpu = metrics.get('cpu_percent', 0)
        if cpu >= thresholds.get('cpu_critical', 95):
            violations['critical'].append(f"CPU usage critical: {cpu}%")
        elif cpu >= thresholds.get('cpu_warning', 80):
            violations['warnings'].append(f"CPU usage high: {cpu}%")
        
        # Check RAM
        ram_pct = metrics.get('ram_percent', 0)
        if ram_pct >= thresholds.get('ram_critical', 95):
            violations['critical'].append(f"RAM usage critical: {ram_pct}%")
        elif ram_pct >= thresholds.get('ram_warning', 85):
            violations['warnings'].append(f"RAM usage high: {ram_pct}%")
        
        # Check disks
        for disk in metrics.get('disks', []):
            used = disk['used_percent']
            mount = disk['mount']
            
            if used >= thresholds.get('disk_critical', 90):
                violations['critical'].append(f"Disk {mount} critical: {used}%")
            elif used >= thresholds.get('disk_warning', 80):
                violations['warnings'].append(f"Disk {mount} high: {used}%")
        
        return violations


def get_all_system_metrics() -> Dict:
    """
    Convenience function to get all system metrics at once
    
    Returns:
        Dictionary with all metrics
    """
    metrics = SystemMetrics()
    
    return {
        'cpu': metrics.get_cpu_stats(),
        'memory': metrics.get_memory_stats(),
        'disks': metrics.get_disk_stats(),
        'network': metrics.get_network_stats(),
        'uptime': metrics.get_system_uptime(),
        'load_average': metrics.get_load_average(),
    }
