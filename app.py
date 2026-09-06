from datetime import datetime, date
import random
import requests
import pandas as pd
import streamlit as st
from supabase import Client, create_client

# பக்க வடிவமைப்பு
st.set_page_config(page_title="Branch Operations System", layout="wide")

# ==============================================================================
# ஹை-லுக் ஆப் தீம் (Native App Feel - Lavender, Deep Violet & Luxury Gold)
# ==============================================================================
st.markdown("""
<style>
    /* 1. பிரவுசர் & Streamlit கட்டுப்பாடுகளை முழுமையாக மறைத்தல் */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    footer, div[data-testid="stStatusWidget"], .viewerBadge_container__r5tak, div[class*="viewerBadge_container"] {
        display: none !important;
    }

    /* 2. ஆப் பின்னணி - மென்மையான லாவெண்டர் மேட் பினிஷ் */
    .stApp {
        background: #F4EFFB !important;
        color: #26153B !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
        -webkit-tap-highlight-color: transparent;
    }

    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 1400px;
        margin: auto;
    }

    /* 3. ஆப் ஸ்டைல் டாப் பார் (Top App Bar Card) */
    div[data-testid="stHorizontalBlock"]:first-of-type {
        background: #FFFFFF !important;
        border-radius: 14px !important;
        padding: 10px 16px !important;
        border: 1px solid #E4D5F7 !important;
        box-shadow: 0 4px 12px rgba(90, 42, 130, 0.06) !important;
        align-items: center;
        margin-bottom: 0.5rem;
    }

    /* 4. முகப்பு கார்டு (Deep Violet Native Card) */
    .login-box {
        background: linear-gradient(145deg, #2D144E 0%, #1E0B36 100%) !important;
        border: 1.5px solid #D4AF37 !important;
        border-radius: 20px !important;
        padding: 32px 28px !important;
        box-shadow: 0 14px 35px rgba(30, 11, 54, 0.35), 0 0 12px rgba(212, 175, 55, 0.25) !important;
        color: #FFFFFF !important;
    }

    .login-box h3 {
        color: #F8E29B !important;
        font-weight: 800 !important;
        text-align: center;
        margin-bottom: 4px;
        letter-spacing: 0.5px;
    }

    .login-box p {
        color: #D3C1EC !important;
        text-align: center;
        font-size: 0.9rem;
        margin-bottom: 22px;
    }

    /* 5. ஆப் ஸ்டைல் உள்ளீட்டுப் புலங்கள் (Inputs & Dropdowns) */
    .stTextInput input, .stNumberInput input {
        background-color: #FFFFFF !important;
        border: 1.5px solid #D6C2F0 !important;
        border-radius: 10px !important;
        color: #24113A !important;
        font-weight: 500 !important;
        height: 42px !important;
        box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.03) !important;
    }

    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #A36B00 !important;
        box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.2) !important;
    }

    .login-box .stTextInput input {
        background-color: #F8F5FD !important;
        border: 1.5px solid #D4AF37 !important;
        color: #200B36 !important;
        font-weight: 600 !important;
    }

    /* 6. தொடு-உணர்வு பட்டன்கள் (Touch Responsive Gold Buttons) */
    button[kind="primary"], .stButton > button[type="primary"] {
        background: linear-gradient(135deg, #D4AF37 0%, #E8CA65 50%, #B8860B 100%) !important;
        color: #2B1800 !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.45rem 1rem !important;
        box-shadow: 0 4px 12px rgba(184, 134, 11, 0.3) !important;
        transition: transform 0.1s ease, box-shadow 0.1s ease !important;
    }

    button[kind="primary"]:active, .stButton > button[type="primary"]:active {
        transform: scale(0.97) !important;
        box-shadow: 0 2px 6px rgba(184, 134, 11, 0.2) !important;
    }

    button[kind="secondary"], .stButton > button {
        background: #FFFFFF !important;
        color: #4A207A !important;
        border: 1.5px solid #C5A059 !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        transition: transform 0.1s ease !important;
    }

    button[kind="secondary"]:active, .stButton > button:active {
        transform: scale(0.97) !important;
    }

    /* 7. ஆப் கார்டுகள் & கண்டெய்னர்கள் (Rounded App Cards) */
    div[data-testid="stExpander"], div[data-testid="stVerticalBlock"] > div[style*="border:"] {
        background: #FFFFFF !important;
        border: 1.5px solid #E1D2F5 !important;
        border-radius: 14px !important;
        box-shadow: 0 3px 12px rgba(74, 32, 122, 0.05) !important;
        overflow: hidden;
    }

    /* 8. மெட்ரிக் கார்டுகள் (Fintech Pill Metrics) */
    div[data-testid="stMetric"] {
        background: #FFFFFF !important;
        border: 1px solid #E8DCF8 !important;
        border-left: 4px solid #D4AF37 !important;
        padding: 8px 14px !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02) !important;
    }

    div[data-testid="stMetricValue"] {
        color: #8C5D00 !important;
        font-weight: 800 !important;
        font-size: 1.3rem !important;
    }

    div[data-testid="stMetricLabel"] {
        color: #4A207A !important;
        font-weight: 600 !important;
    }

    /* 9. ஆப் ஸ்டைல் டேப்கள் (App Nav Tabs) */
    button[data-baseweb="tab"] {
        background: transparent !important;
        color: #613E8D !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        padding: 6px 14px !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #7A4E00 !important;
        background: rgba(212, 175, 55, 0.15) !important;
        font-weight: 700 !important;
        border-bottom: 3px solid #D4AF37 !important;
    }
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
# 2. ஆவணப் பதிவேற்றம், SMS & கல்லா இருப்பு செயல்பாடுகள்
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
        res = (
            supabase.table("customer_visits")
            .select("visit_no")
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
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
    """Fast2SMS DLT (MTHSEG - 219823) மூலம் SMS அனுப்புகிறது"""
    try:
        api_key = "eBGQYanRZNKVCpMSg3KB5kUxY2QhDnOjxesh3Hqr7FOG792XV9wut4TPhQia"
        if "sms" in st.secrets and "fast2sms_api_key" in st.secrets["sms"]:
            api_key = st.secrets["sms"]["fast2sms_api_key"]

        clean_mobile = "".join(filter(str.isdigit, str(mobile_no)))[-10:]

        url = "https://www.fast2sms.com/dev/bulkV2"
        headers = {
            "authorization": api_key.strip(),
            "Content-Type": "application/json",
            "accept": "application/json",
        }

        params_dlt = {
            "route": "dlt",
            "sender_id": "MTHSEG",
            "message": "219823",
            "variables_values": str(otp_code),
            "numbers": clean_mobile,
            "flash": "0",
        }

        resp = requests.get(url, headers=headers, params=params_dlt, timeout=10)
        res_json = resp.json()

        if res_json.get("return") is True:
            return True, "SMS வெற்றிகரமாக அனுப்பப்பட்டது!"

        params_otp = {
            "route": "otp",
            "variables_values": str(otp_code),
            "numbers": clean_mobile,
        }
        resp_fallback = requests.get(url, headers=headers, params=params_otp, timeout=10)
        fallback_json = resp_fallback.json()

        if fallback_json.get("return") is True:
            return True, "SMS வெற்றிகரமாக அனுப்பப்பட்டது!"

        err_msg = res_json.get("message") or fallback_json.get("message") or str(res_json)
        return False, str(err_msg)

    except Exception as e:
        return False, f"இணைப்புப் பிழை: {e}"

def get_current_branch_cash_drawer(branch_id: int):
    """கிளையின் தொடக்க இருப்பு மற்றும் இந்நாள் வரை நடந்த பரிவர்த்தனைகள் கழிந்த நேரடி நோட்டுக் கையிருப்பை கணக்கிடுகிறது"""
    empty_stock = {"500": 0, "200": 0, "100": 0, "50": 0, "20": 0, "10": 0, "5": 0, "coins": 0}
    try:
        box_res = (
            supabase.table("branch_cash_box")
            .select("opening_denomination")
            .eq("branch_id", branch_id)
            .order("entry_date", desc=True)
            .limit(1)
            .execute()
        )
        stock = empty_stock.copy()
        if box_res.data and box_res.data[0].get("opening_denomination"):
            op_data = box_res.data[0]["opening_denomination"]
            for k in stock:
                stock[k] = int(op_data.get(k, 0) or 0)

        visits_res = (
            supabase.table("customer_visits")
            .select("denomination_details")
            .eq("branch_id", branch_id)
            .execute()
        )
        if visits_res.data:
            for row in visits_res.data:
                d_info = row.get("denomination_details")
                if isinstance(d_info, dict):
                    in_notes = d_info.get("in", {})
                    out_notes = d_info.get("out", {})
                    for k in stock:
                        stock[k] += int(in_notes.get(k, 0) or 0)
                        stock[k] -= int(out_notes.get(k, 0) or 0)

        for k in stock:
            stock[k] = max(0, stock[k])

        return stock
    except Exception:
        return empty_stock

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
branch_options = (
    {b["branch_name"]: b["id"] for b in branches_res.data}
    if branches_res.data
    else {}
)
branch_id_to_name = (
    {b["id"]: b["branch_name"] for b in branches_res.data}
    if branches_res.data
    else {}
)

# ==========================================
# 4. உள்நுழைவு திரை (Royal Violet Theme)
# ==========================================
if not st.session_state.logged_in:
    col_left, col_center, col_right = st.columns([1.3, 1.4, 1.3])

    with col_center:
        st.markdown("""
        <div class="login-box">
            <h3>🏦 கிளை சிஸ்டம்</h3>
            <p>பணியாளர் பாதுகாப்பான உள்நுழைவு</p>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("பயனர் பெயர் (Username)", placeholder="Username")
            password = st.text_input("கடவுச்சொல் (Password)", type="password", placeholder="Password")
            submitted = st.form_submit_button("உள்நுழைக (Login)", use_container_width=True, type="primary")

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

                        if role in ["Admin", "Auditor", "Operations"]:
                            b_name = f"Head Office / {role}"
                        else:
                            branch_rel = user_info.get("branches")
                            b_name = branch_rel.get("branch_name") if branch_rel else "ஒதுக்கப்படாத கிளை"

                        if role not in ["Admin", "Auditor", "Operations"] and not b_id:
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

        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 5. முதன்மை திரை
# ==========================================
else:
    top_col1, top_col2, top_col3 = st.columns([3, 2, 1])
    with top_col1:
        st.write(f"🏢 **கிளை:** {st.session_state.branch}")
    with top_col2:
        st.write(f"👤 **பயனர்:** {st.session_state.username} ({st.session_state.user_role})")
    with top_col3:
        if st.button("வெளியேறு (Logout)"):
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
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
            [
                "🏢 கிளைகள்",
                "👥 பணியாளர்கள்",
                "📥 மொத்தப் பதிவேற்றம்",
                "🗂️ வாடிக்கையாளர் மேலாண்மை",
                "📊 வருகை & பரிவர்த்தனை திருத்தம்",
                "💰 கிளை துவக்க இருப்பு & கல்லா"
            ]
        )

        with tab1:
            st.subheader("➕ புதிய கிளை சேர்த்தல்")
            with st.form("admin_add_branch_form", clear_on_submit=True):
                b_name = st.text_input("கிளையின் பெயர் (Branch Name)", placeholder="எ.கா: திங்கள்நகர் கிளை")
                b_code = st.text_input("கிளை குறியீடு (Branch Code)", placeholder="எ.கா: TGL")
                if st.form_submit_button("கிளையைச் சேர் (Add Branch)"):
                    if b_name.strip() and b_code.strip():
                        try:
                            supabase.table("branches").insert({
                                "branch_name": b_name.strip(),
                                "branch_code": b_code.strip().upper(),
                            }).execute()
                            st.success(f"'{b_name}' வெற்றிகரமாகச் சேர்க்கப்பட்டது!")
                            st.rerun()
                        except Exception as err:
                            st.error(f"பிழை: {err}")
                    else:
                        st.warning("கிளையின் பெயர் மற்றும் குறியீட்டை உள்ளிடவும்.")

            b_list_res = supabase.table("branches").select("id, branch_name, branch_code").order("id").execute()
            if b_list_res.data:
                st.dataframe(pd.DataFrame(b_list_res.data), use_container_width=True)

        with tab2:
            st.subheader("👥 பணியாளர்கள் பட்டியல் (Existing Users)")
            users_res = supabase.table("users").select("id, name, username, role, branch_id, is_active").order("id").execute()

            if users_res.data:
                user_table_data = []
                for u in users_res.data:
                    b_name = branch_id_to_name.get(u.get("branch_id"), "Head Office / Special")
                    status_text = "🟢 Active" if u.get("is_active", True) else "🔴 Inactive"
                    user_table_data.append({
                        "ID": u["id"],
                        "பெயர்": u["name"],
                        "Username": u["username"],
                        "பணி நிலை (Role)": u["role"],
                        "கிளை": b_name,
                        "நிலை (Status)": status_text,
                    })
                st.dataframe(pd.DataFrame(user_table_data), use_container_width=True)

            st.markdown("---")
            sub_col1, sub_col2 = st.columns(2)

            with sub_col1:
                st.subheader("➕ புதிய பணியாளர் சேர்த்தல்")
                with st.form("admin_add_user_form", clear_on_submit=True):
                    u_name = st.text_input("பணியாளர் முழுப் பெயர்")
                    u_username = st.text_input("உள்நுழைவு பெயர் (Username)")
                    u_pass = st.text_input("கடவுச்சொல் (Password)", type="password")
                    u_role = st.selectbox(
                        "பணி நிலை (Role)",
                        ["Branch Head / Cashier", "Staff", "Operations", "Auditor", "Admin"],
                        key="admin_new_role",
                    )
                    b_selection = st.selectbox(
                        "கிளையைத் தேர்ந்தெடுக்கவும்",
                        options=list(branch_options.keys()) if branch_options else ["கிளைகள் இல்லை"],
                        key="admin_new_branch",
                    )

                    if st.form_submit_button("பயனாளரை உருவாக்கு (Create User)"):
                        if u_name.strip() and u_username.strip() and u_pass.strip():
                            b_id = branch_options.get(b_selection) if u_role not in ["Admin", "Auditor", "Operations"] else None
                            try:
                                supabase.table("users").insert({
                                    "name": u_name.strip(),
                                    "username": u_username.strip(),
                                    "password_hash": u_pass.strip(),
                                    "role": u_role,
                                    "branch_id": b_id,
                                    "is_active": True,
                                }).execute()
                                st.success(f"'{u_username}' என்ற பயனர் உருவாக்கப்பட்டுவிட்டார்!")
                                st.rerun()
                            except Exception as err:
                                st.error(f"பிழை: {err}")
                        else:
                            st.warning("அனைத்து விவரங்களையும் உள்ளிடவும்.")

            with sub_col2:
                st.subheader("✏️ பணியாளர் விவரங்களை திருத்துதல் (Edit)")
                if users_res.data:
                    user_choices = {f"{u['name']} (@{u['username']})": u for u in users_res.data}
                    selected_user_key = st.selectbox(
                        "திருத்த வேண்டிய பணியாளரைத் தேர்ந்தெடுக்கவும்",
                        list(user_choices.keys()),
                        key="admin_edit_user_select",
                    )
                    curr_user = user_choices[selected_user_key]

                    with st.form("admin_edit_user_form"):
                        edit_name = st.text_input("பெயர்", value=curr_user["name"])
                        edit_pass = st.text_input(
                            "புதிய கடவுச்சொல் (மாற்ற விரும்பினால் மட்டும்)",
                            placeholder="பழைய கடவுச்சொல்லையே தொடர காலியாக விடவும்",
                            type="password",
                        )
                        roles_list = ["Branch Head / Cashier", "Staff", "Operations", "Auditor", "Admin"]
                        role_index = roles_list.index(curr_user["role"]) if curr_user["role"] in roles_list else 0
                        edit_role = st.selectbox("பணி நிலை (Role)", roles_list, index=role_index, key="admin_edit_role_select")

                        current_b_name = branch_id_to_name.get(curr_user.get("branch_id"), list(branch_options.keys())[0] if branch_options else "")
                        b_list_keys = list(branch_options.keys())
                        b_idx = b_list_keys.index(current_b_name) if current_b_name in b_list_keys else 0
                        edit_branch = st.selectbox("கிளை", options=b_list_keys, index=b_idx, key="admin_edit_branch_select")

                        edit_status = st.radio(
                            "பயனர் நிலை (Status)",
                            ["Active (செயலில் உள்ளார்)", "Inactive (முடக்கு)"],
                            index=0 if curr_user.get("is_active", True) else 1,
                            key="admin_edit_status_radio",
                        )

                        if st.form_submit_button("மாற்றங்களைச் சேமி (Update User)", type="primary"):
                            try:
                                update_payload = {
                                    "name": edit_name.strip(),
                                    "role": edit_role,
                                    "branch_id": branch_options.get(edit_branch) if edit_role not in ["Admin", "Auditor", "Operations"] else None,
                                    "is_active": True if "Active" in edit_status else False,
                                }
                                if edit_pass.strip():
                                    update_payload["password_hash"] = edit_pass.strip()

                                supabase.table("users").update(update_payload).eq("id", curr_user["id"]).execute()
                                st.success("பணியாளர் விவரங்கள் புதுப்பிக்கப்பட்டன!")
                                st.rerun()
                            except Exception as err:
                                st.error(f"புதுப்பிப்பதில் பிழை: {err}")

        with tab3:
            st.subheader("📥 பழைய வாடிக்கையாளர் அறிக்கையைப் பதிவேற்றுதல் (Customer Report Import)")
            uploaded_cust_file = st.file_uploader("Customer Report Excel கோப்பைத் தேர்வு செய்யவும்", type=["xls", "xlsx", "csv"], key="admin_customer_report_uploader")

            if uploaded_cust_file:
                try:
                    df_raw = pd.read_csv(uploaded_cust_file, skiprows=2) if uploaded_cust_file.name.endswith(".csv") else pd.read_excel(uploaded_cust_file, skiprows=2)
                    df_cust = df_raw.dropna(subset=["Full Name", "Mobile No"]).copy()
                    st.success(f"📊 மொத்த வாடிக்கையாளர்கள் கண்டறியப்பட்டனர்: **{len(df_cust)}**")

                    if st.button("🚀 அனைத்து வாடிக்கையாளர்களையும் டேட்டாபேஸில் உடனே இணை (Start Bulk Upload)", type="primary"):
                        all_b = supabase.table("branches").select("id, branch_code").execute()
                        b_code_to_id = {b["branch_code"].strip().upper(): b["id"] for b in all_b.data} if all_b.data else {}

                        records_to_insert = []
                        seen_codes = set()

                        for idx, row in df_cust.iterrows():
                            b_code = str(row.get("Branch", "")).strip().upper()
                            target_branch_id = b_code_to_id.get(b_code)

                            raw_c_no = str(row.get("Customer No", "")).replace(".0", "").strip()
                            if not raw_c_no or raw_c_no in ["0", "nan"]:
                                c_code = f"{b_code}-0-{idx+1}"
                            else:
                                c_code = f"{b_code}-{raw_c_no}"

                            if c_code in seen_codes:
                                c_code = f"{c_code}-{idx+1}"
                            seen_codes.add(c_code)

                            mob2 = str(row.get("Secondary No", "")).replace(".0", "").strip() if pd.notna(row.get("Secondary No")) else ""

                            records_to_insert.append({
                                "branch_id": target_branch_id,
                                "customer_code": c_code,
                                "name": str(row.get("Full Name", "")).strip(),
                                "guardian_name": str(row.get("Guardian", "")).strip() if pd.notna(row.get("Guardian")) else "",
                                "gender": str(row.get("Gender", "Male")).strip(),
                                "mobile": str(row.get("Mobile No", "")).replace(".0", "").strip(),
                                "mobile2": mob2,
                                "address": str(row.get("Comm Address", "")).strip() if pd.notna(row.get("Comm Address")) else "",
                                "nominee_relation": str(row.get("Relation", "")).strip() if pd.notna(row.get("Relation")) else "",
                                "is_active": True,
                            })

                        batch_size = 100
                        for i in range(0, len(records_to_insert), batch_size):
                            batch = records_to_insert[i : i + batch_size]
                            supabase.table("customers").upsert(batch, on_conflict="customer_code").execute()

                        st.success(f"✅ **{len(records_to_insert)} வாடிக்கையாளர்கள்** வெற்றிகரமாகப் பதிவேற்றப்பட்டனர்!")
                        st.rerun()
                except Exception as e:
                    st.error(f"பதிவேற்றுவதில் பிழை: {e}")

        with tab4:
            st.subheader("🗂️ வாடிக்கையாளர் பட்டியல் & திருத்தம் (Customer Directory & Control)")

            filter_col1, filter_col2 = st.columns([2, 3])
            with filter_col1:
                branch_filter_options = ["அனைத்து கிளைகளும் (All Branches)"] + list(branch_options.keys())
                selected_b_filter = st.selectbox("கிளை வாரியாகப் பார்க்க:", branch_filter_options, key="admin_cust_b_filter")

            with filter_col2:
                admin_search_q = st.text_input("வாடிக்கையாளர் பெயர் / மொபைல் / Customer Code தேடுக:", placeholder="எ.கா: MYL-1 அல்லது ராம்", key="admin_cust_search")

            cust_query = supabase.table("customers").select("id, customer_code, name, mobile, mobile2, guardian_name, gender, address, nominee_relation, branch_id, is_active").order("id", desc=True)
            if selected_b_filter != "அனைத்து கிளைகளும் (All Branches)":
                cust_query = cust_query.eq("branch_id", branch_options.get(selected_b_filter))

            if admin_search_q.strip():
                sq = admin_search_q.strip()
                cust_query = cust_query.or_(f"name.ilike.%{sq}%,mobile.ilike.%{sq}%,customer_code.ilike.%{sq}%")
            else:
                cust_query = cust_query.limit(200)

            data_view = cust_query.execute().data or []
            st.write(f"📊 கண்டறியப்பட்ட வாடிக்கையாளர்கள்: **{len(data_view)}** (அதிகபட்சம் 200 பதிவுகள்)")

            if data_view:
                st.dataframe(pd.DataFrame([{
                    "ID": cv["id"],
                    "Code": cv.get("customer_code", "-"),
                    "பெயர்": cv["name"],
                    "மொபைல்": cv.get("mobile", "-"),
                    "கார்டியன் பெயர்": cv.get("guardian_name", "-"),
                    "கிளை": branch_id_to_name.get(cv.get("branch_id"), "பொது"),
                    "நிலை": "🟢 Active" if cv.get("is_active", True) else "🔴 Inactive",
                    "முகவரி": cv.get("address", "-"),
                } for cv in data_view]), use_container_width=True)

                st.markdown("---")
                st.subheader("✏️ வாடிக்கையாளர் விவரங்களைத் திருத்துதல் & நிலை மாற்றம் (Edit / Status)")

                cust_edit_choices = {f"{c.get('customer_code', '')} - {c['name']} ({c.get('mobile', '')})": c for c in data_view}
                selected_edit_cust_label = st.selectbox("திருத்த வேண்டிய வாடிக்கையாளரைத் தேர்ந்தெடுக்கவும்:", list(cust_edit_choices.keys()), key="admin_edit_cust_dropdown")
                target_cust = cust_edit_choices[selected_edit_cust_label]

                with st.form("admin_edit_customer_form"):
                    ec_col1, ec_col2, ec_col3 = st.columns(3)

                    with ec_col1:
                        edit_c_name = st.text_input("வாடிக்கையாளர் பெயர்", value=target_cust.get("name", ""))
                        edit_c_guard = st.text_input("கார்டியன் பெயர்", value=target_cust.get("guardian_name", "") or "")
                        gender_opts = ["Male", "Female", "Other", "ஆண்", "பெண்"]
                        curr_g = target_cust.get("gender", "Male")
                        g_idx = gender_opts.index(curr_g) if curr_g in gender_opts else 0
                        edit_c_gender = st.selectbox("பாலினம்", gender_opts, index=g_idx)

                    with ec_col2:
                        edit_c_mob = st.text_input("முதன்மை மொபைல்", value=str(target_cust.get("mobile", "") or ""))
                        edit_c_mob2 = st.text_input("கூடுதல் மொபைல் / Whatsapp", value=str(target_cust.get("mobile2", "") or ""))
                        curr_c_bname = branch_id_to_name.get(target_cust.get("branch_id"), list(branch_options.keys())[0] if branch_options else "")
                        b_keys = list(branch_options.keys())
                        b_sel_idx = b_keys.index(curr_c_bname) if curr_c_bname in b_keys else 0
                        edit_c_branch = st.selectbox("ஒதுக்கப்பட்ட கிளை", b_keys, index=b_sel_idx)

                    with ec_col3:
                        edit_c_addr = st.text_area("முகவரி", value=target_cust.get("address", "") or "", height=68)
                        edit_c_status = st.radio(
                            "வாடிக்கையாளர் நிலை (Status)",
                            ["Active (செயலில் உள்ளார்)", "Inactive (முடக்கு)"],
                            index=0 if target_cust.get("is_active", True) else 1,
                            key="admin_cust_status_radio",
                        )

                    if st.form_submit_button("வாடிக்கையாளர் விவரங்களை சேமி (Update Customer)", type="primary"):
                        try:
                            cust_update_data = {
                                "name": edit_c_name.strip(),
                                "guardian_name": edit_c_guard.strip(),
                                "gender": edit_c_gender,
                                "mobile": edit_c_mob.strip(),
                                "mobile2": edit_c_mob2.strip(),
                                "address": edit_c_addr.strip(),
                                "branch_id": branch_options.get(edit_c_branch),
                                "is_active": True if "Active" in edit_c_status else False,
                            }
                            supabase.table("customers").update(cust_update_data).eq("id", target_cust["id"]).execute()
                            st.success("வாடிக்கையாளர் விவரங்கள் வெற்றிகரமாக மாற்றப்பட்டன!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"சேமிப்பதில் பிழை: {e}")
            else:
                st.info("தேர்ந்தெடுக்கப்பட்ட பிரிவில் வாடிக்கையாளர்கள் இல்லை.")

        with tab5:
            st.subheader("📊 வருகை & பரிவர்த்தனை மேலாண்மை (Admin Control)")
            v_search = st.text_input("வருகை எண் உள்ளிடவும்:", placeholder="எ.கா: VST-1001", key="admin_v_search")
            vq = supabase.table("customer_visits").select("*, customers(name, mobile), transactions(*)").order("id", desc=True)
            if v_search.strip():
                vq = vq.ilike("visit_no", f"%{v_search.strip()}%")
            else:
                vq = vq.limit(20)
            v_records = vq.execute().data or []

            for vr in v_records:
                c_name = vr.get("customers", {}).get("name", "Unknown") if vr.get("customers") else "Unknown"
                with st.expander(f"வருகை: {vr['visit_no']} | வாடிக்கையாளர்: {c_name} | நிகர தொகை: ₹{vr['net_cash_amount']:,.2f} | நிலை: {vr['status']}"):
                    if vr.get("transactions"):
                        st.dataframe(pd.DataFrame(vr["transactions"]))
                    act_c1, act_c2 = st.columns(2)
                    with act_c1:
                        new_st = st.selectbox(
                            "நிலையை மாற்று:",
                            ["Pending_Calling_Verification", "Pending_Branch_Docs", "Submitted_to_Auditor", "Approved", "Cancelled"],
                            index=["Pending_Calling_Verification", "Pending_Branch_Docs", "Submitted_to_Auditor", "Approved", "Cancelled"].index(vr["status"]) if vr["status"] in ["Pending_Calling_Verification", "Pending_Branch_Docs", "Submitted_to_Auditor", "Approved", "Cancelled"] else 0,
                            key=f"st_sel_{vr['id']}"
                        )
                        if st.button("நிலையைப் புதுப்பி", key=f"up_st_{vr['id']}"):
                            supabase.table("customer_visits").update({"status": new_st}).eq("id", vr["id"]).execute()
                            st.success("நிலை புதுப்பிக்கப்பட்டது!")
                            st.rerun()
                    with act_c2:
                        st.write("🗑️ **வருகையை நீக்குதல்:**")
                        if st.button(f"🚨 நிரந்தரமாக நீக்கு ({vr['visit_no']})", key=f"del_adm_v_{vr['id']}"):
                            supabase.table("audit_records").delete().eq("visit_id", vr["id"]).execute()
                            supabase.table("transactions").delete().eq("visit_id", vr["id"]).execute()
                            supabase.table("customer_visits").delete().eq("id", vr["id"]).execute()
                            st.success(f"{vr['visit_no']} நீக்கப்பட்டது!")
                            st.rerun()

        with tab6:
            st.subheader("💰 கிளை துவக்க இருப்பு மற்றும் நோட்டுகள் நிர்ணயம் (Opening Cash Box Entry)")
            st.caption("ஒவ்வொரு கிளையின் தொடக்க ரொக்கக் கையிருப்பு மற்றும் நோட்டுகளின் எண்ணிக்கையை அட்மின் இங்கே பதிவு செய்யலாம்.")

            sel_op_branch = st.selectbox("துவக்க இருப்பு பதிவு செய்ய வேண்டிய கிளை:", list(branch_options.keys()), key="sel_op_branch")
            target_b_id = branch_options[sel_op_branch]
            entry_dt = st.date_input("துவக்க இருப்பு தேதி (Date):", value=date.today(), key="op_date_entry")

            with st.form("admin_opening_cash_form"):
                st.markdown("##### 💵 நோட்டுகள் எண்ணிக்கை (Opening Denominations)")
                op1, op2, op3, op4 = st.columns(4)
                with op1:
                    op_500 = st.number_input("₹500 நோட்டுகள்", min_value=0, step=1, key="op_500")
                    op_20 = st.number_input("₹20 நோட்டுகள்", min_value=0, step=1, key="op_20")
                with op2:
                    op_200 = st.number_input("₹200 நோட்டுகள்", min_value=0, step=1, key="op_200")
                    op_10 = st.number_input("₹10 நோட்டுகள்", min_value=0, step=1, key="op_10")
                with op3:
                    op_100 = st.number_input("₹100 நோட்டுகள்", min_value=0, step=1, key="op_100")
                    op_5 = st.number_input("₹5 நோட்டுகள்", min_value=0, step=1, key="op_5")
                with op4:
                    op_50 = st.number_input("₹50 நோட்டுகள்", min_value=0, step=1, key="op_50")
                    op_coins = st.number_input("நாணயங்கள் (Coins ₹)", min_value=0, step=1, key="op_coins")

                total_opening_calc = (
                    (op_500 * 500) + (op_200 * 200) + (op_100 * 100) + (op_50 * 50) +
                    (op_20 * 20) + (op_10 * 10) + (op_5 * 5) + op_coins
                )

                st.markdown("---")
                st.info(f"📊 **கணக்கிடப்பட்ட மொத்த துவக்க இருப்பு (Total Opening Cash): ₹{total_opening_calc:,.2f}**")

                if st.form_submit_button("💾 துவக்க இருப்பை உறுதிசெய்து சேமி (Save Opening Balance)", type="primary"):
                    payload = {
                        "branch_id": target_b_id,
                        "entry_date": str(entry_dt),
                        "opening_balance": float(total_opening_calc),
                        "opening_denomination": {
                            "500": op_500, "200": op_200, "100": op_100, "50": op_50,
                            "20": op_20, "10": op_10, "5": op_5, "coins": op_coins
                        }
                    }
                    try:
                        supabase.table("branch_cash_box").upsert(payload, on_conflict="branch_id,entry_date").execute()
                        st.success(f"✅ {sel_op_branch} கிளைக்கான துவக்க இருப்பு ₹{total_opening_calc:,.2f} வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"சேமிப்பதில் பிழை: {err}")

            st.markdown("---")
            st.subheader("📋 கிளை வாரியான துவக்க இருப்புப் பதிவுகள்")
            existing_boxes = supabase.table("branch_cash_box").select("*, branches(branch_name)").order("entry_date", desc=True).limit(20).execute().data or []
            if existing_boxes:
                view_records = []
                for box in existing_boxes:
                    view_records.append({
                        "தேதி": box["entry_date"],
                        "கிளை": box.get("branches", {}).get("branch_name", "-"),
                        "துவக்க இருப்பு (₹)": f"₹{box['opening_balance']:,.2f}",
                        "நோட்டுகள் விவரம்": str(box.get("opening_denomination", {}))
                    })
                st.dataframe(pd.DataFrame(view_records), use_container_width=True)

    # ----------------------------------------------------
    # B. அழைப்பு சரிபார்ப்பு திரை (OPERATIONS CALLING DESK)
    # ----------------------------------------------------
    elif st.session_state.user_role == "Operations":
        st.header("📞 ஆப்பரேஷன்ஸ் அழைப்பு சரிபார்ப்பு (Operations Calling Desk)")
        ops_visits = supabase.table("customer_visits").select("*, customers(*), transactions(*), branches(branch_name)").eq("status", "Pending_Calling_Verification").order("id").execute().data or []

        if not ops_visits:
            st.info("✅ அழைப்பு சரிபார்ப்புக்கு புதிய வாடிக்கையாளர் வருகைகள் ஏதுமில்லை.")
        else:
            st.write(f"📊 நிலுவையில் உள்ள அழைப்புகள்: **{len(ops_visits)}**")
            for item in ops_visits:
                cust = item.get("customers", {})
                b_name = item.get("branches", {}).get("branch_name", "Branch")
                with st.expander(f"🔔 வருகை எண்: {item['visit_no']} | கிளை: {b_name} | வாடிக்கையாளர்: {cust.get('name')} | நிகர ரொக்கம்: ₹{item['net_cash_amount']:,.2f}"):
                    c_col1, c_col2 = st.columns([1.5, 1])
                    with c_col1:
                        st.write(f"👤 **வாடிக்கையாளர் பெயர்:** {cust.get('name')}")
                        st.write(f"📞 **அழைக்க வேண்டிய எண்:** `{cust.get('mobile')}` | **கூடுதல் எண்:** `{cust.get('mobile2', '-')}`")
                        st.write(f"🏠 **முகவரி:** {cust.get('address', '-')}")
                        st.write(f"👨‍👦 **கார்டியன்:** {cust.get('guardian_name', '-')}")
                    with c_col2:
                        st.write(f"💰 **பரிவர்த்தனை நிகர தொகை:** ₹{item['net_cash_amount']:,.2f}")
                        st.write(f"🕒 **கவுண்ட்டர் நேரம்:** {item['created_at']}")

                    st.markdown("##### 📌 பரிவர்த்தனை விவரங்கள்:")
                    if item.get("transactions"):
                        st.dataframe(pd.DataFrame(item["transactions"])[["transaction_type", "paid_amount", "received_amount", "remarks"]], use_container_width=True)

                    btn_op1, btn_op2 = st.columns(2)
                    with btn_op1:
                        if st.button("✅ வாடிக்கையாளர் அழைப்பு சரிபார்க்கப்பட்டது (Call Verified)", key=f"v_call_{item['id']}", type="primary"):
                            supabase.table("customer_visits").update({
                                "status": "Pending_Branch_Docs"
                            }).eq("id", item["id"]).execute()
                            st.success(f"{item['visit_no']} சரிபார்க்கப்பட்டது! கிளை ஆவணங்கள் பதிவேற்றத்திற்கு அனுப்பப்பட்டது.")
                            st.rerun()
                    with btn_op2:
                        if st.button("⚠️ சந்தேகம் / மறுப்பு (Flag Issue)", key=f"flag_call_{item['id']}"):
                            supabase.table("customer_visits").update({
                                "status": "Needs_Clarification"
                            }).eq("id", item["id"]).execute()
                            st.warning("விளக்கம் கோரப்பட்டுள்ளது.")
                            st.rerun()

    # ----------------------------------------------------
    # C. தணிக்கையர் திரை (AUDITOR DESK)
    # ----------------------------------------------------
    elif st.session_state.user_role == "Auditor":
        st.header("🔍 தணிக்கையர் பணிப்பாய்வு (Auditor Verification)")
        response = supabase.table("customer_visits").select("*, customers(name, mobile), transactions(*), audit_records(*)").eq("status", "Submitted_to_Auditor").execute()
        pending_visits = response.data or []

        if not pending_visits:
            st.info("தணிக்கை செய்ய எந்த ஆவணங்களும் வரவில்லை.")
        else:
            for item in pending_visits:
                c_name = item.get("customers", {}).get("name", "Customer")
                with st.expander(f"வருகை எண்: {item['visit_no']} | வாடிக்கையாளர்: {c_name} | நிகர ரொக்கம்: ₹{item['net_cash_amount']:,.2f}"):
                    st.write(f"**பதிவு நேரம்:** {item['created_at']}")
                    st.write("### 📌 வணிக நடவடிக்கைகள்:")
                    if item.get("transactions"):
                        st.dataframe(pd.DataFrame(item["transactions"]))

                    st.write("### 📁 இணைக்கப்பட்ட ஆவணங்கள்:")
                    audit_recs = item.get("audit_records", [])
                    if audit_recs and audit_recs[0].get("document_urls"):
                        for doc_url in audit_recs[0]["document_urls"]:
                            st.markdown(f"- 🔗 [ஆவணத்தைப் பார்க்க கிளிக் செய்யவும்]({doc_url})")
                    else:
                        st.write("ஆவணங்கள் ஏதுமில்லை.")

                    col_a1, col_a2 = st.columns(2)
                    with col_a1:
                        if st.button(f"அங்கீகரி (Approve) - {item['visit_no']}", key=f"app_{item['id']}"):
                            supabase.table("customer_visits").update({"status": "Approved"}).eq("id", item["id"]).execute()
                            supabase.table("audit_records").update({
                                "audit_status": "Approved",
                                "auditor_name": st.session_state.username,
                                "audited_at": datetime.now().isoformat(),
                            }).eq("visit_id", item["id"]).execute()
                            st.success(f"{item['visit_no']} அங்கீகரிக்கப்பட்டது!")
                            st.rerun()
                    with col_a2:
                        if st.button("விளக்கம் கேள் (Need Clarification)", key=f"rej_{item['id']}"):
                            supabase.table("customer_visits").update({"status": "Needs_Clarification"}).eq("id", item["id"]).execute()
                            st.warning("விளக்கம் கேட்கப்பட்டது.")
                            st.rerun()

    # ----------------------------------------------------
    # D. கிளை செயல்பாடுகள் திரை (BRANCH FLOW)
    # ----------------------------------------------------
    else:
        branch_tab1, branch_tab2, branch_tab3 = st.tabs([
            "🛒 கவுண்ட்டர் வருகை & OTP",
            "📁 கிளை ஆவணங்கள் பதிவேற்றம் (Doc Desk)",
            "💼 கிளை கல்லா & டினாமினேசன் நிலை (Cash Drawer)"
        ])

        with branch_tab3:
            st.subheader("💼 கிளை கல்லா கையிருப்பு & டினாமினேசன் நிலை")
            curr_stock = get_current_branch_cash_drawer(st.session_state.branch_id)
            total_stock_val = (
                (curr_stock["500"] * 500) + (curr_stock["200"] * 200) + (curr_stock["100"] * 100) +
                (curr_stock["50"] * 50) + (curr_stock["20"] * 20) + (curr_stock["10"] * 10) +
                (curr_stock["5"] * 5) + curr_stock["coins"]
            )
            st.metric("கல்லாவில் தற்போது உள்ள மொத்த ரொக்கம்", f"₹{total_stock_val:,.2f}")
            st.markdown("##### 💵 தற்போதைய நோட்டுகள் எண்ணிக்கை (Live Stock):")
            c_s1, c_s2, c_s3, c_s4 = st.columns(4)
            c_s1.metric("₹500 தாள்கள்", f"{curr_stock['500']}")
            c_s1.metric("₹20 தாள்கள்", f"{curr_stock['20']}")
            c_s2.metric("₹200 தாள்கள்", f"{curr_stock['200']}")
            c_s2.metric("₹10 தாள்கள்", f"{curr_stock['10']}")
            c_s3.metric("₹100 தாள்கள்", f"{curr_stock['100']}")
            c_s3.metric("₹5 தாள்கள்", f"{curr_stock['5']}")
            c_s4.metric("₹50 தாள்கள்", f"{curr_stock['50']}")
            c_s4.metric("நாணயங்கள் (Coins)", f"₹{curr_stock['coins']:,.2f}")

        with branch_tab2:
            st.subheader("📁 கிளை ஆவணங்கள் பதிவேற்றம் (Upload Docs Desk)")
            st.caption("OTP முடிந்து, ஆப்பரேஷன்ஸ் அழைப்பு உறுதி செய்யப்பட்ட வருகைகளுக்கு இங்கே ஓய்வான நேரத்தில் ஆவணங்களை இணைக்கலாம்.")

            branch_pending = supabase.table("customer_visits").select("*, customers(name, mobile), transactions(*)").eq("branch_id", st.session_state.branch_id).in_("status", ["Pending_Branch_Docs", "Pending_Calling_Verification"]).order("id", desc=True).execute().data or []

            if not branch_pending:
                st.info("தற்போது ஆவணங்கள் ஏற்ற வேண்டிய வருகைகள் எதுவும் இல்லை.")
            else:
                for b_item in branch_pending:
                    c_info = b_item.get("customers", {})
                    st_badge = "🟢 ஆப்பரேஷன் சரிபார்க்கப்பட்டது" if b_item["status"] == "Pending_Branch_Docs" else "🟡 அழைப்பு சரிபார்ப்பில் உள்ளது"
                    with st.expander(f"📄 வருகை: {b_item['visit_no']} | வாடிக்கையாளர்: {c_info.get('name')} | தொகை: ₹{b_item['net_cash_amount']:,.2f} | {st_badge}"):
                        st.write(f"📞 மொபைல்: {c_info.get('mobile')} | தேதி: {b_item['created_at']}")
                        if b_item.get("transactions"):
                            st.dataframe(pd.DataFrame(b_item["transactions"])[["transaction_type", "paid_amount", "received_amount", "remarks"]], use_container_width=True)

                        up_docs = st.file_uploader(f"ஆவணங்களை இணைக்கவும் - {b_item['visit_no']}", accept_multiple_files=True, key=f"doc_up_{b_item['id']}")

                        if st.button(f"ஆவணங்களைச் சமர்ப்பித்து தணிக்கைக்கு அனுப்புக ({b_item['visit_no']})", key=f"btn_sub_{b_item['id']}", type="primary"):
                            if up_docs:
                                with st.spinner("ஆவணங்கள் பதிவேற்றப்படுகின்றன..."):
                                    links = upload_files_to_supabase(up_docs, b_item["visit_no"])
                                    supabase.table("customer_visits").update({"status": "Submitted_to_Auditor"}).eq("id", b_item["id"]).execute()
                                    supabase.table("audit_records").insert({
                                        "visit_id": b_item["id"],
                                        "document_urls": links,
                                        "audit_status": "Pending"
                                    }).execute()
                                    st.success("✅ ஆவணங்கள் வெற்றிகரமாகத் தணிக்கைக்கு (Auditor) அனுப்பப்பட்டுவிட்டன!")
                                    st.rerun()
                            else:
                                st.error("குறைந்தது ஒரு ஆவணமாவது தேர்ந்தெடுக்கப்பட வேண்டும்.")

        with branch_tab1:
            staff_res = supabase.table("users").select("name").eq("branch_id", st.session_state.branch_id).eq("is_active", True).execute()
            current_staff_list = ["Walk-in (நேரடி வருகை)"] + [s["name"] for s in staff_res.data] if staff_res.data else ["Walk-in (நேரடி வருகை)"]

            if st.session_state.current_visit is None:
                st.subheader("படி 1: வாடிக்கையாளர் வருகைப் பதிவு (Visit Token)")

                visit_type = st.radio(
                    "வாடிக்கையாளர் வகை:",
                    ["ஏற்கனவே உள்ள வாடிக்கையாளர் (Existing Customer)", "புதிய வாடிக்கையாளர் பதிவு (New Customer)"],
                    horizontal=True,
                )

                if "Existing" in visit_type:
                    st.markdown("##### 🔍 வாடிக்கையாளர் தேடல்")
                    search_query = st.text_input(
                        "பெயர் / மொபைல் எண் / Customer ID உள்ளிடவும்:", 
                        placeholder="எ.கா: ராம் அல்லது 98765...",
                        key="live_cust_search_input"
                    )

                    if len(search_query.strip()) >= 2:
                        q = search_query.strip()
                        cust_filter_query = supabase.table("customers").select("*").eq("is_active", True)
                        if st.session_state.user_role not in ["Admin", "Auditor", "Operations"]:
                            cust_filter_query = cust_filter_query.eq("branch_id", st.session_state.branch_id)

                        matched_custs = (
                            cust_filter_query
                            .or_(f"name.ilike.%{q}%,mobile.ilike.%{q}%,customer_code.ilike.%{q}%")
                            .limit(20)
                            .execute()
                        )

                        if matched_custs.data:
                            cust_dropdown_dict = {
                                f"{c['name']} | {c.get('customer_code', '')} | 📞 {c.get('mobile', '')}": c 
                                for c in matched_custs.data
                            }
                            selected_label = st.selectbox(
                                "பொருந்தும் வாடிக்கையாளர் பட்டியல்:",
                                options=list(cust_dropdown_dict.keys()),
                                key="dropdown_cust_select"
                            )
                            selected_cust = cust_dropdown_dict[selected_label]

                            with st.container(border=True):
                                c_col1, c_col2, c_col3 = st.columns([1, 2.5, 1])
                                with c_col1:
                                    if selected_cust.get("photo_url"):
                                        st.image(selected_cust["photo_url"], width=120)
                                    else:
                                        st.info("📷 படம் இல்லை")
                                with c_col2:
                                    st.markdown(f"### {selected_cust['name']} <small style='color:gray;'>({selected_cust.get('customer_code', 'CUST-ID')})</small>", unsafe_allow_html=True)
                                    st.write(f"📞 **முதன்மை மொபைல்:** {selected_cust.get('mobile', '-')} | **கூடுதல் மொபைல்:** {selected_cust.get('mobile2', '-')}")
                                    st.write(f"👨‍👦 **கார்டியன் பெயர்:** {selected_cust.get('guardian_name', '-')} | **பாலினம்:** {selected_cust.get('gender', '-')}")
                                    st.write(f"🏠 **முகவரி:** {selected_cust.get('address', '-')}")
                                with c_col3:
                                    st.write("")
                                    st.write("")
                                    if st.button("வருகையைத் தொடங்கு ➔", key=f"start_visit_{selected_cust['id']}", type="primary", use_container_width=True):
                                        st.session_state.current_visit = {
                                            "visit_no": generate_short_visit_no(),
                                            "customer_id": selected_cust["id"],
                                            "customer_name": selected_cust["name"],
                                            "customer_code": selected_cust.get("customer_code", ""),
                                            "mobile": selected_cust.get("mobile", ""),
                                            "step": "TRANSACTIONS",
                                        }
                                        st.rerun()
                        else:
                            st.warning("பொருந்தும் வாடிக்கையாளர் விவரங்கள் எதுவும் இல்லை.")

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
                            new_id_no = st.text_input("அடையாள எண் (ID No)")
                            new_photo = st.file_uploader("வாடிக்கையாளர் புகைப்படம் (Photo)", type=["jpg", "jpeg", "png"])

                        with col_n3:
                            new_address = st.text_area("முழு முகவரி (Address)", height=100)
                            new_nominee = st.text_input("நாமினி பெயர் (Nominee Name)")
                            new_relation = st.text_input("உறவுமுறை (Nominee Relation)")

                        if st.form_submit_button("வாடிக்கையாளரைப் பதிவு செய்து வருகையைத் தொடங்கு ➔", type="primary"):
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
                                    cust_insert_res = supabase.table("customers").insert({
                                        "branch_id": st.session_state.branch_id,
                                        "customer_code": timestamp_code,
                                        "name": new_name.strip(),
                                        "guardian_name": new_guardian.strip(),
                                        "dob": str(new_dob),
                                        "gender": new_gender,
                                        "mobile": new_mob1.strip(),
                                        "mobile2": new_mob2.strip(),
                                        "aadhaar": new_id_no.strip(),
                                        "address": new_address.strip(),
                                        "nominee_name": new_nominee.strip(),
                                        "nominee_relation": new_relation.strip(),
                                        "photo_url": photo_url,
                                        "is_active": True,
                                    }).execute()

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
                                        st.success(f"வாடிக்கையாளர் எண் {timestamp_code} பதிவு செய்யப்பட்டார்!")
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"பதிவு செய்வதில் பிழை: {e}")
                            else:
                                st.error("பெயர் மற்றும் முதன்மை மொபைல் எண் கட்டாயம் தேவை.")

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
                        custom_remarks = st.text_input("கூடுதல் குறிப்பு (Optional Remarks):", placeholder="எ.கா: சிறப்பு தள்ளுபடி")

                    st.markdown("---")

                    paid_amt = 0.0
                    received_amt = 0.0
                    detail_summary = []

                    if txn_category == "Pledge (புதிய நகைக் கடன்)":
                        st.markdown("##### 🪙 புதிய நகைக் கடன் விவரங்கள்")
                        p_col1, p_col2, p_col3 = st.columns(3)
                        with p_col1:
                            new_gl_no = st.text_input("புதிய கடன் எண் (GL No) *")
                            scheme_name = st.selectbox("வட்டி திட்டம்", ["ஸ்கீம் A (12%)", "ஸ்கீம் B (15%)", "ஸ்கீம் C (18%)", "மாதாந்திர ஸ்கீம்"])
                        with p_col2:
                            gross_wt = st.number_input("மொத்த எடை (Gross Weight - gms) *", min_value=0.0, step=0.1, format="%.2f")
                            net_wt = st.number_input("நிகர எடை (Net Weight - gms) *", min_value=0.0, step=0.1, format="%.2f")
                        with p_col3:
                            item_count = st.number_input("நகை எண்ணிக்கை", min_value=1, step=1)
                            paid_amt = st.number_input("கடன் தொகை (Paid Amount ₹) *", min_value=0.0, step=500.0)

                        detail_summary = [f"GL: {new_gl_no}", f"ஸ்கீம்: {scheme_name}", f"மொத்த எடை: {gross_wt}g", f"நிகர எடை: {net_wt}g", f"எண்ணிக்கை: {item_count}"]

                    elif txn_category == "GL Release (அடமானம் மீட்டல்)":
                        st.markdown("##### 🔓 அடகு மீட்டல் கணக்கீடு")
                        r_col1, r_col2 = st.columns(2)
                        with r_col1:
                            rel_gl_no = st.text_input("மீட்கப்படும் கடன் எண் (GL No) *")
                            principal_amt = st.number_input("அசல் தொகை (₹) *", min_value=0.0, step=500.0)
                        with r_col2:
                            interest_amt = st.number_input("வட்டித் தொகை (₹) *", min_value=0.0, step=50.0)
                            other_charges = st.number_input("இதர கட்டணம் (₹)", min_value=0.0, step=10.0)

                        received_amt = principal_amt + interest_amt + other_charges
                        st.info(f"💰 வாடிக்கையாளர் செலுத்த வேண்டிய மொத்தத் தொகை (வரவு): **₹{received_amt:,.2f}**")
                        detail_summary = [f"GL: {rel_gl_no}", f"அசல்: ₹{principal_amt}", f"வட்டி: ₹{interest_amt}"]

                    elif txn_category in ["Interest Payment (வட்டி வரவு)", "Part Payment (அசல் வரவு)"]:
                        st.markdown(f"##### 💵 {txn_category} விவரங்கள்")
                        i_col1, i_col2 = st.columns(2)
                        with i_col1:
                            part_gl_no = st.text_input("கடன் எண் (GL No) *")
                        with i_col2:
                            received_amt = st.number_input(f"செலுத்திய தொகை ({txn_category} ₹) *", min_value=0.0, step=100.0)
                        detail_summary = [f"GL: {part_gl_no}"]

                    elif txn_category == "Take Over (பிற நிறுவன கடன் மீட்டல்)":
                        st.markdown("##### 🏦 பிற நிறுவன கடன் மீட்பு விவரங்கள்")
                        to_col1, to_col2 = st.columns(2)
                        with to_col1:
                            bank_source = st.text_input("முந்தைய வங்கி / நிறுவனம் *")
                            prev_loan_no = st.text_input("முந்தைய லோன் எண் *")
                        with to_col2:
                            approx_wt = st.number_input("தோராய எடை (Grams)", min_value=0.0, step=0.1)
                            paid_amt = st.number_input("மீட்பிற்கு செலுத்திய தொகை (Paid ₹) *", min_value=0.0, step=500.0)
                        detail_summary = [f"வங்கி: {bank_source}", f"பழைய எண்: {prev_loan_no}", f"எடை: {approx_wt}g"]

                    elif "RD" in txn_category or "FD" in txn_category:
                        st.markdown(f"##### 📑 {txn_category} விவரங்கள்")
                        d_col1, d_col2 = st.columns(2)
                        with d_col1:
                            acc_no = st.text_input("கணக்கு எண் (RD/FD Account No) *")
                        with d_col2:
                            if "Closure" in txn_category or "Interest" in txn_category:
                                paid_amt = st.number_input("வழங்கப்பட்ட தொகை (Paid ₹) *", min_value=0.0, step=100.0)
                            else:
                                received_amt = st.number_input("செலுத்திய தொகை (Received ₹) *", min_value=0.0, step=100.0)
                        detail_summary = [f"A/c No: {acc_no}"]

                    elif txn_category == "GP (Gold Purchase - பழைய நகை வாங்குதல்)":
                        gp_col1, gp_col2 = st.columns(2)
                        with gp_col1:
                            gp_wt = st.number_input("நகை எடை (Grams) *", min_value=0.0, step=0.1)
                            gp_purity = st.selectbox("தரம்", ["916 (22K)", "KDM", "999 (24K)", "750 (18K)"])
                        with gp_col2:
                            paid_amt = st.number_input("வழங்கிய தொகை (Paid ₹) *", min_value=0.0, step=500.0)
                        detail_summary = [f"எடை: {gp_wt}g", f"தரம்: {gp_purity}"]

                    elif txn_category == "GS (Gold Sale - நகை விற்பனை)":
                        gs_col1, gs_col2 = st.columns(2)
                        with gs_col1:
                            gs_bill_no = st.text_input("விற்பனை பில் எண் *")
                            gs_item_name = st.text_input("பொருள் பெயர்")
                        with gs_col2:
                            received_amt = st.number_input("பெற்ற தொகை (Received ₹) *", min_value=0.0, step=500.0)
                        detail_summary = [f"பில்: {gs_bill_no}", f"பொருள்: {gs_item_name}"]

                    st.markdown("---")
                    if st.form_submit_button("➕ பட்டியலில் சேர் (Add to Cart)", type="primary"):
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
                            st.success(f"'{txn_category}' சேர்க்கப்பட்டது!")
                            st.rerun()
                        else:
                            st.error("தொகையை உள்ளிடவும்.")

                if st.session_state.transactions_cart:
                    st.markdown("### 🛒 நடப்பு வருகையின் நடவடிக்கைகள் பட்டியல்:")
                    df_cart = pd.DataFrame(st.session_state.transactions_cart)
                    st.dataframe(df_cart, use_container_width=True)

                    total_paid = df_cart["paid_amount"].sum()
                    total_received = df_cart["received_amount"].sum()
                    net_amount = total_paid - total_received

                    c1, c2, c3 = st.columns(3)
                    c1.metric("மொத்த பட்டுவாடா", f"₹{total_paid:,.2f}")
                    c2.metric("மொத்த வரவு", f"₹{total_received:,.2f}")
                    c3.metric("நிகர ரொக்கம்", f"₹{abs(net_amount):,.2f}")

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

            elif st.session_state.current_visit["step"] == "CASH_OTP":
                visit = st.session_state.current_visit
                net_target = visit["net_amount"]

                current_drawer = get_current_branch_cash_drawer(st.session_state.branch_id)
                otp_already_sent = "generated_otp" in st.session_state and st.session_state.generated_otp is not None

                st.subheader("படி 3: ரூபாய் நோட்டு கணக்கீடு & OTP சரிபார்ப்பு")

                hdr_text = (
                    f"💸 வாடிக்கையாளருக்கு வழங்க வேண்டிய தொகை (Cash OUT): ₹{net_target:,.2f}"
                    if net_target > 0
                    else f"💰 வாடிக்கையாளரிடம் பெற வேண்டிய தொகை (Cash IN): ₹{abs(net_target):,.2f}"
                )
                st.info(f"**{hdr_text}** (வாடிக்கையாளர்: {visit['customer_name']})")

                with st.expander("💼 தற்போதைய கல்லா கையிருப்பு நோட்டுகள் (Live Drawer Stock)", expanded=False):
                    ds1, ds2, ds3, ds4 = st.columns(4)
                    ds1.metric("₹500", f"{current_drawer['500']} தாள்கள்")
                    ds1.metric("₹20", f"{current_drawer['20']} தாள்கள்")
                    ds2.metric("₹200", f"{current_drawer['200']} தாள்கள்")
                    ds2.metric("₹10", f"{current_drawer['10']} தாள்கள்")
                    ds3.metric("₹100", f"{current_drawer['100']} தாள்கள்")
                    ds3.metric("₹5", f"{current_drawer['5']} தாள்கள்")
                    ds4.metric("₹50", f"{current_drawer['50']} தாள்கள்")
                    ds4.metric("நாணயங்கள்", f"₹{current_drawer['coins']:,.2f}")

                if otp_already_sent:
                    st.warning("🔒 **OTP வாடிக்கையாளருக்கு அனுப்பப்பட்டுவிட்டது! பணக் கணக்கீட்டில் இனி எந்த மாற்றமும் செய்ய முடியாது.**")

                col_den1, col_den2 = st.columns([1.4, 1])

                with col_den1:
                    st.markdown("#### 💵 ரொக்கப் பரிமாற்ற விவரங்கள் (Cash In & Out)")

                    with st.expander("📥 வாடிக்கையாளர் தந்த நோட்டுகள் / நாணயங்கள் (Cash IN)", expanded=True):
                        r1_1, r1_2, r1_3, r1_4 = st.columns(4)
                        with r1_1:
                            in_500 = st.number_input("₹500 (IN)", min_value=0, step=1, key="in_500", disabled=otp_already_sent)
                        with r1_2:
                            in_200 = st.number_input("₹200 (IN)", min_value=0, step=1, key="in_200", disabled=otp_already_sent)
                        with r1_3:
                            in_100 = st.number_input("₹100 (IN)", min_value=0, step=1, key="in_100", disabled=otp_already_sent)
                        with r1_4:
                            in_50 = st.number_input("₹50 (IN)", min_value=0, step=1, key="in_50", disabled=otp_already_sent)

                        r2_1, r2_2, r2_3, r2_4 = st.columns(4)
                        with r2_1:
                            in_20 = st.number_input("₹20 (IN)", min_value=0, step=1, key="in_20", disabled=otp_already_sent)
                        with r2_2:
                            in_10 = st.number_input("₹10 (IN)", min_value=0, step=1, key="in_10", disabled=otp_already_sent)
                        with r2_3:
                            in_5 = st.number_input("₹5 (IN)", min_value=0, step=1, key="in_5", disabled=otp_already_sent)
                        with r2_4:
                            in_coins = st.number_input("நாணயங்கள் (IN)", min_value=0, step=1, key="in_coins", disabled=otp_already_sent)

                        total_cash_in = (
                            (in_500 * 500) + (in_200 * 200) + (in_100 * 100) + (in_50 * 50) +
                            (in_20 * 20) + (in_10 * 10) + (in_5 * 5) + (in_coins * 1)
                        )
                        st.write(f"**வாடிக்கையாளர் தந்த மொத்தத் தொகை:** `₹{total_cash_in:,.2f}`")

                    with st.expander("📤 நாம் கொடுத்த நோட்டுகள் / சில்லறை (Cash OUT)", expanded=True):
                        max_500 = max(0, current_drawer["500"] + in_500)
                        max_200 = max(0, current_drawer["200"] + in_200)
                        max_100 = max(0, current_drawer["100"] + in_100)
                        max_50 = max(0, current_drawer["50"] + in_50)
                        max_20 = max(0, current_drawer["20"] + in_20)
                        max_10 = max(0, current_drawer["10"] + in_10)
                        max_5 = max(0, current_drawer["5"] + in_5)
                        max_coins = max(0, current_drawer["coins"] + in_coins)

                        for k, m_val in [("out_500", max_500), ("out_200", max_200), ("out_100", max_100), 
                                         ("out_50", max_50), ("out_20", max_20), ("out_10", max_10), 
                                         ("out_5", max_5), ("out_coins", max_coins)]:
                            if k in st.session_state and st.session_state[k] > m_val:
                                st.session_state[k] = m_val

                        o1_1, o1_2, o1_3, o1_4 = st.columns(4)
                        with o1_1:
                            out_500 = st.number_input(f"₹500 (இருப்பு: {max_500})", min_value=0, max_value=max(0, max_500), step=1, key="out_500", disabled=otp_already_sent)
                        with o1_2:
                            out_200 = st.number_input(f"₹200 (இருப்பு: {max_200})", min_value=0, max_value=max(0, max_200), step=1, key="out_200", disabled=otp_already_sent)
                        with o1_3:
                            out_100 = st.number_input(f"₹100 (இருப்பு: {max_100})", min_value=0, max_value=max(0, max_100), step=1, key="out_100", disabled=otp_already_sent)
                        with o1_4:
                            out_50 = st.number_input(f"₹50 (இருப்பு: {max_50})", min_value=0, max_value=max(0, max_50), step=1, key="out_50", disabled=otp_already_sent)

                        o2_1, o2_2, o2_3, o2_4 = st.columns(4)
                        with o2_1:
                            out_20 = st.number_input(f"₹20 (இருப்பு: {max_20})", min_value=0, max_value=max(0, max_20), step=1, key="out_20", disabled=otp_already_sent)
                        with o2_2:
                            out_10 = st.number_input(f"₹10 (இருப்பு: {max_10})", min_value=0, max_value=max(0, max_10), step=1, key="out_10", disabled=otp_already_sent)
                        with o2_3:
                            out_5 = st.number_input(f"₹5 (இருப்பு: {max_5})", min_value=0, max_value=max(0, max_5), step=1, key="out_5", disabled=otp_already_sent)
                        with o2_4:
                            out_coins = st.number_input(f"நாணயங்கள் (இருப்பு: {max_coins})", min_value=0, max_value=max(0, max_coins), step=1, key="out_coins", disabled=otp_already_sent)

                        total_cash_out = (
                            (out_500 * 500) + (out_200 * 200) + (out_100 * 100) + (out_50 * 50) +
                            (out_20 * 20) + (out_10 * 10) + (out_5 * 5) + (out_coins * 1)
                        )
                        st.write(f"**நாம் கொடுத்த மொத்தத் தொகை:** `₹{total_cash_out:,.2f}`")

                    if net_target < 0:
                        calculated_handover = total_cash_in - total_cash_out
                        target_needed = abs(net_target)
                    else:
                        calculated_handover = total_cash_out - total_cash_in
                        target_needed = net_target

                    is_tally_matched = (calculated_handover == target_needed)

                    st.markdown("---")
                    with st.container(border=True):
                        t_c1, t_c2 = st.columns(2)
                        t_c1.metric("தேவையான நிகர ரொக்கம்", f"₹{target_needed:,.2f}")
                        t_c2.metric("நோட்டுகளின் நிகரக் கணக்கீடு", f"₹{calculated_handover:,.2f}")

                        if is_tally_matched:
                            st.success("✅ நோட்டுகளின் கணக்கீடு சரியானது!")
                        else:
                            st.error(f"❌ நோட்டு கணக்கீடு பொருந்தவில்லை! வித்தியாசம்: ₹{abs(target_needed - calculated_handover):,.2f}")

                with col_den2:
                    st.markdown("#### 📲 OTP சரிபார்ப்பு (Fast2SMS DLT)")
                    st.write(f"வாடிக்கையாளர்: **{visit['customer_name']}**")
                    st.write(f"மொபைல் எண்: **{visit['mobile']}**")

                    if not is_tally_matched:
                        st.warning("⚠️ டேலி சரியாக அமைந்ததும் பட்டன் இயங்கும்.")
                        st.button("📲 OTP அனுப்புக (Send SMS OTP)", disabled=True, key="otp_btn_disabled")
                    elif otp_already_sent:
                        st.success("✅ OTP வாடிக்கையாளருக்கு அனுப்பப்பட்டுவிட்டது!")
                    else:
                        if st.button("📲 OTP அனுப்புக (Send SMS OTP)", type="primary", key="otp_btn_active"):
                            otp_code = str(random.randint(1000, 9999))
                            st.session_state.generated_otp = otp_code
                            with st.spinner("MTHSEG DLT மூலம் SMS அனுப்பப்படுகிறது..."):
                                sms_success, msg_detail = send_fast2sms_otp(visit["mobile"], otp_code)
                            if sms_success:
                                st.success("✅ OTP SMS அனுப்பப்பட்டது!")
                            else:
                                st.info(f"💡 தற்காலிக சோதனை OTP: **{otp_code}**")
                            st.rerun()

                    entered_otp = st.text_input("வாடிக்கையாளர் மொபைலுக்கு வந்த OTP உள்ளிடவும்", max_chars=4)

                    if st.button("✅ வருகையை நிறைவு செய்க (Complete Visit)", type="primary", use_container_width=True):
                        if not is_tally_matched:
                            st.error("❌ நோட்டுகளின் கூட்டுத்தொகை பொருந்தவில்லை!")
                        elif not otp_already_sent:
                            st.error("❌ முதலில் வாடிக்கையாளருக்கு OTP அனுப்பவும்!")
                        else:
                            expected_otp = st.session_state.get("generated_otp")
                            if entered_otp and entered_otp == expected_otp:
                                with st.spinner("வருகை சேமிக்கப்படுகிறது..."):
                                    visit_data = {
                                        "visit_no": visit["visit_no"],
                                        "customer_id": visit["customer_id"],
                                        "branch_id": st.session_state.branch_id,
                                        "total_paid": visit["total_paid"],
                                        "total_received": visit["total_received"],
                                        "net_cash_amount": visit["net_amount"],
                                        "denomination_details": {
                                            "in": {"500": in_500, "200": in_200, "100": in_100, "50": in_50, "20": in_20, "10": in_10, "5": in_5, "coins": in_coins, "total": total_cash_in},
                                            "out": {"500": out_500, "200": out_200, "100": out_100, "50": out_50, "20": out_20, "10": out_10, "5": out_5, "coins": out_coins, "total": total_cash_out},
                                            "net_change": total_cash_in - total_cash_out,
                                        },
                                        "otp_verified": True,
                                        "status": "Pending_Calling_Verification",
                                    }
                                    visit_res = supabase.table("customer_visits").insert(visit_data).execute()
                                    created_visit_id = visit_res.data[0]["id"]

                                    for txn in st.session_state.transactions_cart:
                                        txn["visit_id"] = created_visit_id
                                        supabase.table("transactions").insert(txn).execute()

                                    st.success(f"🎉 வருகை {visit['visit_no']} நிறைவுபெற்றது! இது ஆப்பரேஷன்ஸ் அழைப்பு சரிபார்ப்புக்கு அனுப்பப்பட்டுள்ளது.")
                                    st.session_state.current_visit = None
                                    st.session_state.transactions_cart = []
                                    st.session_state.generated_otp = None
                                    st.rerun()
                            else:
                                st.error("தவறான OTP! மொபைலுக்கு வந்த எண்ணைச் சரியாக உள்ளிடவும்.")

                    st.write("")
                    if not otp_already_sent:
                        if st.button("⬅️ நடவடிக்கைகளை மாற்ற பின்செல்க", use_container_width=True):
                            st.session_state.current_visit["step"] = "TRANSACTIONS"
                            st.rerun()
                    else:
                        st.caption("🔒 OTP அனுப்பப்பட்டதால் பின்செல்லும் வசதி லாக் செய்யப்பட்டுள்ளது.")
