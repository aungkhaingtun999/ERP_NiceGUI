-- ============================================================
-- ERP ENTERPRISE SQLITE BACKUP
-- PART 5
-- POS / PRICING / PRODUCT PROFIT / BRANCH PROFIT
-- ============================================================

PRAGMA foreign_keys = ON;


-- ============================================================
-- 1. POS PRODUCTS VIEW
-- ============================================================

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

        -- OWNER PRICE
        WHEN p.owner_price_locked = 1
             AND p.owner_selling_price IS NOT NULL
        THEN p.owner_selling_price

        -- PRODUCT MARKUP
        WHEN p.markup_percent IS NOT NULL
        THEN ROUND(
            p.purchase_price
            +
            (
                p.purchase_price
                * p.markup_percent
                / 100.0
            ),
            2
        )

        -- CATEGORY MARKUP
        WHEN c.markup_percent IS NOT NULL
        THEN ROUND(
            p.purchase_price
            +
            (
                p.purchase_price
                * c.markup_percent
                / 100.0
            ),
            2
        )

        -- SYSTEM MARKUP
        WHEN s.value IS NOT NULL
        THEN ROUND(
            p.purchase_price
            +
            (
                p.purchase_price
                * CAST(s.value AS REAL)
                / 100.0
            ),
            2
        )

        -- MANUAL PRICE
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

    COALESCE(ws.qty, 0)
        AS qty,

    COALESCE(ws.reserved_qty, 0)
        AS reserved_qty,

    COALESCE(ws.available_qty, 0)
        AS available_qty,

    p.minimum_stock

FROM products AS p

LEFT JOIN categories AS c
    ON c.id = p.category_id

LEFT JOIN warehouse_stock AS ws
    ON ws.product_id = p.id

LEFT JOIN erp_settings AS s
    ON s.key = 'DEFAULT_MARKUP_PERCENT';


-- ============================================================
-- 2. PRODUCT PROFIT REPORT
-- ============================================================

DROP VIEW IF EXISTS product_profit_report;

CREATE VIEW product_profit_report AS

WITH sales AS
(
    SELECT

        si.product_id,

        SUM(si.quantity)
            AS sold_qty,

        SUM(si.total)
            AS gross_sales

    FROM sale_items AS si

    GROUP BY si.product_id
),

refunds AS
(
    SELECT

        ri.product_id,

        SUM(ri.quantity)
            AS refund_qty,

        SUM(ri.total)
            AS refund_amount

    FROM refund_items AS ri

    GROUP BY ri.product_id
),

costs AS
(
    SELECT

        ict.product_id,

        SUM(ict.qty)
            AS cogs_qty,

        SUM(ict.total_cost)
            AS cogs

    FROM inventory_cost_transactions AS ict

    GROUP BY ict.product_id
)

SELECT

    s.product_id,

    p.name,

    s.sold_qty,

    COALESCE(
        r.refund_qty,
        0
    ) AS refund_qty,

    s.gross_sales,

    COALESCE(
        r.refund_amount,
        0
    ) AS refund_amount,

    (
        s.gross_sales
        -
        COALESCE(r.refund_amount, 0)
    ) AS net_sales,

    COALESCE(
        c.cogs,
        0
    ) AS cogs,

    (
        (
            s.gross_sales
            -
            COALESCE(r.refund_amount, 0)
        )
        -
        COALESCE(c.cogs, 0)
    ) AS gross_profit,

    CASE

        WHEN
            (
                s.gross_sales
                -
                COALESCE(r.refund_amount, 0)
            ) = 0
        THEN 0

        ELSE ROUND(

            (
                (
                    (
                        s.gross_sales
                        -
                        COALESCE(r.refund_amount, 0)
                    )
                    -
                    COALESCE(c.cogs, 0)
                )
                /
                (
                    s.gross_sales
                    -
                    COALESCE(r.refund_amount, 0)
                )
            )
            * 100.0,

            2
        )

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
             AND cat.markup_percent IS NOT NULL
        THEN cat.markup_percent

        ELSE NULL

    END AS category_markup

