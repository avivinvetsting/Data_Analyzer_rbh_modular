# modules/chart_creator.py
import plotly.graph_objects as go
import pandas as pd
from flask import current_app
import plotly.express as px
from typing import Optional, Dict, List # הוספת Optional, Dict, List

import json # הוספנו למקרה שנצטרך לבדוק את ה-JSON שנוצר


def resample_ohlc(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """
    Resample OHLC data to a given frequency (e.g., 'W' for weekly, 'M' for monthly).
    """
    current_app.logger.debug(f"Resampling OHLC data with rule: {rule}. Original shape: {df.shape}")
    ohlc_dict = {
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
    }
    # הוספת עמודות אופציונליות רק אם הן קיימות
    if 'Volume' in df.columns: ohlc_dict['Volume'] = 'sum'
    if 'Dividends' in df.columns: ohlc_dict['Dividends'] = 'sum'
    if 'Stock Splits' in df.columns: ohlc_dict['Stock Splits'] = 'sum'
    
    try:
        df_resampled = df.resample(rule).apply(ohlc_dict)
        df_resampled.dropna(how='all', inplace=True) 
        current_app.logger.info(f"Resampled OHLC data. New shape: {df_resampled.shape}")
        return df_resampled
    except Exception as e:
        current_app.logger.error(f"Error during OHLC resampling with rule '{rule}': {str(e)}")
        current_app.logger.exception("Detailed traceback for OHLC resampling error:")
        return pd.DataFrame()


def create_candlestick_chart(df: pd.DataFrame, chart_title: str, add_ma: bool = False, display_years: Optional[int] = None) -> Optional[str]:
    current_app.logger.info(f"Attempting to create candlestick chart: '{chart_title}' (MA: {add_ma}, Display Years: {display_years})")
    
    if df is None or df.empty:
        current_app.logger.warning(f"Cannot create chart '{chart_title}': Input DataFrame is empty or None.")
        return None

    df = df.sort_index() 
    if not isinstance(df.index, pd.DatetimeIndex):
        try:
            df.index = pd.to_datetime(df.index, errors='coerce')
            # השתמש ב- df.index.name אם הוא קיים, אחרת פשוט תבדוק אם האינדקס ריק אחרי הסרת NaT
            index_name = df.index.name if df.index.name is not None else 'index'
            df.dropna(subset=[index_name] if index_name == 'index' and df.index.name is None else None, inplace=True) # יסיר שורות עם NaT באינדקס
            if df.empty:
                 current_app.logger.warning(f"DataFrame became empty after index conversion/dropna for chart '{chart_title}'.")
                 return None
            current_app.logger.debug(f"Index converted to DatetimeIndex for chart '{chart_title}'.")
        except Exception as e:
            current_app.logger.error(f"Error converting or cleaning index for chart '{chart_title}': {str(e)}")
            current_app.logger.exception("Detailed traceback for index conversion error in create_candlestick_chart:")
            return None
    
    df_display = df.copy()

    if display_years and not df_display.empty:
        try:
            latest_date_in_data = df_display.index.max()
            if pd.isna(latest_date_in_data):
                current_app.logger.warning(f"Latest date in data for chart '{chart_title}' is NaT. Cannot slice by years.")
            else:
                cutoff_date = latest_date_in_data - pd.DateOffset(years=display_years)
                df_display = df_display[df_display.index >= cutoff_date]
                current_app.logger.debug(f"Data for chart '{chart_title}' sliced to display last {display_years} years. Rows after slice: {len(df_display)}")
        except Exception as e:
            current_app.logger.error(f"Error slicing data by display_years for chart '{chart_title}': {str(e)}")

    if df_display.empty:
        current_app.logger.warning(f"No data to display for chart '{chart_title}' after potential slicing.")
        return None

    ohlc_cols = ['Open', 'High', 'Low', 'Close']
    missing_ohlc = [col for col in ohlc_cols if col not in df_display.columns]
    if missing_ohlc:
        current_app.logger.error(f"Missing OHLC columns {missing_ohlc} in DataFrame for chart '{chart_title}'. Cannot create Candlestick trace.")
        return None

    for col in ohlc_cols:
        if not pd.api.types.is_numeric_dtype(df_display[col]):
            df_display[col] = pd.to_numeric(df_display[col], errors='coerce')
    
    df_display.dropna(subset=ohlc_cols, inplace=True)
    
    if len(df_display) < 1:
        current_app.logger.warning(f"Not enough valid data points (after NaN drop) for chart '{chart_title}'. Rows: {len(df_display)}")
        return None
        
    try:
        candlestick = go.Candlestick(
            x=df_display.index,
            open=df_display['Open'],
            high=df_display['High'],
            low=df_display['Low'],
            close=df_display['Close'],
            name='Price',
            increasing_line_color='#26a69a',
            decreasing_line_color='#ef5350',
            line=dict(width=1),
            whiskerwidth=0.5,
            opacity=1.0
        )
        figure_data: List[go.BaseTraceType] = [candlestick]

        if add_ma:
            windows = [20, 50, 100, 150, 200]
            ma_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'] 
            current_app.logger.debug(f"Calculating moving averages for chart '{chart_title}'.")
            for i, window in enumerate(windows):
                if len(df_display) >= window:
                    ma_col = f'MA{window}'
                    df_display[ma_col] = df_display['Close'].rolling(window=window, min_periods=1).mean()
                    figure_data.append(
                        go.Scatter(
                            x=df_display.index, 
                            y=df_display[ma_col], 
                            mode='lines', 
                            name=ma_col,
                            line=dict(width=1.5, color=ma_colors[i % len(ma_colors)])
                        )
                    )
                else:
                    current_app.logger.debug(f"Skipping MA{window} for chart '{chart_title}' due to insufficient data points ({len(df_display)} < {window}).")

        fig = go.Figure(data=figure_data)
        fig.update_layout(
            title_text=chart_title, title_x=0.5,
            xaxis_title="Date", yaxis_title="Price",
            xaxis_rangeslider_visible=False,
            legend_title_text='Legend',
            margin=dict(l=50, r=50, b=50, t=80, pad=4),
            plot_bgcolor='white', paper_bgcolor='white',
            xaxis=dict(gridcolor='lightgray', showgrid=True, type='date'),
            yaxis=dict(gridcolor='lightgray', showgrid=True, autorange=True, fixedrange=False),
            hovermode='x unified', hoverdistance=100, spikedistance=1000,
            showlegend=True, legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
        )
        
        chart_json = fig.to_json()
        current_app.logger.debug(f"Chart JSON for '{chart_title}' created. Length: {len(chart_json)}")
        
        try:
            json_data = json.loads(chart_json)
            if 'data' not in json_data or not json_data['data']:
                current_app.logger.error(f"Chart JSON for '{chart_title}' has no data array or data array is empty after creation.")
                return None
            if 'layout' not in json_data:
                current_app.logger.error(f"Chart JSON for '{chart_title}' has no layout after creation.")
                return None
        except json.JSONDecodeError as json_e:
            current_app.logger.error(f"Failed to decode chart_json for '{chart_title}': {str(json_e)}")
            return None

        current_app.logger.info(f"Successfully created and validated JSON for chart '{chart_title}'.")
        return chart_json

    except Exception as e:
        current_app.logger.error(f"Error during chart figure creation for '{chart_title}': {str(e)}")
        current_app.logger.exception("Detailed traceback for chart creation error:")
        return None


def create_all_candlestick_charts(df_daily_full: pd.DataFrame, ticker: str, company_name: str) -> Dict[str, Optional[str]]:
    charts: Dict[str, Optional[str]] = { # Type hint עבור המשתנה charts
        'daily_chart_json': None,
        'weekly_chart_json': None,
        'monthly_chart_json': None
    }
    current_app.logger.info(f"Creating all candlestick charts for ticker: {ticker} ({company_name})")

    if df_daily_full is None or df_daily_full.empty:
        current_app.logger.warning(f"Cannot create any charts for {ticker}: Input daily DataFrame is empty or None.")
        return charts

    charts['daily_chart_json'] = create_candlestick_chart(df_daily_full, f"{company_name} ({ticker}) - Daily Prices (Last 2 Years)", add_ma=True, display_years=2)

    try:
        current_app.logger.info(f"Resampling daily data to weekly for {ticker}.")
        weekly_df = resample_ohlc(df_daily_full, 'W-FRI')
        if weekly_df.empty:
            current_app.logger.warning(f"Weekly resampled data is empty for {ticker}.")
        else:
            charts['weekly_chart_json'] = create_candlestick_chart(weekly_df, f"{company_name} ({ticker}) - Weekly Prices (Last 5 Years)", add_ma=False, display_years=5)
    except Exception as e:
        current_app.logger.error(f"Error creating weekly chart for {ticker}: {str(e)}")
        current_app.logger.exception("Detailed traceback for weekly chart creation error:")
    
    try:
        current_app.logger.info(f"Resampling daily data to monthly for {ticker}.")
        monthly_df = resample_ohlc(df_daily_full, 'M')
        if monthly_df.empty:
            current_app.logger.warning(f"Monthly resampled data is empty for {ticker}.")
        else:
            charts['monthly_chart_json'] = create_candlestick_chart(monthly_df, f"{company_name} ({ticker}) - Monthly Prices (Last 10 Years)", add_ma=False, display_years=10)
    except Exception as e:
        current_app.logger.error(f"Error creating monthly chart for {ticker}: {str(e)}")
        current_app.logger.exception("Detailed traceback for monthly chart creation error:")
        
    return charts


def create_simple_timeseries_chart(df: pd.DataFrame, date_column: str, value_column: str, chart_title: str, y_axis_title: str = "Value") -> Optional[str]:
    current_app.logger.info(f"Attempting to create simple timeseries chart. Title: '{chart_title}'")

    if df is None or df.empty:
        current_app.logger.warning(f"Cannot create chart '{chart_title}': Input DataFrame is empty or None.")
        return None
    
    if date_column not in df.columns:
        current_app.logger.error(f"Date column '{date_column}' not found in DataFrame for chart '{chart_title}'.")
        return None
    if value_column not in df.columns:
        current_app.logger.error(f"Value column '{value_column}' not found in DataFrame for chart '{chart_title}'.")
        return None

    try:
        df_copy = df.copy() # עבודה על עותק כדי לא לשנות את ה-DataFrame המקורי
        if not pd.api.types.is_datetime64_any_dtype(df_copy[date_column]):
            df_copy[date_column] = pd.to_datetime(df_copy[date_column], errors='coerce')
            df_copy.dropna(subset=[date_column], inplace=True)
            if df_copy.empty:
                current_app.logger.warning(f"DataFrame became empty after date conversion for chart '{chart_title}'.")
                return None
        
        if not pd.api.types.is_numeric_dtype(df_copy[value_column]):
            if df_copy[value_column].dtype == 'object':
                 df_copy[value_column] = df_copy[value_column].astype(str).str.replace(',', '', regex=False)
            df_copy[value_column] = pd.to_numeric(df_copy[value_column], errors='coerce')
            df_copy.dropna(subset=[value_column], inplace=True)
            if df_copy.empty:
                current_app.logger.warning(f"DataFrame became empty after value conversion for chart '{chart_title}'.")
                return None

        fig = px.line(df_copy, x=date_column, y=value_column, title=chart_title, markers=True,
                      labels={date_column: "תאריך", value_column: y_axis_title})
        
        fig.update_layout(
            title_x=0.5,
            xaxis_title="תאריך",
            yaxis_title=y_axis_title,
            margin=dict(l=50, r=50, b=50, t=80, pad=4),
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(gridcolor='lightgray', showgrid=True),
            yaxis=dict(gridcolor='lightgray', showgrid=True)
        )
        
        chart_json = fig.to_json()
        current_app.logger.info(f"Successfully created JSON for simple timeseries chart '{chart_title}'.")
        return chart_json

    except Exception as e:
        current_app.logger.error(f"Error during simple timeseries chart creation for '{chart_title}': {str(e)}")
        current_app.logger.exception("Detailed traceback for simple timeseries chart creation error:")
        return None