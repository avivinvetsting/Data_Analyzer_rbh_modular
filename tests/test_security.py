# tests/test_security.py
import pytest
from unittest.mock import patch
from flask import session, current_app, url_for, request # הוספנו request
import pandas as pd
import json
import html as html_mod
import re

from app import User, generate_password_hash, USERS_FILE, save_users, load_users, ADMIN_USERNAME
# from modules.routes.home import TICKER_MIN_LENGTH, TICKER_MAX_LENGTH # אם רוצים להשתמש בקבועים ישירות

@pytest.fixture
def app_with_temp_users_for_security(app, tmp_path): # שם ייחודי ל-fixture
    original_users_file_in_app_module = app.config.get('_ORIGINAL_USERS_FILE_FOR_TEST_SECURITY', None)
    import app as main_app_module
    if original_users_file_in_app_module is None:
        original_users_file_in_app_module = main_app_module.USERS_FILE
        app.config['_ORIGINAL_USERS_FILE_FOR_TEST_SECURITY'] = original_users_file_in_app_module
    
    temp_file = tmp_path / "temp_security_users.json"
    admin_hashed_password = generate_password_hash('Admin123!')
    regular_user_password_hash = generate_password_hash('password123')
    
    initial_users_data = {
        "1": {"username": ADMIN_USERNAME, "password_hash": admin_hashed_password, "is_approved": True},
        "100": {"username": "normaluser", "password_hash": regular_user_password_hash, "is_approved": True}
    }
    with open(temp_file, 'w') as f:
        json.dump(initial_users_data, f)
    
    with patch('app.USERS_FILE', str(temp_file)):
        main_app_module.USERS = main_app_module.load_users()
        yield app

# Helper to extract CSRF token from HTML
def extract_csrf_token(html):
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    if not match:
        raise Exception("CSRF token not found in form")
    return match.group(1)

class TestCSRFProtection:
    # בדיקות אלו מניחות ש-CSRF מופעל כברירת מחדל (כלומר, לא ביטלנו אותו ב-conftest.py)
    # או שהן מפעילות אותו מחדש. אם WTF_CSRF_ENABLED = False ב-conftest, בדיקות אלו ייכשלו.

    def test_csrf_protection_on_login(self, client, app):
        app.config['WTF_CSRF_ENABLED'] = True
        response = client.get(url_for('login'))
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert 'csrf_token' in html
        csrf_token = extract_csrf_token(html)
        # POST ללא טוקן
        response_post = client.post(url_for('login'), data={'username': 'a', 'password': 'b'})
        assert response_post.status_code == 400
        assert b"Reason: The CSRF token is missing." in response_post.data
        # POST עם טוקן
        response_post_valid = client.post(url_for('login'), data={
            'username': 'a',
            'password': 'b',
            'csrf_token': csrf_token
        })
        assert response_post_valid.status_code in (200, 302)
        app.config['WTF_CSRF_ENABLED'] = False

    def test_csrf_protection_on_register(self, client, app):
        app.config['WTF_CSRF_ENABLED'] = True
        response = client.get(url_for('register'))
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert 'csrf_token' in html
        csrf_token = extract_csrf_token(html)
        # POST ללא טוקן
        response_post = client.post(url_for('register'), data={'username': 'a', 'password': 'b', 'confirm_password': 'c'})
        assert response_post.status_code == 400
        assert b"Reason: The CSRF token is missing." in response_post.data
        # POST עם טוקן
        response_post_valid = client.post(url_for('register'), data={
            'username': 'a',
            'password': 'b',
            'confirm_password': 'c',
            'csrf_token': csrf_token
        })
        assert response_post_valid.status_code in (200, 400)  # 400 אם יש ולידציה, 200 אם עובר
        app.config['WTF_CSRF_ENABLED'] = False

    def test_csrf_protection_on_analyze(self, authenticated_client, app):
        app.config['WTF_CSRF_ENABLED'] = True
        home_response = authenticated_client.get(url_for('home_bp.index'))
        assert home_response.status_code == 200
        html = home_response.data.decode('utf-8')
        assert 'csrf_token' in html
        csrf_token = extract_csrf_token(html)
        # POST ללא טוקן
        response_post = authenticated_client.post('/analyze', data={'ticker': 'AAPL'})
        assert response_post.status_code == 400
        assert b"Reason: The CSRF token is missing." in response_post.data
        # POST עם טוקן
        response_post_valid = authenticated_client.post('/analyze', data={'ticker': 'AAPL', 'csrf_token': csrf_token})
        assert response_post_valid.status_code in (200, 400)  # 400 אם יש ולידציה, 200 אם עובר
        app.config['WTF_CSRF_ENABLED'] = False


