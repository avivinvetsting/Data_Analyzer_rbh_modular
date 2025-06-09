# app/utils.py
"""
Utility functions for the Data Analyzer application.

This module contains shared utility functions that can be used across
different blueprints and modules in the application.
"""

import re
from flask import session, current_app, request
from typing import Optional
from werkzeug.exceptions import BadRequest
import re
import html
import unicodedata


def validate_ticker_symbol(ticker: str) -> bool:
    """
    Validate stock ticker symbol format.
    
    Ticker symbols should contain only:
    - Letters (A-Z)
    - Numbers (0-9) 
    - Periods (.)
    - Hyphens (-)
    - Carets (^)
    
    Args:
        ticker (str): Ticker symbol to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not ticker or not isinstance(ticker, str):
        return False
    
    # Check length (1-12 characters is typical for stock symbols)
    if len(ticker) < 1 or len(ticker) > 12:
        return False
    
    # Check format using regex
    if not re.match(r'^[A-Z0-9.\-^]+$', ticker.upper()):
        return False
    
    return True


def sanitize_ticker_symbol(ticker: str) -> Optional[str]:
    """
    Sanitize and normalize ticker symbol input.
    
    Args:
        ticker (str): Raw ticker symbol input
        
    Returns:
        str or None: Sanitized ticker symbol or None if invalid
    """
    if not ticker:
        return None
    
    # Remove whitespace and convert to uppercase
    cleaned = ticker.strip().upper()
    
    # Validate the cleaned ticker
    if validate_ticker_symbol(cleaned):
        return cleaned
    
    return None


def format_currency(amount: float, currency: str = 'USD') -> str:
    """
    Format currency amounts for display.
    
    Args:
        amount (float): Amount to format
        currency (str): Currency code (default: USD)
        
    Returns:
        str: Formatted currency string
    """
    try:
        if currency.upper() == 'USD':
            return f"${amount:,.2f}"
        elif currency.upper() == 'ILS':
            return f"₪{amount:,.2f}"
        else:
            return f"{amount:,.2f} {currency}"
    except (ValueError, TypeError):
        return f"N/A {currency}"


def format_percentage(value: float, decimal_places: int = 2) -> str:
    """
    Format percentage values for display.
    
    Args:
        value (float): Percentage value (e.g., 0.05 for 5%)
        decimal_places (int): Number of decimal places
        
    Returns:
        str: Formatted percentage string
    """
    try:
        percentage = value * 100
        return f"{percentage:.{decimal_places}f}%"
    except (ValueError, TypeError):
        return "N/A%"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length with optional suffix.
    
    Args:
        text (str): Text to truncate
        max_length (int): Maximum length before truncation
        suffix (str): Suffix to add when truncated
        
    Returns:
        str: Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def log_user_action(action: str, details: str = "", user_id: Optional[int] = None) -> None:
    """
    Log user actions with consistent formatting.
    
    Args:
        action (str): Action performed (e.g., "login", "analyze_stock")
        details (str): Additional details about the action
        user_id (int, optional): User ID performing the action
    """
    log_message = f"USER_ACTION: {action}"
    
    if user_id:
        log_message += f" (User ID: {user_id})"
    
    if details:
        log_message += f" - {details}"
    
    current_app.logger.info(log_message)


def safe_get_nested_dict(data: dict, keys: list, default=None):
    """
    Safely get value from nested dictionary.
    
    Args:
        data (dict): Dictionary to search
        keys (list): List of keys for nested access
        default: Default value if key path doesn't exist
        
    Returns:
        Value at key path or default value
    """
    try:
        result = data
        for key in keys:
            result = result[key]
        return result
    except (KeyError, TypeError):
        return default


def calculate_moving_average(data: list, window: int) -> list:
    """
    Calculate simple moving average for a list of values.
    
    Args:
        data (list): List of numeric values
        window (int): Window size for moving average
        
    Returns:
        list: Moving averages (shorter than input by window-1)
    """
    if len(data) < window:
        return []
    
    moving_averages = []
    for i in range(window - 1, len(data)):
        window_data = data[i - window + 1:i + 1]
        avg = sum(window_data) / window
        moving_averages.append(avg)
    
    return moving_averages


def get_client_ip() -> str:
    """
    Get client IP address from Flask request, handling proxies.
    
    Returns:
        str: Client IP address
    """
    from flask import request
    
    # Check for forwarded headers (proxy/load balancer)
    if 'X-Forwarded-For' in request.headers:
        # X-Forwarded-For can contain multiple IPs, first one is original client
        return request.headers['X-Forwarded-For'].split(',')[0].strip()
    elif 'X-Real-IP' in request.headers:
        return request.headers['X-Real-IP']
    else:
        return request.remote_addr or 'Unknown'


def is_market_hours() -> bool:
    """
    Check if current time is during market hours (US Eastern Time).
    
    Note: This is a simplified check. For production use, consider
    using a proper market calendar library like pandas_market_calendars.
    
    Returns:
        bool: True if during market hours, False otherwise
    """
    from datetime import datetime
    import pytz
    
    try:
        # Get current time in US Eastern timezone
        eastern = pytz.timezone('US/Eastern')
        now = datetime.now(eastern)
        
        # Check if it's a weekday (Monday=0, Sunday=6)
        if now.weekday() > 4:  # Saturday=5, Sunday=6
            return False
        
        # Check if it's between 9:30 AM and 4:00 PM ET
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return market_open <= now <= market_close
        
    except Exception as e:
        current_app.logger.warning(f"Error checking market hours: {e}")
        return False  # Conservative default


def clear_session_data():
    """
    Clear custom session data while preserving Flask-Login state.
    
    Removes all custom application data from the session
    but keeps the Flask-Login authentication information.
    """
    login_preserved_keys = ['_user_id', '_remember', '_fresh', '_id']
    
    # Get keys to clear (all except Flask-Login keys)
    keys_to_clear = [k for k in session.keys() if k not in login_preserved_keys]
    
    # Remove each key
    for key in keys_to_clear:
        session.pop(key, None)
    
    current_app.logger.debug(f"Cleared {len(keys_to_clear)} custom session keys")


# Constants for ticker validation
TICKER_MIN_LENGTH = 1
TICKER_MAX_LENGTH = 12
TICKER_VALID_PATTERN = re.compile(r"^[A-Za-z0-9.\-^]+$")


def sanitize_ticker(ticker_input):
    """
    Sanitize and normalize ticker symbol input.
    
    Args:
        ticker_input (str): Raw ticker symbol input
        
    Returns:
        str: Sanitized ticker symbol
    """
    processed_ticker = ticker_input.strip()
    processed_ticker = unicodedata.normalize('NFKD', processed_ticker).encode('ASCII', 'ignore').decode('ASCII')
    return processed_ticker


def validate_ticker(raw_ticker_input):
    """
    Validate ticker symbol format.
    
    Checks for empty input, invalid characters, and length constraints.
    Returns the ticker in uppercase and HTML-escaped if valid.
    
    Args:
        raw_ticker_input (str): Raw ticker input to validate
        
    Returns:
        str: Validated and normalized ticker symbol
        
    Raises:
        BadRequest: If validation fails with appropriate error message
    """
    if not raw_ticker_input:
        raise BadRequest('אנא הזן סימול טיקר.')

    # Remove whitespace from start and end
    processed_ticker = raw_ticker_input.strip()

    if not processed_ticker:
        raise BadRequest('אנא הזן סימול טיקר.')

    # Check valid characters pattern
    if not TICKER_VALID_PATTERN.match(processed_ticker):
        raise BadRequest('הסימול יכול להכיל רק אותיות באנגלית, ספרות, נקודה (.), מקף (-), או גג (^).')

    # Check length constraints
    if not (TICKER_MIN_LENGTH <= len(processed_ticker) <= TICKER_MAX_LENGTH):
        raise BadRequest(f'אורך הסימול חייב להיות בין {TICKER_MIN_LENGTH} ל-{TICKER_MAX_LENGTH} תווים.')

    # Convert to uppercase and escape HTML
    return html.escape(processed_ticker.upper())
