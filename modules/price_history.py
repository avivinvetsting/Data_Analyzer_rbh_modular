# modules/price_history.py
import yfinance as yf
import pandas as pd
from cachetools import TTLCache, cached # 1. ייבוא הרכיבים הנדרשים מ-cachetools

# 2. הגדרת אובייקטי הקאש
# קאש לנתוני מחירים: מקסימום 100 פריטים, כל פריט נשמר ל-15 דקות (900 שניות)
price_data_cache = TTLCache(maxsize=100, ttl=900)
# קאש לשמות חברות: מקסימום 200 פריטים, כל פריט נשמר לשעה (3600 שניות)
company_name_cache = TTLCache(maxsize=200, ttl=3600)

# 3. פונקציית עזר ליצירת מפתח קאש דינמי לנתוני מחירים
# (מכיוון שהתוצאה תלויה בטיקר, תקופה ואינטרוול)
def _make_price_cache_key(ticker_symbol, period, interval):
    return (str(ticker_symbol).upper(), str(period), str(interval))

# 4. הוספת ה-decorator @cached לפונקציות
@cached(cache=price_data_cache, key=lambda ticker_symbol, period, interval: _make_price_cache_key(ticker_symbol, period, interval))
def get_price_history(ticker_symbol, period, interval):
    """
    Downloads historical price data for a given ticker, period, and interval.
    Results are cached.
    """
    # הדפסה לצורך בדיקה מתי הנתונים נטענים מ-yfinance (ולא מהקאש)
    print(f"CACHE MISS: Fetching FRESH price data for {ticker_symbol} ({period}, {interval}) from yfinance...")
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=period, interval=interval)
        if hist.empty:
            print(f"No data returned by yfinance for {ticker_symbol} ({period}, {interval})")
            # שקול אם לשמור גם DataFrame ריק בקאש כדי למנוע קריאות חוזרות ונשנות לטיקר שלא מחזיר נתונים
        return hist
    except Exception as e:
        print(f"Error fetching price data for {ticker_symbol} with yfinance: {e}")
        return pd.DataFrame() # החזר DataFrame ריק במקרה של שגיאה

@cached(cache=company_name_cache) # כאן, מפתח הקאש ייווצר אוטומטית מהארגומנטים (ticker_symbol)
def get_company_name(ticker_symbol):
    """
    Gets company name using yfinance. Results are cached.
    """
    # הדפסה לצורך בדיקה מתי הנתונים נטענים מ-yfinance (ולא מהקאש)
    print(f"CACHE MISS: Fetching FRESH company name for {ticker_symbol} from yfinance...")
    try:
        ticker_info = yf.Ticker(ticker_symbol).info
        name = ticker_info.get('longName', ticker_info.get('shortName', ticker_symbol))
        if not name: # אם yfinance החזיר שם ריק
            return ticker_symbol # חזור לטיקר כברירת מחדל
        return name
    except Exception as e:
        print(f"Error fetching company name for {ticker_symbol} with yfinance: {e}")
        return ticker_symbol # חזור לטיקר כברירת מחדל במקרה של שגיאה