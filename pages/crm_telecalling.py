import streamlit as st
from datetime import datetime
import pandas as pd

# பக்கத்தின் தலைப்பு மற்றும் அமைப்பு
st.set_page_config(page_title="CRM & டெலிகாலிங் மேசை", page_icon="📞", layout="wide")

st.subheader("📞 CRM, மார்க்கெட்டிங் லீடுகள் மற்றும் டெலிகாலிங் மேசை")
st.caption("மார்க்கெட்டிங் லீடுகள் பதிவேற்றம், டெலிகாலர் பின்தொடர்தல் மற்றும் கிளைகளுக்கு லீடு ஒதுக்கீடு செய்யும் பகுதி.")

# Supabase இணைப்புக் குறிப்பு (மெயின் ஆப்பில் உள்ள அதே supabase இன்ஸ்டன்ஸைப் பயன்படுத்தலாம்)
# ஒருவேளை மெயின் ஆப்பிலிருந்து இம்போர்ட் செய்ய வேண்டுமெனில்: from app import supabase
# (அல்லது உங்கள் ஒரிஜினல் கோடில் உள்ள supabase கனெக்ஷனை இங்கே இணைக்கவும்)
try:
    from app import supabase
except ImportError:
    # ஒருவேளை app.py-லிருந்து எடுக்க முடியவில்லை எனில், இங்கு உங்களது supabase கனெக்ஷனை அமைக்கலாம்
    pass

# 4 பிரிவுகளாக (Tabs) பிரித்தல்
crm_tab1, crm_tab2, crm_tab3, crm_tab4 = st.tabs([
    "📂 மார்க்கெட்டிங் லீடுகள் (Excel Upload)",
    "🎧 டெலிகாலிங் டெஸ்க் (Telecalling Desk)",
    "🏢 கிளை லீடுகள் மேலாண்மை (Branch Leads)",
    "📊 அட்மின் கண்காணிப்பு (Analytics)"
])

# -------------------------------------------------------------
# டேப் 1: மார்க்கெட்டிங் லீடுகள் எக்செல் மூலம் Bulk Upload செய்தல்
# -------------------------------------------------------------
with crm_tab1:
    st.markdown("##### 📂 மார்க்கெட்டிங் லீடுகள் எக்செல் / CSV பதிவேற்றம்")
    uploaded_excel = st.file_uploader("எக்செல் கோப்பைத் தேர்ந்தெடுக்கவும் (.xlsx, .csv)", type=["xlsx", "csv"], key="crm_file_up")
    
    if uploaded_excel is not None:
        try:
            df_upload = pd.read_excel(uploaded_excel) if uploaded_excel.name.endswith('.xlsx') else pd.read_csv(uploaded_excel)
            st.write("📋 **முன்னோட்டத் தரவுகள் (Preview):**", df_upload.head())
            
            if st.button("🚀 லீடுகளை டேட்டாபேஸில் பதிவேற்று", type="primary", key="btn_upload_leads"):
                success_count = 0
                for _, row in df_upload.iterrows():
                    lead_data = {
                        "customer_name": str(row.get("Name", row.get("Customer Name", ""))),
                        "phone": str(row.get("Phone", row.get("Mobile", ""))),
                        "address": str(row.get("Address", "")),
                        "city": str(row.get("City", row.get("Place", ""))),
                        "status": "New",
                        "telecaller_name": st.session_state.get("username", "Admin")
                    }
                    supabase.table("leads").insert(lead_data).execute()
                    success_count += 1
                st.success(f"🎉 வெற்றிகரமாக {success_count} லீடுகள் டேட்டாபேஸில் சேர்க்கப்பட்டன!")
        except Exception as e:
            st.error(f"கோப்பைப் படிப்பதில் பிழை: {e}")

