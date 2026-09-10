try:
    test_res = supabase.table("branches").select("*").limit(1).execute()
    st.success("✅ Supabase டேட்டாபேஸ் இணைப்பு வெற்றிகரமாக உள்ளது!")
except Exception as e:
    st.error(f"❌ இணைப்புப் பிழை: {e}")
