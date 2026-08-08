-- ============================================================================
-- ERP SQLITE BACKUP
-- PART 6 / 6
-- REPORT VIEWS
-- SQLite Compatible
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ============================================================================
-- 1. PRODUCT PROFIT REPORT
-- ============================================================================

DROP VIEW IF EXISTS product_profit_report;

CREATE VIEW product_profit_report AS
WITH sales AS (
    SELECT
        si.product_id,
        SUM(si.quantity) AS sold_qty,
        SUM(si.total) AS gross_sales
    FROM sale_items si
    GROUP BY si.product_id
),
refunds AS (
    SELECT
        ri.product_id,
        SUM(ri.quantity) AS refund_qty,
        SUM(ri.total) AS refund_amount
    FROM refund_items ri
    GROUP BY ri.product_id
),
costs AS (
    SELECT
        ict.product_id,
        SUM(ict.qty) AS cogs_qty,
        SUM(ict.total_cost) AS cogs
    FROM inventory_cost_transactions ict
    GROUP BY ict.product_id
)
SELECT
    s.product_id,
    p.name,
    s.sold_qty,

    COALESCE(r.refund_qty, 0) AS refund_qty,

    s.gross_sales,

    COALESCE(r.refund_amount, 0) AS refund_amount,

    (
        s.gross_sales
        - COALESCE(r.refund_amount, 0)
    ) AS net_sales,

    COALESCE(c.cogs, 0) AS cogs,

    (
        s.gross_sales
        - COALESCE(r.refund_amount, 0)
        - COALESCE(c.cogs, 0)
    ) AS gross_profit,

    CASE
        WHEN (
            s.gross_sales
            - COALESCE(r.refund_amount, 0)
        ) <> 0
        THEN ROUND(
            (
                (
                    s.gross_sales
                    - COALESCE(r.refund_amount, 0)
                    - COALESCE(c.cogs, 0)
                )
                /
                (
                    s.gross_sales
                    - COALESCE(r.refund_amount, 0)
                )
            ) * 100,
            2
        )
        ELSE 0
    END AS profit_margin_percent,

    p.final_selling_price,
    p.price_source,
    p.owner_selling_price,
    p.owner_price_locked,

    CASE
        WHEN p.owner_selling_price IS NULL
         AND p.markup_percent IS NOT NULL
        THEN p.markup_percent
        ELSE NULL
    END AS markup_percent,

    CASE
        WHEN p.owner_selling_price IS NULL
         AND p.markup_percent IS NULL
         AND c2.markup_percent IS NOT NULL
        THEN c2.markup_percent
        ELSE NULL
    END AS category_markup

FROM sales s

JOIN products p
    ON p.id = s.product_id

LEFT JOIN categories c2
    ON c2.id = p.category_id

LEFT JOIN refunds r
    ON r.product_id = s.product_id

LEFT JOIN costs c
    ON c.product_id = s.product_id;


-- ============================================================================
-- 2. DAILY PROFIT REPORT
-- ============================================================================

DROP VIEW IF EXISTS daily_profit_report;

CREATE VIEW daily_profit_report AS
WITH sales_data AS (
    SELECT
        DATE(s.created_at) AS sale_date,
        SUM(si.total) AS revenue
    FROM sales s
    JOIN sale_items si
        ON si.sale_id = s.id
    GROUP BY DATE(s.created_at)
),
cost_data AS (
    SELECT
        DATE(ict.created_at) AS sale_date,
        SUM(ict.total_cost) AS cogs
    FROM inventory_cost_transactions ict
    GROUP BY DATE(ict.created_at)
)
SELECT
    COALESCE(s.sale_date, c.sale_date) AS sale_date,

    COALESCE(s.revenue, 0) AS revenue,

    COALESCE(c.cogs, 0) AS cogs,

    (
        COALESCE(s.revenue, 0)
        - COALESCE(c.cogs, 0)
    ) AS gross_profit

FROM sales_data s

LEFT JOIN cost_data c
    ON c.sale_date = s.sale_date

UNION

SELECT
    c.sale_date,
    0 AS revenue,
    c.cogs,
    -c.cogs AS gross_profit

FROM cost_data c

LEFT JOIN sales_data s
    ON s.sale_date = c.sale_date

WHERE s.sale_date IS NULL;


-- ============================================================================
-- 3. BRANCH PROFIT REPORT
-- ============================================================================

DROP VIEW IF EXISTS branch_profit_report;