FROM sales AS s

JOIN products AS p
    ON p.id = s.product_id

LEFT JOIN categories AS cat
    ON cat.id = p.category_id

LEFT JOIN refunds AS r
    ON r.product_id = s.product_id

LEFT JOIN costs AS c
    ON c.product_id = s.product_id;


-- ============================================================
-- 3. PRODUCT PROFIT REPORT FINAL
-- ============================================================

DROP VIEW IF EXISTS product_profit_report_final;

CREATE VIEW product_profit_report_final AS

SELECT

    si.product_id,

    p.name,

    SUM(si.quantity)
        AS sold_qty,

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

    p.final_selling_price,
    p.price_source,
    p.owner_selling_price,
    p.markup_percent,

    c.markup_percent
        AS category_markup

FROM sale_items AS si

JOIN products AS p
    ON p.id = si.product_id

LEFT JOIN categories AS c
    ON c.id = p.category_id

LEFT JOIN inventory_cost_transactions AS ict
    ON ict.sale_item_id = si.id

GROUP BY

    si.product_id,
    p.name,
    p.final_selling_price,
    p.price_source,
    p.owner_selling_price,
    p.markup_percent,
    c.markup_percent;


-- ============================================================
-- 4. PRODUCT PROFIT REPORT V2
-- ============================================================

DROP VIEW IF EXISTS product_profit_report_v2;

CREATE VIEW product_profit_report_v2 AS

WITH sales_data AS
(
    SELECT

        si.product_id,

        SUM(si.quantity)
            AS sold_qty,

        SUM(si.total)
            AS sales_amount

    FROM sale_items AS si

    GROUP BY si.product_id
),

cogs_data AS
(
    SELECT

        ict.product_id,

        SUM(ict.total_cost)
            AS total_cogs

    FROM inventory_cost_transactions AS ict

    WHERE ict.sale_id <> 999

    GROUP BY ict.product_id
),

refund_data AS
(
    SELECT

        ri.product_id,

        SUM(ri.total)
            AS refund_amount,

        SUM(
            CAST(ri.quantity AS REAL)
            *
            CAST(ict.unit_cost AS REAL)
        ) AS refund_cost

    FROM refund_items AS ri

    JOIN inventory_cost_transactions AS ict
        ON ict.sale_item_id = ri.sale_item_id

    GROUP BY ri.product_id
)

SELECT

    s.product_id,

    s.sold_qty,

    (
        s.sales_amount
        -
        COALESCE(r.refund_amount, 0)
    ) AS revenue,

    (
        COALESCE(c.total_cogs, 0)
        -
        COALESCE(r.refund_cost, 0)
    ) AS cogs

FROM sales_data AS s

LEFT JOIN cogs_data AS c
    ON c.product_id = s.product_id

LEFT JOIN refund_data AS r
    ON r.product_id = s.product_id;


-- ============================================================
-- 5. PRODUCT PROFIT REPORT V3
-- ============================================================

DROP VIEW IF EXISTS product_profit_report_v3;

CREATE VIEW product_profit_report_v3 AS

WITH sales AS
(
    SELECT

        si.product_id,

        SUM(si.quantity)
            AS sold_qty,

        SUM(si.total)
            AS gross_sales

    FROM sale_items AS si

    GROUP BY si.product_id
),

refunds AS
(
    SELECT

        ri.product_id,

        SUM(ri.quantity)
            AS refund_qty,

        SUM(ri.total)
            AS refund_amount

    FROM refund_items AS ri

    GROUP BY ri.product_id
),

costs AS
(
    SELECT

        ict.product_id,

        SUM(ict.qty)
            AS cogs_qty,

        SUM(ict.total_cost)
            AS cogs

    FROM inventory_cost_transactions AS ict

    GROUP BY ict.product_id
)

