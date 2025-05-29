# modules/routes/home.py
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from flask_login import login_required, current_user # ודא ש-current_user מיובא
import pandas as pd
import re 
# ודא שהנתיבים לייבוא נכונים. אם הקבצים באותה תיקיית modules, אז:
from modules.price_history import get_price_history, get_company_name, get_company_info 
from modules.chart_creator import create_all_candlestick_charts # נשתמש בפונקציה המרכזת

home_bp = Blueprint('home_bp', __name__)

# קבועים לולידציה
TICKER_MIN_LENGTH = 1
TICKER_MAX_LENGTH = 12
TICKER_VALID_PATTERN = re.compile(r"^[A-Z0-9.\-^]+$")


@home_bp.route('/') # הנתיב הראשי של ה-blueprint
@login_required
def index(): # שם הפונקציה הוא 'index'
    current_app.logger.info(f"User '{current_user.username}' accessed home page (index route). Method: {request.method}")
    
    selected_ticker = session.get('selected_ticker')
    company_name = session.get('company_name')
    company_info_data = session.get('company_info') # שליפת מידע חברה מהסשן
    chart1_json = session.get('chart1_json')
    chart2_json = session.get('chart2_json')
    chart3_json = session.get('chart3_json')
    
    current_app.logger.debug(f"Rendering content_home.html for GET. Ticker from session: {selected_ticker}")
    return render_template('content_home.html',
                           ticker=selected_ticker, # השם המקורי בתבנית שלך
                           selected_ticker=selected_ticker, # נשאיר גם את זה למקרה שהתבנית עודכנה
                           company_name=company_name,
                           company_info=company_info_data, # העברת מידע חברה
                           chart1_json=chart1_json,
                           chart2_json=chart2_json,
                           chart3_json=chart3_json)


