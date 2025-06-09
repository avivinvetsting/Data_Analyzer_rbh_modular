# config.py
"""
Centralized configuration settings for the Data Analyzer application.

This module defines configuration classes for different environments:
- Development: For local development with debug enabled
- Testing: For running tests with specific test settings
- Production: For production deployment with security features
"""

import os
from typing import Optional


class Config:
    """
    Base configuration class containing default settings and common configuration.
    
    All environment-specific configurations inherit from this base class.
    """
    
    # Security settings
    SECRET_KEY: Optional[str] = None
    
    # Session configuration
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # CSRF protection
    WTF_CSRF_ENABLED = True
    
    # File paths
    USERS_FILE = 'users.json'
    LOG_DIRECTORY = 'logs'
    LOG_FILE = 'logs/data_analyzer.log'
    
    # Logging configuration
    LOG_MAX_BYTES = 10240000  # 10MB
    LOG_BACKUP_COUNT = 10
    
    # Cache settings (TTL in seconds)
    PRICE_DATA_CACHE_TTL = 43000  # 12 hours
    COMPANY_INFO_CACHE_TTL = 3600  # 1 hour
    CACHE_MAX_SIZE = 200
    
    # Admin credentials (should be overridden in environment-specific configs)
    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = 'Admin123!'
    
    @staticmethod
    def init_app(app):
        """
        Initialize application with this configuration.
        
        This method can be overridden in subclasses to perform
        environment-specific initialization.
        """
        # Ensure log directory exists
        if not os.path.exists(Config.LOG_DIRECTORY):
            try:
                os.makedirs(Config.LOG_DIRECTORY)
                print(f"Created '{Config.LOG_DIRECTORY}' directory.")
            except OSError as e:
                print(f"Error creating logs directory: {e}")


class DevelopmentConfig(Config):
    """
    Development environment configuration.
    
    Enables debug mode and uses default credentials for easy local development.
    """
    
    DEBUG = True
    TESTING = False
    
    # Development-specific settings
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development
    
    @classmethod
    def init_app(cls, app):
        """Initialize development-specific settings."""
        Config.init_app(app)
        
        # Load development credentials from secret.py or use defaults
        try:
            from secret import FLASK_SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD
            cls.SECRET_KEY = FLASK_SECRET_KEY
            cls.ADMIN_USERNAME = ADMIN_USERNAME
            cls.ADMIN_PASSWORD = ADMIN_PASSWORD
        except ImportError:
            print("="*80)
            print("Development: secret.py not found - using default credentials.")
            print("Create secret.py for production security.")
            print("="*80)
            cls.SECRET_KEY = 'dev_secret_key_not_for_production'


class TestingConfig(Config):
    """
    Testing environment configuration.
    
    Optimized for running automated tests with minimal side effects.
    """
    
    TESTING = True
    DEBUG = False
    
    # Disable CSRF for easier testing
    WTF_CSRF_ENABLED = False
    
    # Test-specific settings
    SECRET_KEY = 'test_secret_key_for_pytest'
    SERVER_NAME = 'localhost.test'
    
    # Use in-memory or temporary files for testing
    USERS_FILE = 'test_users.json'
    LOG_DIRECTORY = 'test_logs'
    LOG_FILE = 'test_logs/data_analyzer.log'
    
    @classmethod
    def init_app(cls, app):
        """Initialize testing-specific settings."""
        Config.init_app(app)
        
        # Override with test credentials
        cls.ADMIN_USERNAME = 'admin'
        cls.ADMIN_PASSWORD = 'Admin123!'


class ProductionConfig(Config):
    """
    Production environment configuration.
    
    Emphasizes security and performance for production deployment.
    """
    
    DEBUG = False
    TESTING = False
    
    # Enhanced security for production
    SESSION_COOKIE_SECURE = True
    
    @classmethod
    def init_app(cls, app):
        """Initialize production-specific settings."""
        Config.init_app(app)
        
        # Require secret.py in production
        try:
            from secret import FLASK_SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD
            
            # Validate required secrets
            if not FLASK_SECRET_KEY:
                raise ValueError("FLASK_SECRET_KEY cannot be empty in production")
            if not ADMIN_USERNAME or not ADMIN_PASSWORD:
                raise ValueError("Admin credentials cannot be empty in production")
                
            cls.SECRET_KEY = FLASK_SECRET_KEY
            cls.ADMIN_USERNAME = ADMIN_USERNAME
            cls.ADMIN_PASSWORD = ADMIN_PASSWORD
            
        except ImportError as e:
            raise RuntimeError(
                "Production requires secret.py with FLASK_SECRET_KEY, "
                "ADMIN_USERNAME, and ADMIN_PASSWORD defined"
            ) from e


# Configuration mapping for easy environment selection
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}