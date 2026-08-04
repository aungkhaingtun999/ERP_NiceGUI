import os
import streamlit.components.v1 as components


COMPONENT_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../erp_components/zxing_scanner/frontend"
    )
)


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
