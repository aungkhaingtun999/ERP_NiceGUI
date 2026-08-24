# ==========================================
# language.py
# ERP ENTERPRISE i18n ENGINE v2.0
# Centralized Multi Language System
# NICE GUI VERSION
# ==========================================

from typing import Dict, Any, Optional, Callable
from nicegui import ui, app, context

from config import session_manager


# ==========================================
# LANGUAGE DATABASE
# ==========================================

TEXT = {
    "English": {
        "app": {
            "pos_system": "Enterprise POS System",
            "products": "Products",
            "cart": "Shopping Cart",
            "checkout": "Checkout",
            "dashboard": "Admin Dashboard",
            "no_product": "No products available"
        },
        "auth": {
            "login_required": "Please login first"
        },
        "search": {
            "product_name": "Product Name",
            "barcode": "Barcode / SKU",
            "choose": "Choose Product"
        },
        "cart": {
            "title": "Shopping Cart",
            "qty": "Quantity",
            "qty_short": "Qty",
            "add": "Add To Cart"
        },
        "payment": {
            "tax_rate": "Tax %",
            "discount": "Discount",
            "total": "Total",
            "method": "Payment Method",
            "cash": "Cash",
            "card": "Card",
            "mobile": "Mobile Banking",
            "credit": "Credit",
            "received": "Received Amount",
            "change": "Change",
            "confirm": "Confirm Sale"
        },
        "error": {
            "insufficient": "Payment is insufficient",
            "checkout_failed": "Checkout Failed"
        },
        "receipt": {
            "success": "Sale Completed",
            "no": "Receipt No",
            "print": "Print Receipt",
            "pdf": "Download PDF",
            "new_sale": "New Sale"
        },
        "stock": {
            "not_enough": "Not enough stock",
            "available": "Available"
        }
    },
    
    # ======================================
    # MYANMAR LANGUAGE
    # ======================================
    
    "မြန်မာ": {
        "app": {
            "pos_system": "Enterprise POS အရောင်းစနစ်",
            "products": "ကုန်ပစ္စည်းများ",
            "cart": "စျေးခြင်းတောင်း",
            "checkout": "ငွေရှင်းခြင်း",
            "dashboard": "စီမံခန့်ခွဲမှု Dashboard",
            "no_product": "ကုန်ပစ္စည်း မရှိပါ"
        },
        "auth": {
            "login_required": "ကျေးဇူးပြု၍ Login ဝင်ပါ"
        },
        "search": {
            "product_name": "ကုန်ပစ္စည်းအမည်",
            "barcode": "Barcode / SKU",
            "choose": "ကုန်ပစ္စည်းရွေးပါ"
        },
        "cart": {
            "title": "စျေးခြင်းတောင်း",
            "qty": "အရေအတွက်",
            "qty_short": "Qty",
            "add": "ထည့်မည်"
        },
        "payment": {
            "tax_rate": "အခွန် %",
            "discount": "လျှော့ငွေ",
            "total": "စုစုပေါင်း",
            "method": "ငွေပေးချေမှု",
            "cash": "ငွေသား",
            "card": "ကတ်",
            "mobile": "Mobile Banking",
            "credit": "အကြွေး",
            "received": "လက်ခံရရှိငွေ",
            "change": "ပြန်အမ်းငွေ",
            "confirm": "ရောင်းချမှု အတည်ပြု"
        },
        "error": {
            "insufficient": "ပေးချေငွေ မလုံလောက်ပါ",
            "checkout_failed": "ရောင်းချမှု မအောင်မြင်ပါ"
        },
        "receipt": {
            "success": "ရောင်းချမှု အောင်မြင်ပါသည်",
            "no": "ဘောက်ချာနံပါတ်",
            "print": "ဘောက်ချာထုတ်မည်",
            "pdf": "PDF Download",
            "new_sale": "အသစ်ပြန်ရောင်းမည်"
        },
        "stock": {
            "not_enough": "လက်ကျန် မလုံလောက်ပါ",
            "available": "လက်ကျန်"
        }
    }
}


# ==========================================
# LANGUAGE MANAGER CLASS
# ==========================================

