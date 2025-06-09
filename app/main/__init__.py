# app/main/__init__.py
"""
Main blueprint for the Data Analyzer application.

This blueprint handles the core application functionality including
the home page and main user interface components.
"""

from flask import Blueprint

# Create the main application blueprint
bp = Blueprint('main', __name__, template_folder='templates')

# Import routes to register them with the blueprint
from app.main import routes