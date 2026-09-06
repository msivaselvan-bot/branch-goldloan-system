import streamlit as st
import pandas as pd
from datetime import datetime
import io
from supabase import create_client, Client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# பக்க வடிவமைப்பு
st.set_page_config(page_title="Branch Operations System", layout="wide")

# ==========================================
# கிளவுட் சேவைகள் இணைப்பு (Supabase & Drive)
# ==========================================

# 1. Supabase இணைப்பு
@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

# 2. Google Drive API இணைப்பு
@st.cache_resource
def get_drive_service():
    info = dict(st.secrets["gcp_service_account"])
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)

# 3. ஆவணங்களை கூகுள் டிரைவில் அப்லோட் செய்யும் செயல்பாடு
def upload_files_to_drive(files, visit_no):
    drive_service = get_drive_service()
    parent_folder_id = st.secrets["drive"]["parent_folder_id"]

    # வருகை எண்ணுக்கு (Visit No) தனி சப்-ஃபோல்டர் உருவாக்குதல்
    folder_metadata = {
        "name": visit_no,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_folder_id],
    }
    created_folder = drive_service.files().create(body=folder_metadata, fields="id").execute()
    sub_folder_id = created_folder.get("id")

    uploaded_links = []
    for f in files:
        file_metadata = {"name": f.name, "parents": [sub_folder_id]}
        media = MediaIoBaseUpload(io.BytesIO(f.getvalue()), mimetype=f.type, resumable=True)
        uploaded = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, webViewLink"
        ).execute()
        uploaded_links.append({"name": f.name, "link": uploaded.get("webViewLink")})

    return uploaded_links

try:
    supabase = get_supabase_client()
except Exception as e:
    st.error(f"டேட்டாபேஸ் இணைப்பு பிழை: {e}")
    st.stop()

# ==========================================
# தற்காலிக சேமிப்பக மாறிகள் (Session State)
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.branch = None
    st.session_state.username = None

if "current_visit" not in st.session_state:
    st.session_state.current_visit = None

if "transactions_cart" not in st.session_state:
    st.session_state.transactions_cart = []

BRANCHES = [f"கிளை {i} - Branch {i}" for i in range(1, 11)]
STAFF_LIST = ["Walk-in (நேரடி வருகை)", "ரமேஷ் (Staff 1)", "சுரேஷ் (Staff 2)", "கவிதா (Staff 3)", "பிரியா (Staff 4)"]

# ==========================================
# 1. உள்நுழைவு திரை (LOGIN SCREEN)
# ==========================================
if not st.session_state.logged_in:
    st.title("🏦 கிளை செயல்பாட்டு மேலாண்மை சிஸ்டம்")
    st.subheader("பணியாளர் உள்நுழைவு (User Login)")

    with st.form("login_form"):
        col1, col2 = st.columns(2)
        with col1:
            branch = st.selectbox("கிளையைத் தேர்ந்தெடுக்கவும் (Branch)", BRANCHES)
            username = st.text_input("பயனர் பெயர் (Username)")
        with col2:
            role = st.selectbox("பணி நிலை (Role)", ["Branch Head / Cashier", "Auditor", "Admin"])
            password = st.text_input("கடவுச்சொல் (Password)", type="password")

        submitted = st.form_submit_button("உள்நுழைக (Login)")
        if submitted:
            if username and password:
                st.session_state.logged_in = True
                st.session_state.user_role = role
                st.session_state.branch = branch
                st.session_state.username = username
                st.rerun()
            else:
                st.error("சரியான பயனர் பெயர் மற்றும் கடவுச்சொல்லை உள்ளிடவும்.")

