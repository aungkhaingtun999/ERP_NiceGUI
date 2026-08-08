## Table `products`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `name` | `text` |  |
| `price` | `numeric` |  |
| `stock` | `int4` |  |
| `created_at` | `timestamptz` |  Nullable |
| `barcode` | `text` |  Nullable Unique |
| `sku` | `text` |  Nullable Unique |
| `category_id` | `int8` |  Nullable |
| `purchase_price` | `numeric` |  |
| `selling_price` | `numeric` |  Nullable |
| `minimum_stock` | `int4` |  |
| `unit` | `text` |  |
| `image_url` | `text` |  Nullable |
| `notes` | `text` |  Nullable |
| `is_active` | `bool` |  |
| `updated_at` | `timestamptz` |  |
| `short_name` | `text` |  Nullable |
| `brand_id` | `int8` |  Nullable |
| `supplier_id` | `int8` |  Nullable |
| `wholesale_price` | `numeric` |  Nullable |
| `vip_price` | `numeric` |  Nullable |
| `member_price` | `numeric` |  Nullable |
| `tax_rate` | `numeric` |  Nullable |
| `discount_allowed` | `bool` |  Nullable |
| `reorder_level` | `int4` |  Nullable |
| `markup_percent` | `numeric` |  Nullable |
| `owner_selling_price` | `numeric` |  Nullable |
| `price_source` | `varchar` |  Nullable |
| `final_selling_price` | `numeric` |  Nullable |
| `owner_price_locked` | `bool` |  Nullable |
| `track_batches` | `bool` |  Nullable |
| `track_expiry` | `bool` |  Nullable |
| `shelf_life_days` | `int4` |  Nullable |

## Table `roles`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `name` | `text` |  Unique |
| `description` | `text` |  Nullable |
| `created_at` | `timestamptz` |  |

## Table `users`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `username` | `text` |  Unique |
| `full_name` | `text` |  |
| `password_hash` | `text` |  |
| `role_id` | `int8` |  |
| `is_active` | `bool` |  |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |
| `failed_attempts` | `int4` |  Nullable |
| `locked_until` | `timestamptz` |  Nullable |
| `employee_code` | `text` |  Nullable Unique |

## Table `categories`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `name` | `text` |  Unique |
| `description` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `category_code` | `text` |  Nullable Unique |
| `is_active` | `bool` |  |
| `updated_at` | `timestamptz` |  |
| `markup_percent` | `numeric` |  Nullable |

## Table `customers`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `customer_code` | `text` |  Nullable Unique |
| `full_name` | `text` |  |
| `phone` | `text` |  Nullable |
| `email` | `text` |  Nullable |
| `address` | `text` |  Nullable |
| `loyalty_points` | `int4` |  |
| `is_active` | `bool` |  |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `suppliers`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `supplier_code` | `text` |  Nullable Unique |
| `company_name` | `text` |  |
| `contact_name` | `text` |  Nullable |
| `phone` | `text` |  Nullable |
| `email` | `text` |  Nullable |
| `address` | `text` |  Nullable |
| `is_active` | `bool` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `sales`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `invoice_no` | `text` |  Unique |
| `customer_id` | `int8` |  Nullable |
| `cashier_id` | `uuid` |  |
| `subtotal` | `numeric` |  |
| `discount` | `numeric` |  Nullable |
| `tax` | `numeric` |  Nullable |
| `total` | `numeric` |  |
| `paid_amount` | `numeric` |  |
| `change_amount` | `numeric` |  Nullable |
| `payment_method` | `text` |  |
| `sale_status` | `text` |  |
| `created_at` | `timestamptz` |  Nullable |
| `status` | `text` |  Nullable |
| `total_amount` | `numeric` |  Nullable |
| `warehouse_id` | `int8` |  Nullable |
| `counter_id` | `int4` |  Nullable |
| `tax_rate` | `numeric` |  Nullable |

