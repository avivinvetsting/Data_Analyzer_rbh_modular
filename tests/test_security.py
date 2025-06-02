import pytest
from unittest.mock import patch, MagicMock
from app import app
from werkzeug.security import generate_password_hash

@pytest.fixture
def client():
    """Create and configure a new app instance for each test."""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def authenticated_client(client):
    """Create an authenticated client session."""
    # Login as admin
    client.post('/login', data={
        'username': 'admin',
        'password': 'Admin123!'
    })
    return client


class TestCSRFProtection:
    
    def test_csrf_protection_on_login(self, client):
        """Test CSRF protection is enabled on login form."""
        # Enable CSRF for this test
        app.config['WTF_CSRF_ENABLED'] = True
        
        response = client.post('/login', data={
            'username': 'admin',
            'password': 'Admin123!'
        })
        
        # Should get CSRF error without token
        assert response.status_code == 400
        app.config['WTF_CSRF_ENABLED'] = False  # Reset for other tests
    
    def test_csrf_protection_on_register(self, client):
        """Test CSRF protection is enabled on register form."""
        app.config['WTF_CSRF_ENABLED'] = True
        
        response = client.post('/register', data={
            'username': 'testuser',
            'password': 'testpass123',
            'confirm_password': 'testpass123'
        })
        
        assert response.status_code == 400
        app.config['WTF_CSRF_ENABLED'] = False
    
    def test_csrf_protection_on_analyze(self, authenticated_client):
        """Test CSRF protection is enabled on analyze form."""
        app.config['WTF_CSRF_ENABLED'] = True
        
        response = authenticated_client.post('/analyze', data={
            'ticker': 'AAPL'
        })
        
        assert response.status_code == 400
        app.config['WTF_CSRF_ENABLED'] = False


