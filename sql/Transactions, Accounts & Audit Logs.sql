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
    qr_mode text,
    PRIMARY KEY (id)
);

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
    updated_at timestamp with time zone,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.audit_logs (
    id bigint NOT NULL,
    table_name text NOT NULL,
    operation text NOT NULL,
    record_id bigint NOT NULL,
    old_data jsonb,
    new_data jsonb,
    changed_by text,
    changed_at timestamp with time zone,
    PRIMARY KEY (id)
);

