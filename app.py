from datetime import datetime
import random
import requests
import pandas as pd
import streamlit as st
from supabase import Client, create_client

# பக்க வடிவமைப்பு
st.set_page_config(page_title="Branch Operations System", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 1.5rem; padding-left: 1.5rem; padding-right: 1.5rem; }
    div[data-testid="stMetricValue"] { font-size: 1.25rem; }
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
    """Fast2SMS DLT (MTHSEG - 219823) மூலம் வாடிக்கையாளருக்கு SMS அனுப்புகிறது"""
    try:
        api_key = "eBGQYanRZNKVCpMSg3KB5kUxY2QhDnOjxesh3Hqr7FOG792XV9wut4TPhQia"
        if "sms" in st.secrets and "fast2sms_api_key" in st.secrets["sms"]:
            api_key = st.secrets["sms"]["fast2sms_api_key"]

        clean_mobile = "".join(filter(str.isdigit, str(mobile_no)))[-10:]
        url = "https://www.fast2sms.com/dev/bulkV2"
        headers = {
            "authorization": api_key.strip(),
            "Content-Type": "application/json",
            "accept": "application/json"
        }

        # 1. DLT முறை (Sender: MTHSEG, Template: 219823)
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
            return True, "SMS வெற்றிகரமாக அனுப்பப்பட்டது!"

        # 2. DLT மாறியில் முரண்பாடு இருப்பின் மாற்று முறை
        params_otp = {
            "route": "otp",
            "variables_values": str(otp_code),
            "numbers": clean_mobile
        }
        resp_fallback = requests.get(url, headers=headers, params=params_otp, timeout=8)
        fallback_json = resp_fallback.json()

        if fallback_json.get("return") is True:
            return True, "SMS வெற்றிகரமாக அனுப்பப்பட்டது!"

        err_msg = res_json.get("message") or fallback_json.get("message") or str(res_json)
        return False, str(err_msg)
    except Exception as e:
        return False, f"இணைப்புப் பிழை: {e}"