# ==========================================
# 2. முதன்மை திரை
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
            st.rerun()

    st.markdown("---")

    # ----------------------------------------------------
    # தணிக்கையர் திரை (AUDITOR DESK)
    # ----------------------------------------------------
    if st.session_state.user_role == "Auditor":
        st.header("🔍 தணிக்கையர் பணிப்பாய்வு (Auditor Verification)")
        
        response = supabase.table("customer_visits").select("*, transactions(*), audit_records(*)").eq("status", "Submitted_to_Auditor").execute()
        pending_visits = response.data

        if not pending_visits:
            st.info("தணிக்கை செய்ய எந்த புதிய பரிவர்த்தனைகளும் வரவில்லை.")
        else:
            for item in pending_visits:
                with st.expander(f"வருகை எண்: {item['visit_no']} | நிகர ரொக்கம்: ₹{item['net_cash_amount']}"):
                    st.write(f"**பதிவு நேரம்:** {item['created_at']}")
                    
                    st.write("### 📌 வணிக நடவடிக்கைகள்:")
                    if item.get("transactions"):
                        st.dataframe(pd.DataFrame(item["transactions"]))

                    st.write("### 📁 கூகுள் டிரைவ் ஆவணங்கள்:")
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
                                "audited_at": datetime.now().isoformat()
                            }).eq("visit_id", item["id"]).execute()
                            st.success(f"{item['visit_no']} அங்கீகரிக்கப்பட்டது!")
                            st.rerun()
                    with col_a2:
                        if st.button(f"விளக்கம் கேள் (Need Clarification)", key=f"rej_{item['id']}"):
                            supabase.table("customer_visits").update({"status": "Needs_Clarification"}).eq("id", item["id"]).execute()
                            st.warning("விளக்கம் கேட்கப்பட்டது.")
                            st.rerun()

    # ----------------------------------------------------
    # கிளை செயல்பாடுகள் திரை (BRANCH FLOW)
    # ----------------------------------------------------
    else:
        st.header("📋 வாடிக்கையாளர் வருகை மற்றும் பரிவர்த்தனைகள்")

        # படி 1: வருகைப் பதிவு
        if st.session_state.current_visit is None:
            st.subheader("படி 1: புதிய வருகைப் பதிவு (Generate Visit Token)")
            with st.form("visit_form"):
                v_col1, v_col2, v_col3 = st.columns(3)
                with v_col1:
                    cust_name = st.text_input("வாடிக்கையாளர் பெயர் (Customer Name)")
                with v_col2:
                    cust_mobile = st.text_input("மொபைல் எண் (Mobile No)")
                with v_col3:
                    cust_aadhaar = st.text_input("ஆதார் எண் (Aadhaar No)")

                start_visit = st.form_submit_button("வருகையைத் தொடங்கு (Start Visit)")
                if start_visit:
                    if cust_name and cust_mobile:
                        # கஸ்டமரை Supabase-ல் பதிவு செய்தல் அல்லது தேடுதல்
                        cust_res = supabase.table("customers").insert({
                            "name": cust_name,
                            "mobile": cust_mobile,
                            "aadhaar": cust_aadhaar
                        }).execute()
                        cust_id = cust_res.data[0]["id"]

                        v_num = f"VISIT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                        st.session_state.current_visit = {
                            "visit_no": v_num,
                            "customer_id": cust_id,
                            "customer_name": cust_name,
                            "mobile": cust_mobile,
                            "aadhaar": cust_aadhaar,
                            "step": "TRANSACTIONS"
                        }
                        st.rerun()
                    else:
                        st.error("பெயர் மற்றும் மொபைல் எண் அவசியம்.")

        # படி 2: நடவடிக்கைகள் சேர்த்தல் (Cart)
        elif st.session_state.current_visit["step"] == "TRANSACTIONS":
            visit = st.session_state.current_visit
            st.success(f"வாடிக்கையாளர்: **{visit['customer_name']}** (வருகை எண்: {visit['visit_no']})")

            st.subheader("படி 2: வணிக நடவடிக்கைகள் சேர்த்தல்")
            with st.form("add_txn_form"):
                t_col1, t_col2, t_col3, t_col4 = st.columns(4)
                with t_col1:
                    txn_type = st.selectbox("நடவடிக்கை வகை", [
                        "Pledge (நகைக் கடன்)", "GL Release (அடமானம் மீட்டல்)",
                        "Part Payment (அசல் வரவு)", "Interest Payment (வட்டி)",
                        "RD Open", "RD Due", "RD Closure",
                        "FD Open", "FD Interest", "FD Closure",
                        "GS (நகை விற்பனை)", "GP (நகை வாங்குதல்)", "Take Over"
                    ])
                with t_col2:
                    staff = st.selectbox("கையாண்ட பணியாளர் (Staff Attribution)", STAFF_LIST)
                with t_col3:
                    amount_paid = st.number_input("செலுத்தியது (Paid Amount ₹)", min_value=0.0, step=100.0)
                with t_col4:
                    amount_received = st.number_input("பெற்றது (Received Amount ₹)", min_value=0.0, step=100.0)

                remarks = st.text_input("விவரக் குறிப்பு (எடை, ஸ்கீம், லோன் எண்)")
                add_btn = st.form_submit_button("நடவடிக்கையை பட்டியலில் சேர் (Add Transaction)")

                if add_btn:
                    if amount_paid > 0 or amount_received > 0:
                        st.session_state.transactions_cart.append({
                            "transaction_type": txn_type,
                            "staff_name": staff,
                            "paid_amount": float(amount_paid),
                            "received_amount": float(amount_received),
                            "remarks": remarks
                        })
                        st.success("நடவடிக்கை சேர்க்கப்பட்டது!")
                        st.rerun()
                    else:
                        st.error("தொகையை உள்ளிடவும்.")

            # நடப்பு நடவடிக்கைகள் கார்ட்
            if st.session_state.transactions_cart:
                st.write("### நடப்பு வருகையின் நடவடிக்கைகள்:")
                df_cart = pd.DataFrame(st.session_state.transactions_cart)
                st.dataframe(df_cart, use_container_width=True)

                total_paid = df_cart["paid_amount"].sum()
                total_received = df_cart["received_amount"].sum()
                net_amount = total_paid - total_received

                c1, c2, c3 = st.columns(3)
                c1.metric("மொத்த பட்டுவாடா", f"₹{total_paid:,.2f}")
                c2.metric("மொத்த வரவு", f"₹{total_received:,.2f}")
                c3.metric("நிகர ரொக்கம்", f"₹{abs(net_amount):,.2f}")

                if st.button("பணக் கணக்கீடு மற்றும் OTP பிரிவிற்குச் செல் ➔"):
                    st.session_state.current_visit["net_amount"] = net_amount
                    st.session_state.current_visit["total_paid"] = total_paid
                    st.session_state.current_visit["total_received"] = total_received
                    st.session_state.current_visit["step"] = "CASH_OTP"
                    st.rerun()

        # படி 3: Denomination & OTP
        elif st.session_state.current_visit["step"] == "CASH_OTP":
            visit = st.session_state.current_visit
            st.subheader("படி 3: ரூபாய் நோட்டு கணக்கீடு & OTP சரிபார்ப்பு")
            st.info(f"நிகர தொகை: **₹{abs(visit['net_amount']):,.2f}** " + ("(வாடிக்கையாளருக்கு செலுத்த வேண்டியது)" if visit['net_amount'] > 0 else "(வாடிக்கையாளரிடம் பெற வேண்டியது)"))

            col_den1, col_den2 = st.columns(2)
            with col_den1:
                st.write("**நோட்டு விவரங்கள் (Denomination Count)**")
                n500 = st.number_input("₹500 நோட்டுகள்", min_value=0, step=1)
                n200 = st.number_input("₹200 நோட்டுகள்", min_value=0, step=1)
                n100 = st.number_input("₹100 நோட்டுகள்", min_value=0, step=1)
                n50 = st.number_input("₹50 நோட்டுகள்", min_value=0, step=1)
                tally_total = (n500 * 500) + (n200 * 200) + (n100 * 100) + (n50 * 50)
                st.write(f"**எண்ணப்பட்ட தொகை:** ₹{tally_total:,.2f}")

            with col_den2:
                st.write("**OTP சரிபார்ப்பு**")
                st.write(f"வாடிக்கையாளர் மொபைல் எண்: **{visit['mobile']}**")
                if st.button("OTP அனுப்புக (Send OTP)"):
                    st.session_state.generated_otp = "1234"
                    st.success("OTP அனுப்பப்பட்டது! (டெமோ குறியீடு: 1234)")

                entered_otp = st.text_input("OTP உள்ளிடவும்")
                if st.button("OTP சரிபார் (Verify OTP)"):
                    if entered_otp == "1234":
                        if tally_total == abs(visit['net_amount']):
                            visit['denomination'] = {"500": n500, "200": n200, "100": n100, "50": n50}
                            st.session_state.current_visit["step"] = "DOC_UPLOAD"
                            st.success("டேலி மற்றும் OTP வெற்றிகரமாகச் சரிபார்க்கப்பட்டது!")
                            st.rerun()
                        else:
                            st.error(f"நோட்டு கூட்டுத்தொகை (₹{tally_total}) நிகர தொகையுடன் (₹{abs(visit['net_amount'])}) ஒத்துப்போகவில்லை!")
                    else:
                        st.error("தவறான OTP!")

        # படி 4: Google Drive-ல் ஆவணங்கள் பதிவேற்றம் & Supabase-ல் பதிவு செய்தல்
        elif st.session_state.current_visit["step"] == "DOC_UPLOAD":
            visit = st.session_state.current_visit
            st.subheader("படி 4: ஆவணங்கள் பதிவேற்றம் & தணிக்கைக்கு சமர்ப்பித்தல்")

            uploaded_files = st.file_uploader("ஆவணங்களைத் தேர்ந்தெடுக்கவும் (Pledge Form / Photo / KYC)", accept_multiple_files=True)

            if st.button("பரிவர்த்தனையை நிறைவு செய்து தணிக்கையருக்கு அனுப்புக"):
                if uploaded_files:
                    with st.spinner("கூகுள் டிரைவில் ஆவணங்கள் பதிவேற்றப்பட்டு வருகின்றன..."):
                        try:
                            # 1. Google Drive-ல் கோப்புகளை அப்லோட் செய்து லிங்க்குகளைப் பெறுதல்
                            drive_results = upload_files_to_drive(uploaded_files, visit["visit_no"])
                            doc_links = [item["link"] for item in drive_results]

                            # 2. Supabase-ல் Customer Visit பதிவு
                            visit_data = {
                                "visit_no": visit["visit_no"],
                                "customer_id": visit["customer_id"],
                                "total_paid": visit["total_paid"],
                                "total_received": visit["total_received"],
                                "net_cash_amount": visit["net_amount"],
                                "denomination_details": visit.get("denomination", {}),
                                "otp_verified": True,
                                "status": "Submitted_to_Auditor"
                            }
                            visit_res = supabase.table("customer_visits").insert(visit_data).execute()
                            created_visit_id = visit_res.data[0]["id"]

                            # 3. வணிக நடவடிக்கைகளை (Transactions) பதிவு செய்தல்
                            for txn in st.session_state.transactions_cart:
                                txn["visit_id"] = created_visit_id
                                supabase.table("transactions").insert(txn).execute()

                            # 4. தணிக்கையர் பதிவில் டிரைவ் லிங்க்குகளைச் சேர்த்தல்
                            supabase.table("audit_records").insert({
                                "visit_id": created_visit_id,
                                "document_urls": doc_links,
                                "audit_status": "Pending"
                            }).execute()

                            st.success("✅ ஆவணங்கள் கூகுள் டிரைவில் அப்லோட் செய்யப்பட்டு, தணிக்கையருக்கு (Auditor) வெற்றிகரமாக அனுப்பப்பட்டது!")
                            
                            # படிவத்தை ரீசெட் செய்தல்
                            st.session_state.current_visit = None
                            st.session_state.transactions_cart = []
                            st.button("அடுத்த வாடிக்கையாளர் வருகையைத் தொடங்கு")
                        except Exception as err:
                            st.error(f"பிழை ஏற்பட்டது: {err}")
                else:
                    st.error("குறைந்தது ஒரு ஆவணமாவது இணைக்கப்பட வேண்டும்.")
