import pytest
import os
import json
import tempfile
from unittest.mock import patch
from werkzeug.security import generate_password_hash
from app import app, USERS, save_users, load_users, User

@pytest.fixture
def client():
    """Create and configure a new app instance for each test."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def temp_users_file():
    """Create a temporary users file for testing."""
    temp_fd, temp_path = tempfile.mkstemp(suffix='.json')
    os.close(temp_fd)
    
    # Mock the USERS_FILE path
    with patch('app.USERS_FILE', temp_path):
        yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)

class TestAuthentication:
    
    def test_login_page_loads(self, client):
        """Test that login page loads correctly."""
        response = client.get('/login')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        # Check for login form elements
        assert 'Login' in html
        assert 'name="username"' in html
        assert 'name="password"' in html
    
    def test_register_page_loads(self, client):
        """Test that register page loads correctly."""
        response = client.get('/register')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        # Check for register form elements
        assert 'Register' in html
        assert 'name="username"' in html
        assert 'name="password"' in html
        assert 'name="confirm_password"' in html
    
    def test_login_with_valid_credentials(self, client):
        """Test successful login with valid credentials."""
        # Use the default admin credentials
        response = client.post('/login', data={
            'username': 'admin',  # From secret.py
            'password': 'Admin123!'  # From secret.py
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should redirect to home page after successful login
        html = response.data.decode('utf-8')
        assert ('Stock Analysis' in html or 'ניתוח מניות' in html)
    
    def test_login_with_invalid_credentials(self, client):
        """Test login failure with invalid credentials."""
        response = client.post('/login', data={
            'username': 'wronguser',
            'password': 'wrongpass'
        })
        
        assert response.status_code == 200
        assert 'שם משתמש או סיסמה שגויים' in response.data.decode('utf-8')
    
    def test_login_with_unapproved_user(self, client, temp_users_file):
        """Test login failure for unapproved user."""
        # Create an unapproved user
        users = {
            1: User(1, 'admin', generate_password_hash('Admin123!'), True),
            2: User(2, 'testuser', generate_password_hash('testpass'), False)  # Not approved
        }
        
        with patch('app.USERS', users):
            response = client.post('/login', data={
                'username': 'testuser',
                'password': 'testpass'
            })
            
            assert response.status_code == 200
            assert 'חשבונך ממתין לאישור מנהל' in response.data.decode('utf-8')
    
    def test_registration_with_valid_data(self, client, temp_users_file):
        """Test successful user registration."""
        with patch('app.USERS', {1: User(1, 'admin', generate_password_hash('Admin123!'), True)}):
            response = client.post('/register', data={
                'username': 'newuser',
                'password': 'newpass123',
                'confirm_password': 'newpass123'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            assert 'ההרשמה הושלמה בהצלחה' in response.data.decode('utf-8')
    
    def test_registration_with_mismatched_passwords(self, client):
        """Test registration failure with mismatched passwords."""
        response = client.post('/register', data={
            'username': 'newuser',
            'password': 'newpass123',
            'confirm_password': 'differentpass'
        })
        
        assert response.status_code == 200
        assert 'הסיסמאות אינן תואמות' in response.data.decode('utf-8')
    
    def test_registration_with_short_password(self, client):
        """Test registration failure with short password."""
        response = client.post('/register', data={
            'username': 'newuser',
            'password': '123',
            'confirm_password': '123'
        })
        
        assert response.status_code == 200
        assert 'הסיסמה חייבת להכיל לפחות 6 תווים' in response.data.decode('utf-8')
    
    def test_registration_with_existing_username(self, client):
        """Test registration failure with existing username."""
        response = client.post('/register', data={
            'username': 'admin',  # Already exists
            'password': 'newpass123',
            'confirm_password': 'newpass123'
        })
        
        assert response.status_code == 200
        assert 'שם המשתמש כבר קיים במערכת' in response.data.decode('utf-8')
    
    def test_registration_with_empty_fields(self, client):
        """Test registration failure with empty fields."""
        response = client.post('/register', data={
            'username': '',
            'password': '',
            'confirm_password': ''
        })
        
        assert response.status_code == 200
        assert 'נא למלא את כל השדות' in response.data.decode('utf-8')
    
    def test_logout_functionality(self, client):
        """Test logout functionality."""
        # First login
        client.post('/login', data={
            'username': 'admin',
            'password': 'Admin123!'
        })
        
        # Then logout
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        assert 'התנתקת בהצלחה' in response.data.decode('utf-8')
    
    def test_logout_requires_login(self, client):
        """Test that logout requires login."""
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        # Should redirect to login page
        html = response.data.decode('utf-8')
        assert 'Login' in html and 'name="username"' in html
    
    def test_home_requires_login(self, client):
        """Test that home page requires login."""
        response = client.get('/', follow_redirects=True)
        assert response.status_code == 200
        # Should redirect to login page
        html = response.data.decode('utf-8')
        assert 'Login' in html and 'name="username"' in html


class TestUserManagement:
    
    def test_user_creation_and_persistence(self, temp_users_file):
        """Test user creation and file persistence."""
        user = User(1, 'testuser', generate_password_hash('testpass'), True)
        users = {1: user}
        
        with patch('app.USERS_FILE', temp_users_file):
            save_users(users)
            
            # Verify file was created and contains correct data
            assert os.path.exists(temp_users_file)
            
            with open(temp_users_file, 'r') as f:
                saved_data = json.load(f)
            
            assert '1' in saved_data
            assert saved_data['1']['username'] == 'testuser'
            assert saved_data['1']['is_approved'] == True
    
    def test_load_users_from_file(self, temp_users_file):
        """Test loading users from file."""
        # Create test data
        test_data = {
            '1': {
                'username': 'admin',
                'password_hash': generate_password_hash('testpass'),
                'is_approved': True
            },
            '2': {
                'username': 'user2',
                'password_hash': generate_password_hash('pass2'),
                'is_approved': False
            }
        }
        
        with open(temp_users_file, 'w') as f:
            json.dump(test_data, f)
        
        with patch('app.USERS_FILE', temp_users_file):
            loaded_users = load_users()
        
        assert len(loaded_users) == 2
        assert loaded_users[1].username == 'admin'
        assert loaded_users[1].is_approved == True
        assert loaded_users[2].username == 'user2'
        assert loaded_users[2].is_approved == False
    
    def test_load_users_missing_file(self, temp_users_file):
        """Test loading users when file doesn't exist."""
        # Remove the temp file
        os.unlink(temp_users_file)
        
        with patch('app.USERS_FILE', temp_users_file):
            with patch('app.ADMIN_USERNAME', 'testadmin'):
                with patch('app.ADMIN_PASSWORD', 'testpass'):
                    loaded_users = load_users()
        
        # Should create default admin user
        assert len(loaded_users) == 1
        assert 1 in loaded_users
        assert loaded_users[1].username == 'testadmin'
        assert loaded_users[1].is_approved == True


