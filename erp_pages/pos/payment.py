# ==============================================================================
# erp_pages/pos/payment.py
# ERP ENTERPRISE POS PAYMENT MODULE v15.0 STABLE
# ==============================================================================

import streamlit as str_module  # or keep as st
import streamlit as st
import datetime

from database import generate_payment_qr
from erp_core.repositories.payment_account_repository import \
    get_payment_account
from supabase_client import get_supabase
from .cart import calculate_subtotal
from .checkout import process_checkout
from .engine import get_default_tax_rate
from .session import start_processing, stop_processing


# ==============================================================================
# MONEY FORMAT
# ==============================================================================

def money(value):
    try:
        return f"{float(value):,.0f} MMK"
    except Exception:
        return "0 MMK"


# ==============================================================================
# HELPER: POST JOURNAL ENTRY FOR DOUBLE ENTRY SYSTEM
# ==============================================================================

def post_sale_journal_entry(sale_id: int, total_amount: float, payment_method: str = "CASH"):
    """
    အရောင်းအဝယ် (Sale) ပြီးမြောက်ပါက journal_entries ဇယားသို့ 
    Double Entry (Debit နှင့် Credit) အလိုအလျောက် ထည့်သွင်းပေးသည်။
    """
    try:
        supabase = get_supabase()
        if not supabase:
            return False

        if total_amount <= 0:
            return True

        # ငွေပေးချေမှုပုံစံအလိုက် Account ID သတ်မှတ်ခြင်း
        debit_account_id = 1 if "CASH" in payment_method.upper() else 2  # 1: Cash, 2: Bank/AR
        credit_account_id = 4  # Sales Revenue

        journal_rows = [
            {
                "sale_id": sale_id,
                "account_id": debit_account_id,
                "debit": total_amount,
                "credit": 0.00,
                "description": f"Sale #{sale_id} - Payment via {payment_method}",
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            },
            {
                "sale_id": sale_id,
                "account_id": credit_account_id,
                "debit": 0.00,
                "credit": total_amount,
                "description": f"Sale #{sale_id} - Revenue",
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
        ]

        response = supabase.table("journal_entries").insert(journal_rows).execute()
        return bool(response.data)

    except Exception as e:
        print(f"Error posting journal entry: {str(e)}")
        return False


# ==============================================================================
# PAYMENT UI
# ==============================================================================

def render_payment(warehouse_id):
    cart = st.session_state.get("cart", [])

    if not cart:
        return

    st.divider()
    st.subheader("💳 Payment")

    # --------------------------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------------------------

    subtotal = calculate_subtotal(cart)

    total_qty = sum(
        int(item.get("qty", 0))
        for item in cart
    )

    tax_rate = get_default_tax_rate()

    tax_amount = subtotal * tax_rate / 100

    c1, c2, c3 = st.columns(3)

    with c1:
        st.caption("Items")
        st.write(len(cart))

    with c2:
        st.caption("Total Qty")
        st.write(total_qty)

    with c3:
        st.caption("Subtotal")
        st.write(money(subtotal))

    st.caption(
        f"🧾 Tax {tax_rate:.2f}% : {money(tax_amount)}"
    )

    # --------------------------------------------------------------------------
    # DISCOUNT
    # --------------------------------------------------------------------------

    discount = st.number_input(
        "Discount (MMK)",
        min_value=0.0,
        value=float(st.session_state.get("discount", 0)),
        step=100.0
    )

    st.session_state.discount = discount

    # --------------------------------------------------------------------------
    # TOTAL
    # --------------------------------------------------------------------------

    grand_total = max(
        0,
        subtotal + tax_amount - discount
    )

    st.markdown(
        f"""
### 💰 Total Payable

# {money(grand_total)}
"""
    )

    st.caption(
        f"""
Subtotal : {money(subtotal)}

Tax : {money(tax_amount)}

Discount : {money(discount)}
"""
    )

    # --------------------------------------------------------------------------
    # PAYMENT METHOD
    # --------------------------------------------------------------------------

    payment_method = st.selectbox(
        "Payment Method",
        [
            "CASH",
            "BANK",
            "MOBILE",
            "CREDIT"
        ]
    )

    st.session_state.payment_method = payment_method

    # --------------------------------------------------------------------------
    # MOBILE PAYMENT
    # --------------------------------------------------------------------------

    if payment_method == "MOBILE":

        provider = st.selectbox(
            "Mobile Provider",
            [
                "KBZ Pay",
                "Wave Pay",
                "AYA Pay"
            ]
        )

        branch_id = st.session_state.get("branch_id", 1)

        account = get_payment_account(
            provider,
            branch_id=branch_id
        )

        if not account:
            st.error(f"{provider} account not configured")
            return

        account_name = account.get("account_name", "ERP SHOP")
        account_no = account.get("account_no", "")

        qr_mode = account.get("qr_mode", "DYNAMIC")

        # ----------------------------------------------------------------------
        # KBZ PAY : STATIC / DYNAMIC
        # ----------------------------------------------------------------------

        if provider == "KBZ Pay":

            if qr_mode == "STATIC" and account.get("qr_payload_template"):
                qr_buffer = generate_payment_qr(
                    provider=provider,
                    account_name=account_name,
                    account_no=account_no,
                    amount=grand_total,
                    sale_id="TEMP",
                    raw_payload=account.get("qr_payload_template")
                )

            else:
                qr_buffer = PaymentQRService.generate_qr(
                    provider=provider,
                    account_name=account_name,
                    account_no=account_no,
                    amount=grand_total,
                    sale_id="TEMP"
                )

        # ----------------------------------------------------------------------
        # OTHER PROVIDERS
        # ----------------------------------------------------------------------

        else:
            qr_buffer = generate_payment_qr(
                provider=provider,
                account_name=account_name,
                account_no=account_no,
                amount=grand_total,
                sale_id="TEMP"
            )

        st.image(
            qr_buffer,
            caption=f"Scan to pay with {provider}",
            width=250
        )

        st.success(
            f"""
💰 Payment Amount

# {grand_total:,.0f} MMK
"""
        )

        st.info(
            f"""
Pay to:

👤 {account_name}

📱 {account_no}

Amount: {grand_total:,.0f} MMK
"""
        )

        if qr_mode == "STATIC":
            st.info(
                f"Scan with {provider} and pay to {account_name} ({account_no})"
            )

            st.warning(
                "⚠️ Static QR is enabled. Customer may need to enter amount manually."
            )

        else:
            st.info(
                f"Pay MMK {grand_total:,.0f} to {account_name} ({account_no})"
            )

        mobile_txn = st.text_input(
            "Transaction ID",
            placeholder="Enter mobile banking transaction number"
        )

        st.session_state.mobile_provider = provider
        st.session_state.mobile_txn = mobile_txn

        received = grand_total

        st.success(
            f"Mobile payment expected: {money(received)}"
        )

    else:
        received = st.number_input(
            "Received Amount",
            min_value=0.0,
            step=100.0
        )

    change = max(0, received - grand_total)

    st.caption(
        f"""
Received : {money(received)}

Change : {money(change)}
"""
    )

    # --------------------------------------------------------------------------
    # COMPLETE SALE
    # --------------------------------------------------------------------------

    if st.button(
        "✅ Complete Sale",
        use_container_width=True,
        type="primary"
    ):

        if received < grand_total:
            st.error("Insufficient payment.")
            return

        start_processing()

        try:
            result = process_checkout(
                cart=cart,
                paid_amount=received,
                warehouse_id=warehouse_id,
                cashier_id=st.session_state.get(
                    "user",
                    {}
                ).get(
                    "id"
                ),
                payment_method=payment_method,
                discount=discount
            )

            if result.get("success", False):
                raw_data = result.get("data", {})
                
                # Supabase က List (သို့) Dict ထွက်လာသည်ကို အလိုအလျောက် စစ်ဆေးခြင်း
                if isinstance(raw_data, list) and len(raw_data) > 0:
                    sale_data = raw_data[0]
                elif isinstance(raw_data, dict):
                    sale_data = raw_data
                else:
                    sale_data = {}

                sale_id = sale_data.get("id")

                # ဂျာနယ်စာရင်း (Double Entry) အလိုအလျောက် ထည့်သွင်းခြင်း
                if sale_id:
                    post_sale_journal_entry(
                        sale_id=int(sale_id),
                        total_amount=float(grand_total),
                        payment_method=str(payment_method)
                    )
                else:
                    # sale_id သေချာမရလျှင် sales ဇယားမှ ID အသစ်ဆုံးကို ယူ၍ ဂျာနယ်သွင်းရန် Fallback
                    try:
                        supabase = get_supabase()
                        latest_sale = supabase.table("sales").select("id").order("id", desc=True).limit(1).execute()
                        if latest_sale.data:
                            fallback_sale_id = latest_sale.data[0]["id"]
                            post_sale_journal_entry(
                                sale_id=int(fallback_sale_id),
                                total_amount=float(grand_total),
                                payment_method=str(payment_method)
                            )
                    except Exception:
                        pass

                sale_data.update({
                    "subtotal": subtotal,
                    "discount": discount,
                    "tax": tax_amount,
                    "tax_rate": tax_rate,
                    "total": grand_total,
                    "paid_amount": received,
                    "change_amount": change,
                    "payment_method": payment_method,
                    "items": cart
                })

                # MOBILE PAYMENT INFO
                if payment_method == "MOBILE":
                    sale_data.update({
                        "mobile_provider":
                            st.session_state.get("mobile_provider"),
                        "mobile_txn":
                            st.session_state.get("mobile_txn")
                    })

                st.session_state.sale_data = sale_data
                st.session_state.show_receipt = True

                st.rerun()

            else:
                st.error(
                    result.get(
                        "message",
                        "Checkout Failed"
                    )
                )

        except Exception as e:
            st.error(
                f"Checkout Error : {e}"
            )

        finally:
            stop_processing()
