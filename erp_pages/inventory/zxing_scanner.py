import streamlit.components.v1 as components
import os


_RELEASE = True


if _RELEASE:

    _component_func = components.declare_component(
        "zxing_scanner",
        path=os.path.join(
            os.path.dirname(__file__),
            "frontend"
        )
    )

else:

    _component_func = components.declare_component(
        "zxing_scanner",
        url="http://localhost:3001"
    )


def zxing_scanner():

    return _component_func(
        default="",
        key="zxing_scanner"
    )
