# ==============================================================================
# erp_pages/pos/styles_nicegui.py
# ERP ENTERPRISE POS UI STYLE ENGINE v1.1 SAFE
# NiceGUI Version
# ==============================================================================

from nicegui import ui, app
from typing import Optional

# ==============================================================================
# CSS STYLES
# ==============================================================================

POS_CUSTOM_CSS = """
<style>
/* ==========================================================================
   POS LAYOUT STYLES
   ========================================================================== */

/* Main POS container */
.pos-container {
    padding: 1rem;
    max-width: 100%;
}

/* POS header */
.pos-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
}

/* POS title */
.pos-title {
    font-size: 1.5rem;
    font-weight: bold;
    margin: 0;
}

/* POS subtitle */
.pos-subtitle {
    font-size: 0.875rem;
    opacity: 0.9;
    margin: 0;
}

/* Product cards */
.product-card {
    cursor: pointer;
    transition: all 0.3s ease;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    padding: 0.75rem;
    margin: 0.25rem;
    background: white;
}

.product-card:hover {
    border-color: #667eea;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
}

/* Product card selected state */
.product-card.selected {
    border-color: #667eea;
    background: #f0f0ff;
}

/* Product name */
.product-name {
    font-size: 0.9rem;
    font-weight: 600;
    margin: 0;
    color: #333;
}

/* Product price */
.product-price {
    font-size: 0.875rem;
    font-weight: bold;
    color: #667eea;
    margin: 0;
}

/* Product stock */
.product-stock {
    font-size: 0.75rem;
    color: #666;
    margin: 0;
}

/* Cart table */
.cart-table {
    width: 100%;
    border-collapse: collapse;
}

.cart-table th {
    background: #f5f5f5;
    padding: 0.5rem;
    text-align: left;
    font-weight: 600;
    font-size: 0.875rem;
}

.cart-table td {
    padding: 0.5rem;
    border-bottom: 1px solid #e0e0e0;
    font-size: 0.875rem;
}

/* Payment section */
.payment-section {
    background: #fafafa;
    border-radius: 8px;
    padding: 1rem;
    margin-top: 1rem;
}

/* Total display */
.total-display {
    font-size: 2rem;
    font-weight: bold;
    color: #667eea;
    text-align: center;
    margin: 1rem 0;
}

/* Action buttons */
.pos-button {
    border-radius: 6px;
    font-size: 0.9rem;
    font-weight: 600;
    padding: 0.5rem 1rem;
    transition: all 0.3s ease;
}

.pos-button:hover {
    opacity: 0.9;
    transform: translateY(-1px);
}

/* Receipt styles */
.receipt-container {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 1.5rem;
    max-width: 600px;
    margin: 0 auto;
}

.receipt-header {
    text-align: center;
    border-bottom: 2px dashed #ccc;
    padding-bottom: 1rem;
    margin-bottom: 1rem;
}

.receipt-total {
    font-size: 1.5rem;
    font-weight: bold;
    text-align: center;
    margin: 1rem 0;
    padding: 1rem;
    background: #f0f0ff;
    border-radius: 8px;
}

/* Mobile payment QR */
.qr-container {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 1rem;
}

/* Notification styles */
.pos-notification {
    border-radius: 6px;
    padding: 0.75rem;
    margin: 0.5rem 0;
}

/* Loading overlay */
.loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(255, 255, 255, 0.8);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 9999;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .pos-container {
        padding: 0.5rem;
    }
    
    .pos-title {
        font-size: 1.25rem;
    }
    
    .total-display {
        font-size: 1.5rem;
    }
    
    .product-card {
        padding: 0.5rem;
    }
}
</style>
"""

# ==============================================================================
# STYLE FUNCTIONS
# ==============================================================================

def load_pos_style():
    """
    Load POS custom styles
    Safe for NiceGUI
    """
    # Add custom CSS
    ui.add_head_html(POS_CUSTOM_CSS)
    
    # Apply global styles
    app.add_static_files('/static/pos', 'erp_pages/pos/static')

def apply_container_styles(element: ui.element):
    """
    Apply POS container styles to an element
    
    Args:
        element: NiceGUI element to style
    """
    element.classes('pos-container')

def style_product_card(element: ui.element, selected: bool = False):
    """
    Style a product card
    
    Args:
        element: NiceGUI element (card/container)
        selected: Whether the product is selected
    """
    base_classes = 'product-card'
    if selected:
        base_classes += ' selected'
    element.classes(base_classes)

def style_button(element: ui.button, variant: str = 'primary'):
    """
    Style a POS button
    
    Args:
        element: NiceGUI button element
        variant: Button variant (primary, secondary, danger, success)
    """
    base_classes = 'pos-button'
    
    variant_classes = {
        'primary': 'bg-blue-500 text-white',
        'secondary': 'bg-gray-500 text-white',
        'danger': 'bg-red-500 text-white',
        'success': 'bg-green-500 text-white',
        'warning': 'bg-orange-500 text-white',
    }
    
    classes = f'{base_classes} {variant_classes.get(variant, variant_classes["primary"])}'
    element.classes(classes)

def style_total_display(element: ui.element):
    """
    Style total display element
    """
    element.classes('total-display')

def style_receipt_container(element: ui.element):
    """
    Style receipt container
    """
    element.classes('receipt-container')

# ==============================================================================
# THEME CONFIGURATION
# ==============================================================================

def configure_pos_theme():
    """
    Configure POS theme colors and appearance
    """
    # Set NiceGUI theme
    ui.colors(
        primary='#667eea',
        secondary='#764ba2',
        accent='#4f46e5',
        positive='#10b981',
        negative='#ef4444',
        warning='#f59e0b',
        info='#3b82f6',
    )
    
    # Set dark mode
    ui.dark_mode(False)

# ==============================================================================
# COMPONENT STYLES
# ==============================================================================

def get_product_card_style() -> str:
    """Get product card inline style"""
    return """
        cursor: pointer;
        transition: all 0.3s ease;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        padding: 0.75rem;
        margin: 0.25rem;
        background: white;
    """

def get_selected_product_card_style() -> str:
    """Get selected product card inline style"""
    return """
        cursor: pointer;
        transition: all 0.3s ease;
        border: 2px solid #667eea;
        border-radius: 8px;
        padding: 0.75rem;
        margin: 0.25rem;
        background: #f0f0ff;
    """

def get_total_display_style() -> str:
    """Get total display inline style"""
    return """
        font-size: 2rem;
        font-weight: bold;
        color: #667eea;
        text-align: center;
        margin: 1rem 0;
    """

# ==============================================================================
# INITIALIZATION
# ==============================================================================

def init_pos_style():
    """
    Initialize POS styles
    Call this once when POS module loads
    """
    # Load custom CSS
    load_pos_style()
    
    # Configure theme
    configure_pos_theme()

# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = [
    'load_pos_style',
    'apply_container_styles',
    'style_product_card',
    'style_button',
    'style_total_display',
    'style_receipt_container',
    'configure_pos_theme',
    'init_pos_style',
    'get_product_card_style',
    'get_selected_product_card_style',
    'get_total_display_style',
    'POS_CUSTOM_CSS'
]