CREATE VIEW branch_profit_report AS
SELECT
    s.warehouse_id,

    w.name AS branch_name,

    ict.product_id,

    p.name AS product_name,

    SUM(ict.qty) AS sold_qty,

    SUM(si.total) AS revenue,

    SUM(ict.total_cost) AS cogs,

    (
        SUM(si.total)
        - SUM(ict.total_cost)
    ) AS gross_profit,

    CASE
        WHEN SUM(si.total) <> 0
        THEN ROUND(
            (
                (
                    SUM(si.total)
                    - SUM(ict.total_cost)
                )
                / SUM(si.total)
            ) * 100,
            2
        )
        ELSE 0
    END AS profit_margin_percent

FROM inventory_cost_transactions ict

JOIN sale_items si
    ON si.id = ict.sale_item_id

JOIN sales s
    ON s.id = ict.sale_id

JOIN warehouses w
    ON w.id = s.warehouse_id

JOIN products p
    ON p.id = ict.product_id

GROUP BY
    s.warehouse_id,
    w.name,
    ict.product_id,
    p.name;


-- ============================================================================
-- 4. SALES PROFIT
-- ============================================================================

DROP VIEW IF EXISTS v_sales_profit;

CREATE VIEW v_sales_profit AS
SELECT
    s.id AS sale_id,

    s.invoice_no,

    s.created_at,

    SUM(si.total) AS revenue,

    COALESCE(
        SUM(ict.total_cost),
        0
    ) AS cogs,

    (
        SUM(si.total)
        - COALESCE(SUM(ict.total_cost), 0)
    ) AS gross_profit,

    CASE
        WHEN SUM(si.total) <> 0
        THEN ROUND(
            (
                (
                    SUM(si.total)
                    - COALESCE(SUM(ict.total_cost), 0)
                )
                / SUM(si.total)
            ) * 100,
            2
        )
        ELSE 0
    END AS margin_percent

FROM sales s

JOIN sale_items si
    ON si.sale_id = s.id

LEFT JOIN inventory_cost_transactions ict
    ON ict.sale_id = s.id
   AND ict.sale_item_id = si.id

GROUP BY
    s.id,
    s.invoice_no,
    s.created_at;


-- ============================================================================
-- 5. DAILY SALES REPORT
-- ============================================================================

DROP VIEW IF EXISTS view_daily_sales_report;

CREATE VIEW view_daily_sales_report AS
SELECT
    DATE(created_at) AS sale_day,

    COUNT(id) AS total_transactions,

    SUM(
        COALESCE(total_amount, total)
    ) AS total_revenue

FROM sales

GROUP BY DATE(created_at);


-- ============================================================================
-- 6. INVENTORY VALUATION
-- ============================================================================

DROP VIEW IF EXISTS inventory_valuation;

CREATE VIEW inventory_valuation AS
SELECT
    product_id,

    warehouse_id,

    SUM(qty_remaining) AS stock_qty,

    SUM(
        qty_remaining * unit_cost
    ) AS stock_value

FROM inventory_cost_layers

WHERE qty_remaining > 0

GROUP BY
    product_id,
    warehouse_id;


-- ============================================================================
-- 7. INVENTORY VALUATION DETAIL
-- ============================================================================

DROP VIEW IF EXISTS inventory_valuation_view;

CREATE VIEW inventory_valuation_view AS
SELECT
    icl.product_id,

    p.name AS product_name,

    icl.warehouse_id,

    w.name AS warehouse_name,

    SUM(icl.qty_remaining) AS available_qty,

    SUM(
        icl.qty_remaining * icl.unit_cost
    ) AS stock_value,

    MIN(icl.unit_cost) AS lowest_cost,

    MAX(icl.unit_cost) AS highest_cost,

    COUNT(icl.id) AS cost_layers

FROM inventory_cost_layers icl

JOIN products p
    ON p.id = icl.product_id

JOIN warehouses w
    ON w.id = icl.warehouse_id

WHERE icl.qty_remaining > 0

GROUP BY
    icl.product_id,
    p.name,
    icl.warehouse_id,
    w.name;


-- ============================================================================
-- 8. INVENTORY KPI
-- ============================================================================

DROP VIEW IF EXISTS inventory_kpi_view;

CREATE VIEW inventory_kpi_view AS
SELECT
    COUNT(DISTINCT product_id) AS total_products,

    COUNT(DISTINCT warehouse_id) AS total_warehouses,

    SUM(available_qty) AS total_stock_qty,

    SUM(stock_value) AS total_inventory_value,

    CASE
        WHEN SUM(available_qty) <> 0
        THEN SUM(stock_value) / SUM(available_qty)
        ELSE 0
    END AS average_unit_value,

    SUM(
        CASE
            WHEN available_qty <= 5
            THEN 1
            ELSE 0
        END
    ) AS low_stock_items

