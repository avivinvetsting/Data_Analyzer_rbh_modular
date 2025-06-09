# app/auth/__init__.py
"""
Authentication blueprint for the Data Analyzer application.

This blueprint handles all authentication-related functionality including
user login, registration, logout, and user session management.
"""

from flask import Blueprint

# Create the authentication blueprint
bp = Blueprint('auth', __name__, template_folder='templates')

# Import routes to register them with the blueprint
from app.auth import routes