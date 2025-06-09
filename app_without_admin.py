# app.py (MODIFIED - Authentication and Admin routes removed)
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import logging
from logging.handlers import RotatingFileHandler
import os
from werkzeug.security import generate_password_hash, check_password_hash
import json
import re
import warnings

# Display deprecation warning
warnings.warn(
    "This module is deprecated. Use run.py as the application entry point instead.",
    DeprecationWarning, stacklevel=2
)

# ---------------------------------------------------------------------------
# 1. טעינת המפתח הסודי
# ---------------------------------------------------------------------------
try:
    from secret import FLASK_SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD
    if not FLASK_SECRET_KEY: # בדיקה נוספת שהמפתח אינו מחרוזת ריקה
        raise ValueError("FLASK_SECRET_KEY in secret.py is empty.")
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        raise ValueError("ADMIN_USERNAME or ADMIN_PASSWORD in secret.py is empty or missing.")

except ImportError:
    # For testing, provide fallback values
    FLASK_SECRET_KEY = 'test_secret_key_fallback'
    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = 'Admin123!'
    print("="*80)
    print("שגיאה: קובץ secret.py לא נמצא - משתמש בערכי ברירת מחדל לבדיקות.")
    print("אנא צור קובץ secret.py בתיקייה הראשית של הפרויקט להפעלה בסביבת ייצור.")
    print("="*80) 
except ValueError as ve: # תופס את השגיאה שהעלינו אם המפתח ריק
    print("="*80)
    print(f"שגיאה קריטית בקובץ secret.py: {ve}")
    print("האפליקציה לא יכולה לעלות ללא הגדרות אלו.")
    print("="*80)
    raise SystemExit(f"CRITICAL: Configuration error in secret.py: {ve}. Application cannot start.")

# ---------------------------------------------------------------------------
# 2. יצירת אפליקציית Flask והגדרת מפתח סודי
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

# אתחול CSRF
csrf = CSRFProtect(app)

# הגדרות סשן
app.config['SESSION_COOKIE_SECURE'] = True  # שינוי ל-True בטסטים
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

# ---------------------------------------------------------------------------
# 3. הגדרת מערכת הלוגינג (Logging)
# ---------------------------------------------------------------------------
if not os.path.exists('logs'):
    try:
        os.mkdir('logs')
        print("Created 'logs' directory.")
    except OSError as e:
        print(f"Error creating logs directory: {e}")

file_handler = RotatingFileHandler('logs/data_analyzer.log', maxBytes=10240000, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
if app.debug:
    app.logger.setLevel(logging.DEBUG)
    file_handler.setLevel(logging.DEBUG) 
    app.logger.info('Data Analyzer application startup - Running in DEBUG mode.')
else:
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.info('Data Analyzer application startup - Logging to file initialized.')
app.logger.addHandler(file_handler)

# ---------------------------------------------------------------------------
# 4. הגדרת מערכת Login
# ---------------------------------------------------------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'  # Updated to use blueprint route
login_manager.login_message = 'נא להתחבר כדי לגשת לדף זה.'
login_manager.login_message_category = 'info'

class User(UserMixin):
    def __init__(self, id, username, password_hash, is_approved=False):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.is_approved = is_approved

USERS_FILE = 'users.json'

def save_users(users_dict):
    users_data = {str(uid): {
        'username': u.username, 
        'password_hash': u.password_hash,
        'is_approved': u.is_approved
    } for uid, u in users_dict.items()}
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users_data, f, indent=4)
        app.logger.info("Users data saved successfully.")
    except IOError as e:
        app.logger.error(f"Error saving users data to {USERS_FILE}: {e}")

