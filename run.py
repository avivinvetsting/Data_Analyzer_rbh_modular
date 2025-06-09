#!/usr/bin/env python3
# run.py
"""
Entry point for the Data Analyzer Flask application.

This script creates and runs the Flask application using the application factory pattern.
It supports different configuration environments and provides a clean entry point for
production deployment and development.

Usage:
    python run.py                  # Runs in development mode (default)
    FLASK_ENV=production python run.py  # Runs in production mode
    FLASK_ENV=testing python run.py     # Runs in testing mode
"""

import os
import sys
from app import create_app

def main():
    """
    Main entry point for the application.
    
    Creates the Flask application with the appropriate configuration
    based on environment variables and command line arguments.
    """
    
    # Determine configuration environment
    config_name = os.environ.get('FLASK_ENV', 'development')
    
    # Validate configuration name
    valid_configs = ['development', 'testing', 'production']
    if config_name not in valid_configs:
        print(f"Invalid FLASK_ENV: {config_name}")
        print(f"Valid options: {', '.join(valid_configs)}")
        sys.exit(1)
    
    # Create the application
    try:
        app = create_app(config_name)
        
        # Display startup information
        print("="*60)
        print(f"🚀 Data Analyzer Application Starting")
        print(f"📊 Environment: {config_name.upper()}")
        print(f"🐛 Debug Mode: {'ON' if app.debug else 'OFF'}")
        print(f"🔒 CSRF Protection: {'ON' if app.config.get('WTF_CSRF_ENABLED', True) else 'OFF'}")
        print("="*60)
        
        # Run the application
        if config_name == 'development':
            # Development server with debug mode and auto-reload
            app.run(
                host='127.0.0.1',
                port=5000,
                debug=True,
                use_reloader=True,
                threaded=True
            )
        else:
            # Production-like server (use proper WSGI server in production)
            app.run(
                host='0.0.0.0',
                port=int(os.environ.get('PORT', 5000)),
                debug=False,
                threaded=True
            )
            
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()