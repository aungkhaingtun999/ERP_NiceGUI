-- --- PERFORMANCE INDEXES BACKUP ---

-- Audit & ERP
CREATE INDEX IF NOT EXISTS idx_audit_changed_at ON public.audit_logs USING btree (changed_at);
CREATE INDEX IF NOT EXISTS idx_audit_table_name ON public.audit_logs USING btree (table_name);
CREATE UNIQUE INDEX IF NOT EXISTS erp_settings_key_idx ON public.erp_settings USING btree (key);

-- Cost Layers & Batches
CREATE INDEX IF NOT EXISTS idx_cost_layers_product_warehouse ON public.inventory_cost_layers USING btree (product_id, warehouse_id);
CREATE INDEX IF NOT EXISTS idx_cost_layers_remaining ON public.inventory_cost_layers USING btree (qty_remaining);
CREATE UNIQUE INDEX IF NOT EXISTS idx_inventory_cost_unique ON public.inventory_cost_transactions USING btree (sale_id, sale_item_id, cost_layer_id);
CREATE INDEX IF NOT EXISTS idx_inventory_batches_expiry ON public.inventory_batches USING btree (expiry_date);
CREATE INDEX IF NOT EXISTS idx_inventory_batches_product ON public.inventory_batches USING btree (product_id);
CREATE INDEX IF NOT EXISTS idx_inventory_batches_warehouse ON public.inventory_batches USING btree (warehouse_id);

-- Inventory Transactions & Logs
CREATE INDEX IF NOT EXISTS idx_inventory_transactions_date ON public.inventory_transactions USING btree (created_at);
CREATE INDEX IF NOT EXISTS idx_inventory_transactions_product ON public.inventory_transactions USING btree (product_id);
CREATE INDEX IF NOT EXISTS idx_inventory_transactions_warehouse ON public.inventory_transactions USING btree (warehouse_id);

-- Payment Indexes
CREATE INDEX IF NOT EXISTS idx_payment_accounts_branch ON public.payment_accounts USING btree (branch_id);
CREATE INDEX IF NOT EXISTS idx_payment_accounts_enabled ON public.payment_accounts USING btree (enabled);
CREATE INDEX IF NOT EXISTS idx_payment_accounts_provider ON public.payment_accounts USING btree (provider);
CREATE INDEX IF NOT EXISTS idx_payment_status ON public.payment_transactions USING btree (status);
CREATE INDEX IF NOT EXISTS idx_payment_transaction_id ON public.payment_transactions USING btree (transaction_id);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_sale ON public.payment_transactions USING btree (sale_id);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_status ON public.payment_transactions USING btree (status);

-- Pricing & Imports
CREATE INDEX IF NOT EXISTS idx_price_import_queue_product ON public.price_import_queue USING btree (product_id);
CREATE INDEX IF NOT EXISTS idx_price_import_queue_status ON public.price_import_queue USING btree (status);
CREATE INDEX IF NOT EXISTS idx_purchase_batches_fifo ON public.purchase_batches USING btree (product_id, warehouse_id, created_at);
CREATE INDEX IF NOT EXISTS idx_purchase_batches_product ON public.purchase_batches USING btree (product_id);

-- Refunds & Settings Changes
CREATE INDEX IF NOT EXISTS idx_refund_items_product ON public.refund_items USING btree (product_id);
CREATE INDEX IF NOT EXISTS idx_refund_items_refund ON public.refund_items USING btree (refund_id);
CREATE INDEX IF NOT EXISTS idx_settings_change_requested_by ON public.settings_change_requests USING btree (requested_by);
CREATE INDEX IF NOT EXISTS idx_settings_change_status ON public.settings_change_requests USING btree (status);

-- Stock Adjustments, Counts & Movements
CREATE INDEX IF NOT EXISTS idx_stock_adjustments_date ON public.stock_adjustments USING btree (created_at);
CREATE INDEX IF NOT EXISTS idx_stock_adjustments_product ON public.stock_adjustments USING btree (product_id);
CREATE INDEX IF NOT EXISTS idx_stock_adjustments_status ON public.stock_adjustments USING btree (status);
CREATE INDEX IF NOT EXISTS idx_stock_adjustments_warehouse ON public.stock_adjustments USING btree (warehouse_id);
CREATE INDEX IF NOT EXISTS idx_stock_count_items_count ON public.stock_count_items USING btree (count_id);
CREATE INDEX IF NOT EXISTS idx_stock_count_items_product ON public.stock_count_items USING btree (product_id);
CREATE INDEX IF NOT EXISTS idx_stock_counts_warehouse ON public.stock_counts USING btree (warehouse_id);
CREATE INDEX IF NOT EXISTS idx_stock_movements_date ON public.stock_movements USING btree (created_at);
CREATE INDEX IF NOT EXISTS idx_stock_movements_product ON public.stock_movements USING btree (product_id);
CREATE INDEX IF NOT EXISTS idx_stock_movements_reference ON public.stock_movements USING btree (reference_type, reference_id);
CREATE INDEX IF NOT EXISTS idx_stock_movements_warehouse ON public.stock_movements USING btree (warehouse_id);

-- Stock Transfers
CREATE INDEX IF NOT EXISTS idx_stock_transfers_created ON public.stock_transfers USING btree (created_at);
CREATE INDEX IF NOT EXISTS idx_stock_transfers_from ON public.stock_transfers USING btree (from_warehouse_id);
CREATE INDEX IF NOT EXISTS idx_stock_transfers_product ON public.stock_transfers USING btree (product_id);
CREATE INDEX IF NOT EXISTS idx_stock_transfers_to ON public.stock_transfers USING btree (to_warehouse_id);
