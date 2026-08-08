create_table_sql
"--- TABLE: audit_logs ---
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id bigint NOT NULL,
    table_name text NOT NULL,
    operation text NOT NULL,
    record_id bigint NOT NULL,
    old_data jsonb,
    new_data jsonb,
    changed_by text,
    changed_at timestamp with time zone
);
"
"--- TABLE: backup_inventory_cost_layers_20260808 ---
CREATE TABLE IF NOT EXISTS public.backup_inventory_cost_layers_20260808 (
    id bigint,
    product_id bigint,
    warehouse_id bigint,
    qty_in integer,
    qty_remaining integer,
    unit_cost numeric,
    reference_type text,
    reference_id bigint,
    created_at timestamp with time zone
);
"
"--- TABLE: backup_products_20260808 ---
CREATE TABLE IF NOT EXISTS public.backup_products_20260808 (
    id bigint,
    name text,
    price numeric,
    stock integer,
    created_at timestamp with time zone,
    barcode text,
    sku text,
    category_id bigint,
    purchase_price numeric,
    selling_price numeric,
    minimum_stock integer,
    unit text,
    image_url text,
    notes text,
    is_active boolean,
    updated_at timestamp with time zone,
    short_name text,
    brand_id bigint,
    supplier_id bigint,
    wholesale_price numeric,
    vip_price numeric,
    member_price numeric,
    tax_rate numeric,
    discount_allowed boolean,
    reorder_level integer,
    markup_percent numeric,
    owner_selling_price numeric,
    price_source character varying(50),
    final_selling_price numeric,
    owner_price_locked boolean,
    track_batches boolean,
    track_expiry boolean,
    shelf_life_days integer
);
"
"--- TABLE: backup_stock_adjustments_20260808 ---
CREATE TABLE IF NOT EXISTS public.backup_stock_adjustments_20260808 (
    id bigint,
    product_id bigint,
    warehouse_id bigint,
    adjustment_type text,
    qty numeric,
    unit_cost numeric,
    reason text,
    status text,
    requested_by uuid,
    approved_by uuid,
    approved_at timestamp with time zone,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);
"
"--- TABLE: backup_stock_movements_20260808 ---
CREATE TABLE IF NOT EXISTS public.backup_stock_movements_20260808 (
    id bigint,
    product_id bigint,
    warehouse_id bigint,
    movement_type text,
    qty numeric,
    reference_type text,
    reference_id bigint,
    unit_cost numeric,
    total_cost numeric,
    note text,
    created_by uuid,
    created_at timestamp with time zone
);
"
"--- TABLE: backup_warehouse_stock_20260808 ---
CREATE TABLE IF NOT EXISTS public.backup_warehouse_stock_20260808 (
    id bigint,
    warehouse_id bigint,
    product_id bigint,
    qty integer,
    reserved_qty integer,
    available_qty integer,
    minimum_stock integer,
    maximum_stock integer,
    reorder_level integer,
    location text,
    batch_no text,
    expiry_date date,
    updated_at timestamp with time zone,
    created_at timestamp with time zone
);
"
"--- TABLE: branch_profit_report ---
CREATE TABLE IF NOT EXISTS public.branch_profit_report (
    warehouse_id bigint,
    branch_name text,
    product_id bigint,
    product_name text,
    sold_qty bigint,
    revenue numeric,
    cogs numeric,
    gross_profit numeric,
    profit_margin_percent numeric
);
"
"--- TABLE: brand_markup ---
CREATE TABLE IF NOT EXISTS public.brand_markup (
    id bigint NOT NULL,
    brand_id bigint NOT NULL,
    markup_percent numeric NOT NULL,
    is_active boolean,
    created_at timestamp with time zone
);
"
"--- TABLE: categories ---
CREATE TABLE IF NOT EXISTS public.categories (
    id bigint NOT NULL,
    name text NOT NULL,
    description text,
    created_at timestamp with time zone,
    category_code text,
    is_active boolean NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    markup_percent numeric
);
"
"--- TABLE: category_markup ---
CREATE TABLE IF NOT EXISTS public.category_markup (
    id bigint NOT NULL,
    category_id bigint NOT NULL,
    markup_percent numeric NOT NULL,
    is_active boolean,
    created_at timestamp with time zone
);
"
"--- TABLE: category_markup_approval ---
CREATE TABLE IF NOT EXISTS public.category_markup_approval (
    id bigint NOT NULL,
    category_id bigint NOT NULL,
    old_markup_percent numeric,
    new_markup_percent numeric NOT NULL,
    requested_by uuid,
    approved_by uuid,
    status text,
    request_note text,
    created_at timestamp with time zone,
    approved_at timestamp with time zone
);
"
"--- TABLE: category_markup_settings ---
CREATE TABLE IF NOT EXISTS public.category_markup_settings (
    id bigint NOT NULL,
    category_id bigint,
    markup_percent numeric,
    created_at timestamp with time zone,
    status text,
    created_by uuid,
    approved_by uuid,
    approved_at timestamp with time zone,
    updated_at timestamp with time zone
);
"
"--- TABLE: category_pricing_rules ---
CREATE TABLE IF NOT EXISTS public.category_pricing_rules (
    id bigint NOT NULL,
    category_id bigint NOT NULL,
    markup_percent numeric NOT NULL,
    auto_update boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);
