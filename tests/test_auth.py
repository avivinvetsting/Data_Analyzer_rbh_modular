# tests/test_auth.py
import pytest
from unittest.mock import patch, MagicMock
from flask import session, current_app, request, url_for
from werkzeug.security import check_password_hash
import os
import json
from urllib.parse import unquote # הוספנו unquote

# ייבוא מהאפליקציה שלך (ודא שהנתיבים נכונים)
from app import User, USERS_FILE, save_users, load_users, generate_password_hash
# נייבא את משתני האדמין מ-conftest כי הם מוגדרים שם עם fallback
# הנחה ש-conftest.py נמצא באותה תיקייה (tests)
from .conftest import ADMIN_USERNAME, ADMIN_PASSWORD


@pytest.fixture
def temp_users_file_for_auth(tmp_path, app): # ה-app fixture מגיע מ-conftest.py
    """
    Fixture to create a temporary and clean users file for auth tests.
    It patches app.USERS_FILE and reloads app.USERS.
    """
    original_users_file_in_app_module = app.config.get('_ORIGINAL_USERS_FILE_FOR_TEST_AUTH', None)
    
    # גישה ישירה למשתנה הגלובלי USERS_FILE במודול app
    import app as main_app_module 
    if original_users_file_in_app_module is None:
        original_users_file_in_app_module = main_app_module.USERS_FILE
        app.config['_ORIGINAL_USERS_FILE_FOR_TEST_AUTH'] = original_users_file_in_app_module
    
    temp_file_path = tmp_path / "temp_auth_users.json"
    
    # יצירת קובץ התחלתי עם משתמש אדמין בלבד
    admin_hashed_password = generate_password_hash(ADMIN_PASSWORD)
    initial_users_data = {
        "1": {"username": ADMIN_USERNAME, "password_hash": admin_hashed_password, "is_approved": True}
    }
    with open(temp_file_path, 'w') as f:
        json.dump(initial_users_data, f)
    
    # Patching app.USERS_FILE וטעינה מחדש של USERS בתוך מודול app
    with patch('app.USERS_FILE', str(temp_file_path)):
        main_app_module.USERS = main_app_module.load_users() # טעינה מחדש מהקובץ הזמני
        yield str(temp_file_path) # הבדיקה תשתמש בקובץ זה
    
    # שחזור אופציונלי: אם רוצים להחזיר את המצב לקדמותו באופן מפורש
    # setattr(main_app_module, 'USERS_FILE', original_users_file_in_app_module)
    # main_app_module.USERS = main_app_module.load_users() # טעינה מחדש מהנתיב המקורי


