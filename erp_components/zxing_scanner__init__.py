import os

import streamlit.components.v1 as components


_component = components.declare_component(

    "zxing_scanner",

    path=os.path.join(

        os.path.dirname(__file__),

        "frontend"

    )

)



def zxing_scanner(
    key=None
):

    return _component(

        key=key,

        default=""

    )