"
"--- TABLE: customers ---
CREATE TABLE IF NOT EXISTS public.customers (
    id bigint NOT NULL,
    customer_code text,
    full_name text NOT NULL,
    phone text,
    email text,
    address text,
    loyalty_points integer NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);
"
"--- TABLE: daily_profit_report ---
CREATE TABLE IF NOT EXISTS public.daily_profit_report (
    sale_date date,
    revenue numeric,
    cogs numeric,
    gross_profit numeric
);
"
"--- TABLE: daily_profit_report_v1 ---
CREATE TABLE IF NOT EXISTS public.daily_profit_report_v1 (
    sale_date date,
    gross_sales numeric,
    refund_amount numeric,
    net_sales numeric,
    sale_cogs numeric,
    refund_cogs numeric,
    net_cogs numeric,
    gross_profit numeric,
    profit_margin_percent numeric
);
"
"--- TABLE: erp_settings ---
CREATE TABLE IF NOT EXISTS public.erp_settings (
    id bigint NOT NULL,
    key text NOT NULL,
    value text,
    created_at timestamp without time zone
);
"
"--- TABLE: function_backup_purchase_receive ---
CREATE TABLE IF NOT EXISTS public.function_backup_purchase_receive (
    backup_time timestamp with time zone,
    proname name,
    function_definition text
);
"
"--- TABLE: inventory_batches ---
CREATE TABLE IF NOT EXISTS public.inventory_batches (
    id bigint NOT NULL,
    product_id bigint NOT NULL,
    warehouse_id bigint NOT NULL,
    batch_no text NOT NULL,
    manufacturing_date date,
    expiry_date date,
    quantity numeric NOT NULL,
    unit_cost numeric NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);
