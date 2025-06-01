# Project Map - Data Analyzer

## 📁 Directory Structure

```
Data_Analyzer/
├── app.py                     # Main application entry point
├── secret.py                  # Secret configuration (not in git)
├── requirements.txt           # Project dependencies
├── README.md                 # Project documentation
├── PROJECT_MAP.md            # This file - detailed project mapping
├── .env                      # Environment variables (not in git)
├── .gitignore               # Git ignore rules
│
├── modules/                  # Core functionality modules
│   ├── __init__.py
│   ├── price_history.py      # Price data retrieval and caching
│   ├── chart_creator.py      # Chart generation and styling
│   └── routes/              # Route handlers (Blueprints)
│       ├── __init__.py
│       ├── home.py          # Main routes and ticker analysis
│       ├── graphs.py        # Financial graphs routes
│       └── valuations.py    # Company valuation routes
│
├── templates/               # HTML templates
│   ├── base_layout.html    # Base template with common elements
│   ├── content_home.html   # Home page content
│   ├── graphs_page.html    # Graphs page template
│   ├── evaluation_page.html # Valuation page template
│   ├── login.html         # Login page
│   ├── register.html      # Registration page
│   └── admin/            # Admin templates
│       └── users.html    # User management page
│
├── static/                # Static files
│   ├── css/             # Stylesheets
│   ├── js/              # JavaScript files
│   └── img/             # Images and icons
│
├── tests/               # Test suite
│   ├── __init__.py
│   ├── test_routes.py   # Route tests
│   └── conftest.py      # Test configuration
│
└── logs/               # Application logs
    └── data_analyzer.log
```

## 🔄 Data Flow

1. **User Input**
   - Ticker symbol input
   - Time range selection
   - Chart type selection

2. **Data Retrieval** (`price_history.py`)
   - Yahoo Finance API calls
   - Data caching
   - Error handling

3. **Data Processing** (`chart_creator.py`)
   - OHLCV data processing
   - Technical indicators calculation
   - Chart data preparation

4. **Response Generation**
   - JSON chart data
   - Company information
   - Error messages

## 🛠️ Core Components

### 1. Data Management
- **Price History Module**
  - Real-time data fetching
  - Caching system
  - Data validation

- **Chart Creation Module**
  - Candlestick charts
  - Technical indicators
  - Chart styling

### 2. User Interface
- **Base Layout**
  - Navigation menu
  - Common elements
  - Responsive design

- **Content Pages**
  - Home page
  - Graph pages
  - Valuation pages

### 3. Authentication
- **User Management**
  - Login/Register
  - Password hashing
  - Session management

- **Admin Features**
  - User approval
  - User management
  - Access control

### 4. Security
- **Protection Mechanisms**
  - CSRF protection
  - Rate limiting
  - Input validation

- **Configuration**
  - Secret key management
  - Environment variables
  - Secure headers

## 🔍 Module Dependencies

```
app.py
├── modules/
│   ├── price_history.py
│   │   ├── yfinance
│   │   └── cachetools
│   │
│   ├── chart_creator.py
│   │   ├── plotly
│   │   └── pandas
│   │
│   └── routes/
│       ├── home.py
│       │   ├── price_history
│       │   └── chart_creator
│       │
│       ├── graphs.py
│       │   └── chart_creator
│       │
│       └── valuations.py
│           └── price_history
```

## 📊 Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_approved BOOLEAN DEFAULT FALSE
);
```

## 🔐 Security Measures

1. **Authentication**
   - Password hashing
   - Session management
   - Login attempts limiting

2. **Data Protection**
   - CSRF tokens
   - Secure cookies
   - Input sanitization

3. **Access Control**
   - Role-based access
   - Admin privileges
   - Rate limiting

## 🚀 Deployment

### Development
```bash
flask run
```

### Production
```bash
gunicorn app:app
```

## 📈 Monitoring

### Logging
- Application logs
- Error tracking
- User activity

### Performance
- Response times
- Cache hit rates
- API call statistics
