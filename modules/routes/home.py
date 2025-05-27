# modules/routes/home.py
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from modules.price_history import get_price_history, get_company_name
from modules.chart_creator import create_candlestick_chart
import pandas as pd

home_bp = Blueprint('home_bp', __name__)

@home_bp.route('/', methods=['GET', 'POST'])
def home():
    # אתחול משתנים שיועברו לתבנית
    # selected_ticker נלקח מהסשן כדי לאכלס מחדש את שדה הטופס אם הוא קיים
    selected_ticker_from_session = session.get('selected_ticker')
    
    # משתנים שיועברו לתבנית, מאותחלים ל-None או ערכי ברירת מחדל עבור בקשת GET
    # או אם אין נתונים ב-POST
    current_ticker_for_display = None
    company_name_for_display = None
    chart1_json_for_display = None
    chart2_json_for_display = None
    chart3_json_for_display = None

    if request.method == 'POST':
        ticker_symbol_from_form = request.form.get('ticker')
        if not ticker_symbol_from_form:
            flash('אנא הזן סימול טיקר.', 'warning')
            # אם הטופס נשלח ריק, עדיין נרצה להציג את הטיקר הקודם אם היה כזה
            return render_template('content_home.html',
                                   selected_ticker=selected_ticker_from_session) 

        # עדכון הטיקר שנבחר בסשן (לשימוש עתידי או לאכלוס חוזר של הטופס)
        session['selected_ticker'] = ticker_symbol_from_form.upper()
        current_ticker_for_display = session['selected_ticker'] # השתמש בטיקר המעודכן לתצוגה
        
        company_name_for_display = get_company_name(current_ticker_for_display)

        # גרף 1
        try:
            daily_data_3y = get_price_history(current_ticker_for_display, period="3y", interval="1d")
            if not daily_data_3y.empty:
                chart1_json_for_display = create_candlestick_chart(
                    daily_data_3y,
                    chart_title=f"{company_name_for_display} ({current_ticker_for_display}) - מחירים יומיים (שנתיים אחרונות)",
                    display_years=2
                )
            else:
                 flash(f"לא נמצאו נתונים יומיים עבור {current_ticker_for_display}.", 'warning')
        except Exception as e:
            flash(f"שגיאה בהורדת נתונים יומיים עבור {current_ticker_for_display}: {str(e)}", 'danger')

        # גרף 2
        try:
            weekly_data_5y = get_price_history(current_ticker_for_display, period="5y", interval="1wk")
            if not weekly_data_5y.empty:
                chart2_json_for_display = create_candlestick_chart(
                    weekly_data_5y,
                    chart_title=f"{company_name_for_display} ({current_ticker_for_display}) - מחירים שבועיים (5 שנים אחרונות)"
                )
            else:
                flash(f"לא נמצאו נתונים שבועיים עבור {current_ticker_for_display}.", 'warning')
        except Exception as e:
            flash(f"שגיאה בהורדת נתונים שבועיים עבור {current_ticker_for_display}: {str(e)}", 'danger')

        # גרף 3
        try:
            monthly_data_10y = get_price_history(current_ticker_for_display, period="10y", interval="1mo")
            if not monthly_data_10y.empty:
                chart3_json_for_display = create_candlestick_chart(
                    monthly_data_10y,
                    chart_title=f"{company_name_for_display} ({current_ticker_for_display}) - מחירים חודשיים (10 שנים אחרונות)"
                )
            else:
                flash(f"לא נמצאו נתונים חודשיים עבור {current_ticker_for_display}.", 'warning')
        except Exception as e:
            flash(f"שגיאה בהורדת נתונים חודשיים עבור {current_ticker_for_display}: {str(e)}", 'danger')
        
        # במקום redirect, אנחנו מרנדרים את התבנית ישירות עם הנתונים החדשים
        return render_template('content_home.html',
                               selected_ticker=current_ticker_for_display, # הטיקר שכרגע נבחר/עובד
                               company_name=company_name_for_display,
                               chart1_json=chart1_json_for_display,
                               chart2_json=chart2_json_for_display,
                               chart3_json=chart3_json_for_display)

    # לוגיקה עבור בקשת GET (כניסה ראשונית לדף או רענון ללא POST)
    # selected_ticker_from_session ישמש לאכלוס הטופס אם קיים
    # שאר המשתנים כבר מאותחלים ל-None, כך שלא יוצגו גרפים ישנים
    return render_template('content_home.html',
                           selected_ticker=selected_ticker_from_session, # לאכלוס הטופס
                           company_name=company_name_for_display,     # יהיה None
                           chart1_json=chart1_json_for_display,       # יהיה None
                           chart2_json=chart2_json_for_display,       # יהיה None
                           chart3_json=chart3_json_for_display)       # יהיה None