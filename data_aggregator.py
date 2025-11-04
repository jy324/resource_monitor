"""
Data aggregator module for storing and managing collected metrics.
"""

import json
import logging
from typing import Dict, List
from datetime import datetime, timedelta
from collections import defaultdict
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataAggregator:
    """Aggregates and stores resource monitoring data."""
    
    def __init__(self, max_history_hours: int = 24):
        """
        Initialize the data aggregator.
        
        Args:
            max_history_hours: Maximum hours of history to keep
        """
        self.max_history_hours = max_history_hours
        self.resource_data = defaultdict(list)  # server_name -> list of resource metrics
        self.disk_data = defaultdict(list)  # server_name -> list of disk metrics
        self.lock = threading.Lock()
        
    def add_resource_data(self, data: Dict):
        """
        Add resource monitoring data.
        
        Args:
            data: Dictionary containing resource metrics
        """
        with self.lock:
            server_name = data.get('server')
            if server_name:
                self.resource_data[server_name].append(data)
                self._cleanup_old_data(self.resource_data[server_name])
                logger.info(f"Added resource data for {server_name}")
    
    def add_disk_data(self, data: Dict):
        """
        Add disk monitoring data.
        
        Args:
            data: Dictionary containing disk metrics
        """
        with self.lock:
            server_name = data.get('server')
            if server_name:
                self.disk_data[server_name].append(data)
                self._cleanup_old_data(self.disk_data[server_name])
                logger.info(f"Added disk data for {server_name}")
    
    def _cleanup_old_data(self, data_list: List[Dict]):
        """
        Remove data older than max_history_hours.
        
        Args:
            data_list: List of data dictionaries with 'timestamp' field
        """
        if not data_list:
            return
        
        cutoff_time = datetime.now() - timedelta(hours=self.max_history_hours)
        
        # Remove old entries
        i = 0
        while i < len(data_list):
            try:
                timestamp = datetime.fromisoformat(data_list[i]['timestamp'])
                if timestamp < cutoff_time:
                    data_list.pop(i)
                else:
                    i += 1
            except (KeyError, ValueError):
                i += 1
    
    def get_latest_data(self) -> Dict:
        """
        Get the latest data for all servers.
        
        Returns:
            Dictionary containing latest metrics for all servers
        """
        with self.lock:
            result = {
                'timestamp': datetime.now().isoformat(),
                'servers': []
            }
            
            # Collect all server names
            all_servers = set(self.resource_data.keys()) | set(self.disk_data.keys())
            
            for server_name in all_servers:
                server_data = {
                    'name': server_name,
                    'resource_metrics': None,
                    'disk_metrics': None
                }
                
                # Get latest resource data
                if server_name in self.resource_data and self.resource_data[server_name]:
                    server_data['resource_metrics'] = self.resource_data[server_name][-1]
                
                # Get latest disk data
                if server_name in self.disk_data and self.disk_data[server_name]:
                    server_data['disk_metrics'] = self.disk_data[server_name][-1]
                
                result['servers'].append(server_data)
            
            return result
    
    def get_historical_data(self, server_name: str = None, hours: int = 1) -> Dict:
        """
        Get historical data for specified server(s).
        
        Args:
            server_name: Name of server (None for all servers)
            hours: Number of hours of history to retrieve
            
        Returns:
            Dictionary containing historical metrics
        """
        with self.lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            result = {
                'timestamp': datetime.now().isoformat(),
                'period_hours': hours,
                'servers': []
            }
            
            servers_to_query = [server_name] if server_name else list(set(self.resource_data.keys()) | set(self.disk_data.keys()))
            
            for srv_name in servers_to_query:
                server_data = {
                    'name': srv_name,
                    'resource_history': [],
                    'disk_history': []
                }
                
                # Get resource history
                if srv_name in self.resource_data:
                    for entry in self.resource_data[srv_name]:
                        try:
                            timestamp = datetime.fromisoformat(entry['timestamp'])
                            if timestamp >= cutoff_time:
                                server_data['resource_history'].append(entry)
                        except (KeyError, ValueError):
                            continue
                
                # Get disk history
                if srv_name in self.disk_data:
                    for entry in self.disk_data[srv_name]:
                        try:
                            timestamp = datetime.fromisoformat(entry['timestamp'])
                            if timestamp >= cutoff_time:
                                server_data['disk_history'].append(entry)
                        except (KeyError, ValueError):
                            continue
                
                result['servers'].append(server_data)
            
            return result
    
    def get_summary_stats(self) -> Dict:
        """
        Get summary statistics for all servers.
        
        Returns:
            Dictionary containing summary statistics
        """
        with self.lock:
            result = {
                'timestamp': datetime.now().isoformat(),
                'total_servers': len(set(self.resource_data.keys()) | set(self.disk_data.keys())),
                'servers_online': 0,
                'servers_offline': 0,
                'summary': []
            }
            
            all_servers = set(self.resource_data.keys()) | set(self.disk_data.keys())
            
            for server_name in all_servers:
                server_summary = {
                    'name': server_name,
                    'status': 'unknown',
                    'cpu_avg': None,
                    'memory_avg': None,
                    'gpu_count': 0,
                    'disk_usage': {}
                }
                
                # Check status from latest resource data
                if server_name in self.resource_data and self.resource_data[server_name]:
                    latest = self.resource_data[server_name][-1]
                    server_summary['status'] = latest.get('status', 'unknown')
                    
                    if latest.get('status') == 'connected':
                        result['servers_online'] += 1
                    else:
                        result['servers_offline'] += 1
                    
                    # Calculate averages for last hour
                    cutoff_time = datetime.now() - timedelta(hours=1)
                    cpu_values = []
                    memory_values = []
                    
                    for entry in self.resource_data[server_name]:
                        try:
                            timestamp = datetime.fromisoformat(entry['timestamp'])
                            if timestamp >= cutoff_time:
                                if entry.get('cpu') is not None:
                                    cpu_values.append(entry['cpu'])
                                if entry.get('memory') and entry['memory'].get('percentage') is not None:
                                    memory_values.append(entry['memory']['percentage'])
                        except (KeyError, ValueError):
                            continue
                    
                    if cpu_values:
                        server_summary['cpu_avg'] = round(sum(cpu_values) / len(cpu_values), 2)
                    if memory_values:
                        server_summary['memory_avg'] = round(sum(memory_values) / len(memory_values), 2)
                    
                    # GPU count from latest
                    if latest.get('gpu'):
                        server_summary['gpu_count'] = len(latest['gpu'])
                else:
                    result['servers_offline'] += 1
                
                # Get latest disk info
                if server_name in self.disk_data and self.disk_data[server_name]:
                    latest_disk = self.disk_data[server_name][-1]
                    if latest_disk.get('disk'):
                        server_summary['disk_usage'] = latest_disk['disk']
                
                result['summary'].append(server_summary)
            
            return result
