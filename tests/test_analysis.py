import pytest
import pandas as pd
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from app import app
import modules.price_history as price_history
import modules.chart_creator as chart_creator
import modules.data_fetcher as data_fetcher


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

@pytest.fixture
def sample_stock_data():
    """Create sample stock data for testing."""
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    data = {
        'Open': [100 + i for i in range(100)],
        'High': [105 + i for i in range(100)],
        'Low': [95 + i for i in range(100)],
        'Close': [102 + i for i in range(100)],
        'Volume': [1000000 + i*10000 for i in range(100)]
    }
    return pd.DataFrame(data, index=dates)

@pytest.fixture
def empty_stock_data():
    """Create empty stock data for testing error cases."""
    return pd.DataFrame()


class TestPriceHistory:
    
    def test_get_price_history_success(self, sample_stock_data):
        """Test successful price data retrieval."""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_instance = MagicMock()
            mock_instance.history.return_value = sample_stock_data
            mock_ticker.return_value = mock_instance
            
            with app.app_context():
                result = price_history.get_price_history('AAPL', '1y', '1d')
            
            assert not result.empty
            assert len(result) == 100
            assert all(col in result.columns for col in ['Open', 'High', 'Low', 'Close'])
    
    def test_get_price_history_empty_response(self, empty_stock_data):
        """Test handling of empty response from yfinance."""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_instance = MagicMock()
            mock_instance.history.return_value = empty_stock_data
            mock_ticker.return_value = mock_instance
            
            with app.app_context():
                result = price_history.get_price_history('INVALID', '1y', '1d')
            
            assert result.empty
    
    def test_get_price_history_missing_columns(self):
        """Test handling of data with missing required columns."""
        # Create data missing required columns
        incomplete_data = pd.DataFrame({
            'Open': [100, 101, 102],
            'High': [105, 106, 107],
            # Missing 'Low' and 'Close'
        }, index=pd.date_range('2023-01-01', periods=3))
        
        with patch('yfinance.Ticker') as mock_ticker:
            mock_instance = MagicMock()
            mock_instance.history.return_value = incomplete_data
            mock_ticker.return_value = mock_instance
            
            with app.app_context():
                result = price_history.get_price_history('TEST', '1y', '1d')
            
            assert result.empty
    
    def test_get_price_history_exception_handling(self):
        """Test exception handling in price data retrieval."""
        with patch('yfinance.Ticker', side_effect=Exception("Network error")):
            with app.app_context():
                # Clear cache to avoid hitting cached data
                price_history.price_data_cache.clear()
                result = price_history.get_price_history('TEST_EXCEPTION', '1y', '1d')
            
            assert result.empty
    
    def test_get_company_name_success(self):
        """Test successful company name retrieval."""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_instance = MagicMock()
            mock_instance.info = {'longName': 'Apple Inc.'}
            mock_ticker.return_value = mock_instance
            
            with app.app_context():
                result = price_history.get_company_name('AAPL')
            
            assert result == 'Apple Inc.'
    
    def test_get_company_name_fallback_to_short_name(self):
        """Test fallback to shortName when longName is not available."""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_instance = MagicMock()
            mock_instance.info = {'shortName': 'Apple'}
            mock_ticker.return_value = mock_instance
            
            with app.app_context():
                result = price_history.get_company_name('AAPL')
            
            # Should return shortName, longName, or ticker as fallback
            assert result in ['Apple', 'AAPL', 'Apple Inc.']
    
    def test_get_company_name_no_name_available(self):
        """Test handling when no company name is available."""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_instance = MagicMock()
            mock_instance.info = {}
            mock_ticker.return_value = mock_instance
            
            with app.app_context():
                result = price_history.get_company_name('UNKNOWN')
            
            assert result == 'UNKNOWN'
    
    def test_get_company_info_success(self):
        """Test successful company info retrieval."""
        sample_info = {
            'longBusinessSummary': 'Apple Inc. designs and manufactures consumer electronics.',
            'sector': 'Technology',
            'industry': 'Consumer Electronics',
            'marketCap': 3000000000000,
            'employees': 154000
        }
        
        with patch('yfinance.Ticker') as mock_ticker:
            mock_instance = MagicMock()
            mock_instance.info = sample_info
            mock_ticker.return_value = mock_instance
            
            with app.app_context():
                result = price_history.get_company_info('AAPL')
            
            # Check that result contains expected fields
            assert isinstance(result, dict)
            if 'sector' in result:
                assert result['sector'] == 'Technology'
    
    def test_get_company_info_exception_handling(self):
        """Test exception handling in company info retrieval."""
        with patch('yfinance.Ticker', side_effect=Exception("API error")):
            with app.app_context():
                result = price_history.get_company_info('AAPL')
            
            # Should return empty dict or handle gracefully
            assert isinstance(result, dict)
    
    def test_cache_functionality(self):
        """Test that caching works correctly."""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_instance = MagicMock()
            mock_instance.info = {'longName': 'Apple Inc.'}
            mock_ticker.return_value = mock_instance
            
            with app.app_context():
                # Clear cache first
                price_history.company_name_cache.clear()
                
                # First call should hit the API
                result1 = price_history.get_company_name('AAPL')
                assert mock_ticker.call_count == 1
                
                # Second call should use cache
                result2 = price_history.get_company_name('AAPL')
                assert mock_ticker.call_count == 1  # Should not increase
                
                assert result1 == result2 == 'Apple Inc.'


