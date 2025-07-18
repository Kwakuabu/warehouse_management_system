# Role-Based Access Control Implementation

## Overview

The warehouse management system now implements comprehensive role-based access control (RBAC) with three distinct user roles:

- **Admin** - Full system access
- **Manager** - Operational management access  
- **Staff** - Basic operational access

## User Roles

### Admin Role
- **Full system access** to all features
- Can access all routes and perform all operations
- System configuration and user management
- Security settings and audit logs

### Manager Role  
- **Operational management** access
- Can create and manage orders, products, customers, vendors
- Can view reports and manage alerts
- Cannot access system settings or user management

### Staff Role
- **Basic operational** access
- Can view inventory, products, customers, vendors
- Can view orders but cannot create or modify them
- Cannot access reports, alerts, or settings

## Route Access Matrix

| Route Category | Admin | Manager | Staff | Description |
|---------------|-------|---------|-------|-------------|
| **Dashboard** | ✅ | ✅ | ✅ | All users can access dashboard with role-based data |
| **Authentication** | ✅ | ✅ | ✅ | Login/logout for all users |
| **Products** | | | | |
| - View | ✅ | ✅ | ✅ | All users can view products |
| - Create/Edit | ✅ | ✅ | ❌ | Only admin/manager can modify products |
| **Inventory** | | | | |
| - View | ✅ | ✅ | ✅ | All users can view inventory |
| - Receive/Adjust | ✅ | ✅ | ❌ | Only admin/manager can receive/adjust |
| **Purchase Orders** | | | | |
| - View | ✅ | ✅ | ✅ | All users can view POs |
| - Create/Approve | ✅ | ✅ | ❌ | Only admin/manager can create/approve |
| **Sales Orders** | | | | |
| - View | ✅ | ✅ | ✅ | All users can view SOs |
| - Create/Approve | ✅ | ✅ | ❌ | Only admin/manager can create/approve |
| **Customers** | | | | |
| - View | ✅ | ✅ | ✅ | All users can view customers |
| - Create/Edit | ✅ | ✅ | ❌ | Only admin/manager can modify customers |
| **Vendors** | | | | |
| - View | ✅ | ✅ | ✅ | All users can view vendors |
| - Create/Edit | ✅ | ✅ | ❌ | Only admin/manager can modify vendors |
| **Categories** | | | | |
| - View | ✅ | ✅ | ✅ | All users can view categories |
| - Create/Edit | ✅ | ✅ | ❌ | Only admin/manager can modify categories |
| **Reports** | ✅ | ✅ | ❌ | Only admin/manager can access reports |
| **Alerts** | ✅ | ✅ | ❌ | Only admin/manager can manage alerts |
| **Settings** | | | | |
| - System Settings | ✅ | ❌ | ❌ | Only admin can access system settings |
| - User Preferences | ✅ | ✅ | ✅ | All users can manage their preferences |
| - Security Settings | ✅ | ❌ | ❌ | Only admin can access security settings |
| - Notification Settings | ✅ | ✅ | ❌ | Only admin/manager can manage notifications |

## Implementation Details

### Authentication Dependencies

The system uses two main authentication dependencies:

1. **`get_current_active_user`** - Basic authentication for all users
2. **`check_user_role(role)`** - Role-based authorization

### Code Examples

#### Basic Authentication (All Users)
```python
@router.get("/products", response_class=HTMLResponse)
async def products_list(
    request: Request, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Display products list page - All authenticated users"""
```

#### Role-Based Authorization (Manager/Admin Only)
```python
@router.get("/products/add", response_class=HTMLResponse)
async def add_product_page(
    request: Request, 
    current_user: User = Depends(check_user_role("manager")),
    db: Session = Depends(get_db)
):
    """Display add product page - Manager and Admin only"""
```

#### Admin-Only Authorization
```python
@router.get("/settings/system", response_class=HTMLResponse)
async def system_settings_page(
    request: Request,
    current_user: User = Depends(check_user_role("admin"))
):
    """Display system settings page - Admin only"""
```

### Role Hierarchy

The `check_user_role()` function implements a hierarchy where:
- **Admin** can access everything (admin role + any specific role)
- **Manager** can access manager-level and staff-level features
- **Staff** can only access staff-level features

```python
def check_user_role(required_role: str):
    """Decorator to check user role"""
    def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role != required_role and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker
```

## Security Features

### JWT Authentication
- Secure token-based authentication
- Token expiration and refresh
- HTTP-only cookies for web interface

### Role Validation
- Server-side role validation on every request
- 403 Forbidden responses for unauthorized access
- No client-side role bypass possible

### Audit Trail
- All actions are logged with user information
- `created_by` field tracks who created records
- Complete audit trail for compliance

## User Management

### Default Users
The system creates a default admin user:
- **Username**: `admin`
- **Password**: `admin123` (change in production!)
- **Role**: `admin`

### User Registration
- New users default to `staff` role
- Only admins can change user roles
- Email verification recommended for production

## Testing Role-Based Access

### Test Different Roles
1. **Login as Admin**: Full access to all features
2. **Login as Manager**: Access to operational features, no system settings
3. **Login as Staff**: View-only access to most features

### Test Unauthorized Access
- Try accessing admin routes as staff user
- Verify 403 Forbidden responses
- Check that sensitive data is not exposed

## Production Considerations

### Security Best Practices
1. **Change default passwords** immediately
2. **Use strong password policies**
3. **Enable HTTPS** in production
4. **Implement session timeout**
5. **Regular security audits**

### Role Management
1. **Principle of least privilege** - assign minimum required roles
2. **Regular role reviews** - audit user permissions
3. **Role-based training** - train users on their specific permissions
4. **Separation of duties** - critical operations require multiple approvals

### Monitoring and Logging
1. **Access logs** - monitor who accesses what
2. **Failed authentication attempts** - detect brute force attacks
3. **Role changes** - audit when user roles are modified
4. **Sensitive operations** - log all admin and manager actions

## API Endpoints

### Public Endpoints
- `/auth/login` - User authentication
- `/auth/register` - User registration
- `/health` - System health check

### Protected Endpoints
All other endpoints require authentication and appropriate role permissions.

## Error Handling

### Authentication Errors
- **401 Unauthorized** - Invalid or missing token
- **403 Forbidden** - Valid token but insufficient permissions
- **400 Bad Request** - Inactive user account

### User-Friendly Messages
The system provides clear error messages to help users understand access restrictions.

## Future Enhancements

### Planned Features
1. **Fine-grained permissions** - Individual permission flags
2. **Role inheritance** - Hierarchical role system
3. **Temporary permissions** - Time-limited access grants
4. **Multi-factor authentication** - Enhanced security
5. **API rate limiting** - Prevent abuse

### Integration Points
1. **LDAP/Active Directory** - Enterprise authentication
2. **SSO integration** - Single sign-on support
3. **Audit log export** - Compliance reporting
4. **Role templates** - Predefined role configurations 