## Table `sale_items`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `sale_id` | `int8` |  |
| `product_id` | `int8` |  |
| `quantity` | `int4` |  |
| `unit_price` | `numeric` |  |
| `discount` | `numeric` |  Nullable |
| `total` | `numeric` |  |
| `product_name` | `text` |  Nullable |

## Table `inventory_logs`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `product_id` | `int8` |  |
| `reference_type` | `text` |  |
| `reference_id` | `int8` |  Nullable |
| `quantity` | `int4` |  |
| `balance_after` | `int4` |  Nullable |
| `remarks` | `text` |  Nullable |
| `created_by` | `uuid` |  Nullable |
| `created_at` | `timestamptz` |  |
| `warehouse_id` | `int8` |  Nullable |
| `transaction_id` | `text` |  Nullable |

## Table `receipts`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary |
| `sale_id` | `int8` |  Nullable |
| `receipt_no` | `text` |  Nullable |
| `total` | `numeric` |  Nullable |
| `paid_amount` | `numeric` |  Nullable |
| `change_amount` | `numeric` |  Nullable |
| `created_at` | `timestamp` |  Nullable |

## Table `refund_items`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary |
| `refund_id` | `int8` |  |
| `sale_item_id` | `int8` |  Nullable |
| `product_id` | `int8` |  |
| `quantity` | `int4` |  |
| `unit_price` | `numeric` |  |
| `total` | `numeric` |  |

## Table `warehouses`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary |
| `code` | `text` |  Unique |
| `name` | `text` |  |
| `branch` | `text` |  Nullable |
| `address` | `text` |  Nullable |
| `phone` | `text` |  Nullable |
| `manager_name` | `text` |  Nullable |
| `is_active` | `bool` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `warehouse_stock`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary |
| `warehouse_id` | `int8` |  |
| `product_id` | `int8` |  |
| `qty` | `int4` |  Nullable |
| `reserved_qty` | `int4` |  Nullable |
| `available_qty` | `int4` |  Nullable |
| `minimum_stock` | `int4` |  Nullable |
| `maximum_stock` | `int4` |  Nullable |
| `reorder_level` | `int4` |  Nullable |
| `location` | `text` |  Nullable |
| `batch_no` | `text` |  Nullable |
| `expiry_date` | `date` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `erp_settings`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary |
| `key` | `text` |  Unique |
| `value` | `text` |  Nullable |
| `created_at` | `timestamp` |  Nullable |

## Table `stock_transfers`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary |
| `transfer_no` | `text` |  Unique |
| `from_warehouse_id` | `int8` |  |
| `to_warehouse_id` | `int8` |  |
| `product_id` | `int8` |  |
| `qty` | `int4` |  |
| `status` | `text` |  |
| `remarks` | `text` |  Nullable |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |

## Table `purchases`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `product_id` | `int8` |  |
| `qty` | `numeric` |  |
| `price` | `numeric` |  |
| `total` | `numeric` |  |
| `created_at` | `timestamptz` |  Nullable |
| `supplier_id` | `int8` |  Nullable |
| `warehouse_id` | `int8` |  Nullable |
| `purchase_no` | `text` |  Nullable Unique |
| `status` | `text` |  Nullable |
| `notes` | `text` |  Nullable |
| `created_by` | `uuid` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `tax` | `numeric` |  Nullable |
| `discount` | `numeric` |  Nullable |
| `net_total` | `numeric` |  Nullable |
| `payment_method` | `text` |  Nullable |
| `reference_no` | `text` |  Nullable |

## Table `audit_logs`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `table_name` | `text` |  |
| `operation` | `text` |  |
| `record_id` | `int8` |  |
| `old_data` | `jsonb` |  Nullable |
| `new_data` | `jsonb` |  Nullable |
| `changed_by` | `text` |  Nullable |
| `changed_at` | `timestamptz` |  Nullable |

