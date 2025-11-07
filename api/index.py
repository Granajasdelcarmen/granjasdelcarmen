"""
Vercel Serverless Function Entry Point
This file is the entry point for Vercel serverless functions
"""
import sys
import os
import logging

# Configure logging for Vercel
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import the app
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from app import create_app
    
    # Create Flask app instance
    # Use 'production' config for Vercel deployment
    logger.info("Creating Flask app for Vercel...")
    app = create_app('production')
    logger.info("Flask app created successfully")
    
except Exception as e:
    logger.error(f"Failed to create Flask app: {e}", exc_info=True)
    import traceback
    logger.error(traceback.format_exc())
    
    # Create a minimal error handler app
    from flask import Flask, jsonify
    app = Flask(__name__)
    
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def error_handler(path):
        return jsonify({
            'error': 'Application initialization failed',
            'message': str(e),
            'type': type(e).__name__
        }), 500

# Export the Flask app - Vercel will use it as WSGI application
# The app object itself is the handler

