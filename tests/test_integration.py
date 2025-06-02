import pytest
import pandas as pd
import json
import tempfile
import os
from unittest.mock import patch, MagicMock
from app import app, User
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
def temp_users_file():
    """Create a temporary users file for testing."""
    temp_fd, temp_path = tempfile.mkstemp(suffix='.json')
    os.close(temp_fd)
    
    with patch('app.USERS_FILE', temp_path):
        yield temp_path
    
    if os.path.exists(temp_path):
        os.unlink(temp_path)

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


class TestCompleteUserWorkflow:
    """Test complete user workflows from registration to analysis."""
    
    def test_full_new_user_workflow(self, client, temp_users_file, sample_stock_data):
        """Test complete workflow: register -> admin approval -> login -> analysis."""
        
        import time
        unique_username = f'newuser_{int(time.time())}'
        
        # Step 1: New user registration
        response = client.post('/register', data={
            'username': unique_username,
            'password': 'newpass123',
            'confirm_password': 'newpass123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'ההרשמה הושלמה בהצלחה' in response.data.decode('utf-8')
        
        # Step 2: User tries to login but is not approved yet
        response = client.post('/login', data={
            'username': unique_username,
            'password': 'newpass123'
        })
        
        assert response.status_code == 200
        assert 'חשבונך ממתין לאישור מנהל' in response.data.decode('utf-8')
        
        # Step 3: Admin logs in and approves user
        response = client.post('/login', data={
            'username': 'admin',
            'password': 'Admin123!'
        })
        assert response.status_code == 302  # Redirect after successful login
        
        # Admin accesses user management
        response = client.get('/admin/users')
        assert response.status_code == 200
        assert unique_username in response.data.decode('utf-8')
        
        # Admin approves the user (need to mock USERS dict)
        users_dict = {
            1: User(1, 'admin', generate_password_hash('Admin123!'), True),
            2: User(2, unique_username, generate_password_hash('newpass123'), False)
        }
        
        with patch('app.USERS', users_dict):
            response = client.get('/admin/users/2/approve', follow_redirects=True)
            assert response.status_code == 200
            assert 'אושר בהצלחה' in response.data.decode('utf-8')
            
            # Update the user approval status
            users_dict[2].is_approved = True
        
        # Step 4: Admin logs out
        response = client.get('/logout', follow_redirects=True)
        assert 'התנתקת בהצלחה' in response.data.decode('utf-8')
        
        # Step 5: Approved user logs in successfully
        with patch('app.USERS', users_dict):
            response = client.post('/login', data={
                'username': unique_username,
                'password': 'newpass123'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            assert 'Stock Analysis - Home' in response.data.decode('utf-8')
        
        # Step 6: User performs stock analysis
        with patch('app.USERS', users_dict):
            with patch('modules.routes.home.get_price_history') as mock_price:
                with patch('modules.routes.home.get_company_name') as mock_name:
                    with patch('modules.routes.home.get_company_info') as mock_info:
                        with patch('modules.routes.home.create_all_candlestick_charts') as mock_charts:
                            mock_price.return_value = sample_stock_data
                            mock_name.return_value = "Apple Inc."
                            mock_info.return_value = {"sector": "Technology"}
                            mock_charts.return_value = {
                                'daily_chart_json': 'chart1',
                                'weekly_chart_json': 'chart2', 
                                'monthly_chart_json': 'chart3'
                            }
                            
                            response = client.post('/analyze', data={
                                'ticker': 'AAPL'
                            }, follow_redirects=True)
                            
                            assert response.status_code == 200
                            assert 'Apple Inc.' in response.data.decode('utf-8')
    
    def test_admin_user_management_workflow(self, client, temp_users_file):
        """Test complete admin user management workflow."""
        
        # Create multiple test users
        users_dict = {
            1: User(1, 'admin', generate_password_hash('Admin123!'), True),
            2: User(2, 'user1', generate_password_hash('pass1'), False),
            3: User(3, 'user2', generate_password_hash('pass2'), False),
            4: User(4, 'user3', generate_password_hash('pass3'), True),
        }
        
        with patch('app.USERS', users_dict):
            # Admin login
            response = client.post('/login', data={
                'username': 'admin',
                'password': 'Admin123!'
            })
            assert response.status_code == 302
            
            # View user management page
            response = client.get('/admin/users')
            assert response.status_code == 200
            html = response.data.decode('utf-8')
            assert 'user1' in html
            assert 'user2' in html
            assert 'user3' in html
            
            # Approve user1
            response = client.get('/admin/users/2/approve', follow_redirects=True)
            assert 'אושר בהצלחה' in response.data.decode('utf-8')
            
            # Approve user2
            response = client.get('/admin/users/3/approve', follow_redirects=True)
            assert 'אושר בהצלחה' in response.data.decode('utf-8')
            
            # Delete user3
            response = client.get('/admin/users/4/delete', follow_redirects=True)
            assert 'נמחק בהצלחה' in response.data.decode('utf-8')
            
            # Try to delete admin (should fail)
            response = client.get('/admin/users/1/delete', follow_redirects=True)
            assert 'לא ניתן למחוק את חשבון המנהל הראשי' in response.data.decode('utf-8')
            
            # Try invalid action
            response = client.get('/admin/users/2/invalid', follow_redirects=True)
            assert 'פעולה לא חוקית' in response.data.decode('utf-8')
    
    def test_multiple_user_sessions_isolation(self, client, sample_stock_data):
        """Test that multiple user sessions are properly isolated."""
        
        users_dict = {
            1: User(1, 'admin', generate_password_hash('Admin123!'), True),
            2: User(2, 'user1', generate_password_hash('pass1'), True),
            3: User(3, 'user2', generate_password_hash('pass2'), True),
        }
        
        with patch('app.USERS', users_dict):
            # Create two separate client instances
            with app.test_client() as client1, app.test_client() as client2:
                app.config['TESTING'] = True
                app.config['WTF_CSRF_ENABLED'] = False
                
                # User1 logs in on client1
                client1.post('/login', data={
                    'username': 'user1',
                    'password': 'pass1'
                })
                
                # User2 logs in on client2  
                client2.post('/login', data={
                    'username': 'user2',
                    'password': 'pass2'
                })
                
                # User1 performs analysis
                with patch('modules.price_history.get_price_history') as mock_price:
                    with patch('modules.price_history.get_company_name') as mock_name:
                        with patch('modules.price_history.get_company_info') as mock_info:
                            with patch('modules.chart_creator.create_all_candlestick_charts') as mock_charts:
                                mock_price.return_value = sample_stock_data
                                mock_name.return_value = "Apple Inc."
                                mock_info.return_value = {"sector": "Technology"}
                                mock_charts.return_value = ('chart1', 'chart2', 'chart3')
                                
                                client1.post('/analyze', data={'ticker': 'AAPL'})
                
                # User2 performs different analysis
                with patch('modules.price_history.get_price_history') as mock_price:
                    with patch('modules.price_history.get_company_name') as mock_name:
                        with patch('modules.price_history.get_company_info') as mock_info:
                            with patch('modules.chart_creator.create_all_candlestick_charts') as mock_charts:
                                mock_price.return_value = sample_stock_data
                                mock_name.return_value = "Microsoft Corp."
                                mock_info.return_value = {"sector": "Technology"}
                                mock_charts.return_value = ('chart1', 'chart2', 'chart3')
                                
                                client2.post('/analyze', data={'ticker': 'MSFT'})
                
                # Check that sessions are isolated
                with client1.session_transaction() as sess1:
                    assert sess1.get('selected_ticker') == 'AAPL'
                    assert sess1.get('company_name') == 'Apple Inc.'
                
                with client2.session_transaction() as sess2:
                    assert sess2.get('selected_ticker') == 'MSFT'
                    assert sess2.get('company_name') == 'Microsoft Corp.'


class TestErrorRecoveryWorkflows:
    """Test error recovery and edge case workflows."""
    
    def test_analysis_error_recovery(self, client, temp_users_file):
        """Test recovery from analysis errors."""
        
        # Login first
        client.post('/login', data={
            'username': 'admin',
            'password': 'Admin123!'
        })
        
        # First analysis fails due to network error
        with patch('modules.price_history.get_price_history', side_effect=Exception("Network error")):
            response = client.post('/analyze', data={
                'ticker': 'AAPL'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            assert 'אירעה שגיאה בלתי צפויה בעת ניתוח הטיקר' in response.data.decode('utf-8')
        
        # Session should not contain failed analysis data
        with client.session_transaction() as sess:
            assert sess.get('selected_ticker') is None
            assert sess.get('company_name') is None
        
        # Second analysis succeeds
        sample_data = pd.DataFrame({
            'Open': [100, 101], 'High': [105, 106],
            'Low': [95, 96], 'Close': [102, 103]
        }, index=pd.date_range('2023-01-01', periods=2))
        
        with patch('modules.price_history.get_price_history') as mock_price:
            with patch('modules.price_history.get_company_name') as mock_name:
                with patch('modules.price_history.get_company_info') as mock_info:
                    with patch('modules.chart_creator.create_all_candlestick_charts') as mock_charts:
                        mock_price.return_value = sample_data
                        mock_name.return_value = "Apple Inc."
                        mock_info.return_value = {"sector": "Technology"}
                        mock_charts.return_value = ('chart1', 'chart2', 'chart3')
                        
                        response = client.post('/analyze', data={
                            'ticker': 'AAPL'
                        }, follow_redirects=True)
                        
                        assert response.status_code == 200
                        assert 'Apple Inc.' in response.data.decode('utf-8')
        
        # Session should now contain successful analysis data
        with client.session_transaction() as sess:
            assert sess.get('selected_ticker') == 'AAPL'
            assert sess.get('company_name') == 'Apple Inc.'
    
    def test_login_logout_session_cleanup(self, client):
        """Test proper session cleanup on login/logout cycles."""
        
        # Login
        client.post('/login', data={
            'username': 'admin',
            'password': 'Admin123!'
        })
        
        # Perform analysis to populate session
        sample_data = pd.DataFrame({
            'Open': [100], 'High': [105], 'Low': [95], 'Close': [102]
        }, index=pd.date_range('2023-01-01', periods=1))
        
        with patch('modules.price_history.get_price_history') as mock_price:
            with patch('modules.price_history.get_company_name') as mock_name:
                with patch('modules.price_history.get_company_info') as mock_info:
                    with patch('modules.chart_creator.create_all_candlestick_charts') as mock_charts:
                        mock_price.return_value = sample_data
                        mock_name.return_value = "Test Company"
                        mock_info.return_value = {"sector": "Technology"}
                        mock_charts.return_value = ('chart1', 'chart2', 'chart3')
                        
                        client.post('/analyze', data={'ticker': 'TEST'})
        
        # Verify session has data
        with client.session_transaction() as sess:
            assert sess.get('selected_ticker') == 'TEST'
            assert sess.get('company_name') == 'Test Company'
        
        # Logout
        client.get('/logout')
        
        # Try to access protected page - should redirect to login
        response = client.get('/', follow_redirects=True)
        assert 'התחברות' in response.data.decode('utf-8')
        
        # Login again
        client.post('/login', data={
            'username': 'admin',
            'password': 'Admin123!'
        })
        
        # Session should be clean (no previous analysis data)
        response = client.get('/')
        with client.session_transaction() as sess:
            # Previous session data should be gone
            assert sess.get('selected_ticker') is None
            assert sess.get('company_name') is None
    
    def test_concurrent_analysis_requests(self, client, sample_stock_data):
        """Test handling of rapid consecutive analysis requests."""
        
        # Login first
        client.post('/login', data={
            'username': 'admin',
            'password': 'Admin123!'
        })
        
        tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
        companies = ['Apple Inc.', 'Microsoft Corp.', 'Alphabet Inc.', 'Tesla Inc.']
        
        # Perform multiple rapid analyses
        for ticker, company in zip(tickers, companies):
            with patch('modules.price_history.get_price_history') as mock_price:
                with patch('modules.price_history.get_company_name') as mock_name:
                    with patch('modules.price_history.get_company_info') as mock_info:
                        with patch('modules.chart_creator.create_all_candlestick_charts') as mock_charts:
                            mock_price.return_value = sample_stock_data
                            mock_name.return_value = company
                            mock_info.return_value = {"sector": "Technology"}
                            mock_charts.return_value = ('chart1', 'chart2', 'chart3')
                            
                            response = client.post('/analyze', data={
                                'ticker': ticker
                            }, follow_redirects=True)
                            
                            assert response.status_code == 200
                            assert company in response.data.decode('utf-8')
            
            # Each analysis should overwrite the previous one
            with client.session_transaction() as sess:
                assert sess.get('selected_ticker') == ticker
                assert sess.get('company_name') == company


class TestDataPersistenceWorkflows:
    """Test data persistence and file operations."""
    
    def test_user_data_persistence_across_restarts(self, temp_users_file):
        """Test that user data persists across app restarts."""
        
        # Simulate app startup with empty users file
        with patch('app.USERS_FILE', temp_users_file):
            # First startup - should create admin user
            from app import load_users
            users1 = load_users()
            
            assert len(users1) == 1
            assert users1[1].username == 'admin'
            assert users1[1].is_approved == True
        
        # Add a new user
        with patch('app.USERS_FILE', temp_users_file):
            from app import save_users, User
            users1[2] = User(2, 'testuser', generate_password_hash('testpass'), False)
            save_users(users1)
        
        # Simulate app restart - should load existing users
        with patch('app.USERS_FILE', temp_users_file):
            users2 = load_users()
            
            assert len(users2) == 2
            assert users2[1].username == 'admin'
            assert users2[2].username == 'testuser'
            assert users2[2].is_approved == False
    
    def test_corrupted_users_file_recovery(self, temp_users_file):
        """Test recovery from corrupted users file."""
        
        # Create corrupted JSON file
        with open(temp_users_file, 'w') as f:
            f.write('{"invalid": json content}')
        
        with patch('app.USERS_FILE', temp_users_file):
            from app import load_users
            users = load_users()
            
            # Should fall back to creating admin user
            assert len(users) == 1
            assert users[1].username == 'admin'
            assert users[1].is_approved == True


class TestChartGenerationWorkflows:
    """Test complete chart generation workflows."""
    
    def test_complete_chart_generation_workflow(self, client, sample_stock_data):
        """Test complete workflow from ticker input to chart display."""
        
        # Login
        client.post('/login', data={
            'username': 'admin',
            'password': 'Admin123!'
        })
        
        # Perform analysis with all chart types
        with patch('modules.price_history.get_price_history') as mock_price:
            with patch('modules.price_history.get_company_name') as mock_name:
                with patch('modules.price_history.get_company_info') as mock_info:
                    with patch('modules.chart_creator.create_all_candlestick_charts') as mock_charts:
                        mock_price.return_value = sample_stock_data
                        mock_name.return_value = "Apple Inc."
                        mock_info.return_value = {
                            "sector": "Technology",
                            "longBusinessSummary": "Apple Inc. designs consumer electronics."
                        }
                        
                        # Mock chart generation
                        daily_chart = json.dumps({"data": [{"type": "candlestick"}], "layout": {"title": "Daily"}})
                        weekly_chart = json.dumps({"data": [{"type": "candlestick"}], "layout": {"title": "Weekly"}})
                        monthly_chart = json.dumps({"data": [{"type": "candlestick"}], "layout": {"title": "Monthly"}})
                        
                        mock_charts.return_value = (daily_chart, weekly_chart, monthly_chart)
                        
                        response = client.post('/analyze', data={
                            'ticker': 'AAPL'
                        }, follow_redirects=True)
                        
                        assert response.status_code == 200
                        html = response.data.decode('utf-8')
                        
                        # Check that page contains chart data
                        assert 'Apple Inc.' in html
                        assert 'Technology' in html
                        
                        # Check session contains all chart data
                        with client.session_transaction() as sess:
                            assert sess.get('chart1_json') == daily_chart
                            assert sess.get('chart2_json') == weekly_chart
                            assert sess.get('chart3_json') == monthly_chart
        
        # Access home page again - should display persisted charts
        response = client.get('/')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert 'Apple Inc.' in html
    
    def test_chart_generation_error_handling(self, client, sample_stock_data):
        """Test chart generation with various error conditions."""
        
        client.post('/login', data={
            'username': 'admin',
            'password': 'Admin123!'
        })
        
        # Test with chart generation failure
        with patch('modules.price_history.get_price_history') as mock_price:
            with patch('modules.price_history.get_company_name') as mock_name:
                with patch('modules.price_history.get_company_info') as mock_info:
                    with patch('modules.chart_creator.create_all_candlestick_charts') as mock_charts:
                        mock_price.return_value = sample_stock_data
                        mock_name.return_value = "Apple Inc."
                        mock_info.return_value = {"sector": "Technology"}
                        mock_charts.side_effect = Exception("Chart generation failed")
                        
                        response = client.post('/analyze', data={
                            'ticker': 'AAPL'
                        }, follow_redirects=True)
                        
                        assert response.status_code == 200
                        # Should handle chart generation error gracefully
                        assert 'אירעה שגיאה בלתי צפויה בעת ניתוח הטיקר' in response.data.decode('utf-8')
                        
                        # Session should not contain invalid chart data
                        with client.session_transaction() as sess:
                            assert sess.get('chart1_json') is None