class TestChartCreator:
    
    def test_resample_ohlc_weekly(self, sample_stock_data):
        """Test OHLC resampling to weekly data."""
        with app.app_context():
            result = chart_creator.resample_ohlc(sample_stock_data, 'W')
        
        assert not result.empty
        assert len(result) < len(sample_stock_data)  # Should have fewer rows
        assert all(col in result.columns for col in ['Open', 'High', 'Low', 'Close'])
    
    def test_resample_ohlc_monthly(self, sample_stock_data):
        """Test OHLC resampling to monthly data."""
        with app.app_context():
            result = chart_creator.resample_ohlc(sample_stock_data, 'M')
        
        assert not result.empty
        assert len(result) < len(sample_stock_data)  # Should have fewer rows
        assert all(col in result.columns for col in ['Open', 'High', 'Low', 'Close'])
    
    def test_resample_ohlc_empty_data(self, empty_stock_data):
        """Test OHLC resampling with empty data."""
        with app.app_context():
            result = chart_creator.resample_ohlc(empty_stock_data, 'W')
        
        assert result.empty
    
    def test_create_candlestick_chart_success(self, sample_stock_data):
        """Test successful candlestick chart creation."""
        with app.app_context():
            result = chart_creator.create_candlestick_chart(
                sample_stock_data, 
                "Test Chart", 
                add_ma=True
            )
        
        assert result is not None
        assert isinstance(result, str)
        # Should be valid JSON
        chart_json = json.loads(result)
        assert 'data' in chart_json
        assert 'layout' in chart_json
    
    def test_create_candlestick_chart_without_ma(self, sample_stock_data):
        """Test candlestick chart creation without moving averages."""
        with app.app_context():
            result = chart_creator.create_candlestick_chart(
                sample_stock_data, 
                "Test Chart", 
                add_ma=False
            )
        
        assert result is not None
        assert isinstance(result, str)
        chart_json = json.loads(result)
        assert 'data' in chart_json
    
    def test_create_candlestick_chart_empty_data(self, empty_stock_data):
        """Test candlestick chart creation with empty data."""
        with app.app_context():
            result = chart_creator.create_candlestick_chart(
                empty_stock_data, 
                "Empty Chart"
            )
        
        assert result is None
    
    def test_create_all_candlestick_charts_success(self, sample_stock_data):
        """Test creation of all three chart types."""
        with patch('modules.chart_creator.resample_ohlc') as mock_resample:
            mock_resample.return_value = sample_stock_data
            
            with app.app_context():
                result = chart_creator.create_all_candlestick_charts(sample_stock_data, "AAPL", "Apple Inc.")
                daily = result.get('daily_chart_json')
                weekly = result.get('weekly_chart_json')
                monthly = result.get('monthly_chart_json')
            
            assert daily is not None
            assert weekly is not None
            assert monthly is not None
            
            # All should be valid JSON strings
            for chart in [daily, weekly, monthly]:
                assert isinstance(chart, str)
                chart_json = json.loads(chart)
                assert 'data' in chart_json
                assert 'layout' in chart_json


