-- =========================================================
-- STEP 1: ENABLE ROW LEVEL SECURITY ON ALL TABLES
-- =========================================================

ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.products ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.purchases ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.refunds ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.role_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sale_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.stock_transfers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.warehouse_stock ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.warehouses ENABLE ROW LEVEL SECURITY;


-- =========================================================
-- STEP 2: CREATE RLS POLICIES (CLEANED & DEDUPLICATED)
-- =========================================================

-- Audit Logs Policies
CREATE POLICY "Admin can view audit logs" ON public.audit_logs AS PERMISSIVE FOR SELECT TO authenticated USING ((EXISTS ( SELECT 1
   FROM (user_roles ur
     JOIN roles r ON ((ur.role_id = r.id)))
  WHERE ((ur.user_id = auth.uid()) AND (r.name = 'Admin'::text)))));

CREATE POLICY "No one can modify audit logs" ON public.audit_logs AS PERMISSIVE FOR INSERT TO public WITH CHECK (false);


-- Refunds Policies
CREATE POLICY "Allow ERP read refunds" ON public.refunds AS PERMISSIVE FOR SELECT TO anon USING (true);


-- Products Policies
CREATE POLICY "Allow anon insert products" ON public.products AS PERMISSIVE FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "Allow anon read products" ON public.products AS PERMISSIVE FOR SELECT TO anon USING (true);
CREATE POLICY "Allow authenticated delete products" ON public.products AS PERMISSIVE FOR DELETE TO authenticated USING (true);
CREATE POLICY "Allow authenticated insert products" ON public.products AS PERMISSIVE FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Allow authenticated read products" ON public.products AS PERMISSIVE FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow authenticated update products" ON public.products AS PERMISSIVE FOR UPDATE TO authenticated USING (true) WITH CHECK (true);


-- Purchases Policies
CREATE POLICY "Allow anon insert purchases" ON public.purchases AS PERMISSIVE FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "Allow authenticated insert purchases" ON public.purchases AS PERMISSIVE FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Allow authenticated update purchases" ON public.purchases AS PERMISSIVE FOR UPDATE TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "ERP purchase insert" ON public.purchases AS PERMISSIVE FOR INSERT TO authenticated WITH CHECK (true);


-- Roles Policies
CREATE POLICY "Allow anon read roles" ON public.roles AS PERMISSIVE FOR SELECT TO anon USING (true);
CREATE POLICY "Allow authenticated read roles" ON public.roles AS PERMISSIVE FOR SELECT TO authenticated USING (true);


-- Sales & Sale Items Policies
CREATE POLICY "Allow authenticated read sale_items" ON public.sale_items AS PERMISSIVE FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow authenticated read sales" ON public.sales AS PERMISSIVE FOR SELECT TO authenticated USING (true);


-- Stock Transfers Policies
CREATE POLICY "Allow anon insert stock transfers" ON public.stock_transfers AS PERMISSIVE FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "Allow authenticated insert stock transfers" ON public.stock_transfers AS PERMISSIVE FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Allow stock transfer insert" ON public.stock_transfers AS PERMISSIVE FOR INSERT TO public WITH CHECK (true);


-- Warehouse Stock Policies (Duplicates removed & consolidated)
CREATE POLICY "Allow anon insert warehouse_stock" ON public.warehouse_stock AS PERMISSIVE FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "Allow anon read warehouse stock" ON public.warehouse_stock AS PERMISSIVE FOR SELECT TO anon USING (true);
CREATE POLICY "Allow anon update warehouse_stock" ON public.warehouse_stock AS PERMISSIVE FOR UPDATE TO anon USING (true) WITH CHECK (true);
CREATE POLICY "Allow authenticated delete warehouse stock" ON public.warehouse_stock AS PERMISSIVE FOR DELETE TO authenticated USING (true);
CREATE POLICY "Allow authenticated insert warehouse_stock" ON public.warehouse_stock AS PERMISSIVE FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Allow authenticated read warehouse_stock" ON public.warehouse_stock AS PERMISSIVE FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow authenticated update warehouse_stock" ON public.warehouse_stock AS PERMISSIVE FOR UPDATE TO authenticated USING (true) WITH CHECK (true);


-- Warehouses Policies
CREATE POLICY "Enable read access for all users" ON public.warehouses AS PERMISSIVE FOR SELECT TO public USING (true);