"
"--- TABLE: inventory_cost_layers ---
CREATE TABLE IF NOT EXISTS public.inventory_cost_layers (
    id bigint NOT NULL,
    product_id bigint NOT NULL,
    warehouse_id bigint NOT NULL,
    qty_in integer NOT NULL,
    qty_remaining integer NOT NULL,
    unit_cost numeric NOT NULL,
    reference_type text,
    reference_id bigint,
    created_at timestamp with time zone
);
"
"--- TABLE: inventory_cost_layers_backup ---
CREATE TABLE IF NOT EXISTS public.inventory_cost_layers_backup (
    id bigint,
    product_id bigint,
    warehouse_id bigint,
    qty_in integer,
    qty_remaining integer,
    unit_cost numeric,
    reference_type text,
    reference_id bigint,
    created_at timestamp with time zone
);
"
"--- TABLE: inventory_cost_layers_backup_20260806 ---
CREATE TABLE IF NOT EXISTS public.inventory_cost_layers_backup_20260806 (
    id bigint,
    product_id bigint,
    warehouse_id bigint,
    qty_in integer,
    qty_remaining integer,
    unit_cost numeric,
    reference_type text,
    reference_id bigint,
    created_at timestamp with time zone
);
"
"--- TABLE: inventory_cost_layers_backup_before_opening ---
CREATE TABLE IF NOT EXISTS public.inventory_cost_layers_backup_before_opening (
    id bigint,
    product_id bigint,
    warehouse_id bigint,
    qty_in integer,
    qty_remaining integer,
    unit_cost numeric,
    reference_type text,
    reference_id bigint,
    created_at timestamp with time zone
);
"
"--- TABLE: inventory_cost_layers_backup_fifo_fix ---
CREATE TABLE IF NOT EXISTS public.inventory_cost_layers_backup_fifo_fix (
    id bigint,
    product_id bigint,
    warehouse_id bigint,
    qty_in integer,
    qty_remaining integer,
    unit_cost numeric,
    reference_type text,
    reference_id bigint,
    created_at timestamp with time zone
);
"
"--- TABLE: inventory_cost_layers_backup_final ---
CREATE TABLE IF NOT EXISTS public.inventory_cost_layers_backup_final (
    id bigint,
    product_id bigint,
    warehouse_id bigint,
    qty_in integer,
    qty_remaining integer,
    unit_cost numeric,
    reference_type text,
    reference_id bigint,
    created_at timestamp with time zone
);
"
"--- TABLE: inventory_cost_transactions ---
CREATE TABLE IF NOT EXISTS public.inventory_cost_transactions (
    id bigint NOT NULL,
    sale_id bigint NOT NULL,
    sale_item_id bigint NOT NULL,
    product_id bigint NOT NULL,
    warehouse_id bigint NOT NULL,
    cost_layer_id bigint NOT NULL,
    qty integer NOT NULL,
    unit_cost numeric NOT NULL,
    total_cost numeric NOT NULL,
    created_at timestamp with time zone
);
"
"--- TABLE: inventory_cost_transactions_backup ---
CREATE TABLE IF NOT EXISTS public.inventory_cost_transactions_backup (
    id bigint,
    sale_id bigint,
    sale_item_id bigint,
    product_id bigint,
    warehouse_id bigint,
    cost_layer_id bigint,
    qty integer,
    unit_cost numeric,
    total_cost numeric,
    created_at timestamp with time zone
);
"
"--- TABLE: inventory_cost_transactions_backup_before_fifo_rebuild ---
CREATE TABLE IF NOT EXISTS public.inventory_cost_transactions_backup_before_fifo_rebuild (
    id bigint,
    sale_id bigint,
    sale_item_id bigint,
    product_id bigint,
    warehouse_id bigint,
    cost_layer_id bigint,
    qty integer,
    unit_cost numeric,
    total_cost numeric,
    created_at timestamp with time zone
);
"
"--- TABLE: inventory_cost_transactions_backup_final ---
CREATE TABLE IF NOT EXISTS public.inventory_cost_transactions_backup_final (
    id bigint,
    sale_id bigint,
    sale_item_id bigint,
    product_id bigint,
    warehouse_id bigint,
    cost_layer_id bigint,
    qty integer,
    unit_cost numeric,
    total_cost numeric,
    created_at timestamp with time zone
);
"
"--- TABLE: inventory_kpi_view ---
CREATE TABLE IF NOT EXISTS public.inventory_kpi_view (
    total_products bigint,
    total_warehouses bigint,
    total_stock_qty numeric,
    total_inventory_value numeric,
    average_unit_value numeric,
    low_stock_items bigint
);
"
"--- TABLE: inventory_logs ---
CREATE TABLE IF NOT EXISTS public.inventory_logs (
    id bigint NOT NULL,
    product_id bigint NOT NULL,
    reference_type text NOT NULL,
    reference_id bigint,
    quantity integer NOT NULL,
    balance_after integer,
    remarks text,
    created_by uuid,
    created_at timestamp with time zone NOT NULL,
    warehouse_id bigint,
    transaction_id text
);
"
"--- TABLE: inventory_loss_kpi_view ---
CREATE TABLE IF NOT EXISTS public.inventory_loss_kpi_view (
    reference_type text,
    movement_type text,
    transactions bigint,
    lost_qty numeric,
    total_loss numeric
);
"
"--- TABLE: inventory_stock_view ---
CREATE TABLE IF NOT EXISTS public.inventory_stock_view (
    product_id bigint,
    product_name text,
    warehouse_id bigint,
    warehouse_name text,
    available_qty bigint,
    qty bigint,
    minimum_stock integer
);
"
"--- TABLE: inventory_transactions ---
CREATE TABLE IF NOT EXISTS public.inventory_transactions (
    id bigint NOT NULL,
    product_id bigint NOT NULL,
    warehouse_id bigint NOT NULL,
    transaction_type text NOT NULL,
    qty_in numeric,
    qty_out numeric,
    unit_cost numeric,
    reference_type text,
    reference_id bigint,
    remarks text,
    created_by uuid,
    created_at timestamp with time zone
);
"
"--- TABLE: inventory_valuation ---
CREATE TABLE IF NOT EXISTS public.inventory_valuation (
    product_id bigint,
    warehouse_id bigint,
    stock_qty bigint,
    stock_value numeric
);
"
"--- TABLE: inventory_valuation_view ---
CREATE TABLE IF NOT EXISTS public.inventory_valuation_view (
    product_id bigint,
    product_name text,
    warehouse_id bigint,
    warehouse_name text,
    available_qty bigint,
    stock_value numeric,
    lowest_cost numeric,
    highest_cost numeric,
    cost_layers bigint
);
"
"--- TABLE: opening_stock ---
CREATE TABLE IF NOT EXISTS public.opening_stock (
    id bigint NOT NULL,
    warehouse_id bigint NOT NULL,
    opening_date date NOT NULL,
    remarks text,
    created_by uuid,
    created_at timestamp with time zone NOT NULL
);
"
"--- TABLE: opening_stock_items ---
CREATE TABLE IF NOT EXISTS public.opening_stock_items (
    id bigint NOT NULL,
    opening_stock_id bigint NOT NULL,
    product_id bigint NOT NULL,
    warehouse_id bigint NOT NULL,
    qty numeric NOT NULL,
    unit_cost numeric NOT NULL,
    total_cost numeric,
    created_at timestamp with time zone NOT NULL
);
"
"--- TABLE: payment_accounts ---
CREATE TABLE IF NOT EXISTS public.payment_accounts (
    id bigint NOT NULL,
    company_id uuid,
    branch_id bigint,
    provider text NOT NULL,
    account_name text NOT NULL,
    account_no text NOT NULL,
    enabled boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    qr_payload_template text,
    qr_prefix text,
    qr_mode text
);
"
"--- TABLE: payment_transactions ---
CREATE TABLE IF NOT EXISTS public.payment_transactions (
    id uuid NOT NULL,
    sale_id bigint,
    payment_method text NOT NULL,
    provider text,
    transaction_id text,
    amount numeric NOT NULL,
    status text,
    verified_by uuid,
    verified_at timestamp with time zone,
    note text,
    created_at timestamp with time zone,
    cashier_id uuid,
    rejected_reason text,
    updated_at timestamp with time zone
);
"
"--- TABLE: permissions ---
CREATE TABLE IF NOT EXISTS public.permissions (
    id bigint NOT NULL,
    name text NOT NULL,
    permission_key text,
    module text,
    description text
);
"
"--- TABLE: pos_products_view ---
CREATE TABLE IF NOT EXISTS public.pos_products_view (
    id bigint,
    name text,
    sku text,
    barcode text,
    purchase_price numeric,
    selling_price numeric,
    owner_selling_price numeric,
    owner_price_locked boolean,
    final_selling_price numeric,
    price_source text,
    category_id bigint,
    category text,
    warehouse_id bigint,
    qty integer,
    reserved_qty integer,
    available_qty integer,
    minimum_stock integer
);
"
"--- TABLE: pos_products_view_backup ---
CREATE TABLE IF NOT EXISTS public.pos_products_view_backup (
    id bigint,
    name text,
    sku text,
    barcode text,
    purchase_price numeric,
    selling_price numeric,
    owner_selling_price numeric,
    final_selling_price numeric,
    price_source text,
    category_id bigint,
    category text,
    warehouse_id bigint,
    qty integer,
    reserved_qty integer,
    available_qty integer,
    minimum_stock integer
);
"
"--- TABLE: price_import_queue ---
CREATE TABLE IF NOT EXISTS public.price_import_queue (
    id bigint NOT NULL,
    product_id bigint,
    barcode text,
    sku text,
    name text,
    old_selling_price numeric,
    purchase_price numeric,
    markup_percent numeric,
    new_selling_price numeric,
    price_source text,
    status text,
    reason text,
    created_by uuid,
    created_at timestamp with time zone,
    approved_by uuid,
    approved_at timestamp with time zone
);
"
"--- TABLE: product_markup ---
CREATE TABLE IF NOT EXISTS public.product_markup (
    id bigint NOT NULL,
    product_id bigint NOT NULL,
    markup_percent numeric,
    fixed_price numeric,
    is_active boolean,
    created_at timestamp with time zone
);
"
"--- TABLE: product_profit_report ---
CREATE TABLE IF NOT EXISTS public.product_profit_report (
    product_id bigint,
    name text,
    sold_qty bigint,
    refund_qty bigint,
    gross_sales numeric,
    refund_amount numeric,
    net_sales numeric,
    cogs numeric,
    gross_profit numeric,
    profit_margin_percent numeric,
    final_selling_price numeric,
    price_source character varying(50),
    owner_selling_price numeric,
    owner_price_locked boolean,
    markup_percent numeric,
    category_markup numeric
);
"
"--- TABLE: product_profit_report_final ---
CREATE TABLE IF NOT EXISTS public.product_profit_report_final (
    product_id bigint,
    name text,
    sold_qty bigint,
    revenue numeric,
    cogs numeric,
    gross_profit numeric,
    final_selling_price numeric,
    price_source character varying(50),
    owner_selling_price numeric,
    markup_percent numeric,
    category_markup numeric
);
"
"--- TABLE: product_profit_report_v2 ---
CREATE TABLE IF NOT EXISTS public.product_profit_report_v2 (
    product_id bigint,
    sold_qty bigint,
    revenue numeric,
    cogs numeric
);
"
"--- TABLE: product_profit_report_v3 ---
CREATE TABLE IF NOT EXISTS public.product_profit_report_v3 (
    product_id bigint,
    sold_qty bigint,
    refund_qty bigint,
    gross_sales numeric,
    refund_amount numeric,
    net_sales numeric,
    cogs numeric,
    gross_profit numeric,
    profit_margin_percent numeric
);
"
"--- TABLE: product_profit_report_v4 ---
CREATE TABLE IF NOT EXISTS public.product_profit_report_v4 (
    product_id bigint,
    sold_qty bigint,
    refund_qty bigint,
    gross_sales numeric,
    refund_amount numeric,
    net_sales numeric,
    sale_cogs numeric,
    refund_cogs numeric,
    net_cogs numeric,
    gross_profit numeric,
    profit_margin_percent numeric
);
"
"--- TABLE: product_profit_report_v5 ---
CREATE TABLE IF NOT EXISTS public.product_profit_report_v5 (
    product_id bigint,
    name text,
    sold_qty bigint,
    refund_qty bigint,
    gross_sales numeric,
    refund_amount numeric,
    net_sales numeric,
    cogs numeric,
    gross_profit numeric,
    profit_margin_percent numeric,
    final_selling_price numeric,
    price_source character varying(50),
    owner_selling_price numeric,
    owner_price_locked boolean,
    markup_percent numeric,
    category_markup numeric
);
"
"--- TABLE: products ---
CREATE TABLE IF NOT EXISTS public.products (
    id bigint NOT NULL,
    name text NOT NULL,
    price numeric NOT NULL,
    stock integer NOT NULL,
    created_at timestamp with time zone,
    barcode text,
    sku text,
    category_id bigint,
    purchase_price numeric NOT NULL,
    selling_price numeric,
    minimum_stock integer NOT NULL,
    unit text NOT NULL,
    image_url text,
    notes text,
    is_active boolean NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    short_name text,
    brand_id bigint,
    supplier_id bigint,
    wholesale_price numeric,
    vip_price numeric,
    member_price numeric,
    tax_rate numeric,
    discount_allowed boolean,
    reorder_level integer,
    markup_percent numeric,
    owner_selling_price numeric,
    price_source character varying(50),
    final_selling_price numeric,
    owner_price_locked boolean,
    track_batches boolean,
    track_expiry boolean,
    shelf_life_days integer
);
"
"--- TABLE: products_stock_backup ---
CREATE TABLE IF NOT EXISTS public.products_stock_backup (
    id bigint,
    name text,
    price numeric,
    stock integer,
    created_at timestamp with time zone,
    barcode text,
    sku text,
    category_id bigint,
    purchase_price numeric,
    selling_price numeric,
    minimum_stock integer,
    unit text,
    image_url text,
    notes text,
    is_active boolean,
    updated_at timestamp with time zone,
    short_name text,
    brand_id bigint,
    supplier_id bigint,
    wholesale_price numeric,
    vip_price numeric,
    member_price numeric,
    tax_rate numeric,
    discount_allowed boolean,
    reorder_level integer
);
"
"--- TABLE: purchase_batches ---
CREATE TABLE IF NOT EXISTS public.purchase_batches (
    id bigint NOT NULL,
    product_id bigint NOT NULL,
    warehouse_id bigint NOT NULL,
    purchase_id bigint,
    qty numeric NOT NULL,
    remaining_qty numeric NOT NULL,
    cost numeric NOT NULL,
    created_at timestamp with time zone,
    selling_price numeric
);
"
"--- TABLE: purchases ---
CREATE TABLE IF NOT EXISTS public.purchases (
    id bigint NOT NULL,
    product_id bigint NOT NULL,
    qty numeric NOT NULL,
    price numeric NOT NULL,
    total numeric NOT NULL,
    created_at timestamp with time zone,
    supplier_id bigint,
    warehouse_id bigint,
    purchase_no text,
    status text,
    notes text,
    created_by uuid,
    updated_at timestamp with time zone,
    tax numeric,
    discount numeric,
    net_total numeric,
    payment_method text,
    reference_no text
);
"
"--- TABLE: receipts ---
CREATE TABLE IF NOT EXISTS public.receipts (
    id bigint NOT NULL,
    sale_id bigint,
    receipt_no text,
    total numeric,
    paid_amount numeric,
    change_amount numeric,
    created_at timestamp without time zone
);
"
"--- TABLE: refund_cost_report ---
CREATE TABLE IF NOT EXISTS public.refund_cost_report (
    refund_id bigint,
    product_id bigint,
    refund_qty bigint,
    refund_cogs numeric
);
"
"--- TABLE: refund_detail_view ---
CREATE TABLE IF NOT EXISTS public.refund_detail_view (
    refund_id bigint,
    sale_item_id bigint,
    product_id bigint,
    product_name text,
    quantity integer,
    unit_price numeric,
    item_total numeric,
    sale_id bigint,
    invoice_no text
);
"
"--- TABLE: refund_header_view ---
CREATE TABLE IF NOT EXISTS public.refund_header_view (
    refund_id bigint,
    sale_id bigint,
    invoice_no text,
    refund_date timestamp with time zone,
    refund_amount numeric,
    status text,
    reason text,
    cashier_name text,
    processed_by text,
    approved_at timestamp with time zone,
    warehouse_name text
);
"
"--- TABLE: refund_items ---
CREATE TABLE IF NOT EXISTS public.refund_items (
    id bigint NOT NULL,
    refund_id bigint NOT NULL,
    sale_item_id bigint,
    product_id bigint NOT NULL,
    quantity integer NOT NULL,
    unit_price numeric NOT NULL,
    total numeric NOT NULL
);
"
"--- TABLE: refund_kpi_view ---
CREATE TABLE IF NOT EXISTS public.refund_kpi_view (
    total_refunds bigint,
    pending bigint,
    completed bigint,
    rejected bigint,
    total_amount numeric
);
"
"--- TABLE: refund_report_view ---
CREATE TABLE IF NOT EXISTS public.refund_report_view (
    refund_id bigint,
    sale_id bigint,
    invoice_no text,
    refund_date timestamp with time zone,
    refund_amount numeric,
    status text,
    reason text,
    product_id bigint,
    product_name text,
    quantity integer,
    unit_price numeric,
    item_total numeric,
    cashier_name text,
    processed_by text,
    approved_at timestamp with time zone,
    warehouse_name text
);
"
"--- TABLE: refunds ---
CREATE TABLE IF NOT EXISTS public.refunds (
    id bigint NOT NULL,
    sale_id bigint,
    refund_date timestamp with time zone,
    reason text,
    refund_amount numeric,
    cashier_id uuid,
    status text,
    approved_by uuid,
    approved_at timestamp with time zone,
    rejected_by uuid,
    rejected_reason text
);
"
"--- TABLE: role_permissions ---
CREATE TABLE IF NOT EXISTS public.role_permissions (
    role_id bigint NOT NULL,
    permission_id bigint NOT NULL
);
"
"--- TABLE: roles ---
CREATE TABLE IF NOT EXISTS public.roles (
    id bigint NOT NULL,
    name text NOT NULL,
    description text,
    created_at timestamp with time zone NOT NULL
);
"
"--- TABLE: sale_items ---
CREATE TABLE IF NOT EXISTS public.sale_items (
    id bigint NOT NULL,
    sale_id bigint NOT NULL,
    product_id bigint NOT NULL,
    quantity integer NOT NULL,
    unit_price numeric NOT NULL,
    discount numeric,
    total numeric NOT NULL,
    product_name text
);
"
"--- TABLE: sales ---
CREATE TABLE IF NOT EXISTS public.sales (
    id bigint NOT NULL,
    invoice_no text NOT NULL,
    customer_id bigint,
    cashier_id uuid NOT NULL,
    subtotal numeric NOT NULL,
    discount numeric,
    tax numeric,
    total numeric NOT NULL,
    paid_amount numeric NOT NULL,
    change_amount numeric,
    payment_method text NOT NULL,
    sale_status text NOT NULL,
    created_at timestamp with time zone,
    status text,
    total_amount numeric,
    warehouse_id bigint,
    counter_id integer,
    tax_rate numeric
);
"
"--- TABLE: settings ---
CREATE TABLE IF NOT EXISTS public.settings (
    id bigint NOT NULL,
    key text NOT NULL,
    value text,
    description text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);
