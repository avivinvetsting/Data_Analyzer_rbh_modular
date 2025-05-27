# modules/chart_creator.py
import plotly.graph_objects as go
import pandas as pd

def create_candlestick_chart(df, chart_title, display_years=None):
    """
    Creates a Plotly candlestick chart from a DataFrame with moving averages.
    Returns chart data as JSON string.
    If display_years is provided, it truncates the data to the last N years for display.
    """
    if df.empty:
        return None

    # ודא שהאינדקס הוא מסוג datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    df_display = df.copy() # עבודה עם עותק

    # חיתוך הנתונים אם display_years סופק
    if display_years and not df_display.empty:
        # מצא את התאריך המאוחר ביותר בנתונים
        latest_date_in_data = df_display.index.max()
        # חשב את תאריך החיתוך אחורה מהתאריך המאוחר ביותר
        cutoff_date = latest_date_in_data - pd.DateOffset(years=display_years)
        df_display = df_display[df_display.index >= cutoff_date]

    if df_display.empty: # אם לאחר החיתוך אין נתונים (מקרה קצה)
        return None

    # חישוב ממוצעים נעים אם יש נתונים
    if not df_display.empty:
        windows = [20, 50, 100, 150, 200]
        for window in windows:
            # min_periods=1 יחשב את הממוצע גם אם אין מספיק נתונים לחלון המלא (בתחילת הסדרה)
            df_display[f'MA{window}'] = df_display['Close'].rolling(window=window, min_periods=1).mean()

    # יצירת רשימת הנתונים לגרף
    figure_data = []
    if not df_display.empty: # ודא שיש נתונים להצגת נרות
        figure_data.append(
            go.Candlestick(x=df_display.index,
                           open=df_display['Open'],
                           high=df_display['High'],
                           low=df_display['Low'],
                           close=df_display['Close'],
                           name='מחיר') # שם לעקבת הנרות
        )

        # הוספת עקבות (traces) של הממוצעים הנעים אם הם קיימים ב-df_display
        ma_windows = [20, 50, 100, 150, 200]
        # ניתן להתאים את הצבעים לפי העדפה
        ma_colors = ['blue', 'orange', 'green', 'red', 'purple'] 
        
        for i, window in enumerate(ma_windows):
            ma_col_name = f'MA{window}'
            if ma_col_name in df_display.columns: # בדוק אם עמודת הממוצע הנע אכן קיימת
                figure_data.append(
                    go.Scatter(x=df_display.index, 
                               y=df_display[ma_col_name], 
                               mode='lines', 
                               name=ma_col_name,
                               line=dict(width=1.5, color=ma_colors[i % len(ma_colors)])) # קו דק יותר לממוצעים
                )
    
    # אם לאחר כל החישובים והבדיקות, אין נתונים להציג בגרף
    if not figure_data:
        return None

    # יצירת אובייקט הגרף עם כל הנתונים
    fig = go.Figure(data=figure_data)
    
    # עדכון ה-layout של הגרף
    fig.update_layout(
        title_text=chart_title,
        title_x=0.5, # מרכוז הכותרת
        xaxis_title="תאריך",
        yaxis_title="מחיר",
        xaxis_rangeslider_visible=False, # הסתרת ה-rangeslider התחתון
        legend_title_text='מקרא', # הוספת כותרת לאגדה
        margin=dict(l=50, r=50, b=50, t=80, pad=4) # התאמת שוליים
    )
    return fig.to_json()