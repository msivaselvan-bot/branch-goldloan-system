from datetime import datetime, date
import random
import requests
import pandas as pd
import streamlit as st
from supabase import Client, create_client

# 1. பக்க வடிவமைப்பு
st.set_page_config(page_title="Branch Operations System", layout="wide")

# ==============================================================================
# ஹை-லுக் ஆப் தீம் (Native App Feel - Lavender, Deep Violet & Luxury Gold)
# ==============================================================================
st.markdown("""
<style>
    /* 1. Streamlit Header, Footer மற்றும் Floating Badges-களை முழுமையாக மறைத்தல் */
    header[data-testid="stHeader"] {
        display: none !important;
        visibility: hidden !important;
        height: 0% !important;
    }

    footer,
    [data-testid="manage-app-button"],
    .viewerBadge_container__r5tak,
    .viewerBadge_link__qRIco,
    div[class*="viewerBadge"],
    div[class*="manage-app"],
    div[class*="floating-actions"],
    div[class*="StatusWidget"],
    #manage-app-button,
    div[data-testid="stStatusWidget"],
    div[class*="floating"],
    div[class*="badge"],
    button[data-testid*="manage"],
    div[data-testid="stToolbar"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
        height: 0 !important;
        width: 0 !important;
        transform: scale(0) !important;
    }

    /* 2. ஆப் பின்னணி - மென்மையான லாவெண்டர் மேட் பினிஷ் */
    .stApp {
        background: #F4EFFB !important;
        color: #26153B !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
        -webkit-tap-highlight-color: transparent;
    }

    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 1400px;
        margin: auto;
    }

    /* 3. முகப்பு கார்டு (Deep Violet Native Card with Gold Glow) */
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

    /* 4. ஆப் ஸ்டைல் உள்ளீட்டுப் புலங்கள் */
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

    /* 5. தொடு-உணர்வு பட்டன்கள் */
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

    /* 6. கார்டுகள் & கண்டெய்னர்கள் */
    div[data-testid="stExpander"], div[data-testid="stVerticalBlock"] > div[style*="border:"] {
        background: #FFFFFF !important;
        border: 1.5px solid #E1D2F5 !important;
        border-radius: 14px !important;
        box-shadow: 0 3px 12px rgba(74, 32, 122, 0.05) !important;
        color: #26153B !important;
        overflow: hidden;
    }

    /* 7. மெட்ரிக் கார்டுகள் */
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

    /* 8. ஆப் ஸ்டைல் டேப்கள் */
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
# 2. Supabase இணைப்பு
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
# 3. ஆவணப் பதிவேற்றம், SMS & கல்லா இருப்பு செயல்பாடுகள்
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

        params_otp = {"route": "otp", "variables_values": str(otp_code), "numbers": clean_mobile}
        resp_fallback = requests.get(url, headers=headers, params=params_otp, timeout=10)
        fallback_json = resp_fallback.json()
        if fallback_json.get("return") is True:
            return True, "SMS வெற்றிகரமாக அனுப்பப்பட்டது!"

        err_msg = res_json.get("message") or fallback_json.get("message") or str(res_json)
        return False, str(err_msg)
    except Exception as e:
        return False, f"இணைப்புப் பிழை: {e}"

def get_current_branch_cash_drawer(branch_id: int):
    """தொடக்க இருப்பு, வாடிக்கையாளர் பரிவர்த்தனைகள் மற்றும் HO ⇄ கிளை பணப் பரிமாற்றம் ஆகியவற்றைக் கணக்கிடுகிறது"""
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

        fund_res = (
            supabase.table("branch_fund_transfers")
            .select("transfer_type, denomination_details")
            .eq("branch_id", branch_id)
            .eq("payment_mode", "Cash")
            .execute()
        )
        if fund_res.data:
            for f_row in fund_res.data:
                t_type = f_row.get("transfer_type")
                t_den = f_row.get("denomination_details") or {}
                for k in stock:
                    notes_qty = int(t_den.get(k, 0) or 0)
                    if t_type == "HO_TO_BRANCH":
                        stock[k] += notes_qty
                    elif t_type == "BRANCH_TO_HO":
                        stock[k] -= notes_qty

        for k in stock:
            stock[k] = max(0, stock[k])

        return stock
    except Exception:
        return empty_stock

def render_staff_attribution_report(selected_branch_id=None):
    """பணியாளர் வாரியான வணிக நடவடிக்கைகள் மற்றும் தொகையைத் தொகுத்து அறிக்கையாகக் காட்டுகிறது"""
    st.markdown("### 📊 பணியாளர் வாரியான நடவடிக்கைகள் அறிக்கை (Staff Attribution Report)")

    d_col1, d_col2 = st.columns(2)
    start_date = d_col1.date_input("தொடக்கத் தேதி (From Date):", value=date.today().replace(day=1), key=f"rep_start_{selected_branch_id}")
    end_date = d_col2.date_input("முடிவுத் தேதி (To Date):", value=date.today(), key=f"rep_end_{selected_branch_id}")

    if start_date > end_date:
        st.error("தொடக்கத் தேதி முடிவுத் தேதியை விட அதிகமாக இருக்கக்கூடாது!")
        return

    start_dt_str = f"{start_date}T00:00:00"
    end_dt_str = f"{end_date}T23:59:59"

    query = (
        supabase.table("customer_visits")
        .select("id, visit_no, branch_id, created_at, payment_mode, cash_amount, bank_amount, branches(branch_name), transactions(*)")
        .gte("created_at", start_dt_str)
        .lte("created_at", end_dt_str)
    )

    if selected_branch_id:
        query = query.eq("branch_id", selected_branch_id)

    res = query.execute()
    visits = res.data or []

    flat_data = []
    for v in visits:
        b_name = v.get("branches", {}).get("branch_name", "Unknown") if v.get("branches") else "Unknown"
        for t in v.get("transactions", []):
            flat_data.append({
                "தேதி": str(v.get("created_at", ""))[:10],
                "வருகை எண்": v.get("visit_no", "-"),
                "கிளை": b_name,
                "பணியாளர்": t.get("staff_name", "Walk-in"),
                "நடவடிக்கை வகை": t.get("transaction_type", "-"),
                "பட்டுவாடா (Paid ₹)": float(t.get("paid_amount", 0.0)),
                "வரவு (Received ₹)": float(t.get("received_amount", 0.0)),
                "பணம் செலுத்திய முறை": v.get("payment_mode", "Cash"),
                "குறிப்பு": t.get("remarks", "")
            })

    if not flat_data:
        st.info("தேர்ந்தெடுக்கப்பட்ட தேதி வரம்பில் பரிவர்த்தனைகள் எதுவும் இல்லை.")
        return

    df_rep = pd.DataFrame(flat_data)

    tot_txns = len(df_rep)
    tot_paid = df_rep["பட்டுவாடா (Paid ₹)"].sum()
    tot_rec = df_rep["வரவு (Received ₹)"].sum()

    m1, m2, m3 = st.columns(3)
    m1.metric("மொத்த நடவடிக்கைகள்", f"{tot_txns:,}")
    m2.metric("மொத்த பட்டுவாடா", f"₹{tot_paid:,.2f}")
    m3.metric("மொத்த வரவு", f"₹{tot_rec:,.2f}")

    st.markdown("---")

    st.markdown("##### 👥 பணியாளர் வாரியான தொகுப்பு விவரங்கள்")
    staff_summary = df_rep.groupby(["பணியாளர்", "நடவடிக்கை வகை"]).agg(
        எண்ணிக்கை=("நடவடிக்கை வகை", "count"),
        வழங்கிய_தொகை=("பட்டுவாடா (Paid ₹)", "sum"),
        பெற்ற_தொகை=("வரவு (Received ₹)", "sum")
    ).reset_index()

    staff_summary["நிகர_ரொக்கம்"] = staff_summary["வழங்கிய_தொகை"] - staff_summary["பெற்ற_தொகை"]
    staff_summary.columns = ["பணியாளர்", "நடவடிக்கை வகை", "எண்ணிக்கை", "பட்டுவாடா (Paid ₹)", "வரவு (Received ₹)", "நிகர ரொக்கம் (Net ₹)"]
    st.dataframe(staff_summary, use_container_width=True)

    with st.expander("📑 அனைத்து தனிநபர் பரிவர்த்தனைகளின் விரிவான பட்டியல் (Detailed Log)"):
        st.dataframe(df_rep, use_container_width=True)

    csv = staff_summary.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 அறிக்கையைப் பதிவிறக்குக (Download CSV)",
        data=csv,
        file_name=f"Staff_Report_{start_date}_to_{end_date}.csv",
        mime="text/csv",
        key=f"dl_csv_{selected_branch_id}"
    )

# ==========================================
# 4. தற்காலிக சேமிப்பக மாறிகள் (Session State)
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
# 5. உள்நுழைவு திரை (Royal Violet Theme)
# ==========================================
if not st.session_state.logged_in:
    col_left, col_center, col_right = st.columns([1.2, 1.4, 1.2])

    with col_center:
        st.markdown("""
        <div class="login-box">
            <h3>🏦 கிளை சிஸ்டம்</h3>
            <p>பணியாளர் பாதுகாப்பான உள்நுழைவு</p>
        </div>
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

# ==========================================
# 6. முதன்மை திரை
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
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(
            [
                "🏢 கிளைகள்",
                "👥 பணியாளர்கள்",
                "📥 மொத்தப் பதிவேற்றம்",
                "🗂️ வாடிக்கையாளர் மேலாண்மை",
                "📊 வருகை & பரிவர்த்தனை திருத்தம்",
                "💰 கிளை துவக்க இருப்பு & கல்லா",
                "🏦 தலைமையக பணப் பரிமாற்றம் (Fund Transfer)",
                "📈 பணியாளர் அறிக்கை (Staff Report)"
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
                with st.expander(f"வருகை: {vr['visit_no']} | வாடிக்கையாளர்: {c_name} | நிகர தொகை: ₹{vr['net_cash_amount']:,.2f} | முறை: {vr.get('payment_mode', 'Cash')} | நிலை: {vr['status']}"):
                    if vr.get("transactions"):
                        st.dataframe(pd.DataFrame(vr["transactions"]))
                    act_c1, act_c2 = st.columns(2)
                    with act_c1:
                        new_st = st.selectbox(
                            "நிலையை மாற்று:",
                            ["Pending_Calling_Verification", "Pending_Branch_Docs", "Submitted_to_Auditor", "Needs_Clarification", "Approved", "Cancelled"],
                            index=["Pending_Calling_Verification", "Pending_Branch_Docs", "Submitted_to_Auditor", "Needs_Clarification", "Approved", "Cancelled"].index(vr["status"]) if vr["status"] in ["Pending_Calling_Verification", "Pending_Branch_Docs", "Submitted_to_Auditor", "Needs_Clarification", "Approved", "Cancelled"] else 0,
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
                st.info(f"📊 **கணக்கிடப்பட்ட மொத்த துவக்க இருப்பு: ₹{total_opening_calc:,.2f}**")

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

        with tab7:
            st.subheader("🏦 தலைமையக பணப் பரிமாற்றம் (Head Office ⇄ Branch Fund Transfer)")
            st.caption("தலைமையகத்தில் இருந்து கிளைக்கு ரொக்கம் அனுப்புதல் அல்லது கிளையிலிருந்து தலைமையகத்திற்கு ரொக்கத்தை திரும்பப் பெறுதல்.")

            with st.form("admin_fund_transfer_form"):
                ft_c1, ft_c2, ft_c3 = st.columns(3)
                with ft_c1:
                    ft_branch = st.selectbox("கிளையைத் தேர்ந்தெடுக்கவும்:", list(branch_options.keys()), key="adm_ft_branch")
                    ft_type = st.selectbox("பரிமாற்ற வகை (Transfer Type):", ["HO_TO_BRANCH (தலைமையகத்திலிருந்து கிளைக்கு)", "BRANCH_TO_HO (கிளையிலிருந்து தலைமையகத்திற்கு)"])
                with ft_c2:
                    ft_mode = st.selectbox("பணப்பரிமாற்ற முறை:", ["Cash (ரொக்கம்)", "Bank Transfer (வங்கி வரவு)", "NEFT/RTGS"])
                    ft_ref = st.text_input("குறிப்பு எண் (UTR / Ref No / Voucher No):")
                with ft_c3:
                    ft_date = st.date_input("பரிமாற்ற தேதி:", value=date.today(), key="adm_ft_date")

                st.markdown("##### 💵 நோட்டுகள் விவரம் (ரொக்கமாக இருந்தால் மட்டும்):")
                f_d1, f_d2, f_d3, f_d4 = st.columns(4)
                with f_d1:
                    ft_500 = st.number_input("₹500 தாள்கள்", min_value=0, step=1, key="ft_500")
                    ft_20 = st.number_input("₹20 தாள்கள்", min_value=0, step=1, key="ft_20")
                with f_d2:
                    ft_200 = st.number_input("₹200 தாள்கள்", min_value=0, step=1, key="ft_200")
                    ft_10 = st.number_input("₹10 தாள்கள்", min_value=0, step=1, key="ft_10")
                with f_d3:
                    ft_100 = st.number_input("₹100 தாள்கள்", min_value=0, step=1, key="ft_100")
                    ft_5 = st.number_input("₹5 தாள்கள்", min_value=0, step=1, key="ft_5")
                with f_d4:
                    ft_50 = st.number_input("₹50 தாள்கள்", min_value=0, step=1, key="ft_50")
                    ft_coins = st.number_input("நாணயங்கள் (₹)", min_value=0, step=1, key="ft_coins")

                calc_cash_total = (
                    (ft_500 * 500) + (ft_200 * 200) + (ft_100 * 100) + (ft_50 * 50) +
                    (ft_20 * 20) + (ft_10 * 10) + (ft_5 * 5) + ft_coins
                )

                if "Cash" in ft_mode:
                    ft_total_amount = float(calc_cash_total)
                    st.info(f"💵 **கணக்கிடப்பட்ட ரொக்கத் தொகை: ₹{ft_total_amount:,.2f}**")
                else:
                    ft_total_amount = st.number_input("பரிமாற்றத் தொகை (₹):", min_value=0.0, step=5000.0)

                if st.form_submit_button("பணப் பரிமாற்றத்தைப் பதிவு செய்க (Save Transfer)", type="primary"):
                    if ft_total_amount > 0:
                        pure_type = "HO_TO_BRANCH" if "HO_TO_BRANCH" in ft_type else "BRANCH_TO_HO"
                        pure_mode = "Cash" if "Cash" in ft_mode else "Bank Transfer"
                        t_payload = {
                            "branch_id": branch_options[ft_branch],
                            "transfer_date": str(ft_date),
                            "transfer_type": pure_type,
                            "amount": ft_total_amount,
                            "payment_mode": pure_mode,
                            "reference_no": ft_ref.strip(),
                            "denomination_details": {
                                "500": ft_500, "200": ft_200, "100": ft_100, "50": ft_50,
                                "20": ft_20, "10": ft_10, "5": ft_5, "coins": ft_coins
                            } if pure_mode == "Cash" else {},
                            "created_by": st.session_state.username,
                            "status": "Completed"
                        }
                        try:
                            supabase.table("branch_fund_transfers").insert(t_payload).execute()
                            st.success(f"✅ {ft_branch} கிளைக்கான பணப் பரிமாற்றம் ₹{ft_total_amount:,.2f} வெற்றிகரமாகப் பதிவு செய்யப்பட்டது!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"சேமிப்பதில் பிழை: {e}")
                    else:
                        st.error("தொகையை உள்ளிடவும்.")

            st.markdown("---")
            st.subheader("📋 சமீபத்திய தலைமையகப் பணப் பரிமாற்றங்கள்")
            fund_history = supabase.table("branch_fund_transfers").select("*, branches(branch_name)").order("id", desc=True).limit(20).execute().data or []
            if fund_history:
                st.dataframe(pd.DataFrame([{
                    "தேதி": f["transfer_date"],
                    "கிளை": f.get("branches", {}).get("branch_name", "-"),
                    "பரிமாற்றம்": "📥 HO ➔ கிளை" if f["transfer_type"] == "HO_TO_BRANCH" else "📤 கிளை ➔ HO",
                    "தொகை (₹)": f"₹{float(f['amount']):,.2f}",
                    "முறை": f["payment_mode"],
                    "குறிப்பு / UTR": f.get("reference_no", "-"),
                    "பதிவு செய்தவர்": f.get("created_by", "-")
                } for f in fund_history]), use_container_width=True)

        with tab8:
            st.subheader("📈 அனைத்து கிளைகளின் பணியாளர் அறிக்கை (All Branches Report)")
            rep_b_opts = ["அனைத்து கிளைகளும் (All Branches)"] + list(branch_options.keys())
            sel_rep_b = st.selectbox("கிளையை வடிகட்டவும்:", rep_b_opts, key="adm_rep_branch_sel")
            filter_b_id = branch_options.get(sel_rep_b) if sel_rep_b != "அனைத்து கிளைகளும் (All Branches)" else None
            render_staff_attribution_report(selected_branch_id=filter_b_id)

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
                with st.expander(f"🔔 வருகை: {item['visit_no']} | கிளை: {b_name} | வாடிக்கையாளர்: {cust.get('name')} | நிகர: ₹{item['net_cash_amount']:,.2f} | முறை: {item.get('payment_mode', 'Cash')}"):
                    c_col1, c_col2 = st.columns([1.5, 1])
                    with c_col1:
                        st.write(f"👤 **வாடிக்கையாளர் பெயர்:** {cust.get('name')}")
                        st.write(f"📞 **அழைக்க வேண்டிய எண்:** `{cust.get('mobile')}` | **கூடுதல் எண்:** `{cust.get('mobile2', '-')}`")
                        st.write(f"🏠 **முகவரி:** {cust.get('address', '-')}")
                        st.write(f"💳 **பணம் பரிமாற்ற முறை:** `{item.get('payment_mode', 'Cash')}` (ரொக்கம்: ₹{item.get('cash_amount', 0):,.2f} | வங்கி/UPI: ₹{item.get('bank_amount', 0):,.2f})")
                        if item.get("bank_reference_no"):
                            st.write(f"🔗 **UTR / வங்கி குறிப்பு எண்:** `{item['bank_reference_no']}`")
                    with c_col2:
                        st.write(f"💰 **மொத்தத் தொகை:** ₹{item['net_cash_amount']:,.2f}")
                        st.write(f"🕒 **கவுண்ட்டர் நேரம்:** {item['created_at']}")

                    st.markdown("##### 📌 பரிவர்த்தனை விவரங்கள்:")
                    if item.get("transactions"):
                        st.dataframe(pd.DataFrame(item["transactions"])[["transaction_type", "paid_amount", "received_amount", "remarks"]], use_container_width=True)

                    flag_note = st.text_input("சந்தேகத்திற்கான காரணம் / விளக்கம் தேவைப்படும் விபரம்:", key=f"flag_txt_{item['id']}")

                    btn_op1, btn_op2 = st.columns(2)
                    with btn_op1:
                        if st.button("✅ வாடிக்கையாளர் அழைப்பு சரிபார்க்கப்பட்டது (Call Verified)", key=f"v_call_{item['id']}", type="primary"):
                            try:
                                supabase.table("customer_visits").update({
                                    "status": "Pending_Branch_Docs",
                                    "verification_remarks": "Operations: Call Verified"
                                }).eq("id", item["id"]).execute()
                            except Exception:
                                supabase.table("customer_visits").update({"status": "Pending_Branch_Docs"}).eq("id", item["id"]).execute()
                            st.success(f"{item['visit_no']} சரிபார்க்கப்பட்டது!")
                            st.rerun()
                    with btn_op2:
                        if st.button("⚠️ சந்தேகம் / மறுப்பு (Flag Issue)", key=f"flag_call_{item['id']}"):
                            if flag_note.strip():
                                try:
                                    supabase.table("customer_visits").update({
                                        "status": "Needs_Clarification",
                                        "verification_remarks": f"Operations Clarification: {flag_note.strip()}"
                                    }).eq("id", item["id"]).execute()
                                except Exception:
                                    supabase.table("customer_visits").update({"status": "Needs_Clarification"}).eq("id", item["id"]).execute()
                                st.warning("கிளையிடம் விளக்கம் கோரப்பட்டது.")
                                st.rerun()
                            else:
                                st.error("காரணத்தை உள்ளிடவும்.")

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
                    st.write(f"💳 **முறை:** {item.get('payment_mode', 'Cash')} | ரொக்கம்: ₹{item.get('cash_amount', 0):,.2f} | வங்கி/UPI: ₹{item.get('bank_amount', 0):,.2f}")
                    if item.get("bank_reference_no"):
                        st.write(f"🔗 **UTR எண்:** `{item['bank_reference_no']}`")

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

                    auditor_query = st.text_input("விளக்கம் கோருவதற்கான காரணம்:", key=f"aud_q_{item['id']}")

                    col_a1, col_a2 = st.columns(2)
                    with col_a1:
                        if st.button(f"அங்கீகரி (Approve) - {item['visit_no']}", key=f"app_{item['id']}", type="primary"):
                            try:
                                supabase.table("customer_visits").update({
                                    "status": "Approved",
                                    "verification_remarks": "Auditor: Approved"
                                }).eq("id", item["id"]).execute()
                            except Exception:
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
                            if auditor_query.strip():
                                try:
                                    supabase.table("customer_visits").update({
                                        "status": "Needs_Clarification",
                                        "verification_remarks": f"Auditor Clarification: {auditor_query.strip()}"
                                    }).eq("id", item["id"]).execute()
                                except Exception:
                                    supabase.table("customer_visits").update({"status": "Needs_Clarification"}).eq("id", item["id"]).execute()
                                st.warning("கிளையிடம் விளக்கம் கேட்கப்பட்டது.")
                                st.rerun()
                            else:
                                st.error("விளக்கத்திற்கான காரணத்தை உள்ளிடவும்.")

    # ----------------------------------------------------
    # D. கிளை செயல்பாடுகள் திரை (BRANCH FLOW)
    # ----------------------------------------------------
    else:
        branch_tab1, branch_tab2, branch_tab3, branch_tab4, branch_tab5, branch_tab6 = st.tabs([
            "🛒 கவுண்ட்டர் வருகை & OTP",
            "📁 கிளை ஆவணங்கள் பதிவேற்றம் (Doc Desk)",
            "⚠️ விளக்கம் அளிக்க வேண்டியவை (Clarifications)",
            "💼 கிளை கல்லா & டினாமினேசன் நிலை (Cash Drawer)",
            "🏦 HO பணப் பரிமாற்றம் (Fund Transfer)",
            "📈 பணியாளர் அறிக்கை (Staff Report)"
        ])

        with branch_tab6:
            render_staff_attribution_report(selected_branch_id=st.session_state.branch_id)

        with branch_tab5:
            st.subheader("🏦 தலைமையக பணப் பரிமாற்றம் (HO Fund Transfer Desk)")
            st.caption("கிளையிலிருந்து தலைமையகத்திற்கு ரொக்கம் அனுப்புதல் அல்லது வங்கி மூலம் பரிமாற்றம் செய்தல்.")

            curr_b_drawer = get_current_branch_cash_drawer(st.session_state.branch_id)

            with st.expander("💼 தற்போதைய கிளை கல்லா கையிருப்பு (Live Cash Drawer)", expanded=False):
                bd1, bd2, bd3, bd4 = st.columns(4)
                bd1.metric("₹500 தாள்கள்", f"{curr_b_drawer['500']}")
                bd1.metric("₹20 தாள்கள்", f"{curr_b_drawer['20']}")
                bd2.metric("₹200 தாள்கள்", f"{curr_b_drawer['200']}")
                bd2.metric("₹10 தாள்கள்", f"{curr_b_drawer['10']}")
                bd3.metric("₹100 தாள்கள்", f"{curr_b_drawer['100']}")
                bd3.metric("₹5 தாள்கள்", f"{curr_b_drawer['5']}")
                bd4.metric("₹50 தாள்கள்", f"{curr_b_drawer['50']}")
                bd4.metric("நாணயங்கள் (₹)", f"{curr_b_drawer['coins']:,.2f}")

            # 1. clear_on_submit=True சேர்க்கப்பட்டுள்ளது
            with st.form("branch_to_ho_fund_form", clear_on_submit=True):
                st.markdown("##### 📤 கிளையிலிருந்து தலைமையகத்திற்கு பணம் அனுப்புதல் (Branch ➔ Head Office)")
                b_ft_c1, b_ft_c2 = st.columns(2)
                with b_ft_c1:
                    b_ft_mode = st.selectbox("அனுப்பும் முறை:", ["Cash (ரொக்கம்)", "Bank Transfer (வங்கி வரவு)"], key="b_ft_mode")
                    b_ft_ref = st.text_input("குறிப்பு எண் / ரசீது எண் / UTR No:", placeholder="எ.கா: HO-REC-01 / UTR...", key="b_ft_ref")
                with b_ft_c2:
                    b_ft_date = st.date_input("பரிமாற்ற தேதி:", value=date.today(), key="b_ft_date")

                st.markdown("##### 💵 நோட்டுகள் விவரம் (கல்லாவில் இருந்து எடுக்கப்படும் தாள்கள்):")
                bf_1, bf_2, bf_3, bf_4 = st.columns(4)
                with bf_1:
                    b_out_500 = st.number_input(f"₹500 (இருப்பு: {curr_b_drawer['500']})", min_value=0, max_value=max(0, curr_b_drawer['500']), step=1, key="b_out_500")
                    b_out_20 = st.number_input(f"₹20 (இருப்பு: {curr_b_drawer['20']})", min_value=0, max_value=max(0, curr_b_drawer['20']), step=1, key="b_out_20")
                with bf_2:
                    b_out_200 = st.number_input(f"₹200 (இருப்பு: {curr_b_drawer['200']})", min_value=0, max_value=max(0, curr_b_drawer['200']), step=1, key="b_out_200")
                    b_out_10 = st.number_input(f"₹10 (இருப்பு: {curr_b_drawer['10']})", min_value=0, max_value=max(0, curr_b_drawer['10']), step=1, key="b_out_10")
                with bf_3:
                    b_out_100 = st.number_input(f"₹100 (இருப்பு: {curr_b_drawer['100']})", min_value=0, max_value=max(0, curr_b_drawer['100']), step=1, key="b_out_100")
                    b_out_5 = st.number_input(f"₹5 (இருப்பு: {curr_b_drawer['5']})", min_value=0, max_value=max(0, curr_b_drawer['5']), step=1, key="b_out_5")
                with bf_4:
                    b_out_50 = st.number_input(f"₹50 (இருப்பு: {curr_b_drawer['50']})", min_value=0, max_value=max(0, curr_b_drawer['50']), step=1, key="b_out_50")
                    b_out_coins = st.number_input(f"நாணயங்கள் (இருப்பு: ₹{curr_b_drawer['coins']:,.2f})", min_value=0.0, max_value=max(0.0, float(curr_b_drawer['coins'])), step=1.0, key="b_out_coins")

                calc_b_cash_total = (
                    (b_out_500 * 500) + (b_out_200 * 200) + (b_out_100 * 100) + (b_out_50 * 50) +
                    (b_out_20 * 20) + (b_out_10 * 10) + (b_out_5 * 5) + b_out_coins
                )

                if "Cash" in b_ft_mode:
                    b_final_amt = float(calc_b_cash_total)
                    st.info(f"💵 **கணக்கிடப்பட்ட மொத்த ரொக்கம்: ₹{b_final_amt:,.2f}**")
                else:
                    b_final_amt = st.number_input("வங்கி மூலம் அனுப்பிய தொகை (₹):", min_value=0.0, step=1000.0, key="b_ft_bank_amt")

                submit_btn = st.form_submit_button("பணத்தை தலைமையகத்திற்கு அனுப்பு (Submit to HO)", type="primary")

                if submit_btn:
                    if b_final_amt > 0:
                        pure_mode = "Cash" if "Cash" in b_ft_mode else "Bank Transfer"
                        b_payload = {
                            "branch_id": st.session_state.branch_id,
                            "transfer_date": str(b_ft_date),
                            "transfer_type": "BRANCH_TO_HO",
                            "amount": float(b_final_amt),
                            "payment_mode": pure_mode,
                            "reference_no": b_ft_ref.strip(),
                            "denomination_details": {
                                "500": b_out_500, "200": b_out_200, "100": b_out_100, "50": b_out_50,
                                "20": b_out_20, "10": b_out_10, "5": b_out_5, "coins": b_out_coins
                            } if pure_mode == "Cash" else {},
                            "created_by": st.session_state.username,
                            "status": "Completed"
                        }
                        try:
                            supabase.table("branch_fund_transfers").insert(b_payload).execute()
                            
                            # 2. சமர்ப்பித்த பின் உள்ளீட்டுப் புலங்களை பூஜ்ஜியமாக்க session state-ஐ மீட்டமைத்தல்
                            reset_keys = ["b_out_500", "b_out_200", "b_out_100", "b_out_50", 
                                          "b_out_20", "b_out_10", "b_out_5", "b_out_coins", 
                                          "b_ft_ref", "b_ft_bank_amt"]
                            for k in reset_keys:
                                if k in st.session_state:
                                    del st.session_state[k]

                            st.success(f"✅ ₹{b_final_amt:,.2f} தலைமையகத்திற்கு அனுப்பப்பட்டதாகப் பதிவு செய்யப்பட்டது!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"சேமிப்பதில் பிழை: {e}")
                    else:
                        st.error("நோட்டுகள் அல்லது தொகையை உள்ளிடவும்.")

            st.markdown("---")
            st.subheader("📋 உங்கள் கிளையின் சமீபத்திய பணப் பரிமாற்றங்கள்")
            b_fund_logs = supabase.table("branch_fund_transfers").select("*").eq("branch_id", st.session_state.branch_id).order("id", desc=True).limit(15).execute().data or []
            if b_fund_logs:
                st.dataframe(pd.DataFrame([{
                    "தேதி": f["transfer_date"],
                    "பரிமாற்றம்": "📥 HO ➔ கிளைக்கு வந்தது" if f["transfer_type"] == "HO_TO_BRANCH" else "📤 கிளை ➔ HO-க்கு அனுப்பியது",
                    "தொகை (₹)": f"₹{float(f['amount']):,.2f}",
                    "முறை": f["payment_mode"],
                    "நோட்டுகள் விபரம்": str(f.get("denomination_details", {})),
                    "குறிப்பு எண்": f.get("reference_no", "-"),
                    "பணியாளர்": f.get("created_by", "-")
                } for f in b_fund_logs]), use_container_width=True)

        with branch_tab4:
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

        with branch_tab3:
            st.subheader("⚠️ தலைமை அலுவலக விளக்கங்கள் & மறுப்புகள் (Clarifications Inbox)")
            clarification_visits = supabase.table("customer_visits").select("*, customers(name, mobile), transactions(*)").eq("branch_id", st.session_state.branch_id).eq("status", "Needs_Clarification").order("id", desc=True).execute().data or []

            if not clarification_visits:
                st.info("✅ எந்த விளக்கங்களும் நிலுவையில் இல்லை.")
            else:
                for c_item in clarification_visits:
                    c_cust = c_item.get("customers", {})
                    v_remarks = c_item.get("verification_remarks", "விளக்கம் கோரப்பட்டுள்ளது.")
                    with st.expander(f"🚨 {c_item['visit_no']} | {c_cust.get('name')} | தொகை: ₹{c_item['net_cash_amount']:,.2f}"):
                        st.error(f"**தலைமை அலுவலகக் குறிப்பு:** {v_remarks}")
                        if c_item.get("transactions"):
                            st.dataframe(pd.DataFrame(c_item["transactions"])[["transaction_type", "paid_amount", "received_amount", "remarks"]], use_container_width=True)

                        with st.form(f"reply_clarification_form_{c_item['id']}"):
                            branch_reply = st.text_area("கிளையின் பதில் விளக்கம் (Branch Explanation / Reply):")
                            re_upload_files = st.file_uploader("கூடுதல் / திருத்தப்பட்ட ஆவணங்கள்:", accept_multiple_files=True, key=f"re_up_{c_item['id']}")

                            if st.form_submit_button("பதிலைச் சமர்ப்பித்து மீண்டும் அனுப்புக ➔", type="primary"):
                                if branch_reply.strip():
                                    update_links = []
                                    if re_upload_files:
                                        update_links = upload_files_to_supabase(re_upload_files, c_item["visit_no"])
                                        exist_audit = supabase.table("audit_records").select("*").eq("visit_id", c_item["id"]).execute().data
                                        if exist_audit:
                                            old_links = exist_audit[0].get("document_urls") or []
                                            supabase.table("audit_records").update({"document_urls": old_links + update_links}).eq("visit_id", c_item["id"]).execute()
                                        else:
                                            supabase.table("audit_records").insert({"visit_id": c_item["id"], "document_urls": update_links, "audit_status": "Pending"}).execute()

                                    next_st = "Pending_Calling_Verification" if "Operations" in v_remarks else "Submitted_to_Auditor"
                                    try:
                                        supabase.table("customer_visits").update({
                                            "status": next_st,
                                            "verification_remarks": f"Branch Reply: {branch_reply.strip()} (முந்தைய குறிப்பு: {v_remarks})"
                                        }).eq("id", c_item["id"]).execute()
                                    except Exception:
                                        supabase.table("customer_visits").update({"status": next_st}).eq("id", c_item["id"]).execute()

                                    st.success("விளக்கம் சமர்ப்பிக்கப்பட்டது!")
                                    st.rerun()
                                else:
                                    st.error("பதிலை உள்ளிடவும்.")

        with branch_tab2:
            st.subheader("📁 கிளை ஆவணங்கள் பதிவேற்றம் (Upload Docs Desk)")
            branch_pending = supabase.table("customer_visits").select("*, customers(name, mobile), transactions(*)").eq("branch_id", st.session_state.branch_id).in_("status", ["Pending_Branch_Docs", "Pending_Calling_Verification"]).order("id", desc=True).execute().data or []

            if not branch_pending:
                st.info("தற்போது ஆவணங்கள் ஏற்ற வேண்டிய வருகைகள் எதுவும் இல்லை.")
            else:
                for b_item in branch_pending:
                    c_info = b_item.get("customers", {})
                    st_badge = "🟢 ஆப்பரேஷன் சரிபார்க்கப்பட்டது" if b_item["status"] == "Pending_Branch_Docs" else "🟡 அழைப்பு சரிபார்ப்பில் உள்ளது"
                    with st.expander(f"📄 வருகை: {b_item['visit_no']} | வாடிக்கையாளர்: {c_info.get('name')} | தொகை: ₹{b_item['net_cash_amount']:,.2f} | முறை: {b_item.get('payment_mode', 'Cash')} | {st_badge}"):
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
                                    st.success("✅ ஆவணங்கள் தணிக்கைக்கு அனுப்பப்பட்டுவிட்டன!")
                                    st.rerun()
                            else:
                                st.error("ஆவணத்தைத் தேர்ந்தெடுக்கவும்.")

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
                    search_query = st.text_input("பெயர் / மொபைல் எண் / Customer ID உள்ளிடவும்:", placeholder="எ.கா: ராம் அல்லது 98765...", key="live_cust_search_input")

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
                            cust_dropdown_dict = {f"{c['name']} | {c.get('customer_code', '')} | 📞 {c.get('mobile', '')}": c for c in matched_custs.data}
                            selected_label = st.selectbox("பொருந்தும் வாடிக்கையாளர் பட்டியல்:", options=list(cust_dropdown_dict.keys()), key="dropdown_cust_select")
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
                        st.info(f"💰 வாடிக்கையாளர் செலுத்த வேண்டிய மொத்தத் தொகை: **₹{received_amt:,.2f}**")
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
                    c3.metric("நிகரத் தொகை", f"₹{abs(net_amount):,.2f}")

                    cart_b1, cart_b2 = st.columns([4, 1])
                    with cart_b1:
                        if st.button("பணம் செலுத்தும் முறை மற்றும் OTP பிரிவிற்குச் செல் ➔", type="primary"):
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
                total_needed_abs = abs(net_target)

                current_drawer = get_current_branch_cash_drawer(st.session_state.branch_id)
                otp_already_sent = "generated_otp" in st.session_state and st.session_state.generated_otp is not None

                st.subheader("படி 3: பணப் பரிமாற்ற முறை & ரூபாய் நோட்டு கணக்கீடு")

                hdr_text = (
                    f"💸 வாடிக்கையாளருக்கு வழங்க வேண்டிய தொகை (Pay-OUT): ₹{net_target:,.2f}"
                    if net_target > 0
                    else f"💰 வாடிக்கையாளரிடம் பெற வேண்டிய தொகை (Pay-IN): ₹{total_needed_abs:,.2f}"
                )
                st.info(f"**{hdr_text}** (வாடிக்கையாளர்: {visit['customer_name']})")

                # பகுதி 3.1: பலவகை பணப்பரிவர்த்தனைத் தேர்வு
                with st.container(border=True):
                    st.markdown("#### 💳 பணம் செலுத்தும் / பெறும் வழிகள் (Payment Modes & Split)")
                    pm_c1, pm_c2, pm_c3 = st.columns(3)

                    with pm_c1:
                        pay_option = st.selectbox(
                            "பரிமாற்ற வகை:",
                            [
                                "முழுவதும் ரொக்கம் (100% Cash)",
                                "முழுவதும் வங்கி / UPI (100% Online)",
                                "பகுதி ரொக்கம் + பகுதி வங்கி (Split Cash & Online)"
                            ],
                            disabled=otp_already_sent,
                            key="pay_option_select"
                        )

                    with pm_c2:
                        if pay_option == "முழுவதும் ரொக்கம் (100% Cash)":
                            cash_portion = total_needed_abs
                            bank_portion = 0.0
                        elif pay_option == "முழுவதும் வங்கி / UPI (100% Online)":
                            cash_portion = 0.0
                            bank_portion = total_needed_abs
                        else:
                            cash_portion = st.number_input(
                                "ரொக்கமாக செலுத்தப்படும் / பெறப்படும் தொகை (₹):",
                                min_value=0.0,
                                max_value=float(total_needed_abs),
                                step=500.0,
                                disabled=otp_already_sent,
                                key="cash_portion_input"
                            )
                            bank_portion = total_needed_abs - cash_portion

                        st.metric("ரொக்கம் (Cash Target)", f"₹{cash_portion:,.2f}")

                    with pm_c3:
                        st.metric("வங்கி / UPI தொகை", f"₹{bank_portion:,.2f}")
                        bank_ref_no = ""
                        if bank_portion > 0:
                            bank_ref_no = st.text_input(
                                "வங்கி பரிவர்த்தனை எண் (UTR / Ref No / GPay Txn ID) *:",
                                disabled=otp_already_sent,
                                key="bank_ref_input"
                            )

                # பகுதி 3.2: ரூபாய் நோட்டுகள் கணக்கீடு
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
                    st.warning("🔒 **OTP அனுப்பப்பட்டுவிட்டது! பணக் கணக்கீட்டில் இனி எந்த மாற்றமும் செய்ய முடியாது.**")

                col_den1, col_den2 = st.columns([1.4, 1])

                with col_den1:
                    st.markdown("#### 💵 ரொக்கப் பரிமாற்ற நோட்டுகள் கணக்கீடு")

                    in_500, in_200, in_100, in_50, in_20, in_10, in_5, in_coins = 0, 0, 0, 0, 0, 0, 0, 0
                    out_500, out_200, out_100, out_50, out_20, out_10, out_5, out_coins = 0, 0, 0, 0, 0, 0, 0, 0

                    if cash_portion > 0:
                        if net_target < 0:
                            with st.expander("📥 வாடிக்கையாளர் தந்த நோட்டுகள் (Cash IN)", expanded=True):
                                r1_1, r1_2, r1_3, r1_4 = st.columns(4)
                                in_500 = r1_1.number_input("₹500", min_value=0, step=1, key="in_500", disabled=otp_already_sent)
                                in_200 = r1_2.number_input("₹200", min_value=0, step=1, key="in_200", disabled=otp_already_sent)
                                in_100 = r1_3.number_input("₹100", min_value=0, step=1, key="in_100", disabled=otp_already_sent)
                                in_50 = r1_4.number_input("₹50", min_value=0, step=1, key="in_50", disabled=otp_already_sent)

                                r2_1, r2_2, r2_3, r2_4 = st.columns(4)
                                in_20 = r2_1.number_input("₹20", min_value=0, step=1, key="in_20", disabled=otp_already_sent)
                                in_10 = r2_2.number_input("₹10", min_value=0, step=1, key="in_10", disabled=otp_already_sent)
                                in_5 = r2_3.number_input("₹5", min_value=0, step=1, key="in_5", disabled=otp_already_sent)
                                in_coins = r2_4.number_input("சில்லறை ₹", min_value=0, step=1, key="in_coins", disabled=otp_already_sent)

                        else:
                            with st.expander("📤 நாம் வாடிக்கையாளருக்கு கொடுத்த நோட்டுகள் (Cash OUT)", expanded=True):
                                max_500 = max(0, current_drawer["500"])
                                max_200 = max(0, current_drawer["200"])
                                max_100 = max(0, current_drawer["100"])
                                max_50 = max(0, current_drawer["50"])
                                max_20 = max(0, current_drawer["20"])
                                max_10 = max(0, current_drawer["10"])
                                max_5 = max(0, current_drawer["5"])
                                max_coins = max(0, current_drawer["coins"])

                                o1_1, o1_2, o1_3, o1_4 = st.columns(4)
                                out_500 = o1_1.number_input(f"₹500 (இருப்பு:{max_500})", min_value=0, max_value=max_500, step=1, key="out_500", disabled=otp_already_sent)
                                out_200 = o1_2.number_input(f"₹200 (இருப்பு:{max_200})", min_value=0, max_value=max_200, step=1, key="out_200", disabled=otp_already_sent)
                                out_100 = o1_3.number_input(f"₹100 (இருப்பு:{max_100})", min_value=0, max_value=max_100, step=1, key="out_100", disabled=otp_already_sent)
                                out_50 = o1_4.number_input(f"₹50 (இருப்பு:{max_50})", min_value=0, max_value=max_50, step=1, key="out_50", disabled=otp_already_sent)

                                o2_1, o2_2, o2_3, o2_4 = st.columns(4)
                                out_20 = o2_1.number_input(f"₹20 (இருப்பு:{max_20})", min_value=0, max_value=max_20, step=1, key="out_20", disabled=otp_already_sent)
                                out_10 = o2_2.number_input(f"₹10 (இருப்பு:{max_10})", min_value=0, max_value=max_10, step=1, key="out_10", disabled=otp_already_sent)
                                out_5 = o2_3.number_input(f"₹5 (இருப்பு:{max_5})", min_value=0, max_value=max_5, step=1, key="out_5", disabled=otp_already_sent)
                                out_coins = o2_4.number_input(f"நாணயங்கள் (இருப்பு:{max_coins})", min_value=0, max_value=max_coins, step=1, key="out_coins", disabled=otp_already_sent)

                    total_cash_in = (in_500 * 500) + (in_200 * 200) + (in_100 * 100) + (in_50 * 50) + (in_20 * 20) + (in_10 * 10) + (in_5 * 5) + in_coins
                    total_cash_out = (out_500 * 500) + (out_200 * 200) + (out_100 * 100) + (out_50 * 50) + (out_20 * 20) + (out_10 * 10) + (out_5 * 5) + out_coins

                    actual_counted_cash = total_cash_in if net_target < 0 else total_cash_out

                    is_cash_tally = (actual_counted_cash == cash_portion)
                    is_bank_valid = True if bank_portion == 0 else bool(bank_ref_no.strip())
                    is_ready_to_verify = is_cash_tally and is_bank_valid

                    st.markdown("---")
                    with st.container(border=True):
                        t_c1, t_c2 = st.columns(2)
                        t_c1.metric("தேவையான ரொக்கம்", f"₹{cash_portion:,.2f}")
                        t_c2.metric("எண்ணப்பட்ட ரொக்கம்", f"₹{actual_counted_cash:,.2f}")

                        if not is_cash_tally:
                            st.error(f"❌ ரொக்க நோட்டுகளின் கூட்டுத்தொகை பொருந்தவில்லை! வித்தியாசம்: ₹{abs(cash_portion - actual_counted_cash):,.2f}")
                        elif bank_portion > 0 and not bank_ref_no.strip():
                            st.warning("⚠️ வங்கி பரிவர்த்தனைக்கான UTR / Ref எண்ணை உள்ளிடவும்!")
                        else:
                            st.success("✅ ரொக்கம் மற்றும் வங்கிப் பிரிவுகள் சரியாகப் பொருந்துகின்றன!")

                # பகுதி 3.3: OTP சரிபார்ப்பு & நிறைவு செய்தல்
                with col_den2:
                    st.markdown("#### 📲 OTP சரிபார்ப்பு (Fast2SMS DLT)")
                    st.write(f"வாடிக்கையாளர்: **{visit['customer_name']}**")
                    st.write(f"மொபைல் எண்: **{visit['mobile']}**")

                    if not is_ready_to_verify:
                        st.warning("⚠️ ரொக்கம் மற்றும் UTR எண் சரியாக அமைந்ததும் OTP இயங்கும்.")
                        st.button("📲 OTP அனுப்புக (Send SMS OTP)", disabled=True, key="otp_btn_disabled")
                    elif otp_already_sent:
                        st.success("✅ OTP வாடிக்கையாளருக்கு அனுப்பப்பட்டுவிட்டது!")
                    else:
                        if st.button("📲 OTP அனுப்புக (Send SMS OTP)", type="primary", key="otp_btn_active"):
                            otp_code = str(random.randint(1000, 9999))
                            st.session_state.generated_otp = otp_code
                            with st.spinner("DLT மூலம் SMS அனுப்பப்படுகிறது..."):
                                sms_success, msg_detail = send_fast2sms_otp(visit["mobile"], otp_code)
                            if sms_success:
                                st.success("✅ OTP SMS அனுப்பப்பட்டது!")
                            else:
                                st.info(f"💡 தற்காலிக சோதனை OTP: **{otp_code}**")
                            st.rerun()

                    entered_otp = st.text_input("வாடிக்கையாளர் மொபைலுக்கு வந்த OTP உள்ளிடவும்", max_chars=4)

                    if st.button("✅ வருகையை நிறைவு செய்க (Complete Visit)", type="primary", use_container_width=True):
                        if not is_ready_to_verify:
                            st.error("❌ கணக்கீடு அல்லது UTR எண் விடுபட்டுள்ளது!")
                        elif not otp_already_sent:
                            st.error("❌ முதலில் வாடிக்கையாளருக்கு OTP அனுப்பவும்!")
                        else:
                            expected_otp = st.session_state.get("generated_otp")
                            if entered_otp and entered_otp == expected_otp:
                                with st.spinner("வருகை சேமிக்கப்படுகிறது..."):
                                    pm_label = "Cash" if bank_portion == 0 else ("Bank/UPI" if cash_portion == 0 else "Split (Cash+Online)")
                                    visit_data = {
                                        "visit_no": visit["visit_no"],
                                        "customer_id": visit["customer_id"],
                                        "branch_id": st.session_state.branch_id,
                                        "total_paid": visit["total_paid"],
                                        "total_received": visit["total_received"],
                                        "net_cash_amount": visit["net_amount"],
                                        "cash_amount": float(cash_portion),
                                        "bank_amount": float(bank_portion),
                                        "payment_mode": pm_label,
                                        "bank_reference_no": bank_ref_no.strip() if bank_portion > 0 else None,
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

                                    st.success(f"🎉 வருகை {visit['visit_no']} நிறைவுபெற்றது! இது அழைப்பு சரிபார்ப்புக்கு அனுப்பப்பட்டுள்ளது.")
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
