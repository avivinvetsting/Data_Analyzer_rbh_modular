# Data_Analyzer - Project Map (Updated May 27, 2025)

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

This document provides a comprehensive map of the Data_Analyzer application, explaining the purpose and relationships between different components, key design decisions, and future developments.

## 1. Overall Program Purpose:

* Create a web application (Flask-based Python) that enables users to analyze financial data of companies.
* The application downloads historical price data and company names using the `yfinance` library.
* The application displays data visually using interactive `Plotly` candlestick charts, including moving averages.
* Future functionality planned for financial statement analysis, valuations, and more.

## 2. Core Components and File Structure:

### 2.1. Application Entry Point
**File**: `app.py`
* Main entry point that defines and runs the Flask application.
* Loads the secret key (`FLASK_SECRET_KEY`) from `secret.py`.
* Registers Blueprints for different parts of the application (`home_bp`, `graphs_bp`, `valuations_bp`).

### 2.2. Core Functional Modules (`modules/`)

**File**: `modules/price_history.py`
* Responsible for retrieving historical price data (OHLCV) using `yfinance` (`get_price_history`).
* Responsible for retrieving full company names using `yfinance` (`get_company_name`).

**File**: `modules/chart_creator.py`
* Function `create_candlestick_chart` creates interactive candlestick charts with `Plotly` from the received data.
* The function includes calculation and addition of moving averages (20, 50, 100, 150, 200) to the charts.
* Returns chart data as JSON for client-side rendering.

### 2.3. Route Handlers (Blueprints) (`modules/routes/`)

**File**: `modules/routes/home.py` (Blueprint: `home_bp`, route: `/`)
* Handles the main home page display and ticker input from users.
* Receives `GET` requests for page display and `POST` requests for ticker processing.
* After receiving a ticker via `POST`:
    * Activates `price_history.py` to download price data and company name.
    * Activates `chart_creator.py` to create JSON for three charts (daily, weekly, monthly) with moving averages.
    * Passes the chart JSON directly to the `content_home.html` template for rendering (without using session for the JSON itself).
* Uses `flash` for displaying user messages.

**File**: `modules/routes/graphs.py` (Blueprint: `graphs_bp`, prefix: `/graphs`)
* Handles graph views (currently placeholders): annual (`/annual`) and quarterly (`/quarterly`).
* Renders the `graphs_page.html` template.

**File**: `modules/routes/valuations.py` (Blueprint: `valuations_bp`, prefix: `/valuations`)
* Handles views related to valuations (`/`).
* Renders the `evaluation_page.html` template (currently placeholder).

### 2.4. HTML Templates (`templates/`)

* `base_layout.html`: Main base template. Includes:
    * Top bar with ticker input form (located in top left).
    * Side menu for navigation.
    * Content (`{% block content %}`) and title (`{% block title %}`) blocks.
* `content_home.html`: Home page specific content.
    * Displays the company name and selected ticker.
    * Shows `flash` messages.
    * Includes `div`s for each of the three charts.
    * Contains JavaScript for loading `Plotly.js` and rendering charts from the server-passed JSON.
* `graphs_page.html`: Template placeholder for graph pages.
* `evaluation_page.html`: Template placeholder for valuation page.

### 2.5. Other Key Files

* `secret.py` (not in Git): Contains the `FLASK_SECRET_KEY`.
* `requirements.txt`: Lists project dependencies.
* `tests/test_routes.py`: Contains basic unit tests for routes.

## 3. Key Relationships and Data Flow (for Home Page):

1. User enters a ticker in the form in `base_layout.html` and submits (POST to `/`).
2. The `home()` function in `modules/routes/home.py` receives the ticker.
3. `home()` calls `get_company_name` and `get_price_history` from `modules/price_history.py` to retrieve data.
4. `home()` calls `create_candlestick_chart` from `modules/chart_creator.py` for each required time range, creating JSON for charts with moving averages.
5. `home()` passes the chart JSON, company name, and ticker directly to the `render_template` function with the `content_home.html` template.
6. `content_home.html` uses JavaScript and Plotly.js to render the charts from the received JSON.

## 4. Key Design Decisions (Current):

* **Modular Architecture:** Using Flask Blueprints.
* **Client-side Chart Rendering:** Plotly charts are created as JSON on the server and rendered in the browser using Plotly.js.
* **Live Data Retrieval:** Using `yfinance` for up-to-date price data.
* **Chart Data Transfer Without Large Session:** To prevent "session cookie too large" issues, chart JSON is passed directly from the route to the template during POST, not through the session. `session` is mainly used for storing the last entered ticker and `flash messages`.

## 5. Future Considerations and Areas for Improvement:

* **Add option to hide/show moving averages** interactively in charts.
* Further improve error handling and user feedback.
* Develop functionality for financial statement charts and valuations pages.
* Performance optimization if needed.
* Expand test coverage.
* Consider transitioning to AJAX for dynamic chart loading to further improve user experience.