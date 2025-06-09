# Template Update Plan

To ensure that templates work correctly with the blueprint routes, we need to check and update any hardcoded URLs or route references in the templates. Here's a plan for updating the templates:

## 1. Authentication Templates

### Login Template
- **File**: `templates/login.html` → `app/templates/auth/login.html`
- **Updates Needed**:
  - Update form action from `action="{{ url_for('login') }}"` to `action="{{ url_for('auth.login') }}"`
  - Update register link from `href="{{ url_for('register') }}"` to `href="{{ url_for('auth.register') }}"`

### Register Template
- **File**: `templates/register.html` → `app/templates/auth/register.html`
- **Updates Needed**:
  - Update form action from `action="{{ url_for('register') }}"` to `action="{{ url_for('auth.register') }}"`
  - Update login link from `href="{{ url_for('login') }}"` to `href="{{ url_for('auth.login') }}"`

## 2. Admin Templates

### User Management Template
- **File**: `templates/admin/users.html` → `app/templates/admin/users.html`
- **Updates Needed**:
  - Update user actions from `href="{{ url_for('user_action', user_id=user.id, action='approve') }}"` to `href="{{ url_for('admin.user_action', user_id=user.id, action='approve') }}"`
  - Update delete/reject actions from `href="{{ url_for('user_action', user_id=user.id, action='delete') }}"` to `href="{{ url_for('admin.user_action', user_id=user.id, action='delete') }}"`

## 3. Layout/Navigation Templates

### Base Layout Template
- **File**: `templates/base_layout.html` → `app/templates/base_layout.html`
- **Updates Needed**:
  - Update logout link from `href="{{ url_for('logout') }}"` to `href="{{ url_for('auth.logout') }}"`
  - Update admin links from `href="{{ url_for('manage_users') }}"` to `href="{{ url_for('admin.manage_users') }}"`

## Implementation Strategy

1. First, check if the templates have already been duplicated in the new blueprint structure
2. If templates exist in both locations, update the new templates with the correct URL references
3. If templates only exist in the original location, create copies in the new blueprint structure with updated URL references
4. Update compatibility routes in `app/__init__.py` to handle both old and new template references during transition

## Template Organization for Blueprints

The final template structure should follow this pattern:

```
app/templates/
├── auth/
│   ├── login.html
│   └── register.html
├── admin/
│   ├── dashboard.html
│   └── users.html
├── main/
│   ├── index.html
│   └── content_home.html
└── shared/
    ├── base_layout.html
    ├── 404.html
    ├── 500.html
    └── csrf_error.html
```

This structure aligns with the blueprint organization and makes it clear which templates belong to which part of the application.
