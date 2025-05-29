import yfinance as yf
from flask import current_app
import pandas as pd

def get_stock_data(ticker):
    """
    Fetch stock data for the given ticker.
    Returns a DataFrame with OHLC data or None if there's an error.
    """
    current_app.logger.info(f"Fetching stock data for ticker: {ticker}")
    
    try:
        # Fetch data from yfinance
        current_app.logger.info("Fetching data from yfinance...")
        stock = yf.Ticker(ticker)
        df = stock.history(period="5y")
        
        if df is None or df.empty:
            current_app.logger.error("No data received from yfinance")
            return None
            
        current_app.logger.info(f"Received data from yfinance. Shape: {df.shape}")
        current_app.logger.info(f"Data columns: {df.columns.tolist()}")
        current_app.logger.info(f"Data types:\n{df.dtypes}")
        current_app.logger.info(f"First few rows:\n{df.head().to_string()}")
        
        # Validate required columns
        required_columns = ['Open', 'High', 'Low', 'Close']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            current_app.logger.error(f"Missing required columns: {missing_columns}")
            return None
            
        # Check for missing values
        missing_values = df[required_columns].isnull().sum()
        if missing_values.any():
            current_app.logger.warning(f"Missing values found:\n{missing_values}")
            df = df.dropna(subset=required_columns)
            if df.empty:
                current_app.logger.error("No valid data after removing missing values")
                return None
                
        # Check for invalid values
        for col in required_columns:
            if (df[col] <= 0).any():
                current_app.logger.error(f"Found non-positive values in {col} column")
                return None
                
        # Sort by date
        df = df.sort_index()
        
        current_app.logger.info("Successfully processed stock data")
        return df
        
    except Exception as e:
        current_app.logger.error(f"Error fetching stock data: {str(e)}")
        current_app.logger.exception("Detailed traceback:")
        return None 