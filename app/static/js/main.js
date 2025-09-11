// Main JavaScript for Alive Pharmaceuticals Warehouse Management System

// Global variables
let currentUser = null;
let notifications = [];

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    loadDashboardData();
});

// Initialize Application
function initializeApp() {
    // Check authentication
    checkAuthStatus();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Setup mobile menu toggle
    setupMobileMenu();
    
    // Initialize form validations
    initializeFormValidations();
    
    // Setup real-time updates
    setupRealTimeUpdates();
}

// Check Authentication Status
function checkAuthStatus() {
    const token = getCookie('access_token');
    if (!token) {
        window.location.href = '/auth/login';
        return;
    }
    
    // Verify token and get user info
    fetch('/auth/me', {
        headers: {
            'Authorization': `Bearer ${token.replace('Bearer ', '')}`
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Authentication failed');
        }
        return response.json();
    })
    .then(user => {
        currentUser = user;
        updateUserInterface(user);
    })
    .catch(error => {
        console.error('Auth error:', error);
        window.location.href = '/auth/login';
    });
}

// Update User Interface
function updateUserInterface(user) {
    const userNameElements = document.querySelectorAll('.user-name');
    const userRoleElements = document.querySelectorAll('.user-role');
    
    userNameElements.forEach(element => {
        element.textContent = user.full_name;
    });
    
    userRoleElements.forEach(element => {
        element.textContent = user.role.charAt(0).toUpperCase() + user.role.slice(1);
    });
}

// Setup Event Listeners
function setupEventListeners() {
    // Logout functionality
    const logoutBtn = document.querySelector('.logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
    
    // Form submissions
    setupFormSubmissions();
    
    // Search functionality
    setupSearchFunctionality();
    
    // Modal interactions
    setupModalInteractions();
    
    // Table interactions
    setupTableInteractions();
}

// Handle Logout
function handleLogout(e) {
    e.preventDefault();
    
    // Clear cookies
    document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    
    // Redirect to login
    window.location.href = '/auth/login';
}

// Setup Form Submissions
function setupFormSubmissions() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(form)) {
                e.preventDefault();
                return false;
            }
            
            // Show loading state
            showLoadingState(form);
        });
    });
}

// Form Validation
function validateForm(form) {
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            showFieldError(field, 'This field is required');
            isValid = false;
        } else {
            clearFieldError(field);
        }
    });
    
    // Email validation
    const emailFields = form.querySelectorAll('input[type="email"]');
    emailFields.forEach(field => {
        if (field.value && !isValidEmail(field.value)) {
            showFieldError(field, 'Please enter a valid email address');
            isValid = false;
        }
    });
    
    // Password confirmation
    const passwordField = form.querySelector('input[name="password"]');
    const confirmPasswordField = form.querySelector('input[name="confirm_password"]');
    
    if (passwordField && confirmPasswordField) {
        if (passwordField.value !== confirmPasswordField.value) {
            showFieldError(confirmPasswordField, 'Passwords do not match');
            isValid = false;
        }
    }
    
    return isValid;
}

// Show Field Error
function showFieldError(field, message) {
    clearFieldError(field);
    
    field.classList.add('error');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error';
    errorDiv.textContent = message;
    errorDiv.style.color = 'var(--danger-color)';
    errorDiv.style.fontSize = '0.8rem';
    errorDiv.style.marginTop = '0.25rem';
    
    field.parentNode.appendChild(errorDiv);
}

// Clear Field Error
function clearFieldError(field) {
    field.classList.remove('error');
    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
}

// Email Validation
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Show Loading State
function showLoadingState(form) {
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<div class="spinner"></div> Processing...';
        submitBtn.disabled = true;
        
        // Re-enable after form submission
        setTimeout(() => {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }, 5000);
    }
}

// Setup Search Functionality
function setupSearchFunctionality() {
    const searchInputs = document.querySelectorAll('.search-input');
    
    searchInputs.forEach(input => {
        input.addEventListener('input', debounce(function() {
            performSearch(this.value, this.dataset.target);
        }, 300));
    });
}

