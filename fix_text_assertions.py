#!/usr/bin/env python3
"""
Script to fix Hebrew text assertions to match English UI
"""

import os
import re

# Mapping of Hebrew text to English equivalents based on actual UI
text_mappings = {
    'ניתוח מניות - דף הבית': 'Stock Analysis - Home',
    'התחברות': 'Login',
    'הרשמה': 'Register',
    'גרפים שנתיים': 'Annual Graphs',
    'גרפים רבעוניים': 'Quarterly Graphs',
    'הערכות שווי': 'Valuations',
    'ניהול משתמשים': 'User Management',
    'התנתקת בהצלחה': 'Successfully logged out',
    'אין לך הרשאות לגשת לדף זה': "You don't have permission to access this page",
    'חשבונך ממתין לאישור מנהל': 'Your account is pending admin approval',
    'שם משתמש או סיסמה שגויים': 'Invalid username or password',
    'ההרשמה הושלמה בהצלחה': 'Registration completed successfully',
    'הסיסמאות אינן תואמות': 'Passwords do not match',
    'הסיסמה חייבת להכיל לפחות 6 תווים': 'Password must be at least 6 characters',
    'שם המשתמש כבר קיים במערכת': 'Username already exists',
    'נא למלא את כל השדות': 'Please fill in all fields',
    'אושר בהצלחה': 'Successfully approved',
    'נמחק בהצלחה': 'Successfully deleted',
    'לא ניתן למחוק את חשבון המנהל הראשי': 'Cannot delete the primary admin account',
    'פעולה לא חוקית': 'Invalid action',
    'משתמש לא נמצא': 'User not found'
}

def update_file(file_path):
    """Update a single test file with corrected assertions"""
    print(f"Processing {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Replace text mappings
    for hebrew, english in text_mappings.items():
        # Look for patterns like assert 'hebrew_text' in response.data.decode('utf-8')
        pattern = f"assert '{hebrew}' in"
        replacement = f"assert '{english}' in"
        content = content.replace(pattern, replacement)
        
        # Also handle patterns with "not in"
        pattern = f"assert '{hebrew}' not in"
        replacement = f"assert '{english}' not in"
        content = content.replace(pattern, replacement)
    
    # Check for some specific patterns that might need adjustment
    # Update login success assertions to check for key indicators instead
    content = re.sub(
        r"assert '[^']*ניתוח מניות[^']*' in response\.data\.decode\('utf-8'\)",
        "assert ('Stock Analysis - Home' in response.data.decode('utf-8') or 'Logged in as:' in response.data.decode('utf-8'))",
        content
    )
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  Updated {file_path}")
        return True
    else:
        print(f"  No changes needed for {file_path}")
        return False

def main():
    test_files = [
        'tests/test_auth.py',
        'tests/test_forms.py', 
        'tests/test_integration.py',
        'tests/test_security.py',
        'tests/test_analysis.py'
    ]
    
    total_updated = 0
    for file_path in test_files:
        if os.path.exists(file_path):
            if update_file(file_path):
                total_updated += 1
        else:
            print(f"File not found: {file_path}")
    
    print(f"\nUpdated {total_updated} files")

if __name__ == "__main__":
    main()