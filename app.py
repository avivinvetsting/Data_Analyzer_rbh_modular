from flask import Flask
import sys

# הגדרת אורך מינימלי רצוי למפתח הסודי
MIN_SECRET_KEY_LENGTH = 32  # לדוגמה, מינימום 32 תווים

try:
    from secret import FLASK_SECRET_KEY
    
    known_weak_keys = [
        'your_very_secure_random_secret_key_here',
        'a_default_fallback_key_for_development_only_CHANGE_ME',
        'fallback_development_secret_key_CHANGE_ME' 
    ]

    error_message = None

    if not FLASK_SECRET_KEY:
        error_message = "CRITICAL ERROR: FLASK_SECRET_KEY in secret.py is not defined or is empty."
    elif FLASK_SECRET_KEY in known_weak_keys:
        error_message = "CRITICAL ERROR: FLASK_SECRET_KEY in secret.py is set to a common weak default value."
    elif len(FLASK_SECRET_KEY) < MIN_SECRET_KEY_LENGTH:
        error_message = (f"CRITICAL ERROR: FLASK_SECRET_KEY in secret.py is too short. "
                         f"It must be at least {MIN_SECRET_KEY_LENGTH} characters long for security. "
                         f"(Current length: {len(FLASK_SECRET_KEY)})")

    if error_message:
        print("="*80)
        print(error_message)
        print("The application cannot run without a strong, unique secret key.")
        print("Please define a strong and unique secret key in your secret.py file.")
        print("You can generate a strong key (64 hex characters) by running the following in a Python terminal:")
        print("python -c \"import secrets; print(secrets.token_hex(32))\"")
        print("="*80)
        sys.exit(1)

except ImportError:
    print("="*80)
    print("CRITICAL ERROR: The secret.py file was not found, or FLASK_SECRET_KEY is not defined within it.")
    print("The application cannot run without a proper secret key.")
    print("Please create a secret.py file in the project root and define a FLASK_SECRET_KEY variable with a strong, unique key.")
    print("For example, in your secret.py file, write:")
    print(f"FLASK_SECRET_KEY = 'your_generated_strong_secret_key_at_least_{MIN_SECRET_KEY_LENGTH}_chars_long'")
    print("You can generate a strong key (64 hex characters) by running the following in a Python terminal:")
    print("python -c \"import secrets; print(secrets.token_hex(32))\"")
    print("="*80)
    sys.exit(1)

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

# Import and register blueprints
from modules.routes.home import home_bp
from modules.routes.graphs import graphs_bp
from modules.routes.valuations import valuations_bp

app.register_blueprint(home_bp)
app.register_blueprint(graphs_bp)
app.register_blueprint(valuations_bp)

if __name__ == '__main__':
    app.run(debug=True)