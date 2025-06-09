# tests/conftest.py
import pytest
from app import create_app  # Use application factory instead

# נסה לייבא את פרטי האדמין מקובץ ה-secret שלך
# אם הם לא שם, השתמש בברירת מחדל (פחות מומלץ לטווח ארוך אבל יכול לעזור לבדיקות להתחיל)
try:
    from secret import ADMIN_USERNAME, ADMIN_PASSWORD
except ImportError:
    ADMIN_USERNAME = 'admin'  # החלף אם יש לך שם משתמש אדמין דיפולטיבי אחר
    ADMIN_PASSWORD = 'Admin123!' # החלף אם יש לך סיסמת אדמין דיפולטיבית אחרת

@pytest.fixture(scope='session')
def app():
    """מגדיר את אפליקציית Flask עבור כל סשן הבדיקות."""
    flask_app = create_app('testing')  # Use testing configuration
    yield flask_app

@pytest.fixture()
def client(app):
    """מחזיר לקוח בדיקות של Flask."""
    return app.test_client()

@pytest.fixture()
def runner(app):
    """מחזיר רץ פקודות CLI של Flask לבדיקות."""
    return app.test_cli_runner()

@pytest.fixture
def authenticated_client(client):
    """
    מחזיר לקוח בדיקות של Flask שכבר ביצע התחברות למערכת
    כמשתמש האדמין שהוגדר (מ-secret.py או מברירת המחדל כאן).
    """
    login_response = client.post('/login', data={
        'username': ADMIN_USERNAME,
        'password': ADMIN_PASSWORD
    }, follow_redirects=True)
    
    # אפשר להוסיף כאן assert כדי לוודא שההתחברות באמת הצליחה, לדוגמה:
    # if b"שם משתמש או סיסמה שגויים." in login_response.data:
    #     raise AssertionError(f"Login failed for user {ADMIN_USERNAME} in authenticated_client fixture")
        
    return client