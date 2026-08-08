-- 1. public.branch_profit_report
CREATE OR REPLACE VIEW public.branch_profit_report AS  
SELECT s.warehouse_id,
    w.name AS branch_name,
    ict.product_id,
    p.name AS product_name,
    sum(ict.qty) AS sold_qty,
    sum(si.total) AS revenue,
    sum(ict.total_cost) AS cogs,
    (sum(si.total) - sum(ict.total_cost)) AS gross_profit,
    round((((sum(si.total) - sum(ict.total_cost)) / NULLIF(sum(si.total), (0)::numeric)) * (100)::numeric), 2) AS profit_margin_percent
   FROM ((((inventory_cost_transactions ict
     JOIN sale_items si ON ((si.id = ict.sale_item_id)))
     JOIN sales s ON ((s.id = ict.sale_id)))
     JOIN warehouses w ON ((w.id = s.warehouse_id)))
     JOIN products p ON ((p.id = ict.product_id)))
  GROUP BY s.warehouse_id, w.name, ict.product_id, p.name;

-- 2. public.daily_profit_report
CREATE OR REPLACE VIEW public.daily_profit_report AS  
SELECT date(s.created_at) AS sale_date,
    sum(s.total) AS revenue,
    COALESCE(sum(t.total_cost), (0)::numeric) AS cogs,
    (sum(s.total) - COALESCE(sum(t.total_cost), (0)::numeric)) AS gross_profit
   FROM (sales s
     LEFT JOIN inventory_cost_transactions t ON ((s.id = t.sale_id)))
  GROUP BY (date(s.created_at))
  ORDER BY (date(s.created_at)) DESC;

-- 3. public.daily_profit_report_v1
CREATE OR REPLACE VIEW public.daily_profit_report_v1 AS  
WITH sales AS (
         SELECT date(s_1.created_at) AS sale_date,
            sum(si.total) AS gross_sales
           FROM (public.sales s_1
             JOIN sale_items si ON ((si.sale_id = s_1.id)))
          GROUP BY (date(s_1.created_at))
        ), refunds AS (
         SELECT date(refunds.refund_date) AS sale_date,
            sum(refunds.refund_amount) AS refund_amount
           FROM public.refunds
          GROUP BY (date(refunds.refund_date))
        ), sale_cost AS (
         SELECT date(inventory_cost_transactions.created_at) AS sale_date,
            sum(inventory_cost_transactions.total_cost) AS sale_cogs
           FROM inventory_cost_transactions
          GROUP BY (date(inventory_cost_transactions.created_at))
        ), refund_cost AS (
         SELECT date(inventory_cost_layers.created_at) AS sale_date,
            sum(((inventory_cost_layers.qty_in)::numeric * inventory_cost_layers.unit_cost)) AS refund_cogs
           FROM inventory_cost_layers
          WHERE (inventory_cost_layers.reference_type = 'REFUND'::text)
          GROUP BY (date(inventory_cost_layers.created_at))
        )
 SELECT COALESCE(s.sale_date, r.sale_date, sc.sale_date, rc.sale_date) AS sale_date,
    COALESCE(s.gross_sales, (0)::numeric) AS gross_sales,
    COALESCE(r.refund_amount, (0)::numeric) AS refund_amount,
    (COALESCE(s.gross_sales, (0)::numeric) - COALESCE(r.refund_amount, (0)::numeric)) AS net_sales,
    COALESCE(sc.sale_cogs, (0)::numeric) AS sale_cogs,
    COALESCE(rc.refund_cogs, (0)::numeric) AS refund_cogs,
    (COALESCE(sc.sale_cogs, (0)::numeric) - COALESCE(rc.refund_cogs, (0)::numeric)) AS net_cogs,
    ((COALESCE(s.gross_sales, (0)::numeric) - COALESCE(r.refund_amount, (0)::numeric)) - (COALESCE(sc.sale_cogs, (0)::numeric) - COALESCE(rc.refund_cogs, (0)::numeric))) AS gross_profit,
        CASE
            WHEN ((COALESCE(s.gross_sales, (0)::numeric) - COALESCE(r.refund_amount, (0)::numeric)) > (0)::numeric) THEN round(((((COALESCE(s.gross_sales, (0)::numeric) - COALESCE(r.refund_amount, (0)::numeric)) - (COALESCE(sc.sale_cogs, (0)::numeric) - COALESCE(rc.refund_cogs, (0)::numeric))) / (COALESCE(s.gross_sales, (0)::numeric) - COALESCE(r.refund_amount, (0)::numeric))) * (100)::numeric), 2)
            ELSE (0)::numeric
        END AS profit_margin_percent
   FROM (((sales s
     FULL JOIN refunds r ON ((s.sale_date = r.sale_date)))
     FULL JOIN sale_cost sc ON ((COALESCE(s.sale_date, r.sale_date) = sc.sale_date)))
     FULL JOIN refund_cost rc ON ((COALESCE(s.sale_date, r.sale_date, sc.sale_date) = rc.sale_date)));

