Data_Analyzer - Project Map & Memory Bank
Last Updated: May 26, 2025 (תאריך עדכון לדוגמה)

This document provides a comprehensive map of the Data_Analyzer modular implementation, explaining the purpose and relationships between different components, key design decisions, historical context, and future considerations.

Overview
The Data_Analyzer application has been refactored from a monolithic structure (and earlier SimFin API dependency) into a modular, maintainable architecture focusing on loading and analyzing locally stored financial data. The application follows modern Python practices including:

Separation of concerns
Modular design
Blueprint-based routing
Comprehensive testing (planned/in-progress, as per README.md)
Configuration management
1. Overall Program Goal:
To create a web application (Flask-based in Python) that allows users to analyze financial data of companies.
The application retrieves financial statement data from locally stored CSV files and historical price data from Yahoo Finance.
The application processes and saves data (primarily uses the session for caching certain processed data like income statements as JSON) and presents it visually (interactive Plotly graphs).
Future functionality for performing valuations, user accounts, data export, and more is planned.
2. Core Components & File Structure:
2.1. Application Entry Point
File: app.py

Main entry point that configures the Flask application.
Sets up logging.
Registers blueprints for different sections.
Handles secret key management (checks for secrets.py or generates a default key).
2.2. Configuration
Directory: config/
File: config/config.ini (Expected)

Stores application settings like file paths and chart configurations.
Loaded by utils.config_loader.
2.3. Data Storage (Local CSVs for Financial Statements)
Directory: data/

data/Annual/[TICKER]/: Dynamically created directories for each ticker, storing annual financial statements as CSV files (e.g., Income_Statement.csv, Balance_Sheet.csv, Cash_Flow.csv).
data/Quarterly/[TICKER]/: Dynamically created directories for each ticker, storing quarterly financial statements as CSV files (similarly named).
(Price data from Yahoo Finance is typically fetched on demand and may be cached in session or processed without persistent raw storage by this app).
2.4. Core Functional Modules
Directory: modules/

File: modules/data_loader.py

Manages company name retrieval using yfinance (get_company_name_yf).
May contain utility functions for path resolution if ConfigLoader is used extensively for paths.
(SimFin API configuration and API key management have been removed).
File: modules/financial_statements.py

Loads financial statements (income, balance, cashflow; annual & quarterly) from local CSV files based on ticker and period type (using utils.helpers.get_statement_file_path).
Processes data: Loads specific statement CSV for a ticker.
Provides get_dataframe_from_session_or_csv for loading data, prioritizing session then local CSV.
Uses utils.helpers.ensure_directory_exists (implicitly, for potential future use if the app writes processed data, though currently it reads pre-existing CSVs).
File: modules/price_history.py

Downloads historical price data (OHLCV) using yfinance.
Calculates moving averages (e.g., MA20, MA50, MA100, MA150, MA200).
Can calculate additional technical indicators and summary statistics.
File: modules/chart_creator.py

Creates interactive time series charts (bar, line) using Plotly Express.
Generates candlestick charts with moving averages using Plotly Graph Objects.
Returns chart data as JSON (data and layout) for client-side rendering.
Handles cases of missing or invalid data for plotting.
2.5. Route Handlers (Blueprints)
Directory: modules/routes/

File: modules/routes/home.py (Blueprint: home_bp)

Handles the main home page display (/).
Processes ticker selection (POST request), triggers loading of local financial data and yfinance price data, and updates session.
(API key update functionality has been removed).
Displays candlestick chart and data load status.
Handles requests to update chart intervals for price data.
File: modules/routes/graphs.py (Blueprint: graphs_bp, prefix: /graphs)

Handles annual (/annual) and quarterly (/quarterly) graph views.
Generates and displays revenue and net income charts from financial statements.
Processes financial statements data for display, loading from session or local CSV via modules.financial_statements.
File: modules/routes/valuations.py (Blueprint: valuations_bp, prefix: /valuations)

Handles valuation-related views (/).
Currently a placeholder for future valuation metrics implementation.
2.6. Utility Modules
Directory: utils/

File: utils/config_loader.py

Manages application configuration.
Loads settings from config.ini.
Creates default configuration if config.ini is missing (default config now excludes SimFin-specific items).
Provides a centralized configuration interface.
File: utils/helpers.py

Contains common helper functions.
Key function: get_statement_file_path for determining paths to local CSV financial statements.
File path management (e.g., ensure_directory_exists).
(SimFin-related helpers like get_api_key_status_for_display have been removed).
Formatting utilities (e.g. format_number_for_display).
File: utils/decorators.py

Contains decorators like ticker_required to ensure a ticker is selected before accessing certain routes.
2.7. Templates & Static Files
Directory: templates/

base_layout.html: Main layout, includes sidebar, top ticker form. (API key modal removed).
content_home.html: Home page specific content, candlestick chart rendering script.
content_graphs.html: Graphs page specific content, financial chart rendering script.
content_valuations.html: Valuations page placeholder.
Directory: static/ (Standard Flask directory for CSS, JS, images - if used by the user)

2.8. Other Key Files
requirements.txt: Project dependencies (e.g., Flask, pandas, plotly, yfinance).
README.md: Main project documentation (needs update to Data_Analyzer).
secret.py (Optional, not in Git): For FLASK_SECRET_KEY.
app.log: Log file for application events.
tests/: Directory containing all test files (conftest.py, test_app.py, subdirectories like test_modules/, test_routes/, test_utils/).
3. Key Relationships & Data Flow:
Configuration Flow:

utils.config_loader loads settings from config/config.ini.
Route handlers and other modules may use this configuration for paths and settings.
(modules.data_loader no longer configures an external API based on these settings).
Data Processing Pipeline (on Ticker Selection):

User selects ticker in UI (form in base_layout.html).
modules.routes.home.route_set_ticker (POST) receives the ticker.
Triggers data loading:
modules.financial_statements.load_financial_statements_from_local (reads local CSV financial data).
modules.price_history.download_price_history_with_mavg (fetches Yahoo Finance price data).
Financial statements are read from data/[Annual/Quarterly]/[TICKER]/ by modules.financial_statements. The app does not save these CSVs; it assumes they pre-exist.
Key data (e.g., income statement DataFrames as JSON, data load status) is stored in the Flask session for caching.
User is redirected to the home page (or current page refreshed).
Visualization Chain:

When a page requiring charts is loaded (e.g., home, graphs):
Route handlers (e.g., in modules.routes.home, modules.routes.graphs) retrieve necessary data:
Price history from modules.price_history.
Financial statements by calling modules.financial_statements.get_dataframe_from_session_or_csv (which reads from session or local CSVs).
modules.chart_creator functions (create_candlestick_chart_with_mavg, create_timeseries_chart) transform data into Plotly figure JSON.
Route handlers pass this JSON to the HTML templates.
JavaScript in the templates (content_home.html, content_graphs.html) uses Plotly.newPlot() to render the charts client-side.
4. Key Design Decisions:
Modular Architecture: Transitioned to a modular structure using Flask Blueprints for better organization and maintainability.
Client-Side Graph Rendering: Plotly graphs are generated as JSON on the server and rendered in the browser using Plotly.js.
Data Source for Financial Statements: Financial statements are read from pre-existing local CSV files per ticker and period type. This removes external API dependencies for this data.
Data Caching (Session): Flask session is used to cache frequently accessed data (like income statements as JSON, ticker status) for the current user session, with a fallback to reading local CSVs.
(SimFin Data Retrieval Strategy and API Key Management are no longer applicable).
5. Historical Challenges & Solutions (Adapted):
TypeError with yfinance and older Python versions: Resolved by upgrading the Python environment (e.g., to Python 3.10+). (Still potentially relevant)
ModuleNotFoundError for yfinance (or other dependencies): Ensured correct installation within the active virtual environment. (simfin part is obsolete).
NameError for functions: Ensured proper function definitions before calls and correct imports between modules (aided by modularization). (Still relevant)
(SimFin load() error with ticker argument is obsolete).
Graphs not rendering in browser:
Initial issues with passing HTML directly.
Solved by server generating Plotly chart specs as JSON, and client-side JavaScript rendering.
Ensured up-to-date Plotly.js CDN link. (Still relevant)
CSV Permission Denied errors (for reading local files): User needs to ensure application has read permissions for the data/ directory and its contents. (Adapted)
Git Branch Management confusion: Explained correct Git commands. (Still relevant)
6. Current/Future Considerations & Enhancement Areas:
6.1. Core Functionality Enhancements
Graph Customization:
Allow user selection of moving averages and their periods for candlestick charts.
Enable user selection of date ranges for candlestick charts.
Add more financial statement items to graph (e.g., Gross Profit, Operating Income, FCF, R&D, SG&A) - dependent on these items being present in the local CSVs.
Valuation Module (modules/routes/valuations.py):
Define and implement specific valuation models (e.g., DCF, DDM, P/E, P/S, EV/EBITDA).
Require data from multiple financial statements (income, balance, cashflow loaded from local CSVs) and price data.
Error Handling & User Feedback: Continue to improve robustness and clarity of messages, especially around missing local data files or incorrect CSV formats.
Session Management:
Monitor session size.
Ensure proper clearing of ticker-specific session data.
6.2. Performance & Optimization
Local Data File I/O Efficiency: Reading CSV files repeatedly can be slow if files are very large or numerous.
Investigate optimizing DataFrame creation from CSVs.
Consider if a more efficient local storage format (e.g., Parquet, Feather, or a simple database like SQLite) might be beneficial if performance with CSVs becomes an issue, though this would be a significant change from the current CSV-based approach.
Data Caching: Implement more sophisticated server-side caching (beyond Flask session) for frequently accessed, less volatile data (e.g., using Flask-Caching) to reduce file I/O. Consider data expiration and refresh strategies if the underlying CSVs can change.
6.3. New Features (Long-Term)
User Accounts:
Implement user registration and login.
Allow users to save favorite tickers, custom analysis, or chart configurations.
Data Management Interface (Optional): If users need to update or add new CSV data, a simple interface to manage the data/ directory contents might be useful (though this adds complexity).
Export Functionality:
Allow exporting chart data or tables to CSV/Excel.
Generate PDF reports of analyses.
Advanced Analytics & Comparisons:
Sector comparison analysis (would require metadata about sectors for each ticker, perhaps from another local source).
Basic machine learning predictions (e.g., trend analysis based on historical data).
UI/UX Improvements:
More polished visual design.
Enhanced interactivity in charts.
6.4. Testing
Update and expand test coverage to reflect the new data loading mechanism (testing local file interactions, mocking pd.read_csv).
Ensure unit tests for all core modules and route tests for web interfaces are robust. Remove tests related to SimFin API interaction.
This comprehensive project_map.md should serve as an excellent "memory bank" for any AI tool, as well as for human developers working on the Data_Analyzer project.