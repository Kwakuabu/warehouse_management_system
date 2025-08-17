# Staff Access Restrictions - Products & Categories

## Overview

This document outlines the access restrictions implemented for **staff users** (hospital buyers) regarding product and category management. Staff users are restricted from adding, editing, or deleting products and categories, as these are warehouse management functions.

## **🚫 What Staff Users CANNOT Do**

### **Products Management**
- ❌ **Add new products** - No access to `/products/add` route
- ❌ **Edit existing products** - No access to `/products/{id}/edit` route  
- ❌ **Delete products** - No access to `/products/{id}/delete` route
- ❌ **Add Product button** - Hidden from products list page
- ❌ **Edit/Delete buttons** - Hidden from product detail page

### **Categories Management**
- ❌ **Add new categories** - No access to `/categories/add` route
- ❌ **Edit existing categories** - No access to `/categories/{id}/edit` route
- ❌ **Delete categories** - No access to `/categories/{id}/delete` route
- ❌ **Add Category button** - Hidden from categories list page
- ❌ **Edit/Delete buttons** - Hidden from category detail page

## **✅ What Staff Users CAN Do**

### **Products**
- ✅ **View all products** - Access to `/products/` route
- ✅ **View product details** - Access to `/products/{id}` route
- ✅ **Browse product catalog** - Search and filter products
- ✅ **View product inventory** - See stock levels and availability
- ✅ **Order products** - Create sales orders for products

### **Categories**
- ✅ **View all categories** - Access to `/categories/` route
- ✅ **View category details** - Access to `/categories/{id}` route
- ✅ **Browse products by category** - See products in each category
- ✅ **Use categories for navigation** - Filter products by category

## **🔐 Route-Level Restrictions**

### **Products Routes**
```python
# ✅ Staff can access - View only
@router.get("/", response_class=HTMLResponse)
async def list_products(
    current_user: User = Depends(get_current_active_user_from_cookie),
    # ...

@router.get("/{product_id}", response_class=HTMLResponse)
async def product_detail(
    current_user: User = Depends(get_current_active_user_from_cookie),
    # ...

# ❌ Staff cannot access - Manager+ only
@router.get("/add", response_class=HTMLResponse)
async def add_product_page(
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    # ...

@router.get("/{product_id}/edit", response_class=HTMLResponse)
async def edit_product_page(
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    # ...

@router.post("/{product_id}/delete")
async def delete_product(
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    # ...
```

### **Categories Routes**
```python
# ✅ Staff can access - View only
@router.get("/", response_class=HTMLResponse)
async def list_categories(
    current_user: User = Depends(get_current_active_user_from_cookie),
    # ...

@router.get("/{category_id}", response_class=HTMLResponse)
async def category_detail(
    current_user: User = Depends(get_current_active_user_from_cookie),
    # ...

# ❌ Staff cannot access - Manager+ only
@router.get("/add", response_class=HTMLResponse)
async def add_category_page(
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    # ...

@router.get("/{category_id}/edit", response_class=HTMLResponse)
async def edit_category_page(
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    # ...

@router.post("/{category_id}/delete")
async def delete_category(
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    # ...
```

## **🎨 Template-Level Restrictions**

### **Products List Page**
```html
<!-- Add Product button - Hidden for staff -->
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2 class="mb-0">
        <i class="fas fa-boxes me-2"></i>Products
    </h2>
    {% if current_user.role in ['admin', 'manager'] %}
    <a href="/products/add" class="btn btn-primary">
        <i class="fas fa-plus me-2"></i>Add Product
    </a>
    {% endif %}
</div>

<!-- Edit/Delete buttons - Hidden for staff -->
<td>
    <div class="btn-group" role="group">
        <a href="/products/{{ product.id }}" class="btn btn-sm btn-outline-primary" title="View">
            <i class="fas fa-eye"></i>
        </a>
        {% if current_user.role in ['admin', 'manager'] %}
        <a href="/products/{{ product.id }}/edit" class="btn btn-sm btn-outline-warning" title="Edit">
            <i class="fas fa-edit"></i>
        </a>
        <button type="button" class="btn btn-sm btn-outline-danger" onclick="deleteProduct(...)" title="Delete">
            <i class="fas fa-trash"></i>
        </button>
        {% endif %}
    </div>
</td>
```

### **Categories List Page**
```html
<!-- Add Category button - Hidden for staff -->
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2 class="mb-0">
        <i class="fas fa-tags me-2"></i>Categories
    </h2>
    {% if current_user.role in ['admin', 'manager'] %}
    <a href="/categories/add" class="btn btn-primary">
        <i class="fas fa-plus me-2"></i>Add Category
    </a>
    {% endif %}
</div>

<!-- Edit/Delete buttons - Hidden for staff -->
<td>
    <div class="btn-group" role="group">
        <a href="/categories/{{ category.id }}" class="btn btn-sm btn-outline-primary" title="View">
            <i class="fas fa-eye"></i>
        </a>
        {% if current_user.role in ['admin', 'manager'] %}
        <a href="/categories/{{ category.id }}/edit" class="btn btn-sm btn-outline-warning" title="Edit">
            <i class="fas fa-edit"></i>
        </a>
        <button type="button" class="btn btn-sm btn-outline-danger" onclick="deleteCategory(...)" title="Delete">
            <i class="fas fa-trash"></i>
        </button>
        {% endif %}
    </div>
</td>
```

