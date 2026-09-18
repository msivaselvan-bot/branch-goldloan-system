from datetime import datetime, date
import random
import json
import requests
import pandas as pd
import streamlit as st
from supabase import Client, create_client
import uuid
import os
import pytz

# ==============================================================================
# 1. பக்க வடிவமைப்பு & தலைப்பு
# ==============================================================================
st.set_page_config(page_title="Branch Operations System", layout="wide")

# ==============================================================================
# 2. இந்திய நேர மண்டலம் (IST Helper)
# ==============================================================================
IST = pytz.timezone('Asia/Kolkata')

def get_ist_now():
    """இந்திய நேரப்படி தற்போதைய நேரத்தை வழங்கும்"""
    return datetime.now(IST)

def get_ist_time_str(fmt="%Y-%m-%d %H:%M:%S"):
    """இந்திய நேரத்தை உரை வடிவில் வழங்கும்"""
    return datetime.now(IST).strftime(fmt)

# ==============================================================================
# 3. ஒருங்கிணைக்கப்பட்ட பாதுகாப்பான Supabase இணைப்பு (Secrets & Env)
# ==============================================================================
@st.cache_resource
def init_supabase() -> Client:
    url = None
    key = None
    
    # Secrets-ல் இருந்தால் எடுத்தல்
    try:
        if "supabase" in st.secrets:
            url = st.secrets["supabase"].get("url")
            key = st.secrets["supabase"].get("key")
        elif "SUPABASE_URL" in st.secrets:
            url = st.secrets.get("SUPABASE_URL")
            key = st.secrets.get("SUPABASE_KEY")
    except Exception:
        pass

    # Environment Variables-ல் இருந்தால் எடுத்தல்
    if not url or not key:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        st.error("டேட்டாபேஸ் இணைப்புக் குறியீடுகள் (SUPABASE_URL / SUPABASE_KEY) கிடைக்கவில்லை!")
        st.stop()

    return create_client(url, key)

try:
    supabase: Client = init_supabase()
except Exception as e:
    st.error(f"டேட்டாபேஸ் இணைப்பு பிழை: {e}")
    st.stop()

# ==============================================================================
# 4. ஹை-லுக் ஆப் தீம் (Native App Feel - Lavender, Deep Violet & Luxury Gold)
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

# ==============================================================================
# 5. கோப்புப் பதிவேற்றம் & சேமிப்புச் செயல்பாடுகள்
# ==============================================================================
def upload_ornament_image(file_obj):
    if not file_obj:
        return None
    try:
        bucket_name = "ornaments"
        file_ext = file_obj.name.split(".")[-1]
        file_path = f"ornament_{get_ist_now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}.{file_ext}"
        supabase.storage.from_(bucket_name).upload(
            path=file_path,
            file=file_obj.getvalue(),
            file_options={"content-type": file_obj.type, "upsert": "true"},
        )
        return supabase.storage.from_(bucket_name).get_public_url(file_path)
    except Exception as e:
        st.warning(f"நகை படம் பதிவேற்றுவதில் சிக்கல்: {e}")
        return None

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
    file_path = f"{folder_name}/{get_ist_now().strftime('%Y%m%d%H%M%S')}_{file_obj.name}"
    supabase.storage.from_(bucket_name).upload(
        path=file_path,
        file=file_obj.getvalue(),
        file_options={"content-type": file_obj.type, "upsert": "true"},
    )
    return supabase.storage.from_(bucket_name).get_public_url(file_path)

# ==============================================================================
# 6. ஆவண உருவாக்கம், SMS & எண்கள் ஜெனரேட்டர்
# ==============================================================================
def generate_declaration_html(data):
    try:
        loan_amt_val = float(data.get('loan_amount', 0) or 0)
    except (ValueError, TypeError):
        loan_amt_val = 0.0

    html_content = f"""<!DOCTYPE html>
<html lang="ta">
<head>
    <meta charset="UTF-8">
    <title>கடன் உறுதி ஆவணம் - {data.get('loan_number', '')}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Mukta+Malar:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        @page {{ size: A4 portrait; margin: 20mm; }}
        * {{ box-sizing: border-box; }}
        body {{
            font-family: 'Mukta Malar', sans-serif;
            color: #111;
            padding: 30px;
            max-width: 800px;
            margin: 0 auto;
            line-height: 1.9;
        }}
        .header {{
            text-align: center;
            font-size: 21px;
            font-weight: 700;
            margin-top: 25px;
            margin-bottom: 25px;
            text-decoration: underline;
        }}
        .section-from, .section-to {{
            font-size: 15px;
            line-height: 1.7;
            margin-bottom: 20px;
        }}
        .content {{
            font-size: 16px;
            text-align: justify;
            text-indent: 40px;
            margin-top: 15px;
            margin-bottom: 35px;
        }}
        .footer-table {{
            width: 100%;
            margin-top: 40px;
            font-size: 15px;
            border-collapse: collapse;
        }}
        .footer-table td {{ vertical-align: bottom; }}
        @media print {{
            body {{ padding: 0; }}
            .no-print {{ display: none !important; }}
        }}
    </style>
</head>
<body onload="window.print()">
    <div class="section-from">
        <b>FROM</b><br>
        {data.get('customer_name', '')}<br>
        {data.get('address', '')}<br>
        தொடர்பு எண்: {data.get('contact_number', '')}
    </div>
    <div class="section-to">
        <b>To</b><br>
        ஐயா,<br>
        <b>முத்துசிஸ் கோல்டு புரொடக்ட் பிரைவேட் லிமிடெட்</b><br>
        {data.get('branch_name', '')}
    </div>
    <div class="header">கடன் தொடர்பான உறுதி ஆவணம்</div>
    <div class="content">
        நான் மேற்கூறிய முகவரியில் வசித்து வருகிறேன். நான் தங்களிடம் <b>{data.get('pledge_date', '')}</b> அன்று கடன் எண் <b>{data.get('loan_number', '')}</b> மீது கடனாக <b>₹{loan_amt_val:,.2f}</b> ரூபாய் பெற்றுள்ளேன். எனக்கு பணத்தேவை அதிகமாக உள்ளபடியால் தாங்கள் சாதாரணமாக கொடுக்கும் நகைக்கான கடனைவிட எனது வேண்டுகோளால் அதிகமான பணத்தினை மேலே உள்ள நகைகடனுக்கு பெற்றுள்ளேன். மேலும் மேற்கூறிய கடனுக்கு மாதம் தோறும் வட்டி கட்டுவேன் எனவும் மூன்று மாதத்தில் திருப்பிக்கொள்வேன் எனவும் உறுதியளிக்கிறேன். மீறினால் நிறுவனமே எனது நகைகளை விற்று எனது கடனை நேர் செய்து கொள்ளலாம் எனவும் இதன் மூலம் உறுதியளிக்கிறேன். எனது கடனுக்கு காலம் மூன்று மாதமே என்பதனை நன்கு அறிவேன் மூன்று மாதங்களில் கடன் நேர் செய்யப்படவில்லை எனில் அடகு வைத்த நகை மீது எனக்கு எந்த உரிமையும் இல்லை என்பதனை நன்கு அறிவேன்.
    </div>
    <table class="footer-table">
        <tr>
            <td style="width: 50%;">
                <b>கிளை:</b> {data.get('branch_name', '')}<br>
                <b>தேதி:</b> {data.get('current_date', '')}
            </td>
            <td style="width: 50%; text-align: right;">
                <b>தங்கள் உண்மையுள்ள</b><br><br><br><br>
                ({data.get('customer_name', '')})
            </td>
        </tr>
    </table>
</body>
</html>"""
    return html_content

def generate_short_visit_no() -> str:
    try:
        res = supabase.table("customer_visits").select("visit_no").order("id", desc=True).limit(50).execute()
        existing_numbers = []
        if res.data:
            for row in res.data:
                v_no = str(row.get("visit_no", ""))
                if v_no.startswith("VST-"):
                    parts = v_no.replace("VST-", "").split("-")
                    if parts[0].isdigit():
                        existing_numbers.append(int(parts[0]))
        if existing_numbers:
            next_num = max(existing_numbers) + 1
            return f"VST-{next_num:04d}"
        return "VST-1001"
    except Exception:
        pass
    return f"VST-{get_ist_now().strftime('%y%m%d%H%M%S')}"

def generate_gp_number(branch_code: str) -> str:
    clean_code = branch_code.strip().upper() if branch_code else "BR"
    try:
        res = supabase.table("transactions")\
            .select("gp_number")\
            .ilike("gp_number", f"{clean_code}/GP/%")\
            .order("id", desc=True)\
            .limit(1)\
            .execute()
        
        last_num = 0
        if res.data and res.data[0].get("gp_number"):
            parts = res.data[0]["gp_number"].split("/")
            if len(parts) == 3 and parts[2].isdigit():
                last_num = int(parts[2])
        return f"{clean_code}/GP/{last_num + 1:04d}"
    except Exception:
        return f"{clean_code}/GP/{get_ist_now().strftime('%d%H%M')}"

def send_fast2sms_otp(mobile_no: str, otp_code: str):
    try:
        api_key = os.getenv("FAST2SMS_API_KEY", "")
        if "sms" in st.secrets and "fast2sms_api_key" in st.secrets["sms"]:
            api_key = st.secrets["sms"]["fast2sms_api_key"]
        elif "FAST2SMS_API_KEY" in st.secrets:
            api_key = st.secrets["FAST2SMS_API_KEY"]

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

# ==============================================================================
# 7. அதிவேக கேச்சிங் & டேட்டாபேஸ் செயல்பாடுகள் (Speed Cache)
# ==============================================================================
@st.cache_data(ttl=300)
def get_branch_name_cached(b_id):
    if not b_id:
        return "ஒதுக்கப்படாத கிளை"
    try:
        b_res = supabase.table("branches").select("branch_name").eq("id", b_id).execute()
        if b_res.data:
            return b_res.data[0].get("branch_name", "கிளை")
    except Exception:
        pass
    return "கிளை"

@st.cache_data(ttl=300)
def load_branches_data():
    try:
        res = supabase.table("branches").select("*").order("id").execute()
        return res.data or []
    except Exception:
        return []

@st.cache_data(ttl=300)
def get_active_loan_schemes():
    try:
        res = supabase.table("gold_loan_schemes").select("*").execute()
        if res.data:
            schemes = [
                row.get("scheme_name") or row.get("name") or row.get("scheme_code") or row.get("scheme")
                for row in res.data
                if (row.get("scheme_name") or row.get("name") or row.get("scheme_code") or row.get("scheme"))
            ]
            if schemes:
                return list(dict.fromkeys(schemes))
    except Exception:
        pass
    return ["VVH149", "Standard Gold Loan"]

def get_current_branch_cash_drawer(branch_id):
    empty_stock = {"500": 0, "200": 0, "100": 0, "50": 0, "20": 0, "10": 0, "5": 0, "coins": 0.0}
    if not branch_id:
        return empty_stock

    try:
        clean_b_id = int(branch_id)
        stock = empty_stock.copy()

        box_res = supabase.table("branch_cash_box")\
            .select("opening_denomination, entry_date")\
            .eq("branch_id", clean_b_id)\
            .order("id", desc=True)\
            .limit(1)\
            .execute()
        
        last_op_date = None
        if box_res.data and box_res.data[0].get("opening_denomination"):
            last_op_date = box_res.data[0].get("entry_date")
            op_data = box_res.data[0]["opening_denomination"]
            if isinstance(op_data, str):
                try:
                    op_data = json.loads(op_data)
                except Exception:
                    op_data = {}
            for k in stock:
                val = op_data.get(k, 0)
                stock[k] = float(val or 0) if k == "coins" else int(float(val or 0))

        visits_query = supabase.table("customer_visits")\
            .select("denomination_details, created_at")\
            .eq("branch_id", clean_b_id)\
            .neq("status", "Rejected")
        
        if last_op_date:
            visits_query = visits_query.gte("created_at", f"{last_op_date}T00:00:00")
            
        visits_res = visits_query.execute()
        if visits_res.data:
            for row in visits_res.data:
                d_info = row.get("denomination_details")
                if isinstance(d_info, str):
                    try:
                        d_info = json.loads(d_info)
                    except Exception:
                        d_info = {}
                if isinstance(d_info, dict):
                    in_notes = d_info.get("in", {})
                    out_notes = d_info.get("out", {})
                    for k in stock:
                        val_in = float(in_notes.get(k, 0) or 0) if k == "coins" else int(float(in_notes.get(k, 0) or 0))
                        val_out = float(out_notes.get(k, 0) or 0) if k == "coins" else int(float(out_notes.get(k, 0) or 0))
                        stock[k] += (val_in - val_out)

        fund_query = supabase.table("branch_fund_transfers")\
            .select("transfer_type, denomination_details, payment_mode, status")\
            .eq("branch_id", clean_b_id)\
            .eq("payment_mode", "Cash")\
            .neq("status", "Rejected")
        
        if last_op_date:
            fund_query = fund_query.gte("created_at", f"{last_op_date}T00:00:00")
            
        fund_res = fund_query.execute()
        if fund_res.data:
            for f_row in fund_res.data:
                t_type = f_row.get("transfer_type")
                t_den = f_row.get("denomination_details") or {}
                if isinstance(t_den, str):
                    try:
                        t_den = json.loads(t_den)
                    except Exception:
                        t_den = {}

                notes_dict = t_den.get("out", {}) if "out" in t_den else t_den
                for k in stock:
                    qty = float(notes_dict.get(k, 0) or 0) if k == "coins" else int(float(notes_dict.get(k, 0) or 0))
                    if t_type in ["HO_TO_BRANCH", "HO_DEPOSIT"]:
                        stock[k] += qty
                    elif t_type in ["BRANCH_TO_HO", "HO_TRANSFER"]:
                        stock[k] -= qty

        exp_query = supabase.table("branch_expenses")\
            .select("denomination_details, status")\
            .eq("branch_id", clean_b_id)\
            .neq("status", "Rejected")
        
        if last_op_date:
            exp_query = exp_query.gte("created_at", f"{last_op_date}T00:00:00")
            
        exp_res = exp_query.execute()
        if exp_res.data:
            for e_row in exp_res.data:
                e_den = e_row.get("denomination_details") or {}
                if isinstance(e_den, str):
                    try:
                        e_den = json.loads(e_den)
                    except Exception:
                        e_den = {}
                out_notes = e_den.get("out", {}) if "out" in e_den else e_den
                in_notes = e_den.get("in", {})
                for k in stock:
                    out_val = float(out_notes.get(k, 0) or 0) if k == "coins" else int(float(out_notes.get(k, 0) or 0))
                    in_val = float(in_notes.get(k, 0) or 0) if k == "coins" else int(float(in_notes.get(k, 0) or 0))
                    stock[k] += (in_val - out_val)

        for k in stock:
            stock[k] = max(0.0 if k == "coins" else 0, stock[k])

        return stock
    except Exception:
        return empty_stock

