# tests/test_forms.py
import pytest
from unittest.mock import patch, ANY
from flask import session
import pandas as pd
import json

# נתונים לדוגמה
FORM_TEST_TICKER = "GOOG"
FORM_TEST_EXPECTED_COMPANY_NAME = "Alphabet Inc."
FORM_TEST_COMPANY_INFO = {"sector": "Communication Services", "longBusinessSummary": "Alphabet Inc. is a global technology company."}
FORM_TEST_PRICE_DATA_DF = pd.DataFrame({
    'Open': [2000.0, 2010.0], 'High': [2020.0, 2015.0],
    'Low': [1990.0, 2000.0], 'Close': [2010.0, 2005.0],
    'Volume': [500000, 550000]
}, index=pd.to_datetime(['2023-01-01', '2023-01-02']))
FORM_TEST_PRICE_DATA_DF.index.name = 'Date'

# Mocks עבור כותרות גרפים
FORM_MOCK_DAILY_CHART_TITLE = f"{FORM_TEST_EXPECTED_COMPANY_NAME} ({FORM_TEST_TICKER}) - Daily Prices From Form Test"
FORM_MOCK_WEEKLY_CHART_TITLE = f"{FORM_TEST_EXPECTED_COMPANY_NAME} ({FORM_TEST_TICKER}) - Weekly Prices From Form Test"
FORM_MOCK_MONTHLY_CHART_TITLE = f"{FORM_TEST_EXPECTED_COMPANY_NAME} ({FORM_TEST_TICKER}) - Monthly Prices From Form Test"

# מילון החזרה תקין ל-mock_charts
FORM_MOCK_ALL_CHARTS_RETURN_DICT = {
    'daily_chart_json': json.dumps({"layout": {"title": FORM_MOCK_DAILY_CHART_TITLE}}),
    'weekly_chart_json': json.dumps({"layout": {"title": FORM_MOCK_WEEKLY_CHART_TITLE}}),
    'monthly_chart_json': json.dumps({"layout": {"title": FORM_MOCK_MONTHLY_CHART_TITLE}})
}


class TestAnalyzeForm:

    def test_analyze_form_valid_ticker_and_data_display(self, authenticated_client):
        with patch('modules.routes.home.get_price_history', return_value=FORM_TEST_PRICE_DATA_DF), \
             patch('modules.routes.home.get_company_name', return_value=FORM_TEST_EXPECTED_COMPANY_NAME), \
             patch('modules.routes.home.get_company_info', return_value=FORM_TEST_COMPANY_INFO), \
             patch('modules.routes.home.create_all_candlestick_charts', return_value=FORM_MOCK_ALL_CHARTS_RETURN_DICT):
            response = authenticated_client.post('/analyze', data={'ticker': FORM_TEST_TICKER}, follow_redirects=True)
            assert response.status_code == 200
            response_html = response.data.decode('utf-8')
            assert FORM_TEST_EXPECTED_COMPANY_NAME in response_html
            if FORM_TEST_COMPANY_INFO and FORM_TEST_COMPANY_INFO.get("sector"):
                 assert FORM_TEST_COMPANY_INFO["sector"] in response_html
            # *** תיקון: בדוק כותרות ב-HTML ***
            assert FORM_MOCK_DAILY_CHART_TITLE in response_html

    def test_analyze_form_preserves_session_data(self, authenticated_client):
        with patch('modules.routes.home.get_price_history', return_value=FORM_TEST_PRICE_DATA_DF), \
             patch('modules.routes.home.get_company_name', return_value=FORM_TEST_EXPECTED_COMPANY_NAME), \
             patch('modules.routes.home.get_company_info', return_value=FORM_TEST_COMPANY_INFO), \
             patch('modules.routes.home.create_all_candlestick_charts', return_value=FORM_MOCK_ALL_CHARTS_RETURN_DICT) as mock_create_charts: # שים לב לשימוש ב-DICT
            response = authenticated_client.post('/analyze', data={'ticker': FORM_TEST_TICKER}, follow_redirects=True)
            assert response.status_code == 200
            with authenticated_client.session_transaction() as sess:
                assert sess.get('selected_ticker') == FORM_TEST_TICKER
                assert sess.get('company_name') == FORM_TEST_EXPECTED_COMPANY_NAME
                company_info_in_session = sess.get('company_info')
                assert company_info_in_session is not None
                assert company_info_in_session.get('sector') == FORM_TEST_COMPANY_INFO["sector"]
                assert sess.get('chart1_json') is None
                assert sess.get('chart2_json') is None
                assert sess.get('chart3_json') is None
            mock_create_charts.assert_called_once()
            response_html = response.data.decode('utf-8')
            # *** תיקון: בדוק כותרת ב-HTML ***
            assert FORM_MOCK_DAILY_CHART_TITLE in response_html

    def test_analyze_form_empty_ticker_message(self, authenticated_client):
        response = authenticated_client.post('/analyze', data={'ticker': ''}, follow_redirects=True)
        assert response.status_code == 200
        assert 'אנא הזן סימול טיקר.' in response.data.decode('utf-8')

    def test_analyze_form_whitespace_only_ticker(self, authenticated_client):
        response = authenticated_client.post('/analyze', data={'ticker': '   '}, follow_redirects=True)
        assert response.status_code == 200
        assert 'אנא הזן סימול טיקר.' in response.data.decode('utf-8')

    def test_analyze_form_invalid_char_ticker_message(self, authenticated_client):
        response = authenticated_client.post('/analyze', data={'ticker': 'AAPL@!'}, follow_redirects=True)
        assert response.status_code == 200
        assert 'הסימול יכול להכיל רק אותיות באנגלית, ספרות, נקודה (.), מקף (-), או גג (^).' in response.data.decode('utf-8')

    def test_analyze_form_ticker_too_long(self, authenticated_client):
        long_ticker = "A" * (12 + 1) 
        response = authenticated_client.post('/analyze', data={'ticker': long_ticker}, follow_redirects=True)
        assert response.status_code == 200
        # ודא שהאורך המדויק מופיע בהודעה כפי שהוא מוגדר ב-home.py
        assert f'אורך הסימול חייב להיות בין 1 ל-12 תווים.' in response.data.decode('utf-8')