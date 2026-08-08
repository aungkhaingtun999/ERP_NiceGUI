-- --- CONSTRAINTS & RULES BACKUP ---

-- Audit Logs & Brands
ALTER TABLE public.audit_logs ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);
ALTER TABLE public.brand_markup ADD CONSTRAINT brand_markup_pkey PRIMARY KEY (id);

-- Categories
ALTER TABLE public.categories ADD CONSTRAINT categories_category_code_key UNIQUE (category_code);
ALTER TABLE public.categories ADD CONSTRAINT categories_name_key UNIQUE (name);
ALTER TABLE public.categories ADD CONSTRAINT categories_pkey PRIMARY KEY (id);

-- Category Markups & Settings
ALTER TABLE public.category_markup_approval ADD CONSTRAINT category_markup_approval_pkey PRIMARY KEY (id);
ALTER TABLE public.category_markup ADD CONSTRAINT category_markup_pkey PRIMARY KEY (id);
ALTER TABLE public.category_markup_settings ADD CONSTRAINT category_markup_settings_category_id_unique UNIQUE (category_id);
ALTER TABLE public.category_markup_settings ADD CONSTRAINT category_markup_settings_pkey PRIMARY KEY (id);
ALTER TABLE public.category_pricing_rules ADD CONSTRAINT category_pricing_rules_category_id_fkey FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE;
ALTER TABLE public.category_pricing_rules ADD CONSTRAINT category_pricing_rules_category_id_key UNIQUE (category_id);
ALTER TABLE public.category_pricing_rules ADD CONSTRAINT category_pricing_rules_pkey PRIMARY KEY (id);

-- Stock Adjustments & Movements Check Constraints
ALTER TABLE public.stock_adjustments ADD CONSTRAINT chk_stock_adjustment_status CHECK ((status = ANY (ARRAY['PENDING'::text, 'APPROVED'::text, 'APPLIED'::text, 'CANCELLED'::text])));
ALTER TABLE public.stock_movements ADD CONSTRAINT chk_stock_movement_direction CHECK ((((movement_type = ANY (ARRAY['PURCHASE_IN'::text, 'ADJUSTMENT_IN'::text, 'TRANSFER_IN'::text, 'REFUND_IN'::text])) AND (qty > (0)::numeric)) OR ((movement_type = ANY (ARRAY['SALE_OUT'::text, 'ADJUSTMENT_OUT'::text, 'TRANSFER_OUT'::text, 'DAMAGE_OUT'::text])) AND (qty > (0)::numeric))));
ALTER TABLE public.stock_movements ADD CONSTRAINT chk_stock_movement_qty_positive CHECK ((qty >= (0)::numeric));

-- Customers & ERP Settings
ALTER TABLE public.customers ADD CONSTRAINT customers_customer_code_key UNIQUE (customer_code);
ALTER TABLE public.customers ADD CONSTRAINT customers_pkey PRIMARY KEY (id);
ALTER TABLE public.erp_settings ADD CONSTRAINT erp_settings_key_key UNIQUE (key);
ALTER TABLE public.erp_settings ADD CONSTRAINT erp_settings_pkey PRIMARY KEY (id);

-- Inventory Cost Layers & Transactions Foreign Keys
ALTER TABLE public.inventory_cost_layers ADD CONSTRAINT fk_cost_layer_product FOREIGN KEY (product_id) REFERENCES products(id);
ALTER TABLE public.inventory_cost_layers ADD CONSTRAINT fk_cost_layer_warehouse FOREIGN KEY (warehouse_id) REFERENCES warehouses(id);
ALTER TABLE public.inventory_cost_transactions ADD CONSTRAINT fk_cost_tx_layer FOREIGN KEY (cost_layer_id) REFERENCES inventory_cost_layers(id);
ALTER TABLE public.inventory_cost_transactions ADD CONSTRAINT fk_cost_tx_product FOREIGN KEY (product_id) REFERENCES products(id);
ALTER TABLE public.inventory_cost_transactions ADD CONSTRAINT fk_cost_tx_warehouse FOREIGN KEY (warehouse_id) REFERENCES warehouses(id);
ALTER TABLE public.inventory_cost_layers ADD CONSTRAINT inventory_cost_layers_pkey PRIMARY KEY (id);
ALTER TABLE public.inventory_cost_transactions ADD CONSTRAINT inventory_cost_transactions_pkey PRIMARY KEY (id);