FROM inventory_valuation_view;


-- ============================================================================
-- 9. WAREHOUSE INVENTORY KPI
-- ============================================================================

DROP VIEW IF EXISTS warehouse_inventory_kpi_view;

CREATE VIEW warehouse_inventory_kpi_view AS
SELECT
    warehouse_id,

    warehouse_name,

    SUM(available_qty) AS total_qty,

    SUM(stock_value) AS total_value,

    COUNT(product_id) AS product_count

FROM inventory_valuation_view

GROUP BY
    warehouse_id,
    warehouse_name;


-- ============================================================================
-- 10. INVENTORY STOCK VIEW
-- ============================================================================

DROP VIEW IF EXISTS inventory_stock_view;

CREATE VIEW inventory_stock_view AS
SELECT
    p.id AS product_id,

    p.name AS product_name,

    w.id AS warehouse_id,

    w.name AS warehouse_name,

    COALESCE(ws.available_qty, 0) AS available_qty,

    COALESCE(ws.qty, 0) AS qty,

    p.minimum_stock

FROM products p

CROSS JOIN warehouses w

LEFT JOIN warehouse_stock ws
    ON ws.product_id = p.id
   AND ws.warehouse_id = w.id

WHERE p.is_active = 1;


-- ============================================================================
-- 11. INVENTORY LOSS KPI
-- ============================================================================

DROP VIEW IF EXISTS inventory_loss_kpi_view;

CREATE VIEW inventory_loss_kpi_view AS
SELECT
    reference_type,

    movement_type,

    COUNT(*) AS transactions,

    SUM(ABS(qty)) AS lost_qty,

    SUM(ABS(total_cost)) AS total_loss

FROM stock_movements

WHERE qty < 0

  AND movement_type LIKE 'ADJUSTMENT%'

GROUP BY
    reference_type,
    movement_type;


-- ============================================================================
-- 12. STOCK CARD VIEW
-- ============================================================================

DROP VIEW IF EXISTS stock_card_view;

CREATE VIEW stock_card_view AS
WITH movement_data AS (
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

    FROM stock_movements sm
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

    SUM(md.qty) OVER (
        PARTITION BY
            md.product_id,
            md.warehouse_id

        ORDER BY
            md.created_at,
            md.movement_id

        ROWS BETWEEN UNBOUNDED PRECEDING
        AND CURRENT ROW
    ) AS running_balance

FROM movement_data md

JOIN products p
    ON p.id = md.product_id

JOIN warehouses w
    ON w.id = md.warehouse_id;


-- ============================================================================
-- 13. STOCK ADJUSTMENT AUDIT
-- ============================================================================

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
        sa.qty * sa.unit_cost
    ) AS total_loss,

    sa.reason,

    sa.status,

    sa.requested_by,

    sa.approved_by,

    sa.approved_at,

    sa.created_at

FROM stock_adjustments sa

JOIN products p
    ON p.id = sa.product_id

JOIN warehouses w
    ON w.id = sa.warehouse_id;


-- ============================================================================
-- 14. TRANSFER COST REPORT
-- ============================================================================

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

FROM stock_transfer_costs stc

JOIN stock_transfers st
    ON st.id = stc.transfer_id

JOIN warehouses wf
    ON wf.id = st.from_warehouse_id

JOIN warehouses wt
    ON wt.id = st.to_warehouse_id

JOIN products p
    ON p.id = st.product_id;


-- ============================================================================
-- 15. REFUND COST REPORT
-- ============================================================================

DROP VIEW IF EXISTS refund_cost_report;

CREATE VIEW refund_cost_report AS
SELECT
    reference_id AS refund_id,

    product_id,

    SUM(qty_in) AS refund_qty,

    SUM(
        qty_in * unit_cost
    ) AS refund_cogs

FROM inventory_cost_layers

WHERE reference_type = 'REFUND'

GROUP BY
    reference_id,
    product_id;


-- ============================================================================
-- 16. REFUND DETAIL
-- ============================================================================

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

FROM refund_items ri

LEFT JOIN products p
    ON p.id = ri.product_id

LEFT JOIN sale_items si
    ON si.id = ri.sale_item_id

LEFT JOIN sales s
    ON s.id = si.sale_id;


-- ============================================================================
-- 17. REFUND HEADER
-- ============================================================================

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

    w.name AS warehouse_name

FROM refunds r

LEFT JOIN sales s
    ON s.id = r.sale_id