# ==========================================
# 3. தற்காலிக சேமிப்பக மாறிகள் (Session State)
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
        st.markdown("<p style='text-align: center; color: gray;'>பணியாளர் உள்நுழைவு</p>", unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("பயனர் பெயர் (Username)", placeholder="Username")
            password = st.text_input("கடவுச்சொல் (Password)", type="password", placeholder="Password")
            submitted = st.form_submit_button("உள்நுழைக (Login)", use_container_width=True)

            if submitted:
                if username.strip() and password.strip():
                    user_query = (
                        supabase.table("users")
                        .select("id, name, username, role, branch_id, is_active, branches(branch_name)")
                        .eq("username", username.strip())
                        .eq("password_hash", password.strip())
                        .eq("is_active", True)
                        .execute()
                    )

                    if user_query.data:
                        user_info = user_query.data[0]
                        role = user_info["role"]
                        b_id = user_info.get("branch_id")

                        if role in ["Admin", "Auditor"]:
                            b_name = "Head Office / Admin"
                        else:
                            branch_rel = user_info.get("branches")
                            b_name = branch_rel.get("branch_name") if branch_rel else "ஒதுக்கப்படாத கிளை"

                        if role not in ["Admin", "Auditor"] and not b_id:
                            st.error("உங்களுக்கு இன்னும் கிளை ஒதுக்கப்படவில்லை!")
                        else:
                            st.session_state.logged_in = True
                            st.session_state.user_role = role
                            st.session_state.branch = b_name
                            st.session_state.branch_id = b_id
                            st.session_state.username = user_info["name"]
                            st.rerun()
                    else:
                        st.error("தவறான பயனர் பெயர் அல்லது கடவுச்சொல்! (அல்லது கணக்கு முடக்கப்பட்டுள்ளது)")
                else:
                    st.warning("விவரங்களை உள்ளிடவும்.")

# ==========================================
# 5. முதன்மை திரை
# ==========================================
else:
    top_col1, top_col2, top_col3 = st.columns([4, 2, 1])
    with top_col1:
        st.write(f"🏢 **கிளை:** {st.session_state.branch}")
    with top_col2:
        st.write(f"👤 **பயனர்:** {st.session_state.username} ({st.session_state.user_role})")
    with top_col3:
        if st.button("வெளியேறு (Logout)", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.current_visit = None
            st.session_state.transactions_cart = []
            st.session_state.generated_otp = None
            st.rerun()

    st.markdown("---")

    # ----------------------------------------------------
    # A. நிர்வாக மேலாண்மை திரை (ADMIN PANEL)
    # ----------------------------------------------------
    if st.session_state.user_role == "Admin":
        st.header("⚙️ நிர்வாக மேலாண்மை (Admin Control Panel)")
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🏢 கிளைகள் மேலாண்மை",
            "👥 பணியாளர்கள் மேலாண்மை",
            "📥 மொத்தப் பதிவேற்றம் (Bulk Import)",
            "🗂️ வாடிக்கையாளர் மேலாண்மை",
            "📊 பரிவர்த்தனை திருத்தம் & நீக்கம் (Visits & Transactions)"
        ])

        with tab1:
            st.subheader("➕ புதிய கிளை சேர்த்தல்")
            with st.form("admin_add_branch_form", clear_on_submit=True):
                b_col1, b_col2 = st.columns(2)
                b_name = b_col1.text_input("கிளையின் பெயர்")
                b_code = b_col2.text_input("கிளை குறியீடு (Branch Code)")
                if st.form_submit_button("கிளையைச் சேர்"):
                    if b_name.strip() and b_code.strip():
                        try:
                            supabase.table("branches").insert({
                                "branch_name": b_name.strip(),
                                "branch_code": b_code.strip().upper(),
                            }).execute()
                            st.success("கிளை சேர்க்கப்பட்டது!")
                            st.rerun()
                        except Exception as err:
                            st.error(f"பிழை: {err}")

            b_list_res = supabase.table("branches").select("id, branch_name, branch_code").order("id").execute()
            if b_list_res.data:
                st.dataframe(pd.DataFrame(b_list_res.data), use_container_width=True)

        with tab2:
            st.subheader("👥 பணியாளர்கள் பட்டியல்")
            users_res = supabase.table("users").select("id, name, username, role, branch_id, is_active").order("id").execute()
            if users_res.data:
                u_data = [{
                    "ID": u["id"],
                    "பெயர்": u["name"],
                    "Username": u["username"],
                    "Role": u["role"],
                    "கிளை": branch_id_to_name.get(u.get("branch_id"), "Admin"),
                    "நிலை": "🟢 Active" if u.get("is_active") else "🔴 Inactive"
                } for u in users_res.data]
                st.dataframe(pd.DataFrame(u_data), use_container_width=True)

            st.markdown("---")
            sub_col1, sub_col2 = st.columns(2)
            with sub_col1:
                with st.form("admin_add_user_form", clear_on_submit=True):
                    st.write("**➕ புதிய பணியாளர் சேர்த்தல்**")
                    u_name = st.text_input("முழுப் பெயர்")
                    u_username = st.text_input("உள்நுழைவு பெயர் (Username)")
                    u_pass = st.text_input("கடவுச்சொல்", type="password")
                    u_role = st.selectbox("பணி நிலை (Role)", ["Branch Head / Cashier", "Staff", "Auditor", "Admin"])
                    b_sel = st.selectbox("கிளை", list(branch_options.keys()) if branch_options else ["கிளைகள் இல்லை"])
                    if st.form_submit_button("உருவாக்கு"):
                        if u_name.strip() and u_username.strip() and u_pass.strip():
                            supabase.table("users").insert({
                                "name": u_name.strip(),
                                "username": u_username.strip(),
                                "password_hash": u_pass.strip(),
                                "role": u_role,
                                "branch_id": branch_options.get(b_sel) if u_role not in ["Admin", "Auditor"] else None,
                                "is_active": True
                            }).execute()
                            st.success("பணியாளர் சேர்க்கப்பட்டார்!")
                            st.rerun()

            with sub_col2:
                if users_res.data:
                    u_dict = {f"{u['name']} (@{u['username']})": u for u in users_res.data}
                    sel_u = st.selectbox("திருத்த வேண்டிய பணியாளர்:", list(u_dict.keys()))
                    target_u = u_dict[sel_u]
                    with st.form("admin_edit_user_form"):
                        ed_name = st.text_input("பெயர்", value=target_u["name"])
                        ed_pass = st.text_input("புதிய கடவுச்சொல் (மாற்ற விரும்பினால்)", type="password")
                        roles_list = ["Branch Head / Cashier", "Staff", "Auditor", "Admin"]
                        ed_role = st.selectbox("Role", roles_list, index=roles_list.index(target_u["role"]) if target_u["role"] in roles_list else 0)
                        ed_stat = st.radio("நிலை", ["Active", "Inactive"], index=0 if target_u.get("is_active") else 1)
                        if st.form_submit_button("புதுப்பி"):
                            pl = {"name": ed_name.strip(), "role": ed_role, "is_active": (ed_stat == "Active")}
                            if ed_pass.strip():
                                pl["password_hash"] = ed_pass.strip()
                            supabase.table("users").update(pl).eq("id", target_u["id"]).execute()
                            st.success("புதுப்பிக்கப்பட்டது!")
                            st.rerun()

        with tab3:
            st.subheader("📥 பழைய வாடிக்கையாளர் அறிக்கைப் பதிவேற்றம்")
            uploaded_cust_file = st.file_uploader("கோப்பைத் தேர்வு செய்க (xls, xlsx, csv)", type=["xls", "xlsx", "csv"])
            if uploaded_cust_file:
                try:
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
                            if c_code in seen:
                                c_code = f"{c_code}-{idx+1}"
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
                        st.success("வாடிக்கையாளர்கள் வெற்றிகரமாகப் பதிவேற்றப்பட்டனர்!")
                        st.rerun()
                except Exception as e:
                    st.error(f"பிழை: {e}")

        with tab4:
            st.subheader("🗂️ வாடிக்கையாளர் பட்டியல் & மேலாண்மை")
            f_col1, f_col2 = st.columns([1, 2])
            b_filt = f_col1.selectbox("கிளை வடிகட்டல்:", ["அனைத்தும்"] + list(branch_options.keys()))
            c_srch = f_col2.text_input("வாடிக்கையாளர் பெயர் / மொபைல் / Code தேடுக:")
            cq = supabase.table("customers").select("*").order("id", desc=True)
            if b_filt != "அனைத்தும்":
                cq = cq.eq("branch_id", branch_options[b_filt])
            if c_srch.strip():
                cq = cq.or_(f"name.ilike.%{c_srch.strip()}%,mobile.ilike.%{c_srch.strip()}%,customer_code.ilike.%{c_srch.strip()}%")
            else:
                cq = cq.limit(100)
            res_c = cq.execute().data or []

            if res_c:
                st.dataframe(pd.DataFrame([{
                    "ID": c["id"],
                    "Code": c["customer_code"],
                    "பெயர்": c["name"],
                    "மொபைல்": c["mobile"],
                    "கிளை": branch_id_to_name.get(c["branch_id"]),
                    "நிலை": "Active" if c.get("is_active") else "Inactive"
                } for c in res_c]), use_container_width=True)

                target_c = st.selectbox("திருத்த வேண்டிய வாடிக்கையாளர்:", res_c, format_func=lambda x: f"{x.get('customer_code')} - {x['name']} ({x.get('mobile')})")
                with st.form("edit_c_form"):
                    e1, e2, e3 = st.columns(3)
                    en = e1.text_input("பெயர்", value=target_c["name"])
                    em = e2.text_input("மொபைல்", value=target_c["mobile"])
                    es = e3.radio("நிலை", ["Active", "Inactive"], index=0 if target_c.get("is_active") else 1)
                    if st.form_submit_button("சேமி"):
                        supabase.table("customers").update({
                            "name": en.strip(),
                            "mobile": em.strip(),
                            "is_active": (es == "Active")
                        }).eq("id", target_c["id"]).execute()
                        st.success("வாடிக்கையாளர் விவரங்கள் புதுப்பிக்கப்பட்டன!")
                        st.rerun()

        # Tab 5: அட்மின் பரிவர்த்தனை திருத்தம் மற்றும் நீக்கம்
        with tab5:
            st.subheader("📊 பரிவர்த்தனை & வருகை மேலாண்மை (Edit / Delete Visits & Transactions)")
            v_srch = st.text_input("தேடுக (வருகை எண்):", placeholder="எ.கா: VST-1001", key="adm_v_srch")
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
                        st.write(f"**தேதி:** {v['created_at']} | **பட்டுவாடா:** ₹{v['total_paid']} | **வரவு:** ₹{v['total_received']}")

                        txns = v.get("transactions", [])
                        if txns:
                            st.dataframe(pd.DataFrame(txns)[["id", "transaction_type", "staff_name", "paid_amount", "received_amount", "remarks"]], use_container_width=True)

                        col_act1, col_act2 = st.columns([1, 1])
                        with col_act1:
                            with st.form(f"edit_visit_form_{v['id']}"):
                                st.write("**✏️ நிலையை மாற்றுதல்:**")
                                stat_opts = ["Submitted_to_Auditor", "Approved", "Needs_Clarification", "Cancelled"]
                                cur_stat = v.get("status", "Submitted_to_Auditor")
                                new_stat = st.selectbox("நிலை (Status)", stat_opts, index=stat_opts.index(cur_stat) if cur_stat in stat_opts else 0)
                                if st.form_submit_button("புதுப்பி"):
                                    supabase.table("customer_visits").update({"status": new_stat}).eq("id", v["id"]).execute()
                                    st.success("நிலை மாற்றப்பட்டது!")
                                    st.rerun()

                        with col_act2:
                            st.write("**🗑️ வருகையை நீக்குதல்:**")
                            st.caption("இந்த வருகையின் கீழ் உள்ள அனைத்து பரிவர்த்தனைகளும் நீக்கப்படும்.")
                            if st.button(f"🚨 நிரந்தரமாக நீக்கு ({v['visit_no']})", key=f"del_v_{v['id']}", type="secondary"):
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
                            st.markdown(f"- 🔗 [ஆவணத்தைப் பார்க்க கிளிக் செய்க]({doc_url})")
                    c_a1, c_a2 = st.columns(2)
                    if c_a1.button(f"அங்கீகரி (Approve) - {item['visit_no']}", key=f"app_{item['id']}"):
                        supabase.table("customer_visits").update({"status": "Approved"}).eq("id", item["id"]).execute()
                        supabase.table("audit_records").update({
                            "audit_status": "Approved",
                            "auditor_name": st.session_state.username,
                            "audited_at": datetime.now().isoformat()
                        }).eq("visit_id", item["id"]).execute()
                        st.success("அங்கீகரிக்கப்பட்டது!")
                        st.rerun()
                    if c_a2.button(f"விளக்கம் கேள் - {item['visit_no']}", key=f"rej_{item['id']}"):
                        supabase.table("customer_visits").update({"status": "Needs_Clarification"}).eq("id", item["id"]).execute()
                        st.warning("விளக்கம் கேட்கப்பட்டது!")
                        st.rerun()

    # ----------------------------------------------------
    # C. கிளை செயல்பாடுகள் (BRANCH FLOW)
    # ----------------------------------------------------
    else:
        st.subheader("📋 கிளை செயல்பாடுகள் கவுண்ட்டர்")
        staff_res = supabase.table("users").select("name").eq("branch_id", st.session_state.branch_id).eq("is_active", True).execute()
        current_staff_list = ["Walk-in"] + [s["name"] for s in staff_res.data] if staff_res.data else ["Walk-in"]

        # படி 1: வருகைப் பதிவு
        if st.session_state.current_visit is None:
            v_type = st.radio("வாடிக்கையாளர் வகை:", ["ஏற்கனவே உள்ள வாடிக்கையாளர்", "புதிய வாடிக்கையாளர்"], horizontal=True)

            if "ஏற்கனவே" in v_type:
                search_q = st.text_input("பெயர் / மொபைல் / Code உள்ளிடவும்:", placeholder="எ.கா: ராம் அல்லது 98765...", key="c_srch_fld")
                if len(search_q.strip()) >= 2:
                    cq = supabase.table("customers").select("*").eq("is_active", True)
                    if st.session_state.user_role not in ["Admin", "Auditor"]:
                        cq = cq.eq("branch_id", st.session_state.branch_id)
                    matched = cq.or_(f"name.ilike.%{search_q.strip()}%,mobile.ilike.%{search_q.strip()}%,customer_code.ilike.%{search_q.strip()}%").limit(20).execute().data or []

                    if matched:
                        c_dict = {f"{c['name']} | {c.get('customer_code', '')} | 📞 {c.get('mobile', '')}": c for c in matched}
                        sel_label = st.selectbox("பொருந்தும் வாடிக்கையாளர் பட்டியல்:", list(c_dict.keys()))
                        sel_c = c_dict[sel_label]

                        with st.container(border=True):
                            c_col1, c_col2, c_col3 = st.columns([1, 2.5, 1])
                            with c_col1:
                                if sel_c.get("photo_url"):
                                    st.image(sel_c["photo_url"], width=110)
                                else:
                                    st.info("📷 படம் இல்லை")
                            with c_col2:
                                st.markdown(f"### {sel_c['name']} <small style='color:gray;'>({sel_c.get('customer_code', 'CUST-ID')})</small>", unsafe_allow_html=True)
                                st.write(f"📞 **முதன்மை மொபைல்:** {sel_c.get('mobile', '-')} | **கூடுதல் மொபைல்:** {sel_c.get('mobile2', '-')}")
                                st.write(f"👨‍👦 **கார்டியன் பெயர்:** {sel_c.get('guardian_name', '-')} | **பாலினம்:** {sel_c.get('gender', '-')}")
                                st.write(f"🏠 **முகவரி:** {sel_c.get('address', '-')}")
                                st.write(f"🤝 **நாமினி உறவு:** {sel_c.get('nominee_relation', '-')}")
                            with c_col3:
                                st.write("")
                                st.write("")
                                if st.button("வருகையைத் தொடங்கு ➔", key=f"start_visit_{sel_c['id']}", type="primary", use_container_width=True):
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
                st.markdown("##### 📝 புதிய வாடிக்கையாளர் பதிவுப் படிவம்")
                with st.form("new_customer_form"):
                    col_n1, col_n2, col_n3 = st.columns(3)
                    with col_n1:
                        new_name = st.text_input("வாடிக்கையாளர் பெயர் *")
                        new_guardian = st.text_input("கார்டியன் / தந்தை / கணவர் பெயர்")
                        new_dob = st.date_input("பிறந்த தேதி (DOB)", min_value=datetime(1940, 1, 1), max_value=datetime.today())
                        new_gender = st.selectbox("பாலினம் (Gender)", ["ஆண் (Male)", "பெண் (Female)", "மற்றவை (Other)"])

                    with col_n2:
                        new_mob1 = st.text_input("முதன்மை மொபைல் எண் (Mobile 1) *")
                        new_mob2 = st.text_input("கூடுதல் மொபைல் எண் (Mobile 2)")
                        new_photo = st.file_uploader("வாடிக்கையாளர் புகைப்படம் (Photo)", type=["jpg", "jpeg", "png"])

                    with col_n3:
                        new_address = st.text_area("முழு முகவரி (Address)", height=100)
                        new_nominee = st.text_input("நாமினி பெயர் (Nominee Name)")
                        new_relation = st.text_input("உறவுமுறை (Nominee Relation)")

                    submit_new_cust = st.form_submit_button("வாடிக்கையாளரைப் பதிவு செய்து வருகையைத் தொடங்கு ➔", type="primary")

                    if submit_new_cust:
                        if new_name.strip() and new_mob1.strip():
                            try:
                                photo_url = None
                                if new_photo:
                                    photo_path = f"customer_profiles/{datetime.now().strftime('%Y%m%d%H%M%S')}_{new_photo.name}"
                                    supabase.storage.from_("branch-documents").upload(
                                        path=photo_path,
                                        file=new_photo.getvalue(),
                                        file_options={"content-type": new_photo.type, "upsert": "true"},
                                    )
                                    photo_url = supabase.storage.from_("branch-documents").get_public_url(photo_path)

                                timestamp_code = f"CUST-{datetime.now().strftime('%m%d%H%M%S')}"
                                insert_data = {
                                    "branch_id": st.session_state.branch_id,
                                    "customer_code": timestamp_code,
                                    "name": new_name.strip(),
                                    "guardian_name": new_guardian.strip(),
                                    "dob": str(new_dob),
                                    "gender": new_gender,
                                    "mobile": new_mob1.strip(),
                                    "mobile2": new_mob2.strip(),
                                    "address": new_address.strip(),
                                    "nominee_name": new_nominee.strip(),
                                    "nominee_relation": new_relation.strip(),
                                    "photo_url": photo_url,
                                    "is_active": True,
                                }
                                cust_insert_res = supabase.table("customers").insert(insert_data).execute()

                                if cust_insert_res.data:
                                    created_cust = cust_insert_res.data[0]
                                    st.session_state.current_visit = {
                                        "visit_no": generate_short_visit_no(),
                                        "customer_id": created_cust["id"],
                                        "customer_name": created_cust["name"],
                                        "customer_code": created_cust["customer_code"],
                                        "mobile": created_cust["mobile"],
                                        "step": "TRANSACTIONS",
                                    }
                                    st.success(f"வாடிக்கையாளர் எண் {timestamp_code} உடன் பதிவு செய்யப்பட்டார்!")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"பதிவு செய்வதில் பிழை: {e}")
                        else:
                            st.error("பெயர் மற்றும் முதன்மை மொபைல் எண் கட்டாயம் தேவை.")

        # படி 2: வணிக நடவடிக்கைகள் சேர்த்தல் (முழுமையான டைனமிக் படிவம்)
        elif st.session_state.current_visit["step"] == "TRANSACTIONS":
            visit = st.session_state.current_visit
            st.success(f"வாடிக்கையாளர்: **{visit['customer_name']}** (வருகை எண்: **{visit['visit_no']}**)")

            st.subheader("படி 2: வணிக நடவடிக்கைகள் சேர்த்தல்")

            txn_category = st.selectbox(
                "நடவடிக்கை வகையைத் தேர்ந்தெடுக்கவும் (Transaction Type):",
                [
                    "Pledge (புதிய நகைக் கடன்)",
                    "GL Release (அடமானம் மீட்டல்)",
                    "Interest Payment (வட்டி வரவு)",
                    "Part Payment (அசல் வரவு)",
                    "Take Over (பிற நிறுவன கடன் மீட்டல்)",
                    "RD Open (புதிய RD சேமிப்பு)",
                    "RD Due (RD தவணை செலுத்துதல்)",
                    "RD Closure (RD முதிர்வு பட்டுவாடா)",
                    "FD Open (புதிய வைப்பு நிதி)",
                    "FD Interest (FD வட்டி பட்டுவாடா)",
                    "FD Closure (FD முதிர்வு பட்டுவாடா)",
                    "GP (Gold Purchase - பழைய நகை வாங்குதல்)",
                    "GS (Gold Sale - நகை விற்பனை)",
                ],
                key="dynamic_txn_type_select",
            )

            with st.form("dynamic_txn_form", clear_on_submit=True):
                col_st1, col_st2 = st.columns(2)
                with col_st1:
                    staff = st.selectbox("கையாண்ட பணியாளர் (Staff Attribution):", current_staff_list)
                with col_st2:
                    custom_remarks = st.text_input("கூடுதல் குறிப்பு (Optional Remarks):", placeholder="எ.கா: சிறப்பு தள்ளுபடி / விசேஷ குறிப்பு")

                st.markdown("---")

                paid_amt = 0.0
                received_amt = 0.0
                detail_summary = []

                if txn_category == "Pledge (புதிய நகைக் கடன்)":
                    st.markdown("##### 🪙 புதிய நகைக் கடன் விவரங்கள்")
                    p_col1, p_col2, p_col3 = st.columns(3)
                    with p_col1:
                        new_gl_no = st.text_input("புதிய கடன் எண் (GL No) *", placeholder="எ.கா: GL-2026-001")
                        scheme_name = st.selectbox("வட்டி திட்டம் (Scheme)", ["ஸ்கீம் A (12%)", "ஸ்கீம் B (15%)", "ஸ்கீம் C (18%)", "மாதாந்திர ஸ்கீம்"])
                    with p_col2:
                        gross_wt = st.number_input("மொத்த எடை (Gross Weight - gms) *", min_value=0.0, step=0.1, format="%.2f")
                        net_wt = st.number_input("நிகர எடை (Net Weight - gms) *", min_value=0.0, step=0.1, format="%.2f")
                    with p_col3:
                        item_count = st.number_input("நகை எண்ணிக்கை (Item Count)", min_value=1, step=1)
                        paid_amt = st.number_input("வாடிக்கையாளருக்கு செலுத்திய கடன் தொகை (Paid Loan Amount ₹) *", min_value=0.0, step=500.0)

                    detail_summary = [f"GL: {new_gl_no}", f"ஸ்கீம்: {scheme_name}", f"மொத்த எடை: {gross_wt}g", f"நிகர எடை: {net_wt}g", f"எண்ணிக்கை: {item_count}"]

                elif txn_category == "GL Release (அடமானம் மீட்டல்)":
                    st.markdown("##### 🔓 அடகு மீட்டல் கணக்கீடு")
                    r_col1, r_col2 = st.columns(2)
                    with r_col1:
                        rel_gl_no = st.text_input("மீட்கப்படும் கடன் எண் (GL No) *", placeholder="எ.கா: GL-1025")
                        principal_amt = st.number_input("அசல் தொகை (Principal ₹) *", min_value=0.0, step=500.0)
                    with r_col2:
                        interest_amt = st.number_input("வட்டித் தொகை (Interest ₹) *", min_value=0.0, step=50.0)
                        other_charges = st.number_input("இதர கட்டணம் / அபராதம் (₹)", min_value=0.0, step=10.0)

                    received_amt = principal_amt + interest_amt + other_charges
                    st.info(f"💰 வாடிக்கையாளர் செலுத்த வேண்டிய மொத்தத் தொகை (வரவு): **₹{received_amt:,.2f}**")
                    detail_summary = [f"GL: {rel_gl_no}", f"அசல்: ₹{principal_amt}", f"வட்டி: ₹{interest_amt}"]

                elif txn_category in ["Interest Payment (வட்டி வரவு)", "Part Payment (அசல் வரவு)"]:
                    st.markdown(f"##### 💵 {txn_category} விவரங்கள்")
                    i_col1, i_col2 = st.columns(2)
                    with i_col1:
                        part_gl_no = st.text_input("கடன் எண் (GL No) *", placeholder="எ.கா: GL-1025")
                    with i_col2:
                        received_amt = st.number_input(f"வாடிக்கையாளர் செலுத்திய தொகை ({txn_category} ₹) *", min_value=0.0, step=100.0)

                    detail_summary = [f"GL: {part_gl_no}"]

                elif txn_category == "Take Over (பிற நிறுவன கடன் மீட்டல்)":
                    st.markdown("##### 🏦 பிற நிறுவன கடன் மீட்பு விவரங்கள்")
                    to_col1, to_col2 = st.columns(2)
                    with to_col1:
                        bank_source = st.text_input("முந்தைய வங்கி / நிதி நிறுவனம் *", placeholder="எ.கா: SBI / Muthoot / Manappuram")
                        prev_loan_no = st.text_input("முந்தைய லோன் எண் *")
                    with to_col2:
                        approx_wt = st.number_input("தோராய எடை (Grams)", min_value=0.0, step=0.1)
                        paid_amt = st.number_input("மீட்பிற்கு செலுத்திய தொகை (Paid Amount ₹) *", min_value=0.0, step=500.0)

                    detail_summary = [f"வங்கி: {bank_source}", f"பழைய எண்: {prev_loan_no}", f"எடை: {approx_wt}g"]

                elif "RD" in txn_category or "FD" in txn_category:
                    st.markdown(f"##### 📑 {txn_category} விவரங்கள்")
                    d_col1, d_col2 = st.columns(2)
                    with d_col1:
                        acc_no = st.text_input("கணக்கு எண் (RD/FD Account No) *")
                    with d_col2:
                        if "Closure" in txn_category or "Interest" in txn_category:
                            paid_amt = st.number_input("வாடிக்கையாளருக்கு வழங்கப்பட்ட தொகை (Paid ₹) *", min_value=0.0, step=100.0)
                        else:
                            received_amt = st.number_input("வாடிக்கையாளர் செலுத்திய தொகை (Received ₹) *", min_value=0.0, step=100.0)

                    detail_summary = [f"A/c No: {acc_no}"]

                elif txn_category == "GP (Gold Purchase - பழைய நகை வாங்குதல்)":
                    st.markdown("##### ⚖️ பழைய நகை கொள்முதல் விவரங்கள்")
                    gp_col1, gp_col2 = st.columns(2)
                    with gp_col1:
                        gp_wt = st.number_input("நகை எடை (Grams) *", min_value=0.0, step=0.1)
                        gp_purity = st.selectbox("தரம் (Purity)", ["916 (22K)", "KDM", "999 (24K)", "750 (18K)"])
                    with gp_col2:
                        paid_amt = st.number_input("வாடிக்கையாளருக்கு வழங்கிய தொகை (Paid ₹) *", min_value=0.0, step=500.0)
                    detail_summary = [f"எடை: {gp_wt}g", f"தரம்: {gp_purity}"]

                elif txn_category == "GS (Gold Sale - நகை விற்பனை)":
                    st.markdown("##### 💍 நகை விற்பனை விவரங்கள்")
                    gs_col1, gs_col2 = st.columns(2)
                    with gs_col1:
                        gs_bill_no = st.text_input("விற்பனை பில் எண் *")
                        gs_item_name = st.text_input("பொருள் பெயர்", placeholder="எ.கா: மோதிரம் / செயின்")
                    with gs_col2:
                        received_amt = st.number_input("வாடிக்கையாளரிடம் பெற்ற தொகை (Received ₹) *", min_value=0.0, step=500.0)
                    detail_summary = [f"பில்: {gs_bill_no}", f"பொருள்: {gs_item_name}"]

                st.markdown("---")
                submit_txn_btn = st.form_submit_button("➕ இந்த நடவடிக்கையை பட்டியலில் சேர் (Add to Cart)", type="primary")

                if submit_txn_btn:
                    if paid_amt > 0 or received_amt > 0:
                        all_remarks = " | ".join(detail_summary)
                        if custom_remarks.strip():
                            all_remarks += f" ({custom_remarks.strip()})"

                        st.session_state.transactions_cart.append({
                            "transaction_type": txn_category,
                            "staff_name": staff,
                            "paid_amount": float(paid_amt),
                            "received_amount": float(received_amt),
                            "remarks": all_remarks,
                        })
                        st.success(f"'{txn_category}' வெற்றிகரமாகப் பட்டியலில் சேர்க்கப்பட்டது!")
                        st.rerun()
                    else:
                        st.error("தொகை ₹0 ஆக இருக்க முடியாது! சரியான தொகையை உள்ளிடவும்.")

            if st.session_state.transactions_cart:
                st.markdown("### 🛒 நடப்பு வருகையின் நடவடிக்கைகள் பட்டியல்:")
                df_cart = pd.DataFrame(st.session_state.transactions_cart)
                st.dataframe(df_cart[["transaction_type", "staff_name", "paid_amount", "received_amount", "remarks"]], use_container_width=True)

                total_paid = df_cart["paid_amount"].sum()
                total_received = df_cart["received_amount"].sum()
                net_amount = total_paid - total_received

                c1, c2, c3 = st.columns(3)
                c1.metric("மொத்த பட்டுவாடா (Paid to Customer)", f"₹{total_paid:,.2f}")
                c2.metric("மொத்த வரவு (Received from Customer)", f"₹{total_received:,.2f}")

                if net_amount > 0:
                    c3.metric("நிகர ரொக்கம் (செலுத்த வேண்டியது)", f"₹{net_amount:,.2f}", delta="நிறுவன பட்டுவாடா")
                elif net_amount < 0:
                    c3.metric("நிகர ரொக்கம் (பெற வேண்டியது)", f"₹{abs(net_amount):,.2f}", delta="நிறுவன வரவு", delta_color="inverse")
                else:
                    c3.metric("நிகர ரொக்கம்", "₹0.00")

                cart_b1, cart_b2 = st.columns([4, 1])
                with cart_b1:
                    if st.button("பணக் கணக்கீடு மற்றும் OTP பிரிவிற்குச் செல் ➔", type="primary"):
                        st.session_state.current_visit["net_amount"] = net_amount
                        st.session_state.current_visit["total_paid"] = total_paid
                        st.session_state.current_visit["total_received"] = total_received
                        st.session_state.current_visit["step"] = "CASH_OTP"
                        st.rerun()
                with cart_b2:
                    if st.button("பட்டியலை அழி (Clear Cart)"):
                        st.session_state.transactions_cart = []
                        st.rerun()

        # படி 3: ரொக்க நோட்டுகள் & OTP திரை (Single Screen 4-Column Grid with Security Locks)
        elif st.session_state.current_visit["step"] == "CASH_OTP":
            visit = st.session_state.current_visit
            net_target = visit["net_amount"]

            # OTP அனுப்பப்பட்டதா என்பதை அறியும் கொடி
            otp_already_sent = "generated_otp" in st.session_state and st.session_state.generated_otp is not None

            hdr_text = f"💸 வழங்க வேண்டிய தொகை: ₹{net_target:,.2f}" if net_target > 0 else f"💰 பெற வேண்டிய தொகை: ₹{abs(net_target):,.2f}"
            st.info(f"**{hdr_text}** (வாடிக்கையாளர்: {visit['customer_name']})")

            if otp_already_sent:
                st.warning("🔒 **OTP வாடிக்கையாளருக்கு அனுப்பப்பட்டுவிட்டது! பணக் கணக்கீடு லாக் செய்யப்பட்டுள்ளது.** (மாற்ற விரும்பினால் கீழே உள்ள 'OTP ரத்து' பட்டனை அழுத்தவும்)")

            col_main1, col_main2 = st.columns([3, 1.4])

            with col_main1:
                tab_in, tab_out = st.tabs(["📥 வாடிக்கையாளர் தந்தவை (Cash IN)", "📤 நாம் கொடுத்தவை (Cash OUT)"])

                with tab_in:
                    c1, c2, c3, c4 = st.columns(4)
                    i500 = c1.number_input("₹500", min_value=0, step=1, key="i500", disabled=otp_already_sent)
                    i200 = c2.number_input("₹200", min_value=0, step=1, key="i200", disabled=otp_already_sent)
                    i100 = c3.number_input("₹100", min_value=0, step=1, key="i100", disabled=otp_already_sent)
                    i50 = c4.number_input("₹50", min_value=0, step=1, key="i50", disabled=otp_already_sent)
                    i20 = c1.number_input("₹20", min_value=0, step=1, key="i20", disabled=otp_already_sent)
                    i10 = c2.number_input("₹10", min_value=0, step=1, key="i10", disabled=otp_already_sent)
                    i5 = c3.number_input("₹5", min_value=0, step=1, key="i5", disabled=otp_already_sent)
                    icoin = c4.number_input("Coins", min_value=0, step=1, key="icoin", disabled=otp_already_sent)
                    tot_in = (i500*500) + (i200*200) + (i100*100) + (i50*50) + (i20*20) + (i10*10) + (i5*5) + icoin

                with tab_out:
                    o1, o2, o3, o4 = st.columns(4)
                    o500 = o1.number_input("₹500 ", min_value=0, step=1, key="o500", disabled=otp_already_sent)
                    o200 = o2.number_input("₹200 ", min_value=0, step=1, key="o200", disabled=otp_already_sent)
                    o100 = o3.number_input("₹100 ", min_value=0, step=1, key="o100", disabled=otp_already_sent)
                    o50 = o4.number_input("₹50 ", min_value=0, step=1, key="o50", disabled=otp_already_sent)
                    o20 = o1.number_input("₹20 ", min_value=0, step=1, key="o20", disabled=otp_already_sent)
                    o10 = o2.number_input("₹10 ", min_value=0, step=1, key="o10", disabled=otp_already_sent)
                    o5 = o3.number_input("₹5 ", min_value=0, step=1, key="o5", disabled=otp_already_sent)
                    ocoin = o4.number_input("Coins ", min_value=0, step=1, key="ocoin", disabled=otp_already_sent)
                    tot_out = (o500*500) + (o200*200) + (o100*100) + (o50*50) + (o20*20) + (o10*10) + (o5*5) + ocoin

                calc_net = (tot_in - tot_out) if net_target < 0 else (tot_out - tot_in)
                target_val = abs(net_target)
                matched = (calc_net == target_val)

                st.write(f"கணக்கீடு: **₹{calc_net:,.2f}** / தேவை: **₹{target_val:,.2f}** | " + ("✅ **டேலி சரியானது**" if matched else f"❌ **வித்தியாசம்: ₹{abs(target_val - calc_net):,.2f}**"))

            with col_main2:
                st.write(f"📞 மொபைல்: **{visit['mobile']}**")

                if not matched:
                    st.button("📲 OTP அனுப்புக", disabled=True, key="btn_otp_nomatch")
                    st.caption("⚠️ டேலி சரியாக அமைந்ததும் பட்டன் இயங்கும்.")
                elif otp_already_sent:
                    st.success("✅ OTP அனுப்பப்பட்டுவிட்டது!")
                else:
                    if st.button("📲 OTP அனுப்புக", type="primary", key="btn_otp_send"):
                        otp_c = str(random.randint(1000, 9999))
                        st.session_state.generated_otp = otp_c
                        ok, msg = send_fast2sms_otp(visit["mobile"], otp_c)
                        if ok:
                            st.success("OTP அனுப்பப்பட்டது!")
                        else:
                            st.info(f"சோதனை OTP: **{otp_c}**")
                        st.rerun()

                ent_otp = st.text_input("OTP உள்ளிடவும்:", max_chars=4, key="ent_otp_input")

                if st.button("அடுத்து ➔", type="primary", use_container_width=True):
                    if not matched:
                        st.error("டேலி பொருந்தவில்லை!")
                    elif not otp_already_sent:
                        st.error("முதலில் வாடிக்கையாளருக்கு OTP அனுப்பவும்!")
                    elif ent_otp and ent_otp == st.session_state.get("generated_otp"):
                        visit["denomination"] = {
                            "in": {"500": i500, "200": i200, "100": i100, "50": i50, "20": i20, "10": i10, "5": i5, "coins": icoin, "total": tot_in},
                            "out": {"500": o500, "200": o200, "100": o100, "50": o50, "20": o20, "10": o10, "5": o5, "coins": ocoin, "total": tot_out},
                            "net_change": tot_in - tot_out
                        }
                        visit["step"] = "DOC_UPLOAD"
                        st.rerun()
                    else:
                        st.error("தவறான OTP!")

                st.write("")
                # OTP அனுப்பாத வரை மட்டுமே நேரடியாக பின்செல்ல அனுமதி
                if not otp_already_sent:
                    if st.button("⬅️ நடவடிக்கைகளை மாற்ற பின்செல்க", use_container_width=True):
                        st.session_state.current_visit["step"] = "TRANSACTIONS"
                        st.rerun()
                else:
                    # OTP அனுப்பிய பின் மாற்ற விரும்பினால் பழைய OTP-யை ரத்து செய்ய வேண்டும்
                    if st.button("🔄 OTP ரத்து செய்து கணக்கீட்டை மாற்று", type="secondary", use_container_width=True):
                        st.session_state.generated_otp = None
                        st.session_state.current_visit["step"] = "TRANSACTIONS"
                        st.rerun()

        # படி 4: ஆவணப் பதிவேற்றம்
        elif st.session_state.current_visit["step"] == "DOC_UPLOAD":
            visit = st.session_state.current_visit
            st.subheader("படி 4: ஆவணப் பதிவேற்றம் & நிறைவு செய்தல்")
            uploaded_files = st.file_uploader("ஆவணங்களைத் தேர்ந்தெடுக்கவும் (Pledge Form / Photo / KYC)", accept_multiple_files=True)

            btn_col1, btn_col2 = st.columns([2, 1])
            with btn_col1:
                if st.button("நிறைவு செய்து தணிக்கைக்கு அனுப்புக ➔", type="primary", use_container_width=True):
                    if uploaded_files:
                        with st.spinner("ஆவணங்கள் பதிவேற்றப்பட்டு வருகின்றன..."):
                            try:
                                doc_links = upload_files_to_supabase(uploaded_files, visit["visit_no"])
                                visit_data = {
                                    "visit_no": visit["visit_no"],
                                    "customer_id": visit["customer_id"],
                                    "branch_id": st.session_state.branch_id,
                                    "total_paid": visit["total_paid"],
                                    "total_received": visit["total_received"],
                                    "net_cash_amount": visit["net_amount"],
                                    "denomination_details": visit.get("denomination", {}),
                                    "otp_verified": True,
                                    "status": "Submitted_to_Auditor",
                                }
                                visit_res = supabase.table("customer_visits").insert(visit_data).execute()
                                created_visit_id = visit_res.data[0]["id"]

                                for txn in st.session_state.transactions_cart:
                                    txn["visit_id"] = created_visit_id
                                    supabase.table("transactions").insert(txn).execute()

                                supabase.table("audit_records").insert({
                                    "visit_id": created_visit_id,
                                    "document_urls": doc_links,
                                    "audit_status": "Pending",
                                }).execute()

                                st.success("✅ ஆவணங்கள் பதிவேற்றப்பட்டு தணிக்கையருக்கு (Auditor) வெற்றிகரமாக அனுப்பப்பட்டது!")
                                st.session_state.current_visit = None
                                st.session_state.transactions_cart = []
                                st.session_state.generated_otp = None
                                st.rerun()
                            except Exception as err:
                                st.error(f"பிழை ஏற்பட்டது: {err}")
                    else:
                        st.error("குறைந்தது ஒரு ஆவணமாவது இணைக்கப்பட வேண்டும்.")

            with btn_col2:
                if st.button("⬅️ நோட்டு கணக்கீட்டிற்கு பின்செல்க", use_container_width=True):
                    st.session_state.current_visit["step"] = "CASH_OTP"
                    st.rerun()
