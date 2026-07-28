# ==============================================================================
# erp_core/services/inventory_service.py
# ERP ENTERPRISE INVENTORY SERVICE
# Version: V1.2 DI PRODUCTION
#
# FIFO
# Valuation
# Stock Card
# KPI
# Loss Analytics
#
# Dependency Injection Pattern
# ==============================================================================
from erp_core.services.inventory_service import InventoryService

from typing import Any, Dict, List


# ==============================================================================
# Inventory Service
# ==============================================================================


class InventoryService:


    # ==========================================================================
    # Constructor
    # ==========================================================================

    def __init__(self, client):

        self.client = client



    # ==========================================================================
    # Inventory KPI
    # ==========================================================================

    def get_inventory_kpi(
        self
    ) -> Dict[str, Any]:


        try:

            result = (

                self.client

                .table(
                    "inventory_kpi_view"
                )

                .select(
                    "*"
                )

                .single()

                .execute()

            )


            return result.data or {}


        except Exception as e:


            return {

                "success": False,

                "message": str(e)

            }





    # ==========================================================================
    # Warehouse Inventory KPI
    # ==========================================================================

    def get_warehouse_inventory_kpi(
        self
    ) -> List[Dict]:


        try:

            result = (

                self.client

                .table(
                    "warehouse_inventory_kpi_view"
                )

                .select(
                    "*"
                )

                .execute()

            )


            return result.data or []


        except Exception:


            return []





    # ==========================================================================
    # FIFO Inventory Valuation
    # ==========================================================================

    def get_inventory_valuation(
        self
    ) -> List[Dict]:


        try:

            result = (

                self.client

                .table(
                    "inventory_valuation_view"
                )

                .select(
                    "*"
                )

                .execute()

            )


            return result.data or []



        except Exception:


            return []





    # ==========================================================================
    # Inventory Loss Report
    # ==========================================================================

    def get_inventory_loss_report(
        self
    ) -> List[Dict]:


        try:

            result = (

                self.client

                .table(
                    "inventory_loss_kpi_view"
                )

                .select(
                    "*"
                )

                .execute()

            )


            return result.data or []



        except Exception:


            return []





    # ==========================================================================
    # Stock Card
    # ==========================================================================

    def get_stock_card(

        self,

        product_id:int,

        warehouse_id:int

    ) -> List[Dict]:


        try:


            result = (

                self.client

                .table(
                    "stock_card_view"
                )

                .select(
                    "*"
                )

                .eq(
                    "product_id",
                    product_id
                )

                .eq(
                    "warehouse_id",
                    warehouse_id
                )

                .order(
                    "created_at"
                )

                .execute()

            )


            return result.data or []



        except Exception:


            return []





    # ==========================================================================
    # Stock Adjustment History
    # ==========================================================================

    def get_stock_adjustments(

        self,

        warehouse_id=None

    ) -> List[Dict]:


        try:


            query = (

                self.client

                .table(
                    "stock_adjustments"
                )

                .select(
                    "*"
                )

            )


            if warehouse_id:


                query = query.eq(

                    "warehouse_id",

                    warehouse_id

                )



            result = query.execute()


            return result.data or []



        except Exception:


            return []





# ==============================================================================
# Export
# ==============================================================================


__all__ = [

    "InventoryService"

]

# =========================================================
# 🔧 STOCK ADJUSTMENT
# =========================================================