-- 4. public.inventory_kpi_view
CREATE OR REPLACE VIEW public.inventory_kpi_view AS  
SELECT count(DISTINCT product_id) AS total_products,
    count(DISTINCT warehouse_id) AS total_warehouses,
    sum(available_qty) AS total_stock_qty,
    sum(stock_value) AS total_inventory_value,
    avg((stock_value / (NULLIF(available_qty, 0))::numeric)) AS average_unit_value,
    sum(
        CASE
            WHEN (available_qty <= 5) THEN 1
            ELSE 0
        END) AS low_stock_items
   FROM inventory_valuation_view;

-- 5. public.inventory_loss_kpi_view
CREATE OR REPLACE VIEW public.inventory_loss_kpi_view AS  
SELECT reference_type,
    movement_type,
    count(*) AS transactions,
    sum(abs(qty)) AS lost_qty,
    sum(abs(total_cost)) AS total_loss
   FROM stock_movements sm
  WHERE ((qty < (0)::numeric) AND (movement_type ~~ 'ADJUSTMENT%'::text))
  GROUP BY reference_type, movement_type;

-- 6. public.inventory_stock_view
CREATE OR REPLACE VIEW public.inventory_stock_view AS  
SELECT p.id AS product_id,
    p.name AS product_name,
    w.id AS warehouse_id,
    w.name AS warehouse_name,
    COALESCE((ws.available_qty)::bigint, (0)::bigint) AS available_qty,
    COALESCE((ws.qty)::bigint, (0)::bigint) AS qty,
    p.minimum_stock
   FROM ((products p
     CROSS JOIN warehouses w)
     LEFT JOIN warehouse_stock ws ON (((ws.product_id = p.id) AND (ws.warehouse_id = w.id))))
  WHERE (p.is_active = true);

-- 7. public.inventory_valuation
CREATE OR REPLACE VIEW public.inventory_valuation AS  
SELECT product_id,
    warehouse_id,
    sum(qty_remaining) AS stock_qty,
    sum(((qty_remaining)::numeric * unit_cost)) AS stock_value
   FROM inventory_cost_layers icl
  WHERE (qty_remaining > 0)
  GROUP BY product_id, warehouse_id;

-- 8. public.inventory_valuation_view
CREATE OR REPLACE VIEW public.inventory_valuation_view AS  
SELECT icl.product_id,
    p.name AS product_name,
    icl.warehouse_id,
    w.name AS warehouse_name,
    sum(icl.qty_remaining) AS available_qty,
    sum(((icl.qty_remaining)::numeric * icl.unit_cost)) AS stock_value,
    min(icl.unit_cost) AS lowest_cost,
    max(icl.unit_cost) AS highest_cost,
    count(icl.id) AS cost_layers
   FROM ((inventory_cost_layers icl
     JOIN products p ON ((p.id = icl.product_id)))
     JOIN warehouses w ON ((w.id = icl.warehouse_id)))
  WHERE (icl.qty_remaining > 0)
  GROUP BY icl.product_id, p.name, icl.warehouse_id, w.name;

