"""
Resource monitoring collector module.
Connects to remote servers and collects CPU, GPU, memory, and disk usage.
"""

import paramiko
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResourceCollector:
    """Collects resource metrics from remote servers via SSH."""
    
    def __init__(self, server_config: Dict):
        """
        Initialize the resource collector.
        
        Args:
            server_config: Dictionary containing server connection details
        """
        self.name = server_config['name']
        self.host = server_config['host']
        self.port = server_config['port']
        self.username = server_config['username']
        self.password = server_config.get('password', '')
        self.ssh_client = None
        
    def connect(self) -> bool:
        """
        Establish SSH connection to the remote server.
        
        Returns:
            True if connection successful, False otherwise
        
        Note:
            - If password is provided in config, uses password authentication
            - If password is empty/not provided, uses SSH key authentication (default)
            - This uses AutoAddPolicy for host key acceptance. In production,
              consider using known_hosts file with RejectPolicy for better security.
        """
        try:
            self.ssh_client = paramiko.SSHClient()
            # Load system host keys for security (if available)
            try:
                self.ssh_client.load_system_host_keys()
            except:
                pass
            # AutoAddPolicy: accepts unknown hosts (convenient but less secure)
            # For production, consider: paramiko.RejectPolicy() with proper known_hosts
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Use password authentication if password is provided, otherwise use SSH keys
            connect_params = {
                'hostname': self.host,
                'port': self.port,
                'username': self.username,
                'timeout': 10
            }
            
            # Only add password if it's explicitly provided (not empty)
            if self.password:
                connect_params['password'] = self.password
                logger.debug(f"Connecting to {self.name} using password authentication")
            else:
                # When no password, paramiko will automatically try SSH key authentication
                # It looks for keys in ~/.ssh/ (id_rsa, id_dsa, id_ecdsa, id_ed25519)
                logger.debug(f"Connecting to {self.name} using SSH key authentication")
            
            self.ssh_client.connect(**connect_params)
            
            logger.info(f"Successfully connected to {self.name} ({self.host})")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to {self.name} ({self.host}): {e}")
            return False
    
    def disconnect(self):
        """Close SSH connection."""
        if self.ssh_client:
            self.ssh_client.close()
            logger.info(f"Disconnected from {self.name}")
    
    def _execute_command(self, command: str) -> Optional[str]:
        """
        Execute a command on the remote server.
        
        Args:
            command: Command to execute
            
        Returns:
            Command output or None if execution failed
        """
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            output = stdout.read().decode('utf-8').strip()
            error = stderr.read().decode('utf-8').strip()
            
            if error and not output:
                logger.warning(f"Command error on {self.name}: {error}")
                return None
            
            return output
        except Exception as e:
            logger.error(f"Failed to execute command on {self.name}: {e}")
            return None
    
    def collect_cpu_usage(self) -> Optional[float]:
        """
        Collect CPU usage percentage.
        
        Returns:
            CPU usage as a float percentage or None if collection failed
        """
        # Using top command to get CPU usage
        command = "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1"
        output = self._execute_command(command)
        
        if output:
            try:
                return float(output)
            except ValueError:
                logger.error(f"Failed to parse CPU usage from {self.name}: {output}")
        
        return None
    
    def collect_memory_usage(self) -> Optional[Dict[str, float]]:
        """
        Collect memory usage information.
        
        Returns:
            Dictionary with total, used, and percentage or None if collection failed
        """
        command = "free -m | grep Mem | awk '{print $2,$3}'"
        output = self._execute_command(command)
        
        if output:
            try:
                total, used = map(float, output.split())
                percentage = (used / total) * 100
                return {
                    'total_mb': total,
                    'used_mb': used,
                    'percentage': round(percentage, 2)
                }
            except (ValueError, ZeroDivisionError) as e:
                logger.error(f"Failed to parse memory usage from {self.name}: {e}")
        
        return None
    
    def collect_gpu_usage(self) -> Optional[List[Dict]]:
        """
        Collect GPU usage information using nvidia-smi.
        
        Returns:
            List of GPU information dictionaries or None if no GPU or collection failed
        """
        # Check if nvidia-smi is available
        command = "which nvidia-smi"
        if not self._execute_command(command):
            logger.info(f"No GPU found on {self.name}")
            return []
        
        # Get GPU information
        command = "nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits"
        output = self._execute_command(command)
        
        if output:
            gpus = []
            for line in output.split('\n'):
                if line.strip():
                    try:
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 5:
                            gpus.append({
                                'index': int(parts[0]),
                                'name': parts[1],
                                'utilization': float(parts[2]),
                                'memory_used_mb': float(parts[3]),
                                'memory_total_mb': float(parts[4])
                            })
                    except (ValueError, IndexError) as e:
                        logger.error(f"Failed to parse GPU data from {self.name}: {e}")
            
            return gpus
        
        return []
    
    def collect_disk_usage(self, paths: List[str] = ['/home', '/data']) -> Dict[str, Optional[Dict]]:
        """
        Collect disk usage for specified paths.
        
        Args:
            paths: List of paths to check disk usage for
            
        Returns:
            Dictionary mapping paths to their usage information
        """
        disk_info = {}
        
        for path in paths:
            command = f"df -BM {path} | tail -1 | awk '{{print $2,$3,$4,$5}}'"
            output = self._execute_command(command)
            
            if output:
                try:
                    parts = output.split()
                    if len(parts) >= 4:
                        disk_info[path] = {
                            'total_mb': int(parts[0].replace('M', '')),
                            'used_mb': int(parts[1].replace('M', '')),
                            'available_mb': int(parts[2].replace('M', '')),
                            'percentage': float(parts[3].replace('%', ''))
                        }
                except (ValueError, IndexError) as e:
                    logger.error(f"Failed to parse disk usage for {path} on {self.name}: {e}")
                    disk_info[path] = None
            else:
                disk_info[path] = None
        
        return disk_info
    
    def collect_all_resources(self) -> Dict:
        """
        Collect all resource metrics.
        
        Returns:
            Dictionary containing all collected metrics
        """
        if not self.ssh_client or not self.ssh_client.get_transport() or not self.ssh_client.get_transport().is_active():
            if not self.connect():
                return {
                    'server': self.name,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'disconnected',
                    'error': 'Failed to connect to server'
                }
        
        data = {
            'server': self.name,
            'host': self.host,
            'timestamp': datetime.now().isoformat(),
            'status': 'connected',
            'cpu': self.collect_cpu_usage(),
            'memory': self.collect_memory_usage(),
            'gpu': self.collect_gpu_usage()
        }
        
        return data
    
    def collect_disk_info(self) -> Dict:
        """
        Collect disk usage information.
        
        Returns:
            Dictionary containing disk usage metrics
        """
        if not self.ssh_client or not self.ssh_client.get_transport() or not self.ssh_client.get_transport().is_active():
            if not self.connect():
                return {
                    'server': self.name,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'disconnected',
                    'error': 'Failed to connect to server'
                }
        
        data = {
            'server': self.name,
            'host': self.host,
            'timestamp': datetime.now().isoformat(),
            'status': 'connected',
            'disk': self.collect_disk_usage()
        }
        
        return data
