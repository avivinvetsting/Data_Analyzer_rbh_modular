# tests/test_routes.py
import pytest
from app import app # ייבוא אפליקציית ה-Flask שלך
from flask import url_for
from urllib.parse import unquote

@pytest.fixture
def client():
    """Create and configure a new app instance for each test."""
    app.config['TESTING'] = True
    # הגדרת SERVER_NAME הכרחית כדי ש-url_for יעבוד מחוץ לקונטקסט בקשה פעילה בבדיקות
    app.config['SERVER_NAME'] = 'localhost.localdomain' 
    # לפעמים צריך גם את זה, אבל נתחיל רק עם SERVER_NAME
    # app.config['APPLICATION_ROOT'] = '/'
    # app.config['PREFERRED_URL_SCHEME'] = 'http'
    
    with app.test_client() as client:
        with app.app_context(): # דחיפת קונטקסט אפליקציה
            yield client

def test_home_page_redirects_when_not_logged_in(client):
    """Test that the home page (home_bp.index) redirects to login when not logged in."""
    target_url = url_for('home_bp.index', _external=False)  # Get relative path only
    response = client.get(target_url)
    assert response.status_code == 302
    # ודא שההפניה היא לדף הלוגין, ושהיא כוללת את 'next' שמפנה חזרה לדף המקורי
    expected_redirect_path = url_for('login', next=target_url, _external=False)
    # Decode URL encoding in response.location to handle %2F -> /
    actual_location_decoded = unquote(response.location)
    assert expected_redirect_path in actual_location_decoded 

def test_annual_graphs_page_redirects_when_not_logged_in(client):
    """Test that the annual graphs page redirects to login when not logged in."""
    target_url = url_for('graphs_bp.annual_graphs_page', _external=False)
    response = client.get(target_url)
    assert response.status_code == 302
    expected_redirect_path = url_for('login', next=target_url, _external=False)
    actual_location_decoded = unquote(response.location)
    assert expected_redirect_path in actual_location_decoded

def test_quarterly_graphs_page_redirects_when_not_logged_in(client):
    """Test that the quarterly graphs page redirects to login when not logged in."""
    target_url = url_for('graphs_bp.quarterly_graphs_page', _external=False)
    response = client.get(target_url)
    assert response.status_code == 302
    expected_redirect_path = url_for('login', next=target_url, _external=False)
    actual_location_decoded = unquote(response.location)
    assert expected_redirect_path in actual_location_decoded

def test_valuations_page_redirects_when_not_logged_in(client):
    """Test that the valuations page redirects to login when not logged in."""
    target_url = url_for('valuations_bp.valuations_page', _external=False)
    response = client.get(target_url)
    assert response.status_code == 302
    expected_redirect_path = url_for('login', next=target_url, _external=False)
    actual_location_decoded = unquote(response.location)
    assert expected_redirect_path in actual_location_decoded