#!/usr/bin/env python3
"""
Script to revert English text assertions back to Hebrew to match the actual app
"""

import os
import re

# Mapping back to Hebrew text based on actual app messages
text_mappings = {
    'Stock Analysis - Home': 'ניתוח מניות - דף הבית',
    'Login': 'התחברות',
    'Register': 'הרשמה',
    'Annual Graphs': 'גרפים שנתיים',
    'Quarterly Graphs': 'גרפים רבעוניים', 
    'Valuations': 'הערכות שווי',
    'User Management': 'ניהול משתמשים',
    'Successfully logged out': 'התנתקת בהצלחה',
    "You don't have permission to access this page": 'אין לך הרשאות לגשת לדף זה',
    'Your account is pending admin approval': 'חשבונך ממתין לאישור מנהל',
    'Invalid username or password': 'שם משתמש או סיסמה שגויים',
    'Registration completed successfully': 'ההרשמה הושלמה בהצלחה',
    'Passwords do not match': 'הסיסמאות אינן תואמות',
    'Password must be at least 6 characters': 'הסיסמה חייבת להכיל לפחות 6 תווים',
    'Username already exists': 'שם המשתמש כבר קיים במערכת',
    'Please fill in all fields': 'נא למלא את כל השדות',
    'Successfully approved': 'אושר בהצלחה',
    'Successfully deleted': 'נמחק בהצלחה',
    'Cannot delete the primary admin account': 'לא ניתן למחוק את חשבון המנהל הראשי',
    'Invalid action': 'פעולה לא חוקית',
    'User not found': 'משתמש לא נמצא'
}

def update_file(file_path):
    """Update a single test file with corrected assertions"""
    print(f"Processing {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Replace text mappings
    for english, hebrew in text_mappings.items():
        # Look for patterns like assert 'english_text' in response.data.decode('utf-8')
        pattern = f"assert '{english}' in"
        replacement = f"assert '{hebrew}' in"
        content = content.replace(pattern, replacement)
        
        pattern = f'assert "{english}" in'
        replacement = f"assert '{hebrew}' in"
        content = content.replace(pattern, replacement)
        
        # Also handle patterns with "not in"
        pattern = f"assert '{english}' not in"
        replacement = f"assert '{hebrew}' not in"
        content = content.replace(pattern, replacement)
        
        pattern = f'assert "{english}" not in'
        replacement = f"assert '{hebrew}' not in"
        content = content.replace(pattern, replacement)
    
    # Special handling for the Home page assertion that was changed
    content = re.sub(
        r"assert \('Stock Analysis - Home' in response\.data\.decode\('utf-8'\) or 'Logged in as:' in response\.data\.decode\('utf-8'\)\)",
        "assert 'ניתוח מניות - דף הבית' in response.data.decode('utf-8')",
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
    
    print(f"\nReverted {total_updated} files to Hebrew")

if __name__ == "__main__":
    main()