class TestInputValidation:

    def test_ticker_validation_empty(self, authenticated_client):
        home_response = authenticated_client.get(url_for('home_bp.index'))
        html = home_response.data.decode('utf-8')
        csrf_token = extract_csrf_token(html)
        response = authenticated_client.post('/analyze', data={'ticker': '', 'csrf_token': csrf_token}, follow_redirects=True)
        assert response.status_code == 200
        assert 'אנא הזן סימול טיקר.' in response.data.decode('utf-8')

    def test_ticker_validation_too_long(self, authenticated_client):
        home_response = authenticated_client.get(url_for('home_bp.index'))
        html = home_response.data.decode('utf-8')
        csrf_token = extract_csrf_token(html)
        long_ticker = "A" * 13 
        response = authenticated_client.post('/analyze', data={'ticker': long_ticker, 'csrf_token': csrf_token}, follow_redirects=True)
        assert response.status_code == 200
        assert 'אורך הסימול חייב להיות בין 1 ל-12 תווים.' in response.data.decode('utf-8')

    def test_ticker_validation_invalid_characters(self, authenticated_client):
        home_response = authenticated_client.get(url_for('home_bp.index'))
        html = home_response.data.decode('utf-8')
        csrf_token = extract_csrf_token(html)
        invalid_tickers = [
            'AAPL@', 'AAPL#', 'AAPL$', 'AAPL%', 'AAPL&', 'AAPL*', 'AAPL(', 'AAPL)', 
            'AAPL+', 'AAPL=', 'AAPL[', 'AAPL]', 'AAPL{', 'AAPL}', 'AAPL|', 
            'AAPL\\', 'AAPL:', 'AAPL;', 'AAPL"', 'AAPL\'', 'AAPL<', 'AAPL>', 
            'AAPL,', 'AAPL?', 'AAPL/', 'AAPL~', 'AAPL`', 'AAPL!',
        ]
        expected_message = 'הסימול יכול להכיל רק אותיות באנגלית, ספרות, נקודה (.), מקף (-), או גג (^).'
        for ticker in invalid_tickers:
            with patch('modules.routes.home.get_price_history', side_effect=Exception("Should not reach here for invalid ticker")):
                response = authenticated_client.post('/analyze', data={'ticker': ticker, 'csrf_token': csrf_token}, follow_redirects=True)
            assert response.status_code == 200 
            assert expected_message in response.data.decode('utf-8'), f"Failed for ticker: {ticker}"
        response_space = authenticated_client.post('/analyze', data={'ticker': '   ', 'csrf_token': csrf_token}, follow_redirects=True)
        assert 'אנא הזן סימול טיקר.' in response_space.data.decode('utf-8')
        with patch('modules.routes.home.get_price_history', return_value=pd.DataFrame({'Close': [100]})) as mock_price_aapl, \
             patch('modules.routes.home.get_company_name', return_value="APPLE INC") as mock_name_aapl, \
             patch('modules.routes.home.get_company_info', return_value={"sector":"Tech"}) as mock_info_aapl, \
             patch('modules.routes.home.create_all_candlestick_charts', return_value={'daily_chart_json': 'mock_aapl_chart'}) as mock_charts_aapl:
            response_aapl = authenticated_client.post('/analyze', data={'ticker': 'aapl', 'csrf_token': csrf_token}, follow_redirects=True)
            assert response_aapl.status_code == 200
            assert expected_message not in response_aapl.data.decode('utf-8')
            assert 'mock_aapl_chart' in response_aapl.data.decode('utf-8')

    def test_ticker_validation_valid_characters(self, authenticated_client):
        home_response = authenticated_client.get(url_for('home_bp.index'))
        html = home_response.data.decode('utf-8')
        csrf_token = extract_csrf_token(html)
        valid_tickers = ['AAPL', 'MSFT', 'GOOGL', 'BRK.B', 'BF-B', '000001.SZ', '^GSPC', 'TSLA123']
        with patch('modules.routes.home.get_price_history', return_value=pd.DataFrame({'Close': [100]})), \
             patch('modules.routes.home.get_company_name', side_effect=lambda x: x.upper()), \
             patch('modules.routes.home.get_company_info', return_value={"sector":"Tech"}), \
             patch('modules.routes.home.create_all_candlestick_charts', return_value={'daily_chart_json': 'mock_chart_json_string'}):
            for ticker in valid_tickers:
                response = authenticated_client.post('/analyze', data={'ticker': ticker, 'csrf_token': csrf_token}, follow_redirects=True)
                assert response.status_code == 200
                response_html = response.data.decode('utf-8')
                assert 'הסימול יכול להכיל רק אותיות באנגלית' not in response_html
                assert 'אנא הזן סימול טיקר' not in response_html
                assert 'אורך הסימול חייב להיות בין' not in response_html
                assert ticker.upper() in response_html


