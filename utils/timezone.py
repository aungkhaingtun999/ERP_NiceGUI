# ==============================================================================
# utils/timezone.py
# ERP ENTERPRISE TIME ENGINE v4
# UTC DATABASE -> LOCAL DISPLAY
# ==============================================================================


from datetime import datetime, timezone
from zoneinfo import ZoneInfo


try:
    from config import (
        DEFAULT_TIMEZONE,
        DATETIME_FORMAT
    )

except Exception:

    DEFAULT_TIMEZONE = "Asia/Yangon"

    DATETIME_FORMAT = "%d-%m-%Y %H:%M:%S"



# ==============================================================================
# GLOBAL
# ==============================================================================

_CURRENT_TIMEZONE = DEFAULT_TIMEZONE



# ==============================================================================
# SET / GET
# ==============================================================================

def set_timezone(tz):

    global _CURRENT_TIMEZONE

    _CURRENT_TIMEZONE = tz



def get_timezone():

    return _CURRENT_TIMEZONE



# ==============================================================================
# UTC
# ==============================================================================

def utc_now():

    return datetime.now(
        timezone.utc
    )



# ==============================================================================
# LOCAL
# ==============================================================================

def local_now(tz=None):

    zone = tz or _CURRENT_TIMEZONE

    return utc_now().astimezone(
        ZoneInfo(zone)
    )



# ==============================================================================
# FORMAT CURRENT
# ==============================================================================

def format_datetime(
    tz=None,
    fmt=None
):

    return local_now(tz).strftime(
        fmt or DATETIME_FORMAT
    )



def format_date(tz=None):

    return local_now(tz).strftime(
        "%d-%m-%Y"
    )



def format_time(tz=None):

    return local_now(tz).strftime(
        "%H:%M:%S"
    )



# ==============================================================================
# DATABASE UTC -> LOCAL
# ==============================================================================

def db_to_local(
    value,
    tz=None
):

    if value is None:

        return None



    zone = tz or _CURRENT_TIMEZONE



    if isinstance(value, str):

        value = datetime.fromisoformat(

            value.replace(
                "Z",
                "+00:00"
            )

        )



    if value.tzinfo is None:

        value = value.replace(

            tzinfo=timezone.utc

        )



    return value.astimezone(

        ZoneInfo(zone)

    )




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
# SHORTCUT
# ==============================================================================

def myanmar_now():

    return local_now(
        "Asia/Yangon"
    )



def utc_iso():

    return utc_now().isoformat()



# DEBUG

print(
    "TIMEZONE ENGINE LOADED"
)

print(
    "format_db_datetime:",
    callable(format_db_datetime)
)
