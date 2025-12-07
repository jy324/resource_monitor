#!/usr/bin/env python3
"""
Main entry point for the resource monitoring system.
"""

import sys
import signal
import logging
from http_server import run_server

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Received shutdown signal, exiting...")
    sys.exit(0)


def main():
    """Main entry point."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Get config path from command line arguments
    config_path = sys.argv[1] if len(sys.argv) > 1 else 'config.json'
    
    logger.info("Starting Resource Monitor System")
    logger.info(f"Using configuration file: {config_path}")
    
    try:
        # Load configuration
        import json
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Get HTTP server settings
        host = config['http_server']['host']
        port = config['http_server']['port']
        
        # Start the server
        run_server(host=host, port=port, config_path=config_path)
        
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in configuration file: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