// Debounce Function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Perform Search
function performSearch(query, target) {
    if (!query.trim()) {
        // Show all items
        const items = document.querySelectorAll(`[data-search-target="${target}"]`);
        items.forEach(item => item.style.display = '');
        return;
    }
    
    const items = document.querySelectorAll(`[data-search-target="${target}"]`);
    const searchTerm = query.toLowerCase();
    
    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        if (text.includes(searchTerm)) {
            item.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
}

// Setup Modal Interactions
function setupModalInteractions() {
    // Open modal
    const modalTriggers = document.querySelectorAll('[data-modal]');
    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', function(e) {
            e.preventDefault();
            const modalId = this.dataset.modal;
            openModal(modalId);
        });
    });
    
    // Close modal
    const modalCloses = document.querySelectorAll('.modal-close, .modal-overlay');
    modalCloses.forEach(close => {
        close.addEventListener('click', function() {
            closeModal(this.closest('.modal'));
        });
    });
    
    // Close modal with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal.open');
            if (openModal) {
                closeModal(openModal);
            }
        }
    });
}

// Open Modal
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('open');
        document.body.style.overflow = 'hidden';
    }
}

// Close Modal
function closeModal(modal) {
    if (modal) {
        modal.classList.remove('open');
        document.body.style.overflow = '';
    }
}

// Setup Table Interactions
function setupTableInteractions() {
    // Sortable tables
    const sortableHeaders = document.querySelectorAll('.sortable');
    sortableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            sortTable(this);
        });
    });
    
    // Row selection
    const selectableRows = document.querySelectorAll('.table tbody tr[data-id]');
    selectableRows.forEach(row => {
        row.addEventListener('click', function() {
            toggleRowSelection(this);
        });
    });
}

// Sort Table
function sortTable(header) {
    const table = header.closest('table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const columnIndex = Array.from(header.parentNode.children).indexOf(header);
    const isAscending = header.classList.contains('asc');
    
    // Clear previous sort indicators
    table.querySelectorAll('th').forEach(th => {
        th.classList.remove('asc', 'desc');
    });
    
    // Sort rows
    rows.sort((a, b) => {
        const aValue = a.children[columnIndex].textContent.trim();
        const bValue = b.children[columnIndex].textContent.trim();
        
        // Try to parse as numbers
        const aNum = parseFloat(aValue);
        const bNum = parseFloat(bValue);
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return isAscending ? bNum - aNum : aNum - bNum;
        }
        
        // String comparison
        return isAscending ? 
            bValue.localeCompare(aValue) : 
            aValue.localeCompare(bValue);
    });
    
    // Update sort indicator
    header.classList.add(isAscending ? 'desc' : 'asc');
    
    // Reorder rows
    rows.forEach(row => tbody.appendChild(row));
}

// Toggle Row Selection
function toggleRowSelection(row) {
    row.classList.toggle('selected');
    
    // Update bulk actions
    updateBulkActions();
}

// Update Bulk Actions
function updateBulkActions() {
    const selectedRows = document.querySelectorAll('.table tbody tr.selected');
    const bulkActions = document.querySelector('.bulk-actions');
    
    if (bulkActions) {
        if (selectedRows.length > 0) {
            bulkActions.style.display = 'flex';
            bulkActions.querySelector('.selected-count').textContent = selectedRows.length;
        } else {
            bulkActions.style.display = 'none';
        }
    }
}

// Setup Mobile Menu
function setupMobileMenu() {
    const menuToggle = document.querySelector('.menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (menuToggle && sidebar) {
        menuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('open');
        });
    }
}

// Initialize Tooltips
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            showTooltip(this);
        });
        
        element.addEventListener('mouseleave', function() {
            hideTooltip();
        });
    });
}

// Show Tooltip
function showTooltip(element) {
    const tooltipText = element.dataset.tooltip;
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = tooltipText;
    
    document.body.appendChild(tooltip);
    
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + 'px';
}