# ==============================================================================
# 8. காரணப் பணியாளர் அறிக்கை (Incentive & Attribution Report)
# ==============================================================================
def render_staff_attribution_report(selected_branch_id=None):
    st.markdown("### 📊 காரணப் பணியாளர் அறிக்கை & ஸ்கீம் வாரியான ஊக்கத்தொகை")

    # படிவத்தில் வைப்பதன் மூலம் தேதிகள் மாற்றும்போது உடனே அனாவசிய ரீபிரெஷ் ஆவதைத் தடுத்தல்
    with st.form("staff_report_filter_form"):
        f_col1, f_col2, f_col3 = st.columns([1.5, 1.5, 2])
        start_date = f_col1.date_input("தொடக்கத் தேதி (From):", value=date.today().replace(day=1))
        end_date = f_col2.date_input("முடிவுத் தேதி (To):", value=date.today())
        filter_btn = f_col3.form_submit_button("அறிக்கையைக் காட்டு (Generate Report)", type="primary")

    if start_date > end_date:
        st.error("தொடக்கத் தேதி முடிவுத் தேதியை விட அதிகமாக இருக்கக்கூடாது!")
        return

    start_dt_str = f"{start_date}T00:00:00"
    end_dt_str = f"{end_date}T23:59:59"

    set_res = supabase.table("incentive_settings").select("*").eq("id", 1).execute().data
    rupees_per_point = float(set_res[0].get("rupees_per_point", 5.0)) if set_res else 5.0
    penalty_per_lakh = float(set_res[0].get("negative_growth_penalty_per_lakh", 15.0)) if set_res else 15.0

    inc_rules = supabase.table("staff_incentive_rules").select("*").eq("is_active", True).execute().data or []
    rule_dict = {(r.get("transaction_type"), r.get("scheme_name", "All")): r for r in inc_rules}

    branch_staff_query = supabase.table("users").select("name, role, branch_id").eq("is_active", True)
    if selected_branch_id:
        branch_staff_query = branch_staff_query.eq("branch_id", selected_branch_id)
    active_users = branch_staff_query.execute().data or []

    branch_staff_dict = {}
    for u in active_users:
        b_id = u.get("branch_id")
        branch_staff_dict.setdefault(b_id, []).append(u)

    query = supabase.table("customer_visits")\
        .select("id, visit_no, branch_id, created_at, payment_mode, cash_amount, bank_amount, branches(branch_name), transactions(*)")\
        .gte("created_at", start_dt_str)\
        .lte("created_at", end_dt_str)

    if selected_branch_id:
        query = query.eq("branch_id", selected_branch_id)

    visits = query.execute().data or []
    detailed_txn_logs = []
    staff_points_map = {}

    def add_staff_points(name, pts):
        staff_points_map[name] = staff_points_map.get(name, 0.0) + pts

    for v in visits:
        b_id = v.get("branch_id")
        b_name = v.get("branches", {}).get("branch_name", "Unknown") if v.get("branches") else "Unknown"
        b_staff_list = branch_staff_dict.get(b_id, [])

        head_staff = next((u["name"] for u in b_staff_list if "Head" in u.get("role", "") or "Cashier" in u.get("role", "")), None)
        other_staff = [u["name"] for u in b_staff_list if u["name"] != head_staff]
        total_staff_count = len(b_staff_list)

        for t in v.get("transactions", []):
            txn_type = t.get("transaction_type", "-")
            raw_staff = t.get("staff_name") or "Walk-in (நேரடி வருகை)"
            paid_val = float(t.get("paid_amount", 0.0) or 0.0)
            rec_val = float(t.get("received_amount", 0.0) or 0.0)
            principal_val = float(t.get("principal_amount", 0.0) or 0.0)
            remarks_str = str(t.get("remarks", ""))

            effective_vol = 0.0
            if "Release" in txn_type or "அடமானம் மீட்டல்" in txn_type or "Part Payment" in txn_type or "அசல் வரவு" in txn_type:
                if principal_val > 0:
                    effective_vol = principal_val
                elif "அசல்: ₹" in remarks_str:
                    try:
                        p_str = remarks_str.split("அசல்: ₹")[1].split("|")[0].strip().replace(",", "")
                        effective_vol = float(p_str)
                    except Exception:
                        effective_vol = rec_val
                else:
                    effective_vol = rec_val
            elif "RD Due" in txn_type or "RD தவணை" in txn_type:
                effective_vol = rec_val
            else:
                effective_vol = paid_val if paid_val > 0 else rec_val

            detected_scheme = "All"
            try:
                if "ஸ்கீம்:" in remarks_str:
                    detected_scheme = remarks_str.split("ஸ்கீம்:")[1].split("|")[0].strip()
                elif "Scheme:" in remarks_str:
                    detected_scheme = remarks_str.split("Scheme:")[1].split("|")[0].strip()
            except Exception:
                detected_scheme = "All"

            rule_info = rule_dict.get((txn_type, detected_scheme)) or rule_dict.get((txn_type, "All")) or {
                "basis_type": "Amount", "unit_value": 100000.0, "points_per_unit": 10.0
            }

            basis = rule_info.get("basis_type", "Amount")
            unit_val = float(rule_info.get("unit_value", 100000.0) or 100000.0)
            pts_per_unit = float(rule_info.get("points_per_unit", 10.0) or 0.0)

            calc_pts = 0.0
            if basis == "Weight_Grams":
                grams_val = float(t.get("net_weight", 0.0) or 0.0)
                if grams_val == 0.0 and "எடை:" in remarks_str:
                    try:
                        part = remarks_str.split("எடை:")[1].split("g")[0].strip()
                        grams_val = float(part)
                    except Exception:
                        grams_val = 0.0
                calc_pts = (grams_val / unit_val) * pts_per_unit if unit_val > 0 else 0.0
                disp_val = f"{grams_val:.3f} g"
            else:
                base_calc = (effective_vol / unit_val) * pts_per_unit if unit_val > 0 else 0.0
                if any(k in txn_type for k in ["Release", "அடமானம் மீட்டல்", "Part Payment", "அசல் வரவு"]):
                    calc_pts = -abs(base_calc)
                else:
                    calc_pts = abs(base_calc)
                disp_val = f"₹{effective_vol:,.2f}"

            assigned_staff_list = []
            if "Walk-in" in raw_staff or not raw_staff or "நேரடி" in raw_staff:
                if total_staff_count == 2 and head_staff and other_staff:
                    assigned_staff_list = [(head_staff, calc_pts * 0.60), (other_staff[0], calc_pts * 0.40)]
                elif total_staff_count == 3 and head_staff and len(other_staff) == 2:
                    assigned_staff_list = [(head_staff, calc_pts * 0.40), (other_staff[0], calc_pts * 0.30), (other_staff[1], calc_pts * 0.30)]
                elif total_staff_count > 3 and head_staff:
                    split_ratio = 0.60 / len(other_staff) if other_staff else 0.0
                    assigned_staff_list = [(head_staff, calc_pts * 0.40)]
                    for s in other_staff:
                        assigned_staff_list.append((s, calc_pts * split_ratio))
                elif head_staff:
                    assigned_staff_list = [(head_staff, calc_pts)]
                else:
                    assigned_staff_list = [("Walk-in", calc_pts)]
            else:
                assigned_staff_list = [(raw_staff, calc_pts)]

            for staff_member, s_pts in assigned_staff_list:
                add_staff_points(staff_member, s_pts)
                detailed_txn_logs.append({
                    "தேதி": str(v.get("created_at", ""))[:10],
                    "வருகை எண்": v.get("visit_no", "-"),
                    "கிளை": b_name,
                    "பணியாளர்": staff_member,
                    "நடவடிக்கை வகை": txn_type,
                    "திட்டம் (Scheme)": detected_scheme,
                    "வணிக அளவு (Effective)": disp_val,
                    "raw_amount": effective_vol,
                    "ஈட்டிய புள்ளிகள்": round(s_pts, 2),
                    "குறிப்பு": remarks_str
                })

    if not detailed_txn_logs:
        st.info("தேர்ந்தெடுக்கப்பட்ட தேதி வரம்பில் பரிவர்த்தனைகள் எதுவும் இல்லை.")
        return

    df_txns = pd.DataFrame(detailed_txn_logs)
    tot_pledge = df_txns[df_txns["நடவடிக்கை வகை"].str.contains("Pledge", na=False)]["raw_amount"].sum()
    tot_release = df_txns[df_txns["நடவடிக்கை வகை"].str.contains("Release", na=False)]["raw_amount"].sum()
    net_gold_growth = tot_pledge - tot_release
    is_negative_growth = net_gold_growth < 0
    penalty_pts = (abs(net_gold_growth) / 100000.0) * penalty_per_lakh if is_negative_growth else 0.0

    staff_filter_options = ["அனைத்து பணியாளர்களும் (All Staff & Walk-in)"] + sorted(list(staff_points_map.keys()))
    selected_staff_filter = st.selectbox("காரணப் பணியாளரை வடிகட்டுக:", staff_filter_options, key=f"staff_flt_{selected_branch_id}")

    df_filtered = df_txns if selected_staff_filter == "அனைத்து பணியாளர்களும் (All Staff & Walk-in)" else df_txns[df_txns["பணியாளர்"] == selected_staff_filter].copy()
    display_df = df_filtered.drop(columns=["raw_amount"]) if "raw_amount" in df_filtered.columns else df_filtered

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("மொத்த நடவடிக்கைகள்", f"{len(df_filtered):,}")
    m2.metric("புதிய நகைக்கடன் (Pledge)", f"₹{tot_pledge:,.2f}")
    m3.metric("அடகு மீட்டல் (Principal)", f"₹{tot_release:,.2f}")

    if is_negative_growth:
        m4.metric("நிகர வளர்ச்சி", f"-₹{abs(net_gold_growth):,.2f}", delta="-நெகட்டிவ் வளர்ச்சி", delta_color="inverse")
        st.error(f"⚠️ **எச்சரிக்கை:** நகைக் கடன் வளர்ச்சி நெகட்டிவாக உள்ளது. மொத்தமாக **-{penalty_pts:,.1f} புள்ளிகள்** கழிக்கப்படும்.")
    else:
        m4.metric("நிகர வளர்ச்சி", f"+₹{net_gold_growth:,.2f}", delta="+பாசிட்டிவ் வளர்ச்சி")

    st.markdown(f"##### 🏆 பணியாளர் வாரியான புள்ளி விவரம் & ஊக்கத்தொகை (1 புள்ளி = ₹{rupees_per_point:.2f})")
    perf_rows = []
    active_staff_count = max(1, len(staff_points_map))

    for s_name, pts in staff_points_map.items():
        deduct_pts = (penalty_pts / active_staff_count) if is_negative_growth else 0.0
        final_pts = pts - deduct_pts
        perf_rows.append({
            "பணியாளர் பெயர்": s_name,
            "ஈட்டிய/குறைந்த நிகரப் புள்ளிகள்": round(final_pts, 2),
            "ஊக்கத்தொகை (Incentive ₹)": f"₹{final_pts * rupees_per_point:,.2f}"
        })

    st.dataframe(pd.DataFrame(perf_rows), use_container_width=True)
    st.markdown("##### 🔍 பரிவர்த்தனை விவரங்கள்")
    st.dataframe(display_df, use_container_width=True)

# ==============================================================================
# 9. அமர்வு மாறிகள் & கடன் வினவல் உகப்பாக்கம் (Optimized State & Queries)
# ==============================================================================
for state_key, default_val in [
    ("logged_in", False), ("user_role", None), ("branch", None),
    ("branch_id", None), ("username", None), ("current_visit", None),
    ("transactions_cart", []), ("current_declaration", None),
    ("declaration_gl_no", None), ("form_reset_counter", 0),
    ("gp_ornament_rows", [{"item": "", "count": 1, "gross_wt": 0.0, "net_wt": 0.0, "purity": "916 KDM"}])
]:
    if state_key not in st.session_state:
        st.session_state[state_key] = default_val

def generate_next_gl_number(branch_id):
    try:
        clean_b_id = int(branch_id)
        res = supabase.table("branch_loan_sequences").select("*").eq("branch_id", clean_b_id).execute()
        if res.data:
            prefix = res.data[0].get("prefix", "GL")
            next_no = int(res.data[0].get("last_number", 0)) + 1
        else:
            prefix = "GL"
            next_no = 1
            supabase.table("branch_loan_sequences").insert({"branch_id": clean_b_id, "prefix": prefix, "last_number": 0}).execute()

        clean_pfx = str(prefix).strip().rstrip("/-")
        return f"{clean_pfx}/{str(next_no).zfill(4)}", next_no
    except Exception:
        return "GL/1001", 1

def get_current_display_gl_number(branch_id):
    try:
        clean_b_id = int(branch_id)
        res = supabase.table("branch_loan_sequences").select("*").eq("branch_id", clean_b_id).execute()
        prefix = "KMK"
        db_last_no = 0
        if res.data:
            prefix = str(res.data[0].get("prefix", "KMK")).strip().rstrip("/-")
            db_last_no = int(res.data[0].get("last_number", 0))

        pledge_count = sum(1 for item in st.session_state.get("transactions_cart", []) if "Pledge" in str(item.get("transaction_type", "")))
        current_seq_no = db_last_no + pledge_count + 1
        return f"{prefix}/{str(current_seq_no).zfill(4)}", current_seq_no
    except Exception:
        return "KMK/1001", 1

def commit_next_gl_number(branch_id, used_number):
    try:
        supabase.table("branch_loan_sequences").upsert({
            "branch_id": int(branch_id), "last_number": int(used_number)
        }).execute()
    except Exception:
        pass

def get_customer_active_loans(customer_mobile="", customer_name="", branch_id=None):
    """முழு அட்டவணைக்கு பதில் குறிப்பிட்ட வாடிக்கையாளரின் தரவை மட்டுமே எடுக்கும் அதிவேக வினவல்"""
    try:
        clean_mob = "".join(filter(str.isdigit, str(customer_mobile)))[-10:] if customer_mobile else ""
        clean_nm = str(customer_name).strip() if customer_name else ""
        
        if not clean_mob and not clean_nm:
            return []

        query = supabase.table("transactions").select("*").ilike("transaction_type", "%Pledge%").neq("status", "Closed")
        if clean_mob:
            query = query.ilike("mobile", f"%{clean_mob}%")
        elif clean_nm:
            query = query.ilike("customer_name", f"%{clean_nm}%")

        res = query.limit(30).execute()
        if not res.data:
            return []

        active_loans = []
        for row in res.data:
            gl_no = row.get("loan_number") or row.get("gp_number") or row.get("gl_no") or ""
            if not gl_no:
                remarks = str(row.get("remarks") or "")
                if "Old GL:" in remarks:
                    gl_no = remarks.split("Old GL:")[-1].split("|")[0].strip()
                elif "GL:" in remarks:
                    gl_no = remarks.split("GL:")[-1].split("|")[0].strip()

            if gl_no:
                active_loans.append({
                    "id": row.get("id"),
                    "gl_no": gl_no,
                    "principal": float(row.get("principal_amount") or row.get("amount") or 0.0),
                    "net_wt": float(row.get("net_weight") or 0.0)
                })

        cart_closed_gls = [c.get("closed_gl_no") for c in st.session_state.get("transactions_cart", []) if c.get("closed_gl_no")]
        return [ln for ln in active_loans if ln["gl_no"] not in cart_closed_gls]
    except Exception:
        return []

# கிளைத் தகவல்கள் தொடக்கம்
branches_data = load_branches_data()
branch_options = {b["branch_name"]: b["id"] for b in branches_data} if branches_data else {}
branch_id_to_name = {b["id"]: b["branch_name"] for b in branches_data} if branches_data else {}

