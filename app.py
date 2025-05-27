# app.py
from flask import Flask, render_template, request # הוספנו request לטיפול בשגיאת CSRF
from flask_wtf.csrf import CSRFProtect, CSRFError
import logging
from logging.handlers import RotatingFileHandler
import os

# ---------------------------------------------------------------------------
# 1. טעינת המפתח הסודי
# ---------------------------------------------------------------------------
try:
    from secret import FLASK_SECRET_KEY
except ImportError:
    FLASK_SECRET_KEY = 'a_default_fallback_key_for_development_only_CHANGE_ME'
    print("="*80)
    print("אזהרה: קובץ secret.py לא נמצא או ש-FLASK_SECRET_KEY אינו מוגדר בו.")
    print("נעשה שימוש במפתח ברירת מחדל חלש. אנא צור קובץ secret.py עם מפתח חזק.")
    print("="*80)

# ---------------------------------------------------------------------------
# 2. יצירת אפליקציית Flask והגדרת מפתח סודי
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

# ---------------------------------------------------------------------------
# 3. הגדרת מערכת הלוגינג (Logging)
# ---------------------------------------------------------------------------
# הגדרת לוגינג לקובץ רק אם אנחנו לא במצב debug
if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = RotatingFileHandler('logs/data_analyzer.log', maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Data Analyzer application startup - Logging to file initialized.')
else: # אם אנחנו במצב debug
    app.logger.setLevel(logging.DEBUG) # אפשר לראות הודעות DEBUG בקונסול
    app.logger.info('Data Analyzer application startup - Running in DEBUG mode.')

# ---------------------------------------------------------------------------
# 4. אתחול CSRF protection
# ---------------------------------------------------------------------------
csrf = CSRFProtect()
csrf.init_app(app)
app.logger.info("CSRF protection initialized.")

# הגדרות אבטחה בסיסיות ל-CSRF - מותאמות לפיתוח (אפשר לשנות לייצור)
app.config['CSRF_COOKIE_SECURE'] = False  # מאפשר HTTP בפיתוח. לייצור: True (דורש HTTPS)
app.config['CSRF_COOKIE_HTTPONLY'] = True
app.config['CSRF_COOKIE_SAMESITE'] = 'Lax'

# טיפול בשגיאות CSRF - הצגת דף שגיאה ידידותי יותר
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    app.logger.warning(f"CSRF Error: {e.description}. IP: {request.remote_addr if request else 'Unknown'}")
    return render_template('csrf_error.html', reason=e.description), 400

# ---------------------------------------------------------------------------
# 5. ייבוא ורישום Blueprints
# ---------------------------------------------------------------------------
try:
    from modules.routes.home import home_bp
    app.register_blueprint(home_bp)
    app.logger.debug("Registered home_bp blueprint.")
except ImportError as e_import:
    app.logger.error(f"Could not import or register home_bp: {e_import}")

try:
    from modules.routes.graphs import graphs_bp
    app.register_blueprint(graphs_bp) # ה-url_prefix מוגדר כבר בקובץ graphs.py
    app.logger.debug("Registered graphs_bp blueprint.")
except ImportError as e_import:
    app.logger.warning(f"Could not import or register graphs_bp: {e_import} - This blueprint may not be available.")

try:
    from modules.routes.valuations import valuations_bp
    app.register_blueprint(valuations_bp) # ה-url_prefix מוגדר כבר בקובץ valuations.py
    app.logger.debug("Registered valuations_bp blueprint.")
except ImportError as e_import:
    app.logger.warning(f"Could not import or register valuations_bp: {e_import} - This blueprint may not be available.")

# אם אתה משתמש גם ב-placeholders_bp, ודא שהוא לא מתנגש עם הנתיבים האחרים
# from modules.routes.placeholders import placeholders_bp
# app.register_blueprint(placeholders_bp)
# app.logger.debug("Registered placeholders_bp blueprint.")

# ---------------------------------------------------------------------------
# 6. הרצת האפליקציה (רק אם הקובץ הזה מורץ ישירות)
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    app.logger.info(f"Starting Flask development server (debug mode: {app.debug}). Access at http://0.0.0.0:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)