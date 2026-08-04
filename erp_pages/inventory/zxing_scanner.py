import os
import streamlit.components.v1 as components


CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


COMPONENT_PATH = os.path.abspath(
    os.path.join(
        CURRENT_DIR,
        "../../erp_components/zxing_scanner/frontend"
    )
)


print("ZXING PATH:", COMPONENT_PATH)


zxing_component = components.declare_component(
    "zxing_scanner",
    path=COMPONENT_PATH
)


def zxing_scanner():

    return zxing_component(
        key="zxing_scanner",
        default="",
        height=450
    )
