# ==============================================================================
# erp_ui/settings/common.py
# ERP SETTINGS UI COMMON HELPERS
# NICE GUI VERSION
# ==============================================================================

from typing import Any, Optional, Union
from nicegui import ui


# ==============================================================================
# SAVE RESULT HANDLER
# ==============================================================================

def show_save_success(
    message: str,
    position: str = 'top',
    timeout: int = 3000
):
    """Show save success notification
    
    Args:
        message: Success message to display
        position: Notification position (top, bottom, top-left, etc.)
        timeout: Notification timeout in milliseconds
    """
    ui.notify(
        message,
        type='positive',
        position=position,
        timeout=timeout,
        icon='check_circle'
    )


def show_save_error(
    message: str,
    position: str = 'top',
    timeout: int = 5000
):
    """Show save error notification
    
    Args:
        message: Error message to display
        position: Notification position (top, bottom, top-left, etc.)
        timeout: Notification timeout in milliseconds
    """
    ui.notify(
        message,
        type='error',
        position=position,
        timeout=timeout,
        icon='error'
    )


def show_save_warning(
    message: str,
    position: str = 'top',
    timeout: int = 4000
):
    """Show save warning notification
    
    Args:
        message: Warning message to display
        position: Notification position (top, bottom, top-left, etc.)
        timeout: Notification timeout in milliseconds
    """
    ui.notify(
        message,
        type='warning',
        position=position,
        timeout=timeout,
        icon='warning'
    )


def show_save_info(
    message: str,
    position: str = 'top',
    timeout: int = 3000
):
    """Show save info notification
    
    Args:
        message: Info message to display
        position: Notification position (top, bottom, top-left, etc.)
        timeout: Notification timeout in milliseconds
    """
    ui.notify(
        message,
        type='info',
        position=position,
        timeout=timeout,
        icon='info'
    )


# ==============================================================================
# SAVE RESULT WITH DIALOG
# ==============================================================================

def show_save_result_dialog(
    success: bool,
    message: str,
    title: Optional[str] = None
):
    """Show save result in a dialog
    
    Args:
        success: Whether the save was successful
        message: Result message
        title: Dialog title
    """
    if title is None:
        title = "✅ Success" if success else "❌ Error"
    
    with ui.dialog() as dialog, ui.card().classes('p-4 min-w-[300px]'):
        with ui.row().classes('items-center gap-2 mb-2'):
            ui.icon(
                'check_circle' if success else 'error'
            ).classes(
                'text-green-500' if success else 'text-red-500'
            )
            ui.label(title).classes('text-xl font-bold')
        
        ui.label(message).classes('mb-4')
        
        ui.button(
            'OK',
            on_click=dialog.close
        ).classes('w-full bg-primary text-white')
    
    dialog.open()


# ==============================================================================
# SAVE RESULT WITH EXPANSION
# ==============================================================================

def show_save_result_expansion(
    success: bool,
    message: str,
    details: Optional[str] = None
):
    """Show save result in an expansion panel
    
    Args:
        success: Whether the save was successful
        message: Result message
        details: Additional details to show
    """
    icon = 'check_circle' if success else 'error'
    color = 'text-green-500' if success else 'text-red-500'
    
    with ui.expansion(
        message,
        icon=icon
    ).classes(f'w-full {color}') as expansion:
        if details:
            ui.code(details, language='text')


# ==============================================================================
# NUMBER SAFE CONVERTER
# ==============================================================================

def safe_float(
    value: Any,
    default: float = 0.0
) -> float:
    """Safely convert value to float
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
    
    Returns:
        Converted float value or default
    """
    try:
        # Handle None and empty strings
        if value is None or value == "":
            return default
        
        # Handle boolean (avoid converting True/False to 1/0)
        if isinstance(value, bool):
            return default
        
        return float(value)
    
    except (ValueError, TypeError, OverflowError):
        return default


