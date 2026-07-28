import sys
import os


# Add project root to python path

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)


from erp_core.services.inventory_service import InventoryService