with tab4:

    st.subheader(
        "🔧 Stock Adjustment"
    )


    products = get_inventory_view(
        warehouse_id=selected_wh_id
    )


    if not products:

        st.warning(
            "No products found"
        )


    else:


        product_map = {

            f"{p.get('id')} | {p.get('name')}": p

            for p in products

        }



        selected = st.selectbox(

            "Select Product",

            list(product_map.keys())

        )


        product = product_map[selected]



        product_id = product.get(
            "id"
        )


        current_stock = (

            product.get(
                "available_qty"
            )

            or

            product.get(
                "qty"
            )

            or

            product.get(
                "stock"
            )

            or 0

        )



        st.info(

            f"""
📦 Product : {product.get('name')}

🆔 ID : {product_id}

🏭 Warehouse : {selected_wh_name}

📊 Current Stock : {current_stock}
"""
        )



        adjustment_qty = st.number_input(

            "Adjustment Quantity (+/-)",

            value=0,

            step=1

        )



        reason = st.text_input(

            "Reason",

            value="Manual Stock Adjustment"

        )



        if st.button(

            "💾 Apply Adjustment",

            use_container_width=True

        ):


            result = stock_adjustment_rpc(

                product_id=int(product_id),

                warehouse_id=int(selected_wh_id),

                quantity=int(adjustment_qty),

                reason=reason,

                created_by=st.session_state.get(
                    "user_id"
                )

            )



            if result.get(
                "success"
            ):


                st.success(

                    "✅ Stock Adjustment Created"

                )


                st.json(
                    result
                )


                st.cache_data.clear()


                time.sleep(1)


                st.rerun()



            else:


                st.error(

                    result.get(

                        "message",

                        "Adjustment Failed"

                    )

                )





# =========================================================
# 📊 ENTERPRISE INVENTORY DASHBOARD
# =========================================================

with tab5:


    st.subheader(

        "📊 Enterprise Inventory Dashboard"

    )


    st.caption(

        f"Current Warehouse : {selected_wh_name}"

    )



    # -----------------------------------------------------
    # Inventory KPI
    # -----------------------------------------------------

    try:


        from erp_core.services.inventory_service import (

            InventoryService

        )


        inventory = InventoryService(
            db()
        )


        kpi = inventory.get_inventory_kpi()



        if kpi.get(
            "success"
        ) is False:


            st.error(
                kpi.get(
                    "message"
                )
            )


        else:


            c1,c2,c3,c4,c5 = st.columns(5)


            c1.metric(

                "📦 Products",

                kpi.get(
                    "total_products",
                    0
                )

            )


            c2.metric(

                "🏭 Warehouses",

                kpi.get(
                    "total_warehouses",
                    0
                )

            )


            c3.metric(

                "📊 Stock Qty",

                kpi.get(
                    "total_stock_qty",
                    0
                )

            )


            c4.metric(

                "💰 Inventory Value",

                f"{float(kpi.get('total_inventory_value',0)):,.0f} MMK"

            )


            c5.metric(

                "⚠ Low Stock",

                kpi.get(
                    "low_stock_items",
                    0
                )

            )



    except Exception as e:


        st.error(

            f"Inventory KPI Error : {e}"

        )





    st.divider()



    # -----------------------------------------------------
    # Warehouse KPI
    # -----------------------------------------------------


    st.subheader(

        "🏭 Warehouse Inventory"

    )


    try:


        warehouse_data = (

            inventory

            .get_warehouse_inventory_kpi()

        )



        if warehouse_data:


            show_table(

                warehouse_data

            )


        else:


            st.info(

                "No warehouse data"

            )


    except Exception as e:


        st.error(

            str(e)

        )





    st.divider()



    # -----------------------------------------------------
    # FIFO VALUATION
    # -----------------------------------------------------


    st.subheader(

        "💰 FIFO Inventory Valuation"

    )


    try:


        valuation = (

            inventory

            .get_inventory_valuation()

        )


        if valuation:


            show_table(

                valuation

            )

        else:

            st.info(

                "No FIFO layers"

            )



    except Exception as e:


        st.error(

            str(e)

        )





    st.divider()



    # -----------------------------------------------------
    # LOSS ANALYTICS
    # -----------------------------------------------------


    st.subheader(

        "📉 Inventory Loss Analytics"

    )



    try:


        loss = (

            inventory

            .get_inventory_loss_report()

        )



        if loss:


            show_table(

                loss

            )


        else:


            st.success(

                "No inventory loss"

            )



    except Exception as e:


        st.error(

            str(e)

        )
