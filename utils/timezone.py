# ==============================================================================
# utils/timezone.py
# ERP ENTERPRISE TIME ENGINE v3
# ==============================================================================

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from config import (
    DEFAULT_TIMEZONE,
    DATETIME_FORMAT,
)

# ------------------------------------------------------------------------------
# GLOBAL TIMEZONE
# ------------------------------------------------------------------------------

_CURRENT_TIMEZONE = DEFAULT_TIMEZONE


def set_timezone(tz: str):
    global _CURRENT_TIMEZONE
    _CURRENT_TIMEZONE = tz


def get_timezone():
    return _CURRENT_TIMEZONE


# ------------------------------------------------------------------------------
# UTC
# ------------------------------------------------------------------------------

def utc_now():
    return datetime.now(timezone.utc)


# ------------------------------------------------------------------------------
# LOCAL
# ------------------------------------------------------------------------------

def local_now(tz=None):
    timezone_name = tz or _CURRENT_TIMEZONE
    return utc_now().astimezone(
        ZoneInfo(timezone_name)
    )


# ------------------------------------------------------------------------------
# FORMAT CURRENT TIME
# ------------------------------------------------------------------------------

def format_datetime(tz=None, fmt=None):
    return local_now(tz).strftime(
        fmt or DATETIME_FORMAT
    )


def format_date(tz=None):
    return local_now(tz).strftime("%d-%m-%Y")


def format_time(tz=None):
    return local_now(tz).strftime("%H:%M:%S")


# ------------------------------------------------------------------------------
# DATABASE UTC → LOCAL
# ------------------------------------------------------------------------------

def db_to_local(value, tz=None):

    timezone_name = tz or _CURRENT_TIMEZONE

    if value is None:
        return None

    if isinstance(value, str):
        value = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

    if value.tzinfo is None:
        value = value.replace(
            tzinfo=timezone.utc
        )

    return value.astimezone(
        ZoneInfo(timezone_name)
    )


def format_db_datetime(value, tz=None, fmt=None):

    dt = db_to_local(value, tz)

    if dt is None:
        return ""

    return dt.strftime(
        fmt or DATETIME_FORMAT
    )


# ------------------------------------------------------------------------------
# ISO
# ------------------------------------------------------------------------------

def iso_datetime(tz=None):
    return local_now(tz).isoformat()


def utc_iso():
    return utc_now().isoformat()


# ------------------------------------------------------------------------------
# SHORTCUTS
# ------------------------------------------------------------------------------

def myanmar_now():
    return local_now("Asia/Yangon")


def singapore_now():
    return local_now("Asia/Singapore")
    print("TIMEZONE MODULE LOADED")
print("HAS format_db_datetime:", "format_db_datetime" in globals())
