from datetime import datetime, date
import random
import json
import requests
import pandas as pd
import streamlit as st
from supabase import create_client, Client, ClientOptions
import uuid
import os
import pytz
import time  # 👈 இணைப்பு துண்டிப்பைச் சரிசெய்ய சேர்க்கப்பட்டுள்ளது
import re

# 1. பக்க வடிவமைப்பு
st.set_page_config(page_title="Branch Operations System", layout="wide")

# ==============================================================================
# 2. இந்திய நேர அமைப்பு (IST Timezone Helper)
# ==============================================================================
IST = pytz.timezone('Asia/Kolkata')

def get_ist_now():
    """இந்திய நேரப்படி தற்போதைய datetime ஆப்ஜெக்ட்டை வழங்கும்"""
    return datetime.now(IST)

def get_ist_time_str(fmt="%Y-%m-%d %H:%M:%S"):
    """இந்திய நேரத்தை வடிவமைக்கப்பட்ட உரை வடிவில் வழங்கும்"""
    return datetime.now(IST).strftime(fmt)

# ==============================================================================
# 3. டேட்டாபேஸ் இணைப்பு (Docker Environment & Streamlit Secrets)
# ==============================================================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Environment variables-ல் இல்லையெனில் மட்டும் st.secrets-ஐ பாதுகாப்பாகச் சரிபார்க்கும்
if not SUPABASE_URL or not SUPABASE_KEY:
    try:
        if hasattr(st, "secrets") and len(st.secrets) > 0:
            SUPABASE_URL = SUPABASE_URL or st.secrets.get("SUPABASE_URL")
            SUPABASE_KEY = SUPABASE_KEY or st.secrets.get("SUPABASE_KEY")
    except Exception:
        pass

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("டேட்டாபேஸ் ரகசியங்கள் (SUPABASE_URL / SUPABASE_KEY) சரியாக அமைக்கப்படவில்லை. Hugging Face Settings -> Variables and secrets பக்கத்தில் சரிபார்க்கவும்.")
    st.stop()

try:
    opts = ClientOptions(postgrest_client_timeout=30)
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY, options=opts)
except Exception:
    # ClientOptions அமைப்பதில் சிக்கல் வந்தால் நேரடி இணைப்பிற்கு மாறும்:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==============================================================================
# ⚡ அதிவேக கேச்சிங் ஃபங்க்ஷன்கள் (Cache Data with TTL)
# ==============================================================================

# 1. கிளைகள் விவரங்களை 10 நிமிடங்களுக்கு நினைவகத்தில் வைத்தல்
@st.cache_data(ttl=600)
def get_cached_branches():
    try:
        res = supabase.table("branches").select("id, branch_name, branch_code").order("id").execute()
        return res.data or []
    except Exception:
        return []

# 2. ஸ்கீம்கள் விவரங்களை 10 நிமிடங்களுக்கு நினைவகத்தில் வைத்தல்
@st.cache_data(ttl=600)
def get_cached_schemes():
    try:
        res = supabase.table("schemes").select("*").execute()
        return res.data or []
    except Exception:
        return []

# 3. பணியாளர்கள் பட்டியலை 5 நிமிடங்களுக்கு நினைவகத்தில் வைத்தல்
@st.cache_data(ttl=300)
def get_cached_staff():
    try:
        res = supabase.table("staff").select("id, name, username, branch_id, role").execute()
        return res.data or []
    except Exception:
        return []

# -------------------------------------------------------------
# ⚡ மின்னல் வேக மாஸ்டர் திட்டங்கள் கேச்சிங் (10 நிமிடங்களுக்கு ஒருமுறை மட்டும் எடுக்கும்)
# -------------------------------------------------------------
@st.cache_data(ttl=600)
def get_cached_master_schemes():
    try:
        g_data = supabase.table("gold_loan_schemes").select("*").eq("is_active", True).execute().data or []
        fd_data = supabase.table("fd_schemes").select("*").eq("is_active", True).execute().data or []
        rd_data = supabase.table("rd_schemes").select("*").eq("is_active", True).execute().data or []
        return g_data, fd_data, rd_data
    except Exception:
        return [], [], []

# ==============================================================================
# 🌟 இணைப்பு துண்டிக்கப்படுவதைத் தடுக்கும் பாதுகாப்பு செயல்பாடு (Safe Query Runner)
# ==============================================================================
def safe_execute(query_builder, retries=2):
    """சர்வர் இணைப்பு துண்டிக்கப்பட்டால் தானாக மீண்டும் இயக்கும் செயல்பாடு"""
    for attempt in range(retries):
        try:
            return query_builder.execute()
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(0.5)
                continue
            raise e

# ==============================================================================
# நகை படம் பதிவேற்றும் செயல்பாடு (Supabase Storage Bucket: ornaments)
# ==============================================================================
def upload_ornament_image(file_obj):
    if not file_obj:
        return None
    try:
        bucket_name = "ornaments"
        file_ext = file_obj.name.split(".")[-1]
        file_path = f"ornament_{get_ist_now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}.{file_ext}"
        
        # ornaments பக்கெட்டில் பதிவேற்றுதல்
        supabase.storage.from_(bucket_name).upload(
            path=file_path,
            file=file_obj.getvalue(),
            file_options={"content-type": file_obj.type, "upsert": "true"},
        )
        # பொதுவான URL எடுத்தல்
        return supabase.storage.from_(bucket_name).get_public_url(file_path)
    except Exception as e:
        st.warning(f"நகை படம் பதிவேற்றுவதில் சிக்கல்: {e}")
        return None

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
# 2.  Supabase இணைப்பு
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

# ==============================================================================
# கடன் உறுதி ஆவணம் உருவாக்கும் செயல்பாடு (Declaration Form HTML Generator)
# ==============================================================================
def generate_declaration_html(data):
    """தமிழ் டிக்ளரேஷன் உறுதி ஆவணம் உருவாக்கும் முறை"""
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
        @page {{
            size: A4 portrait;
            margin: 20mm;
        }}
        * {{
            box-sizing: border-box;
        }}
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
        .footer-table td {{
            vertical-align: bottom;
        }}
        @media print {{
            body {{
                padding: 0;
            }}
            .no-print {{
                display: none !important;
            }}
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

# -------------------------------------------------------------
# 💰 கிளை நேரலை கல்லா ரொக்க இருப்பைப் பெறும் செயல்பாடு (Synced with Notes)
# -------------------------------------------------------------
def get_branch_current_cash(branch_id):
    """கல்லா டிராயரில் உள்ள நேரடி நோட்டுகளின் மொத்த மதிப்பை துல்லியமாக வழங்கும்"""
    try:
        if not branch_id:
            return 0.0
        drawer = get_current_branch_cash_drawer(branch_id)
        total_val = (
            int(drawer.get("500", 0)) * 500 +
            int(drawer.get("200", 0)) * 200 +
            int(drawer.get("100", 0)) * 100 +
            int(drawer.get("50", 0)) * 50 +
            int(drawer.get("20", 0)) * 20 +
            int(drawer.get("10", 0)) * 10 +
            int(drawer.get("5", 0)) * 5 +
            float(drawer.get("coins", 0.0) or 0.0)
        )
        return float(total_val)
    except Exception:
        return 0.0
# -------------------------------------------------------------
# 🔄 கல்லா இருப்பைப் புதுப்பிக்கும் செயல்பாடு
# -------------------------------------------------------------
def update_branch_cash_box(branch_id, cash_in=0.0, cash_out=0.0):
    """பரிவர்த்தனைக்கு ஏற்ப கல்லா இருப்பைப் புதுப்பிக்கும் செயல்பாடு"""
    try:
        if not branch_id:
            return False
            
        net_change = float(cash_in or 0.0) - float(cash_out or 0.0)
        
        cash_res = (
            supabase.table("branch_cash_box")
            .select("*")
            .eq("branch_id", branch_id)
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
        
        if cash_res.data:
            c_box = cash_res.data[0]
            box_id = c_box["id"]
            
            open_bal = float(c_box.get("opening_balance") or 0.0)
            cur_bal = c_box.get("current_balance")
            prev_bal = open_bal if cur_bal is None else float(cur_bal)
            new_bal = prev_bal + net_change
            
            supabase.table("branch_cash_box").update({
                "current_balance": float(new_bal)
            }).eq("id", box_id).execute()
            
        return True
    except Exception:
        return False

# ---------------------------------------------------------------------
# 💰 கல்லா ரொக்கம் & நோட்டுகளின் எண்ணிக்கையைப் புதுப்பிக்கும் முழுமையான செயல்பாடு 
# ---------------------------------------------------------------------
def update_branch_cash_and_denominations(branch_id, cash_in=0.0, cash_out=0.0, denom_in=None, denom_out=None):
    """
    பரிவர்த்தனைக்கு ஏற்ப கல்லா இருப்பு மற்றும் நோட்டுகளின் எண்ணிக்கையைக் கூட்டும்/குறைக்கும்.
    denom_in / denom_out வடிவம்: {"500": 0, "200": 0, "100": 0, "50": 0, "20": 0, "10": 0, "5": 0, "coins": 0.0}
    """
    try:
        if not branch_id:
            return False
            
        denom_in = denom_in or {}
        denom_out = denom_out or {}
        net_cash_change = float(cash_in) - float(cash_out)

        # 1. கிளைக்குரிய கடைசி கல்லாப் பதிவை எடுத்தல்
        cash_res = (
            supabase.table("branch_cash_box")
            .select("*")
            .eq("branch_id", branch_id)
            .order("id", desc=True)
            .limit(1)
            .execute()
        )

        if not cash_res.data:
            return False

        c_box = cash_res.data[0]
        box_id = c_box["id"]

        # முந்தைய இருப்பு
        open_bal = float(c_box.get("opening_balance") or 0.0)
        cur_bal = c_box.get("current_balance")
        prev_bal = open_bal if cur_bal is None else float(cur_bal)
        new_total_bal = prev_bal + net_cash_change

        # 2. முந்தைய நோட்டுகளின் எண்ணிக்கை (Current Denominations)
        # current_denominations இல்லையென்றால் opening_denominations-ஐ எடுக்கும்
        curr_notes = c_box.get("current_denominations")
        if not curr_notes:
            curr_notes = c_box.get("opening_denominations") or c_box.get("denomination_details") or {}

        # நிலையான நோட்டுகள் பட்டியல்
        keys = ["500", "200", "100", "50", "20", "10", "5"]
        updated_notes = {}

        # தாள்களைக் கூட்டி/கழித்தல்
        for k in keys:
            cur_cnt = int(curr_notes.get(k, 0) or 0)
            in_cnt = int(denom_in.get(k, 0) or 0)
            out_cnt = int(denom_out.get(k, 0) or 0)
            updated_notes[k] = max(0, cur_cnt + in_cnt - out_cnt)

        # நாணயங்கள் (Coins)
        cur_coins = float(curr_notes.get("coins", 0.0) or 0.0)
        in_coins = float(denom_in.get("coins", 0.0) or 0.0)
        out_coins = float(denom_out.get("coins", 0.0) or 0.0)
        updated_notes["coins"] = max(0.0, cur_coins + in_coins - out_coins)

        # 3. நோட்டுகளின் மூலம் கிடைக்கும் உண்மையான மொத்தத் தொகை சரிபார்ப்பு
        calc_note_total = sum(int(k) * updated_notes[k] for k in keys) + updated_notes["coins"]

        # 4. Supabase-ல் புதுப்பித்தல்
        supabase.table("branch_cash_box").update({
            "current_balance": float(calc_note_total if calc_note_total > 0 else new_total_bal),
            "current_denominations": updated_notes
        }).eq("id", box_id).execute()

        return True
    except Exception as e:
        st.error(f"கல்லா நோட்டுகளைப் புதுப்பிப்பதில் பிழை: {e}")
        return False
# ==============================================================================
# வருகை வரிசை எண் உருவாக்கும் செயல்பாடு (Unique Incrementing Visit No)
# ==============================================================================
def generate_branch_visit_no(branch_id, branch_code="BR"):
    """கிளை வாரியாக வரிசை எண்ணுடன் கூடிய வருகை எண்ணை உருவாக்குதல் (எ.கா: VST-TGL-0001)"""
    try:
        b_code = str(branch_code or "BR").strip().upper()
        
        # அந்த கிளையில் கடைசியாக பதிவான VST எண்ணை எடுத்தல்
        last_v = (
            supabase.table("customer_visits")
            .select("visit_no")
            .eq("branch_id", branch_id)
            .ilike("visit_no", f"VST-{b_code}-%")
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
        
        next_num = 1
        if last_v.data:
            last_no_str = str(last_v.data[0].get("visit_no", ""))
            parts = last_no_str.split("-")
            # கடைசிப் பகுதியிலிருந்து எண்ணைப் பிரித்தெடுத்தல்
            if len(parts) >= 3 and parts[-1].isdigit():
                next_num = int(parts[-1]) + 1
        
        return f"VST-{b_code}-{str(next_num).zfill(4)}"
        
    except Exception as e:
        # ஏதேனும் பிழை வந்தால் பாதுகாப்புக்காக நேரத்தை வைத்து உருவாக்குதல்:
        return f"VST-{branch_code}-{datetime.now().strftime('%d%H%M%S')}"

# -------------------------------------------------------------
# 🪙 கிளை வாரியான ஜீபி எண் உருவாக்கும் செயல்பாடு (Format: AVL/GP/001)
# -------------------------------------------------------------
import re

# ---------------------------------------------------------------------------------
# 🪙 கிளை வாரியான ஜீபி எண் உருவாக்கும் செயல்பாடு (Format: AVL/GP/001, AVL/GP/002...)
# ---------------------------------------------------------------------------------
def generate_gp_number(branch_identifier=None) -> str:
    """
    1. gold_purchases அட்டவணையில் உள்ள 'purchase_bill_no' பத்தியைத் தேடும்.
    2. AVL/GP/001 அல்லது AVL/GP/001 / 145 என எப்படி இருந்தாலும் GP எண்ணைத் துல்லியமாகப் பிரிக்கும்.
    3. கார்ட்டில் உள்ள GP எண்ணிக்கையையும் சேர்த்து அடுத்த எண்ணை (002, 003...) உருவாக்கும்.
    """
    try:
        # 1. கிளையின் பிரபிக்ஸை (Prefix - எ.கா: AVL) எடுத்தல்
        prefix = "AVL"
        b_id = branch_identifier or st.session_state.get("branch_id")
        
        if b_id:
            try:
                seq_res = supabase.table("branch_loan_sequences").select("prefix").eq("branch_id", int(b_id)).execute()
                if seq_res.data and seq_res.data[0].get("prefix"):
                    prefix = str(seq_res.data[0]["prefix"]).strip().rstrip("/-")
            except Exception:
                prefix = "AVL"
        elif isinstance(branch_identifier, str) and branch_identifier.strip():
            prefix = branch_identifier.strip().upper().rstrip("/-")

        max_num = 0

        # 2. 🌟 gold_purchases அட்டவணையில் 'purchase_bill_no' பத்தியைத் தேடுதல்:
        try:
            gp_res = (
                supabase.table("gold_purchases")
                .select("purchase_bill_no")
                .ilike("purchase_bill_no", f"%{prefix}/GP/%")
                .execute()
            )
            if gp_res.data:
                for row in gp_res.data:
                    val = str(row.get("purchase_bill_no") or "")
                    # Regex மூலம் GP/ க்குப் பின் வரும் எண்களை மட்டும் பிரித்தெடுத்தல்:
                    m = re.search(r"GP/(\d+)", val, re.IGNORECASE)
                    if m:
                        max_num = max(max_num, int(m.group(1)))
        except Exception:
            pass

        # 3. transactions அட்டவணையிலும் ஒருமுறை சரிபார்த்தல்:
        try:
            tx_res = (
                supabase.table("transactions")
                .select("gp_number, loan_number, remarks")
                .or_(f"gp_number.ilike.%{prefix}/GP/%,loan_number.ilike.%{prefix}/GP/%,remarks.ilike.%{prefix}/GP/%")
                .execute()
            )
            if tx_res.data:
                for row in tx_res.data:
                    val = f"{row.get('gp_number', '')} {row.get('loan_number', '')} {row.get('remarks', '')}"
                    m = re.search(r"GP/(\d+)", val, re.IGNORECASE)
                    if m:
                        max_num = max(max_num, int(m.group(1)))
        except Exception:
            pass

        # 4. கார்ட்டில் (Cart) ஏற்கனவே சேர்க்கப்பட்டுள்ள GP எண்ணிக்கையைக் கூட்டுதல்:
        cart = st.session_state.get("transactions_cart", [])
        gp_in_cart = sum(1 for itm in cart if "GP" in str(itm.get("transaction_type", "")))

        # 5. அடுத்த எண்ணைக் கணக்கிடுதல் (1 + 1 = 2):
        next_gp_no = max_num + gp_in_cart + 1
        
        # 3 இலக்க வடிவம்: AVL/GP/002
        formatted_no = f"{next_gp_no:03d}" if next_gp_no < 1000 else f"{next_gp_no}"
        return f"{prefix}/GP/{formatted_no}"

    except Exception:
        return "AVL/GP/001"
# -------------------------------------------------------------------------------------------------
# 📜 சட்டபூர்வ தங்கக் கொள்முதல் உறுதிமொழிப் படிவம் (Legal GP Declaration & Indemnity Bond Generator)
# -------------------------------------------------------------------------------------------------
def generate_gp_declaration_html(gp_data):
    """
    Direct மற்றும் Takeover இரண்டிற்கும் சட்டப்படி செல்லுபடியாகும் 
    A4 பிரிண்ட் உறுதிமொழிப் படிவத்தை (HTML/CSS) உருவாக்கும் ஃபங்க்ஷன்.
    """
    is_takeover = "Takeover" in str(gp_data.get("gp_mode", ""))
    
    # நகைகள் அட்டவணை வரிசைகள்
    ornament_rows_html = ""
    for idx, item in enumerate(gp_data.get("ornaments", [])):
        ornament_rows_html += f"""
        <tr>
            <td style="text-align: center;">{idx + 1}</td>
            <td>{item.get('item', '-')}</td>
            <td style="text-align: center;">{item.get('count', 1)}</td>
            <td style="text-align: right;">{float(item.get('gross_wt', 0)):.3f} g</td>
            <td style="text-align: right;">{float(item.get('net_wt', 0)):.3f} g</td>
            <td style="text-align: center;">{item.get('purity', '916 KDM')}</td>
        </tr>
        """

    # டேக் ஓவர் நிதி விவரங்கள் (Takeover ஆக இருந்தால் மட்டும்)
    takeover_section_html = ""
    if is_takeover:
        takeover_section_html = f"""
        <div style="background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 10px; border-radius: 5px; margin-top: 10px; font-size: 13px;">
            <strong style="color: #723a91;">🏦 பிற நிறுவனக் கடன் மீட்பு விவரம் (Takeover Loan Settlement):</strong>
            <table style="width: 100%; margin-top: 5px; font-size: 12px; border-collapse: collapse;">
                <tr>
                    <td style="width: 50%;"><strong>முந்தைய வங்கி / நிறுவனம்:</strong> {gp_data.get('bank_source', '-')}</td>
                    <td style="width: 50%;"><strong>அடகு கடன் எண்:</strong> {gp_data.get('prev_loan_no', '-')}</td>
                </tr>
                <tr>
                    <td><strong>நிறுவனத்திற்கு செலுத்திய மீட்புத் தொகை:</strong> ₹{float(gp_data.get('advance_paid', 0)):,.2f}</td>
                    <td><strong>வாடிக்கையாளருக்கு வழங்கிய மீதித் தொகை:</strong> ₹{float(gp_data.get('balance_payable', 0)):,.2f}</td>
                </tr>
            </table>
        </div>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{ size: A4; margin: 15mm; }}
            body {{ font-family: 'Arial', 'Latha', sans-serif; color: #111; line-height: 1.4; font-size: 12px; }}
            .header {{ text-align: center; border-bottom: 2px solid #723a91; padding-bottom: 8px; margin-bottom: 12px; }}
            .header h2 {{ margin: 0; color: #723a91; font-size: 20px; }}
            .header p {{ margin: 2px 0; font-size: 11px; color: #555; }}
            .title-badge {{ display: inline-block; background-color: #723a91; color: #fff; padding: 4px 15px; border-radius: 3px; font-weight: bold; font-size: 13px; margin-top: 6px; }}
            .meta-box {{ display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 12px; border: 1px solid #ccc; padding: 8px; border-radius: 4px; }}
            table.data-table {{ width: 100%; border-collapse: collapse; margin-top: 8px; margin-bottom: 10px; }}
            table.data-table th, table.data-table td {{ border: 1px solid #999; padding: 5px 8px; font-size: 11px; }}
            table.data-table th {{ background-color: #f2f2f2; text-align: center; }}
            .legal-terms {{ border: 1px solid #333; padding: 10px; font-size: 11px; text-align: justify; background-color: #fafafa; border-radius: 4px; margin-top: 10px; }}
            .signatures {{ width: 100%; margin-top: 35px; border-collapse: collapse; }}
            .signatures td {{ vertical-align: top; text-align: center; font-size: 11px; padding: 0 10px; }}
            @media print {{
                .no-print {{ display: none !important; }}
                body {{ -webkit-print-color-adjust: exact; }}
            }}
        </style>
    </head>
    <body>
        <div class="no-print" style="margin-bottom: 15px; text-align: right;">
            <button onclick="window.print()" style="background-color: #723a91; color: white; padding: 8px 18px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: bold;">🖨️ பிரிண்ட் எடுக்க (Print Form)</button>
        </div>

        <div class="header">
            <h2>முத்துசிஸ் கோல்டு கம்பெனி (Muthusise Gold Company)</h2>
            <p>கிளை: {gp_data.get('branch_name', 'முதன்மை கிளை')} | தொடர்புக்கு: {gp_data.get('branch_phone', 'Official Branch Contact')}</p>
            <div class="title-badge">பழைய தங்க நகைகள் விற்பனை & சட்டபூர்வ உரிமை உறுதிமொழிப் படிவம் (GP DECLARATION)</div>
        </div>

        <table style="width: 100%; margin-bottom: 8px; font-size: 12px;">
            <tr>
                <td style="width: 50%;"><strong>ஜீபி எண் (GP No):</strong> <span style="font-size: 14px; font-weight: bold; color: #723a91;">{gp_data.get('gp_number')}</span></td>
                <td style="width: 50%; text-align: right;"><strong>தேதி (Date):</strong> {gp_data.get('date')}</td>
            </tr>
            <tr>
                <td><strong>வவுச்சர் எண் (Voucher No):</strong> {gp_data.get('voucher_no', '-')}</td>
                <td style="text-align: right;"><strong>விற்பனை முறை:</strong> {gp_data.get('gp_mode')}</td>
            </tr>
        </table>

        <!-- வாடிக்கையாளர் விவரம் -->
        <div style="border: 1px solid #ccc; padding: 8px; border-radius: 4px; margin-bottom: 8px; font-size: 12px;">
            <table style="width: 100%;">
                <tr>
                    <td style="width: 50%;"><strong>விற்பனையாளர் பெயர்:</strong> {gp_data.get('customer_name')}</td>
                    <td style="width: 50%;"><strong>மொபைல் எண்:</strong> {gp_data.get('customer_mobile')}</td>
                </tr>
                <tr>
                    <td colspan="2"><strong>முகவரி:</strong> {gp_data.get('customer_address', 'பதிவு செய்யப்படவில்லை')}</td>
                </tr>
            </table>
        </div>

        <!-- நகைகள் பட்டியல் -->
        <table class="data-table">
            <thead>
                <tr>
                    <th>வ.எண்</th>
                    <th>நகை விவரம் (Ornament)</th>
                    <th>எண்ணிக்கை</th>
                    <th>மொத்த எடை (Gross Wt)</th>
                    <th>நிகர எடை (Net Wt)</th>
                    <th>தூய்மை (Purity)</th>
                </tr>
            </thead>
            <tbody>
                {ornament_rows_html}
                <tr style="font-weight: bold; background-color: #f9f9f9;">
                    <td colspan="2" style="text-align: right;">மொத்தம்:</td>
                    <td style="text-align: center;">{gp_data.get('total_items', 1)}</td>
                    <td style="text-align: right;">{float(gp_data.get('gross_wt', 0)):.3f} g</td>
                    <td style="text-align: right;">{float(gp_data.get('net_wt', 0)):.3f} g</td>
                    <td style="text-align: center;">-</td>
                </tr>
            </tbody>
        </table>

        <div style="text-align: right; font-size: 13px; margin: 6px 0;">
            <strong>நிர்ணயிக்கப்பட்ட மொத்த கொள்முதல் மதிப்பு:</strong> <span style="font-size: 16px; font-weight: bold; color: #b33939;">₹{float(gp_data.get('total_value', 0)):,.2f}</span>
        </div>

        {takeover_section_html}

        <!-- சட்டபூர்வ உறுதிமொழி -->
        <div class="legal-terms">
            <strong style="text-decoration: underline;">வாடிக்கையாளரின் சட்டபூர்வ உறுதிமொழி & நிபந்தனைகள்:</strong>
            <ol style="margin: 4px 0 0 15px; padding: 0;">
                <li>மேலே விவரிக்கப்பட்ட தங்க நகைகள் அனைத்தும் எனது சுய உழைப்பில்/பூர்வீகமாக/பரிசாக எனக்குச் சொந்தமானவை. இந்நகைகள் மீது வேறு எவருக்கும் எவ்வித உரிமையோ, கூட்டுரிமையோ அல்லது நிதியியல் வில்லங்கங்களோ இல்லை.</li>
                <li>இந்நகைகள் எந்த ஒரு குற்றச் செயலிலோ, திருட்டு சம்பவத்திலோ தொடர்புடையவை அல்ல என்றும், காவல் துறை அல்லது நீதிமன்றத்தில் எவ்வித வழக்கும் நிலுவையில் இல்லை என்றும் முழு மனதுடன் உறுதி கூறுகிறேன்.</li>
                <li>இந்நகைகளின் மாற்றுத்தரம் மற்றும் எடையை எனது முன்னிலையிலேயே பரிசோதித்து, தற்போதைய சந்தை மதிப்பை முழுமையாக அறிந்து, என் சொந்த விருப்பத்தின் பேரில் முத்துசிஸ் கோல்டு கம்பெனிக்கு நிரந்தரமாக விற்பனை செய்கிறேன்.</li>
                <li><strong>இழப்பீட்டுப் பொறுப்பு:</strong> இந்நகைகள் சம்பந்தமாக எதிர்காலத்தில் காவல் துறை, நீதிமன்றம் அல்லது எந்த ஒரு மூன்றாம் நபராலும் ஏதேனும் சட்டரீதியான ஆட்சேபனையோ, புகாரோ அல்லது இழப்போ ஏற்பட்டால், அதற்கு <u>நானே முழு முதற் பொறுப்பாவேன்</u>. மேலும் முத்துசிஸ் கோல்டு கம்பெனிக்கு ஏற்படும் அனைத்து இழப்பீடுகளையும் நானே முழுமையாக ஈடுசெய்வேன் என உறுதியளிக்கிறேன்.</li>
            </ol>
        </div>

        <!-- கையொப்பங்கள் -->
        <table class="signatures">
            <tr>
                <td style="width: 33%;">
                    <div style="border-top: 1px dashed #333; padding-top: 5px; margin-top: 35px;">
                        <strong>வாடிக்கையாளர் கையொப்பம் / இடது பெருவிரல் ரேகை</strong><br>
                        (Customer Signature / LTI)
                    </div>
                </td>
                <td style="width: 33%;">
                    <div style="border-top: 1px dashed #333; padding-top: 5px; margin-top: 35px;">
                        <strong>சாட்சி 1 (அறிமுகம் / ரெபரண்ஸ்):</strong><br>
                        பெயர்: {gp_data.get('ref1_name', '-')}<br>
                        மொபைல்: {gp_data.get('ref1_phone', '-')}
                    </div>
                </td>
                <td style="width: 34%;">
                    <div style="border-top: 1px dashed #333; padding-top: 5px; margin-top: 35px;">
                        <strong>அங்கீகரிக்கப்பட்ட கிளை அலுவலர்</strong><br>
                        முத்துசிஸ் கோல்டு கம்பெனி
                    </div>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    return html_content
import re

def get_branch_code_by_id(branch_id: int) -> str:
    """கிளை ஐடியிலிருந்து கிளை குறியீட்டைப் (Branch Code) பெறுதல்"""
    try:
        b_res = supabase.table("branches").select("branch_code").eq("id", int(branch_id)).execute()
        if b_res.data and b_res.data[0].get("branch_code"):
            return str(b_res.data[0]["branch_code"]).strip().upper()
    except Exception:
        pass
    return "BR"

import re
import json

def generate_fd_account_no(branch_id: int) -> str:
    """fixed_deposits அட்டவணை மற்றும் கார்ட்டில் (transactions_cart) உள்ள உச்சபட்ச எண்ணைப் பார்த்து அடுத்த எண்ணை உருவாக்குதல்"""
    b_code = get_branch_code_by_id(branch_id)
    max_seq = 0
    pattern = re.compile(rf"{re.escape(b_code)}/FD/(\d+)", re.IGNORECASE)
    
    # 1. Supabase database-ல் உள்ள அதிகபட்ச எண்ணை எடுத்தல்
    try:
        res = supabase.table("fixed_deposits").select("fd_account_no").eq("branch_id", int(branch_id)).execute()
        for row in (res.data or []):
            acc = str(row.get("fd_account_no", "")).strip()
            m = pattern.search(acc)
            if m:
                max_seq = max(max_seq, int(m.group(1)))
                
        # transactions டேபிளிலும் சரிபார்த்தல் (பழைய பல்க் பதிவுகள்)
        txns = (
            supabase.table("transactions")
            .select("transaction_details, remarks, customer_visits!inner(branch_id)")
            .eq("customer_visits.branch_id", int(branch_id))
            .ilike("transaction_type", "%FD%")
            .execute()
            .data or []
        )
        for t in txns:
            m1 = pattern.search(str(t.get("transaction_details") or ""))
            if m1:
                max_seq = max(max_seq, int(m1.group(1)))
            m2 = pattern.search(str(t.get("remarks") or ""))
            if m2:
                max_seq = max(max_seq, int(m2.group(1)))
    except Exception:
        pass

    # 2. 🌟 தற்போதைய கார்ட்டில் (transactions_cart) உள்ள "FD Open" பதிவுகளைச் சரிபார்த்தல்
    try:
        cart_items = st.session_state.get("transactions_cart", [])
        for item in cart_items:
            t_type = str(item.get("transaction_type", ""))
            if "FD Open" in t_type or ("FD" in t_type and "Open" in t_type) or ("FD" in t_type and "புதிய" in t_type):
                item_acc = str(item.get("account_no") or (item.get("extra_meta_data") or {}).get("account_no") or "")
                m_cart1 = pattern.search(item_acc)
                if m_cart1:
                    max_seq = max(max_seq, int(m_cart1.group(1)))
                m_cart2 = pattern.search(str(item.get("remarks") or ""))
                if m_cart2:
                    max_seq = max(max_seq, int(m_cart2.group(1)))
    except Exception:
        pass

    return f"{b_code}/FD/{max_seq + 1:04d}"


def generate_rd_account_no(branch_id: int) -> str:
    """recurring_deposits அட்டவணை மற்றும் கார்ட்டில் (transactions_cart) உள்ள உச்சபட்ச எண்ணைப் பார்த்து அடுத்த எண்ணை உருவாக்குதல்"""
    b_code = get_branch_code_by_id(branch_id)
    max_seq = 0
    pattern = re.compile(rf"{re.escape(b_code)}/RD/(\d+)", re.IGNORECASE)
    
    # 1. Supabase database-ல் உள்ள அதிகபட்ச எண்ணை எடுத்தல்
    try:
        res = supabase.table("recurring_deposits").select("rd_account_no").eq("branch_id", int(branch_id)).execute()
        for row in (res.data or []):
            acc = str(row.get("rd_account_no", "")).strip()
            m = pattern.search(acc)
            if m:
                max_seq = max(max_seq, int(m.group(1)))
                
        # transactions டேபிளிலும் சரிபார்த்தல் (பழைய பல்க் பதிவுகள்)
        txns = (
            supabase.table("transactions")
            .select("transaction_details, remarks, customer_visits!inner(branch_id)")
            .eq("customer_visits.branch_id", int(branch_id))
            .ilike("transaction_type", "%RD%")
            .execute()
            .data or []
        )
        for t in txns:
            m1 = pattern.search(str(t.get("transaction_details") or ""))
            if m1:
                max_seq = max(max_seq, int(m1.group(1)))
            m2 = pattern.search(str(t.get("remarks") or ""))
            if m2:
                max_seq = max(max_seq, int(m2.group(1)))
    except Exception:
        pass

    # 2. 🌟 தற்போதைய கார்ட்டில் (transactions_cart) உள்ள "RD Open" பதிவுகளைச் சரிபார்த்தல்
    try:
        cart_items = st.session_state.get("transactions_cart", [])
        for item in cart_items:
            t_type = str(item.get("transaction_type", ""))
            # புதிய RD Open பதிவுகளுக்கு மட்டுமே வரிசை எண்ணைக் கணக்கிட வேண்டும்
            if "RD Open" in t_type or ("RD" in t_type and "Open" in t_type) or ("RD" in t_type and "புதிய" in t_type):
                item_acc = str(item.get("account_no") or (item.get("extra_meta_data") or {}).get("account_no") or "")
                m_cart1 = pattern.search(item_acc)
                if m_cart1:
                    max_seq = max(max_seq, int(m_cart1.group(1)))
                m_cart2 = pattern.search(str(item.get("remarks") or ""))
                if m_cart2:
                    max_seq = max(max_seq, int(m_cart2.group(1)))
    except Exception:
        pass

    return f"{b_code}/RD/{max_seq + 1:04d}"
# =========================================================================
# 🔍 வாடிக்கையாளரின் ஆக்டிவ் RD கணக்குகளை எடுக்கும் ஃபங்க்ஷன் (Hybrid Mode)
# =========================================================================
def get_customer_rd_accounts(customer_id: int):
    """வாடிக்கையாளரின் முடிவடையாத (Active) RD கணக்குகளை எடுத்தல்"""
    try:
        # 1. recurring_deposits அட்டவணையில் முதலில் தேடுதல்
        res = (
            supabase.table("recurring_deposits")
            .select("rd_account_no, monthly_installment")
            .eq("customer_id", int(customer_id))
            .eq("status", "Active")
            .execute()
        )
        if res.data:
            return [{"acc_no": r["rd_account_no"], "installment_amount": float(r["monthly_installment"] or 0.0)} for r in res.data]

        # 2. அட்டவணையில் இல்லை எனில் transactions பதிவுகளில் தேடுதல் (Fallback)
        v_res = supabase.table("customer_visits").select("id").eq("customer_id", int(customer_id)).execute()
        v_ids = [v["id"] for v in (v_res.data or [])]
        if not v_ids:
            return []

        open_res = supabase.table("transactions").select("transaction_details").in_("visit_id", v_ids).ilike("transaction_type", "%RD Open%").execute()
        close_res = supabase.table("transactions").select("transaction_details").in_("visit_id", v_ids).ilike("transaction_type", "%RD Close%").execute()
        closed_accs = {str((t.get("transaction_details") or {}).get("account_no", "")).strip() for t in (close_res.data or [])}

        active_rds = []
        for t in (open_res.data or []):
            d = t.get("transaction_details") or {}
            acc = str(d.get("account_no", "")).strip()
            if acc and acc not in closed_accs and acc not in [x["acc_no"] for x in active_rds]:
                active_rds.append({
                    "acc_no": acc,
                    "installment_amount": float(d.get("installment_amount", 0.0) or 0.0)
                })
        return active_rds
    except Exception:
        return []

# =========================================================================
# 🔍 வாடிக்கையாளரின் ஆக்டிவ் FD கணக்குகளை எடுக்கும் ஃபங்க்ஷன் (Hybrid Mode)
# =========================================================================
def get_customer_fd_accounts(customer_id: int):
    """வாடிக்கையாளரின் முடிவடையாத (Active) FD கணக்குகளை எடுத்தல்"""
    try:
        # 1. fixed_deposits அட்டவணையில் முதலில் தேடுதல்
        res = (
            supabase.table("fixed_deposits")
            .select("fd_account_no, deposit_amount")
            .eq("customer_id", int(customer_id))
            .eq("status", "Active")
            .execute()
        )
        if res.data:
            return [{"acc_no": r["fd_account_no"], "deposit_amount": float(r["deposit_amount"] or 0.0)} for r in res.data]

        # 2. அட்டவணையில் இல்லை எனில் transactions பதிவுகளில் தேடுதல் (Fallback)
        v_res = supabase.table("customer_visits").select("id").eq("customer_id", int(customer_id)).execute()
        v_ids = [v["id"] for v in (v_res.data or [])]
        if not v_ids:
            return []

        open_res = supabase.table("transactions").select("transaction_details").in_("visit_id", v_ids).ilike("transaction_type", "%FD Open%").execute()
        close_res = supabase.table("transactions").select("transaction_details").in_("visit_id", v_ids).ilike("transaction_type", "%FD Close%").execute()
        closed_accs = {str((t.get("transaction_details") or {}).get("account_no", "")).strip() for t in (close_res.data or [])}

        active_fds = []
        for t in (open_res.data or []):
            d = t.get("transaction_details") or {}
            acc = str(d.get("account_no", "")).strip()
            if acc and acc not in closed_accs and acc not in [x["acc_no"] for x in active_fds]:
                active_fds.append({
                    "acc_no": acc,
                    "deposit_amount": float(d.get("deposit_amount", 0.0) or 0.0)
                })
        return active_fds
    except Exception:
        return []

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

def get_current_branch_cash_drawer(branch_id):
    empty_stock = {"500": 0, "200": 0, "100": 0, "50": 0, "20": 0, "10": 0, "5": 0, "coins": 0.0}
    if not branch_id:
        return empty_stock

    try:
        clean_b_id = int(branch_id)
        stock = empty_stock.copy()

        # =========================================================================
        # 1. அட்மின் பதிவு செய்த மிகச் சமீபத்திய துவக்க இருப்பை எடுத்தல் (Opening Stock)
        # =========================================================================
        box_res = (
            supabase.table("branch_cash_box")
            .select("opening_denomination, entry_date")
            .eq("branch_id", clean_b_id)
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
        
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

        # =========================================================================
        # 2. வாடிக்கையாளர் வருகைகளின் வரவு / செலவு நோட்டுகள் (Customer Visits)
        # =========================================================================
        # ✅ ஆப்பரேஷன்ஸ் ஒப்புதல் பெற்ற வருகைகளை மட்டுமே கணக்கிடுதல் (Pending_Calling_Verification இதில் வராது)
        visits_query = (
            supabase.table("customer_visits")
            .select("denomination_details, created_at, status")
            .eq("branch_id", clean_b_id)
            .in_("status", ["Pending_Branch_Docs", "Submitted_to_Auditor", "Approved", "Needs_Clarification"])
        )
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
                        stock[k] += val_in
                        stock[k] -= val_out

        # =========================================================================
        # 3. தலைமையகம் மற்றும் கிளை இடையேயான பணப் பரிமாற்றம் (Fund Transfers)
        # =========================================================================
        fund_query = (
            supabase.table("branch_fund_transfers")
            .select("transfer_type, denomination_details, payment_mode, status")
            .eq("branch_id", clean_b_id)
            .eq("payment_mode", "Cash")
            .neq("status", "Rejected")
        )
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

        # =========================================================================
        # 4. கிளைச் செலவுகள் (Branch Expenses)
        # =========================================================================
        exp_query = (
            supabase.table("branch_expenses")
            .select("denomination_details, status")
            .eq("branch_id", clean_b_id)
            .neq("status", "Rejected")
        )
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
                    stock[k] -= out_val
                    stock[k] += in_val

        # எதிர்மறை மதிப்புகள் வராமல் பாதுகாத்தல்
        for k in stock:
            stock[k] = max(0.0 if k == "coins" else 0, stock[k])

        return stock
    except Exception as e:
        return empty_stock
# ==============================================================================
# காரணப் பணியாளர் அறிக்கை (Incentive & Attribution Report)
# ==============================================================================
def render_staff_attribution_report(selected_branch_id=None):
    st.markdown("### 📊 காரணப் பணியாளர் அறிக்கை & ஸ்கீம் வாரியான ஊக்கத்தொகை (Scheme-wise Incentive & Points Report)")

    f_col1, f_col2, f_col3 = st.columns([1.5, 1.5, 2])
    start_date = f_col1.date_input("தொடக்கத் தேதி (From):", value=date.today().replace(day=1), key=f"rep_s_{selected_branch_id}")
    end_date = f_col2.date_input("முடிவுத் தேதி (To):", value=date.today(), key=f"rep_e_{selected_branch_id}")

    if start_date > end_date:
        st.error("தொடக்கத் தேதி முடிவுத் தேதியை விட அதிகமாக இருக்கக்கூடாது!")
        return

    start_dt_str = f"{start_date}T00:00:00"
    end_dt_str = f"{end_date}T23:59:59"

    set_res = supabase.table("incentive_settings").select("*").eq("id", 1).execute().data
    rupees_per_point = float(set_res[0].get("rupees_per_point", 5.0)) if set_res else 5.0
    penalty_per_lakh = float(set_res[0].get("negative_growth_penalty_per_lakh", 15.0)) if set_res else 15.0

    inc_rules = supabase.table("staff_incentive_rules").select("*").eq("is_active", True).execute().data or []
    rule_dict = {}
    for r in inc_rules:
        t_type = r.get("transaction_type")
        sch_name = r.get("scheme_name", "All")
        rule_dict[(t_type, sch_name)] = r

    branch_staff_query = supabase.table("users").select("name, role, branch_id").eq("is_active", True)
    if selected_branch_id:
        branch_staff_query = branch_staff_query.eq("branch_id", selected_branch_id)
    active_users = branch_staff_query.execute().data or []

    branch_staff_dict = {}
    for u in active_users:
        b_id = u.get("branch_id")
        if b_id not in branch_staff_dict:
            branch_staff_dict[b_id] = []
        branch_staff_dict[b_id].append(u)

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

    detailed_txn_logs = []
    staff_points_map = {}

    def add_staff_points(name, pts):
        if name not in staff_points_map:
            staff_points_map[name] = 0.0
        staff_points_map[name] += pts

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
            if "Release" in txn_type or "அடமானம் மீட்டல்" in txn_type:
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

            elif "Part Payment" in txn_type or "அசல் வரவு" in txn_type:
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

            rule_info = (
                rule_dict.get((txn_type, detected_scheme)) 
                or rule_dict.get((txn_type, "All")) 
                or {"basis_type": "Amount", "unit_value": 100000.0, "points_per_unit": 10.0}
            )

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
    penalty_pts = 0.0
    if is_negative_growth:
        penalty_pts = (abs(net_gold_growth) / 100000.0) * penalty_per_lakh

    staff_filter_options = ["அனைத்து பணியாளர்களும் (All Staff & Walk-in)"] + sorted(list(staff_points_map.keys()))
    with f_col3:
        selected_staff_filter = st.selectbox("காரணப் பணியாளரைத் தேர்ந்தெடுக்கவும்:", staff_filter_options, key=f"staff_flt_{selected_branch_id}")

    if selected_staff_filter != "அனைத்து பணியாளர்களும் (All Staff & Walk-in)":
        df_filtered = df_txns[df_txns["பணியாளர்"] == selected_staff_filter].copy()
    else:
        df_filtered = df_txns.copy()

    display_df = df_filtered.drop(columns=["raw_amount"]) if "raw_amount" in df_filtered.columns else df_filtered

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("மொத்த நடவடிக்கைகள்", f"{len(df_filtered):,}")
    m2.metric("புதிய நகைக்கடன் (Pledge)", f"₹{tot_pledge:,.2f}")
    m3.metric("அடகு மீட்டல் (Principal)", f"₹{tot_release:,.2f}")

    if is_negative_growth:
        m4.metric("நிகர நகைக் கடன் வளர்ச்சி", f"-₹{abs(net_gold_growth):,.2f}", delta="-நெகட்டிவ் வளர்ச்சி", delta_color="inverse")
        st.error(f"⚠️ **எச்சரிக்கை:** நகைக் கடன் வளர்ச்சி நெகட்டிவாக உள்ளது (-₹{abs(net_gold_growth):,.2f}). இதனால் ஊழியர் கணக்கில் மொத்தமாக **-{penalty_pts:,.1f} நெகட்டிவ் புள்ளிகள்** கழிக்கப்படும்.")
    else:
        m4.metric("நிகர நகைக் கடன் வளர்ச்சி", f"+₹{net_gold_growth:,.2f}", delta="+பாசிட்டிவ் வளர்ச்சி")

    st.markdown("---")

    st.markdown(f"##### 🏆 பணியாளர் வாரியான புள்ளி விவரம் & ஊக்கத்தொகை (1 புள்ளி = ₹{rupees_per_point:.2f})")
    perf_rows = []
    active_staff_count = max(1, len(staff_points_map))

    for s_name, pts in staff_points_map.items():
        deduct_pts = (penalty_pts / active_staff_count) if is_negative_growth else 0.0
        final_pts = pts - deduct_pts
        final_incentive = final_pts * rupees_per_point

        perf_rows.append({
            "பணியாளர் பெயர்": s_name,
            "ஈட்டிய/குறைந்த நிகரப் புள்ளிகள்": round(final_pts, 2),
            "ஊக்கத்தொகை (Incentive ₹)": f"₹{final_incentive:,.2f}"
        })

    st.dataframe(pd.DataFrame(perf_rows), use_container_width=True)

    st.markdown("##### 🔍 பரிவர்த்தனை & ஸ்கீம் வாரியான விரிவான புள்ளி அறிக்கை (Detailed Breakdown)")
    st.dataframe(display_df, use_container_width=True)

    csv = pd.DataFrame(perf_rows).to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 அறிக்கையைப் பதிவிறக்குக (Download CSV)",
        data=csv,
        file_name=f"Staff_Scheme_Incentive_Report_{start_date}_to_{end_date}.csv",
        mime="text/csv",
        key=f"dl_csv_{selected_branch_id}"
    )

# ==========================================
# 4. தற்காலிக மாறிகள் (Session State Setup)
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

if "current_declaration" not in st.session_state:
    st.session_state.current_declaration = None

if "declaration_gl_no" not in st.session_state:
    st.session_state.declaration_gl_no = None

if "form_reset_counter" not in st.session_state:
    st.session_state.form_reset_counter = 0

if "gp_ornament_rows" not in st.session_state:
    st.session_state.gp_ornament_rows = [
        {"item": "", "count": 1, "gross_wt": 0.0, "net_wt": 0.0, "purity": "916 KDM"}
    ]

@st.cache_data(ttl=300)
def load_branches_data():
    try:
        res = supabase.table("branches").select("*").order("id").execute()
        return res.data or []
    except Exception as e:
        return []

# -------------------------------------------------------------
# 🏷️ அட்மின் ஸ்கீம் மாஸ்டரில் இருந்து முழு திட்டங்களை எடுக்கும் செயல்பாடு
# -------------------------------------------------------------
@st.cache_data(ttl=60)
def get_active_loan_schemes():
    """அட்மின் அமைத்த செயல்பாட்டில் உள்ள கடன் திட்டங்களின் முழு விவரங்களை வழங்கும்"""
    try:
        res = supabase.table("gold_loan_schemes").select("*").execute()
        if res.data:
            valid_schemes = []
            for row in res.data:
                # is_active பத்தி இருந்து False என இருந்தால் மட்டும் தவிர்க்கும்
                if row.get("is_active") is False:
                    continue

                # திட்டத்தின் பெயர்
                s_name = (
                    row.get("scheme_name") or 
                    row.get("name") or 
                    row.get("scheme_code") or 
                    row.get("scheme")
                )
                if not s_name:
                    continue

                # திட்டத்தின் வட்டி, காலம் மற்றும் கிராம் விலை ஆகியவற்றை எடுத்தல்
                valid_schemes.append({
                    "id": row.get("id"),
                    "scheme_name": str(s_name).strip(),
                    "scheme_code": str(row.get("scheme_code") or s_name[:6]).strip().upper(),
                    "interest_rate": float(row.get("interest_rate") or row.get("rate") or row.get("roi") or 18.0),
                    "tenure_months": int(row.get("tenure_months") or row.get("tenure") or row.get("duration") or 12),
                    "max_rate_per_gram": float(row.get("max_rate_per_gram") or row.get("rpg") or row.get("rate_per_gram") or 0.0),
                })
            
            if valid_schemes:
                return valid_schemes
    except Exception:
        pass

    # டேட்டாபேஸ் கிடைக்காத பட்சத்தில் இயல்பான மாற்றுத் திட்டங்கள் (Fallback)
    return [
        {
            "id": 1,
            "scheme_name": "VVH149",
            "scheme_code": "VVH149",
            "interest_rate": 18.0,
            "tenure_months": 12,
            "max_rate_per_gram": 6500.0
        },
        {
            "id": 2,
            "scheme_name": "Standard Gold Loan",
            "scheme_code": "STDGL",
            "interest_rate": 12.0,
            "tenure_months": 3,
            "max_rate_per_gram": 6800.0
        }
    ]

def generate_next_gl_number(branch_id):
    try:
        clean_b_id = int(branch_id)
        res = supabase.table("branch_loan_sequences").select("*").eq("branch_id", clean_b_id).execute()
        
        if res.data:
            rec = res.data[0]
            prefix = rec.get("prefix", "GL")
            next_no = int(rec.get("last_number", 0)) + 1
        else:
            prefix = "GL"
            next_no = 1
            try:
                supabase.table("branch_loan_sequences").insert({
                    "branch_id": clean_b_id,
                    "prefix": prefix,
                    "last_number": 0
                }).execute()
            except Exception:
                pass

        # 🌟 முன்னொட்டின் முடிவில் உள்ள தேவையில்லாத '-' அல்லது '/' குறியீடுகளை நீக்கிவிட்டு சரியாக '/' சேர்த்தல்
        clean_pfx = str(prefix).strip().rstrip("/-")
        formatted_gl = f"{clean_pfx}/{str(next_no).zfill(4)}"

        return formatted_gl, next_no
    except Exception as e:
        return "GL/1001", 1

# -------------------------------------------------------------
# 🔢 கிளை வாரியான கடன் எண்ணை உருவாக்கும் செயல்பாடு (Format: AVL/1754)
# -------------------------------------------------------------
def get_current_display_gl_number(branch_id):
    """branch_loan_sequences அட்டவணையில் உள்ள prefix மற்றும் last_number-ஐ நேரடியாக எடுத்து AVL/1754 என உருவாக்கும்"""
    try:
        clean_b_id = int(branch_id)
        
        # 1. branch_loan_sequences அட்டவணையில் இருந்து prefix மற்றும் last_number எடுத்தல்
        seq_res = supabase.table("branch_loan_sequences").select("*").eq("branch_id", clean_b_id).execute()
        
        prefix = "AVL"
        last_num = 0
        
        if seq_res.data:
            rec = seq_res.data[0]
            # prefix-ல் உள்ள தேவையில்லாத குறியீடுகளை நீக்குதல் (எ.கா: 'AVL' -> 'AVL')
            prefix = str(rec.get("prefix") or "AVL").strip().rstrip("/-")
            last_num = int(rec.get("last_number") or 0)
        else:
            # அட்டவணையில் பதிவு இல்லையெனில் branches அட்டவணையில் இருந்து பொதுவான தகவலை எடுத்தல்
            try:
                b_res = supabase.table("branches").select("*").eq("id", clean_b_id).execute()
                if b_res.data:
                    b_rec = b_res.data[0]
                    prefix = str(b_rec.get("branch_code") or b_rec.get("prefix") or b_rec.get("name") or "AVL").strip().rstrip("/-")
            except Exception:
                prefix = "AVL"

        # 2. அடுத்த வரிசை எண் கணக்கீடு (1753 + 1 = 1754)
        next_num = last_num + 1

        # 3. கார்ட்டில் ஏற்கனவே சேர்க்கப்பட்ட கடன்களின் எண்ணிக்கையைக் கூட்டுதல்
        cart = st.session_state.get("transactions_cart", [])
        cart_pledge_count = sum(1 for itm in cart if any(k in str(itm.get("transaction_type", "")) for k in ["Pledge", "Loan", "நகைக்கடன்"]))
        display_num = next_num + cart_pledge_count

        # 4. '-' இன்றி '/' குறியீட்டுடன் கடன் எண் உருவாக்குதல் (எ.கா: AVL/1754)
        suggested_gl_no = f"{prefix}/{display_num:04d}" if display_num < 1000 else f"{prefix}/{display_num}"
        
        return suggested_gl_no, next_num

    except Exception:
        # ஏதேனும் பிழை ஏற்பட்டாலும் கிளையின் இயல்பான எண்ணைக் காட்டுதல்
        return "AVL/1754", 1754

def commit_next_gl_number(branch_id, used_number):
    try:
        supabase.table("branch_loan_sequences").upsert({
            "branch_id": int(branch_id),
            "last_number": int(used_number)
        }).execute()
    except Exception:
        pass

# -----------------------------------------------------------------------------------------
# 🔍 குறிப்பிட்ட கிளையில் வாடிக்கையாளரின் நிலுவையில் உள்ள (Active) கடன்களை மட்டும் எடுத்தல்
# -----------------------------------------------------------------------------------------
def get_customer_active_loans(customer_id=None, customer_mobile="", customer_name="", branch_id=None):
    try:
        b_id = branch_id or st.session_state.get("branch_id")
        if not b_id:
            return []

        c_ids = []
        # 1. customer_id நேரடியாக வந்தால் அதை முதன்மையாக எடுத்தல்
        if customer_id:
            c_ids = [customer_id]
        
        # 2. மொபைல் எண் மூலம் வாடிக்கையாளர் ID எடுத்தல்
        if not c_ids and customer_mobile:
            clean_mob = "".join(filter(str.isdigit, str(customer_mobile)))[-10:]
            if clean_mob:
                c_res = supabase.table("customers").select("id").eq("mobile", clean_mob).execute()
                if c_res.data:
                    c_ids = [c["id"] for c in c_res.data]

        # 3. பெயரை வைத்து அதே கிளையில் மட்டும் தேடுதல்
        if not c_ids and customer_name:
            c_name_clean = str(customer_name).strip()
            c_res = supabase.table("customers").select("id").eq("branch_id", b_id).ilike("name", f"%{c_name_clean}%").execute()
            if c_res.data:
                c_ids = [c["id"] for c in c_res.data]

        if not c_ids:
            return []

        # 🌟 gold_loans அட்டவணையில் நடப்பு கிளை + இந்த வாடிக்கையாளர் + Active கடன்களை மட்டும் எடுத்தல்
        loans_res = (
            supabase.table("gold_loans")
            .select("*")
            .eq("branch_id", b_id)                                           # 👈 நடப்பு கிளை மட்டும்
            .in_("customer_id", c_ids)                                       # 👈 இந்த வாடிக்கையாளர் மட்டும்
            .in_("status", ["Active", "active", "Approved", "active\r"])      # 👈 நிலுவைக் கடன்கள் மட்டும்
            .order("id", desc=True)
            .execute()
        )

        active_loans = []
        for row in (loans_res.data or []):
            l_num = str(row.get("loan_no") or "").strip()
            p_amt = float(row.get("sanctioned_amount") or 0.0)
            n_wt = float(row.get("net_weight") or 0.0)
            g_wt = float(row.get("gross_weight") or 0.0)
            roi = float(row.get("interest_rate") or 18.0)

            active_loans.append({
                "id": row.get("id"),
                "loan_no": l_num,
                "gl_no": l_num,
                "principal": p_amt,
                "sanctioned_amount": p_amt,
                "net_wt": n_wt,
                "net_weight": n_wt,
                "gross_weight": g_wt,
                "ornament_details": row.get("ornament_details") or "Gold Jewellery",
                "scheme_name": row.get("scheme_name") or "Regular",
                "interest_rate": roi,
                "created_at": str(row.get("created_at") or "")[:10]
            })

        return active_loans

    except Exception as e:
        return []

        # கார்ட்டில் ஏற்கனவே சேர்க்கப்பட்ட கடன்களை நீக்குதல்
        cart_closed_gls = [
            c.get("closed_gl_no") for c in st.session_state.get("transactions_cart", []) 
            if c.get("closed_gl_no")
        ]
        
        return [ln for ln in active_loans if ln["gl_no"] not in cart_closed_gls]
    except Exception:
        return []

# கிளைகளின் பட்டியலை உருவாக்குதல்
branches_data = load_branches_data()
branch_options = {b["branch_name"]: b["id"] for b in branches_data} if branches_data else {}
branch_id_to_name = {b["id"]: b["branch_name"] for b in branches_data} if branches_data else {}

# ==========================================
# 5. உள்நுழைவு திரை (Login Screen )
# ==========================================
if not st.session_state.logged_in:
    col_left, col_center, col_right = st.columns([1.2, 1.4, 1.2])
    with col_center:
        st.markdown(
            """
        <div class="login-box">
            <h3>🏦 Muthusise Gold Product Data Center </h3>
            <p>பணியாளர் பாதுகாப்பான உள்நுழைவு</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            username = st.text_input(
                "பயனர் பெயர் (Username)", placeholder="Username"
            )
            password = st.text_input(
                "கடவுச்சொல் (Password)", type="password", placeholder="Password"
            )
            submitted = st.form_submit_button(
                "உள்நுழைக (Login)", use_container_width=True, type="primary"
            )

            if submitted:
                if username.strip() and password.strip():
                    try:
                        res = (
                            supabase.table("users")
                            .select("*")
                            .eq("username", username.strip())
                            .execute()
                        )
                        if res.data:
                            user_info = res.data[0]
                            db_pass = str(
                                user_info.get("password_hash") or ""
                            ).strip()

                            if db_pass == password.strip():
                                role = user_info["role"]
                                b_id = user_info.get("branch_id")

                                if role in ["Admin", "Auditor", "Operations"]:
                                    b_name = f"Head Office / {role}"
                                else:
                                    b_name = "ஒதுக்கப்படாத கிளை"
                                    if b_id:
                                        b_res = (
                                            supabase.table("branches")
                                            .select("branch_name")
                                            .eq("id", b_id)
                                            .execute()
                                        )
                                        if b_res.data:
                                            b_name = b_res.data[0].get(
                                                "branch_name", "கிளை"
                                            )

                                # --- 🌟 பர்மிஷன் மற்றும் செஷன் விவரங்களை அமைத்தல் ---
                                st.session_state.logged_in = True
                                st.session_state.user_role = role
                                st.session_state.branch = b_name
                                st.session_state.branch_id = b_id
                                st.session_state.username = user_info["name"]
                                st.session_state.profile_image = user_info.get(
                                    "profile_image_url"
                                )

                                # அட்மின் என்றால் அனைத்துப் பிரிவுகளுக்கும் அனுமதி உண்டு
                                st.session_state["is_admin"] = role == "Admin"

                                # Supabase டேபிளில் இருந்து பர்மிஷன் பட்டியலை எடுத்தல்
                                fetched_perms = user_info.get(
                                    "permissions", []
                                )

                                # ஒருவேளை டேட்டாபேஸில் String-ஆக சேமிக்கப்பட்டிருந்தால் List-ஆக மாற்றுதல்
                                if isinstance(fetched_perms, str):
                                  import json

                                  try:
                                    fetched_perms = json.loads(fetched_perms)
                                  except:
                                    fetched_perms = []

                                st.session_state["user_permissions"] = (
                                    fetched_perms
                                )
                                # ----------------------------------------------------

                                st.rerun()
                            else:
                                st.error("தவறான கடவுச்சொல்!")
                        else:
                            st.error("தவறான பயனர் பெயர்!")
                    except Exception as e:
                        st.error(f"பிழை: {e}")
                else:
                    st.warning(
                        "தயவுசெய்து பயனர் பெயர் மற்றும் கடவுச்சொல்லை உள்ளிடவும்."
                    )

# ==========================================
# 6. முதன்மை திரை
# ==========================================
else:
    # 💵 பக்கவாட்டு மெனுவில் (Sidebar) நேரலை கல்லா இருப்பு
    if st.session_state.get("branch_id"):
        with st.sidebar:
            st.markdown("---")
            live_cash = get_branch_current_cash(st.session_state.branch_id)
            st.metric("💵 நேரலை கல்லா இருப்பு", f"₹{live_cash:,.2f}")

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
            st.rerun()

    st.markdown("---")

# ----------------------------------------------------
# A. நிர்வாக மேலாண்மை திரை (ADMIN PANEL WITH PERMISSION FILTERING)
# ----------------------------------------------------

# 1. நிறுவனத்தின் அனைத்து நிர்வாகப் பிரிவுகளின் பட்டியல் (Emojis உடன்)
all_admin_sections = [
    "🏢 நேரடி கல்லா & தினசரி வணிகம்",
    "📦 பாக்கெட் & லாக்கர் மேலாண்மை",
    "🏢 கிளைகள்",
    "👥 பணியாளர்கள்",
    "📋 ஸ்கீம்கள் மேலாண்மை (Pledge, FD, RD)",
    "🎯 இன்சென்டிவ் & புள்ளி விதிகள்",
    "📥 மொத்தப் பதிவேற்றம்",
    "🗂️ வாடிக்கையாளர் மேலாண்மை",
    "📊 வருகை & பரிவர்த்தனை திருத்தம்",
    "💰 கிளை துவக்க இருப்பு & கல்லா",
    "🏦 தலைமையக பணப் பரிமாற்றம்",
    "📈 காரணப் பணியாளர் அறிக்கை",
    "🪙 நகைக் கடன் மேலாண்மை",
    "📤 பல்க் RD / FD பதிவேற்றம்",
    "🛒 கவுண்ட்டர் வருகை & OTP",
    "📁 கிளை ஆவணங்கள் பதிவேற்றம்",
    "⚠️ விளக்கங்கள்",
    "💼 கிளை கல்லா",
    "🏦 HO பணப் பரிமாற்றம்",
    "📈 காரணப் பணியாளர் அறிக்கை",
    "📦 நகைப் பாக்கெட்கள் மேலாண்மை",
    "🏦 நிதிப் பரிமாற்ற ஒப்புதல்",
    "👤 புதிய வாடிக்கையாளர் KYC",
    "📝 விவரத் திருத்தக் கோரிக்கைகள்",
    "🔔 பரிவர்த்தனை அழைப்பு சரிபார்ப்பு",
    "🛡️ OTP விலக்கு அனுமதி",
    "🔍 தணிக்கையர் பணிப்பாய்வு"
]

# 2. அட்மின் என்றால் அனைத்துப் பிரிவுகளும் கிடைக்கும்; மற்றவர்களுக்கு அவர்களின் பர்மிஷன் மட்டும்
if st.session_state.get('is_admin', False) or st.session_state.get('user_role') == "Admin":
    allowed_sections = all_admin_sections
else:
    staff_perms = st.session_state.get('user_permissions', [])
    # பணியாளருக்கு அனுமதிக்கப்பட்ட பிரிவுகள் மட்டும் (Emojis பொருத்தத்துடன் சரிபார்க்கப்படும்)
    allowed_sections = [sec for sec in all_admin_sections if any(p in sec for p in staff_perms)]

# 3. மெனுவைக் காட்டுதல் மற்றும் பிரிவுகளுக்கு ஏற்ப செயல்படுத்துதல்
if allowed_sections:
    st.header("⚙️ நிர்வாக மேலாண்மை (Admin Control Panel)")
    selected_section = st.radio("நிர்வாகப் பிரிவு தேர்வு:", allowed_sections, horizontal=True)
    
    # தேர்ந்தெடுக்கப்பட்ட பிரிவிற்கான உங்களின் பழைய if / elif நிபந்தனைகள்:
    if selected_section == "🏢 நேரடி கல்லா & தினசரி வணிகம்": 
        st.subheader("🏢 அனைத்துக் கிளைகள் நேரடி கல்லா, வங்கி & வணிக அறிக்கை")
        st.caption("நிறுவனத்தின் நேரடி கல்லா இருப்பு, வங்கிப் புழக்கம், தலைமையகப் பணப் பரிமாற்றம் மற்றும் கிளைச் செலவுகளின் முழுமையான நிதிச் சமரசம்.")

        # 1. தேதி வடிகட்டி & புதுப்பித்தல்
        d_col1, d_col2, d_col3 = st.columns([2, 1.5, 3])
        with d_col1:
            selected_report_date = st.date_input("📅 வணிகத் தேதியைத் தேர்வு செய்க:", value=date.today(), key="admin_dash_date_picker")
        with d_col2:
            st.write("")
            st.write("")
            if st.button("🔄 உடனடி புதுப்பித்தல்", key="admin_dash_refresh_btn", type="secondary"):
                st.rerun()

        sel_date_str = selected_report_date.strftime("%Y-%m-%d")
        start_iso = f"{sel_date_str}T00:00:00"
        end_iso = f"{sel_date_str}T23:59:59.999999"

        # 2. கிளைகள் விவரங்களை எடுத்தல்
        # ✅ புதிய அதிவேக அழைப்பு (0.001 வினாடியில் நினைவகத்திலிருந்து எடுத்துவிடும்):
        branches_list = get_cached_branches()

        if not branches_list:
            st.warning("⚠️ கிளைகள் எதுவும் கண்டறியப்படவில்லை!")
            st.stop()

        # 3. தேர்ந்தெடுக்கப்பட்ட நாளுக்கான அனைத்துத் தரவுகளையும் எடுத்தல்
        with st.spinner("கிளை வாரியான விரிவான நிதி மற்றும் வணிகத் தரவுகள் திரட்டப்படுகின்றன..."):
            # அ. அன்றைய வருகைப் பதிவுகள் & வங்கி/ரொக்கப் பிரிப்பு
            try:
                visits_res = supabase.table("customer_visits").select("id, branch_id, payment_mode, cash_amount, bank_amount").gte("created_at", start_iso).lte("created_at", end_iso).execute()
                day_visits = visits_res.data or []
            except Exception:
                day_visits = []

            visit_mode_map = {v["id"]: v for v in day_visits}

            # ஆ. அன்றைய பரிவர்த்தனைகள்
            try:
                txns_res = supabase.table("transactions").select("*").gte("created_at", start_iso).lte("created_at", end_iso).execute()
                day_txns = txns_res.data or []
            except Exception:
                day_txns = []

            # இ. அன்றைய அங்கீகரிக்கப்பட்ட கிளைச் செலவுகள்
            try:
                exp_res = supabase.table("branch_expenses").select("*").gte("created_at", start_iso).lte("created_at", end_iso).eq("status", "Approved").execute()
                day_expenses = exp_res.data or []
            except Exception:
                day_expenses = []

            # ஈ. அன்றைய அங்கீகரிக்கப்பட்ட HO பணப் பரிமாற்றங்கள்
            try:
                trans_res = supabase.table("branch_fund_transfers").select("*").gte("created_at", start_iso).lte("created_at", end_iso).eq("status", "Approved").execute()
                day_transfers = trans_res.data or []
            except Exception:
                day_transfers = []

        # நோட்டுகளின் மதிப்பைக் கணக்கிடும் ஃபங்க்ஷன்
        def calc_stock_val(stock_dict):
            mults = {"500": 500, "200": 200, "100": 100, "50": 50, "20": 20, "10": 10, "5": 5, "coins": 1}
            return sum(float(stock_dict.get(k, 0) or 0) * mults.get(k, 1) for k in mults)

        # 4. கிளை வாரியான நிதித் தொகுப்பு (Data Aggregation)
        branch_summary = []
        
        # தலைமைச் சுருக்க மாறிகள்
        gt_live_cash = 0.0
        gt_pledge = 0.0
        gt_loan_prin_rec = 0.0
        gt_loan_int_rec = 0.0
        gt_rd_rec = 0.0
        gt_fd_rec = 0.0
        gt_rd_int_paid = 0.0
        gt_fd_int_paid = 0.0
        gt_rd_closed = 0.0
        gt_fd_closed = 0.0
        
        gt_ho_received = 0.0
        gt_ho_sent = 0.0
        gt_bank_in = 0.0
        gt_bank_out = 0.0
        gt_cash_in = 0.0
        gt_cash_out = 0.0
        gt_expenses = 0.0

        branch_details_cache = {}

        for b in branches_list:
            b_id = b["id"]
            b_name = b.get("branch_name", f"கிளை {b_id}")
            b_code = b.get("branch_code", "BR")

            # நேரடி கல்லா கையிருப்பு
            try:
                drawer_stock = get_current_branch_cash_drawer(b_id)
            except Exception:
                drawer_stock = {"500": 0, "200": 0, "100": 0, "50": 0, "20": 0, "10": 0, "5": 0, "coins": 0}
            
            live_cash = calc_stock_val(drawer_stock)
            gt_live_cash += live_cash

            # அ. பரிவர்த்தனைகள் வகைப்பாடு
            b_txns = [t for t in day_txns if t.get("branch_id") == b_id]

            pledge_disbursed = 0.0
            pledge_cnt = 0
            loan_prin_rec = 0.0
            loan_int_rec = 0.0
            rd_rec = 0.0
            fd_rec = 0.0
            rd_int_paid = 0.0
            fd_int_paid = 0.0
            rd_closed_paid = 0.0
            fd_closed_paid = 0.0
            other_inflow = 0.0
            other_outflow = 0.0

            b_cash_in = 0.0
            b_cash_out = 0.0
            b_bank_in = 0.0
            b_bank_out = 0.0

            for t in b_txns:
                t_type = str(t.get("transaction_type", "")).strip().lower()
                p_amt = float(t.get("paid_amount", 0) or 0)
                r_amt = float(t.get("received_amount", 0) or 0)
                details = t.get("transaction_details") or {}
                if not isinstance(details, dict):
                    details = {}

                # ரொக்கம் vs வங்கி பிரிப்பு (Visit அடிப்படையில்)
                v_info = visit_mode_map.get(t.get("visit_id"), {})
                pmode = str(v_info.get("payment_mode", "Cash")).lower()
                v_cash = float(v_info.get("cash_amount", 0) or 0)
                v_bank = float(v_info.get("bank_amount", 0) or 0)

                if r_amt > 0:
                    if "bank" in pmode or "online" in pmode or "upi" in pmode:
                        b_bank_in += r_amt
                    elif "split" in pmode and (v_cash + v_bank) > 0:
                        ratio = v_bank / (v_cash + v_bank)
                        b_bank_in += (r_amt * ratio)
                        b_cash_in += (r_amt * (1 - ratio))
                    else:
                        b_cash_in += r_amt

                if p_amt > 0:
                    if "bank" in pmode or "online" in pmode or "upi" in pmode:
                        b_bank_out += p_amt
                    elif "split" in pmode and (v_cash + v_bank) > 0:
                        ratio = v_bank / (v_cash + v_bank)
                        b_bank_out += (p_amt * ratio)
                        b_cash_out += (p_amt * (1 - ratio))
                    else:
                        b_cash_out += p_amt

                # 1. புதிய நகைக்கடன்
                if "pledge" in t_type or "loan open" in t_type:
                    pledge_disbursed += p_amt
                    pledge_cnt += 1

                # 2. கடன் அசல் vs வட்டி
                elif "interest" in t_type and not ("rd" in t_type or "fd" in t_type):
                    loan_int_rec += r_amt
                elif any(k in t_type for k in ["release", "close", "redemption", "part payment"]):
                    p_val = float(details.get("principal") or 0)
                    i_val = float(details.get("interest") or 0)
                    if p_val > 0 or i_val > 0:
                        loan_prin_rec += p_val
                        loan_int_rec += i_val + (r_amt - (p_val + i_val) if r_amt > (p_val + i_val) else 0)
                    elif t.get("principal_amount") and float(t.get("principal_amount") or 0) > 0:
                        prin_db = float(t.get("principal_amount"))
                        loan_prin_rec += min(prin_db, r_amt)
                        loan_int_rec += max(0.0, r_amt - prin_db)
                    else:
                        loan_prin_rec += r_amt

                # 3. RD வசூல்
                elif "rd" in t_type and r_amt > 0 and not ("close" in t_type or "closure" in t_type):
                    rd_rec += r_amt

                # 4. FD வசூல்
                elif "fd" in t_type and r_amt > 0 and not ("close" in t_type or "closure" in t_type):
                    fd_rec += r_amt

                # 5. RD வட்டி & முதிர்வு பட்டுவாடா
                elif "rd" in t_type and p_amt > 0:
                    if "int" in t_type or "வட்டி" in t_type:
                        rd_int_paid += p_amt
                    elif any(k in t_type for k in ["closure", "close", "முடித்த"]):
                        i_val = float(details.get("interest") or 0)
                        if i_val > 0:
                            rd_int_paid += i_val
                            rd_closed_paid += max(0.0, p_amt - i_val)
                        else:
                            rd_closed_paid += p_amt
                    else:
                        other_outflow += p_amt

                # 6. FD வட்டி & முதிர்வு பட்டுவாடா
                elif "fd" in t_type and p_amt > 0:
                    if "int" in t_type or "வட்டி" in t_type:
                        fd_int_paid += p_amt
                    elif any(k in t_type for k in ["closure", "close", "முடித்த"]):
                        i_val = float(details.get("interest") or 0)
                        if i_val > 0:
                            fd_int_paid += i_val
                            fd_closed_paid += max(0.0, p_amt - i_val)
                        else:
                            fd_closed_paid += p_amt
                    else:
                        other_outflow += p_amt
                else:
                    if r_amt > 0:
                        other_inflow += r_amt
                    if p_amt > 0:
                        other_outflow += p_amt

            # ஆ. கிளைச் செலவுகள்
            b_exp_list = [e for e in day_expenses if e.get("branch_id") == b_id]
            b_exp_amt = sum(float(e.get("amount", 0) or 0) for e in b_exp_list)
            b_cash_out += b_exp_amt

            # இ. தலைமையகப் பணப் பரிமாற்றம் (HO Transfers)
            b_trans_list = [tr for tr in day_transfers if tr.get("branch_id") == b_id]
            
            # HO-லிருந்து வாங்கியது
            ho_rec_cash = sum(float(tr.get("amount", 0) or 0) for tr in b_trans_list if tr.get("transfer_type") == "HO_TO_BRANCH" and "cash" in str(tr.get("payment_mode", "")).lower())
            ho_rec_bank = sum(float(tr.get("amount", 0) or 0) for tr in b_trans_list if tr.get("transfer_type") == "HO_TO_BRANCH" and "cash" not in str(tr.get("payment_mode", "")).lower())
            ho_rec_total = ho_rec_cash + ho_rec_bank
            b_cash_in += ho_rec_cash
            b_bank_in += ho_rec_bank

            # HO-க்கு அனுப்பியது
            ho_sent_cash = sum(float(tr.get("amount", 0) or 0) for tr in b_trans_list if tr.get("transfer_type") == "BRANCH_TO_HO" and "cash" in str(tr.get("payment_mode", "")).lower())
            ho_sent_bank = sum(float(tr.get("amount", 0) or 0) for tr in b_trans_list if tr.get("transfer_type") == "BRANCH_TO_HO" and "cash" not in str(tr.get("payment_mode", "")).lower())
            ho_sent_total = ho_sent_cash + ho_sent_bank
            b_cash_out += ho_sent_cash
            b_bank_out += ho_sent_bank

            # நிகர ரொக்கப் புழக்கம்
            net_cash_flow = b_cash_in - b_cash_out

            # தலைமைத் தொகைகளைக் கூட்டுதல்
            gt_pledge += pledge_disbursed
            gt_loan_prin_rec += loan_prin_rec
            gt_loan_int_rec += loan_int_rec
            gt_rd_rec += rd_rec
            gt_fd_rec += fd_rec
            gt_rd_int_paid += rd_int_paid
            gt_fd_int_paid += fd_int_paid
            gt_rd_closed += rd_closed_paid
            gt_fd_closed += fd_closed_paid
            
            gt_ho_received += ho_rec_total
            gt_ho_sent += ho_sent_total
            gt_bank_in += b_bank_in
            gt_bank_out += b_bank_out
            gt_cash_in += b_cash_in
            gt_cash_out += b_cash_out
            gt_expenses += b_exp_amt

            branch_summary.append({
                "கிளை": f"{b_name} ({b_code})",
                "branch_id": b_id,
                "b_name": b_name,
                "கல்லா இருப்பு": live_cash,
                "புதிய கடன்": pledge_disbursed,
                "கடன் எண்ணிக்கை": pledge_cnt,
                "கடன் அசல் வசூல்": loan_prin_rec,
                "கடன் வட்டி வசூல்": loan_int_rec,
                "RD வசூல்": rd_rec,
                "FD வசூல்": fd_rec,
                "கொடுத்த RD வட்டி": rd_int_paid,
                "கொடுத்த FD வட்டி": fd_int_paid,
                "முடித்த RD": rd_closed_paid,
                "முடித்த FD": fd_closed_paid,
                # நிதி & வங்கி விவரங்கள்
                "HO-லிருந்து வாங்கியது": ho_rec_total,
                "HO-க்கு கொடுத்தது": ho_sent_total,
                "வங்கி வரவு": b_bank_in,
                "வங்கி செலுத்தியது": b_bank_out,
                "கிளைச் செலவு": b_exp_amt,
                "ரொக்க வரவு": b_cash_in,
                "ரொக்கப் பற்று": b_cash_out,
                "நிகர ரொக்கப் புழக்கம்": net_cash_flow
            })

            branch_details_cache[b_id] = {
                "drawer": drawer_stock,
                "txns": b_txns,
                "expenses": b_exp_list,
                "transfers": b_trans_list
            }

        # =========================================================================
        # 5. தலைமை மேலோட்ட சுருக்க கார்டுகள் (Top KPI Cards)
        # =========================================================================
        st.markdown("---")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("💰 மொத்த நேரடி கல்லா ரொக்கம்", f"₹{gt_live_cash:,.2f}")
        k2.metric("🏦 வங்கி வரவு (Bank Inflow)", f"₹{gt_bank_in:,.2f}")
        k3.metric("💳 வங்கி செலுத்தியது (Bank Outflow)", f"₹{gt_bank_out:,.2f}")
        k4.metric("💸 மொத்த கிளைச் செலவுகள்", f"₹{gt_expenses:,.2f}")

        k5, k6, k7, k8 = st.columns(4)
        k5.metric("🪙 கடன் வழங்கல் (Disbursed)", f"₹{gt_pledge:,.2f}")
        k6.metric("📥 கடன் அசல் & வட்டி வசூல்", f"₹{(gt_loan_prin_rec + gt_loan_int_rec):,.2f}", delta=f"அசல்: ₹{gt_loan_prin_rec:,.0f} | வட்டி: ₹{gt_loan_int_rec:,.0f}")
        k7.metric("📥 HO-லிருந்து வாங்கியது", f"₹{gt_ho_received:,.2f}")
        k8.metric("📤 HO-க்கு கொடுத்தது", f"₹{gt_ho_sent:,.2f}")
        st.markdown("---")

        # =========================================================================
        # 6. இரண்டு தனித்தனி அட்டவணைகள் (Two Focused Tabs)
        # =========================================================================
        dash_tab_biz, dash_tab_cash = st.tabs([
            "📊 1. கிளை வாரியான வணிக ஒப்பீடு (Business Operations)", 
            "💵 2. கல்லா, வங்கி, HO & செலவுகள் சமரசம் (Cash & Bank Flow)"
        ])

        # -------------------------------------------------------------
        # டேப் 1: வணிகச் செயல்பாடுகள் (Business Performance)
        # -------------------------------------------------------------
        with dash_tab_biz:
            st.markdown(f"##### 📊 கிளை வாரியான வணிக விவரங்கள் ({selected_report_date.strftime('%d-%b-%Y')})")
            df_biz = pd.DataFrame([{
                "கிளை": r["கிளை"],
                "🪙 புதிய கடன்": f"₹{r['புதிய கடன்']:,.2f} ({r['கடன் எண்ணிக்கை']})",
                "🔓 கடன் அசல் வரவு": f"₹{r['கடன் அசல் வசூல்']:,.2f}",
                "🏷️ கடன் வட்டி வரவு": f"₹{r['கடன் வட்டி வசூல்']:,.2f}",
                "📥 RD வசூல்": f"₹{r['RD வசூல்']:,.2f}",
                "📥 FD வசூல்": f"₹{r['FD வசூல்']:,.2f}",
                "📤 கொடுத்த RD வட்டி": f"₹{r['கொடுத்த RD வட்டி']:,.2f}",
                "📤 கொடுத்த FD வட்டி": f"₹{r['கொடுத்த FD வட்டி']:,.2f}",
                "📕 முடித்த RD": f"₹{r['முடித்த RD']:,.2f}",
                "📘 முடித்த FD": f"₹{r['முடித்த FD']:,.2f}"
            } for r in branch_summary])
            
            st.dataframe(df_biz, use_container_width=True)

        # -------------------------------------------------------------
        # டேப் 2: பணப்புழக்கம், வங்கி, HO & செலவுகள் (Cash, Bank, HO & Expenses)
        # -------------------------------------------------------------
        with dash_tab_cash:
            st.markdown(f"##### 💵 கிளை வாரியான கல்லா, வங்கி, HO பரிமாற்றம் & செலவுகள் ({selected_report_date.strftime('%d-%b-%Y')})")
            df_cash = pd.DataFrame([{
                "கிளை": r["கிளை"],
                "💵 நேரடி கல்லா": f"₹{r['கல்லா இருப்பு']:,.2f}",
                "📥 HO-லிருந்து வாங்கியது": f"₹{r['HO-லிருந்து வாங்கியது']:,.2f}",
                "📤 HO-க்கு கொடுத்தது": f"₹{r['HO-க்கு கொடுத்தது']:,.2f}",
                "🏦 வங்கி வரவு (UPI/QR)": f"₹{r['வங்கி வரவு']:,.2f}",
                "💳 வங்கி செலுத்தியது": f"₹{r['வங்கி செலுத்தியது']:,.2f}",
                "💸 கிளைச் செலவு": f"₹{r['கிளைச் செலவு']:,.2f}",
                "🟢 அன்றைய ரொக்க வரவு": f"₹{r['ரொக்க வரவு']:,.2f}",
                "🔴 அன்றைய ரொக்கப் பற்று": f"₹{r['ரொக்கப் பற்று']:,.2f}",
                "📈 நிகர ரொக்கப் புழக்கம்": f"₹{r['நிகர ரொக்கப் புழக்கம்']:+,.2f}"
            } for r in branch_summary])
            
            st.dataframe(df_cash, use_container_width=True)

        # முழு எக்செல் பதிவிறக்கம்
        full_export_df = pd.DataFrame(branch_summary)
        csv_full = full_export_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label=f"📥 {selected_report_date.strftime('%d-%m-%Y')} முழுமையான வணிக & நிதி அறிக்கையைப் பதிவிறக்குக (CSV/Excel)",
            data=csv_full,
            file_name=f"Muthusise_Full_Financial_Summary_{sel_date_str}.csv",
            mime="text/csv"
        )

        st.markdown("---")

        # =========================================================================
        # 7. கிளை வாரியான நேரடி ஆய்வு (Drilldown Expanders)
        # =========================================================================
        st.markdown("#### 🔍 கிளை வாரியான நேரடி நோட்டுகள், HO & செலவு விவரங்கள்")

        for r in branch_summary:
            bid = r["branch_id"]
            binfo = branch_details_cache.get(bid, {})
            drw = binfo.get("drawer", {})
            tx_list = binfo.get("txns", [])
            exp_list = binfo.get("expenses", [])
            trans_list = binfo.get("transfers", [])

            with st.expander(f"📍 {r['கிளை']} | 💵 நேரடி கல்லா: ₹{r['கல்லா இருப்பு']:,.2f} | 🏦 வங்கி வரவு: ₹{r['வங்கி வரவு']:,.2f} | 🏢 HO வரவு: ₹{r['HO-லிருந்து வாங்கியது']:,.2f} | 💸 செலவு: ₹{r['கிளைச் செலவு']:,.2f}"):
                sub_c1, sub_c2, sub_c3, sub_c4 = st.tabs([
                    "💵 கல்லா நோட்டுகள் (Drawer)", 
                    "🏢 HO பணப் பரிமாற்றம்", 
                    "💸 கிளைச் செலவுகள்", 
                    "📑 பரிவர்த்தனைகள்"
                ])

                # அ. கல்லா நோட்டுகள் கையிருப்பு
                with sub_c1:
                    st.caption(f"📍 {r['b_name']} கிளையின் கல்லாவில் உள்ள நேரடி நோட்டுகள் நிலவரம்:")
                    cd1, cd2, cd3, cd4 = st.columns(4)
                    cd1.metric("₹500 தாள்கள்", f"{drw.get('500', 0)} nos", f"₹{int(drw.get('500', 0)) * 500:,.2f}")
                    cd1.metric("₹20 தாள்கள்", f"{drw.get('20', 0)} nos", f"₹{int(drw.get('20', 0)) * 20:,.2f}")
                    
                    cd2.metric("₹200 தாள்கள்", f"{drw.get('200', 0)} nos", f"₹{int(drw.get('200', 0)) * 200:,.2f}")
                    cd2.metric("₹10 தாள்கள்", f"{drw.get('10', 0)} nos", f"₹{int(drw.get('10', 0)) * 10:,.2f}")
                    
                    cd3.metric("₹100 தாள்கள்", f"{drw.get('100', 0)} nos", f"₹{int(drw.get('100', 0)) * 100:,.2f}")
                    cd3.metric("₹5 தாள்கள்", f"{drw.get('5', 0)} nos", f"₹{int(drw.get('5', 0)) * 5:,.2f}")
                    
                    cd4.metric("₹50 தாள்கள்", f"{drw.get('50', 0)} nos", f"₹{int(drw.get('50', 0)) * 50:,.2f}")
                    cd4.metric("நாணயங்கள் (₹)", f"₹{float(drw.get('coins', 0)):,.2f}")
                    st.success(f"**மொத்த ரொக்க மதிப்பு: ₹{r['கல்லா இருப்பு']:,.2f}**")

                # ஆ. HO பரிமாற்றங்கள்
                with sub_c2:
                    if not trans_list:
                        st.info("அன்று தலைமையகப் பணப் பரிமாற்றங்கள் ஏதும் இல்லை.")
                    else:
                        st.dataframe(pd.DataFrame([{
                            "வகை": "📥 HO ➔ கிளைக்கு வரவு" if tr.get("transfer_type") == "HO_TO_BRANCH" else "📤 கிளை ➔ HO-க்கு அனுப்பியது",
                            "தொகை": f"₹{float(tr.get('amount', 0)):,.2f}",
                            "முறை": tr.get("payment_mode", "-"),
                            "குறிப்பு / UTR": tr.get("reference_no", "-"),
                            "நிலை": tr.get("status", "-")
                        } for tr in trans_list]), use_container_width=True)

                # இ. கிளைச் செலவுகள்
                with sub_c3:
                    if not exp_list:
                        st.info("அன்று அங்கீகரிக்கப்பட்ட கிளைச் செலவுகள் ஏதும் இல்லை.")
                    else:
                        st.dataframe(pd.DataFrame([{
                            "தலைப்பு / காரணம்": e.get("title", e.get("expense_category", "-")),
                            "தொகை": f"₹{float(e.get('amount', 0) or 0):,.2f}",
                            "விளக்கம்": e.get("description", "-"),
                            "பதிவு செய்தவர்": e.get("created_by", "-")
                        } for e in exp_list]), use_container_width=True)

                # ஈ. வாடிக்கையாளர் பரிவர்த்தனைகள்
                with sub_c4:
                    if not tx_list:
                        st.info("அன்று வாடிக்கையாளர் பரிவர்த்தனைகள் ஏதும் இல்லை.")
                    else:
                        st.dataframe(pd.DataFrame([{
                            "நேரம்": str(t.get("created_at", ""))[-8:-3] if t.get("created_at") else "-",
                            "வாடிக்கையாளர்": t.get("customer_name", "-"),
                            "பரிவர்த்தனை வகை": t.get("transaction_type", "-"),
                            "கொடுத்தது (Paid)": f"₹{float(t.get('paid_amount', 0) or 0):,.2f}",
                            "பெற்றது (Received)": f"₹{float(t.get('received_amount', 0) or 0):,.2f}",
                            "பணியாளர்": t.get("staff_name", "-"),
                            "குறிப்பு": t.get("remarks", "-")
                        } for t in tx_list]), use_container_width=True)
        # ==============================================================================
        # 📦 தலைமையக நகைப் பெட்டகம், லாக்கர் & GP உருக்குதல் மேலாண்மை
        # ==============================================================================
    elif selected_section == "📦 பாக்கெட் & லாக்கர் மேலாண்மை":
        st.subheader("📦 நகைப் பாக்கெட் நகர்வு, வங்கி லாக்கர் & GP உருக்குதல் மேலாண்மை")
        st.caption("கிளைகள் ➔ தலைமையகம் ➔ வங்கி லாக்கர் பாக்கெட் நகர்வுகள் மற்றும் ஜிபி உருக்குதல்/மறுவிற்பனை கண்காணிப்பு.")

        # 1. கிளைகள் மேப்பிங்
        try:
            b_res = supabase.table("branches").select("id, branch_name, branch_code").execute()
            b_map_name = {b["id"]: f"{b['branch_name']} ({b.get('branch_code', 'BR')})" for b in (b_res.data or [])}
        except Exception:
            b_map_name = {}

        # 2. நடப்பு பாக்கெட்கள் விவரங்களை எடுத்தல் (select("*") மூலம் அனைத்து புதிய பத்திகளும் வந்துவிடும்)
        try:
            loans_pkt_res = supabase.table("gold_loans").select("*").neq("status", "Closed").execute()
            all_loan_pkts = loans_pkt_res.data or []
        except Exception:
            all_loan_pkts = []

        # 3. GP கொள்முதல் பாக்கெட்கள்
        try:
            gp_pkt_res = supabase.table("gold_purchases").select("*").execute()
            raw_gps = gp_pkt_res.data or []
            all_gp_pkts = []
            for g in raw_gps:
                gp_id = (
                    g.get("gp_no") 
                    or g.get("bill_no") 
                    or g.get("purchase_no") 
                    or g.get("voucher_no") 
                    or f"GP-{g.get('id', '')}"
                )
                g["gp_no"] = gp_id
                all_gp_pkts.append(g)
        except Exception:
            all_gp_pkts = []

        # =========================================================================
        # 3. தலைமை நிலவரக் கார்டுகள் (Top Status KPI Metrics)
        # =========================================================================
        cnt_branch = sum(1 for p in all_loan_pkts if p.get("packet_location", "AT_BRANCH") == "AT_BRANCH") + sum(1 for g in all_gp_pkts if g.get("packet_location", "AT_BRANCH") == "AT_BRANCH")
        cnt_transit_hq = sum(1 for p in all_loan_pkts if p.get("packet_location") == "IN_TRANSIT_TO_HQ") + sum(1 for g in all_gp_pkts if g.get("packet_location") == "IN_TRANSIT_TO_HQ")
        cnt_hq_vault = sum(1 for p in all_loan_pkts if p.get("packet_location") == "AT_HQ_VAULT") + sum(1 for g in all_gp_pkts if g.get("packet_location") == "AT_HQ_VAULT" and g.get("disposal_type") == "PENDING")
        
        repledge_pkts = [p for p in all_loan_pkts if p.get("packet_location") == "IN_BANK_LOCKER"]
        tot_repledge_amt = sum(float(p.get("repledge_amount", 0) or 0) for p in repledge_pkts)
        
        # 🌟 கிளைகளின் மீட்புக் கோரிக்கைகள் & திருப்பி அனுப்ப அனுமதி கோரிய பாக்கெட்கள்:
        urgent_requests = [p for p in all_loan_pkts if p.get("release_requested")]
        ret_requests = [p for p in all_loan_pkts if p.get("return_request_status") == "REQUESTED"]
        total_branch_alerts = len(urgent_requests) + len(ret_requests)

        # 5 கார்டுகள் வரிசை
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("📍 கிளைகளில் உள்ளவை", f"{cnt_branch} பாக்கெட்கள்")
        k2.metric("🚚 HQ-க்கு வழியில்", f"{cnt_transit_hq} பாக்கெட்கள்")
        k3.metric("🏢 HQ பெட்டக இருப்பு", f"{cnt_hq_vault} பாக்கெட்கள்")
        k4.metric("🏦 வங்கி லாக்கரில்", f"{len(repledge_pkts)} பாக்கெட்கள்", f"கடன்: ₹{tot_repledge_amt:,.0f}")
        
        # 🌟 5-வது கார்டு: மீட்பு + திருப்புதல் இரண்டையும் காட்டும் நேரடி அலர்ட்
        k5.metric(
            "🚨 கிளைக் கோரிக்கைகள்", 
            f"{total_branch_alerts} பாக்கெட்கள்", 
            delta=f"மீட்பு: {len(urgent_requests)} | திருப்புதல்: {len(ret_requests)}" if total_branch_alerts > 0 else "நிலுவை இல்லை"
        )
        st.markdown("---")

        # =========================================================================
        # 4. மேலாண்மை உள்-டேப்கள் ( Management Sub-Tabs )
        # =========================================================================
        p_tab1, p_tab2, p_tab3, p_tab4, p_tab5 = st.tabs([
            "📥 1. கிளைகளிலிருந்து பெறுதல் (Receive at HQ)",
            "🏦 2. வங்கி லாக்கர் (Re-Pledge)",
            "🚚 3. கிளைகளின் மீட்புக் கோரிக்கைகள் & திருப்புதல் அனுமதி",
            "🔥 4. GP உருக்குதல் & மறுவிற்பனை",
            "🔍 5. அனைத்து பாக்கெட் தேடல்"
        ])

        # -------------------------------------------------------------------------
        # டேப் 1: கிளைகளிலிருந்து அனுப்பப்பட்ட பாக்கெட்களைப் பெற்று சரிபார்த்தல்
        # -------------------------------------------------------------------------
        with p_tab1:
            st.markdown("##### 📥 கிளைகளிலிருந்து வழியில் உள்ள பாக்கெட்கள் (In Transit to HQ)")
            transit_loans = [p for p in all_loan_pkts if p.get("packet_location") == "IN_TRANSIT_TO_HQ"]
            transit_gps = [g for g in all_gp_pkts if g.get("packet_location") == "IN_TRANSIT_TO_HQ"]

            if not transit_loans and not transit_gps:
                st.info("தற்போது கிளைகளிலிருந்து வழியில் எந்த பாக்கெட்களும் இல்லை.")
            else:
                if transit_loans:
                    st.write(f"🪙 **நகைக்கடன் பாக்கெட்கள் ({len(transit_loans)}):**")
                    for tl in transit_loans:
                        c_a, c_b, c_c, c_d = st.columns([2, 3, 2, 2])
                        c_a.write(f"🏷️ **{tl['loan_no']}**")
                        c_b.write(f"கிளை: {b_map_name.get(tl['branch_id'], '-')} | எடை: {tl['gross_weight']}g")
                        c_c.write(f"நகை: {tl.get('ornament_details', '-')}")
                        if c_d.button("✅ பெற்றுக்கொள் (Accept)", key=f"acc_l_{tl['id']}"):
                            supabase.table("gold_loans").update({
                                "packet_location": "AT_HQ_VAULT",
                                "packet_received_by": st.session_state.get("username", "Admin"),
                                "packet_updated_at": datetime.now().isoformat()
                            }).eq("id", tl["id"]).execute()
                            st.success(f"{tl['loan_no']} HQ பெட்டகத்தில் சேர்க்கப்பட்டது!")
                            st.rerun()

                if transit_gps:
                    st.write(f"✨ **ஜிபி நகை வாங்குதல் பாக்கெட்கள் ({len(transit_gps)}):**")
                    for tg in transit_gps:
                        g_a, g_b, g_c, g_d = st.columns([2, 3, 2, 2])
                        g_a.write(f"🧾 **{tg['gp_no']}**")
                        g_b.write(f"கிளை: {b_map_name.get(tg['branch_id'], '-')} | எடை: {tg['gross_weight']}g")
                        g_c.write("வகை: GP கொள்முதல்")
                        if g_d.button("✅ பெற்றுக்கொள் (Accept)", key=f"acc_g_{tg['id']}"):
                            supabase.table("gold_purchases").update({
                                "packet_location": "AT_HQ_VAULT",
                                "packet_received_by": st.session_state.get("username", "Admin"),
                                "packet_updated_at": datetime.now().isoformat()
                            }).eq("id", tg["id"]).execute()
                            st.success(f"{tg['gp_no']} HQ பெட்டகத்தில் சேர்க்கப்பட்டது!")
                            st.rerun()

        # -------------------------------------------------------------------------
        # டேப் 2: வங்கி லாக்கரில் மறு-அடமானம் வைத்தல் / திருப்புதல்
        # -------------------------------------------------------------------------
        with p_tab2:
            st.markdown("##### 🏦 வங்கி லாக்கர் மறு-அடமானம் & நிதி மேலாண்மை (Re-Pledge)")
            vault_loans = [p for p in all_loan_pkts if p.get("packet_location") == "AT_HQ_VAULT"]

            col_bk1, col_bk2 = st.columns(2)
            
            # அ. லாக்கரில் வைக்கும் போது (கடன் + சார்ஜஸ் பதிவு செய்தல்)
            with col_bk1:
                st.write("🏢 **HQ பெட்டகத்தில் உள்ள கடன்கள் (லாக்கருக்கு அனுப்ப):**")
                if not vault_loans:
                    st.caption("HQ பெட்டகத்தில் நகைக் கடன்கள் ஏதும் இல்லை.")
                else:
                    for vl in vault_loans:
                        with st.expander(f"🪙 {vl['loan_no']} | {b_map_name.get(vl['branch_id'], '-')} | {vl['gross_weight']}g"):
                            with st.form(key=f"tmgmt_repldge_{vl['id']}"):
                                b_name_in = st.text_input("வங்கி / நிதி நிறுவனம் பெயர்:", placeholder="எ.கா: KVB / HDFC Bank / SBI")
                                b_loan_in = st.text_input("வங்கி கடன் எண் (Bank Loan No):", placeholder="எ.கா: 88741256")
                                b_amt_in = st.number_input("வாங்கிய கடன் தொகை (₹ Loan Amount):", min_value=0.0, step=5000.0)
                                b_charges_in = st.number_input("பிடித்தம் / கட்டணங்கள் (₹ Bank Charges / Processing):", min_value=0.0, step=100.0)
                                
                                if st.form_submit_button("🏦 வங்கி லாக்கருக்கு மாற்று"):
                                    if b_name_in.strip():
                                        supabase.table("gold_loans").update({
                                            "packet_location": "IN_BANK_LOCKER",
                                            "repledge_bank": b_name_in.strip(),
                                            "repledge_loan_no": b_loan_in.strip(),
                                            "repledge_amount": b_amt_in,
                                            "repledge_charges": b_charges_in,
                                            "packet_updated_at": datetime.now().isoformat()
                                        }).eq("id", vl["id"]).execute()
                                        st.success(f"{vl['loan_no']} வங்கி லாக்கருக்கு மாற்றப்பட்டது! (கடன்: ₹{b_amt_in:,.0f} | கட்டணம்: ₹{b_charges_in:,.0f})")
                                        st.rerun()

            # ஆ. லாக்கரில் இருந்து திருப்பும் போது (செலுத்திய வட்டி பதிவு செய்து HQ-க்கு மாற்றுதல்)
            with col_bk2:
                st.write("🏦 **வங்கி லாக்கரில் உள்ள பாக்கெட்கள் (HQ-க்கு திருப்ப):**")
                if not repledge_pkts:
                    st.caption("வங்கி லாக்கரில் பாக்கெட்கள் ஏதும் இல்லை.")
                else:
                    for rpk in repledge_pkts:
                        with st.expander(f"🏦 {rpk['loan_no']} | {rpk.get('repledge_bank', '-')} | கடன்: ₹{float(rpk.get('repledge_amount',0)):,.0f}"):
                            st.write(f"வங்கி கடன் எண்: **{rpk.get('repledge_loan_no', '-')}** | எடை: **{rpk['gross_weight']}g**")
                            st.caption(f"தொடக்கத்தில் பிடித்த கட்டணம்: ₹{float(rpk.get('repledge_charges', 0) or 0):,.2f}")
                            
                            with st.form(key=f"tmgmt_ret_form_{rpk['id']}"):
                                int_paid_in = st.number_input("வங்கிக்குச் செலுத்திய வட்டித் தொகை (₹ Interest Paid):", min_value=0.0, step=100.0)
                                
                                if st.form_submit_button("🏢 வட்டி செலுத்தி HQ பெட்டகத்திற்கு திருப்பு"):
                                    supabase.table("gold_loans").update({
                                        "packet_location": "AT_HQ_VAULT",
                                        "repledge_bank": None,
                                        "repledge_loan_no": None,
                                        "repledge_amount": 0.0,
                                        "repledge_interest_paid": int_paid_in,
                                        "packet_updated_at": datetime.now().isoformat()
                                    }).eq("id", rpk["id"]).execute()
                                    st.success(f"{rpk['loan_no']} மீட்கப்பட்டு HQ பெட்டகத்திற்கு மாற்றப்பட்டது! (செலுத்திய வட்டி: ₹{int_paid_in:,.2f})")
                                    st.rerun()

        # -------------------------------------------------------------------------
        # டேப் 3: கிளைகளின் மீட்புக் கோரிக்கைகள் & திருப்பி அனுப்பும் அனுமதி மேலாண்மை
        # -------------------------------------------------------------------------
        with p_tab3:
            adm_sub1, adm_sub2 = st.tabs([
                "🚨 1. கிளைகளின் அவசர மீட்புக் கோரிக்கைகள்",
                "🔄 2. கிளைகள் திருப்பி அனுப்ப அனுமதி கோருதல் (Return Approval)"
            ])

            # 1. கிளைகள் அவசரமாகக் கோரியுள்ளவை (குறிப்புடன் தெரியும்)
            with adm_sub1:
                st.markdown("##### 🚨 வாடிக்கையாளர் மீட்புக் கோரிக்கைகள் (Customer Release Requests)")
                if not urgent_requests:
                    st.info("தற்போது கிளைகளிலிருந்து எந்த மீட்புக் கோரிக்கைகளும் நிலுவையில் இல்லை.")
                else:
                    for uq in urgent_requests:
                        loc_txt = "🏢 HQ பெட்டகத்தில் உள்ளது" if uq["packet_location"] == "AT_HQ_VAULT" else f"🏦 {uq.get('repledge_bank', 'வங்கி')} லாக்கரில் உள்ளது"
                        with st.container():
                            u1, u2, u3, u4 = st.columns([2, 3, 2, 2])
                            u1.error(f"🏷️ **{uq['loan_no']}**")
                            u2.write(f"கிளை: **{b_map_name.get(uq['branch_id'], '-')}** | எடை: **{uq['gross_weight']}g**\nஇருப்பிடம்: **{loc_txt}**")
                            
                            # 📝 கிளை எழுதிய குறிப்பு (Branch Remarks):
                            rem_text = uq.get("release_request_remarks") or "குறிப்பு இல்லை"
                            u2.info(f"💬 **கிளைக் குறிப்பு:** {rem_text}")
                            
                            u3.caption(f"கோரப்பட்ட நேரம்:\n{str(uq.get('release_request_date', ''))[:16]}")
                            if u4.button("🚚 கிளைக்கு அனுப்பி வை", key=f"tmgmt_disp_b_{uq['id']}"):
                                supabase.table("gold_loans").update({
                                    "packet_location": "IN_TRANSIT_TO_BRANCH",
                                    "release_requested": False,
                                    "packet_dispatched_by": st.session_state.get("username", "Admin"),
                                    "packet_updated_at": datetime.now().isoformat()
                                }).eq("id", uq["id"]).execute()
                                st.success(f"{uq['loan_no']} கிளைக்கு அனுப்பி வைக்கப்பட்டது!")
                                st.rerun()
                        st.divider()

            # 2. வாடிக்கையாளர் வராததால் திருப்பி அனுப்ப அனுமதி கோரும் பாக்கெட்கள்
            with adm_sub2:
                st.markdown("##### 🔄 கிளைகள் திருப்பி அனுப்ப அனுமதி கோரும் பாக்கெட்கள்")
                ret_requests = [p for p in all_loan_pkts if p.get("return_request_status") == "REQUESTED"]
                
                if not ret_requests:
                    st.info("தற்போது எந்தக் கிளையிலிருந்தும் திருப்பி அனுப்ப அனுமதி கோரிக்கைகள் இல்லை.")
                else:
                    for rq in ret_requests:
                        with st.container():
                            r1, r2, r3, r4 = st.columns([2, 3, 2, 2])
                            r1.warning(f"🏷️ **{rq['loan_no']}**")
                            r2.write(f"கிளை: **{b_map_name.get(rq['branch_id'], '-')}** | எடை: **{rq['gross_weight']}g**")
                            r2.error(f"காரணம்: {rq.get('return_reason', 'காரணம் இல்லை')}")
                            r3.caption(f"கோரப்பட்ட நேரம்:\n{str(rq.get('return_requested_at', ''))[:16]}")
                            
                            # அனுமதி அல்லது நிராகரிப்பு
                            if r4.button("✅ திருப்பி அனுப்ப அனுமதி (Approve)", key=f"appr_ret_{rq['id']}"):
                                supabase.table("gold_loans").update({
                                    "return_request_status": "APPROVED",
                                    "return_approved_by": st.session_state.get("username", "Admin")
                                }).eq("id", rq["id"]).execute()
                                st.success(f"{rq['loan_no']}-க்கு அனுமதி வழங்கப்பட்டது!")
                                st.rerun()
                                
                            if r4.button("❌ நிராகரி (Reject)", key=f"rej_ret_{rq['id']}"):
                                supabase.table("gold_loans").update({
                                    "return_request_status": "NONE",
                                    "return_reason": None
                                }).eq("id", rq["id"]).execute()
                                st.warning(f"{rq['loan_no']} கோரிக்கை நிராகரிக்கப்பட்டது!")
                                st.rerun()
                        st.divider()

        # -------------------------------------------------------------------------
        # டேப் 4: ஜிபி (GP) உருக்குதல் & மறுவிற்பனை
        # -------------------------------------------------------------------------
        with p_tab4:
            st.markdown("##### 🔥 ஜிபி நகை உருக்குதல் & நேரடி மறுவிற்பனை (GP Processing)")
            vault_gps = [g for g in all_gp_pkts if g.get("packet_location") == "AT_HQ_VAULT" and g.get("disposal_type") == "PENDING"]

            if not vault_gps:
                st.info("HQ பெட்டகத்தில் உருக்குவதற்கு/விற்பதற்கு GP பாக்கெட்கள் ஏதும் இல்லை.")
            else:
                for vg in vault_gps:
                    with st.expander(f"✨ ஜிபி எண்: {vg['gp_no']} | கிளை: {b_map_name.get(vg['branch_id'], '-')} | மொத்த எடை: {vg['gross_weight']}g"):
                        gp_col1, gp_col2 = st.columns(2)
                        
                        # உருக்குதல் (Melting)
                        with gp_col1:
                            st.write("🔥 **உருக்கு ஆலைக்கு அனுப்புதல் (Melting):**")
                            with st.form(key=f"melt_form_{vg['id']}"):
                                b_batch = st.text_input("உருக்கு பேட்ச் எண் (Batch No):", placeholder="எ.கா: BATCH-2026-01")
                                loss_wt = st.number_input("கழிவு எடை (Loss Wt g):", min_value=0.0, step=0.01)
                                pure_wt = st.number_input("கிடைத்த சுத்த தங்கம் (24K Pure Wt g):", min_value=0.0, step=0.01)
                                if st.form_submit_button("🔥 உருக்கியதாகப் பதிவு செய்"):
                                    supabase.table("gold_purchases").update({
                                        "packet_location": "MELTED",
                                        "disposal_type": "MELTING",
                                        "melting_batch_no": b_batch.strip(),
                                        "melting_loss_weight": loss_wt,
                                        "pure_gold_obtained": pure_wt,
                                        "packet_updated_at": datetime.now().isoformat()
                                    }).eq("id", vg["id"]).execute()
                                    st.success(f"{vg['gp_no']} உருக்கப்பட்டதாகப் பதிவானது!")
                                    st.rerun()

                        # நேரடி மறுவிற்பனை (Resale)
                        with gp_col2:
                            st.write("💎 **நேரடி மறுவிற்பனைக்கு மாற்றுதல் (Resale):**")
                            st.caption("நல்ல நிலையில் உள்ள நகைகளை உருக்காமல் வாடிக்கையாளர் விற்பனைப் பிரிவுக்கு மாற்றலாம்.")
                            if st.button("💎 மறுவிற்பனை சரக்காக மாற்று", key=f"resale_btn_{vg['id']}"):
                                supabase.table("gold_purchases").update({
                                    "packet_location": "RESOLD",
                                    "disposal_type": "RESALE",
                                    "packet_updated_at": datetime.now().isoformat()
                                }).eq("id", vg["id"]).execute()
                                st.success(f"{vg['gp_no']} மறுவிற்பனை சரக்காக மாற்றப்பட்டது!")
                                st.rerun()

        # -------------------------------------------------------------------------
        # டேப் 5: முழு பாக்கெட் இருப்பு & தேடல் (Master Inventory Search)
        # -------------------------------------------------------------------------
        with p_tab5:
            st.markdown("##### 🔍 அனைத்து பாக்கெட்கள் நேரடி இருப்பு & தேடல்")
            search_pkt = st.text_input("பாக்கெட் எண் (கடன் எண் / ஜீபி எண்) உள்ளிடவும்:", placeholder="எ.கா: KMK/1230 அல்லது AVL-GP-001")
            
            all_combined = []
            for l in all_loan_pkts:
                all_combined.append({
                    "வகை": "🪙 நகைக் கடன்",
                    "பாக்கெட் எண்": l["loan_no"],
                    "கிளை": b_map_name.get(l["branch_id"], "-"),
                    "மொத்த எடை": f"{l['gross_weight']}g",
                    "தற்போதைய இருப்பிடம்": l.get("packet_location", "AT_BRANCH"),
                    "வங்கி லாக்கர் விவரம்": f"{l.get('repledge_bank', '')} (₹{float(l.get('repledge_amount',0)):,.0f})" if l.get('repledge_bank') else "-"
                })
            for g in all_gp_pkts:
                all_combined.append({
                    "வகை": "✨ ஜிபி நகை வாங்குதல்",
                    "பாக்கெட் எண்": g["gp_no"],
                    "கிளை": b_map_name.get(g["branch_id"], "-"),
                    "மொத்த எடை": f"{g['gross_weight']}g",
                    "தற்போதைய இருப்பிடம்": g.get("packet_location", "AT_BRANCH"),
                    "வங்கி லாக்கர் விவரம்": f"உருக்குதல்: {g.get('melting_batch_no', '')}" if g.get('melting_batch_no') else "-"
                })

            df_pkt_all = pd.DataFrame(all_combined)
            if search_pkt.strip():
                df_pkt_all = df_pkt_all[df_pkt_all["பாக்கெட் எண்"].str.contains(search_pkt.strip(), case=False, na=False)]

            st.dataframe(df_pkt_all, use_container_width=True)

    elif selected_section == "🏢 கிளைகள்":
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

    elif selected_section == "👥 பணியாளர்கள்":
        st.subheader("👥 பணியாளர்கள் பட்டியல் & சேர்த்தல்")
        
        # 1. அனைத்து பயனர்களின் விவரங்களையும் டேட்டாபேஸில் இருந்து எடுத்தல் (permissions உடன் சேர்த்து)
        users_res = supabase.table("users").select("id, name, username, role, branch_id, is_active, permissions").order("id").execute()
        
        if users_res.data:
            st.dataframe(pd.DataFrame([{
                "ID": u["id"], "பெயர்": u["name"], "Username": u["username"], "பணி நிலை": u["role"],
                "கிளை": branch_id_to_name.get(u.get("branch_id"), "HO / Special"),
                "நிலை": "🟢 Active" if u.get("is_active", True) else "🔴 Inactive"
            } for u in users_res.data]), use_container_width=True)

        st.markdown("---")
        sub_col1, sub_col2 = st.columns(2)
        
        # ----------------------------------------------------
        # COL 1: புதிய பணியாளரை உருவாக்குவது
        # ----------------------------------------------------
        with sub_col1:
            with st.form("admin_add_user_form", clear_on_submit=True):
                st.markdown("#### ➕ புதிய பணியாளர் சேர்ப்பு")
                u_name = st.text_input("முழுப் பெயர்")
                u_username = st.text_input("உள்நுழைவு பெயர்")
                u_pass = st.text_input("கடவுச்சொல்", type="password")
                u_role = st.selectbox("பணி நிலை", ["Branch Head / Cashier", "Staff", "Operations", "Auditor", "Admin"])
                b_selection = st.selectbox("கிளை", options=list(branch_options.keys()))
                
                if st.form_submit_button("உருவாக்கு"):
                    if u_name.strip() and u_username.strip() and u_pass.strip():
                        b_id = branch_options.get(b_selection) if u_role not in ["Admin", "Auditor", "Operations"] else None
                        # புதிய பயனருக்கு இயல்பாக அனைத்துப் பிரிவுகளும் அல்லது காலியான பர்மிஷன் கொடுக்கலாம்
                        supabase.table("users").insert({
                            "name": u_name.strip(), 
                            "username": u_username.strip(),
                            "password_hash": u_pass.strip(), 
                            "role": u_role, 
                            "branch_id": b_id, 
                            "is_active": True,
                            "permissions": [] # ஆரம்பத்தில் காலியாக இருக்கும், பின்னர் அட்மின் டிக் செய்து கொள்ளலாம்
                        }).execute()
                        st.success("பயனர் உருவாக்கப்பட்டுவிட்டார்!")
                        st.rerun()

        # ----------------------------------------------------
        # COL 2: பணியாளர் விவரங்கள் மற்றும் பர்மிஷன்களைத் திருத்துவது
        # ----------------------------------------------------
        with sub_col2:
            if users_res.data:
                st.markdown("#### ✏️ பணியாளர் திருத்தம் & அனுமதி மேலாண்மை")
                user_choices = {f"{u['name']} (@{u['username']})": u for u in users_res.data}
                selected_user_key = st.selectbox("திருத்த வேண்டிய பணியாளர்", list(user_choices.keys()))
                curr_user = user_choices[selected_user_key]
                
                # பணியாளர் திருத்தும் ஃபார்ம்
                with st.form("admin_edit_user_form"):
                    edit_name = st.text_input("பெயர்", value=curr_user["name"])
                    edit_pass = st.text_input("புதிய கடவுச்சொல் (விரும்பினால் மட்டும்)", type="password")
                    roles_list = ["Branch Head / Cashier", "Staff", "Operations", "Auditor", "Admin"]
                    edit_role = st.selectbox("பணி நிலை", roles_list, index=roles_list.index(curr_user["role"]) if curr_user["role"] in roles_list else 0)
                    edit_status = st.radio("நிலை", ["Active", "Inactive"], index=0 if curr_user.get("is_active", True) else 1)
                    
                    # --- 🌟 குறிப்பிட்ட பணியாளருக்கான 14 பிரிவுகள் செக்பாக்ஸ்கள் ---
                    st.markdown("---")
                    st.write(f"**{curr_user['name']}** அவர்களுக்கான பிரிவு அனுமதிகள்:")
                    
                    current_perms = curr_user.get("permissions", [])
                    if not isinstance(current_perms, list):
                        current_perms = []
                    
                    # நிறுவனத்தின் 14 நிர்வாகப் பிரிவுகள்
                    all_admin_sections = [
                        "🏢 நேரடி கல்லா & தினசரி வணிகம்",
                        "📦 பாக்கெட் & லாக்கர் மேலாண்மை",
                        "🏢 கிளைகள்",
                        "👥 பணியாளர்கள்",
                        "📋 ஸ்கீம்கள் மேலாண்மை (Pledge, FD, RD)",
                        "🎯 இன்சென்டிவ் & புள்ளி விதிகள்",
                        "📥 மொத்தப் பதிவேற்றம்",
                        "🗂️ வாடிக்கையாளர் மேலாண்மை",
                        "📊 வருகை & பரிவர்த்தனை திருத்தம்",
                        "💰 கிளை துவக்க இருப்பு & கல்லா",
                        "🏦 தலைமையக பணப் பரிமாற்றம்",
                        "📈 காரணப் பணியாளர் அறிக்கை",
                        "🪙 நகைக் கடன் மேலாண்மை",
                        "📤 பல்க் RD / FD பதிவேற்றம்"
                    ]
                    
                    updated_perms = []
                    for section in all_admin_sections:
                        is_checked = section in current_perms
                        # ஒவ்வொரு செக்பாக்ஸிற்கும் தனிப்பயன் key கொடுப்பது அவசியம்
                        if st.checkbox(section, value=is_checked, key=f"perm_chk_{curr_user['id']}_{section}"):
                            updated_perms.append(section)
                    # ----------------------------------------------------------------
                    
                    if st.form_submit_button("புதுப்பி & அனுமதிகளைச் சேமி"):
                        up_data = {
                            "name": edit_name.strip(), 
                            "role": edit_role, 
                            "is_active": edit_status == "Active",
                            "permissions": updated_perms  # டிக் செய்யப்பட்ட புதிய அனுமதிகள் சேமிக்கப்படும்
                        }
                        if edit_pass.strip():
                            up_data["password_hash"] = edit_pass.strip()
                            
                        supabase.table("users").update(up_data).eq("id", curr_user["id"]).execute()
                        st.success("பணியாளர் விவரங்களும் அனுமதிகளும் வெற்றிகரமாகப் புதுப்பிக்கப்பட்டன!")
                        st.rerun()

    # -----------------------------------------------------------------
    # tab3: ஸ்கீம்கள் மேலாண்மை (Pledge RPG, FD, RD)
    # -----------------------------------------------------------------
    elif selected_section == "📋 ஸ்கீம்கள் மேலாண்மை (Pledge, FD, RD)":
        st.subheader("📋 ஸ்கீம்கள் மேலாண்மை (Pledge, FD & RD Scheme Master)")
        s_tab1, s_tab2, s_tab3 = st.tabs(["🪙 நகைக்கடன் திட்டங்கள் (Pledge)", "📑 FD திட்டங்கள்", "📈 RD திட்டங்கள்"])

        with s_tab1:
            st.markdown("##### 🪙 புதிய நகைக் கடன் திட்டம் உருவாக்குதல் (Create Gold Loan Scheme)")
            with st.form("admin_gold_scheme_form", clear_on_submit=True):
                gs_col1, gs_col2, gs_col3 = st.columns(3)
                with gs_col1:
                    gs_name = st.text_input("Scheme Name *", placeholder="எ.கா: சூப்பர் சேவர் 12%")
                    gs_rpg = st.number_input("Rate Per Gram (RPG ₹) *", min_value=100.0, value=5500.0, step=50.0, help="ஒரு கிராம் தங்கத்திற்கான அனுமதிக்கப்படும் அதிகபட்ச கடன் தொகை")
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

                st.markdown("###### 📊 Interest Slabs (வட்டி ஸ்லாப்கள் - நேரடி உள்ளீடு):")
                sl_c1, sl_c2, sl_c3 = st.columns(3)
                with sl_c1:
                    st.markdown("**ஸ்லாப் 1 (Slab 1):**")
                    s1_from = st.number_input("தொடக்க நாள்", value=1, step=1, key="s1_f")
                    s1_to = st.number_input("முடிவு நாள்", value=90, step=1, key="s1_t")
                    s1_roi = st.number_input("வட்டி விகிதம் (%)", value=12.0, step=0.5, key="s1_r")
                with sl_c2:
                    st.markdown("**ஸ்லாப் 2 (Slab 2):**")
                    s2_from = st.number_input("தொடக்க நாள்", value=91, step=1, key="s2_f")
                    s2_to = st.number_input("முடிவு நாள்", value=180, step=1, key="s2_t")
                    s2_roi = st.number_input("வட்டி விகிதம் (%)", value=15.0, step=0.5, key="s2_r")
                with sl_c3:
                    st.markdown("**ஸ்லாப் 3 (Slab 3):**")
                    s3_from = st.number_input("தொடக்க நாள்", value=181, step=1, key="s3_f")
                    s3_to = st.number_input("முடிவு நாள்", value=365, step=1, key="s3_t")
                    s3_roi = st.number_input("வட்டி விகிதம் (%)", value=18.0, step=0.5, key="s3_r")

                if st.form_submit_button("நகைக்கடன் ஸ்கீமைச் சேமி", type="primary"):
                    if gs_name.strip():
                        try:
                            formatted_slabs = [
                                {"from_days": int(s1_from), "to_days": int(s1_to), "roi": float(s1_roi)},
                                {"from_days": int(s2_from), "to_days": int(s2_to), "roi": float(s2_roi)},
                                {"from_days": int(s3_from), "to_days": int(s3_to), "roi": float(s3_roi)}
                            ]
                            supabase.table("gold_loan_schemes").insert({
                                "scheme_name": gs_name.strip(),
                                "rate_per_gram": float(gs_rpg),
                                "interest_slabs": formatted_slabs,
                                "min_loan_amount": float(gs_min),
                                "max_loan_amount": float(gs_max),
                                "scheme_tenor_months": int(gs_tenor),
                                "charges_timing": gs_chg_timing,
                                "charges_type": "Percentage" if "Percentage" in gs_chg_type else "Fixed Amount",
                                "charges_value": float(gs_chg_val),
                                "auction_charges_percent": float(gs_auction_chg),
                                "penal_charges_percent": float(gs_penal_chg),
                                "is_active": True
                            }).execute()
                            st.success(f"✅ '{gs_name}' திட்டம் சேமிக்கப்பட்டது!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"பிழை: {e}")

            # ✅ புதிய பாதுகாப்பான முறை:
            res = safe_execute(supabase.table("gold_loan_schemes").select("*").order("id", desc=True))
            g_schemes = res.data or []
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

            st.markdown("---")
            st.markdown("###### 📋 பதிவு செய்யப்பட்ட FD திட்டங்கள்:")
            fd_schemes = supabase.table("fd_schemes").select("*").order("id", desc=True).execute().data or []
            if fd_schemes:
                df_fd = pd.DataFrame(fd_schemes)[["scheme_name", "tenure_months", "annual_interest_percent", "min_deposit_amount", "interest_payout", "is_active"]]
                df_fd.columns = ["திட்டம் பெயர்", "கால அளவு (மாதம்)", "ஆண்டு வட்டி (%)", "குறைந்தபட்ச தொகை (₹)", "வட்டி பட்டுவாடா", "நிலை"]
                st.dataframe(df_fd, use_container_width=True)
            else:
                st.info("திட்டங்கள் எதுவும் இன்னும் பதிவு செய்யப்படவில்லை.")

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
                    rd_int_type = st.selectbox("Interest Type", ["Simple", "Compounding"], key="rd_int_tp")
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

            st.markdown("---")
            st.markdown("###### 📋 பதிவு செய்யப்பட்ட RD திட்டங்கள்:")
            rd_schemes = supabase.table("rd_schemes").select("*").order("id", desc=True).execute().data or []
            if rd_schemes:
                df_rd = pd.DataFrame(rd_schemes)[["scheme_name", "tenure_months", "annual_interest_percent", "min_deposit_amount", "due_frequency", "is_active"]]
                df_rd.columns = ["திட்டம் பெயர்", "கால அளவு (மாதம்)", "ஆண்டு வட்டி (%)", "குறைந்தபட்ச தவணை (₹)", "தவணை முறை", "நிலை"]
                st.dataframe(df_rd, use_container_width=True)
            else:
                st.info("திட்டங்கள் எதுவும் இன்னும் பதிவு செய்யப்படவில்லை.")

        # -----------------------------------------------------------------
        # tab4: இன்சென்டிவ் & புள்ளி விதிகள் (Delete / Edit / Multi-Scheme)
        # -----------------------------------------------------------------
    elif selected_section == "🎯 இன்சென்டிவ் & புள்ளி விதிகள்":
        st.subheader("🎯 பணியாளர் இன்சென்டிவ் & புள்ளிகள் விதிகள் (Staff Incentive Master)")
        
        set_res = supabase.table("incentive_settings").select("*").eq("id", 1).execute().data
        curr_rpp = float(set_res[0].get("rupees_per_point", 5.0)) if set_res else 5.0
        curr_pen = float(set_res[0].get("negative_growth_penalty_per_lakh", 15.0)) if set_res else 15.0

        with st.container(border=True):
            st.markdown("##### 🪙 நிலையான புள்ளி பண மதிப்பு (Global Point Value)")
            gp_col1, gp_col2, gp_col3 = st.columns(3)
            with gp_col1:
                new_rpp = st.number_input("ஒரு புள்ளிக்கான ரூபாய் மதிப்பு (1 Point = ₹):", value=curr_rpp, step=0.5)
            with gp_col2:
                new_pen = st.number_input("நெகட்டிவ் கடன் வளர்ச்சி அபராதப் புள்ளி (₹1 லட்சத்திற்கு):", value=curr_pen, step=1.0)
            with gp_col3:
                st.write("")
                st.write("")
                if st.button("💾 பொது மதிப்புகளைச் சேமி (Update Values)", type="primary"):
                    try:
                        supabase.table("incentive_settings").upsert({
                            "id": 1,
                            "rupees_per_point": float(new_rpp),
                            "negative_growth_penalty_per_lakh": float(new_pen)
                        }, on_conflict="id").execute()
                        st.success("புள்ளி மதிப்பு புதுப்பிக்கப்பட்டது!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"டேட்டாபேஸ் சேமிப்புப் பிழை: {e}")

        st.markdown("---")
        st.markdown("##### ⚙️ குறிப்பிட்ட ஸ்கீம் வாரியான புள்ளி விதிகள் (Scheme-wise Points Rule)")
        
        all_g_sch = [s["scheme_name"] for s in supabase.table("gold_loan_schemes").select("scheme_name").execute().data or []]
        all_fd_sch = [s["scheme_name"] for s in supabase.table("fd_schemes").select("scheme_name").execute().data or []]
        all_rd_sch = [s["scheme_name"] for s in supabase.table("rd_schemes").select("scheme_name").execute().data or []]
        available_schemes = ["All"] + all_g_sch + all_fd_sch + all_rd_sch

        with st.form("admin_custom_incentive_form", clear_on_submit=True):
            ir_c1, ir_c2, ir_c3, ir_c4, ir_c5 = st.columns(5)
            with ir_c1:
                ir_txn_type = st.selectbox(
                    "நடவடிக்கை வகை *:",
                    [
                        "Pledge (புதிய நகைக் கடன்)", 
                        "GL Release (அடமானம் மீட்டல்)",
                        "Interest Payment (வட்டி வரவு)", 
                        "Part Payment (அசல் வரவு)",
                        "Take Over (பிற நிறுவன கடன் மீட்டல்)", 
                        "FD Open (புதிய வைப்பு நிதி)",
                        "RD Open (புதிய RD சேமிப்பு)", 
                        "RD Due (RD தவணை வரவு)",
                        "GP (Gold Purchase)", 
                        "GS (Gold Sale)"
                    ]
                )
            with ir_c2:
                ir_scheme = st.selectbox("குறிப்பிட்ட ஸ்கீம் *:", available_schemes)
            with ir_c3:
                ir_basis = st.selectbox("அடிப்படைக் கணக்கீடு *:", ["Amount (தொகை வழி - ₹)", "Weight_Grams (எடை வழி - Grams)"])
            with ir_c4:
                ir_unit = st.number_input("அலகு மதிப்பு (Unit Value) *:", value=100000.0, step=100.0)
            with ir_c5:
                ir_pts = st.number_input("புள்ளிகள் (Points Per Unit) *:", value=10.0, step=1.0)

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

        st.markdown("###### 📋 தற்போதுள்ள விதிகள் (எடிட் / நீக்கு வசதியுடன்)")
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
                    st.success("விதி நீக்கப்பட்டது!")
                    st.rerun()

    elif selected_section == "📥 மொத்தப் பதிவேற்றம்":
        st.subheader("📥 கிளை வாரியான பழைய வாடிக்கையாளர் இறக்குமதி (Branch-wise Bulk Import)")
        
        branch_res = supabase.table("branches").select("id, branch_name, branch_code").execute()
        branches_data = branch_res.data or []
        
        branch_dict = {b["branch_name"]: b["id"] for b in branches_data}
        branch_code_map = {b["id"]: b.get("branch_code", "BR") for b in branches_data}
        
        if branch_dict:
            chosen_branch_name = st.selectbox("எந்தக் கிளைக்கான பட்டியல் இது? (Select Branch)", list(branch_dict.keys()))
            target_branch_id = branch_dict[chosen_branch_name]
            target_branch_code = branch_code_map.get(target_branch_id, "BR")[:3].upper()
        else:
            st.warning("கிளைகள் எதுவும் கிடைக்கவில்லை!")
            target_branch_id = None
            target_branch_code = "BR"

        uploaded_cust_file = st.file_uploader("கோப்பைத் தேர்வு செய்யவும் (Excel/CSV)", type=["xls", "xlsx", "csv"])
        
        if uploaded_cust_file and target_branch_id:
            try:
                if uploaded_cust_file.name.endswith(".csv"):
                    df_raw = pd.read_csv(uploaded_cust_file, header=0, dtype=str)
                else:
                    df_raw = pd.read_excel(uploaded_cust_file, header=0)
                
                st.write(f"தேர்ந்தெடுக்கப்பட்ட கிளை: **{chosen_branch_name} ({target_branch_code})** | மொத்த வரிசைகள்: **{len(df_raw)}**")
                st.dataframe(df_raw.head(3))
                
                if st.button("🚀 பதிவேற்றத்தைத் தொடங்கு", type="primary"):
                    cols = list(df_raw.columns)
                    
                    # தலைப்புகளைத் தானாகக் கண்டறிதல்
                    name_col = next((c for c in cols if any(k in str(c).lower() for k in ['name', 'பெயர்', 'வாடிக்கையாளர்'])), cols[0])
                    mob_col = next((c for c in cols if any(k in str(c).lower() for k in ['mobile', 'phone', 'மொபைல்', 'contact'])), None)
                    addr_col = next((c for c in cols if any(k in str(c).lower() for k in ['address', 'முகவரி', 'ஊர்', 'place', 'city'])), None)
                    cust_no_col = next((c for c in cols if any(k in str(c).lower() for k in ['cust_no', 'customer_no', 'cust no', 'code', 'வ.எண்', 'எண்'])), None)
                    guard_col = next((c for c in cols if any(k in str(c).lower() for k in ['guardian', 'father', 'husband', 'தந்தை', 'கணவர்'])), None)
                    mob2_col = next((c for c in cols if any(k in str(c).lower() for k in ['mobile2', 'phone2', 'alt'])), None)
                    nom_col = next((c for c in cols if any(k in str(c).lower() for k in ['nominee', 'நாமினி'])), None)
                    rel_col = next((c for c in cols if any(k in str(c).lower() for k in ['relation', 'உறவு'])), None)
                    gender_col = next((c for c in cols if any(k in str(c).lower() for k in ['gender', 'sex', 'பாலினம்', 'ஆண்/பெண்'])), None)
                    dob_col = next((c for c in cols if any(k in str(c).lower() for k in ['dob', 'birth', 'பிறந்த தேதி', 'date of birth', 'பிறந்த'])), None)

                    # ஏற்கனவே உள்ள வாடிக்கையாளர் குறியீடுகளை எடுத்தல் (Duplicate தடுப்பு)
                    exist_res = supabase.table("customers").select("customer_code").eq("branch_id", target_branch_id).execute()
                    existing_codes = {r["customer_code"] for r in (exist_res.data or [])}

                    # பிறந்த தேதியை (DOB) 4 இலக்க ஆண்டாக மாற்றும் பாதுகாப்பு ஃபங்க்ஷன்
                    def parse_safe_dob(raw_val):
                        if not raw_val or pd.isna(raw_val):
                            return None
                        raw_str = str(raw_val).strip()
                        if raw_str.lower() in ['nan', 'nat', 'none', 'null', '-', '']:
                            return None
                        try:
                            # நாள் முதலில் வரும் வடிவம் (DD/MM/YYYY அல்லது DD-MM-YY)
                            dt = pd.to_datetime(raw_str, errors='coerce', dayfirst=True)
                            if pd.isna(dt):
                                dt = pd.to_datetime(raw_str, errors='coerce')
                            if pd.isna(dt):
                                return None
                            
                            yr = dt.year
                            # 2 இலக்க ஆண்டாக இருந்தால் (எ.கா: 52 -> 1952)
                            if yr < 100:
                                yr += 1900
                            # 2026-க்கு மேல் எதிர்கால ஆண்டாக இருந்தால் (எ.கா: 2052 -> 1952)
                            elif yr > datetime.now().year:
                                yr -= 100
                                
                            return f"{yr:04d}-{dt.month:02d}-{dt.day:02d}"
                        except Exception:
                            return None

                    customers_batch = []
                    skipped_count = 0
                    
                    for idx, row in df_raw.iterrows():
                        name_val = str(row.get(name_col, "")).strip() if pd.notna(row.get(name_col)) else ""
                        raw_mob = str(row.get(mob_col, "")).strip() if mob_col and pd.notna(row.get(mob_col)) else ""
                        mobile = "".join(filter(str.isdigit, raw_mob))[-10:]
                        
                        if not name_val or name_val.lower() == 'nan' or len(mobile) != 10:
                            skipped_count += 1
                            continue
                        
                        # வாடிக்கையாளர் எண்: branchcode-001 வரிசை
                        if cust_no_col and pd.notna(row.get(cust_no_col)):
                            raw_cno = str(row.get(cust_no_col)).strip()
                            raw_cno = raw_cno[:-2] if raw_cno.endswith(".0") else raw_cno
                            raw_cno = re.sub(r'^[Cc-]', '', raw_cno).strip()
                            try:
                                tcode = f"{target_branch_code}-{int(raw_cno):03d}"
                            except Exception:
                                tcode = f"{target_branch_code}-{raw_cno}"
                        else:
                            tcode = f"{target_branch_code}-{(idx + 1):03d}"
                        
                        if tcode in existing_codes:
                            skipped_count += 1
                            continue
                        
                        existing_codes.add(tcode)
                        
                        real_addr = str(row.get(addr_col, "")).strip() if addr_col and pd.notna(row.get(addr_col)) else chosen_branch_name
                        if not real_addr or real_addr.lower() == 'nan':
                            real_addr = chosen_branch_name

                        # பாலினம்
                        clean_gender = None
                        if gender_col and pd.notna(row.get(gender_col)):
                            g_raw = str(row.get(gender_col, "")).strip().lower()
                            if g_raw in ["m", "male", "ஆண்", "ஆ"]:
                                clean_gender = "Male"
                            elif g_raw in ["f", "female", "பெண்", "பெ"]:
                                clean_gender = "Female"
                            elif g_raw in ["o", "other", "others", "மற்றவை"]:
                                clean_gender = "Other"
                            elif g_raw and g_raw != "nan":
                                clean_gender = g_raw.capitalize()

                        # பிறந்த தேதி (பிழையின்றி 4 இலக்க வடிவில்)
                        clean_dob = parse_safe_dob(row.get(dob_col)) if dob_col else None
                        
                        customer_item = {
                            "branch_id": target_branch_id,
                            "customer_code": tcode,
                            "name": name_val,
                            "mobile": mobile,
                            "mobile2": "".join(filter(str.isdigit, str(row.get(mob2_col, ""))))[-10:] if mob2_col and pd.notna(row.get(mob2_col)) else None,
                            "guardian_name": str(row.get(guard_col, "")).strip() if guard_col and pd.notna(row.get(guard_col)) else None,
                            "dob": clean_dob,
                            "gender": clean_gender,
                            "address": real_addr,
                            "nominee_name": str(row.get(nom_col, "")).strip() if nom_col and pd.notna(row.get(nom_col)) else None,
                            "nominee_relation": str(row.get(rel_col, "")).strip() if rel_col and pd.notna(row.get(rel_col)) else None,
                            "kyc_status": "Approved",
                            "is_active": True
                        }
                        customers_batch.append(customer_item)

                    # பல்க்காக டேட்டாபேஸில் ஏற்றுதல் (Batch size: 50 + Auto Fallback)
                    success_count = 0
                    error_list = []
                    progress_bar = st.progress(0)
                    
                    if customers_batch:
                        batch_size = 50
                        for i in range(0, len(customers_batch), batch_size):
                            chunk = customers_batch[i:i + batch_size]
                            try:
                                supabase.table("customers").insert(chunk).execute()
                                success_count += len(chunk)
                            except Exception as b_err:
                                # 🌟 Fallback: ஒருவேளை அந்த 50 பேரில் ஒருவரிடம் பிழை இருந்தால், 
                                # மற்ற 49 பேர் விடுபடாமல் இருக்க ஒவ்வொன்றாகச் சேமித்தல்:
                                for single_item in chunk:
                                    try:
                                        supabase.table("customers").insert(single_item).execute()
                                        success_count += 1
                                    except Exception:
                                        try:
                                            # DOB பிழையாக இருந்தால் அதை மட்டும் நீக்கிவிட்டு மீண்டும் சேமித்தல்
                                            single_item["dob"] = None
                                            supabase.table("customers").insert(single_item).execute()
                                            success_count += 1
                                        except Exception as retry_err:
                                            error_list.append(f"{single_item['name']} ({single_item['customer_code']}) பிழை: {retry_err}")
                            
                            progress_bar.progress(min((i + len(chunk)) / len(customers_batch), 1.0))
                    
                    st.success(f"✅ **{chosen_branch_name}** கிளைக்கு மேலும் **{success_count}** வாடிக்கையாளர்கள் வெற்றிகரமாகப் பதிவு செய்யப்பட்டனர்!")
                    if skipped_count > 0:
                        st.info(f"ℹ️ ஏற்கனவே பதிவானதால் / விடுபட்டதால் தவிர்க்கப்பட்டவை: **{skipped_count}** (முந்தைய 200 வாடிக்கையாளர்களையும் சேர்த்து)")
                    if error_list:
                        for err in error_list:
                            st.error(err)
                    st.balloons()
                    
            except Exception as e:
                st.error(f"இறக்குமதி செய்வதில் பிழை: {e}")

    # -----------------------------------------------------------------
    # tab6: வாடிக்கையாளர் மேலாண்மை (Customer Management)
    # -----------------------------------------------------------------
    elif selected_section == "🗂️ வாடிக்கையாளர் மேலாண்மை":
        st.subheader("👥 வாடிக்கையாளர் மேலாண்மை (Customer Management)")
        
        b_data = supabase.table("branches").select("id, branch_name, branch_code").execute().data or []
        branch_map = {b["id"]: f"{b['branch_name']} ({b.get('branch_code', 'BR')})" for b in b_data}
        
        c_sub1, c_sub2 = st.tabs(["📋 வாடிக்கையாளர் பட்டியல் & தேடல்", "➕ புதிய வாடிக்கையாளர் சேர்க்க"])
        
        with c_sub1:
            col_f1, col_f2 = st.columns([1, 2])
            with col_f1:
                branch_filter_options = ["அனைத்துக் கிளைகள் (All Branches)"] + [f"{b['branch_name']} ({b.get('branch_code', 'BR')})" for b in b_data]
                sel_branch_filter = st.selectbox("கிளை வடிகட்டி (Filter by Branch):", branch_filter_options)
            with col_f2:
                search_query = st.text_input("🔍 தேடுக (பெயர், மொபைல் எண், அல்லது வாடிக்கையாளர் குறியீடு):", placeholder="Type name, phone or code...")
            
            query = supabase.table("customers").select("id, customer_code, name, mobile, address, branch_id, kyc_status, is_active, created_at").order("id", desc=True)
            
            if sel_branch_filter != "அனைத்துக் கிளைகள் (All Branches)":
                chosen_b_id = next((b["id"] for b in b_data if f"{b['branch_name']} ({b.get('branch_code', 'BR')})" == sel_branch_filter), None)
                if chosen_b_id:
                    query = query.eq("branch_id", chosen_b_id)
            
            cust_records = query.limit(1000).execute().data or []
            
            if search_query.strip():
                sq = search_query.strip().lower()
                cust_records = [
                    c for c in cust_records 
                    if sq in str(c.get("name", "")).lower() 
                    or sq in str(c.get("mobile", "")) 
                    or sq in str(c.get("customer_code", "")).lower()
                ]
            
            st.markdown(f"**மொத்த வாடிக்கையாளர்கள்:** `{len(cust_records)}`")
            
            if cust_records:
                display_list = []
                for c in cust_records:
                    display_list.append({
                        "ID": c.get("id"),
                        "குறியீடு (Code)": c.get("customer_code", "-"),
                        "பெயர் (Name)": c.get("name", "-"),
                        "மொபைல் எண் (Mobile)": c.get("mobile", "-"),
                        "கிளை (Branch)": branch_map.get(c.get("branch_id"), "-"),
                        "முகவரி (Address)": c.get("address", "-"),
                        "KYC நிலை": c.get("kyc_status", "Approved"),
                        "செயலில் உள்ளதா": "ஆம்" if c.get("is_active") else "இல்லை"
                    })
                
                df_customers = pd.DataFrame(display_list)
                st.dataframe(df_customers, use_container_width=True, hide_index=True)
                
                st.markdown("---")
                st.markdown("##### ✏️ வாடிக்கையாளர் விவரங்களைத் திருத்து (Edit Customer Details)")
                
                cust_options = {f"{c.get('customer_code', '-')} - {c.get('name')} ({c.get('mobile')})": c for c in cust_records}
                sel_cust_label = st.selectbox("திருத்த வேண்டிய வாடிக்கையாளரைத் தேர்வு செய்யவும்:", list(cust_options.keys()))
                
                if sel_cust_label:
                    selected_cust = cust_options[sel_cust_label]
                    with st.form("edit_customer_form"):
                        e_col1, e_col2, e_col3 = st.columns(3)
                        with e_col1:
                            edit_name = st.text_input("பெயர்", value=selected_cust.get("name", ""))
                        with e_col2:
                            edit_mobile = st.text_input("மொபைல் எண்", value=selected_cust.get("mobile", ""), max_chars=10)
                        with e_col3:
                            edit_code = st.text_input("வாடிக்கையாளர் குறியீடு", value=selected_cust.get("customer_code", ""))
                        
                        e_col4, e_col5 = st.columns([2, 1])
                        with e_col4:
                            edit_address = st.text_input("முகவரி", value=selected_cust.get("address", ""))
                        with e_col5:
                            edit_status = st.selectbox("நிலை (Status)", ["Approved", "Pending", "Rejected"], index=["Approved", "Pending", "Rejected"].index(selected_cust.get("kyc_status", "Approved")) if selected_cust.get("kyc_status") in ["Approved", "Pending", "Rejected"] else 0)
                        
                        if st.form_submit_button("💾 மாற்றங்களைச் சேமி (Update Customer)", type="primary"):
                            if edit_name.strip() and len(edit_mobile.strip()) == 10:
                                try:
                                    supabase.table("customers").update({
                                        "name": edit_name.strip(),
                                        "mobile": edit_mobile.strip(),
                                        "customer_code": edit_code.strip(),
                                        "address": edit_address.strip(),
                                        "kyc_status": edit_status
                                    }).eq("id", selected_cust["id"]).execute()
                                    st.success("வாடிக்கையாளர் விவரங்கள் வெற்றிகரமாகப் புதுப்பிக்கப்பட்டன!")
                                    st.rerun()
                                except Exception as err:
                                    st.error(f"புதுப்பிப்பதில் பிழை: {err}")
                            else:
                                st.warning("பெயர் மற்றும் சரியான 10 இலக்க மொபைல் எண்ணை உள்ளிடவும்!")
            else:
                st.info("வாடிக்கையாளர்கள் விவரங்கள் எதுவும் கிடைக்கவில்லை.")

        with c_sub2:
            st.markdown("##### ➕ புதிய வாடிக்கையாளரை நேரடியாகப் பதிவு செய்க")
            with st.form("admin_manual_cust_form", clear_on_submit=True):
                nc_col1, nc_col2 = st.columns(2)
                with nc_col1:
                    target_b = st.selectbox("கிளையைத் தேர்வு செய்யவும்:", [f"{b['branch_name']} ({b.get('branch_code', 'BR')})" for b in b_data])
                    new_cust_name = st.text_input("வாடிக்கையாளர் பெயர் *")
                with nc_col2:
                    new_cust_mobile = st.text_input("10 இலக்க மொபைல் எண் *", max_chars=10)
                    new_cust_code_manual = st.text_input("வாடிக்கையாளர் குறியீடு (விருப்பப்பட்டால் - எ.கா: TGL-150):", placeholder="வெற்றாக விட்டால் தானாக உருவாகும்")
                
                new_cust_addr = st.text_area("முகவரி")
                
                if st.form_submit_button("வாடிக்கையாளரைச் சேமிக்க", type="primary"):
                    if new_cust_name.strip() and len(new_cust_mobile.strip()) == 10:
                        chosen_b_obj = next((b for b in b_data if f"{b['branch_name']} ({b.get('branch_code', 'BR')})" == target_b), None)
                        b_id = chosen_b_obj["id"] if chosen_b_obj else None
                        b_code = chosen_b_obj.get("branch_code", "BR") if chosen_b_obj else "BR"
                        
                        if new_cust_code_manual.strip():
                            final_c_code = new_cust_code_manual.strip()
                        else:
                            final_c_code = f"{b_code}-{datetime.now().strftime('%m%d%H%M')}"
                        
                        try:
                            supabase.table("customers").insert({
                                "branch_id": b_id,
                                "customer_code": final_c_code,
                                "name": new_cust_name.strip(),
                                "mobile": new_cust_mobile.strip(),
                                "address": new_cust_addr.strip() if new_cust_addr.strip() else chosen_b_obj.get("branch_name", ""),
                                "kyc_status": "Approved",
                                "is_active": True
                            }).execute()
                            st.success(f"வாடிக்கையாளர் {new_cust_name} ({final_c_code}) வெற்றிகரமாகச் சேர்க்கப்பட்டார்!")
                            st.rerun()
                        except Exception as err:
                            st.error(f"பதிவு செய்வதில் பிழை: {err}")
                    else:
                        st.warning("தயவுசெய்து பெயர் மற்றும் சரியான 10 இலக்க மொபைல் எண்ணை உள்ளிடவும்!")

    # -----------------------------------------------------------------
    # tab7: வருகை, பரிவர்த்தனை & OTP விலக்கு அட்மின் ஒப்புதல் மேசை
    # -----------------------------------------------------------------
    elif selected_section == "📊 வருகை & பரிவர்த்தனை திருத்தம்":
        st.subheader("📋 OTP விலக்குக் கோரிக்கைகள் (Admin Approval Desk)")
        
        # 🌟 எவ்வித Join-ம் இன்றி நேரடியாக எடுத்தல் (பிழையின்றி வர)
        try:
            res = supabase.table("otp_bypass_requests").select("*").eq("status", "Pending Admin").order("id", desc=True).execute()
            pending_admin = res.data or []
        except Exception as e:
            st.error(f"டேட்டாபேஸ் வினவலில் பிழை: {e}")
            pending_admin = []

        if not pending_admin:
            st.info("✅ தற்போது அட்மின் ஒப்புதலுக்கான OTP விலக்குக் கோரிக்கைகள் எதுவும் நிலுவையில் இல்லை.")
        else:
            for req in pending_admin:
                req_b_id = req.get("branch_id")
                b_lbl = f"Branch ID: {req_b_id}"
                if 'branch_options' in locals() and branch_options:
                    for name, b_id in branch_options.items():
                        if str(b_id) == str(req_b_id):
                            b_lbl = name
                            break

                with st.container(border=True):
                    st.markdown(f"📍 **கிளை:** `{b_lbl}` | 👤 **வாடிக்கையாளர்:** `{req.get('customer_name')}` (`{req.get('mobile')}`)")
                    st.write(f"📝 **கோரியவர்:** {req.get('requested_by')} | **காரணம்:** {req.get('reason')}")
                    
                    b_col1, b_col2 = st.columns(2)
                    with b_col1:
                        if st.button("✅ ஆப்பரேஷன்ஸுக்கு அனுப்பு (Approve to Ops)", key=f"adm_app_{req['id']}", type="primary"):
                            supabase.table("otp_bypass_requests").update({
                                "status": "Pending Operations",
                                "admin_approved_by": st.session_state.username
                            }).eq("id", req["id"]).execute()
                            st.success("ஆப்பரேஷன்ஸ் இறுதி சரிபார்ப்புக்கு அனுப்பப்பட்டது!")
                            st.rerun()
                    with b_col2:
                        if st.button("❌ நிராகரி (Reject)", key=f"adm_rej_{req['id']}"):
                            supabase.table("otp_bypass_requests").update({"status": "Rejected"}).eq("id", req["id"]).execute()
                            st.warning("கோரிக்கை நிராகரிக்கப்பட்டது.")
                            st.rerun()

        st.divider()

        with st.expander("📜 முந்தைய OTP விலக்கு முடிவுகள் & வரலாறு (Audit Log)"):
            try:
                history_res = (
                    supabase.table("otp_bypass_requests")
                    .select("id, created_at, branch_id, customer_name, mobile, reason, status, admin_approved_by, ops_cleared_by")
                    .in_("status", ["Approved", "Used", "Rejected", "Pending Operations"])
                    .order("id", desc=True)
                    .limit(20)
                    .execute()
                )
                history_data = history_res.data or []
                
                if not history_data:
                    st.caption("முந்தைய பதிவுகள் எதுவும் இல்லை.")
                else:
                    for h_item in history_data:
                        h_status = h_item.get("status")
                        # நிலைக்கு ஏற்ப பேட்ஜ் நிறம்
                        if h_status == "Used":
                            s_badge = "🟣 பயன்படுத்தப்பட்டது (Used)"
                        elif h_status == "Approved":
                            s_badge = "🟢 அனுமதி வழங்கப்பட்டது (Active)"
                        elif h_status == "Rejected":
                            s_badge = "🔴 நிராகரிக்கப்பட்டது (Rejected)"
                        else:
                            s_badge = "🟡 ஆப்பரேஷன்ஸ் வசம் (Pending Ops)"

                        h_c1, h_c2 = st.columns([3, 1])
                        with h_c1:
                            st.write(f"👤 **{h_item.get('customer_name')}** ({h_item.get('mobile')}) | நிலை: `{s_badge}`")
                            st.caption(f"காரணம்: {h_item.get('reason')} | கிளை ID: {h_item.get('branch_id')} | அட்மின்: {h_item.get('admin_approved_by', '-')}")
                        with h_c2:
                            # தேங்கி நிற்கும் Approved அனுமதியை அட்மினே ரத்து செய்யும் வசதி:
                            if h_status == "Approved":
                                if st.button("ரத்து செய் (Expire)", key=f"exp_{h_item['id']}"):
                                    supabase.table("otp_bypass_requests").update({"status": "Used"}).eq("id", h_item["id"]).execute()
                                    st.success("அனுமதி ரத்து செய்யப்பட்டது.")
                                    st.rerun()
                        st.write("---")

            except Exception as hist_err:
                st.caption(f"வரலாற்றைப் பெறுவதில் பிழை: {hist_err}")

        st.subheader("📊 வருகை & பரிவர்த்தனை மேலாண்மை")
        v_records = supabase.table("customer_visits").select("*, customers(name, mobile), transactions(*)").order("id", desc=True).limit(20).execute().data or []
        for vr in v_records:
            c_name = vr.get("customers", {}).get("name", "-")
            with st.expander(f"{vr['visit_no']} | {c_name} | ₹{vr['net_cash_amount']:,.2f} | {vr['status']}"):
                if vr.get("transactions"):
                    st.dataframe(pd.DataFrame(vr["transactions"]))
    # -----------------------------------------------------------------
    # tab8: கிளை துவக்க இருப்பு நிர்ணயம் (Opening Stock with 8 Denominations)
    # -----------------------------------------------------------------
    elif selected_section == "💰 கிளை துவக்க இருப்பு & கல்லா":
        st.subheader("💰 கிளை துவக்க இருப்பு நிர்ணயம்")
        
        sel_op_branch = st.selectbox("கிளையைத் தேர்ந்தெடுக்கவும் *:", list(branch_options.keys()), key="sel_op_b_direct")
        selected_b_id = int(branch_options[sel_op_branch])
        
        # டேட்டாபேஸில் உள்ள தற்போதைய கடைசி பதிவை நேரடியாக எடுத்தல்
        cur_db = (
            supabase.table("branch_cash_box")
            .select("*")
            .eq("branch_id", selected_b_id)
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
        
        raw_den = {}
        if cur_db.data and cur_db.data[0].get("opening_denomination"):
            raw_den = cur_db.data[0]["opening_denomination"]
            if isinstance(raw_den, str):
                try:
                    raw_den = json.loads(raw_den)
                except Exception:
                    raw_den = {}

        st.info(f"🔍 **டேட்டாபேஸில் தற்போதுள்ள ₹500 தாள்கள்:** `{raw_den.get('500', 0)}` (பதிவு எண் ID: {cur_db.data[0]['id'] if cur_db.data else 'இல்லை'})")

        # 4 காலம்களில் நேரடி உள்ளீடுகள் (Form இல்லாமல் Instant Update Button உடன்)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            new_500 = st.number_input("₹500 தாள்கள்", min_value=0, value=int(raw_den.get("500", 0) or 0), step=1)
            new_20 = st.number_input("₹20 தாள்கள்", min_value=0, value=int(raw_den.get("20", 0) or 0), step=1)
        with c2:
            new_200 = st.number_input("₹200 தாள்கள்", min_value=0, value=int(raw_den.get("200", 0) or 0), step=1)
            new_10 = st.number_input("₹10 தாள்கள்", min_value=0, value=int(raw_den.get("10", 0) or 0), step=1)
        with c3:
            new_100 = st.number_input("₹100 தாள்கள்", min_value=0, value=int(raw_den.get("100", 0) or 0), step=1)
            new_5 = st.number_input("₹5 தாள்கள்", min_value=0, value=int(raw_den.get("5", 0) or 0), step=1)
        with c4:
            new_50 = st.number_input("₹50 தாள்கள்", min_value=0, value=int(raw_den.get("50", 0) or 0), step=1)
            new_coins = st.number_input("நாணயங்கள் (₹)", min_value=0.0, value=float(raw_den.get("coins", 0) or 0.0), step=1.0)

        calc_tot = (
            (new_500 * 500) + (new_200 * 200) + (new_100 * 100) + (new_50 * 50) +
            (new_20 * 20) + (new_10 * 10) + (new_5 * 5) + new_coins
        )
        st.markdown(f"💼 **மொத்த கணக்கீடு:** `₹{calc_tot:,.2f}`")

        if st.button("💾 துவக்க இருப்பை உடனடியாக மாற்று (Force Update)", type="primary"):
            try:
                today_str = str(date.today())
                new_den_payload = {
                    "500": int(new_500), "200": int(new_200), "100": int(new_100), "50": int(new_50),
                    "20": int(new_20), "10": int(new_10), "5": int(new_5), "coins": float(new_coins)
                }

                # அந்த கிளைக்கு ஏற்கனவே உள்ள பழைய ரெக்கார்டுகள் அனைத்தையும் அழித்துவிட்டு புதியதை மட்டுமே வைத்தல்
                supabase.table("branch_cash_box").delete().eq("branch_id", selected_b_id).execute()

                # புதிய பதிவை சேர்த்தல்
                supabase.table("branch_cash_box").insert({
                    "branch_id": selected_b_id,
                    "entry_date": today_str,
                    "opening_balance": float(calc_tot),
                    "opening_denomination": new_den_payload
                }).execute()

                st.success(f"✅ ₹500 தாள்கள் எண்ணிக்கை `{new_500}` என மாற்றப்பட்டுவிட்டது!")
                st.rerun()
            except Exception as e:
                st.error(f"பிழை: {e}")
        
        st.divider()  # ஒரு பிரிப்பான் கோடு
    
        # =========================================================================
        # 🪙 பழைய கடன்கள் பல்க் அப்லோட் (Smart Gold Loans Bulk Uploader)
        # =========================================================================
        st.markdown("### 🪙 பழைய கடன்கள் பல்க் அப்லோட் & ஆரம்ப எண் நிர்ணயம்")

        branch_res = supabase.table("branches").select("id, branch_name, branch_code").execute()
        branches_data = branch_res.data or []
        b_map = {b["branch_name"]: b["id"] for b in branches_data}
        b_code_map = {b["id"]: b.get("branch_code", "BR") for b in branches_data}

        if b_map:
            sel_b_name = st.selectbox("கிளையைத் தேர்ந்தெடுக்கவும்", list(b_map.keys()), key="gl_bulk_branch_sel")
            cur_b_id = b_map[sel_b_name]
            cur_b_code = b_code_map.get(cur_b_id, "BR")[:3].upper()
        else:
            st.warning("கிளைகள் கிடைக்கவில்லை!")
            cur_b_id = None
            cur_b_code = "BR"

        uploaded_gl_file = st.file_uploader("பழைய கடன் விவரங்கள் (CSV அல்லது Excel கோப்பு):", type=["csv", "xlsx", "xls"], key="gl_bulk_file_uploader")

        if uploaded_gl_file and cur_b_id:
            try:
                if uploaded_gl_file.name.endswith(".csv"):
                    df_gl = pd.read_csv(uploaded_gl_file, dtype={"mobile": str, "loan_no": str})
                else:
                    df_gl = pd.read_excel(uploaded_gl_file, dtype={"mobile": str, "loan_no": str})

                df_gl.columns = [str(c).strip().lower().replace(" ", "_") for c in df_gl.columns]
                st.write(f"📍 தேர்ந்தெடுக்கப்பட்ட கிளை: **{sel_b_name} ({cur_b_code})** | மொத்த கடன்கள்: **{len(df_gl)}**")
                st.dataframe(df_gl.head(3))

                # தேதியை YYYY-MM-DD வடிவத்திற்கு மாற்றும் ஃபங்க்ஷன்
                def safe_parse_loan_date(d_val):
                    if not d_val or pd.isna(d_val):
                        return datetime.now().strftime("%Y-%m-%d")
                    d_str = str(d_val).strip()
                    try:
                        dt = pd.to_datetime(d_str, errors='coerce', dayfirst=True)
                        if pd.isna(dt):
                            dt = pd.to_datetime(d_str, errors='coerce')
                        if pd.isna(dt):
                            return datetime.now().strftime("%Y-%m-%d")
                        
                        yr = dt.year
                        if yr < 100:
                            yr += 2000 if yr <= 35 else 1900
                        elif 1900 <= yr < 1950:
                            yr += 100
                        return f"{yr:04d}-{dt.month:02d}-{dt.day:02d}"
                    except Exception:
                        return datetime.now().strftime("%Y-%m-%d")

                if st.button("🚀 பழைய கடன்களைப் பதிவேற்று (Upload Records)", type="primary"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # 1. ஏற்கனவே உள்ள வாடிக்கையாளர்களைத் தேடுதல் (Mobile -> ID Map)
                    cust_res = supabase.table("customers").select("id, mobile").execute()
                    cust_map = {str(c["mobile"]).strip()[-10:]: c["id"] for c in (cust_res.data or []) if c.get("mobile")}
                    
                    # வாடிக்கையாளர் குறியீட்டுக்கான தற்போதைய வரிசை எண்
                    c_seq_res = supabase.table("customers").select("customer_code").ilike("customer_code", f"{cur_b_code}-%").order("id", desc=True).limit(1).execute()
                    if c_seq_res.data:
                        last_cc = c_seq_res.data[0]["customer_code"]
                        num_p = re.findall(r'\d+', last_cc)
                        cust_seq = int(num_p[-1]) if num_p else 0
                    else:
                        cust_seq = 0

                    # 2. ஏற்கனவே உள்ள கடன் எண்கள் (Duplicate தவிர்ப்பு)
                    existing_loans_res = supabase.table("gold_loans").select("loan_no").execute()
                    existing_loan_nos = {str(l["loan_no"]).strip() for l in (existing_loans_res.data or []) if l.get("loan_no")}

                    success_loans = 0
                    skipped_loans = 0
                    error_details = []

                    for idx, row in df_gl.iterrows():
                        try:
                            raw_mob = str(row.get("mobile", "")).strip().split(".")[0]
                            clean_mob = "".join(filter(str.isdigit, raw_mob))[-10:]
                            
                            raw_lno = str(row.get("loan_no", "")).strip()
                            if not raw_lno or raw_lno.lower() == 'nan':
                                skipped_loans += 1
                                continue
                            
                            if raw_lno in existing_loan_nos:
                                skipped_loans += 1
                                continue

                            # வாடிக்கையாளர் டேட்டாபேஸில் இல்லை என்றால் உடனே உருவாக்குதல்:
                            c_id = cust_map.get(clean_mob)
                            if not c_id:
                                cust_seq += 1
                                new_cust_code = f"{cur_b_code}-{cust_seq:03d}"
                                new_cust_payload = {
                                    "branch_id": cur_b_id,
                                    "customer_code": new_cust_code,
                                    "name": f"Customer {clean_mob}" if clean_mob else f"Walk-in {cust_seq}",
                                    "mobile": clean_mob if clean_mob else f"99999{cust_seq:05d}",
                                    "address": sel_b_name,
                                    "kyc_status": "Approved",
                                    "is_active": True
                                }
                                c_ins = supabase.table("customers").insert(new_cust_payload).execute()
                                if c_ins.data:
                                    c_id = c_ins.data[0]["id"]
                                    if clean_mob:
                                        cust_map[clean_mob] = c_id

                            # தொகைகள் மற்றும் எடைகள்
                            s_amt = float(row.get("sanctioned_amount") or 0.0)
                            g_wt = float(row.get("gross_weight") or 0.0)
                            n_wt = float(row.get("net_weight") or g_wt)
                            m_rate = float(row.get("market_rate_per_gram") or 9000.0)
                            
                            # வட்டி விகிதம் (காலியாக இருந்தால் 12.0%)
                            raw_roi = row.get("interest_rate")
                            roi = float(raw_roi) if pd.notna(raw_roi) and str(raw_roi).strip() != '' else 12.0
                            
                            # நகை விவரம்
                            orn_det = str(row.get("ornament_details", "")).strip()
                            if not orn_det or orn_det.lower() == 'nan':
                                orn_det = "Gold Ornaments"

                            # உருப்படிகள் எண்ணிக்கை
                            raw_items = row.get("items_count")
                            items_cnt = int(raw_items) if pd.notna(raw_items) and str(raw_items).strip() != '' else 1

                            # தரம் & பணியாளர் பெயர்
                            purity = str(row.get("purity", "")).strip()
                            if not purity or purity.lower() == 'nan':
                                purity = "916 KDM"
                                
                            staff_n = str(row.get("staff_name", "")).strip()
                            if not staff_n or staff_n.lower() == 'nan':
                                staff_n = "Migration Admin"

                            # கடன் தேதி
                            formatted_loan_date = safe_parse_loan_date(row.get("loan_date"))

                            loan_payload = {
                                "branch_id": cur_b_id,
                                "customer_id": c_id,
                                "loan_no": raw_lno,
                                "sanctioned_amount": s_amt,
                                "gross_weight": g_wt,
                                "net_weight": n_wt,
                                "purity": purity,
                                "market_rate_per_gram": m_rate,
                                "interest_rate": roi,
                                "scheme_name": str(row.get("scheme_name", "Regular")),
                                "ornament_details": orn_det,
                                "items_count": items_cnt,
                                "staff_name": staff_n,
                                "status": "Active",
                                "created_at": formatted_loan_date
                            }

                            supabase.table("gold_loans").insert(loan_payload).execute()
                            existing_loan_nos.add(raw_lno)
                            success_loans += 1

                        except Exception as row_err:
                            error_details.append(f"கடன் எண் {row.get('loan_no')} பதிவேற்றுவதில் பிழை: {row_err}")

                        progress_bar.progress((idx + 1) / len(df_gl))
                        status_text.text(f"ஏற்றப்படுகிறது: {idx + 1}/{len(df_gl)} | வெற்றி: {success_loans}")

                    st.success(f"🎉 **{sel_b_name}** கிளைக்கு வெற்றிகரமாக **{success_loans}** பழைய கடன்கள் பதிவு செய்யப்பட்டுவிட்டன!")
                    if skipped_loans > 0:
                        st.info(f"ℹ️ ஏற்கனவே பதிவானதால் தவிர்க்கப்பட்டவை: **{skipped_loans}**")
                    if error_details:
                        with st.expander("⚠️ பிழை விவரங்களைக் காண்க"):
                            for e in error_details[:10]:
                                st.write(e)
                    st.balloons()

            except Exception as e:
                st.error(f"கோப்பைப் படிப்பதில் பிழை: {e}")
                # -------------------------------------------------------------
                # 4. ஆட்டோ சீக்வென்ஸ் எண்களைப் புதுப்பித்து அறிவித்தல்
                # -------------------------------------------------------------
                if success_count > 0:
                    for b_id, max_num in branch_max_seq.items():
                        supabase.table("branch_loan_sequences").upsert({
                            "branch_id": b_id,
                            "last_number": max_num
                        }).execute()

                    st.success(f"🎉 மொத்தம் {success_count} பழைய கடன்கள் வெற்றிகரமாக `gold_loans` அட்டவணையில் ஏற்றப்பட்டன!")
                    
                    st.markdown("##### 📌 கிளை வாரியாக அடுத்த புதிய கடன் எண்கள்:")
                    for b_id, max_num in branch_max_seq.items():
                        b_code_name = [k for k, v in branch_map.items() if v == b_id]
                        b_code_str = b_code_name[0] if b_code_name else f"Branch_{b_id}"
                        next_val = max_num + 1
                        formatted_next_no = f"{b_code_str}/{next_val:04d}" if next_val < 1000 else f"{b_code_str}/{next_val}"
                        st.info(f"🏢 கிளை **{b_code_str}**: கடைசி எண் = **{b_code_str}/{max_num}** ➡️ அடுத்த ஆட்டோ எண் = **{formatted_next_no}**")

            except Exception as e:
                st.error(f"❌ கோப்பைப் பதிவேற்றுவதில் பிழை: {e}")

    elif selected_section == "🏦 தலைமையக பணப் பரிமாற்றம்":
        st.subheader("🏦 தலைமையக பணப் பரிமாற்றம் (HO ⇄ Branch)")
        with st.form("adm_fund_form"):
            ft_b = st.selectbox("கிளை:", list(branch_options.keys()))
            ft_type = st.selectbox("வகை:", ["HO_TO_BRANCH", "BRANCH_TO_HO"])
            ft_amt = st.number_input("தொகை (₹):", min_value=0.0, step=1000.0)
            if st.form_submit_button("பரிமாற்றத்தைச் சேமி"):
                supabase.table("branch_fund_transfers").insert({
                    "branch_id": branch_options[ft_b], "transfer_date": str(date.today()),
                    "transfer_type": ft_type, "amount": ft_amt, "payment_mode": "Cash", "created_by": st.session_state.username,
                    "status": "Approved"
                }).execute()
                st.success("பதிவு செய்யப்பட்டது!")
                st.rerun()

    elif selected_section == "📈 காரணப் பணியாளர் அறிக்கை":
        rep_b_opts = ["அனைத்து கிளைகளும் (All Branches)"] + list(branch_options.keys())
        sel_rep_b = st.selectbox("கிளையை வடிகட்டவும்:", rep_b_opts, key="adm_rep_branch_sel")
        filter_b_id = branch_options.get(sel_rep_b) if sel_rep_b != "அனைத்து கிளைகளும் (All Branches)" else None
        render_staff_attribution_report(selected_branch_id=filter_b_id)
    
    # -------------------------------------------------------------
    # 🪙 TAB 11: கிளை வாரியாக நகைக்கடன் மேலாண்மை (Foreign Key பிழையின்றி)
    # -------------------------------------------------------------
    elif selected_section == "🪙 நகைக் கடன் மேலாண்மை":
        st.subheader("📋 கிளை வாரியாக நகைக் கடன் மேலாண்மை & வரிசை எண் கட்டுப்பாடு")
        st.caption("பழைய மற்றும் புதிய கடன்களின் நகை விவரங்கள், எடை மற்றும் நிலையை ஆய்வு செய்யவும், திருத்தவும்.")

        # 1. கிளைகள் பட்டியல் மற்றும் கிளைப் பெயர் மேப்பிங்
        # ⚡ கேச்சில் இருந்து நேரடியாக எடுத்து நினைவகத்திலேயே மேப் செய்தல் (0.0001 நொடி வேகம்):
        b_list = get_cached_branches()
        b_dict = {b["branch_name"]: b["id"] for b in b_list}
        b_name_map = {b["id"]: b["branch_name"] for b in b_list}
        b_opts = ["அனைத்து கிளைகள்"] + list(b_dict.keys())

        # வடிகட்டிகள் (Filters)
        f_col1, f_col2, f_col3 = st.columns([2, 2, 3])
        with f_col1:
            sel_b = st.selectbox("🏢 கிளையைத் தேர்ந்தெடுக்கவும்:", b_opts, key="adm_gl_branch_filter")
        with f_col2:
            sel_stat_filter = st.selectbox(
                "📌 கடன் நிலை (Status):", 
                ["அனைத்தும்", "Active", "Approved", "Closed", "Overdue", "Auctioned", "Cancelled", "Pending"], 
                key="adm_gl_stat_filter"
            )
        with f_col3:
            gl_search = st.text_input("🔍 தேடல் (கடன் எண் / வாடிக்கையாளர் / மொபைல் / நகை):", key="adm_gl_search_box")

        # அ. கிளையின் தற்போதைய கடன் எண் வரிசை நிலை & திருத்தும் கட்டுப்பாடு (Sequence Control)
        if sel_b != "அனைத்து கிளைகள்" and sel_b in b_dict:
            active_bid = b_dict[sel_b]
            try:
                seq_res = supabase.table("branch_loan_sequences").select("*").eq("branch_id", active_bid).execute()
                if seq_res.data:
                    seq_data = seq_res.data[0]
                    p_fix = seq_data.get("prefix", "GL")
                    l_num = seq_data.get("last_number", 0)
                    st.info(f"🔢 **{sel_b}** Prefix: `{p_fix}` | கடைசி எண்: `{l_num}` | அடுத்த கடன் எண்: **`{p_fix}/{str(l_num + 1).zfill(4)}`**")
                    
                    # 🌟 வரிசை எண்ணைத் திரையிலேயே நேரடியாக மாற்றும் வசதி:
                    with st.expander("⚙️ கடன் வரிசை எண்ணை மாற்றியமைக்க (Update Sequence Number)"):
                        sc1, sc2, sc3 = st.columns([2, 2, 2])
                        with sc1:
                            new_pfx = st.text_input("Prefix (எ.கா: KMK, AVL):", value=p_fix, key=f"seq_pfx_{active_bid}")
                        with sc2:
                            new_lno = st.number_input("கடைசி கடன் எண் (Last Used No):", value=int(l_num), step=1, key=f"seq_lno_{active_bid}")
                        with sc3:
                            st.write("")
                            st.write("")
                            if st.button("💾 வரிசை எண்ணைச் சேமி", key=f"save_seq_btn_{active_bid}", type="primary"):
                                supabase.table("branch_loan_sequences").update({
                                    "prefix": new_pfx.strip(),
                                    "last_number": int(new_lno)
                                }).eq("branch_id", active_bid).execute()
                                st.success("✅ வரிசை எண் வெற்றிகரமாகப் புதுப்பிக்கப்பட்டது!")
                                st.rerun()
            except Exception:
                pass

        st.markdown("---")

        # ஆ. gold_loans அட்டவணையில் இருந்து கடன்களை எடுத்தல்
        try:
            q = supabase.table("gold_loans").select("*")

            if sel_b != "அனைத்து கிளைகள்" and sel_b in b_dict:
                q = q.eq("branch_id", b_dict[sel_b])

            if sel_stat_filter != "அனைத்தும்":
                q = q.eq("status", sel_stat_filter)

            gl_data = q.order("id", desc=True).limit(300).execute().data or []
        except Exception as e:
            st.error(f"கடன்களை எடுப்பதில் பிழை: {e}")
            gl_data = []

        # இ. வாடிக்கையாளர் விவரங்களை எடுத்தல் (Customer Data Mapping)
        cust_map = {}
        c_ids = list({r["customer_id"] for r in gl_data if r.get("customer_id")})
        if c_ids:
            try:
                c_res = supabase.table("customers").select("id, name, mobile, customer_code").in_("id", c_ids).execute()
                cust_map = {c["id"]: c for c in (c_res.data or [])}
            except Exception:
                cust_map = {}

        # ஈ. உரைத் தேடல் (Search Filter)
        if gl_search.strip():
            s_val = gl_search.strip().lower()
            filtered_gl = []
            for r in gl_data:
                c_info = cust_map.get(r.get("customer_id"), {})
                c_n = str(c_info.get("name", "")).lower()
                c_m = str(c_info.get("mobile", "")).lower()
                c_cd = str(c_info.get("customer_code", "")).lower()
                l_no = str(r.get("loan_no", "")).lower()
                orn = str(r.get("ornament_details", "")).lower()
                sch = str(r.get("scheme_name", "")).lower()

                if (s_val in l_no or s_val in c_n or s_val in c_m or s_val in c_cd or s_val in orn or s_val in sch):
                    filtered_gl.append(r)
            gl_data = filtered_gl

        # உ. கடன்களைத் திரையில் காட்டுதல்
        if not gl_data:
            st.warning("⚠️ கடன்கள் எதுவும் கண்டறியப்படவில்லை.")
        else:
            st.write(f"📊 மொத்தம் கண்டறியப்பட்ட கடன்கள்: **{len(gl_data)}**")

            for row in gl_data:
                gl_id = row["id"]
                c_id = row.get("customer_id")
                c_info = cust_map.get(c_id, {})
                
                c_name = c_info.get("name") or row.get("customer_name") or "-"
                c_mob = c_info.get("mobile") or row.get("mobile") or "-"
                c_code = c_info.get("customer_code") or ""
                
                b_label = b_name_map.get(row.get("branch_id"), f"கிளை {row.get('branch_id', '')}")
                loan_no = row.get("loan_no", "-") or "-"
                p_amt = float(row.get("sanctioned_amount") or row.get("amount") or 0.0)
                g_wt = float(row.get("gross_weight") or 0.0)
                n_wt = float(row.get("net_weight") or 0.0)
                item_desc = row.get("ornament_details") or "-"
                items_cnt = row.get("items_count") or 1
                t_status = row.get("status") or "Active"
                sch_name = row.get("scheme_name") or "Regular"
                roi_val = float(row.get("interest_rate") or 12.0)
                c_date = str(row.get("created_at", ""))[:10]

                # கார்டு விரிவடையும் பெட்டி
                card_title = f"🏷️ {loan_no} | {c_name} ({b_label}) | ₹{p_amt:,.2f} | ஜி: {g_wt}g / நெட்: {n_wt}g | நிலை: {t_status}"
                with st.expander(card_title):
                    col_t1, col_t2 = st.tabs(["✏️ விவரம் & திருத்து (Edit)", "🗑️ நீக்கு (Delete)"])

                    # -------------------------------------------------------------
                    # ✏️ எடிட் பிரிவு (Edit Tab)
                    # -------------------------------------------------------------
                    with col_t1:
                        with st.form(key=f"edit_gl_form_{gl_id}"):
                            ec1, ec2 = st.columns(2)
                            with ec1:
                                up_name = st.text_input("வாடிக்கையாளர் பெயர்:", value=c_name, key=f"up_name_{gl_id}")
                                up_mob = st.text_input("மொபைல் எண்:", value=c_mob, key=f"up_mob_{gl_id}")
                                up_amt = st.number_input("கடன் தொகை (₹ Sanctioned):", value=p_amt, step=500.0, key=f"up_amt_{gl_id}")
                                up_items = st.text_area("💍 நகை விவரம் (Ornaments):", value=item_desc, key=f"up_items_{gl_id}")
                                up_cnt = st.number_input("பொருட்கள் எண்ணிக்கை:", value=int(items_cnt), step=1, key=f"up_cnt_{gl_id}")

                            with ec2:
                                up_lno = st.text_input("கடன் எண் (Loan No):", value=loan_no, key=f"up_lno_{gl_id}")
                                up_gw = st.number_input("மொத்த எடை (Gross Wt g):", value=g_wt, step=0.1, key=f"up_gw_{gl_id}")
                                up_nw = st.number_input("நிகர எடை (Net Wt g):", value=n_wt, step=0.1, key=f"up_nw_{gl_id}")
                                up_sch = st.text_input("திட்டப் பெயர் (Scheme):", value=sch_name, key=f"up_sch_{gl_id}")
                                up_roi = st.number_input("ஆண்டு வட்டி விகிதம் (% ROI):", value=roi_val, step=0.5, key=f"up_roi_{gl_id}")

                                stat_options = ["Active", "Approved", "Closed", "Overdue", "Auctioned", "Cancelled", "Pending"]
                                stat_idx = stat_options.index(t_status) if t_status in stat_options else 0
                                up_stat = st.selectbox("தற்போதைய கடன் நிலை (Status):", stat_options, index=stat_idx, key=f"up_stat_{gl_id}")

                            if st.form_submit_button("💾 மாற்றங்களைச் சேமி (Update Record)", type="primary"):
                                try:
                                    # 1. gold_loans அட்டவணையைப் புதுப்பித்தல்
                                    supabase.table("gold_loans").update({
                                        "loan_no": up_lno.strip(),
                                        "sanctioned_amount": float(up_amt),
                                        "gross_weight": float(up_gw),
                                        "net_weight": float(up_nw),
                                        "ornament_details": up_items.strip(),
                                        "items_count": int(up_cnt),
                                        "scheme_name": up_sch.strip(),
                                        "interest_rate": float(up_roi),
                                        "status": up_stat
                                    }).eq("id", gl_id).execute()

                                    # 2. வாடிக்கையாளர் அட்டவணையைப் (customers) புதுப்பித்தல்
                                    if c_id:
                                        supabase.table("customers").update({
                                            "name": up_name.strip(),
                                            "mobile": up_mob.strip()
                                        }).eq("id", c_id).execute()

                                    # 3. transactions அட்டவணையில் இருந்தால் அதையும் புதுப்பித்தல்
                                    try:
                                        supabase.table("transactions").update({
                                            "customer_name": up_name.strip(),
                                            "mobile": up_mob.strip(),
                                            "amount": float(up_amt),
                                            "principal_amount": float(up_amt),
                                            "gross_weight": float(up_gw),
                                            "net_weight": float(up_nw),
                                            "item_details": up_items.strip(),
                                            "status": up_stat
                                        }).ilike("remarks", f"%{loan_no}%").execute()
                                    except Exception:
                                        pass

                                    st.success("✅ கடன் விவரங்கள் வெற்றிகரமாகப் புதுப்பிக்கப்பட்டன!")
                                    st.rerun()
                                except Exception as ex:
                                    st.error(f"பிழை: {ex}")

                    # -------------------------------------------------------------
                    # 🗑️ டிலீட் பிரிவு (Delete Tab)
                    # -------------------------------------------------------------
                    with col_t2:
                        st.warning("⚠️ இக்கடனை நீக்கினால் இந்த பதிவு கணக்கிலிருந்து நிரந்தரமாக அழிக்கப்படும்.")
                        confirm_del = st.checkbox(f"நான் உறுதியாக ID: {gl_id} ({loan_no} - {c_name}) கடனை நீக்க விரும்புகிறேன்.", key=f"del_chk_{gl_id}")
                        if st.button("🗑️ நிரந்தரமாக நீக்கு", key=f"del_btn_{gl_id}", disabled=not confirm_del):
                            try:
                                # gold_loans-லிருந்து நீக்குதல்
                                supabase.table("gold_loans").delete().eq("id", gl_id).execute()
                                
                                # transactions-லிருந்து நீக்குதல் (இருந்தால்)
                                try:
                                    supabase.table("transactions").delete().ilike("remarks", f"%{loan_no}%").execute()
                                except Exception:
                                    pass

                                st.success(f"✅ கடன் எண்: {loan_no} வெற்றிகரமாக நீக்கப்பட்டது!")
                                st.rerun()
                            except Exception as dex:
                                st.error(f"நீக்குவதில் பிழை: {dex}")
    # -----------------------------------------------------------------
    # 🌟 பல்க் RD & FD பதிவேற்ற மேசை (Bulk Upload Desk)
    # -----------------------------------------------------------------
    elif selected_section == "📤 பல்க் RD / FD பதிவேற்றம்":
        st.subheader("📤 பழைய RD / FD கணக்குகளைப் பல்க்காக ஏற்றுதல் (Multi-Branch Bulk Import)")
        st.caption("பழைய பாஸ்புக் கணக்கு எண்களுடன் அனைத்துக் கிளைகளின் தரவுகளையும் ஒரே எக்செல் கோப்பில் பதிவேற்றலாம்.")

        # 1. கிளைகள் விவரங்களை எடுத்தல்
        # ⚡ Supabase நெட்வொர்க் அழைப்புக்கு பதிலாக நினைவக கேச்சிலிருந்து எடுத்தல்:
        all_branches = get_cached_branches()

        branch_lookup = {}
        branch_code_map = {}
        for b in all_branches:
            bid = b["id"]
            bname = str(b.get("branch_name", "")).strip().lower()
            bcode = str(b.get("branch_code", "BR")).strip().upper()
            
            branch_lookup[bname] = bid
            branch_lookup[bcode.lower()] = bid
            branch_code_map[bid] = bcode

        # 2. மாதிரி எக்செல் டெம்ப்ளேட் டவுன்லோட்
        sample_csv = "Type,Branch,Account_No,Name,Mobile,Amount,Scheme,Nominee,Relation,Age,Address\nRD,Aundivilai,AVL/RD/0001,ரமேஷ்,9876543210,1000,Regular RD,சுதா,மனைவி,32,ஆவுடையாள்புரம்\nFD,Thingalnagar,TNG/FD/0001,சுரேஷ்,9876543211,25000,Special FD,கார்த்திக்,மகன்,12,திங்கள்நகர்\nRD,KMK,KMK/RD/0001,முருகன்,9876543212,2000,Regular RD,வள்ளி,மனைவி,28,கீழமணக்குடி"
        st.download_button(
            "📥 மாதிரி எக்செல் டெம்ப்ளேட் (Template CSV with Account_No) பதிவிறக்குக",
            data=sample_csv.encode("utf-8-sig"),
            file_name="All_Branches_RD_FD_Template.csv",
            mime="text/csv"
        )

        st.write("---")

        # 3. கோப்புப் பதிவேற்றம்
        uploaded_file = st.file_uploader("📂 பூர்த்தி செய்யப்பட்ட கோப்பைத் தேர்ந்தெடுக்கவும் (CSV அல்லது Excel)", type=["csv", "xlsx", "xls"], key="multi_branch_bulk_uploader")

        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file, dtype=str)
                else:
                    df = pd.read_excel(uploaded_file, dtype=str)

                df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
                st.write(f"📊 கண்டறியப்பட்ட மொத்தப் பதிவுகள்: **{len(df)}**")
                st.dataframe(df.head(5), use_container_width=True)

                # 4. பதிவேற்றும் பட்டன்
                if st.button("🚀 பழைய கணக்குகளை டேட்டாபேஸில் ஏற்று (Start Multi-Branch Import)", type="primary"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    status_text.text("டேட்டாபேஸ் விவரங்களை ஒத்திசைக்கிறது... காத்திருக்கவும்...")

                    # 🌟 A. 1000 லிமிட் தடையின்றி அனைத்து ரெக்கார்டுகளையும் எடுக்கும் பேஜினேஷன் ஃபங்க்ஷன்
                    def fetch_all_rows(table_name, select_cols="*"):
                        all_rows = []
                        step = 1000
                        start = 0
                        while True:
                            res = supabase.table(table_name).select(select_cols).range(start, start + step - 1).execute()
                            rows = res.data or []
                            all_rows.extend(rows)
                            if len(rows) < step:
                                break
                            start += step
                        return all_rows

                    # அனைத்து வாடிக்கையாளர்களையும் முழுமையாக எடுத்தல்
                    all_custs = fetch_all_rows("customers", "id, name, mobile, branch_id, customer_code")
                    
                    # மேப்பிங் மற்றும் அதிகபட்ச எண்களைக் கணக்கிடுதல்
                    cust_by_mobile = {}
                    cust_by_name_branch = {}
                    existing_cust_codes = set()
                    branch_cust_max = {}

                    for c in all_custs:
                        cid = c["id"]
                        cbid = c.get("branch_id")
                        ccode = str(c.get("customer_code", "")).strip().upper()
                        cname = str(c.get("name", "")).strip().lower()
                        cmob = "".join(filter(str.isdigit, str(c.get("mobile", ""))))[-10:]

                        if cmob:
                            cust_by_mobile[cmob] = cid
                        if cbid and cname:
                            cust_by_name_branch[(cbid, cname)] = cid
                        if ccode:
                            existing_cust_codes.add(ccode)
                            if "-" in ccode:
                                pfx, num_part = ccode.split("-", 1)
                                digits = re.findall(r'\d+', num_part)
                                if digits:
                                    branch_cust_max[pfx] = max(branch_cust_max.get(pfx, 0), int(digits[-1]))

                    # ஏற்கனவே உள்ள அனைத்து RD / FD கணக்கு எண்களையும் எடுத்தல்
                    all_rds = fetch_all_rows("recurring_deposits", "rd_account_no")
                    existing_rds = {str(r["rd_account_no"]).strip() for r in all_rds if r.get("rd_account_no")}

                    all_fds = fetch_all_rows("fixed_deposits", "fd_account_no")
                    existing_fds = {str(f["fd_account_no"]).strip() for f in all_fds if f.get("fd_account_no")}

                    # கிளை வாரியாக கடைசி கணக்கு எண் வரிசைகள்
                    rd_counters = {}
                    fd_counters = {}

                    success_rd = 0
                    success_fd = 0
                    skipped_rows = 0
                    total_rows = len(df)
                    error_list = []

                    cols = list(df.columns)
                    acc_col = next((c for c in cols if any(k in c for k in ['account_no', 'account', 'acc_no', 'rd_no', 'fd_no', 'கணக்கு'])), None)

                    for idx, row in df.iterrows():
                        row_type = str(row.get("type", "")).strip().upper()
                        branch_input = str(row.get("branch", "")).strip().lower()
                        name = str(row.get("name", "")).strip()
                        raw_mob = str(row.get("mobile", "")).strip().split(".")[0]
                        mobile = "".join(filter(str.isdigit, raw_mob))[-10:]
                        
                        try:
                            amount = float(str(row.get("amount", 0)).replace(",", "").strip() or 0.0)
                        except Exception:
                            amount = 0.0

                        scheme = str(row.get("scheme", "Regular")).strip()
                        nominee = str(row.get("nominee", "-")).strip()
                        relation = str(row.get("relation", "-")).strip()
                        
                        try:
                            age = int(str(row.get("age", 30)).strip())
                        except Exception:
                            age = 30
                            
                        address = str(row.get("address", "")).strip()

                        if not name or row_type not in ["RD", "FD"]:
                            skipped_rows += 1
                            continue

                        # கிளை அடையாளம் காணுதல்
                        target_b_id = branch_lookup.get(branch_input)
                        if not target_b_id:
                            error_list.append(f"வரிசை {idx+1}: '{branch_input}' என்ற கிளை கண்டறியப்படவில்லை!")
                            skipped_rows += 1
                            continue

                        target_b_code = branch_code_map.get(target_b_id, "BR")[:3].upper()
                        if not address or address.lower() == 'nan':
                            address = f"Branch {target_b_code}"

                        # 🌟 1. பழைய கணக்கு எண் (Account_No)
                        raw_acc_no = str(row.get(acc_col, "")).strip() if acc_col and pd.notna(row.get(acc_col)) else ""
                        if raw_acc_no.endswith(".0"):
                            raw_acc_no = raw_acc_no[:-2]

                        if raw_acc_no and raw_acc_no.lower() != 'nan':
                            if raw_acc_no.isdigit():
                                acc_no = f"{target_b_code}/{row_type}/{int(raw_acc_no):04d}"
                            else:
                                acc_no = raw_acc_no
                        else:
                            # எக்செல்-ல் விடுபட்டிருந்தால் ஆட்டோ-ஜெனரேட்
                            if row_type == "RD":
                                rd_counters[target_b_id] = rd_counters.get(target_b_id, branch_cust_max.get(target_b_code, 0)) + 1
                                acc_no = f"{target_b_code}/RD/{rd_counters[target_b_id]:04d}"
                            else:
                                fd_counters[target_b_id] = fd_counters.get(target_b_id, branch_cust_max.get(target_b_code, 0)) + 1
                                acc_no = f"{target_b_code}/FD/{fd_counters[target_b_id]:04d}"

                        # ஏற்கனவே பதிவாகியிருந்தால் தவிர்த்தல்
                        if (row_type == "RD" and acc_no in existing_rds) or (row_type == "FD" and acc_no in existing_fds):
                            skipped_rows += 1
                            continue

                        try:
                            # 🌟 2. வாடிக்கையாளரைக் கண்டறிதல் (3-அடுக்கு சரிபார்ப்பு)
                            c_id = None
                            if mobile and len(mobile) == 10:
                                c_id = cust_by_mobile.get(mobile)
                            if not c_id:
                                c_id = cust_by_name_branch.get((target_b_id, name.lower()))
                            
                            # மெமரியில் இல்லையெனில் டேட்டாபேஸில் நேரடித் தேடல்
                            if not c_id and mobile and len(mobile) == 10:
                                db_c = supabase.table("customers").select("id").eq("mobile", mobile).limit(1).execute()
                                if db_c.data:
                                    c_id = db_c.data[0]["id"]
                                    cust_by_mobile[mobile] = c_id

                            if not c_id:
                                db_c_name = supabase.table("customers").select("id").eq("branch_id", target_b_id).ilike("name", name.strip()).limit(1).execute()
                                if db_c_name.data:
                                    c_id = db_c_name.data[0]["id"]
                                    cust_by_name_branch[(target_b_id, name.lower())] = c_id

                            # 🌟 3. இல்லையெனில் மட்டுமே புதிய வாடிக்கையாளரை உருவாக்குதல் (மோதலே இல்லாத எண்)
                            if not c_id:
                                cur_max = branch_cust_max.get(target_b_code, 0)
                                while True:
                                    cur_max += 1
                                    cand_code = f"{target_b_code}-{cur_max:03d}"
                                    if cand_code not in existing_cust_codes:
                                        new_c_code = cand_code
                                        break
                                
                                branch_cust_max[target_b_code] = cur_max
                                existing_cust_codes.add(new_c_code)

                                new_cust = supabase.table("customers").insert({
                                    "branch_id": target_b_id,
                                    "customer_code": new_c_code,
                                    "name": name,
                                    "mobile": mobile if mobile and len(mobile) == 10 else f"99999{cur_max:05d}",
                                    "address": address,
                                    "nominee_name": nominee if nominee != "-" else None,
                                    "nominee_relation": relation if relation != "-" else None,
                                    "kyc_status": "Approved",
                                    "is_active": True
                                }).execute()
                                
                                if new_cust.data:
                                    c_id = new_cust.data[0]["id"]
                                    if mobile and len(mobile) == 10:
                                        cust_by_mobile[mobile] = c_id
                                    cust_by_name_branch[(target_b_id, name.lower())] = c_id

                            # 4. மைக்ரேஷன் வருகைப் பதிவு உருவாக்குதல்
                            v_no = f"MIG-{target_b_code}-{row_type}-{idx+1:04d}"
                            visit_payload = {
                                "visit_no": v_no,
                                "customer_id": c_id,
                                "branch_id": target_b_id,
                                "total_paid": 0.0,
                                "total_received": amount,
                                "net_cash_amount": amount,
                                "cash_amount": amount,
                                "bank_amount": 0.0,
                                "payment_mode": "Migration",
                                "otp_verified": True,
                                "status": "Completed"
                            }
                            v_insert = supabase.table("customer_visits").insert(visit_payload).execute()
                            new_visit_id = v_insert.data[0]["id"]

                            # 5. கணக்கு எண்ணுடன் அட்டவணைகளில் சேமித்தல்
                            if row_type == "RD":
                                rd_payload = {
                                    "visit_id": new_visit_id,
                                    "branch_id": target_b_id,
                                    "customer_id": c_id,
                                    "rd_account_no": acc_no,
                                    "monthly_installment": amount,
                                    "tenure_months": 12,
                                    "interest_rate": 12.0,
                                    "total_target_amount": amount * 12,
                                    "current_installment_no": 1,
                                    "nominee_name": nominee,
                                    "nominee_relation": relation,
                                    "status": "Active"
                                }
                                supabase.table("recurring_deposits").insert(rd_payload).execute()
                                existing_rds.add(acc_no)
                                success_rd += 1
                                txn_type_label = "RD Open (புதிய RD சேமிப்பு)"

                            else:  # FD கணக்கு
                                fd_payload = {
                                    "visit_id": new_visit_id,
                                    "branch_id": target_b_id,
                                    "customer_id": c_id,
                                    "fd_account_no": acc_no,
                                    "deposit_amount": amount,
                                    "tenure_months": 12,
                                    "interest_rate": 12.0,
                                    "maturity_amount": amount * 1.12,
                                    "nominee_name": nominee,
                                    "nominee_relation": relation,
                                    "status": "Active"
                                }
                                supabase.table("fixed_deposits").insert(fd_payload).execute()
                                existing_fds.add(acc_no)
                                success_fd += 1
                                txn_type_label = "FD Open (புதிய வைப்பு நிதி)"

                            # 6. transactions அட்டவணையில் பதிவு
                            txn_payload = {
                                "visit_id": new_visit_id,
                                "branch_id": target_b_id,
                                "transaction_type": txn_type_label,
                                "paid_amount": 0.0,
                                "received_amount": amount,
                                "staff_name": "Migration Admin",
                                "remarks": f"Old Migration | {acc_no} | Scheme: {scheme}",
                                "transaction_details": {
                                    "account_no": acc_no,
                                    "amount": amount,
                                    "nominee": nominee,
                                    "relation": relation,
                                    "age": age,
                                    "address": address
                                }
                            }
                            supabase.table("transactions").insert(txn_payload).execute()

                        except Exception as row_e:
                            error_list.append(f"கணக்கு {acc_no} ({name}) பிழை: {row_e}")

                        progress_bar.progress((idx + 1) / total_rows)
                        status_text.text(f"ஏற்றப்படுகிறது... ({idx+1}/{total_rows}) - {name} ({acc_no})")

                    status_text.empty()
                    st.success(f"🎉 **{success_rd} RD** மற்றும் **{success_fd} FD** கணக்குகள் எந்தப் பிழையுமின்றி டேட்டாபேஸில் வெற்றிகரமாக ஏற்றப்பட்டன!")
                    if skipped_rows > 0:
                        st.info(f"ℹ️ ஏற்கனவே பதிவானதால் / விடுபட்டதால் தவிர்க்கப்பட்டவை: **{skipped_rows}**")
                    if error_list:
                        with st.expander("⚠️ பிழை விவரங்களைக் காண்க"):
                            for err in error_list[:15]:
                                st.write(err)
                    st.balloons()

            except Exception as upload_err:
                st.error(f"❌ கோப்பைப் பதிவேற்றுவதில் பிழை: {upload_err}")
    
    elif selected_section == "🛒 கவுண்ட்டர் வருகை & OTP":
        staff_res = (
            supabase.table("users")
            .select("name")
            .eq("branch_id", st.session_state.branch_id)
            .eq("is_active", True)
            .execute()
        )
        current_staff_list = (
            ["Walk-in (நேரடி வருகை)"] + [s["name"] for s in staff_res.data]
            if staff_res.data
            else ["Walk-in (நேரடி வருகை)"]
        )

        # ---------------------------------------------------------------------
        # 🎉 முந்தைய வருகை வெற்றிகரமாக முடிந்ததற்கான செய்திப் பலகை (Success Card)
        # ---------------------------------------------------------------------
        if st.session_state.get("last_saved_visit"):
            saved = st.session_state["last_saved_visit"]

            st.success(
                f"### 🎉 வருகை வெற்றிகரமாகச் சேமிக்கப்பட்டது!\n\n"
                f"**வருகை எண்:** `{saved['visit_no']}` &nbsp;|&nbsp; "
                f"**வாடிக்கையாளர்:** `{saved['customer_name']}` &nbsp;|&nbsp; "
                f"**நடவடிக்கைகள்:** `{saved['txn_count']} எண்ணம்`\n\n"
                f"💰 **செலுத்திய தொகை:** ₹{saved['total_paid']:,.2f} &nbsp;|&nbsp; "
                f"💰 **பெற்ற தொகை:** ₹{saved['total_received']:,.2f}"
            )
            st.balloons()  # வெற்றிகரமான சேமிப்பிற்கான அனிமேஷன்

            # அறிவிப்பை மூட:
            if st.button(
                "✖ இந்த அறிவிப்பை மூடு (Close Alert)", key="btn_close_succ_alert"
            ):
                st.session_state["last_saved_visit"] = None
                st.rerun()

                st.markdown("---")
    
    
    elif selected_section == "📁 கிளை ஆவணங்கள் பதிவேற்றம்":
      st.subheader("📁 கிளை ஆவணங்கள் பதிவேற்றம் (Upload Docs Desk)")
      st.caption(
          "தணிக்கைக்கு அனுப்ப வேண்டிய வாடிக்கையாளர் வருகைகள் மற்றும் அவர்களின் வணிக"
          " நடவடிக்கைகள்."
      )

      branch_pending = (
          supabase.table("customer_visits")
          .select("*, customers(name, mobile), transactions(*)")
          .eq("branch_id", st.session_state.branch_id)
          .in_("status", ["Pending_Branch_Docs", "Pending_Calling_Verification"])
          .order("id", desc=True)
          .execute()
          .data
          or []
      )

      if not branch_pending:
        st.info("தற்போது ஆவணங்கள் ஏற்ற வேண்டிய வருகைகள் எதுவும் இல்லை.")
      else:
        for b_item in branch_pending:
          c_info = b_item.get("customers", {}) or {}
          b_txns = b_item.get("transactions", []) or []

          with st.expander(
              f"📄 வருகை எண்: {b_item['visit_no']} | வாடிக்கையாளர்:"
              f" {c_info.get('name', '-')} (📞 {c_info.get('mobile', '-')}) |"
              f" நிகரத் தொகை: ₹{float(b_item.get('net_cash_amount', 0)):,.2f}"
          ):
            st.markdown("##### 🛒 இந்த வருகையில் மேற்கொள்ளப்பட்ட நடவடிக்கைகள்:")
            if b_txns:
              for idx, t in enumerate(b_txns, 1):
                st.markdown(
                    f"**{idx}. {t.get('transaction_type', '-')}** | காரணப்"
                    f" பணியாளர்: `{t.get('staff_name', '-')}`"
                )
                st.write(
                    f" • பட்டுவாடா: ₹{float(t.get('paid_amount', 0)):,.2f} |"
                    f" வரவு: ₹{float(t.get('received_amount', 0)):,.2f}"
                )
                st.write(f" • குறிப்பு / விவரம்: {t.get('remarks', '-')}")
                st.markdown("")
            else:
              st.warning(
                  "⚠️ இந்த வருகையில் நடவடிக்கைகள் எதுவும் பதிவாகவில்லை."
              )

            st.markdown("---")
            up_docs = st.file_uploader(
                f"ஆவணங்களை இணைக்கவும் ({b_item['visit_no']})",
                accept_multiple_files=True,
                key=f"doc_up_{b_item['id']}",
            )

            if st.button(
                f"ஆவணங்களைச் சமர்ப்பித்து தணிக்கைக்கு அனுப்புக"
                f" ({b_item['visit_no']})",
                key=f"btn_sub_{b_item['id']}",
                type="primary",
            ):
              if up_docs:
                try:
                  links = upload_files_to_supabase(up_docs, b_item["visit_no"])
                  supabase.table("customer_visits").update(
                      {"status": "Submitted_to_Auditor"}
                  ).eq("id", b_item["id"]).execute()
                  supabase.table("audit_records").insert({
                      "visit_id": b_item["id"],
                      "document_urls": links,
                      "audit_status": "Pending",
                  }).execute()
                  st.success(
                      "✅ ஆவணங்கள் வெற்றிகரமாகத் தணிக்கைக்கு"
                      " அனுப்பப்பட்டுவிட்டன!"
                  )
                  st.rerun()
                except Exception as e:
                  st.error(f"பிழை: {e}")
              else:
                st.warning("⚠️ தயவுசெய்து ஆவணங்களைப் பதிவேற்றம் செய்யவும்.")

    elif selected_section == "⚠️ விளக்கங்கள்":
      st.subheader("⚠️ தலைமை அலுவலக விளக்கங்கள் & மறுப்புகள்")
      clarification_visits = (
          supabase.table("customer_visits")
          .select("*, customers(name, mobile), transactions(*)")
          .eq("branch_id", st.session_state.branch_id)
          .eq("status", "Needs_Clarification")
          .order("id", desc=True)
          .execute()
          .data
          or []
      )

      if not clarification_visits:
        st.info("✅ எந்த விளக்கங்களும் நிலுவையில் இல்லை.")
      else:
        for c_item in clarification_visits:
          c_cust = c_item.get("customers", {}) or {}
          prev_remarks = (
              c_item.get("verification_remarks")
              or "விளக்கம் கோரப்பட்டுள்ளது."
          )

          with st.expander(
              f"🚨 {c_item['visit_no']} |"
              f" {c_cust.get('name', 'வாடிக்கையாளர்')} |"
              f" ₹{float(c_item.get('net_cash_amount', 0)):,.2f}",
              expanded=True,
          ):
            st.markdown(
                "##### 📜 தலைமை அலுவலகம் கேட்ட விளக்கம் (Clarification"
                " Requested):"
            )
            st.warning(prev_remarks)

            b_rep = st.text_area(
                "கிளையின் பதில் விளக்கம் (Branch Reply) *:",
                key=f"rep_{c_item['id']}",
                placeholder="உங்கள் பதிலை தெளிவாக உள்ளிடவும்...",
            )

            if st.button(
                "பதிலைச் சமர்ப்பித்து தணிக்கைக்கு அனுப்புக ➔",
                key=f"send_rep_{c_item['id']}",
                type="primary",
            ):
              if not b_rep.strip():
                st.error(
                    "⚠️ தயவுசெய்து உங்கள் பதிலை உள்ளிட்ட பின் சமர்ப்பிக்கவும்!"
                )
              else:
                now_str = datetime.now().strftime("%d-%m-%Y %I:%M %p")
                # 🌟 பழைய வரலாற்றுடன் கிளையின் பதில் தேதி-நேரத்துடன் சேர்க்கப்படுகிறது
                combined_history = (
                    f"{prev_remarks}\n\n"
                    f"💬 [கிளையின் பதில் ({now_str}) -"
                    f" {st.session_state.username}]:\n{b_rep.strip()}"
                )

                supabase.table("customer_visits").update({
                    "status": "Submitted_to_Auditor",
                    "verification_remarks": combined_history,
                }).eq("id", c_item["id"]).execute()

                supabase.table("audit_records").update(
                    {"audit_status": "Pending"}
                ).eq("visit_id", c_item["id"]).execute()

                st.success(
                    "✅ பதில் சமர்ப்பிக்கப்பட்டு மீண்டும் தணிக்கைக்கு"
                    " அனுப்பப்பட்டது!"
                )
                st.rerun()

    elif selected_section == "💼 கிளை கல்லா":
      st.subheader(
          "💸 கிளை செலவுப் பதிவு & சில்லறை மேலாண்மை (Branch Expense Desk)"
      )
      st.caption(
          "செலவுத் தொகைக்கு நாம் கொடுத்த நோட்டுகளையும், கடைக்காரர் திருப்பிக்"
          " கொடுத்த மீதி சில்லறையையும் (Cash Return) சரியாக உள்ளிடவும்."
      )

      curr_b_drawer = get_current_branch_cash_drawer(st.session_state.branch_id)
      total_drawer_cash = (
          (int(curr_b_drawer.get("500", 0)) * 500)
          + (int(curr_b_drawer.get("200", 0)) * 200)
          + (int(curr_b_drawer.get("100", 0)) * 100)
          + (int(curr_b_drawer.get("50", 0)) * 50)
          + (int(curr_b_drawer.get("20", 0)) * 20)
          + (int(curr_b_drawer.get("10", 0)) * 10)
          + (int(curr_b_drawer.get("5", 0)) * 5)
          + float(curr_b_drawer.get("coins", 0.0))
      )
      with st.expander(
          f"💼 தற்போதைய நேரடி கல்லா கையிருப்பு: ₹{total_drawer_cash:,.2f}",
          expanded=False,
      ):
        # எக்ஸ்பாண்டரின் உள்ளே தலைப்பில் பெரிய மெட்ரிக் ஆகவும் காட்டலாம்
        st.markdown(f"### 💵 கல்லா மொத்த இருப்பு: `₹{total_drawer_cash:,.2f}`")
        st.markdown("---")

        bd1, bd2, bd3, bd4 = st.columns(4)
        with bd1:
          bd1.metric("₹500 தாள்கள்", f"{curr_b_drawer['500']}")
          bd1.metric("₹20 தாள்கள்", f"{curr_b_drawer['20']}")
        with bd2:
          bd2.metric("₹200 தாள்கள்", f"{curr_b_drawer['200']}")
          bd2.metric("₹10 தாள்கள்", f"{curr_b_drawer['10']}")
        with bd3:
          bd3.metric("₹100 தாள்கள்", f"{curr_b_drawer['100']}")
          bd3.metric("₹5 தாள்கள்", f"{curr_b_drawer['5']}")
        with bd4:
          bd4.metric("₹50 தாள்கள்", f"{curr_b_drawer['50']}")
          bd4.metric("நாணயங்கள் (₹)", f"₹{float(curr_b_drawer['coins']):,.2f}")

      with st.form("branch_expense_flow_form", clear_on_submit=True):
        st.markdown(
            "##### 🔄 புதிய செலவுப் பதிவு (Submit for Operations Approval)"
        )
        ex_c1, ex_c2, ex_c3 = st.columns(3)
        with ex_c1:
          exp_head = st.selectbox(
              "செலவினத் தலைப்பு (Expense Head) *:",
              [
                  "Rent (வாடகை)",
                  "Electricity (மின் கட்டணம்)",
                  "Staff Salary (சம்பளம்)",
                  (
                      "Water / Staffwelfar (நீர் & பணியாளர் சார் செலவு)"
                  ),
                  "Stationery / Printing (ஸ்டேஷனரி)",
                  "Maintenance / Repair (பராமரிப்பு)",
                  "Transport / Courier (போக்குவரத்து)",
                  "Miscellaneous (இதர செலவுகள்)",
              ],
              key="exp_head_sel",
          )
        with ex_c2:
          actual_exp_amount = st.number_input(
              "உண்மையான செலவுத் தொகை (Actual Expense ₹) *:",
              min_value=1.0,
              step=10.0,
              key="actual_exp_amt",
          )
        with ex_c3:
          exp_ref = st.text_input(
              "வவுச்சர் / பில் எண் *:",
              placeholder="எ.கா: VOU-101...",
              key="exp_ref_in",
          )

        exp_desc = st.text_area(
            "செலவுக்கான விளக்கம் / காரணங்கள் *:",
            placeholder="எ.கா: தேநீர் மற்றும் சிற்றுண்டி வாங்கியது...",
            key="exp_desc_in",
        )

        st.markdown("---")
        col_ex_in, col_ex_out = st.columns(2)

        with col_ex_out:
          st.markdown("##### 📤 நாம் கொடுத்த நோட்டுகள் (Cash OUT):")
          st.caption("செலவுக்காகவும் சில்லறை வாங்குவதற்காகவும் நாம் கொடுத்தவை:")
          o_500 = st.number_input(
              "₹500 கொடுத்தது",
              min_value=0,
              max_value=curr_b_drawer["500"],
              step=1,
              key="ex_out_500",
          )
          o_200 = st.number_input(
              "₹200 கொடுத்தது",
              min_value=0,
              max_value=curr_b_drawer["200"],
              step=1,
              key="ex_out_200",
          )
          o_100 = st.number_input(
              "₹100 கொடுத்தது",
              min_value=0,
              max_value=curr_b_drawer["100"],
              step=1,
              key="ex_out_100",
          )
          o_50 = st.number_input(
              "₹50 கொடுத்தது",
              min_value=0,
              max_value=curr_b_drawer["50"],
              step=1,
              key="ex_out_50",
          )
          o_20 = st.number_input(
              "₹20 கொடுத்தது",
              min_value=0,
              max_value=curr_b_drawer["20"],
              step=1,
              key="ex_out_20",
          )
          o_10 = st.number_input(
              "₹10 கொடுத்தது",
              min_value=0,
              max_value=curr_b_drawer["10"],
              step=1,
              key="ex_out_10",
          )
          o_5 = st.number_input(
              "₹5 கொடுத்தது",
              min_value=0,
              max_value=curr_b_drawer["5"],
              step=1,
              key="ex_out_5",
          )
          o_coins = st.number_input(
              "நாணயங்கள் கொடுத்தது (₹)",
              min_value=0.0,
              max_value=float(curr_b_drawer["coins"]),
              step=1.0,
              key="ex_out_coins",
          )

          total_cash_out = (
              (o_500 * 500)
              + (o_200 * 200)
              + (o_100 * 100)
              + (o_50 * 50)
              + (o_20 * 20)
              + (o_10 * 10)
              + (o_5 * 5)
              + o_coins
          )
          st.markdown(f"**கொடுத்த மொத்தப் பணம்:** `₹{total_cash_out:,.2f}`")

        with col_ex_in:
          st.markdown("##### 📥 கடைக்காரர் திருப்பிக் கொடுத்த மீதி (Cash IN - Return):")
          st.caption("கடைக்காரர் மீதியாகத் திருப்பிக் கொடுத்த நோட்டுகள்:")
          i_500 = st.number_input(
              "₹500 மீதி பெற்றது", min_value=0, step=1, key="ex_in_500"
          )
          i_200 = st.number_input(
              "₹200 மீதி பெற்றது", min_value=0, step=1, key="ex_in_200"
          )
          i_100 = st.number_input(
              "₹100 மீதி பெற்றது", min_value=0, step=1, key="ex_in_100"
          )
          i_50 = st.number_input(
              "₹50 மீதி பெற்றது", min_value=0, step=1, key="ex_in_50"
          )
          i_20 = st.number_input(
              "₹20 மீதி பெற்றது", min_value=0, step=1, key="ex_in_20"
          )
          i_10 = st.number_input(
              "₹10 மீதி பெற்றது", min_value=0, step=1, key="ex_in_10"
          )
          i_5 = st.number_input(
              "₹5 மீதி பெற்றது", min_value=0, step=1, key="ex_in_5"
          )
          i_coins = st.number_input(
              "நாணயங்கள் மீதி பெற்றது (₹)", min_value=0.0, step=1.0, key="ex_in_coins"
          )

          total_cash_in = (
              (i_500 * 500)
              + (i_200 * 200)
              + (i_100 * 100)
              + (i_50 * 50)
              + (i_20 * 20)
              + (i_10 * 10)
              + (i_5 * 5)
              + i_coins
          )
          st.markdown(f"**பெற்ற மீதி மொத்தப் பணம்:** `₹{total_cash_in:,.2f}`")

        net_deducted_cash = total_cash_out - total_cash_in

        st.markdown("---")
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("உண்மையான செலவு", f"₹{actual_exp_amount:,.2f}")
        col_m2.metric(
            "கல்லாவில் குறையும் நிகரப் பணம்", f"₹{net_deducted_cash:,.2f}"
        )

        is_tally = net_deducted_cash == actual_exp_amount
        if is_tally:
          col_m3.success("✅ கணக்கீடு சரியானது!")
        else:
          col_m3.error(
              f"❌ வித்தியாசம்: ₹{abs(actual_exp_amount - net_deducted_cash):,.2f}"
          )

        st.caption(
            "ℹ️ குறிப்பு: ஆப்பரேஷன்ஸ் அங்கீகரித்த பின்னரே கல்லாவில் இருந்து"
            " நிகரப் பணம் கழியும்."
        )

        if st.form_submit_button(
            "செலவுப் பதிவை ஆப்பரேஷன்ஸ் ஒப்புதலுக்கு அனுப்புக", type="primary"
        ):
          if (
              is_tally
              and actual_exp_amount > 0
              and exp_ref.strip()
              and exp_desc.strip()
          ):
            try:
              supabase.table("branch_expenses").insert({
                  "branch_id": st.session_state.branch_id,
                  "expense_date": str(date.today()),
                  "expense_head": exp_head,
                  "amount": float(actual_exp_amount),
                  "voucher_no": exp_ref.strip(),
                  "description": exp_desc.strip(),
                  "denomination_details": {
                      "out": {
                          "500": o_500,
                          "200": o_200,
                          "100": o_100,
                          "50": o_50,
                          "20": o_20,
                          "10": o_10,
                          "5": o_5,
                          "coins": o_coins,
                      },
                      "in": {
                          "500": i_500,
                          "200": i_200,
                          "100": i_100,
                          "50": i_50,
                          "20": i_20,
                          "10": i_10,
                          "5": i_5,
                          "coins": i_coins,
                      },
                      "net_deducted": net_deducted_cash,
                  },
                  "created_by": st.session_state.username,
                  "status": "Pending_Approval",
              }).execute()

              st.success(
                  f"✅ ₹{actual_exp_amount:,.2f} செலவுப் பதிவு ஆப்பரேஷன்ஸ்"
                  " ஒப்புதலுக்கு அனுப்பப்பட்டது!"
              )
              st.rerun()
            except Exception as e:
              st.error(f"பிழை: {e}")
          else:
            st.error(
                "⚠️ உண்மையான செலவுத் தொகையும், (கொடுத்த பணம் - மீதிப் பணம்)"
                " கணக்கீடும் சரியாகப் பொருந்த வேண்டும்."
            )

      st.markdown("---")
      st.subheader("📋 கிளை செலவுகளின் சமீபத்திய நிலை (Expense Logs)")
      b_exp_logs = (
          supabase.table("branch_expenses")
          .select("*")
          .eq("branch_id", st.session_state.branch_id)
          .order("id", desc=True)
          .limit(15)
          .execute()
          .data
          or []
      )
      if b_exp_logs:
        st.dataframe(
            pd.DataFrame([
                {
                    "தேதி": e["expense_date"],
                    "தலைப்பு": e["expense_head"],
                    "தொகை (₹)": f"₹{float(e['amount']):,.2f}",
                    "வவுச்சர் எண்": e.get("voucher_no", "-"),
                    "விவரம்": e.get("description", "-"),
                    "நிலை (Status)": (
                        "🟢 Approved (ஏற்கப்பட்டது)"
                        if e.get("status") == "Approved"
                        else (
                            "🔴 Rejected (மறுக்கப்பட்டது)"
                            if e.get("status") == "Rejected"
                            else "🟡 Pending (ஒப்புதல் நிலுவை)"
                        )
                    ),
                    "பதிவு செய்தவர்": e.get("created_by", "-"),
                }
                for e in b_exp_logs
            ]),
            use_container_width=True,
        )

    elif selected_section == "🏦 HO பணப் பரிமாற்றம்":
      st.subheader(
          "🏦 தலைமையக பணப் பரிமாற்றம் (Head Office ⇄ Branch Fund Transfer"
          " Desk)"
      )
      st.caption(
          "தலைமையகத்திலிருந்து ரொக்கம் பெறுதல் அல்லது தலைமையகத்திற்கு ரொக்கம்"
          " அனுப்புதல். (அனைத்துப் பரிமாற்றங்களும் ஆப்பரேஷன்ஸ் ஒப்புதலுக்குப் பிறகே"
          " கல்லாவில் கணக்கிடப்படும்)."
      )

      curr_b_drawer = get_current_branch_cash_drawer(st.session_state.branch_id)

      with st.expander(
          "💼 தற்போதைய நேரடி கல்லா கையிருப்பு (Live Approved Stock)",
          expanded=False,
      ):
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
        st.markdown(
            "##### 🔄 புதிய பணப் பரிமாற்றப் பதிவு (Submit for Operations"
            " Approval)"
        )
        b_ft_c1, b_ft_c2, b_ft_c3 = st.columns(3)
        with b_ft_c1:
          b_ft_dir = st.selectbox(
              "பரிமாற்ற திசை (Direction) *:",
              [
                  (
                      "HO_TO_BRANCH (தலைமையகத்திலிருந்து கிளைக்கு ரொக்கம் பெறுதல்)"
                  ),
                  (
                      "BRANCH_TO_HO (கிளையிலிருந்து தலைமையகத்திற்கு ரொக்கம்"
                      " அனுப்புதல்)"
                  ),
              ],
              key="b_ft_dir_select",
          )
        with b_ft_c2:
          b_ft_mode = st.selectbox(
              "அனுப்பும் / பெறும் முறை *:",
              ["Cash (ரொக்கம்)", "Bank Transfer (வங்கி வரவு)"],
              key="b_ft_mode_select",
          )
        with b_ft_c3:
          b_ft_ref = st.text_input(
              "குறிப்பு எண் / UTR No / ரசீது எண் *:",
              placeholder="எ.கா: HO-PAY-101 / UTR...",
              key="b_ft_ref_input",
          )

        st.markdown("##### 💵 ரூபாய் நோட்டுகள் விவரம் (Denominations):")
        bf_1, bf_2, bf_3, bf_4 = st.columns(4)
        is_sending_to_ho = "BRANCH_TO_HO" in b_ft_dir

        with bf_1:
          m_500 = (
              max(0, curr_b_drawer["500"]) if is_sending_to_ho else 100000
          )
          b_t_500 = st.number_input(
              f"₹500 {'(இருப்பு:'+str(curr_b_drawer['500'])+')' if is_sending_to_ho else ''}",
              min_value=0,
              max_value=m_500,
              step=1,
              key="bt_500",
          )
          m_20 = max(0, curr_b_drawer["20"]) if is_sending_to_ho else 100000
          b_t_20 = st.number_input(
              f"₹20 {'(இருப்பு:'+str(curr_b_drawer['20'])+')' if is_sending_to_ho else ''}",
              min_value=0,
              max_value=m_20,
              step=1,
              key="bt_20",
          )
        with bf_2:
          m_200 = (
              max(0, curr_b_drawer["200"]) if is_sending_to_ho else 100000
          )
          b_t_200 = st.number_input(
              f"₹200 {'(இருப்பு:'+str(curr_b_drawer['200'])+')' if is_sending_to_ho else ''}",
              min_value=0,
              max_value=m_200,
              step=1,
              key="bt_200",
          )
          m_10 = max(0, curr_b_drawer["10"]) if is_sending_to_ho else 100000
          b_t_10 = st.number_input(
              f"₹10 {'(இருப்பு:'+str(curr_b_drawer['10'])+')' if is_sending_to_ho else ''}",
              min_value=0,
              max_value=m_10,
              step=1,
              key="bt_10",
          )
        with bf_3:
          m_100 = (
              max(0, curr_b_drawer["100"]) if is_sending_to_ho else 100000
          )
          b_t_100 = st.number_input(
              f"₹100 {'(இருப்பு:'+str(curr_b_drawer['100'])+')' if is_sending_to_ho else ''}",
              min_value=0,
              max_value=m_100,
              step=1,
              key="bt_100",
          )
          m_5 = max(0, curr_b_drawer["5"]) if is_sending_to_ho else 100000
          b_t_5 = st.number_input(
              f"₹5 {'(இருப்பு:'+str(curr_b_drawer['5'])+')' if is_sending_to_ho else ''}",
              min_value=0,
              max_value=m_5,
              step=1,
              key="bt_5",
          )
        with bf_4:
          m_50 = max(0, curr_b_drawer["50"]) if is_sending_to_ho else 100000
          b_t_50 = st.number_input(
              f"₹50 {'(இருப்பு:'+str(curr_b_drawer['50'])+')' if is_sending_to_ho else ''}",
              min_value=0,
              max_value=m_50,
              step=1,
              key="bt_50",
          )
          m_coins = (
              float(curr_b_drawer["coins"]) if is_sending_to_ho else 100000.0
          )
          b_t_coins = st.number_input(
              "நாணயங்கள் (₹)",
              min_value=0.0,
              max_value=m_coins,
              step=1.0,
              key="bt_coins",
          )

        calc_b_cash = (
            (b_t_500 * 500)
            + (b_t_200 * 200)
            + (b_t_100 * 100)
            + (b_t_50 * 50)
            + (b_t_20 * 20)
            + (b_t_10 * 10)
            + (b_t_5 * 5)
            + b_t_coins
        )

        if "Cash" in b_ft_mode:
          b_final_fund_amt = float(calc_b_cash)
          st.info(
              f"💵 **நோட்டுகளின் கூட்டுத்தொகை மொத்தத் தொகை: ₹{b_final_fund_amt:,.2f}**"
          )
        else:
          b_final_fund_amt = st.number_input(
              "வங்கிப் பரிவர்த்தனைத் தொகை (₹) *:",
              min_value=0.0,
              step=5000.0,
              key="b_bank_amt_in",
          )

        st.caption(
            "ℹ️ குறிப்பு: இது ஆப்பரேஷன்ஸ் ஒப்புதலுக்குச் செல்லும். ஆப்பரேஷன்ஸ்"
            " அங்கீகரித்த பிறகே கல்லாவில் சேரும் / கழியும்."
        )

        if st.form_submit_button(
            "பணப் பரிமாற்றத்தை ஆப்பரேஷன்ஸ் ஒப்புதலுக்கு அனுப்புக (Submit)",
            type="primary",
        ):
          if b_final_fund_amt > 0:
            pure_dir = (
                "HO_TO_BRANCH"
                if "HO_TO_BRANCH" in b_ft_dir
                else "BRANCH_TO_HO"
            )
            pure_m = "Cash" if "Cash" in b_ft_mode else "Bank Transfer"
            try:
              supabase.table("branch_fund_transfers").insert({
                  "branch_id": st.session_state.branch_id,
                  "transfer_date": str(date.today()),
                  "transfer_type": pure_dir,
                  "amount": b_final_fund_amt,
                  "payment_mode": pure_m,
                  "reference_no": b_ft_ref.strip(),
                  "denomination_details": (
                      {
                          "500": b_t_500,
                          "200": b_t_200,
                          "100": b_t_100,
                          "50": b_t_50,
                          "20": b_t_20,
                          "10": b_t_10,
                          "5": b_t_5,
                          "coins": b_t_coins,
                      }
                      if pure_m == "Cash"
                      else {}
                  ),
                  "created_by": st.session_state.username,
                  "status": "Pending_Approval",
              }).execute()

              st.success(
                  f"✅ ₹{b_final_fund_amt:,.2f} பணப் பரிமாற்றம் ஆப்பரேஷன்ஸ்"
                  " ஒப்புதலுக்கு அனுப்பப்பட்டது!"
              )
              st.rerun()
            except Exception as e:
              st.error(f"பிழை: {e}")
          else:
            st.error("நோட்டுகள் அல்லது பரிமாற்றத் தொகையை உள்ளிடவும்.")

      st.markdown("---")
      st.subheader(
          "📋 உங்கள் கிளையின் சமீபத்திய பணப் பரிமாற்றங்கள் & ஒப்புதல் நிலை"
      )
      b_fund_logs = (
          supabase.table("branch_fund_transfers")
          .select("*")
          .eq("branch_id", st.session_state.branch_id)
          .order("id", desc=True)
          .limit(20)
          .execute()
          .data
          or []
      )
      if b_fund_logs:
        st.dataframe(
            pd.DataFrame([
                {
                    "தேதி": f["transfer_date"],
                    "பரிமாற்றம்": (
                        "📥 HO ➔ கிளைக்கு பணம் பெறுதல்"
                        if f["transfer_type"] == "HO_TO_BRANCH"
                        else "📤 கிளை ➔ HO-க்கு அனுப்புதல்"
                    ),
                    "தொகை (₹)": f"₹{float(f['amount']):,.2f}",
                    "முறை": f["payment_mode"],
                    "நிலை (Status)": (
                        "🟢 Approved (ஏற்கப்பட்டது)"
                        if f.get("status") == "Approved"
                        else (
                            "🔴 Rejected (மறுக்கப்பட்டது)"
                            if f.get("status") == "Rejected"
                            else "🟡 Pending (ஆப்பரேஷன்ஸ் ஒப்புதல் நிலுவை)"
                        )
                    ),
                    "குறிப்பு / UTR": f.get("reference_no", "-"),
                    "பதிவு செய்தவர்": f.get("created_by", "-"),
                }
                for f in b_fund_logs
            ]),
            use_container_width=True,
        )

    elif selected_section == "📈 காரணப் பணியாளர் அறிக்கை":
      render_staff_attribution_report(selected_branch_id=st.session_state.branch_id)
    
    elif selected_section == "📦 நகைப் பாக்கெட்கள் மேலாண்மை":
      st.subheader("📦 நகைப் பாக்கெட்கள் அனுப்புதல், கோருதல் & ஒப்படைத்தல்")
      st.caption(
          "கிளையில் உள்ள பாக்கெட்களை HQ-க்கு அனுப்புதல், மீட்புக் குறிப்புடன்"
          " கோருதல் மற்றும் மீட்காத நகைகளை அட்மின் அனுமதியுடன் திருப்புதல்."
      )

      curr_b_id = st.session_state.get("branch_id")
      staff_uname = st.session_state.get("username", "Staff")

      # 1. இந்த கிளையின் நகைக் கடன்கள் மற்றும் ஜிபி கொள்முதல் விவரங்களை எடுத்தல்
      try:
        b_loans_res = (
            supabase.table("gold_loans")
            .select(
                "id, loan_no, gross_weight, ornament_details,"
                " packet_location, release_requested,"
                " release_request_remarks, return_request_status,"
                " return_reason, status"
            )
            .eq("branch_id", curr_b_id)
            .neq("status", "Closed")
            .execute()
        )
        b_loans = b_loans_res.data or []
      except Exception:
        b_loans = []

      try:
        b_gps_res = (
            supabase.table("gold_purchases")
            .select("id, gp_no, gross_weight, packet_location, disposal_type")
            .eq("branch_id", curr_b_id)
            .execute()
        )
        b_gps = b_gps_res.data or []
      except Exception:
        b_gps = []

      # உள்-டேப்கள் (3 நிலைகள்)
      sub_bp1, sub_bp2, sub_bp3 = st.tabs([
          "🚚 1. தலைமையகத்திற்கு அனுப்புதல் (Dispatch to HQ)",
          "🚨 2. தலைமையகத்திடம் கோருதல் (Request Release)",
          "🤝 3. ஒப்படைத்தல் / அட்மின் அனுமதியுடன் திருப்புதல்",
      ])

      # -----------------------------------------------------------------
      # நிலை 1: கிளையில் உள்ள பாக்கெட்களை HQ-க்கு அனுப்புதல்
      # -----------------------------------------------------------------
      with sub_bp1:
        st.markdown(
            "##### 🚚 கிளையில் உள்ள பாக்கெட்களை தலைமையகத்திற்கு அனுப்புதல்"
        )
        loans_to_send = [
            l
            for l in b_loans
            if l.get("packet_location", "AT_BRANCH") == "AT_BRANCH"
        ]
        gps_to_send = [
            g
            for g in b_gps
            if g.get("packet_location", "AT_BRANCH") == "AT_BRANCH"
        ]

        if not loans_to_send and not gps_to_send:
          st.info(
              "தற்போது கிளையில் தலைமையகத்திற்கு அனுப்ப வேண்டிய பாக்கெட்கள்"
              " ஏதும் இல்லை."
          )
        else:
          if loans_to_send:
            st.write(f"🪙 **நகைக்கடன் பாக்கெட்கள் ({len(loans_to_send)}):**")
            for l in loans_to_send:
              c1, c2, c3 = st.columns([3, 4, 3])
              c1.write(f"🏷️ **{l['loan_no']}**")
              c2.write(
                  f"எடை: **{l['gross_weight']}g** |"
                  f" {l.get('ornament_details', '-')}"
              )
              if c3.button("🚚 HQ-க்கு அனுப்பி வை", key=f"br_disp_l_{l['id']}"):
                supabase.table("gold_loans").update({
                    "packet_location": "IN_TRANSIT_TO_HQ",
                    "packet_dispatched_by": staff_uname,
                    "packet_updated_at": datetime.now().isoformat(),
                }).eq("id", l["id"]).execute()
                st.success(f"{l['loan_no']} தலைமையகத்திற்கு அனுப்பப்பட்டது!")
                st.rerun()

          if gps_to_send:
            st.write(
                f"✨ **ஜிபி நகை வாங்குதல் பாக்கெட்கள் ({len(gps_to_send)}):**"
            )
            for g in gps_to_send:
              gc1, gc2, gc3 = st.columns([3, 4, 3])
              gc1.write(f"🧾 **{g['gp_no']}**")
              gc2.write(f"எடை: **{g['gross_weight']}g** (GP கொள்முதல்)")
              if gc3.button("🚚 HQ-க்கு அனுப்பி வை", key=f"br_disp_g_{g['id']}"):
                supabase.table("gold_purchases").update({
                    "packet_location": "IN_TRANSIT_TO_HQ",
                    "packet_dispatched_by": staff_uname,
                    "packet_updated_at": datetime.now().isoformat(),
                }).eq("id", g["id"]).execute()
                st.success(f"{g['gp_no']} தலைமையகத்திற்கு அனுப்பப்பட்டது!")
                st.rerun()

      # -----------------------------------------------------------------
      # நிலை 2: பாக்கெட்டைத் தேடி, குறிப்புடன் தலைமையகத்திடம் கோருதல்
      # -----------------------------------------------------------------
      with sub_bp2:
        st.markdown(
            "##### 🚨 வாடிக்கையாளர் கடன் அடைப்பிற்காக HQ-டம் பாக்கெட்டைக் கோருதல்"
        )

        # 🔍 1. விரைவுத் தேடல் வசதி (Fast Search Box)
        search_q = st.text_input(
            "🔍 கடன் எண் கொண்டு தேடுக (Quick Search):",
            placeholder="எ.கா: KMK/0087 அல்லது 0087",
            key="br_pkt_search_input",
        )

        hq_hold_loans = [
            l
            for l in b_loans
            if l.get("packet_location") in ["AT_HQ_VAULT", "IN_BANK_LOCKER"]
            and not l.get("release_requested")
        ]

        # தேடல் வடிகட்டல்
        if search_q.strip():
          hq_hold_loans = [
              l
              for l in hq_hold_loans
              if search_q.strip().lower()
              in str(l.get("loan_no", "")).lower()
          ]

        if not hq_hold_loans:
          st.info(
              "தலைமையகப் பாதுகாப்பில் கோருவதற்கு பாக்கெட்கள் ஏதும் இல்லை /"
              " பொருந்தவில்லை."
          )
        else:
          st.caption(f"கண்டறியப்பட்ட பாக்கெட்கள்: **{len(hq_hold_loans)}**")
          for hl in hq_hold_loans:
            with st.expander(
                f"🪙 {hl['loan_no']} | எடை: {hl['gross_weight']}g |"
                f" 🏢 தலைமையகப் பாதுகாப்பில் உள்ளது"
            ):
              with st.form(key=f"br_req_form_{hl['id']}"):
                # 📝 2. குறிப்பு எழுதும் புலம் (Remarks Field)
                req_note = st.text_area(
                    "கோரிக்கைக்கான குறிப்பு / காரணம் (Branch Remarks):",
                    placeholder=(
                        "எ.கா: வாடிக்கையாளர் இன்று மாலை 4 மணிக்கு கடனை அடைத்து"
                        " நகையை மீட்க வருகிறார்."
                    ),
                )
                if st.form_submit_button(
                    "🚨 தலைமையகத்திடம் பாக்கெட்டைக் கோரு (Send Request)"
                ):
                  supabase.table("gold_loans").update({
                      "release_requested": True,
                      "release_request_date": datetime.now().isoformat(),
                      "release_request_remarks": (
                          req_note.strip()
                          if req_note
                          else "காரணம் குறிப்பிடப்படவில்லை"
                      ),
                  }).eq("id", hl["id"]).execute()
                  st.success(
                      f"{hl['loan_no']} அவசரக் கோரிக்கை குறிப்புடன்"
                      " தலைமையகத்திற்கு அனுப்பப்பட்டது!"
                  )
                  st.rerun()

      # -----------------------------------------------------------------
      # நிலை 3: வாடிக்கையாளரிடம் ஒப்படைத்தல் அல்லது அட்மின் அனுமதியுடன் திருப்புதல்
      # -----------------------------------------------------------------
      with sub_bp3:
        st.markdown(
            "##### 🤝 வாடிக்கையாளரிடம் ஒப்படைத்தல் / திருப்பி அனுப்புதல்"
        )
        transit_to_br = [
            l
            for l in b_loans
            if l.get("packet_location") == "IN_TRANSIT_TO_BRANCH"
        ]

        if not transit_to_br:
          st.info("HQ-லிருந்து கிளைக்கு வழியில்/வந்த பாக்கெட்கள் ஏதும் இல்லை.")
        else:
          st.caption("HQ-லிருந்து வந்த பாக்கெட்கள் பட்டியல்:")
          for tb in transit_to_br:
            ret_status = tb.get("return_request_status", "NONE")

            with st.expander(
                f"🏷️ **{tb['loan_no']}** | எடை: {tb['gross_weight']}g | நிலை:"
                f" {ret_status}"
            ):
              col_del, col_ret = st.columns(2)

              # அ. வாடிக்கையாளரிடம் ஒப்படைத்தல்
              with col_del:
                st.write("✅ **வாடிக்கையாளர் நகையை மீட்டுச் சென்றால்:**")
                if st.button(
                    "🤝 வாடிக்கையாளரிடம் ஒப்படைக்கப்பட்டது",
                    key=f"deliv_c_{tb['id']}",
                ):
                  supabase.table("gold_loans").update({
                      "packet_location": "DELIVERED",
                      "return_request_status": "NONE",
                      "packet_updated_at": datetime.now().isoformat(),
                  }).eq("id", tb["id"]).execute()
                  st.success(
                      f"{tb['loan_no']} வாடிக்கையாளரிடம் வெற்றிகரமாக"
                      " ஒப்படைக்கப்பட்டது!"
                  )
                  st.rerun()

              # ஆ. வாடிக்கையாளர் வராததால் திருப்பி அனுப்புதல் (அட்மின் அனுமதி தேவை)
              with col_ret:
                st.write("🔙 **வாடிக்கையாளர் வராததால் HQ-க்கு திருப்புதல்:**")

                if ret_status == "NONE":
                  st.caption(
                      "⚠️ திருப்பி அனுப்ப முதலில் தலைமையக அட்மினிடம் அனுமதி பெற"
                      " வேண்டும்."
                  )
                  with st.form(key=f"ret_req_form_{tb['id']}"):
                    r_reason = st.text_input(
                        "திருப்பி அனுப்பவதற்கான காரணம்:",
                        placeholder=(
                            "எ.கா: வாடிக்கையாளர் பணம் கொண்டுவரவில்லை / வர"
                            " தாமதமாகும் என்றார்."
                        ),
                    )
                    if st.form_submit_button(
                        "📩 அட்மினிடம் அனுமதி கோரு (Request Return)"
                    ):
                      if r_reason.strip():
                        supabase.table("gold_loans").update({
                            "return_request_status": "REQUESTED",
                            "return_reason": r_reason.strip(),
                            "return_requested_at": datetime.now().isoformat(),
                        }).eq("id", tb["id"]).execute()
                        st.warning(
                            "அட்மின் ஒப்புதலுக்காகக் கோரிக்கை அனுப்பப்பட்டுள்ளது!"
                        )
                        st.rerun()
                      else:
                        st.error(
                            "காரணத்தைக் கட்டாயம் குறிப்பிட வேண்டும்!"
                        )

                elif ret_status == "REQUESTED":
                  st.warning(
                      f"⏳ அட்மின் அனுமதிக்காகக் காத்திருக்கிறது...\n(காரணம்:"
                      f" {tb.get('return_reason')})"
                  )

                elif ret_status == "APPROVED":
                  st.success(
                      "✅ அட்மின் அனுமதி வழங்கியுள்ளார்! இப்போது தலைமையகத்திற்கு"
                      " அனுப்பி வைக்கலாம்."
                  )
                  if st.button(
                      "🚚 HQ-க்கு அனுப்பி வை (Dispatch Back to HQ)",
                      key=f"disp_back_{tb['id']}",
                  ):
                    supabase.table("gold_loans").update({
                        "packet_location": "IN_TRANSIT_TO_HQ",
                        "return_request_status": "NONE",
                        "packet_dispatched_by": staff_uname,
                        "packet_updated_at": datetime.now().isoformat(),
                    }).eq("id", tb["id"]).execute()
                    st.success(
                        f"{tb['loan_no']} தலைமையகத்திற்குத் திருப்பி"
                        " அனுப்பப்பட்டது!"
                    )
                    st.rerun()

    elif selected_section == "🏦 நிதிப் பரிமாற்ற ஒப்புதல்":
      st.subheader("🏦 தலைமையக & கிளை நிதிப் பரிமாற்ற ஒப்புதல் மேசை")

      try:
        pending_fund_transfers = (
            supabase.table("branch_fund_transfers")
            .select("*, branches(branch_name)")
            .eq("status", "Pending_Approval")
            .order("id", desc=True)
            .execute()
            .data
            or []
        )
      except Exception as e:
        st.error(f"நிதிப் பரிமாற்றத் தரவுகளைப் பெறுவதில் பிழை: {e}")
        pending_fund_transfers = []

      if not pending_fund_transfers:
        st.info("✅ எந்தப் பணப் பரிமாற்றங்களும் ஒப்புதலுக்கு நிலுவையில் இல்லை.")
      else:
        for f_item in pending_fund_transfers:
          b_name = f_item.get("branches", {}).get("branch_name", "கிளை")
          t_type = f_item.get("transfer_type", "பரிமாற்றம்")
          amt = float(f_item.get("amount", 0))

          with st.expander(f"💰 {t_type} | {b_name} | ₹{amt:,.2f}"):
            col_info1, col_info2 = st.columns(2)
            with col_info1:
              st.write(f"• **கிளை:** {b_name}")
              st.write(f"• **பரிமாற்ற வகை:** {t_type}")
            with col_info2:
              st.write(f"• **தொகை:** ₹{amt:,.2f}")
              st.write(
                  f"• **தேதி:** {f_item.get('created_at', '-')[:10] if f_item.get('created_at') else '-'}"
              )

            st.markdown("##### 💵 டினாமினேஷன் விவரம்:")
            denoms = f_item.get("denomination_details") or {}
            f_items = []
            if isinstance(denoms, dict) and denoms:
              for k, v in denoms.items():
                try:
                  count = (
                      int(float(v)) if v not in (None, "", " ") else 0
                  )
                  if count > 0:
                    f_items.append(f"**₹{k}:** {count}")
                except (ValueError, TypeError):
                  continue
              denom_text = " | ".join(f_items)
              st.info(
                  denom_text
                  if denom_text
                  else "டினாமினேஷன் விவரம் இல்லை"
              )
            else:
              st.json(denoms)

            current_user = st.session_state.get("username", "Admin")
            col_f1, col_f2 = st.columns(2)
            with col_f1:
              if st.button(
                  "✅ அங்கீகரி (Approve)",
                  key=f"app_f_{f_item['id']}",
                  type="primary",
                  use_container_width=True,
              ):
                try:
                  supabase.table("branch_fund_transfers").update({
                      "status": "Approved",
                      "approved_by": current_user,
                  }).eq("id", f_item["id"]).execute()
                  st.success(
                      "✅ நிதிப் பரிமாற்றம் வெற்றிகரமாக அங்கீகரிக்கப்பட்டது!"
                  )
                  st.rerun()
                except Exception as e:
                  st.error(f"பிழை: {e}")

            with col_f2:
              if st.button(
                  "❌ ரத்து செய் (Reject)",
                  key=f"rej_f_{f_item['id']}",
                  type="secondary",
                  use_container_width=True,
              ):
                try:
                  supabase.table("branch_fund_transfers").update({
                      "status": "Rejected",
                      "approved_by": current_user,
                  }).eq("id", f_item["id"]).execute()
                  st.warning(
                      "⚠️ நிதிப் பரிமாற்றம் நிராகரிக்கப்பட்டது / ரத்து"
                      " செய்யப்பட்டது."
                  )
                  st.rerun()
                except Exception as e:
                  st.error(f"பிழை: {e}")

      st.markdown("---")

      # -------------------------------------------------------------
      # 💸 கிளைச் செலவு ஒப்புதல் மேசை
      # -------------------------------------------------------------
      st.subheader(
          "💸 கிளைச் செலவு ஒப்புதல் மேசை (Branch Expenses Approval Desk)"
      )

      try:
        pending_expenses = (
            supabase.table("branch_expenses")
            .select("*, branches(branch_name)")
            .eq("status", "Pending_Approval")
            .order("id", desc=True)
            .execute()
            .data
            or []
        )
      except Exception as e:
        st.error(f"செலவுத் தரவுகளைப் பெறுவதில் பிழை: {e}")
        pending_expenses = []

      if not pending_expenses:
        st.info("✅ ஒப்புதலுக்கு நிலுவையில் உள்ள கிளைச் செலவுகள் எதுவும் இல்லை.")
      else:
        for ex in pending_expenses:
          b_name = ex.get("branches", {}).get("branch_name", "கிளை")
          ex_amt = float(ex.get("amount", 0))

          with st.expander(
              f"📌 செலவு: {ex.get('expense_head', '-')} | கிளை: {b_name} |"
              f" தொகை: ₹{ex_amt:,.2f} | வவுச்சர்: {ex.get('voucher_no', '-')}"
          ):
            col_e1, col_e2 = st.columns(2)
            with col_e1:
              st.write(f"• **செலவுத் தலைப்பு:** {ex.get('expense_head', '-')}")
              st.write(f"• **விளக்கம்:** {ex.get('description', '-')}")
              st.write(f"• **தேதி:** {ex.get('expense_date', '-')}")
            with col_e2:
              st.write(f"• **வவுச்சர் எண்:** `{ex.get('voucher_no', '-')}`")
              st.write(f"• **பதிவு செய்தவர்:** `{ex.get('created_by', '-')}`")
              st.write(f"• **தொகை:** ₹{ex_amt:,.2f}")

            st.markdown("##### 💵 செலவுக்கான டினாமினேஷன் விவரம்:")
            
            ex_denoms = ex.get("denomination_details") or {}
            ex_items = []
            if isinstance(ex_denoms, dict) and ex_denoms:
              for k, v in ex_denoms.items():
                 try:
                   count = int(float(v)) if v not in (None, "", " ") else 0
                   if count > 0:
                    ex_items.append(f"**₹{k}:** {count}")
                 except (ValueError, TypeError):
                   continue
                ex_denom_text = " | ".join(ex_items)
                st.info(
                    ex_denom_text if ex_denom_text else "டினாமினேஷன் விவரம் இல்லை"
                )
              else:
                st.json(ex_denoms)

            current_user = st.session_state.get("username", "Admin")
            col_ex1, col_ex2 = st.columns(2)

            with col_ex1:
              if st.button(
                  "✅ அங்கீகரி (Approve)",
                  key=f"app_ex_{ex['id']}",
                  type="primary",
                  use_container_width=True,
              ):
                try:
                  supabase.table("branch_expenses").update({
                      "status": "Approved",
                      "approved_by": current_user,
                  }).eq("id", ex["id"]).execute()
                  st.success("✅ செலவு வெற்றிகரமாக அங்கீகரிக்கப்பட்டது!")
                  st.rerun()
                except Exception as e:
                  st.error(f"பிழை: {e}")

            with col_ex2:
              if st.button(
                  "❌ ரத்து செய் (Reject)",
                  key=f"rej_ex_{ex['id']}",
                  type="secondary",
                  use_container_width=True,
              ):
                try:
                  supabase.table("branch_expenses").update({
                      "status": "Rejected",
                      "approved_by": current_user,
                  }).eq("id", ex["id"]).execute()
                  st.warning("⚠️ செலவு நிராகரிக்கப்பட்டது.")
                  st.rerun()
                except Exception as e:
                  st.error(f"பிழை: {e}")

    elif selected_section == "👤 புதிய வாடிக்கையாளர் KYC":
      st.subheader("👤 புதிய வாடிக்கையாளர் KYC ஒப்புதல்")
      pending_kyc = (
          supabase.table("customers")
          .select("*")
          .eq("kyc_status", "Pending_KYC_Approval")
          .execute()
          .data
          or []
      )
      if not pending_kyc:
        st.info("✅ எந்த KYC-யும் நிலுவையில் இல்லை.")
      else:
        for pc in pending_kyc:
          with st.expander(f"🆕 {pc['customer_code']} | {pc['name']}"):
            k_c1, k_c2, k_c3 = st.columns([1.5, 1, 1])
            with k_c1:
              st.write(f"👤 பெயர்: {pc['name']} | 📞 {pc['mobile']}")
              st.write(f"🏠 முகவரி: {pc.get('address', '-')}")
            with k_c2:
              if pc.get("photo_url"):
                st.image(pc["photo_url"], width=130)
            with k_c3:
              if pc.get("id_proof_url"):
                st.markdown(f"🪪 [அடையாள ஆவணம்]({pc['id_proof_url']})")
              if pc.get("address_proof_url"):
                st.markdown(f"📄 [முகவரி ஆவணம்]({pc['address_proof_url']})")

            if st.button("✅ அங்கீகரி", key=f"app_k_{pc['id']}", type="primary"):
              supabase.table("customers").update(
                  {"kyc_status": "Approved", "is_active": True}
              ).eq("id", pc["id"]).execute()
              st.success("அங்கீகரிக்கப்பட்டார்!")
              st.rerun()
                
        elif selected_section == "📝 விவரத் திருத்தக் கோரிக்கைகள்":
        st.subheader(
            "📝 வாடிக்கையாளர் விவரத் திருத்தக் கோரிக்கைகள் (Profile Update"
            " Requests)"
        )
        pending_reqs = (
            supabase.table("customer_update_requests")
            .select("*, customers(*), branches(branch_name)")
            .eq("status", "Pending_Approval")
            .order("id", desc=True)
            .execute()
            .data
            or []
        )
        if not pending_reqs:
            st.info("✅ எந்த கோரிக்கைகளும் இல்லை.")
        else:
            for u_req in pending_reqs:
            target_c = u_req.get("customers", {}) or {}
            b_name = u_req.get("branches", {}).get("branch_name", "Branch")
            new_d = u_req.get("updated_data", {}) or {}
            with st.expander(
                f"📌 {target_c.get('name')} | கிளை: {b_name} | காரணம்:"
                f" {u_req.get('change_reason')}"
            ):
                comp_col1, comp_col2 = st.columns(2)
                with comp_col1:
                st.markdown("#### 🔴 பழைய விவரங்கள்")
                st.write(f"பெயர்: {target_c.get('name')}")
                st.write(f"மொபைல்: {target_c.get('mobile')}")
                st.write(f"முகவரி: {target_c.get('address')}")
                with comp_col2:
                st.markdown("#### 🟢 புதிய விவரங்கள்")
                st.write(f"பெயர்: {new_d.get('name')}")
                st.write(f"மொபைல்: {new_d.get('mobile')}")
                st.write(f"முகவரி: {new_d.get('address')}")

                if st.button(
                    "✅ ஏற்றுக்கொள் & புதுப்பி",
                    key=f"app_u_{u_req['id']}",
                    type="primary",
                ):
                supabase.table("customers").update(new_d).eq(
                    "id", target_c["id"]
                ).execute()
                supabase.table("customer_update_requests").update({
                    "status": "Approved",
                    "reviewed_by": st.session_state.username,
                }).eq("id", u_req["id"]).execute()
                st.success("மாற்றப்பட்டது!")
                st.rerun()

        elif selected_section == "🔔 பரிவர்த்தனை அழைப்பு சரிபார்ப்பு":
      st.subheader(
          "📞 பரிவர்த்தனை அழைப்பு சரிபார்ப்பு (Transaction Call Verification)"
      )
      st.caption(
          "கிளை ஊழியர்களால் முடிக்கப்பட்டு, தலைமையக அழைப்புச் சரிபார்ப்புக்காக"
          " உள்ள வருகைகள் மற்றும் அவற்றின் முழுமையான நடவடிக்கைகள்."
      )

      # 1. கிளைப் பெயர்களை மேப் செய்தல் (Foreign Key பிழை வராமல் இருக்க)
      try:
        b_res = (
            supabase.table("branches").select("id, branch_name").execute()
        )
        b_map = {b["id"]: b["branch_name"] for b in (b_res.data or [])}
      except Exception:
        b_map = {}

      # 2. நிலைகள் மற்றும் தேடல் வடிகட்டிகள் (Filters)
      f_col1, f_col2 = st.columns([2, 2])
      with f_col1:
        stat_filter = st.selectbox(
            "📌 வருகை நிலை (Status Filter):",
            [
                "Pending_Calling_Verification",
                "அனைத்தும் (All)",
                "Pending_Branch_Docs",
                "Completed",
                "Needs_Clarification",
            ],
            key="ops_visit_stat_filter",
        )
      with f_col2:
        visit_search = st.text_input(
            "🔍 தேடல் (வருகை எண் / வாடிக்கையாளர் / மொபைல்):",
            placeholder="எ.கா: VST-101 / 98765...",
            key="ops_visit_search_box",
        )

      # 3. Join இன்றி பாதுகாப்பான நேரடி வினவல்
      try:
        q = supabase.table("customer_visits").select("*")
        if stat_filter != "அனைத்தும் (All)":
          q = q.eq("status", stat_filter)

        ops_visits = q.order("id", desc=True).limit(50).execute().data or []
      except Exception as e:
        st.error(f"வருகைகளை எடுப்பதில் பிழை: {e}")
        ops_visits = []

      # உரைத் தேடல் வடிகட்டல்
      if visit_search.strip() and ops_visits:
        s_key = visit_search.strip().lower()
        ops_visits = [
            v
            for v in ops_visits
            if s_key in str(v.get("visit_no", "")).lower()
            or s_key in str(v.get("customer_name", "")).lower()
            or s_key in str(v.get("mobile", "")).lower()
        ]

      # 4. முடிவுகள் மற்றும் விபரங்கள் காட்சி
      if not ops_visits:
        st.info(
            "ℹ️ தேர்ந்தெடுக்கப்பட்ட நிலையில் வருகைகள் எதுவும் தற்போது"
            " நிலுவையில் இல்லை."
        )
      else:
        st.write(f"🔔 கண்டறியப்பட்ட மொத்த வருகைகள்: **{len(ops_visits)}**")

        for item in ops_visits:
          v_id = item["id"]
          v_no = item.get("visit_no", f"VST-{v_id}")
          cust_id = item.get("customer_id")
          b_id = item.get("branch_id")
          b_name = b_map.get(b_id, f"கிளை {b_id}")
          net_amt = float(item.get("net_cash_amount", 0) or 0.0)
          cur_stat = item.get("status", "Pending")

          # அ. வாடிக்கையாளர் விவரங்கள்
          cust = {}
          if cust_id:
            try:
              c_res = (
                  supabase.table("customers")
                  .select("name, mobile, mobile2")
                  .eq("id", cust_id)
                  .execute()
              )
              cust = c_res.data[0] if c_res.data else {}
            except Exception:
              cust = {}

          c_name = cust.get("name", item.get("customer_name", "-"))
          c_mob = cust.get("mobile", item.get("mobile", "-"))
          c_mob2 = cust.get("mobile2", "-")

          # ஆ. இந்த வருகையில் நடந்த அனைத்து நடவடிக்கைகளையும் (Transactions) எடுத்தல்
          try:
            t_res = (
                supabase.table("transactions")
                .select("*")
                .eq("visit_id", v_id)
                .execute()
            )
            visit_txns = t_res.data or []
          except Exception:
            visit_txns = []

          with st.expander(
              f"🔔 வருகை: {v_no} | {c_name} | கிளை: {b_name} | நிகரத் தொகை:"
              f" ₹{net_amt:,.2f} | [நிலை: {cur_stat}]"
          ):
            # ---------------------------------------------------------
            # பிரிவு 1: வாடிக்கையாளர் & கட்டண விபரம்
            # ---------------------------------------------------------
            col_o1, col_o2 = st.columns(2)
            with col_o1:
              st.markdown("##### 👤 வாடிக்கையாளர் விவரங்கள்:")
              st.write(f"• **பெயர்:** `{c_name}`")
              st.write(f"• **முதன்மை எண் (அழைக்க):** 📞 **`{c_mob}`**")
              if c_mob2 and c_mob2 != "-":
                st.write(f"• **கூடுதல் மொபைல்:** `{c_mob2}`")
              st.write(f"• **கிளை:** {b_name}")

            with col_o2:
              st.markdown("##### 💳 பரிவர்த்தனை & செலுத்தும் முறை:")
              st.write(
                  f"• **பரிமாற்ற முறை:** {item.get('payment_mode', 'Cash')}"
              )
              st.write(f"• **கல்லா நிகரத் தொகை:** ₹{net_amt:,.2f}")
              if item.get("bank_reference_no"):
                st.write(
                    f"• **UTR / வங்கி Ref:** `{item.get('bank_reference_no')}`"
                )
              st.write(
                  "• **OTP சரிபார்ப்பு:**"
                  f" {'🟢 Verified' if item.get('otp_verified') else '🔴 Pending'}"
              )
              st.write(f"• **தற்போதைய நிலை:** `{cur_stat}`")

            st.markdown("---")

            # ---------------------------------------------------------
            # பிரிவு 2: இந்த வருகையில் மேற்கொள்ளப்பட்ட அனைத்து நடவடிக்கைகள்
            # ---------------------------------------------------------
            st.markdown(
                "##### 🛒 இந்த வருகையில் மேற்கொள்ளப்பட்ட நடவடிக்கைகள்"
                " (Activities):"
            )

            if visit_txns:
              for idx, t in enumerate(visit_txns, 1):
                t_type = t.get("transaction_type", "Pledge")
                p_amt = float(
                    t.get("paid_amount", t.get("amount", 0)) or 0.0
                )
                r_amt = float(t.get("received_amount", 0) or 0.0)
                g_wt = float(t.get("gross_weight", 0) or 0.0)
                n_wt = float(t.get("net_weight", 0) or 0.0)
                itm_desc = t.get("item_details", "-") or "-"
                staff = t.get("staff_name", "-")
                rem = t.get("remarks", "-") or "-"

                with st.container():
                  st.markdown(
                      f"**{idx}. வகை:** `{t_type}` | **பணியாளர்:** `{staff}`"
                  )
                  t_c1, t_c2, t_c3 = st.columns(3)
                  with t_c1:
                    if p_amt > 0:
                      st.write(
                          "• **பட்டுவாடா (கொடுத்தது):**"
                          f" :green[**₹{p_amt:,.2f}**]"
                      )
                    if r_amt > 0:
                      st.write(
                          "• **வரவு (செலுத்தியது):** :blue[**₹{r_amt:,.2f}**]"
                      )
                  with t_c2:
                    if g_wt > 0 or n_wt > 0:
                      st.write(
                          f"• **எடை:** ஜி: **{g_wt}g** | நெட்: **{n_wt}g**"
                      )
                    st.write(f"• **நகை விபரம்:** {itm_desc}")
                  with t_c3:
                    st.write(f"• **கடன் / ரசீது குறிப்பு:** `{rem}`")
                  st.markdown("")
            else:
              st.warning(
                  "⚠️ இந்த வருகைக்கான நடவடிக்கைகள் 'transactions' அட்டவணையில்"
                  " இன்னும் பதிவாகவில்லை."
              )

            st.markdown("---")

            # ---------------------------------------------------------
            # பிரிவு 3: வாடிக்கையாளரிடம் கேட்க வேண்டிய சரிபார்ப்பு வழிகாட்டி (Script)
            # ---------------------------------------------------------
            with st.expander(
                "📋 வாடிக்கையாளரிடம் கேட்க வேண்டிய சரிபார்ப்பு வினாக்கள்"
                " (Checklist):",
                expanded=False,
            ):
              st.info("""
                            **அழைப்பு வழிகாட்டுதல் (Calling Script):**
                            1. **அறிமுகம்:** *"வணக்கம் [வாடிக்கையாளர் பெயர்] அவர்களே, முத்துசிஸ் கோல்டு கம்பெனி தலைமையகத்திலிருந்து அழைக்கிறோம்."*
                            2. **கிளை வருகை:** *"இன்று எங்கள் [கிளை பெயர்] கிளைக்கு நேரில் வருகை தந்தீர்களா?"*
                            3. **தொகை சரிபார்ப்பு:** 
                               - கடன் பெற்றிருந்தால்: *"உங்களுக்குப் பட்டுவாடா தொகையான ₹[தொகை] ரொக்கமாக / வங்கிக் கணக்கில் சரியாகக் கிடைத்ததா?"*
                               - பணம் செலுத்தியிருந்தால்: *"நீங்கள் செலுத்திய தொகை ₹[தொகை]-க்கு உரிய ரசீது வழங்கப்பட்டதா?"*
                            4. **நகை எடை:** *"நீங்கள் அடகு வைத்த நகையின் எடை [நிகர எடை] கிராம் என்பது சரியாகக் கணக்கிடப்பட்டதா?"*
                            5. **கூடுதல் கட்டணம்:** *"ரசீதில் உள்ள தொகையைத் தவிர வேறு ஏதேனும் கூடுதல் தொகையோ அல்லது கமிஷனோ ஊழியரால் கேட்கப்பட்டதா?"*
                            """)

            # ---------------------------------------------------------
            # பிரிவு 4: அப்ரூவல் / கிளாரிஃபிகேஷன் பொத்தான்கள்
            # ---------------------------------------------------------
            ops_call_remark = st.text_input(
                "அழைப்பு சரிபார்ப்பு குறிப்பு / விளக்கம்:",
                placeholder=(
                    "எ.கா: வாடிக்கையாளரிடம் பேசப்பட்டது, தொகை மற்றும் நகை விவரங்கள்"
                    " உறுதி செய்யப்பட்டன..."
                ),
                key=f"ops_call_rem_{v_id}",
            )

            o_btn1, o_btn2 = st.columns(2)
            with o_btn1:
              if st.button(
                  "✅ தொலைபேசி வழி சரிபார்க்கப்பட்டது (Approve)",
                  key=f"v_call_{v_id}",
                  type="primary",
                  use_container_width=True,
              ):
                try:
                  supabase.table("customer_visits").update({
                      "status": "Pending_Branch_Docs",
                      "verification_remarks": (
                          ops_call_remark.strip()
                          if ops_call_remark.strip()
                          else "Call Verified"
                      ),
                  }).eq("id", v_id).execute()
                  st.success(
                      f"✅ வருகை {v_no} ஆவணப் பதிவேற்றத்திற்கு (Pending Docs)"
                      " அனுப்பப்பட்டது!"
                  )
                  st.rerun()
                except Exception as e:
                  st.error(f"பிழை: {e}")

            with o_btn2:
              if st.button(
                  "⚠️ கிளை விளக்கம் கேட்க (Need Clarification)",
                  key=f"v_clar_{v_id}",
                  type="secondary",
                  use_container_width=True,
              ):
                if not ops_call_remark.strip():
                  st.error(
                      "⚠️ தயவுசெய்து குறிப்பில் என்ன விளக்கம் வேண்டும் என்பதை"
                      " உள்ளிடவும்!"
                  )
                else:
                  try:
                    supabase.table("customer_visits").update({
                        "status": "Needs_Clarification",
                        "verification_remarks": (
                            f"Operations: {ops_call_remark.strip()}"
                        ),
                    }).eq("id", v_id).execute()
                    st.warning("⚠️ விளக்கம் கேட்டு கிளைக்கு அனுப்பப்பட்டது!")
                    st.rerun()
                  except Exception as e:
                    st.error(f"பிழை: {e}")

    elif selected_section == "🛡️ OTP விலக்கு அனுமதி":
      st.subheader("🛡️ OTP விலக்கு இறுதி சரிபார்ப்பு (Operations Clearance)")
      st.caption(
          "அட்மின் ஒப்புதல் வழங்கி, ஆப்பரேஷன்ஸ் குழுவின் இறுதி அனுமதிக்காக"
          " நிலுவையில் உள்ள கோரிக்கைகள்."
      )

      try:
        res = (
            supabase.table("otp_bypass_requests")
            .select("*")
            .eq("status", "Pending Operations")
            .order("id", desc=True)
            .execute()
        )
        pending_ops = res.data or []
      except Exception as e:
        st.error(f"டேட்டாபேஸ் வினவலில் பிழை: {e}")
        pending_ops = []

      if not pending_ops:
        st.info(
            "✅ சரிபார்ப்பிற்கு நிலுவையில் உள்ள OTP விலக்குக் கோரிக்கைகள் எதுவும்"
            " இல்லை."
        )
      else:
        for op_req in pending_ops:
          op_b_id = op_req.get("branch_id")
          b_lbl = f"Branch ID: {op_b_id}"
          if "branch_options" in locals() and branch_options:
            for name, b_id in branch_options.items():
              if str(b_id) == str(op_b_id):
                b_lbl = name
                break

          with st.container(border=True):
            st.markdown(
                f"📍 **கிளை:** `{b_lbl}` | 👤 **வாடிக்கையாளர்:**"
                f" `{op_req.get('customer_name')}` (`{op_req.get('mobile')}`)"
            )
            st.write(
                f"📝 **கோரிய மேலாளர்:** {op_req.get('requested_by')} | **காரணம்:**"
                f" {op_req.get('reason')}"
            )
            st.write(
                f"👤 **அட்மின் ஒப்புதல் அளித்தவர்:**"
                f" `{op_req.get('admin_approved_by')}`"
            )

            op_c1, op_c2 = st.columns(2)
            with op_c1:
              if st.button(
                  "🎯 முழு அனுமதி அளி (Authorize Bypass)",
                  key=f"ops_clr_{op_req['id']}",
                  type="primary",
              ):
                supabase.table("otp_bypass_requests").update({
                    "status": "Approved",
                    "ops_cleared_by": st.session_state.username,
                }).eq("id", op_req["id"]).execute()
                st.success(
                    "முழு அனுமதி வழங்கப்பட்டது! கிளை மேலாளர் OTP இன்றியே"
                    " வருகையை நிறைவு செய்யலாம்."
                )
                st.rerun()
            with op_c2:
              if st.button("❌ நிராகரி (Reject)", key=f"ops_rej_{op_req['id']}"):
                supabase.table("otp_bypass_requests").update(
                    {"status": "Rejected"}
                ).eq("id", op_req["id"]).execute()
                st.warning("கோரிக்கை நிராகரிக்கப்பட்டது.")
                st.rerun()

        elif selected_section == "🔍 தணிக்கையர் பணிப்பாய்வு" or st.session_state.get("user_role") == "Auditor":
            st.header("🔍 தணிக்கையர் பணிப்பாய்வு (Auditor Verification)")
            pending_visits = (
                supabase.table("customer_visits")
                .select("*, customers(*), transactions(*), audit_records(*)")
                .eq("status", "Submitted_to_Auditor")
                .order("id", desc=True)
                .execute()
                .data
                or []
            )

            if not pending_visits:
                st.info("✅ தணிக்கைக்கு நிலுவையில் உள்ள வருகைகள் எதுவும் இல்லை.")
            else:
                for item in pending_visits:
                c_data = item.get("customers", {}) or {}
                hist_remarks = item.get("verification_remarks")

                with st.expander(
                    f"வருகை எண்: {item['visit_no']} | வாடிக்கையாளர்:"
                    f" {c_data.get('name', '-')} | நிகரத் தொகை:"
                    f" ₹{float(item.get('net_cash_amount', 0)):,.2f}"
                ):

                    # 🌟 ஏற்கனவே கேட்கப்பட்ட விளக்கங்கள் மற்றும் கிளை கொடுத்த பதில்கள் இருந்தால் காட்டவும்
                    if hist_remarks and hist_remarks != "Auditor Approved":
                    st.markdown(
                        "##### 📜 முந்தைய விளக்கம் & பதில்களின் வரலாறு (Communication"
                        " Trail):"
                    )
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

                    # புதிய குறிப்பு அல்லது கூடுதல் விளக்கம் கேட்பதற்கான இடம்
                    aud_remarks = st.text_area(
                        "புதிய குறிப்பு / கூடுதல் விளக்கம் (தேவைப்பட்டால் மட்டும்):",
                        placeholder=(
                            "கூடுதல் விளக்கம் கேட்க வேண்டுமெனில் மட்டும் இங்கு எழுதவும்..."
                        ),
                        key=f"aud_rem_{item['id']}",
                    )

                    btn_c1, btn_c2 = st.columns(2)
                    with btn_c1:
                    if st.button(
                        "✅ திருப்திகரமாக உள்ளது - அங்கீகரி (Approve)",
                        key=f"aud_app_{item['id']}",
                        type="primary",
                        use_container_width=True,
                    ):
                        now_str = datetime.now().strftime("%d-%m-%Y %I:%M %p")
                        final_notes = (
                            f"{hist_remarks}\n\n✅ [Auditor Approved at {now_str}]"
                            if hist_remarks
                            else "Auditor Approved"
                        )

                        supabase.table("customer_visits").update({
                            "status": "Approved",
                            "verification_remarks": final_notes,
                        }).eq("id", item["id"]).execute()
                        supabase.table("audit_records").update(
                            {"audit_status": "Approved"}
                        ).eq("visit_id", item["id"]).execute()
                        st.success("✅ முழுமையாக அங்கீகரிக்கப்பட்டது!")
                        st.rerun()

                    with btn_c2:
                    if st.button(
                        "⚠️ மீண்டும் கூடுதல் விளக்கம் கேட்க",
                        key=f"aud_clar_{item['id']}",
                        type="secondary",
                        use_container_width=True,
                    ):
                        if not aud_remarks.strip():
                        st.error(
                            "⚠️ தயவுசெய்து என்ன கூடுதல் விளக்கம் வேண்டும் என்பதை"
                            " உள்ளிடவும்!"
                        )
                        else:
                        now_str = datetime.now().strftime("%d-%m-%Y %I:%M %p")
                        new_query = (
                            f"❓ [Auditor Query ({now_str}) -"
                            f" {st.session_state.username}]:\n{aud_remarks.strip()}"
                        )

                        updated_hist = (
                            f"{hist_remarks}\n\n{new_query}"
                            if hist_remarks
                            else new_query
                        )

                        supabase.table("customer_visits").update({
                            "status": "Needs_Clarification",
                            "verification_remarks": updated_hist,
                        }).eq("id", item["id"]).execute()
                        supabase.table("audit_records").update({
                            "audit_status": "Clarification_Requested"
                        }).eq("visit_id", item["id"]).execute()
                        st.warning(
                            "⚠️ கூடுதல் விளக்கம் கேட்டு கிளைக்கு அனுப்பப்பட்டது!"
                        )
                        st.rerun()
    
    # ----------------------------------------------------
    # D. கிளை செயல்பாடுகள் திரை (BRANCH FLOW)
    # ----------------------------------------------------
    else:
        # 🌟 branch_tab7 (7-வது புதிய டேப்) சேர்க்கப்பட்டுள்ளது:
        branch_tab1, branch_tab2, branch_tab3, branch_tab4, branch_tab5, branch_tab6, branch_tab7 = st.tabs([
            "🛒 கவுண்ட்டர் வருகை & OTP", 
            "📁 கிளை ஆவணங்கள் பதிவேற்றம்",
            "⚠️ விளக்கங்கள்", 
            "💼 கிளை கல்லா", 
            "🏦 HO பணப் பரிமாற்றம்", 
            "📈 காரணப் பணியாளர் அறிக்கை",
            "📦 நகைப் பாக்கெட்கள் மேலாண்மை"  # 👈 7-வது புதிய டேப்!
        ])
        # ==============================================================================
        # 📦 7. கிளை நகைப் பாக்கெட்கள் மேலாண்மை (Branch Packet Management)
        # ==============================================================================
        with branch_tab7:
            st.subheader("📦 நகைப் பாக்கெட்கள் அனுப்புதல், கோருதல் & ஒப்படைத்தல்")
            st.caption("கிளையில் உள்ள பாக்கெட்களை HQ-க்கு அனுப்புதல், மீட்புக் குறிப்புடன் கோருதல் மற்றும் மீட்காத நகைகளை அட்மின் அனுமதியுடன் திருப்புதல்.")

            curr_b_id = st.session_state.get("branch_id")
            staff_uname = st.session_state.get("username", "Staff")

            # 1. இந்த கிளையின் நகைக் கடன்கள் மற்றும் ஜிபி கொள்முதல் விவரங்களை எடுத்தல்
            try:
                b_loans_res = supabase.table("gold_loans").select(
                    "id, loan_no, gross_weight, ornament_details, packet_location, "
                    "release_requested, release_request_remarks, return_request_status, "
                    "return_reason, status"
                ).eq("branch_id", curr_b_id).neq("status", "Closed").execute()
                b_loans = b_loans_res.data or []
            except Exception:
                b_loans = []

            try:
                b_gps_res = supabase.table("gold_purchases").select(
                    "id, gp_no, gross_weight, packet_location, disposal_type"
                ).eq("branch_id", curr_b_id).execute()
                b_gps = b_gps_res.data or []
            except Exception:
                b_gps = []

            # உள்-டேப்கள் (3 நிலைகள்)
            sub_bp1, sub_bp2, sub_bp3 = st.tabs([
                "🚚 1. தலைமையகத்திற்கு அனுப்புதல் (Dispatch to HQ)",
                "🚨 2. தலைமையகத்திடம் கோருதல் (Request Release)",
                "🤝 3. ஒப்படைத்தல் / அட்மின் அனுமதியுடன் திருப்புதல்"
            ])

            # -----------------------------------------------------------------
            # நிலை 1: கிளையில் உள்ள பாக்கெட்களை HQ-க்கு அனுப்புதல்
            # -----------------------------------------------------------------
            with sub_bp1:
                st.markdown("##### 🚚 கிளையில் உள்ள பாக்கெட்களை தலைமையகத்திற்கு அனுப்புதல்")
                loans_to_send = [l for l in b_loans if l.get("packet_location", "AT_BRANCH") == "AT_BRANCH"]
                gps_to_send = [g for g in b_gps if g.get("packet_location", "AT_BRANCH") == "AT_BRANCH"]

                if not loans_to_send and not gps_to_send:
                    st.info("தற்போது கிளையில் தலைமையகத்திற்கு அனுப்ப வேண்டிய பாக்கெட்கள் ஏதும் இல்லை.")
                else:
                    if loans_to_send:
                        st.write(f"🪙 **நகைக்கடன் பாக்கெட்கள் ({len(loans_to_send)}):**")
                        for l in loans_to_send:
                            c1, c2, c3 = st.columns([3, 4, 3])
                            c1.write(f"🏷️ **{l['loan_no']}**")
                            c2.write(f"எடை: **{l['gross_weight']}g** | {l.get('ornament_details', '-')}")
                            if c3.button("🚚 HQ-க்கு அனுப்பி வை", key=f"br_disp_l_{l['id']}"):
                                supabase.table("gold_loans").update({
                                    "packet_location": "IN_TRANSIT_TO_HQ",
                                    "packet_dispatched_by": staff_uname,
                                    "packet_updated_at": datetime.now().isoformat()
                                }).eq("id", l["id"]).execute()
                                st.success(f"{l['loan_no']} தலைமையகத்திற்கு அனுப்பப்பட்டது!")
                                st.rerun()

                    if gps_to_send:
                        st.write(f"✨ **ஜிபி நகை வாங்குதல் பாக்கெட்கள் ({len(gps_to_send)}):**")
                        for g in gps_to_send:
                            gc1, gc2, gc3 = st.columns([3, 4, 3])
                            gc1.write(f"🧾 **{g['gp_no']}**")
                            gc2.write(f"எடை: **{g['gross_weight']}g** (GP கொள்முதல்)")
                            if gc3.button("🚚 HQ-க்கு அனுப்பி வை", key=f"br_disp_g_{g['id']}"):
                                supabase.table("gold_purchases").update({
                                    "packet_location": "IN_TRANSIT_TO_HQ",
                                    "packet_dispatched_by": staff_uname,
                                    "packet_updated_at": datetime.now().isoformat()
                                }).eq("id", g["id"]).execute()
                                st.success(f"{g['gp_no']} தலைமையகத்திற்கு அனுப்பப்பட்டது!")
                                st.rerun()

            # -----------------------------------------------------------------
            # நிலை 2: பாக்கெட்டைத் தேடி, குறிப்புடன் தலைமையகத்திடம் கோருதல்
            # -----------------------------------------------------------------
            with sub_bp2:
                st.markdown("##### 🚨 வாடிக்கையாளர் கடன் அடைப்பிற்காக HQ-டம் பாக்கெட்டைக் கோருதல்")
                
                # 🔍 1. விரைவுத் தேடல் வசதி (Fast Search Box)
                search_q = st.text_input("🔍 கடன் எண் கொண்டு தேடுக (Quick Search):", placeholder="எ.கா: KMK/0087 அல்லது 0087", key="br_pkt_search_input")
                
                hq_hold_loans = [
                    l for l in b_loans 
                    if l.get("packet_location") in ["AT_HQ_VAULT", "IN_BANK_LOCKER"] and not l.get("release_requested")
                ]

                # தேடல் வடிகட்டல்
                if search_q.strip():
                    hq_hold_loans = [l for l in hq_hold_loans if search_q.strip().lower() in str(l.get("loan_no", "")).lower()]

                if not hq_hold_loans:
                    st.info("தலைமையகப் பாதுகாப்பில் கோருவதற்கு பாக்கெட்கள் ஏதும் இல்லை / பொருந்தவில்லை.")
                else:
                    st.caption(f"கண்டறியப்பட்ட பாக்கெட்கள்: **{len(hq_hold_loans)}**")
                    for hl in hq_hold_loans:
                        with st.expander(f"🪙 {hl['loan_no']} | எடை: {hl['gross_weight']}g | 🏢 தலைமையகப் பாதுகாப்பில் உள்ளது"):
                            with st.form(key=f"br_req_form_{hl['id']}"):
                                # 📝 2. குறிப்பு எழுதும் புலம் (Remarks Field)
                                req_note = st.text_area(
                                    "கோரிக்கைக்கான குறிப்பு / காரணம் (Branch Remarks):",
                                    placeholder="எ.கா: வாடிக்கையாளர் இன்று மாலை 4 மணிக்கு கடனை அடைத்து நகையை மீட்க வருகிறார்."
                                )
                                if st.form_submit_button("🚨 தலைமையகத்திடம் பாக்கெட்டைக் கோரு (Send Request)"):
                                    supabase.table("gold_loans").update({
                                        "release_requested": True,
                                        "release_request_date": datetime.now().isoformat(),
                                        "release_request_remarks": req_note.strip() if req_note else "காரணம் குறிப்பிடப்படவில்லை"
                                    }).eq("id", hl["id"]).execute()
                                    st.success(f"{hl['loan_no']} அவசரக் கோரிக்கை குறிப்புடன் தலைமையகத்திற்கு அனுப்பப்பட்டது!")
                                    st.rerun()

            # -----------------------------------------------------------------
            # நிலை 3: வாடிக்கையாளரிடம் ஒப்படைத்தல் அல்லது அட்மின் அனுமதியுடன் திருப்புதல்
            # -----------------------------------------------------------------
            with sub_bp3:
                st.markdown("##### 🤝 வாடிக்கையாளரிடம் ஒப்படைத்தல் / திருப்பி அனுப்புதல்")
                transit_to_br = [l for l in b_loans if l.get("packet_location") == "IN_TRANSIT_TO_BRANCH"]

                if not transit_to_br:
                    st.info("HQ-லிருந்து கிளைக்கு வழியில்/வந்த பாக்கெட்கள் ஏதும் இல்லை.")
                else:
                    st.caption("HQ-லிருந்து வந்த பாக்கெட்கள் பட்டியல்:")
                    for tb in transit_to_br:
                        ret_status = tb.get("return_request_status", "NONE")
                        
                        with st.expander(f"🏷️ **{tb['loan_no']}** | எடை: {tb['gross_weight']}g | நிலை: {ret_status}"):
                            col_del, col_ret = st.columns(2)
                            
                            # அ. வாடிக்கையாளரிடம் ஒப்படைத்தல்
                            with col_del:
                                st.write("✅ **வாடிக்கையாளர் நகையை மீட்டுச் சென்றால்:**")
                                if st.button("🤝 வாடிக்கையாளரிடம் ஒப்படைக்கப்பட்டது", key=f"deliv_c_{tb['id']}"):
                                    supabase.table("gold_loans").update({
                                        "packet_location": "DELIVERED",
                                        "return_request_status": "NONE",
                                        "packet_updated_at": datetime.now().isoformat()
                                    }).eq("id", tb["id"]).execute()
                                    st.success(f"{tb['loan_no']} வாடிக்கையாளரிடம் வெற்றிகரமாக ஒப்படைக்கப்பட்டது!")
                                    st.rerun()

                            # ஆ. வாடிக்கையாளர் வராததால் திருப்பி அனுப்புதல் (அட்மின் அனுமதி தேவை)
                            with col_ret:
                                st.write("🔙 **வாடிக்கையாளர் வராததால் HQ-க்கு திருப்புதல்:**")
                                
                                if ret_status == "NONE":
                                    st.caption("⚠️ திருப்பி அனுப்ப முதலில் தலைமையக அட்மினிடம் அனுமதி பெற வேண்டும்.")
                                    with st.form(key=f"ret_req_form_{tb['id']}"):
                                        r_reason = st.text_input("திருப்பி அனுப்புவதற்கான காரணம்:", placeholder="எ.கா: வாடிக்கையாளர் பணம் கொண்டுவரவில்லை / வர தாமதமாகும் என்றார்.")
                                        if st.form_submit_button("📩 அட்மினிடம் அனுமதி கோரு (Request Return)"):
                                            if r_reason.strip():
                                                supabase.table("gold_loans").update({
                                                    "return_request_status": "REQUESTED",
                                                    "return_reason": r_reason.strip(),
                                                    "return_requested_at": datetime.now().isoformat()
                                                }).eq("id", tb["id"]).execute()
                                                st.warning("அட்மின் ஒப்புதலுக்காகக் கோரிக்கை அனுப்பப்பட்டுள்ளது!")
                                                st.rerun()
                                            else:
                                                st.error("காரணத்தைக் கட்டாயம் குறிப்பிட வேண்டும்!")
                                                
                                elif ret_status == "REQUESTED":
                                    st.warning(f"⏳ அட்மின் அனுமதிக்காகக் காத்திருக்கிறது...\n(காரணம்: {tb.get('return_reason')})")
                                    
                                elif ret_status == "APPROVED":
                                    st.success("✅ அட்மின் அனுமதி வழங்கியுள்ளார்! இப்போது தலைமையகத்திற்கு அனுப்பி வைக்கலாம்.")
                                    if st.button("🚚 HQ-க்கு அனுப்பி வை (Dispatch Back to HQ)", key=f"disp_back_{tb['id']}"):
                                        supabase.table("gold_loans").update({
                                            "packet_location": "IN_TRANSIT_TO_HQ",
                                            "return_request_status": "NONE",
                                            "packet_dispatched_by": staff_uname,
                                            "packet_updated_at": datetime.now().isoformat()
                                        }).eq("id", tb["id"]).execute()
                                        st.success(f"{tb['loan_no']} தலைமையகத்திற்குத் திருப்பி அனுப்பப்பட்டது!")
                                        st.rerun()

        # Tab 6: காரணப் பணியாளர் அறிக்கை
        with branch_tab6:
            render_staff_attribution_report(selected_branch_id=st.session_state.branch_id)

        # Tab 5: தலைமையக பணப் பரிமாற்றம்
        with branch_tab5:
            st.subheader("🏦 தலைமையக பணப் பரிமாற்றம் (Head Office ⇄ Branch Fund Transfer Desk)")
            st.caption("தலைமையகத்திலிருந்து ரொக்கம் பெறுதல் அல்லது தலைமையகத்திற்கு ரொக்கம் அனுப்புதல். (அனைத்துப் பரிமாற்றங்களும் ஆப்பரேஷன்ஸ் ஒப்புதலுக்குப் பிறகே கல்லாவில் கணக்கிடப்படும்).")

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
                with b_ft_c1:
                    b_ft_dir = st.selectbox(
                        "பரிமாற்ற திசை (Direction) *:",
                        [
                            "HO_TO_BRANCH (தலைமையகத்திலிருந்து கிளைக்கு ரொக்கம் பெறுதல்)",
                            "BRANCH_TO_HO (கிளையிலிருந்து தலைமையகத்திற்கு ரொக்கம் அனுப்புதல்)"
                        ],
                        key="b_ft_dir_select"
                    )
                with b_ft_c2:
                    b_ft_mode = st.selectbox("அனுப்பும் / பெறும் முறை *:", ["Cash (ரொக்கம்)", "Bank Transfer (வங்கி வரவு)"], key="b_ft_mode_select")
                with b_ft_c3:
                    b_ft_ref = st.text_input("குறிப்பு எண் / UTR No / ரசீது எண் *:", placeholder="எ.கா: HO-PAY-101 / UTR...", key="b_ft_ref_input")

                st.markdown("##### 💵 ரூபாய் நோட்டுகள் விவரம் (Denominations):")
                bf_1, bf_2, bf_3, bf_4 = st.columns(4)
                is_sending_to_ho = "BRANCH_TO_HO" in b_ft_dir

                with bf_1:
                    m_500 = max(0, curr_b_drawer['500']) if is_sending_to_ho else 100000
                    b_t_500 = st.number_input(f"₹500 {'(இருப்பு:'+str(curr_b_drawer['500'])+')' if is_sending_to_ho else ''}", min_value=0, max_value=m_500, step=1, key="bt_500")
                    m_20 = max(0, curr_b_drawer['20']) if is_sending_to_ho else 100000
                    b_t_20 = st.number_input(f"₹20 {'(இருப்பு:'+str(curr_b_drawer['20'])+')' if is_sending_to_ho else ''}", min_value=0, max_value=m_20, step=1, key="bt_20")
                with bf_2:
                    m_200 = max(0, curr_b_drawer['200']) if is_sending_to_ho else 100000
                    b_t_200 = st.number_input(f"₹200 {'(இருப்பு:'+str(curr_b_drawer['200'])+')' if is_sending_to_ho else ''}", min_value=0, max_value=m_200, step=1, key="bt_200")
                    m_10 = max(0, curr_b_drawer['10']) if is_sending_to_ho else 100000
                    b_t_10 = st.number_input(f"₹10 {'(இருப்பு:'+str(curr_b_drawer['10'])+')' if is_sending_to_ho else ''}", min_value=0, max_value=m_10, step=1, key="bt_10")
                with bf_3:
                    m_100 = max(0, curr_b_drawer['100']) if is_sending_to_ho else 100000
                    b_t_100 = st.number_input(f"₹100 {'(இருப்பு:'+str(curr_b_drawer['100'])+')' if is_sending_to_ho else ''}", min_value=0, max_value=m_100, step=1, key="bt_100")
                    m_5 = max(0, curr_b_drawer['5']) if is_sending_to_ho else 100000
                    b_t_5 = st.number_input(f"₹5 {'(இருப்பு:'+str(curr_b_drawer['5'])+')' if is_sending_to_ho else ''}", min_value=0, max_value=m_5, step=1, key="bt_5")
                with bf_4:
                    m_50 = max(0, curr_b_drawer['50']) if is_sending_to_ho else 100000
                    b_t_50 = st.number_input(f"₹50 {'(இருப்பு:'+str(curr_b_drawer['50'])+')' if is_sending_to_ho else ''}", min_value=0, max_value=m_50, step=1, key="bt_50")
                    m_coins = float(curr_b_drawer['coins']) if is_sending_to_ho else 100000.0
                    b_t_coins = st.number_input(f"நாணயங்கள் (₹)", min_value=0.0, max_value=m_coins, step=1.0, key="bt_coins")

                calc_b_cash = (
                    (b_t_500 * 500) + (b_t_200 * 200) + (b_t_100 * 100) + (b_t_50 * 50) +
                    (b_t_20 * 20) + (b_t_10 * 10) + (b_t_5 * 5) + b_t_coins
                )
                
                if "Cash" in b_ft_mode:
                    b_final_fund_amt = float(calc_b_cash)
                    st.info(f"💵 **நோட்டுகளின் கூட்டுத்தொகை மொத்தத் தொகை: ₹{b_final_fund_amt:,.2f}**")
                else:
                    b_final_fund_amt = st.number_input("வங்கிப் பரிவர்த்தனைத் தொகை (₹) *:", min_value=0.0, step=5000.0, key="b_bank_amt_in")

                st.caption("ℹ️ குறிப்பு: இது ஆப்பரேஷன்ஸ் ஒப்புதலுக்குச் செல்லும். ஆப்பரேஷன்ஸ் அங்கீகரித்த பிறகே கல்லாவில் சேரும் / கழியும்.")

                if st.form_submit_button("பணப் பரிமாற்றத்தை ஆப்பரேஷன்ஸ் ஒப்புதலுக்கு அனுப்புக (Submit)", type="primary"):
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
            st.subheader("📋 உங்கள் கிளையின் சமீபத்திய பணப் பரிமாற்றங்கள் & ஒப்புதல் நிலை")
            b_fund_logs = supabase.table("branch_fund_transfers").select("*").eq("branch_id", st.session_state.branch_id).order("id", desc=True).limit(20).execute().data or []
            if b_fund_logs:
                st.dataframe(pd.DataFrame([{
                    "தேதி": f["transfer_date"],
                    "பரிமாற்றம்": "📥 HO ➔ கிளைக்கு பணம் பெறுதல்" if f["transfer_type"] == "HO_TO_BRANCH" else "📤 கிளை ➔ HO-க்கு அனுப்புதல்",
                    "தொகை (₹)": f"₹{float(f['amount']):,.2f}",
                    "முறை": f["payment_mode"],
                    "நிலை (Status)": "🟢 Approved (ஏற்கப்பட்டது)" if f.get("status") == "Approved" else ("🔴 Rejected (மறுக்கப்பட்டது)" if f.get("status") == "Rejected" else "🟡 Pending (ஆப்பரேஷன்ஸ் ஒப்புதல் நிலுவை)"),
                    "குறிப்பு / UTR": f.get("reference_no", "-"),
                    "பதிவு செய்தவர்": f.get("created_by", "-")
                } for f in b_fund_logs]), use_container_width=True)

        # Tab 4: கிளை கல்லா & செலவுப் பதிவு
        with branch_tab4:
            st.subheader("💸 கிளை செலவுப் பதிவு & சில்லறை மேலாண்மை (Branch Expense Desk)")
            st.caption("செலவுத் தொகைக்கு நாம் கொடுத்த நோட்டுகளையும், கடைக்காரர் திருப்பிக் கொடுத்த மீதி சில்லறையையும் (Cash Return) சரியாக உள்ளிடவும்.")

            curr_b_drawer = get_current_branch_cash_drawer(st.session_state.branch_id)
            total_drawer_cash = (
                (int(curr_b_drawer.get('500', 0)) * 500) +
                (int(curr_b_drawer.get('200', 0)) * 200) +
                (int(curr_b_drawer.get('100', 0)) * 100) +
                (int(curr_b_drawer.get('50', 0)) * 50) +
                (int(curr_b_drawer.get('20', 0)) * 20) +
                (int(curr_b_drawer.get('10', 0)) * 10) +
                (int(curr_b_drawer.get('5', 0)) * 5) +
                float(curr_b_drawer.get('coins', 0.0))
            )
            with st.expander(f"💼 தற்போதைய நேரடி கல்லா கையிருப்பு: ₹{total_drawer_cash:,.2f}", expanded=False):
            # எக்ஸ்பாண்டரின் உள்ளே தலைப்பில் பெரிய மெட்ரிக் ஆகவும் காட்டலாம்
                st.markdown(f"### 💵 கல்லா மொத்த இருப்பு: `₹{total_drawer_cash:,.2f}`")
                st.markdown("---")
            
                bd1, bd2, bd3, bd4 = st.columns(4)
                with bd1:
                    bd1.metric("₹500 தாள்கள்", f"{curr_b_drawer['500']}")
                    bd1.metric("₹20 தாள்கள்", f"{curr_b_drawer['20']}")
                with bd2:
                    bd2.metric("₹200 தாள்கள்", f"{curr_b_drawer['200']}")
                    bd2.metric("₹10 தாள்கள்", f"{curr_b_drawer['10']}")
                with bd3:
                    bd3.metric("₹100 தாள்கள்", f"{curr_b_drawer['100']}")
                    bd3.metric("₹5 தாள்கள்", f"{curr_b_drawer['5']}")
                with bd4:
                    bd4.metric("₹50 தாள்கள்", f"{curr_b_drawer['50']}")
                    bd4.metric("நாணயங்கள் (₹)", f"₹{float(curr_b_drawer['coins']):,.2f}")

            with st.form("branch_expense_flow_form", clear_on_submit=True):
                st.markdown("##### 🔄 புதிய செலவுப் பதிவு (Submit for Operations Approval)")
                ex_c1, ex_c2, ex_c3 = st.columns(3)
                with ex_c1:
                    exp_head = st.selectbox(
                        "செலவினத் தலைப்பு (Expense Head) *:",
                        [
                            "Rent (வாடகை)", "Electricity (மின் கட்டணம்)", "Staff Salary (சம்பளம்)",
                            "Water / Staffwelfar (நீர் & பணியாளர் சார் செலவு)", "Stationery / Printing (ஸ்டேஷனரி)",
                            "Maintenance / Repair (பராமரிப்பு)", "Transport / Courier (போக்குவரத்து)", "Miscellaneous (இதர செலவுகள்)"
                        ],
                        key="exp_head_sel"
                    )
                with ex_c2:
                    actual_exp_amount = st.number_input("உண்மையான செலவுத் தொகை (Actual Expense ₹) *:", min_value=1.0, step=10.0, key="actual_exp_amt")
                with ex_c3:
                    exp_ref = st.text_input("வவுச்சர் / பில் எண் *:", placeholder="எ.கா: VOU-101...", key="exp_ref_in")

                exp_desc = st.text_area("செலவுக்கான விளக்கம் / காரணங்கள் *:", placeholder="எ.கா: தேநீர் மற்றும் சிற்றுண்டி வாங்கியது...", key="exp_desc_in")

                st.markdown("---")
                col_ex_in, col_ex_out = st.columns(2)

                with col_ex_out:
                    st.markdown("##### 📤 நாம் கொடுத்த நோட்டுகள் (Cash OUT):")
                    st.caption("செலவுக்காகவும் சில்லறை வாங்குவதற்காகவும் நாம் கொடுத்தவை:")
                    o_500 = st.number_input("₹500 கொடுத்தது", min_value=0, max_value=curr_b_drawer['500'], step=1, key="ex_out_500")
                    o_200 = st.number_input("₹200 கொடுத்தது", min_value=0, max_value=curr_b_drawer['200'], step=1, key="ex_out_200")
                    o_100 = st.number_input("₹100 கொடுத்தது", min_value=0, max_value=curr_b_drawer['100'], step=1, key="ex_out_100")
                    o_50  = st.number_input("₹50 கொடுத்தது", min_value=0, max_value=curr_b_drawer['50'], step=1, key="ex_out_50")
                    o_20  = st.number_input("₹20 கொடுத்தது", min_value=0, max_value=curr_b_drawer['20'], step=1, key="ex_out_20")
                    o_10  = st.number_input("₹10 கொடுத்தது", min_value=0, max_value=curr_b_drawer['10'], step=1, key="ex_out_10")
                    o_5   = st.number_input("₹5 கொடுத்தது", min_value=0, max_value=curr_b_drawer['5'], step=1, key="ex_out_5")
                    o_coins = st.number_input("நாணயங்கள் கொடுத்தது (₹)", min_value=0.0, max_value=float(curr_b_drawer['coins']), step=1.0, key="ex_out_coins")

                    total_cash_out = (o_500*500) + (o_200*200) + (o_100*100) + (o_50*50) + (o_20*20) + (o_10*10) + (o_5*5) + o_coins
                    st.markdown(f"**கொடுத்த மொத்தப் பணம்:** `₹{total_cash_out:,.2f}`")

                with col_ex_in:
                    st.markdown("##### 📥 கடைக்காரர் திருப்பிக் கொடுத்த மீதி (Cash IN - Return):")
                    st.caption("கடைக்காரர் மீதியாகத் திருப்பிக் கொடுத்த நோட்டுகள்:")
                    i_500 = st.number_input("₹500 மீதி பெற்றது", min_value=0, step=1, key="ex_in_500")
                    i_200 = st.number_input("₹200 மீதி பெற்றது", min_value=0, step=1, key="ex_in_200")
                    i_100 = st.number_input("₹100 மீதி பெற்றது", min_value=0, step=1, key="ex_in_100")
                    i_50  = st.number_input("₹50 மீதி பெற்றது", min_value=0, step=1, key="ex_in_50")
                    i_20  = st.number_input("₹20 மீதி பெற்றது", min_value=0, step=1, key="ex_in_20")
                    i_10  = st.number_input("₹10 மீதி பெற்றது", min_value=0, step=1, key="ex_in_10")
                    i_5   = st.number_input("₹5 மீதி பெற்றது", min_value=0, step=1, key="ex_in_5")
                    i_coins = st.number_input("நாணயங்கள் மீதி பெற்றது (₹)", min_value=0.0, step=1.0, key="ex_in_coins")

                    total_cash_in = (i_500*500) + (i_200*200) + (i_100*100) + (i_50*50) + (i_20*20) + (i_10*10) + (i_5*5) + i_coins
                    st.markdown(f"**பெற்ற மீதி மொத்தப் பணம்:** `₹{total_cash_in:,.2f}`")

                net_deducted_cash = total_cash_out - total_cash_in

                st.markdown("---")
                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("உண்மையான செலவு", f"₹{actual_exp_amount:,.2f}")
                col_m2.metric("கல்லாவில் குறையும் நிகரப் பணம்", f"₹{net_deducted_cash:,.2f}")
                
                is_tally = (net_deducted_cash == actual_exp_amount)
                if is_tally:
                    col_m3.success("✅ கணக்கீடு சரியானது!")
                else:
                    col_m3.error(f"❌ வித்தியாசம்: ₹{abs(actual_exp_amount - net_deducted_cash):,.2f}")

                st.caption("ℹ️ குறிப்பு: ஆப்பரேஷன்ஸ் அங்கீகரித்த பின்னரே கல்லாவில் இருந்து நிகரப் பணம் கழியும்.")

                if st.form_submit_button("செலவுப் பதிவை ஆப்பரேஷன்ஸ் ஒப்புதலுக்கு அனுப்புக", type="primary"):
                    if is_tally and actual_exp_amount > 0 and exp_ref.strip() and exp_desc.strip():
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
                                    "net_deducted": net_deducted_cash
                                },
                                "created_by": st.session_state.username,
                                "status": "Pending_Approval"
                            }).execute()

                            st.success(f"✅ ₹{actual_exp_amount:,.2f} செலவுப் பதிவு ஆப்பரேஷன்ஸ் ஒப்புதலுக்கு அனுப்பப்பட்டது!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"பிழை: {e}")
                    else:
                        st.error("⚠️ உண்மையான செலவுத் தொகையும், (கொடுத்த பணம் - மீதிப் பணம்) கணக்கீடும் சரியாகப் பொருந்த வேண்டும்.")

            st.markdown("---")
            st.subheader("📋 கிளை செலவுகளின் சமீபத்திய நிலை (Expense Logs)")
            b_exp_logs = supabase.table("branch_expenses").select("*").eq("branch_id", st.session_state.branch_id).order("id", desc=True).limit(15).execute().data or []
            if b_exp_logs:
                st.dataframe(pd.DataFrame([{
                    "தேதி": e["expense_date"],
                    "தலைப்பு": e["expense_head"],
                    "தொகை (₹)": f"₹{float(e['amount']):,.2f}",
                    "வவுச்சர் எண்": e.get("voucher_no", "-"),
                    "விவரம்": e.get("description", "-"),
                    "நிலை (Status)": "🟢 Approved (ஏற்கப்பட்டது)" if e.get("status") == "Approved" else ("🔴 Rejected (மறுக்கப்பட்டது)" if e.get("status") == "Rejected" else "🟡 Pending (ஒப்புதல் நிலுவை)"),
                    "பதிவு செய்தவர்": e.get("created_by", "-")
                } for e in b_exp_logs]), use_container_width=True)
                
        # =========================================================================
        # 1-வது டேப்: கவுண்ட்டர் வருகை & OTP (Counter Visit & Flow)
        # =========================================================================
        with branch_tab1:
            staff_res = supabase.table("users").select("name").eq("branch_id", st.session_state.branch_id).eq("is_active", True).execute()
            current_staff_list = ["Walk-in (நேரடி வருகை)"] + [s["name"] for s in staff_res.data] if staff_res.data else ["Walk-in (நேரடி வருகை)"]
            # ---------------------------------------------------------------------
            # 🎉 முந்தைய வருகை வெற்றிகரமாக முடிந்ததற்கான செய்திப் பலகை (Success Card)
            # ---------------------------------------------------------------------
            if st.session_state.get("last_saved_visit"):
                saved = st.session_state["last_saved_visit"]
                
                st.success(
                    f"### 🎉 வருகை வெற்றிகரமாகச் சேமிக்கப்பட்டது!\n\n"
                    f"**வருகை எண்:** `{saved['visit_no']}` &nbsp;|&nbsp; "
                    f"**வாடிக்கையாளர்:** `{saved['customer_name']}` &nbsp;|&nbsp; "
                    f"**நடவடிக்கைகள்:** `{saved['txn_count']} எண்ணம்`\n\n"
                    f"💰 **செலுத்திய தொகை:** ₹{saved['total_paid']:,.2f} &nbsp;|&nbsp; "
                    f"💰 **பெற்ற தொகை:** ₹{saved['total_received']:,.2f}"
                )
                st.balloons()  # வெற்றிகரமான சேமிப்பிற்கான அனிமேஷன்
                
                # அறிவிப்பை மூட:
                if st.button("✖ இந்த அறிவிப்பை மூடு (Close Alert)", key="btn_close_succ_alert"):
                    st.session_state["last_saved_visit"] = None
                    st.rerun()

                st.markdown("---")
            # ---------------------------------------------------------------------
            # படி 1: வாடிக்கையாளர் வருகைப் பதிவு  (Visit Token)
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
                        cust_filter_query = (
                            supabase.table("customers").select("*").eq("is_active", True)
                            .neq("kyc_status", "Rejected").neq("kyc_status", "Pending_KYC_Approval")
                        )
                        if st.session_state.user_role not in ["Admin", "Auditor", "Operations"]:
                            cust_filter_query = cust_filter_query.eq("branch_id", st.session_state.branch_id)

                        matched_custs = cust_filter_query.or_(f"name.ilike.%{q}%,mobile.ilike.%{q}%,customer_code.ilike.%{q}%").limit(20).execute().data or []
                        if matched_custs:
                            cust_dropdown_dict = {f"{c['name']} | {c.get('customer_code', '')} | 📞 {c.get('mobile', '')}": c for c in matched_custs}
                            selected_label = st.selectbox("வாடிக்கையாளர் பட்டியல்:", options=list(cust_dropdown_dict.keys()), key="dd_cust_sel")
                            selected_cust = cust_dropdown_dict[selected_label]

                            existing_req_check = (
                                supabase.table("customer_update_requests").select("*")
                                .eq("customer_id", selected_cust["id"]).eq("status", "Pending_Approval").order("id", desc=True).limit(1).execute().data or []
                            )
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
                                        # ✅ புதிய கிளை வாரியான வரிசை எண் உருவாக்கம்:
                                        b_code = st.session_state.get("branch_code", st.session_state.get("branch", "BR")[:3]).upper()
                                        v_token = generate_branch_visit_no(st.session_state.branch_id, b_code)

                                        st.session_state.current_visit = {
                                            "visit_no": v_token,
                                            "customer_id": selected_cust["id"],
                                            "customer_name": selected_cust["name"],
                                            "customer_code": selected_cust.get("customer_code", ""),
                                            "mobile": selected_cust.get("mobile", ""),
                                            "address": selected_cust.get("address", ""),
                                            "step": "TRANSACTIONS"
                                        }
                                        st.session_state.transactions_cart = []
                                        st.session_state.gp_ornament_rows = [{"item": "", "count": 1, "gross_wt": 0.0, "net_wt": 0.0, "purity": "916 KDM"}]

                                        # 👈👈👈 🌟 புதிய வருகைக்காக OTP நிலைகளை முழுமையாக ரீசெட் செய்தல்:
                                        st.session_state.otp_cleared = False
                                        st.session_state.otp_already_sent = False
                                        st.session_state.generated_otp = None
                                        if "otp_bypass_requested" in st.session_state:
                                            st.session_state.otp_bypass_requested = False

                                        st.rerun()

                            with st.expander(f"✏️ {selected_cust['name']} விவரங்களில் மாற்றம் செய்ய கோரிக்கை அனுப்புக"):
                                if has_pending_update_req:
                                    st.error("🚫 ஏற்கனவே அனுப்பிய விவரத் திருத்தக் கோரிக்கை ஆப்பரேஷன்ஸ் ஒப்புதலுக்காக நிலுவையில் உள்ளது!")
                                else:
                                    u_c1, u_c2 = st.columns(2)
                                    with u_c1:
                                        req_name = st.text_input("பெயர்", value=selected_cust.get("name", "") or "", key=f"rn_{selected_cust['id']}")
                                        req_guard = st.text_input("கார்டியன் பெயர்", value=selected_cust.get("guardian_name", "") or "", key=f"rg_{selected_cust['id']}")
                                        req_mob = st.text_input("புதிய முதன்மை மொபைல் எண்", value=selected_cust.get("mobile", "") or "", key=f"rm_{selected_cust['id']}")
                                        req_mob2 = st.text_input("கூடுதல் மொபைல் எண்", value=selected_cust.get("mobile2", "") or "", key=f"rm2_{selected_cust['id']}")
                                    with u_c2:
                                        req_addr = st.text_area("புதிய முகவரி", value=selected_cust.get("address", "") or "", height=80, key=f"ra_{selected_cust['id']}")
                                        req_reason = st.text_input("விவர மாற்றத்திற்கான காரணம் *:", placeholder="எ.கா: முகவரி மாற்றம்", key=f"rr_{selected_cust['id']}")

                                    doc_r1, doc_r2, doc_r3 = st.columns(3)
                                    with doc_r1:
                                        req_photo = st.file_uploader("புதிய புகைப்படம்:", type=["jpg", "jpeg", "png"], key=f"r_p_{selected_cust['id']}")
                                    with doc_r2:
                                        req_id_doc = st.file_uploader("புதிய அடையாள ஆவணம்:", type=["jpg", "jpeg", "png", "pdf"], key=f"r_id_{selected_cust['id']}")
                                    with doc_r3:
                                        req_proof = st.file_uploader("மாற்றத்திற்கான ஆதாரம்:", type=["jpg", "jpeg", "png", "pdf"], key=f"r_prf_{selected_cust['id']}")

                                    if st.button("ஆப்பரேஷன்ஸ் ஒப்புதலுக்கு அனுப்புக ➔", key=f"btn_send_req_{selected_cust['id']}", type="primary"):
                                        if not req_reason.strip():
                                            st.error("⚠️ தயவுசெய்து மாற்றத்திற்கான காரணத்தைக் குறிப்பிடவும்!")
                                        else:
                                            with st.spinner("கோரிக்கை அனுப்பப்படுகிறது..."):
                                                try:
                                                    new_photo_link = upload_single_file(req_photo, "customer_photos") if req_photo else selected_cust.get("photo_url")
                                                    new_id_link = upload_single_file(req_id_doc, "customer_id_proofs") if req_id_doc else selected_cust.get("id_proof_url")
                                                    proof_link = upload_single_file(req_proof, "update_proofs") if req_proof else None

                                                    request_payload = {
                                                        "customer_id": selected_cust["id"],
                                                        "branch_id": st.session_state.branch_id,
                                                        "requested_by": st.session_state.username,
                                                        "updated_data": {
                                                            "name": req_name.strip(),
                                                            "guardian_name": req_guard.strip(),
                                                            "mobile": req_mob.strip(),
                                                            "mobile2": req_mob2.strip(),
                                                            "address": req_addr.strip(),
                                                            "photo_url": new_photo_link,
                                                            "id_proof_url": new_id_link
                                                        },
                                                        "change_reason": req_reason.strip(),
                                                        "proof_document_url": proof_link,
                                                        "status": "Pending_Approval"
                                                    }

                                                    insert_res = supabase.table("customer_update_requests").insert(request_payload).execute()
                                                    if insert_res.data:
                                                        st.success("✅ கோரிக்கை ஆப்பரேஷன்ஸ் குழுவுக்கு வெற்றிகரமாக அனுப்பப்பட்டது!")
                                                        st.rerun()
                                                    else:
                                                        st.error("டேட்டாபேஸில் பதிவு செய்ய முடியவில்லை. விவரங்களைச் சரிபார்க்கவும்.")
                                                except Exception as err:
                                                    st.error(f"❌ கோரிக்கை அனுப்புவதில் பிழை: {err}")

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

                                tcode = f"CUST-{datetime.now().strftime('%m%d%H%M%S')}"
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

                # 🌟 கவுண்டரை ஆரம்பத்தில் மட்டும் உருவாக்குங்கள் (இங்கு கூட்டக் கூடாது!)
                if "form_reset_counter" not in st.session_state:
                    st.session_state.form_reset_counter = 0
                fc = st.session_state.form_reset_counter

                active_g_schemes, active_fd_schemes, active_rd_schemes = get_cached_master_schemes()

                g_scheme_map = {s["scheme_name"]: s for s in active_g_schemes}
                gold_scheme_options = list(g_scheme_map.keys()) if g_scheme_map else ["General 12%"]
                fd_scheme_options = [s["scheme_name"] for s in active_fd_schemes] if active_fd_schemes else ["Standard FD 9.5%"]
                rd_scheme_options = [s["scheme_name"] for s in active_rd_schemes] if active_rd_schemes else ["Standard RD 10%"]

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

                col_st1, col_st2 = st.columns(2)
                with col_st1:
                    staff = st.selectbox("காரணப் பணியாளர்:", current_staff_list)
                with col_st2:
                    custom_remarks = st.text_input("கூடுதல் குறிப்பு:", placeholder="எ.கா: சிறப்பு தள்ளுபடி")

                st.markdown("---")
                paid_amt, received_amt, detail_summary = 0.0, 0.0, []
                ornament_details = None
                other_charges = 0.0
                total_weight = 0.0
                net_weight = 0.0
                gp_number = None
                ref1_name, ref1_phone = None, None
                ref2_name, ref2_phone = None, None
                principal_amount = 0.0
                interest_amount = 0.0
                nominee_name, nominee_relation, nominee_address = None, None, None
                ornament_file = None

                # 1. நகைக்கடன் (Pledge)
                if "Pledge" in txn_category:
                    # 🌟 அட்மின் திட்டங்களை எடுத்தல்
                    db_schemes = get_active_loan_schemes()
                    scheme_map = {s["scheme_name"]: s for s in db_schemes} if db_schemes else {}
                    
                    pl_col1, pl_col2, pl_col3 = st.columns(3)
            
                    with pl_col1:
                        # 🌟 கார்ட்டின் நிலைக்கு ஏற்ப மாறும் ஆட்டோ எண்
                        suggested_gl, next_seq_num = get_current_display_gl_number(st.session_state.branch_id)
                        
                        new_gl_no = st.text_input(
                            "கடன் எண் (Auto Generated GL No) *", 
                            value=suggested_gl, 
                            disabled=True, 
                            key=f"gl_no_in_{fc}"
                        )
                        
                        # திட்டங்கள் தேர்வுப் பட்டியல் (Scheme Dropdown)
                        scheme_options = list(scheme_map.keys()) if scheme_map else ["Standard Gold Loan"]
                        selected_scheme = st.selectbox(
                            "அட்மின் நகைக் கடன் திட்டம் (Scheme) *", 
                            options=scheme_options, 
                            key=f"sch_sel_{fc}"
                        )
                        scheme_name = selected_scheme
                        cur_scheme = scheme_map.get(selected_scheme, {})
                        cur_rpg = float(cur_scheme.get("max_rate_per_gram", 0.0))
                        cur_roi = float(cur_scheme.get("interest_rate", 18.0))
                        cur_tenure = int(cur_scheme.get("tenure_months", 12))

                    with pl_col2:
                        total_weight = st.number_input("மொத்த எடை (Gross Weight - gms) *", min_value=0.0, step=0.001, format="%.3f", key=f"gwt_in_{fc}")
                        net_weight = st.number_input("நிகர எடை (Net Weight - gms) *", min_value=0.0, step=0.001, format="%.3f", key=f"nwt_in_{fc}")

                    with pl_col3:
                        paid_amt = st.number_input("கடன் தொகை (Paid ₹) *", min_value=0.0, step=500.0, key=f"amt_in_{fc}")
                        other_charges = st.number_input("இதர கட்டணங்கள் (Other Charges ₹)", min_value=0.0, step=10.0, key=f"chg_in_{fc}")

                    # 💡 திட்டத்தின் வட்டி மற்றும் அதிகபட்ச கடன் தகுதியைக் காட்டுதல்
                    max_eligible = net_weight * cur_rpg if cur_rpg > 0 else 0.0
                    info_col1, info_col2, info_col3 = st.columns(3)
                    with info_col1:
                        st.caption(f"📈 ஆண்டு வட்டி: **{cur_roi}%** ({cur_roi/12:.2f}% / மாதம்)")
                    with info_col2:
                        st.caption(f"⏳ கால அளவு: **{cur_tenure} மாதங்கள்**")
                    with info_col3:
                        if cur_rpg > 0:
                            st.caption(f"💰 அதிகபட்ச கடன் தகுதி (RPG ₹{cur_rpg:,.2f}): **₹{max_eligible:,.2f}**")

                    ornament_details = st.text_area("நகை விபரம்", key=f"orn_det_{fc}")
                    ornament_file = st.file_uploader("நகை படம்", type=["jpg", "jpeg", "png"], key=f"orn_file_{fc}")
                    detail_summary = [
                        f"GL: {new_gl_no}", 
                        f"ஸ்கீம்: {selected_scheme}", 
                        f"வட்டி: {cur_roi}%",
                        f"RPG: ₹{cur_rpg:,.2f}", 
                        f"எடை: {net_weight:.3f}g"
                    ]
                # -------------------------------------------------------------
                # 2. அடமானம் மீட்டல் (GL Release)
                # -------------------------------------------------------------
                elif txn_category == "GL Release (அடமானம் மீட்டல்)":
                    v_info = st.session_state.get("current_visit", {}) or (visit if 'visit' in locals() else {})
                    cust_id = v_info.get("customer_id")
                    cust_mobile = v_info.get("mobile") or v_info.get("customer_mobile") or v_info.get("phone") or ""
                    cust_name = v_info.get("customer_name") or v_info.get("name") or ""
                    
                    # 🌟 நடப்பு கிளையின் ஐடி (branch_id) மற்றும் வாடிக்கையாளர் ஐடி இணைக்கப்பட்டு துல்லியமாக எடுத்தல்:
                    active_loans = get_customer_active_loans(
                        customer_id=cust_id,
                        customer_mobile=cust_mobile, 
                        customer_name=cust_name,
                        branch_id=st.session_state.get("branch_id")
                    )
                    
                    loan_display_map = {
                        f"📌 {l['gl_no']} (அசல்: ₹{l['principal']:,.2f}, எடை: {l['net_wt']:.2f}g | {l.get('scheme_name', '')})": l 
                        for l in active_loans
                    }

                    if not loan_display_map:
                        st.warning("⚠️ இந்த வாடிக்கையாளருக்கு இந்தக் கிளையில் நிலுவையில் உள்ள அடமானக் கடன்கள் எதுவும் இல்லை!")
                        selected_gl_no = ""
                        rel_gl_no = ""
                        selected_loan_db_id = None
                        auto_principal = 0.0
                    else:
                        selected_loan_label = st.selectbox(
                            "அடமானக் கடன் எண்ணைத் தேர்ந்தெடுக்கவும் *",
                            options=list(loan_display_map.keys()),
                            key=f"loan_sel_{fc}"
                        )
                        chosen_loan = loan_display_map[selected_loan_label]
                        selected_gl_no = chosen_loan["gl_no"]
                        rel_gl_no = chosen_loan["gl_no"]
                        selected_loan_db_id = chosen_loan["id"]
                        auto_principal = float(chosen_loan["principal"])

                    r_col1, r_col2 = st.columns(2)
                    with r_col1:
                        principal_amount = st.number_input("அசல் தொகை (₹) *", value=auto_principal, min_value=0.0, step=500.0, key=f"rel_pr_in_{fc}")
                        interest_amount = st.number_input("வட்டித் தொகை (₹) *", min_value=0.0, step=50.0, key=f"rel_int_in_{fc}")
                    with r_col2:
                        other_charges = st.number_input("இதர கட்டணம் (₹)", min_value=0.0, step=10.0, key=f"rel_oth_in_{fc}")
                        received_amt = principal_amount + interest_amount + other_charges
                        st.info(f"💰 பெற வேண்டிய மொத்தத் தொகை: ₹{received_amt:,.2f}")

                    detail_summary = [f"GL: {rel_gl_no}", f"அசல்: ₹{principal_amount}", f"வட்டி: ₹{interest_amount}"]

                # -------------------------------------------------------------
                # 3. அசல் வரவு & வட்டி வரவு (Interest Payment & Part Payment)
                # -------------------------------------------------------------
                elif txn_category in ["Interest Payment (வட்டி வரவு)", "Part Payment (அசல் வரவு)"]:
                    v_info = st.session_state.get("current_visit", {}) or (visit if 'visit' in locals() else {})
                    cust_id = v_info.get("customer_id")
                    cust_mobile = v_info.get("mobile") or v_info.get("customer_mobile") or v_info.get("phone") or ""
                    cust_name = v_info.get("customer_name") or v_info.get("name") or ""
                    
                    # 🌟 நடப்பு கிளையின் ஐடி (branch_id) மற்றும் வாடிக்கையாளர் ஐடி இணைக்கப்பட்டு துல்லியமாக எடுத்தல்:
                    active_loans = get_customer_active_loans(
                        customer_id=cust_id,
                        customer_mobile=cust_mobile, 
                        customer_name=cust_name,
                        branch_id=st.session_state.get("branch_id")
                    )
                    
                    loan_display_map = {
                        f"📌 {l['gl_no']} (அசல்: ₹{l['principal']:,.2f}, எடை: {l['net_wt']:.2f}g | {l.get('scheme_name', '')})": l 
                        for l in active_loans
                    }

                    if not loan_display_map:
                        st.warning("⚠️ இந்த வாடிக்கையாளருக்கு இந்தக் கிளையில் நிலுவையில் உள்ள அடமானக் கடன்கள் எதுவும் இல்லை!")
                        part_gl_no = ""
                        selected_gl_no = ""
                        selected_loan_db_id = None
                        auto_principal = 0.0
                    else:
                        selected_loan_label = st.selectbox(
                            "கடன் எண்ணைத் தேர்ந்தெடுக்கவும் *",
                            options=list(loan_display_map.keys()),
                            key=f"part_int_loan_sel_{fc}"
                        )
                        chosen_loan = loan_display_map[selected_loan_label]
                        part_gl_no = chosen_loan["gl_no"]
                        selected_gl_no = chosen_loan["gl_no"]
                        selected_loan_db_id = chosen_loan["id"]
                        auto_principal = float(chosen_loan["principal"])

                    i_col1, i_col2 = st.columns(2)
                    with i_col1:
                        principal_amount = st.number_input("அசல் தொகை (₹)", value=auto_principal if "Part" in txn_category else 0.0, min_value=0.0, step=100.0, key=f"pi_pr_{fc}")
                    with i_col2:
                        interest_amount = st.number_input("வட்டித் தொகை (₹)", min_value=0.0, step=50.0, key=f"pi_int_{fc}")
                    
                    received_amt = principal_amount + interest_amount
                    st.info(f"💰 பெற வேண்டிய மொத்தத் தொகை: ₹{received_amt:,.2f}")
                    detail_summary = [f"GL: {part_gl_no}", f"அசல்: ₹{principal_amount}", f"வட்டி: ₹{interest_amount}"]

                # 4. Take Over
                elif txn_category == "Take Over (பிற நிறுவன கடன் மீட்டல்)":
                    to_col1, to_col2 = st.columns(2)
                    with to_col1:
                        bank_source = st.text_input("முந்தைய நிறுவனம் *")
                        prev_loan_no = st.text_input("முந்தைய லோன் எண் *")
                    with to_col2:
                        paid_amt = st.number_input("செலுத்திய தொகை (₹) *", min_value=0.0, step=500.0)
                    detail_summary = [f"வங்கி: {bank_source}", f"கடன் எண்: {prev_loan_no}"]

                # -------------------------------------------------------------
                # 5. FD Open (புதிய வைப்பு நிதி - Auto Account No)
                # -------------------------------------------------------------
                elif txn_category == "FD Open (புதிய வைப்பு நிதி)":
                    st.markdown("##### 📑 புதிய FD கணக்கு விவரங்கள் & நாமினி")
                    fd_c1, fd_c2 = st.columns(2)
                    with fd_c1:
                        auto_fd_no = generate_fd_account_no(st.session_state.branch_id)
                        fd_acc_no = st.text_input("FD கணக்கு எண்:", value=auto_fd_no, disabled=True, key=f"fd_acc_box_{auto_fd_no}")
                        fd_sel_scheme = st.selectbox("அட்மின் FD திட்டம் (Scheme) *", fd_scheme_options)
                        received_amt = st.number_input("வைப்புத் தொகை (Deposit ₹) *", min_value=0.0, step=1000.0)
                        fd_nominee = st.text_input("நாமினி பெயர் *")
                    with fd_c2:
                        fd_relation = st.text_input("உறவுமுறை *")
                        fd_age = st.number_input("வயது *", min_value=1, max_value=120, value=30)
                        fd_address = st.text_area("நாமினி முகவரி *", height=82)
                    
                    acc_no = fd_acc_no
                    detail_summary = [f"FD No: {fd_acc_no}", f"Scheme: {fd_sel_scheme}", f"Dep: ₹{received_amt:,.2f}", f"Nominee: {fd_nominee}"]
                    extra_meta_data = {
                        "account_no": fd_acc_no,
                        "deposit_amount": received_amt,
                        "nominee": fd_nominee,
                        "relation": fd_relation,
                        "age": fd_age,
                        "address": fd_address
                    }

                # -------------------------------------------------------------
                # 6. RD Open (புதிய RD சேமிப்பு - Auto Account No)
                # -------------------------------------------------------------
                elif txn_category == "RD Open (புதிய RD சேமிப்பு)":
                    st.markdown("##### 📈 புதிய RD கணக்கு விவரங்கள் & நாமினி")
                    rd_c1, rd_c2 = st.columns(2)
                    with rd_c1:
                        auto_rd_no = generate_rd_account_no(st.session_state.branch_id)
                        rd_acc_no = st.text_input("RD கணக்கு எண்:", value=auto_rd_no, disabled=True, key=f"rd_acc_box_{auto_rd_no}")
                        rd_sel_scheme = st.selectbox("அட்மின் RD திட்டம் (Scheme) *", rd_scheme_options)
                        received_amt = st.number_input("முதல் தவணைத் தொகை (Installment ₹) *", min_value=0.0, step=500.0)
                        rd_nominee = st.text_input("நாமினி பெயர் *")
                    with rd_c2:
                        rd_relation = st.text_input("உறவுமுறை *")
                        rd_age = st.number_input("வயது *", min_value=1, max_value=120, value=30, key="rd_age_in")
                        rd_address = st.text_area("நாமினி முகவரி *", height=82, key="rd_addr_in")
                    
                    acc_no = rd_acc_no
                    detail_summary = [f"RD No: {rd_acc_no}", f"Scheme: {rd_sel_scheme}", f"Inst: ₹{received_amt:,.2f}", f"Nominee: {rd_nominee}"]
                    extra_meta_data = {
                        "account_no": rd_acc_no,
                        "installment_amount": received_amt,
                        "nominee": rd_nominee,
                        "relation": rd_relation,
                        "age": rd_age,
                        "address": rd_address
                    }

                # -------------------------------------------------------------
                # 7. RD தவணை செலுத்துதல் (RD Due - Auto Account Fetch)
                # -------------------------------------------------------------
                elif "RD" in txn_category and ("தவணை" in txn_category or "Due" in txn_category):
                    st.markdown("##### 📈 RD தவணை செலுத்துதல்")
                    c_id = visit.get("customer_id")
                    cust_rds = get_customer_rd_accounts(c_id) if c_id else []

                    c1, c2 = st.columns(2)
                    with c1:
                        if cust_rds:
                            rd_options = [r["acc_no"] for r in cust_rds] + ["கைமுறையாக உள்ளிட (Manual)"]
                            sel_rd = st.selectbox("RD கணக்கு எண் தேர்ந்தெடுக்கவும் *", rd_options, key="rd_due_sel")
                            if sel_rd == "கைமுறையாக உள்ளிட (Manual)":
                                acc_no = st.text_input("RD கணக்கு எண் உள்ளிடவும் *", key="rd_due_man_acc")
                                default_inst = 500.0
                            else:
                                acc_no = sel_rd
                                matched = next((r for r in cust_rds if r["acc_no"] == sel_rd), None)
                                default_inst = float(matched["installment_amount"]) if matched else 500.0
                        else:
                            st.info("💡 இந்த வாடிக்கையாளருக்கு முந்தைய RD கணக்குகள் கண்டறியப்படவில்லை.")
                            acc_no = st.text_input("RD கணக்கு எண் உள்ளிடவும் *", key="rd_due_empty_acc")
                            default_inst = 500.0

                    with c2:
                        received_amt = st.number_input("பெற்ற தவணைத் தொகை (₹) *", min_value=0.0, value=default_inst, step=100.0, key="rd_due_amt")

                    detail_summary = [f"RD No: {acc_no}", f"Due Amount: ₹{received_amt:,.2f}"]
                    extra_meta_data = {"account_no": acc_no, "installment_amount": received_amt}

                # -------------------------------------------------------------
                # 8. RD முதிர்வு / முடித்தல் (RD Closure - Auto Account Fetch)
                # -------------------------------------------------------------
                elif "RD" in txn_category and ("Closure" in txn_category or "முதிர்வு" in txn_category or "முடித்தல்" in txn_category):
                    st.markdown("##### 📉 RD முதிர்வு / கணக்கு முடித்தல்")
                    c_id = visit.get("customer_id")
                    cust_rds = get_customer_rd_accounts(c_id) if c_id else []

                    c1, c2 = st.columns(2)
                    with c1:
                        if cust_rds:
                            rd_options = [r["acc_no"] for r in cust_rds] + ["கைமுறையாக உள்ளிட (Manual)"]
                            sel_rd = st.selectbox("கணக்கு எண் (தேர்ந்தெடுக்கவும்) *", rd_options, key="rd_cls_sel")
                            if sel_rd == "கைமுறையாக உள்ளிட (Manual)":
                                acc_no = st.text_input("கணக்கு எண் உள்ளிடவும் *", key="rd_cls_man_acc")
                                default_dep = 0.0
                            else:
                                acc_no = sel_rd
                                matched_rd = next((r for r in cust_rds if r["acc_no"] == sel_rd), None)
                                default_dep = float(matched_rd.get("installment_amount", 0.0)) if matched_rd else 0.0
                        else:
                            st.info("💡 இந்த வாடிக்கையாளருக்கு ஆக்டிவ் RD கணக்குகள் எதுவும் கண்டறியப்படவில்லை.")
                            acc_no = st.text_input("கணக்கு எண் உள்ளிடவும் *", key="rd_cls_empty_acc")
                            default_dep = 0.0

                    with c2:
                        principal_amount = st.number_input("முதலீடு செய்த/கட்டிய தொகை (₹) *", min_value=0.0, value=default_dep, step=500.0, key="rd_cls_prin")
                        interest_amount = st.number_input("வட்டி தொகை (₹) *", min_value=0.0, step=50.0, key="rd_cls_int")
                        paid_amt = principal_amount + interest_amount
                        st.info(f"💰 **மொத்த முதிர்வுத் தொகை: ₹{paid_amt:,.2f}**")

                    detail_summary = [f"RD No: {acc_no}", f"முதலீடு: ₹{principal_amount:,.2f}", f"வட்டி: ₹{interest_amount:,.2f}", f"மொத்தம்: ₹{paid_amt:,.2f}"]
                    extra_meta_data = {"account_no": acc_no, "deposit_amount": principal_amount, "interest_amount": interest_amount, "closed_amount": paid_amt}

                # -------------------------------------------------------------
                # 9. FD வட்டி வழங்குதல் (FD Interest - Auto Account Fetch)
                # -------------------------------------------------------------
                elif "FD" in txn_category and ("வட்டி" in txn_category or "Interest" in txn_category):
                    st.markdown("##### 💵 FD வட்டி வழங்குதல்")
                    c_id = visit.get("customer_id")
                    cust_fds = get_customer_fd_accounts(c_id) if c_id else []

                    c1, c2 = st.columns(2)
                    with c1:
                        if cust_fds:
                            fd_options = [f["acc_no"] for f in cust_fds] + ["கைமுறையாக உள்ளிட (Manual)"]
                            sel_fd = st.selectbox("FD கணக்கு எண் தேர்ந்தெடுக்கவும் *", fd_options, key="fd_int_sel")
                            if sel_fd == "கைமுறையாக உள்ளிட (Manual)":
                                acc_no = st.text_input("FD கணக்கு எண் உள்ளிடவும் *", key="fd_int_man_acc")
                            else:
                                acc_no = sel_fd
                        else:
                            acc_no = st.text_input("FD கணக்கு எண் உள்ளிடவும் *", key="fd_int_empty_acc")

                    with c2:
                        paid_amt = st.number_input("வழங்கிய வட்டித் தொகை (₹) *", min_value=0.0, step=100.0, key="fd_int_amt")

                    detail_summary = [f"FD No: {acc_no}", f"Interest Paid: ₹{paid_amt:,.2f}"]
                    extra_meta_data = {"account_no": acc_no, "interest_amount": paid_amt}

                # -------------------------------------------------------------
                # 10. FD முதிர்வு / முடித்தல் (FD Closure - Auto Account Fetch)
                # -------------------------------------------------------------
                elif "FD" in txn_category and ("Closure" in txn_category or "முதிர்வு" in txn_category or "முடித்தல்" in txn_category):
                    st.markdown("##### 📑 FD முதிர்வு / கணக்கு முடித்தல்")
                    c_id = visit.get("customer_id")
                    cust_fds = get_customer_fd_accounts(c_id) if c_id else []

                    c1, c2 = st.columns(2)
                    with c1:
                        if cust_fds:
                            fd_options = [f["acc_no"] for f in cust_fds] + ["கைமுறையாக உள்ளிட (Manual)"]
                            sel_fd = st.selectbox("முடிக்க வேண்டிய FD கணக்கு எண் *", fd_options, key="fd_cls_sel")
                            if sel_fd == "கைமுறையாக உள்ளிட (Manual)":
                                acc_no = st.text_input("FD கணக்கு எண் *", key="fd_cls_man_acc")
                                default_dep = 0.0
                            else:
                                acc_no = sel_fd
                                matched_fd = next((f for f in cust_fds if f["acc_no"] == sel_fd), None)
                                default_dep = float(matched_fd["deposit_amount"]) if matched_fd else 0.0
                        else:
                            acc_no = st.text_input("முடிக்க வேண்டிய FD கணக்கு எண் *", key="fd_cls_empty_acc")
                            default_dep = 0.0

                    with c2:
                        principal_amount = st.number_input("முதலீடு செய்த அசல் தொகை (₹) *", min_value=0.0, value=default_dep, step=1000.0, key="fd_cls_prin")
                        interest_amount = st.number_input("வட்டி தொகை (₹) *", min_value=0.0, step=100.0, key="fd_cls_int")
                        paid_amt = principal_amount + interest_amount
                        st.info(f"💰 **மொத்த முதிர்வுத் தொகை: ₹{paid_amt:,.2f}**")

                    detail_summary = [f"Closed FD: {acc_no}", f"அசல்: ₹{principal_amount:,.2f}", f"வட்டி: ₹{interest_amount:,.2f}", f"மொத்தம்: ₹{paid_amt:,.2f}"]
                    extra_meta_data = {"account_no": acc_no, "deposit_amount": principal_amount, "interest_amount": interest_amount, "closed_amount": paid_amt}
                # -------------------------------------------------------------
                # 7. GP (Gold Purchase) - முழுமையான திருத்தப்பட்ட பகுதி
                # -------------------------------------------------------------
                elif txn_category == "GP (Gold Purchase)":
                    st.markdown("##### 🪙 தங்கம் வாங்குதல் (GP Details)")
                    gp_mode = st.radio("GP வகை தேர்வு செய்க *:", ["Direct (நேரடி கொள்முதல்)", "Takeover (பிற நிறுவன மீட்டல் வழி கொள்முதல்)"], horizontal=True)
                    is_takeover = "Takeover" in gp_mode

                    bank_source = ""
                    prev_loan_no = ""
                    advance_paid = 0.0

                    gp_col1, gp_col2 = st.columns(2)
                    with gp_col1:
                        # 🌟 ஆட்டோ ஜீபி எண் (key நீக்கப்பட்டுள்ளதால் அடுத்தடுத்த எண்கள் உடனுக்குடன் மாறும்)
                        auto_gp_no = generate_gp_number(st.session_state.get("branch_id"))
                    gp_number = st.text_input(
                        "1) ஜீபி எண் (Auto-generated):", 
                        value=auto_gp_no, 
                        disabled=True,
                        key=f"gp_disp_{auto_gp_no}"  # 👈 புதிய எண் வரும்போது விட்ஜெட் உடனே புதுப்பிக்கப்பட இது உதவும்
                    )
                    with gp_col2:
                        voucher_no = st.text_input("2) வவுச்சர் எண் *:", placeholder="எ.கா: VCH-1002", key=f"gp_vch_{fc}")

                    st.markdown("---")
                    st.markdown("###### 📋 3) நகை விவரப் பட்டியல்:")
                    purity_options = ["916 KDM", "916 BIS Hallmarked", "22ct (91.6%)", "20ct", "18ct (75.0%)", "மற்றவை"]

                    for idx, row in enumerate(st.session_state.gp_ornament_rows):
                        r_c1, r_c2, r_c3, r_c4, r_c5, r_c6 = st.columns([3, 2, 2.5, 2.5, 2.5, 1])
                        with r_c1:
                            st.session_state.gp_ornament_rows[idx]["item"] = st.text_input(f"நகை #{idx+1}", value=row["item"], key=f"gp_item_{idx}", placeholder="எ.கா: செயின்")
                        with r_c2:
                            st.session_state.gp_ornament_rows[idx]["count"] = st.number_input(f"எண்ணிக்கை #{idx+1}", min_value=1, value=int(row["count"]), step=1, key=f"gp_cnt_{idx}")
                        with r_c3:
                            st.session_state.gp_ornament_rows[idx]["gross_wt"] = st.number_input(f"மொத்த எடை (g) #{idx+1}", min_value=0.0, value=float(row["gross_wt"]), step=0.01, format="%.3f", key=f"gp_gwt_{idx}")
                        with r_c4:
                            st.session_state.gp_ornament_rows[idx]["net_wt"] = st.number_input(f"நிகர எடை (g) #{idx+1}", min_value=0.0, value=float(row["net_wt"]), step=0.01, format="%.3f", key=f"gp_nwt_{idx}")
                        with r_c5:
                            curr_pur = row.get("purity", "916 KDM")
                            pur_idx = purity_options.index(curr_pur) if curr_pur in purity_options else 0
                            st.session_state.gp_ornament_rows[idx]["purity"] = st.selectbox(f"தூய்மை #{idx+1}", purity_options, index=pur_idx, key=f"gp_pur_{idx}")
                        with r_c6:
                            st.write("")
                            st.write("")
                            if len(st.session_state.gp_ornament_rows) > 1:
                                if st.button("❌", key=f"del_gp_row_{idx}", help="நீக்கு"):
                                    st.session_state.gp_ornament_rows.pop(idx)
                                    st.rerun()

                    if st.button("➕ கூடுதல் நகை சேர்க்க", key="btn_add_gp_row"):
                        st.session_state.gp_ornament_rows.append({"item": "", "count": 1, "gross_wt": 0.0, "net_wt": 0.0, "purity": "916 KDM"})
                        st.rerun()

                    calc_total_gross = sum(float(r["gross_wt"]) for r in st.session_state.gp_ornament_rows)
                    calc_total_net = sum(float(r["net_wt"]) for r in st.session_state.gp_ornament_rows)
                    calc_total_items = sum(int(r["count"]) for r in st.session_state.gp_ornament_rows)

                    st.markdown("---")
                    w_col1, w_col2, w_col3 = st.columns(3)
                    with w_col1:
                        total_weight = st.number_input("4) மொத்த எடை (Gross Wt - g):", value=calc_total_gross, format="%.3f", disabled=True)
                    with w_col2:
                        net_weight = st.number_input("5) மொத்த நிகர எடை (Net Wt - g):", value=calc_total_net, format="%.3f", disabled=True)
                    with w_col3:
                        total_gp_value = st.number_input("6) மொத்த மதிப்பு (Total Value - ₹) *:", min_value=0.0, step=500.0, format="%.2f", key=f"gp_val_{fc}")

                    # -------------------------------------------------------------
                    # 🌟 மீதித் தொகை கணக்கீடு (key இல்லாததால் தானாக உடனடியாக மாறும்)
                    # -------------------------------------------------------------
                    balance_payable = float(total_gp_value)
                    if is_takeover:
                        t_col1, t_col2 = st.columns(2)
                        with t_col1:
                            advance_paid = st.number_input("7) அட்வான்ஸ் செலுத்திய தொகை (₹):", min_value=0.0, max_value=float(total_gp_value), step=500.0, format="%.2f", key=f"gp_adv_{fc}")
                        with t_col2:
                            balance_payable = max(0.0, float(total_gp_value) - float(advance_paid))
                            # 🌟 key நீக்கப்பட்டுள்ளது (இதனால் ₹40,000 உடனே தானாக வரும்):
                            st.number_input("8) மீதி தொகை (Balance Payable - ₹):", value=balance_payable, format="%.2f", disabled=True)

                        tb_c1, tb_c2 = st.columns(2)
                        with tb_c1:
                            bank_source = st.text_input("முந்தைய நிறுவனம் / வங்கி பெயர் *:", placeholder="எ.கா: SBI / Muthoot", key=f"gp_bsrc_{fc}")
                        with tb_c2:
                            prev_loan_no = st.text_input("முந்தைய அடகு கடன் எண் *:", placeholder="எ.கா: 12450/2025", key=f"gp_plno_{fc}")

                    st.markdown("---")
                    img_c1, img_c2 = st.columns(2)
                    with img_c1:
                        cust_with_ornaments_img = st.file_uploader("வாடிக்கையாளர் படம் நகையுடன் *:", type=["jpg", "jpeg", "png"], key="gp_cust_img")
                    with img_c2:
                        ornaments_summary_img = st.file_uploader("நகைகள் விபர படம் *:", type=["jpg", "jpeg", "png"], key="gp_orn_img")

                    ref1_c1, ref1_c2, ref1_c3, ref1_c4 = st.columns(4)
                    with ref1_c1:
                        gp_ref1_name = st.text_input("ரெபரண்ஸ் 1 - பெயர்:", key="gp_r1_n")
                    with ref1_c2:
                        gp_ref1_addr = st.text_input("முகவரி:", key="gp_r1_a")
                    with ref1_c3:
                        gp_ref1_rel = st.text_input("உறவுமுறை:", key="gp_r1_r")
                    with ref1_c4:
                        gp_ref1_phone = st.text_input("மொபைல் எண்:", key="gp_r1_p")

                    ref2_c1, ref2_c2, ref2_c3, ref2_c4 = st.columns(4)
                    with ref2_c1:
                        gp_ref2_name = st.text_input("ரெபரண்ஸ் 2 - பெயர்:", key="gp_r2_n")
                    with ref2_c2:
                        gp_ref2_addr = st.text_input("முகவரி:", key="gp_r2_a")
                    with ref2_c3:
                        gp_ref2_rel = st.text_input("உறவுமுறை:", key="gp_r2_r")
                    with ref2_c4:
                        gp_ref2_phone = st.text_input("மொபைல் எண்:", key="gp_r2_p")

                    paid_amt = balance_payable if is_takeover else total_gp_value
                    received_amt = 0.0

                    gp_remarks = f"GP வகை: {gp_mode} | வவுச்சர்: {voucher_no.strip() if voucher_no else '-'} | உருப்படிகள்: {calc_total_items} nos | நிகர எடை: {calc_total_net:.3f}g"
                    if is_takeover:
                        gp_remarks += f" | அட்வான்ஸ்: ₹{advance_paid:,.2f} | மீதி: ₹{balance_payable:,.2f}"

                    # -------------------------------------------------------------
                    # 📄 சட்டபூர்வ உறுதிமொழிப் படிவ முன்னோட்டம் & பிரிண்ட் பட்டன்
                    # -------------------------------------------------------------
                    st.markdown("---")
                    col_gp_act1, col_gp_act2 = st.columns(2)
                    with col_gp_act1:
                        if st.button("📄 சட்டபூர்வ உறுதிமொழிப் படிவத்தை உருவாக்கு (Generate GP Form)", key="btn_gen_gp_doc"):
                            st.session_state["show_gp_print_modal"] = True

                    if st.session_state.get("show_gp_print_modal"):
                        st.markdown("---")
                        st.subheader("🖨️ வாடிக்கையாளர் உறுதிமொழிப் படிவம் (Print Preview)")
                        
                        gp_preview_data = {
                            "gp_number": gp_number,
                            "voucher_no": voucher_no,
                            "date": datetime.now().strftime("%d/%m/%Y"),
                            "gp_mode": gp_mode,
                            "branch_name": st.session_state.get("branch_name", "Aundivilai"),
                            "branch_phone": st.session_state.get("branch_phone", ""),
                            "customer_name": visit.get("customer_name"),
                            "customer_mobile": visit.get("mobile"),
                            "customer_address": visit.get("address", ""),
                            "ornaments": st.session_state.gp_ornament_rows,
                            "total_items": calc_total_items,
                            "gross_wt": calc_total_gross,
                            "net_wt": calc_total_net,
                            "total_value": total_gp_value,
                            "bank_source": bank_source if is_takeover else "",
                            "prev_loan_no": prev_loan_no if is_takeover else "",
                            "advance_paid": advance_paid if is_takeover else 0.0,
                            "balance_payable": balance_payable if is_takeover else total_gp_value,
                            "ref1_name": gp_ref1_name,
                            "ref1_phone": gp_ref1_phone
                        }

                        import streamlit.components.v1 as components
                        doc_html = generate_gp_declaration_html(gp_preview_data)
                        components.html(doc_html, height=800, scrolling=True)

                    # -------------------------------------------------------------
                    # ➕ GP நடவடிக்கையைக் கார்ட்டில் சேர்த்தல் (Add to Cart)
                    # -------------------------------------------------------------
                    if st.button("➕ பட்டியலில் சேர் (Add to Cart)", type="primary", key="btn_add_gp_to_cart"):
                        if not voucher_no.strip():
                            st.warning("⚠️ தயவுசெய்து வவுச்சர் எண்ணை உள்ளிடவும்!")
                        elif total_gp_value <= 0:
                            st.warning("⚠️ மொத்த மதிப்பு ₹0-க்கு மேல் இருக்க வேண்டும்!")
                        elif is_takeover and not bank_source.strip():
                            st.warning("⚠️ தயவுசெய்து முந்தைய நிறுவனம் / வங்கிப் பெயரை உள்ளிடவும்!")
                        elif is_takeover and not prev_loan_no.strip():
                            st.warning("⚠️ தயவுசெய்து முந்தைய அடகு கடன் எண்ணை உள்ளிடவும்!")
                        else:
                            try:
                                with st.spinner("விவரங்கள் கார்ட்டில் சேர்க்கப்படுகின்றன..."):
                                    cust_pic_url = upload_ornament_image(cust_with_ornaments_img) if cust_with_ornaments_img else None
                                    orn_pic_url = upload_ornament_image(ornaments_summary_img) if ornaments_summary_img else None

                                    # நகைகள் விவரங்களை டெக்ஸ்டாக மாற்றுதல்
                                    orn_list_details = []
                                    valid_ornaments = []
                                    for idx, r in enumerate(st.session_state.gp_ornament_rows):
                                        if r.get("item", "").strip():
                                            orn_list_details.append(
                                                f"{idx+1}. {r['item']} ({r.get('count', 1)} nos) - Gross: {r.get('gross_wt', 0.0)}g, Net: {r.get('net_wt', 0.0)}g, Purity: {r.get('purity', '916 KDM')}"
                                            )
                                            valid_ornaments.append(dict(r))
                                    
                                    full_ornament_text = "\n".join(orn_list_details) if orn_list_details else "விவரங்கள் இல்லை"

                                    # 🌟 gold_purchases மற்றும் transactions ஆகிய இரண்டிற்கும் தேவையான முழு விவரங்களையும் கார்ட்டில் சேர்த்தல்:
                                    st.session_state.transactions_cart.append({
                                        "transaction_type": f"GP - {gp_mode}",
                                        "gp_mode": gp_mode,
                                        "is_takeover": is_takeover,
                                        "staff_name": staff,
                                        "paid_amount": float(paid_amt),
                                        "received_amount": 0.0,
                                        "amount": float(total_gp_value),
                                        "total_value": float(total_gp_value),
                                        "advance_paid": float(advance_paid if is_takeover else 0.0),
                                        "balance_payable": float(balance_payable if is_takeover else total_gp_value),
                                        "bank_source": bank_source.strip() if is_takeover else "",
                                        "prev_loan_no": prev_loan_no.strip() if is_takeover else "",
                                        "remarks": gp_remarks,
                                        "custom_remarks": custom_remarks,
                                        "ornament_details": full_ornament_text,
                                        "ornaments": valid_ornaments,                    # 👈 gold_purchases அட்டவணைக்குத் தேவையான பட்டியல்
                                        "other_charges": 0.0,
                                        "ornament_image_url": orn_pic_url,
                                        "customer_photo_url": cust_pic_url,
                                        "total_weight": float(calc_total_gross),
                                        "net_weight": float(calc_total_net),
                                        "gross_weight": float(calc_total_gross),
                                        "gp_number": gp_number,
                                        "voucher_no": voucher_no.strip(),
                                        "ref1_name": f"{gp_ref1_name} ({gp_ref1_rel})" if gp_ref1_name else "",
                                        "ref1_phone": f"{gp_ref1_phone} - {gp_ref1_addr}".strip(" -"),
                                        "ref2_name": f"{gp_ref2_name} ({gp_ref2_rel})" if gp_ref2_name else "",
                                        "ref2_phone": f"{gp_ref2_phone} - {gp_ref2_addr}".strip(" -"),
                                        "principal_amount": float(total_gp_value),
                                        "interest_amount": 0.0
                                    })

                                    # கார்ட்டில் சேர்த்த பின் படிவத்தை ரீசெட் செய்தல்
                                    st.session_state.gp_ornament_rows = [{"item": "", "count": 1, "gross_wt": 0.0, "net_wt": 0.0, "purity": "916 KDM"}]
                                    if "form_reset_counter" in st.session_state:
                                        st.session_state.form_reset_counter += 1
                                    st.session_state["show_gp_print_modal"] = False

                                    st.success("✅ GP நடவடிக்கை வெற்றிகரமாகப் பட்டியலில் சேர்க்கப்பட்டது!")
                                    st.rerun()

                            except Exception as err:
                                st.error(f"❌ கார்ட்டில் சேர்ப்பதில் பிழை: {err}")

                # 8. GS (Gold Sale)
                elif txn_category == "GS (Gold Sale)":
                    gs_col1, gs_col2, gs_col3 = st.columns(3)
                    with gs_col1:
                        gs_bill_no = st.text_input("விற்பனை பில் எண் *")
                        total_weight = st.number_input("மொத்த எடை (Gross Wt - g) *", min_value=0.0, step=0.001, format="%.3f")
                    with gs_col2:
                        gs_item_name = st.text_input("பொருள் பெயர்")
                        net_weight = st.number_input("நிகர எடை (Net Wt - g) *", min_value=0.0, step=0.001, format="%.3f")
                    with gs_col3:
                        received_amt = st.number_input("பெற்ற தொகை (Received ₹) *", min_value=0.0, step=500.0)

                    ornament_details = st.text_area("நகை விபரம் (Ornament Details)", key="gs_details")
                    ornament_file = st.file_uploader("நகை படம் (Ornament Photo)", type=["jpg", "jpeg", "png"], key="gs_img")
                    detail_summary = [f"பில்: {gs_bill_no}", f"பொருள்: {gs_item_name}", f"எடை: {net_weight}g"]
                    
                    # கார்ட்டில் சேர்க்கும் பட்டன் (GP அல்லாத பிற நடவடிக்கைகளுக்கு மட்டும்)
                if txn_category != "GP (Gold Purchase)":
                    if st.button("➕ பட்டியலில் சேர் (Add to Cart)", type="primary", key="btn_add_to_cart_main"):
                        if "Pledge" in txn_category:
                            actual_paid_amt = max(0.0, float(paid_amt) - float(other_charges)) if 'paid_amt' in locals() else 0.0
                        else:
                            actual_paid_amt = float(paid_amt) if 'paid_amt' in locals() else 0.0

                        chk_received = float(received_amt) if 'received_amt' in locals() else 0.0

                        if actual_paid_amt <= 0 and chk_received <= 0:
                            st.warning("⚠️ தயவுசெய்து பட்டுவாடா தொகை அல்லது பெற்ற தொகையை உள்ளிடவும்!")
                        else:
                            all_remarks = " | ".join(detail_summary) if 'detail_summary' in locals() else ""
                            if 'custom_remarks' in locals() and custom_remarks.strip():
                                all_remarks += f" ({custom_remarks.strip()})"

                            img_url = upload_ornament_image(ornament_file) if ('ornament_file' in locals() and ornament_file) else None

                            cart_entry = {
                                "transaction_type": txn_category,
                                "staff_name": staff if 'staff' in locals() else "",
                                "paid_amount": float(actual_paid_amt),
                                "received_amount": float(chk_received),
                                "amount": float(actual_paid_amt if actual_paid_amt > 0 else chk_received),
                                "remarks": all_remarks,
                                "ornament_details": ornament_details if ('ornament_details' in locals() and ornament_details) else "",
                                "other_charges": float(other_charges) if 'other_charges' in locals() else 0.0,
                                "ornament_image_url": img_url,
                                "total_weight": float(total_weight) if 'total_weight' in locals() else 0.0,
                                "net_weight": float(net_weight) if 'net_weight' in locals() else 0.0,
                                "gp_number": selected_gl_no if 'selected_gl_no' in locals() else (new_gl_no if 'new_gl_no' in locals() else (gp_number if 'gp_number' in locals() else "")),
                                "ref1_name": ref1_name if ('ref1_name' in locals() and ref1_name) else "",
                                "ref1_phone": ref1_phone if ('ref1_phone' in locals() and ref1_phone) else "",
                                "ref2_name": ref2_name if ('ref2_name' in locals() and ref2_name) else "",
                                "ref2_phone": ref2_phone if ('ref2_phone' in locals() and ref2_phone) else "",
                                "principal_amount": float(principal_amount) if 'principal_amount' in locals() else (float(paid_amt) if 'paid_amt' in locals() else 0.0),
                                "interest_amount": float(interest_amount) if 'interest_amount' in locals() else 0.0,
                                "nominee_name": nominee_name if ('nominee_name' in locals() and nominee_name) else "",
                                "nominee_relation": nominee_relation if ('nominee_relation' in locals() and nominee_relation) else "",
                                "nominee_address": nominee_address if ('nominee_address' in locals() and nominee_address) else "",

                                # 🌟 திட்ட மாஸ்டரின் தகவல்கள் (Scheme Master Details):
                                "scheme_name": selected_scheme if 'selected_scheme' in locals() else (scheme_name if 'scheme_name' in locals() else ""),
                                "interest_rate": float(cur_roi) if 'cur_roi' in locals() else 18.0,
                                "tenure_months": int(cur_tenure) if 'cur_tenure' in locals() else 12,
                                "market_rate": float(cur_rpg) if 'cur_rpg' in locals() else 0.0,

                                # 🌟 RD / FD கணக்கு எண் & கூடுதல் மெட்டாடேட்டா:
                                "account_no": acc_no if 'acc_no' in locals() else None,
                                "extra_meta_data": extra_meta_data if 'extra_meta_data' in locals() else {}
                            }

                            st.session_state.transactions_cart.append(cart_entry)
                            st.rerun()

                            # 🌟 அடமானம் மீட்டல் (Release) என்றால் Closed செய்யக் குறித்தல்:
                            if "மீட்டல்" in txn_category or "Release" in txn_category:
                                cart_entry["closed_gl_no"] = selected_gl_no if 'selected_gl_no' in locals() else ""
                                cart_entry["closed_loan_id"] = selected_loan_db_id if 'selected_loan_db_id' in locals() else None

                            # கார்ட்டில் சேர்த்தல்
                            st.session_state.transactions_cart.append(cart_entry)

                            # புதிய அடமானம் என்றால் உறுதி ஆவணத்தை தயார் செய்தல்
                            if "Pledge" in txn_category:
                                st.session_state.current_declaration = cart_entry
                                st.session_state.declaration_gl_no = cart_entry.get("gp_number", "")

                            st.session_state.form_reset_counter += 1
                            st.rerun()  # 🌟 Rerun ஆகும் போது ஆட்டோ எண் தானாக +1 முன்னோக்கி கூடும்

                    
                            # 🌟 அடமானம் மீட்டல் (Release) என்றால் 'Closed' செய்ய வேண்டிய கடன் எண் மற்றும் ஐடி குறித்தல்
                            if "மீட்டல்" in txn_category or "Release" in txn_category:
                                cart_entry["closed_gl_no"] = selected_gl_no if 'selected_gl_no' in locals() else ""
                                cart_entry["closed_loan_id"] = selected_loan_db_id if 'selected_loan_db_id' in locals() else None
                            
                            # 1. Pledge உறுதி ஆவணம் உருவாக்கம் (Declaration Form)
                            if "Pledge" in txn_category:
                                decl_payload = {
                                    "customer_name": visit.get("customer_name", ""),
                                    "address": visit.get("address", ""),
                                    "contact_number": visit.get("mobile", ""),
                                    "branch_name": st.session_state.get("branch", ""),
                                    "pledge_date": datetime.now().strftime("%d-%m-%Y"),
                                    "loan_number": new_gl_no if 'new_gl_no' in locals() else "",
                                    "loan_amount": paid_amt if 'paid_amt' in locals() else 0.0,
                                    "current_date": datetime.now().strftime("%d-%m-%Y")
                                }
                                st.session_state.declaration_gl_no = new_gl_no if 'new_gl_no' in locals() else "GL"
                                st.session_state.current_declaration = generate_declaration_html(decl_payload)

                            # 2. புதிய அடமானம் (Pledge) கார்ட்டில் சேர்ந்தால் அடுத்த ஆட்டோ கடன் எண்ணை உறுதி செய்தல்
                            if "Pledge" in txn_category and 'next_seq_num' in locals():
                                commit_next_gl_number(st.session_state.branch_id, next_seq_num)

                            # 3. கார்ட்டில் சேர்த்தல் மற்றும் படிவத்தை ரீசெட் செய்தல்
                            st.session_state.transactions_cart.append(cart_entry)
                            st.session_state.form_reset_counter += 1
                            st.rerun()


                            # கார்ட்டில் சேர்த்த பின் படிவத்தை ரீசெட் செய்தல்
                            if "form_reset_counter" not in st.session_state:
                                st.session_state.form_reset_counter = 0
                            st.session_state.form_reset_counter += 1

                            st.success(f"'{txn_category}' வெற்றிகரமாகப் பட்டியலில் சேர்க்கப்பட்டது!")
                            st.rerun()

                # உறுதி ஆவணப் பதிவிறக்கப் பகுதி
                if st.session_state.get("current_declaration"):
                    decl_info = st.session_state.current_declaration
                    gl_no_val = st.session_state.get("declaration_gl_no") or decl_info.get("gp_number", "GL")
                    clean_gl_key = str(gl_no_val).replace("/", "_")

                    # வாடிக்கையாளர் மற்றும் கடன் தகவல்கள்
                    v_info = st.session_state.get("current_visit", {}) or (visit if 'visit' in locals() else {})
                    cust_name = v_info.get("customer_name") or v_info.get("name") or "Cyril Jenson"
                    cust_mob = v_info.get("mobile") or v_info.get("customer_mobile") or v_info.get("phone") or "-"
                    branch_name = st.session_state.get("branch_name", "முத்துசிஸ் கோல்டு புரொடக்ட் பிரைவேட் லிமிடெட்")
                    
                    from datetime import datetime
                    from dateutil.relativedelta import relativedelta

                    today_dt = datetime.now()
                    today_str = today_dt.strftime("%d-%m-%Y")
                    due_date_str = (today_dt + relativedelta(months=3)).strftime("%d-%m-%Y")

                    amt_val = float(decl_info.get("principal_amount", 0.0) or decl_info.get("paid_amount", 0.0) or decl_info.get("amount", 0.0))
                    tot_wt = float(decl_info.get("total_weight", 0.0))
                    net_wt = float(decl_info.get("net_weight", 0.0))

                    # 🌟 A4 அளவுக்கு கச்சிதமாகப் பொருந்தும் HTML & CSS கட்டமைப்பு
                    html_template = f"""<!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>கூடுதல் கடன் உறுதிமொழிப் பத்திரம் - {gl_no_val}</title>
                    <style>
                        @page {{
                            size: A4 portrait;
                            margin: 10mm 15mm;
                        }}
                        * {{
                            box-sizing: border-box;
                        }}
                        body {{
                            font-family: Arial, sans-serif;
                            margin: 0;
                            padding: 0;
                            line-height: 1.4;
                            color: #111;
                            font-size: 12px;
                        }}
                        .title {{
                            text-align: center;
                            font-size: 14px;
                            font-weight: bold;
                            border-bottom: 1.5px solid #222;
                            padding-bottom: 4px;
                            margin-bottom: 10px;
                        }}
                        .parties-table {{
                            width: 100%;
                            margin-bottom: 8px;
                            font-size: 12px;
                            border-collapse: collapse;
                        }}
                        .parties-table td {{
                            vertical-align: top;
                            padding: 0;
                        }}
                        .subject {{
                            background-color: #f2f2f2;
                            padding: 5px 8px;
                            font-weight: bold;
                            font-size: 12px;
                            border-left: 3px solid #b8860b;
                            margin-bottom: 8px;
                        }}
                        .content {{
                            text-align: justify;
                            font-size: 11.5px;
                        }}
                        .content p {{
                            margin: 0 0 6px 0;
                        }}
                        .summary-box {{
                            border: 1px dashed #444;
                            padding: 6px 10px;
                            margin: 8px 0;
                            background: #fafafa;
                            font-size: 11.5px;
                        }}
                        .signature-table {{
                            width: 100%;
                            margin-top: 15px;
                            border-collapse: collapse;
                        }}
                        .signature-table td {{
                            vertical-align: top;
                            font-size: 11.5px;
                            padding: 0;
                        }}
                        @media print {{
                            body {{
                                width: 100%;
                            }}
                        }}
                    </style>
                </head>
                <body>
                    <div class="title">
                        அடகு நகைக்கடன் கூடுதல் தொகை பெறுதல் தொடர்பான உறுதிமொழிப் பத்திரம்
                    </div>

                    <table class="parties-table">
                        <tr>
                            <td style="width: 50%;">
                                <strong>அனுப்புநர்:</strong><br>
                                திரு/திருமதி. {cust_name}<br>
                                தொடர்பு எண்: {cust_mob}
                            </td>
                            <td style="width: 50%;">
                                <strong>பெறுநர்:</strong><br>
                                மேலாளர் அவர்கள்,<br>
                                முத்துசிஸ் கோல்டு புரொடக்ட் பிரைவேட் லிமிடெட்,<br>
                                கிளை: {branch_name}
                            </td>
                        </tr>
                    </table>

                    <div class="subject">
                        பொருள்: கடன் எண்: {gl_no_val} – கூடுதல் கடன் தொகை பெற்றமைக்கான உறுதிமொழி ஆவணம்.
                    </div>

                    <div class="content">
                        <p>ஐயா,</p>
                        <p>நான் தங்களது நிறுவனத்தில் <strong>{today_str}</strong> அன்று கடன் எண் <strong>{gl_no_val}</strong>-ன் கீழ் எனது தங்க நகைகளை அடமானம் வைத்து <strong>₹{amt_val:,.2f}</strong> கடனாகப் பெற்றுள்ளேன்.</p>
                        
                        <p>எனது அவசர பணத்தேவையின் காரணமாக, நிறுவனத்தின் வழக்கமான கடன் மதிப்பீட்டு வரம்பை (LTV) விட எனது தனிப்பட்ட வேண்டுகோளின் பேரில் கூடுதல் தொகையினை கடனாகப் பெற்றுள்ளேன் என்பதை மனப்பூர்வமாக ஒப்புக்கொள்கிறேன்.</p>
                        
                        <p>இக்கடனுக்கான கால அளவு 3 (மூன்று) மாதங்கள் மட்டுமே. இக்காலக்கட்டத்தில் மாதாந்திர வட்டியை தவறாமல் செலுத்தி, 3 மாத கால முடிவிற்குள் (அதாவது <strong>{due_date_str}</strong>-க்குள்) அசல் மற்றும் முழு வட்டியையும் செலுத்தி நகைகளைத் திருப்பிக் கொள்கிறேன் என உறுதியளிக்கிறேன். தவணை தவறினால், நிறுவனத்தின் விதிகளின்படி கூடுதல் அபராத வட்டி செலுத்த நான் கட்டுப்பட்டவன் ஆவேன்.</p>
                        
                        <p>3 மாத காலத்திற்குள் அசல் மற்றும் வட்டி முழுவதையும் செலுத்தி கடனை நேர் செய்யத் தவறினால், இந்திய ஒப்பந்தச் சட்ட விதிகளின்படி (Indian Contract Act, 1872) நிறுவனம் எனக்கு உரிய முன்னறிவிப்பு வழங்கி, அடமானம் வைக்கப்பட்ட நகைகளை வெளிப்படை ஏலத்திலோ அல்லது நேரடி விற்பனை மூலமாகவோ விற்று கடன் பாக்கியை வசூலித்துக் கொள்ள முழு உரிமை உண்டு.</p>
                        
                        <p>அவ்வாறு நகைகளை விற்பனை செய்து கடன் தொகையை ஈடுசெய்வதில் எனக்கு எவ்வித ஆட்சேபனையோ, உரிமைகோரலோ இருக்காது. விற்பனைத் தொகையானது நிலுவைக் கடனை விடக் குறைவாக இருக்கும் பட்சத்தில், எஞ்சிய கடன் தொகையை நான் செலுத்த முழுப் பொறுப்பேற்கிறேன்.</p>
                        
                        <p>மேற்கண்ட அனைத்து விதிகளையும் முழுமையாகப் படித்துப் புரிந்து கொண்டு, எந்தவித வற்புறுத்தலும் இன்றி எனது சொந்த விருப்பத்தின் பேரில் இந்த உறுதிமொழிப் பத்திரத்தில் கையொப்பமிடுகிறேன்.</p>
                    </div>

                    <div class="summary-box">
                        <strong>அடகு வைக்கப்பட்ட நகைகளின் சுருக்கம்:</strong><br>
                        ரசீது எண்: <strong>{gl_no_val}</strong> | மொத்த எடை: <strong>{tot_wt}g</strong> | நிகர எடை: <strong>{net_wt}g</strong> | தேதி: <strong>{today_str}</strong> | இடம்: <strong>{branch_name}</strong>
                    </div>

                    <table class="signature-table">
                        <tr>
                            <td style="width: 50%;">
                                <strong>சாட்சிகள்:</strong><br><br>
                                1. பெயர்: ______________________ கையொப்பம்: ____________<br><br>
                                2. பெயர்: ______________________ கையொப்பம்: ____________
                            </td>
                            <td style="width: 50%; text-align: right; vertical-align: bottom;">
                                வாடிக்கையாளர் கையொப்பம்: ___________________<br><br>
                                (<strong>{cust_name}</strong>)
                            </td>
                        </tr>
                    </table>
                </body>
                </html>"""

                    download_bytes = html_template.encode("utf-8")

                    st.markdown("---")
                    with st.container(border=True):
                        st.warning("⚠️ **கவனிக்க:** கூடுதல் நகைக் கடன் உறுதிமொழிப் பத்திரம் அவசியமாகிறது.")
                        st.download_button(
                            label=f"📄 உறுதி ஆவணத்தைப் பதிவிறக்குக (Print Declaration - GL: {gl_no_val})",
                            data=download_bytes,
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
                            st.rerun()  # 🌟 Rerun ஆகும் போது ஆட்டோ எண் தானாகப் பின்னோக்கி இறங்கிவிடும்

            # ---------------------------------------------------------------------
            # படி 3: பணம் மற்றும் OTP சரிபார்ப்பு (CASH_OTP )
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

                with st.container(border=True):
                    st.markdown("#### 💳 பணம் செலுத்தும் / பெறும் வழிகள் (Payment Split)")
                    pm_c1, pm_c2, pm_c3 = st.columns(3)
                    with pm_c1:
                        pay_option = st.selectbox(
                            "பரிமாற்ற வகை:",
                            ["முழுவதும் ரொக்கம் (100% Cash)", "முழுவதும் வங்கி / UPI (100% Online)", "பகுதி ரொக்கம் + பகுதி வங்கி (Split)"],
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
                                "ரொக்கப் பகுதி (₹):",
                                min_value=0.0,
                                max_value=float(total_needed_abs),
                                step=500.0,
                                disabled=otp_already_sent,
                                key="cash_portion_input"
                            )
                            bank_portion = total_needed_abs - cash_portion
                        st.metric("நிகர ரொக்க இலக்கு (Net Cash Target)", f"₹{cash_portion:,.2f}")

                    with pm_c3:
                        st.metric("வங்கி / UPI தொகை", f"₹{bank_portion:,.2f}")
                        bank_ref_no = st.text_input("UTR / Ref எண் *:", disabled=otp_already_sent, key="bank_ref_input") if bank_portion > 0 else ""

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

                    col_den1, col_den2 = st.columns([1.5, 1])

                    with col_den1:
                        st.markdown("#### 💵 நோட்டுகள் மற்றும் மீதி சில்லறை கணக்கீடு")

                        with st.expander("📥 வாடிக்கையாளர் தந்த நோட்டுகள் (Cash IN)", expanded=True):
                            r1_1, r1_2, r1_3, r1_4 = st.columns(4)
                            in_500 = r1_1.number_input("₹500 (IN)", min_value=0, step=1, disabled=otp_already_sent, key="in_500")
                            in_200 = r1_2.number_input("₹200 (IN)", min_value=0, step=1, disabled=otp_already_sent, key="in_200")
                            in_100 = r1_3.number_input("₹100 (IN)", min_value=0, step=1, disabled=otp_already_sent, key="in_100")
                            in_50 = r1_4.number_input("₹50 (IN)", min_value=0, step=1, disabled=otp_already_sent, key="in_50")

                            r2_1, r2_2, r2_3, r2_4 = st.columns(4)
                            in_20 = r2_1.number_input("₹20 (IN)", min_value=0, step=1, disabled=otp_already_sent, key="in_20")
                            in_10 = r2_2.number_input("₹10 (IN)", min_value=0, step=1, disabled=otp_already_sent, key="in_10")
                            in_5 = r2_3.number_input("₹5 (IN)", min_value=0, step=1, disabled=otp_already_sent, key="in_5")
                            in_coins = r2_4.number_input("சில்லறை ₹ (IN)", min_value=0, step=1, disabled=otp_already_sent, key="in_coins")

                            total_cash_in = (
                                (in_500 * 500) + (in_200 * 200) + (in_100 * 100) + (in_50 * 50) +
                                (in_20 * 20) + (in_10 * 10) + (in_5 * 5) + in_coins
                            )
                            st.markdown(f"**வாடிக்கையாளர் தந்த மொத்தத் தொகை:** `₹{total_cash_in:,.2f}`")

                        with st.expander("📤 கிளை கொடுத்த நோட்டுகள் / பேலன்ஸ் சில்லறை (Cash OUT)", expanded=True):
                            max_500 = max(0, current_drawer["500"] + in_500)
                            max_200 = max(0, current_drawer["200"] + in_200)
                            max_100 = max(0, current_drawer["100"] + in_100)
                            max_50 = max(0, current_drawer["50"] + in_50)
                            max_20 = max(0, current_drawer["20"] + in_20)
                            max_10 = max(0, current_drawer["10"] + in_10)
                            max_5 = max(0, current_drawer["5"] + in_5)
                            max_coins = max(0, int(current_drawer["coins"]) + in_coins)

                            o1_1, o1_2, o1_3, o1_4 = st.columns(4)
                            out_500 = o1_1.number_input(f"₹500 (இருப்பு:{max_500})", min_value=0, max_value=max_500, step=1, disabled=otp_already_sent, key="out_500")
                            out_200 = o1_2.number_input(f"₹200 (இருப்பு:{max_200})", min_value=0, max_value=max_200, step=1, disabled=otp_already_sent, key="out_200")
                            out_100 = o1_3.number_input(f"₹100 (இருப்பு:{max_100})", min_value=0, max_value=max_100, step=1, disabled=otp_already_sent, key="out_100")
                            out_50 = o1_4.number_input(f"₹50 (இருப்பு:{max_50})", min_value=0, max_value=max_50, step=1, disabled=otp_already_sent, key="out_50")

                            o2_1, o2_2, o2_3, o2_4 = st.columns(4)
                            out_20 = o2_1.number_input(f"₹20 (இருப்பு:{max_20})", min_value=0, max_value=max_20, step=1, disabled=otp_already_sent, key="out_20")
                            out_10 = o2_2.number_input(f"₹10 (இருப்பு:{max_10})", min_value=0, max_value=max_10, step=1, disabled=otp_already_sent, key="out_10")
                            out_5 = o2_3.number_input(f"₹5 (இருப்பு:{max_5})", min_value=0, max_value=max_5, step=1, disabled=otp_already_sent, key="out_5")
                            out_coins = o2_4.number_input(f"சில்லறை (இருப்பு:{max_coins})", min_value=0, max_value=max_coins, step=1, disabled=otp_already_sent, key="out_coins")

                            total_cash_out = (
                                (out_500 * 500) + (out_200 * 200) + (out_100 * 100) + (out_50 * 50) +
                                (out_20 * 20) + (out_10 * 10) + (out_5 * 5) + out_coins
                            )
                            st.markdown(f"**கிளை வழங்கிய மொத்தத் தொகை:** `₹{total_cash_out:,.2f}`")

                        if net_target < 0:
                            actual_net_handover = total_cash_in - total_cash_out
                        else:
                            actual_net_handover = total_cash_out - total_cash_in

                        is_cash_tally = (actual_net_handover == cash_portion)
                        is_bank_valid = True if bank_portion == 0 else bool(bank_ref_no.strip())
                        is_ready = is_cash_tally and is_bank_valid

                        st.markdown("---")
                        with st.container(border=True):
                            t_c1, t_c2, t_c3 = st.columns(3)
                            t_c1.metric("தேவையான நிகர ரொக்கம்", f"₹{cash_portion:,.2f}")
                            t_c2.metric("எண்ணப்பட்ட நிகர ரொக்கம்", f"₹{actual_net_handover:,.2f}")
                            diff_amt = cash_portion - actual_net_handover
                            t_c3.metric("வித்தியாசம்", f"₹{abs(diff_amt):,.2f}")

                            if not is_cash_tally:
                                st.error(f"❌ நோட்டுகளின் நிகரக் கணக்கீடு பொருந்தவில்லை! வித்தியாசம்: ₹{abs(diff_amt):,.2f}")
                            elif bank_portion > 0 and not bank_ref_no.strip():
                                st.warning("⚠️ வங்கி பரிவர்த்தனைக்கான UTR / Ref எண்ணை உள்ளிடவும்!")
                            else:
                                st.success("✅ நோட்டுகள் மற்றும் பேலன்ஸ் சில்லறை சரியாகப் பொருந்தியது!")

                    with col_den2:
                        st.markdown("#### 📲 OTP சரிபார்ப்பு")
                        c_name = visit.get("customer_name") or visit.get("name") or "வாடிக்கையாளர்"
                        c_mob = visit.get("mobile") or visit.get("customer_mobile") or "-"
                        st.write(f"வாடிக்கையாளர்: **{c_name}**")
                        st.write(f"மொபைல் எண்: `{c_mob}`")

                        # 🌟 1. வருகை எண் மற்றும் வாடிக்கையாளர் ஐடி எடுத்தல்
                        current_v_no = visit.get("visit_no", "-")
                        v_id = current_v_no  # Line 4726-ல் எரர் வராமல் பாதுகாக்க இது கட்டாயம் தேவை
                        c_id = visit.get("customer_id")
                        current_status = None

                        if current_v_no and current_v_no != "-":
                            try:
                                req_res = (
                                    supabase.table("otp_bypass_requests")
                                    .select("status")
                                    .eq("customer_id", c_id)
                                    .eq("visit_no", current_v_no)
                                    .neq("status", "Used")  # 👈🌟 இந்த ஒரு வரியை மட்டும் இணைத்துக் கொள்ளுங்கள்!
                                    .order("id", desc=True)
                                    .limit(1)
                                    .execute()
                                )
                                if req_res.data:
                                    current_status = req_res.data[0].get("status")
                            except Exception:
                                current_status = None

                        otp_cleared = False

                        # 🌟 2. ஸ்டேட்டஸ் செய்திகள்
                        if current_status == "Approved":
                            st.success("✅ **அட்மின் & ஆப்பரேஷன்ஸ் அனுமதி வழங்கப்பட்டுவிட்டது!** OTP விலக்கு அளிக்கப்பட்டது.")
                            otp_cleared = True  # இது உங்களிடம் ஏற்கனவே உள்ள வரி
                        
                        # 👈🌟 இந்த ஒரு வரியை மட்டும் இங்கே புதிதாகச் சேர்க்கவும்:
                            st.session_state.otp_verified = True
                        elif current_status == "Pending Admin":
                            st.warning("⏳ **OTP விலக்குக் கோரிக்கை அட்மின் (Admin) ஒப்புதலுக்காக நிலுவையில் உள்ளது.**")
                        elif current_status == "Pending Operations":
                            st.info("🔄 **அட்மின் ஒப்புதல் அளித்துவிட்டார்.** ஆப்பரேஷன்ஸ் இறுதி அனுமதிக்காக காத்திருக்கிறது...")
                        elif current_status == "Rejected":
                            st.error("❌ OTP விலக்குக் கோரிக்கை நிராகரிக்கப்பட்டது! வழக்கமான OTP-ஐப் பயன்படுத்தவும்.")

                        # 🌟 3. OTP அனுப்பும் பட்டன்
                        if not otp_cleared:
                            if not is_ready:
                                st.warning("⚠️ ரொக்க நோட்டுகளும் பேலன்ஸ் சில்லறையும் சரியாக அமைந்ததும் OTP இயங்கும்.")
                                st.button("📲 OTP அனுப்புக", disabled=True, key="otp_btn_disabled")
                            elif otp_already_sent:
                                st.success("✅ OTP வாடிக்கையாளருக்கு அனுப்பப்பட்டுவிட்டது!")
                            else:
                                if st.button("📲 OTP அனுப்புக", type="primary", key="otp_btn_active"):
                                    otp_code = str(random.randint(1000, 9999))
                                    st.session_state.generated_otp = otp_code
                                    with st.spinner("SMS அனுப்பப்படுகிறது..."):
                                        sms_success, msg_detail = send_fast2sms_otp(c_mob, otp_code)
                                    if sms_success:
                                        st.success("✅ OTP SMS அனுப்பப்பட்டது!")
                                    else:
                                        st.info(f"💡 சோதனை OTP: **{otp_code}**")
                                    st.rerun()

                            # OTP உள்ளீடு
                            entered_otp = st.text_input("வாடிக்கையாளர் OTP உள்ளிடவும்", max_chars=4, key="entered_otp_val")
                            if entered_otp and str(entered_otp).strip() == str(st.session_state.get("generated_otp", "")).strip():
                                otp_cleared = True

                            # 🌟 4. விலக்குக் கோரிக்கை அனுப்பும் பகுதி (항상 தெரியும் வகையில்)
                            with st.expander("🚨 வாடிக்கையாளர் OTP பெற முடியவில்லையா? (விலக்குக் கோரிக்கை)", expanded=True):
                                bypass_reason = st.text_area("விலக்குக் கோருவதற்கான காரணம் *", value="Old Mobile / No Signal", key=f"bp_rea_{v_id}")
                                if st.button("அட்மினுக்கு கோரிக்கை அனுப்பு (Request Bypass)", key=f"btn_send_bp_{v_id}", type="primary"):
                                    if not bypass_reason.strip():
                                        st.warning("⚠️ தயவுசெய்து காரணத்தைக் குறிப்பிடவும்!")
                                    else:
                                        try:
                                            b_id = st.session_state.get("branch_id") or visit.get("branch_id") or 1
                                            u_name = st.session_state.get("username") or "Branch Manager"
                                            
                                            req_payload = {
                                                "branch_id": st.session_state.branch_id,
                                                "customer_id": c_id,
                                                "visit_no": visit.get("visit_no"),  # 👈 இந்த வருகை எண்ணை இணைக்கவும்
                                                "customer_name": visit.get("customer_name"),
                                                "mobile": visit.get("mobile"),
                                                "reason": bypass_reason,
                                                "status": "Pending Admin",
                                                "requested_by": st.session_state.username
                                            }
                                            supabase.table("otp_bypass_requests").insert(req_payload).execute()
                                            st.success("✅ கோரிக்கை அனுப்பப்பட்டது! அட்மின் ஒப்புதலுக்காகக் காத்திருக்கவும்.")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"கோரிக்கை அனுப்புவதில் பிழை: {e}")

                    

                # -------------------------------------------------------------
                # 🌟 5. வருகையை நிறைவு செய்யும் பட்டன் (முழுமையாக ஒருங்கிணைக்கப்பட்ட வடிவம்)
                # -------------------------------------------------------------
                # OTP விலக்கு அல்லது நேரடி OTP நிலையை உறுதிப்படுத்துதல்
                if st.session_state.get("current_visit"):
                    st.markdown("---")
                    if st.session_state.get("otp_verified", False):
                        otp_cleared = True

                    if st.button("✅ வருகையை நிறைவு செய்க", type="primary", use_container_width=True, key="btn_complete_visit_final"):
                        if not is_ready:
                            st.error("❌ ரொக்கக் கணக்கீடு அல்லது UTR எண் விடுபட்டுள்ளது! (ரொக்க வித்தியாசம் ₹0.00 ஆக இருக்க வேண்டும்)")
                        elif not otp_cleared and not locals().get("otp_already_sent", False):
                            st.error("❌ முதலில் வாடிக்கையாளருக்கு OTP அனுப்பவும் அல்லது அட்மின் விலக்குக் கோரவும்!")
                        elif not otp_cleared:
                            st.error("❌ தவறான OTP! அல்லது ஆப்பரேஷன்ஸ் இறுதி அனுமதி இன்னும் கிடைக்கவில்லை.")
                        elif not st.session_state.get("transactions_cart"):
                            st.error("❌ பட்டியலில் (Cart) எந்த நடவடிக்கைகளும் சேர்க்கப்படவில்லை! முதலில் 'படி 2'-ல் வணிக நடவடிக்கையைச் சேர்த்துவிட்டு வரவும்.")
                        else:
                            try:
                                with st.spinner("டேட்டாபேஸில் விவரங்கள் சேமிக்கப்படுகின்றன... தயவுசெய்து காத்திருக்கவும்..."):
                                    b_id = st.session_state.branch_id
                                    c_id = visit.get("customer_id")
                                    
                                    # =========================================================================
                                    # 1. தனித்துவமான வருகை எண் (Visit No) உறுதி செய்தல்
                                    # =========================================================================
                                    current_v_no = visit.get("visit_no")
                                    chk_exist = supabase.table("customer_visits").select("id").eq("visit_no", current_v_no).execute()
                                    if chk_exist.data:
                                        b_code = st.session_state.get("branch_code", "BR")[:3].upper()
                                        current_v_no = generate_branch_visit_no(b_id, b_code)

                                    pm_label = "Cash" if bank_portion == 0 else ("Bank/UPI" if cash_portion == 0 else "Split")

                                    # =========================================================================
                                    # 2. customer_visits அட்டவணையில் சேர்த்தல் (கல்லா நோட்டுகள் கணக்கீட்டுடன்)
                                    # =========================================================================
                                    visit_data = {
                                        "visit_no": current_v_no,
                                        "customer_id": c_id,
                                        "branch_id": b_id,
                                        "total_paid": float(visit.get("total_paid", 0.0) or 0.0),
                                        "total_received": float(visit.get("total_received", 0.0) or 0.0),
                                        "net_cash_amount": float(visit.get("net_amount", 0.0) or (cash_portion if 'cash_portion' in locals() else 0.0)),
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
                                        "status": "Pending_Calling_Verification"
                                    }
                                    v_insert = supabase.table("customer_visits").insert(visit_data).execute()
                                    if not v_insert.data:
                                        raise Exception("customer_visits அட்டவணையில் பதிவைச் சேர்க்க முடியவில்லை! RLS கொள்கையைச் சரிபார்க்கவும்.")
                                    
                                    new_visit_id = v_insert.data[0]["id"]

                                    # =========================================================================
                                    # 3. கார்ட்டில் உள்ள ஒவ்வொரு பரிவர்த்தனையையும் தனித்தனி அட்டவணைகளில் சேமித்தல் (ஒரே லூப்)
                                    # =========================================================================
                                    for item in st.session_state.transactions_cart:
                                        t_type = str(item.get("transaction_type", ""))
                                        s_name = item.get("staff_name", "")
                                        p_amt = float(item.get("paid_amount", 0.0) or 0.0)
                                        r_amt = float(item.get("received_amount", 0.0) or 0.0)

                                        # 3.1 மீட்கப்பட்ட கடன்களை 'Closed' ஆக்குதல்
                                        if item.get("closed_loan_id"):
                                            try:
                                                supabase.table("transactions").update({"status": "Closed"}).eq("id", item["closed_loan_id"]).execute()
                                            except Exception:
                                                pass

                                        # 3.2 நகைக்கடன் (Gold Loans)
                                        if any(k in t_type for k in ["Pledge", "Loan", "நகைக்கடன்"]):
                                            try:
                                                actual_gl_no = item.get("loan_no") or item.get("gp_number") or f"GL-{datetime.now().strftime('%y%m%d%H%M%S')}"
                                                loan_payload = {
                                                    "visit_id": new_visit_id,
                                                    "branch_id": b_id,
                                                    "customer_id": c_id,
                                                    "loan_no": actual_gl_no,
                                                    "ornament_details": item.get("ornament_details", ""),
                                                    "items_count": int(item.get("items_count") or 1),
                                                    "gross_weight": float(item.get("total_weight", 0.0) or item.get("gross_weight", 0.0) or 0.0),
                                                    "net_weight": float(item.get("net_weight", 0.0) or 0.0),
                                                    "purity": item.get("purity", "916 KDM"),
                                                    "sanctioned_amount": float(item.get("paid_amount", 0.0) or item.get("amount", 0.0)),
                                                    "scheme_name": item.get("scheme_name", "Regular"),
                                                    "interest_rate": float(item.get("interest_rate", 18.0) or 18.0),
                                                    "market_rate_per_gram": float(item.get("market_rate", 0.0) or 0.0),
                                                    "staff_name": s_name,
                                                    "status": "Active"
                                                }
                                                supabase.table("gold_loans").insert(loan_payload).execute()
                                            except Exception as gl_err:
                                                st.error(f"⚠️ gold_loans அட்டவணையில் சேமிப்பதில் பிழை: {gl_err}")

                                        # 3.3 நகை விற்பனை (Gold Sales)
                                        elif any(k in t_type for k in ["Sale", "விற்பனை"]):
                                            try:
                                                sale_payload = {
                                                    "visit_id": new_visit_id,
                                                    "branch_id": b_id,
                                                    "customer_id": c_id,
                                                    "bill_no": item.get("bill_no") or f"SL-{datetime.now().strftime('%y%m%d%H%M%S')}",
                                                    "item_name": item.get("ornament_details", "Gold Jewellery"),
                                                    "gross_weight": float(item.get("total_weight", 0.0) or item.get("gross_weight", 0.0) or 0.0),
                                                    "net_weight": float(item.get("net_weight", 0.0) or 0.0),
                                                    "gold_rate_per_gram": float(item.get("rate_per_gram") or item.get("gold_rate_per_gram") or item.get("market_rate") or 0.0),
                                                    "total_sale_amount": float(item.get("received_amount", 0.0) or item.get("amount", 0.0)),
                                                    "staff_name": s_name
                                                }
                                                supabase.table("gold_sales").insert(sale_payload).execute()
                                            except Exception as sl_err:
                                                st.error(f"⚠️ gold_sales அட்டவணையில் சேமிப்பதில் பிழை: {sl_err}")

                                        # 3.4 தங்கம் வாங்குதல் (Gold Purchases / GP)
                                        elif any(k in t_type for k in ["GP", "Purchase", "வாங்க", "கொள்முதல்"]):
                                            try:
                                                details_list = [
                                                    f"வகை: {item.get('gp_mode', 'Direct')}",
                                                    f"வவுச்சர் எண்: {item.get('voucher_no', '-')}",
                                                    f"நகைகள் விவரம்:\n{item.get('ornament_details', 'Gold Jewellery')}"
                                                ]
                                                if item.get("is_takeover") or item.get("bank_source"):
                                                    details_list.append(
                                                        f"\n[Takeover விவரங்கள்]\n"
                                                        f"முந்தைய நிறுவனம்: {item.get('bank_source', '-')}\n"
                                                        f"முந்தைய கடன் எண்: {item.get('prev_loan_no', '-')}\n"
                                                        f"மீட்பு அட்வான்ஸ்: ₹{float(item.get('advance_paid', 0.0)):,.2f}\n"
                                                        f"மீதி வழங்கியது: ₹{float(item.get('balance_payable', 0.0)):,.2f}"
                                                    )
                                                if item.get("remarks"):
                                                    details_list.append(f"குறிப்பு: {item.get('remarks')}")

                                                full_details_text = "\n".join(details_list)
                                                clean_gp_no = item.get("gp_number") or item.get("loan_number") or f"AVL/GP/{datetime.now().strftime('%y%m%d%H%M')}"

                                                purchase_payload = {
                                                    "visit_id": new_visit_id,
                                                    "branch_id": b_id,
                                                    "customer_id": c_id,
                                                    "purchase_bill_no": clean_gp_no,
                                                    "item_details": full_details_text,
                                                    "gross_weight": float(item.get("gross_weight") or item.get("total_weight") or 0.0),
                                                    "net_pure_weight": float(item.get("net_weight") or 0.0),
                                                    "buy_rate_per_gram": float(item.get("rate_per_gram", 0.0) or 0.0),
                                                    "purchase_amount": float(item.get("total_value") or item.get("amount") or item.get("paid_amount") or 0.0),
                                                    "staff_name": s_name
                                                }
                                                supabase.table("gold_purchases").insert(purchase_payload).execute()
                                            except Exception as gp_err:
                                                st.error(f"⚠️ gold_purchases அட்டவணையில் சேமிப்பதில் பிழை: {gp_err}")

                                        # =============================================================
                                        # 3.5 புதிய நிலையான வைப்பு நிதி (Fixed Deposits - FD)
                                        # =============================================================
                                        elif "FD Open" in t_type or ("FD" in t_type and "Open" in t_type):
                                            try:
                                                fd_meta = item.get("extra_meta_data", {}) or item
                                                dep_amt = float(fd_meta.get("deposit_amount") or item.get("received_amount") or item.get("amount") or 0.0)
                                                
                                                # 🌟 1. எண்களை எடுக்கும் பல அடுக்கு பாதுகாப்பு:
                                                final_fd_no = fd_meta.get("account_no") or item.get("account_no") or item.get("acc_no")
                                                if not final_fd_no:
                                                    # remarks-ல் இருந்து Regex மூலம் தேடுதல் (எ.கா: FD No: AVL/FD/0021)
                                                    m_fd = re.search(r'([A-Za-z0-9]+/[Ff][Dd]/\d+)', str(item.get("remarks", "")))
                                                    if m_fd:
                                                        final_fd_no = m_fd.group(1)
                                                    else:
                                                        final_fd_no = generate_fd_account_no(b_id)

                                                fd_insert_data = {
                                                    "visit_id": new_visit_id,
                                                    "branch_id": b_id,
                                                    "customer_id": c_id,
                                                    "fd_account_no": final_fd_no,  # 👈 எந்த நிலையிலும் NULL ஆகாது!
                                                    "deposit_amount": dep_amt,
                                                    "tenure_months": int(fd_meta.get("tenure_months", 12)),
                                                    "interest_rate": float(fd_meta.get("interest_rate", 12.0)),
                                                    "maturity_amount": dep_amt * 1.12,
                                                    "nominee_name": fd_meta.get("nominee") or fd_meta.get("nominee_name", "-"),
                                                    "nominee_relation": fd_meta.get("relation") or fd_meta.get("nominee_relation", "-"),
                                                    "status": "Active"
                                                }
                                                supabase.table("fixed_deposits").insert(fd_insert_data).execute()
                                            except Exception as fd_err:
                                                st.error(f"⚠️ fixed_deposits அட்டவணையில் சேமிப்பதில் பிழை: {fd_err}")

                                        # =============================================================
                                        # 3.6 புதிய தொடர் வைப்பு நிதி (Recurring Deposits - RD)
                                        # =============================================================
                                        elif "RD Open" in t_type or ("RD" in t_type and "Open" in t_type):
                                            try:
                                                rd_meta = item.get("extra_meta_data", {}) or item
                                                inst_amt = float(rd_meta.get("installment_amount") or item.get("received_amount") or item.get("amount") or 0.0)
                                                
                                                # 🌟 1. எண்களை எடுக்கும் பல அடுக்கு பாதுகாப்பு:
                                                final_rd_no = rd_meta.get("account_no") or item.get("account_no") or item.get("acc_no")
                                                if not final_rd_no:
                                                    # remarks-ல் இருந்து Regex மூலம் தேடுதல் (எ.கா: RD No: AVL/RD/0016)
                                                    m_rd = re.search(r'([A-Za-z0-9]+/[Rr][Dd]/\d+)', str(item.get("remarks", "")))
                                                    if m_rd:
                                                        final_rd_no = m_rd.group(1)
                                                    else:
                                                        final_rd_no = generate_rd_account_no(b_id)

                                                rd_insert_data = {
                                                    "visit_id": new_visit_id,
                                                    "branch_id": b_id,
                                                    "customer_id": c_id,
                                                    "rd_account_no": final_rd_no,  # 👈 எந்த நிலையிலும் NULL ஆகாது!
                                                    "monthly_installment": inst_amt,
                                                    "tenure_months": int(rd_meta.get("tenure_months", 12)),
                                                    "interest_rate": float(rd_meta.get("interest_rate", 12.0)),
                                                    "total_target_amount": inst_amt * 12,
                                                    "current_installment_no": 1,
                                                    "nominee_name": rd_meta.get("nominee") or rd_meta.get("nominee_name", "-"),
                                                    "nominee_relation": rd_meta.get("relation") or rd_meta.get("nominee_relation", "-"),
                                                    "status": "Active"
                                                }
                                                supabase.table("recurring_deposits").insert(rd_insert_data).execute()
                                            except Exception as rd_err:
                                                st.error(f"⚠️ recurring_deposits அட்டவணையில் சேமிப்பதில் பிழை: {rd_err}")

                                        # 3.7 பொதுவான transactions அட்டவணையில் பதிவு (ஆடிட் & பாஸ்புக்)
                                        try:
                                            general_txn = {
                                                "visit_id": new_visit_id,
                                                "branch_id": b_id,
                                                "customer_id": c_id,
                                                "customer_name": visit.get("customer_name"),
                                                "mobile": visit.get("mobile"),
                                                "transaction_type": t_type,
                                                "staff_name": s_name,
                                                "amount": float(item.get("amount", 0.0) or (p_amt if p_amt > 0 else r_amt)),
                                                "paid_amount": p_amt,
                                                "received_amount": r_amt,
                                                "gross_weight": float(item.get("total_weight", 0.0) or item.get("gross_weight", 0.0) or 0.0),
                                                "net_weight": float(item.get("net_weight", 0.0) or 0.0),
                                                "item_details": item.get("ornament_details", ""),
                                                "remarks": item.get("remarks", ""),
                                                "transaction_details": item.get("extra_meta_data") or item,
                                                "status": "Pending"
                                            }
                                            supabase.table("transactions").insert(general_txn).execute()
                                        except Exception as txn_err:
                                            st.error(f"⚠️ transactions அட்டவணையில் சேமிப்பதில் பிழை: {txn_err}")

                                    # =========================================================================
                                    # 4. நகைக்கடன் வரிசை எண்களை உயர்த்துதல் (Branch Sequence Update)
                                    # =========================================================================
                                    pledge_items = [i for i in st.session_state.transactions_cart if "Pledge" in str(i.get("transaction_type", ""))]
                                    if pledge_items:
                                        try:
                                            res = supabase.table("branch_loan_sequences").select("last_number").eq("branch_id", b_id).execute()
                                            current_db_last = int(res.data[0]["last_number"]) if res.data else 0
                                            new_db_last = current_db_last + len(pledge_items)
                                            supabase.table("branch_loan_sequences").update({"last_number": new_db_last}).eq("branch_id", b_id).execute()
                                        except Exception:
                                            pass

                                    # =========================================================================
                                    # 5. பயன்படுத்தப்பட்ட OTP பைபாஸை 'Used' என மாற்றுதல்
                                    # =========================================================================
                                    try:
                                        supabase.table("otp_bypass_requests").update({"status": "Used"}).eq("customer_id", c_id).eq("status", "Approved").execute()
                                    except Exception:
                                        pass

                                    # =========================================================================
                                    # 6. நினைவகத்தை (Session State) முழுமையாக ரீசெட் செய்து நிறைவு செய்தல்
                                    # =========================================================================
                                    st.session_state["last_saved_visit"] = {
                                        "visit_no": current_v_no,
                                        "customer_name": visit.get("customer_name", "-"),
                                        "txn_count": len(st.session_state.transactions_cart),
                                        "total_paid": float(visit.get("total_paid", 0.0) or 0.0),
                                        "total_received": float(visit.get("total_received", 0.0) or 0.0)
                                    }

                                    st.session_state.transactions_cart = []
                                    st.session_state.current_visit = None
                                    st.session_state.otp_cleared = False
                                    st.session_state.otp_verified = False
                                    st.session_state.otp_already_sent = False
                                    st.session_state.generated_otp = None
                                    st.session_state.current_declaration = None
                                    st.session_state.declaration_gl_no = None
                                    if "otp_bypass_requested" in st.session_state:
                                        st.session_state.otp_bypass_requested = False
                                    if "form_reset_counter" in st.session_state:
                                        st.session_state.form_reset_counter += 1

                                    st.success(f"🎉 வருகை {current_v_no} வெற்றிகரமாக நிறைவுபெற்றது! (ஆப்பரேஷன்ஸ் ஒப்புதலுக்கு அனுப்பப்பட்டது)")
                                    st.balloons()
                                    st.rerun()

                            except Exception as save_err:
                                st.error(f"❌ வருகையைச் சேமிப்பதில் பிழை ஏற்பட்டது: {save_err}")
                                st.warning("⚠️ மேலே உள்ள எரரைச் சரிபார்க்கவும். உங்கள் கார்ட்டில் உள்ள தரவுகள் அழியாமல் அப்படியே உள்ளன.")