## Table `permissions`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `name` | `text` |  Unique |
| `permission_key` | `text` |  Nullable |
| `module` | `text` |  Nullable |
| `description` | `text` |  Nullable |

## Table `role_permissions`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `role_id` | `int8` | Primary |
| `permission_id` | `int8` | Primary |

## Table `user_roles`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `user_id` | `uuid` | Primary |
| `role_id` | `int8` | Primary |

## Table `refunds`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `sale_id` | `int8` |  Nullable |
| `refund_date` | `timestamptz` |  Nullable |
| `reason` | `text` |  Nullable |
| `refund_amount` | `numeric` |  Nullable |
| `cashier_id` | `uuid` |  Nullable |
| `status` | `text` |  Nullable |
| `approved_by` | `uuid` |  Nullable |
| `approved_at` | `timestamptz` |  Nullable |
| `rejected_by` | `uuid` |  Nullable |
| `rejected_reason` | `text` |  Nullable |

## Table `products_stock_backup`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` |  Nullable |
| `name` | `text` |  Nullable |
| `price` | `numeric` |  Nullable |
| `stock` | `int4` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `barcode` | `text` |  Nullable |
| `sku` | `text` |  Nullable |
| `category_id` | `int8` |  Nullable |
| `purchase_price` | `numeric` |  Nullable |
| `selling_price` | `numeric` |  Nullable |
| `minimum_stock` | `int4` |  Nullable |
| `unit` | `text` |  Nullable |
| `image_url` | `text` |  Nullable |
| `notes` | `text` |  Nullable |
| `is_active` | `bool` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `short_name` | `text` |  Nullable |
| `brand_id` | `int8` |  Nullable |
| `supplier_id` | `int8` |  Nullable |
| `wholesale_price` | `numeric` |  Nullable |
| `vip_price` | `numeric` |  Nullable |
| `member_price` | `numeric` |  Nullable |
| `tax_rate` | `numeric` |  Nullable |
| `discount_allowed` | `bool` |  Nullable |
| `reorder_level` | `int4` |  Nullable |

## Table `inventory_transactions`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `product_id` | `int8` |  |
| `warehouse_id` | `int8` |  |
| `transaction_type` | `text` |  |
| `qty_in` | `numeric` |  Nullable |
| `qty_out` | `numeric` |  Nullable |
| `unit_cost` | `numeric` |  Nullable |
| `reference_type` | `text` |  Nullable |
| `reference_id` | `int8` |  Nullable |
| `remarks` | `text` |  Nullable |
| `created_by` | `uuid` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `inventory_cost_layers`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `product_id` | `int8` |  |
| `warehouse_id` | `int8` |  |
| `qty_in` | `int4` |  |
| `qty_remaining` | `int4` |  |
| `unit_cost` | `numeric` |  |
| `reference_type` | `text` |  Nullable |
| `reference_id` | `int8` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `inventory_cost_transactions`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary |
| `sale_id` | `int8` |  |
| `sale_item_id` | `int8` |  |
| `product_id` | `int8` |  |
| `warehouse_id` | `int8` |  |
| `cost_layer_id` | `int8` |  |
| `qty` | `int4` |  |
| `unit_cost` | `numeric` |  |
| `total_cost` | `numeric` |  |
| `created_at` | `timestamptz` |  Nullable |

## Table `function_backup_purchase_receive`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `backup_time` | `timestamptz` |  Nullable |
| `proname` | `name` |  Nullable |
| `function_definition` | `text` |  Nullable |

