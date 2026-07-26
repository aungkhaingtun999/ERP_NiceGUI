# ==============================================================================
# utils/timezone.py
# ERP ENTERPRISE TIME ENGINE v5
# UTC DATABASE -> LOCAL DISPLAY ENGINE
# ==============================================================================


from datetime import datetime, timezone
from zoneinfo import ZoneInfo


# ==============================================================================
# CONFIG SAFE LOAD
# ==============================================================================

try:

    from config import (
        DEFAULT_TIMEZONE,
        DATETIME_FORMAT
    )

except Exception:

    DEFAULT_TIMEZONE = "Asia/Yangon"

    DATETIME_FORMAT = "%d-%m-%Y %H:%M:%S"



# ==============================================================================
# GLOBAL TIMEZONE STATE
# ==============================================================================

_CURRENT_TIMEZONE = DEFAULT_TIMEZONE



# ==============================================================================
# TIMEZONE CONTROL
# ==============================================================================

def set_timezone(
    tz: str
):
    """
    Change ERP display timezone.

    Example:

        set_timezone("Asia/Yangon")
        set_timezone("Asia/Bangkok")
        set_timezone("UTC")
    """

    global _CURRENT_TIMEZONE

    _CURRENT_TIMEZONE = tz



def get_timezone():

    return _CURRENT_TIMEZONE



# ==============================================================================
# UTC TIME
# ==============================================================================

def utc_now():

    """
    Database standard time.
    """

    return datetime.now(
        timezone.utc
    )



# ==============================================================================
# LOCAL TIME
# ==============================================================================

def local_now(
    tz=None
):

    zone = tz or _CURRENT_TIMEZONE

    return utc_now().astimezone(
        ZoneInfo(zone)
    )



# ==============================================================================
# CURRENT TIME FORMAT
# ==============================================================================

def format_datetime(
    tz=None,
    fmt=None
):

    return local_now(
        tz
    ).strftime(
        fmt or DATETIME_FORMAT
    )



def format_date(
    tz=None
):

    return local_now(
        tz
    ).strftime(
        "%d-%m-%Y"
    )



def format_time(
    tz=None
):

    return local_now(
        tz
    ).strftime(
        "%H:%M:%S"
    )



# ==============================================================================
# DATABASE UTC -> LOCAL CONVERSION
# ==============================================================================

def db_to_local(
    value,
    tz=None
):
    """
    Convert database timestamp into ERP display timezone.

    Supports:

    - datetime object
    - PostgreSQL timestamp
    - Supabase ISO string
    - UTC Z format

    """

    if value is None:

        return None



    zone = tz or _CURRENT_TIMEZONE



    # String timestamp

    if isinstance(
        value,
        str
    ):

        value = datetime.fromisoformat(

            value.replace(
                "Z",
                "+00:00"
            )

        )



    # Database timestamp without timezone

    if value.tzinfo is None:

        value = value.replace(

            tzinfo=timezone.utc

        )



    return value.astimezone(

        ZoneInfo(zone)

    )



# ==============================================================================
# DATABASE DATE FORMATTER
# Used by Receipt Viewer / Reports
# ==============================================================================

def format_db_datetime(
    value,
    tz=None,
    fmt=None
):

    dt = db_to_local(
        value,
        tz
    )


    if dt is None:

        return ""


    return dt.strftime(

        fmt or DATETIME_FORMAT

    )



# ==============================================================================
# ISO FORMAT
# ==============================================================================

def iso_datetime(
    tz=None
):

    return local_now(
        tz
    ).isoformat()



def utc_iso():

    return utc_now().isoformat()



# ==============================================================================
# SHORTCUT TIMEZONES
# ==============================================================================

def myanmar_now():

    return local_now(
        "Asia/Yangon"
    )



def singapore_now():

    return local_now(
        "Asia/Singapore"
    )



# ==============================================================================
# PUBLIC EXPORTS
# ==============================================================================

__all__ = [

    "set_timezone",

    "get_timezone",

    "utc_now",

    "local_now",

    "format_datetime",

    "format_date",

    "format_time",

    "db_to_local",

    "format_db_datetime",

    "iso_datetime",

    "utc_iso",

    "myanmar_now",

    "singapore_now",

]
