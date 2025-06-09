# Implementation Plan for Architecture Simplification

Based on the architecture analysis, here's a detailed plan to simplify the codebase and complete the migration to the Blueprint/Application Factory pattern.

## Phase 1: Utils Module and Dependency Resolution

### Create a Utilities Module

1. Create `app/utils.py` with session utility functions:
   ```python
   # app/utils.py
   """
   Utility functions for the Data Analyzer application.

   This module contains shared utility functions used across
   the application, extracted from legacy code to support
   the new architectural pattern.
   """

   from flask import session, current_app


   def clear_session_data():
       """
       Clear custom session data while preserving Flask-Login state.
       
       Removes all custom application data from the session
       but keeps the Flask-Login authentication information.
       """
       login_preserved_keys = ['_user_id', '_remember', '_fresh', '_id']
       
       # Get keys to clear (all except Flask-Login keys)
       keys_to_clear = [k for k in session.keys() if k not in login_preserved_keys]
       
       # Remove each key
       for key in keys_to_clear:
           session.pop(key, None)
       
       current_app.logger.debug(f"Cleared {len(keys_to_clear)} custom session keys")
   ```

2. Update `app/auth/routes.py` to use the new utility function:
   - Replace the import from `modules.routes.home` with import from `app.utils`

## Phase 2: Remove Duplicate Authentication Routes

1. Remove the following routes from `app.py`:
   - `/login`
   - `/register`
   - `/logout`

2. Update any templates or redirects to use blueprint routes:
   - Change `url_for('login')` to `url_for('auth.login')`
   - Change `url_for('register')` to `url_for('auth.register')`
   - Change `url_for('logout')` to `url_for('auth.logout')`

## Phase 3: Complete Admin Blueprint Migration

1. Remove admin routes from `app.py`:
   - `/admin/users`
   - `/admin/users/<int:user_id>/<action>`

2. Update any templates using these routes to reference the blueprint versions:
   - Change `url_for('manage_users')` to `url_for('admin.manage_users')`
   - Update form actions and links to point to blueprint routes

## Phase 4: Error Handler Migration

1. Move error handlers from `app.py` to `app/__init__.py`:
   - 404 handler
   - 500 handler
   - CSRF error handler

2. Ensure the handlers use the new blueprint route references

## Phase 5: Remove Legacy Entry Point

1. Remove the `if __name__ == '__main__':` block from `app.py`
2. Add a deprecation warning to `app.py`:
   ```python
   import warnings
   warnings.warn(
       "This module is deprecated. Use run.py as the application entry point instead.",
       DeprecationWarning, stacklevel=2
   )
   ```

## Phase 6: Clean Up Compatibility Layer

1. Create a migration plan for remaining legacy blueprints:
   - Determine which legacy blueprints (home_bp, graphs_bp, etc.) should be migrated
   - Plan the route migrations for each

2. Gradually move functionality from legacy blueprints to new structure:
   - Create corresponding routes in `app/main/routes.py`
   - Update templates to use new route references
   - Phase out the `register_legacy_blueprints` function as functionality is migrated

## Phase 7: Template Organization

1. Organize templates according to blueprint structure:
   - Move templates from root `templates/` to `app/templates/`
   - Ensure correct blueprint subdirectories: `auth/`, `admin/`, `main/`

2. Update template references in routes to use the new locations

## Phase 8: Documentation and Testing

1. Update docstrings to reflect the new architecture
2. Add migration notes for future developers
3. Test all functionality to ensure nothing was broken during migration

## Phase 9: Code Cleanup

1. Remove any remaining duplicate or unused code
2. Remove deprecated functionality with appropriate warnings
3. Consider refactoring any remaining complex functions

## Conclusion

This phased approach allows for gradual migration while maintaining a functioning application. Each phase can be implemented and tested separately, reducing the risk of breaking existing functionality. The end result will be a cleaner, more maintainable codebase that fully implements the Application Factory pattern and Blueprint structure outlined in the architecture proposal.
