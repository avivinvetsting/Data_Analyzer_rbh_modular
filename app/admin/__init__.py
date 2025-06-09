# app/admin/__init__.py
"""
Admin blueprint for the Data Analyzer application.

This blueprint handles administrative functionality including
user management, system administration, and admin-only features.
"""

from flask import Blueprint

# Create the admin blueprint
bp = Blueprint('admin', __name__, template_folder='templates')

# Import routes to register them with the blueprint
from app.admin import routes