-- 9. public.pos_products_view
CREATE OR REPLACE VIEW public.pos_products_view AS  
SELECT p.id,
    p.name,
    p.sku,
    p.barcode,
    p.purchase_price,
    p.selling_price,
    p.owner_selling_price,
    p.owner_price_locked,
        CASE
            WHEN ((p.owner_price_locked = true) AND (p.owner_selling_price IS NOT NULL)) THEN p.owner_selling_price
            WHEN (p.markup_percent IS NOT NULL) THEN round((p.purchase_price + ((p.purchase_price * p.markup_percent) / (100)::numeric)), 2)
            WHEN (c.markup_percent IS NOT NULL) THEN round((p.purchase_price + ((p.purchase_price * c.markup_percent) / (100)::numeric)), 2)
            WHEN (s.value IS NOT NULL) THEN round((p.purchase_price + ((p.purchase_price * (s.value)::numeric) / (100)::numeric)), 2)
            ELSE p.selling_price
        END AS final_selling_price,
        CASE
            WHEN ((p.owner_price_locked = true) AND (p.owner_selling_price IS NOT NULL)) THEN 'OWNER'::text
            WHEN (p.markup_percent IS NOT NULL) THEN 'PRODUCT'::text
            WHEN (c.markup_percent IS NOT NULL) THEN 'CATEGORY'::text
            WHEN (s.value IS NOT NULL) THEN 'SYSTEM'::text
            ELSE 'MANUAL'::text
        END AS price_source,
    c.id AS category_id,
    c.name AS category,
    ws.warehouse_id,
    COALESCE(ws.qty, 0) AS qty,
    COALESCE(ws.reserved_qty, 0) AS reserved_qty,
    COALESCE(ws.available_qty, 0) AS available_qty,
    p.minimum_stock
   FROM (((products p
     LEFT JOIN categories c ON ((c.id = p.category_id)))
     LEFT JOIN warehouse_stock ws ON ((ws.product_id = p.id)))
     LEFT JOIN settings s ON ((s.key = 'DEFAULT_MARKUP_PERCENT'::text)));

-- 10. public.product_profit_report
CREATE OR REPLACE VIEW public.product_profit_report AS  
WITH sales AS (
         SELECT si.product_id,
            sum(si.quantity) AS sold_qty,
            sum(si.total) AS gross_sales
           FROM sale_items si
          GROUP BY si.product_id
        ), refunds AS (
         SELECT ri.product_id,
            sum(ri.quantity) AS refund_qty,
            sum(ri.total) AS refund_amount
           FROM refund_items ri
          GROUP BY ri.product_id
        ), costs AS (
         SELECT ict.product_id,
            sum(ict.qty) AS cogs_qty,
            sum(ict.total_cost) AS cogs
           FROM inventory_cost_transactions ict
          GROUP BY ict.product_id
        )
 SELECT s.product_id,
    p.name,
    s.sold_qty,
    COALESCE(r.refund_qty, (0)::bigint) AS refund_qty,
    s.gross_sales,
    COALESCE(r.refund_amount, (0)::numeric) AS refund_amount,
    (s.gross_sales - COALESCE(r.refund_amount, (0)::numeric)) AS net_sales,
    COALESCE(c.cogs, (0)::numeric) AS cogs,
    ((s.gross_sales - COALESCE(r.refund_amount, (0)::numeric)) - COALESCE(c.cogs, (0)::numeric)) AS gross_profit,
    round(((((s.gross_sales - COALESCE(r.refund_amount, (0)::numeric)) - COALESCE(c.cogs, (0)::numeric)) / NULLIF((s.gross_sales - COALESCE(r.refund_amount, (0)::numeric)), (0)::numeric)) * (100)::numeric), 2) AS profit_margin_percent,
    p.final_selling_price,
    p.price_source,
    p.owner_selling_price,
    p.owner_price_locked,
        CASE
            WHEN ((p.owner_selling_price IS NULL) AND (p.markup_percent IS NOT NULL)) THEN p.markup_percent
            ELSE NULL::numeric
        END AS markup_percent,
        CASE
            WHEN ((p.owner_selling_price IS NULL) AND (p.markup_percent IS NULL) AND (cat.markup_percent IS NOT NULL)) THEN cat.markup_percent
            ELSE NULL::numeric
        END AS category_markup
   FROM ((((sales s
     JOIN products p ON ((p.id = s.product_id)))
     LEFT JOIN categories cat ON ((cat.id = p.category_id)))
     LEFT JOIN refunds r ON ((r.product_id = s.product_id)))
     LEFT JOIN costs c ON ((c.product_id = s.product_id)));

