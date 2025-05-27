import pytest
from app import app # ייבוא אפליקציית ה-Flask שלך

@pytest.fixture
def client():
    """Create and configure a new app instance for each test."""
    # app.config['TESTING'] = True # מומלץ להוסיף בהמשך
    with app.test_client() as client:
        yield client

def test_home_page(client):
    """Test that the home page loads correctly."""
    response = client.get('/')
    assert response.status_code == 200
    # Decode response.data to a string and compare with a unicode string
    assert "<h1>ניתוח מניות - דף הבית</h1>" in response.data.decode('utf-8')

def test_annual_graphs_page(client):
    """Test that the annual graphs page loads correctly (placeholder)."""
    response = client.get('/graphs/annual')
    assert response.status_code == 200
    # Decode response.data to a string
    assert "<h1>גרפים שנתיים</h1>" in response.data.decode('utf-8')

def test_quarterly_graphs_page(client):
    """Test that the quarterly graphs page loads correctly (placeholder)."""
    response = client.get('/graphs/quarterly')
    assert response.status_code == 200
    # Decode response.data to a string
    assert "<h1>גרפים רבעוניים</h1>" in response.data.decode('utf-8')

def test_valuations_page(client):
    """Test that the valuations page loads correctly (placeholder)."""
    response = client.get('/valuations/') # Ensure trailing slash matches your route definition
    assert response.status_code == 200
    # Decode response.data to a string
    assert "<h1>הערכות שווי</h1>" in response.data.decode('utf-8')