## Table `inventory_cost_transactions_backup`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` |  Nullable |
| `sale_id` | `int8` |  Nullable |
| `sale_item_id` | `int8` |  Nullable |
| `product_id` | `int8` |  Nullable |
| `warehouse_id` | `int8` |  Nullable |
| `cost_layer_id` | `int8` |  Nullable |
| `qty` | `int4` |  Nullable |
| `unit_cost` | `numeric` |  Nullable |
| `total_cost` | `numeric` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `inventory_cost_layers_backup_before_opening`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` |  Nullable |
| `product_id` | `int8` |  Nullable |
| `warehouse_id` | `int8` |  Nullable |
| `qty_in` | `int4` |  Nullable |
| `qty_remaining` | `int4` |  Nullable |
| `unit_cost` | `numeric` |  Nullable |
| `reference_type` | `text` |  Nullable |
| `reference_id` | `int8` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `inventory_cost_transactions_backup_before_fifo_rebuild`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` |  Nullable |
| `sale_id` | `int8` |  Nullable |
| `sale_item_id` | `int8` |  Nullable |
| `product_id` | `int8` |  Nullable |
| `warehouse_id` | `int8` |  Nullable |
| `cost_layer_id` | `int8` |  Nullable |
| `qty` | `int4` |  Nullable |
| `unit_cost` | `numeric` |  Nullable |
| `total_cost` | `numeric` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `inventory_cost_layers_backup_final`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` |  Nullable |
| `product_id` | `int8` |  Nullable |
| `warehouse_id` | `int8` |  Nullable |
| `qty_in` | `int4` |  Nullable |
| `qty_remaining` | `int4` |  Nullable |
| `unit_cost` | `numeric` |  Nullable |
| `reference_type` | `text` |  Nullable |
| `reference_id` | `int8` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `inventory_cost_transactions_backup_final`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` |  Nullable |
| `sale_id` | `int8` |  Nullable |
| `sale_item_id` | `int8` |  Nullable |
| `product_id` | `int8` |  Nullable |
| `warehouse_id` | `int8` |  Nullable |
| `cost_layer_id` | `int8` |  Nullable |
| `qty` | `int4` |  Nullable |
| `unit_cost` | `numeric` |  Nullable |
| `total_cost` | `numeric` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `inventory_cost_layers_backup_fifo_fix`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` |  Nullable |
| `product_id` | `int8` |  Nullable |
| `warehouse_id` | `int8` |  Nullable |
| `qty_in` | `int4` |  Nullable |
| `qty_remaining` | `int4` |  Nullable |
| `unit_cost` | `numeric` |  Nullable |
| `reference_type` | `text` |  Nullable |
| `reference_id` | `int8` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `inventory_cost_layers_backup`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` |  Nullable |
| `product_id` | `int8` |  Nullable |
| `warehouse_id` | `int8` |  Nullable |
| `qty_in` | `int4` |  Nullable |
| `qty_remaining` | `int4` |  Nullable |
| `unit_cost` | `numeric` |  Nullable |
| `reference_type` | `text` |  Nullable |
| `reference_id` | `int8` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `user_activity_logs`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary |
| `user_id` | `uuid` |  Nullable |
| `action` | `text` |  |
| `description` | `text` |  Nullable |
| `created_at` | `timestamp` |  Nullable |

## Table `purchase_batches`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `product_id` | `int8` |  |
| `warehouse_id` | `int8` |  |
| `purchase_id` | `int8` |  Nullable |
| `qty` | `numeric` |  |
| `remaining_qty` | `numeric` |  |
| `cost` | `numeric` |  |
| `created_at` | `timestamptz` |  Nullable |
| `selling_price` | `numeric` |  Nullable |

