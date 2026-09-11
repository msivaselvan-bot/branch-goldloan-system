from datetime import datetime, date
import random
import json
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

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

def generate_fd_bond_pdf(data):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # வெளிப் பார்டர்
    c.setLineWidth(1.5)
    c.rect(25, 25, width - 50, height - 50)

    # நிறுவனத் தலைப்பு
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 50, "MUTHUSISE GOLD PRODUCT PRIVATE LIMITED")
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width / 2, height - 65, "CIN: U47912TN2024PTC171143 | (Indian Gold Finance)")
    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2, height - 80, "435, 2nd Floor, KP Road, Chettikulam Junction, Nagercoil-629001")

    c.setLineWidth(0.75)
    c.line(40, height - 92, width - 40, height - 92)

    # ஆவணத் தலைப்பு
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(width / 2, height - 115, "PROMISSORY NOTE & FIXED DEPOSIT RECEIPT")

    # விவரங்கள்
    c.setFont("Helvetica", 10)
    y = height - 150
    gap = 22

    details = [
        ("Managing Director:", "M SIVASELVAN - DIN10673471"),
        ("FD Account / Ref No:", data.get("account_no", "-")),
        ("Customer Name:", data.get("customer_name", "-")),
        ("Customer Code:", data.get("customer_code", "-")),
        ("Principal Amount:", f"Rs. {float(data.get('deposit_amount') or 0):,.2f} (INR)"),
        ("Interest Rate / Terms:", "15.6% p.a. (1.3% pm) monthly basis"),
        ("Maturity Date:", str(data.get("maturity_date", "August 18th 2030"))),
        ("Nominee Name:", data.get("nominee", "-")),
        ("Relationship / Details:", f"Relationship: {data.get('relation', '-')}, Age: {data.get('age', '-')}, Address: {data.get('address', '-')}")
    ]

    for label, val in details:
        c.drawString(50, y, label)
        c.drawString(190, y, f": {val}")
        y -= gap

    # கையொப்பப் பகுதி
    y -= 30
    c.drawString(50, y, "Nagercoil")
    c.drawString(50, y - 15, f"Date: {str(date.today())}")

    c.drawString(width - 220, y, "For Muthusise Gold Product Private Limited")
    c.drawString(width - 180, y - 45, "M SIVASELVAN")
    c.drawString(width - 190, y - 60, "DIN10673471 (Managing Director)")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


def generate_rd_certificate_pdf(data):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setLineWidth(1.5)
    c.rect(25, 25, width - 50, height - 50)

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 50, "MUTHUSISE GOLD PRODUCT PRIVATE LIMITED")
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width / 2, height - 65, "RECURRING DEPOSIT BOND / CERTIFICATE")

    c.setLineWidth(0.75)
    c.line(40, height - 78, width - 40, height - 78)

    y = height - 110
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, f"RECEIPT NO.: {data.get('account_no', '0013')}")

    y -= 25
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "NAME AND FULL ADDRESS OF CUSTOMER:")
    c.setFont("Helvetica", 10)
    c.drawString(50, y - 15, str(data.get('customer_name', '-')))
    c.drawString(50, y - 30, str(data.get('address', '-')))

    y -= 65
    c.setFont("Helvetica-Bold", 9)
    c.drawString(50, y, "ACCOUNT NUMBER")
    c.drawString(180, y, "BRANCH CODE")
    c.drawString(280, y, "DURATION")
    c.drawString(380, y, "MATURITY DATE")
    c.drawString(480, y, "ROI")

    c.setFont("Helvetica", 9)
    c.drawString(50, y - 15, str(data.get('account_no', '-')))
    c.drawString(180, y - 15, str(data.get('branch_code', 'EDK')))
    c.drawString(280, y - 15, str(data.get('duration', '48 Months')))
    c.drawString(380, y - 15, str(data.get('maturity_date', '-')))
    c.drawString(480, y - 15, str(data.get('roi', '12.25%')))

    y -= 45
    c.setFont("Helvetica-Bold", 9)
    c.drawString(50, y, "INSTALLMENT AMOUNT")
    c.drawString(200, y, "TOTAL DEPOSIT AMOUNT")
    c.drawString(380, y, "MATURITY AMOUNT")

    c.setFont("Helvetica", 9)
    c.drawString(50, y - 15, f"Rs. {float(data.get('installment_amount') or 0):,.2f}")
    c.drawString(200, y - 15, f"Rs. {float(data.get('total_deposit') or 0):,.2f}")
    c.drawString(380, y - 15, f"Rs. {float(data.get('maturity_amount') or 0):,.2f}")

    y -= 55
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "NOMINEE DETAILS:")

    c.setFont("Helvetica-Bold", 9)
    c.drawString(50, y - 20, "NOMINEE NAME")
    c.drawString(250, y - 20, "AGE")
    c.drawString(350, y - 20, "RELATIONSHIP")

    c.setFont("Helvetica", 9)
    c.drawString(50, y - 35, str(data.get('nominee', '-')))
    c.drawString(250, y - 35, str(data.get('age', '-')))
    c.drawString(350, y - 35, str(data.get('relation', '-')))

    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, 100, "Branch Head")
    c.drawString(width - 180, 100, "Signature of Director")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
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
            .eq("status", "Approved")
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

        # அங்கீகரிக்கப்பட்ட கிளைச் செலவுகளுக்கான நோட்டுகளைக் கழித்து, மீதி வாங்கியதைச் சேர்த்தல்
        exp_res = (
            supabase.table("branch_expenses")
            .select("denomination_details")
            .eq("branch_id", branch_id)
            .eq("status", "Approved")
            .execute()
        )
        if exp_res.data:
            for e_row in exp_res.data:
                e_den = e_row.get("denomination_details") or {}
                out_notes = e_den.get("out", {})
                in_notes = e_den.get("in", {})

                if not out_notes and not in_notes:
                    out_notes = e_den

                for k in stock:
                    stock[k] -= int(out_notes.get(k, 0) or 0)
                    stock[k] += int(in_notes.get(k, 0) or 0)

        for k in stock:
            stock[k] = max(0, stock[k])

        return stock
    except Exception:
        return empty_stock

