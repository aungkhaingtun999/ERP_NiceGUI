# ==============================================================================
# SAFE PAGE LOADER
# ==============================================================================

def load_page(page_id):

    # --------------------------------------------------------------------------
    # PAGE FILE PATH
    # --------------------------------------------------------------------------
    page_folder = os.path.join(
        BASE_DIR,
        'erp_pages'
    )

    file_path = os.path.join(
        page_folder,
        f'{page_id}.py'
    )

    # --------------------------------------------------------------------------
    # FILE EXISTS CHECK
    # --------------------------------------------------------------------------
    if not os.path.exists(file_path):

        st.error(
            f'Page file not found:\n{file_path}'
        )

        return

    try:

        # ----------------------------------------------------------------------
        # MODULE NAME
        # ----------------------------------------------------------------------
        module_name = f'erp_pages.{page_id}'

        # ----------------------------------------------------------------------
        # LOAD MODULE
        # ----------------------------------------------------------------------
        spec = importlib.util.spec_from_file_location(
            module_name,
            file_path
        )

        if spec is None:

            raise ImportError(
                f'Cannot load {module_name}'
            )

        module = importlib.util.module_from_spec(spec)

        sys.modules[module_name] = module

        spec.loader.exec_module(module)

        # ----------------------------------------------------------------------
        # IMPORTANT
        # ----------------------------------------------------------------------
        # DO NOT CALL module.run() HERE
        #
        # 1_POS.py already executes run() itself.
        # Calling run() again here causes duplicate Streamlit widgets.
        # ----------------------------------------------------------------------

        return

    except Exception as e:

        st.error(
            f'Page Load Error : {e}'
        )

        with st.expander('Debug Trace'):

            st.exception(e)
