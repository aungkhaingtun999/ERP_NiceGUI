# ==============================================================================
# ERP ENTERPRISE PAYMENT ACCOUNT REPOSITORY v1.0
# KBZ / WAVE / AYA ACCOUNT MASTER
# ==============================================================================


from erp_core import get_supabase



supabase = get_supabase()



# ==============================================================================
# GET ACTIVE PAYMENT ACCOUNTS
# ==============================================================================


def get_payment_accounts(
    branch_id=None
):

    query = (

        supabase

        .table(
            "payment_accounts"
        )

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
        branch_id
    )


    for account in accounts:

        if account.get(
            "provider"
        ) == provider:

            return account


    return None