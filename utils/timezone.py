# ==============================================================================
# utils/timezone.py
# ERP ENTERPRISE GLOBAL TIMEZONE ENGINE v5.0
#
# Multi Country Support
#
# Settings:
# DEFAULT_TIMEZONE
#
# Example:
# Asia/Yangon
# Asia/Bangkok
# Asia/Tokyo
# Europe/London
# America/New_York
#
# ==============================================================================


from datetime import datetime, timezone
from zoneinfo import ZoneInfo



# ==============================================================================
# DEFAULT
# ==============================================================================

DEFAULT_TIMEZONE = "Asia/Yangon"



# ==============================================================================
# GET ERP TIMEZONE
# ==============================================================================

def get_timezone():

    try:

        # ERP Settings connection

        from erp_core import get_setting


        tz_name = get_setting(
            "DEFAULT_TIMEZONE",
            DEFAULT_TIMEZONE
        )


        return ZoneInfo(
            tz_name
        )


    except Exception:

        return ZoneInfo(
            DEFAULT_TIMEZONE
        )




# ==============================================================================
# CURRENT ERP TIME
# ==============================================================================

def now_local():


    return datetime.now(

        get_timezone()

    )





# Backward compatibility

def now_myanmar():

    return now_local()





# ==============================================================================
# UTC / DATABASE → ERP TIME
# ==============================================================================

def to_local_datetime(value):


    if value is None:

        return None



    try:


        if isinstance(value,str):


            value=value.strip()


            value=value.replace(
                "Z",
                "+00:00"
            )


            dt=datetime.fromisoformat(
                value
            )


        else:

            dt=value




        # No timezone = Database UTC

        if dt.tzinfo is None:


            dt=dt.replace(
                tzinfo=timezone.utc
            )



        return dt.astimezone(

            get_timezone()

        )


    except Exception:


        return None





# ==============================================================================
# FORMAT
# ==============================================================================

def format_datetime(
    value=None,
    fmt="%d-%m-%Y %I:%M:%S %p"
):


    if value is None:

        value=now_local()



    dt=to_local_datetime(
        value
    )


    if dt is None:

        return "-"



    return dt.strftime(
        fmt
    )





# Compatibility

def format_db_datetime(
    value,
    fmt="%d-%m-%Y %I:%M:%S %p"
):

    return format_datetime(
        value,
        fmt
    )





def format_db_date(value):

    return format_datetime(
        value,
        "%d-%m-%Y"
    )





def format_db_time(value):

    return format_datetime(
        value,
        "%I:%M:%S %p"
    )





__all__ = [

    "DEFAULT_TIMEZONE",

    "get_timezone",

    "now_local",

    "now_myanmar",

    "to_local_datetime",

    "format_datetime",

    "format_db_datetime",

    "format_db_date",

    "format_db_time"

]