-- 11. public.product_profit_report_final
CREATE OR REPLACE VIEW public.product_profit_report_final AS  
SELECT si.product_id,
    p.name,
    sum(si.quantity) AS sold_qty,
    sum(si.total) AS revenue,
    COALESCE(sum(ict.total_cost), (0)::numeric) AS cogs,
    (sum(si.total) - COALESCE(sum(ict.total_cost), (0)::numeric)) AS gross_profit,
    p.final_selling_price,
    p.price_source,
    p.owner_selling_price,
    p.markup_percent,
    c.markup_percent AS category_markup
   FROM (((sale_items si
     JOIN products p ON ((p.id = si.product_id)))
     LEFT JOIN categories c ON ((c.id = p.category_id)))
     LEFT JOIN inventory_cost_transactions ict ON ((ict.sale_item_id = si.id)))
  GROUP BY si.product_id, p.name, p.final_selling_price, p.price_source, p.owner_selling_price, p.markup_percent, c.markup_percent;

-- 12. public.product_profit_report_v2
CREATE OR REPLACE VIEW public.product_profit_report_v2 AS  
WITH sales_data AS (
         SELECT si.product_id,
            sum(si.quantity) AS sold_qty,
            sum(si.total) AS sales_amount
           FROM sale_items si
          GROUP BY si.product_id
        ), cogs_data AS (
         SELECT ict.product_id,
            sum(ict.total_cost) AS total_cogs
           FROM inventory_cost_transactions ict
          WHERE (ict.sale_id <> 999)
          GROUP BY ict.product_id
        ), refund_data AS (
         SELECT ri.product_id,
            sum(ri.total) AS refund_amount,
            sum(((ri.quantity)::numeric * ict.unit_cost)) AS refund_cost
           FROM (refund_items ri
             JOIN inventory_cost_transactions ict ON ((ict.sale_item_id = ri.sale_item_id)))
          GROUP BY ri.product_id
        )
 SELECT s.product_id,
    s.sold_qty,
    (s.sales_amount - COALESCE(r.refund_amount, (0)::numeric)) AS revenue,
    (COALESCE(c.total_cogs, (0)::numeric) - COALESCE(r.refund_cost, (0)::numeric)) AS cogs
   FROM ((sales_data s
     LEFT JOIN cogs_data c ON ((c.product_id = s.product_id)))
     LEFT JOIN refund_data r ON ((r.product_id = s.product_id)));

-- 13. public.product_profit_report_v3
CREATE OR REPLACE VIEW public.product_profit_report_v3 AS  
WITH sales AS (
         SELECT si.product_id,
            sum(si.quantity) AS sold_qty,
            sum(si.total) AS gross_sales
           FROM sale_items si
          GROUP BY si.product_id
        ), refunds AS (
         SELECT ri.product_id,
            sum(ri.quantity) AS refund_qty,
            sum(ri.total) AS refund_amount
           FROM refund_items ri
          GROUP BY ri.product_id
        ), costs AS (
         SELECT ict.product_id,
            sum(ict.qty) AS cogs_qty,
            sum(ict.total_cost) AS cogs
           FROM inventory_cost_transactions ict
          GROUP BY ict.product_id
        )
 SELECT s.product_id,
    s.sold_qty,
    COALESCE(r.refund_qty, (0)::bigint) AS refund_qty,
    s.gross_sales,
    COALESCE(r.refund_amount, (0)::numeric) AS refund_amount,
    (s.gross_sales - COALESCE(r.refund_amount, (0)::numeric)) AS net_sales,
    COALESCE(c.cogs, (0)::numeric) AS cogs,
    ((s.gross_sales - COALESCE(r.refund_amount, (0)::numeric)) - COALESCE(c.cogs, (0)::numeric)) AS gross_profit,
    round(((((s.gross_sales - COALESCE(r.refund_amount, (0)::numeric)) - COALESCE(c.cogs, (0)::numeric)) / NULLIF((s.gross_sales - COALESCE(r.refund_amount, (0)::numeric)), (0)::numeric)) * (100)::numeric), 2) AS profit_margin_percent
   FROM ((sales s
     LEFT JOIN refunds r ON ((r.product_id = s.product_id)))
     LEFT JOIN costs c ON ((c.product_id = s.product_id)));