-- Inventory Batches
ALTER TABLE public.inventory_batches ADD CONSTRAINT inventory_batches_date_check CHECK (((manufacturing_date IS NULL) OR (expiry_date IS NULL) OR (manufacturing_date <= expiry_date)));
ALTER TABLE public.inventory_batches ADD CONSTRAINT inventory_batches_pkey PRIMARY KEY (id);
ALTER TABLE public.inventory_batches ADD CONSTRAINT inventory_batches_product_id_fkey FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE;
ALTER TABLE public.inventory_batches ADD CONSTRAINT inventory_batches_product_id_warehouse_id_batch_no_key UNIQUE (product_id, warehouse_id, batch_no);
ALTER TABLE public.inventory_batches ADD CONSTRAINT inventory_batches_qty_nonnegative CHECK ((quantity >= (0)::numeric));
ALTER TABLE public.inventory_batches ADD CONSTRAINT inventory_batches_warehouse_id_fkey FOREIGN KEY (warehouse_id) REFERENCES warehouses(id) ON DELETE CASCADE;

-- Inventory Logs & Transactions
ALTER TABLE public.inventory_logs ADD CONSTRAINT inventory_logs_created_by_fkey FOREIGN KEY (created_by) REFERENCES users(id);
ALTER TABLE public.inventory_logs ADD CONSTRAINT inventory_logs_pkey PRIMARY KEY (id);
ALTER TABLE public.inventory_logs ADD CONSTRAINT inventory_logs_product_id_fkey FOREIGN KEY (product_id) REFERENCES products(id);
ALTER TABLE public.inventory_logs ADD CONSTRAINT inventory_logs_reference_type_check CHECK ((reference_type = ANY (ARRAY['PURCHASE'::text, 'SALE'::text, 'REFUND'::text, 'ADJUSTMENT'::text, 'OPENING'::text])));
ALTER TABLE public.inventory_logs ADD CONSTRAINT inventory_logs_warehouse_id_fkey FOREIGN KEY (warehouse_id) REFERENCES warehouses(id);
ALTER TABLE public.inventory_transactions ADD CONSTRAINT inventory_transactions_pkey PRIMARY KEY (id);
ALTER TABLE public.inventory_transactions ADD CONSTRAINT inventory_transactions_type_check CHECK ((transaction_type = ANY (ARRAY['PURCHASE'::text, 'SALE'::text, 'RETURN'::text, 'TRANSFER'::text, 'ADJUSTMENT'::text])));

-- Opening Stock
ALTER TABLE public.opening_stock_items ADD CONSTRAINT opening_stock_items_opening_stock_id_fkey FOREIGN KEY (opening_stock_id) REFERENCES opening_stock(id) ON DELETE CASCADE;
ALTER TABLE public.opening_stock_items ADD CONSTRAINT opening_stock_items_pkey PRIMARY KEY (id);
ALTER TABLE public.opening_stock_items ADD CONSTRAINT opening_stock_items_product_id_fkey FOREIGN KEY (product_id) REFERENCES products(id);
ALTER TABLE public.opening_stock_items ADD CONSTRAINT opening_stock_items_qty_check CHECK ((qty > (0)::numeric));
ALTER TABLE public.opening_stock_items ADD CONSTRAINT opening_stock_items_unit_cost_check CHECK ((unit_cost >= (0)::numeric));
ALTER TABLE public.opening_stock_items ADD CONSTRAINT opening_stock_items_warehouse_id_fkey FOREIGN KEY (warehouse_id) REFERENCES warehouses(id);
ALTER TABLE public.opening_stock ADD CONSTRAINT opening_stock_pkey PRIMARY KEY (id);

-- Payments & Permissions
ALTER TABLE public.payment_accounts ADD CONSTRAINT payment_accounts_pkey PRIMARY KEY (id);
ALTER TABLE public.payment_transactions ADD CONSTRAINT payment_transactions_pkey PRIMARY KEY (id);
ALTER TABLE public.payment_transactions ADD CONSTRAINT payment_transactions_sale_id_fkey FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE;
ALTER TABLE public.permissions ADD CONSTRAINT permissions_name_key UNIQUE (name);
ALTER TABLE public.permissions ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);

-- Price Imports & Product Markups
ALTER TABLE public.price_import_queue ADD CONSTRAINT price_import_queue_pkey PRIMARY KEY (id);
ALTER TABLE public.price_import_queue ADD CONSTRAINT price_import_queue_product_id_fkey FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE;
ALTER TABLE public.product_markup ADD CONSTRAINT product_markup_pkey PRIMARY KEY (id);
ALTER TABLE public.product_markup ADD CONSTRAINT product_markup_product_id_key UNIQUE (product_id);

-- Products
ALTER TABLE public.products ADD CONSTRAINT products_barcode_key UNIQUE (barcode);
ALTER TABLE public.products ADD CONSTRAINT products_category_id_fkey FOREIGN KEY (category_id) REFERENCES categories(id);
ALTER TABLE public.products ADD CONSTRAINT products_pkey PRIMARY KEY (id);
ALTER TABLE public.products ADD CONSTRAINT products_sku_key UNIQUE (sku);

