# ==============================================================================
# utils/timezone.py
# ERP ENTERPRISE GLOBAL TIMEZONE ENGINE v4.0
#
# UTC <-> Country Timezone
# Myanmar Standard Time Support
# ==============================================================================


from datetime import datetime, timezone, timedelta


# ==============================================================================
# TIMEZONE DATABASE
# ==============================================================================

TIMEZONES = {

    "Myanmar": timezone(
        timedelta(hours=6, minutes=30),
        name="MMT"
    ),

    "Thailand": timezone(
        timedelta(hours=7),
        name="ICT"
    ),

    "Japan": timezone(
        timedelta(hours=9),
        name="JST"
    ),

    "Korea": timezone(
        timedelta(hours=9),
        name="KST"
    ),

    "China": timezone(
        timedelta(hours=8),
        name="CST"
    ),

    "Singapore": timezone(
        timedelta(hours=8),
        name="SGT"
    ),

    "India": timezone(
        timedelta(hours=5, minutes=30),
        name="IST"
    ),

    "Mongolia": timezone(
        timedelta(hours=8),
        name="ULAT"
    ),

    "UTC": timezone.utc

}



# Default ERP Timezone

DEFAULT_TIMEZONE = "Myanmar"



# ==============================================================================
# GET TIMEZONE
# ==============================================================================


def get_timezone(country=None):


    if not country:

        country = DEFAULT_TIMEZONE


    return TIMEZONES.get(

        country,

        TIMEZONES[DEFAULT_TIMEZONE]

    )





# ==============================================================================
# CURRENT TIME
# ==============================================================================


def now_myanmar():

    return datetime.now(

        TIMEZONES["Myanmar"]

    )





def now_erp():

    return datetime.now(

        get_timezone()

    )





# ==============================================================================
# CONVERT UTC TO LOCAL
# ==============================================================================


def to_local_datetime(
    value,
    country=None
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

            get_timezone(country)

        )



    except Exception:


        return None





# ==============================================================================
# DATABASE DATETIME FORMAT
# ==============================================================================


def format_db_datetime(
    value,
    fmt="%d-%m-%Y %I:%M:%S %p"
):


    dt = to_local_datetime(
        value
    )


    if dt is None:

        return "-"



    return dt.strftime(fmt)





# ==============================================================================
# UNIVERSAL FORMAT FUNCTION
# Used by POS Receipt
# ==============================================================================


def format_datetime(
    value=None
):


    if value is None:

        return format_db_datetime(

            now_erp()

        )


    return format_db_datetime(

        value

    )





# ==============================================================================
# DATE ONLY
# ==============================================================================


def format_db_date(value):


    return format_db_datetime(

        value,

        "%d-%m-%Y"

    )





# ==============================================================================
# TIME ONLY
# ==============================================================================


def format_db_time(value):


    return format_db_datetime(

        value,

        "%I:%M:%S %p"

    )





# ==============================================================================
# EXPORT
# ==============================================================================


__all__ = [

    "TIMEZONES",

    "get_timezone",

    "now_myanmar",

    "now_erp",

    "to_local_datetime",

    "format_db_datetime",

    "format_datetime",

    "format_db_date",

    "format_db_time"

]