class TestSessionSecurity:
    def test_session_cookie_attributes(self, client):
        response = client.get('/') 
        cookie_header = response.headers.get('Set-Cookie')
        if cookie_header: # Cookie יוגדר רק אם נכתב משהו לסשן
            assert 'HttpOnly' in cookie_header
            assert 'SameSite=Lax' in cookie_header

    @pytest.mark.skip(reason="Session isolation test needs review for multiple client handling or alternative setup")
    def test_session_isolation(self, app):
        # יצירת שני משתמשים לבדיקה
        users_dict = {
            1: User(1, 'admin_sec_test', generate_password_hash('Admin123!'), True),
            2: User(2, 'user1_sec_test', generate_password_hash('pass1'), True),
            3: User(3, 'user2_sec_test', generate_password_hash('pass2'), True),
        }

        # שמירת המשתמשים המקוריים ושחזורם בסוף
        import app as main_app
        original_users = main_app.USERS
        main_app.USERS = users_dict

        try:
            with app.test_client() as client1, app.test_client() as client2:
                # קבלת CSRF token עבור כל לקוח
                response1 = client1.get('/login')
                csrf_token1 = extract_csrf_token(response1.data.decode('utf-8'))
                
                response2 = client2.get('/login')
                csrf_token2 = extract_csrf_token(response2.data.decode('utf-8'))

                # התחברות עם CSRF token
                client1.post('/login', data={
                    'username': 'user1_sec_test',
                    'password': 'pass1',
                    'csrf_token': csrf_token1
                })
                
                client2.post('/login', data={
                    'username': 'user2_sec_test',
                    'password': 'pass2',
                    'csrf_token': csrf_token2
                })

                # בדיקת בידוד הסשנים
                with client1.session_transaction() as sess1:
                    assert sess1.get('_user_id') == '2'
                    sess1['test_key'] = 'test_value_1'

                with client2.session_transaction() as sess2:
                    assert sess2.get('_user_id') == '3'
                    sess2['test_key'] = 'test_value_2'

                # בדיקה שהערכים לא התערבבו
                with client1.session_transaction() as sess1:
                    assert sess1.get('test_key') == 'test_value_1'
                    assert sess1.get('_user_id') == '2'

                with client2.session_transaction() as sess2:
                    assert sess2.get('test_key') == 'test_value_2'
                    assert sess2.get('_user_id') == '3'

                # בדיקת התנתקות
                client1.get('/logout')
                client2.get('/logout')

                # בדיקה שהסשנים נוקו
                with client1.session_transaction() as sess1:
                    assert sess1.get('_user_id') is None
                    assert sess1.get('test_key') is None

                with client2.session_transaction() as sess2:
                    assert sess2.get('_user_id') is None
                    assert sess2.get('test_key') is None

        finally:
            # שחזור המשתמשים המקוריים
            main_app.USERS = original_users

    def test_session_persistence(self, client):
        with client.session_transaction() as sess:
            sess['test_key'] = 'test_value'
        with client.session_transaction() as sess:
            assert sess.get('test_key') == 'test_value'

    def test_logout_clears_session(self, authenticated_client):
        with authenticated_client.session_transaction() as sess:
            sess['selected_ticker'] = 'LOGOUTTEST'
            assert sess.get('selected_ticker') == 'LOGOUTTEST'

        logout_response = authenticated_client.get('/logout', follow_redirects=True)
        assert url_for('login') in logout_response.request.path 
        assert 'התנתקת בהצלחה.' in logout_response.data.decode('utf-8')
        assert 'Username:' in logout_response.data.decode('utf-8') # בהנחה שדף הלוגין באנגלית

        with authenticated_client.session_transaction() as sess_after_logout:
            assert sess_after_logout.get('selected_ticker') is None
            assert sess_after_logout.get('company_name') is None
            assert sess_after_logout.get('company_info') is None
            assert sess_after_logout.get('_user_id') is None