-- Purchases
ALTER TABLE public.purchase_batches ADD CONSTRAINT purchase_batches_pkey PRIMARY KEY (id);
ALTER TABLE public.purchase_batches ADD CONSTRAINT purchase_batches_product_id_fkey FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE;
ALTER TABLE public.purchase_batches ADD CONSTRAINT purchase_batches_purchase_id_fkey FOREIGN KEY (purchase_id) REFERENCES purchases(id) ON DELETE SET NULL;
ALTER TABLE public.purchase_batches ADD CONSTRAINT purchase_batches_warehouse_id_fkey FOREIGN KEY (warehouse_id) REFERENCES warehouses(id) ON DELETE CASCADE;
ALTER TABLE public.purchases ADD CONSTRAINT purchases_pkey PRIMARY KEY (id);
ALTER TABLE public.purchases ADD CONSTRAINT purchases_product_id_fkey FOREIGN KEY (product_id) REFERENCES products(id);
ALTER TABLE public.purchases ADD CONSTRAINT purchases_purchase_no_key UNIQUE (purchase_no);
ALTER TABLE public.purchases ADD CONSTRAINT purchases_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES suppliers(id);
ALTER TABLE public.purchases ADD CONSTRAINT purchases_warehouse_id_fkey FOREIGN KEY (warehouse_id) REFERENCES warehouses(id);

-- Receipts & Refunds
ALTER TABLE public.receipts ADD CONSTRAINT receipts_pkey PRIMARY KEY (id);
ALTER TABLE public.refund_items ADD CONSTRAINT refund_items_pkey PRIMARY KEY (id);
ALTER TABLE public.refund_items ADD CONSTRAINT refund_items_product_id_fkey FOREIGN KEY (product_id) REFERENCES products(id);
ALTER TABLE public.refund_items ADD CONSTRAINT refund_items_quantity_check CHECK ((quantity > 0));
ALTER TABLE public.refund_items ADD CONSTRAINT refund_items_sale_item_id_fkey FOREIGN KEY (sale_item_id) REFERENCES sale_items(id);
ALTER TABLE public.refunds ADD CONSTRAINT refunds_pkey PRIMARY KEY (id);
ALTER TABLE public.refunds ADD CONSTRAINT refunds_sale_id_fkey FOREIGN KEY (sale_id) REFERENCES sales(id);

-- Roles & Permissions Mappings
ALTER TABLE public.role_permissions ADD CONSTRAINT role_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE;
ALTER TABLE public.role_permissions ADD CONSTRAINT role_permissions_pkey PRIMARY KEY (role_id, permission_id);
ALTER TABLE public.role_permissions ADD CONSTRAINT role_permissions_role_id_fkey FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE;
ALTER TABLE public.roles ADD CONSTRAINT roles_name_key UNIQUE (name);
ALTER TABLE public.roles ADD CONSTRAINT roles_pkey PRIMARY KEY (id);

-- Sales & Sale Items
ALTER TABLE public.sale_items ADD CONSTRAINT sale_items_pkey PRIMARY KEY (id);
ALTER TABLE public.sale_items ADD CONSTRAINT sale_items_product_id_fkey FOREIGN KEY (product_id) REFERENCES products(id);
ALTER TABLE public.sale_items ADD CONSTRAINT sale_items_sale_id_fkey FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE;
ALTER TABLE public.sales ADD CONSTRAINT sales_cashier_id_fkey FOREIGN KEY (cashier_id) REFERENCES users(id);
ALTER TABLE public.sales ADD CONSTRAINT sales_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES customers(id);
ALTER TABLE public.sales ADD CONSTRAINT sales_invoice_no_key UNIQUE (invoice_no);
ALTER TABLE public.sales ADD CONSTRAINT sales_pkey PRIMARY KEY (id);
ALTER TABLE public.sales ADD CONSTRAINT sales_warehouse_id_fkey FOREIGN KEY (warehouse_id) REFERENCES warehouses(id);

