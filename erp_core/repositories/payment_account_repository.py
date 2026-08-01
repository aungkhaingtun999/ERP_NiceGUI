# ==============================================================================
# ERP ENTERPRISE PAYMENT ACCOUNT REPOSITORY v2.0
# PAYMENT ACCOUNT MASTER
# KBZ / WAVE / AYA
# ==============================================================================


from erp_core import get_supabase


supabase = get_supabase()



# ==============================================================================
# GET ACTIVE PAYMENT ACCOUNTS
# ==============================================================================


def get_payment_accounts(
    branch_id=None,
    provider=None
):

    query = (

        supabase
        .table("payment_accounts")
        .select("*")
        .eq(
            "enabled",
            True
        )

    )


    if branch_id:

        query = query.eq(
            "branch_id",
            branch_id
        )


    if provider:

        query = query.eq(
            "provider",
            provider
        )


    result = query.execute()


    return result.data or []





# ==============================================================================
# GET ACCOUNT BY PROVIDER
# ==============================================================================


def get_payment_account(
    provider,
    branch_id=None
):


    accounts = get_payment_accounts(

        branch_id=branch_id,

        provider=provider

    )


    if accounts:

        return accounts[0]


    return None





# ==============================================================================
# CREATE ACCOUNT
# ==============================================================================


def create_payment_account(
    data
):

    result = (

        supabase

        .table(
            "payment_accounts"
        )

        .insert(
            data
        )

        .execute()

    )


    return result.data





# ==============================================================================
# UPDATE ACCOUNT
# ==============================================================================


def update_payment_account(
    account_id,
    data
):

    result = (

        supabase

        .table(
            "payment_accounts"
        )

        .update(
            data
        )

        .eq(
            "id",
            account_id
        )

        .execute()

    )


    return result.data





# ==============================================================================
# DISABLE ACCOUNT
# ==============================================================================


def disable_payment_account(
    account_id
):

    return update_payment_account(

        account_id,

        {
            "enabled": False
        }

    )
