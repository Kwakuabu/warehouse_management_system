# Export all route modules
from . import auth
from . import categories
from . import products
from . import customers
from . import inventory
from . import purchase_orders
from . import sales_order
from . import dashboard
from . import vendors
from . import reports
from . import alerts
from . import settings

__all__ = [
    'auth',
    'categories', 
    'products',
    'customers',
    'inventory',
    'purchase_orders',
    'sales_order',
    'dashboard',
    'vendors',
    'reports',
    'alerts',
    'settings'
]
