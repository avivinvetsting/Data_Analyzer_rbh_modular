# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
# current_user מיובא מ-flask_login
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import logging
from logging.handlers import RotatingFileHandler
import os
from werkzeug.security import generate_password_hash, check_password_hash
import json

# ---------------------------------------------------------------------------
# 1. טעינת המפתח הסודי
# ---------------------------------------------------------------------------
try:
    from secret import FLASK_SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD
except ImportError:
    print("="*80)
    print("שגיאה: קובץ secret.py לא נמצא או שחסרים בו הגדרות.")
    print("אנא צור קובץ secret.py עם המפתח והפרטים הבאים:")
    print("FLASK_SECRET_KEY = 'your_strong_random_key'")
    print("ADMIN_USERNAME = 'your_admin_username'")
    print("ADMIN_PASSWORD = 'your_admin_password'")
    print("="*80)
    # במקום SystemExit, נעלה חריגה כדי שהשרת יתרסק אם הקובץ קריטי ולא נמצא
    raise ImportError("Critical: secret.py not found or misconfigured. Application cannot start if it's essential.")


# ---------------------------------------------------------------------------
# 2. יצירת אפליקציית Flask והגדרת מפתח סודי
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

# הגדרות אבטחה בסיסיות לסשן
# ב-production, מומלץ להגדיר SESSION_COOKIE_SECURE = True (דורש HTTPS)
app.config['SESSION_COOKIE_SECURE'] = False 
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # שעה אחת (בשניות)

# ---------------------------------------------------------------------------
# 3. הגדרת מערכת הלוגינג (Logging)
# ---------------------------------------------------------------------------
if not os.path.exists('logs'):
    try:
        os.mkdir('logs')
        print("Created 'logs' directory.") # הודעה לקונסול
    except OSError as e:
        print(f"Error creating logs directory: {e}") # הדפסת שגיאה לקונסול

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
login_manager.login_view = 'login' # שם הפונקציה (endpoint) של נתיב הלוגין
login_manager.login_message = 'נא להתחבר כדי לגשת לדף זה.' # הודעה למשתמש לא מאומת
login_manager.login_message_category = 'info' # קטגוריה להודעת ה-flash

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
        hashed_password = generate_password_hash(ADMIN_PASSWORD) # השתמש ב-ADMIN_PASSWORD מקובץ secret.py
        app.logger.info(f"Admin username: {ADMIN_USERNAME}, Hashed password (prefix): {hashed_password[:10]}...")
        users = {
            1: User(1, ADMIN_USERNAME, hashed_password, True) # משתמש מנהל מאושר כברירת מחדל
        }
        save_users(users)
        return users
    
    try:
        with open(USERS_FILE, 'r') as f:
            users_data = json.load(f)
        
        loaded_users = {int(uid): User(
            int(uid), 
            data['username'], 
            data['password_hash'],
            data.get('is_approved', False) # .get() עם ערך ברירת מחדל למקרה שהשדה חסר בקבצים ישנים
        ) for uid, data in users_data.items()}
        app.logger.info(f"Users loaded successfully from {USERS_FILE}. Count: {len(loaded_users)}")
        return loaded_users
    except (IOError, json.JSONDecodeError, KeyError, TypeError) as e: # הוספתי TypeError לכיסוי מקרים נוספים
        app.logger.error(f"Error loading users from {USERS_FILE}: {e}. Falling back to initial admin user ONLY.")
        hashed_password = generate_password_hash(ADMIN_PASSWORD)
        users = {
            1: User(1, ADMIN_USERNAME, hashed_password, True)
        }
        # במקרה של שגיאה בטעינה, אל תנסה לשמור כאן את המשתמש הדיפולטיבי כדי למנוע דריסה אפשרית
        return users


USERS = load_users()

@login_manager.user_loader
def load_user(user_id_str): # השם שונה כדי להבהיר שזה מחרוזת
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


