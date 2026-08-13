# ==============================================================================
# erp_core/repositories/product_repository.py
# ERP ENTERPRISE PRODUCT REPOSITORY v32.0 FINAL
#
# Product Master + POS Product View + Inventory
#
# Architecture:
#
# Supabase
#     ↓
# Repository
#     ↓
# Loader
#     ↓
# POS / Inventory / Sales
#
# IMPORTANT
# ------------------------------------------------------------------------------
# POS canonical source:
#
#     pos_products_view
#
# Actual POS view columns:
#
#     id
#     name
#     sku
#     barcode
#     purchase_price
#     selling_price
#     owner_selling_price
#     owner_price_locked
#     final_selling_price
#     price_source
#     category_id
#     category
#     warehouse_id
#     qty
#     reserved_qty
#     available_qty
#     minimum_stock
#
# Do NOT query is_active from pos_products_view.
# ==============================================================================


from typing import (
    List,
    Dict,
    Any,
    Optional,
)


from ..base_repo import (
    log_error,
)


from .base_repository import (
    BaseRepository,
)


from ..config import (
    TABLE_PRODUCT_VIEW,
    TABLE_PRODUCTS,
    TABLE_WAREHOUSE_STOCK,
)


# ==============================================================================
# PRODUCT REPOSITORY
# ==============================================================================


