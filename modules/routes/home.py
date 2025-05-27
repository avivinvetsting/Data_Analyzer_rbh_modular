from flask import Blueprint, render_template

home_bp = Blueprint('home_bp', __name__)

@home_bp.route('/')
def home():
    """Renders the home page."""
    # The project_map.md indicates that the home page might eventually display
    # a candlestick chart and data load status after ticker selection. [cite: 45]
    # For now, it just renders the initial content.
    return render_template('content_home.html')

# The ticker submission will be handled by a POST request to this route later. [cite: 45]
@home_bp.route('/set_ticker', methods=['POST'])
def set_ticker():
    # Logic for handling ticker submission will go here.
    # For now, it can just redirect back to home or show a message.
    # This aligns with "מעבד בחירת טיקר (POST request)" [cite: 45]
    return "Ticker selection processing (not implemented yet)"