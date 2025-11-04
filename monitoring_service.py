"""
Main monitoring service that schedules and coordinates resource collection.
"""

import json
import logging
from typing import List
from apscheduler.schedulers.background import BackgroundScheduler
from resource_collector import ResourceCollector
from data_aggregator import DataAggregator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MonitoringService:
    """Main service for coordinating resource monitoring."""
    
    def __init__(self, config_path: str = 'config.json'):
        """
        Initialize the monitoring service.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.data_aggregator = DataAggregator()
        self.collectors: List[ResourceCollector] = []
        self.scheduler = BackgroundScheduler()
        
        # Initialize collectors for each server
        for server_config in self.config['servers']:
            collector = ResourceCollector(server_config)
            self.collectors.append(collector)
        
        logger.info(f"Initialized monitoring service with {len(self.collectors)} servers")
    
    def _load_config(self, config_path: str) -> dict:
        """
        Load configuration from file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
    
    def collect_resources(self):
        """Collect resource metrics from all servers."""
        logger.info("Starting resource collection cycle")
        
        for collector in self.collectors:
            try:
                data = collector.collect_all_resources()
                self.data_aggregator.add_resource_data(data)
            except Exception as e:
                logger.error(f"Error collecting resources from {collector.name}: {e}")
        
        logger.info("Resource collection cycle completed")
    
    def collect_disk_usage(self):
        """Collect disk usage from all servers."""
        logger.info("Starting disk usage collection cycle")
        
        for collector in self.collectors:
            try:
                data = collector.collect_disk_info()
                self.data_aggregator.add_disk_data(data)
            except Exception as e:
                logger.error(f"Error collecting disk usage from {collector.name}: {e}")
        
        logger.info("Disk usage collection cycle completed")
    
    def start(self):
        """Start the monitoring service."""
        logger.info("Starting monitoring service")
        
        # Get intervals from config
        resource_interval = self.config['monitoring']['resource_check_interval']  # 300 seconds (5 minutes)
        disk_interval = self.config['monitoring']['disk_check_interval']  # 28800 seconds (8 hours)
        
        # Schedule resource collection every 5 minutes
        self.scheduler.add_job(
            self.collect_resources,
            'interval',
            seconds=resource_interval,
            id='resource_collection',
            max_instances=1
        )
        
        # Schedule disk usage collection every 8 hours
        self.scheduler.add_job(
            self.collect_disk_usage,
            'interval',
            seconds=disk_interval,
            id='disk_collection',
            max_instances=1
        )
        
        # Run initial collection immediately
        self.collect_resources()
        self.collect_disk_usage()
        
        # Start scheduler
        self.scheduler.start()
        logger.info("Monitoring service started successfully")
    
    def stop(self):
        """Stop the monitoring service."""
        logger.info("Stopping monitoring service")
        
        # Disconnect all collectors
        for collector in self.collectors:
            try:
                collector.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting from {collector.name}: {e}")
        
        # Shutdown scheduler
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
        
        logger.info("Monitoring service stopped")
    
    def get_data_aggregator(self) -> DataAggregator:
        """
        Get the data aggregator instance.
        
        Returns:
            DataAggregator instance
        """
        return self.data_aggregator