class ProductRepository(BaseRepository):

    """
    ERP Product Database Operations.

    POS:
        pos_products_view

    Product Master:
        products

    Inventory:
        warehouse_stock
    """

    # ==========================================================================
    # POS PRODUCTS
    # ==========================================================================
    #
    # Canonical POS source = pos_products_view
    #
    # This method is intentionally separate from Product Master.
    # ==========================================================================

    def get_pos_products(
        self,
        warehouse_id: Optional[int] = None,
        keyword: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:

        try:

            query = (
                self.client
                .table(TABLE_PRODUCT_VIEW)
                .select(
                    """
                    id,
                    name,
                    sku,
                    barcode,
                    purchase_price,
                    selling_price,
                    owner_selling_price,
                    owner_price_locked,
                    final_selling_price,
                    price_source,
                    category_id,
                    category,
                    warehouse_id,
                    qty,
                    reserved_qty,
                    available_qty,
                    minimum_stock
                    """
                )
            )

            # ------------------------------------------------------------------
            # WAREHOUSE
            # ------------------------------------------------------------------

            if warehouse_id is not None:

                query = query.eq(
                    "warehouse_id",
                    int(warehouse_id),
                )

            # ------------------------------------------------------------------
            # SEARCH
            # ------------------------------------------------------------------

            if keyword:

                keyword = str(
                    keyword
                ).strip()

                if keyword:

                    safe_keyword = (
                        keyword
                        .replace(",", " ")
                    )

                    query = query.or_(
                        f"name.ilike.%{safe_keyword}%,"
                        f"sku.ilike.%{safe_keyword}%,"
                        f"barcode.ilike.%{safe_keyword}%"
                    )

            # ------------------------------------------------------------------
            # ORDER
            # ------------------------------------------------------------------

            query = query.order(
                "id"
            )

            # ------------------------------------------------------------------
            # LIMIT
            # ------------------------------------------------------------------

            result = (
                query
                .limit(
                    int(limit)
                )
                .execute()
            )

            rows = []

            for product in result.data or []:

                rows.append(
                    self._normalize_pos_product(
                        product,
                        warehouse_id,
                    )
                )

            return rows

        except Exception as e:

            log_error(
                message="POS product load failed",
                exception=e,
                payload={
                    "warehouse_id": warehouse_id,
                    "keyword": keyword,
                    "limit": limit,
                },
            )

            return []

    # ==========================================================================
    # NORMALIZE POS PRODUCT
    # ==========================================================================

    @staticmethod
    def _normalize_pos_product(
        product: Dict[str, Any],
        warehouse_id: Optional[int] = None,
    ) -> Dict[str, Any]:

        if not product:

            return {}

        return {

            "id":
                product.get("id"),

            "name":
                product.get("name") or "",

            "sku":
                product.get("sku") or "",

            "barcode":
                product.get("barcode") or "",

            "purchase_price":
                product.get(
                    "purchase_price",
                    0,
                ) or 0,

            "selling_price":
                product.get(
                    "selling_price",
                    0,
                ) or 0,

            "owner_selling_price":
                product.get(
                    "owner_selling_price"
                ),

            "owner_price_locked":
                bool(
                    product.get(
                        "owner_price_locked",
                        False,
                    )
                ),

            "final_selling_price":
                product.get(
                    "final_selling_price",
                    product.get(
                        "selling_price",
                        0,
                    ),
                ) or 0,

            "price_source":
                product.get(
                    "price_source",
                    "SYSTEM",
                ) or "SYSTEM",

            "category_id":
                product.get(
                    "category_id"
                ),

            "category":
                product.get(
                    "category"
                ),

            "warehouse_id":
                product.get(
                    "warehouse_id",
                    warehouse_id,
                ),

            "qty":
                product.get(
                    "qty",
                    0,
                ) or 0,

            "reserved_qty":
                product.get(
                    "reserved_qty",
                    0,
                ) or 0,

            "available_qty":
                product.get(
                    "available_qty",
                    0,
                ) or 0,

            "minimum_stock":
                product.get(
                    "minimum_stock",
                    0,
                ) or 0,

        }

    # ==========================================================================
    # INVENTORY PRODUCTS
    # ==========================================================================

    def get_inventory_products(
        self,
        warehouse_id=None,
        keyword=None,
        limit=100,
    ):

        try:

            query = (
                self.client
                .table(
                    TABLE_WAREHOUSE_STOCK
                )
                .select(
                    """
                    warehouse_id,
                    qty,
                    reserved_qty,
                    available_qty,

                    products(
                        id,
                        name,
                        sku,
                        barcode,
                        purchase_price,
                        selling_price,
                        owner_selling_price,
                        final_selling_price,
                        price_source,
                        owner_price_locked,
                        markup_percent,
                        category_id,
                        minimum_stock,
                        unit,
                        notes,
                        is_active
                    ),

                    warehouses(
                        id,
                        name
                    )
                    """
                )
            )

            # ------------------------------------------------------------------
            # WAREHOUSE
            # ------------------------------------------------------------------

            if warehouse_id is not None:

                query = query.eq(
                    "warehouse_id",
                    int(warehouse_id),
                )

            # ------------------------------------------------------------------
            # QUERY
            # ------------------------------------------------------------------

            result = (
                query
                .limit(
                    int(limit)
                )
                .execute()
            )

            rows = []

            for item in result.data or []:

                product = (
                    item.get("products")
                    or {}
                )

                warehouse = (
                    item.get("warehouses")
                    or {}
                )

                rows.append({

                    "id":
                        product.get("id"),

                    "name":
                        product.get("name"),

                    "sku":
                        product.get("sku"),

                    "barcode":
                        product.get("barcode"),

                    "purchase_price":
                        product.get(
                            "purchase_price",
                            0,
                        ),

                    "selling_price":
                        product.get(
                            "selling_price",
                            0,
                        ),

                    "owner_selling_price":
                        product.get(
                            "owner_selling_price"
                        ),

                    "final_selling_price":
                        product.get(
                            "final_selling_price"
                        ),

                    "price_source":
                        product.get(
                            "price_source"
                        ),

                    "owner_price_locked":
                        product.get(
                            "owner_price_locked",
                            False,
                        ),

                    "markup_percent":
                        product.get(
                            "markup_percent"
                        ),

                    "category_id":
                        product.get(
                            "category_id"
                        ),

                    "minimum_stock":
                        product.get(
                            "minimum_stock",
                            0,
                        ),

                    "unit":
                        product.get(
                            "unit",
                            "pcs",
                        ),

                    "notes":
                        product.get(
                            "notes"
                        ),

                    "is_active":
                        product.get(
                            "is_active",
                            True,
                        ),

                    "warehouse_id":
                        item.get(
                            "warehouse_id"
                        ),

                    "warehouse":
                        warehouse.get(
                            "name"
                        ),

                    "qty":
                        item.get(
                            "qty",
                            0,
                        ),

                    "reserved_qty":
                        item.get(
                            "reserved_qty",
                            0,
                        ),

                    "available_qty":
                        item.get(
                            "available_qty",
                            0,
                        ),

                })

            return rows

        except Exception as e:

            log_error(
                message=
                    "Inventory product load failed",
                exception=e,
            )

            return []

    # ==========================================================================
    # GET PRODUCTS — PRODUCT MASTER + WAREHOUSE STOCK
    # ==========================================================================

    def get_products(
        self,
        warehouse_id: Optional[int] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:

        try:

            # ------------------------------------------------------------------
            # PRODUCT MASTER
            # ------------------------------------------------------------------

            product_result = (

                self.client

                .table(TABLE_PRODUCTS)

                .select(
                    """
                    id,
                    name,
                    sku,
                    barcode,
                    purchase_price,
                    selling_price,
                    owner_selling_price,
                    owner_price_locked,
                    final_selling_price,
                    price_source,
                    category_id,
                    minimum_stock,
                    unit,
                    notes,
                    is_active
                    """
                )

                .order("id")

                .range(
                    int(offset),
                    int(offset) + int(limit) - 1,
                )

                .execute()
            )

            products = product_result.data or []

            if not products:

                return []

            # ------------------------------------------------------------------
            # WAREHOUSE STOCK
            # ------------------------------------------------------------------

            stock_map = {}

            if warehouse_id is not None:

                stock_result = (

                    self.client

                    .table(TABLE_WAREHOUSE_STOCK)

                    .select(
                        """
                        product_id,
                        warehouse_id,
                        qty,
                        reserved_qty,
                        available_qty
                        """
                    )

                    .eq(
                        "warehouse_id",
                        int(warehouse_id),
                    )

                    .execute()
                )

                for stock in stock_result.data or []:

                    product_id = stock.get(
                        "product_id"
                    )

                    if product_id is None:
                        continue

                    stock_map[
                        int(product_id)
                    ] = stock

            # ------------------------------------------------------------------
            # MERGE PRODUCT + STOCK
            # ------------------------------------------------------------------

            rows = []

            for product in products:

                product_id = product.get("id")

                stock = (
                    stock_map.get(
                        int(product_id)
                    )
                    if product_id is not None
                    else None
                )

                stock = stock or {}

                rows.append({

                    # ----------------------------------------------------------
                    # PRODUCT
                    # ----------------------------------------------------------

                    "id":
                        product_id,

                    "name":
                        product.get("name"),

                    "sku":
                        product.get("sku"),

                    "barcode":
                        product.get("barcode"),

                    # ----------------------------------------------------------
                    # COST
                    # ----------------------------------------------------------

                    "purchase_price":
                        product.get(
                            "purchase_price",
                            0,
                        ),

                    # ----------------------------------------------------------
                    # PRICE ENGINE
                    # ----------------------------------------------------------

                    "selling_price":
                        product.get(
                            "selling_price",
                            0,
                        ),

                    "owner_selling_price":
                        product.get(
                            "owner_selling_price"
                        ),

                    "owner_price_locked":
                        product.get(
                            "owner_price_locked",
                            False,
                        ),

                    "final_selling_price":
                        product.get(
                            "final_selling_price",
                            product.get(
                                "selling_price",
                                0,
                            ),
                        ),

                    "price_source":
                        product.get(
                            "price_source",
                            "SYSTEM",
                        ),

                    # ----------------------------------------------------------
                    # CATEGORY
                    # ----------------------------------------------------------

                    "category_id":
                        product.get(
                            "category_id"
                        ),

                    # ----------------------------------------------------------
                    # PRODUCT SETTINGS
                    # ----------------------------------------------------------

                    "minimum_stock":
                        product.get(
                            "minimum_stock",
                            0,
                        ),

                    "unit":
                        product.get(
                            "unit",
                            "pcs",
                        ),

                    "notes":
                        product.get(
                            "notes"
                        ),

                    "is_active":
                        product.get(
                            "is_active",
                            True,
                        ),

                    # ----------------------------------------------------------
                    # WAREHOUSE
                    # ----------------------------------------------------------

                    "warehouse_id":
                        warehouse_id,

                    # ----------------------------------------------------------
                    # STOCK
                    # ----------------------------------------------------------

                    "qty":
                        stock.get(
                            "qty",
                            0,
                        ),

                    "reserved_qty":
                        stock.get(
                            "reserved_qty",
                            0,
                        ),

                    "available_qty":
                        stock.get(
                            "available_qty",
                            0,
                        ),

                })

            return rows

        except Exception as e:

            log_error(
                message=
                    "Product + warehouse stock load failed",
                exception=e,
            )

            return []

    # ==========================================================================
    # GET SINGLE PRODUCT
    # ==========================================================================

    def get_product(
        self,
        product_id: int,
    ) -> Optional[Dict[str, Any]]:

        try:

            result = (
                self.client
                .table(
                    TABLE_PRODUCT_VIEW
                )
                .select("*")
                .eq(
                    "id",
                    int(product_id),
                )
                .maybe_single()
                .execute()
            )

            return result.data

        except Exception as e:

            log_error(
                message=
                    "Product get_product failed",
                exception=e,
            )

            return None

    # ==========================================================================
    # SEARCH PRODUCT
    # ==========================================================================

    def search(
        self,
        keyword: Optional[str] = None,
        warehouse_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:

        try:

            query = (
                self.client
                .table(
                    TABLE_PRODUCT_VIEW
                )
                .select("*")
            )

            if warehouse_id is not None:

                query = query.eq(
                    "warehouse_id",
                    int(warehouse_id),
                )

            if keyword:

                keyword = str(
                    keyword
                ).strip()

                if keyword:

                    query = query.or_(
                        f"name.ilike.%{keyword}%,"
                        f"sku.ilike.%{keyword}%,"
                        f"barcode.ilike.%{keyword}%"
                    )

            result = (
                query
                .execute()
            )

            return result.data or []

        except Exception as e:

            log_error(
                message=
                    "Product search failed",
                exception=e,
            )

            return []

    # ==========================================================================
    # BARCODE LOOKUP
    # ==========================================================================

    def get_by_barcode(
        self,
        barcode: str,
        warehouse_id: Optional[int] = None,
    ):

        try:

            query = (
                self.client
                .table(
                    TABLE_PRODUCT_VIEW
                )
                .select("*")
                .eq(
                    "barcode",
                    barcode,
                )
            )

            if warehouse_id is not None:

                query = query.eq(
                    "warehouse_id",
                    int(warehouse_id),
                )

            result = (
                query
                .maybe_single()
                .execute()
            )

            return result.data

        except Exception as e:

            log_error(
                message=
                    "Barcode lookup failed",
                exception=e,
            )

            return None

    # ==========================================================================
    # SKU LOOKUP
    # ==========================================================================

    def get_by_sku(
        self,
        sku: str,
        warehouse_id: Optional[int] = None,
    ):

        try:

            query = (
                self.client
                .table(
                    TABLE_PRODUCT_VIEW
                )
                .select("*")
                .eq(
                    "sku",
                    sku,
                )
            )

            if warehouse_id is not None:

                query = query.eq(
                    "warehouse_id",
                    int(warehouse_id),
                )

            result = (
                query
                .maybe_single()
                .execute()
            )

            return result.data

        except Exception as e:

            log_error(
                message=
                    "SKU lookup failed",
                exception=e,
            )

            return None


# ==============================================================================
# PUBLIC
# ==============================================================================

__all__ = [
    "ProductRepository",
]