"
"--- TABLE: settings_change_requests ---
CREATE TABLE IF NOT EXISTS public.settings_change_requests (
    id bigint NOT NULL,
    setting_key text NOT NULL,
    old_value text,
    new_value text,
    reason text,
    status text,
    requested_by uuid,
    approved_by uuid,
    rejected_by uuid,
    rejected_reason text,
    created_at timestamp with time zone,
    approved_at timestamp with time zone,
    updated_at timestamp with time zone
);
"
"--- TABLE: stock_adjustment_audit_view ---
CREATE TABLE IF NOT EXISTS public.stock_adjustment_audit_view (
    adjustment_id bigint,
    product_id bigint,
    product_name text,
    warehouse_id bigint,
    warehouse_name text,
    adjustment_type text,
    qty numeric,
    unit_cost numeric,
    total_loss numeric,
    reason text,
    status text,
    requested_by uuid,
    approved_by uuid,
    approved_by_name text,
    approved_at timestamp with time zone,
    created_at timestamp with time zone
);
"
"--- TABLE: stock_adjustments ---
CREATE TABLE IF NOT EXISTS public.stock_adjustments (
    id bigint NOT NULL,
    product_id bigint NOT NULL,
    warehouse_id bigint NOT NULL,
    adjustment_type text NOT NULL,
    qty numeric NOT NULL,
    unit_cost numeric NOT NULL,
    reason text,
    status text,
    requested_by uuid,
    approved_by uuid,
    approved_at timestamp with time zone,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);
