# modules/routes/home.py
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
# from flask_wtf.csrf import CSRFProtect # ודא שזה מוגדר כראוי אם אתה משתמש ב-CSRF
import pandas as pd
import re
import html
import unicodedata

# ודא שהנתיבים לייבוא נכונים.
from modules.price_history import get_price_history, get_company_name, get_company_info
from modules.chart_creator import create_all_candlestick_charts
from werkzeug.exceptions import BadRequest


home_bp = Blueprint('home_bp', __name__)

# קבועים לולידציה
TICKER_MIN_LENGTH = 1
TICKER_MAX_LENGTH = 12
# דפוס התווים החוקיים לטיקר
TICKER_VALID_PATTERN = re.compile(r"^[A-Za-z0-9.\-^]+$")

def sanitize_ticker(ticker_input):
    """פונקציית עזר לניקוי טיקר - בעיקר להמרת Unicode והסרת תווים בעייתיים מאוד (אם נשארו)."""
    # הסרת רווחים מיותרים כבר נעשתה ב-validate_ticker לפני הקריאה לזה (אם בכלל נקרא)
    # המרת תווים מיוחדים ל-ASCII (אם עדיין רוצים את השלב הזה)
    # ticker = unicodedata.normalize('NFKD', ticker_input).encode('ASCII', 'ignore').decode('ASCII')
    # הסרת תווים שאינם חלק מהתבנית המאושרת (בדרך כלל לא אמור לקרות אם validate_ticker עובד נכון)
    # ticker = re.sub(r'[^A-Za-z0-9.\-^]', '', ticker)
    # בשלב זה, אחרי התיקון ל-validate_ticker, ייתכן שפונקציה זו כבר לא נחוצה שם,
    # או שתפקידה מצטמצם. כרגע נשאיר אותה כפי שהייתה אם כי השימוש בה עשוי להשתנות.
    processed_ticker = ticker_input.strip()
    processed_ticker = unicodedata.normalize('NFKD', processed_ticker).encode('ASCII', 'ignore').decode('ASCII')
    # חשוב: השורה הבאה עלולה להסיר תווים שכבר אושרו. יש לשקול אם היא עדיין נחוצה.
    # processed_ticker = re.sub(r'[^A-Za-z0-9.\-^]', '', processed_ticker) 
    return processed_ticker


def clear_session_data():
    """ניקוי כל נתוני הסשן (כולל מפתחות דינמיים שנוספו ע"י טסטים)"""
    keys_to_keep = {'_permanent', 'csrf_token'}
    for key in list(session.keys()):
        if key not in keys_to_keep:
            session.pop(key, None)
    current_app.logger.debug("Cleared all session data except system keys.")


def validate_ticker(raw_ticker_input):
    """
    ולידציה של טיקר.
    בודק קלט ריק, תווים לא חוקיים, ואורך.
    מחזיר את הטיקר באותיות גדולות ועבר html.escape אם תקין.
    """
    if not raw_ticker_input: # בודק אם הקלט המקורי ריק
        raise BadRequest('אנא הזן סימול טיקר.')

    # הסר רווחים מההתחלה והסוף לפני בדיקת התבנית
    processed_ticker = raw_ticker_input.strip()

    if not processed_ticker: # אם לאחר strip לא נשאר כלום (היה רק רווחים)
        raise BadRequest('אנא הזן סימול טיקר.')

    # שלב 1: בדוק את תבנית התווים החוקיים על הקלט (לאחר strip)
    if not TICKER_VALID_PATTERN.match(processed_ticker):
        raise BadRequest('הסימול יכול להכיל רק אותיות באנגלית, ספרות, נקודה (.), מקף (-), או גג (^).')

    # שלב 2: בדוק אורך (לאחר שהתווים אושרו כתקינים)
    # הפונקציה sanitize_ticker כבר לא אמורה לשנות את התווים המותרים כאן.
    # אם יש צורך בנורמליזציית Unicode נוספת, אפשר לשלב את sanitize_ticker כאן בזהירות.
    # כרגע נניח ש-processed_ticker הוא מה שנבדוק לאורך.
    if not (TICKER_MIN_LENGTH <= len(processed_ticker) <= TICKER_MAX_LENGTH):
        raise BadRequest(f'אורך הסימול חייב להיות בין {TICKER_MIN_LENGTH} ל-{TICKER_MAX_LENGTH} תווים.')

    # המרה לאותיות גדולות ו-escape בסוף, לאחר כל הולידציות
    return html.escape(processed_ticker.upper())