# נתיב ברירת מחדל '/' מוגדר ב-home_bp, אז נסיר את ההגדרה הכפולה מכאן.
# @app.route('/')
# def index():
#     if not current_user.is_authenticated:
#         return redirect(url_for('login'))
#     # הפניה לדף הראשי של האפליקציה (שמוגדר ב-home_bp)
#     return redirect(url_for('home_bp.index')) 


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        app.logger.info(f"User '{current_user.username}' already authenticated, redirecting to home_bp.index.")
        return redirect(url_for('home_bp.index')) 
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        app.logger.info(f"Login attempt for username: '{username}'")
        
        user_found = None
        for u in USERS.values(): # USERS הוא dict, אז USERS.values()
            if u.username == username:
                user_found = u
                break
        
        if user_found and check_password_hash(user_found.password_hash, password):
            if not user_found.is_approved:
                flash('חשבונך ממתין לאישור מנהל.', 'warning')
                app.logger.warning(f"Unapproved user '{username}' attempted to login.")
                return render_template('login.html')
                
            login_user(user_found)
            app.logger.info(f"User '{username}' logged in successfully.")
            session.permanent = True 
            next_page = request.args.get('next')
            
            if next_page and not (next_page.startswith('/') or next_page.startswith(request.host_url)):
                app.logger.warning(f"Potentially unsafe next_page URL '{next_page}' in login. Redirecting to home_bp.index.")
                next_page = None 

            return redirect(next_page or url_for('home_bp.index'))
        
        flash('שם משתמש או סיסמה שגויים.', 'danger') # השתמש ב-danger לשגיאות קריטיות יותר
        app.logger.warning(f"Failed login attempt for username: '{username}'.")
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home_bp.index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        app.logger.info(f"Registration attempt for username: '{username}'")

        if not username or not password or not confirm_password:
            flash('נא למלא את כל השדות.', 'warning')
            return render_template('register.html')
            
        if len(password) < 6:
            flash('הסיסמה חייבת להכיל לפחות 6 תווים.', 'warning')
            return render_template('register.html')

        if password != confirm_password:
            flash('הסיסמאות אינן תואמות.', 'warning')
            return render_template('register.html')
            
        if any(u.username == username for u in USERS.values()): # USERS הוא dict
            flash('שם המשתמש כבר קיים במערכת.', 'warning')
            app.logger.warning(f"Registration failed: Username '{username}' already exists.")
            return render_template('register.html')
        
        new_id = max(USERS.keys(), default=0) + 1 
        USERS[new_id] = User(new_id, username, generate_password_hash(password), False) 
        save_users(USERS)
        
        flash('ההרשמה הושלמה בהצלחה! אנא המתן לאישור מנהל.', 'success')
        app.logger.info(f"New user registered (pending approval): '{username}' with ID {new_id}.")
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    username = current_user.username 
    logout_user()
    app.logger.info(f"User '{username}' logged out.")
    flash('התנתקת בהצלחה.', 'info')
    return redirect(url_for('login'))


@app.route('/admin/users')
@login_required
def manage_users():
    app.logger.info(f"User '{current_user.username}' attempting to access user management.")
    if current_user.id != 1: 
        flash('אין לך הרשאות לגשת לדף זה.', 'danger')
        app.logger.warning(f"User '{current_user.username}' (ID: {current_user.id}) denied access to user management.")
        return redirect(url_for('home_bp.index'))
        
    app.logger.info(f"Admin user '{current_user.username}' accessed user management.")
    # העבר את המילון של משתמשים לתבנית
    return render_template('admin/users.html', users=USERS)

@app.route('/admin/users/<int:user_id>/<action>')
@login_required
def user_action(user_id, action):
    app.logger.info(f"Admin '{current_user.username}' attempting action '{action}' on user ID {user_id}.")
    if current_user.id != 1:
        flash('אין לך הרשאות לבצע פעולה זו.', 'danger')
        app.logger.warning(f"User '{current_user.username}' denied permission for user action '{action}' on user ID {user_id}.")
        return redirect(url_for('home_bp.index'))
        
    target_user = USERS.get(user_id) # חיפוש במילון לפי מפתח
    if not target_user:
        flash('משתמש לא נמצא.', 'danger')
        app.logger.warning(f"User action failed: User ID {user_id} not found.")
        return redirect(url_for('manage_users')) # שם הפונקציה של ניהול משתמשים
        
    if action == 'approve':
        target_user.is_approved = True
        save_users(USERS)
        flash(f'משתמש {target_user.username} אושר בהצלחה.', 'success')
        app.logger.info(f"User '{target_user.username}' (ID: {user_id}) was approved by admin '{current_user.username}'.")
    elif action == 'delete': # שיניתי מ-reject ל-delete כדי להתאים ללוגיקה שלך
        if user_id == 1: 
            flash('לא ניתן למחוק את חשבון המנהל הראשי.', 'danger')
            app.logger.warning(f"Admin '{current_user.username}' attempted to delete primary admin account (ID: {user_id}). Action denied.")
        else:
            deleted_username = target_user.username
            del USERS[user_id] # מחיקה מהמילון
            save_users(USERS)
            flash(f'משתמש {deleted_username} נמחק בהצלחה.', 'success')
            app.logger.info(f"User '{deleted_username}' (ID: {user_id}) was deleted by admin '{current_user.username}'.")
    else:
        flash('פעולה לא חוקית.', 'warning')
        app.logger.warning(f"Invalid action '{action}' attempted on user ID {user_id} by admin '{current_user.username}'.")
        
    return redirect(url_for('manage_users')) # שם הפונקציה של ניהול משתמשים


