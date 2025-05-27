# modules/chart_creator.py
import plotly.graph_objects as go
import pandas as pd
from flask import current_app

def create_candlestick_chart(df, chart_title, display_years=None):
    current_app.logger.info(f"Attempting to create candlestick chart. Title: '{chart_title}', Display Years: {display_years}")

    if df is None or df.empty:
        current_app.logger.warning(f"Cannot create chart '{chart_title}': Input DataFrame is empty or None.")
        return None

    if not isinstance(df.index, pd.DatetimeIndex):
        try:
            df.index = pd.to_datetime(df.index)
            current_app.logger.debug(f"Converted index to DatetimeIndex for chart '{chart_title}'.")
        except Exception as e:
            current_app.logger.error(f"Error converting index to DatetimeIndex for chart '{chart_title}': {str(e)}")
            current_app.logger.exception("Detailed traceback for index conversion error:")
            return None

    df_display = df.copy()

    if display_years and not df_display.empty:
        try:
            latest_date_in_data = df_display.index.max()
            cutoff_date = latest_date_in_data - pd.DateOffset(years=display_years)
            df_display = df_display[df_display.index >= cutoff_date]
            current_app.logger.debug(f"Data for chart '{chart_title}' sliced to display last {display_years} years. Rows after slice: {len(df_display)}")
        except Exception as e:
            current_app.logger.error(f"Error slicing data by display_years for chart '{chart_title}': {str(e)}")

    if df_display.empty:
        current_app.logger.warning(f"No data to display for chart '{chart_title}' after potential slicing (or initially empty).")
        return None

    try:
        current_app.logger.debug(f"Calculating moving averages for chart '{chart_title}'.")
        windows = [20, 50, 100, 150, 200]
        for window in windows:
            df_display[f'MA{window}'] = df_display['Close'].rolling(window=window, min_periods=1).mean()
        current_app.logger.debug(f"Moving averages calculated for chart '{chart_title}'.")

        figure_data = []
        figure_data.append(
            go.Candlestick(x=df_display.index,
                           open=df_display['Open'],
                           high=df_display['High'],
                           low=df_display['Low'],
                           close=df_display['Close'],
                           name='מחיר')
        )

        ma_colors = ['blue', 'orange', 'green', 'red', 'purple'] 
        for i, window in enumerate(windows):
            ma_col_name = f'MA{window}'
            if ma_col_name in df_display.columns:
                figure_data.append(
                    go.Scatter(x=df_display.index, 
                               y=df_display[ma_col_name], 
                               mode='lines', 
                               name=ma_col_name,
                               line=dict(width=1.5, color=ma_colors[i % len(ma_colors)]))
                )
        
        if not figure_data:
            current_app.logger.warning(f"No figure data could be prepared for chart '{chart_title}'.")
            return None

        fig = go.Figure(data=figure_data)
        
        fig.update_layout(
            title_text=chart_title,
            title_x=0.5,
            xaxis_title="תאריך",
            yaxis_title="מחיר",
            xaxis_rangeslider_visible=False,
            legend_title_text='מקרא',
            margin=dict(l=50, r=50, b=50, t=80, pad=4)
        )
        chart_json = fig.to_json()
        current_app.logger.info(f"Successfully created JSON for chart '{chart_title}'.")
        return chart_json

    except Exception as e:
        current_app.logger.error(f"Error during chart figure creation for '{chart_title}': {str(e)}")
        current_app.logger.exception("Detailed traceback for chart creation error:")
        return None