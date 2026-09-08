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

    div[data-testid="stExpander"], div[data-testid="stVerticalBlock"] > div[style*="border:"] {
        background: #FFFFFF !important;
        border: 1.5px solid #E1D2F5 !important;
        border-radius: 14px !important;
        box-shadow: 0 3px 12px rgba(74, 32, 122, 0.05) !important;
        color: #26153B !important;
        overflow: hidden;
    }

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
# 3. ஆவணப் பதிவேற்றம், SMS & கல்லா செயல்பாடுகள்
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

def upload_single_file(file_obj, folder_name):
    if not file_obj:
        return None
    bucket_name = "branch-documents"
    file_path = f"{folder_name}/{datetime.now().strftime('%Y%m%d%H%M%S')}_{file_obj.name}"
    supabase.storage.from_(bucket_name).upload(
        path=file_path,
        file=file_obj.getvalue(),
        file_options={"content-type": file_obj.type, "upsert": "true"},
    )
    return supabase.storage.from_(bucket_name).get_public_url(file_path)

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
    st.markdown("### 📊 காரணப் பணியாளர் வாரியான நடவடிக்கைகள் அறிக்கை")

    f_col1, f_col2, f_col3 = st.columns([1.5, 1.5, 2])
    start_date = f_col1.date_input("தொடக்கத் தேதி (From):", value=date.today().replace(day=1), key=f"rep_s_{selected_branch_id}")
    end_date = f_col2.date_input("முடிவுத் தேதி (To):", value=date.today(), key=f"rep_e_{selected_branch_id}")

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
    all_staff_set = set(["Walk-in (நேரடி வருகை)"])

    for v in visits:
        b_name = v.get("branches", {}).get("branch_name", "Unknown") if v.get("branches") else "Unknown"
        for t in v.get("transactions", []):
            s_name = t.get("staff_name") or "Walk-in (நேரடி வருகை)"
            all_staff_set.add(s_name)
            flat_data.append({
                "தேதி": str(v.get("created_at", ""))[:10],
                "வருகை எண்": v.get("visit_no", "-"),
                "கிளை": b_name,
                "காரணப் பணியாளர்": s_name,
                "நடவடிக்கை வகை": t.get("transaction_type", "-"),
                "பட்டுவாடா (Paid ₹)": float(t.get("paid_amount", 0.0)),
                "வரவு (Received ₹)": float(t.get("received_amount", 0.0)),
                "பணம் செலுத்திய முறை": v.get("payment_mode", "Cash"),
                "குறிப்பு": t.get("remarks", "")
            })

    if not flat_data:
        st.info("தேர்ந்தெடுக்கப்பட்ட தேதி வரம்பில் பரிவர்த்தனைகள் எதுவும் இல்லை.")
        return

    staff_filter_options = ["அனைத்து பணியாளர்களும் (All Staff & Walk-in)"] + sorted(list(all_staff_set))
    with f_col3:
        selected_staff_filter = st.selectbox("காரணப் பணியாளரைத் தேர்ந்தெடுக்கவும்:", staff_filter_options, key=f"staff_flt_{selected_branch_id}")

    df_rep = pd.DataFrame(flat_data)

    if selected_staff_filter != "அனைத்து பணியாளர்களும் (All Staff & Walk-in)":
        df_filtered = df_rep[df_rep["காரணப் பணியாளர்"] == selected_staff_filter].copy()
    else:
        df_filtered = df_rep.copy()

    tot_txns = len(df_filtered)
    tot_paid = df_filtered["பட்டுவாடா (Paid ₹)"].sum()
    tot_rec = df_filtered["வரவு (Received ₹)"].sum()
    net_business_flow = tot_paid - tot_rec

    walkin_df = df_rep[df_rep["காரணப் பணியாளர்"].str.contains("Walk-in", na=False)]
    walkin_vol = walkin_df["பட்டுவாடா (Paid ₹)"].sum() + walkin_df["வரவு (Received ₹)"].sum()

    staff_biz_df = df_rep[~df_rep["காரணப் பணியாளர்"].str.contains("Walk-in", na=False)]
    staff_biz_vol = staff_biz_df["பட்டுவாடா (Paid ₹)"].sum() + staff_biz_df["வரவு (Received ₹)"].sum()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("மொத்த நடவடிக்கைகள்", f"{tot_txns:,}")
    m2.metric("மொத்த பட்டுவாடா", f"₹{tot_paid:,.2f}")
    m3.metric("மொத்த வரவு", f"₹{tot_rec:,.2f}")
    m4.metric("நிகர ரொக்கப் புழக்கம்", f"₹{abs(net_business_flow):,.2f}")

    if selected_staff_filter == "அனைத்து பணியாளர்களும் (All Staff & Walk-in)":
        st.caption(f"💡 **பிசினஸ் பங்களிப்பு ஒப்பீடு:** பணியாளர்கள் வழி பிசினஸ்: **₹{staff_biz_vol:,.2f}** | நேரடி வருகை (Walk-in) பிசினஸ்: **₹{walkin_vol:,.2f}**")

    st.markdown("---")

    st.markdown(f"##### 👥 பிசினஸ் தொகுப்பு விவரங்கள் ({selected_staff_filter})")
    staff_summary = df_filtered.groupby(["காரணப் பணியாளர்", "நடவடிக்கை வகை"]).agg(
        எண்ணிக்கை=("நடவடிக்கை வகை", "count"),
        வழங்கிய_தொகை=("பட்டுவாடா (Paid ₹)", "sum"),
        பெற்ற_தொகை=("வரவு (Received ₹)", "sum")
    ).reset_index()

    staff_summary["நிகர_ரொக்கம்"] = staff_summary["வழங்கிய_தொகை"] - staff_summary["பெற்ற_தொகை"]
    staff_summary.columns = ["காரணப் பணியாளர்", "நடவடிக்கை வகை", "எண்ணிக்கை", "பட்டுவாடா (Paid ₹)", "வரவு (Received ₹)", "நிகர ரொக்கம் (Net ₹)"]
    st.dataframe(staff_summary, use_container_width=True)

    with st.expander("📑 அனைத்து தனிநபர் பரிவர்த்தனைகளின் விரிவான பட்டியல் (Detailed Log)"):
        st.dataframe(df_filtered, use_container_width=True)

    csv = staff_summary.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 அறிக்கையைப் பதிவிறக்குக (Download CSV)",
        data=csv,
        file_name=f"Staff_Report_{start_date}_to_{end_date}.csv",
        mime="text/csv",
        key=f"dl_csv_{selected_branch_id}"
    )

