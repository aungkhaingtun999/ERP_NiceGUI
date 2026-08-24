# ==============================================================================
# erp_pages/2_Products.py
# ERP ENTERPRISE PRODUCT PRICING CONTROL v4.0
# NICE GUI VERSION
#
# OWNER PRICE PRIORITY ENGINE
#
# OWNER MANUAL PRICE
#        ↓
# PRODUCT MARKUP
#        ↓
# CATEGORY MARKUP
#        ↓
# GLOBAL MARKUP
#
# ==============================================================================

from typing import Dict, Any, Optional, List, Callable
from decimal import Decimal
import io
import pandas as pd
from nicegui import ui

from erp_core.base_repo import db


# ==============================================================================
# DATABASE CLIENT
# ==============================================================================

client = db()


# ==============================================================================
# LOAD PRODUCTS
# ==============================================================================

def load_products() -> List[Dict[str, Any]]:
    """Load products from database."""
    try:
        result = (
            client
            .table("products")
            .select("""
                id,
                name,
                sku,
                barcode,
                purchase_price,
                selling_price,
                owner_selling_price,
                final_selling_price,
                price_source,
                markup_percent,
                category_id
            """)
            .order("name")
            .execute()
        )
        
        return result.data or []
    
    except Exception as e:
        ui.notify(f"Product Load Error : {e}", type='error', position='top')
        return []


# ==============================================================================
# LOAD CATEGORY
# ==============================================================================

def get_category(category_id: Any) -> Dict[str, Any]:
    """Get category information."""
    if not category_id:
        return {"name": "-", "markup": None}
    
    try:
        result = (
            client
            .table("categories")
            .select("name, markup_percent")
            .eq("id", category_id)
            .execute()
        )
        
        if result.data:
            row = result.data[0]
            return {
                "name": row.get("name", "-"),
                "markup": row.get("markup_percent")
            }
    
    except Exception:
        pass
    
    return {"name": "-", "markup": None}


# ==============================================================================
# GET GLOBAL MARKUP SETTING
# ==============================================================================

def get_global_markup() -> Decimal:
    """Get global markup percentage."""
    try:
        result = (
            client
            .table("settings")
            .select("value")
            .eq("key", "DEFAULT_MARKUP_PERCENT")
            .execute()
        )
        
        if result.data:
            return Decimal(str(result.data[0].get("value", 0)))
    
    except Exception:
        pass
    
    return Decimal("0")


# ==============================================================================
# PRICE CALCULATION PREVIEW
# ==============================================================================

