# ==============================================================================
# utils/timezone.py
# ERP ENTERPRISE TIMEZONE ENGINE v4.0
# Multi Country Ready
# ==============================================================================

from datetime import datetime, timezone, timedelta


# Myanmar Standard Time
MYANMAR_TZ = timezone(
    timedelta(hours=6, minutes=30),
    name="MMT"
)


# --------------------------------------------------
# Current Myanmar Time
# --------------------------------------------------

def now_myanmar():

    return datetime.now(MYANMAR_TZ)



# --------------------------------------------------
# Convert Any Datetime To Myanmar
# --------------------------------------------------

def to_myanmar_datetime(value):

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
            MYANMAR_TZ
        )


    except Exception:

        return None




# --------------------------------------------------
# Database Date Format
# --------------------------------------------------

def format_db_datetime(
    value,
    fmt="%d-%m-%Y %I:%M:%S %p"
):

    dt = to_myanmar_datetime(
        value
    )


    if dt is None:

        return "-"


    return dt.strftime(
        fmt
    )




# --------------------------------------------------
# Universal Alias
# Existing pages use this
# --------------------------------------------------

def format_datetime(
    value=None
):

    if value is None:

        value = now_myanmar()


    return format_db_datetime(
        value
    )




# --------------------------------------------------
# Date only
# --------------------------------------------------

def format_db_date(value):

    return format_db_datetime(
        value,
        "%d-%m-%Y"
    )




# --------------------------------------------------
# Time only
# --------------------------------------------------

def format_db_time(value):

    return format_db_datetime(
        value,
        "%I:%M:%S %p"
    )



__all__ = [

    "MYANMAR_TZ",

    "now_myanmar",

    "to_myanmar_datetime",

    "format_db_datetime",

    "format_datetime",

    "format_db_date",

    "format_db_time"

]