-- 14. public.product_profit_report_v4
CREATE OR REPLACE VIEW public.product_profit_report_v4 AS  
WITH sales AS (
         SELECT si.product_id,
            sum(si.quantity) AS sold_qty,
            sum(si.total) AS gross_sales
           FROM sale_items si
          GROUP BY si.product_id
        ), refunds AS (
         SELECT ri.product_id,
            sum(ri.quantity) AS refund_qty,
            sum(ri.total) AS refund_amount
           FROM refund_items ri
          GROUP BY ri.product_id
        ), sale_cost AS (
         SELECT ict.product_id,
            sum(ict.total_cost) AS sale_cogs
           FROM inventory_cost_transactions ict
          GROUP BY ict.product_id
        ), refund_cost AS (
         SELECT refund_cost_report.product_id,
            sum(refund_cost_report.refund_cogs) AS refund_cogs
           FROM refund_cost_report
          GROUP BY refund_cost_report.product_id
        )
 SELECT s.product_id,
    s.sold_qty,
    COALESCE(r.refund_qty, (0)::bigint) AS refund_qty,
    s.gross_sales,
    COALESCE(r.refund_amount, (0)::numeric) AS refund_amount,
    (s.gross_sales - COALESCE(r.refund_amount, (0)::numeric)) AS net_sales,
    COALESCE(sc.sale_cogs, (0)::numeric) AS sale_cogs,
    COALESCE(rc.refund_cogs, (0)::numeric) AS refund_cogs,
    (COALESCE(sc.sale_cogs, (0)::numeric) - COALESCE(rc.refund_cogs, (0)::numeric)) AS net_cogs,
    ((s.gross_sales - COALESCE(r.refund_amount, (0)::numeric)) - (COALESCE(sc.sale_cogs, (0)::numeric) - COALESCE(rc.refund_cogs, (0)::numeric))) AS gross_profit,
    round(((((s.gross_sales - COALESCE(r.refund_amount, (0)::numeric)) - (COALESCE(sc.sale_cogs, (0)::numeric) - COALESCE(rc.refund_cogs, (0)::numeric))) / NULLIF((s.gross_sales - COALESCE(r.refund_amount, (0)::numeric)), (0)::numeric)) * (100)::numeric), 2) AS profit_margin_percent
   FROM (((sales s
     LEFT JOIN refunds r ON ((r.product_id = s.product_id)))
     LEFT JOIN sale_cost sc ON ((sc.product_id = s.product_id)))
     LEFT JOIN refund_cost rc ON ((rc.product_id = s.product_id)));

