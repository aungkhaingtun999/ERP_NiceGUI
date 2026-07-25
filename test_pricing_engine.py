# ==============================================================================
# test_pricing_engine.py
# ERP PRICING ENGINE TEST
# ==============================================================================


from supabase_client import supabase

from erp_core.services.pricing_service import (
    PricingService
)



def test_pricing():

    pricing = PricingService(
        supabase
    )


    result = pricing.calculate_selling_price(

        cost=10000,

        product_id=15

    )


    print("\n========== PRICING RESULT ==========")

    print(
        "Cost:",
        result["cost"]
    )

    print(
        "Markup:",
        result["markup"]
    )

    print(
        "Selling Price:",
        result["selling_price"]
    )

    print(
        "Source:",
        result["source"]
    )



if __name__ == "__main__":

    test_pricing()