// Hide Tooltip
function hideTooltip() {
    const tooltip = document.querySelector('.tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

// Initialize Form Validations
function initializeFormValidations() {
    // Real-time validation
    const inputs = document.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
        });
        
        input.addEventListener('input', function() {
            if (this.classList.contains('error')) {
                validateField(this);
            }
        });
    });
}

// Validate Field
function validateField(field) {
    const value = field.value.trim();
    
    // Required validation
    if (field.hasAttribute('required') && !value) {
        showFieldError(field, 'This field is required');
        return false;
    }
    
    // Email validation
    if (field.type === 'email' && value && !isValidEmail(value)) {
        showFieldError(field, 'Please enter a valid email address');
        return false;
    }
    
    // Min length validation
    if (field.hasAttribute('minlength')) {
        const minLength = parseInt(field.getAttribute('minlength'));
        if (value.length < minLength) {
            showFieldError(field, `Minimum ${minLength} characters required`);
            return false;
        }
    }
    
    // Clear error if valid
    clearFieldError(field);
    return true;
}

// Setup Real-time Updates
function setupRealTimeUpdates() {
    // Update dashboard data every 30 seconds
    setInterval(loadDashboardData, 30000);
    
    // Check for notifications every minute
    setInterval(checkNotifications, 60000);
}

// Load Dashboard Data
function loadDashboardData() {
    // Load real-time statistics
    fetch('/api/dashboard/stats')
        .then(response => response.json())
        .then(data => {
            updateDashboardStats(data);
        })
        .catch(error => {
            console.error('Error loading dashboard data:', error);
        });
}

// Update Dashboard Stats
function updateDashboardStats(data) {
    const statElements = {
        'total-products': data.total_products,
        'low-stock-alerts': data.low_stock_alerts,
        'expiring-soon': data.expiring_soon,
        'inventory-value': data.inventory_value,
        'pending-orders': data.pending_orders,
        'active-customers': data.active_customers
    };
    
    Object.keys(statElements).forEach(key => {
        const element = document.querySelector(`[data-stat="${key}"]`);
        if (element) {
            element.textContent = formatStatValue(key, statElements[key]);
        }
    });
}

// Format Stat Value
function formatStatValue(key, value) {
    switch (key) {
        case 'inventory-value':
            return `$${(value / 1000000).toFixed(1)}M`;
        case 'low-stock-alerts':
        case 'expiring-soon':
            return value > 0 ? value.toString() : '0';
        default:
            return value.toString();
    }
}

// Check Notifications
function checkNotifications() {
    fetch('/api/notifications')
        .then(response => response.json())
        .then(data => {
            if (data.notifications && data.notifications.length > 0) {
                showNotifications(data.notifications);
            }
        })
        .catch(error => {
            console.error('Error checking notifications:', error);
        });
}

// Show Notifications
function showNotifications(notifications) {
    notifications.forEach(notification => {
        showToast(notification.message, notification.type);
    });
}

// Show Toast Notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <i class="fas fa-${getToastIcon(type)}"></i>
            <span>${message}</span>
        </div>
        <button class="toast-close">&times;</button>
    `;
    
    document.body.appendChild(toast);
    
    // Show toast
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);
    
    // Auto hide after 5 seconds
    setTimeout(() => {
        hideToast(toast);
    }, 5000);
    
    // Close button
    toast.querySelector('.toast-close').addEventListener('click', () => {
        hideToast(toast);
    });
}

// Hide Toast
function hideToast(toast) {
    toast.classList.remove('show');
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 300);
}

// Get Toast Icon
function getToastIcon(type) {
    switch (type) {
        case 'success': return 'check-circle';
        case 'warning': return 'exclamation-triangle';
        case 'error': return 'times-circle';
        default: return 'info-circle';
    }
}

// Utility Functions
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

function setCookie(name, value, days = 7) {
    const expires = new Date();
    expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
    document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
}

function deleteCookie(name) {
    document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
}

// Export functions for global use
window.WMS = {
    showToast,
    openModal,
    closeModal,
    validateForm,
    performSearch,
    sortTable,
    getCookie,
    setCookie,
    deleteCookie
}; 