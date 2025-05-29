from flask import Blueprint, render_template
from flask_login import login_required

graphs_bp = Blueprint('graphs_bp', __name__, url_prefix='/graphs')

@graphs_bp.route('/annual')
@login_required
def annual_graphs_page():
    return render_template('graphs_page.html', page_title="גרפים שנתיים")

@graphs_bp.route('/quarterly')
@login_required
def quarterly_graphs_page():
    return render_template('graphs_page.html', page_title="גרפים רבעוניים")