-- Settings & Change Requests
ALTER TABLE public.settings_change_requests ADD CONSTRAINT settings_change_requests_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES users(id);
ALTER TABLE public.settings_change_requests ADD CONSTRAINT settings_change_requests_pkey PRIMARY KEY (id);
ALTER TABLE public.settings_change_requests ADD CONSTRAINT settings_change_requests_rejected_by_fkey FOREIGN KEY (rejected_by) REFERENCES users(id);
ALTER TABLE public.settings_change_requests ADD CONSTRAINT settings_change_requests_requested_by_fkey FOREIGN KEY (requested_by) REFERENCES users(id);
ALTER TABLE public.settings_change_requests ADD CONSTRAINT settings_change_status_check CHECK ((status = ANY (ARRAY['PENDING'::text, 'APPROVED'::text, 'REJECTED'::text, 'CANCELLED'::text])));
ALTER TABLE public.settings ADD CONSTRAINT settings_key_key UNIQUE (key);
ALTER TABLE public.settings ADD CONSTRAINT settings_pkey PRIMARY KEY (id);

-- Stock Adjustments & Counts & Transfers
ALTER TABLE public.stock_adjustments ADD CONSTRAINT stock_adjustments_pkey PRIMARY KEY (id);
ALTER TABLE public.stock_count_items ADD CONSTRAINT stock_count_items_pkey PRIMARY KEY (id);
ALTER TABLE public.stock_counts ADD CONSTRAINT stock_counts_count_no_key UNIQUE (count_no);
ALTER TABLE public.stock_counts ADD CONSTRAINT stock_counts_pkey PRIMARY KEY (id);
ALTER TABLE public.stock_movements ADD CONSTRAINT stock_movements_pkey PRIMARY KEY (id);
ALTER TABLE public.stock_transfer_costs ADD CONSTRAINT stock_transfer_costs_pkey PRIMARY KEY (id);
ALTER TABLE public.stock_transfers ADD CONSTRAINT stock_transfers_from_warehouse_id_fkey FOREIGN KEY (from_warehouse_id) REFERENCES warehouses(id);
ALTER TABLE public.stock_transfers ADD CONSTRAINT stock_transfers_pkey PRIMARY KEY (id);
ALTER TABLE public.stock_transfers ADD CONSTRAINT stock_transfers_product_id_fkey FOREIGN KEY (product_id) REFERENCES products(id);
ALTER TABLE public.stock_transfers ADD CONSTRAINT stock_transfers_qty_check CHECK ((qty > 0));
ALTER TABLE public.stock_transfers ADD CONSTRAINT stock_transfers_to_warehouse_id_fkey FOREIGN KEY (to_warehouse_id) REFERENCES warehouses(id);
ALTER TABLE public.stock_transfers ADD CONSTRAINT stock_transfers_transfer_no_key UNIQUE (transfer_no);

-- Suppliers & System Settings
ALTER TABLE public.suppliers ADD CONSTRAINT suppliers_pkey PRIMARY KEY (id);
ALTER TABLE public.suppliers ADD CONSTRAINT suppliers_supplier_code_key UNIQUE (supplier_code);
ALTER TABLE public.system_settings ADD CONSTRAINT system_settings_pkey PRIMARY KEY (id);
ALTER TABLE public.system_settings ADD CONSTRAINT system_settings_setting_key_key UNIQUE (setting_key);

-- Users, Activity Logs & Warehouse Stock (Consolidated unique constraints)
ALTER TABLE public.user_activity_logs ADD CONSTRAINT user_activity_logs_pkey PRIMARY KEY (id);
ALTER TABLE public.user_roles ADD CONSTRAINT user_roles_pkey PRIMARY KEY (user_id, role_id);
ALTER TABLE public.user_roles ADD CONSTRAINT user_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE;
ALTER TABLE public.user_roles ADD CONSTRAINT user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE public.users ADD CONSTRAINT users_employee_code_key UNIQUE (employee_code);
ALTER TABLE public.users ADD CONSTRAINT users_pkey PRIMARY KEY (id);
ALTER TABLE public.users ADD CONSTRAINT users_role_id_fkey FOREIGN KEY (role_id) REFERENCES roles(id);
ALTER TABLE public.users ADD CONSTRAINT users_username_key UNIQUE (username);

ALTER TABLE public.warehouse_stock ADD CONSTRAINT warehouse_stock_pkey PRIMARY KEY (id);
ALTER TABLE public.warehouse_stock ADD CONSTRAINT warehouse_stock_product_id_fkey FOREIGN KEY (product_id) REFERENCES products(id);
ALTER TABLE public.warehouse_stock ADD CONSTRAINT warehouse_stock_warehouse_id_fkey FOREIGN KEY (warehouse_id) REFERENCES warehouses(id);
ALTER TABLE public.warehouse_stock ADD CONSTRAINT warehouse_product_unique UNIQUE (warehouse_id, product_id);

-- Warehouses
ALTER TABLE public.warehouses ADD CONSTRAINT warehouses_code_key UNIQUE (code);
ALTER TABLE public.warehouses ADD CONSTRAINT warehouses_pkey PRIMARY KEY (id);
