#!/usr/bin/env python3
"""
Script to safely replace app.py with the modified version.

This script:
1. Creates a backup of the original app.py
2. Replaces app.py with app_modified.py
3. Logs the operation
"""

import os
import shutil
import datetime
import sys

def backup_and_replace_app_py():
    """
    Backup the original app.py and replace it with app_modified.py
    """
    # File paths
    original_app = "app.py"
    modified_app = "app_without_admin.py"
    
    # Check if files exist
    if not os.path.exists(original_app):
        print(f"Error: {original_app} not found")
        return False
    
    if not os.path.exists(modified_app):
        print(f"Error: {modified_app} not found")
        return False
    
    # Create backup with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"app.py.bak_{timestamp}"
    
    try:
        # Create backup
        shutil.copy2(original_app, backup_path)
        print(f"Created backup of {original_app} at {backup_path}")
        
        # Replace app.py with app_modified.py
        shutil.copy2(modified_app, original_app)
        print(f"Successfully replaced {original_app} with {modified_app} (authentication and admin routes removed)")
        
        # Append to log file
        with open("app_migration.log", "a") as log_file:
            log_file.write(f"{timestamp}: Replaced {original_app} with {modified_app}. Backup created at {backup_path}\n")
        
        return True
    
    except Exception as e:
        print(f"Error during replacement: {e}")
        return False

if __name__ == "__main__":
    print("Starting app.py replacement...")
    
    success = backup_and_replace_app_py()
    
    if success:
        print("Operation completed successfully")
        print("To test, run 'python run.py' and verify the application works correctly")
    else:
        print("Operation failed. Please check errors above")
        sys.exit(1)
