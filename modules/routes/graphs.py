from flask import Blueprint, render_template

graphs_bp = Blueprint('graphs_bp', __name__, url_prefix='/graphs')

@graphs_bp.route('/annual')
def annual_graphs_page():
    return render_template('graphs_page.html', page_title="גרפים שנתיים")

@graphs_bp.route('/quarterly')
def quarterly_graphs_page():
    return render_template('graphs_page.html', page_title="גרפים רבעוניים")