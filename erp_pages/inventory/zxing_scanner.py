import os
import streamlit.components.v1 as components


CURRENT = os.path.abspath(__file__)

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../.."
    )
)


FRONTEND = os.path.join(
    PROJECT_ROOT,
    "erp_components",
    "zxing_scanner",
    "frontend"
)


print("==========================")
print("CURRENT FILE:")
print(CURRENT)

print("PROJECT ROOT:")
print(PROJECT_ROOT)

print("FRONTEND PATH:")
print(FRONTEND)

print("FRONTEND EXISTS:")
print(os.path.exists(FRONTEND))

print("INDEX EXISTS:")
print(
    os.path.exists(
        os.path.join(FRONTEND, "index.html")
    )
)

print("MAIN EXISTS:")
print(
    os.path.exists(
        os.path.join(FRONTEND, "main.js")
    )
)
print("==========================")


zxing_component = components.declare_component(
    "zxing_scanner",
    path=FRONTEND
)


def zxing_scanner():

    return zxing_component(
        key="zxing_scanner",
        default="",
        height=450
    )
