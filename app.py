import streamlit as st
from supabase import create_client

# Supabase இணைப்பு விவரங்கள்
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# இப்போது சோதனைக் குறியீட்டை இயக்கவும்
try:
    test_res = supabase.table("branches").select("*").limit(1).execute()
    st.success("✅ Supabase டேட்டாபேஸ் இணைப்பு வெற்றிகரமாக உள்ளது!")
except Exception as e:
    st.error(f"❌ இணைப்புப் பிழை: {e}")
