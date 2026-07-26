# ==============================================================================
# utils/timezone.py
# ERP ENTERPRISE TIME ENGINE v2
# ==============================================================================

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from config import (
    DEFAULT_TIMEZONE,
    DATETIME_FORMAT,
)


# ------------------------------------------------------------------------------
# DEFAULT TIMEZONE
# ------------------------------------------------------------------------------

_CURRENT_TIMEZONE = DEFAULT_TIMEZONE


# ------------------------------------------------------------------------------
# GET / SET TIMEZONE
# ------------------------------------------------------------------------------

def set_timezone(tz: str):
    """
    Change timezone globally.

    Example:
        set_timezone("Asia/Yangon")
        set_timezone("Asia/Bangkok")
        set_timezone("UTC")
    """

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
# LOCAL TIME
# ------------------------------------------------------------------------------

def local_now(tz=None):

    timezone_name = tz or _CURRENT_TIMEZONE

    return utc_now().astimezone(
        ZoneInfo(timezone_name)
    )


# ------------------------------------------------------------------------------
# FORMATTING
# ------------------------------------------------------------------------------

def format_datetime(
    tz=None,
    fmt=None
):

    return local_now(tz).strftime(
        fmt or DATETIME_FORMAT
    )


def format_date(
    tz=None
):

    return local_now(tz).strftime(
        "%Y-%m-%d"
    )


def format_time(
    tz=None
):

    return local_now(tz).strftime(
        "%H:%M:%S"
    )


# ------------------------------------------------------------------------------
# ISO FORMAT
# ------------------------------------------------------------------------------

def iso_datetime(
    tz=None
):

    return local_now(tz).isoformat()


# ------------------------------------------------------------------------------
# COMMON SHORTCUTS
# ------------------------------------------------------------------------------

def myanmar_now():

    return local_now("Asia/Yangon")


def singapore_now():

    return local_now("Asia/Singapore")


def utc_iso():

    return utc_now().isoformat()