-- 15. public.product_profit_report_v5
CREATE OR REPLACE VIEW public.product_profit_report_v5 AS  
WITH sales AS (
         SELECT si.product_id,
            sum(si.quantity) AS sold_qty,
            sum(si.total) AS gross_sales
           FROM sale_items si
          GROUP BY si.product_id
        ), refunds AS (
         SELECT ri.product_id,
            sum(ri.quantity) AS refund_qty,
            sum(ri.total) AS refund_amount
           FROM refund_items ri
          GROUP BY ri.product_id
        ), costs AS (
         SELECT ict.product_id,
            sum(ict.qty) AS cogs_qty,
            sum(ict.total_cost) AS cogs
           FROM inventory_cost_transactions ict
          GROUP BY ict.product_id
        )
 SELECT s.product_id,
    p.name,
    s.sold_qty,
    COALESCE(r.refund_qty, (0)::bigint) AS refund_qty,
    s.gross_sales,
    COALESCE(r.refund_amount, (0)::numeric) AS refund_amount,
    (s.gross_sales - COALESCE(r.refund_amount, (0)::numeric)) AS net_sales,
    COALESCE(c.cogs, (0)::numeric) AS cogs,
    ((s.gross_sales - COALESCE(r.refund_amount, (0)::numeric)) - COALESCE(c.cogs, (0)::numeric)) AS gross_profit,
    round(((((s.gross_sales - COALESCE(r.refund_amount, (0)::numeric)) - COALESCE(c.cogs, (0)::numeric)) / NULLIF((s.gross_sales - COALESCE(r.refund_amount, (0)::numeric)), (0)::numeric)) * (100)::numeric), 2) AS profit_margin_percent,
    p.final_selling_price,
    p.price_source,
    p.owner_selling_price,
    p.owner_price_locked,
        CASE
            WHEN ((p.owner_selling_price IS NULL) AND (p.markup_percent IS NOT NULL)) THEN p.markup_percent
            ELSE NULL::numeric
        END AS markup_percent,
        CASE
            WHEN ((p.owner_selling_price IS NULL) AND (p.markup_percent IS NULL) AND (cat.markup_percent IS NOT NULL)) THEN cat.markup_percent
            ELSE NULL::numeric
        END AS category_markup
   FROM ((((sales s
     JOIN products p ON ((p.id = s.product_id)))
     LEFT JOIN categories cat ON ((cat.id = p.category_id)))
     LEFT JOIN refunds r ON ((r.product_id = s.product_id)))
     LEFT JOIN costs c ON ((c.product_id = s.product_id)));

-- 16. public.refund_cost_report
CREATE OR REPLACE VIEW public.refund_cost_report AS  
SELECT reference_id AS refund_id,
    product_id,
    sum(qty_in) AS refund_qty,
    sum(((qty_in)::numeric * unit_cost)) AS refund_cogs
   FROM inventory_cost_layers il
  WHERE (reference_type = 'REFUND'::text)
  GROUP BY reference_id, product_id;

-- 17. public.refund_detail_view
CREATE OR REPLACE VIEW public.refund_detail_view AS  
SELECT ri.refund_id,
    ri.sale_item_id,
    ri.product_id,
    p.name AS product_name,
    ri.quantity,
    ri.unit_price,
    ri.total AS item_total,
    si.sale_id,
    s.invoice_no
   FROM (((refund_items ri
     LEFT JOIN products p ON ((p.id = ri.product_id)))
     LEFT JOIN sale_items si ON ((si.id = ri.sale_item_id)))
     LEFT JOIN sales s ON ((s.id = si.sale_id)));

-- 18. public.refund_header_view
CREATE OR REPLACE VIEW public.refund_header_view AS  
SELECT r.id AS refund_id,
    r.sale_id,
    s.invoice_no,
    r.refund_date,
    r.refund_amount,
    r.status,
    r.reason,
    cu.full_name AS cashier_name,
    pu.full_name AS processed_by,
    r.approved_at,
    w.name AS warehouse_name
   FROM ((((refunds r
     LEFT JOIN sales s ON ((s.id = r.sale_id)))
     LEFT JOIN users cu ON ((cu.id = r.cashier_id)))
     LEFT JOIN users pu ON ((pu.id = r.approved_by)))
     LEFT JOIN warehouses w ON ((w.id = s.warehouse_id)));

-- 19. public.refund_kpi_view
CREATE OR REPLACE VIEW public.refund_kpi_view AS  
SELECT count(*) AS total_refunds,
    count(*) FILTER (WHERE (status = 'PENDING'::text)) AS pending,
    count(*) FILTER (WHERE (status = 'COMPLETED'::text)) AS completed,
    count(*) FILTER (WHERE (status = 'REJECTED'::text)) AS rejected,
    COALESCE(sum(refund_amount), (0)::numeric) AS total_amount
   FROM refunds;

