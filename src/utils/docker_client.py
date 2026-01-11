"""
Docker client wrapper for collecting container metrics and logs
"""

import docker
from typing import List, Dict, Optional
import re


class DockerMonitor:
    """Wrapper for Docker API to collect container metrics"""
    
    def __init__(self, socket_url: str = "unix:///var/run/docker.sock"):
        """
        Initialize Docker client
        
        Args:
            socket_url: Docker socket URL
        """
        self.client = docker.DockerClient(base_url=socket_url)
    
    def get_all_containers(self, ignore_list: List[str] = None) -> List[Dict]:
        """
        Get all containers with their status and stats
        
        Args:
            ignore_list: List of container names to ignore
            
        Returns:
            List of container info dictionaries
        """
        ignore_list = ignore_list or []
        containers = []
        
        for container in self.client.containers.list(all=True):
            name = container.name
            
            # Skip ignored containers
            if name in ignore_list:
                continue
            
            # Get basic info
            info = {
                'name': name,
                'id': container.short_id,
                'status': container.status,
                'state': self._get_container_state(container),
                'health': self._get_health_status(container),
                'created': container.attrs['Created'],
                'image': container.image.tags[0] if container.image.tags else 'unknown',
            }
            
            # Get stats if running
            if container.status == 'running':
                stats = self._get_container_stats(container)
                info.update(stats)
                
                # Get restart count
                info['restarts'] = container.attrs['RestartCount']
                
                # Get recent logs for errors
                info['errors'] = self._get_container_errors(container)
            else:
                # Default values for stopped containers
                info.update({
                    'cpu_percent': 0.0,
                    'mem_mb': 0.0,
                    'mem_percent': 0.0,
                    'net_rx_mb': 0.0,
                    'net_tx_mb': 0.0,
                    'restarts': container.attrs['RestartCount'],
                    'errors': []
                })
            
            containers.append(info)
        
        return containers
    
    def _get_container_state(self, container) -> str:
        """Extract container state"""
        return container.attrs['State']['Status']
    
    def _get_health_status(self, container) -> Optional[str]:
        """Extract health status if available"""
        try:
            health = container.attrs['State'].get('Health', {})
            return health.get('Status', None)
        except KeyError:
            return None
    
    def _get_container_stats(self, container) -> Dict:
        """
        Get resource usage stats for a running container
        
        Args:
            container: Docker container object
            
        Returns:
            Dictionary with CPU, memory, and network stats
        """
        try:
            # Get stats (non-streaming)
            stats = container.stats(stream=False)
            
            # Calculate CPU percentage
            cpu_percent = self._calculate_cpu_percent(stats)
            
            # Calculate memory usage
            mem_usage = stats['memory_stats'].get('usage', 0)
            mem_limit = stats['memory_stats'].get('limit', 1)
            mem_mb = mem_usage / (1024 * 1024)
            mem_percent = (mem_usage / mem_limit) * 100 if mem_limit > 0 else 0
            
            # Calculate network I/O
            networks = stats.get('networks', {})
            net_rx_bytes = sum(net['rx_bytes'] for net in networks.values())
            net_tx_bytes = sum(net['tx_bytes'] for net in networks.values())
            net_rx_mb = net_rx_bytes / (1024 * 1024)
            net_tx_mb = net_tx_bytes / (1024 * 1024)
            
            return {
                'cpu_percent': round(cpu_percent, 2),
                'mem_mb': round(mem_mb, 2),
                'mem_percent': round(mem_percent, 2),
                'net_rx_mb': round(net_rx_mb, 2),
                'net_tx_mb': round(net_tx_mb, 2),
            }
        except Exception as e:
            # Return zeros if stats fail
            return {
                'cpu_percent': 0.0,
                'mem_mb': 0.0,
                'mem_percent': 0.0,
                'net_rx_mb': 0.0,
                'net_tx_mb': 0.0,
            }
    
    def _calculate_cpu_percent(self, stats: Dict) -> float:
        """
        Calculate CPU usage percentage
        
        Args:
            stats: Docker stats dictionary
            
        Returns:
            CPU percentage
        """
        try:
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            
            cpu_count = stats['cpu_stats'].get('online_cpus', 1)
            
            if system_delta > 0 and cpu_delta > 0:
                return (cpu_delta / system_delta) * cpu_count * 100.0
        except (KeyError, ZeroDivisionError):
            pass
        
        return 0.0
    
    def _get_container_errors(self, container, lines: int = 50) -> List[str]:
        """
        Extract error messages from container logs
        
        Args:
            container: Docker container object
            lines: Number of log lines to check
            
        Returns:
            List of error messages
        """
        try:
            logs = container.logs(tail=lines, timestamps=False).decode('utf-8', errors='ignore')
            
            errors = []
            error_patterns = [
                r'ERROR',
                r'Error',
                r'error:',
                r'ERR\]',
                r'CRITICAL',
                r'Exception',
                r'Failed',
                r'failed',
                r'WARN',
                r'Warning',
            ]
            
            for line in logs.split('\n'):
                line = line.strip()
                if any(re.search(pattern, line) for pattern in error_patterns):
                    # Limit line length
                    if len(line) > 200:
                        line = line[:197] + "..."
                    errors.append(line)
            
            # Return unique errors (deduplicate)
            return list(dict.fromkeys(errors))[:10]  # Max 10 errors per container
            
        except Exception:
            return []
    
    def get_docker_info(self) -> Dict:
        """
        Get Docker system information
        
        Returns:
            Dictionary with Docker system info
        """
        try:
            info = self.client.info()
            return {
                'containers_total': info['Containers'],
                'containers_running': info['ContainersRunning'],
                'containers_paused': info['ContainersPaused'],
                'containers_stopped': info['ContainersStopped'],
                'images': info['Images'],
                'docker_version': info['ServerVersion'],
            }
        except Exception as e:
            return {
                'error': str(e)
            }
    
    def close(self):
        """Close Docker client connection"""
        self.client.close()