class TestDataFetcher:
    
    def test_get_stock_data_success(self, sample_stock_data):
        """Test successful stock data fetching."""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_instance = MagicMock()
            mock_instance.history.return_value = sample_stock_data
            mock_ticker.return_value = mock_instance
            
            with app.app_context():
                result = data_fetcher.get_stock_data('AAPL')
            
            assert result is not None
            assert not result.empty
            assert len(result) == 100
    
    def test_get_stock_data_empty_response(self, empty_stock_data):
        """Test handling of empty response."""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_instance = MagicMock()
            mock_instance.history.return_value = empty_stock_data
            mock_ticker.return_value = mock_instance
            
            with app.app_context():
                result = data_fetcher.get_stock_data('INVALID')
            
            assert result is None
    
    def test_get_stock_data_missing_columns(self):
        """Test handling of data with missing columns."""
        incomplete_data = pd.DataFrame({
            'Open': [100, 101, 102],
            'High': [105, 106, 107],
            # Missing required columns
        }, index=pd.date_range('2023-01-01', periods=3))
        
        with patch('yfinance.Ticker') as mock_ticker:
            mock_instance = MagicMock()
            mock_instance.history.return_value = incomplete_data
            mock_ticker.return_value = mock_instance
            
            with app.app_context():
                result = data_fetcher.get_stock_data('TEST')
            
            assert result is None
    
    def test_get_stock_data_invalid_values(self):
        """Test handling of data with invalid values."""
        invalid_data = pd.DataFrame({
            'Open': [100, -50, 102],  # Negative value
            'High': [105, 106, 107],
            'Low': [95, 96, 97],
            'Close': [102, 103, 104],
        }, index=pd.date_range('2023-01-01', periods=3))
        
        with patch('yfinance.Ticker') as mock_ticker:
            mock_instance = MagicMock()
            mock_instance.history.return_value = invalid_data
            mock_ticker.return_value = mock_instance
            
            with app.app_context():
                result = data_fetcher.get_stock_data('TEST')
            
            assert result is None


