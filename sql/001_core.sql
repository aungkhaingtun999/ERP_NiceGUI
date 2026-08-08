PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

-- ============================================================
-- ERP SQLITE DATABASE
-- PART 1
-- FOUNDATION + MASTER TABLES
-- ============================================================


-- ============================================================
-- 1. ERP SETTINGS
-- ============================================================

CREATE TABLE IF NOT EXISTS erp_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 2. CATEGORIES
-- ============================================================

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    category_code TEXT UNIQUE,
    is_active INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    markup_percent NUMERIC
);


-- ============================================================
-- 3. BRAND MARKUP
-- ============================================================

CREATE TABLE IF NOT EXISTS brand_markup (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_id INTEGER NOT NULL,
    markup_percent NUMERIC NOT NULL DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 4. CATEGORY MARKUP
-- ============================================================

CREATE TABLE IF NOT EXISTS category_markup (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    markup_percent NUMERIC NOT NULL DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (category_id)
        REFERENCES categories(id)
);


-- ============================================================
-- 5. CATEGORY MARKUP APPROVAL
-- ============================================================

CREATE TABLE IF NOT EXISTS category_markup_approval (
    id INTEGER PRIMARY KEY,
    category_id INTEGER NOT NULL,
    old_markup_percent NUMERIC,
    new_markup_percent NUMERIC NOT NULL,
    requested_by TEXT,
    approved_by TEXT,
    status TEXT DEFAULT 'PENDING',
    request_note TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    approved_at TEXT,

    FOREIGN KEY (category_id)
        REFERENCES categories(id)
);


-- ============================================================
-- 6. CATEGORY MARKUP SETTINGS
-- ============================================================

CREATE TABLE IF NOT EXISTS category_markup_settings (
    id INTEGER PRIMARY KEY,
    category_id INTEGER,
    markup_percent NUMERIC,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'PENDING',
    created_by TEXT,
    approved_by TEXT,
    approved_at TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (category_id)
        REFERENCES categories(id)
);


-- ============================================================
-- 7. CATEGORY PRICING RULES
-- ============================================================

CREATE TABLE IF NOT EXISTS category_pricing_rules (
    id INTEGER PRIMARY KEY,
    category_id INTEGER NOT NULL,
    markup_percent NUMERIC NOT NULL DEFAULT 0,
    auto_update INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (category_id)
        REFERENCES categories(id)
);


-- ============================================================
-- 8. CUSTOMERS
-- ============================================================

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY,
    customer_code TEXT,
    full_name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    address TEXT,
    loyalty_points INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(customer_code)
);


-- ============================================================
-- 9. PRODUCTS
-- ============================================================

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,

    name TEXT NOT NULL,

    price NUMERIC NOT NULL DEFAULT 0,

    stock INTEGER NOT NULL DEFAULT 0,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    barcode TEXT,
    sku TEXT,

    category_id INTEGER,

    purchase_price NUMERIC NOT NULL DEFAULT 0,

    selling_price NUMERIC,

    minimum_stock INTEGER NOT NULL DEFAULT 5,

    unit TEXT NOT NULL DEFAULT 'PCS',

    image_url TEXT,
    notes TEXT,

    is_active INTEGER NOT NULL DEFAULT 1,

    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    short_name TEXT,

    brand_id INTEGER,

    supplier_id INTEGER,

    wholesale_price NUMERIC DEFAULT 0,
    vip_price NUMERIC DEFAULT 0,
    member_price NUMERIC DEFAULT 0,

    tax_rate NUMERIC DEFAULT 5,

    discount_allowed INTEGER DEFAULT 1,

    reorder_level INTEGER DEFAULT 10,

    markup_percent NUMERIC,

    owner_selling_price NUMERIC,

    price_source TEXT DEFAULT 'SYSTEM',

    final_selling_price NUMERIC,

    owner_price_locked INTEGER DEFAULT 0,

    track_batches INTEGER DEFAULT 0,

    track_expiry INTEGER DEFAULT 0,

    shelf_life_days INTEGER,

    FOREIGN KEY (category_id)
        REFERENCES categories(id)
);


-- ============================================================
-- 10. PRODUCT INDEXES
-- ============================================================

CREATE UNIQUE INDEX IF NOT EXISTS idx_products_barcode
ON products(barcode)
WHERE barcode IS NOT NULL;


CREATE UNIQUE INDEX IF NOT EXISTS idx_products_sku
ON products(sku)
WHERE sku IS NOT NULL;


CREATE INDEX IF NOT EXISTS idx_products_category
ON products(category_id);


CREATE INDEX IF NOT EXISTS idx_products_brand
ON products(brand_id);


CREATE INDEX IF NOT EXISTS idx_products_supplier
ON products(supplier_id);


CREATE INDEX IF NOT EXISTS idx_products_active
ON products(is_active);


-- ============================================================
-- 11. AUDIT LOGS
-- ============================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY,

    table_name TEXT NOT NULL,

    operation TEXT NOT NULL,

    record_id INTEGER NOT NULL,

    old_data TEXT,

    new_data TEXT,

    changed_by TEXT DEFAULT 'SYSTEM',

    changed_at TEXT DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- DEFAULT ERP SETTINGS
-- ============================================================

INSERT OR IGNORE INTO erp_settings
    (key, value)
VALUES
    ('currency', 'MMK');


INSERT OR IGNORE INTO erp_settings
    (key, value)
VALUES
    ('DEFAULT_MARKUP_PERCENT', '20');


INSERT OR IGNORE INTO erp_settings
    (key, value)
VALUES
    ('PRICING_METHOD', 'MARKUP');


INSERT OR IGNORE INTO erp_settings
    (key, value)
VALUES
    ('min_stock', '10');


INSERT OR IGNORE INTO erp_settings
    (key, value)
VALUES
    ('default_tax_rate', '5');


INSERT OR IGNORE INTO erp_settings
    (key, value)
VALUES
    ('payment_methods',
     'Cash,Bank Transfer,Mobile Pay,Credit');


INSERT OR IGNORE INTO erp_settings
    (key, value)
VALUES
    ('discount_policy', 'allowed');


INSERT OR IGNORE INTO erp_settings
    (key, value)
VALUES
    ('auto_reorder', 'true');


COMMIT;


-- ============================================================
-- VERIFICATION
-- ============================================================

SELECT
    name AS table_name
FROM sqlite_master
WHERE type = 'table'
ORDER BY name;