## Table `settings`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary |
| `key` | `text` |  Unique |
| `value` | `text` |  Nullable |
| `description` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `category_markup`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary |
| `category_id` | `int8` |  |
| `markup_percent` | `numeric` |  |
| `is_active` | `bool` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `brand_markup`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary |
| `brand_id` | `int8` |  |
| `markup_percent` | `numeric` |  |
| `is_active` | `bool` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `product_markup`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary |
| `product_id` | `int8` |  Unique |
| `markup_percent` | `numeric` |  Nullable |
| `fixed_price` | `numeric` |  Nullable |
| `is_active` | `bool` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `category_markup_settings`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `category_id` | `int8` |  Nullable Unique |
| `markup_percent` | `numeric` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `status` | `text` |  Nullable |
| `created_by` | `uuid` |  Nullable |
| `approved_by` | `uuid` |  Nullable |
| `approved_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `category_pricing_rules`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `category_id` | `int8` |  Unique |
| `markup_percent` | `numeric` |  |
| `auto_update` | `bool` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `opening_stock`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary |
| `warehouse_id` | `int8` |  |
| `opening_date` | `date` |  |
| `remarks` | `text` |  Nullable |
| `created_by` | `uuid` |  Nullable |
| `created_at` | `timestamptz` |  |

## Table `opening_stock_items`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary |
| `opening_stock_id` | `int8` |  |
| `product_id` | `int8` |  |
| `warehouse_id` | `int8` |  |
| `qty` | `numeric` |  |
| `unit_cost` | `numeric` |  |
| `total_cost` | `numeric` |  Nullable |
| `created_at` | `timestamptz` |  |

## Table `pos_products_view_backup`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` |  Nullable |
| `name` | `text` |  Nullable |
| `sku` | `text` |  Nullable |
| `barcode` | `text` |  Nullable |
| `purchase_price` | `numeric` |  Nullable |
| `selling_price` | `numeric` |  Nullable |
| `owner_selling_price` | `numeric` |  Nullable |
| `final_selling_price` | `numeric` |  Nullable |
| `price_source` | `text` |  Nullable |
| `category_id` | `int8` |  Nullable |
| `category` | `text` |  Nullable |
| `warehouse_id` | `int8` |  Nullable |
| `qty` | `int4` |  Nullable |
| `reserved_qty` | `int4` |  Nullable |
| `available_qty` | `int4` |  Nullable |
| `minimum_stock` | `int4` |  Nullable |

## Table `system_settings`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary |
| `setting_key` | `text` |  Unique |
| `setting_value` | `jsonb` |  |
| `description` | `text` |  Nullable |
| `status` | `text` |  Nullable |
| `created_by` | `uuid` |  Nullable |
| `approved_by` | `uuid` |  Nullable |
| `approved_at` | `timestamptz` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `category_markup_approval`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `category_id` | `int8` |  |
| `old_markup_percent` | `numeric` |  Nullable |
| `new_markup_percent` | `numeric` |  |
| `requested_by` | `uuid` |  Nullable |
| `approved_by` | `uuid` |  Nullable |
| `status` | `text` |  Nullable |
| `request_note` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `approved_at` | `timestamptz` |  Nullable |

