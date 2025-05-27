# modules/routes/home.py
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from modules.price_history import get_price_history, get_company_name
from modules.chart_creator import create_candlestick_chart
import pandas as pd
import re 

home_bp = Blueprint('home_bp', __name__)

# הגדרת קבועים לולידציה
TICKER_MIN_LENGTH = 1
TICKER_MAX_LENGTH = 12
TICKER_VALID_PATTERN = re.compile(r"^[A-Z0-9.\-^]+$")


@home_bp.route('/', methods=['GET', 'POST'])
def home():
    current_app.logger.info(f"Home route accessed. Method: {request.method}")

    selected_ticker_from_session = session.get('selected_ticker')
    
    current_ticker_for_display = None
    company_name_for_display = None
    chart1_json_for_display = None
    chart2_json_for_display = None
    chart3_json_for_display = None

    if request.method == 'POST':
        ticker_symbol_from_form = request.form.get('ticker')
        
        if not ticker_symbol_from_form:
            current_app.logger.warning("POST request: Ticker symbol was empty.")
            flash('אנא הזן סימול טיקר.', 'warning')
            return render_template('content_home.html',
                                   selected_ticker=selected_ticker_from_session)

        processed_ticker = ticker_symbol_from_form.strip().upper()

        if not (TICKER_MIN_LENGTH <= len(processed_ticker) <= TICKER_MAX_LENGTH):
            current_app.logger.warning(f"POST request: Ticker '{processed_ticker}' failed length validation (Length: {len(processed_ticker)}). Expected {TICKER_MIN_LENGTH}-{TICKER_MAX_LENGTH} chars.")
            flash(f"אורך הסימול חייב להיות בין {TICKER_MIN_LENGTH} ל-{TICKER_MAX_LENGTH} תווים.", 'warning')
            return render_template('content_home.html',
                                   selected_ticker=selected_ticker_from_session)

        if not TICKER_VALID_PATTERN.match(processed_ticker):
            current_app.logger.warning(f"POST request: Ticker '{processed_ticker}' failed character validation. Pattern: {TICKER_VALID_PATTERN.pattern}")
            flash('הסימול יכול להכיל רק אותיות באנגלית, ספרות, נקודה (.), מקף (-), או גג (^).', 'warning')
            return render_template('content_home.html',
                                   selected_ticker=selected_ticker_from_session)

        session['selected_ticker'] = processed_ticker
        current_ticker_for_display = session['selected_ticker']
        current_app.logger.info(f"POST request: Ticker symbol '{current_ticker_for_display}' received, validated, and set in session.")
        
        try:
            current_app.logger.info(f"Attempting to get company name for ticker: '{current_ticker_for_display}'")
            company_name_for_display = get_company_name(current_ticker_for_display)
            current_app.logger.info(f"Company name for '{current_ticker_for_display}': '{company_name_for_display}'")
        except Exception as e:
            current_app.logger.error(f"Error getting company name for '{current_ticker_for_display}': {str(e)}")
            current_app.logger.exception("Detailed traceback for get_company_name error:")
            flash(f"שגיאה בקבלת שם החברה עבור {current_ticker_for_display}.", 'danger')
            company_name_for_display = current_ticker_for_display

        session['company_name'] = company_name_for_display

        # גרף 1
        try:
            current_app.logger.info(f"Attempting to get daily (3y) price history for '{current_ticker_for_display}'.")
            daily_data_3y = get_price_history(current_ticker_for_display, period="3y", interval="1d")
            if daily_data_3y is not None and not daily_data_3y.empty:
                current_app.logger.info(f"Daily data fetched successfully for '{current_ticker_for_display}'. Creating chart (displaying last 2 years).")
                chart1_json_for_display = create_candlestick_chart(
                    daily_data_3y,
                    chart_title=f"{company_name_for_display} ({current_ticker_for_display}) - מחירים יומיים (שנתיים אחרונות)",
                    display_years=2
                )
                current_app.logger.info(f"Daily chart created for '{current_ticker_for_display}'.")
            else:
                current_app.logger.warning(f"No daily price data returned or data is empty for '{current_ticker_for_display}'.")
                flash(f"לא נמצאו נתונים יומיים עבור {current_ticker_for_display}.", 'warning')
        except Exception as e:
            current_app.logger.error(f"Error processing daily chart for '{current_ticker_for_display}': {str(e)}")
            current_app.logger.exception("Detailed traceback for daily chart error:")
            flash(f"שגיאה בהורדת/יצירת נתונים יומיים עבור {current_ticker_for_display}: {str(e)}", 'danger')

        # גרף 2
        try:
            current_app.logger.info(f"Attempting to get weekly (5y) price history for '{current_ticker_for_display}'.")
            weekly_data_5y = get_price_history(current_ticker_for_display, period="5y", interval="1wk")
            if weekly_data_5y is not None and not weekly_data_5y.empty:
                current_app.logger.info(f"Weekly data fetched successfully for '{current_ticker_for_display}'. Creating chart.")
                chart2_json_for_display = create_candlestick_chart(
                    weekly_data_5y,
                    chart_title=f"{company_name_for_display} ({current_ticker_for_display}) - מחירים שבועיים (5 שנים אחרונות)"
                )
                current_app.logger.info(f"Weekly chart created for '{current_ticker_for_display}'.")
            else:
                current_app.logger.warning(f"No weekly price data returned or data is empty for '{current_ticker_for_display}'.")
                flash(f"לא נמצאו נתונים שבועיים עבור {current_ticker_for_display}.", 'warning')
        except Exception as e:
            current_app.logger.error(f"Error processing weekly chart for '{current_ticker_for_display}': {str(e)}")
            current_app.logger.exception("Detailed traceback for weekly chart error:")
            flash(f"שגיאה בהורדת/יצירת נתונים שבועיים עבור {current_ticker_for_display}: {str(e)}", 'danger')

        # גרף 3
        try:
            current_app.logger.info(f"Attempting to get monthly (10y) price history for '{current_ticker_for_display}'.")
            monthly_data_10y = get_price_history(current_ticker_for_display, period="10y", interval="1mo")
            if monthly_data_10y is not None and not monthly_data_10y.empty:
                current_app.logger.info(f"Monthly data fetched successfully for '{current_ticker_for_display}'. Creating chart.")
                chart3_json_for_display = create_candlestick_chart(
                    monthly_data_10y,
                    chart_title=f"{company_name_for_display} ({current_ticker_for_display}) - מחירים חודשיים (10 שנים אחרונות)"
                )
                current_app.logger.info(f"Monthly chart created for '{current_ticker_for_display}'.")
            else:
                current_app.logger.warning(f"No monthly price data returned or data is empty for '{current_ticker_for_display}'.")
                flash(f"לא נמצאו נתונים חודשיים עבור {current_ticker_for_display}.", 'warning')
        except Exception as e:
            current_app.logger.error(f"Error processing monthly chart for '{current_ticker_for_display}': {str(e)}")
            current_app.logger.exception("Detailed traceback for monthly chart error:")
            flash(f"שגיאה בהורדת/יצירת נתונים חודשיים עבור {current_ticker_for_display}: {str(e)}", 'danger')
        
        current_app.logger.debug(f"Rendering content_home.html after POST for ticker {current_ticker_for_display}")
        return render_template('content_home.html',
                               selected_ticker=current_ticker_for_display,
                               company_name=company_name_for_display,
                               chart1_json=chart1_json_for_display,
                               chart2_json=chart2_json_for_display,
                               chart3_json=chart3_json_for_display)

    if selected_ticker_from_session:
        current_app.logger.info(f"GET request: Displaying page for previously selected ticker (from session): '{selected_ticker_from_session}'.")
        company_name_for_display = session.get('company_name') 
    else:
        current_app.logger.info("GET request: No ticker in session, displaying initial empty home page.")

    current_app.logger.debug(f"Rendering content_home.html for GET request. Ticker for form: {selected_ticker_from_session}")
    return render_template('content_home.html',
                           selected_ticker=selected_ticker_from_session,
                           company_name=company_name_for_display,
                           chart1_json=chart1_json_for_display,
                           chart2_json=chart2_json_for_display,
                           chart3_json=chart3_json_for_display)