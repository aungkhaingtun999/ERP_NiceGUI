import streamlit as st

def init_pos_cache(supabase_client):
    """
    POS အတွက် Product စာရင်းကို Session State ထဲတွင် Cache လုပ်ပေးသော Function
    """
    if 'products_cache' not in st.session_state:
        st.session_state.products_cache = fetch_products_from_supabase(supabase_client)

def fetch_products_from_supabase(supabase_client):
    """
    Supabase Database မှ active ဖြစ်သော Product များကို ဆွဲထုတ်ခြင်း
    """
    try:
        response = supabase_client.table('products').select("*").eq('is_active', True).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Database မှ Data ဆွဲထုတ်ရာတွင် အမှားအယွင်းရှိပါသည်: {e}")
        return []

def render_pos_sync_sidebar(supabase_client):
    """
    POS မျက်နှာပြင်၏ Sidebar တွင် ထည့်သွင်းရန် Sync / Refresh Control Panel
    """
    with st.sidebar:
        st.subheader("⚙️ POS Control Panel")
        st.write("အရောင်းအဝယ်များ ပြီးဆုံးမှသာ Product စာရင်းကို အသစ်လုပ်ပါ။")
        
        if st.button("🔄 Sync / Refresh Products", type="primary"):
            with st.spinner("Product စာရင်းများကို Database မှ ဆွဲယူနေပါသည်..."):
                # Database မှ Data အသစ်ကို တန်းဆွဲပြီး Session State ကို အစားထိုးမည်
                st.session_state.products_cache = fetch_products_from_supabase(supabase_client)
            st.success("Product စာရင်း အသစ်ဖြစ်သွားပါပြီ!")
            st.rerun()

def get_cached_products(supabase_client):
    """
    POS မျက်နှာပြင်မှ Product များကို ယူသုံးရန် Main Function
    """
    init_pos_cache(supabase_client)
    return st.session_state.products_cache