class LanguageManager:
    """Centralized language management for NiceGUI"""
    
    def __init__(self, default_language: str = "မြန်မာ"):
        self.default_language = default_language
        self._current_language = default_language
        self._listeners: list[Callable] = []
    
    @property
    def current_language(self) -> str:
        """Get current language"""
        return self._current_language
    
    @current_language.setter
    def current_language(self, lang: str):
        """Set current language"""
        if lang in TEXT:
            self._current_language = lang
            self._notify_listeners()
    
    def add_listener(self, listener: Callable):
        """Add language change listener"""
        if listener not in self._listeners:
            self._listeners.append(listener)
    
    def remove_listener(self, listener: Callable):
        """Remove language change listener"""
        if listener in self._listeners:
            self._listeners.remove(listener)
    
    def _notify_listeners(self):
        """Notify all listeners of language change"""
        for listener in self._listeners:
            try:
                listener(self._current_language)
            except Exception as e:
                print(f"Language listener error: {e}")
    
    def translate(self, key: str) -> str:
        """Translate key to current language"""
        return translate_key(key, self._current_language)
    
    def t(self, key: str) -> str:
        """Short alias for translate"""
        return self.translate(key)
    
    def get_languages(self) -> list:
        """Get available languages"""
        return list(TEXT.keys())
    
    def set_language(self, lang: str):
        """Set language"""
        self.current_language = lang
    
    def reset(self):
        """Reset to default language"""
        self.current_language = self.default_language

# Global language manager instance
language_manager = LanguageManager()


# ==========================================
# INIT LANGUAGE
# ==========================================

def init_language(client_id: Optional[str] = None):
    """Initialize language for session
    
    Args:
        client_id: Client ID for session
    """
    session = session_manager.get_session(client_id)
    
    if "language" not in session:
        session["language"] = "မြန်မာ"
        language_manager.current_language = "မြန်မာ"
    else:
        language_manager.current_language = session["language"]


# ==========================================
# GET CURRENT LANGUAGE
# ==========================================

def get_language(client_id: Optional[str] = None) -> str:
    """Get current language from session
    
    Args:
        client_id: Client ID for session
    
    Returns:
        Current language code
    """
    init_language(client_id)
    session = session_manager.get_session(client_id)
    return session.get("language", "မြန်မာ")


# ==========================================
# CHANGE LANGUAGE
# ==========================================

def set_language(lang: str, client_id: Optional[str] = None):
    """Set language for session
    
    Args:
        lang: Language code
        client_id: Client ID for session
    """
    if lang in TEXT:
        session = session_manager.get_session(client_id)
        session["language"] = lang
        language_manager.current_language = lang


# ==========================================
# TRANSLATION FUNCTION
# ==========================================

def translate_key(key: str, lang: Optional[str] = None) -> str:
    """Translate key to specified language
    
    Args:
        key: Translation key (dot notation)
        lang: Language code (optional)
    
    Returns:
        Translated text
    """
    if lang is None:
        lang = language_manager.current_language
    
    data = TEXT.get(lang, TEXT["English"])
    
    # Navigate through nested keys
    for part in key.split("."):
        if isinstance(data, dict):
            data = data.get(part)
        else:
            data = None
        
        if data is None:
            # Fallback to English
            data = TEXT["English"]
            for p in key.split("."):
                if isinstance(data, dict):
                    data = data.get(p)
                else:
                    data = None
                    break
            
            return data if data else key
    
    return data


def t(key: str) -> str:
    """Short alias for translate_key
    
    Args:
        key: Translation key (dot notation)
    
    Returns:
        Translated text
    """
    return translate_key(key)


# ==========================================
# LANGUAGE SELECTOR
# ==========================================

def language_selector(
    container: Optional[Any] = None,
    on_change: Optional[Callable] = None,
    client_id: Optional[str] = None
):
    """Create language selector component
    
    Args:
        container: NiceGUI container to render in
        on_change: Callback after language change
        client_id: Client ID for session
    """
    target = container or ui.column()
    
    init_language(client_id)
    current = get_language(client_id)
    
    with target:
        selector = ui.select(
            list(TEXT.keys()),
            label='🌐 Language',
            value=current,
            on_change=lambda e: handle_language_change(
                e.value,
                on_change,
                client_id
            )
        ).classes('w-full')
        
        return selector


def handle_language_change(
    lang: str,
    on_change: Optional[Callable] = None,
    client_id: Optional[str] = None
):
    """Handle language change
    
    Args:
        lang: New language
        on_change: Callback after change
        client_id: Client ID for session
    """
    set_language(lang, client_id)
    
    if on_change:
        on_change(lang)
    
    # Notify user
    ui.notify(
        f"Language changed to {lang}",
        type='info',
        position='top',
        timeout=2000
    )


# ==========================================
# AVAILABLE LANGUAGES
# ==========================================

def get_languages() -> list:
    """Get available languages"""
    return list(TEXT.keys())


# ==========================================
# REACTIVE LANGUAGE COMPONENT
# ==========================================

