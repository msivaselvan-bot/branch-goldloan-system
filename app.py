from datetime import datetime
import random
import requests
import pandas as pd
import streamlit as st
from supabase import Client, create_client

# பக்க வடிவமைப்பு - முழு அகலம் மற்றும் கச்சிதமான மார்ஜின்
st.set_page_config(page_title="Branch Operations System", layout="wide", initial_sidebar_state="collapsed")

# CSS மூலம் தேவையற்ற அதிகப்படியான இடைவெளிகளைக் குறைத்தல் (Zero Scroll Optimization)
st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 1rem; padding-left: 1.5rem; padding-right: 1.5rem; }
    div[data-testid="stMetricValue"] { font-size: 1.3rem; }
    .stTextInput>div>div>input, .stNumberInput>div>div>input { padding: 4px 8px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. Supabase இணைப்பு
# ==========================================
@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

try:
    supabase = get_supabase_client()
except Exception as e:
    st.error(f"டேட்டாபேஸ் இணைப்பு பிழை: {e}")
    st.stop()

# ==========================================
# 2. ஆவணப் பதிவேற்றம், வருகை எண் & SMS செயல்பாடுகள்
# ==========================================
def upload_files_to_supabase(files, visit_no):
    uploaded_links = []
    bucket_name = "branch-documents"
    for f in files:
        file_path = f"{visit_no}/{f.name}"
        supabase.storage.from_(bucket_name).upload(
            path=file_path,
            file=f.getvalue(),
            file_options={"content-type": f.type, "upsert": "true"},
        )
        public_url = supabase.storage.from_(bucket_name).get_public_url(file_path)
        uploaded_links.append(public_url)
    return uploaded_links

def generate_short_visit_no() -> str:
    try:
        res = supabase.table("customer_visits").select("visit_no").order("id", desc=True).limit(1).execute()
        if res.data and res.data[0].get("visit_no"):
            last_no = res.data[0]["visit_no"]
            if last_no.startswith("VST-"):
                num_part = last_no.split("-")[1]
                next_val = int(num_part) + 1
                return f"VST-{next_val:04d}"
        return "VST-1001"
    except Exception:
        return f"VST-{datetime.now().strftime('%M%S')}"

def send_fast2sms_otp(mobile_no: str, otp_code: str):
    try:
        api_key = "eBGQYanRZNKVCpMSg3KB5kUxY2QhDnOjxesh3Hqr7FOG792XV9wut4TPhQia"
        if "sms" in st.secrets and "fast2sms_api_key" in st.secrets["sms"]:
            api_key = st.secrets["sms"]["fast2sms_api_key"]

        clean_mobile = "".join(filter(str.isdigit, str(mobile_no)))[-10:]
        url = "https://www.fast2sms.com/dev/bulkV2"
        headers = {"authorization": api_key.strip(), "Content-Type": "application/json"}

        params_dlt = {
            "route": "dlt",
            "sender_id": "MTHSEG",
            "message": "219823",
            "variables_values": str(otp_code),
            "numbers": clean_mobile,
            "flash": "0"
        }
        resp = requests.get(url, headers=headers, params=params_dlt, timeout=8)
        res_json = resp.json()
        if res_json.get("return") is True:
            return True, "SMS அனுப்பப்பட்டது!"

        params_otp = {"route": "otp", "variables_values": str(otp_code), "numbers": clean_mobile}
        resp_fallback = requests.get(url, headers=headers, params=params_otp, timeout=8)
        fallback_json = resp_fallback.json()
        if fallback_json.get("return") is True:
            return True, "SMS அனுப்பப்பட்டது!"

        err_msg = res_json.get("message") or fallback_json.get("message") or str(res_json)
        return False, str(err_msg)
    except Exception as e:
        return False, f"பிழை: {e}"

# ==========================================
# 3. தற்காலிக சேமிப்பக மாறிகள்
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.branch = None
    st.session_state.branch_id = None
    st.session_state.username = None

if "current_visit" not in st.session_state:
    st.session_state.current_visit = None

if "transactions_cart" not in st.session_state:
    st.session_state.transactions_cart = []

branches_res = supabase.table("branches").select("*").order("id").execute()
branch_options = {b["branch_name"]: b["id"] for b in branches_res.data} if branches_res.data else {}
branch_id_to_name = {b["id"]: b["branch_name"] for b in branches_res.data} if branches_res.data else {}

# ==========================================
# 4. உள்நுழைவு திரை
# ==========================================
if not st.session_state.logged_in:
    col_left, col_center, col_right = st.columns([1.5, 1.2, 1.5])
    with col_center:
        st.markdown("<h3 style='text-align: center;'>🏦 கிளை சிஸ்டம்</h3>", unsafe_allow_html=True)
        st.caption("<p style='text-align: center;'>பணியாளர் உள்நுழைவு</p>", unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("பயனர் பெயர் (Username)", placeholder="Username")
            password = st.text_input("கடவுச்சொல் (Password)", type="password", placeholder="Password")
            submitted = st.form_submit_button("உள்நுழைக (Login)", use_container_width=True)

            if submitted:
                if username.strip() and password.strip():
                    user_query = supabase.table("users").select("id, name, username, role, branch_id, is_active, branches(branch_name)").eq("username", username.strip()).eq("password_hash", password.strip()).eq("is_active", True).execute()
                    if user_query.data:
                        user_info = user_query.data[0]
                        role = user_info["role"]
                        b_id = user_info.get("branch_id")
                        b_name = "Head Office / Admin" if role in ["Admin", "Auditor"] else (user_info.get("branches", {}).get("branch_name") if user_info.get("branches") else "ஒதுக்கப்படாத கிளை")
                        st.session_state.logged_in = True
                        st.session_state.user_role = role
                        st.session_state.branch = b_name
                        st.session_state.branch_id = b_id
                        st.session_state.username = user_info["name"]
                        st.rerun()
                    else:
                        st.error("தவறான உள்நுழைவு விவரங்கள்!")
                else:
                    st.warning("விவரங்களை உள்ளிடவும்.")

# ==========================================
# 5. முதன்மை திரை
# ==========================================
else:
    top_col1, top_col2, top_col3 = st.columns([4, 3, 1])
    with top_col1:
        st.write(f"🏢 **{st.session_state.branch}** | 👤 **{st.session_state.username}** ({st.session_state.user_role})")
    with top_col3:
        if st.button("வெளியேறு (Logout)", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.current_visit = None
            st.session_state.transactions_cart = []
            st.rerun()

    st.markdown("---")

    # ----------------------------------------------------
    # A. நிர்வாக மேலாண்மை திரை (ADMIN PANEL)
    # ----------------------------------------------------
    if st.session_state.user_role == "Admin":
        st.header("⚙️ நிர்வாக மேலாண்மை (Admin Control Panel)")
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🏢 கிளைகள்",
            "👥 பணியாளர்கள்",
            "📥 மொத்தப் பதிவேற்றம்",
            "🗂️ வாடிக்கையாளர் மேலாண்மை",
            "📊 பரிவர்த்தனை திருத்தம் & நீக்கம் (Transactions/Visits)"
        ])

        with tab1:
            st.subheader("➕ புதிய கிளை சேர்த்தல்")
            with st.form("admin_add_branch_form", clear_on_submit=True):
                b_col1, b_col2 = st.columns(2)
                b_name = b_col1.text_input("கிளையின் பெயர்")
                b_code = b_col2.text_input("கிளை குறியீடு (Branch Code)")
                if st.form_submit_button("கிளையைச் சேர்"):
                    if b_name.strip() and b_code.strip():
                        supabase.table("branches").insert({"branch_name": b_name.strip(), "branch_code": b_code.strip().upper()}).execute()
                        st.success("கிளை சேர்க்கப்பட்டது!")
                        st.rerun()

            b_list_res = supabase.table("branches").select("id, branch_name, branch_code").order("id").execute()
            if b_list_res.data:
                st.dataframe(pd.DataFrame(b_list_res.data), use_container_width=True)

        with tab2:
            st.subheader("👥 பணியாளர்கள் மேலாண்மை")
            users_res = supabase.table("users").select("id, name, username, role, branch_id, is_active").order("id").execute()
            if users_res.data:
                u_data = [{"ID": u["id"], "பெயர்": u["name"], "Username": u["username"], "Role": u["role"], "கிளை": branch_id_to_name.get(u.get("branch_id"), "Admin"), "நிலை": "🟢" if u.get("is_active") else "🔴"} for u in users_res.data]
                st.dataframe(pd.DataFrame(u_data), use_container_width=True)

            sub_col1, sub_col2 = st.columns(2)
            with sub_col1:
                with st.form("admin_add_user_form", clear_on_submit=True):
                    st.write("**➕ புதிய பணியாளர்**")
                    u_name = st.text_input("பெயர்")
                    u_username = st.text_input("Username")
                    u_pass = st.text_input("கடவுச்சொல்", type="password")
                    u_role = st.selectbox("Role", ["Branch Head / Cashier", "Staff", "Auditor", "Admin"])
                    b_sel = st.selectbox("கிளை", list(branch_options.keys()))
                    if st.form_submit_button("உருவாக்கு"):
                        supabase.table("users").insert({
                            "name": u_name.strip(), "username": u_username.strip(), "password_hash": u_pass.strip(),
                            "role": u_role, "branch_id": branch_options.get(b_sel) if u_role not in ["Admin", "Auditor"] else None,
                            "is_active": True
                        }).execute()
                        st.success("பணியாளர் சேர்க்கப்பட்டார்!")
                        st.rerun()

            with sub_col2:
                if users_res.data:
                    u_dict = {f"{u['name']} (@{u['username']})": u for u in users_res.data}
                    sel_u = st.selectbox("திருத்த வேண்டிய பணியாளர்", list(u_dict.keys()))
                    target_u = u_dict[sel_u]
                    with st.form("admin_edit_user_form"):
                        ed_name = st.text_input("பெயர்", value=target_u["name"])
                        ed_pass = st.text_input("புதிய கடவுச்சொல் (விருப்பப்பட்டால்)", type="password")
                        ed_role = st.selectbox("Role", ["Branch Head / Cashier", "Staff", "Auditor", "Admin"], index=["Branch Head / Cashier", "Staff", "Auditor", "Admin"].index(target_u["role"]))
                        ed_stat = st.radio("நிலை", ["Active", "Inactive"], index=0 if target_u.get("is_active") else 1)
                        if st.form_submit_button("புதுப்பி"):
                            pl = {"name": ed_name.strip(), "role": ed_role, "is_active": (ed_stat == "Active")}
                            if ed_pass.strip(): pl["password_hash"] = ed_pass.strip()
                            supabase.table("users").update(pl).eq("id", target_u["id"]).execute()
                            st.success("புதுப்பிக்கப்பட்டது!")
                            st.rerun()

        with tab3:
            st.subheader("📥 பழைய வாடிக்கையாளர் அறிக்கைப் பதிவேற்றம்")
            uploaded_cust_file = st.file_uploader("கோப்பைத் தேர்வு செய்க (xls, xlsx, csv)", type=["xls", "xlsx", "csv"])
            if uploaded_cust_file:
                df_raw = pd.read_csv(uploaded_cust_file, skiprows=2) if uploaded_cust_file.name.endswith(".csv") else pd.read_excel(uploaded_cust_file, skiprows=2)
                df_cust = df_raw.dropna(subset=["Full Name", "Mobile No"]).copy()
                st.write(f"மொத்தம் கண்டறியப்பட்டவை: **{len(df_cust)}**")
                if st.button("டேட்டாபேஸில் மொத்தமாக இணை (Start Bulk Upload)", type="primary"):
                    all_b = supabase.table("branches").select("id, branch_code").execute()
                    b_code_to_id = {b["branch_code"].strip().upper(): b["id"] for b in all_b.data} if all_b.data else {}
                    recs, seen = [], set()
                    for idx, row in df_cust.iterrows():
                        b_code = str(row.get("Branch", "")).strip().upper()
                        raw_c = str(row.get("Customer No", "")).replace(".0", "").strip()
                        c_code = f"{b_code}-0-{idx+1}" if not raw_c or raw_c in ["0", "nan"] else f"{b_code}-{raw_c}"
                        if c_code in seen: c_code = f"{c_code}-{idx+1}"
                        seen.add(c_code)
                        mob2 = str(row.get("Secondary No", "")).replace(".0", "").strip() if pd.notna(row.get("Secondary No")) else ""
                        recs.append({
                            "branch_id": b_code_to_id.get(b_code),
                            "customer_code": c_code,
                            "name": str(row.get("Full Name", "")).strip(),
                            "guardian_name": str(row.get("Guardian", "")).strip() if pd.notna(row.get("Guardian")) else "",
                            "gender": str(row.get("Gender", "Male")).strip(),
                            "mobile": str(row.get("Mobile No", "")).replace(".0", "").strip(),
                            "mobile2": mob2,
                            "address": str(row.get("Comm Address", "")).strip() if pd.notna(row.get("Comm Address")) else "",
                            "is_active": True
                        })
                    for i in range(0, len(recs), 100):
                        supabase.table("customers").upsert(recs[i:i+100], on_conflict="customer_code").execute()
                    st.success("அனைத்து வாடிக்கையாளர்களும் வெற்றிகரமாகப் பதிவேற்றப்பட்டனர்!")
                    st.rerun()

        with tab4:
            st.subheader("🗂️ வாடிக்கையாளர் பட்டியல் & திருத்தம்")
            f_col1, f_col2 = st.columns([1, 2])
            b_filt = f_col1.selectbox("கிளை வடிகட்டல்", ["அனைத்தும்"] + list(branch_options.keys()))
            c_srch = f_col2.text_input("வாடிக்கையாளர் பெயர் / மொபைல் / எண் தேடுக:")
            cq = supabase.table("customers").select("*").order("id", desc=True)
            if b_filt != "அனைத்தும்": cq = cq.eq("branch_id", branch_options[b_filt])
            if c_srch.strip(): cq = cq.or_(f"name.ilike.%{c_srch.strip()}%,mobile.ilike.%{c_srch.strip()}%,customer_code.ilike.%{c_srch.strip()}%")
            else: cq = cq.limit(100)
            res_c = cq.execute().data or []
            if res_c:
                st.dataframe(pd.DataFrame([{"ID": c["id"], "Code": c["customer_code"], "பெயர்": c["name"], "மொபைல்": c["mobile"], "கிளை": branch_id_to_name.get(c["branch_id"]), "நிலை": "Active" if c.get("is_active") else "Inactive"} for c in res_c]), use_container_width=True)
                target_c = st.selectbox("திருத்த வேண்டிய வாடிக்கையாளர்", res_c, format_func=lambda x: f"{x.get('customer_code')} - {x['name']} ({x.get('mobile')})")
                with st.form("edit_c_form"):
                    e1, e2, e3 = st.columns(3)
                    en = e1.text_input("பெயர்", value=target_c["name"])
                    em = e2.text_input("மொபைல்", value=target_c["mobile"])
                    es = e3.radio("நிலை", ["Active", "Inactive"], index=0 if target_c.get("is_active") else 1)
                    if st.form_submit_button("சேமி"):
                        supabase.table("customers").update({"name": en.strip(), "mobile": em.strip(), "is_active": (es == "Active")}).eq("id", target_c["id"]).execute()
                        st.success("புதுப்பிக்கப்பட்டது!")
                        st.rerun()

        # ==========================================
        # Tab 5: அட்மின் பரிவர்த்தனைகள் திருத்தம் & நீக்கம் (Admin Edit & Delete)
        # ==========================================
        with tab5:
            st.subheader("📊 பரிவர்த்தனை & வருகை மேலாண்மை (Edit / Delete Visits & Transactions)")
            v_srch = st.text_input("தேடுக (வருகை எண் / வாடிக்கையாளர் ID):", placeholder="எ.கா: VST-1001", key="adm_v_srch")
            vq = supabase.table("customer_visits").select("*, customers(name, mobile), branches(branch_name), transactions(*)").order("id", desc=True)
            if v_srch.strip():
                vq = vq.ilike("visit_no", f"%{v_srch.strip()}%")
            else:
                vq = vq.limit(30)
            v_list = vq.execute().data or []

            if v_list:
                for v in v_list:
                    c_name = v.get("customers", {}).get("name", "Unknown") if v.get("customers") else "Unknown"
                    b_n = v.get("branches", {}).get("branch_name", "-") if v.get("branches") else "-"
                    with st.expander(f"📌 வருகை: {v['visit_no']} | வாடிக்கையாளர்: {c_name} | கிளை: {b_n} | நிகர ரொக்கம்: ₹{v['net_cash_amount']:,.2f} ({v['status']})"):
                        st.write(f"**தேதி/நேரம்:** {v['created_at']} | **பட்டுவாடா:** ₹{v['total_paid']} | **வரவு:** ₹{v['total_received']}")
                        
                        txns = v.get("transactions", [])
                        if txns:
                            st.dataframe(pd.DataFrame(txns)[["id", "transaction_type", "staff_name", "paid_amount", "received_amount", "remarks"]], use_container_width=True)

                        col_act1, col_act2 = st.columns([1, 1])
                        with col_act1:
                            with st.form(f"edit_visit_form_{v['id']}"):
                                st.write("**✏️ வருகை விவரங்களைத் திருத்துதல்:**")
                                new_stat = st.selectbox("நிலை (Status)", ["Submitted_to_Auditor", "Approved", "Needs_Clarification", "Cancelled"], index=["Submitted_to_Auditor", "Approved", "Needs_Clarification", "Cancelled"].index(v["status"]) if v["status"] in ["Submitted_to_Auditor", "Approved", "Needs_Clarification", "Cancelled"] else 0)
                                if st.form_submit_button("நிலையை மாற்று"):
                                    supabase.table("customer_visits").update({"status": new_stat}).eq("id", v["id"]).execute()
                                    st.success("நிலை மாற்றப்பட்டது!")
                                    st.rerun()

                        with col_act2:
                            st.write("**🗑️ முழு வருகையை நீக்குதல் (Delete Visit & Transactions):**")
                            st.caption("இதை அழுத்தினால் இந்த வருகையுடன் தொடர்புடைய பரிவர்த்தனைகள், தணிக்கைப் பதிவுகள் அனைத்தும் நிரந்தரமாக நீக்கப்படும்.")
                            if st.button(f"🚨 இந்த வருகையை நிரந்தரமாக நீக்கு ({v['visit_no']})", key=f"del_v_{v['id']}", type="secondary"):
                                supabase.table("audit_records").delete().eq("visit_id", v["id"]).execute()
                                supabase.table("transactions").delete().eq("visit_id", v["id"]).execute()
                                supabase.table("customer_visits").delete().eq("id", v["id"]).execute()
                                st.success(f"வருகை {v['visit_no']} வெற்றிகரமாக நீக்கப்பட்டது!")
                                st.rerun()
            else:
                st.info("வருகைப் பதிவுகள் எதுவும் இல்லை.")

    # ----------------------------------------------------
    # B. தணிக்கையர் திரை (AUDITOR DESK)
    # ----------------------------------------------------
    elif st.session_state.user_role == "Auditor":
        st.header("🔍 தணிக்கையர் பணிப்பாய்வு (Auditor Verification)")
        pending_visits = supabase.table("customer_visits").select("*, transactions(*), audit_records(*)").eq("status", "Submitted_to_Auditor").execute().data or []
        if not pending_visits:
            st.info("தணிக்கை செய்ய எந்தப் புதிய பரிவர்த்தனைகளும் வரவில்லை.")
        else:
            for item in pending_visits:
                with st.expander(f"வருகை: {item['visit_no']} | நிகர ரொக்கம்: ₹{item['net_cash_amount']:,.2f}"):
                    if item.get("transactions"):
                        st.dataframe(pd.DataFrame(item["transactions"]))
                    audit_recs = item.get("audit_records", [])
                    if audit_recs and audit_recs[0].get("document_urls"):
                        for doc_url in audit_recs[0]["document_urls"]:
                            st.markdown(f"- 🔗 [ஆவணம் பார்க்க]({doc_url})")
                    c_a1, c_a2 = st.columns(2)
                    if c_a1.button(f"அங்கீகரி (Approve) - {item['visit_no']}", key=f"app_{item['id']}"):
                        supabase.table("customer_visits").update({"status": "Approved"}).eq("id", item["id"]).execute()
                        supabase.table("audit_records").update({"audit_status": "Approved", "auditor_name": st.session_state.username, "audited_at": datetime.now().isoformat()}).eq("visit_id", item["id"]).execute()
                        st.success("அங்கீகரிக்கப்பட்டது!")
                        st.rerun()
                    if c_a2.button(f"விளக்கம் கேள் - {item['visit_no']}", key=f"rej_{item['id']}"):
                        supabase.table("customer_visits").update({"status": "Needs_Clarification"}).eq("id", item["id"]).execute()
                        st.warning("விளக்கம் கேட்கப்பட்டது!")
                        st.rerun()

    # ----------------------------------------------------
    # C. கிளை செயல்பாடுகள் (COMPACT ZERO-SCROLL BRANCH UI)
    # ----------------------------------------------------
    else:
        st.subheader("📋 கிளை செயல்பாடுகள் கவுண்ட்டர்")

        staff_res = supabase.table("users").select("name").eq("branch_id", st.session_state.branch_id).eq("is_active", True).execute()
        current_staff_list = ["Walk-in"] + [s["name"] for s in staff_res.data] if staff_res.data else ["Walk-in"]

        # படி 1: வருகைப் பதிவு
        if st.session_state.current_visit is None:
            v_type = st.radio("வாடிக்கையாளர் வகை:", ["ஏற்கனவே உள்ள வாடிக்கையாளர்", "புதிய வாடிக்கையாளர்"], horizontal=True)

            if "ஏற்கனவே" in v_type:
                search_q = st.text_input("பெயர் / மொபைல் / Code உள்ளிடவும் (குறைந்தது 2 எழுத்துகள்):", placeholder="எ.கா: ராம் அல்லது 98765...", key="c_srch_fld")
                if len(search_q.strip()) >= 2:
                    cq = supabase.table("customers").select("*").eq("is_active", True)
                    if st.session_state.user_role not in ["Admin", "Auditor"]:
                        cq = cq.eq("branch_id", st.session_state.branch_id)
                    matched = cq.or_(f"name.ilike.%{search_q.strip()}%,mobile.ilike.%{search_q.strip()}%,customer_code.ilike.%{search_q.strip()}%").limit(15).execute().data or []
                    if matched:
                        c_dict = {f"{c['name']} | {c.get('customer_code', '')} | 📞 {c.get('mobile', '')}": c for c in matched}
                        sel_label = st.selectbox("பொருந்தும் வாடிக்கையாளர் பட்டியல்:", list(c_dict.keys()))
                        sel_c = c_dict[sel_label]
                        
                        col_card1, col_card2 = st.columns([3, 1])
                        with col_card1:
                            st.info(f"👤 **{sel_c['name']}** ({sel_c.get('customer_code')}) | 📞 {sel_c.get('mobile')} | 🏠 {sel_c.get('address', '-')}")
                        with col_card2:
                            if st.button("வருகையைத் தொடங்கு ➔", type="primary", use_container_width=True):
                                st.session_state.current_visit = {
                                    "visit_no": generate_short_visit_no(),
                                    "customer_id": sel_c["id"],
                                    "customer_name": sel_c["name"],
                                    "customer_code": sel_c.get("customer_code", ""),
                                    "mobile": sel_c.get("mobile", ""),
                                    "step": "TRANSACTIONS"
                                }
                                st.rerun()
                    else:
                        st.warning("வாடிக்கையாளர் இல்லை.")

            else:
                with st.form("compact_new_c_form"):
                    n1, n2, n3 = st.columns(3)
                    new_name = n1.text_input("பெயர் *")
                    new_mob = n2.text_input("முதன்மை மொபைல் *")
                    new_addr = n3.text_input("முகவரி")
                    if st.form_submit_button("பதிவு செய்து வருகையைத் தொடங்கு ➔", type="primary"):
                        if new_name.strip() and new_mob.strip():
                            t_code = f"CUST-{datetime.now().strftime('%m%d%H%M%S')}"
                            c_res = supabase.table("customers").insert({
                                "branch_id": st.session_state.branch_id, "customer_code": t_code,
                                "name": new_name.strip(), "mobile": new_mob.strip(), "address": new_addr.strip(), "is_active": True
                            }).execute()
                            if c_res.data:
                                n_c = c_res.data[0]
                                st.session_state.current_visit = {
                                    "visit_no": generate_short_visit_no(),
                                    "customer_id": n_c["id"],
                                    "customer_name": n_c["name"],
                                    "customer_code": n_c["customer_code"],
                                    "mobile": n_c["mobile"],
                                    "step": "TRANSACTIONS"
                                }
                                st.rerun()
                        else:
                            st.error("பெயர் மற்றும் மொபைல் கட்டாயம் தேவை.")

        # படி 2: வணிக நடவடிக்கைகள் சேர்த்தல்
        elif st.session_state.current_visit["step"] == "TRANSACTIONS":
            visit = st.session_state.current_visit
            st.success(f"வாடிக்கையாளர்: **{visit['customer_name']}** | வருகை எண்: **{visit['visit_no']}**")

            col_t1, col_t2 = st.columns([1.5, 2.5])
            with col_t1:
                txn_category = st.selectbox("நடவடிக்கை வகை:", [
                    "Pledge (புதிய நகைக் கடன்)", "GL Release (அடமானம் மீட்டல்)", "Interest Payment (வட்டி வரவு)",
                    "Part Payment (அசல் வரவு)", "Take Over (பிற நிறுவன கடன் மீட்டல்)", "RD Due (RD தவணை)",
                    "FD Open (புதிய வைப்பு)", "GS (நகை விற்பனை)", "GP (பழைய நகை வாங்குதல்)"
                ])

            with st.form("compact_txn_form", clear_on_submit=True):
                c_f1, c_f2, c_f3 = st.columns(3)
                staff = c_f1.selectbox("பணியாளர்:", current_staff_list)
                paid_amt, received_amt = 0.0, 0.0
                remarks_list = []

                if txn_category == "Pledge (புதிய நகைக் கடன்)":
                    gl_no = c_f2.text_input("GL No *")
                    g_wt = c_f3.number_input("நிகர எடை (Net Wt gms)", min_value=0.0, step=0.1)
                    paid_amt = st.number_input("செலுத்திய கடன் தொகை (Paid ₹) *", min_value=0.0, step=500.0)
                    remarks_list = [f"GL: {gl_no}", f"எடை: {g_wt}g"]

                elif txn_category == "GL Release (அடமானம் மீட்டல்)":
                    gl_no = c_f2.text_input("மீட்கும் GL No *")
                    p_amt = c_f3.number_input("அசல் ₹", min_value=0.0, step=500.0)
                    i_amt = st.number_input("வட்டி ₹", min_value=0.0, step=50.0)
                    received_amt = p_amt + i_amt
                    st.caption(f"மொத்த வரவு: ₹{received_amt:,.2f}")
                    remarks_list = [f"GL: {gl_no}", f"அசல்: {p_amt}", f"வட்டி: {i_amt}"]

                elif "Payment" in txn_category or "Due" in txn_category or "Sale" in txn_category:
                    ref_no = c_f2.text_input("கடன் / ரசீது எண்")
                    received_amt = c_f3.number_input("பெற்ற தொகை (Received ₹) *", min_value=0.0, step=100.0)
                    remarks_list = [f"Ref: {ref_no}"]

                else:
                    ref_no = c_f2.text_input("குறிப்பு / பழைய எண்")
                    paid_amt = c_f3.number_input("வழங்கிய தொகை (Paid ₹) *", min_value=0.0, step=100.0)
                    remarks_list = [f"Ref: {ref_no}"]

                if st.form_submit_button("➕ பட்டியலில் சேர் (Add)", type="primary"):
                    if paid_amt > 0 or received_amt > 0:
                        st.session_state.transactions_cart.append({
                            "transaction_type": txn_category,
                            "staff_name": staff,
                            "paid_amount": float(paid_amt),
                            "received_amount": float(received_amt),
                            "remarks": " | ".join(remarks_list)
                        })
                        st.rerun()

            if st.session_state.transactions_cart:
                df_c = pd.DataFrame(st.session_state.transactions_cart)
                st.dataframe(df_c[["transaction_type", "staff_name", "paid_amount", "received_amount", "remarks"]], use_container_width=True)
                t_p = df_c["paid_amount"].sum()
                t_r = df_c["received_amount"].sum()
                net = t_p - t_r

                m1, m2, m3, m4, m5 = st.columns([2, 2, 2, 2, 1])
                m1.metric("பட்டுவாடா", f"₹{t_p:,.2f}")
                m2.metric("வரவு", f"₹{t_r:,.2f}")
                m3.metric("நிகர ரொக்கம்", f"₹{abs(net):,.2f}")
                if m4.button("பணக் கணக்கீட்டிற்குச் செல் ➔", type="primary", use_container_width=True):
                    st.session_state.current_visit["net_amount"] = net
                    st.session_state.current_visit["total_paid"] = t_p
                    st.session_state.current_visit["total_received"] = t_r
                    st.session_state.current_visit["step"] = "CASH_OTP"
                    st.rerun()
                if m5.button("அழி", use_container_width=True):
                    st.session_state.transactions_cart = []
                    st.rerun()

        # படி 3: சுருக்கப்பட்ட ரொக்க நோட்டுகள் & OTP திரை (Compact Zero-Scroll Grid)
        elif st.session_state.current_visit["step"] == "CASH_OTP":
            visit = st.session_state.current_visit
            net_target = visit["net_amount"]
            
            hdr_text = f"💸 வழங்க வேண்டியது: ₹{net_target:,.2f}" if net_target > 0 else f"💰 பெற வேண்டியது: ₹{abs(net_target):,.2f}"
            st.info(f"**{hdr_text}** (வாடிக்கையாளர்: {visit['customer_name']})")

            col_main1, col_main2 = st.columns([3, 1.5])

            with col_main1:
                # 4 நெடுவரிசை கச்சிதமான கட்டமைப்பு (Compact 4-column Grid)
                tab_in, tab_out = st.tabs(["📥 வாடிக்கையாளர் தந்தவை (Cash IN)", "📤 நாம் கொடுத்தவை (Cash OUT)"])
                
                with tab_in:
                    c1, c2, c3, c4 = st.columns(4)
                    i500 = c1.number_input("₹500", min_value=0, step=1, key="i500")
                    i200 = c2.number_input("₹200", min_value=0, step=1, key="i200")
                    i100 = c3.number_input("₹100", min_value=0, step=1, key="i100")
                    i50 = c4.number_input("₹50", min_value=0, step=1, key="i50")
                    i20 = c1.number_input("₹20", min_value=0, step=1, key="i20")
                    i10 = c2.number_input("₹10", min_value=0, step=1, key="i10")
                    i5 = c3.number_input("₹5", min_value=0, step=1, key="i5")
                    icoin = c4.number_input("Coins", min_value=0, step=1, key="icoin")
                    tot_in = (i500*500) + (i200*200) + (i100*100) + (i50*50) + (i20*20) + (i10*10) + (i5*5) + icoin

                with tab_out:
                    o1, o2, o3, o4 = st.columns(4)
                    o500 = o1.number_input("₹500 ", min_value=0, step=1, key="o500")
                    o200 = o2.number_input("₹200 ", min_value=0, step=1, key="o200")
                    o100 = o3.number_input("₹100 ", min_value=0, step=1, key="o100")
                    o50 = o4.number_input("₹50 ", min_value=0, step=1, key="o50")
                    o20 = o1.number_input("₹20 ", min_value=0, step=1, key="o20")
                    o10 = o2.number_input("₹10 ", min_value=0, step=1, key="o10")
                    o5 = o3.number_input("₹5 ", min_value=0, step=1, key="o5")
                    ocoin = o4.number_input("Coins ", min_value=0, step=1, key="ocoin")
                    tot_out = (o500*500) + (o200*200) + (o100*100) + (o50*50) + (o20*20) + (o10*10) + (o5*5) + ocoin

                calc_net = (tot_in - tot_out) if net_target < 0 else (tot_out - tot_in)
                target_val = abs(net_target)
                matched = (calc_net == target_val)

                st.write(f"கணக்கீடு: **₹{calc_net:,.2f}** / தேவை: **₹{target_val:,.2f}** | " + ("✅ **டேலி சரியானது**" if matched else f"❌ **வித்தியாசம்: ₹{abs(target_val - calc_net):,.2f}**"))

            with col_main2:
                st.write(f"📞 {visit['mobile']}")
                if not matched:
                    st.button("📲 OTP அனுப்புக", disabled=True)
                    st.caption("⚠️ டேலி சரியாக அமைந்ததும் பட்டன் இயங்கும்.")
                else:
                    if st.button("📲 OTP அனுப்புக", type="primary"):
                        otp_c = str(random.randint(1000, 9999))
                        st.session_state.generated_otp = otp_c
                        ok, msg = send_fast2sms_otp(visit["mobile"], otp_c)
                        if ok: st.success("OTP அனுப்பப்பட்டது!")
                        else: st.info(f"சோதனை OTP: **{otp_c}**")

                ent_otp = st.text_input("OTP:", max_chars=4)
                if st.button("அடுத்து ➔", type="primary", use_container_width=True):
                    if not matched:
                        st.error("டேலி பொருந்தவில்லை!")
                    elif ent_otp and ent_otp == st.session_state.get("generated_otp"):
                        visit["denomination"] = {"in_total": tot_in, "out_total": tot_out}
                        visit["step"] = "DOC_UPLOAD"
                        st.rerun()
                    else:
                        st.error("தவறான OTP!")

        # படி 4: ஆவணப் பதிவேற்றம்
        elif st.session_state.current_visit["step"] == "DOC_UPLOAD":
            visit = st.session_state.current_visit
            st.subheader("படி 4: ஆவணப் பதிவேற்றம்")
            up_files = st.file_uploader("ஆவணங்களைத் தேர்வு செய்க (Pledge / Photo)", accept_multiple_files=True)
            if st.button("நிறைவு செய்து அனுப்புக", type="primary"):
                if up_files:
                    links = upload_files_to_supabase(up_files, visit["visit_no"])
                    v_res = supabase.table("customer_visits").insert({
                        "visit_no": visit["visit_no"], "customer_id": visit["customer_id"],
                        "branch_id": st.session_state.branch_id, "total_paid": visit["total_paid"],
                        "total_received": visit["total_received"], "net_cash_amount": visit["net_amount"],
                        "denomination_details": visit.get("denomination", {}), "otp_verified": True,
                        "status": "Submitted_to_Auditor"
                    }).execute()
                    vid = v_res.data[0]["id"]
                    for t in st.session_state.transactions_cart:
                        t["visit_id"] = vid
                        supabase.table("transactions").insert(t).execute()
                    supabase.table("audit_records").insert({"visit_id": vid, "document_urls": links, "audit_status": "Pending"}).execute()
                    st.success("வெற்றிகரமாக தணிக்கைக்கு அனுப்பப்பட்டது!")
                    st.session_state.current_visit = None
                    st.session_state.transactions_cart = []
                    st.button("அடுத்த வருகை")
                else:
                    st.error("ஆவணங்களை இணைக்கவும்.")