class TestAdminFunctionality:
    
    def login_as_admin(self, client):
        """Helper method to login as admin."""
        return client.post('/login', data={
            'username': 'admin',
            'password': 'Admin123!'
        })
    
    def test_admin_users_page_access(self, client):
        """Test admin can access user management page."""
        self.login_as_admin(client)
        
        response = client.get('/admin/users')
        assert response.status_code == 200
        assert 'User Management' in response.data.decode('utf-8')
    
    def test_non_admin_users_page_denied(self, client):
        """Test non-admin users cannot access user management."""
        # Create a non-admin user and login
        users = {
            1: User(1, 'admin', generate_password_hash('Admin123!'), True),
            2: User(2, 'testuser', generate_password_hash('testpass'), True)
        }
        
        with patch('app.USERS', users):
            # Login as non-admin user (ID 2)
            with client.session_transaction() as sess:
                sess['_user_id'] = '2'
            
            response = client.get('/admin/users', follow_redirects=True)
            assert response.status_code == 200
            assert 'אין לך הרשאות לגשת לדף זה' in response.data.decode('utf-8')
    
    def test_admin_approve_user(self, client):
        """Test admin can approve pending users."""
        users = {
            1: User(1, 'admin', generate_password_hash('Admin123!'), True),
            2: User(2, 'testuser', generate_password_hash('testpass'), False)
        }
        
        with patch('app.USERS', users):
            self.login_as_admin(client)
            
            response = client.get('/admin/users/2/approve', follow_redirects=True)
            assert response.status_code == 200
            assert 'אושר בהצלחה' in response.data.decode('utf-8')
    
    def test_admin_delete_user(self, client):
        """Test admin can delete users."""
        users = {
            1: User(1, 'admin', generate_password_hash('Admin123!'), True),
            2: User(2, 'testuser', generate_password_hash('testpass'), True)
        }
        
        with patch('app.USERS', users):
            self.login_as_admin(client)
            
            response = client.get('/admin/users/2/delete', follow_redirects=True)
            assert response.status_code == 200
            assert 'נמחק בהצלחה' in response.data.decode('utf-8')
    
    def test_admin_cannot_delete_self(self, client):
        """Test admin cannot delete their own account."""
        self.login_as_admin(client)
        
        response = client.get('/admin/users/1/delete', follow_redirects=True)
        assert response.status_code == 200
        assert 'לא ניתן למחוק את חשבון המנהל הראשי' in response.data.decode('utf-8')
    
    def test_invalid_user_action(self, client):
        """Test invalid user actions are handled."""
        self.login_as_admin(client)
        
        response = client.get('/admin/users/999/approve', follow_redirects=True)
        assert response.status_code == 200
        assert 'משתמש לא נמצא' in response.data.decode('utf-8')
    
    def test_invalid_action_type(self, client):
        """Test invalid action types are handled."""
        self.login_as_admin(client)
        
        response = client.get('/admin/users/1/invalid_action', follow_redirects=True)
        assert response.status_code == 200
        assert 'פעולה לא חוקית' in response.data.decode('utf-8')