# ==============================================================================
# காரணப் பணியாளர் அறிக்கை (திருத்தப்பட்ட நெகட்டிவ் புள்ளிகள் & பங்கீட்டு விதிகளுடன்)
# ==============================================================================
def render_staff_attribution_report(selected_branch_id=None, key_suffix="default"):
    st.markdown("### 📊 காரணப் பணியாளர் அறிக்கை & ஸ்கீம் வாரியான ஊக்கத்தொகை (Scheme-wise Incentive & Points Report)")

    f_col1, f_col2, f_col3 = st.columns([1.5, 1.5, 2])
    start_date = f_col1.date_input("தொடக்கத் தேதி (From):", value=date.today().replace(day=1), key=f"rep_s_{selected_branch_id}_{key_suffix}")
    end_date = f_col2.date_input("முடிவுத் தேதி (To):", value=date.today(), key=f"rep_e_{selected_branch_id}_{key_suffix}")

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

    try:
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
    except Exception:
        try:
            q_fallback = supabase.table("customer_visits").select("*").gte("created_at", start_dt_str).lte("created_at", end_dt_str)
            if selected_branch_id:
                q_fallback = q_fallback.eq("branch_id", selected_branch_id)
            visits = q_fallback.execute().data or []
        except Exception:
            visits = []

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
            paid_val = float(t.get("paid_amount", 0.0))
            rec_val = float(t.get("received_amount", 0.0))
            remarks_str = str(t.get("remarks", ""))

            effective_vol = 0.0
            if "Release" in txn_type:
                try:
                    if "அசல்: ₹" in remarks_str:
                        p_str = remarks_str.split("அசல்: ₹")[1].split("|")[0].strip().replace(",", "")
                        effective_vol = float(p_str)
                    else:
                        effective_vol = rec_val
                except Exception:
                    effective_vol = rec_val
            elif "Part Payment" in txn_type:
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

            rule_info = rule_dict.get((txn_type, detected_scheme)) or rule_dict.get((txn_type, "All")) or {"basis_type": "Amount", "unit_value": 100000.0, "points_per_unit": 10.0}

            basis = rule_info.get("basis_type", "Amount")
            unit_val = float(rule_info.get("unit_value", 100000.0) or 100000.0)
            pts_per_unit = float(rule_info.get("points_per_unit", 10.0) or 0.0)

            calc_pts = 0.0
            if basis == "Weight_Grams":
                grams_val = 0.0
                try:
                    if "எடை:" in remarks_str:
                        part = remarks_str.split("எடை:")[1].split("g")[0].strip()
                        grams_val = float(part)
                except Exception:
                    grams_val = 0.0
                calc_pts = (grams_val / unit_val) * pts_per_unit if unit_val > 0 else 0.0
                disp_val = f"{grams_val} g"
            else:
                base_calc = (effective_vol / unit_val) * pts_per_unit if unit_val > 0 else 0.0
                if "Release" in txn_type or "Part Payment" in txn_type:
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
        selected_staff_filter = st.selectbox("காரணப் பணியாளரைத் தேர்ந்தெடுக்கவும்:", staff_filter_options, key=f"staff_flt_{selected_branch_id}_{key_suffix}")

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
        key=f"dl_csv_{selected_branch_id}_{key_suffix}"
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

try:
    branches_res = supabase.table("branches").select("*").execute()
    branches_data = branches_res.data if branches_res and branches_res.data else []
except Exception as e:
    branches_data = []
    st.error(f"⚠️ டேட்டாபேஸ் பிழை: {e}")

