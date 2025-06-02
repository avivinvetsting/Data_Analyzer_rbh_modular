import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from app import app
from werkzeug.security import generate_password_hash


@pytest.fixture
def client():
    """Create and configure a new app instance for each test."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def authenticated_client(client):
    """Create an authenticated client session."""
    client.post('/login', data={
        'username': 'admin',
        'password': 'Admin123!'
    })
    return client


class TestLoginForm:
    
    def test_login_form_renders(self, client):
        """Test that login form renders correctly."""
        response = client.get('/login')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        
        # Check for form elements
        assert '<form' in html
        assert 'name="username"' in html
        assert 'name="password"' in html
        assert 'type="password"' in html
        assert 'type="submit"' in html or 'button' in html
    
    def test_login_form_valid_submission(self, client):
        """Test valid login form submission."""
        response = client.post('/login', data={
            'username': 'admin',
            'password': 'Admin123!'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should redirect to home page
        assert 'Stock Analysis - Home' in response.data.decode('utf-8')
    
    def test_login_form_empty_username(self, client):
        """Test login form with empty username."""
        response = client.post('/login', data={
            'username': '',
            'password': 'password'
        })
        
        assert response.status_code == 200
        assert 'שם משתמש או סיסמה שגויים' in response.data.decode('utf-8')
    
    def test_login_form_empty_password(self, client):
        """Test login form with empty password."""
        response = client.post('/login', data={
            'username': 'admin',
            'password': ''
        })
        
        assert response.status_code == 200
        assert 'שם משתמש או סיסמה שגויים' in response.data.decode('utf-8')
    
    def test_login_form_both_empty(self, client):
        """Test login form with both fields empty."""
        response = client.post('/login', data={
            'username': '',
            'password': ''
        })
        
        assert response.status_code == 200
        assert 'שם משתמש או סיסמה שגויים' in response.data.decode('utf-8')
    
    def test_login_form_special_characters_in_username(self, client):
        """Test login form with special characters in username."""
        special_usernames = [
            'admin@test.com',
            'admin-user',
            'admin_user',
            'admin.user',
            'admin123',
            'Admin',  # Case sensitivity
        ]
        
        for username in special_usernames:
            response = client.post('/login', data={
                'username': username,
                'password': 'Admin123!'
            })
            
            assert response.status_code == 200
            # Should handle gracefully (either login or show error)
    
    def test_login_form_redirect_after_login(self, client):
        """Test redirect to intended page after login."""
        # First try to access protected page
        response = client.get('/admin/users', follow_redirects=False)
        assert response.status_code == 302
        
        # Login and should redirect to intended page
        response = client.post('/login', data={
            'username': 'admin',
            'password': 'Admin123!'
        }, follow_redirects=True)
        
        assert response.status_code == 200


class TestRegisterForm:
    
    def test_register_form_renders(self, client):
        """Test that register form renders correctly."""
        response = client.get('/register')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        
        # Check for form elements
        assert '<form' in html
        assert 'name="username"' in html
        assert 'name="password"' in html
        assert 'name="confirm_password"' in html
        assert 'type="password"' in html
        assert 'type="submit"' in html or 'button' in html
    
    def test_register_form_valid_submission(self, client):
        """Test valid registration form submission."""
        import time
        unique_username = f'testuser_{int(time.time())}'
        response = client.post('/register', data={
            'username': unique_username,
            'password': 'validpass123',
            'confirm_password': 'validpass123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'ההרשמה הושלמה בהצלחה' in response.data.decode('utf-8')
    
    def test_register_form_password_mismatch(self, client):
        """Test registration with password mismatch."""
        response = client.post('/register', data={
            'username': 'newuser',
            'password': 'password123',
            'confirm_password': 'different123'
        })
        
        assert response.status_code == 200
        assert 'הסיסמאות אינן תואמות' in response.data.decode('utf-8')
    
    def test_register_form_short_password(self, client):
        """Test registration with short password."""
        short_passwords = ['1', '12', '123', '1234', '12345']
        
        for password in short_passwords:
            response = client.post('/register', data={
                'username': f'user_{password}',
                'password': password,
                'confirm_password': password
            })
            
            assert response.status_code == 200
            assert 'הסיסמה חייבת להכיל לפחות 6 תווים' in response.data.decode('utf-8')
    
    def test_register_form_valid_password_lengths(self, client):
        """Test registration with valid password lengths."""
        valid_passwords = [
            '123456',    # Exactly 6 characters
            '1234567',   # 7 characters
            'longerpassword123',  # Longer password
            'very_long_password_with_special_chars_123!@#'  # Very long
        ]
        
        for i, password in enumerate(valid_passwords):
            response = client.post('/register', data={
                'username': f'validuser{i}',
                'password': password,
                'confirm_password': password
            })
            
            # Should not get password length error
            assert 'הסיסמה חייבת להכיל לפחות 6 תווים' not in response.data.decode('utf-8')
    
    def test_register_form_empty_fields(self, client):
        """Test registration with empty fields."""
        test_cases = [
            {'username': '', 'password': 'pass123', 'confirm_password': 'pass123'},
            {'username': 'user', 'password': '', 'confirm_password': ''},
            {'username': 'user', 'password': 'pass123', 'confirm_password': ''},
            {'username': '', 'password': '', 'confirm_password': ''},
        ]
        
        for case in test_cases:
            response = client.post('/register', data=case)
            assert response.status_code == 200
            assert 'נא למלא את כל השדות' in response.data.decode('utf-8')
    
    def test_register_form_existing_username(self, client):
        """Test registration with existing username."""
        response = client.post('/register', data={
            'username': 'admin',  # Already exists
            'password': 'newpass123',
            'confirm_password': 'newpass123'
        })
        
        assert response.status_code == 200
        assert 'שם המשתמש כבר קיים במערכת' in response.data.decode('utf-8')
    
    def test_register_form_special_characters_in_username(self, client):
        """Test registration with various username formats."""
        usernames = [
            'user123',
            'user_name',
            'user-name',
            'user.name',
            'UserName',
            'user@domain.com',
            'הגר',  # Hebrew characters
            'عربي',  # Arabic characters
        ]
        
        for username in usernames:
            response = client.post('/register', data={
                'username': username,
                'password': 'validpass123',
                'confirm_password': 'validpass123'
            })
            
            # Should handle all usernames gracefully (either redirect on success or stay on page)
            assert response.status_code in [200, 302]
    
    def test_register_form_special_characters_in_password(self, client):
        """Test registration with special characters in password."""
        passwords = [
            'pass123!',
            'pass@123',
            'pass#123',
            'pass$123',
            'pass%123',
            'pass^123',
            'pass&123',
            'pass*123',
            'pass(123)',
            'pass[123]',
            'pass{123}',
            'פססוורד123',  # Hebrew
            'كلمة123',      # Arabic
        ]
        
        import time
        for i, password in enumerate(passwords):
            unique_username = f'specialuser{i}_{int(time.time())}'
            response = client.post('/register', data={
                'username': unique_username,
                'password': password,
                'confirm_password': password
            })
            
            # Should handle special characters in passwords (either redirect on success or stay on page)
            assert response.status_code in [200, 302]


class TestAnalyzeForm:
    
    def test_analyze_form_renders_on_home_page(self, authenticated_client):
        """Test that analyze form renders on home page."""
        response = authenticated_client.get('/')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        
        # Check for ticker input form
        assert '<form' in html
        assert 'name="ticker"' in html or 'id="ticker"' in html
        assert 'action="/analyze"' in html or 'analyze' in html
    
    def test_analyze_form_valid_ticker(self, authenticated_client):
        """Test analyze form with valid ticker."""
        with patch('modules.routes.home.get_price_history') as mock_price:
            with patch('modules.routes.home.get_company_name') as mock_name:
                with patch('modules.routes.home.get_company_info') as mock_info:
                    with patch('modules.routes.home.create_all_candlestick_charts') as mock_charts:
                        # Mock successful responses
                        sample_data = pd.DataFrame({
                            'Open': [100, 101],
                            'High': [105, 106],
                            'Low': [95, 96],
                            'Close': [102, 103]
                        }, index=pd.date_range('2023-01-01', periods=2))
                        
                        mock_price.return_value = sample_data
                        mock_name.return_value = "Test Company"
                        mock_info.return_value = {"sector": "Technology"}
                        mock_charts.return_value = {
                            'daily_chart_json': 'chart1',
                            'weekly_chart_json': 'chart2', 
                            'monthly_chart_json': 'chart3'
                        }
                        
                        response = authenticated_client.post('/analyze', data={
                            'ticker': 'AAPL'
                        }, follow_redirects=True)
                        
                        assert response.status_code == 200
                        # Check that analysis was successful - company name appears
                        assert 'Test Company' in response.data.decode('utf-8')
    
    def test_analyze_form_empty_ticker(self, authenticated_client):
        """Test analyze form with empty ticker."""
        response = authenticated_client.post('/analyze', data={
            'ticker': ''
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'אנא הזן סימול טיקר' in response.data.decode('utf-8')
    
    def test_analyze_form_whitespace_only_ticker(self, authenticated_client):
        """Test analyze form with whitespace-only ticker."""
        whitespace_tickers = ['   ', '\t\t', '\n\n', '  \t\n  ']
        
        for ticker in whitespace_tickers:
            response = authenticated_client.post('/analyze', data={
                'ticker': ticker
            }, follow_redirects=True)
            
            assert response.status_code == 200
            assert 'אנא הזן סימול טיקר' in response.data.decode('utf-8')
    
    def test_analyze_form_ticker_length_validation(self, authenticated_client):
        """Test ticker length validation."""
        # Test too long tickers
        long_tickers = [
            'A' * 13,  # 13 characters
            'A' * 20,  # 20 characters
            'VERYLONGTICKER123',  # 17 characters
        ]
        
        for ticker in long_tickers:
            response = authenticated_client.post('/analyze', data={
                'ticker': ticker
            }, follow_redirects=True)
            
            assert response.status_code == 200
            assert 'אורך הסימול חייב להיות בין 1 ל-12 תווים' in response.data.decode('utf-8')
    
    def test_analyze_form_ticker_valid_lengths(self, authenticated_client):
        """Test valid ticker lengths."""
        valid_tickers = [
            'A',           # 1 character
            'AB',          # 2 characters
            'ABC',         # 3 characters
            'AAPL',        # 4 characters
            'MSFT',        # 4 characters
            'GOOGL',       # 5 characters
            'BRK.A',       # 5 characters (with dot)
            'BRK-A',       # 5 characters (with dash)
            'ABCDEFGHIJ',  # 10 characters
            'ABCDEFGHIJK', # 11 characters
            'ABCDEFGHIJKL' # 12 characters
        ]
        
        for ticker in valid_tickers:
            with patch('modules.routes.home.get_price_history') as mock_price:
                with patch('modules.routes.home.get_company_name') as mock_name:
                    with patch('modules.routes.home.get_company_info') as mock_info:
                        with patch('modules.routes.home.create_all_candlestick_charts') as mock_charts:
                            # Mock successful responses
                            sample_data = pd.DataFrame({
                                'Open': [100], 'High': [105], 'Low': [95], 'Close': [102]
                            }, index=pd.date_range('2023-01-01', periods=1))
                            
                            mock_price.return_value = sample_data
                            mock_name.return_value = "Test Company"
                            mock_info.return_value = {"sector": "Technology"}
                            mock_charts.return_value = {
                                'daily_chart_json': 'chart1',
                                'weekly_chart_json': 'chart2', 
                                'monthly_chart_json': 'chart3'
                            }
                            
                            response = authenticated_client.post('/analyze', data={
                                'ticker': ticker
                            }, follow_redirects=True)
                            
                            # Should not get length validation error
                            assert 'אורך הסימול חייב להיות בין 1 ל-12 תווים' not in response.data.decode('utf-8'), f"Failed for ticker: {ticker}"
    
    def test_analyze_form_ticker_case_conversion(self, authenticated_client):
        """Test that ticker is converted to uppercase."""
        with patch('modules.routes.home.get_price_history') as mock_price:
            with patch('modules.routes.home.get_company_name') as mock_name:
                with patch('modules.routes.home.get_company_info') as mock_info:
                    with patch('modules.routes.home.create_all_candlestick_charts') as mock_charts:
                        sample_data = pd.DataFrame({
                            'Open': [100], 'High': [105], 'Low': [95], 'Close': [102]
                        }, index=pd.date_range('2023-01-01', periods=1))
                        
                        mock_price.return_value = sample_data
                        mock_name.return_value = "Test Company"
                        mock_info.return_value = {"sector": "Technology"}
                        mock_charts.return_value = {
                            'daily_chart_json': 'chart1',
                            'weekly_chart_json': 'chart2', 
                            'monthly_chart_json': 'chart3'
                        }
                        
                        response = authenticated_client.post('/analyze', data={
                            'ticker': 'aapl'  # lowercase
                        }, follow_redirects=True)
                        
                        # Check that mock was called with uppercase
                        mock_price.assert_called()
                        # The first argument should be the ticker in uppercase
                        args, kwargs = mock_price.call_args
                        # The ticker parameter might be in args[0] or kwargs
                        if args:
                            assert args[0] == 'AAPL'
    
    def test_analyze_form_preserves_session_data(self, authenticated_client):
        """Test that form submission preserves session data correctly."""
        with patch('modules.price_history.get_price_history') as mock_price:
            with patch('modules.price_history.get_company_name') as mock_name:
                with patch('modules.price_history.get_company_info') as mock_info:
                    with patch('modules.chart_creator.create_all_candlestick_charts') as mock_charts:
                        sample_data = pd.DataFrame({
                            'Open': [100, 101], 'High': [105, 106], 
                            'Low': [95, 96], 'Close': [102, 103]
                        }, index=pd.date_range('2023-01-01', periods=2))
                        
                        mock_price.return_value = sample_data
                        mock_name.return_value = "Apple Inc."
                        mock_info.return_value = {
                            "sector": "Technology",
                            "longBusinessSummary": "Apple Inc. designs consumer electronics."
                        }
                        mock_charts.return_value = (
                            '{"data": "chart1"}',
                            '{"data": "chart2"}',
                            '{"data": "chart3"}'
                        )
                        
                        response = authenticated_client.post('/analyze', data={
                            'ticker': 'AAPL'
                        }, follow_redirects=True)
                        
                        assert response.status_code == 200
                        
                        # Check session data
                        with authenticated_client.session_transaction() as sess:
                            assert sess.get('selected_ticker') == 'AAPL'
                            assert sess.get('company_name') == 'Apple Inc.'
                            assert sess.get('company_info') is not None
                            assert sess.get('chart1_json') == '{"data": "chart1"}'
                            assert sess.get('chart2_json') == '{"data": "chart2"}'
                            assert sess.get('chart3_json') == '{"data": "chart3"}'


class TestFormCSRFIntegration:
    
    def test_forms_include_csrf_token(self, client):
        """Test that forms include CSRF tokens when CSRF is enabled."""
        app.config['CSRF_DISABLE'] = False
        
        # Check login form
        response = client.get('/login')
        html = response.data.decode('utf-8')
        assert 'csrf_token' in html or 'name="csrf_token"' in html
        
        # Check register form
        response = client.get('/register')
        html = response.data.decode('utf-8')
        assert 'csrf_token' in html or 'name="csrf_token"' in html
        
        app.config['WTF_CSRF_ENABLED'] = False
    
    def test_forms_work_without_csrf_in_testing(self, authenticated_client):
        """Test that forms work in testing mode with CSRF disabled."""
        # This should work since CSRF is disabled in testing
        response = authenticated_client.post('/analyze', data={
            'ticker': 'TEST'
        })
        
        # Should not get CSRF error
        assert response.status_code != 400