SELECT

    s.product_id,

    s.sold_qty,

    COALESCE(
        r.refund_qty,
        0
    ) AS refund_qty,

    s.gross_sales,

    COALESCE(
        r.refund_amount,
        0
    ) AS refund_amount,

    (
        s.gross_sales
        -
        COALESCE(r.refund_amount, 0)
    ) AS net_sales,

    COALESCE(
        c.cogs,
        0
    ) AS cogs,

    (
        (
            s.gross_sales
            -
            COALESCE(r.refund_amount, 0)
        )
        -
        COALESCE(c.cogs, 0)
    ) AS gross_profit,

    CASE

        WHEN
            (
                s.gross_sales
                -
                COALESCE(r.refund_amount, 0)
            ) = 0
        THEN 0

        ELSE ROUND(

            (
                (
                    (
                        s.gross_sales
                        -
                        COALESCE(r.refund_amount, 0)
                    )
                    -
                    COALESCE(c.cogs, 0)
                )
                /
                (
                    s.gross_sales
                    -
                    COALESCE(r.refund_amount, 0)
                )
            )
            * 100.0,

            2
        )

    END AS profit_margin_percent

FROM sales AS s

LEFT JOIN refunds AS r
    ON r.product_id = s.product_id

LEFT JOIN costs AS c
    ON c.product_id = s.product_id;


-- ============================================================
-- 6. PRODUCT PROFIT REPORT V4
-- ============================================================

DROP VIEW IF EXISTS product_profit_report_v4;

CREATE VIEW product_profit_report_v4 AS

WITH sales AS
(
    SELECT

        si.product_id,

        SUM(si.quantity)
            AS sold_qty,

        SUM(si.total)
            AS gross_sales

    FROM sale_items AS si

    GROUP BY si.product_id
),

refunds AS
(
    SELECT

        ri.product_id,

        SUM(ri.quantity)
            AS refund_qty,

        SUM(ri.total)
            AS refund_amount

    FROM refund_items AS ri

    GROUP BY ri.product_id
),

sale_cost AS
(
    SELECT

        ict.product_id,

        SUM(ict.total_cost)
            AS sale_cogs

    FROM inventory_cost_transactions AS ict

    GROUP BY ict.product_id
),

refund_cost AS
(
    SELECT

        product_id,

        SUM(refund_cogs)
            AS refund_cogs

    FROM refund_cost_report

    GROUP BY product_id
)

SELECT

    s.product_id,

    s.sold_qty,

    COALESCE(
        r.refund_qty,
        0
    ) AS refund_qty,

    s.gross_sales,

    COALESCE(
        r.refund_amount,
        0
    ) AS refund_amount,

    (
        s.gross_sales
        -
        COALESCE(r.refund_amount, 0)
    ) AS net_sales,

    COALESCE(
        sc.sale_cogs,
        0
    ) AS sale_cogs,

    COALESCE(
        rc.refund_cogs,
        0
    ) AS refund_cogs,

    (
        COALESCE(sc.sale_cogs, 0)
        -
        COALESCE(rc.refund_cogs, 0)
    ) AS net_cogs,

    (
        (
            s.gross_sales
            -
            COALESCE(r.refund_amount, 0)
        )
        -
        (
            COALESCE(sc.sale_cogs, 0)
            -
            COALESCE(rc.refund_cogs, 0)
        )
    ) AS gross_profit,

    CASE

        WHEN
            (
                s.gross_sales
                -
                COALESCE(r.refund_amount, 0)
            ) = 0
        THEN 0

        ELSE ROUND(

            (
                (
                    (
                        s.gross_sales
                        -
                        COALESCE(r.refund_amount, 0)
                    )
                    -
                    (
                        COALESCE(sc.sale_cogs, 0)
                        -
                        COALESCE(rc.refund_cogs, 0)
                    )
                )
                /
                (
                    s.gross_sales
                    -
                    COALESCE(r.refund_amount, 0)
                )
            )
            * 100.0,

            2
        )

    END AS profit_margin_percent

