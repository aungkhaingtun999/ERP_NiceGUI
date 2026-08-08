PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;


-- ============================================================
-- ERP SQLITE DATABASE
-- PART 2
-- WAREHOUSE / STOCK / PURCHASE / OPENING STOCK
-- ============================================================


-- ============================================================
-- 1. WAREHOUSES
-- ============================================================

CREATE TABLE IF NOT EXISTS warehouses (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    code TEXT,
    address TEXT,
    phone TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 2. WAREHOUSE STOCK
-- ============================================================

CREATE TABLE IF NOT EXISTS warehouse_stock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    product_id INTEGER NOT NULL,

    warehouse_id INTEGER NOT NULL,

    qty NUMERIC NOT NULL DEFAULT 0,

    reserved_qty NUMERIC NOT NULL DEFAULT 0,

    available_qty NUMERIC
        GENERATED ALWAYS AS
        (qty - reserved_qty) STORED,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(product_id, warehouse_id),

    FOREIGN KEY (product_id)
        REFERENCES products(id),

    FOREIGN KEY (warehouse_id)
        REFERENCES warehouses(id)
);


-- ============================================================
-- WAREHOUSE STOCK INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_warehouse_stock_product
ON warehouse_stock(product_id);


CREATE INDEX IF NOT EXISTS idx_warehouse_stock_warehouse
ON warehouse_stock(warehouse_id);


CREATE INDEX IF NOT EXISTS idx_warehouse_stock_product_warehouse
ON warehouse_stock(product_id, warehouse_id);


-- ============================================================
-- 3. PURCHASES
-- ============================================================

CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY,

    product_id INTEGER NOT NULL,

    qty NUMERIC NOT NULL,

    price NUMERIC NOT NULL,

    total NUMERIC NOT NULL,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    supplier_id INTEGER,

    warehouse_id INTEGER,

    purchase_no TEXT,

    status TEXT DEFAULT 'COMPLETED',

    notes TEXT,

    created_by TEXT,

    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

    tax NUMERIC DEFAULT 0,

    discount NUMERIC DEFAULT 0,

    net_total NUMERIC DEFAULT 0,

    payment_method TEXT DEFAULT 'Cash',

    reference_no TEXT,

    FOREIGN KEY (product_id)
        REFERENCES products(id),

    FOREIGN KEY (warehouse_id)
        REFERENCES warehouses(id)
);


-- ============================================================
-- PURCHASE INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_purchases_product
ON purchases(product_id);


CREATE INDEX IF NOT EXISTS idx_purchases_warehouse
ON purchases(warehouse_id);


CREATE INDEX IF NOT EXISTS idx_purchases_supplier
ON purchases(supplier_id);


CREATE INDEX IF NOT EXISTS idx_purchases_created_at
ON purchases(created_at);


CREATE UNIQUE INDEX IF NOT EXISTS idx_purchases_purchase_no
ON purchases(purchase_no)
WHERE purchase_no IS NOT NULL;


-- ============================================================
-- 4. PURCHASE BATCHES
-- ============================================================

CREATE TABLE IF NOT EXISTS purchase_batches (
    id INTEGER PRIMARY KEY,

    product_id INTEGER NOT NULL,

    warehouse_id INTEGER NOT NULL,

    purchase_id INTEGER,

    qty NUMERIC NOT NULL DEFAULT 0,

    remaining_qty NUMERIC NOT NULL DEFAULT 0,

    cost NUMERIC NOT NULL DEFAULT 0,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    selling_price NUMERIC DEFAULT 0,

    FOREIGN KEY (product_id)
        REFERENCES products(id),

    FOREIGN KEY (warehouse_id)
        REFERENCES warehouses(id),

    FOREIGN KEY (purchase_id)
        REFERENCES purchases(id)
);


-- ============================================================
-- PURCHASE BATCH INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_purchase_batches_product
ON purchase_batches(product_id);


CREATE INDEX IF NOT EXISTS idx_purchase_batches_warehouse
ON purchase_batches(warehouse_id);


CREATE INDEX IF NOT EXISTS idx_purchase_batches_purchase
ON purchase_batches(purchase_id);


CREATE INDEX IF NOT EXISTS idx_purchase_batches_fifo
ON purchase_batches(product_id, warehouse_id, created_at, id);


-- ============================================================
-- 5. INVENTORY BATCHES
-- ============================================================

CREATE TABLE IF NOT EXISTS inventory_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    product_id INTEGER NOT NULL,

    warehouse_id INTEGER NOT NULL,

    batch_no TEXT NOT NULL,

    manufacturing_date TEXT,

    expiry_date TEXT,

    quantity NUMERIC NOT NULL DEFAULT 0,

    unit_cost NUMERIC NOT NULL DEFAULT 0,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (product_id)
        REFERENCES products(id),

    FOREIGN KEY (warehouse_id)
        REFERENCES warehouses(id)
);


