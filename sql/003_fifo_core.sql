PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

-- ============================================================
-- ERP SQLITE DATABASE
-- PART 3
-- FIFO COST LAYERS + COST TRANSACTIONS + STOCK MOVEMENTS
-- ============================================================


-- ============================================================
-- 1. INVENTORY COST LAYERS
-- ============================================================

CREATE TABLE IF NOT EXISTS inventory_cost_layers (
    id INTEGER PRIMARY KEY,

    product_id INTEGER NOT NULL,

    warehouse_id INTEGER NOT NULL,

    qty_in INTEGER NOT NULL DEFAULT 0,

    qty_remaining INTEGER NOT NULL DEFAULT 0,

    unit_cost NUMERIC NOT NULL DEFAULT 0,

    reference_type TEXT,

    reference_id INTEGER,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (product_id)
        REFERENCES products(id),

    FOREIGN KEY (warehouse_id)
        REFERENCES warehouses(id)
);


-- ============================================================
-- FIFO INDEX
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_cost_layers_fifo
ON inventory_cost_layers (
    product_id,
    warehouse_id,
    created_at,
    id
);


CREATE INDEX IF NOT EXISTS idx_cost_layers_remaining
ON inventory_cost_layers (
    product_id,
    warehouse_id,
    qty_remaining
);


CREATE INDEX IF NOT EXISTS idx_cost_layers_reference
ON inventory_cost_layers (
    reference_type,
    reference_id
);


-- ============================================================
-- 2. INVENTORY COST TRANSACTIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS inventory_cost_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    sale_id INTEGER NOT NULL,

    sale_item_id INTEGER NOT NULL,

    product_id INTEGER NOT NULL,

    warehouse_id INTEGER NOT NULL,

    cost_layer_id INTEGER NOT NULL,

    qty INTEGER NOT NULL,

    unit_cost NUMERIC NOT NULL,

    total_cost NUMERIC NOT NULL,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (sale_id)
        REFERENCES sales(id),

    FOREIGN KEY (sale_item_id)
        REFERENCES sale_items(id),

    FOREIGN KEY (product_id)
        REFERENCES products(id),

    FOREIGN KEY (warehouse_id)
        REFERENCES warehouses(id),

    FOREIGN KEY (cost_layer_id)
        REFERENCES inventory_cost_layers(id)
);


-- ============================================================
-- COST TRANSACTION INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_cost_transactions_sale
ON inventory_cost_transactions(sale_id);


CREATE INDEX IF NOT EXISTS idx_cost_transactions_sale_item
ON inventory_cost_transactions(sale_item_id);


CREATE INDEX IF NOT EXISTS idx_cost_transactions_product
ON inventory_cost_transactions(product_id);


CREATE INDEX IF NOT EXISTS idx_cost_transactions_warehouse
ON inventory_cost_transactions(warehouse_id);


CREATE INDEX IF NOT EXISTS idx_cost_transactions_layer
ON inventory_cost_transactions(cost_layer_id);


CREATE INDEX IF NOT EXISTS idx_cost_transactions_created
ON inventory_cost_transactions(created_at);


-- ============================================================
-- 3. STOCK MOVEMENTS
-- ============================================================

CREATE TABLE IF NOT EXISTS stock_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    product_id INTEGER NOT NULL,

    warehouse_id INTEGER NOT NULL,

    movement_type TEXT NOT NULL,

    qty NUMERIC NOT NULL,

    reference_type TEXT,

    reference_id INTEGER,

    unit_cost NUMERIC,

    total_cost NUMERIC,

    note TEXT,

    created_by TEXT,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (product_id)
        REFERENCES products(id),

    FOREIGN KEY (warehouse_id)
        REFERENCES warehouses(id)
);


-- ============================================================
-- STOCK MOVEMENT INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_stock_movements_product
ON stock_movements(product_id);


CREATE INDEX IF NOT EXISTS idx_stock_movements_warehouse
ON stock_movements(warehouse_id);


CREATE INDEX IF NOT EXISTS idx_stock_movements_product_warehouse
ON stock_movements(product_id, warehouse_id);


CREATE INDEX IF NOT EXISTS idx_stock_movements_reference
ON stock_movements(reference_type, reference_id);


CREATE INDEX IF NOT EXISTS idx_stock_movements_created
ON stock_movements(created_at);


-- ============================================================
-- 4. FIFO COST LAYER VIEW
-- ============================================================

CREATE VIEW IF NOT EXISTS inventory_fifo_layers_view AS
SELECT
    icl.id AS layer_id,
    icl.product_id,
    p.name AS product_name,
    icl.warehouse_id,
    w.name AS warehouse_name,

    icl.qty_in,
    icl.qty_remaining,

    (icl.qty_in - icl.qty_remaining) AS qty_consumed,

    icl.unit_cost,

    (
        icl.qty_remaining * icl.unit_cost
    ) AS remaining_value,

    icl.reference_type,
    icl.reference_id,
    icl.created_at

FROM inventory_cost_layers icl

JOIN products p
    ON p.id = icl.product_id

JOIN warehouses w
    ON w.id = icl.warehouse_id

WHERE icl.qty_remaining > 0

ORDER BY
    icl.product_id,
    icl.warehouse_id,
    icl.created_at,
    icl.id;


-- ============================================================
-- 5. FIFO INVENTORY VALUATION
-- ============================================================

CREATE VIEW IF NOT EXISTS inventory_fifo_valuation_view AS
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


-- ============================================================
-- 6. STOCK CARD VIEW
-- ============================================================

CREATE VIEW IF NOT EXISTS stock_card_view AS

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
    ) AS running_balance

FROM movement_data md

JOIN products p
    ON p.id = md.product_id

JOIN warehouses w
    ON w.id = md.warehouse_id;


-- ============================================================
-- 7. INVENTORY VALUATION
-- ============================================================

CREATE VIEW IF NOT EXISTS inventory_valuation AS
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


-- ============================================================
-- 8. INVENTORY VALUATION VIEW
-- ============================================================

CREATE VIEW IF NOT EXISTS inventory_valuation_view AS

SELECT

    icl.product_id,

    p.name AS product_name,

    icl.warehouse_id,

    w.name AS warehouse_name,

    SUM(
        icl.qty_remaining
    ) AS available_qty,

    SUM(
        icl.qty_remaining * icl.unit_cost
    ) AS stock_value,

    MIN(
        icl.unit_cost
    ) AS lowest_cost,

    MAX(
        icl.unit_cost
    ) AS highest_cost,

    COUNT(
        icl.id
    ) AS cost_layers

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


-- ============================================================
-- 9. INVENTORY KPI VIEW
-- ============================================================

CREATE VIEW IF NOT EXISTS inventory_kpi_view AS

SELECT

    COUNT(
        DISTINCT product_id
    ) AS total_products,

    COUNT(
        DISTINCT warehouse_id
    ) AS total_warehouses,

    COALESCE(
        SUM(available_qty),
        0
    ) AS total_stock_qty,

    COALESCE(
        SUM(stock_value),
        0
    ) AS total_inventory_value,

    COALESCE(
        AVG(
            stock_value /
            NULLIF(available_qty, 0)
        ),
        0
    ) AS average_unit_value,

    SUM(
        CASE
            WHEN available_qty <= 5
            THEN 1
            ELSE 0
        END
    ) AS low_stock_items

FROM inventory_valuation_view;


COMMIT;


-- ============================================================
-- VERIFICATION
-- ============================================================

SELECT
    name,
    type
FROM sqlite_master
WHERE type IN ('table', 'view')
ORDER BY type, name;
