    # --------------------------------------------------
    # PRODUCT SELECT & ADD TO CART (Layout Update)
    # --------------------------------------------------

    # Select Product နှင့် Add Button ကို ဘေးချင်းကပ်ပေါ်စေရန် columns ခွဲခြင်း
    col_sel, col_btn_layout = st.columns([3, 1])

    with col_sel:
        selected = st.selectbox(
            "Select Product",
            matches,
            format_func=product_label,
            key="pos_product_select"
        )

    qty = st.number_input(
        "Quantity",
        min_value=1,
        value=1,
        step=1,
        key="pos_qty"
    )

    if selected:

        price_data = get_cached_price(
            selected.get("id"),
            selected
        )

        final_price = float(
            price_data.get(
                "price",
                0
            )
        )

        st.info(
            f"""
Product :
{selected.get('name')}

Price :
{money(final_price)}

Stock :
{selected.get('available_qty',0)}
"""
        )

        # --------------------------------------------------
        # ADD CART BUTTON (selectbox ဘေးနား သို့မဟုတ် အောက်တန်းတူညီစွာ ထည့်သွင်းခြင်း)
        # --------------------------------------------------
        
        # အကယ်၍ Select product ဘေးနားတည့်တည့်အတိအကျ ကပ်ချင်ပါက col_btn_layout ထဲတွင် ခလုတ်နှင့် quantity ကို ထည့်နိုင်ပါသည်။
        with col_btn_layout:
            # UI ပုံစံလှပစေရန် ခလုတ်ကို Select box နဲ့ အმაင့်တန်းတူဖြစ်အောင် နေရာလွတ် (Spacing) သို့မဟုတ် တိုက်ရိုက်ခလုတ်တင်ပေးနိုင်ပါသည်
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True) # Label နေရာလွတ်ညှိရန်
            
            add_clicked = st.button(
                "➕ Add",
                type="primary",
                use_container_width=True,
                key="add_cart_btn"
            )

        if add_clicked:

            if not check_stock(
                selected,
                qty
            ):
                st.error(
                    "Insufficient stock"
                )
                return products

            add_to_cart(
                st.session_state.cart,
                selected,
                int(qty),
                final_price,
                price_data.get(
                    "source",
                    "SYSTEM"
                )
            )

            st.session_state.cart = (
                st.session_state.cart
            )

            st.success(
                f"{selected.get('name')} added"
            )

            # No full reload
            st.rerun()