"
"--- TABLE: stock_card_view ---
CREATE TABLE IF NOT EXISTS public.stock_card_view (
    movement_id bigint,
    product_id bigint,
    product_name text,
    warehouse_id bigint,
    warehouse_name text,
    movement_type text,
    reference_type text,
    reference_id bigint,
    qty_in numeric,
    qty_out numeric,
    unit_cost numeric,
    total_cost numeric,
    note text,
    created_at timestamp with time zone,
    running_balance numeric
);
"
"--- TABLE: stock_count_items ---
CREATE TABLE IF NOT EXISTS public.stock_count_items (
    id bigint NOT NULL,
    count_id bigint NOT NULL,
    product_id bigint NOT NULL,
    system_qty numeric NOT NULL,
    counted_qty numeric NOT NULL,
    variance_qty numeric,
    unit_cost numeric NOT NULL,
    variance_cost numeric,
    note text,
    created_at timestamp with time zone
);
"
"--- TABLE: stock_counts ---
CREATE TABLE IF NOT EXISTS public.stock_counts (
    id bigint NOT NULL,
    warehouse_id bigint NOT NULL,
    count_no text,
    count_date timestamp with time zone,
    status text,
    counted_by uuid,
    approved_by uuid,
    approved_at timestamp with time zone,
    note text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);