def load_users():
    if not os.path.exists(USERS_FILE):
        app.logger.info(f"{USERS_FILE} not found. Creating initial admin user.")
        hashed_password = generate_password_hash(ADMIN_PASSWORD)
        app.logger.info(f"Admin username: {ADMIN_USERNAME}, Hashed password (prefix): {hashed_password[:10]}...")
        users = {1: User(1, ADMIN_USERNAME, hashed_password, True)}
        save_users(users)
        return users
    try:
        with open(USERS_FILE, 'r') as f:
            users_data = json.load(f)
        loaded_users = {int(uid): User(
            int(uid), 
            data['username'], 
            data['password_hash'],
            data.get('is_approved', False)
        ) for uid, data in users_data.items()}
        app.logger.info(f"Users loaded successfully from {USERS_FILE}. Count: {len(loaded_users)}")
        return loaded_users
    except (IOError, json.JSONDecodeError, KeyError, TypeError) as e:
        app.logger.error(f"Error loading users from {USERS_FILE}: {e}. Falling back to initial admin user ONLY.")
        hashed_password = generate_password_hash(ADMIN_PASSWORD)
        return {1: User(1, ADMIN_USERNAME, hashed_password, True)}

USERS = load_users()

@login_manager.user_loader
def load_user(user_id_str):
    try:
        user_id = int(user_id_str)
        user = USERS.get(user_id)
        if user:
            app.logger.debug(f"User loaded by ID: {user_id} -> {user.username} (Approved: {user.is_approved})")
        else:
            app.logger.warning(f"User ID {user_id} not found in USERS during load_user.")
        return user
    except ValueError:
        app.logger.error(f"Invalid user_id format: {user_id_str}. Cannot convert to int.")
        return None

# Authentication routes removed - now using blueprints
# Admin routes removed - now using admin blueprint

# ---------------------------------------------------------------------------
# 5. אתחול CSRF protection
# ---------------------------------------------------------------------------
csrf = CSRFProtect()
csrf.init_app(app)
app.logger.info("CSRF protection initialized.")
app.config['CSRF_TIME_LIMIT'] = 3600

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    app.logger.warning(f"CSRF Error: {e.description}. IP: {request.remote_addr if request else 'Unknown'}. URL: {request.url if request else 'N/A'}")
    return render_template('csrf_error.html', reason=e.description), 400

# ---------------------------------------------------------------------------
# 6. טיפול בשגיאות כלליות HTTP
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def page_not_found_error_handler(error):
    app.logger.warning(f"404 Error: Page not found at {request.url} - IP: {request.remote_addr if request else 'Unknown'}")
    return render_template('404.html', error=error), 404

@app.errorhandler(500)
def internal_server_error_handler(error):
    app.logger.error(f"500 Internal Server Error: {error} at {request.url} - IP: {request.remote_addr if request else 'Unknown'}")
    app.logger.exception("Detailed traceback for 500 error:")
    return render_template('500.html', error=error), 500

# ---------------------------------------------------------------------------
# 7. ייבוא ורישום Blueprints
# ---------------------------------------------------------------------------
try:
    from modules.routes.home import home_bp
    app.register_blueprint(home_bp)
    app.logger.debug("Registered home_bp blueprint.")
    
    # Register auth blueprint if it exists
    try:
        from app.auth import bp as auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.logger.debug("Registered auth_bp blueprint.")
    except ImportError:
        app.logger.warning("Could not import auth blueprint - using direct auth routes only.")
except ImportError as e_import:
    app.logger.critical(f"CRITICAL: Could not import or register home_bp: {e_import}.")

try:
    from modules.routes.graphs import graphs_bp
    app.register_blueprint(graphs_bp)
    app.logger.debug("Registered graphs_bp blueprint.")
except ImportError as e_import:
    app.logger.warning(f"Could not import or register graphs_bp: {e_import}")

try:
    from modules.routes.valuations import valuations_bp
    app.register_blueprint(valuations_bp)
    app.logger.debug("Registered valuations_bp blueprint.")
except ImportError as e_import:
    app.logger.warning(f"Could not import or register valuations_bp: {e_import}")

try:
    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.logger.debug("Registered admin_bp blueprint.")
except ImportError as e_import:
    app.logger.warning(f"Could not import or register admin_bp: {e_import}")

# Entry point removed - use run.py instead
