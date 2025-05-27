from flask import Flask
from flask_wtf.csrf import CSRFProtect, CSRFError
import sys

# נסה לייבא את המפתח מקובץ secret.py
try:
    from secret import FLASK_SECRET_KEY
except ImportError:
    FLASK_SECRET_KEY = 'a_default_fallback_key_for_development_only_CHANGE_ME'
    print("="*80)
    print("אזהרה: קובץ secret.py לא נמצא או ש-FLASK_SECRET_KEY אינו מוגדר בו.")
    print("נעשה שימוש במפתח ברירת מחדל חלש. אנא צור קובץ secret.py עם מפתח חזק.")
    print("="*80)

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

# אתחול CSRF protection
csrf = CSRFProtect()
csrf.init_app(app)

# הגדרות אבטחה בסיסיות ל-CSRF - מותאמות לפיתוח
app.config['CSRF_COOKIE_SECURE'] = False  # מאפשר HTTP בפיתוח
app.config['CSRF_COOKIE_HTTPONLY'] = True
app.config['CSRF_COOKIE_SAMESITE'] = 'Lax'  # פחות מגביל מ-Strict

# טיפול בשגיאות CSRF
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    return "CSRF token missing or invalid", 400

# Import and register blueprints
from modules.routes.home import home_bp
from modules.routes.graphs import graphs_bp
from modules.routes.valuations import valuations_bp

app.register_blueprint(home_bp)
app.register_blueprint(graphs_bp)
app.register_blueprint(valuations_bp)

if __name__ == '__main__':
    app.run(debug=True)