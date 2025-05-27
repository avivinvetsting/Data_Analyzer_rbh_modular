from flask import Flask

app = Flask(__name__)
app.secret_key = 'your_very_secure_random_secret_key_here'

# Import and register blueprints
from modules.routes.home import home_bp
from modules.routes.graphs import graphs_bp  # חדש
from modules.routes.valuations import valuations_bp # חדש
# from modules.routes.placeholders import placeholders_bp # נסיר או נשנה אם כבר לא בשימוש לדפים אלו

app.register_blueprint(home_bp)
app.register_blueprint(graphs_bp) # חדש
app.register_blueprint(valuations_bp) # חדש
# app.register_blueprint(placeholders_bp) # נסיר או נשנה

if __name__ == '__main__':
    app.run(debug=True)