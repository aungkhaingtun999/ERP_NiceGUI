# ==============================================================================
# ERP ENTERPRISE PAYMENT SERVICE v1.0
# MOBILE BANKING VERIFICATION ENGINE
# ==============================================================================


from erp_core.repositories.payment_repository import (
    create_payment_transaction,
    get_payment,
    get_payment_by_sale,
    update_payment_status,
    get_pending_payments,
)



class PaymentService:


    # ==========================================================================
    # CREATE MOBILE PAYMENT
    # ==========================================================================

    @staticmethod
    def create_mobile_payment(
        sale_id,
        provider,
        transaction_id,
        amount,
        cashier_id=None
    ):

        payload = {

            "sale_id": sale_id,

            "payment_method": "Mobile Pay",

            "provider": provider,

            "transaction_id": transaction_id,

            "amount": amount,

            "status": "PENDING",

            "cashier_id": cashier_id

        }


        return create_payment_transaction(payload)



    # ==========================================================================
    # GET PAYMENT
    # ==========================================================================

    @staticmethod
    def get_payment(payment_id):

        return get_payment(payment_id)



    # ==========================================================================
    # CHECK SALE PAYMENT
    # ==========================================================================

    @staticmethod
    def get_sale_payment(sale_id):

        return get_payment_by_sale(sale_id)



    # ==========================================================================
    # VERIFY PAYMENT
    # ==========================================================================

    @staticmethod
    def verify_payment(
        payment_id,
        verified_by
    ):

        return update_payment_status(

            payment_id,

            "PAID",

            verified_by

        )



    # ==========================================================================
    # REJECT PAYMENT
    # ==========================================================================

    @staticmethod
    def reject_payment(
        payment_id,
        verified_by,
        reason
    ):

        return update_payment_status(

            payment_id,

            "REJECTED",

            verified_by,

            reason

        )



    # ==========================================================================
    # PENDING LIST
    # ==========================================================================

    @staticmethod
    def pending_payments():

        return get_pending_payments()