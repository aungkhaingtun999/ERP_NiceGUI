# ==============================================================================
# ERP SETTINGS REPOSITORY
# Database Access Layer
# ==============================================================================


from erp_core.base_repo import get_db



def create_setting_request(
    setting_key,
    old_value,
    new_value,
    reason,
    requested_by
):

    conn = get_db()

    cur = conn.cursor()


    cur.execute(
        """
        INSERT INTO settings_change_requests
        (
            setting_key,
            old_value,
            new_value,
            reason,
            requested_by
        )

        VALUES
        (
            %s,%s,%s,%s,%s
        )

        RETURNING id
        """,

        (
            setting_key,
            old_value,
            new_value,
            reason,
            requested_by
        )
    )


    request_id = cur.fetchone()[0]


    conn.commit()

    conn.close()


    return request_id





def get_pending_setting_requests():


    conn = get_db()

    cur = conn.cursor()


    cur.execute(
        """
        SELECT
            id,
            setting_key,
            old_value,
            new_value,
            reason,
            status,
            requested_by,
            created_at

        FROM settings_change_requests

        WHERE status='PENDING'

        ORDER BY created_at DESC
        """
    )


    rows = cur.fetchall()


    conn.close()


    return rows


# ==============================================================================
# APPROVE SETTING CHANGE
# ==============================================================================


from erp_core.base_repo import get_db



def approve_setting_change(
    request_id,
    checker_id
):


    conn = get_db()

    cur = conn.cursor()


    try:


        cur.execute(

            """
            SELECT approve_setting_change_rpc(
                %s,
                %s
            )
            """,

            (
                request_id,
                checker_id
            )

        )


        result = cur.fetchone()[0]


        conn.commit()


        return result



    except Exception as e:


        conn.rollback()

        raise e



    finally:


        conn.close()
