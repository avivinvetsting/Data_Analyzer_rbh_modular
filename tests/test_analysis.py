# tests/test_analysis.py
import pytest
from unittest.mock import patch, ANY
from flask import session, current_app
import pandas as pd
import json

# ודא שהייבוא של האפליקציה שלך תקין בהתאם למבנה הפרויקט
# from app import app # מגיע מ-conftest.py

# נתונים לדוגמה עבור Mocks
SAMPLE_TICKER = "AAPL"
SAMPLE_COMPANY_NAME = "Apple Inc."
EXPECTED_COMPANY_DISPLAY_NAME = "Apple Inc."

SAMPLE_COMPANY_INFO = {"sector": "Technology", "longBusinessSummary": "Apple designs consumer electronics."}
# ניצור DataFrame לדוגמה עם העמודות הנדרשות
SAMPLE_PRICE_DATA_DF = pd.DataFrame({
    'Open': [150.0, 151.0, 150.5, 152.0, 153.0],
    'High': [152.0, 152.5, 151.5, 153.0, 154.0],
    'Low': [149.0, 150.0, 149.5, 151.0, 152.0],
    'Close': [151.0, 150.5, 151.0, 152.5, 153.5],
    'Volume': [1000000, 1100000, 1050000, 1200000, 1150000]
}, index=pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05']))
SAMPLE_PRICE_DATA_DF.index.name = 'Date'


# Mocks עבור JSON של גרפים - נשתמש רק בכותרות לבדיקה ב-HTML
MOCK_DAILY_CHART_TITLE = f"{EXPECTED_COMPANY_DISPLAY_NAME} ({SAMPLE_TICKER}) - Daily Prices (Last 2 Years)"
MOCK_WEEKLY_CHART_TITLE = f"{EXPECTED_COMPANY_DISPLAY_NAME} ({SAMPLE_TICKER}) - Weekly Prices (Last 5 Years)"
MOCK_MONTHLY_CHART_TITLE = f"{EXPECTED_COMPANY_DISPLAY_NAME} ({SAMPLE_TICKER}) - Monthly Prices (Last 10 Years)"

MOCK_ALL_CHARTS_RETURN_VALUE = {
    'daily_chart_json': json.dumps({"layout": {"title": MOCK_DAILY_CHART_TITLE}}), # מספיק JSON עם כותרת
    'weekly_chart_json': json.dumps({"layout": {"title": MOCK_WEEKLY_CHART_TITLE}}),
    'monthly_chart_json': json.dumps({"layout": {"title": MOCK_MONTHLY_CHART_TITLE}})
}


class TestAnalysisWorkflow:

    def test_complete_analysis_workflow_success(self, authenticated_client):
        with patch('modules.routes.home.get_price_history', return_value=SAMPLE_PRICE_DATA_DF) as mock_get_price, \
             patch('modules.routes.home.get_company_name', return_value=SAMPLE_COMPANY_NAME) as mock_get_name, \
             patch('modules.routes.home.get_company_info', return_value=SAMPLE_COMPANY_INFO) as mock_get_info, \
             patch('modules.routes.home.create_all_candlestick_charts', return_value=MOCK_ALL_CHARTS_RETURN_VALUE) as mock_create_charts:

            response = authenticated_client.post('/analyze', data={'ticker': SAMPLE_TICKER}, follow_redirects=True)
            assert response.status_code == 200
            response_html = response.data.decode('utf-8')

            assert EXPECTED_COMPANY_DISPLAY_NAME in response_html
            assert SAMPLE_COMPANY_INFO["sector"] in response_html
            
            # *** תיקון: בדוק רק את כותרות הגרפים ב-HTML ***
            assert MOCK_DAILY_CHART_TITLE in response_html
            assert MOCK_WEEKLY_CHART_TITLE in response_html
            assert MOCK_MONTHLY_CHART_TITLE in response_html

            with authenticated_client.session_transaction() as sess:
                assert sess.get('selected_ticker') == SAMPLE_TICKER
                assert sess.get('company_name') == EXPECTED_COMPANY_DISPLAY_NAME
                company_info_in_session = sess.get('company_info')
                assert company_info_in_session is not None
                assert company_info_in_session.get('sector') == SAMPLE_COMPANY_INFO["sector"]
                assert sess.get('chart1_json') is None
                assert sess.get('chart2_json') is None
                assert sess.get('chart3_json') is None

            mock_get_price.assert_called_once_with(SAMPLE_TICKER, period="10y", interval="1d")
            mock_get_name.assert_called_once_with(SAMPLE_TICKER)
            mock_get_info.assert_called_once_with(SAMPLE_TICKER)
            mock_create_charts.assert_called_once()
            call_args = mock_create_charts.call_args[0]
            pd.testing.assert_frame_equal(call_args[0], SAMPLE_PRICE_DATA_DF)
            assert call_args[1] == SAMPLE_TICKER
            assert call_args[2] == EXPECTED_COMPANY_DISPLAY_NAME

    def test_analysis_workflow_no_price_data(self, authenticated_client):
        with patch('modules.routes.home.get_price_history', return_value=pd.DataFrame()) as mock_get_price, \
             patch('modules.routes.home.get_company_name', return_value="NoData Inc.") as mock_get_name, \
             patch('modules.routes.home.get_company_info', return_value={"sector": "N/A"}) as mock_get_info, \
             patch('modules.routes.home.create_all_candlestick_charts') as mock_create_charts:
            response = authenticated_client.post('/analyze', data={'ticker': 'NODATA'}, follow_redirects=True)
            assert response.status_code == 200
            response_html = response.data.decode('utf-8')
            assert "NoData Inc." in response_html
            assert 'לא נמצאו נתוני מחירים בסיסיים עבור NODATA ליצירת גרפים.' in response_html
            mock_create_charts.assert_not_called()
            with authenticated_client.session_transaction() as sess:
                assert sess.get('selected_ticker') == 'NODATA'
                assert sess.get('company_name') == "NoData Inc."

    def test_analysis_workflow_no_chart_data_created(self, authenticated_client):
        empty_charts_return = {'daily_chart_json': None, 'weekly_chart_json': None, 'monthly_chart_json': None}
        with patch('modules.routes.home.get_price_history', return_value=SAMPLE_PRICE_DATA_DF), \
             patch('modules.routes.home.get_company_name', return_value=SAMPLE_COMPANY_NAME), \
             patch('modules.routes.home.get_company_info', return_value=SAMPLE_COMPANY_INFO), \
             patch('modules.routes.home.create_all_candlestick_charts', return_value=empty_charts_return) as mock_create_charts:
            response = authenticated_client.post('/analyze', data={'ticker': SAMPLE_TICKER}, follow_redirects=True)
            assert response.status_code == 200
            response_html = response.data.decode('utf-8')
            assert EXPECTED_COMPANY_DISPLAY_NAME in response_html
            assert f"לא נמצאו מספיק נתונים ליצירת גרפים עבור {SAMPLE_TICKER}." in response_html
            mock_create_charts.assert_called_once()

    def test_analysis_workflow_api_failure(self, authenticated_client):
        with patch('modules.routes.home.get_price_history', side_effect=Exception("API Error")):
            response = authenticated_client.post('/analyze', data={'ticker': 'FAILTICKER'}, follow_redirects=True)
            assert response.status_code == 200
            # *** תיקון הודעת שגיאה ***
            assert 'אירעה שגיאה בעת ניתוח הטיקר. אנא נסה שוב.' in response.data.decode('utf-8')
            with authenticated_client.session_transaction() as sess:
                assert sess.get('selected_ticker') is None
                assert sess.get('company_name') is None
                assert sess.get('company_info') is None

    def test_bad_request_invalid_ticker_format(self, authenticated_client):
        response = authenticated_client.post('/analyze', data={'ticker': 'INVALIDTICKER@!'}, follow_redirects=True)
        assert response.status_code == 200
        assert 'הסימול יכול להכיל רק אותיות באנגלית, ספרות, נקודה (.), מקף (-), או גג (^).' in response.data.decode('utf-8')

    def test_bad_request_empty_ticker(self, authenticated_client):
        response = authenticated_client.post('/analyze', data={'ticker': ''}, follow_redirects=True)
        assert response.status_code == 200
        assert 'אנא הזן סימול טיקר.' in response.data.decode('utf-8')

    def test_bad_request_whitespace_ticker(self, authenticated_client):
        response = authenticated_client.post('/analyze', data={'ticker': '   '}, follow_redirects=True)
        assert response.status_code == 200
        assert 'אנא הזן סימול טיקר.' in response.data.decode('utf-8')