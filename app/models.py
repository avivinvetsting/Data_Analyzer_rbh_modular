# app/models.py
"""
Data models for the Data Analyzer application.

This module contains all data models and related database operations,
including the User model and user management functions.
"""

from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash
import json
import os
from typing import Dict, Optional


class User(UserMixin):
    """
    User model for authentication and authorization.
    
    Inherits from Flask-Login's UserMixin to provide default implementations
    for authentication-related methods (is_authenticated, is_active, etc.).
    
    Attributes:
        id (int): Unique user identifier
        username (str): User's login name
        password_hash (str): Hashed password for security
        is_approved (bool): Whether user is approved by admin
    """
    
    def __init__(self, id: int, username: str, password_hash: str, is_approved: bool = False):
        """
        Initialize a new User instance.
        
        Args:
            id (int): Unique user identifier
            username (str): User's login name
            password_hash (str): Hashed password
            is_approved (bool): Admin approval status, defaults to False
        """
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.is_approved = is_approved
    
    def __repr__(self) -> str:
        """String representation of User for debugging."""
        return f'<User {self.username}(id={self.id}, approved={self.is_approved})>'


class UserManager:
    """
    Manages user data persistence and operations.
    
    This class handles loading, saving, and managing users in the JSON file-based
    storage system. In a production environment, this could be replaced with
    a proper database ORM.
    """
    
    def __init__(self, users_file: Optional[str] = None):
        """
        Initialize UserManager with specified users file.
        
        Args:
            users_file (str, optional): Path to users JSON file.
                                      Uses config default if not provided.
        """
        self.users_file = users_file or current_app.config.get('USERS_FILE', 'users.json')
        self._users_cache: Dict[int, User] = {}
        self._load_users()
    
    def _load_users(self) -> None:
        """
        Load users from JSON file into memory cache.
        
        Creates initial admin user if file doesn't exist or is corrupted.
        """
        if not os.path.exists(self.users_file):
            current_app.logger.info(f"{self.users_file} not found. Creating initial admin user.")
            self._create_initial_admin()
            return
        
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
            
            # Convert JSON data to User objects
            self._users_cache = {
                int(uid): User(
                    int(uid),
                    data['username'],
                    data['password_hash'],
                    data.get('is_approved', False)
                )
                for uid, data in users_data.items()
            }
            
            current_app.logger.info(
                f"Users loaded successfully from {self.users_file}. Count: {len(self._users_cache)}"
            )
            
        except (IOError, json.JSONDecodeError, KeyError, TypeError) as e:
            current_app.logger.error(
                f"Error loading users from {self.users_file}: {e}. "
                "Falling back to initial admin user ONLY."
            )
            self._create_initial_admin()
    
    def _create_initial_admin(self) -> None:
        """
        Create initial admin user with credentials from configuration.
        """
        admin_username = current_app.config.get('ADMIN_USERNAME', 'admin')
        admin_password = current_app.config.get('ADMIN_PASSWORD', 'Admin123!')
        
        hashed_password = generate_password_hash(admin_password)
        current_app.logger.info(
            f"Creating admin user: {admin_username}, "
            f"Hashed password (prefix): {hashed_password[:10]}..."
        )
        
        admin_user = User(1, admin_username, hashed_password, True)
        self._users_cache = {1: admin_user}
        self.save_users()
    
    def save_users(self) -> bool:
        """
        Save current users cache to JSON file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert User objects to JSON-serializable format
            users_data = {
                str(uid): {
                    'username': user.username,
                    'password_hash': user.password_hash,
                    'is_approved': user.is_approved
                }
                for uid, user in self._users_cache.items()
            }
            
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(users_data, f, indent=4, ensure_ascii=False)
            
            current_app.logger.info("Users data saved successfully.")
            return True
            
        except IOError as e:
            current_app.logger.error(f"Error saving users data to {self.users_file}: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id (int): User ID to lookup
            
        Returns:
            User or None: User object if found, None otherwise
        """
        user = self._users_cache.get(user_id)
        if user:
            current_app.logger.debug(
                f"User loaded by ID: {user_id} -> {user.username} (Approved: {user.is_approved})"
            )
        else:
            current_app.logger.warning(f"User ID {user_id} not found in users cache.")
        return user
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username (str): Username to lookup
            
        Returns:
            User or None: User object if found, None otherwise
        """
        for user in self._users_cache.values():
            if user.username == username:
                return user
        return None
    
    def add_user(self, username: str, password_hash: str, is_approved: bool = False) -> User:
        """
        Add a new user to the system.
        
        Args:
            username (str): Username for new user
            password_hash (str): Hashed password
            is_approved (bool): Admin approval status
            
        Returns:
            User: Newly created user object
            
        Raises:
            ValueError: If username already exists
        """
        # Check if username already exists
        if self.get_user_by_username(username):
            raise ValueError(f"Username '{username}' already exists")
        
        # Generate new user ID
        new_id = max(self._users_cache.keys(), default=0) + 1
        
        # Create and store new user
        new_user = User(new_id, username, password_hash, is_approved)
        self._users_cache[new_id] = new_user
        
        # Save to file
        self.save_users()
        
        current_app.logger.info(
            f"New user created: '{username}' with ID {new_id} (Approved: {is_approved})"
        )
        
        return new_user
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        """
        Update user attributes.
        
        Args:
            user_id (int): ID of user to update
            **kwargs: Attributes to update
            
        Returns:
            bool: True if user was updated, False if not found
        """
        user = self.get_user(user_id)
        if not user:
            return False
        
        # Update allowed attributes
        for attr, value in kwargs.items():
            if hasattr(user, attr):
                setattr(user, attr, value)
                current_app.logger.info(f"Updated user {user_id} {attr} to {value}")
        
        self.save_users()
        return True
    
    def delete_user(self, user_id: int) -> bool:
        """
        Delete user from system.
        
        Args:
            user_id (int): ID of user to delete
            
        Returns:
            bool: True if user was deleted, False if not found
        """
        if user_id not in self._users_cache:
            return False
        
        username = self._users_cache[user_id].username
        del self._users_cache[user_id]
        self.save_users()
        
        current_app.logger.info(f"User deleted: '{username}' (ID: {user_id})")
        return True
    
    def get_all_users(self) -> Dict[int, User]:
        """
        Get all users in the system.
        
        Returns:
            Dict[int, User]: Dictionary mapping user IDs to User objects
        """
        return self._users_cache.copy()
    
    def username_exists(self, username: str) -> bool:
        """
        Check if username already exists in the system.
        
        Args:
            username (str): Username to check
            
        Returns:
            bool: True if username exists, False otherwise
        """
        return self.get_user_by_username(username) is not None


# Global user manager instance (will be initialized when app starts)
user_manager: Optional[UserManager] = None


def init_user_manager(app) -> None:
    """
    Initialize the global user manager with app configuration.
    
    Args:
        app: Flask application instance
    """
    global user_manager
    with app.app_context():
        user_manager = UserManager()


def get_user_manager() -> UserManager:
    """
    Get the global user manager instance.
    
    Returns:
        UserManager: Global user manager instance
        
    Raises:
        RuntimeError: If user manager hasn't been initialized
    """
    if user_manager is None:
        raise RuntimeError("User manager not initialized. Call init_user_manager() first.")
    return user_manager