class ReactiveText:
    """Reactive text component that updates on language change"""
    
    def __init__(self, key: str, container: Optional[Any] = None):
        self.key = key
        self.container = container
        self.label = None
        self.render()
        
        # Add listener for language changes
        language_manager.add_listener(self.update)
    
    def render(self):
        """Render the text component"""
        target = self.container or ui.column()
        
        with target:
            self.label = ui.label(t(self.key))
    
    def update(self, lang: str):
        """Update text on language change"""
        if self.label:
            self.label.text = translate_key(self.key, lang)
    
    def destroy(self):
        """Remove language change listener"""
        language_manager.remove_listener(self.update)


def reactive_text(key: str, container: Optional[Any] = None) -> ReactiveText:
    """Create reactive text component
    
    Args:
        key: Translation key
        container: NiceGUI container
    
    Returns:
        ReactiveText instance
    """
    return ReactiveText(key, container)


# ==========================================
# TRANSLATION HELPER FUNCTIONS
# ==========================================

def translate_dict(data: Dict[str, Any], lang: Optional[str] = None) -> Dict[str, Any]:
    """Translate dictionary values
    
    Args:
        data: Dictionary with translation keys
        lang: Language code
    
    Returns:
        Translated dictionary
    """
    result = {}
    
    for key, value in data.items():
        if isinstance(value, str) and value.startswith("t:"):
            # Translate key
            translation_key = value[2:]
            result[key] = translate_key(translation_key, lang)
        elif isinstance(value, dict):
            result[key] = translate_dict(value, lang)
        else:
            result[key] = value
    
    return result


def translate_list(data: list, lang: Optional[str] = None) -> list:
    """Translate list values
    
    Args:
        data: List with translation keys
        lang: Language code
    
    Returns:
        Translated list
    """
    result = []
    
    for item in data:
        if isinstance(item, str) and item.startswith("t:"):
            translation_key = item[2:]
            result.append(translate_key(translation_key, lang))
        elif isinstance(item, dict):
            result.append(translate_dict(item, lang))
        elif isinstance(item, list):
            result.append(translate_list(item, lang))
        else:
            result.append(item)
    
    return result


# ==========================================
# LANGUAGE PERSISTENCE
# ==========================================

def save_language_preference(lang: str, user_id: Optional[str] = None):
    """Save language preference to database
    
    Args:
        lang: Language code
        user_id: User ID (optional)
    """
    try:
        if user_id:
            from erp_core.base_repo import db
            
            client = db()
            
            client.table("user_preferences").upsert({
                "user_id": user_id,
                "language": lang,
            }).execute()
    except Exception as e:
        print(f"Error saving language preference: {e}")


def load_language_preference(user_id: str) -> Optional[str]:
    """Load language preference from database
    
    Args:
        user_id: User ID
    
    Returns:
        Language code or None
    """
    try:
        from erp_core.base_repo import db
        
        client = db()
        
        result = client.table("user_preferences").select(
            "language"
        ).eq("user_id", user_id).limit(1).execute()
        
        if result.data:
            lang = result.data[0].get("language")
            if lang in TEXT:
                return lang
    
    except Exception as e:
        print(f"Error loading language preference: {e}")
    
    return None


# ==========================================
# LANGUAGE DROPDOWN WITH FLAGS
# ==========================================

def language_dropdown_with_flags(
    container: Optional[Any] = None,
    on_change: Optional[Callable] = None
):
    """Create language dropdown with flags
    
    Args:
        container: NiceGUI container to render in
        on_change: Callback after language change
    """
    target = container or ui.column()
    
    language_options = {
        "🇬🇧 English": "English",
        "🇲🇲 မြန်မာ": "မြန်မာ",
    }
    
    current = language_manager.current_language
    
    with target:
        selector = ui.select(
            list(language_options.keys()),
            label='🌐 Language',
            value=f"🇬🇧 {current}" if current == "English" else f"🇲🇲 {current}",
            on_change=lambda e: handle_flag_language_change(
                language_options[e.value],
                on_change
            )
        ).classes('w-full')
        
        return selector


def handle_flag_language_change(
    lang: str,
    on_change: Optional[Callable] = None
):
    """Handle language change from flag dropdown"""
    set_language(lang)
    
    if on_change:
        on_change(lang)


# ==========================================
# PUBLIC EXPORTS
# ==========================================

__all__ = [
    # Language data
    "TEXT",
    
    # Language manager
    "LanguageManager",
    "language_manager",
    
    # Functions
    "init_language",
    "get_language",
    "set_language",
    "translate_key",
    "t",
    "language_selector",
    "handle_language_change",
    "get_languages",
    
    # Reactive components
    "ReactiveText",
    "reactive_text",
    
    # Helpers
    "translate_dict",
    "translate_list",
    
    # Persistence
    "save_language_preference",
    "load_language_preference",
    
    # UI components
    "language_dropdown_with_flags",
]
