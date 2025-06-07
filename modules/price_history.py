# modules/price_history.py
import yfinance as yf
import pandas as pd
from cachetools import TTLCache, cached
from flask import current_app 
from typing import Optional, Dict # הוספנו Optional ו-Dict 
from googletrans import Translator # 1. ייבוא ספריית התרגום

# הגדרת אובייקטי הקאש
price_data_cache = TTLCache(maxsize=100, ttl=43000)  # 12 שעות
company_name_cache = TTLCache(maxsize=200, ttl=3600) # שעה 
company_info_cache = TTLCache(maxsize=200, ttl=3600) # קאש גם למידע כללי על החברה

# 2. פונקציית התרגום
def translate_text_to_hebrew(text_to_translate: Optional[str]) -> Optional[str]:
    if not text_to_translate:
        current_app.logger.debug("translate_text_to_hebrew: No text provided for translation.")
        return None
    try:
        translator = Translator()
        # ניסיון לזהות את שפת המקור, אך אם אנחנו יודעים שהיא אנגלית, אפשר לציין src='en'
        translation_result = translator.translate(text_to_translate, dest='he') # תרגום לעברית
        if translation_result and translation_result.text:
            current_app.logger.info(f"Text translated from '{translation_result.src}' to Hebrew successfully.")
            return translation_result.text
        else:
            current_app.logger.warning("Translation attempt returned no text.")
            return None # או החזר את הטקסט המקורי
    except Exception as e:
        current_app.logger.error(f"Error during translation: {str(e)}")
        current_app.logger.exception("Detailed traceback for translation error:")
        return None # או החזר את הטקסט המקורי במקרה של שגיאה


def _make_price_cache_key(ticker_symbol, period, interval):
    key = (str(ticker_symbol).upper(), str(period), str(interval))
    # current_app.logger.debug(f"Generated price_data_cache key: {key}")
    return key

@cached(cache=price_data_cache, key=lambda ticker_symbol, period, interval: _make_price_cache_key(ticker_symbol, period, interval))
def get_price_history(ticker_symbol, period, interval) -> pd.DataFrame: # הוספתי type hint לערך המוחזר
    # הלוג הבא ירוץ רק אם הפונקציה המעוטרת נקראת (כלומר, אין HIT בקאש או שה-TTL עבר)
    current_app.logger.info(f"CACHE MISS/EXPIRED for price data: {ticker_symbol} (P:{period}, I:{interval}). Fetching FRESH from yfinance...")
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            current_app.logger.warning(f"No price data returned by yfinance for {ticker_symbol} (P:{period}, I:{interval})")
            return pd.DataFrame() 
            
        required_columns = ['Open', 'High', 'Low', 'Close'] 
        missing_columns = [col for col in required_columns if col not in hist.columns]
        if missing_columns:
            current_app.logger.error(f"Missing required columns {missing_columns} in price data for {ticker_symbol} (P:{period}, I:{interval}). Available columns: {list(hist.columns)}")
            return pd.DataFrame() 
            
        current_app.logger.info(f"Successfully fetched price data for {ticker_symbol} (P:{period}, I:{interval}). Rows: {len(hist)}")
        return hist
        
    except Exception as e:
        current_app.logger.error(f"Error fetching price data for {ticker_symbol} (P:{period}, I:{interval}) with yfinance: {str(e)}")
        current_app.logger.exception("Detailed traceback for get_price_history error:")
        return pd.DataFrame()

@cached(cache=company_name_cache)
def get_company_name(ticker_symbol: str) -> str:
    current_app.logger.info(f"CACHE MISS/EXPIRED for company name: '{ticker_symbol}'. Fetching FRESH from yfinance...")
    try:
        ticker_info = yf.Ticker(ticker_symbol).info
        name = ticker_info.get('longName', ticker_info.get('shortName', ticker_symbol))
        if not name or name == ticker_symbol and ('longName' in ticker_info or 'shortName' in ticker_info) : 
             current_app.logger.warning(f"Company name from yfinance for '{ticker_symbol}' was empty or effectively same as ticker ('{name}'). Using ticker symbol as name.")
             name = ticker_symbol
        elif name: 
             current_app.logger.info(f"Successfully fetched company name for '{ticker_symbol}': '{name}'")
        else: 
             current_app.logger.warning(f"Could not determine company name for '{ticker_symbol}'. Defaulting to ticker symbol.")
             name = ticker_symbol
        return name
    except Exception as e:
        current_app.logger.error(f"Error fetching company name for '{ticker_symbol}' with yfinance: {str(e)}")
        current_app.logger.exception(f"Detailed traceback for get_company_name error (ticker: {ticker_symbol}):")
        return ticker_symbol

@cached(cache=company_info_cache)
def get_company_info(ticker_symbol: str) -> Optional[Dict[str, Optional[str]]]: # עדכון Type Hint
    current_app.logger.info(f"Attempting to get_company_info for '{ticker_symbol}'.")
    # הלוג הבא ירוץ רק אם הפונקציה המעוטרת נקראת
    current_app.logger.info(f"CACHE MISS/EXPIRED for company info: '{ticker_symbol}'. Fetching FRESH from yfinance...")
    try:
        ticker_obj = yf.Ticker(ticker_symbol)
        info = ticker_obj.info
        if not info: 
            current_app.logger.warning(f"No company info dictionary returned by yfinance for '{ticker_symbol}'")
            return { # החזר מילון ברירת מחדל כדי שהתבנית לא תישבר
                "name": ticker_symbol, "description": "N/A", "description_he": "אין מידע זמין", 
                "sector": "N/A", "industry": "N/A", "website": "N/A"
            }
        
        english_description = info.get("longBusinessSummary")
        hebrew_description = None

        if english_description:
            # 3. קריאה לפונקציית התרגום
            hebrew_description = translate_text_to_hebrew(english_description)
            if not hebrew_description: # אם התרגום נכשל או החזיר None, נשתמש בטקסט חלופי
                hebrew_description = "לא ניתן היה לתרגם את התיאור."
        else:
            current_app.logger.info(f"No English description found for {ticker_symbol} to translate.")
            english_description = "No description available." # טקסט ברירת מחדל
            hebrew_description = "אין תיאור זמין."
            
        company_details: Dict[str, Optional[str]] = {
            "name": info.get("longName", info.get("shortName", ticker_symbol)),
            "description": english_description, 
            "description_he": hebrew_description, # הוספת השדה המתורגם
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "website": info.get("website"),
        }
        
        # סינון ערכי None מהמילון הסופי אם רוצים, אבל עדיף להשאיר אותם כ-None
        # מאשר למחוק את המפתח, כי התבנית עשויה לצפות למפתח.
        # company_details_filtered = {k: v for k, v in company_details.items() if v is not None}
        # הפכתי את זה להערה, כי עדיף שהמפתחות תמיד יהיו קיימים והערך יהיה None אם אין מידע

        current_app.logger.info(f"Successfully fetched and processed company info for '{ticker_symbol}'.")
        return company_details
        
    except Exception as e:
        current_app.logger.error(f"Error fetching company info for '{ticker_symbol}' with yfinance: {str(e)}")
        current_app.logger.exception(f"Detailed traceback for get_company_info error (ticker: {ticker_symbol}):")
        return { # החזר מילון ברירת מחדל במקרה של שגיאה
            "name": ticker_symbol, "description": "Error retrieving description.", "description_he": "שגיאה בקבלת התיאור.",
            "sector": "N/A", "industry": "N/A", "website": "N/A"
        }