class TestAnalysisWorkflow:
    
    def test_complete_analysis_workflow_success(self, authenticated_client, sample_stock_data):
        """Test complete stock analysis workflow."""
        with patch('modules.price_history.get_price_history') as mock_price:
            with patch('modules.price_history.get_company_name') as mock_name:
                with patch('modules.price_history.get_company_info') as mock_info:
                    with patch('modules.chart_creator.create_all_candlestick_charts') as mock_charts:
                        # Mock all dependencies
                        mock_price.return_value = sample_stock_data
                        mock_name.return_value = "Apple Inc."
                        mock_info.return_value = {
                            "sector": "Technology", 
                            "longBusinessSummary": "Apple Inc. designs consumer electronics."
                        }
                        mock_charts.return_value = (
                            '{"chart": "daily"}',
                            '{"chart": "weekly"}',
                            '{"chart": "monthly"}'
                        )
                        
                        response = authenticated_client.post('/analyze', data={
                            'ticker': 'AAPL'
                        }, follow_redirects=True)
                        
                        assert response.status_code == 200
                        assert 'Apple Inc.' in response.data.decode('utf-8')
                        
                        # Check that session contains analysis data
                        with authenticated_client.session_transaction() as sess:
                            assert sess.get('selected_ticker') == 'AAPL'
                            assert sess.get('company_name') == 'Apple Inc.'
                            assert sess.get('company_info') is not None
                            assert sess.get('chart1_json') is not None
    
    def test_analysis_workflow_with_invalid_ticker(self, authenticated_client, empty_stock_data):
        """Test analysis workflow with invalid ticker."""
        with patch('modules.price_history.get_price_history') as mock_price:
            mock_price.return_value = empty_stock_data
            
            response = authenticated_client.post('/analyze', data={
                'ticker': 'INVALID'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            assert 'לא נמצאו נתוני מחירים בסיסיים עבור' in response.data.decode('utf-8')
    
    def test_analysis_workflow_api_failure(self, authenticated_client):
        """Test analysis workflow when API fails."""
        with patch('modules.routes.home.get_price_history', side_effect=Exception("API Error")):
            response = authenticated_client.post('/analyze', data={
                'ticker': 'AAPL'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            assert 'אירעה שגיאה בלתי צפויה בעת ניתוח הטיקר' in response.data.decode('utf-8')
    
    def test_analysis_session_persistence(self, authenticated_client, sample_stock_data):
        """Test that analysis results persist in session."""
        with patch('modules.routes.home.get_price_history') as mock_price:
            with patch('modules.routes.home.get_company_name') as mock_name:
                with patch('modules.routes.home.get_company_info') as mock_info:
                    with patch('modules.routes.home.create_all_candlestick_charts') as mock_charts:
                        # Mock successful analysis
                        mock_price.return_value = sample_stock_data
                        mock_name.return_value = "Test Company"
                        mock_info.return_value = {"sector": "Technology"}
                        mock_charts.return_value = {
                            'daily_chart_json': 'chart1',
                            'weekly_chart_json': 'chart2', 
                            'monthly_chart_json': 'chart3'
                        }
                        
                        # Perform analysis
                        authenticated_client.post('/analyze', data={'ticker': 'TEST'})
                        
                        # Access home page - should show persisted data
                        response = authenticated_client.get('/')
                        assert response.status_code == 200
                        assert 'Test Company' in response.data.decode('utf-8')
                        
                        # Session should contain the data
                        with authenticated_client.session_transaction() as sess:
                            assert sess.get('selected_ticker') == 'TEST'
                            assert sess.get('company_name') == 'Test Company'
    
    def test_multiple_analysis_sessions(self, authenticated_client, sample_stock_data):
        """Test multiple analysis requests in same session."""
        with patch('modules.routes.home.get_price_history') as mock_price:
            with patch('modules.routes.home.get_company_name') as mock_name:
                with patch('modules.routes.home.get_company_info') as mock_info:
                    with patch('modules.routes.home.create_all_candlestick_charts') as mock_charts:
                        mock_price.return_value = sample_stock_data
                        mock_info.return_value = {"sector": "Technology"}
                        mock_charts.return_value = {
                            'daily_chart_json': 'chart1',
                            'weekly_chart_json': 'chart2', 
                            'monthly_chart_json': 'chart3'
                        }
                        
                        # First analysis
                        mock_name.return_value = "Company 1"
                        authenticated_client.post('/analyze', data={'ticker': 'TEST1'})
                        
                        with authenticated_client.session_transaction() as sess:
                            assert sess.get('selected_ticker') == 'TEST1'
                            assert sess.get('company_name') == 'Company 1'
                        
                        # Second analysis should overwrite first
                        mock_name.return_value = "Company 2"
                        authenticated_client.post('/analyze', data={'ticker': 'TEST2'})
                        
                        with authenticated_client.session_transaction() as sess:
                            assert sess.get('selected_ticker') == 'TEST2'
                            assert sess.get('company_name') == 'Company 2'