### **Product Detail Page**
```html
<!-- Edit/Delete actions - Hidden for staff -->
<div class="product-actions">
    {% if current_user.role in ['admin', 'manager'] %}
    <a href="/products/edit/{{ product.id }}" class="action-btn btn-warning">
        <i class="fas fa-edit"></i>
        Edit Product
    </a>
    <a href="/purchase-orders/create?product_id={{ product.id }}" class="action-btn btn-success">
        <i class="fas fa-plus"></i>
        Order Product
    </a>
    {% endif %}
    
    <a href="/products" class="action-btn btn-secondary">
        <i class="fas fa-list"></i>
        Back to Products
    </a>
    
    {% if current_user.role in ['admin', 'manager'] %}
    <button class="action-btn btn-danger" onclick="deleteProduct({{ product.id }}, '{{ product.name }}')">
        <i class="fas fa-trash"></i>
        Delete Product
    </button>
    {% endif %}
</div>
```

### **Category Detail Page**
```html
<!-- Edit/Delete actions - Hidden for staff -->
<div class="category-actions">
    {% if current_user.role in ['admin', 'manager'] %}
    <a href="/categories/edit/{{ category.id }}" class="action-btn btn-warning">
        <i class="fas fa-edit"></i>
        Edit Category
    </a>
    <a href="/products/add?category_id={{ category.id }}" class="action-btn btn-success">
        <i class="fas fa-plus"></i>
        Add Product
    </a>
    {% endif %}
    
    <a href="/categories" class="action-btn btn-secondary">
        <i class="fas fa-list"></i>
        Back to Categories
    </a>
    
    {% if current_user.role in ['admin', 'manager'] %}
    <button class="action-btn btn-danger" onclick="deleteCategory({{ category.id }}, '{{ category.name }}')">
        <i class="fas fa-trash"></i>
        Delete Category
    </button>
    {% endif %}
</div>
```

## **🔒 Security Implementation**

### **Multi-Layer Protection**
1. **Route-Level**: Server-side role checking prevents unauthorized access
2. **Template-Level**: UI elements hidden for unauthorized users
3. **Database-Level**: No direct database access for staff users

### **Role Verification**
```python
# All restricted routes use role checking
current_user: User = Depends(check_user_role_from_cookie("manager"))

# This ensures only manager+ users can access these functions
# Staff users get 403 Forbidden if they try to access restricted routes
```

## **📱 User Experience**

### **Staff Users See**
- Clean, uncluttered interface
- No confusing "Add" or "Edit" buttons
- Focus on browsing and ordering products
- Clear separation between view and management functions

### **Admin/Manager Users See**
- Full management interface
- Add/Edit/Delete buttons for products and categories
- Complete warehouse management capabilities
- All administrative functions available

## **🧪 Testing Scenarios**

### **Test Staff Access Restrictions**
1. **Login as staff user** (`staff` / `staff123`)
2. **Navigate to Products** → Should not see "Add Product" button
3. **Navigate to Categories** → Should not see "Add Category" button
4. **View product details** → Should not see "Edit" or "Delete" buttons
5. **View category details** → Should not see "Edit" or "Delete" buttons
6. **Try direct URL access** → Should get 403 Forbidden for restricted routes

### **Test Admin/Manager Access**
1. **Login as admin/manager** (`admin` / `admin123` or `manager` / `manager123`)
2. **Navigate to Products** → Should see "Add Product" button
3. **Navigate to Categories** → Should see "Add Category" button
4. **View product details** → Should see "Edit" and "Delete" buttons
5. **View category details** → Should see "Edit" and "Delete" buttons
6. **Access all routes** → Should work normally

## **🎯 Business Logic**

### **Why These Restrictions?**
- **Staff users** are hospital buyers, not warehouse operators
- **Product management** is a warehouse function, not customer function
- **Category management** affects the entire system, not individual orders
- **Data integrity** must be maintained by authorized personnel only

### **Staff User Workflow**
1. **Browse available products** (read-only)
2. **View product details** (read-only)
3. **Create sales orders** for needed supplies
4. **Track order status** and delivery
5. **No product/category management** responsibilities

## **Conclusion**

The access restrictions successfully implement the principle of **least privilege** for staff users:

- **Can do**: Everything needed to order medical supplies
- **Cannot do**: Anything related to warehouse management
- **Security**: Multi-layer protection prevents unauthorized access
- **UX**: Clean interface focused on customer needs

This ensures staff users have a focused, customer-facing experience while maintaining system security and data integrity.
