#!/usr/bin/env python3
"""
Test script for the resource monitoring system.
Tests the data structures and API without requiring actual server connections.
"""

import json
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_aggregator import DataAggregator
from datetime import datetime


def test_data_aggregator():
    """Test the data aggregator functionality."""
    print("Testing DataAggregator...")
    
    aggregator = DataAggregator(max_history_hours=24)
    
    # Add sample resource data
    resource_data = {
        'server': 'test_server1',
        'host': '192.168.1.101',
        'timestamp': datetime.now().isoformat(),
        'status': 'connected',
        'cpu': 45.2,
        'memory': {
            'total_mb': 16384,
            'used_mb': 8192,
            'percentage': 50.0
        },
        'gpu': [
            {
                'index': 0,
                'name': 'NVIDIA Tesla V100',
                'utilization': 75.5,
                'memory_used_mb': 8192,
                'memory_total_mb': 16384
            }
        ]
    }
    
    aggregator.add_resource_data(resource_data)
    print("✓ Added resource data")
    
    # Add sample disk data
    disk_data = {
        'server': 'test_server1',
        'host': '192.168.1.101',
        'timestamp': datetime.now().isoformat(),
        'status': 'connected',
        'disk': {
            '/home': {
                'total_mb': 102400,
                'used_mb': 51200,
                'available_mb': 51200,
                'percentage': 50.0
            },
            '/data': {
                'total_mb': 2048000,
                'used_mb': 819200,
                'available_mb': 1228800,
                'percentage': 40.0
            }
        }
    }
    
    aggregator.add_disk_data(disk_data)
    print("✓ Added disk data")
    
    # Get latest data
    latest = aggregator.get_latest_data()
    print(f"✓ Retrieved latest data: {len(latest['servers'])} server(s)")
    
    # Get summary
    summary = aggregator.get_summary_stats()
    print(f"✓ Retrieved summary: {summary['total_servers']} total server(s), "
          f"{summary['servers_online']} online, {summary['servers_offline']} offline")
    
    # Get historical data
    history = aggregator.get_historical_data(hours=1)
    print(f"✓ Retrieved historical data for last 1 hour")
    
    print("\nDataAggregator tests passed! ✓\n")
    return True


def test_config_structure():
    """Test that the config file is valid."""
    print("Testing config.json structure...")
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        # Check required fields
        assert 'servers' in config, "Missing 'servers' field"
        assert 'monitoring' in config, "Missing 'monitoring' field"
        assert 'http_server' in config, "Missing 'http_server' field"
        
        assert isinstance(config['servers'], list), "'servers' must be a list"
        assert len(config['servers']) > 0, "'servers' list is empty"
        
        # Check server structure
        for server in config['servers']:
            assert 'name' in server, "Server missing 'name' field"
            assert 'host' in server, "Server missing 'host' field"
            assert 'port' in server, "Server missing 'port' field"
            assert 'username' in server, "Server missing 'username' field"
        
        # Check monitoring config
        assert 'resource_check_interval' in config['monitoring']
        assert 'disk_check_interval' in config['monitoring']
        
        # Check HTTP server config
        assert 'host' in config['http_server']
        assert 'port' in config['http_server']
        
        print(f"✓ Config file is valid")
        print(f"✓ Configured {len(config['servers'])} server(s)")
        print(f"✓ Resource check interval: {config['monitoring']['resource_check_interval']}s")
        print(f"✓ Disk check interval: {config['monitoring']['disk_check_interval']}s")
        print(f"✓ HTTP server: {config['http_server']['host']}:{config['http_server']['port']}")
        print("\nConfig tests passed! ✓\n")
        return True
        
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        return False


def test_imports():
    """Test that all modules can be imported."""
    print("Testing module imports...")
    
    try:
        import resource_collector
        print("✓ resource_collector imported")
        
        import data_aggregator
        print("✓ data_aggregator imported")
        
        import monitoring_service
        print("✓ monitoring_service imported")
        
        import http_server
        print("✓ http_server imported")
        
        print("\nImport tests passed! ✓\n")
        return True
        
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Resource Monitor System - Test Suite")
    print("="*60)
    print()
    
    results = []
    
    # Run tests
    results.append(("Module Imports", test_imports()))
    results.append(("Config Structure", test_config_structure()))
    results.append(("Data Aggregator", test_data_aggregator()))
    
    # Print summary
    print("="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{name:.<40} {status}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    print("="*60)
    
    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