FROM sales AS s

LEFT JOIN refunds AS r
    ON r.product_id = s.product_id

LEFT JOIN sale_cost AS sc
    ON sc.product_id = s.product_id

LEFT JOIN refund_cost AS rc
    ON rc.product_id = s.product_id;


-- ============================================================
-- 7. PRODUCT PROFIT REPORT V5
-- ============================================================

DROP VIEW IF EXISTS product_profit_report_v5;

CREATE VIEW product_profit_report_v5 AS

WITH sales AS
(
    SELECT

        si.product_id,

        SUM(si.quantity)
            AS sold_qty,

        SUM(si.total)
            AS gross_sales

    FROM sale_items AS si

    GROUP BY si.product_id
),

refunds AS
(
    SELECT

        ri.product_id,

        SUM(ri.quantity)
            AS refund_qty,

        SUM(ri.total)
            AS refund_amount

    FROM refund_items AS ri

    GROUP BY ri.product_id
),

costs AS
(
    SELECT

        ict.product_id,

        SUM(ict.qty)
            AS cogs_qty,

        SUM(ict.total_cost)
            AS cogs

    FROM inventory_cost_transactions AS ict

    GROUP BY ict.product_id
)

SELECT

    s.product_id,

    p.name,

    s.sold_qty,

    COALESCE(
        r.refund_qty,
        0
    ) AS refund_qty,

    s.gross_sales,

    COALESCE(
        r.refund_amount,
        0
    ) AS refund_amount,

    (
        s.gross_sales
        -
        COALESCE(r.refund_amount, 0)
    ) AS net_sales,

    COALESCE(
        c.cogs,
        0
    ) AS cogs,

    (
        (
            s.gross_sales
            -
            COALESCE(r.refund_amount, 0)
        )
        -
        COALESCE(c.cogs, 0)
    ) AS gross_profit,

    CASE

        WHEN
            (
                s.gross_sales
                -
                COALESCE(r.refund_amount, 0)
            ) = 0
        THEN 0

        ELSE ROUND(

            (
                (
                    (
                        s.gross_sales
                        -
                        COALESCE(r.refund_amount, 0)
                    )
                    -
                    COALESCE(c.cogs, 0)
                )
                /
                (
                    s.gross_sales
                    -
                    COALESCE(r.refund_amount, 0)
                )
            )
            * 100.0,

            2
        )

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
             AND cat.markup_percent IS NOT NULL
        THEN cat.markup_percent

        ELSE NULL

    END AS category_markup

FROM sales AS s

JOIN products AS p
    ON p.id = s.product_id

LEFT JOIN categories AS cat
    ON cat.id = p.category_id

LEFT JOIN refunds AS r
    ON r.product_id = s.product_id

LEFT JOIN costs AS c
    ON c.product_id = s.product_id;


-- ============================================================
-- 8. BRANCH PROFIT REPORT
-- ============================================================

DROP VIEW IF EXISTS branch_profit_report;

CREATE VIEW branch_profit_report AS

SELECT

    s.warehouse_id,

    w.name AS branch_name,

    ict.product_id,

    p.name AS product_name,

    SUM(ict.qty)
        AS sold_qty,

    SUM(si.total)
        AS revenue,

    SUM(ict.total_cost)
        AS cogs,

    (
        SUM(si.total)
        -
        SUM(ict.total_cost)
    ) AS gross_profit,

    CASE

        WHEN SUM(si.total) = 0
        THEN 0

        ELSE ROUND(

            (
                (
                    SUM(si.total)
                    -
                    SUM(ict.total_cost)
                )
                /
                SUM(si.total)
            )
            * 100.0,

            2
        )

    END AS profit_margin_percent

FROM inventory_cost_transactions AS ict

JOIN sale_items AS si
    ON si.id = ict.sale_item_id

JOIN sales AS s
    ON s.id = ict.sale_id

JOIN warehouses AS w
    ON w.id = s.warehouse_id

