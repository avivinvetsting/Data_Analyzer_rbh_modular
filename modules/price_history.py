# modules/price_history.py
import yfinance as yf
import pandas as pd
from cachetools import TTLCache, cached
from flask import current_app 

price_data_cache = TTLCache(maxsize=100, ttl=43000) 
company_name_cache = TTLCache(maxsize=200, ttl=3600)

def _make_price_cache_key(ticker_symbol, period, interval):
    key = (str(ticker_symbol).upper(), str(period), str(interval))
    return key

@cached(cache=price_data_cache, key=lambda ticker_symbol, period, interval: _make_price_cache_key(ticker_symbol, period, interval))
def get_price_history(ticker_symbol, period, interval):
    # ההודעה הזו תירשם תמיד, גם אם הנתונים נלקחים מהקאש, כדי שנדע שהפונקציה נקראה.
    # אם רוצים לדעת רק על CACHE MISS, נצטרך להוסיף את הלוג בתוך הלוגיקה של הפונקציה המקורית (לפני ה-return).
    # כרגע, נשאיר את זה כך שההודעה הבאה היא על CACHE MISS בפועל.
    # current_app.logger.debug(f"get_price_history called for {ticker_symbol} (P:{period}, I:{interval}). Checking cache.")
    
    # הלוג הבא צריך להיות בתוך הפונקציה המקורית כדי לדעת אם זה באמת CACHE MISS.
    # לצורך הדוגמה, נניח שאנחנו רוצים לדעת כל פעם ש-yf.Ticker נקרא.
    current_app.logger.info(f"Attempting to fetch/retrieve price history for {ticker_symbol} (P:{period}, I:{interval}).")
    # אם cachetools היה מאפשר hook פשוט ל-on_miss, היינו שמים שם את הלוג של CACHE MISS.
    # כרגע, הלוג יופיע גם אם זה מגיע מהקאש, אלא אם נעטוף את הקריאה ל-yfinance בלוג נפרד.
    # בפועל, ההודעה "CACHE MISS or EXPIRED" תופיע רק כשהפונקציה המעוטרת רצה בפועל.
    # אז אם @cached מחזיר ערך שמור, ההודעה למטה לא תרוץ.

    # כדי לדמות את הלוג של CACHE MISS בצורה מדויקת יותר, נוסיף בדיקה האם המפתח בקאש
    cache_key = _make_price_cache_key(ticker_symbol, period, interval)
    if cache_key not in price_data_cache: # או אם רוצים לבדוק גם תפוגה, זה יותר מורכב עם cachetools ישירות
        current_app.logger.info(f"CACHE MISS/EXPIRED for price data: {ticker_symbol} (P:{period}, I:{interval}). Fetching FRESH from yfinance...")
    else:
        current_app.logger.info(f"CACHE HIT for price data: {ticker_symbol} (P:{period}, I:{interval}).")

    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=period, interval=interval)
        if hist.empty:
            current_app.logger.warning(f"No price data returned by yfinance for {ticker_symbol} (P:{period}, I:{interval})")
        else:
            current_app.logger.info(f"Successfully fetched/retrieved price data for {ticker_symbol} (P:{period}, I:{interval}). Rows: {len(hist)}")
        return hist
    except Exception as e:
        current_app.logger.error(f"Error fetching price data for {ticker_symbol} (P:{period}, I:{interval}) with yfinance: {str(e)}")
        return pd.DataFrame()

@cached(cache=company_name_cache)
def get_company_name(ticker_symbol):
    # current_app.logger.debug(f"get_company_name called for '{ticker_symbol}'. Checking cache.")
    cache_key = (str(ticker_symbol).upper(),) # מפתח קאש פשוט יותר לשם חברה
    if cache_key not in company_name_cache:
        current_app.logger.info(f"CACHE MISS/EXPIRED for company name: '{ticker_symbol}'. Fetching FRESH from yfinance...")
    else:
        current_app.logger.info(f"CACHE HIT for company name: '{ticker_symbol}'.")
        
    try:
        ticker_info = yf.Ticker(ticker_symbol).info
        name = ticker_info.get('longName', ticker_info.get('shortName', ticker_symbol))
        if not name or name == ticker_symbol:
            current_app.logger.warning(f"Company name from yfinance for '{ticker_symbol}' was empty or same as ticker. Using ticker symbol as name.")
            name = ticker_symbol
        else:
            current_app.logger.info(f"Successfully fetched/retrieved company name for '{ticker_symbol}': '{name}'")
        return name
    except Exception as e:
        current_app.logger.error(f"Error fetching company name for '{ticker_symbol}' with yfinance: {str(e)}")
        current_app.logger.warning(f"Returning ticker symbol '{ticker_symbol}' as fallback company name due to error.")
        return ticker_symbol