def safe_int(
    value: Any,
    default: int = 0
) -> int:
    """Safely convert value to integer
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
    
    Returns:
        Converted integer value or default
    """
    try:
        # Handle None and empty strings
        if value is None or value == "":
            return default
        
        # Handle boolean (avoid converting True/False to 1/0)
        if isinstance(value, bool):
            return default
        
        # Convert float to int safely
        if isinstance(value, float):
            return int(value)
        
        return int(value)
    
    except (ValueError, TypeError, OverflowError):
        return default


def safe_decimal(
    value: Any,
    default: float = 0.0,
    decimal_places: int = 2
) -> float:
    """Safely convert value to decimal with specified precision
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        decimal_places: Number of decimal places
    
    Returns:
        Converted decimal value or default
    """
    result = safe_float(value, default)
    
    try:
        return round(result, decimal_places)
    except Exception:
        return default


# ==============================================================================
# BOOL SAFE CONVERTER
# ==============================================================================

def safe_bool(
    value: Any,
    default: bool = False
) -> bool:
    """Safely convert value to boolean
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
    
    Returns:
        Converted boolean value or default
    """
    if value is None:
        return default
    
    if isinstance(value, bool):
        return value
    
    if isinstance(value, (int, float)):
        return value != 0
    
    return str(value).lower() in (
        "true",
        "1",
        "yes",
        "y",
        "on",
        "enabled",
        "active"
    )


# ==============================================================================
# STRING SAFE CONVERTER
# ==============================================================================

def safe_string(
    value: Any,
    default: str = ""
) -> str:
    """Safely convert value to string
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
    
    Returns:
        Converted string value or default
    """
    if value is None:
        return default
    
    try:
        return str(value)
    except Exception:
        return default


# ==============================================================================
# SAFE VALUE CONVERTER
# ==============================================================================

def safe_value(
    value: Any,
    value_type: type,
    default: Any = None
) -> Any:
    """Safely convert value to specified type
    
    Args:
        value: Value to convert
        value_type: Target type (str, int, float, bool)
        default: Default value if conversion fails
    
    Returns:
        Converted value or default
    """
    if value_type == str:
        return safe_string(value, default if default is not None else "")
    
    elif value_type == int:
        return safe_int(value, default if default is not None else 0)
    
    elif value_type == float:
        return safe_float(value, default if default is not None else 0.0)
    
    elif value_type == bool:
        return safe_bool(value, default if default is not None else False)
    
    else:
        return value if value is not None else default


# ==============================================================================
# VALIDATION HELPERS
# ==============================================================================

def validate_required(
    value: Any,
    field_name: str = "Field"
) -> Optional[str]:
    """Validate required field
    
    Args:
        value: Value to validate
        field_name: Name of the field for error message
    
    Returns:
        Error message if invalid, None if valid
    """
    if value is None or value == "":
        return f"{field_name} is required."
    
    return None


def validate_number(
    value: Any,
    field_name: str = "Field",
    min_value: Optional[float] = None,
    max_value: Optional[float] = None
) -> Optional[str]:
    """Validate numeric field
    
    Args:
        value: Value to validate
        field_name: Name of the field for error message
        min_value: Minimum allowed value
        max_value: Maximum allowed value
    
    Returns:
        Error message if invalid, None if valid
    """
    try:
        num_value = float(value)
        
        if min_value is not None and num_value < min_value:
            return f"{field_name} must be at least {min_value}."
        
        if max_value is not None and num_value > max_value:
            return f"{field_name} must be at most {max_value}."
        
        return None
    
    except (ValueError, TypeError):
        return f"{field_name} must be a valid number."


def validate_length(
    value: Any,
    field_name: str = "Field",
    min_length: Optional[int] = None,
    max_length: Optional[int] = None
) -> Optional[str]:
    """Validate string length
    
    Args:
        value: Value to validate
        field_name: Name of the field for error message
        min_length: Minimum allowed length
        max_length: Maximum allowed length
    
    Returns:
        Error message if invalid, None if valid
    """
    str_value = safe_string(value)
    
    if min_length is not None and len(str_value) < min_length:
        return f"{field_name} must be at least {min_length} characters."
    
    if max_length is not None and len(str_value) > max_length:
        return f"{field_name} must be at most {max_length} characters."
    
    return None