def calculate_preview_price(product: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate preview price based on priority."""
    cost = Decimal(str(product.get("purchase_price", 0) or 0))
    
    # Owner price first
    owner_price = product.get("owner_selling_price")
    if owner_price is not None:
        return {
            "price": Decimal(str(owner_price)),
            "source": "OWNER"
        }
    
    # Product markup
    product_markup = product.get("markup_percent")
    if product_markup is not None:
        price = cost + (cost * Decimal(str(product_markup)) / Decimal("100"))
        return {
            "price": price.quantize(Decimal("0.01")),
            "source": "PRODUCT_MARKUP"
        }
    
    # Category markup
    category = get_category(product.get("category_id"))
    category_markup = category.get("markup")
    if category_markup is not None:
        price = cost + (cost * Decimal(str(category_markup)) / Decimal("100"))
        return {
            "price": price.quantize(Decimal("0.01")),
            "source": "CATEGORY_MARKUP"
        }
    
    # Global markup
    global_markup = get_global_markup()
    if global_markup > 0:
        price = cost + (cost * global_markup / Decimal("100"))
        return {
            "price": price.quantize(Decimal("0.01")),
            "source": "GLOBAL_MARKUP"
        }
    
    return {
        "price": Decimal(str(product.get("selling_price", 0) or 0)),
        "source": "CURRENT_PRICE"
    }


# ==============================================================================
# UI COMPONENTS
# ==============================================================================

def build_product_info(container: Any, product: Dict[str, Any], preview: Dict[str, Any]):
    """Build product information cards."""
    container.clear()
    
    final_preview_price = preview["price"]
    preview_source = preview["source"]
    
    source_colors = {
        "OWNER": "🟢 OWNER MANUAL PRICE",
        "PRODUCT_MARKUP": "🟡 PRODUCT MARKUP",
        "CATEGORY_MARKUP": "🔵 CATEGORY MARKUP",
        "GLOBAL_MARKUP": "🟣 GLOBAL MARKUP",
        "CURRENT_PRICE": "⚪ CURRENT SELLING PRICE"
    }
    
    with container:
        with ui.row().classes('w-full gap-4 flex-wrap mb-4'):
            # Purchase Cost
            with ui.card().classes('p-4 flex-1 min-w-[180px]'):
                ui.label('Purchase Cost').classes('text-sm text-gray-600')
                ui.label(f"{float(product.get('purchase_price') or 0):,.0f}").classes('text-2xl font-bold')
            
            # Current Selling
            with ui.card().classes('p-4 flex-1 min-w-[180px]'):
                ui.label('Current Selling').classes('text-sm text-gray-600')
                ui.label(f"{float(product.get('selling_price') or 0):,.0f}").classes('text-2xl font-bold')
            
            # Owner Price
            with ui.card().classes('p-4 flex-1 min-w-[180px]'):
                ui.label('Owner Price').classes('text-sm text-gray-600')
                owner_price = product.get('owner_selling_price')
                ui.label(
                    f"{float(owner_price):,.0f}" if owner_price else "Not Set"
                ).classes('text-2xl font-bold')
            
            # Final Price
            with ui.card().classes('p-4 flex-1 min-w-[180px]'):
                ui.label('Final Price').classes('text-sm text-gray-600')
                ui.label(f"{float(final_preview_price):,.0f}").classes('text-2xl font-bold')
        
        # Pricing decision
        with ui.card().classes('w-full p-4 bg-green-50 border border-green-200'):
            ui.label('Pricing Decision').classes('font-bold mb-2')
            ui.label(f"Source: {source_colors.get(preview_source, preview_source)}").classes('mb-1')
            ui.label(f"Final Selling Price: {float(final_preview_price):,.2f}").classes('text-xl font-bold')


def build_owner_price_control(
    container: Any,
    product: Dict[str, Any],
    on_save: Optional[Callable] = None
):
    """Build owner price control section."""
    container.clear()
    
    current_owner_price = product.get("owner_selling_price")
    
    with container:
        ui.label('👑 Owner Manual Selling Price').classes('text-xl font-bold mb-2')
        ui.label(
            'Owner Price has highest priority. If Owner Price exists, system will ignore automatic markup calculation.'
        ).classes('text-gray-500 mb-4')
        
        owner_price_input = ui.number(
            '💰 Set Owner Selling Price',
            min=0.0,
            value=float(current_owner_price or 0),
            step=100.0,
        ).classes('w-full mb-4')
        
        with ui.row().classes('w-full gap-2'):
            # Save button
            save_btn = ui.button(
                '👑 Save Owner Price',
                on_click=lambda: handle_save_owner_price(
                    product["id"],
                    owner_price_input.value,
                    save_btn,
                    on_save
                )
            ).classes('flex-1 bg-primary text-white')
            
            # Reset button
            reset_btn = ui.button(
                '♻ Reset Owner Price',
                on_click=lambda: handle_reset_owner_price(
                    product["id"],
                    reset_btn,
                    on_save
                )
            ).classes('flex-1 bg-gray-500 text-white')


def handle_save_owner_price(
    product_id: str,
    owner_price: float,
    save_btn: Any,
    on_save: Optional[Callable] = None
):
    """Handle save owner price."""
    try:
        save_btn.disable()
        save_btn.text = '⏳ Saving...'
        
        result = client.rpc(
            "save_owner_product_price_rpc",
            {
                "p_product_id": product_id,
                "p_owner_price": owner_price
            }
        ).execute()
        
        ui.notify(str(result.data), type='positive', position='top')
        
        if on_save:
            on_save()
    
    except Exception as e:
        ui.notify(f"Save Owner Price Failed : {e}", type='error', position='top')
    
    finally:
        save_btn.enable()
        save_btn.text = '👑 Save Owner Price'


def handle_reset_owner_price(
    product_id: str,
    reset_btn: Any,
    on_save: Optional[Callable] = None
):
    """Handle reset owner price."""
    try:
        reset_btn.disable()
        reset_btn.text = '⏳ Resetting...'
        
        result = client.rpc(
            "save_owner_product_price_rpc",
            {
                "p_product_id": product_id,
                "p_owner_price": None
            }
        ).execute()
        
        ui.notify(str(result.data), type='positive', position='top')
        
        if on_save:
            on_save()
    
    except Exception as e:
        ui.notify(f"Reset Failed : {e}", type='error', position='top')
    
    finally:
        reset_btn.enable()
        reset_btn.text = '♻ Reset Owner Price'


def build_markup_info(
    container: Any,
    product: Dict[str, Any],
    category: Dict[str, Any]
):
    """Build markup information section."""
    container.clear()
    
    global_markup = get_global_markup()
    
    with container:
        ui.label('⚙ Pricing Rule Preview').classes('text-xl font-bold mb-4')
        
        with ui.row().classes('w-full gap-4 flex-wrap'):
            with ui.card().classes('p-4 flex-1 min-w-[200px] bg-yellow-50'):
                ui.label('Product Markup').classes('font-bold mb-1')
                ui.label(f"{product.get('markup_percent') or 0}%").classes('text-2xl')
            
            with ui.card().classes('p-4 flex-1 min-w-[200px] bg-blue-50'):
                ui.label('Category').classes('font-bold mb-1')
                ui.label(category.get('name', '-')).classes('text-lg')
                ui.label(f"Markup: {category.get('markup') or 0}%").classes('text-sm text-gray-600')
            
            with ui.card().classes('p-4 flex-1 min-w-[200px] bg-purple-50'):
                ui.label('Global Markup').classes('font-bold mb-1')
                ui.label(f"{global_markup}%").classes('text-2xl')


def build_csv_import(container: Any, on_import: Optional[Callable] = None):
    """Build CSV import section."""
    container.clear()
    
    with container:
        ui.label('📥 Owner Manual Price CSV Import').classes('text-xl font-bold mb-2')
        
        ui.label('''CSV Format:
product_id,owner_selling_price
Example:
2,1500
37,2000
15,11500''').classes('font-mono text-sm text-gray-600 mb-4')
        
        # Download template
        template_df = pd.DataFrame([{"product_id": "", "owner_selling_price": ""}])
        template_bytes = template_df.to_csv(index=False).encode('utf-8')
        
        ui.button(
            '📄 Download Owner Price CSV Template',
            on_click=lambda: ui.download(template_bytes, 'owner_price_template.csv')
        ).props('flat').classes('w-full bg-gray-100 mb-4')
        
        # Upload
        ui.upload(
            on_upload=lambda e: handle_csv_upload(e, container, on_import),
            auto_upload=True,
            label='Upload Owner Price CSV',
        ).props('accept=.csv').classes('w-full')


def handle_csv_upload(e: Any, container: Any, on_import: Optional[Callable] = None):
    """Handle CSV upload."""
    try:
        content = e.content.read()
        df = pd.read_csv(io.BytesIO(content))
        
        required_columns = ["product_id", "owner_selling_price"]
        missing = [c for c in required_columns if c not in df.columns]
        
        if missing:
            ui.notify(f"Missing Columns : {missing}", type='error', position='top')
            return
        
        # Show preview
        with container:
            columns = [
                {'name': col, 'label': col, 'field': col}
                for col in df.columns
            ]
            ui.table(columns=columns, rows=df.to_dict('records'), row_key='product_id').classes('w-full mb-4')
            
            import_btn = ui.button(
                '🚀 Import Owner Prices',
                on_click=lambda: handle_bulk_import(df, import_btn, on_import)
            ).classes('w-full bg-primary text-white')
    
    except Exception as e:
        ui.notify(f"CSV Error : {e}", type='error', position='top')


def handle_bulk_import(df: pd.DataFrame, import_btn: Any, on_import: Optional[Callable] = None):
    """Handle bulk import."""
    try:
        import_btn.disable()
        import_btn.text = '⏳ Importing...'
        
        success_count = 0
        fail_count = 0
        errors = []
        
        for _, row in df.iterrows():
            try:
                product_id = int(row["product_id"])
                owner_price = float(row["owner_selling_price"])
                
                result = client.rpc(
                    "save_owner_product_price_rpc",
                    {
                        "p_product_id": product_id,
                        "p_owner_price": owner_price
                    }
                ).execute()
                
                if result.data:
                    success_count += 1
                else:
                    fail_count += 1
            
            except Exception as e:
                fail_count += 1
                errors.append({
                    "product_id": row.get("product_id"),
                    "error": str(e)
                })
        
        ui.notify(
            f'✅ Import Completed - Success: {success_count}, Failed: {fail_count}',
            type='positive',
            position='top',
            timeout=5000
        )
        
        if errors:
            ui.notify(f'Errors: {len(errors)}', type='warning', position='top')
        
        if on_import:
            on_import()
    
    except Exception as e:
        ui.notify(f"Import Failed: {e}", type='error', position='top')
    
    finally:
        import_btn.enable()
        import_btn.text = '🚀 Import Owner Prices'


# ==============================================================================
# MAIN PAGE
# ==============================================================================

def run(container: Optional[Any] = None):
    """Main page entry point."""
    target = container or ui.column()
    
    with target:
        # Header
        ui.label('📦 Product Pricing Control').classes('text-3xl font-bold mb-2')
        ui.label('ERP Enterprise Pricing Engine').classes('text-gray-500 mb-4')
        
        # Load products
        products = load_products()
        
        if not products:
            ui.notify('No Products Found', type='warning', position='top')
            return
        
        # Search
        search_input = ui.input('🔍 Search Product', placeholder='Type product name...').classes('w-full mb-4')
        
        # Product select
        product_container = ui.column().classes('w-full')
        
        def refresh_product_view(search_text: str = ""):
            product_container.clear()
            
            filtered_products = products
            if search_text:
                filtered_products = [
                    p for p in products
                    if search_text.lower() in p.get("name", "").lower()
                ]
            
            if not filtered_products:
                with product_container:
                    ui.label('No matching products').classes('text-gray-500')
                return
            
            with product_container:
                product_map = {
                    f"{p['id']} - {p['name']}": p
                    for p in filtered_products
                }
                
                selected_key = ui.select(
                    list(product_map.keys()),
                    label='📦 Select Product',
                ).classes('w-full mb-4')
                
                # Dynamic sections
                info_section = ui.column().classes('w-full mb-4')
                owner_section = ui.column().classes('w-full mb-4')
                markup_section = ui.column().classes('w-full mb-4')
                csv_section = ui.column().classes('w-full')
                
                def update_product_details():
                    product = product_map[selected_key.value]
                    category = get_category(product.get("category_id"))
                    preview = calculate_preview_price(product)
                    
                    build_product_info(info_section, product, preview)
                    build_owner_price_control(owner_section, product, update_product_details)
                    build_markup_info(markup_section, product, category)
                
                selected_key.on_value_change(lambda e: update_product_details())
                
                # Initial load
                update_product_details()
                
                # CSV Import (always visible)
                build_csv_import(csv_section, update_product_details)
        
        # Wire up search
        search_input.on_value_change(lambda e: refresh_product_view(e.value or ""))
        
        # Initial render
        refresh_product_view()


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    run()
