import os

import streamlit.components.v1 as components


# Production / Streamlit Cloud
_RELEASE = True



if _RELEASE:

    _component_func = components.declare_component(

        "zxing_barcode",

        path=os.path.join(
            os.path.dirname(__file__),
            "frontend"
        )

    )


else:

    _component_func = components.declare_component(

        "zxing_barcode",

        url="http://localhost:3001"

    )



def zxing_scanner(key=None):

    return _component_func(
        key=key,
        default=""
    )