-- ============================================================
-- INVENTORY BATCH INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_inventory_batches_product
ON inventory_batches(product_id);


CREATE INDEX IF NOT EXISTS idx_inventory_batches_warehouse
ON inventory_batches(warehouse_id);


CREATE INDEX IF NOT EXISTS idx_inventory_batches_expiry
ON inventory_batches(expiry_date);


CREATE INDEX IF NOT EXISTS idx_inventory_batches_product_warehouse
ON inventory_batches(product_id, warehouse_id);


-- ============================================================
-- 6. OPENING STOCK
-- ============================================================

CREATE TABLE IF NOT EXISTS opening_stock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    warehouse_id INTEGER NOT NULL,

    opening_date TEXT NOT NULL
        DEFAULT (date('now')),

    remarks TEXT,

    created_by TEXT,

    created_at TEXT NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (warehouse_id)
        REFERENCES warehouses(id)
);


-- ============================================================
-- 7. OPENING STOCK ITEMS
-- ============================================================

CREATE TABLE IF NOT EXISTS opening_stock_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    opening_stock_id INTEGER NOT NULL,

    product_id INTEGER NOT NULL,

    warehouse_id INTEGER NOT NULL,

    qty NUMERIC NOT NULL,

    unit_cost NUMERIC NOT NULL,

    total_cost NUMERIC,

    created_at TEXT NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (opening_stock_id)
        REFERENCES opening_stock(id),

    FOREIGN KEY (product_id)
        REFERENCES products(id),

    FOREIGN KEY (warehouse_id)
        REFERENCES warehouses(id)
);


-- ============================================================
-- OPENING STOCK INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_opening_stock_warehouse
ON opening_stock(warehouse_id);


CREATE INDEX IF NOT EXISTS idx_opening_stock_items_header
ON opening_stock_items(opening_stock_id);


CREATE INDEX IF NOT EXISTS idx_opening_stock_items_product
ON opening_stock_items(product_id);


CREATE INDEX IF NOT EXISTS idx_opening_stock_items_warehouse
ON opening_stock_items(warehouse_id);


-- ============================================================
-- 8. INVENTORY TRANSACTIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS inventory_transactions (
    id INTEGER PRIMARY KEY,

    product_id INTEGER NOT NULL,

    warehouse_id INTEGER NOT NULL,

    transaction_type TEXT NOT NULL,

    qty_in NUMERIC DEFAULT 0,

    qty_out NUMERIC DEFAULT 0,

    unit_cost NUMERIC DEFAULT 0,

    reference_type TEXT,

    reference_id INTEGER,

    remarks TEXT,

    created_by TEXT,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (product_id)
        REFERENCES products(id),

    FOREIGN KEY (warehouse_id)
        REFERENCES warehouses(id)
);


-- ============================================================
-- INVENTORY TRANSACTION INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_inventory_transactions_product
ON inventory_transactions(product_id);


CREATE INDEX IF NOT EXISTS idx_inventory_transactions_warehouse
ON inventory_transactions(warehouse_id);


CREATE INDEX IF NOT EXISTS idx_inventory_transactions_reference
ON inventory_transactions(reference_type, reference_id);


CREATE INDEX IF NOT EXISTS idx_inventory_transactions_created
ON inventory_transactions(created_at);


-- ============================================================
-- 9. INVENTORY LOGS
-- ============================================================

CREATE TABLE IF NOT EXISTS inventory_logs (
    id INTEGER PRIMARY KEY,

    product_id INTEGER NOT NULL,

    reference_type TEXT NOT NULL,

    reference_id INTEGER,

    quantity INTEGER NOT NULL,

    balance_after INTEGER,

    remarks TEXT,

    created_by TEXT,

    created_at TEXT NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    warehouse_id INTEGER,

    transaction_id TEXT,

    FOREIGN KEY (product_id)
        REFERENCES products(id),

    FOREIGN KEY (warehouse_id)
        REFERENCES warehouses(id)
);


-- ============================================================
-- INVENTORY LOG INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_inventory_logs_product
ON inventory_logs(product_id);


CREATE INDEX IF NOT EXISTS idx_inventory_logs_warehouse
ON inventory_logs(warehouse_id);


CREATE INDEX IF NOT EXISTS idx_inventory_logs_reference
ON inventory_logs(reference_type, reference_id);


CREATE INDEX IF NOT EXISTS idx_inventory_logs_created
ON inventory_logs(created_at);


COMMIT;


-- ============================================================
-- VERIFICATION
-- ============================================================

SELECT
    name AS table_name
FROM sqlite_master
WHERE type = 'table'
ORDER BY name;