# ==============================================================================
# SETTINGS VALUE HANDLER
# ==============================================================================

class SettingsValueHandler:
    """Handle settings values with type conversion and validation"""
    
    @staticmethod
    def convert(
        value: Any,
        setting_type: str,
        default: Any = None
    ) -> Any:
        """Convert value based on setting type
        
        Args:
            value: Raw value to convert
            setting_type: Type of setting ('string', 'integer', 'float', 'boolean')
            default: Default value if conversion fails
        
        Returns:
            Converted value
        """
        converters = {
            'string': safe_string,
            'str': safe_string,
            'integer': safe_int,
            'int': safe_int,
            'float': safe_float,
            'decimal': safe_decimal,
            'boolean': safe_bool,
            'bool': safe_bool,
        }
        
        converter = converters.get(setting_type.lower())
        
        if converter:
            return converter(value, default)
        
        return value if value is not None else default
    
    @staticmethod
    def validate(
        value: Any,
        setting_type: str,
        setting_name: str,
        required: bool = False,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> List[str]:
        """Validate settings value
        
        Args:
            value: Value to validate
            setting_type: Type of setting
            setting_name: Name of setting
            required: Whether value is required
            min_value: Minimum allowed value
            max_value: Maximum allowed value
        
        Returns:
            List of validation errors
        """
        errors = []
        
        # Required validation
        if required:
            required_error = validate_required(value, setting_name)
            if required_error:
                errors.append(required_error)
                return errors
        
        # Type-specific validation
        if setting_type in ['integer', 'int', 'float', 'decimal']:
            number_error = validate_number(
                value,
                setting_name,
                min_value,
                max_value
            )
            if number_error:
                errors.append(number_error)
        
        elif setting_type in ['string', 'str']:
            if min_value:
                length_error = validate_length(
                    value,
                    setting_name,
                    min_length=int(min_value)
                )
                if length_error:
                    errors.append(length_error)
        
        return errors


# ==============================================================================
# UI COMPONENT HELPERS
# ==============================================================================

def create_setting_input(
    label: str,
    value: Any,
    setting_type: str = 'string',
    required: bool = False,
    placeholder: Optional[str] = None
):
    """Create appropriate input component based on setting type
    
    Args:
        label: Input label
        value: Initial value
        setting_type: Type of setting
        required: Whether field is required
        placeholder: Placeholder text
    
    Returns:
        NiceGUI input component
    """
    label_text = label + (" *" if required else "")
    
    if setting_type in ['boolean', 'bool']:
        return ui.switch(
            label_text,
            value=safe_bool(value, False)
        )
    
    elif setting_type in ['integer', 'int']:
        return ui.number(
            label_text,
            value=safe_int(value, 0),
            step=1
        ).classes('w-full')
    
    elif setting_type in ['float', 'decimal']:
        return ui.number(
            label_text,
            value=safe_float(value, 0.0),
            step=0.01
        ).classes('w-full')
    
    else:  # string
        return ui.input(
            label_text,
            value=safe_string(value),
            placeholder=placeholder
        ).classes('w-full')


def create_setting_select(
    label: str,
    options: List[Any],
    value: Any = None,
    required: bool = False
):
    """Create select component for settings
    
    Args:
        label: Select label
        options: List of options
        value: Initial value
        required: Whether field is required
    
    Returns:
        NiceGUI select component
    """
    label_text = label + (" *" if required else "")
    
    return ui.select(
        options,
        label=label_text,
        value=value
    ).classes('w-full')


# ==============================================================================
# PUBLIC EXPORTS
# ==============================================================================

__all__ = [
    # Notifications
    "show_save_success",
    "show_save_error",
    "show_save_warning",
    "show_save_info",
    "show_save_result_dialog",
    "show_save_result_expansion",
    
    # Converters
    "safe_float",
    "safe_int",
    "safe_decimal",
    "safe_bool",
    "safe_string",
    "safe_value",
    
    # Validation
    "validate_required",
    "validate_number",
    "validate_length",
    
    # Settings Handler
    "SettingsValueHandler",
    
    # UI Components
    "create_setting_input",
    "create_setting_select",
]
