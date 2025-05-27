import yfinance as yf
import pandas as pd

def get_price_history(ticker_symbol, period, interval):
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=period, interval=interval)
        if hist.empty:
            print(f"No data returned for {ticker_symbol} with period={period}, interval={interval}")
        return hist
    except Exception as e:
        print(f"Error fetching data for {ticker_symbol} with yfinance: {e}")
        return pd.DataFrame()

def get_company_name(ticker_symbol):
    try:
        ticker_info = yf.Ticker(ticker_symbol).info
        return ticker_info.get('longName', ticker_info.get('shortName', ticker_symbol))
    except Exception:
        return ticker_symbol