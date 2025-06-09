# app/auth/routes.py
"""
Authentication routes for user login, registration, and logout functionality.

This module contains all authentication-related routes including:
- User login and logout
- User registration with admin approval
- Session management
"""

from flask import render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import re

from app.auth import bp
from app.models import get_user_manager


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login functionality.
    
    GET: Display login form
    POST: Process login credentials and authenticate user
    
    Returns:
        Response: Login form on GET, redirect on successful POST
    """
    # Redirect if user is already authenticated
    if current_user.is_authenticated:
        current_app.logger.info(f"Already authenticated user '{current_user.username}' accessed login page")
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        current_app.logger.info(f"Login attempt for username: '{username}'")
        
        # Get user from user manager
        user_manager = get_user_manager()
        user_found = user_manager.get_user_by_username(username)
        
        # Validate credentials
        if user_found and check_password_hash(user_found.password_hash, password):
            # Check if user is approved
            if not user_found.is_approved:
                flash('חשבונך ממתין לאישור מנהל.', 'warning')
                current_app.logger.warning(f"Unapproved user '{username}' attempted to login.")
                return render_template('auth/login.html')
            
            # Log in the user
            login_user(user_found)
            current_app.logger.info(f"User '{username}' logged in successfully.")
            
            # Set session as permanent
            session.permanent = True
            
            # Redirect to next page or home
            next_page = request.args.get('next')
            if next_page and not (next_page.startswith('/') or next_page.startswith(request.host_url)):
                current_app.logger.warning(f"Potentially unsafe redirect attempt: {next_page}")
                next_page = None
            
            return redirect(next_page or url_for('main.index'))
        else:
            flash('שם משתמש או סיסמה שגויים.', 'danger')
            current_app.logger.warning(f"Failed login attempt for username: '{username}'")
    
    return render_template('auth/login.html')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handle user registration functionality.
    
    Creates new user accounts that require admin approval before login.
    
    Returns:
        Response: Registration form on GET, redirect on successful POST
    """
    # Redirect if user is already authenticated
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        current_app.logger.info(f"Registration attempt for username: '{username}'")
        
        # Validate form data
        if not username or not password or not confirm_password:
            flash('נא למלא את כל השדות.', 'danger')
            current_app.logger.warning(f"Registration failed: Empty fields for username '{username}'")
            return render_template('auth/register.html'), 400
        
        # Validate username format (alphanumeric and basic symbols)
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', username):
            flash('שם המשתמש יכול להכיל רק אותיות, מספרים, נקודה, מקף ומקף תחתון.', 'danger')
            current_app.logger.warning(f"Registration failed: Invalid username format '{username}'")
            return render_template('auth/register.html'), 400
        
        # Validate password length
        if len(password) < 6:
            flash('הסיסמה חייבת להכיל לפחות 6 תווים.', 'danger')
            current_app.logger.warning(f"Registration failed: Password too short for username '{username}'")
            return render_template('auth/register.html'), 400
        
        # Validate password confirmation
        if password != confirm_password:
            flash('הסיסמאות אינן תואמות.', 'danger')
            current_app.logger.warning(f"Registration failed: Password mismatch for username '{username}'")
            return render_template('auth/register.html'), 400
        
        # Check if username already exists
        user_manager = get_user_manager()
        if user_manager.username_exists(username):
            flash('שם המשתמש כבר קיים במערכת.', 'warning')
            current_app.logger.warning(f"Registration failed: Username '{username}' already exists.")
            return render_template('auth/register.html'), 400
        
        try:
            # Create new user (not approved by default)
            password_hash = generate_password_hash(password)
            new_user = user_manager.add_user(username, password_hash, is_approved=False)
            
            flash('ההרשמה הושלמה בהצלחה! אנא המתן לאישור מנהל.', 'success')
            current_app.logger.info(f"New user registered (pending approval): '{username}' with ID {new_user.id}.")
            
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            flash('שגיאה ביצירת החשבון. נסה שוב.', 'danger')
            current_app.logger.error(f"Registration error for username '{username}': {e}")
            return render_template('auth/register.html'), 500
    
    return render_template('auth/register.html')



@bp.route('/logout')
@login_required
def logout():
    """
    Handle user logout functionality.
    
    Logs out the current user and clears session data.
    
    Returns:
        Response: Redirect to login page with success message
    """
    username_on_logout = current_user.username
    
    # Clear custom session data (if any)
    from app.utils import clear_session_data
    clear_session_data()
    
    # Log out user
    logout_user()
    
    current_app.logger.info(f"User '{username_on_logout}' logged out and session data cleared.")
    flash('התנתקת בהצלחה.', 'info')
    
    return redirect(url_for('auth.login'))
