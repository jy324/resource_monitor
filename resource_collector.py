"""
Resource monitoring collector module.
Connects to remote servers and collects CPU, GPU, memory, and disk usage.
Supports both remote (SSH) and local (psutil) monitoring.
"""

import paramiko
import json
import logging
import subprocess
import socket
import psutil
from typing import Dict, List, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResourceCollector:
    """Collects resource metrics from remote servers via SSH or locally via psutil."""
    
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
        self.is_local = self._is_local_host()
        
        if self.is_local:
            logger.info(f"{self.name} detected as local server, will use direct monitoring")
    
    def _resolve_tailscale_hostname(self, hostname: str) -> Optional[str]:
        """
        Resolve a Tailscale hostname to IP address using tailscale CLI.
        
        Args:
            hostname: Tailscale machine name to resolve
            
        Returns:
            IPv4 address string if successful, None otherwise
        """
        try:
            # Try to use tailscale CLI to resolve the hostname
            result = subprocess.run(
                ['tailscale', 'ip', hostname],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # tailscale ip returns multiple lines (IPv4 and IPv6)
                # We only want the IPv4 address (first line, starts with 100.x.x.x)
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not ':' in line:  # IPv4 doesn't contain ':'
                        logger.info(f"Resolved Tailscale hostname '{hostname}' to IP: {line}")
                        return line
        except FileNotFoundError:
            # tailscale CLI not installed
            pass
        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout resolving Tailscale hostname: {hostname}")
        except Exception as e:
            logger.debug(f"Failed to resolve Tailscale hostname '{hostname}': {e}")
        
        return None
    
    def _resolve_hostname(self, hostname: str) -> Optional[str]:
        """
        Resolve a hostname to IP address. Tries Tailscale first, then falls back to DNS.
        
        Args:
            hostname: Hostname to resolve
            
        Returns:
            IP address string if successful, None otherwise
        """
        # Skip resolution for literal IPs
        if hostname in ['localhost', '127.0.0.1', '::1']:
            return hostname
        
        # Try Tailscale resolution first
        tailscale_ip = self._resolve_tailscale_hostname(hostname)
        if tailscale_ip:
            return tailscale_ip
        
        # Fall back to standard DNS
        try:
            return socket.gethostbyname(hostname)
        except socket.gaierror:
            logger.warning(f"Failed to resolve hostname via DNS: {hostname}")
            return None
    
    def _is_local_host(self) -> bool:
        """
        Determine if the configured host is the local machine.
        Supports Tailscale hostnames.
        
        Returns:
            True if host is local, False otherwise
        """
        local_hosts = ['localhost', '127.0.0.1', '::1']
        
        # Check if host is in common local host names
        if self.host in local_hosts:
            return True
        
        # Check if host matches local hostname
        try:
            local_hostname = socket.gethostname()
            if self.host == local_hostname:
                return True
            
            # Also check FQDN
            local_fqdn = socket.getfqdn()
            if self.host == local_fqdn:
                return True
            
            # Check if host resolves to a local IP (with Tailscale support)
            try:
                host_ip = self._resolve_hostname(self.host)
                if not host_ip:
                    return False
                    
                local_ips = [socket.gethostbyname(local_hostname)]
                # Add all local interface IPs
                for interface, addrs in psutil.net_if_addrs().items():
                    for addr in addrs:
                        if addr.family == socket.AF_INET:
                            local_ips.append(addr.address)
                
                if host_ip in local_ips:
                    return True
            except:
                pass
        except:
            pass
        
        return False
        
    def connect(self) -> bool:
        """
        Establish SSH connection to the remote server (not needed for local monitoring).
        
        Returns:
            True if connection successful, False otherwise
        
        Note:
            - If password is provided in config, uses password authentication
            - If password is empty/not provided, uses SSH key authentication (default)
            - This uses AutoAddPolicy for host key acceptance. In production,
              consider using known_hosts file with RejectPolicy for better security.
            - Local servers don't need SSH connection
        """
        # Local server doesn't need SSH connection
        if self.is_local:
            logger.info(f"{self.name} is local, skipping SSH connection")
            return True
        
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
            
            # Resolve hostname (supports Tailscale hostnames)
            resolved_host = self._resolve_hostname(self.host)
            if not resolved_host:
                logger.error(f"Failed to resolve hostname: {self.host}")
                return False
            
            # Use password authentication if password is provided, otherwise use SSH keys
            connect_params = {
                'hostname': resolved_host,
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
            
            logger.info(f"Successfully connected to {self.name} ({self.host} -> {resolved_host})")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to {self.name} ({self.host}): {e}")
            return False
    
    def disconnect(self):
        """Close SSH connection."""
        if self.ssh_client:
            self.ssh_client.close()
            logger.info(f"Disconnected from {self.name}")
    
    def _execute_command_local(self, command: str) -> Optional[str]:
        """
        Execute a command locally using subprocess.
        
        Args:
            command: Command to execute
            
        Returns:
            Command output or None if execution failed
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                if result.stderr:
                    logger.warning(f"Command error on {self.name}: {result.stderr.strip()}")
                return result.stdout.strip() if result.stdout else None
        except Exception as e:
            logger.error(f"Failed to execute local command on {self.name}: {e}")
            return None
    
    def _execute_command(self, command: str) -> Optional[str]:
        """
        Execute a command on the server (local or remote).
        
        Args:
            command: Command to execute
            
        Returns:
            Command output or None if execution failed
        """
        if self.is_local:
            return self._execute_command_local(command)
        
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
    
    def _collect_cpu_usage_local(self) -> Optional[float]:
        """Collect CPU usage locally using psutil."""
        try:
            # Get CPU percentage (1 second interval for accuracy)
            cpu_percent = psutil.cpu_percent(interval=1)
            return cpu_percent
        except Exception as e:
            logger.error(f"Failed to get local CPU usage: {e}")
            return None
    
    def _collect_memory_usage_local(self) -> Optional[Dict[str, float]]:
        """Collect memory usage locally using psutil."""
        try:
            mem = psutil.virtual_memory()
            return {
                'total_mb': mem.total / (1024 * 1024),
                'used_mb': mem.used / (1024 * 1024),
                'percentage': round(mem.percent, 2)
            }
        except Exception as e:
            logger.error(f"Failed to get local memory usage: {e}")
            return None
    
    def _collect_gpu_usage_local(self) -> Optional[List[Dict]]:
        """Collect GPU usage locally using nvidia-smi."""
        try:
            # Check if nvidia-smi is available
            result = subprocess.run(['which', 'nvidia-smi'], capture_output=True)
            if result.returncode != 0:
                logger.info(f"No GPU found on {self.name}")
                return []
            
            # Get GPU information
            command = "nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits"
            output = self._execute_command_local(command)
            
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
                            logger.error(f"Failed to parse GPU data: {e}")
                
                return gpus
        except Exception as e:
            logger.error(f"Failed to get local GPU usage: {e}")
        
        return []
    
    def _collect_disk_usage_local(self, paths: List[str] = ['/home', '/data']) -> Dict[str, Optional[Dict]]:
        """Collect disk usage locally using psutil."""
        disk_info = {}
        
        for path in paths:
            try:
                usage = psutil.disk_usage(path)
                disk_info[path] = {
                    'total_mb': int(usage.total / (1024 * 1024)),
                    'used_mb': int(usage.used / (1024 * 1024)),
                    'available_mb': int(usage.free / (1024 * 1024)),
                    'percentage': round(usage.percent, 1)
                }
            except Exception as e:
                logger.warning(f"Failed to get disk usage for {path}: {e}")
                disk_info[path] = None
        
        return disk_info
    
    def collect_cpu_usage(self) -> Optional[float]:
        """
        Collect CPU usage percentage.
        
        Returns:
            CPU usage as a float percentage or None if collection failed
        """
        if self.is_local:
            return self._collect_cpu_usage_local()
        
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
        if self.is_local:
            return self._collect_memory_usage_local()
        
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
        if self.is_local:
            return self._collect_gpu_usage_local()
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
        if self.is_local:
            return self._collect_disk_usage_local(paths)
        
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
        # For local monitoring, we don't need SSH connection
        if not self.is_local:
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
        # For local monitoring, we don't need SSH connection
        if not self.is_local:
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
