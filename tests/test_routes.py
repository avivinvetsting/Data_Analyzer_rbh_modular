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
    response_html = response.data.decode('utf-8')
    
    # בדוק שהטקסט המרכזי של הכותרת קיים ב-HTML
    assert "ניתוח מניות - דף הבית" in response_html
    
    # בדוק באופן כללי שתג <h1> קיים (בלי להתייחס לתוכן שלו או למאפיינים)
    # זה פחות קריטי אם הבדיקה הקודמת עוברת, אבל יכול להוסיף ודאות שהמבנה הבסיסי נשמר.
    assert "<h1" in response_html 
    # או אם תרצה לוודא שזה כולל את מאפיין ה-style (אבל עדיין פחות שביר מהבדיקה המקורית):
    # assert '<h1 style="text-align: center;">' in response_html
    
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