class TestAuthentication:

    def test_login_successful(self, client, temp_users_file_for_auth):
        # temp_users_file_for_auth מבטיח שמשתמש אדמין קיים בקובץ הזמני
        response = client.post('/login', data={
            'username': ADMIN_USERNAME,
            'password': ADMIN_PASSWORD
        }, follow_redirects=True)
        assert response.status_code == 200
        response_text = response.data.decode('utf-8')
        assert 'שם משתמש או סיסמה שגויים.' not in response_text
        # בדוק טקסט שמצביע על התחברות מוצלחת, למשל כפתור Logout או הודעת ברוכים הבאים
        # אם תבנית הבית שלך מציגה את שם המשתמש:
        # assert f'Welcome, {ADMIN_USERNAME}' in response_text 
        assert 'Logout' in response_text # או כל טקסט אחר שמצביע על כך שהמשתמש מחובר
        with client.session_transaction() as sess:
            assert sess.get('_user_id') is not None

    def test_login_failed_wrong_password(self, client, temp_users_file_for_auth):
        response = client.post('/login', data={
            'username': ADMIN_USERNAME,
            'password': 'wrongpassword'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert 'שם משתמש או סיסמה שגויים.' in response.data.decode('utf-8')

    def test_login_failed_nonexistent_user(self, client, temp_users_file_for_auth):
        response = client.post('/login', data={
            'username': 'nouser',
            'password': 'password'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert 'שם משתמש או סיסמה שגויים.' in response.data.decode('utf-8')

    def test_login_to_protected_page_redirect(self, client):
        # נניח ש- /admin/users הוא דף מוגן
        response_admin_page = client.get('/admin/users', follow_redirects=False) # אל תעקוב אחרי הפניות
        assert response_admin_page.status_code == 302 # צפה להפניה
        
        # השווה את הנתיב המלא (כולל query string) לאחר unquote
        expected_redirect_url = url_for('login', next='/admin/users', _external=False)
        actual_location_decoded = unquote(response_admin_page.location)
        assert actual_location_decoded == expected_redirect_url

        # בצע את ההפניה ידנית כדי לבדוק את דף ההתחברות
        response_after_redirect = client.get(response_admin_page.location) 
        assert response_after_redirect.status_code == 200
        # בדוק תוכן ספציפי מדף ההתחברות login.html
        assert 'Username:' in response_after_redirect.data.decode('utf-8') 
        assert 'Password:' in response_after_redirect.data.decode('utf-8')
        
    def test_registration_successful(self, client, temp_users_file_for_auth):
        with patch('app.USERS_FILE', temp_users_file_for_auth):
            import app as main_app_module
            main_app_module.USERS = main_app_module.load_users()
            original_users_count = len(main_app_module.USERS)
            new_username = 'newtestuser_auth'
            response = client.post('/register', data={
                'username': new_username,
                'password': 'newpassword123',
                'confirm_password': 'newpassword123'
            }, follow_redirects=True) 
            assert response.status_code == 200 
            assert 'ההרשמה הושלמה בהצלחה! אנא המתן לאישור מנהל.' in response.data.decode('utf-8')
            main_app_module.USERS = main_app_module.load_users()
            assert len(main_app_module.USERS) == original_users_count + 1
            new_user = next((u for u in main_app_module.USERS.values() if u.username == new_username), None)
            assert new_user is not None
            assert not new_user.is_approved

    def test_registration_with_mismatched_passwords(self, client):
        response = client.post('/register', data={
            'username': 'testuser1_auth_mismatch', 'password': 'password123', 'confirm_password': 'password456'
        }) 
        assert response.status_code == 400 
        assert 'הסיסמאות אינן תואמות.' in response.data.decode('utf-8')

    def test_registration_with_short_password(self, client):
        response = client.post('/register', data={
            'username': 'testuser2_auth_short', 'password': '123', 'confirm_password': '123'
        })
        assert response.status_code == 400
        assert 'הסיסמה חייבת להכיל לפחות 6 תווים.' in response.data.decode('utf-8')

    def test_registration_with_existing_username(self, client, temp_users_file_for_auth):
        with patch('app.USERS_FILE', temp_users_file_for_auth):
            import app as main_app_module
            main_app_module.USERS = main_app_module.load_users() 
            response = client.post('/register', data={
                'username': ADMIN_USERNAME, 'password': 'password123', 'confirm_password': 'password123'
            })
            assert response.status_code == 400
            assert 'שם המשתמש כבר קיים במערכת.' in response.data.decode('utf-8')

    def test_registration_with_empty_fields(self, client):
        response = client.post('/register', data={
            'username': '', 'password': 'password123', 'confirm_password': 'password123'
        })
        assert response.status_code == 400 
        # ההודעה הזו אמורה להגיע מהולידציה בפונקציה register ב-app.py
        assert 'נא למלא את כל השדות.' in response.data.decode('utf-8') # <<< --- התיקון כאן

    def test_logout_functionality(self, authenticated_client):
        response = authenticated_client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        assert 'התנתקת בהצלחה.' in response.data.decode('utf-8')
        assert 'Username:' in response.data.decode('utf-8') 
        with authenticated_client.session_transaction() as sess:
            assert sess.get('_user_id') is None

    def test_logout_requires_login(self, client): 
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        assert 'נא להתחבר כדי לגשת לדף זה.' in response.data.decode('utf-8')
        assert url_for('login', _external=False) in unquote(response.request.path) # שימוש ב-unquote גם כאן

    def test_home_requires_login(self, client):
        response = client.get('/', follow_redirects=True)
        assert response.status_code == 200
        assert 'נא להתחבר כדי לגשת לדף זה.' in response.data.decode('utf-8')
        assert url_for('login', _external=False) in unquote(response.request.path) # שימוש ב-unquote גם כאן


class TestUserManagement:
    def test_user_creation_and_persistence(self, temp_users_file_for_auth):
        with patch('app.USERS_FILE', temp_users_file_for_auth):
            import app as main_app_module
            main_app_module.USERS = main_app_module.load_users()
            original_users_count = len(main_app_module.USERS)
            new_id = original_users_count + 2 
            new_username = "persistentuser_auth"
            new_password_hash = generate_password_hash("persistpass")
            main_app_module.USERS[new_id] = User(new_id, new_username, new_password_hash, False)
            save_users(main_app_module.USERS) 
            main_app_module.USERS = load_users() 
            assert new_id in main_app_module.USERS
            assert main_app_module.USERS[new_id].username == new_username
            assert len(main_app_module.USERS) == original_users_count + 1

    def test_load_users_from_file(self, temp_users_file_for_auth):
        with patch('app.USERS_FILE', temp_users_file_for_auth):
            users = load_users() 
            assert 1 in users
            assert users[1].username == ADMIN_USERNAME

    def test_load_users_missing_file(self, tmp_path):
        missing_file_path = tmp_path / "non_existent_users.json"
        if os.path.exists(missing_file_path):
            os.remove(missing_file_path)
        with patch('app.USERS_FILE', str(missing_file_path)):
            users = load_users()
            assert 1 in users
            assert users[1].username == ADMIN_USERNAME
            assert users[1].is_approved is True
            assert os.path.exists(missing_file_path)


class TestAdminFunctionality:
    def test_admin_users_page_access(self, authenticated_client, temp_users_file_for_auth):
        with patch('app.USERS_FILE', temp_users_file_for_auth):
            import app as main_app_module
            main_app_module.USERS = main_app_module.load_users()
            response = authenticated_client.get('/admin/users')
            assert response.status_code == 200
            assert 'User Management' in response.data.decode('utf-8')

    def test_non_admin_users_page_denied(self, client, temp_users_file_for_auth):
        with patch('app.USERS_FILE', temp_users_file_for_auth):
            import app as main_app_module
            main_app_module.USERS = main_app_module.load_users()
            regular_user_id = 2 
            regular_username = "notadmin_auth"
            regular_password = "password123"
            if regular_user_id not in main_app_module.USERS:
                main_app_module.USERS[regular_user_id] = User(regular_user_id, regular_username, generate_password_hash(regular_password), True)
                save_users(main_app_module.USERS)
                main_app_module.USERS = main_app_module.load_users()
            login_resp = client.post('/login', data={'username': regular_username, 'password': regular_password}, follow_redirects=True)
            assert login_resp.status_code == 200 
            response = client.get('/admin/users', follow_redirects=True)
            assert response.status_code == 200 
            assert 'אין לך הרשאות לגשת לדף זה.' in response.data.decode('utf-8')

    def test_admin_approve_user(self, authenticated_client, temp_users_file_for_auth):
        with patch('app.USERS_FILE', temp_users_file_for_auth):
            import app as main_app_module
            main_app_module.USERS = main_app_module.load_users()
            pending_user_id = 3 
            pending_username = "pendinguser_auth"
            if pending_user_id not in main_app_module.USERS:
                main_app_module.USERS[pending_user_id] = User(pending_user_id, pending_username, generate_password_hash("pendingpass"), False)
                save_users(main_app_module.USERS)
                main_app_module.USERS = main_app_module.load_users()
            assert not main_app_module.USERS[pending_user_id].is_approved
            response = authenticated_client.get(f'/admin/users/{pending_user_id}/approve', follow_redirects=True)
            assert response.status_code == 200
            expected_message = f'משתמש {pending_username} אושר בהצלחה.'
            assert expected_message in response.data.decode('utf-8')
            main_app_module.USERS = main_app_module.load_users()
            assert main_app_module.USERS[pending_user_id].is_approved

    def test_admin_delete_user(self, authenticated_client, temp_users_file_for_auth):
        with patch('app.USERS_FILE', temp_users_file_for_auth):
            import app as main_app_module
            main_app_module.USERS = main_app_module.load_users()
            user_to_delete_id = 2 
            user_to_delete_username = "testuser_auth_delete"
            if user_to_delete_id not in main_app_module.USERS :
                main_app_module.USERS[user_to_delete_id] = User(user_to_delete_id, user_to_delete_username, generate_password_hash("deleteme"), True)
                save_users(main_app_module.USERS)
                main_app_module.USERS = main_app_module.load_users()
            assert user_to_delete_id in main_app_module.USERS
            response = authenticated_client.get(f'/admin/users/{user_to_delete_id}/delete', follow_redirects=True)
            assert response.status_code == 200
            expected_message = f'משתמש {user_to_delete_username} נמחק/נדחה בהצלחה.'
            assert expected_message in response.data.decode('utf-8')
            main_app_module.USERS = main_app_module.load_users()
            assert user_to_delete_id not in main_app_module.USERS

    def test_admin_cannot_delete_self(self, authenticated_client, temp_users_file_for_auth):
        with patch('app.USERS_FILE', temp_users_file_for_auth):
            import app as main_app_module
            main_app_module.USERS = main_app_module.load_users()
            admin_id = 1
            response = authenticated_client.get(f'/admin/users/{admin_id}/delete', follow_redirects=True)
            assert response.status_code == 200
            assert 'לא ניתן למחוק את חשבון המנהל הראשי.' in response.data.decode('utf-8')
            main_app_module.USERS = main_app_module.load_users()
            assert admin_id in main_app_module.USERS

    def test_invalid_user_action_on_admin(self, authenticated_client, temp_users_file_for_auth):
        with patch('app.USERS_FILE', temp_users_file_for_auth):
            import app as main_app_module
            main_app_module.USERS = main_app_module.load_users()
            admin_id = 1
            response = authenticated_client.get(f'/admin/users/{admin_id}/unknownaction', follow_redirects=True)
            assert response.status_code == 200
            assert 'פעולה לא חוקית.' in response.data.decode('utf-8')

    def test_invalid_action_type_on_user(self, authenticated_client, temp_users_file_for_auth):
        with patch('app.USERS_FILE', temp_users_file_for_auth):
            import app as main_app_module
            main_app_module.USERS = main_app_module.load_users()
            user_id_for_action = 2
            if user_id_for_action not in main_app_module.USERS :
                main_app_module.USERS[user_id_for_action] = User(user_id_for_action, "usertestaction2_auth", generate_password_hash("test"), True)
                save_users(main_app_module.USERS)
                main_app_module.USERS = main_app_module.load_users()
            response = authenticated_client.get(f'/admin/users/{user_id_for_action}/some_other_action', follow_redirects=True)
            assert response.status_code == 200
            assert 'פעולה לא חוקית.' in response.data.decode('utf-8')