# tests/test_integration.py
import pytest
from unittest.mock import patch, ANY
from flask import session, current_app, Flask
import pandas as pd
import json
import os
import re  # הוספנו ייבוא של re

# ודא שהייבוא של User, generate_password_hash ו-app (אפליקציית Flask) נכונים
# אם הם מוגדרים ב-app.py הראשי שלך. ה-app fixture מגיע מ-conftest.py.
from app import User, generate_password_hash
# את main_app_for_client_creation נייבא מ-conftest דרך ה-fixture של app
# from app import app as main_app_for_client_creation # הסרנו את זה כי app מגיע מ-conftest

# פונקציה לחילוץ CSRF token
def extract_csrf_token(html):
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    if not match:
        raise Exception("CSRF token not found in form")
    return match.group(1)

# נתונים לדוגמה
SAMPLE_INTEGRATION_TICKER_AAPL = "AAPL"
EXPECTED_INTEGRATION_COMPANY_AAPL = "Apple Inc."
SAMPLE_INTEGRATION_TICKER_MSFT = "MSFT"
EXPECTED_INTEGRATION_COMPANY_MSFT = "Microsoft Corp."
SAMPLE_INTEGRATION_TICKER_TEST = "TEST"
EXPECTED_INTEGRATION_COMPANY_TEST = "Test Company XYZ"

# --- הגדרת ה-FIXTURE כאן ברמת המודול ---
@pytest.fixture
def sample_stock_data():
    """Fixture to provide sample stock data as a DataFrame."""
    data = {
        'Open': [100.0, 101.0, 102.0, 103.0, 104.0],
        'High': [105.0, 106.0, 107.0, 108.0, 109.0],
        'Low': [95.0, 96.0, 97.0, 98.0, 99.0],
        'Close': [102.0, 103.0, 104.0, 105.0, 106.0],
        'Volume': [1000000, 1100000, 1200000, 1300000, 1400000]
    }
    idx = pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05'])
    df = pd.DataFrame(data, index=idx)
    df.index.name = 'Date'
    # נוודא שהעמודות הנדרשות ל-resample_ohlc קיימות
    required_ohlc_cols = ['Open', 'High', 'Low', 'Close']
    for col in required_ohlc_cols:
        if col not in df.columns:
            df[col] = 100 # ערך ברירת מחדל כלשהו אם חסר
    if 'Volume' not in df.columns:
        df['Volume'] = 100000 # ערך ברירת מחדל
    return df
# ---------------------------------------

MOCK_DAILY_JSON_INTEGRATION = json.dumps({"data": [{"type": "candlestick"}], "layout": {"title": "Daily Chart Integration Mock Title"}})
MOCK_WEEKLY_JSON_INTEGRATION = json.dumps({"data": [{"type": "candlestick"}], "layout": {"title": "Weekly Chart Integration Mock Title"}})
MOCK_MONTHLY_JSON_INTEGRATION = json.dumps({"data": [{"type": "candlestick"}], "layout": {"title": "Monthly Chart Integration Mock Title"}})

MOCK_CHARTS_DICT_INTEGRATION = {
    'daily_chart_json': MOCK_DAILY_JSON_INTEGRATION,
    'weekly_chart_json': MOCK_WEEKLY_JSON_INTEGRATION,
    'monthly_chart_json': MOCK_MONTHLY_JSON_INTEGRATION
}
EMPTY_CHARTS_DICT_INTEGRATION = {
    'daily_chart_json': None, 'weekly_chart_json': None, 'monthly_chart_json': None
}