-- 20. public.refund_report_view
CREATE OR REPLACE VIEW public.refund_report_view AS  
SELECT r.id AS refund_id,
    r.sale_id,
    s.invoice_no,
    r.refund_date,
    r.refund_amount,
    r.status,
    r.reason,
    ri.product_id,
    p.name AS product_name,
    ri.quantity,
    ri.unit_price,
    ri.total AS item_total,
    cu.full_name AS cashier_name,
    pu.full_name AS processed_by,
    r.approved_at,
    w.name AS warehouse_name
   FROM ((((((refunds r
     LEFT JOIN sales s ON ((s.id = r.sale_id)))
     LEFT JOIN refund_items ri ON ((ri.refund_id = r.id)))
     LEFT JOIN products p ON ((p.id = ri.product_id)))
     LEFT JOIN users cu ON ((cu.id = r.cashier_id)))
     LEFT JOIN users pu ON ((pu.id = r.approved_by)))
     LEFT JOIN warehouses w ON ((w.id = s.warehouse_id)));

-- 21. public.stock_adjustment_audit_view
CREATE OR REPLACE VIEW public.stock_adjustment_audit_view AS  
SELECT sa.id AS adjustment_id,
    p.id AS product_id,
    p.name AS product_name,
    w.id AS warehouse_id,
    w.name AS warehouse_name,
    sa.adjustment_type,
    sa.qty,
    sa.unit_cost,
    (sa.qty * sa.unit_cost) AS total_loss,
    sa.reason,
    sa.status,
    sa.requested_by,
    sa.approved_by,
    u.full_name AS approved_by_name,
    sa.approved_at,
    sa.created_at
   FROM (((stock_adjustments sa
     JOIN products p ON ((p.id = sa.product_id)))
     JOIN warehouses w ON ((w.id = sa.warehouse_id)))
     LEFT JOIN users u ON ((u.id = sa.approved_by)));

-- 22. public.stock_card_view
CREATE OR REPLACE VIEW public.stock_card_view AS  
WITH movement_data AS (
         SELECT sm.id AS movement_id,
            sm.product_id,
            sm.warehouse_id,
            sm.movement_type,
            sm.qty,
            sm.unit_cost,
            sm.total_cost,
            sm.reference_type,
            sm.reference_id,
            sm.note,
            sm.created_at,
                CASE
                    WHEN (sm.qty > (0)::numeric) THEN sm.qty
                    ELSE (0)::numeric
                END AS qty_in,
                CASE
                    WHEN (sm.qty < (0)::numeric) THEN abs(sm.qty)
                    ELSE (0)::numeric
                END AS qty_out
           FROM stock_movements sm
        )
 SELECT md.movement_id,
    md.product_id,
    p.name AS product_name,
    md.warehouse_id,
    w.name AS warehouse_name,
    md.movement_type,
    md.reference_type,
    md.reference_id,
    md.qty_in,
    md.qty_out,
    md.unit_cost,
    md.total_cost,
    md.note,
    md.created_at,
    sum(md.qty) OVER (PARTITION BY md.product_id, md.warehouse_id ORDER BY md.created_at, md.movement_id) AS running_balance
   FROM ((movement_data md
     JOIN products p ON ((p.id = md.product_id)))
     JOIN warehouses w ON ((w.id = md.warehouse_id)));

-- 23. public.transfer_cost_report
CREATE OR REPLACE VIEW public.transfer_cost_report AS  
SELECT st.id AS transfer_id,
    st.transfer_no,
    st.created_at AS transfer_date,
    wf.name AS from_branch,
    wt.name AS to_branch,
    p.name AS product_name,
    stc.qty,
    stc.unit_cost,
    stc.total_cost
   FROM ((((stock_transfer_costs stc
     JOIN stock_transfers st ON ((st.id = stc.transfer_id)))
     JOIN warehouses wf ON ((wf.id = st.from_warehouse_id)))
     JOIN warehouses wt ON ((wt.id = st.to_warehouse_id)))
     JOIN products p ON ((p.id = st.product_id)));