## Table `stock_transfer_costs`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary |
| `transfer_id` | `int8` |  |
| `product_id` | `int8` |  |
| `from_warehouse_id` | `int8` |  |
| `to_warehouse_id` | `int8` |  |
| `cost_layer_id` | `int8` |  Nullable |
| `qty` | `numeric` |  |
| `unit_cost` | `numeric` |  |
| `total_cost` | `numeric` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `stock_movements`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary |
| `product_id` | `int8` |  |
| `warehouse_id` | `int8` |  |
| `movement_type` | `text` |  |
| `qty` | `numeric` |  |
| `reference_type` | `text` |  Nullable |
| `reference_id` | `int8` |  Nullable |
| `unit_cost` | `numeric` |  Nullable |
| `total_cost` | `numeric` |  Nullable |
| `note` | `text` |  Nullable |
| `created_by` | `uuid` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `stock_adjustments`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `product_id` | `int8` |  |
| `warehouse_id` | `int8` |  |
| `adjustment_type` | `text` |  |
| `qty` | `numeric` |  |
| `unit_cost` | `numeric` |  |
| `reason` | `text` |  Nullable |
| `status` | `text` |  Nullable |
| `requested_by` | `uuid` |  Nullable |
| `approved_by` | `uuid` |  Nullable |
| `approved_at` | `timestamptz` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `stock_counts`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `warehouse_id` | `int8` |  |
| `count_no` | `text` |  Nullable Unique |
| `count_date` | `timestamptz` |  Nullable |
| `status` | `text` |  Nullable |
| `counted_by` | `uuid` |  Nullable |
| `approved_by` | `uuid` |  Nullable |
| `approved_at` | `timestamptz` |  Nullable |
| `note` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `stock_count_items`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `count_id` | `int8` |  |
| `product_id` | `int8` |  |
| `system_qty` | `numeric` |  |
| `counted_qty` | `numeric` |  |
| `variance_qty` | `numeric` |  Nullable |
| `unit_cost` | `numeric` |  |
| `variance_cost` | `numeric` |  Nullable |
| `note` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `settings_change_requests`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary |
| `setting_key` | `text` |  |
| `old_value` | `text` |  Nullable |
| `new_value` | `text` |  Nullable |
| `reason` | `text` |  Nullable |
| `status` | `text` |  Nullable |
| `requested_by` | `uuid` |  Nullable |
| `approved_by` | `uuid` |  Nullable |
| `rejected_by` | `uuid` |  Nullable |
| `rejected_reason` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `approved_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `price_import_queue`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary |
| `product_id` | `int8` |  Nullable |
| `barcode` | `text` |  Nullable |
| `sku` | `text` |  Nullable |
| `name` | `text` |  Nullable |
| `old_selling_price` | `numeric` |  Nullable |
| `purchase_price` | `numeric` |  Nullable |
| `markup_percent` | `numeric` |  Nullable |
| `new_selling_price` | `numeric` |  Nullable |
| `price_source` | `text` |  Nullable |
| `status` | `text` |  Nullable |
| `reason` | `text` |  Nullable |
| `created_by` | `uuid` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `approved_by` | `uuid` |  Nullable |
| `approved_at` | `timestamptz` |  Nullable |

## Table `payment_transactions`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `sale_id` | `int8` |  Nullable |
| `payment_method` | `text` |  |
| `provider` | `text` |  Nullable |
| `transaction_id` | `text` |  Nullable |
| `amount` | `numeric` |  |
| `status` | `text` |  Nullable |
| `verified_by` | `uuid` |  Nullable |
| `verified_at` | `timestamptz` |  Nullable |
| `note` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `cashier_id` | `uuid` |  Nullable |
| `rejected_reason` | `text` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `payment_accounts`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary |
| `company_id` | `uuid` |  Nullable |
| `branch_id` | `int8` |  Nullable |
| `provider` | `text` |  |
| `account_name` | `text` |  |
| `account_no` | `text` |  |
| `enabled` | `bool` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `qr_payload_template` | `text` |  Nullable |
| `qr_prefix` | `text` |  Nullable |
| `qr_mode` | `text` |  Nullable |

## Table `inventory_cost_layers_backup_20260806`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` |  Nullable |
| `product_id` | `int8` |  Nullable |
| `warehouse_id` | `int8` |  Nullable |
| `qty_in` | `int4` |  Nullable |
| `qty_remaining` | `int4` |  Nullable |
| `unit_cost` | `numeric` |  Nullable |
| `reference_type` | `text` |  Nullable |
| `reference_id` | `int8` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `inventory_batches`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary |
| `product_id` | `int8` |  |
| `warehouse_id` | `int8` |  |
| `batch_no` | `text` |  |
| `manufacturing_date` | `date` |  Nullable |
| `expiry_date` | `date` |  Nullable |
| `quantity` | `numeric` |  |
| `unit_cost` | `numeric` |  |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `backup_stock_adjustments_20260808`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` |  Nullable |
| `product_id` | `int8` |  Nullable |
| `warehouse_id` | `int8` |  Nullable |
| `adjustment_type` | `text` |  Nullable |
| `qty` | `numeric` |  Nullable |
| `unit_cost` | `numeric` |  Nullable |
| `reason` | `text` |  Nullable |
| `status` | `text` |  Nullable |
| `requested_by` | `uuid` |  Nullable |
| `approved_by` | `uuid` |  Nullable |
| `approved_at` | `timestamptz` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `backup_inventory_cost_layers_20260808`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` |  Nullable |
| `product_id` | `int8` |  Nullable |
| `warehouse_id` | `int8` |  Nullable |
| `qty_in` | `int4` |  Nullable |
| `qty_remaining` | `int4` |  Nullable |
| `unit_cost` | `numeric` |  Nullable |
| `reference_type` | `text` |  Nullable |
| `reference_id` | `int8` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `backup_warehouse_stock_20260808`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` |  Nullable |
| `warehouse_id` | `int8` |  Nullable |
| `product_id` | `int8` |  Nullable |
| `qty` | `int4` |  Nullable |
| `reserved_qty` | `int4` |  Nullable |
| `available_qty` | `int4` |  Nullable |
| `minimum_stock` | `int4` |  Nullable |
| `maximum_stock` | `int4` |  Nullable |
| `reorder_level` | `int4` |  Nullable |
| `location` | `text` |  Nullable |
| `batch_no` | `text` |  Nullable |
| `expiry_date` | `date` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `backup_stock_movements_20260808`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` |  Nullable |
| `product_id` | `int8` |  Nullable |
| `warehouse_id` | `int8` |  Nullable |
| `movement_type` | `text` |  Nullable |
| `qty` | `numeric` |  Nullable |
| `reference_type` | `text` |  Nullable |
| `reference_id` | `int8` |  Nullable |
| `unit_cost` | `numeric` |  Nullable |
| `total_cost` | `numeric` |  Nullable |
| `note` | `text` |  Nullable |
| `created_by` | `uuid` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `backup_products_20260808`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` |  Nullable |
| `name` | `text` |  Nullable |
| `price` | `numeric` |  Nullable |
| `stock` | `int4` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `barcode` | `text` |  Nullable |
| `sku` | `text` |  Nullable |
| `category_id` | `int8` |  Nullable |
| `purchase_price` | `numeric` |  Nullable |
| `selling_price` | `numeric` |  Nullable |
| `minimum_stock` | `int4` |  Nullable |
| `unit` | `text` |  Nullable |
| `image_url` | `text` |  Nullable |
| `notes` | `text` |  Nullable |
| `is_active` | `bool` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `short_name` | `text` |  Nullable |
| `brand_id` | `int8` |  Nullable |
| `supplier_id` | `int8` |  Nullable |
| `wholesale_price` | `numeric` |  Nullable |
| `vip_price` | `numeric` |  Nullable |
| `member_price` | `numeric` |  Nullable |
| `tax_rate` | `numeric` |  Nullable |
| `discount_allowed` | `bool` |  Nullable |
| `reorder_level` | `int4` |  Nullable |
| `markup_percent` | `numeric` |  Nullable |
| `owner_selling_price` | `numeric` |  Nullable |
| `price_source` | `varchar` |  Nullable |
| `final_selling_price` | `numeric` |  Nullable |
| `owner_price_locked` | `bool` |  Nullable |
| `track_batches` | `bool` |  Nullable |
| `track_expiry` | `bool` |  Nullable |
| `shelf_life_days` | `int4` |  Nullable |

## Table `stock_movements_backup_20260808`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` |  Nullable |
| `product_id` | `int8` |  Nullable |
| `warehouse_id` | `int8` |  Nullable |
| `movement_type` | `text` |  Nullable |
| `qty` | `numeric` |  Nullable |
| `reference_type` | `text` |  Nullable |
| `reference_id` | `int8` |  Nullable |
| `unit_cost` | `numeric` |  Nullable |
| `total_cost` | `numeric` |  Nullable |
| `note` | `text` |  Nullable |
| `created_by` | `uuid` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## RLS Policies

