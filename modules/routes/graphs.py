from flask import Blueprint, render_template

graphs_bp = Blueprint('graphs_bp', __name__, url_prefix='/graphs') # הוספת url_prefix

@graphs_bp.route('/annual')
def annual_graphs_page():
    """Renders the annual graphs page."""
    return render_template('graphs_page.html', page_title="גרפים שנתיים")

@graphs_bp.route('/quarterly')
def quarterly_graphs_page():
    """Renders the quarterly graphs page."""
    return render_template('graphs_page.html', page_title="גרפים רבעוניים")