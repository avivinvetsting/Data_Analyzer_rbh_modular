# Data_Analyzer - Project Map (Updated May 27, 2025)

## Project Structure
```
Data_Analyzer/
│
├── app.py                  # קובץ ראשי, אתחול Flask, רישום Blueprints
├── requirements.txt        # תלויות
├── secret.py               # מפתח סודי (לא ב-VCS)
│
├── modules/
│   ├── routes/
│   │   ├── home.py         # דף הבית, ניתוח טיקר, שליחת נתונים ל-HTML
│   │   ├── graphs.py       # גרפים שנתיים/רבעוניים (placeholder)
│   │   └── valuations.py   # עמוד הערכות שווי (placeholder)
│   ├── price_history.py    # שליפת נתוני מחיר מ-yfinance, מידע על חברה
│   ├── chart_creator.py    # יצירת גרפי נרות (Plotly), פונקציות עזר לגרפים
│   └── data_fetcher.py     # (ייתכן שאינו בשימוש, היסטורי)
│
├── templates/
│   ├── base_layout.html    # תבנית בסיסית, תפריט, טעינת Plotly
│   ├── content_home.html   # דף הבית: טופס, גרפים, מידע חברה
│   ├── graphs_page.html    # עמוד גרפים (placeholder)
│   └── evaluation_page.html# עמוד הערכות שווי (placeholder)
│
├── static/                 # קבצי CSS/JS נוספים (אם יש)
│
├── logs/
│   └── data_analyzer.log   # קובץ לוגים ראשי
│
└── tests/
    └── test_routes.py      # בדיקות מסלולים בסיסיות

זרימת נתונים לגרפי נרות
המשתמש מזין טיקר ב־base_layout.html או content_home.html.
routes/home.py:
קורא ל־get_price_history (מ־price_history.py) עבור שלושה טווחים (יומי, שבועי, חודשי).
יוצר שלושה גרפים עם create_candlestick_chart (מ־chart_creator.py).
שולח את ה־JSON ל־content_home.html.
content_home.html:
מציג את שם החברה.
מציג שלושה גרפים (Plotly) ומידע על החברה.
ה־JS משתמש ב־JSON.parse כדי להמיר את ה־JSON לאובייקט JS ולרנדר את הגרפים.
3. אבטחה
כל המסלולים המרכזיים מוגנים ב־@login_required.
CSRF מופעל בכל הטפסים.
4. בדיקות
קיים קובץ tests/test_routes.py עם בדיקות גישה לדפים (דורש התחברות).