### `stock_transfers`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Allow anon insert stock transfers` | INSERT | anon | PERMISSIVE | — | `true` |
| `Allow insert stock transfers` | INSERT | authenticated | PERMISSIVE | — | `true` |
| `Allow stock transfer insert` | INSERT | public | PERMISSIVE | — | `true` |

### `warehouse_stock`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Allow anon insert warehouse_stock` | INSERT | anon | PERMISSIVE | — | `true` |
| `Allow anon read warehouse stock` | SELECT | anon | PERMISSIVE | `true` | — |
| `Allow anon update warehouse_stock` | UPDATE | anon | PERMISSIVE | `true` | `true` |
| `Allow authenticated delete warehouse stock` | DELETE | authenticated | PERMISSIVE | `true` | — |
| `Allow authenticated insert warehouse stock` | INSERT | authenticated | PERMISSIVE | — | `true` |
| `Allow authenticated insert warehouse_stock` | INSERT | authenticated | PERMISSIVE | — | `true` |
| `Allow authenticated read stock` | SELECT | authenticated | PERMISSIVE | `true` | — |
| `Allow authenticated read warehouse_stock` | SELECT | authenticated | PERMISSIVE | `true` | — |
| `Allow authenticated update warehouse stock` | UPDATE | authenticated | PERMISSIVE | `true` | `true` |
| `Allow authenticated update warehouse_stock` | UPDATE | authenticated | PERMISSIVE | `true` | `true` |
| `Allow authenticated users read warehouse stock` | SELECT | authenticated | PERMISSIVE | `true` | — |