# மேப்பிங் மாறிகள் சரியாக வரையறுக்கப்பட்டுள்ளதா என்பதை உறுதிப்படுத்தவும்:
branch_options = {b["branch_name"]: b["id"] for b in branches_data}
branch_id_to_name = {b["id"]: b["branch_name"] for b in branches_data}
# ==========================================
# 5. லாகின் மற்றும் முதன்மை திரை கட்டுப்பாடு
# ==========================================
if not st.session_state.get("logged_in", False):
    col_left, col_center, col_right = st.columns([1.2, 1.4, 1.2])
    with col_center:
        st.markdown("""
        <div class="login-box" style="text-align: center; padding: 20px; background-color: #3b1443; color: white; border-radius: 10px;">
            <h3>🏦 முத்துசிஸ் கோல்டு கம்பெனி</h3>
            <p>பணியாளர் பாதுகாப்பான உள்நுழைவு</p>
        </div>
        """, unsafe_allow_html=True)

        st.subheader("🔐 அமைப்புக்குள் உள்நுழைதல் (Login)")

        with st.form("login_form_unique_final"):
            entered_username = st.text_input("Username").strip()
            entered_password = st.text_input("Password", type="password").strip()
            submit_login = st.form_submit_button("உள்நுழை (Login)", type="primary")

            if submit_login:
                if entered_username and entered_password:
                    try:
                        res = supabase.table("users").select("*").eq("username", entered_username).execute()
                        user_list = res.data if res.data else []

                        if user_list:
                            user_info = user_list[0]
                            db_pass = str(user_info.get("password_hash") or user_info.get("password") or "").strip()
                            is_active = user_info.get("is_active", True)

                            if db_pass == entered_password:
                                if is_active:
                                    st.session_state.logged_in = True
                                    st.session_state.user_role = user_info.get("role", "Staff")
                                    
                                    b_id = user_info.get("branch_id")
                                    b_name = "Head Office / பொது"
                                    if b_id:
                                        try:
                                            b_res = supabase.table("branches").select("branch_name").eq("id", b_id).execute()
                                            if b_res.data:
                                                b_name = b_res.data[0].get("branch_name", "Head Office")
                                        except Exception:
                                            pass
                                    
                                    st.session_state.branch = b_name
                                    st.session_state.branch_id = b_id
                                    st.session_state.username = user_info.get("name", entered_username)
                                    st.session_state.profile_image = user_info.get("profile_image_url")
                                    
                                    st.success("வெற்றிகரமாக உள்நுழைந்துவிட்டீர்கள்!")
                                    st.rerun()
                                else:
                                    st.error("❌ இந்தக் கணக்கு முடக்கப்பட்டுள்ளது.")
                            else:
                                st.error("❌ தவறான கடவுச்சொல்!")
                        else:
                            st.error("❌ இந்தப் பெயரில் பயனர் இல்லை.")
                    except Exception as err:
                        st.error(f"பிழை: {err}")
                else:
                    st.warning("தயவுசெய்து Username மற்றும் Password இரண்டையும் உள்ளிடவும்.")

    st.stop()

# ==========================================
# 6. லாகின் செய்த பிறகு மட்டுமே இயங்கும் மெயின் ஆப் பகுதி
# ==========================================
top_col1, top_col2, top_col3, top_col4 = st.columns([2.5, 2, 1, 1])
with top_col1:
    st.write(f"🏢 **கிளை:** {st.session_state.get('branch', 'General')}")
with top_col2:
    st.write(f"👤 **பயனர்:** {st.session_state.get('username', '')} ({st.session_state.get('user_role', '')})")
with top_col3:
    if st.button("🔄 Refresh", use_container_width=True, help="பக்கத்தை முழுமையாகப் புதுப்பிக்க"):
        st.rerun()