-- 24. public.v_sales_profit
CREATE OR REPLACE VIEW public.v_sales_profit AS  
SELECT s.id AS sale_id,
    s.invoice_no,
    s.created_at,
    sum(si.total) AS revenue,
    COALESCE(sum(ict.total_cost), (0)::numeric) AS cogs,
    (sum(si.total) - COALESCE(sum(ict.total_cost), (0)::numeric)) AS gross_profit,
        CASE
            WHEN (sum(si.total) = (0)::numeric) THEN (0)::numeric
            ELSE round((((sum(si.total) - COALESCE(sum(ict.total_cost), (0)::numeric)) / sum(si.total)) * (100)::numeric), 2)
        END AS margin_percent
   FROM ((sales s
     JOIN sale_items si ON ((si.sale_id = s.id)))
     LEFT JOIN inventory_cost_transactions ict ON (((ict.sale_id = s.id) AND (ict.sale_item_id = si.id))))
  GROUP BY s.id, s.invoice_no, s.created_at;

-- 25. public.view_daily_sales_report
CREATE OR REPLACE VIEW public.view_daily_sales_report AS  
SELECT date_trunc('day'::text, created_at) AS sale_day,
    count(id) AS total_transactions,
    sum(total_amount) AS total_revenue
   FROM sales
  GROUP BY (date_trunc('day'::text, created_at));

-- 26. public.view_inventory_reorder
CREATE OR REPLACE VIEW public.view_inventory_reorder AS  
SELECT w.id AS warehouse_id,
    w.name AS warehouse_name,
    p.id AS product_id,
    p.name AS product_name,
    s.qty AS current_qty,
    COALESCE(p.minimum_stock, p.reorder_level, ( SELECT (erp_settings.value)::integer AS value
           FROM erp_settings
          WHERE (erp_settings.key = 'min_stock'::text))) AS minimum_stock,
    p.supplier_id,
    p.purchase_price,
        CASE
            WHEN (s.qty <= COALESCE(p.minimum_stock, p.reorder_level, ( SELECT (erp_settings.value)::integer AS value
               FROM erp_settings
              WHERE (erp_settings.key = 'min_stock'::text)))) THEN true
            ELSE false
        END AS need_reorder
   FROM ((warehouse_stock s
     JOIN warehouses w ON ((w.id = s.warehouse_id)))
     JOIN products p ON ((p.id = s.product_id)))
  WHERE (p.is_active = true);

-- 27. public.view_inventory_status
CREATE OR REPLACE VIEW public.view_inventory_status AS  
SELECT w.name AS warehouse_name,
    p.name AS product_name,
    s.qty,
    COALESCE(( SELECT ((erp_settings.value)::numeric)::integer AS value
           FROM erp_settings
          WHERE (erp_settings.key = 'min_stock'::text)
         LIMIT 1), p.reorder_level, 10) AS reorder_level
   FROM ((warehouse_stock s
     JOIN warehouses w ON ((s.warehouse_id = w.id)))
     JOIN products p ON ((s.product_id = p.id)));

-- 28. public.view_refund_report
CREATE OR REPLACE VIEW public.view_refund_report AS  
SELECT r.id AS refund_id,
    r.sale_id,
    s.invoice_no,
    r.refund_date,
    r.reason,
    r.refund_amount,
    ri.product_id,
    p.name AS product_name,
    ri.quantity,
    ri.unit_price,
    ri.total AS item_total,
    u.full_name AS cashier_name,
    w.name AS warehouse_name
   FROM (((((refunds r
     LEFT JOIN sales s ON ((s.id = r.sale_id)))
     LEFT JOIN refund_items ri ON ((ri.refund_id = r.id)))
     LEFT JOIN products p ON ((p.id = ri.product_id)))
     LEFT JOIN users u ON ((u.id = r.cashier_id)))
     LEFT JOIN warehouses w ON ((w.id = s.warehouse_id)));

-- 29. public.warehouse_inventory_kpi_view
CREATE OR REPLACE VIEW public.warehouse_inventory_kpi_view AS  
SELECT warehouse_id,
    warehouse_name,
    sum(available_qty) AS total_qty,
    sum(stock_value) AS total_value,
    count(product_id) AS product_count
   FROM inventory_valuation_view
  GROUP BY warehouse_id, warehouse_name;
