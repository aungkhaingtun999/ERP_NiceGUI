# ==============================================================================
# utils/timezone.py
# ERP ENTERPRISE GLOBAL TIMEZONE ENGINE v4.0
#
# UTC ↔ Country Timezone
# Default Myanmar Time (+06:30)
# ==============================================================================


from datetime import datetime, timezone, timedelta


try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None



# ==============================================================================
# DEFAULT TIMEZONE
# ==============================================================================

DEFAULT_TIMEZONE = "Asia/Yangon"



# ==============================================================================
# GET TIMEZONE
# ==============================================================================

def get_timezone(name=None):

    tz_name = name or DEFAULT_TIMEZONE


    try:

        if ZoneInfo:

            return ZoneInfo(tz_name)


    except Exception:

        pass


    return timezone(
        timedelta(hours=6, minutes=30),
        name="MMT"
    )



# ==============================================================================
# CURRENT TIME
# ==============================================================================

def now_myanmar():

    return datetime.now(
        get_timezone()
    )



# ==============================================================================
# CONVERT UTC / DB TIME
# ==============================================================================

def to_local_datetime(
    value,
    timezone_name=None
):

    if value is None:

        return None


    try:


        if isinstance(value, str):

            value = value.replace(
                "Z",
                "+00:00"
            )

            dt = datetime.fromisoformat(
                value
            )

        else:

            dt = value



        if dt.tzinfo is None:

            dt = dt.replace(
                tzinfo=timezone.utc
            )


        return dt.astimezone(
            get_timezone(timezone_name)
        )


    except Exception:

        return None



# ==============================================================================
# FORMAT MAIN FUNCTION
# ==============================================================================

def format_datetime(
    value=None,
    fmt="%d-%m-%Y %I:%M:%S %p"
):


    if value is None:

        value = datetime.now(
            timezone.utc
        )


    dt = to_local_datetime(
        value
    )


    if dt is None:

        return "-"


    return dt.strftime(
        fmt
    )



# ==============================================================================
# BACKWARD COMPATIBILITY
# Old ERP pages use this
# ==============================================================================

def format_db_datetime(
    value
):

    return format_datetime(
        value
    )



def format_db_date(
    value
):

    return format_datetime(
        value,
        "%d-%m-%Y"
    )



def format_db_time(
    value
):

    return format_datetime(
        value,
        "%I:%M:%S %p"
    )



__all__ = [

    "now_myanmar",

    "format_datetime",

    "format_db_datetime",

    "format_db_date",

    "format_db_time",

    "to_local_datetime"

]
