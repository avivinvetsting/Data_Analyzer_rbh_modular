# modules/routes/home.py
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from flask_wtf.csrf import CSRFProtect
import pandas as pd
import re 
# ודא שהנתיבים לייבוא נכונים. אם הקבצים באותה תיקיית modules, אז:
from modules.price_history import get_price_history, get_company_name, get_company_info 
from modules.chart_creator import create_all_candlestick_charts # נשתמש בפונקציה המרכזת
from werkzeug.exceptions import BadRequest
import html
import unicodedata

home_bp = Blueprint('home_bp', __name__)
csrf = CSRFProtect()

# קבועים לולידציה
TICKER_MIN_LENGTH = 1
TICKER_MAX_LENGTH = 12
TICKER_VALID_PATTERN = re.compile(r"^[A-Za-z0-9.\-^]+$")  # מאפשר אותיות קטנות וגדולות

def sanitize_ticker(ticker):
    """ניקוי וטיהור הטיקר"""
    # הסרת רווחים מיותרים
    ticker = ticker.strip()
    
    # המרת תווים מיוחדים ל-ASCII
    ticker = unicodedata.normalize('NFKD', ticker).encode('ASCII', 'ignore').decode('ASCII')
    
    # הסרת תווים לא רצויים
    ticker = re.sub(r'[^A-Za-z0-9.\-^]', '', ticker)
    
    return ticker

def clear_session_data():
    """ניקוי נתוני סשן בצורה מרוכזת"""
    session_keys = ['selected_ticker', 'company_name', 'company_info', 
                   'chart1_json', 'chart2_json', 'chart3_json']
    for key in session_keys:
        session.pop(key, None)

def validate_ticker(ticker):
    """ולידציה של טיקר"""
    if not ticker:
        raise BadRequest('אנא הזן סימול טיקר.')
        
    # ניקוי וטיהור הטיקר
    ticker = sanitize_ticker(ticker)
        
    if not (TICKER_MIN_LENGTH <= len(ticker) <= TICKER_MAX_LENGTH):
        raise BadRequest(f'אורך הסימול חייב להיות בין {TICKER_MIN_LENGTH} ל-{TICKER_MAX_LENGTH} תווים.')
        
    if not TICKER_VALID_PATTERN.match(ticker):
        raise BadRequest('הסימול יכול להכיל רק אותיות באנגלית, ספרות, נקודה (.), מקף (-), או גג (^).')
    
    return html.escape(ticker.upper())  # ממיר לאותיות גדולות ומונע XSS

@home_bp.route('/') # הנתיב הראשי של ה-blueprint
@login_required
def index(): # שם הפונקציה הוא 'index'
    current_app.logger.debug(f"User '{current_user.username}' accessed home page")
    
    template_data = {
        'selected_ticker': session.get('selected_ticker'),
        'company_name': session.get('company_name'),
        'company_info': session.get('company_info'),
        'chart1_json': session.get('chart1_json'),
        'chart2_json': session.get('chart2_json'),
        'chart3_json': session.get('chart3_json')
    }
    
    return render_template('content_home.html', **template_data)

@home_bp.route('/analyze', methods=['POST']) # הנתיב לניתוח, אליו הטופס מפנה
@login_required
@csrf.exempt  # אם אתה משתמש ב-CSRF token בתבנית
def analyze():
    try:
        ticker_from_form = validate_ticker(request.form.get('ticker', ''))
        
        # ניקוי נתונים קודמים
        clear_session_data()
        
        # שמירת הטיקר החדש
        session['selected_ticker'] = ticker_from_form
        
        # קבלת שם החברה
        company_name_fetched = get_company_name(ticker_from_form)
        company_name_display = company_name_fetched if company_name_fetched and company_name_fetched.upper() != ticker_from_form else ticker_from_form
        session['company_name'] = company_name_display
        
        # קבלת מידע על החברה
        company_info_display = get_company_info(ticker_from_form)
        session['company_info'] = company_info_display
        
        # טעינת נתוני מחירים ויצירת גרפים
        df_daily_for_charts = get_price_history(ticker_from_form, period="10y", interval="1d")
        
        if df_daily_for_charts is not None and not df_daily_for_charts.empty:
            all_charts_json = create_all_candlestick_charts(df_daily_for_charts, ticker_from_form, company_name_display)
            
            # שמירת הגרפים בסשן
            for chart_key, session_key in [
                ('daily_chart_json', 'chart1_json'),
                ('weekly_chart_json', 'chart2_json'),
                ('monthly_chart_json', 'chart3_json')
            ]:
                session[session_key] = all_charts_json.get(chart_key)
            
            if not any(session.get(key) for key in ['chart1_json', 'chart2_json', 'chart3_json']):
                flash(f"לא נמצאו מספיק נתונים ליצירת גרפים עבור {ticker_from_form}.", 'warning')
        else:
            flash(f"לא נמצאו נתוני מחירים בסיסיים עבור {ticker_from_form} ליצירת גרפים.", "danger")
            return redirect(url_for('home_bp.index'))
            
        return render_template('content_home.html',
                             selected_ticker=ticker_from_form,
                             company_name=company_name_display,
                             company_info=company_info_display,
                             chart1_json=session.get('chart1_json'),
                             chart2_json=session.get('chart2_json'),
                             chart3_json=session.get('chart3_json'))
                             
    except BadRequest as e:
        flash(str(e), 'warning')
        return redirect(url_for('home_bp.index'))
    except Exception as e:
        current_app.logger.error(f"Error analyzing ticker '{ticker_from_form}': {str(e)}")
        clear_session_data()
        flash('אירעה שגיאה בעת ניתוח הטיקר. אנא נסה שוב.', 'danger')
        return redirect(url_for('home_bp.index'))