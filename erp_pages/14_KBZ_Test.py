from erp_core.payments.kbz_crc_tool import KBZCRCTool
import streamlit as st


st.divider()

st.subheader('🧪 CRC Sample Analyzer')


default_samples = '''hQZLQlpQYXlhPE8C8FACEFcWCSZ3cjZ9JggQEB+fCAQBAZ8kAzEuMA==F+19fbc3e3e34
hQZLQlpQYXlhPE8C8FACEFcWCSZ3cjZ9JggQEB+fCAQBAZ8kAzIuMA==FJ19fbc3ea850=
hQZLQlpQYXlhPE8C8FACEFcWCSZ3cjZ9JggQEB+fCAQBAZ8kAzMuMA==FS19fbc3ef275
hQZLQlpQYXlhQE8C8FACEFcWCSZ3cjZ9JggQEB+fCAQBAZ8kBTEwMC4wFJ19fbc378385=
hQZLQlpQYXlhQE8C8FACEFcWCSZ3cjZ9JggQEB+fCAQBAZ8kBTIwMC4wFG19fbc37ec19
hQZLQlpQYXlhQE8C8FACEFcWCSZ3cjZ9JggQEB+fCAQBAZ8kBTMwMC4wF719fbc383618='''


sample_text = st.text_area(
    'Paste KBZ QR samples (one per line)',
    value=default_samples,
    height=220,
    key='crc_samples'
)


if st.button('Analyze CRC Samples', key='crc_btn'):


    samples = [

        x.strip()

        for x in sample_text.splitlines()

        if x.strip()

    ]


    result = KBZCRCTool.analyze_samples(samples)


    st.write(result)
if __name__ == "__main__":
    run()
