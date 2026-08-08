-- ============================================================
-- ERP ENTERPRISE SQLITE BACKUP
-- PART 4 : REPORT / ANALYTICS VIEWS
-- ============================================================

PRAGMA foreign_keys = ON;


-- ============================================================
-- 1. INVENTORY VALUATION
-- ============================================================

DROP VIEW IF EXISTS inventory_valuation;

CREATE VIEW inventory_valuation AS
SELECT
    product_id,
    warehouse_id,
    SUM(qty_remaining) AS stock_qty,
    SUM(
        CAST(qty_remaining AS REAL) * CAST(unit_cost AS REAL)
    ) AS stock_value
FROM inventory_cost_layers
WHERE qty_remaining > 0
GROUP BY
    product_id,
    warehouse_id;


-- ============================================================
-- 2. INVENTORY VALUATION VIEW
-- ============================================================

DROP VIEW IF EXISTS inventory_valuation_view;

CREATE VIEW inventory_valuation_view AS
SELECT
    icl.product_id,
    p.name AS product_name,
    icl.warehouse_id,
    w.name AS warehouse_name,

    SUM(icl.qty_remaining) AS available_qty,

    SUM(
        CAST(icl.qty_remaining AS REAL) *
        CAST(icl.unit_cost AS REAL)
    ) AS stock_value,

    MIN(icl.unit_cost) AS lowest_cost,
    MAX(icl.unit_cost) AS highest_cost,
    COUNT(icl.id) AS cost_layers

FROM inventory_cost_layers AS icl

JOIN products AS p
    ON p.id = icl.product_id

JOIN warehouses AS w
    ON w.id = icl.warehouse_id

WHERE icl.qty_remaining > 0

GROUP BY
    icl.product_id,
    p.name,
    icl.warehouse_id,
    w.name;


-- ============================================================
-- 3. INVENTORY KPI
-- ============================================================

DROP VIEW IF EXISTS inventory_kpi_view;

CREATE VIEW inventory_kpi_view AS
SELECT

    COUNT(DISTINCT product_id)
        AS total_products,

    COUNT(DISTINCT warehouse_id)
        AS total_warehouses,

    COALESCE(SUM(available_qty), 0)
        AS total_stock_qty,

    COALESCE(SUM(stock_value), 0)
        AS total_inventory_value,

    AVG(
        CASE
            WHEN available_qty <> 0
            THEN CAST(stock_value AS REAL) /
                 CAST(available_qty AS REAL)
            ELSE NULL
        END
    ) AS average_unit_value,

    SUM(
        CASE
            WHEN available_qty <= 5 THEN 1
            ELSE 0
        END
    ) AS low_stock_items

FROM inventory_valuation_view;


-- ============================================================
-- 4. WAREHOUSE INVENTORY KPI
-- ============================================================

DROP VIEW IF EXISTS warehouse_inventory_kpi_view;

CREATE VIEW warehouse_inventory_kpi_view AS
SELECT

    warehouse_id,
    warehouse_name,

    SUM(available_qty)
        AS total_qty,

    SUM(stock_value)
        AS total_value,

    COUNT(product_id)
        AS product_count

FROM inventory_valuation_view

GROUP BY
    warehouse_id,
    warehouse_name;


-- ============================================================
-- 5. INVENTORY STOCK VIEW
-- ============================================================

DROP VIEW IF EXISTS inventory_stock_view;

CREATE VIEW inventory_stock_view AS
SELECT

    p.id AS product_id,
    p.name AS product_name,

    w.id AS warehouse_id,
    w.name AS warehouse_name,

    COALESCE(ws.available_qty, 0)
        AS available_qty,

    COALESCE(ws.qty, 0)
        AS qty,

    p.minimum_stock

FROM products AS p

CROSS JOIN warehouses AS w

LEFT JOIN warehouse_stock AS ws
    ON ws.product_id = p.id
    AND ws.warehouse_id = w.id

WHERE p.is_active = 1;


-- ============================================================
-- 6. INVENTORY REORDER VIEW
-- ============================================================

DROP VIEW IF EXISTS view_inventory_reorder;

CREATE VIEW view_inventory_reorder AS
SELECT

    w.id AS warehouse_id,
    w.name AS warehouse_name,

    p.id AS product_id,
    p.name AS product_name,

    s.qty AS current_qty,

    COALESCE(
        p.minimum_stock,
        p.reorder_level,
        10
    ) AS minimum_stock,

    p.supplier_id,
    p.purchase_price,

    CASE
        WHEN s.qty <= COALESCE(
            p.minimum_stock,
            p.reorder_level,
            10
        )
        THEN 1
        ELSE 0
    END AS need_reorder

FROM warehouse_stock AS s

JOIN warehouses AS w
    ON w.id = s.warehouse_id

JOIN products AS p
    ON p.id = s.product_id

WHERE p.is_active = 1;


-- ============================================================
-- 7. INVENTORY STATUS
-- ============================================================

DROP VIEW IF EXISTS view_inventory_status;

