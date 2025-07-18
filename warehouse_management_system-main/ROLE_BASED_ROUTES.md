# Role-Based Routes - Warehouse Management System

## Current Role System

### User Roles Defined
- **admin**: Full system access, can manage all modules and settings
- **manager**: Can manage inventory, orders, and view reports
- **staff**: Basic access to view inventory and process orders

### Authentication Infrastructure
✅ **Implemented:**
- JWT-based authentication in `app/utils/auth.py`
- `check_user_role()` function for role verification
- User model with role field in `app/models/models.py`
- Admin override (admin users can access any role's routes)

❌ **Missing:**
- Route-level role protection
- Template-based role display
- Role-specific UI features

## Recommended Role-Based Route Structure

### 🔐 Admin Routes (Admin Only)
```
/settings/*           - System settings, security, company config
/reports/advanced     - Advanced analytics and system reports
/users/*              - User management (not yet implemented)
/system-logs          - System audit logs (not yet implemented)
```

### 👔 Manager Routes (Manager + Admin)
```
/inventory/*          - Full inventory management
/purchase-orders/*    - Purchase order management
/sales-orders/*       - Sales order management
/reports/*            - Business reports and analytics
/alerts/*             - Alert management
/customers/*          - Customer management
/vendors/*            - Vendor management
```

### 👷 Staff Routes (Staff + Manager + Admin)
```
/inventory/view       - View inventory (read-only)
/products/view        - View products (read-only)
/sales-orders/create  - Create sales orders
/sales-orders/view    - View sales orders
/customers/view       - View customers (read-only)
```

## Implementation Status

### ✅ Recently Updated
- **Settings Routes**: Now properly protected with admin-only access
- **User Preferences**: Available to all authenticated users

### 🔄 Needs Implementation
1. **Inventory Routes**: Add role-based protection
2. **Product Routes**: Add role-based protection  
3. **Order Routes**: Add role-based protection
4. **Report Routes**: Add role-based protection
5. **Template Updates**: Show user role and hide unauthorized features

## Example Implementation

### Route Protection Pattern
```python
# Admin only
@router.get("/admin-only")
async def admin_route(
    current_user: User = Depends(check_user_role("admin"))
):
    return {"message": "Admin access"}

# Manager and above
@router.get("/manager-plus")
async def manager_route(
    current_user: User = Depends(check_user_role("manager"))
):
    return {"message": "Manager access"}

# All authenticated users
@router.get("/all-users")
async def user_route(
    current_user: User = Depends(get_current_active_user)
):
    return {"message": "User access"}
```

### Template Role Display
```html
<!-- Show user role -->
<div class="user-role">{{ current_user.role.title() }}</div>

<!-- Hide admin features for non-admin users -->
{% if current_user.role == "admin" %}
<div class="admin-only-section">
    <a href="/settings">System Settings</a>
</div>
{% endif %}
```

## Security Considerations

### Role Hierarchy
- **Admin** > **Manager** > **Staff**
- Admin users can access any role's routes
- Role checks should be implemented at the route level
- Templates should hide unauthorized features

### Best Practices
1. **Always verify roles server-side** (never trust client-side role checks)
2. **Use dependency injection** for role verification
3. **Log access attempts** for security auditing
4. **Provide clear error messages** for unauthorized access
5. **Implement role-based UI** to prevent confusion

## Next Steps

1. **Implement role protection** for remaining routes
2. **Update templates** to show user roles and hide unauthorized features
3. **Add user management** module for admin users
4. **Create role-based dashboards** with different views per role
5. **Add audit logging** for role-based actions
6. **Test role boundaries** thoroughly

## Testing Role Access

### Test Cases
```python
# Test admin access
def test_admin_can_access_settings():
    # Admin should access /settings
    pass

# Test manager access
def test_manager_cannot_access_settings():
    # Manager should get 403 on /settings
    pass

# Test staff access
def test_staff_can_view_inventory():
    # Staff should view inventory but not modify
    pass
```

This role-based structure ensures proper access control while maintaining a clean separation of concerns between different user types in the warehouse management system. 