class TestErrorHandling:
    def test_404_error_handler(self, client):
        response = client.get('/nonexistent-page-for-404-test')
        assert response.status_code == 404
        assert "אופס! הדף לא נמצא." in response.data.decode('utf-8')

    def test_500_error_simulation(self, authenticated_client):
        with patch('modules.routes.home.get_price_history', side_effect=Exception("Simulated Internal Server Error")):
            response = authenticated_client.post('/analyze', data={'ticker': 'TEST500'}, follow_redirects=True)
            assert response.status_code == 200 
            # *** תיקון הודעת שגיאה ***
            assert 'אירעה שגיאה בעת ניתוח הטיקר. אנא נסה שוב.' in response.data.decode('utf-8')


class TestAuthorizationBypass:
    def test_cannot_access_admin_without_permission(self, client):
        response = client.get('/admin/users', follow_redirects=True)
        assert response.status_code == 200 
        assert url_for('login') in response.request.path
        assert 'נא להתחבר כדי לגשת לדף זה.' in response.data.decode('utf-8')
        assert 'Username:' in response.data.decode('utf-8') # בהנחה שדף הלוגין באנגלית

    def test_cannot_perform_admin_actions_without_permission(self, client):
        response = client.get('/admin/users/1/approve', follow_redirects=True)
        assert response.status_code == 200
        assert url_for('login') in response.request.path
        assert 'נא להתחבר כדי לגשת לדף זה.' in response.data.decode('utf-8')
        assert 'Username:' in response.data.decode('utf-8')

    def test_non_admin_cannot_access_admin_page(self, client, app_with_temp_users_for_security): # שימוש ב-fixture המעודכן
        with app_with_temp_users_for_security.test_client() as regular_user_client:
            login_resp = regular_user_client.post('/login', data={'username': 'normaluser', 'password': 'password123'}, follow_redirects=True)
            assert login_resp.status_code == 200 

            response = regular_user_client.get('/admin/users', follow_redirects=True)
            assert response.status_code == 200 
            assert 'אין לך הרשאות לגשת לדף זה.' in response.data.decode('utf-8')
            assert 'User Management' not in response.data.decode('utf-8')


class TestDataSanitization:
    def test_username_input_sanitization(self, client):
        response = client.get(url_for('register'))
        html = response.data.decode('utf-8')
        csrf_token = extract_csrf_token(html)
        xss_attempts = [
            '<script>alert("xss")</script>',
            '\"><img src=x onerror=alert("xss")>',
            "admin'; DROP TABLE users; --",
        ]
        expected_error_message = 'שם המשתמש יכול להכיל רק אותיות (אנגלית), מספרים, נקודה (.), קו תחתון (_) ומקף (-).'
        for xss_username in xss_attempts:
            response = client.post('/register', data={
                'username': xss_username,
                'password': 'testpass123',
                'confirm_password': 'testpass123',
                'csrf_token': csrf_token
            }, follow_redirects=False) 
            assert response.status_code == 400, f"Registration with '{xss_username}' should return 400 Bad Request"
            assert expected_error_message in response.data.decode('utf-8'), f"Flash message for invalid username '{xss_username}' not found or incorrect. Response: {response.data.decode('utf-8')}"

    def test_ticker_input_sanitization(self, authenticated_client):
        home_response = authenticated_client.get(url_for('home_bp.index'))
        html_content = home_response.data.decode('utf-8')
        csrf_token = extract_csrf_token(html_content)
        malicious_ticker = "<script>alert('xss_ticker')</script>"
        expected_message = 'הסימול יכול להכיל רק אותיות באנגלית, ספרות, נקודה (.), מקף (-), או גג (^).'
        response = authenticated_client.post('/analyze', data={'ticker': malicious_ticker, 'csrf_token': csrf_token}, follow_redirects=True)
        assert response.status_code == 200
        assert expected_message in response.data.decode('utf-8')
        assert html_mod.escape(malicious_ticker) not in response.data.decode('utf-8').replace('&lt;', '<').replace('&gt;', '>')
        assert "<script>alert('xss_ticker')</script>" not in response.data.decode('utf-8')