class TestCompleteUserWorkflow:
    def test_multiple_user_sessions_isolation(self, app, sample_stock_data):
        # הגדרת משתמשים לבדיקה
        users_dict = {
            1: User(1, 'admin_iso_test', generate_password_hash('Admin123!'), True),
            2: User(2, 'user1_iso_test', generate_password_hash('pass1'), True),
            3: User(3, 'user2_iso_test', generate_password_hash('pass2'), True),
        }

        # הגדרת נתוני גרפים לבדיקה
        mock_charts_for_isolation_test = {
            'daily_chart_json': "chart1_iso_daily",
            'weekly_chart_json': "chart1_iso_weekly",
            'monthly_chart_json': "chart1_iso_monthly"
        }

        # הגדרת משתנים גלובליים זמניים
        import app as main_app
        original_users = main_app.USERS
        main_app.USERS = users_dict

        try:
            # יצירת לקוחות נפרדים
            client1 = app.test_client()
            client2 = app.test_client()

            # התחברות משתמש ראשון
            with client1:
                # קבלת CSRF token
                response = client1.get('/login')
                csrf_token = extract_csrf_token(response.data.decode('utf-8'))
                
                # התחברות
                client1.post('/login', data={
                    'username': 'user1_iso_test',
                    'password': 'pass1',
                    'csrf_token': csrf_token
                }, follow_redirects=True)

                # קבלת CSRF token לניתוח
                analyze_response = client1.get('/')
                analyze_csrf = extract_csrf_token(analyze_response.data.decode('utf-8'))

                # ניתוח
                with patch('modules.routes.home.get_price_history', return_value=sample_stock_data), \
                     patch('modules.routes.home.get_company_name', return_value="CompanyForUser1"), \
                     patch('modules.routes.home.get_company_info', return_value={"sector": "Tech1"}), \
                     patch('modules.routes.home.create_all_candlestick_charts', return_value=mock_charts_for_isolation_test):
                    client1.post('/analyze', data={
                        'ticker': 'TICKER1',
                        'csrf_token': analyze_csrf
                    }, follow_redirects=True)

                # בדיקת סשן משתמש ראשון
                with client1.session_transaction() as sess:
                    assert sess.get('selected_ticker') == 'TICKER1'
                    assert sess.get('company_name') == "CompanyForUser1"
                    assert sess.get('_user_id') == '2'

                # התנתקות משתמש ראשון
                client1.get('/logout', follow_redirects=True)

            # התחברות משתמש שני
            with client2:
                # קבלת CSRF token
                response = client2.get('/login')
                csrf_token = extract_csrf_token(response.data.decode('utf-8'))
                
                # התחברות
                client2.post('/login', data={
                    'username': 'user2_iso_test',
                    'password': 'pass2',
                    'csrf_token': csrf_token
                }, follow_redirects=True)

                # קבלת CSRF token לניתוח
                analyze_response = client2.get('/')
                analyze_csrf = extract_csrf_token(analyze_response.data.decode('utf-8'))

                # ניתוח
                with patch('modules.routes.home.get_price_history', return_value=sample_stock_data), \
                     patch('modules.routes.home.get_company_name', return_value="CompanyForUser2"), \
                     patch('modules.routes.home.get_company_info', return_value={"sector": "Tech2"}), \
                     patch('modules.routes.home.create_all_candlestick_charts', return_value=mock_charts_for_isolation_test):
                    client2.post('/analyze', data={
                        'ticker': 'TICKER2',
                        'csrf_token': analyze_csrf
                    }, follow_redirects=True)

                # בדיקת סשן משתמש שני
                with client2.session_transaction() as sess:
                    assert sess.get('selected_ticker') == 'TICKER2'
                    assert sess.get('company_name') == "CompanyForUser2"
                    assert sess.get('_user_id') == '3'

                # התנתקות משתמש שני
                client2.get('/logout', follow_redirects=True)

        finally:
            # שחזור המשתמשים המקוריים
            main_app.USERS = original_users