"
"--- TABLE: stock_movements ---
CREATE TABLE IF NOT EXISTS public.stock_movements (
    id bigint NOT NULL,
    product_id bigint NOT NULL,
    warehouse_id bigint NOT NULL,
    movement_type text NOT NULL,
    qty numeric NOT NULL,
    reference_type text,
    reference_id bigint,
    unit_cost numeric,
    total_cost numeric,
    note text,
    created_by uuid,
    created_at timestamp with time zone
);
"
"--- TABLE: stock_movements_backup_20260808 ---
CREATE TABLE IF NOT EXISTS public.stock_movements_backup_20260808 (
    id bigint,
    product_id bigint,
    warehouse_id bigint,
    movement_type text,
    qty numeric,
    reference_type text,
    reference_id bigint,
    unit_cost numeric,
    total_cost numeric,
    note text,
    created_by uuid,
    created_at timestamp with time zone
);
"
"--- TABLE: stock_transfer_costs ---
CREATE TABLE IF NOT EXISTS public.stock_transfer_costs (
    id bigint NOT NULL,
    transfer_id bigint NOT NULL,
    product_id bigint NOT NULL,
    from_warehouse_id bigint NOT NULL,
    to_warehouse_id bigint NOT NULL,
    cost_layer_id bigint,
    qty numeric NOT NULL,
    unit_cost numeric NOT NULL,
    total_cost numeric,
    created_at timestamp with time zone
);
"
"--- TABLE: stock_transfers ---
CREATE TABLE IF NOT EXISTS public.stock_transfers (
    id bigint NOT NULL,
    transfer_no text NOT NULL,
    from_warehouse_id bigint NOT NULL,
    to_warehouse_id bigint NOT NULL,
    product_id bigint NOT NULL,
    qty integer NOT NULL,
    status text NOT NULL,
    remarks text,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);
