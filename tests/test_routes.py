import pytest
from app import app

@pytest.fixture
def client():
    """Create and configure a new app instance for each test."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def authenticated_client(client):
    """Create an authenticated client session."""
    # Login as admin using actual credentials from secret.py
    response = client.post('/login', data={
        'username': 'admin',
        'password': 'Admin123!'
    }, follow_redirects=True)
    return client

def test_login_page_loads(client):
    """Test that login page loads without authentication."""
    response = client.get('/login')
    assert response.status_code == 200
    # Check for login form elements instead of specific text
    html = response.data.decode('utf-8')
    assert 'name="username"' in html
    assert 'name="password"' in html
    assert 'type="password"' in html

def test_home_page_requires_auth(client):
    """Test that home page redirects when not authenticated."""
    response = client.get('/', follow_redirects=False)
    assert response.status_code == 302  # Redirect to login

def test_home_page_with_auth(authenticated_client):
    """Test that home page loads correctly when authenticated."""
    response = authenticated_client.get('/')
    assert response.status_code == 200
    response_html = response.data.decode('utf-8')
    # Check for key elements that indicate successful page load
    assert "Stock Analysis - Home" in response_html
    assert "Logged in as: admin" in response_html
    assert "Please enter a stock ticker" in response_html

def test_annual_graphs_page(authenticated_client):
    """Test that the annual graphs page loads correctly (placeholder)."""
    response = authenticated_client.get('/graphs/annual')
    assert response.status_code == 200
    assert "<h1>גרפים שנתיים</h1>" in response.data.decode('utf-8')

def test_quarterly_graphs_page(authenticated_client):
    """Test that the quarterly graphs page loads correctly (placeholder)."""
    response = authenticated_client.get('/graphs/quarterly')
    assert response.status_code == 200
    assert "<h1>גרפים רבעוניים</h1>" in response.data.decode('utf-8')

def test_valuations_page(authenticated_client):
    """Test that the valuations page loads correctly (placeholder)."""
    response = authenticated_client.get('/valuations/')
    assert response.status_code == 200
    assert "<h1>הערכות שווי</h1>" in response.data.decode('utf-8')