"""
HTTP server for serving monitoring data and frontend.
"""

import json
import logging
from flask import Flask, jsonify, request, send_from_directory
from monitoring_service import MonitoringService
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', static_url_path='')
monitoring_service = None


def init_monitoring_service(config_path: str = 'config.json'):
    """
    Initialize the monitoring service.
    
    Args:
        config_path: Path to configuration file
    """
    global monitoring_service
    monitoring_service = MonitoringService(config_path)
    monitoring_service.start()


@app.route('/')
def index():
    """Serve the main dashboard page."""
    return send_from_directory('static', 'index.html')


@app.route('/api/latest')
def get_latest():
    """
    Get latest monitoring data for all servers.
    
    Returns:
        JSON response with latest metrics
    """
    try:
        data = monitoring_service.get_data_aggregator().get_latest_data()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error getting latest data: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/history')
def get_history():
    """
    Get historical monitoring data.
    
    Query parameters:
        server: Server name (optional, defaults to all servers)
        hours: Number of hours of history (optional, defaults to 1)
    
    Returns:
        JSON response with historical metrics
    """
    try:
        server_name = request.args.get('server', None)
        hours = int(request.args.get('hours', 1))
        
        data = monitoring_service.get_data_aggregator().get_historical_data(
            server_name=server_name,
            hours=hours
        )
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error getting historical data: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/summary')
def get_summary():
    """
    Get summary statistics for all servers.
    
    Returns:
        JSON response with summary statistics
    """
    try:
        data = monitoring_service.get_data_aggregator().get_summary_stats()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error getting summary data: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/health')
def health_check():
    """
    Health check endpoint.
    
    Returns:
        JSON response indicating service health
    """
    return jsonify({
        'status': 'healthy',
        'service': 'resource_monitor'
    })


def run_server(host: str = '0.0.0.0', port: int = 8080, config_path: str = 'config.json'):
    """
    Start the HTTP server.
    
    Args:
        host: Host address to bind to
        port: Port number to listen on
        config_path: Path to configuration file
    """
    # Initialize monitoring service
    init_monitoring_service(config_path)
    
    # Create static directory if it doesn't exist
    os.makedirs('static', exist_ok=True)
    
    # Run Flask app
    logger.info(f"Starting HTTP server on {host}:{port}")
    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == '__main__':
    import sys
    
    config_path = sys.argv[1] if len(sys.argv) > 1 else 'config.json'
    
    # Load config to get HTTP server settings
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    host = config['http_server']['host']
    port = config['http_server']['port']
    
    run_server(host=host, port=port, config_path=config_path)
