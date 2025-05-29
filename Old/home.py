# modules/routes/home.py
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from modules.price_history import get_price_history, get_company_name # ודא שהנתיב נכון אם הקבצים לא באותה תיקייה ישירות
from modules.chart_creator import create_candlestick_chart # ודא שהנתיב נכון
import pandas as pd

home_bp = Blueprint('home_bp', __name__)

@home_bp.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        ticker_symbol = request.form.get('ticker')
        if not ticker_symbol:
            flash('אנא הזן סימול טיקר.', 'warning')
            return redirect(url_for('home_bp.home'))

        session['selected_ticker'] = ticker_symbol.upper()
        company_name = get_company_name(session['selected_ticker'])
        session['company_name'] = company_name
        
        # ניקוי נתוני גרפים קודמים מהסשן לפני טעינה חדשה
        session.pop('chart1_json', None)
        session.pop('chart2_json', None)
        session.pop('chart3_json', None)

        # גרף 1: נתונים יומיים, 3 שנים אחורה, הצגת שנתיים
        try:
            daily_data_3y = get_price_history(session['selected_ticker'], period="3y", interval="1d")
            if not daily_data_3y.empty:
                session['chart1_json'] = create_candlestick_chart(
                    daily_data_3y,
                    chart_title=f"{company_name} ({session['selected_ticker']}) - מחירים יומיים (שנתיים אחרונות)",
                    display_years=2
                )
            else:
                 flash(f"לא נמצאו נתונים יומיים עבור {session['selected_ticker']}.", 'warning')
        except Exception as e:
            flash(f"שגיאה בהורדת נתונים יומיים עבור {session['selected_ticker']}: {str(e)}", 'danger')

        # גרף 2: נתונים שבועיים, 5 שנים אחורה
        try:
            weekly_data_5y = get_price_history(session['selected_ticker'], period="5y", interval="1wk")
            if not weekly_data_5y.empty:
                session['chart2_json'] = create_candlestick_chart(
                    weekly_data_5y,
                    chart_title=f"{company_name} ({session['selected_ticker']}) - מחירים שבועיים (5 שנים אחרונות)"
                )
            else:
                flash(f"לא נמצאו נתונים שבועיים עבור {session['selected_ticker']}.", 'warning')
        except Exception as e:
            flash(f"שגיאה בהורדת נתונים שבועיים עבור {session['selected_ticker']}: {str(e)}", 'danger')

        # גרף 3: נתונים חודשיים, 10 שנים אחורה
        try:
            monthly_data_10y = get_price_history(session['selected_ticker'], period="10y", interval="1mo")
            if not monthly_data_10y.empty:
                session['chart3_json'] = create_candlestick_chart(
                    monthly_data_10y,
                    chart_title=f"{company_name} ({session['selected_ticker']}) - מחירים חודשיים (10 שנים אחרונות)"
                )
            else:
                flash(f"לא נמצאו נתונים חודשיים עבור {session['selected_ticker']}.", 'warning')
        except Exception as e:
            flash(f"שגיאה בהורדת נתונים חודשיים עבור {session['selected_ticker']}: {str(e)}", 'danger')
        
        return redirect(url_for('home_bp.home'))

    # GET request logic
    selected_ticker = session.get('selected_ticker')
    company_name = session.get('company_name')
    chart1_json = session.get('chart1_json')
    chart2_json = session.get('chart2_json')
    chart3_json = session.get('chart3_json')

    if request.method == 'GET' and not selected_ticker:
        session.pop('company_name', None)
        session.pop('chart1_json', None)
        session.pop('chart2_json', None)
        session.pop('chart3_json', None)

    return render_template('content_home.html',
                           selected_ticker=selected_ticker,
                           company_name=company_name,
                           chart1_json=chart1_json,
                           chart2_json=chart2_json,
                           chart3_json=chart3_json)