LEFT JOIN warehouses w
    ON w.id = s.warehouse_id;


-- ============================================================================
-- 18. REFUND KPI
-- ============================================================================

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


-- ============================================================================
-- 19. REFUND REPORT
-- ============================================================================

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

    r.approved_at,

    w.name AS warehouse_name

FROM refunds r

LEFT JOIN sales s
    ON s.id = r.sale_id

LEFT JOIN refund_items ri
    ON ri.refund_id = r.id

LEFT JOIN products p
    ON p.id = ri.product_id

LEFT JOIN warehouses w
    ON w.id = s.warehouse_id;


-- ============================================================================
-- 20. INVENTORY REORDER
-- ============================================================================

DROP VIEW IF EXISTS view_inventory_reorder;

CREATE VIEW view_inventory_reorder AS
SELECT
    w.id AS warehouse_id,

    w.name AS warehouse_name,

    p.id AS product_id,

    p.name AS product_name,

    ws.qty AS current_qty,

    COALESCE(
        p.minimum_stock,
        p.reorder_level,
        10
    ) AS minimum_stock,

    p.supplier_id,

    p.purchase_price,

    CASE
        WHEN ws.qty <= COALESCE(
            p.minimum_stock,
            p.reorder_level,
            10
        )
        THEN 1
        ELSE 0
    END AS need_reorder

FROM warehouse_stock ws

JOIN warehouses w
    ON w.id = ws.warehouse_id

JOIN products p
    ON p.id = ws.product_id

WHERE p.is_active = 1;


-- ============================================================================
-- 21. INVENTORY STATUS
-- ============================================================================

DROP VIEW IF EXISTS view_inventory_status;

CREATE VIEW view_inventory_status AS
SELECT
    w.name AS warehouse_name,

    p.name AS product_name,

    ws.qty,

    COALESCE(
        p.reorder_level,
        p.minimum_stock,
        10
    ) AS reorder_level

FROM warehouse_stock ws

JOIN warehouses w
    ON ws.warehouse_id = w.id

JOIN products p
    ON ws.product_id = p.id;


-- ============================================================================
-- 22. POS PRODUCTS VIEW
-- ============================================================================

DROP VIEW IF EXISTS pos_products_view;

CREATE VIEW pos_products_view AS
SELECT
    p.id,

    p.name,

    p.sku,

    p.barcode,

    p.purchase_price,

    p.selling_price,

    p.owner_selling_price,

    p.owner_price_locked,

    CASE

        WHEN p.owner_price_locked = 1
         AND p.owner_selling_price IS NOT NULL
        THEN p.owner_selling_price

        WHEN p.markup_percent IS NOT NULL
        THEN ROUND(
            p.purchase_price
            +
            (
                p.purchase_price
                * p.markup_percent
                / 100
            ),
            2
        )

        WHEN c.markup_percent IS NOT NULL
        THEN ROUND(
            p.purchase_price
            +
            (
                p.purchase_price
                * c.markup_percent
                / 100
            ),
            2
        )

        WHEN s.value IS NOT NULL
        THEN ROUND(
            p.purchase_price
            +
            (
                p.purchase_price
                * CAST(s.value AS REAL)
                / 100
            ),
            2
        )

        ELSE p.selling_price

    END AS final_selling_price,

    CASE

        WHEN p.owner_price_locked = 1
         AND p.owner_selling_price IS NOT NULL
        THEN 'OWNER'

        WHEN p.markup_percent IS NOT NULL
        THEN 'PRODUCT'

        WHEN c.markup_percent IS NOT NULL
        THEN 'CATEGORY'

        WHEN s.value IS NOT NULL
        THEN 'SYSTEM'

        ELSE 'MANUAL'

    END AS price_source,

    c.id AS category_id,

    c.name AS category,

    ws.warehouse_id,

    COALESCE(ws.qty, 0) AS qty,

    COALESCE(ws.reserved_qty, 0) AS reserved_qty,

    COALESCE(ws.available_qty, 0) AS available_qty,

    p.minimum_stock

FROM products p

LEFT JOIN categories c
    ON c.id = p.category_id

LEFT JOIN warehouse_stock ws
    ON ws.product_id = p.id

LEFT JOIN erp_settings s
    ON s.key = 'DEFAULT_MARKUP_PERCENT';


-- ============================================================================
-- PART 6 COMPLETE
-- ============================================================================

PRAGMA foreign_keys = ON;

-- Verification
SELECT
    name
FROM sqlite_master
WHERE type = 'view'
ORDER BY name;