# ==========================================
# 4. தற்காலிக மாறிகள்
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
# 5. உள்நுழைவு திரை
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
                        st.error("தவறான பயனர் பெயர் அல்லது கடவுச்சொல்!")
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
                "📈 காரணப் பணியாளர் அறிக்கை"
            ]
        )

        with tab1:
            st.subheader("➕ புதிய கிளை சேர்த்தல்")
            with st.form("admin_add_branch_form", clear_on_submit=True):
                b_name = st.text_input("கிளையின் பெயர்", placeholder="எ.கா: திங்கள்நகர் கிளை")
                b_code = st.text_input("கிளை குறியீடு", placeholder="எ.கா: TGL")
                if st.form_submit_button("கிளையைச் சேர்"):
                    if b_name.strip() and b_code.strip():
                        try:
                            supabase.table("branches").insert({"branch_name": b_name.strip(), "branch_code": b_code.strip().upper()}).execute()
                            st.success(f"'{b_name}' வெற்றிகரமாகச் சேர்க்கப்பட்டது!")
                            st.rerun()
                        except Exception as err:
                            st.error(f"பிழை: {err}")

            b_list_res = supabase.table("branches").select("id, branch_name, branch_code").order("id").execute()
            if b_list_res.data:
                st.dataframe(pd.DataFrame(b_list_res.data), use_container_width=True)

        with tab2:
            st.subheader("👥 பணியாளர்கள் பட்டியல் & சேர்த்தல்")
            users_res = supabase.table("users").select("id, name, username, role, branch_id, is_active").order("id").execute()
            if users_res.data:
                st.dataframe(pd.DataFrame([{
                    "ID": u["id"], "பெயர்": u["name"], "Username": u["username"], "பணி நிலை": u["role"],
                    "கிளை": branch_id_to_name.get(u.get("branch_id"), "HO / Special"),
                    "நிலை": "🟢 Active" if u.get("is_active", True) else "🔴 Inactive"
                } for u in users_res.data]), use_container_width=True)

            st.markdown("---")
            sub_col1, sub_col2 = st.columns(2)
            with sub_col1:
                with st.form("admin_add_user_form", clear_on_submit=True):
                    u_name = st.text_input("முழுப் பெயர்")
                    u_username = st.text_input("உள்நுழைவு பெயர்")
                    u_pass = st.text_input("கடவுச்சொல்", type="password")
                    u_role = st.selectbox("பணி நிலை", ["Branch Head / Cashier", "Staff", "Operations", "Auditor", "Admin"])
                    b_selection = st.selectbox("கிளை", options=list(branch_options.keys()))
                    if st.form_submit_button("உருவாக்கு"):
                        if u_name.strip() and u_username.strip() and u_pass.strip():
                            b_id = branch_options.get(b_selection) if u_role not in ["Admin", "Auditor", "Operations"] else None
                            supabase.table("users").insert({
                                "name": u_name.strip(), "username": u_username.strip(),
                                "password_hash": u_pass.strip(), "role": u_role, "branch_id": b_id, "is_active": True
                            }).execute()
                            st.success("பயனர் உருவாக்கப்பட்டுவிட்டார்!")
                            st.rerun()

            with sub_col2:
                if users_res.data:
                    user_choices = {f"{u['name']} (@{u['username']})": u for u in users_res.data}
                    selected_user_key = st.selectbox("திருத்த வேண்டிய பணியாளர்", list(user_choices.keys()))
                    curr_user = user_choices[selected_user_key]
                    with st.form("admin_edit_user_form"):
                        edit_name = st.text_input("பெயர்", value=curr_user["name"])
                        edit_pass = st.text_input("புதிய கடவுச்சொல் (விரும்பினால் மட்டும்)", type="password")
                        roles_list = ["Branch Head / Cashier", "Staff", "Operations", "Auditor", "Admin"]
                        edit_role = st.selectbox("பணி நிலை", roles_list, index=roles_list.index(curr_user["role"]))
                        edit_status = st.radio("நிலை", ["Active", "Inactive"], index=0 if curr_user.get("is_active", True) else 1)
                        if st.form_submit_button("புதுப்பி"):
                            up_data = {"name": edit_name.strip(), "role": edit_role, "is_active": edit_status == "Active"}
                            if edit_pass.strip():
                                up_data["password_hash"] = edit_pass.strip()
                            supabase.table("users").update(up_data).eq("id", curr_user["id"]).execute()
                            st.success("புதுப்பிக்கப்பட்டது!")
                            st.rerun()

        with tab3:
            st.subheader("📥 பழைய வாடிக்கையாளர் இறக்குமதி (Bulk Import)")
            uploaded_cust_file = st.file_uploader("கோப்பைத் தேர்வு செய்யவும்", type=["xls", "xlsx", "csv"])
            if uploaded_cust_file and st.button("பதிவேற்றத்தைத் தொடங்கு", type="primary"):
                df_raw = pd.read_csv(uploaded_cust_file, skiprows=2) if uploaded_cust_file.name.endswith(".csv") else pd.read_excel(uploaded_cust_file, skiprows=2)
                df_cust = df_raw.dropna(subset=["Full Name", "Mobile No"]).copy()
                st.success(f"{len(df_cust)} வாடிக்கையாளர்கள் பதிவு செய்யப்படுகிறார்கள்...")

        # -----------------------------------------------------------------
        # tab4: வாடிக்கையாளர் மேலாண்மை (முழுமையான திருத்தப் படிவத்துடன்)
        # -----------------------------------------------------------------
        with tab4:
            st.subheader("🗂️ வாடிக்கையாளர் பட்டியல் & திருத்தம் (Customer Directory & Edit)")

            filter_c1, filter_c2 = st.columns([2, 3])
            with filter_c1:
                b_filters = ["அனைத்து கிளைகளும் (All Branches)"] + list(branch_options.keys())
                sel_b_flt = st.selectbox("கிளை வாரியாகப் பார்க்க:", b_filters, key="adm_cust_b_filter")
            with filter_c2:
                admin_search_q = st.text_input("வாடிக்கையாளர் பெயர் / மொபைல் / Code தேடுக:", placeholder="எ.கா: ராம் அல்லது 98765...", key="adm_cust_search")

            cq = supabase.table("customers").select("*, branches(branch_name)").order("id", desc=True)
            if sel_b_flt != "அனைத்து கிளைகளும் (All Branches)":
                cq = cq.eq("branch_id", branch_options.get(sel_b_flt))

            if admin_search_q.strip():
                sq = admin_search_q.strip()
                cq = cq.or_(f"name.ilike.%{sq}%,mobile.ilike.%{sq}%,customer_code.ilike.%{sq}%")
            else:
                cq = cq.limit(100)

            cust_list_data = cq.execute().data or []
            st.write(f"📊 கண்டறியப்பட்ட வாடிக்கையாளர்கள்: **{len(cust_list_data)}**")

            if cust_list_data:
                st.dataframe(pd.DataFrame([{
                    "ID": c["id"],
                    "Code": c.get("customer_code", "-"),
                    "பெயர்": c["name"],
                    "கார்டியன்": c.get("guardian_name", "-"),
                    "மொபைல்": c.get("mobile", "-"),
                    "கிளை": c.get("branches", {}).get("branch_name", "பொது"),
                    "KYC நிலை": c.get("kyc_status", "Approved"),
                    "நிலை": "🟢 Active" if c.get("is_active", True) else "🔴 Inactive",
                    "முகவரி": c.get("address", "-")
                } for c in cust_list_data]), use_container_width=True)

                st.markdown("---")
                st.subheader("✏️ வாடிக்கையாளர் விவரங்கள் மற்றும் KYC ஆவணங்கள் திருத்துதல்")

                cust_dict_edit = {f"{c.get('customer_code', '')} - {c['name']} ({c.get('mobile', '')})": c for c in cust_list_data}
                sel_cust_key = st.selectbox("திருத்த வேண்டிய வாடிக்கையாளரைத் தேர்வு செய்க:", list(cust_dict_edit.keys()), key="adm_sel_cust_edit")
                curr_c = cust_dict_edit[sel_cust_key]

                with st.form("admin_edit_customer_full_form"):
                    e_col1, e_col2, e_col3 = st.columns(3)

                    with e_col1:
                        ed_name = st.text_input("வாடிக்கையாளர் பெயர்", value=curr_c.get("name", ""))
                        ed_guard = st.text_input("கார்டியன் பெயர்", value=curr_c.get("guardian_name", "") or "")
                        gender_list = ["Male", "Female", "Other", "ஆண்", "பெண்"]
                        g_curr = curr_c.get("gender", "Male")
                        g_idx = gender_list.index(g_curr) if g_curr in gender_list else 0
                        ed_gender = st.selectbox("பாலினம்", gender_list, index=g_idx)
                        ed_dob = st.text_input("பிறந்த தேதி (YYYY-MM-DD)", value=str(curr_c.get("dob", "") or ""))

                    with e_col2:
                        ed_mob = st.text_input("முதன்மை மொபைல்", value=str(curr_c.get("mobile", "") or ""))
                        ed_mob2 = st.text_input("கூடுதல் மொபைல்", value=str(curr_c.get("mobile2", "") or ""))
                        ed_bname = branch_id_to_name.get(curr_c.get("branch_id"), list(branch_options.keys())[0] if branch_options else "")
                        b_opts_list = list(branch_options.keys())
                        b_idx = b_opts_list.index(ed_bname) if ed_bname in b_opts_list else 0
                        ed_branch = st.selectbox("ஒதுக்கப்பட்ட கிளை", b_opts_list, index=b_idx)
                        ed_nominee = st.text_input("நாமினி பெயர்", value=curr_c.get("nominee_name", "") or "")
                        ed_rel = st.text_input("நாமினி உறவுமுறை", value=curr_c.get("nominee_relation", "") or "")

                    with e_col3:
                        ed_addr = st.text_area("முழு முகவரி", value=curr_c.get("address", "") or "", height=80)
                        
                        kyc_options = ["Approved", "Pending_KYC_Approval", "Rejected"]
                        curr_kyc_st = curr_c.get("kyc_status", "Approved") or "Approved"
                        k_idx = kyc_options.index(curr_kyc_st) if curr_kyc_st in kyc_options else 0
                        ed_kyc_st = st.selectbox("KYC ஒப்புதல் நிலை (KYC Status)", kyc_options, index=k_idx)

                        ed_status = st.radio(
                            "வாடிக்கையாளர் நிலை (Active / Inactive)",
                            ["Active (செயலில் உள்ளார்)", "Inactive (முடக்கு)"],
                            index=0 if curr_c.get("is_active", True) else 1
                        )

                    st.markdown("##### 📁 தற்போது இணைக்கப்பட்டுள்ள ஆவணங்கள்:")
                    doc_c1, doc_c2, doc_c3 = st.columns(3)
                    with doc_c1:
                        if curr_c.get("photo_url"):
                            st.markdown(f"🔗 [தற்போதைய படம்]({curr_c['photo_url']})")
                        ed_new_photo = st.file_uploader("புதிய படம் மாற்ற (Optional):", type=["jpg", "jpeg", "png"], key=f"adm_n_p_{curr_c['id']}")
                    with doc_c2:
                        if curr_c.get("id_proof_url"):
                            st.markdown(f"🔗 [தற்போதைய அடையாள அட்டை]({curr_c['id_proof_url']})")
                        ed_new_id = st.file_uploader("புதிய அடையாள ஆவணம் (Optional):", type=["jpg", "jpeg", "png", "pdf"], key=f"adm_n_id_{curr_c['id']}")
                    with doc_c3:
                        if curr_c.get("address_proof_url"):
                            st.markdown(f"🔗 [தற்போதைய முகவரி ஆவணம்]({curr_c['address_proof_url']})")
                        ed_new_addr = st.file_uploader("புதிய முகவரி ஆவணம் (Optional):", type=["jpg", "jpeg", "png", "pdf"], key=f"adm_n_ad_{curr_c['id']}")

                    if st.form_submit_button("வாடிக்கையாளர் மாற்றங்களைச் சேமி (Update Customer)", type="primary"):
                        try:
                            up_payload = {
                                "name": ed_name.strip(),
                                "guardian_name": ed_guard.strip(),
                                "gender": ed_gender,
                                "dob": ed_dob.strip() if ed_dob.strip() else None,
                                "mobile": ed_mob.strip(),
                                "mobile2": ed_mob2.strip(),
                                "branch_id": branch_options.get(ed_branch),
                                "nominee_name": ed_nominee.strip(),
                                "nominee_relation": ed_rel.strip(),
                                "address": ed_addr.strip(),
                                "kyc_status": ed_kyc_st,
                                "is_active": True if "Active" in ed_status else False
                            }
                            if ed_new_photo:
                                up_payload["photo_url"] = upload_single_file(ed_new_photo, "customer_photos")
                            if ed_new_id:
                                up_payload["id_proof_url"] = upload_single_file(ed_new_id, "customer_id_proofs")
                            if ed_new_addr:
                                up_payload["address_proof_url"] = upload_single_file(ed_new_addr, "customer_address_proofs")

                            supabase.table("customers").update(up_payload).eq("id", curr_c["id"]).execute()
                            st.success("வாடிக்கையாளர் விவரங்கள் வெற்றிகரமாகப் புதுப்பிக்கப்பட்டன!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"சேமிப்பதில் பிழை: {e}")
            else:
                st.info("வாடிக்கையாளர் விவரங்கள் எதுவும் இல்லை.")

        with tab5:
            st.subheader("📊 வருகை & பரிவர்த்தனை மேலாண்மை")
            v_records = supabase.table("customer_visits").select("*, customers(name, mobile), transactions(*)").order("id", desc=True).limit(20).execute().data or []
            for vr in v_records:
                c_name = vr.get("customers", {}).get("name", "-")
                with st.expander(f"{vr['visit_no']} | {c_name} | ₹{vr['net_cash_amount']:,.2f} | {vr['status']}"):
                    if vr.get("transactions"):
                        st.dataframe(pd.DataFrame(vr["transactions"]))

        with tab6:
            st.subheader("💰 கிளை துவக்க இருப்பு நிர்ணயம்")
            sel_op_branch = st.selectbox("கிளை:", list(branch_options.keys()), key="sel_op_b")
            with st.form("admin_op_form"):
                op_500 = st.number_input("₹500", min_value=0, step=1)
                op_200 = st.number_input("₹200", min_value=0, step=1)
                op_100 = st.number_input("₹100", min_value=0, step=1)
                op_50 = st.number_input("₹50", min_value=0, step=1)
                calc_total = (op_500 * 500) + (op_200 * 200) + (op_100 * 100) + (op_50 * 50)
                if st.form_submit_button("சேமி", type="primary"):
                    supabase.table("branch_cash_box").upsert({
                        "branch_id": branch_options[sel_op_branch],
                        "entry_date": str(date.today()),
                        "opening_balance": calc_total,
                        "opening_denomination": {"500": op_500, "200": op_200, "100": op_100, "50": op_50}
                    }, on_conflict="branch_id,entry_date").execute()
                    st.success("சேமிக்கப்பட்டது!")
                    st.rerun()

        with tab7:
            st.subheader("🏦 தலைமையக பணப் பரிமாற்றம் (HO ⇄ Branch)")
            with st.form("adm_fund_form"):
                ft_b = st.selectbox("கிளை:", list(branch_options.keys()))
                ft_type = st.selectbox("வகை:", ["HO_TO_BRANCH", "BRANCH_TO_HO"])
                ft_amt = st.number_input("தொகை (₹):", min_value=0.0, step=1000.0)
                if st.form_submit_button("பரிமாற்றத்தைச் சேமி"):
                    supabase.table("branch_fund_transfers").insert({
                        "branch_id": branch_options[ft_b], "transfer_date": str(date.today()),
                        "transfer_type": ft_type, "amount": ft_amt, "payment_mode": "Cash", "created_by": st.session_state.username
                    }).execute()
                    st.success("பதிவு செய்யப்பட்டது!")
                    st.rerun()

        with tab8:
            rep_b_opts = ["அனைத்து கிளைகளும் (All Branches)"] + list(branch_options.keys())
            sel_rep_b = st.selectbox("கிளையை வடிகட்டவும்:", rep_b_opts, key="adm_rep_branch_sel")
            filter_b_id = branch_options.get(sel_rep_b) if sel_rep_b != "அனைத்து கிளைகளும் (All Branches)" else None
            render_staff_attribution_report(selected_branch_id=filter_b_id)

    # ----------------------------------------------------
    # B. ஆப்பரேஷன்ஸ் திரை (OPERATIONS CALLING & KYC DESK)
    # ----------------------------------------------------
    elif st.session_state.user_role == "Operations":
        st.header("📞 ஆப்பரேஷன்ஸ் மேசை (Operations Desk)")
        ops_tab1, ops_tab2 = st.tabs([
            "👤 புதிய வாடிக்கையாளர் KYC ஒப்புதல் (New Customer KYC)",
            "🔔 பரிவர்த்தனை அழைப்பு சரிபார்ப்பு (Transaction Calls)"
        ])

        with ops_tab1:
            st.subheader("👤 புதிய வாடிக்கையாளர் KYC ஆவண சரிபார்ப்பு & ஒப்புதல்")
            pending_kyc_custs = (
                supabase.table("customers")
                .select("*, branches(branch_name)")
                .eq("kyc_status", "Pending_KYC_Approval")
                .order("id", desc=True)
                .execute()
                .data or []
            )

            if not pending_kyc_custs:
                st.info("✅ சரிபார்ப்புக்கு புதிய வாடிக்கையாளர்கள் எவரும் நிலுவையில் இல்லை.")
            else:
                st.write(f"📊 ஒப்புதலுக்குக் காத்திருக்கும் புதிய வாடிக்கையாளர்கள்: **{len(pending_kyc_custs)}**")
                for pcust in pending_kyc_custs:
                    b_name = pcust.get("branches", {}).get("branch_name", "Branch")
                    with st.expander(f"🆕 {pcust['customer_code']} | {pcust['name']} | கிளை: {b_name} | 📞 {pcust['mobile']}"):
                        k_c1, k_c2, k_c3 = st.columns([1.5, 1, 1])

                        with k_c1:
                            st.markdown(f"### {pcust['name']}")
                            st.write(f"👨‍👦 **கார்டியன்:** {pcust.get('guardian_name', '-')}")
                            st.write(f"🎂 **பிறந்த தேதி:** {pcust.get('dob', '-')} | **பாலினம்:** {pcust.get('gender', '-')}")
                            st.write(f"📞 **முதன்மை எண்:** `{pcust.get('mobile')}` | **கூடுதல்:** `{pcust.get('mobile2', '-')}`")
                            st.write(f"🏠 **முகவரி:** {pcust.get('address', '-')}")
                            st.write(f"👥 **நாமினி:** {pcust.get('nominee_name', '-')} ({pcust.get('nominee_relation', '-')})")

                        with k_c2:
                            st.markdown("##### 📸 வாடிக்கையாளர் படம்")
                            if pcust.get("photo_url"):
                                st.image(pcust["photo_url"], width=150)
                            else:
                                st.caption("படம் இணைக்கப்படவில்லை")

                        with k_c3:
                            st.markdown("##### 📁 KYC ஆவணங்கள்")
                            if pcust.get("id_proof_url"):
                                st.markdown(f"- 🪪 [அடையாள ஆவணத்தைப் பார்க்க]({pcust['id_proof_url']})")
                            else:
                                st.caption("🪪 அடையாள ஆவணம் இல்லை")

                            if pcust.get("address_proof_url"):
                                st.markdown(f"- 📄 [முகவரி ஆவணத்தைப் பார்க்க]({pcust['address_proof_url']})")
                            else:
                                st.caption("📄 முகவரி ஆவணம் இல்லை")

                        kyc_reason = st.text_input("காரணம் / குறிப்பு:", key=f"kyc_note_{pcust['id']}")

                        kyc_btn1, kyc_btn2 = st.columns(2)
                        with kyc_btn1:
                            if st.button("✅ வாடிக்கையாளரை அங்கீகரி (Approve KYC)", key=f"app_kyc_{pcust['id']}", type="primary"):
                                supabase.table("customers").update({
                                    "kyc_status": "Approved",
                                    "is_active": True,
                                    "kyc_remarks": f"Approved by {st.session_state.username} | {kyc_reason}"
                                }).eq("id", pcust["id"]).execute()
                                st.success(f"{pcust['name']} அங்கீகரிக்கப்பட்டார்!")
                                st.rerun()

                        with kyc_btn2:
                            if st.button("❌ மறுப்பு (Reject)", key=f"rej_kyc_{pcust['id']}"):
                                if kyc_reason.strip():
                                    supabase.table("customers").update({
                                        "kyc_status": "Rejected",
                                        "is_active": False,
                                        "kyc_remarks": f"Rejected by {st.session_state.username} | {kyc_reason.strip()}"
                                    }).eq("id", pcust["id"]).execute()
                                    st.warning("நிராகரிக்கப்பட்டார்.")
                                    st.rerun()
                                else:
                                    st.error("காரணத்தை உள்ளிடவும்.")

        with ops_tab2:
            st.subheader("📞 அழைப்பு சரிபார்ப்பு (Operations Calling Desk)")
            ops_visits = supabase.table("customer_visits").select("*, customers(*), transactions(*), branches(branch_name)").eq("status", "Pending_Calling_Verification").order("id").execute().data or []
            if not ops_visits:
                st.info("✅ சரிபார்ப்புக்கு பரிவர்த்தனைகள் எதுவும் இல்லை.")
            else:
                for item in ops_visits:
                    cust = item.get("customers", {})
                    b_name = item.get("branches", {}).get("branch_name", "Branch")
                    with st.expander(f"🔔 {item['visit_no']} | {b_name} | {cust.get('name')} | ₹{item['net_cash_amount']:,.2f}"):
                        st.write(f"📞 அழைக்க வேண்டிய எண்: `{cust.get('mobile')}`")
                        if item.get("transactions"):
                            st.dataframe(pd.DataFrame(item["transactions"])[["transaction_type", "paid_amount", "received_amount", "remarks"]], use_container_width=True)
                        if st.button("✅ அழைப்பு சரிபார்க்கப்பட்டது (Call Verified)", key=f"v_call_{item['id']}", type="primary"):
                            supabase.table("customer_visits").update({"status": "Pending_Branch_Docs"}).eq("id", item["id"]).execute()
                            st.success("சரிபார்க்கப்பட்டது!")
                            st.rerun()

    # ----------------------------------------------------
    # C. தணிக்கையர் திரை (AUDITOR DESK)
    # ----------------------------------------------------
    elif st.session_state.user_role == "Auditor":
        st.header("🔍 தணிக்கையர் பணிப்பாய்வு (Auditor Verification)")
        pending_visits = supabase.table("customer_visits").select("*, customers(name, mobile), transactions(*), audit_records(*)").eq("status", "Submitted_to_Auditor").execute().data or []
        if not pending_visits:
            st.info("தணிக்கை செய்ய எந்த ஆவணங்களும் வரவில்லை.")
        else:
            for item in pending_visits:
                c_name = item.get("customers", {}).get("name", "-")
                with st.expander(f"வருகை: {item['visit_no']} | வாடிக்கையாளர்: {c_name} | ₹{item['net_cash_amount']:,.2f}"):
                    if item.get("transactions"):
                        st.dataframe(pd.DataFrame(item["transactions"]))
                    audit_recs = item.get("audit_records", [])
                    if audit_recs and audit_recs[0].get("document_urls"):
                        for doc_url in audit_recs[0]["document_urls"]:
                            st.markdown(f"- 🔗 [ஆவணத்தைப் பார்க்க]({doc_url})")
                    if st.button(f"அங்கீகரி (Approve) - {item['visit_no']}", key=f"aud_app_{item['id']}", type="primary"):
                        supabase.table("customer_visits").update({"status": "Approved"}).eq("id", item["id"]).execute()
                        st.success("அங்கீகரிக்கப்பட்டது!")
                        st.rerun()

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
            "📈 காரணப் பணியாளர் அறிக்கை"
        ])

        with branch_tab6:
            render_staff_attribution_report(selected_branch_id=st.session_state.branch_id)

        with branch_tab5:
            st.subheader("🏦 தலைமையக பணப் பரிமாற்றம் (HO Fund Transfer Desk)")
            curr_b_drawer = get_current_branch_cash_drawer(st.session_state.branch_id)

            with st.form("branch_to_ho_fund_form", clear_on_submit=True):
                st.markdown("##### 📤 கிளையிலிருந்து தலைமையகத்திற்கு பணம் அனுப்புதல்")
                b_ft_c1, b_ft_c2 = st.columns(2)
                with b_ft_c1:
                    b_ft_mode = st.selectbox("அனுப்பும் முறை:", ["Cash (ரொக்கம்)", "Bank Transfer (வங்கி வரவு)"], key="b_ft_mode")
                    b_ft_ref = st.text_input("குறிப்பு எண் / UTR No:", key="b_ft_ref")
                with b_ft_c2:
                    b_ft_date = st.date_input("பரிமாற்ற தேதி:", value=date.today(), key="b_ft_date")

                st.markdown("##### 💵 நோட்டுகள் விவரம்:")
                bf_1, bf_2, bf_3, bf_4 = st.columns(4)
                with bf_1:
                    b_out_500 = st.number_input(f"₹500 (இருப்பு:{curr_b_drawer['500']})", min_value=0, max_value=max(0, curr_b_drawer['500']), step=1, key="b_out_500")
                    b_out_20 = st.number_input(f"₹20 (இருப்பு:{curr_b_drawer['20']})", min_value=0, max_value=max(0, curr_b_drawer['20']), step=1, key="b_out_20")
                with bf_2:
                    b_out_200 = st.number_input(f"₹200 (இருப்பு:{curr_b_drawer['200']})", min_value=0, max_value=max(0, curr_b_drawer['200']), step=1, key="b_out_200")
                    b_out_10 = st.number_input(f"₹10 (இருப்பு:{curr_b_drawer['10']})", min_value=0, max_value=max(0, curr_b_drawer['10']), step=1, key="b_out_10")
                with bf_3:
                    b_out_100 = st.number_input(f"₹100 (இருப்பு:{curr_b_drawer['100']})", min_value=0, max_value=max(0, curr_b_drawer['100']), step=1, key="b_out_100")
                    b_out_5 = st.number_input(f"₹5 (இருப்பு:{curr_b_drawer['5']})", min_value=0, max_value=max(0, curr_b_drawer['5']), step=1, key="b_out_5")
                with bf_4:
                    b_out_50 = st.number_input(f"₹50 (இருப்பு:{curr_b_drawer['50']})", min_value=0, max_value=max(0, curr_b_drawer['50']), step=1, key="b_out_50")
                    b_out_coins = st.number_input(f"நாணயங்கள் (₹)", min_value=0.0, step=1.0, key="b_out_coins")

                calc_b_cash_total = (b_out_500 * 500) + (b_out_200 * 200) + (b_out_100 * 100) + (b_out_50 * 50) + (b_out_20 * 20) + (b_out_10 * 10) + (b_out_5 * 5) + b_out_coins
                b_final_amt = float(calc_b_cash_total) if "Cash" in b_ft_mode else st.number_input("வங்கி தொகை (₹):", min_value=0.0, step=1000.0)

                if st.form_submit_button("சமர்ப்பிக்கவும்", type="primary"):
                    if b_final_amt > 0:
                        supabase.table("branch_fund_transfers").insert({
                            "branch_id": st.session_state.branch_id, "transfer_date": str(b_ft_date),
                            "transfer_type": "BRANCH_TO_HO", "amount": b_final_amt, "payment_mode": "Cash" if "Cash" in b_ft_mode else "Bank Transfer",
                            "reference_no": b_ft_ref.strip(), "denomination_details": {"500": b_out_500, "200": b_out_200, "100": b_out_100, "50": b_out_50, "20": b_out_20, "10": b_out_10, "5": b_out_5, "coins": b_out_coins} if "Cash" in b_ft_mode else {},
                            "created_by": st.session_state.username, "status": "Completed"
                        }).execute()
                        st.success(f"₹{b_final_amt:,.2f} தலைமையகத்திற்கு அனுப்பப்பட்டது!")
                        st.rerun()

        with branch_tab4:
            st.subheader("💼 கிளை கல்லா கையிருப்பு நிலை")
            curr_stock = get_current_branch_cash_drawer(st.session_state.branch_id)
            total_stock_val = (curr_stock["500"] * 500) + (curr_stock["200"] * 200) + (curr_stock["100"] * 100) + (curr_stock["50"] * 50) + (curr_stock["20"] * 20) + (curr_stock["10"] * 10) + (curr_stock["5"] * 5) + curr_stock["coins"]
            st.metric("கல்லாவில் உள்ள மொத்த ரொக்கம்", f"₹{total_stock_val:,.2f}")
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
            st.subheader("⚠️ விளக்கம் அளிக்க வேண்டியவை (Clarifications Inbox)")
            clarification_visits = supabase.table("customer_visits").select("*, customers(name, mobile), transactions(*)").eq("branch_id", st.session_state.branch_id).eq("status", "Needs_Clarification").execute().data or []
            if not clarification_visits:
                st.info("✅ எந்த விளக்கங்களும் நிலுவையில் இல்லை.")
            else:
                for c_item in clarification_visits:
                    c_cust = c_item.get("customers", {})
                    with st.expander(f"🚨 {c_item['visit_no']} | {c_cust.get('name')} | ₹{c_item['net_cash_amount']:,.2f}"):
                        st.error(f"குறிப்பு: {c_item.get('verification_remarks', '-')}")
                        b_rep = st.text_area("கிளையின் பதில் விளக்கம்:", key=f"rep_{c_item['id']}")
                        if st.button("பதிலை அனுப்பு", key=f"send_rep_{c_item['id']}", type="primary"):
                            supabase.table("customer_visits").update({"status": "Submitted_to_Auditor", "verification_remarks": b_rep}).eq("id", c_item["id"]).execute()
                            st.success("அனுப்பப்பட்டது!")
                            st.rerun()

        # -----------------------------------------------------------------
        # branch_tab2: கிளை ஆவணங்கள் பதிவேற்றம் (மீண்டும் முழுமையாக இணைக்கப்பட்டது)
        # -----------------------------------------------------------------
        with branch_tab2:
            st.subheader("📁 கிளை ஆவணங்கள் பதிவேற்றம் (Upload Docs Desk)")
            st.caption("OTP முடிந்து, ஆப்பரேஷன்ஸ் அழைப்பு உறுதி செய்யப்பட்ட வருகைகளுக்கு இங்கே ஆவணங்களை இணைத்து தணிக்கைக்கு (Auditor) அனுப்பலாம்.")

            branch_pending = (
                supabase.table("customer_visits")
                .select("*, customers(name, mobile), transactions(*)")
                .eq("branch_id", st.session_state.branch_id)
                .in_("status", ["Pending_Branch_Docs", "Pending_Calling_Verification"])
                .order("id", desc=True)
                .execute()
                .data or []
            )

            if not branch_pending:
                st.info("தற்போது ஆவணங்கள் ஏற்ற வேண்டிய வருகைகள் எதுவும் இல்லை.")
            else:
                for b_item in branch_pending:
                    c_info = b_item.get("customers", {})
                    st_badge = "🟢 ஆப்பரேஷன் சரிபார்க்கப்பட்டது" if b_item["status"] == "Pending_Branch_Docs" else "🟡 அழைப்பு சரிபார்ப்பில் உள்ளது"
                    with st.expander(f"📄 வருகை: {b_item['visit_no']} | வாடிக்கையாளர்: {c_info.get('name')} | தொகை: ₹{b_item['net_cash_amount']:,.2f} | முறை: {b_item.get('payment_mode', 'Cash')} | {st_badge}"):
                        st.write(f"📞 **மொபைல்:** {c_info.get('mobile')} | **தேதி:** {b_item['created_at']}")
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
                visit_type = st.radio("வாடிக்கையாளர் வகை:", ["ஏற்கனவே உள்ள வாடிக்கையாளர் (Existing Customer)", "புதிய வாடிக்கையாளர் பதிவு (New Customer)"], horizontal=True)

                if "Existing" in visit_type:
                    st.markdown("##### 🔍 வாடிக்கையாளர் தேடல்")
                    search_query = st.text_input("பெயர் / மொபைல் எண் / Customer ID:", placeholder="எ.கா: ராம் அல்லது 98765...", key="live_cust_search")

                    if len(search_query.strip()) >= 2:
                        q = search_query.strip()
                        cust_filter_query = (
                            supabase.table("customers")
                            .select("*")
                            .eq("is_active", True)
                            .neq("kyc_status", "Rejected")
                            .neq("kyc_status", "Pending_KYC_Approval")
                        )

                        if st.session_state.user_role not in ["Admin", "Auditor", "Operations"]:
                            cust_filter_query = cust_filter_query.eq("branch_id", st.session_state.branch_id)

                        matched_custs = cust_filter_query.or_(f"name.ilike.%{q}%,mobile.ilike.%{q}%,customer_code.ilike.%{q}%").limit(20).execute().data or []

                        if matched_custs:
                            cust_dropdown_dict = {f"{c['name']} | {c.get('customer_code', '')} | 📞 {c.get('mobile', '')}": c for c in matched_custs}
                            selected_label = st.selectbox("வாடிக்கையாளர் பட்டியல்:", options=list(cust_dropdown_dict.keys()), key="dd_cust_sel")
                            selected_cust = cust_dropdown_dict[selected_label]

                            with st.container(border=True):
                                c_col1, c_col2, c_col3 = st.columns([1, 2.5, 1])
                                with c_col1:
                                    if selected_cust.get("photo_url"):
                                        st.image(selected_cust["photo_url"], width=120)
                                    else:
                                        st.info("📷 படம் இல்லை")
                                with c_col2:
                                    st.markdown(f"### {selected_cust['name']} <small style='color:gray;'>({selected_cust.get('customer_code', '')})</small>", unsafe_allow_html=True)
                                    st.write(f"📞 **முதன்மை:** {selected_cust.get('mobile', '-')} | **கூடுதல்:** {selected_cust.get('mobile2', '-')}")
                                    st.write(f"👨‍👦 **கார்டியன்:** {selected_cust.get('guardian_name', '-')} | 🏠 **முகவரி:** {selected_cust.get('address', '-')}")
                                with c_col3:
                                    if st.button("வருகையைத் தொடங்கு ➔", key=f"start_v_{selected_cust['id']}", type="primary", use_container_width=True):
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
                            st.warning("பொருந்தும் அல்லது அங்கீகரிக்கப்பட்ட வாடிக்கையாளர் விவரங்கள் இல்லை.")

                else:
                    st.markdown("##### 📝 புதிய வாடிக்கையாளர் பதிவுப் படிவம் (New KYC Registration)")
                    with st.form("new_customer_form", clear_on_submit=True):
                        col_n1, col_n2, col_n3 = st.columns(3)
                        with col_n1:
                            new_name = st.text_input("வாடிக்கையாளர் பெயர் *")
                            new_guardian = st.text_input("கார்டியன் / தந்தை / கணவர் பெயர்")
                            new_dob = st.date_input("பிறந்த தேதி", min_value=datetime(1940, 1, 1), max_value=datetime.today())
                            new_gender = st.selectbox("பாலினம்", ["ஆண் (Male)", "பெண் (Female)", "மற்றவை (Other)"])
                            new_photo = st.file_uploader("1. வாடிக்கையாளர் புகைப்படம் (Customer Photo) *", type=["jpg", "jpeg", "png"])

                        with col_n2:
                            new_mob1 = st.text_input("முதன்மை மொபைல் எண் *")
                            new_mob2 = st.text_input("கூடுதல் மொபைல் எண்")
                            new_id_no = st.text_input("அடையாள எண் (ID Card Number) *")
                            new_id_doc = st.file_uploader("2. அடையாள அட்டை ஆவணம் (ID Proof Image/PDF) *", type=["jpg", "jpeg", "png", "pdf"])

                        with col_n3:
                            new_address = st.text_area("முழு முகவரி (Communication Address) *", height=85)
                            new_nominee = st.text_input("நாமினி பெயர்")
                            new_relation = st.text_input("உறவுமுறை")
                            new_addr_doc = st.file_uploader("3. முகவரி சான்று ஆவணம் (Address Proof Image/PDF) *", type=["jpg", "jpeg", "png", "pdf"])

                        st.caption("ℹ️ குறிப்பு: புதிய வாடிக்கையாளர் பதிவு செய்தவுடன் ஆப்பரேஷன்ஸ் ஒப்புதலுக்குச் செல்லும் (Pending KYC). அவர்கள் ஒப்புதல் அளித்த பிறகே கடன் பரிவர்த்தனை செய்ய முடியும்.")

                        if st.form_submit_button("வாடிக்கையாளரைப் பதிவு செய்து ஒப்புதலுக்கு அனுப்புக (Submit KYC)", type="primary"):
                            if new_name.strip() and new_mob1.strip() and new_address.strip():
                                try:
                                    with st.spinner("ஆவணங்கள் மற்றும் புகைப்படங்கள் பதிவேற்றப்படுகின்றன..."):
                                        photo_url = upload_single_file(new_photo, "customer_photos")
                                        id_doc_url = upload_single_file(new_id_doc, "customer_id_proofs")
                                        addr_doc_url = upload_single_file(new_addr_doc, "customer_address_proofs")

                                        timestamp_code = f"CUST-{datetime.now().strftime('%m%d%H%M%S')}"
                                        supabase.table("customers").insert({
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
                                            "id_proof_url": id_doc_url,
                                            "address_proof_url": addr_doc_url,
                                            "kyc_status": "Pending_KYC_Approval",
                                            "is_active": False,
                                        }).execute()

                                    st.success(f"✅ வாடிக்கையாளர் {new_name} பதிவு செய்யப்பட்டு ஆப்பரேஷன்ஸ் ஒப்புதலுக்கு அனுப்பப்பட்டது!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"பதிவு செய்வதில் பிழை: {e}")
                            else:
                                st.error("பெயர், மொபைல் எண் மற்றும் முகவரி கட்டாயம் தேவை.")

            elif st.session_state.current_visit["step"] == "TRANSACTIONS":
                visit = st.session_state.current_visit
                st.success(f"வாடிக்கையாளர்: **{visit['customer_name']}** (வருகை எண்: **{visit['visit_no']}**)")
                st.subheader("படி 2: வணிக நடவடிக்கைகள் சேர்த்தல்")

                txn_category = st.selectbox(
                    "நடவடிக்கை வகை:",
                    [
                        "Pledge (புதிய நகைக் கடன்)", "GL Release (அடமானம் மீட்டல்)",
                        "Interest Payment (வட்டி வரவு)", "Part Payment (அசல் வரவு)",
                        "Take Over (பிற நிறுவன கடன் மீட்டல்)", "RD Open (புதிய RD)",
                        "RD Due (RD தவணை)", "RD Closure (RD முதிர்வு)",
                        "FD Open (புதிய வைப்பு நிதி)", "FD Interest (FD வட்டி)",
                        "FD Closure (FD முதிர்வு)", "GP (Gold Purchase)", "GS (Gold Sale)"
                    ],
                    key="dyn_txn_sel"
                )

                with st.form("dynamic_txn_form", clear_on_submit=True):
                    col_st1, col_st2 = st.columns(2)
                    with col_st1:
                        staff = st.selectbox("காரணப் பணியாளர்:", current_staff_list)
                    with col_st2:
                        custom_remarks = st.text_input("கூடுதல் குறிப்பு:", placeholder="எ.கா: சிறப்பு தள்ளுபடி")

                    st.markdown("---")
                    paid_amt, received_amt, detail_summary = 0.0, 0.0, []

                    if txn_category == "Pledge (புதிய நகைக் கடன்)":
                        p_col1, p_col2, p_col3 = st.columns(3)
                        with p_col1:
                            new_gl_no = st.text_input("புதிய கடன் எண் (GL No) *")
                            scheme_name = st.selectbox("ஸ்கீம்", ["ஸ்கீம் A (12%)", "ஸ்கீம் B (15%)", "ஸ்கீம் C (18%)"])
                        with p_col2:
                            gross_wt = st.number_input("மொத்த எடை (gms) *", min_value=0.0, step=0.1)
                            net_wt = st.number_input("நிகர எடை (gms) *", min_value=0.0, step=0.1)
                        with p_col3:
                            item_count = st.number_input("நகை எண்ணிக்கை", min_value=1, step=1)
                            paid_amt = st.number_input("கடன் தொகை (Paid ₹) *", min_value=0.0, step=500.0)
                        detail_summary = [f"GL: {new_gl_no}", f"ஸ்கீம்: {scheme_name}", f"எடை: {net_wt}g"]

                    elif txn_category == "GL Release (அடமானம் மீட்டல்)":
                        r_col1, r_col2 = st.columns(2)
                        with r_col1:
                            rel_gl_no = st.text_input("மீட்கப்படும் கடன் எண் *")
                            principal_amt = st.number_input("அசல் தொகை (₹) *", min_value=0.0, step=500.0)
                        with r_col2:
                            interest_amt = st.number_input("வட்டித் தொகை (₹) *", min_value=0.0, step=50.0)
                            other_charges = st.number_input("இதர கட்டணம் (₹)", min_value=0.0, step=10.0)
                        received_amt = principal_amt + interest_amt + other_charges
                        detail_summary = [f"GL: {rel_gl_no}", f"அசல்: ₹{principal_amt}", f"வட்டி: ₹{interest_amt}"]

                    elif txn_category in ["Interest Payment (வட்டி வரவு)", "Part Payment (அசல் வரவு)"]:
                        i_col1, i_col2 = st.columns(2)
                        with i_col1:
                            part_gl_no = st.text_input("கடன் எண் *")
                        with i_col2:
                            received_amt = st.number_input("செலுத்திய தொகை (₹) *", min_value=0.0, step=100.0)
                        detail_summary = [f"GL: {part_gl_no}"]

                    elif txn_category == "Take Over (பிற நிறுவன கடன் மீட்டல்)":
                        to_col1, to_col2 = st.columns(2)
                        with to_col1:
                            bank_source = st.text_input("முந்தைய நிறுவனம் *")
                            prev_loan_no = st.text_input("முந்தைய லோன் எண் *")
                        with to_col2:
                            paid_amt = st.number_input("செலுத்திய தொகை (₹) *", min_value=0.0, step=500.0)
                        detail_summary = [f"வங்கி: {bank_source}", f"கடன் எண்: {prev_loan_no}"]

                    elif "RD" in txn_category or "FD" in txn_category:
                        d_col1, d_col2 = st.columns(2)
                        with d_col1:
                            acc_no = st.text_input("கணக்கு எண் *")
                        with d_col2:
                            if "Closure" in txn_category or "Interest" in txn_category:
                                paid_amt = st.number_input("வழங்கிய தொகை (₹) *", min_value=0.0, step=100.0)
                            else:
                                received_amt = st.number_input("பெற்ற தொகை (₹) *", min_value=0.0, step=100.0)
                        detail_summary = [f"A/c: {acc_no}"]

                    elif txn_category == "GP (Gold Purchase)":
                        paid_amt = st.number_input("வழங்கிய தொகை (₹) *", min_value=0.0, step=500.0)
                    elif txn_category == "GS (Gold Sale)":
                        received_amt = st.number_input("பெற்ற தொகை (₹) *", min_value=0.0, step=500.0)

                    if st.form_submit_button("➕列表中 சேர் (Add to Cart)", type="primary"):
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
                    st.markdown("### 🛒 நடவடிக்கைகள் பட்டியல்:")
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
                        if st.button("பட்டியலை அழி"):
                            st.session_state.transactions_cart = []
                            st.rerun()

            elif st.session_state.current_visit["step"] == "CASH_OTP":
                visit = st.session_state.current_visit
                net_target = visit["net_amount"]
                total_needed_abs = abs(net_target)
                current_drawer = get_current_branch_cash_drawer(st.session_state.branch_id)
                otp_already_sent = "generated_otp" in st.session_state and st.session_state.generated_otp is not None

                st.subheader("படி 3: பணப் பரிமாற்ற முறை & ரூபாய் நோட்டு கணக்கீடு")
                hdr_text = f"💸 வாடிக்கையாளருக்கு வழங்க வேண்டிய தொகை: ₹{net_target:,.2f}" if net_target > 0 else f"💰 வாடிக்கையாளரிடம் பெற வேண்டிய தொகை: ₹{total_needed_abs:,.2f}"
                st.info(f"**{hdr_text}** (வாடிக்கையாளர்: {visit['customer_name']})")

                with st.container(border=True):
                    st.markdown("#### 💳 பணம் செலுத்தும் / பெறும் வழிகள் (Payment Split)")
                    pm_c1, pm_c2, pm_c3 = st.columns(3)
                    with pm_c1:
                        pay_option = st.selectbox("பரிமாற்ற வகை:", ["முழுவதும் ரொக்கம் (100% Cash)", "முழுவதும் வங்கி / UPI (100% Online)", "பகுதி ரொக்கம் + பகுதி வங்கி (Split)"], disabled=otp_already_sent)

                    with pm_c2:
                        if pay_option == "முழுவதும் ரொக்கம் (100% Cash)":
                            cash_portion = total_needed_abs
                            bank_portion = 0.0
                        elif pay_option == "முழுவதும் வங்கி / UPI (100% Online)":
                            cash_portion = 0.0
                            bank_portion = total_needed_abs
                        else:
                            cash_portion = st.number_input("ரொக்கத் தொகை (₹):", min_value=0.0, max_value=float(total_needed_abs), step=500.0, disabled=otp_already_sent)
                            bank_portion = total_needed_abs - cash_portion
                        st.metric("ரொக்கம் (Cash)", f"₹{cash_portion:,.2f}")

                    with pm_c3:
                        st.metric("வங்கி / UPI", f"₹{bank_portion:,.2f}")
                        bank_ref_no = st.text_input("UTR / Ref எண் *:", disabled=otp_already_sent) if bank_portion > 0 else ""

                col_den1, col_den2 = st.columns([1.4, 1])
                with col_den1:
                    st.markdown("#### 💵 நோட்டுகள் கணக்கீடு")
                    in_500, in_200, in_100, in_50, in_20, in_10, in_5, in_coins = 0, 0, 0, 0, 0, 0, 0, 0
                    out_500, out_200, out_100, out_50, out_20, out_10, out_5, out_coins = 0, 0, 0, 0, 0, 0, 0, 0

                    if cash_portion > 0:
                        if net_target < 0:
                            r1_1, r1_2, r1_3, r1_4 = st.columns(4)
                            in_500 = r1_1.number_input("₹500 (IN)", min_value=0, step=1, disabled=otp_already_sent)
                            in_200 = r1_2.number_input("₹200 (IN)", min_value=0, step=1, disabled=otp_already_sent)
                            in_100 = r1_3.number_input("₹100 (IN)", min_value=0, step=1, disabled=otp_already_sent)
                            in_50 = r1_4.number_input("₹50 (IN)", min_value=0, step=1, disabled=otp_already_sent)
                            r2_1, r2_2, r2_3, r2_4 = st.columns(4)
                            in_20 = r2_1.number_input("₹20 (IN)", min_value=0, step=1, disabled=otp_already_sent)
                            in_10 = r2_2.number_input("₹10 (IN)", min_value=0, step=1, disabled=otp_already_sent)
                            in_5 = r2_3.number_input("₹5 (IN)", min_value=0, step=1, disabled=otp_already_sent)
                            in_coins = r2_4.number_input("சில்லறை (IN)", min_value=0, step=1, disabled=otp_already_sent)
                        else:
                            o1_1, o1_2, o1_3, o1_4 = st.columns(4)
                            out_500 = o1_1.number_input(f"₹500 (இருப்பு:{current_drawer['500']})", min_value=0, max_value=current_drawer['500'], step=1, disabled=otp_already_sent)
                            out_200 = o1_2.number_input(f"₹200 (இருப்பு:{current_drawer['200']})", min_value=0, max_value=current_drawer['200'], step=1, disabled=otp_already_sent)
                            out_100 = o1_3.number_input(f"₹100 (இருப்பு:{current_drawer['100']})", min_value=0, max_value=current_drawer['100'], step=1, disabled=otp_already_sent)
                            out_50 = o1_4.number_input(f"₹50 (இருப்பு:{current_drawer['50']})", min_value=0, max_value=current_drawer['50'], step=1, disabled=otp_already_sent)
                            o2_1, o2_2, o2_3, o2_4 = st.columns(4)
                            out_20 = o2_1.number_input(f"₹20 (இருப்பு:{current_drawer['20']})", min_value=0, max_value=current_drawer['20'], step=1, disabled=otp_already_sent)
                            out_10 = o2_2.number_input(f"₹10 (இருப்பு:{current_drawer['10']})", min_value=0, max_value=current_drawer['10'], step=1, disabled=otp_already_sent)
                            out_5 = o2_3.number_input(f"₹5 (இருப்பு:{current_drawer['5']})", min_value=0, max_value=current_drawer['5'], step=1, disabled=otp_already_sent)
                            out_coins = o2_4.number_input(f"சில்லறை (இருப்பு:{current_drawer['coins']})", min_value=0, max_value=int(current_drawer['coins']), step=1, disabled=otp_already_sent)

                    total_cash_in = (in_500 * 500) + (in_200 * 200) + (in_100 * 100) + (in_50 * 50) + (in_20 * 20) + (in_10 * 10) + (in_5 * 5) + in_coins
                    total_cash_out = (out_500 * 500) + (out_200 * 200) + (out_100 * 100) + (out_50 * 50) + (out_20 * 20) + (out_10 * 10) + (out_5 * 5) + out_coins
                    actual_cash = total_cash_in if net_target < 0 else total_cash_out

                    is_cash_tally = (actual_cash == cash_portion)
                    is_ready = is_cash_tally and (bank_portion == 0 or bool(bank_ref_no.strip()))

                    if is_ready:
                        st.success("✅ கணக்கீடு சரியாகப் பொருந்தியது!")
                    else:
                        st.error("❌ நோட்டுகளின் கூட்டுத்தொகை அல்லது UTR விடுபட்டுள்ளது!")

                with col_den2:
                    st.markdown("#### 📲 OTP சரிபார்ப்பு")
                    st.write(f"வாடிக்கையாளர்: **{visit['customer_name']}** | 📞 `{visit['mobile']}`")

                    if not is_ready:
                        st.warning("⚠️ டேலி அமைந்ததும் OTP அனுப்பலாம்.")
                    elif not otp_already_sent:
                        if st.button("📲 OTP அனுப்புக", type="primary"):
                            otp_code = str(random.randint(1000, 9999))
                            st.session_state.generated_otp = otp_code
                            send_fast2sms_otp(visit["mobile"], otp_code)
                            st.rerun()
                    else:
                        st.success("✅ OTP அனுப்பப்பட்டுவிட்டது!")

                    entered_otp = st.text_input("OTP உள்ளிடவும்", max_chars=4)
                    if st.button("✅ வருகையை நிறைவு செய்க", type="primary", use_container_width=True):
                        if is_ready and otp_already_sent and entered_otp == st.session_state.get("generated_otp"):
                            pm_label = "Cash" if bank_portion == 0 else ("Bank/UPI" if cash_portion == 0 else "Split")
                            vres = supabase.table("customer_visits").insert({
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
                                },
                                "otp_verified": True,
                                "status": "Pending_Calling_Verification",
                            }).execute()

                            for txn in st.session_state.transactions_cart:
                                txn["visit_id"] = vres.data[0]["id"]
                                supabase.table("transactions").insert(txn).execute()

                            st.success("வருகை வெற்றிகரமாக நிறைவடைந்தது!")
                            st.session_state.current_visit = None
                            st.session_state.transactions_cart = []
                            st.session_state.generated_otp = None
                            st.rerun()
                        else:
                            st.error("தவறான OTP அல்லது கணக்கீடு முரண்பாடு!")
