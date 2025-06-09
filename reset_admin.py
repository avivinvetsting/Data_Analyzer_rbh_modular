#!/usr/bin/env python3
"""
Reset admin password script for Data Analyzer

This script resets the admin user's password to the default value.
Use this if you're having trouble logging in with the admin account.
"""

import json
import os
from werkzeug.security import generate_password_hash

# Configuration
USERS_FILE = 'users.json'
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'Admin123!'

def reset_admin_password():
    """Reset the admin user's password to the default value."""
    print(f"Resetting password for admin user to '{ADMIN_PASSWORD}'")
    
    # Check if users file exists
    if not os.path.exists(USERS_FILE):
        print(f"Error: {USERS_FILE} not found. Creating a new users file.")
        users_data = {}
    else:
        try:
            # Load existing users data
            with open(USERS_FILE, 'r') as f:
                users_data = json.load(f)
            print(f"Loaded existing users data from {USERS_FILE}")
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading {USERS_FILE}: {e}")
            print("Creating a new users file.")
            users_data = {}
    
    # Generate new password hash
    password_hash = generate_password_hash(ADMIN_PASSWORD)
    print(f"Generated new password hash")
    
    # Update or create admin user
    users_data["1"] = {
        "username": ADMIN_USERNAME,
        "password_hash": password_hash,
        "is_approved": True
    }
    
    # Save updated users data
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users_data, f, indent=4)
        print(f"Successfully updated {USERS_FILE}")
        print(f"You can now login with username '{ADMIN_USERNAME}' and password '{ADMIN_PASSWORD}'")
        return True
    except IOError as e:
        print(f"Error saving {USERS_FILE}: {e}")
        return False

if __name__ == "__main__":
    print("=== Admin Password Reset Tool ===")
    reset_admin_password()
    print("=== Operation completed ===")