with top_col4:
    if st.button("வெளியேறு", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.current_visit = None
        st.session_state.transactions_cart = []
        st.session_state.generated_otp = None
        st.rerun()

st.markdown("---")

user_role = st.session_state.get("user_role", "Staff")

# ----------------------------------------------------
# A. நிர்வாக மேலாண்மை திரை (ADMIN PANEL WITH 10 FULL TABS)
# ----------------------------------------------------
if user_role == "Admin":
    st.header("⚙️ நிர்வாக மேலாண்மை (Admin Control Panel)")
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
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
    ])

    with tab1:
        st.subheader("🏢 கிளைகள் மேலாண்மை (Branches Management)")
        b_sub_tab1, b_sub_tab2 = st.tabs(["➕ புதிய கிளை சேர்த்தல்", "✏️ கிளை விவரங்களைத் திருத்துதல் (Edit)"])

        with b_sub_tab1:
            st.markdown("##### புதிய கிளை பதிவுப் படிவம்")
            with st.form("admin_add_branch_form", clear_on_submit=True):
                bc1, bc2 = st.columns(2)
                with bc1:
                    b_name = st.text_input("கிளையின் பெயர் *", placeholder="எ.கா: திங்கள்நகர் கிளை")
                    b_code = st.text_input("கிளை குறியீடு *", placeholder="எ.கா: TGL")
                    b_phone = st.text_input("தொடர்பு எண் (Contact No)", placeholder="எ.கா: 9876543210")
                with bc2:
                    b_email = st.text_input("இமெயில் ஐடி (Email ID)", placeholder="branch@muthusise.com")
                    b_manager = st.text_input("Office Manager பெயர்", placeholder="மேனேஜர் பெயர்")
                
                b_address = st.text_area("கிளை முகவரி (Branch Address)", placeholder="முழு முகவரி...")
                submit_branch = st.form_submit_button("கிளையைச் சேர்", type="primary")

                if submit_branch:
                    if b_name.strip() and b_code.strip():
                        try:
                            supabase.table("branches").insert({
                                "branch_name": b_name.strip(),
                                "branch_code": b_code.strip().upper(),
                                "address": b_address.strip(),
                                "branch_address": b_address.strip(),
                                "email": b_email.strip(),
                                "phone": b_phone.strip(),
                                "office_manager": b_manager.strip()
                            }).execute()
                            st.success(f"'{b_name}' வெற்றிகரமாகச் சேர்க்கப்பட்டது!")
                            st.rerun()
                        except Exception as err:
                            st.error(f"பிழை: {err}")
                    else:
                        st.warning("தயவுசெய்து கிளையின் பெயர் மற்றும் குறியீட்டை உள்ளிடவும்.")

            st.markdown("---")
            st.markdown("##### 📋 ஏற்கனவே உள்ள கிளைகள் பட்டியல்")
            b_list_res = supabase.table("branches").select("id, branch_name, branch_code, address, phone, email, office_manager").order("id").execute()
            if b_list_res.data:
                st.dataframe(pd.DataFrame(b_list_res.data), use_container_width=True)
            else:
                st.info("கிளைகள் எதுவும் பதிவு செய்யப்படவில்லை.")

        with b_sub_tab2:
            st.markdown("##### ✏️ கிளை விவரங்களைத் திருத்துதல்")
            b_edit_res = supabase.table("branches").select("*").order("id").execute()
            branches_data = b_edit_res.data if b_edit_res.data else []

            if branches_data:
                branch_choices = {f"{b['branch_name']} ({b['branch_code']}) - ID: {b['id']}": b for b in branches_data}
                selected_choice = st.selectbox("எடிட் செய்ய வேண்டிய கிளೆಯನ್ನುத் தேர்ந்தெடுக்கவும்", list(branch_choices.keys()), key="select_branch_to_edit_unique_tab2")
                curr_b = branch_choices[selected_choice]

                with st.form(key=f"unique_edit_branch_form_{curr_b['id']}_{curr_b['branch_code']}"):
                    e_name = st.text_input("கிளையின் பெயர்", value=curr_b.get("branch_name", ""), key=f"e_name_{curr_b['id']}")
                    e_code = st.text_input("கிளை குறியீடு", value=curr_b.get("branch_code", ""), key=f"e_code_{curr_b['id']}")
                    e_phone = st.text_input("தொடர்பு எண்", value=curr_b.get("phone", ""), key=f"e_phone_{curr_b['id']}")
                    e_email = st.text_input("இமெயில் ஐடி", value=curr_b.get("email", ""), key=f"e_email_{curr_b['id']}")
                    e_manager = st.text_input("Office Manager பெயர்", value=curr_b.get("office_manager", ""), key=f"e_manager_{curr_b['id']}")
                    e_address = st.text_area("கிளை முகவரி", value=curr_b.get("address", "") or curr_b.get("branch_address", ""), key=f"e_address_{curr_b['id']}")

                    if st.form_submit_button("கிளை விவரங்களைப் புதுப்பி", type="primary"):
                        try:
                            supabase.table("branches").update({
                                "branch_name": e_name.strip(),
                                "branch_code": e_code.strip().upper(),
                                "address": e_address.strip(),
                                "branch_address": e_address.strip(),
                                "email": e_email.strip(),
                                "phone": e_phone.strip(),
                                "office_manager": e_manager.strip()
                            }).eq("id", curr_b["id"]).execute()
                            st.success("✅ கிளை விவரங்கள் வெற்றிகரமாகப் புதுப்பிக்கப்பட்டன!")
                            st.rerun()
                        except Exception as err:
                            st.error(f"பிழை: {err}")
            else:
                st.info("திருத்துவதற்கு கிளைகள் எதுவும் இல்லை.")

    with tab2:
        st.subheader("👥 பணியாளர்கள் பட்டியல் & சேர்த்தல்")
        users_res = supabase.table("users").select("id, name, username, role, branch_id, is_active").order("id").execute()
        br_res_global = supabase.table("branches").select("id, branch_name, branch_code").execute()
        branches_dict_global = {b["id"]: f"{b['branch_name']} ({b['branch_code']})" for b in br_res_global.data} if br_res_global.data else {}

        if users_res.data:
            st.dataframe(pd.DataFrame([{
                "ID": u["id"], "பெயர்": u["name"], "Username": u["username"], "பணி நிலை": u["role"],
                "கிளை": branches_dict_global.get(u.get("branch_id"), "HO / Special"),
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
                branch_ids = list(branches_dict_global.keys())
                user_choices = {}
                for u in users_res.data:
                    b_id = u.get("branch_id")
                    b_name = branches_dict_global.get(b_id, "கிளை ஒதுக்கப்படவில்லை")
                    display_name = f"{u.get('name', 'No Name')} (@{u.get('username', '')}) - கிளை: {b_name}"
                    user_choices[display_name] = u

                selected_user_key = st.selectbox("திருத்த வேண்டிய பணியாளர்", list(user_choices.keys()), key="edit_staff_select_box_unique")
                curr_user = user_choices[selected_user_key]

                with st.form(key=f"admin_edit_user_form_{curr_user['id']}"):
                    edit_name = st.text_input("பெயர்", value=curr_user.get("name", ""), key=f"edit_name_{curr_user['id']}")
                    edit_pass = st.text_input("புதிய கடவுச்சொல் (விரும்பினால் மட்டும்)", type="password", key=f"edit_pass_{curr_user['id']}")
                    current_branch_id = curr_user.get("branch_id")
                    default_idx = branch_ids.index(current_branch_id) if current_branch_id in branch_ids else 0
                    
                    selected_branch_name = st.selectbox(
                        "கிளையை மாற்றுக (Assign Branch)",
                        options=list(branches_dict_global.values()) if branches_dict_global else ["கிளைகள் இல்லை"],
                        index=default_idx if branches_dict_global else 0,
                        key=f"staff_branch_select_{curr_user['id']}"
                    )
                    
                    selected_branch_id = None
                    for b_id, b_label in branches_dict_global.items():
                        if b_label == selected_branch_name:
                            selected_branch_id = b_id
                            break

                    roles_list = ["Branch Head / Cashier", "Staff", "Operations", "Auditor", "Admin"]
                    current_role = curr_user.get("role", "Staff")
                    role_idx = roles_list.index(current_role) if current_role in roles_list else 0
                    edit_role = st.selectbox("பணி நிலை", roles_list, index=role_idx, key=f"edit_role_{curr_user['id']}")
                    edit_status = st.radio("நிலை", ["Active", "Inactive"], index=0 if curr_user.get("is_active", True) else 1, key=f"edit_status_{curr_user['id']}")

                    if st.form_submit_button("புதுப்பி", type="primary"):
                        try:
                            up_data = {
                                "name": edit_name.strip(), "role": edit_role, 
                                "branch_id": selected_branch_id, "is_active": edit_status == "Active"
                            }
                            if edit_pass.strip():
                                up_data["password_hash"] = edit_pass.strip()
                            supabase.table("users").update(up_data).eq("id", curr_user["id"]).execute()
                            st.success("✅ பணியாளர் விவரங்கள் மற்றும் கிளை வெற்றிகரமாகப் புதுப்பிக்கப்பட்டன!")
                            st.rerun()
                        except Exception as err:
                            st.error(f"பிழை: {err}")

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
                    gs_penal_chg = st.number_input("Penal Charges (%)", min_value=0.0, value=2.0, step=0.5)

                if st.form_submit_button("நகைக்கடன் ஸ்கீமைச் சேமி", type="primary"):
                    if gs_name.strip():
                        supabase.table("gold_loan_schemes").insert({
                            "scheme_name": gs_name.strip(), "rate_per_gram": float(gs_rpg),
                            "min_loan_amount": float(gs_min), "max_loan_amount": float(gs_max),
                            "scheme_tenor_months": int(gs_tenor), "is_active": True
                        }).execute()
                        st.success("நகைக்கடன் திட்டம் சேமிக்கப்பட்டது!")
                        st.rerun()

        with s_tab2:
            st.markdown("##### 📑 புதிய FD திட்டம் உருவாக்குதல்")
            with st.form("admin_fd_scheme_form", clear_on_submit=True):
                fd_name = st.text_input("Scheme Name *")
                if st.form_submit_button("FD ஸ்கீமைச் சேமி", type="primary"):
                    if fd_name.strip():
                        supabase.table("fd_schemes").insert({"scheme_name": fd_name.strip(), "is_active": True}).execute()
                        st.success("FD திட்டம் சேமிக்கப்பட்டது!")
                        st.rerun()

        with s_tab3:
            st.markdown("##### 📈 புதிய RD திட்டம் உருவாக்குதல்")
            with st.form("admin_rd_scheme_form", clear_on_submit=True):
                rd_name = st.text_input("Scheme Name *")
                if st.form_submit_button("RD ஸ்கீமைச் சேமி", type="primary"):
                    if rd_name.strip():
                        supabase.table("rd_schemes").insert({"scheme_name": rd_name.strip(), "is_active": True}).execute()
                        st.success("RD திட்டம் சேமிக்கப்பட்டது!")
                        st.rerun()

    with tab4:
        st.subheader("🎯 பணியாளர் இன்சென்டிவ் & புள்ளிகள் விதிகள் (Staff Incentive Master)")
        set_res = supabase.table("incentive_settings").select("*").eq("id", 1).execute().data
        curr_rpp = float(set_res[0].get("rupees_per_point", 5.0)) if set_res else 5.0
        curr_pen = float(set_res[0].get("negative_growth_penalty_per_lakh", 15.0)) if set_res else 15.0

        with st.container(border=True):
            gp_col1, gp_col2, gp_col3 = st.columns(3)
            with gp_col1:
                new_rpp = st.number_input("ஒரு புள்ளிக்கான ரூபாய் மதிப்பு (1 Point = ₹):", value=curr_rpp, step=0.5)
            with gp_col2:
                new_pen = st.number_input("நெகட்டிவ் கடன் வளர்ச்சி அபராதப் புள்ளி (₹1 லட்சத்திற்கு):", value=curr_pen, step=1.0)
            with gp_col3:
                st.write("")
                if st.button("💾 பொது மதிப்புகளைச் சேமி (Update Values)", type="primary"):
                    supabase.table("incentive_settings").upsert({
                        "id": 1, "rupees_per_point": float(new_rpp),
                        "negative_growth_penalty_per_lakh": float(new_pen)
                    }).execute()
                    st.success("புள்ளி மதிப்பு புதுப்பிக்கப்பட்டது!")
                    st.rerun()

    with tab5:
        st.subheader("📥 மொத்தப் பதிவேற்றம் (Bulk Import)")
        st.info("பழைய தரவுகளை மொத்தமாகப் பதிவேற்றுக.")

    with tab6:
        st.subheader("🗂️ வாடிக்கையாளர் மேலாண்மை (Customer Directory)")
        cust_res_admin = supabase.table("customers").select("*").order("id", desc=True).limit(50).execute().data or []
        if cust_res_admin:
            st.dataframe(pd.DataFrame(cust_res_admin), use_container_width=True)

    with tab7:
        st.subheader("📊 வருகை & பரிவர்த்தனை திருத்தம்")
        visits_admin = supabase.table("customer_visits").select("*").order("id", desc=True).limit(20).execute().data or []
        if visits_admin:
            st.dataframe(pd.DataFrame(visits_admin), use_container_width=True)

    with tab8:
        st.subheader("💰 கிளை துவக்க இருப்பு & கல்லா")
        sel_op_branch = st.selectbox("கிளை:", list(branch_options.keys()), key="sel_op_b_admin")
        with st.form("admin_op_form_main"):
            op_500 = st.number_input("₹500", min_value=0, step=1, key="op_500_key_m")
            calc_total = op_500 * 500
            st.write(f"**மொத்தத் தொகை:** ₹{calc_total:,.2f}")
            if st.form_submit_button("சேமி", type="primary"):
                st.success("சேமிக்கப்பட்டது!")

    with tab9:
        st.subheader("🏦 தலைமையக பணப் பரிமாற்றம்")
        fund_rows = supabase.table("branch_fund_transfers").select("*").order("id", desc=True).limit(20).execute().data or []
        if fund_rows:
            st.dataframe(pd.DataFrame(fund_rows), use_container_width=True)

    with tab10:
        rep_b_opts = ["அனைத்து கிளைகளும் (All Branches)"] + list(branch_options.keys())
        sel_rep_b = st.selectbox("கிளையை வடிகட்டவும்:", rep_b_opts, key="adm_rep_branch_sel")
        filter_b_id = branch_options.get(sel_rep_b) if sel_rep_b != "அனைத்து கிளைகளும் (All Branches)" else None
        render_staff_attribution_report(selected_branch_id=filter_b_id, key_suffix="tab10_report")

# ----------------------------------------------------
# B. ஆப்பரேஷன்ஸ் மேசை (OPERATIONS DESK)
# ----------------------------------------------------
elif user_role == "Operations":
    st.header("📞 ஆப்பரேஷன்ஸ் மேசை (Operations Desk)")
    ops_tab1, ops_tab2, ops_tab3, ops_tab4, ops_tab5 = st.tabs([
        "🏦 நிதிப் பரிமாற்ற ஒப்புதல்", "👤 புதிய வாடிக்கையாளர் KYC",
        "📝 விவரத் திருத்தக் கோரிக்கைகள்", "🔔 பரிவர்த்தனை அழைப்பு சரிபார்ப்பு", 
        "📑 FD / RD பாண்ட் & சான்றிதழ்"
    ])
    
    with ops_tab1:
        st.subheader("🏦 தலைமையக & கிளை நிதிப் பரிமாற்ற ஒப்புதல் மேசை")
        pending_fund_transfers = supabase.table("branch_fund_transfers").select("*, branches(branch_name)").eq("status", "Pending_Approval").order("id", desc=True).execute().data or []
        if not pending_fund_transfers:
            st.info("✅ எந்த பணப் பரிமாற்றங்களும் நிலுவையில் இல்லை.")
        else:
            for f_item in pending_fund_transfers:
                with st.expander(f"💰 {f_item['transfer_type']} | ₹{float(f_item['amount']):,.2f}"):
                    if st.button("✅ அங்கீகரி", key=f"app_f_{f_item['id']}", type="primary"):
                        supabase.table("branch_fund_transfers").update({"status": "Approved", "approved_by": st.session_state.username}).eq("id", f_item["id"]).execute()
                        st.success("அங்கீகரிக்கப்பட்டது!")
                        st.rerun()

    with ops_tab2:
        st.subheader("👤 புதிய வாடிக்கையாளர் KYC ஒப்புதல்")
        pending_kyc = supabase.table("customers").select("*").eq("kyc_status", "Pending_KYC_Approval").execute().data or []
        if not pending_kyc:
            st.info("✅ எந்த KYC-யும் நிலுவையில் இல்லை.")
        else:
            for pc in pending_kyc:
                with st.expander(f"🆕 {pc['name']}"):
                    if st.button("✅ அங்கீகரி", key=f"app_k_{pc['id']}", type="primary"):
                        supabase.table("customers").update({"kyc_status": "Approved", "is_active": True}).eq("id", pc["id"]).execute()
                        st.success("அங்கீகரிக்கப்பட்டார்!")
                        st.rerun()

    with ops_tab3:
        st.subheader("📝 வாடிக்கையாளர் விவரத் திருத்தக் கோரிக்கைகள்")
        pending_reqs = supabase.table("customer_update_requests").select("*, customers(*), branches(branch_name)").eq("status", "Pending_Approval").order("id", desc=True).execute().data or []
        if not pending_reqs:
            st.info("✅ எந்த கோரிக்கைகளும் இல்லை.")

    with ops_tab4:
        st.subheader("📞 பரிவர்த்தனை அழைப்பு சரிபார்ப்பு")
        ops_visits = supabase.table("customer_visits").select("*, customers(name, mobile, mobile2), transactions(*), branches(branch_name)").eq("status", "Pending_Calling_Verification").order("id", desc=True).execute().data or []
        if not ops_visits:
            st.info("✅ சரிபார்க்க வேண்டிய வருகைகள் இல்லை.")

    with ops_tab5:
        st.subheader("📑 FD பாண்ட் மற்றும் RD சான்றிதழ் ஜெனரேட்டர்")
        fd_rd_txns = supabase.table("transactions").select("*, customer_visits(visit_no, customers(name, customer_code))").in_("transaction_type", ["FD Open (புதிய வைப்பு நிதி)", "RD Open (புதிய RD சேமிப்பு)"]).order("id", desc=True).execute().data or []
        if not fd_rd_txns:
            st.info("✅ புதிய கணக்குகள் எதுவும் இல்லை.")

# ----------------------------------------------------
# C. தணிக்கையர் மேசை (AUDITOR DESK)
# ----------------------------------------------------
elif user_role == "Auditor":
    st.header("🔍 தணிக்கையர் பணிப்பாய்வு (Auditor Verification)")
    pending_visits = supabase.table("customer_visits").select("*, customers(*), transactions(*), audit_records(*)").eq("status", "Submitted_to_Auditor").execute().data or []
    if not pending_visits:
        st.info("தணிக்கைக்கு நிலுவையில் உள்ள வருகைகள் இல்லை.")
    else:
        for item in pending_visits:
            with st.expander(f"வருகை: {item['visit_no']}"):
                if st.button("அங்கீகரி (Approve)", key=f"aud_app_{item['id']}", type="primary"):
                    supabase.table("customer_visits").update({"status": "Approved"}).eq("id", item["id"]).execute()
                    st.success("அங்கீகரிக்கப்பட்டது!")
                    st.rerun()

# ----------------------------------------------------
# D. கிளைப் பணியாளர் மேசை (BRANCH FLOW - STAFF DESK)
# ----------------------------------------------------
else:
    branch_tab1, branch_tab2, branch_tab3, branch_tab4, branch_tab5, branch_tab6 = st.tabs([
        "🛒 கவுண்ட்டர் வருகை & OTP", "📁 கிளை ஆவணங்கள் பதிவேற்றம்",
        "⚠️ விளக்கங்கள்", "💼 கிளை கல்லா", "🏦 HO பணப் பரிமாற்றம்", "📈 காரணப் பணியாளர் அறிக்கை"
    ])

    with branch_tab1:
        st.subheader("🛒 கவுண்ட்டர் வருகை & OTP (Counter Visit)")
        if st.session_state.get("current_visit") is None:
            st.info("புதிய வருகையைத் தொடங்க வாடிக்கையாளரைத் தேர்ந்தெடுக்கவும்.")
        else:
            st.success("வருகை فعال உள்ளது.")

    with branch_tab2:
        st.subheader("📁 கிளை ஆவணங்கள் பதிவேற்றம் (Upload Docs Desk)")
        branch_pending = supabase.table("customer_visits").select("*, customers(name, mobile), transactions(*)").eq("branch_id", st.session_state.branch_id).in_("status", ["Pending_Branch_Docs", "Pending_Calling_Verification"]).order("id", desc=True).execute().data or []
        if not branch_pending:
            st.info("தற்போது ஆவணங்கள் ஏற்ற வேண்டிய வருகைகள் எதுவும் இல்லை.")

    with branch_tab3:
        st.subheader("⚠️ தலைமை அலுவலக விளக்கங்கள் & மறுப்புகள்")
        clarification_visits = supabase.table("customer_visits").select("*, customers(name, mobile), transactions(*)").eq("branch_id", st.session_state.branch_id).eq("status", "Needs_Clarification").execute().data or []
        if not clarification_visits:
            st.info("✅ எந்த விளக்கங்களும் நிலுவையில் இல்லை.")

    with branch_tab4:
        st.subheader("💸 கிளை செலவுப் பதிவு & சில்லறை மேலாண்மை (Branch Expense Desk)")
        b_exp_logs = []
        if "branch_id" in st.session_state and st.session_state.branch_id is not None:
            try:
                b_branch_id = int(st.session_state.branch_id) if str(st.session_state.branch_id).isdigit() else st.session_state.branch_id
                b_exp_logs = supabase.table("branch_expenses").select("*").eq("branch_id", b_branch_id).order("id", desc=True).limit(15).execute().data or []
            except Exception as e:
                st.error(f"பிழை: {e}")

    with branch_tab5:
        st.subheader("🏦 தலைமையக பணப் பரிமாற்றம் (Head Office ⇄ Branch Fund Transfer Desk)")
        b_fund_logs = []
        if "branch_id" in st.session_state and st.session_state.branch_id:
            try:
                b_fund_logs = supabase.table("branch_fund_transfers").select("*").eq("branch_id", st.session_state.branch_id).order("id", desc=True).limit(20).execute().data or []
            except Exception:
                b_fund_logs = []
        if b_fund_logs:
            st.dataframe(pd.DataFrame(b_fund_logs), use_container_width=True)

    with branch_tab6:
        render_staff_attribution_report(selected_branch_id=st.session_state.branch_id, key_suffix="branch_main_report")
    
# -----------------------------------------------------------------
# Step 3: பணப் பரிமாற்றம், ரூபாய் நோட்டுகள் & OTP சரிபார்ப்பு
# -----------------------------------------------------------------
# வரி 2332-ல் உள்ள பழைய வரியை முழுமையாக நீக்கிவிட்டு இதற்குப் பதிலாக இதை மாற்றவும்:
elif st.session_state.current_visit is not None and st.session_state.current_visit.get("step") == "CASH_OTP":
    visit = st.session_state.current_visit
    net_target = visit.get("net_amount", 0.0)
    total_needed_abs = abs(net_target)
    current_drawer = get_current_branch_cash_drawer(st.session_state.branch_id)
    otp_already_sent = "generated_otp" in st.session_state and st.session_state.generated_otp is not None

    st.subheader("படி 3: பணப் பரிமாற்ற முறை & நோட்டுகள் / மீதித் தொகை கணக்கீடு")
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
                    st.caption("வாடிக்கையாளர் கவுண்ட்டரில் கொடுத்த அனைத்து ரூபாய் நோட்டுகள்:")
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
                    st.caption("வாடிக்கையாளருக்கு நாம் பட்டுவாடா செய்த அல்லது பேலன்ஸ் திருப்பிக் கொடுத்த நோட்டுகள்:")
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
                st.write(f"வாடிக்கையாளர்: **{visit['customer_name']}**")
                st.write(f"மொபைல் எண்: `{visit['mobile']}`")

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
                            sms_success, msg_detail = send_fast2sms_otp(visit["mobile"], otp_code)
                        if sms_success:
                            st.success("✅ OTP SMS அனுப்பப்பட்டது!")
                        else:
                            st.info(f"💡 சோதனை OTP: **{otp_code}**")
                        st.rerun()

                entered_otp = st.text_input("வாடிக்கையாளர் OTP உள்ளிடவும்", max_chars=4, key="entered_otp_val")

                if st.button("✅ வருகையை நிறைவு செய்க", type="primary", use_container_width=True):
                    if not is_ready:
                        st.error("❌ கணக்கீடு அல்லது UTR எண் விடுபட்டுள்ளது!")
                    elif not otp_already_sent:
                        st.error("❌ முதலில் வாடிக்கையாளருக்கு OTP அனுப்பவும்!")
                    else:
                        expected_otp = st.session_state.get("generated_otp")
                        if entered_otp and entered_otp == expected_otp:
                            with st.spinner("வருகை சேமிக்கப்படுகிறது..."):
                                pm_label = "Cash" if bank_portion == 0 else ("Bank/UPI" if cash_portion == 0 else "Split")
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

                                st.success(f"🎉 வருகை {visit['visit_no']} வெற்றிகரமாக நிறைவுபெற்றது!")
                                st.session_state.current_visit = None
                                st.session_state.transactions_cart = []
                                st.session_state.generated_otp = None
                                st.rerun()
                        else:
                            st.error("தவறான OTP! சரியாக உள்ளிடவும்.")

                st.write("")
                if not otp_already_sent:
                    if st.button("⬅️ நடவடிக்கைகளை மாற்ற பின்செல்க", use_container_width=True):
                        st.session_state.current_visit["step"] = "TRANSACTIONS"
                        st.rerun()