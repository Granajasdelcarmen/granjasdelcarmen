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

try:
    # Add the parent directory to the path so we can import the app
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from app import create_app
    
    # Create Flask app instance
    # Use 'production' config for Vercel deployment
    logger.info("Creating Flask app for Vercel...")
    app = create_app('production')
    logger.info("Flask app created successfully")
    
    # Export the app for Vercel
    # Vercel expects a handler function or WSGI app
    handler = app
    
except Exception as e:
    logger.error(f"Failed to create Flask app: {e}", exc_info=True)
    # Create a minimal error handler app
    from flask import Flask, jsonify
    error_app = Flask(__name__)
    
    @error_app.route('/', defaults={'path': ''})
    @error_app.route('/<path:path>')
    def error_handler(path):
        return jsonify({
            'error': 'Application initialization failed',
            'message': str(e)
        }), 500
    
    handler = error_app