class TestErrorRecoveryWorkflows:

    # authenticated_client מגיע מ-conftest.py
    # sample_stock_data מגיע מה-fixture שהגדרנו למעלה בקובץ זה
    def test_analysis_error_recovery(self, authenticated_client, sample_stock_data):
        with patch('modules.routes.home.get_price_history', side_effect=Exception("Network error")) as mock_get_history:
            response = authenticated_client.post('/analyze', data={'ticker': SAMPLE_INTEGRATION_TICKER_AAPL}, follow_redirects=True)
            assert response.status_code == 200
            assert 'אירעה שגיאה בעת ניתוח הטיקר. אנא נסה שוב.' in response.data.decode('utf-8')
            mock_get_history.assert_called_once_with(SAMPLE_INTEGRATION_TICKER_AAPL, period="10y", interval="1d")

        with patch('modules.routes.home.get_price_history', return_value=sample_stock_data), \
             patch('modules.routes.home.get_company_name', return_value=EXPECTED_INTEGRATION_COMPANY_AAPL), \
             patch('modules.routes.home.get_company_info', return_value={"sector": "Tech"}), \
             patch('modules.routes.home.create_all_candlestick_charts', return_value=MOCK_CHARTS_DICT_INTEGRATION) as mock_create_charts_success:
            response_success = authenticated_client.post('/analyze', data={'ticker': SAMPLE_INTEGRATION_TICKER_AAPL}, follow_redirects=True)
            assert response_success.status_code == 200
            response_html_success = response_success.data.decode('utf-8')
            assert EXPECTED_INTEGRATION_COMPANY_AAPL in response_html_success
            assert "Daily Chart Integration Mock Title" in response_html_success
            assert 'אירעה שגיאה בעת ניתוח הטיקר. אנא נסה שוב.' not in response_html_success


    def test_login_logout_session_cleanup(self, client, sample_stock_data):
        client.post('/login', data={'username': 'admin', 'password': 'Admin123!'}, follow_redirects=True)

        with patch('modules.routes.home.get_price_history', return_value=sample_stock_data), \
             patch('modules.routes.home.get_company_name', return_value=EXPECTED_INTEGRATION_COMPANY_TEST) as mock_get_name_call, \
             patch('modules.routes.home.get_company_info', return_value={"sector": "Technology"}), \
             patch('modules.routes.home.create_all_candlestick_charts', return_value=MOCK_CHARTS_DICT_INTEGRATION):
            client.post('/analyze', data={'ticker': SAMPLE_INTEGRATION_TICKER_TEST})

        with client.session_transaction() as sess:
            assert sess.get('selected_ticker') == SAMPLE_INTEGRATION_TICKER_TEST
            assert sess.get('company_name') == EXPECTED_INTEGRATION_COMPANY_TEST
        
        mock_get_name_call.assert_called_once_with(SAMPLE_INTEGRATION_TICKER_TEST)

        logout_response = client.get('/logout', follow_redirects=True)
        assert 'התנתקת בהצלחה.' in logout_response.data.decode('utf-8')

        with client.session_transaction() as sess_after_logout:
            assert sess_after_logout.get('selected_ticker') is None
            assert sess_after_logout.get('company_name') is None # הוספנו לבדיקה
            assert sess_after_logout.get('company_info') is None # הוספנו לבדיקה
            assert sess_after_logout.get('_user_id') is None

        home_response_after_logout = client.get('/', follow_redirects=True)
        assert 'Username:' in home_response_after_logout.data.decode('utf-8')


    def test_concurrent_analysis_requests(self, authenticated_client, sample_stock_data):
        tickers = [SAMPLE_INTEGRATION_TICKER_AAPL, SAMPLE_INTEGRATION_TICKER_MSFT]
        companies = [EXPECTED_INTEGRATION_COMPANY_AAPL, EXPECTED_INTEGRATION_COMPANY_MSFT]
        mock_chart_titles = ["AAPL Concurrent Test Chart Title", "MSFT Concurrent Test Chart Title"]

        for i, (ticker, company) in enumerate(zip(tickers, companies)):
            current_mock_charts_dict = {
                'daily_chart_json': json.dumps({"layout": {"title": mock_chart_titles[i]}}),
                'weekly_chart_json': None,
                'monthly_chart_json': None
            }
            with patch('modules.routes.home.get_price_history', return_value=sample_stock_data), \
                 patch('modules.routes.home.get_company_name', return_value=company), \
                 patch('modules.routes.home.get_company_info', return_value={"sector": "Technology"}), \
                 patch('modules.routes.home.create_all_candlestick_charts', return_value=current_mock_charts_dict):
                response = authenticated_client.post('/analyze', data={'ticker': ticker}, follow_redirects=True)
                assert response.status_code == 200
                response_html = response.data.decode('utf-8')
                assert company in response_html
                assert mock_chart_titles[i] in response_html
                with authenticated_client.session_transaction() as sess:
                    assert sess.get('selected_ticker') == ticker
                    assert sess.get('company_name') == company


class TestChartGenerationWorkflows:

    def test_complete_chart_generation_workflow(self, authenticated_client, sample_stock_data):
        with patch('modules.routes.home.get_price_history', return_value=sample_stock_data), \
             patch('modules.routes.home.get_company_name', return_value=EXPECTED_INTEGRATION_COMPANY_AAPL), \
             patch('modules.routes.home.get_company_info', return_value={"sector": "Technology", "longBusinessSummary": "Some summary"}), \
             patch('modules.routes.home.create_all_candlestick_charts', return_value=MOCK_CHARTS_DICT_INTEGRATION) as mock_charts:
            response = authenticated_client.post('/analyze', data={'ticker': SAMPLE_INTEGRATION_TICKER_AAPL}, follow_redirects=True)
            assert response.status_code == 200
            html_content = response.data.decode('utf-8')
            assert EXPECTED_INTEGRATION_COMPANY_AAPL in html_content
            assert "Technology" in html_content
            assert "Daily Chart Integration Mock Title" in html_content
            assert "Weekly Chart Integration Mock Title" in html_content
            assert "Monthly Chart Integration Mock Title" in html_content
            with authenticated_client.session_transaction() as sess:
                assert sess.get('chart1_json') is None
                assert sess.get('chart2_json') is None
                assert sess.get('chart3_json') is None

    def test_chart_generation_error_handling(self, authenticated_client, sample_stock_data):
        with patch('modules.routes.home.get_price_history', return_value=sample_stock_data), \
             patch('modules.routes.home.get_company_name', return_value=EXPECTED_INTEGRATION_COMPANY_AAPL), \
             patch('modules.routes.home.get_company_info', return_value={"sector": "Technology"}), \
             patch('modules.routes.home.create_all_candlestick_charts', side_effect=Exception("Simulated Chart generation failed")) as mock_create_charts_failure:
            response = authenticated_client.post('/analyze', data={'ticker': SAMPLE_INTEGRATION_TICKER_AAPL}, follow_redirects=True)
            assert response.status_code == 200
            assert 'אירעה שגיאה בעת ניתוח הטיקר. אנא נסה שוב.' in response.data.decode('utf-8')
            mock_create_charts_failure.assert_called_once()