JOIN products AS p
    ON p.id = ict.product_id

GROUP BY

    s.warehouse_id,
    w.name,
    ict.product_id,
    p.name;


-- ============================================================
-- 9. DAILY PROFIT REPORT V1
-- ============================================================

DROP VIEW IF EXISTS daily_profit_report_v1;

CREATE VIEW daily_profit_report_v1 AS

WITH sales_data AS
(
    SELECT

        DATE(s.created_at)
            AS sale_date,

        SUM(si.total)
            AS gross_sales

    FROM sales AS s

    JOIN sale_items AS si
        ON si.sale_id = s.id

    GROUP BY DATE(s.created_at)
),

refunds_data AS
(
    SELECT

        DATE(r.refund_date)
            AS sale_date,

        SUM(r.refund_amount)
            AS refund_amount

    FROM refunds AS r

    GROUP BY DATE(r.refund_date)
),

sale_cost AS
(
    SELECT

        DATE(ict.created_at)
            AS sale_date,

        SUM(ict.total_cost)
            AS sale_cogs

    FROM inventory_cost_transactions AS ict

    GROUP BY DATE(ict.created_at)
),

refund_cost AS
(
    SELECT

        DATE(icl.created_at)
            AS sale_date,

        SUM(
            CAST(icl.qty_in AS REAL)
            *
            CAST(icl.unit_cost AS REAL)
        ) AS refund_cogs

    FROM inventory_cost_layers AS icl

    WHERE icl.reference_type = 'REFUND'

    GROUP BY DATE(icl.created_at)
),

all_dates AS
(
    SELECT sale_date
    FROM sales_data

    UNION

    SELECT sale_date
    FROM refunds_data

    UNION

    SELECT sale_date
    FROM sale_cost

    UNION

    SELECT sale_date
    FROM refund_cost
)

SELECT

    d.sale_date,

    COALESCE(
        s.gross_sales,
        0
    ) AS gross_sales,

    COALESCE(
        r.refund_amount,
        0
    ) AS refund_amount,

    (
        COALESCE(s.gross_sales, 0)
        -
        COALESCE(r.refund_amount, 0)
    ) AS net_sales,

    COALESCE(
        sc.sale_cogs,
        0
    ) AS sale_cogs,

    COALESCE(
        rc.refund_cogs,
        0
    ) AS refund_cogs,

    (
        COALESCE(sc.sale_cogs, 0)
        -
        COALESCE(rc.refund_cogs, 0)
    ) AS net_cogs,

    (
        (
            COALESCE(s.gross_sales, 0)
            -
            COALESCE(r.refund_amount, 0)
        )
        -
        (
            COALESCE(sc.sale_cogs, 0)
            -
            COALESCE(rc.refund_cogs, 0)
        )
    ) AS gross_profit,

    CASE

        WHEN
            (
                COALESCE(s.gross_sales, 0)
                -
                COALESCE(r.refund_amount, 0)
            ) <= 0
        THEN 0

        ELSE ROUND(

            (
                (
                    (
                        COALESCE(s.gross_sales, 0)
                        -
                        COALESCE(r.refund_amount, 0)
                    )
                    -
                    (
                        COALESCE(sc.sale_cogs, 0)
                        -
                        COALESCE(rc.refund_cogs, 0)
                    )
                )
                /
                (
                    COALESCE(s.gross_sales, 0)
                    -
                    COALESCE(r.refund_amount, 0)
                )
            )
            * 100.0,

            2
        )

    END AS profit_margin_percent

FROM all_dates AS d

LEFT JOIN sales_data AS s
    ON s.sale_date = d.sale_date

LEFT JOIN refunds_data AS r
    ON r.sale_date = d.sale_date

LEFT JOIN sale_cost AS sc
    ON sc.sale_date = d.sale_date

LEFT JOIN refund_cost AS rc
    ON rc.sale_date = d.sale_date;


-- ============================================================
-- END PART 5
-- ============================================================