# ==============================================================================
# 5. உள்நுழைவு திரை (Instant Fast Login Screen)
# ==============================================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    col_left, col_center, col_right = st.columns([1.2, 1.4, 1.2])
    with col_center:
        st.markdown("""
        <div class="login-box">
            <h3>🏦 Muthusise Gold Product Data Center </h3>
            <p>பணியாளர் பாதுகாப்பான உள்நுழைவு</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("பயனர் பெயர் (Username)", placeholder="Username")
            password = st.text_input("கடவுச்சொல் (Password)", type="password", placeholder="Password")
            submitted = st.form_submit_button("உள்நுழைக (Login)", use_container_width=True, type="primary")

            if submitted:
                u_clean = username.strip()
                p_clean = password.strip()

                if u_clean and p_clean:
                    try:
                        res = supabase.table("users").select("*").eq("username", u_clean).execute()
                        if res.data:
                            user_info = res.data[0]
                            db_pass = str(user_info.get("password_hash") or "").strip()
                            
                            if db_pass == p_clean:
                                role = user_info.get("role", "Staff")
                                b_id = user_info.get("branch_id")
                                
                                if role in ["Admin", "Auditor", "Operations"]:
                                    b_name = f"Head Office / {role}"
                                else:
                                    b_name = get_branch_name_cached(b_id) if b_id else "ஒதுக்கப்படாத கிளை"

                                # Session-ல் தகவல்களை அமைத்தல்
                                st.session_state.logged_in = True
                                st.session_state.user_role = role
                                st.session_state.branch = b_name
                                st.session_state.branch_id = b_id
                                st.session_state.username = user_info.get("name", u_clean)
                                st.session_state.profile_image = user_info.get("profile_image_url")
                                
                                # ஸ்பின்னர் சிக்கல் இன்றி மின்னல் வேகத்தில் திரையை மாற்றுதல்
                                st.rerun()
                            else:
                                st.error("தவறான கடவுச்சொல்!")
                        else:
                            st.error("தவறான பயனர் பெயர்!")
                    except Exception as e:
                        st.error(f"பிழை: {e}")
                else:
                    st.warning("தயவுசெய்து பயனர் பெயர் மற்றும் கடவுச்சொல்லை உள்ளிடவும்.")

    # பயனர் உள்நுழையாத வரை கீழ் உள்ள எந்தத் தரவுகளும் லோட் ஆகாது
    st.stop()

# ==============================================================================
# 6. முதன்மை திரை
# ==============================================================================
else:
    top_col1, top_col2, top_col3, top_col4 = st.columns([2.5, 2, 1, 1])
    with top_col1:
        st.write(f"🏢 **கிளை:** {st.session_state.branch}")
    with top_col2:
        st.write(f"👤 **பயனர்:** {st.session_state.username} ({st.session_state.user_role})")
    with top_col3:
        if st.button("🔄 Refresh", use_container_width=True, help="பக்கத்தை முழுமையாகப் புதுப்பிக்க"):
            st.rerun()
    with top_col4:
        if st.button("வெளியேறு", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.current_visit = None
            st.session_state.transactions_cart = []
            st.session_state.generated_otp = None
            st.session_state.current_declaration = None
            st.session_state.declaration_gl_no = None
            st.cache_data.clear()
            st.rerun()

    st.markdown("---")

    # ----------------------------------------------------
    # A. நிர்வாக மேலாண்மை திரை (ADMIN PANEL WITH 10 FULL TABS)
    # ----------------------------------------------------
    if st.session_state.user_role == "Admin":
        st.header("⚙️ நிர்வாக மேலாண்மை (Admin Control Panel)")
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs(
            [
                "🏢 கிளைகள்",
                "👥 பணியாளர்கள்",
                "📋 ஸ்கீம்கள் மேலாண்மை (Pledge, FD, RD)",
                "🎯 இன்சென்டிவ் & புள்ளி விதிகள்",
                "📥 மொத்தப் பதிவேற்றம்",
                "🗂️ வாடிக்கையாளர் மேலாண்மை",
                "📊 வருகை & பரிவர்த்தனை திருத்தம்",
                "💰 கிளை துவக்க இருப்பு & கல்லா",
                "🏦 தலைமையக பணப் பரிமாற்றம்",
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
                            st.cache_data.clear()
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
            st.subheader("📋 ஸ்கீம்கள் மேலாண்மை (Pledge, FD & RD Scheme Master)")
            s_tab1, s_tab2, s_tab3 = st.tabs(["🪙 நகைக்கடன் திட்டங்கள் (Pledge)", "📑 FD திட்டங்கள்", "📈 RD திட்டங்கள்"])

            with s_tab1:
                st.markdown("##### 🪙 புதிய நகைக் கடன் திட்டம் உருவாக்குதல்")
                with st.form("admin_gold_scheme_form", clear_on_submit=True):
                    gs_col1, gs_col2, gs_col3 = st.columns(3)
                    with gs_col1:
                        gs_name = st.text_input("Scheme Name *", placeholder="எ.கா: சூப்பர் சேவர் 12%")
                        gs_rpg = st.number_input("Rate Per Gram (RPG ₹) *", min_value=100.0, value=5500.0, step=50.0)
                        gs_min = st.number_input("Min Loan Value (₹)", min_value=0.0, value=1000.0, step=500.0)
                        gs_max = st.number_input("Max Loan Value (₹)", min_value=0.0, value=1000000.0, step=5000.0)
                    with gs_col2:
                        gs_tenor = st.number_input("Scheme Tenor (Months) *", min_value=1, max_value=60, value=12)
                        gs_chg_timing = st.selectbox("Charges Timing", ["Initial", "Closing"])
                        gs_chg_type = st.selectbox("Charges Type", ["Percentage (%)", "Fixed Amount (₹)"])
                        gs_chg_val = st.number_input("Charges Value", min_value=0.0, value=0.0, step=0.1)
                    with gs_col3:
                        gs_auction_chg = st.number_input("Auction Charges (%)", min_value=0.0, value=2.0, step=0.5)
                        gs_penal_chg = st.number_input("Penal Charges (% on total interest after tenor)", min_value=0.0, value=2.0, step=0.5)

                    st.markdown("###### 📊 Interest Slabs (வட்டி ஸ்லாப்கள்):")
                    sl_c1, sl_c2, sl_c3 = st.columns(3)
                    with sl_c1:
                        s1_from = st.number_input("ஸ்லாப் 1 தொடக்க நாள்", value=1, step=1)
                        s1_to = st.number_input("ஸ்லாப் 1 முடிவு நாள்", value=90, step=1)
                        s1_roi = st.number_input("ஸ்லாப் 1 வட்டி (%)", value=12.0, step=0.5)
                    with sl_c2:
                        s2_from = st.number_input("ஸ்லாப் 2 தொடக்க நாள்", value=91, step=1)
                        s2_to = st.number_input("ஸ்லாப் 2 முடிவு நாள்", value=180, step=1)
                        s2_roi = st.number_input("ஸ்லாப் 2 வட்டி (%)", value=15.0, step=0.5)
                    with sl_c3:
                        s3_from = st.number_input("ஸ்லாப் 3 தொடக்க நாள்", value=181, step=1)
                        s3_to = st.number_input("ஸ்லாப் 3 முடிவு நாள்", value=365, step=1)
                        s3_roi = st.number_input("ஸ்லாப் 3 வட்டி (%)", value=18.0, step=0.5)

                    if st.form_submit_button("நகைக்கடன் ஸ்கீமைச் சேமி", type="primary"):
                        if gs_name.strip():
                            try:
                                formatted_slabs = [
                                    {"from_days": int(s1_from), "to_days": int(s1_to), "roi": float(s1_roi)},
                                    {"from_days": int(s2_from), "to_days": int(s2_to), "roi": float(s2_roi)},
                                    {"from_days": int(s3_from), "to_days": int(s3_to), "roi": float(s3_roi)}
                                ]
                                supabase.table("gold_loan_schemes").insert({
                                    "scheme_name": gs_name.strip(), "rate_per_gram": float(gs_rpg),
                                    "interest_slabs": formatted_slabs, "min_loan_amount": float(gs_min),
                                    "max_loan_amount": float(gs_max), "scheme_tenor_months": int(gs_tenor),
                                    "charges_timing": gs_chg_timing, "charges_type": "Percentage" if "Percentage" in gs_chg_type else "Fixed Amount",
                                    "charges_value": float(gs_chg_val), "auction_charges_percent": float(gs_auction_chg),
                                    "penal_charges_percent": float(gs_penal_chg), "is_active": True
                                }).execute()
                                st.cache_data.clear()
                                st.success(f"✅ '{gs_name}' திட்டம் சேமிக்கப்பட்டது!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"பிழை: {e}")

                g_schemes = supabase.table("gold_loan_schemes").select("*").order("id", desc=True).execute().data or []
                if g_schemes:
                    st.dataframe(pd.DataFrame(g_schemes)[["scheme_name", "rate_per_gram", "scheme_tenor_months", "min_loan_amount", "max_loan_amount"]], use_container_width=True)

            with s_tab2:
                st.markdown("##### 📑 புதிய FD திட்டம் உருவாக்குதல்")
                with st.form("admin_fd_scheme_form", clear_on_submit=True):
                    fd_c1, fd_c2, fd_c3 = st.columns(3)
                    with fd_c1:
                        fd_name = st.text_input("Scheme Name *", placeholder="எ.கா: பிக்சட் பிளஸ் 9.5%")
                        fd_tenure = st.number_input("Tenure (Months) *", min_value=1, max_value=120, value=12)
                        fd_lock = st.number_input("Locking Period (Months)", min_value=0, max_value=60, value=3)
                    with fd_c2:
                        fd_min_amt = st.number_input("Minimum Deposit Amount (₹) *", min_value=100.0, value=5000.0, step=1000.0)
                        fd_interest = st.number_input("Annual Interest (%) *", min_value=0.0, value=9.5, step=0.25)
                        fd_int_type = st.selectbox("Interest Type", ["Simple", "Compounding"])
                    with fd_c3:
                        fd_payout = st.selectbox("Interest Payout", ["Monthly", "Quarterly", "Half-Yearly", "Yearly", "At Maturity"])

                    if st.form_submit_button("FD ஸ்கீமைச் சேமி", type="primary"):
                        if fd_name.strip():
                            supabase.table("fd_schemes").insert({
                                "scheme_name": fd_name.strip(), "tenure_months": int(fd_tenure),
                                "locking_period_months": int(fd_lock), "min_deposit_amount": float(fd_min_amt),
                                "annual_interest_percent": float(fd_interest), "interest_type": fd_int_type,
                                "interest_payout": fd_payout, "is_active": True
                            }).execute()
                            st.success("FD திட்டம் சேமிக்கப்பட்டது!")
                            st.rerun()

                fd_schemes = supabase.table("fd_schemes").select("*").order("id", desc=True).execute().data or []
                if fd_schemes:
                    df_fd = pd.DataFrame(fd_schemes)[["scheme_name", "tenure_months", "annual_interest_percent", "min_deposit_amount", "interest_payout", "is_active"]]
                    df_fd.columns = ["திட்டம் பெயர்", "கால அளவு (மாதம்)", "ஆண்டு வட்டி (%)", "குறைந்தபட்ச தொகை (₹)", "வட்டி பட்டுவாடா", "நிலை"]
                    st.dataframe(df_fd, use_container_width=True)

            with s_tab3:
                st.markdown("##### 📈 புதிய RD திட்டம் உருவாக்குதல்")
                with st.form("admin_rd_scheme_form", clear_on_submit=True):
                    rd_c1, rd_c2, rd_c3 = st.columns(3)
                    with rd_c1:
                        rd_name = st.text_input("Scheme Name *", placeholder="எ.கா: மாத சேமிப்பு 10%")
                        rd_tenure = st.number_input("Tenure (Months) *", min_value=1, max_value=120, value=12)
                        rd_lock = st.number_input("Locking Period (Months)", min_value=0, max_value=60, value=3)
                    with rd_c2:
                        rd_min_amt = st.number_input("Minimum Deposit Amount (₹) *", min_value=100.0, value=500.0, step=100.0)
                        rd_interest = st.number_input("Annual Interest (%) *", min_value=0.0, value=10.0, step=0.25)
                        rd_int_type = st.selectbox("Interest Type", ["Simple", "Compounding"])
                    with rd_c3:
                        rd_freq = st.selectbox("Due Frequency", ["Monthly", "Weekly"])
                        rd_grace = st.number_input("Grace Days", min_value=0, max_value=30, value=5)
                        rd_fine = st.number_input("Fine Percentage (%)", min_value=0.0, value=1.5, step=0.25)

                    if st.form_submit_button("RD ஸ்கீமைச் சேமி", type="primary"):
                        if rd_name.strip():
                            supabase.table("rd_schemes").insert({
                                "scheme_name": rd_name.strip(), "tenure_months": int(rd_tenure),
                                "locking_period_months": int(rd_lock), "min_deposit_amount": float(rd_min_amt),
                                "annual_interest_percent": float(rd_interest), "interest_type": rd_int_type,
                                "due_frequency": rd_freq, "grace_days": int(rd_grace), "fine_percentage": float(rd_fine),
                                "is_active": True
                            }).execute()
                            st.success("RD திட்டம் சேமிக்கப்பட்டது!")
                            st.rerun()

                rd_schemes = supabase.table("rd_schemes").select("*").order("id", desc=True).execute().data or []
                if rd_schemes:
                    df_rd = pd.DataFrame(rd_schemes)[["scheme_name", "tenure_months", "annual_interest_percent", "min_deposit_amount", "due_frequency", "is_active"]]
                    df_rd.columns = ["திட்டம் பெயர்", "கால அளவு (மாதம்)", "ஆண்டு வட்டி (%)", "குறைந்தபட்ச தவணை (₹)", "தவணை முறை", "நிலை"]
                    st.dataframe(df_rd, use_container_width=True)

        with tab4:
            st.subheader("🎯 பணியாளர் இன்சென்டிவ் & புள்ளிகள் விதிகள்")
            set_res = supabase.table("incentive_settings").select("*").eq("id", 1).execute().data
            curr_rpp = float(set_res[0].get("rupees_per_point", 5.0)) if set_res else 5.0
            curr_pen = float(set_res[0].get("negative_growth_penalty_per_lakh", 15.0)) if set_res else 15.0

            with st.form("admin_global_incentive_form"):
                st.markdown("##### 🪙 நிலையான புள்ளி பண மதிப்பு (Global Point Value)")
                gp_col1, gp_col2, gp_col3 = st.columns([1.5, 1.5, 1])
                new_rpp = gp_col1.number_input("1 Point = ₹", value=curr_rpp, step=0.5)
                new_pen = gp_col2.number_input("நெகட்டிவ் அபராதப் புள்ளி (₹1 லட்சத்திற்கு):", value=curr_pen, step=1.0)
                if gp_col3.form_submit_button("💾 பொது மதிப்புகளைச் சேமி", type="primary"):
                    try:
                        supabase.table("incentive_settings").upsert({
                            "id": 1, "rupees_per_point": float(new_rpp),
                            "negative_growth_penalty_per_lakh": float(new_pen)
                        }, on_conflict="id").execute()
                        st.success("புள்ளி மதிப்பு புதுப்பிக்கப்பட்டது!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"டேட்டாபேஸ் சேமிப்புப் பிழை: {e}")

            st.markdown("---")
            all_g_sch = [s["scheme_name"] for s in supabase.table("gold_loan_schemes").select("scheme_name").execute().data or []]
            all_fd_sch = [s["scheme_name"] for s in supabase.table("fd_schemes").select("scheme_name").execute().data or []]
            all_rd_sch = [s["scheme_name"] for s in supabase.table("rd_schemes").select("scheme_name").execute().data or []]
            available_schemes = ["All"] + all_g_sch + all_fd_sch + all_rd_sch

            with st.form("admin_custom_incentive_form", clear_on_submit=True):
                st.markdown("##### ⚙️ குறிப்பிட்ட ஸ்கீம் வாரியான புள்ளி விதிகள்")
                ir_c1, ir_c2, ir_c3, ir_c4, ir_c5 = st.columns(5)
                ir_txn_type = ir_c1.selectbox("நடவடிக்கை வகை *:", [
                    "Pledge (புதிய நகைக் கடன்)", "GL Release (அடமானம் மீட்டல்)",
                    "Interest Payment (வட்டி வரவு)", "Part Payment (அசல் வரவு)",
                    "Take Over (பிற நிறுவன கடன் மீட்டல்)", "FD Open (புதிய வைப்பு நிதி)",
                    "RD Open (புதிய RD சேமிப்பு)", "RD Due (RD தவணை வரவு)",
                    "GP (Gold Purchase)", "GS (Gold Sale)"
                ])
                ir_scheme = ir_c2.selectbox("குறிப்பிட்ட ஸ்கீம் *:", available_schemes)
                ir_basis = ir_c3.selectbox("அடிப்படைக் கணக்கீடு *:", ["Amount (தொகை வழி - ₹)", "Weight_Grams (எடை வழி - Grams)"])
                ir_unit = ir_c4.number_input("அலகு மதிப்பு *:", value=100000.0, step=100.0)
                ir_pts = ir_c5.number_input("புள்ளிகள் *:", value=10.0, step=1.0)

                if st.form_submit_button("ஸ்கீம் விதியைச் சேமி", type="primary"):
                    try:
                        clean_basis = "Amount" if "Amount" in ir_basis else "Weight_Grams"
                        payload = {
                            "transaction_type": ir_txn_type, "scheme_name": ir_scheme,
                            "basis_type": clean_basis, "unit_value": float(ir_unit),
                            "points_per_unit": float(ir_pts), "is_active": True
                        }
                        check_existing = supabase.table("staff_incentive_rules").select("id").eq("transaction_type", ir_txn_type).eq("scheme_name", ir_scheme).execute()
                        if check_existing.data:
                            supabase.table("staff_incentive_rules").update(payload).eq("id", check_existing.data[0]["id"]).execute()
                        else:
                            supabase.table("staff_incentive_rules").insert(payload).execute()
                        st.success("✅ விதி சேமிக்கப்பட்டது!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"பிழை: {e}")

            rules_view = supabase.table("staff_incentive_rules").select("*").order("id", desc=True).execute().data or []
            if rules_view:
                for r in rules_view:
                    rc1, rc2, rc3, rc4, rc5 = st.columns([2.5, 2, 1.5, 1.5, 1])
                    rc1.write(f"**{r['transaction_type']}**")
                    rc2.write(f"ஸ்கீம்: `{r.get('scheme_name', 'All')}`")
                    rc3.write(f"யூனிட்: ₹{float(r.get('unit_value', 1)):,.0f}" if r.get("basis_type") == "Amount" else f"யூனிட்: {r.get('unit_value')}g")
                    rc4.write(f"புள்ளிகள்: {r.get('points_per_unit')}")
                    if rc5.button("🗑️ நீக்கு", key=f"del_rule_{r['id']}"):
                        supabase.table("staff_incentive_rules").delete().eq("id", r["id"]).execute()
                        st.rerun()

        with tab5:
            st.subheader("📥 கிளை வாரியான பழைய வாடிக்கையாளர் இறக்குமதி")
            branches_data = load_branches_data()
            branch_dict = {b["branch_name"]: b["id"] for b in branches_data}
            branch_code_map = {b["id"]: b.get("branch_code", "BR") for b in branches_data}
            
            chosen_branch_name = st.selectbox("எந்தக் கிளைக்கான பட்டியல் இது?", list(branch_dict.keys())) if branch_dict else None
            target_branch_id = branch_dict[chosen_branch_name] if chosen_branch_name else None
            target_branch_code = branch_code_map.get(target_branch_id, "BR")

            uploaded_cust_file = st.file_uploader("கோப்பைத் தேர்வு செய்யவும் (Excel/CSV)", type=["xls", "xlsx", "csv"])
            
            if uploaded_cust_file and target_branch_id:
                try:
                    df_raw = pd.read_csv(uploaded_cust_file, header=0) if uploaded_cust_file.name.endswith(".csv") else pd.read_excel(uploaded_cust_file, header=0)
                    st.write(f"மொத்த வரிசைகள்: {len(df_raw)}")
                    
                    if st.button("பதிவேற்றத்தைத் தொடங்கு", type="primary"):
                        cols = list(df_raw.columns)
                        name_col_name = next((c for c in cols if 'name' in str(c).lower() or 'பெயர்' in str(c)), cols[2] if len(cols) > 2 else cols[0])
                        mob_col_name = next((c for c in cols if 'mobile' in str(c).lower() or 'phone' in str(c) or 'மொபைல்' in str(c)), cols[7] if len(cols) > 7 else cols[1])
                        cust_no_col = next((c for c in cols if any(k in str(c).lower() for k in ['cust_no', 'customer_no', 'cust no', 'code', 'id', 'வ.எண்', 'எண்'])), None)
                        
                        progress_bar = st.progress(0)
                        success_count, skipped_count, total_rows = 0, 0, len(df_raw)
                        
                        for idx, row in df_raw.iterrows():
                            name = str(row.get(name_col_name, "")).strip() if pd.notna(row.get(name_col_name)) else ""
                            raw_mob = str(row.get(mob_col_name, "")).strip() if pd.notna(row.get(mob_col_name)) else ""
                            mobile = "".join(filter(str.isdigit, raw_mob))[-10:]
                            
                            sheet_cust_no = str(row.get(cust_no_col)).strip().replace(".0", "") if cust_no_col and pd.notna(row.get(cust_no_col)) else str(idx + 1)
                            tcode = f"{target_branch_code}-{sheet_cust_no}"

                            if name and name.lower() != 'nan' and len(mobile) == 10:
                                existing_code = supabase.table("customers").select("id").eq("customer_code", tcode).execute()
                                if not existing_code.data:
                                    try:
                                        supabase.table("customers").insert({
                                            "branch_id": target_branch_id, "customer_code": tcode,
                                            "name": name, "mobile": mobile, "address": chosen_branch_name,
                                            "kyc_status": "Approved", "is_active": True
                                        }).execute()
                                        success_count += 1
                                    except Exception:
                                        skipped_count += 1
                                else:
                                    skipped_count += 1
                            if total_rows > 0:
                                progress_bar.progress(min((idx + 1) / total_rows, 1.0))
                        
                        st.success(f"✅ {chosen_branch_name} கிளைக்கு வெற்றிகரமாக {success_count} வாடிக்கையாளர்கள் பதிவு செய்யப்பட்டனர்!")
                except Exception as e:
                    st.error(f"இறக்குமதி செய்வதில் பிழை: {e}")

        with tab6:
            st.subheader("👥 வாடிக்கையாளர் மேலாண்மை (Customer Management)")
            b_data = load_branches_data()
            branch_map = {b["id"]: f"{b['branch_name']} ({b.get('branch_code', 'BR')})" for b in b_data}
            
            c_sub1, c_sub2 = st.tabs(["📋 வாடிக்கையாளர் பட்டியல் & தேடல்", "➕ புதிய வாடிக்கையாளர் சேர்க்க"])
            
            with c_sub1:
                col_f1, col_f2 = st.columns([1, 2])
                sel_branch_filter = col_f1.selectbox("கிளை வடிகட்டி:", ["அனைத்துக் கிளைகள் (All Branches)"] + [f"{b['branch_name']} ({b.get('branch_code', 'BR')})" for b in b_data])
                search_query = col_f2.text_input("🔍 தேடுக (பெயர், மொபைல், அல்லது குறியீடு):")
                
                query = supabase.table("customers").select("id, customer_code, name, mobile, address, branch_id, kyc_status, is_active, created_at").order("id", desc=True)
                if sel_branch_filter != "அனைத்துக் கிளைகள் (All Branches)":
                    chosen_b_id = next((b["id"] for b in b_data if f"{b['branch_name']} ({b.get('branch_code', 'BR')})" == sel_branch_filter), None)
                    if chosen_b_id:
                        query = query.eq("branch_id", chosen_b_id)
                
                if search_query.strip():
                    sq = search_query.strip()
                    query = query.or_(f"name.ilike.%{sq}%,mobile.ilike.%{sq}%,customer_code.ilike.%{sq}%")

                cust_records = query.limit(200).execute().data or []
                st.markdown(f"**காட்டப்படும் வாடிக்கையாளர்கள்:** `{len(cust_records)}`")
                
                if cust_records:
                    df_customers = pd.DataFrame([{
                        "ID": c.get("id"), "குறியீடு": c.get("customer_code", "-"), "பெயர்": c.get("name", "-"),
                        "மொபைல்": c.get("mobile", "-"), "கிளை": branch_map.get(c.get("branch_id"), "-"),
                        "முகவரி": c.get("address", "-"), "KYC": c.get("kyc_status", "Approved")
                    } for c in cust_records])
                    st.dataframe(df_customers, use_container_width=True, hide_index=True)
                    
                    st.markdown("##### ✏️ வாடிக்கையாளர் விவரங்களைத் திருத்து")
                    cust_options = {f"{c.get('customer_code', '-')} - {c.get('name')} ({c.get('mobile')})": c for c in cust_records}
                    sel_cust_label = st.selectbox("வாடிக்கையாளரைத் தேர்வு செய்யவும்:", list(cust_options.keys()))
                    
                    if sel_cust_label:
                        selected_cust = cust_options[sel_cust_label]
                        with st.form("edit_customer_form"):
                            e_col1, e_col2, e_col3 = st.columns(3)
                            edit_name = e_col1.text_input("பெயர்", value=selected_cust.get("name", ""))
                            edit_mobile = e_col2.text_input("மொபைல் எண்", value=selected_cust.get("mobile", ""), max_chars=10)
                            edit_code = e_col3.text_input("வாடிக்கையாளர் குறியீடு", value=selected_cust.get("customer_code", ""))
                            
                            e_col4, e_col5 = st.columns([2, 1])
                            edit_address = e_col4.text_input("முகவரி", value=selected_cust.get("address", ""))
                            edit_status = e_col5.selectbox("நிலை (Status)", ["Approved", "Pending", "Rejected"], index=["Approved", "Pending", "Rejected"].index(selected_cust.get("kyc_status", "Approved")) if selected_cust.get("kyc_status") in ["Approved", "Pending", "Rejected"] else 0)
                            
                            if st.form_submit_button("💾 மாற்றங்களைச் சேமி", type="primary"):
                                if edit_name.strip() and len(edit_mobile.strip()) == 10:
                                    supabase.table("customers").update({
                                        "name": edit_name.strip(), "mobile": edit_mobile.strip(),
                                        "customer_code": edit_code.strip(), "address": edit_address.strip(),
                                        "kyc_status": edit_status
                                    }).eq("id", selected_cust["id"]).execute()
                                    st.success("வாடிக்கையாளர் விவரங்கள் புதுப்பிக்கப்பட்டன!")
                                    st.rerun()

            with c_sub2:
                st.markdown("##### ➕ புதிய வாடிக்கையாளரை நேரடியாகப் பதிவு செய்க")
                with st.form("admin_manual_cust_form", clear_on_submit=True):
                    nc_col1, nc_col2 = st.columns(2)
                    target_b = nc_col1.selectbox("கிளையைத் தேர்வு செய்யவும்:", [f"{b['branch_name']} ({b.get('branch_code', 'BR')})" for b in b_data])
                    new_cust_name = nc_col1.text_input("வாடிக்கையாளர் பெயர் *")
                    new_cust_mobile = nc_col2.text_input("10 இலக்க மொபைல் எண் *", max_chars=10)
                    new_cust_code_manual = nc_col2.text_input("வாடிக்கையாளர் குறியீடு (விருப்பப்பட்டால்):")
                    new_cust_addr = st.text_area("முகவரி")
                    
                    if st.form_submit_button("வாடிக்கையாளரைச் சேமிக்க", type="primary"):
                        if new_cust_name.strip() and len(new_cust_mobile.strip()) == 10:
                            chosen_b_obj = next((b for b in b_data if f"{b['branch_name']} ({b.get('branch_code', 'BR')})" == target_b), None)
                            b_id = chosen_b_obj["id"] if chosen_b_obj else None
                            b_code = chosen_b_obj.get("branch_code", "BR") if chosen_b_obj else "BR"
                            final_c_code = new_cust_code_manual.strip() if new_cust_code_manual.strip() else f"{b_code}-{get_ist_now().strftime('%m%d%H%M')}"
                            
                            supabase.table("customers").insert({
                                "branch_id": b_id, "customer_code": final_c_code,
                                "name": new_cust_name.strip(), "mobile": new_cust_mobile.strip(),
                                "address": new_cust_addr.strip() if new_cust_addr.strip() else chosen_b_obj.get("branch_name", ""),
                                "kyc_status": "Approved", "is_active": True
                            }).execute()
                            st.success(f"வாடிக்கையாளர் {new_cust_name} சேர்க்கப்பட்டார்!")
                            st.rerun()

        with tab7:
            st.subheader("📋 OTP விலக்குக் கோரிக்கைகள் (Admin Approval Desk)")
            try:
                res = supabase.table("otp_bypass_requests").select("*").eq("status", "Pending Admin").order("id", desc=True).execute()
                pending_admin = res.data or []
            except Exception as e:
                pending_admin = []

            if not pending_admin:
                st.info("✅ தற்போது அட்மின் ஒப்புதலுக்கான OTP விலக்குக் கோரிக்கைகள் எதுவும் இல்லை.")
            else:
                for req in pending_admin:
                    req_b_id = req.get("branch_id")
                    b_lbl = branch_id_to_name.get(req_b_id, f"Branch {req_b_id}")
                    with st.container(border=True):
                        st.markdown(f"📍 **கிளை:** `{b_lbl}` | 👤 **வாடிக்கையாளர்:** `{req.get('customer_name')}` (`{req.get('mobile')}`)")
                        st.write(f"📝 **காரணம்:** {req.get('reason')}")
                        b_col1, b_col2 = st.columns(2)
                        if b_col1.button("✅ ஆப்பரேஷன்ஸுக்கு அனுப்பு", key=f"adm_app_{req['id']}", type="primary"):
                            supabase.table("otp_bypass_requests").update({"status": "Pending Operations", "admin_approved_by": st.session_state.username}).eq("id", req["id"]).execute()
                            st.rerun()
                        if b_col2.button("❌ நிராகரி", key=f"adm_rej_{req['id']}"):
                            supabase.table("otp_bypass_requests").update({"status": "Rejected"}).eq("id", req["id"]).execute()
                            st.rerun()

        # --- Tab 8: துவக்க இருப்பு & பல்க் லோன் (Form-ல் வைக்கப்பட்டு வேகம் கூட்டப்பட்டது) ---
        with tab8:
            st.subheader("💰 கிளை துவக்க இருப்பு நிர்ணயம்")
            sel_op_branch = st.selectbox("கிளையைத் தேர்ந்தெடுக்கவும் *:", list(branch_options.keys()), key="sel_op_b_direct")
            selected_b_id = int(branch_options[sel_op_branch])
            
            cur_db = supabase.table("branch_cash_box").select("*").eq("branch_id", selected_b_id).order("id", desc=True).limit(1).execute()
            raw_den = {}
            if cur_db.data and cur_db.data[0].get("opening_denomination"):
                raw_den = cur_db.data[0]["opening_denomination"]
                if isinstance(raw_den, str):
                    try:
                        raw_den = json.loads(raw_den)
                    except Exception:
                        raw_den = {}

            # ஒவ்வொரு முறை மாற்றும் போதும் ரீபிரெஷ் ஆகாமல் இருக்க FORM பயன்படுத்தப்பட்டுள்ளது
            with st.form("branch_opening_cash_form"):
                c1, c2, c3, c4 = st.columns(4)
                new_500 = c1.number_input("₹500 தாள்கள்", min_value=0, value=int(raw_den.get("500", 0) or 0), step=1)
                new_20 = c1.number_input("₹20 தாள்கள்", min_value=0, value=int(raw_den.get("20", 0) or 0), step=1)
                new_200 = c2.number_input("₹200 தாள்கள்", min_value=0, value=int(raw_den.get("200", 0) or 0), step=1)
                new_10 = c2.number_input("₹10 தாள்கள்", min_value=0, value=int(raw_den.get("10", 0) or 0), step=1)
                new_100 = c3.number_input("₹100 தாள்கள்", min_value=0, value=int(raw_den.get("100", 0) or 0), step=1)
                new_5 = c3.number_input("₹5 தாள்கள்", min_value=0, value=int(raw_den.get("5", 0) or 0), step=1)
                new_50 = c4.number_input("₹50 தாள்கள்", min_value=0, value=int(raw_den.get("50", 0) or 0), step=1)
                new_coins = c4.number_input("நாணயங்கள் (₹)", min_value=0.0, value=float(raw_den.get("coins", 0) or 0.0), step=1.0)
                
                calc_tot = (new_500 * 500) + (new_200 * 200) + (new_100 * 100) + (new_50 * 50) + (new_20 * 20) + (new_10 * 10) + (new_5 * 5) + new_coins
                st.markdown(f"💼 **மொத்த கணக்கீடு:** `₹{calc_tot:,.2f}`")

                if st.form_submit_button("💾 துவக்க இருப்பைச் சேமி", type="primary"):
                    today_str = str(date.today())
                    new_den_payload = {
                        "500": int(new_500), "200": int(new_200), "100": int(new_100), "50": int(new_50),
                        "20": int(new_20), "10": int(new_10), "5": int(new_5), "coins": float(new_coins)
                    }
                    supabase.table("branch_cash_box").delete().eq("branch_id", selected_b_id).execute()
                    supabase.table("branch_cash_box").insert({
                        "branch_id": selected_b_id, "entry_date": today_str,
                        "opening_balance": float(calc_tot), "opening_denomination": new_den_payload
                    }).execute()
                    st.success("✅ துவக்க இருப்பு மாற்றப்பட்டுவிட்டது!")
                    st.rerun()

            st.divider()
            st.subheader("📥 பழைய கடன்கள் பல்க் அப்லோட்")
            with st.form("bulk_loan_prefix_form"):
                col_u1, col_u2 = st.columns(2)
                branch_prefix = col_u1.text_input("கிளை Prefix", value=f"GL-{selected_b_id}")
                starting_gl_num = col_u2.number_input("தற்போதைய கடைசி கடன் எண்", min_value=0, step=1)
                if st.form_submit_button("கடன் வரிசை எண்ணைச் சேமி 💾"):
                    supabase.table("branch_loan_sequences").upsert({
                        "branch_id": selected_b_id, "prefix": branch_prefix.strip(), "last_number": int(starting_gl_num)
                    }).execute()
                    st.success("கடன் வரிசை அமைக்கப்பட்டது!")

            uploaded_file = st.file_uploader("பழைய கடன் விபரங்கள் (CSV/Excel)", type=["csv", "xlsx"])
            if uploaded_file and st.button("பதிவேற்று (Upload Records) 🚀"):
                try:
                    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
                    df.columns = df.columns.str.strip().str.lower()
                    records = []
                    max_gl_num = starting_gl_num
                    for _, row in df.iterrows():
                        raw_mob = str(row.get("mobile", "")).split(".")[0].strip()
                        clean_mob = "".join(filter(str.isdigit, raw_mob))[-10:]
                        records.append({
                            "branch_id": selected_b_id, "transaction_type": "Pledge (Old)",
                            "staff_name": "Admin Migration", "customer_name": str(row.get("customer_name", "")).strip(),
                            "mobile": clean_mob, "amount": float(row.get("principal_amount", 0) or 0.0),
                            "principal_amount": float(row.get("principal_amount", 0) or 0.0),
                            "net_weight": float(row.get("net_weight", 0) or 0.0),
                            "remarks": f"Old GL: {str(row.get('gl_no', '')).strip()}", "status": "Approved"
                        })
                        digits = "".join(filter(str.isdigit, str(row.get("gl_no", ""))))
                        if digits and int(digits) > max_gl_num:
                            max_gl_num = int(digits)
                    if records:
                        supabase.table("transactions").insert(records).execute()
                        supabase.table("branch_loan_sequences").upsert({
                            "branch_id": selected_b_id, "prefix": branch_prefix.strip(), "last_number": int(max_gl_num)
                        }).execute()
                        st.success(f"✅ {len(records)} பதிவுகள் ஏற்றப்பட்டன!")
                except Exception as e:
                    st.error(f"பிழை: {e}")

        with tab9:
            st.subheader("🏦 தலைமையக பணப் பரிமாற்றம் (HO ⇄ Branch)")
            with st.form("adm_fund_form"):
                ft_b = st.selectbox("கிளை:", list(branch_options.keys()))
                ft_type = st.selectbox("வகை:", ["HO_TO_BRANCH", "BRANCH_TO_HO"])
                ft_amt = st.number_input("தொகை (₹):", min_value=0.0, step=1000.0)
                if st.form_submit_button("பரிமாற்றத்தைச் சேமி"):
                    supabase.table("branch_fund_transfers").insert({
                        "branch_id": branch_options[ft_b], "transfer_date": str(date.today()),
                        "transfer_type": ft_type, "amount": ft_amt, "payment_mode": "Cash",
                        "created_by": st.session_state.username, "status": "Approved"
                    }).execute()
                    st.success("பதிவு செய்யப்பட்டது!")
                    st.rerun()

        with tab10:
            rep_b_opts = ["அனைத்து கிளைகளும் (All Branches)"] + list(branch_options.keys())
            sel_rep_b = st.selectbox("கிளையை வடிகட்டவும்:", rep_b_opts, key="adm_rep_branch_sel")
            filter_b_id = branch_options.get(sel_rep_b) if sel_rep_b != "அனைத்து கிளைகளும் (All Branches)" else None
            render_staff_attribution_report(selected_branch_id=filter_b_id)

    # ----------------------------------------------------
    # B. ஆப்பரேஷன்ஸ் திரை (OPERATIONS DESK)
    # ----------------------------------------------------
    elif st.session_state.user_role == "Operations":
        st.header("📞 ஆப்பரேஷன்ஸ் மேசை (Operations Desk)")
        ops_tab1, ops_tab2, ops_tab3, ops_tab4, ops_tab5 = st.tabs([
            "🏦 நிதிப் பரிமாற்ற ஒப்புதல்", "👤 புதிய வாடிக்கையாளர் KYC",
            "📝 விவரத் திருத்தக் கோரிக்கைகள்", "🔔 பரிவர்த்தனை அழைப்பு சரிபார்ப்பு",
            "🛡️ OTP விலக்கு அனுமதி"
        ])

        with ops_tab1:
            st.subheader("🏦 தலைமையக & கிளை நிதிப் பரிமாற்ற ஒப்புதல் மேசை")
            pending_fund_transfers = supabase.table("branch_fund_transfers").select("*, branches(branch_name)").eq("status", "Pending_Approval").order("id", desc=True).execute().data or []
            if not pending_fund_transfers:
                st.info("✅ எந்த பணப் பரிமாற்றங்களும் நிலுவையில் இல்லை.")
            else:
                for f_item in pending_fund_transfers:
                    b_name = f_item.get("branches", {}).get("branch_name", "Branch")
                    with st.expander(f"💰 {f_item['transfer_type']} | {b_name} | ₹{float(f_item['amount']):,.2f}"):
                        st.json(f_item.get("denomination_details", {}))
                        if st.button("✅ அங்கீகரி", key=f"app_f_{f_item['id']}", type="primary"):
                            supabase.table("branch_fund_transfers").update({"status": "Approved", "approved_by": st.session_state.username}).eq("id", f_item["id"]).execute()
                            st.rerun()

            st.markdown("---")
            st.subheader("💸 கிளைச் செலவு ஒப்புதல் மேசை")
            pending_expenses = supabase.table("branch_expenses").select("*, branches(branch_name)").eq("status", "Pending_Approval").order("id", desc=True).execute().data or []
            if not pending_expenses:
                st.info("✅ ஒப்புதலுக்கு நிலுவையில் உள்ள கிளைச் செலவுகள் எதுவும் இல்லை.")
            else:
                for ex in pending_expenses:
                    b_name = ex.get("branches", {}).get("branch_name", "Branch")
                    with st.expander(f"📌 செலவு: {ex['expense_head']} | கிளை: {b_name} | தொகை: ₹{float(ex['amount']):,.2f}"):
                        st.write(f"• **விளக்கம்:** {ex.get('description', '-')}")
                        st.json(ex.get("denomination_details", {}))
                        col_ex1, col_ex2 = st.columns(2)
                        if col_ex1.button("✅ அங்கீகரி", key=f"app_ex_{ex['id']}", type="primary"):
                            supabase.table("branch_expenses").update({"status": "Approved", "approved_by": st.session_state.username}).eq("id", ex["id"]).execute()
                            st.rerun()
                        if col_ex2.button("❌ நிராகரி", key=f"rej_ex_{ex['id']}"):
                            supabase.table("branch_expenses").update({"status": "Rejected", "approved_by": st.session_state.username}).eq("id", ex["id"]).execute()
                            st.rerun()

        with ops_tab2:
            st.subheader("👤 புதிய வாடிக்கையாளர் KYC ஒப்புதல்")
            pending_kyc = supabase.table("customers").select("*").eq("kyc_status", "Pending_KYC_Approval").execute().data or []
            if not pending_kyc:
                st.info("✅ எந்த KYC-யும் நிலுவையில் இல்லை.")
            else:
                for pc in pending_kyc:
                    with st.expander(f"🆕 {pc['customer_code']} | {pc['name']}"):
                        k_c1, k_c2, k_c3 = st.columns([1.5, 1, 1])
                        k_c1.write(f"👤 பெயர்: {pc['name']} | 📞 {pc['mobile']}")
                        if pc.get("photo_url"):
                            k_c2.image(pc["photo_url"], width=130)
                        if pc.get("id_proof_url"):
                            k_c3.markdown(f"🪪 [அடையாள ஆவணம்]({pc['id_proof_url']})")
                        if st.button("✅ அங்கீகரி", key=f"app_k_{pc['id']}", type="primary"):
                            supabase.table("customers").update({"kyc_status": "Approved", "is_active": True}).eq("id", pc["id"]).execute()
                            st.rerun()

        with ops_tab3:
            st.subheader("📝 விவரத் திருத்தக் கோரிக்கைகள்")
            pending_reqs = supabase.table("customer_update_requests").select("*, customers(*), branches(branch_name)").eq("status", "Pending_Approval").order("id", desc=True).execute().data or []
            if not pending_reqs:
                st.info("✅ எந்த கோரிக்கைகளும் இல்லை.")
            else:
                for u_req in pending_reqs:
                    target_c = u_req.get("customers", {}) or {}
                    b_name = u_req.get("branches", {}).get("branch_name", "Branch")
                    new_d = u_req.get("updated_data", {}) or {}
                    with st.expander(f"📌 {target_c.get('name')} | கிளை: {b_name}"):
                        comp_col1, comp_col2 = st.columns(2)
                        comp_col1.markdown(f"**பழைய:** {target_c.get('name')} | {target_c.get('mobile')}")
                        comp_col2.markdown(f"**புதிய:** {new_d.get('name')} | {new_d.get('mobile')}")
                        if st.button("✅ ஏற்றுக்கொள் & புதுப்பி", key=f"app_u_{u_req['id']}", type="primary"):
                            supabase.table("customers").update(new_d).eq("id", target_c["id"]).execute()
                            supabase.table("customer_update_requests").update({"status": "Approved", "reviewed_by": st.session_state.username}).eq("id", u_req["id"]).execute()
                            st.rerun()

        with ops_tab4:
            st.subheader("📞 பரிவர்த்தனை அழைப்பு சரிபார்ப்பு (Transaction Call Verification)")
            st.caption("கிளை ஊழியர்களால் முடிக்கப்பட்டு, வாடிக்கையாளர் அழைப்புச் சரிபார்ப்புக்காக நிலுவையில் உள்ள வருகைகள்.")
            
            ops_visits = (
                supabase.table("customer_visits")
                .select("*, customers(name, mobile, mobile2), transactions(*), branches(branch_name)")
                .eq("status", "Pending_Calling_Verification")
                .order("id", desc=True)
                .execute()
                .data or []
            )

            if not ops_visits:
                st.info("✅ சரிபார்க்க வேண்டிய வருகைகள் எதுவும் நிலுவையில் இல்லை.")
            else:
                for item in ops_visits:
                    cust = item.get("customers", {}) or {}
                    b_name = item.get("branches", {}).get("branch_name", "கிளை")
                    txns = item.get("transactions", []) or []

                    with st.expander(f"🔔 வருகை: {item['visit_no']} | {cust.get('name', '-')} | கிளை: {b_name} | நிகரத் தொகை: ₹{float(item.get('net_cash_amount', 0)):,.2f}"):
                        col_o1, col_o2 = st.columns(2)
                        with col_o1:
                            st.markdown("##### 👤 வாடிக்கையாளர் விவரங்கள்:")
                            st.write(f"• **பெயர்:** {cust.get('name', '-')}")
                            st.write(f"• **முதன்மை மொபைல்:** `{cust.get('mobile', '-')}`")
                            st.write(f"• **கூடுதல் மொபைல்:** `{cust.get('mobile2', '-')}`")
                        with col_o2:
                            st.markdown("##### 💳 பரிவர்த்தனை விவரம்:")
                            st.write(f"• **முறை:** {item.get('payment_mode', 'Cash')}")
                            if item.get('bank_reference_no'):
                                st.write(f"• **UTR / Ref:** `{item.get('bank_reference_no')}`")
                            st.write(f"• **OTP நிலை:** {'🟢 Verified' if item.get('otp_verified') else '🔴 Pending'}")

                        st.markdown("---")
                        if txns:
                            for idx, t in enumerate(txns, 1):
                                st.markdown(f"**{idx}. {t.get('transaction_type', '-')}** | பணியாளர்: `{t.get('staff_name', '-')}`")
                                st.write(f"   • பட்டுவாடா: ₹{float(t.get('paid_amount', 0)):,.2f} | வரவு: ₹{float(t.get('received_amount', 0)):,.2f}")
                                st.write(f"   • குறிப்பு: {t.get('remarks', '-')}")

                        st.markdown("---")
                        
                        # ஆப்பரேஷன்ஸ் முடிவுக்கான Form (டைப் செய்யும்போது ரீபிரெஷ் ஆகாமல் இருக்க)
                        with st.form(f"ops_call_form_{item['id']}"):
                            ops_call_remark = st.text_input(
                                "அழைப்பு சரிபார்ப்பு குறிப்பு / விளக்கம்:",
                                placeholder="எ.கா: வாடிக்கையாளர் போனை எடுக்கவில்லை / தொகையில் முரண்பாடு உள்ளது...",
                                key=f"ops_call_rem_{item['id']}"
                            )
                            o_btn1, o_btn2 = st.columns(2)
                            app_sub = o_btn1.form_submit_button("✅ தொலைபேசி வழி சரிபார்க்கப்பட்டது (Approve)", type="primary", use_container_width=True)
                            clar_sub = o_btn2.form_submit_button("⚠️ கிளை விளக்கம் கேட்க (Need Clarification)", use_container_width=True)

                            if app_sub:
                                supabase.table("customer_visits").update({
                                    "status": "Pending_Branch_Docs",
                                    "verification_remarks": ops_call_remark.strip() if ops_call_remark.strip() else "Call Verified"
                                }).eq("id", item["id"]).execute()
                                st.success(f"✅ வருகை {item['visit_no']} ஆவணப் பதிவேற்றத்திற்கு அனுப்பப்பட்டது!")
                                st.rerun()

                            if clar_sub:
                                if not ops_call_remark.strip():
                                    st.error("⚠️ தயவுசெய்து என்ன விளக்கம் வேண்டும் என்பதைக் குறிப்பில் உள்ளிடவும்!")
                                else:
                                    supabase.table("customer_visits").update({
                                        "status": "Needs_Clarification",
                                        "verification_remarks": f"Operations: {ops_call_remark.strip()}"
                                    }).eq("id", item["id"]).execute()
                                    st.warning("⚠️ விளக்கம் கேட்டு கிளைக்கு அனுப்பப்பட்டது!")
                                    st.rerun()

        with ops_tab5:
            st.subheader("🛡️ OTP விலக்கு இறுதி சரிபார்ப்பு (Operations Clearance)")
            st.caption("அட்மின் ஒப்புதல் வழங்கி, ஆப்பரேஷன்ஸ் குழுவின் இறுதி அனுமதிக்காக நிலுவையில் உள்ள கோரிக்கைகள்.")

            try:
                res = supabase.table("otp_bypass_requests").select("*").eq("status", "Pending Operations").order("id", desc=True).execute()
                pending_ops = res.data or []
            except Exception as e:
                pending_ops = []

            if not pending_ops:
                st.info("✅ சரிபார்ப்பிற்கு நிலுவையில் உள்ள OTP விலக்குக் கோரிக்கைகள் எதுவும் இல்லை.")
            else:
                for op_req in pending_ops:
                    op_b_id = op_req.get("branch_id")
                    b_lbl = branch_id_to_name.get(op_b_id, f"Branch {op_b_id}")

                    with st.container(border=True):
                        st.markdown(f"📍 **கிளை:** `{b_lbl}` | 👤 **வாடிக்கையாளர்:** `{op_req.get('customer_name')}` (`{op_req.get('mobile')}`)")
                        st.write(f"📝 **கோரிய மேலாளர்:** {op_req.get('requested_by')} | **காரணம்:** {op_req.get('reason')}")
                        st.write(f"👤 **அட்மின் ஒப்புதல் அளித்தவர்:** `{op_req.get('admin_approved_by')}`")
                        
                        op_c1, op_c2 = st.columns(2)
                        with op_c1:
                            if st.button("🎯 முழு அனுமதி அளி (Authorize Bypass)", key=f"ops_clr_{op_req['id']}", type="primary"):
                                supabase.table("otp_bypass_requests").update({
                                    "status": "Approved",
                                    "ops_cleared_by": st.session_state.username
                                }).eq("id", op_req["id"]).execute()
                                st.success("முழு அனுமதி வழங்கப்பட்டது! கிளை மேலாளர் OTP இன்றியே வருகையை நிறைவு செய்யலாம்.")
                                st.rerun()
                        with op_c2:
                            if st.button("❌ நிராகரி (Reject)", key=f"ops_rej_{op_req['id']}"):
                                supabase.table("otp_bypass_requests").update({"status": "Rejected"}).eq("id", op_req["id"]).execute()
                                st.warning("கோரிக்கை நிராகரிக்கப்பட்டது.")
                                st.rerun()

    # ----------------------------------------------------
    # C. தணிக்கையர் திரை (AUDITOR DESK)
    # ----------------------------------------------------
    elif st.session_state.user_role == "Auditor":
        st.header("🔍 தணிக்கையர் பணிப்பாய்வு (Auditor Verification)")
        pending_visits = (
            supabase.table("customer_visits")
            .select("*, customers(*), transactions(*), audit_records(*)")
            .eq("status", "Submitted_to_Auditor")
            .order("id", desc=True)
            .execute()
            .data or []
        )

        if not pending_visits:
            st.info("✅ தணிக்கைக்கு நிலுவையில் உள்ள வருகைகள் எதுவும் இல்லை.")
        else:
            for item in pending_visits:
                c_data = item.get("customers", {}) or {}
                hist_remarks = item.get("verification_remarks")
                
                with st.expander(f"வருகை எண்: {item['visit_no']} | வாடிக்கையாளர்: {c_data.get('name', '-')} | நிகரத் தொகை: ₹{float(item.get('net_cash_amount', 0)):,.2f}"):
                    if hist_remarks and hist_remarks != "Auditor Approved":
                        st.markdown("##### 📜 முந்தைய விளக்கம் & பதில்களின் வரலாறு (Communication Trail):")
                        st.info(hist_remarks)
                        st.markdown("---")

                    if item.get("transactions"):
                        st.markdown("##### 🛒 பரிவர்த்தனைகள்:")
                        st.dataframe(pd.DataFrame(item["transactions"]))

                    audit_recs = item.get("audit_records", [])
                    if audit_recs and audit_recs[0].get("document_urls"):
                        st.markdown("##### 📄 இணைக்கப்பட்ட ஆவணங்கள்:")
                        for doc_url in audit_recs[0]["document_urls"]:
                            st.markdown(f"- 🔗 [ஆவணத்தைப் பார்க்க]({doc_url})")

                    st.markdown("---")
                    
                    with st.form(f"aud_form_{item['id']}"):
                        aud_remarks = st.text_area(
                            "புதிய குறிப்பு / கூடுதல் விளக்கம் (தேவைப்பட்டால் மட்டும்):",
                            placeholder="கூடுதல் விளக்கம் கேட்க வேண்டுமெனில் மட்டும் இங்கு எழுதவும்...",
                            key=f"aud_rem_{item['id']}"
                        )
                        btn_c1, btn_c2 = st.columns(2)
                        aud_app_btn = btn_c1.form_submit_button("✅ திருப்திகரமாக உள்ளது - அங்கீகரி (Approve)", type="primary", use_container_width=True)
                        aud_clar_btn = btn_c2.form_submit_button("⚠️ மீண்டும் கூடுதல் விளக்கம் கேட்க", use_container_width=True)

                        if aud_app_btn:
                            now_str = get_ist_time_str("%d-%m-%Y %I:%M %p")
                            final_notes = f"{hist_remarks}\n\n✅ [Auditor Approved at {now_str}]" if hist_remarks else "Auditor Approved"
                            
                            supabase.table("customer_visits").update({
                                "status": "Approved",
                                "verification_remarks": final_notes
                            }).eq("id", item["id"]).execute()
                            supabase.table("audit_records").update({
                                "audit_status": "Approved"
                            }).eq("visit_id", item["id"]).execute()
                            st.success("✅ முழுமையாக அங்கீகரிக்கப்பட்டது!")
                            st.rerun()

                        if aud_clar_btn:
                            if not aud_remarks.strip():
                                st.error("⚠️ தயவுசெய்து என்ன கூடுதல் விளக்கம் வேண்டும் என்பதை உள்ளிடவும்!")
                            else:
                                now_str = get_ist_time_str("%d-%m-%Y %I:%M %p")
                                new_query = f"❓ [Auditor Query ({now_str}) - {st.session_state.username}]:\n{aud_remarks.strip()}"
                                updated_hist = f"{hist_remarks}\n\n{new_query}" if hist_remarks else new_query
                                
                                supabase.table("customer_visits").update({
                                    "status": "Needs_Clarification",
                                    "verification_remarks": updated_hist
                                }).eq("id", item["id"]).execute()
                                supabase.table("audit_records").update({
                                    "audit_status": "Clarification_Requested"
                                }).eq("visit_id", item["id"]).execute()
                                st.warning("⚠️ கூடுதல் விளக்கம் கேட்டு கிளைக்கு அனுப்பப்பட்டது!")
                                st.rerun()

    # ----------------------------------------------------
    # D. கிளை செயல்பாடுகள் திரை (BRANCH FLOW)
    # ----------------------------------------------------
    else:
        branch_tab1, branch_tab2, branch_tab3, branch_tab4, branch_tab5, branch_tab6 = st.tabs([
            "🛒 கவுண்ட்டர் வருகை & OTP", "📁 கிளை ஆவணங்கள் பதிவேற்றம்",
            "⚠️ விளக்கங்கள்", "💼 கிளை கல்லா", "🏦 HO பணப் பரிமாற்றம்", "📈 காரணப் பணியாளர் அறிக்கை"
        ])

        with branch_tab6:
            render_staff_attribution_report(selected_branch_id=st.session_state.branch_id)

        with branch_tab5:
            st.subheader("🏦 தலைமையக பணப் பரிமாற்றம் (Head Office ⇄ Branch Fund Transfer Desk)")
            st.caption("தலைமையகத்திலிருந்து ரொக்கம் பெறுதல் அல்லது தலைமையகத்திற்கு ரொக்கம் அனுப்புதல்.")

            curr_b_drawer = get_current_branch_cash_drawer(st.session_state.branch_id)

            with st.expander("💼 தற்போதைய நேரடி கல்லா கையிருப்பு (Live Approved Stock)", expanded=False):
                bd1, bd2, bd3, bd4 = st.columns(4)
                bd1.metric("₹500 தாள்கள்", f"{curr_b_drawer['500']}")
                bd1.metric("₹20 தாள்கள்", f"{curr_b_drawer['20']}")
                bd2.metric("₹200 தாள்கள்", f"{curr_b_drawer['200']}")
                bd2.metric("₹10 தாள்கள்", f"{curr_b_drawer['10']}")
                bd3.metric("₹100 தாள்கள்", f"{curr_b_drawer['100']}")
                bd3.metric("₹5 தாள்கள்", f"{curr_b_drawer['5']}")
                bd4.metric("₹50 தாள்கள்", f"{curr_b_drawer['50']}")
                bd4.metric("நாணயங்கள் (₹)", f"{curr_b_drawer['coins']:,.2f}")

            with st.form("branch_fund_transfer_flow_form", clear_on_submit=True):
                st.markdown("##### 🔄 புதிய பணப் பரிமாற்றப் பதிவு (Submit for Operations Approval)")
                b_ft_c1, b_ft_c2, b_ft_c3 = st.columns(3)
                b_ft_dir = b_ft_c1.selectbox(
                    "பரிமாற்ற திசை *:",
                    ["HO_TO_BRANCH (தலைமையகத்திலிருந்து கிளைக்கு ரொக்கம் பெறுதல்)", "BRANCH_TO_HO (கிளையிலிருந்து தலைமையகத்திற்கு ரொக்கம் அனுப்புதல்)"],
                    key="b_ft_dir_select"
                )
                b_ft_mode = b_ft_c2.selectbox("அனுப்பும் / பெறும் முறை *:", ["Cash (ரொக்கம்)", "Bank Transfer (வங்கி வரவு)"], key="b_ft_mode_select")
                b_ft_ref = b_ft_c3.text_input("குறிப்பு எண் / UTR No / ரசீது எண் *:", placeholder="எ.கா: HO-PAY-101 / UTR...", key="b_ft_ref_input")

                st.markdown("##### 💵 ரூபாய் நோட்டுகள் விவரம் (Denominations):")
                bf_1, bf_2, bf_3, bf_4 = st.columns(4)
                is_sending_to_ho = "BRANCH_TO_HO" in b_ft_dir

                m_500 = max(0, curr_b_drawer['500']) if is_sending_to_ho else 100000
                b_t_500 = bf_1.number_input(f"₹500 {'(இருப்பு:'+str(curr_b_drawer['500'])+')' if is_sending_to_ho else ''}", min_value=0, max_value=m_500, step=1, key="bt_500")
                m_20 = max(0, curr_b_drawer['20']) if is_sending_to_ho else 100000
                b_t_20 = bf_1.number_input(f"₹20 {'(இருப்பு:'+str(curr_b_drawer['20'])+')' if is_sending_to_ho else ''}", min_value=0, max_value=m_20, step=1, key="bt_20")
                
                m_200 = max(0, curr_b_drawer['200']) if is_sending_to_ho else 100000
                b_t_200 = bf_2.number_input(f"₹200 {'(இருப்பு:'+str(curr_b_drawer['200'])+')' if is_sending_to_ho else ''}", min_value=0, max_value=m_200, step=1, key="bt_200")
                m_10 = max(0, curr_b_drawer['10']) if is_sending_to_ho else 100000
                b_t_10 = bf_2.number_input(f"₹10 {'(இருப்பு:'+str(curr_b_drawer['10'])+')' if is_sending_to_ho else ''}", min_value=0, max_value=m_10, step=1, key="bt_10")
                
                m_100 = max(0, curr_b_drawer['100']) if is_sending_to_ho else 100000
                b_t_100 = bf_3.number_input(f"₹100 {'(இருப்பு:'+str(curr_b_drawer['100'])+')' if is_sending_to_ho else ''}", min_value=0, max_value=m_100, step=1, key="bt_100")
                m_5 = max(0, curr_b_drawer['5']) if is_sending_to_ho else 100000
                b_t_5 = bf_3.number_input(f"₹5 {'(இருப்பு:'+str(curr_b_drawer['5'])+')' if is_sending_to_ho else ''}", min_value=0, max_value=m_5, step=1, key="bt_5")
                
                m_50 = max(0, curr_b_drawer['50']) if is_sending_to_ho else 100000
                b_t_50 = bf_4.number_input(f"₹50 {'(இருப்பு:'+str(curr_b_drawer['50'])+')' if is_sending_to_ho else ''}", min_value=0, max_value=m_50, step=1, key="bt_50")
                m_coins = float(curr_b_drawer['coins']) if is_sending_to_ho else 100000.0
                b_t_coins = bf_4.number_input("நாணயங்கள் (₹)", min_value=0.0, max_value=m_coins, step=1.0, key="bt_coins")

                calc_b_cash = (
                    (b_t_500 * 500) + (b_t_200 * 200) + (b_t_100 * 100) + (b_t_50 * 50) +
                    (b_t_20 * 20) + (b_t_10 * 10) + (b_t_5 * 5) + b_t_coins
                )
                
                if "Cash" in b_ft_mode:
                    b_final_fund_amt = float(calc_b_cash)
                    st.info(f"💵 **நோட்டுகளின் கூட்டுத்தொகை மொத்தத் தொகை: ₹{b_final_fund_amt:,.2f}**")
                else:
                    b_final_fund_amt = st.number_input("வங்கிப் பரிவர்த்தனைத் தொகை (₹) *:", min_value=0.0, step=5000.0, key="b_bank_amt_in")

                if st.form_submit_button("பணப் பரிமாற்றத்தை ஆப்பரேஷன்ஸ் ஒப்புதலுக்கு அனுப்புக", type="primary"):
                    if b_final_fund_amt > 0:
                        pure_dir = "HO_TO_BRANCH" if "HO_TO_BRANCH" in b_ft_dir else "BRANCH_TO_HO"
                        pure_m = "Cash" if "Cash" in b_ft_mode else "Bank Transfer"
                        try:
                            supabase.table("branch_fund_transfers").insert({
                                "branch_id": st.session_state.branch_id,
                                "transfer_date": str(date.today()),
                                "transfer_type": pure_dir,
                                "amount": b_final_fund_amt,
                                "payment_mode": pure_m,
                                "reference_no": b_ft_ref.strip(),
                                "denomination_details": {
                                    "500": b_t_500, "200": b_t_200, "100": b_t_100, "50": b_t_50,
                                    "20": b_t_20, "10": b_t_10, "5": b_t_5, "coins": b_t_coins
                                } if pure_m == "Cash" else {},
                                "created_by": st.session_state.username,
                                "status": "Pending_Approval"
                            }).execute()
                            st.success(f"✅ ₹{b_final_fund_amt:,.2f} பணப் பரிமாற்றம் ஆப்பரேஷன்ஸ் ஒப்புதலுக்கு அனுப்பப்பட்டது!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"பிழை: {e}")
                    else:
                        st.error("நோட்டுகள் அல்லது பரிமாற்றத் தொகையை உள்ளிடவும்.")

            st.markdown("---")
            st.subheader("📋 உங்கள் கிளையின் சமீபத்திய பணப் பரிமாற்றங்கள்")
            b_fund_logs = supabase.table("branch_fund_transfers").select("*").eq("branch_id", st.session_state.branch_id).order("id", desc=True).limit(20).execute().data or []
            if b_fund_logs:
                st.dataframe(pd.DataFrame([{
                    "தேதி": f["transfer_date"],
                    "பரிமாற்றம்": "📥 HO ➔ கிளைக்கு பணம் பெறுதல்" if f["transfer_type"] == "HO_TO_BRANCH" else "📤 கிளை ➔ HO-க்கு அனுப்புதல்",
                    "தொகை (₹)": f"₹{float(f['amount']):,.2f}",
                    "முறை": f["payment_mode"],
                    "நிலை": "🟢 Approved" if f.get("status") == "Approved" else ("🔴 Rejected" if f.get("status") == "Rejected" else "🟡 Pending"),
                    "குறிப்பு": f.get("reference_no", "-"),
                    "பதிவு செய்தவர்": f.get("created_by", "-")
                } for f in b_fund_logs]), use_container_width=True)

        with branch_tab4:
            st.subheader("💸 கிளை செலவுப் பதிவு & சில்லறை மேலாண்மை (Branch Expense Desk)")
            curr_b_drawer = get_current_branch_cash_drawer(st.session_state.branch_id)
            total_drawer_cash = (
                (int(curr_b_drawer.get('500', 0)) * 500) + (int(curr_b_drawer.get('200', 0)) * 200) +
                (int(curr_b_drawer.get('100', 0)) * 100) + (int(curr_b_drawer.get('50', 0)) * 50) +
                (int(curr_b_drawer.get('20', 0)) * 20) + (int(curr_b_drawer.get('10', 0)) * 10) +
                (int(curr_b_drawer.get('5', 0)) * 5) + float(curr_b_drawer.get('coins', 0.0))
            )
            with st.expander(f"💼 தற்போதைய நேரடி கல்லா கையிருப்பு: ₹{total_drawer_cash:,.2f}", expanded=False):
                bd1, bd2, bd3, bd4 = st.columns(4)
                bd1.metric("₹500 தாள்கள்", f"{curr_b_drawer['500']}")
                bd1.metric("₹20 தாள்கள்", f"{curr_b_drawer['20']}")
                bd2.metric("₹200 தாள்கள்", f"{curr_b_drawer['200']}")
                bd2.metric("₹10 தாள்கள்", f"{curr_b_drawer['10']}")
                bd3.metric("₹100 தாள்கள்", f"{curr_b_drawer['100']}")
                bd3.metric("₹5 தாள்கள்", f"{curr_b_drawer['5']}")
                bd4.metric("₹50 தாள்கள்", f"{curr_b_drawer['50']}")
                bd4.metric("நாணயங்கள் (₹)", f"₹{float(curr_b_drawer['coins']):,.2f}")

            with st.form("branch_expense_flow_form", clear_on_submit=True):
                st.markdown("##### 🔄 புதிய செலவுப் பதிவு (Submit for Operations Approval)")
                ex_c1, ex_c2, ex_c3 = st.columns(3)
                exp_head = ex_c1.selectbox("செலவினத் தலைப்பு *:", [
                    "Rent (வாடகை)", "Electricity (மின் கட்டணம்)", "Staff Salary (சம்பளம்)",
                    "Water / Staffwelfar (நீர் & பணியாளர் சார் செலவு)", "Stationery / Printing (ஸ்டேஷனரி)",
                    "Maintenance / Repair (பராமரிப்பு)", "Transport / Courier (போக்குவரத்து)", "Miscellaneous (இதர செலவுகள்)"
                ])
                actual_exp_amount = ex_c2.number_input("உண்மையான செலவுத் தொகை (₹) *:", min_value=1.0, step=10.0)
                exp_ref = ex_c3.text_input("வவுச்சர் / பில் எண் *:", placeholder="எ.கா: VOU-101...")
                exp_desc = st.text_area("செலவுக்கான விளக்கம் / காரணங்கள் *:", placeholder="எ.கா: தேநீர் மற்றும் சிற்றுண்டி வாங்கியது...")

                st.markdown("---")
                col_ex_in, col_ex_out = st.columns(2)

                with col_ex_out:
                    st.markdown("##### 📤 நாம் கொடுத்த நோட்டுகள் (Cash OUT):")
                    o_500 = st.number_input("₹500 கொடுத்தது", min_value=0, max_value=curr_b_drawer['500'], step=1)
                    o_200 = st.number_input("₹200 கொடுத்தது", min_value=0, max_value=curr_b_drawer['200'], step=1)
                    o_100 = st.number_input("₹100 கொடுத்தது", min_value=0, max_value=curr_b_drawer['100'], step=1)
                    o_50  = st.number_input("₹50 கொடுத்தது", min_value=0, max_value=curr_b_drawer['50'], step=1)
                    o_20  = st.number_input("₹20 கொடுத்தது", min_value=0, max_value=curr_b_drawer['20'], step=1)
                    o_10  = st.number_input("₹10 கொடுத்தது", min_value=0, max_value=curr_b_drawer['10'], step=1)
                    o_5   = st.number_input("₹5 கொடுத்தது", min_value=0, max_value=curr_b_drawer['5'], step=1)
                    o_coins = st.number_input("நாணயங்கள் கொடுத்தது (₹)", min_value=0.0, max_value=float(curr_b_drawer['coins']), step=1.0)

                with col_ex_in:
                    st.markdown("##### 📥 கடைக்காரர் திருப்பிக் கொடுத்த மீதி (Cash IN):")
                    i_500 = st.number_input("₹500 மீதி பெற்றது", min_value=0, step=1)
                    i_200 = st.number_input("₹200 மீதி பெற்றது", min_value=0, step=1)
                    i_100 = st.number_input("₹100 மீதி பெற்றது", min_value=0, step=1)
                    i_50  = st.number_input("₹50 மீதி பெற்றது", min_value=0, step=1)
                    i_20  = st.number_input("₹20 மீதி பெற்றது", min_value=0, step=1)
                    i_10  = st.number_input("₹10 மீதி பெற்றது", min_value=0, step=1)
                    i_5   = st.number_input("₹5 மீதி பெற்றது", min_value=0, step=1)
                    i_coins = st.number_input("நாணயங்கள் மீதி பெற்றது (₹)", min_value=0.0, step=1.0)

                if st.form_submit_button("செலவுப் பதிவை ஆப்பரேஷன்ஸ் ஒப்புதலுக்கு அனுப்புக", type="primary"):
                    tot_out = (o_500*500) + (o_200*200) + (o_100*100) + (o_50*50) + (o_20*20) + (o_10*10) + (o_5*5) + o_coins
                    tot_in = (i_500*500) + (i_200*200) + (i_100*100) + (i_50*50) + (i_20*20) + (i_10*10) + (i_5*5) + i_coins
                    net_deducted = tot_out - tot_in

                    if net_deducted == actual_exp_amount and actual_exp_amount > 0 and exp_ref.strip() and exp_desc.strip():
                        try:
                            supabase.table("branch_expenses").insert({
                                "branch_id": st.session_state.branch_id,
                                "expense_date": str(date.today()),
                                "expense_head": exp_head,
                                "amount": float(actual_exp_amount),
                                "voucher_no": exp_ref.strip(),
                                "description": exp_desc.strip(),
                                "denomination_details": {
                                    "out": {"500": o_500, "200": o_200, "100": o_100, "50": o_50, "20": o_20, "10": o_10, "5": o_5, "coins": o_coins},
                                    "in": {"500": i_500, "200": i_200, "100": i_100, "50": i_50, "20": i_20, "10": i_10, "5": i_5, "coins": i_coins},
                                    "net_deducted": net_deducted
                                },
                                "created_by": st.session_state.username,
                                "status": "Pending_Approval"
                            }).execute()
                            st.success(f"✅ ₹{actual_exp_amount:,.2f} செலவுப் பதிவு அனுப்பப்பட்டது!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"பிழை: {e}")
                    else:
                        st.error("⚠️ செலவுத் தொகையும், (கொடுத்த பணம் - மீதிப் பணம்) கணக்கீடும் சரியாகப் பொருந்த வேண்டும்.")

        # =========================================================================
        # 1-வது டேப்: கவுண்ட்டர் வருகை & OTP (Counter Visit & Flow)
        # =========================================================================
        with branch_tab1:
            staff_res = supabase.table("users").select("name").eq("branch_id", st.session_state.branch_id).eq("is_active", True).execute()
            current_staff_list = ["Walk-in (நேரடி வருகை)"] + [s["name"] for s in staff_res.data] if staff_res.data else ["Walk-in (நேரடி வருகை)"]

            # ---------------------------------------------------------------------
            # படி 1: வாடிக்கையாளர் வருகைப் பதிவு (Visit Token)
            # ---------------------------------------------------------------------
            if st.session_state.current_visit is None:
                st.subheader("படி 1: வாடிக்கையாளர் வருகைப் பதிவு (Visit Token)")
                v_type = st.radio(
                    "வாடிக்கையாளர் வகை:",
                    ["ஏற்கனவே உள்ள வாடிக்கையாளர் (Existing Customer)", "புதிய வாடிக்கையாளர் பதிவு (New Customer)"],
                    horizontal=True,
                    key="visit_v_type_radio"
                )

                if "Existing" in v_type:
                    search_query = st.text_input("பெயர் / மொபைல் எண் / Customer ID:", placeholder="எ.கா: ராம் அல்லது 98765...", key="live_cust_search")
                    if len(search_query.strip()) >= 2:
                        q = search_query.strip()
                        cust_filter_query = supabase.table("customers").select("*").eq("is_active", True).neq("kyc_status", "Rejected").neq("kyc_status", "Pending_KYC_Approval")
                        if st.session_state.user_role not in ["Admin", "Auditor", "Operations"]:
                            cust_filter_query = cust_filter_query.eq("branch_id", st.session_state.branch_id)

                        matched_custs = cust_filter_query.or_(f"name.ilike.%{q}%,mobile.ilike.%{q}%,customer_code.ilike.%{q}%").limit(20).execute().data or []
                        if matched_custs:
                            cust_dropdown_dict = {f"{c['name']} | {c.get('customer_code', '')} | 📞 {c.get('mobile', '')}": c for c in matched_custs}
                            selected_label = st.selectbox("வாடிக்கையாளர் பட்டியல்:", options=list(cust_dropdown_dict.keys()), key="dd_cust_sel")
                            selected_cust = cust_dropdown_dict[selected_label]

                            existing_req_check = supabase.table("customer_update_requests").select("id").eq("customer_id", selected_cust["id"]).eq("status", "Pending_Approval").execute().data or []
                            has_pending_update_req = len(existing_req_check) > 0

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
                                    if has_pending_update_req:
                                        st.warning("⏳ **விவரத் திருத்தக் கோரிக்கை ஆப்பரேஷன்ஸ் ஒப்புதலுக்கு நிலுவையில் உள்ளது!**")
                                with c_col3:
                                    if st.button("வருகையைத் தொடங்கு ➔", key=f"start_v_{selected_cust['id']}", type="primary", use_container_width=True):
                                        st.session_state.current_visit = {
                                            "visit_no": generate_short_visit_no(),
                                            "customer_id": selected_cust["id"],
                                            "customer_name": selected_cust["name"],
                                            "customer_code": selected_cust.get("customer_code", ""),
                                            "mobile": selected_cust.get("mobile", ""),
                                            "address": selected_cust.get("address", ""),
                                            "step": "TRANSACTIONS"
                                        }
                                        st.session_state.transactions_cart = []
                                        st.session_state.gp_ornament_rows = [{"item": "", "count": 1, "gross_wt": 0.0, "net_wt": 0.0, "purity": "916 KDM"}]
                                        st.rerun()

                else:
                    st.markdown("##### 📝 புதிய வாடிக்கையாளர் பதிவுப் படிவம் (New KYC Registration)")
                    with st.form("new_customer_form", clear_on_submit=True):
                        col_n1, col_n2, col_n3 = st.columns(3)
                        with col_n1:
                            new_name = st.text_input("வாடிக்கையாளர் பெயர் *")
                            new_guardian = st.text_input("கார்டியன் / தந்தை / கணவர் பெயர்")
                            new_dob = st.date_input("பிறந்த தேதி", min_value=datetime(1940, 1, 1), max_value=datetime.today())
                            new_gender = st.selectbox("பாலினம்", ["ஆண் (Male)", "பெண் (Female)", "மற்றவை (Other)"])
                            new_photo = st.file_uploader("1. வாடிக்கையாளர் புகைப்படம் *", type=["jpg", "jpeg", "png"])
                        with col_n2:
                            new_mob1 = st.text_input("முதன்மை மொபைல் எண் *")
                            new_mob2 = st.text_input("கூடுதல் மொபைல் எண்")
                            new_id_no = st.text_input("அடையாள எண் (ID Card Number) *")
                            new_id_doc = st.file_uploader("2. அடையாள அட்டை ஆவணம் *", type=["jpg", "jpeg", "png", "pdf"])
                        with col_n3:
                            new_address = st.text_area("முழு முகவரி *", height=85)
                            new_nominee = st.text_input("நாமினி பெயர்")
                            new_relation = st.text_input("உறவுமுறை")
                            new_addr_doc = st.file_uploader("3. முகவரி சான்று ஆவணம் *", type=["jpg", "jpeg", "png", "pdf"])

                        if st.form_submit_button("வாடிக்கையாளரைப் பதிவு செய்து ஒப்புதலுக்கு அனுப்புக", type="primary"):
                            if new_name.strip() and new_mob1.strip() and new_address.strip():
                                photo_url = upload_single_file(new_photo, "customer_photos")
                                id_doc_url = upload_single_file(new_id_doc, "customer_id_proofs")
                                addr_doc_url = upload_single_file(new_addr_doc, "customer_address_proofs")

                                tcode = f"CUST-{get_ist_now().strftime('%m%d%H%M%S')}"
                                supabase.table("customers").insert({
                                    "branch_id": st.session_state.branch_id, "customer_code": tcode,
                                    "name": new_name.strip(), "guardian_name": new_guardian.strip(),
                                    "dob": str(new_dob), "gender": new_gender, "mobile": new_mob1.strip(), "mobile2": new_mob2.strip(),
                                    "address": new_address.strip(), "nominee_name": new_nominee.strip(), "nominee_relation": new_relation.strip(),
                                    "photo_url": photo_url, "id_proof_url": id_doc_url, "address_proof_url": addr_doc_url,
                                    "kyc_status": "Pending_KYC_Approval", "is_active": False
                                }).execute()
                                st.success(f"✅ வாடிக்கையாளர் {new_name} பதிவு செய்யப்பட்டு ஒப்புதலுக்கு அனுப்பப்பட்டது!")
                                st.rerun()

            # ---------------------------------------------------------------------
            # படி 2: வணிக நடவடிக்கைகள் சேர்த்தல் (TRANSACTIONS)
            # ---------------------------------------------------------------------
            elif st.session_state.current_visit and st.session_state.current_visit.get("step") == "TRANSACTIONS":
                visit = st.session_state.current_visit
                st.success(f"வாடிக்கையாளர்: **{visit['customer_name']}** (வருகை எண்: **{visit['visit_no']}**)")
                st.subheader("படி 2: வணிக நடவடிக்கைகள் சேர்த்தல்")

                fc = st.session_state.get("form_reset_counter", 0)
                txn_category = st.selectbox(
                    "நடவடிக்கை வகை:",
                    [
                        "Pledge (புதிய நகைக் கடன்)", "GL Release (அடமானம் மீட்டல்)",
                        "Interest Payment (வட்டி வரவு)", "Part Payment (அசல் வரவு)",
                        "Take Over (பிற நிறுவன கடன் மீட்டல்)", "RD Open (புதிய RD சேமிப்பு)",
                        "RD Due (RD தவணை)", "RD Closure (RD முதிர்வு)",
                        "FD Open (புதிய வைப்பு நிதி)", "FD Interest (FD வட்டி)",
                        "FD Closure (FD முதிர்வு)", "GP (Gold Purchase)", "GS (Gold Sale)"
                    ],
                    key="dyn_txn_sel"
                )

                # 🌟 Form உள்ளே அனைத்து உள்ளீடுகளும் கொண்டுவரப்பட்டுள்ளன (தட்டச்சு செய்யும் போது ரீபிரெஷ் ஆகாது!)
                with st.form("add_transaction_to_cart_form"):
                    col_st1, col_st2 = st.columns(2)
                    staff = col_st1.selectbox("காரணப் பணியாளர்:", current_staff_list)
                    custom_remarks = col_st2.text_input("கூடுதல் குறிப்பு:", placeholder="எ.கா: சிறப்பு தள்ளுபடி")

                    st.markdown("---")
                    paid_amt, received_amt = 0.0, 0.0
                    ornament_details, ornament_file = None, None
                    other_charges, total_weight, net_weight = 0.0, 0.0, 0.0
                    principal_amount, interest_amount = 0.0, 0.0
                    nominee_name, nominee_relation, nominee_address = None, None, None
                    new_gl_no, rel_gl_no, part_gl_no = "", "", ""
                    selected_loan_db_id = None
                    detail_summary = []

                    # 1. Pledge
                    if "Pledge" in txn_category:
                        pl_col1, pl_col2, pl_col3 = st.columns(3)
                        suggested_gl, next_seq_num = get_current_display_gl_number(st.session_state.branch_id)
                        new_gl_no = pl_col1.text_input("கடன் எண் (Auto Generated GL No)", value=suggested_gl, disabled=True)
                        db_schemes = get_active_loan_schemes()
                        scheme_name = pl_col1.selectbox("நகைக் கடன் திட்டம் (Scheme) *", db_schemes)

                        total_weight = pl_col2.number_input("மொத்த எடை (Gross Weight - gms) *", min_value=0.0, step=0.001, format="%.3f")
                        net_weight = pl_col2.number_input("நிகர எடை (Net Weight - gms) *", min_value=0.0, step=0.001, format="%.3f")

                        paid_amt = pl_col3.number_input("கடன் தொகை (Paid ₹) *", min_value=0.0, step=500.0)
                        other_charges = pl_col3.number_input("இதர கட்டணங்கள் (Other Charges ₹)", min_value=0.0, step=10.0)

                        ornament_details = st.text_area("நகை விபரம்")
                        ornament_file = st.file_uploader("நகை படம்", type=["jpg", "jpeg", "png"])
                        detail_summary = [f"GL: {new_gl_no}", f"ஸ்கீம்: {scheme_name}", f"எடை: {net_weight}g"]

                    # 2. GL Release
                    elif txn_category == "GL Release (அடமானம் மீட்டல்)":
                        cust_mobile = visit.get("mobile", "")
                        cust_name = visit.get("customer_name", "")
                        active_loans = get_customer_active_loans(cust_mobile, cust_name)
                        loan_display_map = {f"{l['gl_no']} (அசல்: ₹{l['principal']:,.2f}, எடை: {l['net_wt']}g)": l for l in active_loans}

                        if not loan_display_map:
                            st.warning("⚠️ நிலுவையில் உள்ள அடமானக் கடன்கள் எதுவும் இல்லை!")
                        else:
                            selected_loan_label = st.selectbox("அடமானக் கடன் எண்ணைத் தேர்ந்தெடுக்கவும் *", options=list(loan_display_map.keys()))
                            chosen_loan = loan_display_map[selected_loan_label]
                            rel_gl_no = chosen_loan["gl_no"]
                            selected_loan_db_id = chosen_loan["id"]
                            auto_principal = float(chosen_loan["principal"])

                            r_col1, r_col2 = st.columns(2)
                            principal_amount = r_col1.number_input("அசல் தொகை (₹) *", value=auto_principal, min_value=0.0, step=500.0)
                            interest_amount = r_col1.number_input("வட்டித் தொகை (₹) *", min_value=0.0, step=50.0)
                            other_charges = r_col2.number_input("இதர கட்டணம் (₹)", min_value=0.0, step=10.0)
                            received_amt = principal_amount + interest_amount + other_charges
                            detail_summary = [f"GL: {rel_gl_no}", f"அசல்: ₹{principal_amount}", f"வட்டி: ₹{interest_amount}"]

                    # 3. Interest / Part Payment
                    elif txn_category in ["Interest Payment (வட்டி வரவு)", "Part Payment (அசல் வரவு)"]:
                        cust_mobile = visit.get("mobile", "")
                        cust_name = visit.get("customer_name", "")
                        active_loans = get_customer_active_loans(cust_mobile, cust_name)
                        loan_display_map = {f"{l['gl_no']} (அசல்: ₹{l['principal']:,.2f}, எடை: {l['net_wt']}g)": l for l in active_loans}

                        if not loan_display_map:
                            st.warning("⚠️ நிலுவையில் உள்ள அடமானக் கடன்கள் எதுவும் இல்லை!")
                        else:
                            selected_loan_label = st.selectbox("கடன் எண்ணைத் தேர்ந்தெடுக்கவும் *", options=list(loan_display_map.keys()))
                            part_gl_no = loan_display_map[selected_loan_label]["gl_no"]
                            selected_loan_db_id = loan_display_map[selected_loan_label]["id"]

                            i_col1, i_col2 = st.columns(2)
                            principal_amount = i_col1.number_input("அசல் தொகை (₹)", min_value=0.0, step=100.0) if "Part" in txn_category else 0.0
                            interest_amount = i_col2.number_input("வட்டித் தொகை (₹)", min_value=0.0, step=50.0)
                            received_amt = principal_amount + interest_amount
                            detail_summary = [f"GL: {part_gl_no}", f"அசல்: ₹{principal_amount}", f"வட்டி: ₹{interest_amount}"]

                    # 4. Take Over
                    elif txn_category == "Take Over (பிற நிறுவன கடன் மீட்டல்)":
                        to_col1, to_col2 = st.columns(2)
                        bank_source = to_col1.text_input("முந்தைய நிறுவனம் *")
                        prev_loan_no = to_col1.text_input("முந்தைய லோன் எண் *")
                        paid_amt = to_col2.number_input("செலுத்திய தொகை (₹) *", min_value=0.0, step=500.0)
                        detail_summary = [f"வங்கி: {bank_source}", f"கடன் எண்: {prev_loan_no}"]

                    # 5. RD Open / FD Open
                    elif txn_category in ["RD Open (புதிய RD சேமிப்பு)", "FD Open (புதிய வைப்பு நிதி)"]:
                        f_col1, f_col2 = st.columns(2)
                        acc_no = f_col1.text_input("புதிய கணக்கு எண் *")
                        received_amt = f_col2.number_input("வைப்பு / தவணைத் தொகை (₹) *", min_value=0.0, step=500.0)
                        nom_col1, nom_col2 = st.columns(2)
                        nominee_name = nom_col1.text_input("நாமினி பெயர்")
                        nominee_relation = nom_col1.text_input("உறவுமுறை")
                        nominee_address = nom_col2.text_area("நாமினி முகவரி", height=68)
                        detail_summary = [f"A/c: {acc_no}"]

                    # 6. RD/FD முதிர்வு & தவணை
                    elif "RD" in txn_category or "FD" in txn_category:
                        d_col1, d_col2 = st.columns(2)
                        acc_no = d_col1.text_input("கணக்கு எண் *")
                        if "Closure" in txn_category:
                            principal_amount = d_col2.number_input("முதலீடு செய்த தொகை (₹) *", min_value=0.0, step=100.0)
                            interest_amount = d_col2.number_input("வட்டி தொகை (₹) *", min_value=0.0, step=50.0)
                            paid_amt = principal_amount + interest_amount
                        elif "Interest" in txn_category:
                            paid_amt = d_col2.number_input("வழங்கிய தொகை (₹) *", min_value=0.0, step=100.0)
                        else:
                            received_amt = d_col2.number_input("பெற்ற தவணைத் தொகை (₹) *", min_value=0.0, step=100.0)
                        detail_summary = [f"A/c: {acc_no}"]

                    # 7. GS (Gold Sale)
                    elif txn_category == "GS (Gold Sale)":
                        gs_col1, gs_col2, gs_col3 = st.columns(3)
                        gs_bill_no = gs_col1.text_input("விற்பனை பில் எண் *")
                        total_weight = gs_col1.number_input("மொத்த எடை (Gross Wt - g) *", min_value=0.0, step=0.001, format="%.3f")
                        gs_item_name = gs_col2.text_input("பொருள் பெயர்")
                        net_weight = gs_col2.number_input("நிகர எடை (Net Wt - g) *", min_value=0.0, step=0.001, format="%.3f")
                        received_amt = gs_col3.number_input("பெற்ற தொகை (Received ₹) *", min_value=0.0, step=500.0)
                        ornament_details = st.text_area("நகை விபரம்")
                        ornament_file = st.file_uploader("நகை படம்", type=["jpg", "jpeg", "png"])
                        detail_summary = [f"பில்: {gs_bill_no}", f"பொருள்: {gs_item_name}", f"எடை: {net_weight}g"]

                    # கார்ட்டில் சேர்க்கும் சப்மிட் பட்டன்
                    add_cart_submit = st.form_submit_button("➕ பட்டியலில் சேர் (Add to Cart)", type="primary")

                    if add_cart_submit:
                        actual_paid_amt = max(0.0, float(paid_amt) - float(other_charges)) if "Pledge" in txn_category else float(paid_amt)
                        chk_received = float(received_amt)

                        if actual_paid_amt <= 0 and chk_received <= 0:
                            st.warning("⚠️ தயவுசெய்து பட்டுவாடா தொகை அல்லது பெற்ற தொகையை உள்ளிடவும்!")
                        else:
                            all_remarks = " | ".join(detail_summary)
                            if custom_remarks.strip():
                                all_remarks += f" ({custom_remarks.strip()})"

                            img_url = upload_ornament_image(ornament_file) if ornament_file else None
                            final_gl = new_gl_no or rel_gl_no or part_gl_no or ""

                            cart_entry = {
                                "transaction_type": txn_category,
                                "staff_name": staff,
                                "paid_amount": float(actual_paid_amt),
                                "received_amount": float(chk_received),
                                "amount": float(actual_paid_amt if actual_paid_amt > 0 else chk_received),
                                "remarks": all_remarks,
                                "ornament_details": ornament_details or "",
                                "other_charges": float(other_charges),
                                "ornament_image_url": img_url,
                                "total_weight": float(total_weight),
                                "net_weight": float(net_weight),
                                "gp_number": final_gl,
                                "principal_amount": float(principal_amount or paid_amt),
                                "interest_amount": float(interest_amount),
                                "nominee_name": nominee_name or "",
                                "nominee_relation": nominee_relation or "",
                                "nominee_address": nominee_address or ""
                            }

                            if "மீட்டல்" in txn_category or "Release" in txn_category:
                                cart_entry["closed_gl_no"] = final_gl
                                cart_entry["closed_loan_id"] = selected_loan_db_id

                            if "Pledge" in txn_category:
                                commit_next_gl_number(st.session_state.branch_id, next_seq_num)
                                decl_payload = {
                                    "customer_name": visit.get("customer_name", ""),
                                    "address": visit.get("address", ""),
                                    "contact_number": visit.get("mobile", ""),
                                    "branch_name": st.session_state.get("branch", ""),
                                    "pledge_date": get_ist_time_str("%d-%m-%Y"),
                                    "loan_number": new_gl_no,
                                    "loan_amount": paid_amt,
                                    "current_date": get_ist_time_str("%d-%m-%Y")
                                }
                                st.session_state.declaration_gl_no = new_gl_no
                                st.session_state.current_declaration = generate_declaration_html(decl_payload)

                            st.session_state.transactions_cart.append(cart_entry)
                            st.session_state.form_reset_counter += 1
                            st.success(f"'{txn_category}' வெற்றிகரமாகப் பட்டியலில் சேர்க்கப்பட்டது!")
                            st.rerun()

                # உறுதி ஆவணப் பதிவிறக்கப் பகுதி
                if st.session_state.get("current_declaration"):
                    gl_no_val = st.session_state.get("declaration_gl_no", "GL")
                    clean_gl_key = str(gl_no_val).replace("/", "_")
                    decl_html = st.session_state.current_declaration

                    with st.container(border=True):
                        st.warning("⚠️ **கூடுதல் நகைக் கடன் உறுதிமொழிப் பத்திரம் அவசியமாகிறது.**")
                        st.download_button(
                            label=f"📄 உறுதி ஆவணத்தைப் பதிவிறக்குக (Print Declaration - GL: {gl_no_val})",
                            data=decl_html.encode("utf-8"),
                            file_name=f"Declaration_{clean_gl_key}.html",
                            mime="text/html; charset=utf-8",
                            type="primary",
                            key=f"dl_btn_{clean_gl_key}"
                        )

                # 🛒 கார்ட் பட்டியல்
                st.markdown("---")
                if len(st.session_state.transactions_cart) > 0:
                    st.markdown("### 🛒 நடவடிக்கைகள் பட்டியல்:")
                    df_cart = pd.DataFrame(st.session_state.transactions_cart)
                    display_cols = [c for c in ["transaction_type", "paid_amount", "received_amount", "net_weight", "remarks"] if c in df_cart.columns]
                    st.dataframe(df_cart[display_cols] if display_cols else df_cart, use_container_width=True)

                    total_paid = sum(float(x.get("paid_amount", 0)) for x in st.session_state.transactions_cart)
                    total_received = sum(float(x.get("received_amount", 0)) for x in st.session_state.transactions_cart)
                    net_amount = total_paid - total_received

                    c1, c2, c3 = st.columns(3)
                    c1.metric("மொத்த பட்டுவாடா", f"₹{total_paid:,.2f}")
                    c2.metric("மொத்த வரவு", f"₹{total_received:,.2f}")
                    c3.metric("நிகரத் தொகை", f"₹{abs(net_amount):,.2f}")

                    cart_b1, cart_b2 = st.columns([4, 1])
                    with cart_b1:
                        if st.button("பணம் செலுத்தும் முறை மற்றும் OTP பிரிவிற்குச் செல் ➔", type="primary", key="btn_goto_otp"):
                            st.session_state.current_visit["net_amount"] = net_amount
                            st.session_state.current_visit["total_paid"] = total_paid
                            st.session_state.current_visit["total_received"] = total_received
                            st.session_state.current_visit["step"] = "CASH_OTP"
                            st.rerun()
                    with cart_b2:
                        if st.button("🗑️ பட்டியலை அழி (Clear Cart)", use_container_width=True):
                            st.session_state.transactions_cart = []
                            st.session_state.current_declaration = None
                            st.session_state.declaration_gl_no = None
                            st.session_state.form_reset_counter += 1
                            st.rerun()

            # ---------------------------------------------------------------------
            # படி 3: பணம் மற்றும் OTP சரிபார்ப்பு (CASH_OTP)
            # ---------------------------------------------------------------------
            elif st.session_state.current_visit and st.session_state.current_visit.get("step") == "CASH_OTP":
                visit = st.session_state.current_visit
                net_target = visit.get("net_amount", 0.0)
                total_needed_abs = abs(net_target)
                current_drawer = get_current_branch_cash_drawer(st.session_state.branch_id)
                otp_already_sent = "generated_otp" in st.session_state and st.session_state.generated_otp is not None

                st.subheader("படி 3: பணம் செலுத்தும் முறை மற்றும் OTP சரிபார்ப்பு")
                hdr_text = (
                    f"💸 வாடிக்கையாளருக்கு வழங்க வேண்டிய நிகரத் தொகை (Pay-OUT): ₹{net_target:,.2f}"
                    if net_target > 0
                    else f"💰 வாடிக்கையாளரிடம் பெற வேண்டிய நிகரத் தொகை (Pay-IN): ₹{total_needed_abs:,.2f}"
                )
                st.info(f"**{hdr_text}** (வாடிக்கையாளர்: {visit['customer_name']})")

                # படிவத்திற்குள் வைப்பதன் மூலம் நோட்டுகளை எண்ணி உள்ளிடும் போது ரீபிரெஷ் ஆகாது!
                with st.form("cash_denomination_split_form"):
                    st.markdown("#### 💳 பணம் செலுத்தும் / பெறும் வழிகள் (Payment Split)")
                    pm_c1, pm_c2, pm_c3 = st.columns(3)
                    pay_option = pm_c1.selectbox(
                        "பரிமாற்ற வகை:",
                        ["முழுவதும் ரொக்கம் (100% Cash)", "முழுவதும் வங்கி / UPI (100% Online)", "பகுதி ரொக்கம் + பகுதி வங்கி (Split)"],
                        disabled=otp_already_sent,
                        key="pay_option_select"
                    )

                    if pay_option == "முழுவதும் ரொக்கம் (100% Cash)":
                        cash_portion = total_needed_abs
                        bank_portion = 0.0
                    elif pay_option == "முழுவதும் வங்கி / UPI (100% Online)":
                        cash_portion = 0.0
                        bank_portion = total_needed_abs
                    else:
                        cash_portion = pm_c2.number_input("ரொக்கப் பகுதி (₹):", min_value=0.0, max_value=float(total_needed_abs), step=500.0, disabled=otp_already_sent)
                        bank_portion = total_needed_abs - cash_portion

                    pm_c2.metric("நிகர ரொக்க இலக்கு", f"₹{cash_portion:,.2f}")
                    pm_c3.metric("வங்கி / UPI தொகை", f"₹{bank_portion:,.2f}")
                    bank_ref_no = pm_c3.text_input("UTR / Ref எண் *:", disabled=otp_already_sent) if bank_portion > 0 else ""

                    st.markdown("#### 💵 நோட்டுகள் மற்றும் மீதி சில்லறை கணக்கீடு")
                    col_den1, col_den2 = st.columns(2)

                    with col_den1:
                        st.markdown("##### 📥 வாடிக்கையாளர் தந்த நோட்டுகள் (Cash IN):")
                        r1_1, r1_2, r1_3, r1_4 = st.columns(4)
                        in_500 = r1_1.number_input("₹500 (IN)", min_value=0, step=1, disabled=otp_already_sent)
                        in_200 = r1_2.number_input("₹200 (IN)", min_value=0, step=1, disabled=otp_already_sent)
                        in_100 = r1_3.number_input("₹100 (IN)", min_value=0, step=1, disabled=otp_already_sent)
                        in_50  = r1_4.number_input("₹50 (IN)", min_value=0, step=1, disabled=otp_already_sent)

                        r2_1, r2_2, r2_3, r2_4 = st.columns(4)
                        in_20 = r2_1.number_input("₹20 (IN)", min_value=0, step=1, disabled=otp_already_sent)
                        in_10 = r2_2.number_input("₹10 (IN)", min_value=0, step=1, disabled=otp_already_sent)
                        in_5  = r2_3.number_input("₹5 (IN)", min_value=0, step=1, disabled=otp_already_sent)
                        in_coins = r2_4.number_input("சில்லறை ₹ (IN)", min_value=0, step=1, disabled=otp_already_sent)

                    with col_den2:
                        st.markdown("##### 📤 கிளை வழங்கிய நோட்டுகள் (Cash OUT):")
                        max_500 = max(0, current_drawer["500"] + in_500)
                        max_200 = max(0, current_drawer["200"] + in_200)
                        max_100 = max(0, current_drawer["100"] + in_100)
                        max_50  = max(0, current_drawer["50"] + in_50)
                        max_20  = max(0, current_drawer["20"] + in_20)
                        max_10  = max(0, current_drawer["10"] + in_10)
                        max_5   = max(0, current_drawer["5"] + in_5)
                        max_coins = max(0, int(current_drawer["coins"]) + in_coins)

                        o1_1, o1_2, o1_3, o1_4 = st.columns(4)
                        out_500 = o1_1.number_input("₹500 (OUT)", min_value=0, max_value=max_500, step=1, disabled=otp_already_sent)
                        out_200 = o1_2.number_input("₹200 (OUT)", min_value=0, max_value=max_200, step=1, disabled=otp_already_sent)
                        out_100 = o1_3.number_input("₹100 (OUT)", min_value=0, max_value=max_100, step=1, disabled=otp_already_sent)
                        out_50  = o1_4.number_input("₹50 (OUT)", min_value=0, max_value=max_50, step=1, disabled=otp_already_sent)

                        o2_1, o2_2, o2_3, o2_4 = st.columns(4)
                        out_20 = o2_1.number_input("₹20 (OUT)", min_value=0, max_value=max_20, step=1, disabled=otp_already_sent)
                        out_10 = o2_2.number_input("₹10 (OUT)", min_value=0, max_value=max_10, step=1, disabled=otp_already_sent)
                        out_5  = o2_3.number_input("₹5 (OUT)", min_value=0, max_value=max_5, step=1, disabled=otp_already_sent)
                        out_coins = o2_4.number_input("சில்லறை ₹ (OUT)", min_value=0, max_value=max_coins, step=1, disabled=otp_already_sent)

                    tot_in = (in_500 * 500) + (in_200 * 200) + (in_100 * 100) + (in_50 * 50) + (in_20 * 20) + (in_10 * 10) + (in_5 * 5) + in_coins
                    tot_out = (out_500 * 500) + (out_200 * 200) + (out_100 * 100) + (out_50 * 50) + (out_20 * 20) + (out_10 * 10) + (out_5 * 5) + out_coins
                    actual_net_handover = (tot_in - tot_out) if net_target < 0 else (tot_out - tot_in)

                    is_cash_tally = (actual_net_handover == cash_portion)
                    is_bank_valid = True if bank_portion == 0 else bool(bank_ref_no.strip())
                    is_ready = is_cash_tally and is_bank_valid

                    # பணம் பொருந்தியது என்பதை உறுதி செய்து Lock செய்யும் பட்டன்
                    lock_payment_btn = st.form_submit_button("🔒 பணக் கணக்கீட்டை உறுதிசெய் (Lock Payment & Proceed to OTP)", type="primary")
                    if lock_payment_btn:
                        if not is_cash_tally:
                            st.error(f"❌ நோட்டுகளின் கணக்கீடு பொருந்தவில்லை! வித்தியாசம்: ₹{abs(cash_portion - actual_net_handover):,.2f}")
                        elif not is_bank_valid:
                            st.warning("⚠️ வங்கி UTR / Ref எண்ணை உள்ளிடவும்!")
                        else:
                            st.session_state["locked_payment_data"] = {
                                "payment_mode": pay_option,
                                "cash_amount": cash_portion,
                                "bank_amount": bank_portion,
                                "bank_reference_no": bank_ref_no,
                                "denomination_details": {
                                    "in": {"500": in_500, "200": in_200, "100": in_100, "50": in_50, "20": in_20, "10": in_10, "5": in_5, "coins": in_coins},
                                    "out": {"500": out_500, "200": out_200, "100": out_100, "50": out_50, "20": out_20, "10": out_10, "5": out_5, "coins": out_coins}
                                }
                            }
                            st.success("✅ பணக் கணக்கீடு வெற்றிகரமாக உறுதி செய்யப்பட்டது!")
                            st.rerun()

                # --- OTP பகுதி ---
                st.markdown("---")
                c_name = visit.get("customer_name") or "வாடிக்கையாளர்"
                c_mob = visit.get("mobile", "-")
                v_id = visit.get("id") or visit.get("visit_no")

                current_status = None
                if v_id:
                    try:
                        req_res = supabase.table("otp_bypass_requests").select("status").eq("visit_id", v_id).order("id", desc=True).limit(1).execute()
                        if req_res.data:
                            current_status = req_res.data[0].get("status")
                    except Exception:
                        pass

                otp_cleared = (current_status == "Approved")
                if current_status == "Approved":
                    st.success("✅ **அட்மின் & ஆப்பரேஷன்ஸ் அனுமதி வழங்கப்பட்டுவிட்டது!** OTP விலக்கு அளிக்கப்பட்டது.")
                elif current_status == "Pending Admin":
                    st.warning("⏳ **OTP விலக்குக் கோரிக்கை அட்மின் ஒப்புதலுக்காக நிலுவையில் உள்ளது.**")
                elif current_status == "Pending Operations":
                    st.info("🔄 **அட்மின் ஒப்புதல் அளித்துவிட்டார்.** ஆப்பரேஷன்ஸ் இறுதி அனுமதிக்காக காத்திருக்கிறது...")
                elif current_status == "Rejected":
                    st.error("❌ OTP விலக்குக் கோரிக்கை நிராகரிக்கப்பட்டது! வழக்கமான OTP-ஐப் பயன்படுத்தவும்.")

                if not otp_cleared:
                    otp_c1, otp_c2 = st.columns([1.5, 1])
                    with otp_c1:
                        if not st.session_state.get("locked_payment_data"):
                            st.warning("⚠️ பணக் கணக்கீட்டை உறுதிசெய்த பிறகே OTP அனுப்ப முடியும்.")
                        else:
                            if st.button("📲 OTP அனுப்புக", type="primary", key="otp_btn_active"):
                                otp_code = str(random.randint(1000, 9999))
                                st.session_state.generated_otp = otp_code
                                sms_success, _ = send_fast2sms_otp(c_mob, otp_code)
                                if sms_success:
                                    st.success("✅ OTP SMS அனுப்பப்பட்டது!")
                                else:
                                    st.info(f"💡 சோதனை OTP: **{otp_code}**")
                                st.rerun()

                            entered_otp = st.text_input("வாடிக்கையாளர் OTP உள்ளிடவும்", max_chars=4, key="entered_otp_val")
                            if entered_otp and str(entered_otp).strip() == str(st.session_state.get("generated_otp", "")).strip():
                                otp_cleared = True
                                st.success("✅ OTP சரிபார்க்கப்பட்டது!")

                    with otp_c2:
                        with st.expander("🚨 OTP பெற முடியவில்லையா? (விலக்குக் கோரிக்கை)", expanded=True):
                            bypass_reason = st.text_area("விலக்குக் கோருவதற்கான காரணம் *", value="Old Mobile / No Signal", key=f"bp_rea_{v_id}")
                            if st.button("அட்மினுக்கு கோரிக்கை அனுப்பு", key=f"btn_send_bp_{v_id}", type="primary"):
                                if bypass_reason.strip():
                                    supabase.table("otp_bypass_requests").insert({
                                        "visit_id": v_id,
                                        "branch_id": int(st.session_state.branch_id),
                                        "requested_by": str(st.session_state.username),
                                        "customer_name": str(c_name),
                                        "mobile": str(c_mob),
                                        "reason": str(bypass_reason.strip()),
                                        "status": "Pending Admin"
                                    }).execute()
                                    st.success("✅ கோரிக்கை அனுப்பப்பட்டது!")
                                    st.rerun()

                # --- இறுதி நிறைவு பட்டன் (Final Visit Completion) ---
                if otp_cleared and st.session_state.get("locked_payment_data"):
                    st.markdown("---")
                    if st.button("🏁 வருகையை நிறைவு செய்து ஆப்பரேஷன்ஸ் அழைப்புக்கு அனுப்புக (Complete Visit)", type="primary", use_container_width=True):
                        try:
                            p_data = st.session_state["locked_payment_data"]
                            # 1. வருகைப் பதிவு
                            v_insert = supabase.table("customer_visits").insert({
                                "visit_no": visit["visit_no"],
                                "customer_id": visit["customer_id"],
                                "branch_id": st.session_state.branch_id,
                                "status": "Pending_Calling_Verification",
                                "payment_mode": p_data["payment_mode"],
                                "net_cash_amount": p_data["cash_amount"],
                                "bank_amount": p_data["bank_amount"],
                                "bank_reference_no": p_data["bank_reference_no"],
                                "denomination_details": p_data["denomination_details"],
                                "otp_verified": True,
                                "created_at": get_ist_time_str()
                            }).execute()

                            created_v_id = v_insert.data[0]["id"] if v_insert.data else None

                            # 2. கார்ட் பரிவர்த்தனைகள் பதிவு
                            for tx in st.session_state.transactions_cart:
                                tx_payload = {
                                    "visit_id": created_v_id,
                                    "branch_id": st.session_state.branch_id,
                                    "transaction_type": tx["transaction_type"],
                                    "staff_name": tx["staff_name"],
                                    "customer_name": visit["customer_name"],
                                    "mobile": visit["mobile"],
                                    "amount": tx["amount"],
                                    "paid_amount": tx["paid_amount"],
                                    "received_amount": tx["received_amount"],
                                    "principal_amount": tx.get("principal_amount", 0.0),
                                    "interest_amount": tx.get("interest_amount", 0.0),
                                    "total_weight": tx.get("total_weight", 0.0),
                                    "net_weight": tx.get("net_weight", 0.0),
                                    "remarks": tx["remarks"],
                                    "status": "Approved"
                                }
                                supabase.table("transactions").insert(tx_payload).execute()

                                if tx.get("closed_loan_id"):
                                    supabase.table("transactions").update({"status": "Closed"}).eq("id", tx["closed_loan_id"]).execute()

                            st.session_state.current_visit = None
                            st.session_state.transactions_cart = []
                            st.session_state.generated_otp = None
                            st.session_state["locked_payment_data"] = None
                            st.success("🎉 வருகை வெற்றிகரமாக நிறைவடைந்தது!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"நிறைவு செய்வதில் பிழை: {e}")

                        # =========================================================================
# 🌟 5. வருகையை நிறைவு செய்யும் பட்டன் (Final Visit Completion Desk)
# =========================================================================
if st.button("✅ வருகையை நிறைவு செய்க", type="primary", use_container_width=True, key="btn_complete_visit_final"):
    if not is_ready:
        st.error("❌ கணக்கீடு அல்லது UTR எண் விடுபட்டுள்ளது!")
    elif not otp_cleared and not otp_already_sent:
        st.error("❌ முதலில் வாடிக்கையாளருக்கு OTP அனுப்பவும் அல்லது விலக்குக் கோரவும்!")
    elif not otp_cleared:
        st.error("❌ தவறான OTP! அல்லது ஆப்பரேஷன்ஸ் இறுதி அனுமதி இன்னும் கிடைக்கவில்லை.")
    else:
        try:
            p_data = st.session_state.get("locked_payment_data")
            if not p_data:
                p_data = {
                    "payment_mode": pay_option,
                    "cash_amount": cash_portion,
                    "bank_amount": bank_portion,
                    "bank_reference_no": bank_ref_no,
                    "denomination_details": {
                        "in": {"500": in_500, "200": in_200, "100": in_100, "50": in_50, "20": in_20, "10": in_10, "5": in_5, "coins": in_coins},
                        "out": {"500": out_500, "200": out_200, "100": out_100, "50": out_50, "20": out_20, "10": out_10, "5": out_5, "coins": out_coins}
                    }
                }

            # 1. வாடிக்கையாளர் வருகைப் பதிவு (Customer Visit Entry)
            v_insert = supabase.table("customer_visits").insert({
                "visit_no": visit["visit_no"],
                "customer_id": visit["customer_id"],
                "branch_id": st.session_state.branch_id,
                "status": "Pending_Calling_Verification",
                "payment_mode": p_data["payment_mode"],
                "net_cash_amount": p_data["cash_amount"],
                "bank_amount": p_data["bank_amount"],
                "bank_reference_no": p_data["bank_reference_no"],
                "denomination_details": p_data["denomination_details"],
                "otp_verified": True,
                "created_at": get_ist_time_str()
            }).execute()

            created_v_id = v_insert.data[0]["id"] if v_insert.data else None

            # 2. கார்ட்டில் உள்ள பரிவர்த்தனைகளைப் பதிவு செய்தல் & மீட்டல்களை Closed ஆக்குதல்
            for item in st.session_state.transactions_cart:
                tx_payload = {
                    "visit_id": created_v_id,
                    "branch_id": st.session_state.branch_id,
                    "transaction_type": item["transaction_type"],
                    "staff_name": item["staff_name"],
                    "customer_name": visit["customer_name"],
                    "mobile": visit["mobile"],
                    "amount": item["amount"],
                    "paid_amount": item["paid_amount"],
                    "received_amount": item["received_amount"],
                    "principal_amount": item.get("principal_amount", 0.0),
                    "interest_amount": item.get("interest_amount", 0.0),
                    "total_weight": item.get("total_weight", 0.0),
                    "net_weight": item.get("net_weight", 0.0),
                    "remarks": item["remarks"],
                    "status": "Approved"
                }
                supabase.table("transactions").insert(tx_payload).execute()

                if item.get("closed_loan_id"):
                    try:
                        supabase.table("transactions").update({"status": "Closed"}).eq("id", item["closed_loan_id"]).execute()
                    except Exception:
                        pass

            # 3. புதிய அடமான கடன் வரிசை எண்களைப் புதுப்பித்தல்
            cart = st.session_state.transactions_cart
            pledge_items = [i for i in cart if "Pledge" in str(i.get("transaction_type", ""))]
            if pledge_items:
                try:
                    final_b_id = int(st.session_state.branch_id)
                    res = supabase.table("branch_loan_sequences").select("last_number").eq("branch_id", final_b_id).execute()
                    current_db_last = int(res.data[0]["last_number"]) if res.data else 0
                    new_db_last = current_db_last + len(pledge_items)
                    supabase.table("branch_loan_sequences").update({"last_number": new_db_last}).eq("branch_id", final_b_id).execute()
                except Exception:
                    pass

            st.success(f"🎉 வருகை எண் {visit['visit_no']} வெற்றிகரமாக நிறைவுபெற்றது!")
            st.session_state.current_visit = None
            st.session_state.transactions_cart = []
            st.session_state.generated_otp = None
            st.session_state.current_declaration = None
            st.session_state.declaration_gl_no = None
            st.session_state["locked_payment_data"] = None
            st.rerun()
        except Exception as e:
            st.error(f"நிறைவு செய்வதில் பிழை: {e}")

# =========================================================================
# 2-வது டேப்: கிளை ஆவணங்கள் பதிவேற்றம் (Upload Docs Desk)
# =========================================================================
with branch_tab2:
    st.subheader("📁 கிளை ஆவணங்கள் பதிவேற்றம் (Upload Docs Desk)")
    st.caption("தணிக்கைக்கு அனுப்ப வேண்டிய வாடிக்கையாளர் வருகைகள் மற்றும் அவர்களின் வணிக நடவடிக்கைகள்.")
    
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
            c_info = b_item.get("customers", {}) or {}
            b_txns = b_item.get("transactions", []) or []
            
            with st.expander(f"📄 வருகை எண்: {b_item['visit_no']} | வாடிக்கையாளர்: {c_info.get('name', '-')} (📞 {c_info.get('mobile', '-')}) | நிகரத் தொகை: ₹{float(b_item.get('net_cash_amount', 0)):,.2f}"):
                st.markdown("##### 🛒 இந்த வருகையில் மேற்கொள்ளப்பட்ட நடவடிக்கைகள்:")
                if b_txns:
                    for idx, t in enumerate(b_txns, 1):
                        st.markdown(f"**{idx}. {t.get('transaction_type', '-')}** | காரணப் பணியாளர்: `{t.get('staff_name', '-')}`")
                        st.write(f"   • பட்டுவாடா: ₹{float(t.get('paid_amount', 0)):,.2f} | வரவு: ₹{float(t.get('received_amount', 0)):,.2f}")
                        st.write(f"   • குறிப்பு / விவரம்: {t.get('remarks', '-')}")
                else:
                    st.warning("⚠️ இந்த வருகையில் நடவடிக்கைகள் எதுவும் பதிவாகவில்லை.")

                st.markdown("---")
                
                # ஆவணங்கள் பதிவேற்றத்திற்கான தனி Form
                with st.form(f"doc_upload_form_{b_item['id']}"):
                    up_docs = st.file_uploader(f"ஆவணங்களை இணைக்கவும் ({b_item['visit_no']})", accept_multiple_files=True, key=f"doc_up_{b_item['id']}")
                    sub_doc_btn = st.form_submit_button(f"ஆவணங்களைச் சமர்ப்பித்து தணிக்கைக்கு அனுப்புக ({b_item['visit_no']})", type="primary")
                    
                    if sub_doc_btn:
                        if up_docs:
                            try:
                                links = upload_files_to_supabase(up_docs, b_item["visit_no"])
                                supabase.table("customer_visits").update({"status": "Submitted_to_Auditor"}).eq("id", b_item["id"]).execute()
                                supabase.table("audit_records").insert({"visit_id": b_item["id"], "document_urls": links, "audit_status": "Pending"}).execute()
                                st.success("✅ ஆவணங்கள் வெற்றிகரமாகத் தணிக்கைக்கு அனுப்பப்பட்டுவிட்டன!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"பிழை: {e}")
                        else:
                            st.warning("⚠️ தயவுசெய்து ஆவணங்களைப் பதிவேற்றம் செய்யவும்.")

# =========================================================================
# 3-வது டேப்: தலைமை அலுவலக விளக்கங்கள் & மறுப்புகள்
# =========================================================================
with branch_tab3:
    st.subheader("⚠️ தலைமை அலுவலக விளக்கங்கள் & மறுப்புகள்")
    clarification_visits = (
        supabase.table("customer_visits")
        .select("*, customers(name, mobile), transactions(*)")
        .eq("branch_id", st.session_state.branch_id)
        .eq("status", "Needs_Clarification")
        .order("id", desc=True)
        .execute()
        .data or []
    )
    
    if not clarification_visits:
        st.info("✅ எந்த விளக்கங்களும் நிலுவையில் இல்லை.")
    else:
        for c_item in clarification_visits:
            c_cust = c_item.get("customers", {}) or {}
            prev_remarks = c_item.get("verification_remarks") or "விளக்கம் கோரப்பட்டுள்ளது."
            
            with st.expander(f"🚨 {c_item['visit_no']} | {c_cust.get('name', 'வாடிக்கையாளர்')} | ₹{float(c_item.get('net_cash_amount', 0)):,.2f}", expanded=True):
                st.markdown("##### 📜 தலைமையகம் கேட்ட விளக்கம் (Clarification Requested):")
                st.warning(prev_remarks)
                
                # விளக்கத்திற்கான Form (தட்டச்சு செய்யும் போது ரீபிரெஷ் ஆகாமல் இருக்க)
                with st.form(f"clarification_reply_form_{c_item['id']}"):
                    b_rep = st.text_area("கிளையின் பதில் விளக்கம் (Branch Reply) *:", key=f"rep_{c_item['id']}", placeholder="உங்கள் பதிலை தெளிவாக உள்ளிடவும்...")
                    reply_sub = st.form_submit_button("பதிலைச் சமர்ப்பித்து தணிக்கைக்கு அனுப்புக ➔", type="primary")

                    if reply_sub:
                        if not b_rep.strip():
                            st.error("⚠️ தயவுசெய்து உங்கள் பதிலை உள்ளிட்ட பின் சமர்ப்பிக்கவும்!")
                        else:
                            now_str = get_ist_time_str("%d-%m-%Y %I:%M %p")
                            combined_history = (
                                f"{prev_remarks}\n\n"
                                f"💬 [கிளையின் பதில் ({now_str}) - {st.session_state.username}]:\n{b_rep.strip()}"
                            )
                            
                            supabase.table("customer_visits").update({
                                "status": "Submitted_to_Auditor", 
                                "verification_remarks": combined_history
                            }).eq("id", c_item["id"]).execute()
                            
                            supabase.table("audit_records").update({
                                "audit_status": "Pending"
                            }).eq("visit_id", c_item["id"]).execute()
                            
                            st.success("✅ பதில் சமர்ப்பிக்கப்பட்டு மீண்டும் தணிக்கைக்கு அனுப்பப்பட்டது!")
                            st.rerun()