@home_bp.route('/')
@login_required
def index():
    current_app.logger.debug(f"User '{current_user.username}' accessed home page (index route)")
    template_data = {
        'selected_ticker': session.get('selected_ticker'),
        'company_name': session.get('company_name'),
        'company_info': session.get('company_info'),
        'chart1_json': None,
        'chart2_json': None,
        'chart3_json': None
    }
    return render_template('content_home.html', **template_data)

@home_bp.route('/analyze', methods=['POST'])
@login_required
def analyze():
    ticker_from_form_raw = request.form.get('ticker', '')
    ticker_from_form = "" # אתחול למקרה של שגיאה לפני שהערך נקבע
    try:
        # הולידציה קורית כאן, ואם היא נכשלת, היא מעלה BadRequest
        ticker_from_form = validate_ticker(ticker_from_form_raw)
        current_app.logger.info(f"Analyze request for validated ticker: {ticker_from_form} (raw input: '{ticker_from_form_raw}')")

        session['selected_ticker'] = ticker_from_form

        company_name_fetched = get_company_name(ticker_from_form)
        company_name_display = company_name_fetched if company_name_fetched and company_name_fetched.strip().upper() != ticker_from_form else ticker_from_form
        session['company_name'] = company_name_display
        current_app.logger.debug(f"Company name set in session: {company_name_display}")

        company_info_display = get_company_info(ticker_from_form)
        session['company_info'] = company_info_display
        current_app.logger.debug(f"Company info set in session for: {ticker_from_form}")

        chart1_json_data = None
        chart2_json_data = None
        chart3_json_data = None

        df_daily_for_charts = get_price_history(ticker_from_form, period="10y", interval="1d")

        if df_daily_for_charts is not None and not df_daily_for_charts.empty:
            current_app.logger.info(f"Price data found for {ticker_from_form} (shape: {df_daily_for_charts.shape}). Generating charts.")
            all_charts_json = create_all_candlestick_charts(df_daily_for_charts, ticker_from_form, company_name_display)

            chart1_json_data = all_charts_json.get('daily_chart_json')
            chart2_json_data = all_charts_json.get('weekly_chart_json')
            chart3_json_data = all_charts_json.get('monthly_chart_json')

            if not any([chart1_json_data, chart2_json_data, chart3_json_data]):
                flash(f"לא נמצאו מספיק נתונים ליצירת גרפים עבור {html.escape(ticker_from_form)}.", 'warning')
                current_app.logger.warning(f"Not enough data to create any charts for {ticker_from_form} after attempting generation.")
            else:
                current_app.logger.info(f"Charts generated for {ticker_from_form}. Daily: {bool(chart1_json_data)}, Weekly: {bool(chart2_json_data)}, Monthly: {bool(chart3_json_data)}")
        else:
            flash(f"לא נמצאו נתוני מחירים בסיסיים עבור {html.escape(ticker_from_form)} ליצירת גרפים.", "danger")
            current_app.logger.warning(f"No basic price data found for {ticker_from_form} from get_price_history.")

        return render_template('content_home.html',
                             selected_ticker=ticker_from_form,
                             company_name=company_name_display,
                             company_info=company_info_display,
                             chart1_json=chart1_json_data,
                             chart2_json=chart2_json_data,
                             chart3_json=chart3_json_data)

    except BadRequest as e:
        flash(str(e), 'warning') # הודעת השגיאה מה-BadRequest תוצג ישירות
        current_app.logger.warning(f"BadRequest during analyze for raw ticker '{html.escape(ticker_from_form_raw)}': {str(e)}")
        return redirect(url_for('home_bp.index'))
    except Exception as e:
        # חשוב לכלול את הטיקר המקורי (raw) בלוג השגיאה אם ticker_from_form עדיין ריק
        effective_ticker_for_log = ticker_from_form if ticker_from_form else ticker_from_form_raw
        current_app.logger.error(f"Unhandled exception during analyze for ticker '{html.escape(effective_ticker_for_log)}': {str(e)}")
        current_app.logger.exception("Detailed traceback for unhandled exception in analyze:")
        clear_session_data()
        flash('אירעה שגיאה בעת ניתוח הטיקר. אנא נסה שוב.', 'danger')
        return redirect(url_for('home_bp.index'))