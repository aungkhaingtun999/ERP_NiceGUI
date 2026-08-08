CREATE TABLE IF NOT EXISTS public.inventory_cost_layers (
    id bigint NOT NULL,
    product_id bigint NOT NULL,
    warehouse_id bigint NOT NULL,
    qty_in integer NOT NULL,
    qty_remaining integer NOT NULL,
    unit_cost numeric NOT NULL,
    reference_type text,
    reference_id bigint,
    created_at timestamp with time zone,
    PRIMARY KEY (id)
);

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
    created_at timestamp with time zone,
    PRIMARY KEY (id)
);

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
    updated_at timestamp with time zone,
    PRIMARY KEY (id)
);

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
    created_at timestamp with time zone,
    PRIMARY KEY (id)
);