# ---------------------------------------------------------------------------
# 5. אתחול CSRF protection
# ---------------------------------------------------------------------------
csrf = CSRFProtect()
csrf.init_app(app)
app.logger.info("CSRF protection initialized.")

# הגדרות אבטחה ל-CSRF הועברו למעלה אחרי יצירת app
app.config['CSRF_TIME_LIMIT'] = 3600  # שעה אחת (בשניות)

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    app.logger.warning(f"CSRF Error: {e.description}. IP: {request.remote_addr if request else 'Unknown'}. URL: {request.url if request else 'N/A'}")
    return render_template('csrf_error.html', reason=e.description), 400

# ---------------------------------------------------------------------------
# 6. טיפול בשגיאות כלליות HTTP
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def page_not_found(error): # שיניתי את שם הפונקציה כדי שיהיה ייחודי
    app.logger.warning(f"404 Error: Page not found at {request.url} - IP: {request.remote_addr if request else 'Unknown'}")
    return render_template('404.html', error=error), 404

@app.errorhandler(500)
def internal_server_error(error): # שיניתי את שם הפונקציה
    app.logger.error(f"500 Internal Server Error: {error} at {request.url} - IP: {request.remote_addr if request else 'Unknown'}")
    app.logger.exception("Detailed traceback for 500 error:")
    return render_template('500.html', error=error), 500

# ---------------------------------------------------------------------------
# 7. ייבוא ורישום Blueprints
# ---------------------------------------------------------------------------
try:
    from modules.routes.home import home_bp
    app.register_blueprint(home_bp) # נתיב ראשי / יוגדר ב-home_bp
    app.logger.debug("Registered home_bp blueprint.")
except ImportError as e_import:
    app.logger.critical(f"CRITICAL: Could not import or register home_bp: {e_import}. Application might not work correctly.")
    # אפשר להעלות SystemExit אם ה-blueprint הזה חיוני
    # raise SystemExit(f"Critical error: home_bp could not be registered: {e_import}")

try:
    from modules.routes.graphs import graphs_bp
    app.register_blueprint(graphs_bp) # ה-url_prefix מוגדר כבר ב-graphs.py
    app.logger.debug("Registered graphs_bp blueprint.")
except ImportError as e_import:
    app.logger.warning(f"Could not import or register graphs_bp: {e_import}")

try:
    from modules.routes.valuations import valuations_bp
    app.register_blueprint(valuations_bp) # ה-url_prefix מוגדר כבר ב-valuations.py
    app.logger.debug("Registered valuations_bp blueprint.")
except ImportError as e_import:
    app.logger.warning(f"Could not import or register valuations_bp: {e_import}")

# אם אתה משתמש גם ב-placeholders_bp, ודא שהוא לא מתנגש עם הנתיבים האחרים
# from modules.routes.placeholders import placeholders_bp
# app.register_blueprint(placeholders_bp)
# app.logger.debug("Registered placeholders_bp blueprint.")

# ---------------------------------------------------------------------------
# 8. הרצת האפליקציה
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    app.logger.info(f"Starting Flask development server (debug mode: {app.debug}).")
    app.run(debug=True, host='0.0.0.0', port=5000) # debug=True מפעיל את הדיבאגר של Flask