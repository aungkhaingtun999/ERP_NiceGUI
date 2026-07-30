# ==============================================================================
# utils/timezone.py
#
# ERP ENTERPRISE GLOBAL TIMEZONE ENGINE v4.0
#
# Multi Country Time Support
# ==============================================================================


from datetime import datetime, timezone

from zoneinfo import ZoneInfo



# ==============================================================================
# SUPPORTED TIMEZONES
# ==============================================================================


TIMEZONES = {

    "Myanmar": "Asia/Yangon",

    "Thailand": "Asia/Bangkok",

    "Japan": "Asia/Tokyo",

    "Korea": "Asia/Seoul",

    "China": "Asia/Shanghai",

    "Singapore": "Asia/Singapore",

    "India": "Asia/Kolkata",

    "UAE": "Asia/Dubai",

    "UK": "Europe/London",

    "USA New York": "America/New_York",

    "USA Los Angeles": "America/Los_Angeles",

    "Australia Sydney": "Australia/Sydney"

}




# ==============================================================================
# DEFAULT ERP TIMEZONE
# ==============================================================================


DEFAULT_TIMEZONE = "Asia/Yangon"





# ==============================================================================
# GET TIMEZONE
# ==============================================================================


def get_timezone(
    name=None
):


    try:

        if not name:

            name = DEFAULT_TIMEZONE



        # Country name input

        if name in TIMEZONES:

            name = TIMEZONES[name]



        return ZoneInfo(
            name
        )


    except Exception:


        return ZoneInfo(
            DEFAULT_TIMEZONE
        )





# ==============================================================================
# CURRENT TIME
# ==============================================================================


def now_myanmar():


    return datetime.now(

        get_timezone()

    )





def now_timezone(

    timezone_name=None

):


    return datetime.now(

        get_timezone(
            timezone_name
        )

    )





# ==============================================================================
# UTC → LOCAL TIME
# ==============================================================================


def to_local_datetime(

    value,

    timezone_name=None

):


    if value is None:

        return None



    try:


        if isinstance(value,str):


            value=value.replace(

                "Z",

                "+00:00"

            )


            dt=datetime.fromisoformat(

                value

            )


        else:

            dt=value




        if dt.tzinfo is None:


            dt=dt.replace(

                tzinfo=timezone.utc

            )



        return dt.astimezone(

            get_timezone(
                timezone_name
            )

        )


    except Exception:


        return None





# ==============================================================================
# FORMAT
# ==============================================================================


def format_db_datetime(

    value,

    timezone_name=None,

    fmt="%d-%m-%Y %I:%M:%S %p"

):


    dt=to_local_datetime(

        value,

        timezone_name

    )


    if not dt:

        return "-"



    return dt.strftime(

        fmt

    )





# ==============================================================================
# EXPORT
# ==============================================================================


__all__=[


    "TIMEZONES",

    "get_timezone",

    "now_myanmar",

    "now_timezone",

    "to_local_datetime",

    "format_db_datetime"


]