@home_bp.route('/analyze', methods=['POST']) # הנתיב לניתוח, אליו הטופס מפנה
@login_required
def analyze():
    ticker_from_form = request.form.get('ticker', '').strip().upper()
    current_app.logger.info(f"User '{current_user.username}' initiated analysis for ticker: '{ticker_from_form}'")
    
    # ולידציה
    if not ticker_from_form:
        flash('אנא הזן סימול טיקר.', 'warning')
        current_app.logger.warning("Analysis attempt with empty ticker.")
        return redirect(url_for('home_bp.index'))
        
    if not (TICKER_MIN_LENGTH <= len(ticker_from_form) <= TICKER_MAX_LENGTH):
        flash(f'אורך הסימול חייב להיות בין {TICKER_MIN_LENGTH} ל-{TICKER_MAX_LENGTH} תווים.', 'warning')
        current_app.logger.warning(f"Ticker '{ticker_from_form}' failed length validation (Length: {len(ticker_from_form)}).")
        return redirect(url_for('home_bp.index'))
        
    if not TICKER_VALID_PATTERN.match(ticker_from_form):
        flash('הסימול יכול להכיל רק אותיות באנגלית, ספרות, נקודה (.), מקף (-), או גג (^).', 'warning')
        current_app.logger.warning(f"Ticker '{ticker_from_form}' failed character validation (Pattern: {TICKER_VALID_PATTERN.pattern}).")
        return redirect(url_for('home_bp.index'))

    # אם הולידציה עברה
    session['selected_ticker'] = ticker_from_form
    current_app.logger.info(f"Ticker '{ticker_from_form}' passed validation. Proceeding with data fetching.")

    chart1_json, chart2_json, chart3_json = None, None, None
    company_name_display = ticker_from_form 
    company_info_display = None

    try:
        current_app.logger.info(f"Fetching company name for '{ticker_from_form}'")
        company_name_fetched = get_company_name(ticker_from_form)
        if company_name_fetched and company_name_fetched.upper() != ticker_from_form: # השוואה לא רגישה לרישיות
            company_name_display = company_name_fetched
            current_app.logger.info(f"Company name for '{ticker_from_form}': '{company_name_display}'")
        else:
            current_app.logger.info(f"Using ticker symbol as company name for '{ticker_from_form}'.")
        session['company_name'] = company_name_display

        current_app.logger.info(f"Fetching company info for '{ticker_from_form}'")
        company_info_display = get_company_info(ticker_from_form)
        session['company_info'] = company_info_display # שמירת מידע חברה בסשן
        if company_info_display:
            current_app.logger.info(f"Company info fetched for '{ticker_from_form}'.")
        else:
            current_app.logger.warning(f"No detailed company info found for '{ticker_from_form}'.")


        current_app.logger.info(f"Fetching daily price data (3y) for charts for ticker: '{ticker_from_form}'")
        # נוריד פעם אחת את הנתונים היומיים לתקופה הארוכה ביותר שנצטרך (3 שנים לגרף היומי, אבל אולי יותר אם נרסמפל ממנו)
        # לצורך הדוגמה, נניח שפונקציית הריסמפול מצפה לנתונים יומיים.
        # אם create_all_candlestick_charts מקבלת נתונים יומיים, אז זה בסדר.
        # הגרסה שלך ל-price_history לא כוללת create_all_charts, אלא קריאות נפרדות ל-get_price_history.
        # נשתמש בפונקציה המרכזת מ-chart_creator שהייתה בגרסה הקודמת שלך, או שנשחזר את הקריאות הנפרדות.
        # בגרסה הנוכחית של chart_creator שהעלית, יש create_all_candlestick_charts שמקבלת df_daily_full.
        
        df_daily_for_charts = get_price_history(ticker_from_form, period="10y", interval="1d") # טען מספיק נתונים לכל הריסמפולים

        if df_daily_for_charts is not None and not df_daily_for_charts.empty:
            current_app.logger.info(f"Main daily data ({len(df_daily_for_charts)} rows) fetched for {ticker_from_form}. Creating all charts.")
            all_charts_json = create_all_candlestick_charts(df_daily_for_charts, ticker_from_form, company_name_display)
            chart1_json = all_charts_json.get('daily_chart_json')
            chart2_json = all_charts_json.get('weekly_chart_json')
            chart3_json = all_charts_json.get('monthly_chart_json')
            
            session['chart1_json'] = chart1_json
            session['chart2_json'] = chart2_json
            session['chart3_json'] = chart3_json

            if not chart1_json and not chart2_json and not chart3_json:
                 flash(f"לא נמצאו מספיק נתונים ליצירת גרפים עבור {ticker_from_form}.", 'warning')
                 current_app.logger.warning(f"No charts could be generated for {ticker_from_form} by create_all_candlestick_charts.")
        else:
            flash(f"לא נמצאו נתוני מחירים בסיסיים עבור {ticker_from_form} ליצירת גרפים.", "danger")
            current_app.logger.error(f"Failed to fetch base daily data for {ticker_from_form} to generate charts.")

        current_app.logger.debug(f"Rendering content_home.html after analysis for {ticker_from_form}")
        # נעביר את כל המשתנים לתבנית, גם אם חלקם None
        return render_template('content_home.html',
                             ticker=ticker_from_form, 
                             selected_ticker=ticker_from_form, # כדי לאכלס את התיבה
                             company_name=company_name_display,
                             company_info=company_info_display,
                             chart1_json=chart1_json,
                             chart2_json=chart2_json,
                             chart3_json=chart3_json)
                             
    except Exception as e:
        current_app.logger.error(f"Unexpected error during analysis of ticker '{ticker_from_form}': {str(e)}")
        current_app.logger.exception("Detailed traceback for analysis error:")
        flash('אירעה שגיאה בלתי צפויה בעת ניתוח הטיקר. אנא נסה שוב.', 'danger')
        session.pop('selected_ticker', None)
        session.pop('company_name', None)
        session.pop('company_info', None)
        session.pop('chart1_json', None)
        session.pop('chart2_json', None)
        session.pop('chart3_json', None)
        return redirect(url_for('home_bp.index'))