# -------------------------------------------------------------
# டேப் 2: டெலிகாலிங் டெஸ்க் (Telecaller Desk & 5 Status Updates)
# -------------------------------------------------------------
with crm_tab2:
    st.markdown("##### 🎧 டெலிகாலிங் பின்தொடர்தல் மேசை")
    
    try:
        leads_res = supabase.table("leads").select("*").in_("status", ["New", "Future Lead", "Not Reachable"]).order("id", desc=True).execute()
        active_leads = leads_res.data or []
    except Exception:
        active_leads = []

    if not active_leads:
        st.info("✅ தற்பொழுது தொடர்புகொள்ள வேண்டிய லீடுகள் எதுவும் நிலுவையில் இல்லை.")
    else:
        selected_lead_id = st.selectbox(
            "விவரம் பார்க்க வேண்டிய லீட்டைத் தேர்ந்தெடுக்கவும்:", 
            [l['id'] for l in active_leads], 
            format_func=lambda x: next((f"{l['customer_name']} - {l['phone']} ({l['city']})" for l in active_leads if l['id'] == x), ""),
            key="crm_lead_select"
        )
        
        curr_lead = next((l for l in active_leads if l['id'] == selected_lead_id), None)
        
        if curr_lead:
            col_l1, col_l2 = st.columns(2)
            with col_l1:
                st.write(f"• **பெயர்:** `{curr_lead.get('customer_name')}`")
                st.write(f"• **தொலைபேசி:** 📞 `{curr_lead.get('phone')}`")
                st.write(f"• **ஊர்/முகவரி:** {curr_lead.get('city')} / {curr_lead.get('address')}")
            with col_l2:
                st.write(f"• **தற்போதைய நிலை:** `{curr_lead.get('status')}`")
                st.write(f"• **முந்தைய குறிப்புகள்:** {curr_lead.get('remarks', '-')}")

            st.markdown("---")
            st.markdown("##### ✍️ வாடிக்கையாளரிடம் பேசிய பின் நிலையை மாற்றுக:")
            
            new_status = st.selectbox("நிலை (Status):", [
                "Future Lead (எதிர்கால லீடு)", 
                "Immediate Lead (உடனடி லீடு - கிளைக்கு அனுப்பு)", 
                "Not Interested (ஆர்வம் இல்லை)", 
                "Not Reachable (தொடர்புகொள்ள முடியவில்லை)", 
                "Wrong Number (தவறான எண்)"
            ], key="crm_status_sel")

            try:
                b_res = supabase.table("branches").select("id, branch_name").execute()
                branch_map = {b['branch_name']: b['id'] for b in (b_res.data or [])}
            except Exception:
                branch_map = {}

            target_branch_id = None
            follow_date = None

            if "Immediate Lead" in new_status:
                if branch_map:
                    selected_branch_name = st.selectbox("அருகிலுள்ள கிளையைத் தேர்ந்தெடுக்கவும்:", list(branch_map.keys()), key="crm_branch_sel")
                    target_branch_id = branch_map.get(selected_branch_name)
                else:
                    st.warning("கிளைகள் விவரம் கிடைக்கவில்லை.")
            elif "Future Lead" in new_status:
                follow_date = st.date_input("மீண்டும் பேச வேண்டிய தேதி:", key="crm_follow_date")

            call_remarks = st.text_area("பேசிய விவர குறிப்புகள் (Remarks):", key="crm_call_rem")

            if st.button("💾 டெலிகாலிங் அப்டேட்டைச் சேமி", type="primary", key="btn_save_crm_update"):
                try:
                    clean_status = new_status.split(" ")[0] + (" " + new_status.split(" ")[1] if "Future" in new_status or "Immediate" in new_status or "Not" in new_status else "")
                    update_payload = {
                        "status": clean_status,
                        "remarks": call_remarks,
                        "assigned_branch_id": target_branch_id,
                        "followup_date": str(follow_date) if follow_date else None
                    }
                    supabase.table("leads").update(update_payload).eq("id", curr_lead['id']).execute()
                    st.success("✅ லீடு நிலை வெற்றிகரமாக அப்டேட் செய்யப்பட்டது!")
                    st.rerun()
                except Exception as e:
                    st.error(f"அப்டேட் செய்வதில் பிழை: {e}")

# -------------------------------------------------------------
# டேப் 3: கிளை லீடுகள் மேலாண்மை (Branch Desk)
# -------------------------------------------------------------
with crm_tab3:
    st.markdown("##### 🏢 கிளை லீடுகள் & வணிக மாற்றம் (Branch Manager Desk)")
    user_branch_id = st.session_state.get("branch_id")
    
    try:
        b_leads_res = supabase.table("leads").select("*").eq("assigned_branch_id", user_branch_id).execute()
        b_leads = b_leads_res.data or []
    except Exception:
        b_leads = []

    if not b_leads:
        st.info("📭 தங்களது கிளைக்கு ஒதுக்கப்பட்ட உடனடி லீடுகள் எதுவும் இல்லை.")
    else:
        st.dataframe(pd.DataFrame(b_leads)[["id", "customer_name", "phone", "city", "status", "remarks"]], use_container_width=True)

# -------------------------------------------------------------
# டேப் 4: அட்மின் கண்காணிப்பு (Admin Analytics)
# -------------------------------------------------------------
with crm_tab4:
    st.markdown("##### 📊 அட்மின் கண்காணிப்பு மற்றும் செயல்திறன் அறிக்கை")
    st.info("📈 டெலிகாலர்களின் தினசரி அழைப்புகள் மற்றும் கிளைகளின் லீடு செயல்பாடுகள் குறித்த முழுமையான புள்ளிவிவரங்கள்.")