# app/__init__.py
"""
Application factory for the Data Analyzer Flask application.

This module implements the Application Factory pattern, allowing for
clean separation of concerns and easier testing by creating multiple
app instances with different configurations.
"""

from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
import logging
from logging.handlers import RotatingFileHandler
import os

# Import configuration
from config import config

# Initialize extensions (will be bound to app in create_app)
csrf = CSRFProtect()
login_manager = LoginManager()


def create_app(config_name: str = 'default') -> Flask:
    """
    Application factory function that creates and configures a Flask application.
    
    Args:
        config_name (str): Configuration environment name ('development', 'testing', 'production')
        
    Returns:
        Flask: Configured Flask application instance
    """
    
    # Create Flask application instance
    app = Flask(__name__)
    
    # Load configuration
    config_class = config.get(config_name, config['default'])
    app.config.from_object(config_class)
    config_class.init_app(app)
    
    # Set the secret key from configuration
    app.secret_key = config_class.SECRET_KEY
    
    # Initialize extensions with app
    csrf.init_app(app)
    login_manager.init_app(app)
    
    # Configure Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'נא להתחבר כדי לגשת לדף זה.'
    login_manager.login_message_category = 'info'
    
    # Configure templates to search both legacy and new directories
    _configure_templates(app)
    
    # Configure logging
    _configure_logging(app)
    
    # Initialize user manager
    _initialize_user_manager(app)
    
    # Register blueprints
    _register_blueprints(app)
    
    # Register error handlers
    _register_error_handlers(app)
    
    # Register backward compatibility routes
    _register_compatibility_routes(app)
    
    # Log application startup
    app.logger.info(f'Data Analyzer application startup - Config: {config_name}')
    
    return app


def _configure_templates(app: Flask) -> None:
    """
    Configure Jinja2 template loader to search multiple directories.
    
    This allows the app to find templates in both the legacy 'templates'
    directory and the new 'app/templates' directory structure.
    
    Args:
        app (Flask): Flask application instance
    """
    from jinja2 import ChoiceLoader, FileSystemLoader
    import os
    
    # Define template search paths
    template_paths = [
        os.path.join(os.getcwd(), 'templates'),      # Legacy templates
        os.path.join(os.getcwd(), 'app', 'templates') # New organized templates
    ]
    
    # Create choice loader that searches multiple directories
    app.jinja_loader = ChoiceLoader([
        FileSystemLoader(path) for path in template_paths if os.path.exists(path)
    ])
    
    app.logger.debug(f'Template loader configured with paths: {template_paths}')


def _configure_logging(app: Flask) -> None:
    """
    Configure application logging with rotating file handler.
    
    Args:
        app (Flask): Flask application instance
    """
    
    # Create logs directory if it doesn't exist
    if not os.path.exists(app.config['LOG_DIRECTORY']):
        try:
            os.makedirs(app.config['LOG_DIRECTORY'])
            print(f"Created '{app.config['LOG_DIRECTORY']}' directory.")
        except OSError as e:
            print(f"Error creating logs directory: {e}")
    
    # Set up file handler with rotation
    file_handler = RotatingFileHandler(
        app.config['LOG_FILE'],
        maxBytes=app.config['LOG_MAX_BYTES'],
        backupCount=app.config['LOG_BACKUP_COUNT']
    )
    
    # Configure log format
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    
    # Set log level based on debug mode
    if app.debug:
        app.logger.setLevel(logging.DEBUG)
        file_handler.setLevel(logging.DEBUG)
        app.logger.info('Application startup - Running in DEBUG mode.')
    else:
        app.logger.setLevel(logging.INFO)
        file_handler.setLevel(logging.INFO)
        app.logger.info('Application startup - Logging to file initialized.')
    
    # Add handler to app logger
    app.logger.addHandler(file_handler)


def _initialize_user_manager(app: Flask) -> None:
    """
    Initialize the user manager with Flask-Login integration.
    
    Args:
        app (Flask): Flask application instance
    """
    from app.models import init_user_manager, get_user_manager
    
    # Initialize user manager
    init_user_manager(app)
    
    # Set up Flask-Login user loader
    @login_manager.user_loader
    def load_user(user_id_str):
        try:
            user_id = int(user_id_str)
            user_manager = get_user_manager()
            return user_manager.get_user(user_id)
        except (ValueError, RuntimeError):
            app.logger.error(f"Invalid user_id format or user manager not initialized: {user_id_str}")
            return None
    
    app.logger.debug('User manager initialized successfully')


def _register_blueprints(app: Flask) -> None:
    """
    Register all application blueprints.
    
    Args:
        app (Flask): Flask application instance
    """
    
    # Import blueprints (done here to avoid circular imports)
    from app.main import bp as main_bp
    from app.auth import bp as auth_bp
    from app.admin import bp as admin_bp
    
    # Register new architecture blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Register legacy blueprints for compatibility
    from app.main.routes import register_legacy_blueprints
    register_legacy_blueprints(app)
    
    app.logger.debug('All blueprints registered successfully')


def _register_error_handlers(app: Flask) -> None:
    """
    Register custom error handlers for the application.
    
    Args:
        app (Flask): Flask application instance
    """
    
    from flask import render_template
    from flask_wtf.csrf import CSRFError
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 Not Found errors."""
        app.logger.warning(f'404 error: {error}')
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors."""
        app.logger.error(f'500 error: {error}')
        return render_template('500.html'), 500
    
    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        """Handle CSRF token errors."""
        app.logger.warning(f'CSRF error: {error.description}')
        return render_template('csrf_error.html', reason=error.description), 400
    
    app.logger.debug('Error handlers registered successfully')


def _register_compatibility_routes(app: Flask) -> None:
    """
    Register backward compatibility routes for legacy templates.
    
    This ensures that old template references like url_for('login')
    continue to work with the new blueprint structure.
    
    Args:
        app (Flask): Flask application instance
    """
    from flask import redirect, url_for
    
    @app.route('/login', methods=['GET', 'POST'], endpoint='login')
    def login_compat():
        """Backward compatibility route for login."""
        return redirect(url_for('auth.login'))
    
    @app.route('/register', methods=['GET', 'POST'], endpoint='register')
    def register_compat():
        """Backward compatibility route for register."""
        return redirect(url_for('auth.register'))
    
    @app.route('/logout', endpoint='logout')
    def logout_compat():
        """Backward compatibility route for logout."""
        return redirect(url_for('auth.logout'))
    
    app.logger.debug('Backward compatibility routes registered')


# Import models to ensure they're available when using the app
from app import models