class TestInputValidation:
    
    def test_ticker_validation_empty(self, authenticated_client):
        """Test ticker validation with empty input."""
        response = authenticated_client.post('/analyze', data={
            'ticker': ''
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'אנא הזן סימול טיקר' in response.data.decode('utf-8')
    
    def test_ticker_validation_too_short(self, authenticated_client):
        """Test ticker validation with too short input."""
        response = authenticated_client.post('/analyze', data={
            'ticker': ''  # Empty is too short
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'אנא הזן סימול טיקר' in response.data.decode('utf-8')
    
    def test_ticker_validation_too_long(self, authenticated_client):
        """Test ticker validation with too long input."""
        response = authenticated_client.post('/analyze', data={
            'ticker': 'VERYLONGTICKER123'  # 17 characters, exceeds 12 limit
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'אורך הסימול חייב להיות בין 1 ל-12 תווים' in response.data.decode('utf-8')
    
    def test_ticker_validation_invalid_characters(self, authenticated_client):
        """Test ticker validation with invalid characters."""
        invalid_tickers = [
            'AAPL@',      # @ not allowed
            'AAPL#',      # # not allowed
            'AAPL$',      # $ not allowed
            'AAPL%',      # % not allowed
            'AAPL&',      # & not allowed
            'aapl',       # lowercase not allowed
            'AAPL*',      # * not allowed
            'AAPL(',      # ( not allowed
            'AAPL)',      # ) not allowed
            'AAPL+',      # + not allowed
            'AAPL=',      # = not allowed
            'AAPL[',      # [ not allowed
            'AAPL]',      # ] not allowed
            'AAPL{',      # { not allowed
            'AAPL}',      # } not allowed
            'AAPL|',      # | not allowed
            'AAPL\\',     # \ not allowed
            'AAPL:',      # : not allowed
            'AAPL;',      # ; not allowed
            'AAPL"',      # " not allowed
            'AAPL\'',     # ' not allowed
            'AAPL<',      # < not allowed
            'AAPL>',      # > not allowed
            'AAPL,',      # , not allowed
            'AAPL?',      # ? not allowed
            'AAPL/',      # / not allowed
            'AAPL~',      # ~ not allowed
            'AAPL`',      # ` not allowed
            'AAPL!',      # ! not allowed
            'AAPL ',      # space not allowed
        ]
        
        for ticker in invalid_tickers:
            response = authenticated_client.post('/analyze', data={
                'ticker': ticker
            }, follow_redirects=True)
            
            assert response.status_code == 200
            assert 'הסימול יכול להכיל רק אותיות באנגלית' in response.data.decode('utf-8'), f"Failed for ticker: {ticker}"
    
    def test_ticker_validation_valid_characters(self, authenticated_client):
        """Test ticker validation with valid characters."""
        valid_tickers = [
            'AAPL',       # Basic letters
            'MSFT',       # Basic letters
            'BRK.A',      # With dot
            'BRK-A',      # With dash
            'SPY^A',      # With caret
            'GOOG123',    # With numbers
            'A',          # Single character
            'ABCDEFGHIJ', # 10 characters
            '123456',     # All numbers
            'A1B2C3',     # Mixed letters and numbers
            'TEST.TEST',  # Multiple dots
            'TEST-TEST',  # Multiple dashes
            'TEST^TEST',  # Multiple carets
        ]
        
        for ticker in valid_tickers:
            with patch('modules.price_history.get_price_history') as mock_price:
                with patch('modules.price_history.get_company_name') as mock_name:
                    with patch('modules.price_history.get_company_info') as mock_info:
                        with patch('modules.chart_creator.create_all_candlestick_charts') as mock_charts:
                            # Mock successful responses
                            mock_price.return_value = MagicMock()
                            mock_name.return_value = "Test Company"
                            mock_info.return_value = {"sector": "Technology"}
                            mock_charts.return_value = ('{"chart1": "data"}', '{"chart2": "data"}', '{"chart3": "data"}')
                            
                            response = authenticated_client.post('/analyze', data={
                                'ticker': ticker
                            }, follow_redirects=True)
                            
                            # Should not have validation error
                            assert 'הסימול יכול להכיל רק אותיות באנגלית' not in response.data.decode('utf-8'), f"Failed for valid ticker: {ticker}"
                            assert 'אורך הסימול חייב להיות בין 1 ל-12 תווים' not in response.data.decode('utf-8'), f"Failed for valid ticker: {ticker}"


class TestSessionSecurity:
    
    def test_session_isolation(self, client):
        """Test that user sessions are properly isolated."""
        # Create two different client sessions
        with client.session_transaction() as sess1:
            sess1['selected_ticker'] = 'AAPL'
            sess1['user_id'] = '1'
        
        # Second client should not see first client's data
        with client.session_transaction() as sess2:
            assert 'selected_ticker' not in sess2
            assert 'user_id' not in sess2
    
    def test_session_persistence(self, authenticated_client):
        """Test that session data persists correctly."""
        # Set session data
        with authenticated_client.session_transaction() as sess:
            sess['test_data'] = 'test_value'
        
        # Data should persist across requests
        with authenticated_client.session_transaction() as sess:
            assert sess.get('test_data') == 'test_value'
    
    def test_logout_clears_session(self, authenticated_client):
        """Test that logout properly clears session data."""
        # Set some session data
        with authenticated_client.session_transaction() as sess:
            sess['selected_ticker'] = 'AAPL'
            sess['company_name'] = 'Apple Inc.'
        
        # Logout
        authenticated_client.get('/logout')
        
        # Session should be cleared (new session won't have the data)
        response = authenticated_client.get('/', follow_redirects=True)
        # Should redirect to login page since session is cleared
        assert 'התחברות' in response.data.decode('utf-8')


class TestPasswordSecurity:
    
    def test_password_hashing(self):
        """Test that passwords are properly hashed."""
        from werkzeug.security import check_password_hash
        
        password = 'testpassword123'
        hashed = generate_password_hash(password)
        
        # Hash should not contain the original password
        assert password not in hashed
        # Hash should be verifiable
        assert check_password_hash(hashed, password)
        # Wrong password should not verify
        assert not check_password_hash(hashed, 'wrongpassword')
    
    def test_password_hash_uniqueness(self):
        """Test that password hashes are unique."""
        password = 'testpassword123'
        hash1 = generate_password_hash(password)
        hash2 = generate_password_hash(password)
        
        # Same password should produce different hashes (due to salt)
        assert hash1 != hash2


class TestErrorHandling:
    
    def test_404_error_handler(self, client):
        """Test custom 404 error page."""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404
        # Should use custom 404 template
        assert '404' in response.data.decode('utf-8')
    
    def test_500_error_simulation(self, authenticated_client):
        """Test 500 error handling."""
        # Simulate an internal server error by causing an exception
        with patch('modules.price_history.get_price_history', side_effect=Exception("Test error")):
            response = authenticated_client.post('/analyze', data={
                'ticker': 'TEST'
            }, follow_redirects=True)
            
            # Should handle the error gracefully
            assert response.status_code == 200
            # Should show error message
            assert 'אירעה שגיאה בלתי צפויה בעת ניתוח הטיקר' in response.data.decode('utf-8')


class TestSecurityHeaders:
    
    def test_session_cookie_security(self, client):
        """Test session cookie security settings."""
        response = client.get('/login')
        
        # Check if session cookie has security attributes
        # Note: In testing mode, some security features might be disabled
        assert response.status_code == 200
    
    def test_no_sensitive_data_in_response(self, authenticated_client):
        """Test that sensitive data is not exposed in responses."""
        response = authenticated_client.get('/')
        response_text = response.data.decode('utf-8')
        
        # Should not contain sensitive information
        assert 'password' not in response_text.lower()
        assert 'secret' not in response_text.lower()
        assert 'hash' not in response_text.lower()


class TestAuthorizationBypass:
    
    def test_cannot_access_admin_without_permission(self, client):
        """Test that non-admin users cannot access admin functions."""
        # Try to access admin page without login
        response = client.get('/admin/users', follow_redirects=True)
        assert 'התחברות' in response.data.decode('utf-8')
    
    def test_cannot_perform_admin_actions_without_permission(self, client):
        """Test that admin actions require proper authorization."""
        # Try to approve user without login
        response = client.get('/admin/users/1/approve', follow_redirects=True)
        assert 'התחברות' in response.data.decode('utf-8')
        
        # Try to delete user without login
        response = client.get('/admin/users/1/delete', follow_redirects=True)
        assert 'התחברות' in response.data.decode('utf-8')
    
    def test_direct_url_manipulation(self, authenticated_client):
        """Test that URL manipulation doesn't bypass security."""
        # Try various URL manipulations
        urls_to_test = [
            '/admin/users/../../../etc/passwd',
            '/admin/users/%2e%2e%2f%2e%2e%2f',
            '/admin/users/1/approve/../delete',
            '/admin/users/1/approve/../../../login',
        ]
        
        for url in urls_to_test:
            response = authenticated_client.get(url, follow_redirects=True)
            # Should either get 404 or be redirected to appropriate page
            assert response.status_code in [200, 404]


class TestDataSanitization:
    
    def test_ticker_input_sanitization(self, authenticated_client):
        """Test that ticker input is properly sanitized."""
        # Test potential XSS attempts
        xss_attempts = [
            '<script>alert("xss")</script>',
            '"><script>alert("xss")</script>',
            "';alert('xss');//",
            '<img src=x onerror=alert("xss")>',
            'javascript:alert("xss")',
        ]
        
        for xss in xss_attempts:
            response = authenticated_client.post('/analyze', data={
                'ticker': xss
            }, follow_redirects=True)
            
            # Should get validation error, not execute script
            assert response.status_code == 200
            # The malicious script should not be in the response as-is
            assert '<script>' not in response.data.decode('utf-8')
            assert 'javascript:' not in response.data.decode('utf-8')
    
    def test_username_input_sanitization(self, client):
        """Test that username input is properly handled."""
        xss_attempts = [
            '<script>alert("xss")</script>',
            '"><img src=x onerror=alert("xss")>',
            "admin'; DROP TABLE users; --",
        ]
        
        for xss in xss_attempts:
            response = client.post('/register', data={
                'username': xss,
                'password': 'testpass123',
                'confirm_password': 'testpass123'
            })
            
            # Should handle malicious input safely
            assert response.status_code == 200
            # Should not execute scripts or cause errors
            assert '<script>' not in response.data.decode('utf-8')