#!/usr/bin/env python3
"""
Template Consolidation Script for Data Analyzer

This script consolidates templates from the root 'templates/' directory
into the more organized 'app/templates/' structure, mapping templates to
the appropriate blueprint subdirectories.

The script:
1. Creates a backup of each template file before moving
2. Maps templates to their appropriate blueprint based on patterns
3. Checks for duplicates to avoid overwriting
4. Provides a dry-run option to preview changes
5. Logs all operations
"""

import os
import shutil
import datetime
import sys
import re
from pathlib import Path


# Template mapping definitions
TEMPLATE_MAPPING = {
    # Templates that belong to auth blueprint
    'auth': [
        r'login\.html',
        r'register\.html',
    ],
    # Templates that belong to admin blueprint
    'admin': [
        r'admin/.*\.html',
    ],
    # Templates that belong to main blueprint
    'main': [
        r'home\.html',
        r'content_home\.html',
        r'evaluation_page\.html',
    ],
    # Templates for graphs blueprint
    'graphs': [
        r'graphs_page\.html',
    ],
    # Error pages and base templates
    'errors': [
        r'404\.html',
        r'500\.html',
        r'csrf_error\.html',
    ],
    # Base templates (to go in app/templates directly)
    'base': [
        r'base_layout\.html',
    ]
}


def create_log_entry(message):
    """Add a log entry to the consolidation log."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("template_consolidation.log", "a") as log_file:
        log_file.write(f"{timestamp} - {message}\n")
    print(message)


def map_template_to_blueprint(template_path):
    """Determine which blueprint a template belongs to based on its name."""
    template_name = os.path.basename(template_path)
    template_rel_path = os.path.relpath(template_path, 'templates')
    
    for blueprint, patterns in TEMPLATE_MAPPING.items():
        for pattern in patterns:
            if re.match(pattern, template_rel_path):
                return blueprint
    
    # If no match found, default to main blueprint
    return 'main'


def get_destination_path(template_path, blueprint):
    """Determine the destination path for a template based on its blueprint."""
    template_rel_path = os.path.relpath(template_path, 'templates')
    
    if blueprint == 'base':
        # Base templates go directly in app/templates
        return os.path.join('app/templates', template_rel_path)
    elif blueprint == 'errors':
        # Error templates go directly in app/templates
        return os.path.join('app/templates', template_rel_path)
    else:
        # Blueprint templates go in their respective subdirectories
        
        # Special case for admin templates already in admin/ subdirectory
        if template_rel_path.startswith('admin/'):
            return os.path.join('app/templates', template_rel_path)
            
        # For other templates, place them in their blueprint subdirectory
        return os.path.join('app/templates', blueprint, os.path.basename(template_rel_path))


def create_backup(file_path):
    """Create a backup of a file before modifying it."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.bak_{timestamp}"
    
    try:
        shutil.copy2(file_path, backup_path)
        create_log_entry(f"Created backup of {file_path} at {backup_path}")
        return True
    except Exception as e:
        create_log_entry(f"Error creating backup of {file_path}: {e}")
        return False


def process_template(template_path, dry_run=False):
    """Process a single template file for consolidation."""
    # Map template to blueprint
    blueprint = map_template_to_blueprint(template_path)
    
    # Determine destination path
    dest_path = get_destination_path(template_path, blueprint)
    
    # Log the mapping
    create_log_entry(f"Mapping: {template_path} -> {blueprint} blueprint at {dest_path}")
    
    # Check for duplicate
    if os.path.exists(dest_path):
        create_log_entry(f"WARNING: Destination file already exists: {dest_path}")
        
        # Compare files
        if os.path.getsize(template_path) == os.path.getsize(dest_path):
            with open(template_path, 'r') as f1, open(dest_path, 'r') as f2:
                if f1.read() == f2.read():
                    create_log_entry(f"Files are identical, skipping: {template_path}")
                    return True
        
        create_log_entry(f"Files differ, backup needed: {dest_path}")
        
        if not dry_run:
            if not create_backup(dest_path):
                create_log_entry(f"Error: Failed to backup {dest_path}, skipping...")
                return False
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    if not dry_run:
        try:
            # Copy the file
            shutil.copy2(template_path, dest_path)
            create_log_entry(f"Copied {template_path} to {dest_path}")
            return True
        except Exception as e:
            create_log_entry(f"Error copying {template_path} to {dest_path}: {e}")
            return False
    else:
        create_log_entry(f"[DRY RUN] Would copy {template_path} to {dest_path}")
        return True


def consolidate_templates(dry_run=False):
    """Consolidate all templates from templates/ to app/templates/ structure."""
    templates_dir = 'templates'
    
    if not os.path.exists(templates_dir) or not os.path.isdir(templates_dir):
        create_log_entry(f"Error: Templates directory not found: {templates_dir}")
        return False
    
    if not os.path.exists('app/templates'):
        if not dry_run:
            os.makedirs('app/templates', exist_ok=True)
            create_log_entry("Created app/templates directory")
        else:
            create_log_entry("[DRY RUN] Would create app/templates directory")
    
    # Process all template files
    success_count = 0
    error_count = 0
    skip_count = 0
    
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                template_path = os.path.join(root, file)
                
                if process_template(template_path, dry_run):
                    success_count += 1
                else:
                    error_count += 1
    
    create_log_entry(f"Template consolidation completed with {success_count} successes, {error_count} errors, and {skip_count} skipped")
    return error_count == 0


if __name__ == "__main__":
    print("=== Template Consolidation Tool ===")
    
    # Check for dry run flag
    dry_run = '--dry-run' in sys.argv
    if dry_run:
        print("Running in DRY RUN mode - no files will be changed")
    
    # Create log file
    with open("template_consolidation.log", "w") as log_file:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"{timestamp} - Starting template consolidation\n")
    
    # Run consolidation
    success = consolidate_templates(dry_run)
    
    if success:
        print("Template consolidation completed successfully")
        print("Check template_consolidation.log for details")
        
        if not dry_run:
            print("\nRemember to update your code to reference the new template locations.")
            print("The old templates are still in place, but should be removed once testing is complete.")
    else:
        print("Template consolidation completed with errors")
        print("Check template_consolidation.log for details")
        sys.exit(1)
    
    print("=== Operation completed ===")