### `audit_logs`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Admin can view audit logs` | SELECT | authenticated | PERMISSIVE | `(EXISTS ( SELECT 1    FROM (user_roles ur      JOIN roles r ON ((ur.role_id = r.id)))   WHERE ((ur.user_id = auth.uid()) AND (r.name = 'Admin'::text))))` | — |
| `No one can modify audit logs` | INSERT | public | PERMISSIVE | — | `false` |

### `purchases`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Allow anon insert purchases` | INSERT | anon | PERMISSIVE | — | `true` |
| `Allow authenticated insert purchases` | INSERT | authenticated | PERMISSIVE | — | `true` |
| `Allow authenticated update purchases` | UPDATE | authenticated | PERMISSIVE | `true` | `true` |
| `ERP purchase insert` | INSERT | authenticated | PERMISSIVE | — | `true` |

### `sales`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Allow authenticated read sales` | SELECT | authenticated | PERMISSIVE | `true` | — |

### `roles`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Allow anon read roles` | SELECT | anon | PERMISSIVE | `true` | — |
| `Allow authenticated read roles` | SELECT | authenticated | PERMISSIVE | `true` | — |

### `warehouses`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Enable read access for all users` | SELECT | public | PERMISSIVE | `true` | — |

### `refunds`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Allow ERP read refunds` | SELECT | anon | PERMISSIVE | `true` | — |

### `sale_items`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Allow authenticated read sale_items` | SELECT | authenticated | PERMISSIVE | `true` | — |

### `products`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Allow anon insert products` | INSERT | anon | PERMISSIVE | — | `true` |
| `Allow anon read products` | SELECT | anon | PERMISSIVE | `true` | — |
| `Allow authenticated delete products` | DELETE | authenticated | PERMISSIVE | `true` | — |
| `Allow authenticated insert products` | INSERT | authenticated | PERMISSIVE | — | `true` |
| `Allow authenticated read products` | SELECT | authenticated | PERMISSIVE | `true` | — |
| `Allow authenticated update products` | UPDATE | authenticated | PERMISSIVE | `true` | `true` |
| `Allow read products` | SELECT | authenticated | PERMISSIVE | `true` | — |

