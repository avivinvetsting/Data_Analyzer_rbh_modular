import plotly.graph_objects as go
import pandas as pd

def create_candlestick_chart(df, chart_title, display_years=None):
    if df.empty:
        return None

    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    df_display = df.copy()

    if display_years and not df_display.empty:
        latest_date_in_data = df_display.index.max()
        cutoff_date = latest_date_in_data - pd.DateOffset(years=display_years)
        df_display = df_display[df_display.index >= cutoff_date]

    if df_display.empty:
        return None

    fig = go.Figure(data=[go.Candlestick(x=df_display.index,
                                         open=df_display['Open'],
                                         high=df_display['High'],
                                         low=df_display['Low'],
                                         close=df_display['Close'])])
    fig.update_layout(
        title_text=chart_title,
        title_x=0.5,
        xaxis_title="תאריך",
        yaxis_title="מחיר",
        xaxis_rangeslider_visible=False,
        margin=dict(l=50, r=50, b=50, t=80, pad=4)
    )
    return fig.to_json()