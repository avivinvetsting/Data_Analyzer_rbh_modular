#!/usr/bin/env python3
"""
Compatibility Routes Removal Script for Data Analyzer

This script removes the compatibility routes from app/__init__.py that were added
to maintain compatibility between the old and new routing structures during the
transition period. These routes are no longer needed now that we've consolidated
the templates and simplified the template loader.

The script:
1. Creates a backup of app/__init__.py before modifying
2. Identifies and removes the compatibility routes
3. Logs the operations for review
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


def remove_compatibility_routes(dry_run=False):
    """Remove compatibility routes from app/__init__.py."""
    init_path = 'app/__init__.py'
    
    if not os.path.exists(init_path):
        print(f"Error: {init_path} not found")
        return False
    
    # Read the file content
    with open(init_path, 'r') as f:
        content = f.read()
    
    # Create a backup
    if not dry_run:
        if not create_backup(init_path):
            print(f"Error: Failed to create backup of {init_path}")
            return False
    
    # Define the compatibility routes pattern to remove
    compat_routes_pattern = r"""def _register_compatibility_routes\(app: Flask\) -> None:
    \"\"\"
    Register compatibility routes to maintain backwards compatibility\.
    
    These routes ensure that old URLs and references continue to work
    during the transition to the new blueprint structure\.
    
    Args:
        app \(Flask\): Flask application instance
    \"\"\"
    @app\.route\('/login'\)
    def login_redirect\(\):
        \"\"\"Redirect old login URL to the auth blueprint login route\.\"\"\"
        app\.logger\.debug\("Compatibility redirect: /login -> auth\.login"\)
        return redirect\(url_for\('auth\.login'\)\)
    
    @app\.route\('/register'\)
    def register_redirect\(\):
        \"\"\"Redirect old register URL to the auth blueprint register route\.\"\"\"
        app\.logger\.debug\("Compatibility redirect: /register -> auth\.register"\)
        return redirect\(url_for\('auth\.register'\)\)
    
    @app\.route\('/logout'\)
    @login_required
    def logout_redirect\(\):
        \"\"\"Redirect old logout URL to the auth blueprint logout route\.\"\"\"
        app\.logger\.debug\("Compatibility redirect: /logout -> auth\.logout"\)
        return redirect\(url_for\('auth\.logout'\)\)
    
    app\.logger\.info\("Compatibility routes registered"\)"""
    
    # Check if the pattern exists in the content
    if not re.search(compat_routes_pattern, content, re.DOTALL):
        print(f"Warning: Could not find compatibility routes in {init_path}")
        print("The routes may have already been removed or have a different format.")
        return False
    
    # Remove the compatibility routes
    new_content = re.sub(compat_routes_pattern, "# Compatibility routes removed", content, flags=re.DOTALL)
    
    # Remove the call to _register_compatibility_routes in create_app
    create_app_call_pattern = r"    # Register compatibility routes\n    _register_compatibility_routes\(app\)"
    new_content = re.sub(create_app_call_pattern, "    # Compatibility routes removed", new_content, flags=re.DOTALL)
    
    if not dry_run:
        # Write the modified content back to the file
        with open(init_path, 'w') as f:
            f.write(new_content)
        print(f"Successfully removed compatibility routes from {init_path}")
    else:
        print(f"[DRY RUN] Would remove compatibility routes from {init_path}")
    
    # Log the operation
    with open("compatibility_routes_removal.log", "w") as log_file:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"{timestamp} - {'Would remove' if dry_run else 'Removed'} compatibility routes from {init_path}\n")
    
    return True


if __name__ == "__main__":
    print("=== Compatibility Routes Removal Tool ===")
    
    # Check for dry run flag
    dry_run = '--dry-run' in sys.argv
    if dry_run:
        print("Running in DRY RUN mode - no files will be changed")
    
    # Check if template consolidation is complete
    print("WARNING: This script should only be run after template consolidation and")
    print("         template loader simplification are complete and verified.")
    
    if not dry_run:
        confirm = input("Have you completed and verified these steps? (y/n): ")
        if confirm.lower() != 'y':
            print("Aborting. Please complete and verify these steps first.")
            sys.exit(1)
    
    # Run removal
    success = remove_compatibility_routes(dry_run)
    
    if success:
        print("Compatibility routes removal completed successfully")
        if not dry_run:
            print("\nRemember to verify that your application still works correctly.")
            print("The old /login, /register, and /logout routes will no longer work.")
            print("Users must use the blueprint routes directly (/auth/login, etc.).")
    else:
        print("Compatibility routes removal failed")
        sys.exit(1)
    
    print("=== Operation completed ===")
