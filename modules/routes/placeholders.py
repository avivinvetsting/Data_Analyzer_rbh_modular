from flask import Blueprint, render_template

placeholders_bp = Blueprint('placeholders_bp', __name__)

@placeholders_bp.route('/annual-graphs')
def annual_graphs():
    """Placeholder for annual graphs page."""
    # This corresponds to 'גרפים שנתיים' and the route /graphs/annual [cite: 46]
    return render_template('empty_page.html', page_title="גרפים שנתיים")

@placeholders_bp.route('/quarterly-graphs')
def quarterly_graphs():
    """Placeholder for quarterly graphs page."""
    # This corresponds to 'גרפים רבעוניים' and the route /graphs/quarterly [cite: 46]
    return render_template('empty_page.html', page_title="גרפים רבעוניים")

@placeholders_bp.route('/valuations')
def valuations():
    """Placeholder for valuations page."""
    # This corresponds to 'הערכות שווי' and the route /valuations/ [cite: 48, 49]
    return render_template('empty_page.html', page_title="הערכות שווי")