#!/usr/bin/env python3
"""
Fix for redirect loop issue in Data Analyzer application.

This script updates the app/main/routes.py file to prevent circular redirects
by having the main index route render the template directly instead of redirecting
to the home_bp.index route.
"""

import os
import shutil
import datetime
import sys
import re


def create_backup(file_path):
    """Create a backup of a file before modifying it."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.bak_{timestamp}"
    
    try:
        shutil.copy2(file_path, backup_path)
        print(f"Created backup of {file_path} at {backup_path}")
        return True
    except Exception as e:
        print(f"Error creating backup of {file_path}: {e}")
        return False


def fix_redirect_loop(dry_run=False):
    """Fix the redirect loop in app/main/routes.py."""
    routes_path = 'app/main/routes.py'
    
    if not os.path.exists(routes_path):
        print(f"Error: {routes_path} not found")
        return False
    
    # Read the file content
    with open(routes_path, 'r') as f:
        content = f.read()
    
    # Create a backup
    if not dry_run:
        if not create_backup(routes_path):
            print(f"Error: Failed to create backup of {routes_path}")
            return False
    
    # Define the current function to replace
    current_function_pattern = r'''@bp\.route\('\/'\)
@login_required
def index\(\):
    """
    Main application home page\.
    
    Redirects to the existing home blueprint to maintain compatibility
    with the current modular structure\.
    
    Returns:
        Response: Redirect to home_bp\.index
    """
    # Import here to avoid circular imports
    from modules\.routes\.home import home_bp
    from flask import redirect, url_for
    
    current_app\.logger\.debug\("Main index route accessed, redirecting to home_bp\.index"\)
    return redirect\(url_for\('home_bp\.index'\)\)'''
    
    # Define the new function to avoid redirect loops
    new_function = '''@bp.route('/')
@login_required
def index():
    """
    Main application home page.
    
    Renders the home page template directly to avoid redirect loops.
    
    Returns:
        Response: Rendered content_home.html template
    """
    from flask import render_template, session
    
    current_app.logger.debug(f"User '{current_user.username}' accessed home page (main.index route)")
    template_data = {
        'selected_ticker': session.get('selected_ticker'),
        'company_name': session.get('company_name'),
        'company_info': session.get('company_info'),
        'chart1_json': None,
        'chart2_json': None,
        'chart3_json': None
    }
    return render_template('content_home.html', **template_data)'''
    
    # Check if the pattern exists in the content
    if not re.search(current_function_pattern, content, re.DOTALL):
        print(f"Error: Could not find the expected index function in {routes_path}")
        return False
    
    # Add the current_user import
    updated_imports = 'from flask import current_app\nfrom flask_login import login_required, current_user'
    content = content.replace('from flask import current_app\nfrom flask_login import login_required', updated_imports)
    
    # Replace the function
    new_content = re.sub(current_function_pattern, new_function, content, flags=re.DOTALL)
    
    if not dry_run:
        # Write the modified content back to the file
        with open(routes_path, 'w') as f:
            f.write(new_content)
        print(f"Successfully updated {routes_path} to fix redirect loop")
    else:
        print(f"[DRY RUN] Would update {routes_path} to fix redirect loop")
    
    # Log the operation
    with open("redirect_loop_fix.log", "w") as log_file:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"{timestamp} - {'Would fix' if dry_run else 'Fixed'} redirect loop in {routes_path}\n")
    
    return True


if __name__ == "__main__":
    print("=== Redirect Loop Fix Tool ===")
    
    # Check for dry run flag
    dry_run = '--dry-run' in sys.argv
    if dry_run:
        print("Running in DRY RUN mode - no files will be changed")
    
    # Run fix
    success = fix_redirect_loop(dry_run)
    
    if success:
        print("Redirect loop fix completed successfully")
        if not dry_run:
            print("\nPlease restart the application to apply the changes.")
            print("The fix prevents circular redirects between main.index and home_bp.index.")
    else:
        print("Redirect loop fix failed")
        sys.exit(1)
    
    print("=== Operation completed ===")
