#!/usr/bin/env python3
"""
Template Loader Simplification Script for Data Analyzer

This script simplifies the template loader in app/__init__.py after all templates
have been consolidated into the app/templates/ structure. It removes the
ChoiceLoader configuration and uses the default Flask template loader with a
single path.

The script:
1. Creates a backup of app/__init__.py before modifying
2. Replaces the _configure_templates function with a simpler version
3. Logs the operation
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


def simplify_template_loader(dry_run=False):
    """Simplify the template loader in app/__init__.py."""
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
    
    # Define the current function pattern to replace
    current_function_pattern = r"def _configure_templates\(app: Flask\) -> None:.*?app\.logger\.debug\(f\'Template loader configured with paths: \{template_paths\}\'\)"
    
    # Define the new simplified function
    new_function = '''def _configure_templates(app: Flask) -> None:
    """
    Configure Jinja2 template loader to use app/templates directory.
    
    After template consolidation, all templates now live in the app/templates
    directory structure, organized by blueprint, so we no longer need the
    ChoiceLoader to search multiple directories.
    
    Args:
        app (Flask): Flask application instance
    """
    # No custom configuration needed, Flask will use the default
    # template folder at app/templates
    app.logger.debug('Using default template loader with app/templates')'''
    
    # Check if the pattern exists in the content
    if not re.search(current_function_pattern, content, re.DOTALL):
        print(f"Error: Could not find _configure_templates function in {init_path}")
        return False
    
    # Replace the function
    new_content = re.sub(current_function_pattern, new_function, content, flags=re.DOTALL)
    
    if not dry_run:
        # Write the modified content back to the file
        with open(init_path, 'w') as f:
            f.write(new_content)
        print(f"Successfully simplified template loader in {init_path}")
    else:
        print(f"[DRY RUN] Would simplify template loader in {init_path}")
    
    # Log the operation
    with open("template_loader_simplification.log", "w") as log_file:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"{timestamp} - {'Would simplify' if dry_run else 'Simplified'} template loader in {init_path}\n")
    
    return True


if __name__ == "__main__":
    print("=== Template Loader Simplification Tool ===")
    
    # Check for dry run flag
    dry_run = '--dry-run' in sys.argv
    if dry_run:
        print("Running in DRY RUN mode - no files will be changed")
    
    # Check if template consolidation is complete
    print("WARNING: This script should only be run after all templates have been consolidated")
    print("         into the app/templates/ structure.")
    
    if not dry_run:
        confirm = input("Have you completed template consolidation? (y/n): ")
        if confirm.lower() != 'y':
            print("Aborting. Please run template consolidation first.")
            sys.exit(1)
    
    # Run simplification
    success = simplify_template_loader(dry_run)
    
    if success:
        print("Template loader simplification completed successfully")
        if not dry_run:
            print("\nRemember to verify that your application still works correctly.")
            print("The simplified template loader now only looks in app/templates/.")
    else:
        print("Template loader simplification failed")
        sys.exit(1)
    
    print("=== Operation completed ===")
