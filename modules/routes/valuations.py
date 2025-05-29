from flask import Blueprint, render_template
from flask_login import login_required

valuations_bp = Blueprint('valuations_bp', __name__, url_prefix='/valuations') # הוספת url_prefix

@valuations_bp.route('/')
@login_required
def valuations_page():
    """Renders the valuations page."""
    return render_template('evaluation_page.html', page_title="הערכות שווי")