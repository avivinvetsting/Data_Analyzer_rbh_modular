# modules/price_history.py
import yfinance as yf
import pandas as pd
from cachetools import TTLCache, cached
from flask import current_app 
from typing import Optional, Dict # הוספנו Optional ו-Dict (למרות ש-Dict לא חובה כאן אם משתמשים ב-dict רגיל)


price_data_cache = TTLCache(maxsize=100, ttl=43000) 
company_name_cache = TTLCache(maxsize=200, ttl=3600)
# הוספתי קאש גם ל-company_info כפי שעשינו בדיונים קודמים
company_info_cache = TTLCache(maxsize=200, ttl=3600) 

def _make_price_cache_key(ticker_symbol, period, interval):
    key = (str(ticker_symbol).upper(), str(period), str(interval))
    # current_app.logger.debug(f"Generated price_data_cache key: {key}") # אפשר להפעיל לדיבאג של הקאש
    return key

@cached(cache=price_data_cache, key=lambda ticker_symbol, period, interval: _make_price_cache_key(ticker_symbol, period, interval))
def get_price_history(ticker_symbol, period, interval):
    # הלוג הבא ירוץ רק אם הפונקציה המעוטרת נקראת (כלומר, אין HIT בקאש או שה-TTL עבר)
    current_app.logger.info(f"CACHE MISS/EXPIRED for price data: {ticker_symbol} (P:{period}, I:{interval}). Fetching FRESH from yfinance...")
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            current_app.logger.warning(f"No price data returned by yfinance for {ticker_symbol} (P:{period}, I:{interval})")
            return pd.DataFrame() # החזר DataFrame ריק
            
        required_columns = ['Open', 'High', 'Low', 'Close'] # עמודות חובה
        missing_columns = [col for col in required_columns if col not in hist.columns]
        if missing_columns:
            current_app.logger.error(f"Missing required columns {missing_columns} in price data for {ticker_symbol} (P:{period}, I:{interval}). Available columns: {list(hist.columns)}")
            return pd.DataFrame() # החזר DataFrame ריק
            
        # בדיקה נוספת לערכים חסרים או לא חיוביים יכולה להתבצע כאן אם רוצים, כפי שהיה בקובץ הקודם שלך.
        # כרגע, נשאיר את זה כך כדי לשמור על פשטות יחסית, בהנחה ש-yfinance מחזיר נתונים נקיים יחסית.
        # אם אתה רואה בעיות עם ערכים כאלה, נוכל להוסיף את הולידציות האלה בחזרה.

        current_app.logger.info(f"Successfully fetched price data for {ticker_symbol} (P:{period}, I:{interval}). Rows: {len(hist)}")
        return hist
        
    except Exception as e:
        current_app.logger.error(f"Error fetching price data for {ticker_symbol} (P:{period}, I:{interval}) with yfinance: {str(e)}")
        current_app.logger.exception("Detailed traceback for get_price_history error:") # רושם את ה-traceback
        return pd.DataFrame()

@cached(cache=company_name_cache)
def get_company_name(ticker_symbol: str) -> str:
    # הלוג הבא ירוץ רק אם הפונקציה המעוטרת נקראת
    current_app.logger.info(f"CACHE MISS/EXPIRED for company name: '{ticker_symbol}'. Fetching FRESH from yfinance...")
    try:
        ticker_info = yf.Ticker(ticker_symbol).info
        name = ticker_info.get('longName', ticker_info.get('shortName', ticker_symbol))
        if not name or name == ticker_symbol and ('longName' in ticker_info or 'shortName' in ticker_info) : # אם השם הוא הטיקר, אבל היה שם אחר זמין
             current_app.logger.warning(f"Company name from yfinance for '{ticker_symbol}' was empty or effectively same as ticker ('{name}'). Using ticker symbol as name.")
             name = ticker_symbol
        elif name: # אם name מכיל ערך והוא שונה מהטיקר (או שזה כל מה שיש)
             current_app.logger.info(f"Successfully fetched company name for '{ticker_symbol}': '{name}'")
        else: # מקרה קצה, אם name הוא None או ריק אחרי הכל
             current_app.logger.warning(f"Could not determine company name for '{ticker_symbol}'. Defaulting to ticker symbol.")
             name = ticker_symbol
        return name
    except Exception as e:
        current_app.logger.error(f"Error fetching company name for '{ticker_symbol}' with yfinance: {str(e)}")
        current_app.logger.exception(f"Detailed traceback for get_company_name error (ticker: {ticker_symbol}):")
        return ticker_symbol

@cached(cache=company_info_cache) # הוספת קאש גם לפונקציה זו
def get_company_info(ticker_symbol: str) -> Optional[dict]:
    current_app.logger.info(f"Attempting to get_company_info for '{ticker_symbol}'.")
    # הלוג הבא ירוץ רק אם הפונקציה המעוטרת נקראת
    current_app.logger.info(f"CACHE MISS/EXPIRED for company info: '{ticker_symbol}'. Fetching FRESH from yfinance...")
    try:
        ticker_obj = yf.Ticker(ticker_symbol)
        info = ticker_obj.info
        if not info: # אם המילון info ריק
            current_app.logger.warning(f"No company info dictionary returned by yfinance for '{ticker_symbol}'")
            return None # או החזר מילון ריק עם ערכי ברירת מחדל
        
        company_details = {
            "name": info.get("longName", info.get("shortName", ticker_symbol)), # ודא שיש שם גם כאן
            "description": info.get("longBusinessSummary"), # נסה longBusinessSummary, אם לא קיים יחזיר None
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "website": info.get("website"),
        }
        # הסר מפתחות עם ערכי None אם אתה מעדיף שהם לא יופיעו
        company_details = {k: v for k, v in company_details.items() if v is not None}

        if not any(company_details.values()): # אם כל הערכים הם None או ריקים (אחרי הסינון)
            current_app.logger.warning(f"Company info for '{ticker_symbol}' resulted in all empty fields.")
            # אפשר להחזיר None או את המילון כפי שהוא
        else:
            current_app.logger.info(f"Successfully fetched company info for '{ticker_symbol}'.")
        return company_details
    except Exception as e:
        current_app.logger.error(f"Error fetching company info for '{ticker_symbol}' with yfinance: {str(e)}")
        current_app.logger.exception(f"Detailed traceback for get_company_info error (ticker: {ticker_symbol}):")
        # החזר מילון עם ערכי ברירת מחדל כדי שהתבנית לא תישבר אם היא מצפה למפתחות מסוימים
        return {
            "name": ticker_symbol, "description": "N/A", "sector": "N/A", "industry": "N/A", "website": "N/A"
        }