CREATE VIEW view_inventory_status AS
SELECT

    w.name AS warehouse_name,
    p.name AS product_name,
    s.qty,

    COALESCE(
        p.reorder_level,
        10
    ) AS reorder_level

FROM warehouse_stock AS s

JOIN warehouses AS w
    ON s.warehouse_id = w.id

JOIN products AS p
    ON s.product_id = p.id;


-- ============================================================
-- 8. STOCK CARD
-- ============================================================

DROP VIEW IF EXISTS stock_card_view;

CREATE VIEW stock_card_view AS

WITH movement_data AS
(
    SELECT

        sm.id AS movement_id,
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
            WHEN sm.qty > 0
            THEN sm.qty
            ELSE 0
        END AS qty_in,

        CASE
            WHEN sm.qty < 0
            THEN ABS(sm.qty)
            ELSE 0
        END AS qty_out

    FROM stock_movements AS sm
)

SELECT

    md.movement_id,
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

    SUM(md.qty) OVER
    (
        PARTITION BY
            md.product_id,
            md.warehouse_id

        ORDER BY
            md.created_at,
            md.movement_id

        ROWS BETWEEN
            UNBOUNDED PRECEDING
            AND CURRENT ROW
    ) AS running_balance

FROM movement_data AS md

JOIN products AS p
    ON p.id = md.product_id

JOIN warehouses AS w
    ON w.id = md.warehouse_id;


-- ============================================================
-- 9. STOCK ADJUSTMENT AUDIT
-- ============================================================

DROP VIEW IF EXISTS stock_adjustment_audit_view;

CREATE VIEW stock_adjustment_audit_view AS
SELECT

    sa.id AS adjustment_id,

    p.id AS product_id,
    p.name AS product_name,

    w.id AS warehouse_id,
    w.name AS warehouse_name,

    sa.adjustment_type,
    sa.qty,
    sa.unit_cost,

    (
        CAST(sa.qty AS REAL) *
        CAST(sa.unit_cost AS REAL)
    ) AS total_loss,

    sa.reason,
    sa.status,
    sa.requested_by,
    sa.approved_by,

    u.full_name AS approved_by_name,

    sa.approved_at,
    sa.created_at

FROM stock_adjustments AS sa

JOIN products AS p
    ON p.id = sa.product_id

JOIN warehouses AS w
    ON w.id = sa.warehouse_id

LEFT JOIN users AS u
    ON u.id = sa.approved_by;


-- ============================================================
-- 10. INVENTORY LOSS KPI
-- ============================================================

DROP VIEW IF EXISTS inventory_loss_kpi_view;

CREATE VIEW inventory_loss_kpi_view AS
SELECT

    reference_type,
    movement_type,

    COUNT(*) AS transactions,

    SUM(ABS(qty))
        AS lost_qty,

    SUM(ABS(total_cost))
        AS total_loss

FROM stock_movements

WHERE qty < 0
  AND movement_type LIKE 'ADJUSTMENT%'

GROUP BY
    reference_type,
    movement_type;


-- ============================================================
-- 11. DAILY SALES REPORT
-- ============================================================

DROP VIEW IF EXISTS view_daily_sales_report;

CREATE VIEW view_daily_sales_report AS
SELECT

    DATE(created_at) AS sale_day,

    COUNT(id)
        AS total_transactions,

    SUM(total_amount)
        AS total_revenue

FROM sales

GROUP BY DATE(created_at);


-- ============================================================
-- 12. DAILY PROFIT REPORT
-- ============================================================

DROP VIEW IF EXISTS daily_profit_report;

CREATE VIEW daily_profit_report AS
SELECT

    DATE(s.created_at) AS sale_date,

    SUM(s.total) AS revenue,

    COALESCE(
        SUM(t.total_cost),
        0
    ) AS cogs,

    (
        SUM(s.total)
        -
        COALESCE(SUM(t.total_cost), 0)
    ) AS gross_profit

FROM sales AS s

LEFT JOIN inventory_cost_transactions AS t
    ON s.id = t.sale_id

GROUP BY DATE(s.created_at)

ORDER BY DATE(s.created_at) DESC;


-- ============================================================
-- 13. SALES PROFIT
-- ============================================================

DROP VIEW IF EXISTS v_sales_profit;

CREATE VIEW v_sales_profit AS
SELECT

    s.id AS sale_id,
    s.invoice_no,
    s.created_at,

    SUM(si.total)
        AS revenue,

    COALESCE(
        SUM(ict.total_cost),
        0
    ) AS cogs,

    (
        SUM(si.total)
        -
        COALESCE(SUM(ict.total_cost), 0)
    ) AS gross_profit,

    CASE
        WHEN SUM(si.total) = 0
        THEN 0

        ELSE ROUND(
            (
                (
                    SUM(si.total)
                    -
                    COALESCE(SUM(ict.total_cost), 0)
                )
                /
                SUM(si.total)
            ) * 100,
            2
        )
    END AS margin_percent

FROM sales AS s

