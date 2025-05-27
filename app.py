from flask import Flask

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

# Import and register blueprints
from modules.routes.home import home_bp # Blueprint של דף הבית
from modules.routes.graphs import graphs_bp
from modules.routes.valuations import valuations_bp

app.register_blueprint(home_bp) # *** ודא שרישום זה קיים ותקין ***
app.register_blueprint(graphs_bp)
app.register_blueprint(valuations_bp)

if __name__ == '__main__':
    app.run(debug=True)