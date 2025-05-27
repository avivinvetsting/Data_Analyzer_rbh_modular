# Data_Analyzer (Financial Data Analyzer)

A Flask (Python) web application for analyzing financial data of companies, focusing on downloading live data from Yahoo Finance using the `yfinance` library and displaying it in an interactive visual format using `Plotly`.

## Key Features

- Stock data display with user-input ticker functionality
- Dynamic data retrieval of historical price data (OHLCV) and full company names using `yfinance`
- Advanced visualization
  - Interactive candlestick charts using `Plotly`
  - Three different time ranges for analysis on the home page:
    1. Daily chart (showing last 2 years from 3 years of data)
    2. Weekly chart (last 5 years)
    3. Monthly chart (last 10 years)
  - Moving averages (MA20, MA50, MA100, MA150, MA200) added to all charts
- User Interface
  - Home page for ticker input and chart display
  - Side menu for navigation to future application sections (annual/quarterly financial statement charts, valuations)
  - User feedback messages (flash messages)
- Modular design with clear separation of responsibilities between application components (data loading, chart creation, routing)
- Blueprint architecture for organizing Flask routes
- Secret key management using `secret.py` (not in Git) for storing Flask's secret key
- Testing (in progress) Test infrastructure setup using `pytest`

## Installation

1. Clone the repository
    ```bash
    git clone your_repository_url
    cd Data_Analyzer
    ```

2. Create and activate a virtual environment
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3. Install required dependencies
    Ensure the `requirements.txt` file exists and contains the required libraries (see `requirements.txt` section below), then run:
    ```bash
    pip install -r requirements.txt
    ```

4. Configure the application
    Create a `secret.py` file in the project root with a unique `FLASK_SECRET_KEY`. For example:
    ```python
    # secret.py
    FLASK_SECRET_KEY = 'your_very_secure_random_secret_key_here_generated_by_you'
    ```
    Do not include this file in Git. (Add it to `.gitignore`).

## Usage

1. Run the application (from the main project directory `Data_Analyzer`)
    ```bash
    python app.py
    ```

2. Open your browser and navigate to [http://127.0.0.1:5000](http://127.0.0.1:5000)

3. Enter a stock ticker (e.g., AAPL, MSFT) in the search box in the top left corner and click "Select Stock and Load Data"
    Three candlestick charts with moving averages will be displayed for the selected ticker.

4. Navigate between pages using the side menu (currently, these pages are placeholders).

## Testing

Run the test suite using `pytest` from the main project directory:
```bash
pytest
```

Additional flags can be used as needed (e.g., without code coverage for speed during development):
```bash
pytest -p no:cov -p no:typeguard
```

## Project Structure

```
Data_Analyzer/
├── app.py                     # Main application entry point
├── secret.py                  # (Not in Git) Flask secret key
├── requirements.txt           # Project dependencies
├── modules/                   # Functional modules
│   ├── __init__.py
│   ├── price_history.py       # Price data and company name retrieval from yfinance
│   ├── chart_creator.py       # Interactive chart creation (Plotly)
│   └── routes/                # Route modules (Blueprints)
│       ├── __init__.py
│       ├── home.py            # Home page routes, ticker selection and chart display
│       ├── graphs.py          # Graph page routes (financial statements - placeholder)
│       └── valuations.py      # Valuation page routes (placeholder)
├── templates/                 # HTML templates
│   ├── base_layout.html       # Main base template
│   ├── content_home.html      # Home page content (including chart display)
│   ├── graphs_page.html       # General graphs page template (placeholder)
│   └── evaluation_page.html   # Valuation page template (placeholder)
├── tests/                     # Test directory
│   ├── __init__.py
│   └── test_routes.py         # Route tests
└── .gitignore                 # Git ignore file
```

## Core Design Decisions

- **Modular Architecture:** Using Flask Blueprints
- **Client-side Chart Rendering:** Plotly charts are created as JSON on the server and rendered in the browser using Plotly.js
- **Live Data Retrieval:** Using `yfinance` for up-to-date price data
- **Chart Data Transfer Without Large Session:** To prevent "session cookie too large" issues, chart JSON is passed directly from the route to the template during POST, not through the session. `session` is mainly used for storing the last entered ticker and `flash messages`

## Future Considerations and Improvements

- **Add option to hide/show moving averages** interactively in charts
- Further improve error handling and user feedback
- Develop functionality for financial statement charts and valuations pages
- Performance optimization if needed
- Expand test coverage
- Consider transitioning to AJAX for dynamic chart loading to further improve user experience