"
"--- TABLE: suppliers ---
CREATE TABLE IF NOT EXISTS public.suppliers (
    id bigint NOT NULL,
    supplier_code text,
    company_name text NOT NULL,
    contact_name text,
    phone text,
    email text,
    address text,
    is_active boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);
"
"--- TABLE: system_settings ---
CREATE TABLE IF NOT EXISTS public.system_settings (
    id bigint NOT NULL,
    setting_key text NOT NULL,
    setting_value jsonb NOT NULL,
    description text,
    status text,
    created_by uuid,
    approved_by uuid,
    approved_at timestamp with time zone,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);
"
"--- TABLE: transfer_cost_report ---
CREATE TABLE IF NOT EXISTS public.transfer_cost_report (
    transfer_id bigint,
    transfer_no text,
    transfer_date timestamp with time zone,
    from_branch text,
    to_branch text,
    product_name text,
    qty numeric,
    unit_cost numeric,
    total_cost numeric
);
"
"--- TABLE: user_activity_logs ---
CREATE TABLE IF NOT EXISTS public.user_activity_logs (
    id bigint NOT NULL,
    user_id uuid,
    action text NOT NULL,
    description text,
    created_at timestamp without time zone
);
"
"--- TABLE: user_roles ---
CREATE TABLE IF NOT EXISTS public.user_roles (
    user_id uuid NOT NULL,
    role_id bigint NOT NULL
);
"
"--- TABLE: users ---
CREATE TABLE IF NOT EXISTS public.users (
    id uuid NOT NULL,
    username text NOT NULL,
    full_name text NOT NULL,
    password_hash text NOT NULL,
    role_id bigint NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    failed_attempts integer,
    locked_until timestamp with time zone,
    employee_code text
);
"
"--- TABLE: v_sales_profit ---
CREATE TABLE IF NOT EXISTS public.v_sales_profit (
    sale_id bigint,
    invoice_no text,
    created_at timestamp with time zone,
    revenue numeric,
    cogs numeric,
    gross_profit numeric,
    margin_percent numeric
);
"
"--- TABLE: view_daily_sales_report ---
CREATE TABLE IF NOT EXISTS public.view_daily_sales_report (
    sale_day timestamp with time zone,
    total_transactions bigint,
    total_revenue numeric
);
"
"--- TABLE: view_inventory_reorder ---
CREATE TABLE IF NOT EXISTS public.view_inventory_reorder (
    warehouse_id bigint,
    warehouse_name text,
    product_id bigint,
    product_name text,
    current_qty integer,
    minimum_stock integer,
    supplier_id bigint,
    purchase_price numeric,
    need_reorder boolean
);
"
"--- TABLE: view_inventory_status ---
CREATE TABLE IF NOT EXISTS public.view_inventory_status (
    warehouse_name text,
    product_name text,
    qty integer,
    reorder_level integer
);
"
"--- TABLE: view_refund_report ---
CREATE TABLE IF NOT EXISTS public.view_refund_report (
    refund_id bigint,
    sale_id bigint,
    invoice_no text,
    refund_date timestamp with time zone,
    reason text,
    refund_amount numeric,
    product_id bigint,
    product_name text,
    quantity integer,
    unit_price numeric,
    item_total numeric,
    cashier_name text,
    warehouse_name text
);
"
"--- TABLE: warehouse_inventory_kpi_view ---
CREATE TABLE IF NOT EXISTS public.warehouse_inventory_kpi_view (
    warehouse_id bigint,
    warehouse_name text,
    total_qty numeric,
    total_value numeric,
    product_count bigint
);
"
"--- TABLE: warehouse_stock ---
CREATE TABLE IF NOT EXISTS public.warehouse_stock (
    id bigint NOT NULL,
    warehouse_id bigint NOT NULL,
    product_id bigint NOT NULL,
    qty integer,
    reserved_qty integer,
    available_qty integer,
    minimum_stock integer,
    maximum_stock integer,
    reorder_level integer,
    location text,
    batch_no text,
    expiry_date date,
    updated_at timestamp with time zone,
    created_at timestamp with time zone
);
"
"--- TABLE: warehouses ---
CREATE TABLE IF NOT EXISTS public.warehouses (
    id bigint NOT NULL,
    code text NOT NULL,
    name text NOT NULL,
    branch text,
    address text,
    phone text,
    manager_name text,
    is_active boolean,
    created_at timestamp with time zone
);
"
