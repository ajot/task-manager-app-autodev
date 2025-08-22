/**
 * Task Manager Frontend JavaScript
 */

$(document).ready(function() {
    // Initialize all components
    initializeTaskManager();
});

function initializeTaskManager() {
    // Initialize status updates
    initializeStatusUpdates();
    
    // Initialize form validations
    initializeFormValidations();
    
    // Initialize tooltips and popovers
    initializeBootstrapComponents();
    
    // Initialize auto-dismiss alerts
    initializeAlerts();
    
    // Initialize search and filters
    initializeSearchFilters();
}

// Status update functionality
function initializeStatusUpdates() {
    $('.status-update').on('click', function(e) {
        e.preventDefault();
        
        const taskId = $(this).data('task-id');
        const newStatus = $(this).data('status');
        const button = $(this);
        
        // Show loading state
        button.addClass('loading');
        
        updateTaskStatus(taskId, newStatus)
            .then(response => {
                if (response.success) {
                    updateStatusUI(taskId, newStatus);
                    showNotification('Task status updated successfully!', 'success');
                } else {
                    showNotification('Failed to update task status', 'error');
                }
            })
            .catch(error => {
                console.error('Error updating task status:', error);
                showNotification('Failed to update task status', 'error');
            })
            .finally(() => {
                button.removeClass('loading');
            });
    });
}

// API call to update task status
function updateTaskStatus(taskId, status) {
    return $.ajax({
        url: `/tasks/${taskId}/status`,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ status: status }),
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    });
}

// Update UI after status change
function updateStatusUI(taskId, newStatus) {
    const statusBadge = $(`#status-badge-${taskId}, #status-badge`);
    const taskCard = $(`.task-card[data-task-id="${taskId}"]`);
    
    // Update badge
    const statusColors = {
        'todo': 'secondary',
        'in_progress': 'primary',
        'done': 'success',
        'blocked': 'danger'
    };
    
    const statusLabels = {
        'todo': 'To Do',
        'in_progress': 'In Progress',
        'done': 'Done',
        'blocked': 'Blocked'
    };
    
    statusBadge.removeClass().addClass(`badge bg-${statusColors[newStatus]}`);
    statusBadge.text(statusLabels[newStatus]);
    
    // Update task card border color
    taskCard.removeClass('status-todo status-in_progress status-done status-blocked');
    taskCard.addClass(`status-${newStatus}`);
    
    // Add animation
    statusBadge.addClass('fade-in');
}

// Form validation
function initializeFormValidations() {
    // Custom validation for registration form
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm_password').value;
            
            if (password !== confirmPassword) {
                e.preventDefault();
                showNotification('Passwords do not match', 'error');
                return false;
            }
        });
    }
    
    // Add real-time validation feedback
    $('.form-control, .form-select').on('blur', function() {
        validateField($(this));
    });
}

// Individual field validation
function validateField(field) {
    const value = field.val().trim();
    const fieldType = field.attr('type') || field.prop('tagName').toLowerCase();
    
    field.removeClass('is-valid is-invalid');
    
    if (field.prop('required') && !value) {
        field.addClass('is-invalid');
        return false;
    }
    
    if (fieldType === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            field.addClass('is-invalid');
            return false;
        }
    }
    
    field.addClass('is-valid');
    return true;
}

// Initialize Bootstrap components
function initializeBootstrapComponents() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    const popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// Auto-dismiss alerts
function initializeAlerts() {
    // Auto dismiss success/info alerts after 5 seconds
    $('.alert-success, .alert-info').delay(5000).slideUp(300);
    
    // Keep error/warning alerts until manually dismissed
    $('.alert-danger, .alert-warning').addClass('alert-dismissible');
}

// Search and filter functionality
function initializeSearchFilters() {
    // Real-time search (debounced)
    let searchTimeout;
    $('.search-input').on('input', function() {
        const query = $(this).val();
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            performSearch(query);
        }, 300);
    });
    
    // Filter change handlers
    $('.filter-select').on('change', function() {
        const form = $(this).closest('form');
        if (form.length) {
            form.submit();
        }
    });
}

// Perform search
function performSearch(query) {
    const searchResults = $('.searchable-item');
    
    if (!query.trim()) {
        searchResults.show();
        return;
    }
    
    searchResults.each(function() {
        const item = $(this);
        const searchText = item.text().toLowerCase();
        
        if (searchText.includes(query.toLowerCase())) {
            item.show();
        } else {
            item.hide();
        }
    });
}

// Notification system
function showNotification(message, type = 'info', duration = 5000) {
    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    };
    
    const alertHtml = `
        <div class="alert ${alertClass[type]} alert-dismissible fade show notification-alert" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Add to notification container or create one
    let container = $('.notification-container');
    if (!container.length) {
        container = $('<div class="notification-container position-fixed top-0 end-0 p-3" style="z-index: 1080;"></div>');
        $('body').append(container);
    }
    
    const alert = $(alertHtml);
    container.append(alert);
    
    // Auto dismiss
    if (duration > 0) {
        setTimeout(() => {
            alert.alert('close');
        }, duration);
    }
}

// Utility functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatDateTime(dateTimeString) {
    const date = new Date(dateTimeString);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function truncateText(text, maxLength = 100) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Loading state management
function showLoading(element) {
    element.addClass('loading');
    const spinner = $('<span class="spinner-border spinner-border-sm me-2" role="status"></span>');
    element.prepend(spinner);
}

function hideLoading(element) {
    element.removeClass('loading');
    element.find('.spinner-border').remove();
}

// Keyboard shortcuts
$(document).keydown(function(e) {
    // Ctrl/Cmd + N for new task
    if ((e.ctrlKey || e.metaKey) && e.key === 'n' && !e.target.matches('input, textarea')) {
        e.preventDefault();
        if (window.location.pathname.includes('/tasks')) {
            window.location.href = '/tasks/new';
        }
    }
    
    // Esc to close modals
    if (e.key === 'Escape') {
        $('.modal').modal('hide');
    }
});

// Export functions for global use
window.TaskManager = {
    updateTaskStatus: updateTaskStatus,
    showNotification: showNotification,
    formatDate: formatDate,
    formatDateTime: formatDateTime,
    truncateText: truncateText,
    showLoading: showLoading,
    hideLoading: hideLoading
};