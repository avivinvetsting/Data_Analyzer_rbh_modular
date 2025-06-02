#!/usr/bin/env python3
"""
Simple test runner to verify basic functionality without pytest dependency.
This script performs basic smoke tests to ensure the application works.
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_tests():
    """Run basic tests to verify application functionality."""
    print("="*60)
    print("RUNNING BASIC APPLICATION TESTS")
    print("="*60)
    
    tests_passed = 0
    tests_failed = 0
    
    def test_result(test_name, success, error_msg=None):
        nonlocal tests_passed, tests_failed
        if success:
            print(f"✓ {test_name}")
            tests_passed += 1
        else:
            print(f"✗ {test_name}: {error_msg}")
            tests_failed += 1
    
    # Test 1: Import basic modules
    try:
        import app
        test_result("Import app module", True)
    except Exception as e:
        test_result("Import app module", False, str(e))
        return tests_passed, tests_failed
    
    # Test 2: Check Flask app creation
    try:
        flask_app = app.app
        assert flask_app is not None
        test_result("Flask app creation", True)
    except Exception as e:
        test_result("Flask app creation", False, str(e))
    
    # Test 3: Test basic configuration
    try:
        assert hasattr(flask_app, 'secret_key')
        assert flask_app.secret_key is not None
        test_result("App configuration", True)
    except Exception as e:
        test_result("App configuration", False, str(e))
    
    # Test 4: Import route modules
    try:
        from modules.routes import home
        test_result("Import home routes", True)
    except Exception as e:
        test_result("Import home routes", False, str(e))
    
    try:
        from modules.routes import graphs
        test_result("Import graphs routes", True)
    except Exception as e:
        test_result("Import graphs routes", False, str(e))
    
    try:
        from modules.routes import valuations
        test_result("Import valuations routes", True)
    except Exception as e:
        test_result("Import valuations routes", False, str(e))
    
    # Test 5: Import data modules
    try:
        import modules.price_history as price_history
        test_result("Import price_history module", True)
    except Exception as e:
        test_result("Import price_history module", False, str(e))
    
    try:
        import modules.chart_creator as chart_creator
        test_result("Import chart_creator module", True)
    except Exception as e:
        test_result("Import chart_creator module", False, str(e))
    
    try:
        import modules.data_fetcher as data_fetcher
        test_result("Import data_fetcher module", True)
    except Exception as e:
        test_result("Import data_fetcher module", False, str(e))
    
    # Test 6: Check user management functions
    try:
        assert hasattr(app, 'load_users')
        assert hasattr(app, 'save_users')
        assert hasattr(app, 'User')
        test_result("User management functions", True)
    except Exception as e:
        test_result("User management functions", False, str(e))
    
    # Test 7: Test basic Flask test client
    try:
        with flask_app.test_client() as client:
            response = client.get('/login')
            assert response.status_code == 200
            test_result("Login page accessibility", True)
    except Exception as e:
        test_result("Login page accessibility", False, str(e))
    
    # Test 8: Test register page
    try:
        with flask_app.test_client() as client:
            response = client.get('/register')
            assert response.status_code == 200
            test_result("Register page accessibility", True)
    except Exception as e:
        test_result("Register page accessibility", False, str(e))
    
    # Test 9: Test protected route without authentication
    try:
        with flask_app.test_client() as client:
            response = client.get('/', follow_redirects=False)
            # Should redirect to login (302) or require authentication
            assert response.status_code in [302, 401, 403]
            test_result("Protected route security", True)
    except Exception as e:
        test_result("Protected route security", False, str(e))
    
    # Test 10: Test invalid route (404)
    try:
        with flask_app.test_client() as client:
            response = client.get('/nonexistent-page')
            assert response.status_code == 404
            test_result("404 error handling", True)
    except Exception as e:
        test_result("404 error handling", False, str(e))
    
    # Test 11: Test user creation functionality
    try:
        user = app.User(1, 'testuser', 'hashedpass', True)
        assert user.id == 1
        assert user.username == 'testuser'
        assert user.is_approved == True
        test_result("User object creation", True)
    except Exception as e:
        test_result("User object creation", False, str(e))
    
    # Test 12: Test ticker validation pattern
    try:
        import re
        from modules.routes.home import TICKER_VALID_PATTERN
        
        # Valid tickers
        valid_tickers = ['AAPL', 'BRK.A', 'BRK-A', 'SPY^A', 'TEST123']
        for ticker in valid_tickers:
            assert TICKER_VALID_PATTERN.match(ticker), f"Valid ticker {ticker} failed validation"
        
        # Invalid tickers
        invalid_tickers = ['aapl', 'AAPL@', 'AAPL#', 'AAPL$']
        for ticker in invalid_tickers:
            assert not TICKER_VALID_PATTERN.match(ticker), f"Invalid ticker {ticker} passed validation"
        
        test_result("Ticker validation pattern", True)
    except Exception as e:
        test_result("Ticker validation pattern", False, str(e))
    
    print("="*60)
    print(f"RESULTS: {tests_passed} passed, {tests_failed} failed")
    print("="*60)
    
    return tests_passed, tests_failed

def test_modules_individually():
    """Test individual modules for basic functionality."""
    print("\n" + "="*60)
    print("TESTING INDIVIDUAL MODULES")
    print("="*60)
    
    module_tests_passed = 0
    module_tests_failed = 0
    
    def module_test_result(test_name, success, error_msg=None):
        nonlocal module_tests_passed, module_tests_failed
        if success:
            print(f"✓ {test_name}")
            module_tests_passed += 1
        else:
            print(f"✗ {test_name}: {error_msg}")
            module_tests_failed += 1
    
    # Test price_history module
    try:
        import modules.price_history as ph
        
        # Test cache objects exist
        assert hasattr(ph, 'price_data_cache')
        assert hasattr(ph, 'company_name_cache')
        assert hasattr(ph, 'company_info_cache')
        
        # Test functions exist
        assert callable(ph.get_price_history)
        assert callable(ph.get_company_name)
        assert callable(ph.get_company_info)
        
        module_test_result("Price history module structure", True)
    except Exception as e:
        module_test_result("Price history module structure", False, str(e))
    
    # Test chart_creator module
    try:
        import modules.chart_creator as cc
        
        # Test functions exist
        assert callable(cc.resample_ohlc)
        assert callable(cc.create_candlestick_chart)
        assert callable(cc.create_all_candlestick_charts)
        
        module_test_result("Chart creator module structure", True)
    except Exception as e:
        module_test_result("Chart creator module structure", False, str(e))
    
    # Test data_fetcher module
    try:
        import modules.data_fetcher as df
        
        # Test functions exist
        assert callable(df.get_stock_data)
        
        module_test_result("Data fetcher module structure", True)
    except Exception as e:
        module_test_result("Data fetcher module structure", False, str(e))
    
    print(f"Module tests: {module_tests_passed} passed, {module_tests_failed} failed")
    
    return module_tests_passed, module_tests_failed

def main():
    """Main test runner function."""
    print("Simple Test Runner for Data Analyzer Flask Application")
    print("This script performs basic smoke tests without external dependencies.")
    print()
    
    # Run basic tests
    basic_passed, basic_failed = run_tests()
    
    # Run module tests
    module_passed, module_failed = test_modules_individually()
    
    # Summary
    total_passed = basic_passed + module_passed
    total_failed = basic_failed + module_failed
    total_tests = total_passed + total_failed
    
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    print(f"Total tests run: {total_tests}")
    print(f"Tests passed: {total_passed}")
    print(f"Tests failed: {total_failed}")
    
    if total_failed == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("The application appears to be working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total_failed} TESTS FAILED")
        print("There are issues that need to be addressed.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)