JOIN sale_items AS si
    ON si.sale_id = s.id

LEFT JOIN inventory_cost_transactions AS ict
    ON ict.sale_id = s.id
    AND ict.sale_item_id = si.id

GROUP BY
    s.id,
    s.invoice_no,
    s.created_at;


-- ============================================================
-- 14. REFUND COST REPORT
-- ============================================================

DROP VIEW IF EXISTS refund_cost_report;

CREATE VIEW refund_cost_report AS
SELECT

    reference_id AS refund_id,

    product_id,

    SUM(qty_in)
        AS refund_qty,

    SUM(
        CAST(qty_in AS REAL) *
        CAST(unit_cost AS REAL)
    ) AS refund_cogs

FROM inventory_cost_layers

WHERE reference_type = 'REFUND'

GROUP BY
    reference_id,
    product_id;


-- ============================================================
-- 15. REFUND DETAIL VIEW
-- ============================================================

DROP VIEW IF EXISTS refund_detail_view;

CREATE VIEW refund_detail_view AS
SELECT

    ri.refund_id,
    ri.sale_item_id,
    ri.product_id,

    p.name AS product_name,

    ri.quantity,
    ri.unit_price,

    ri.total AS item_total,

    si.sale_id,
    s.invoice_no

FROM refund_items AS ri

LEFT JOIN products AS p
    ON p.id = ri.product_id

LEFT JOIN sale_items AS si
    ON si.id = ri.sale_item_id

LEFT JOIN sales AS s
    ON s.id = si.sale_id;


-- ============================================================
-- 16. REFUND HEADER VIEW
-- ============================================================

DROP VIEW IF EXISTS refund_header_view;

CREATE VIEW refund_header_view AS
SELECT

    r.id AS refund_id,
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

FROM refunds AS r

LEFT JOIN sales AS s
    ON s.id = r.sale_id

LEFT JOIN users AS cu
    ON cu.id = r.cashier_id

LEFT JOIN users AS pu
    ON pu.id = r.approved_by

LEFT JOIN warehouses AS w
    ON w.id = s.warehouse_id;


-- ============================================================
-- 17. REFUND KPI
-- ============================================================

DROP VIEW IF EXISTS refund_kpi_view;

CREATE VIEW refund_kpi_view AS
SELECT

    COUNT(*) AS total_refunds,

    SUM(
        CASE
            WHEN status = 'PENDING'
            THEN 1
            ELSE 0
        END
    ) AS pending,

    SUM(
        CASE
            WHEN status = 'COMPLETED'
            THEN 1
            ELSE 0
        END
    ) AS completed,

    SUM(
        CASE
            WHEN status = 'REJECTED'
            THEN 1
            ELSE 0
        END
    ) AS rejected,

    COALESCE(
        SUM(refund_amount),
        0
    ) AS total_amount

FROM refunds;


-- ============================================================
-- 18. REFUND REPORT
-- ============================================================

DROP VIEW IF EXISTS refund_report_view;

CREATE VIEW refund_report_view AS
SELECT

    r.id AS refund_id,
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

FROM refunds AS r

LEFT JOIN sales AS s
    ON s.id = r.sale_id

LEFT JOIN refund_items AS ri
    ON ri.refund_id = r.id

LEFT JOIN products AS p
    ON p.id = ri.product_id

LEFT JOIN users AS cu
    ON cu.id = r.cashier_id

LEFT JOIN users AS pu
    ON pu.id = r.approved_by

LEFT JOIN warehouses AS w
    ON w.id = s.warehouse_id;


-- ============================================================
-- 19. SIMPLE REFUND REPORT
-- ============================================================

DROP VIEW IF EXISTS view_refund_report;

CREATE VIEW view_refund_report AS
SELECT

    r.id AS refund_id,
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

FROM refunds AS r

LEFT JOIN sales AS s
    ON s.id = r.sale_id

LEFT JOIN refund_items AS ri
    ON ri.refund_id = r.id

LEFT JOIN products AS p
    ON p.id = ri.product_id

LEFT JOIN users AS u
    ON u.id = r.cashier_id

LEFT JOIN warehouses AS w
    ON w.id = s.warehouse_id;


-- ============================================================
-- 20. TRANSFER COST REPORT
-- ============================================================

DROP VIEW IF EXISTS transfer_cost_report;

CREATE VIEW transfer_cost_report AS
SELECT

    st.id AS transfer_id,
    st.transfer_no,

    st.created_at AS transfer_date,

    wf.name AS from_branch,
    wt.name AS to_branch,

    p.name AS product_name,

    stc.qty,
    stc.unit_cost,
    stc.total_cost

FROM stock_transfer_costs AS stc

JOIN stock_transfers AS st
    ON st.id = stc.transfer_id

JOIN warehouses AS wf
    ON wf.id = st.from_warehouse_id

JOIN warehouses AS wt
    ON wt.id = st.to_warehouse_id

JOIN products AS p
    ON p.id = st.product_id;


-- ============================================================
-- END PART 4
-- ============================================================
