# app/admin/routes.py
"""
Administrative routes for user management and system administration.

This module contains all admin-only routes including:
- User management (approve, delete users)
- System administration
- Admin dashboard
"""

from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user

from app.admin import bp
from app.models import get_user_manager


def admin_required(f):
    """
    Decorator to require admin privileges for accessing a route.
    
    Args:
        f: Function to decorate
        
    Returns:
        Function: Decorated function that checks admin status
    """
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.id != 1:
            flash('אין לך הרשאות לגשת לדף זה.', 'danger')
            current_app.logger.warning(
                f"User '{current_user.username}' (ID: {current_user.id}) "
                "denied access to admin functionality."
            )
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


@bp.route('/users')
@login_required
@admin_required
def manage_users():
    """
    Display user management interface for admin.
    
    Shows all users in the system with options to approve or delete them.
    
    Returns:
        Response: User management template with user data
    """
    current_app.logger.info(f"Admin user '{current_user.username}' accessed user management.")
    
    # Get all users from user manager
    user_manager = get_user_manager()
    all_users = user_manager.get_all_users()
    
    # Convert to list of user objects for template
    users_list = list(all_users.values())
    
    return render_template('admin/users.html', users=users_list)


@bp.route('/users/<int:user_id>/<action>')
@login_required
@admin_required
def user_action(user_id, action):
    """
    Handle admin actions on user accounts.
    
    Supports approve and delete actions for user management.
    
    Args:
        user_id (int): ID of the user to act upon
        action (str): Action to perform ('approve' or 'delete')
        
    Returns:
        Response: Redirect to user management page with status message
    """
    current_app.logger.info(
        f"Admin '{current_user.username}' attempting action '{action}' on user ID {user_id}."
    )
    
    user_manager = get_user_manager()
    target_user = user_manager.get_user(user_id)
    
    # Check if user exists
    if not target_user:
        flash('משתמש לא נמצא.', 'danger')
        current_app.logger.warning(f"User action failed: User ID {user_id} not found.")
        return redirect(url_for('admin.manage_users'))
    
    # Handle different actions
    if action == 'approve':
        # Approve user
        success = user_manager.update_user(user_id, is_approved=True)
        if success:
            flash(f'משתמש {target_user.username} אושר בהצלחה.', 'success')
            current_app.logger.info(
                f"User '{target_user.username}' (ID: {user_id}) was approved by admin '{current_user.username}'."
            )
        else:
            flash('שגיאה באישור המשתמש.', 'danger')
            current_app.logger.error(f"Failed to approve user ID {user_id}")
    
    elif action == 'delete':
        # Prevent admin from deleting themselves
        if user_id == 1:
            flash('לא ניתן למחוק את חשבון המנהל הראשי.', 'danger')
            current_app.logger.warning(
                f"Admin '{current_user.username}' attempted to delete admin account (ID: 1)."
            )
            return redirect(url_for('admin.manage_users'))
        
        # Delete user
        username = target_user.username
        success = user_manager.delete_user(user_id)
        if success:
            flash(f'משתמש {username} נמחק/נדחה בהצלחה.', 'success')
            current_app.logger.info(
                f"User '{username}' (ID: {user_id}) was deleted by admin '{current_user.username}'."
            )
        else:
            flash('שגיאה במחיקת המשתמש.', 'danger')
            current_app.logger.error(f"Failed to delete user ID {user_id}")
    
    else:
        # Invalid action
        flash('פעולה לא חוקית.', 'danger')
        current_app.logger.warning(
            f"Invalid action '{action}' attempted by admin '{current_user.username}' on user ID {user_id}."
        )
    
    return redirect(url_for('admin.manage_users'))


@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """
    Admin dashboard with system overview and statistics.
    
    Returns:
        Response: Admin dashboard template with system information
    """
    current_app.logger.info(f"Admin '{current_user.username}' accessed admin dashboard.")
    
    # Get system statistics
    user_manager = get_user_manager()
    all_users = user_manager.get_all_users()
    
    stats = {
        'total_users': len(all_users),
        'approved_users': sum(1 for user in all_users.values() if user.is_approved),
        'pending_users': sum(1 for user in all_users.values() if not user.is_approved),
    }
    
    return render_template('admin/dashboard.html', stats=stats)