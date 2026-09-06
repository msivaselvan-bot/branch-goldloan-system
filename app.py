import streamlit as st
import pandas as pd
from datetime import datetime

# பக்க அமைப்பு (Wide Layout)
st.set_page_config(page_title="Branch Operations System", layout="wide")

# --- தற்காலிக டேட்டா ஸ்டோரேஜ் (Session State) ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.branch = None
    st.session_state.username = None

if "current_visit" not in st.session_state:
    st.session_state.current_visit = None

if "transactions_cart" not in st.session_state:
    st.session_state.transactions_cart = []

if "audit_queue" not in st.session_state:
    st.session_state.audit_queue = []

# கிளைகள் மற்றும் ஊழியர்கள் பட்டியல் (மாதிரி விவரங்கள்)
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
            if username and password:  # எளிய சரிபார்ப்பு
                st.session_state.logged_in = True
                st.session_state.user_role = role
                st.session_state.branch = branch
                st.session_state.username = username
                st.rerun()
            else:
                st.error("சரியான பயனர் பெயர் மற்றும் கடவுச்சொல்லை உள்ளிடவும்.")

# ==========================================
# 2. உள்நுழைந்த பின் இயங்கும் முதன்மை திரை
# ==========================================
else:
    # மேல் பகுதி தகவல் மற்றும் வெளியேறும் வசதி
    top_col1, top_col2, top_col3 = st.columns([3, 2, 1])
    with top_col1:
        st.write(f"🏢 **கிளை:** {st.session_state.branch}")
    with top_col2:
        st.write(f"👤 **பயனர்:** {st.session_state.username} ({st.session_state.user_role})")
    with top_col3:
        if st.button("வெளியேறு (Logout)"):
            st.session_state.logged_in = False
            st.rerun()

    st.markdown("---")

    # ----------------------------------------------------
    # தணிக்கையர் திரை (AUDITOR DESK)
    # ----------------------------------------------------
    if st.session_state.user_role == "Auditor":
        st.header("🔍 தணிக்கையர் பணிப்பாய்வு (Auditor Verification)")
        if not st.session_state.audit_queue:
            st.info("தணிக்கை செய்ய எந்த புதிய பரிவர்த்தனைகளும் வரவில்லை.")
        else:
            for idx, item in enumerate(st.session_state.audit_queue):
                with st.expander(f"வருகை எண்: {item['visit_no']} | வாடிக்கையாளர்: {item['customer_name']} ({item['branch']})"):
                    st.write(f"**தேதி/நேரம்:** {item['timestamp']}")
                    st.write(f"**நிகர பணப் பரிமாற்றம்:** ₹{item['net_amount']}")
                    st.write("### வணிக நடவடிக்கைகள்:")
                    st.dataframe(pd.DataFrame(item['transactions']))
                    st.write(f"**இணைக்கப்பட்ட ஆவணங்கள்:** {len(item['documents'])} ஆவணங்கள் சமர்ப்பிக்கப்பட்டுள்ளன.")
                    
                    col_a1, col_a2 = st.columns(2)
                    with col_a1:
                        if st.button(f"அங்கீகரி (Approve) - {item['visit_no']}", key=f"app_{idx}"):
                            st.success(f"{item['visit_no']} வெற்றிகரமாக அங்கீகரிக்கப்பட்டது!")
                    with col_a2:
                        if st.button(f"நிராகரி / விளக்கம் கேள் (Reject)", key=f"rej_{idx}"):
                            st.warning("விளக்கம் கேட்கப்பட்டது.")

    # ----------------------------------------------------
    # கிளை செயல்பாடுகள் திரை (CUSTOMER-CENTRIC WORKFLOW)
    # ----------------------------------------------------
    else:
        st.header("📋 வாடிக்கையாளர் வருகை மற்றும் பரிவர்த்தனைகள்")

        # படி 1: வாடிக்கையாளர் வருகை பதிவு
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
                        v_num = f"VISIT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                        st.session_state.current_visit = {
                            "visit_no": v_num,
                            "customer_name": cust_name,
                            "mobile": cust_mobile,
                            "aadhaar": cust_aadhaar,
                            "otp_verified": False,
                            "step": "TRANSACTIONS"
                        }
                        st.rerun()
                    else:
                        st.error("பெயர் மற்றும் மொபைல் எண் அவசியம்.")

        # படி 2: நடவடிக்கைகள் சேர்த்தல் (Cart)
        elif st.session_state.current_visit["step"] == "TRANSACTIONS":
            visit = st.session_state.current_visit
            st.success(f"தற்போதைய வாடிக்கையாளர்: **{visit['customer_name']}** (வருகை எண்: {visit['visit_no']})")

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
                    amount_paid = st.number_input("நிறுவனம் வாடிக்கையாளருக்கு செலுத்தியது (Paid Amount ₹)", min_value=0.0, step=100.0)
                with t_col4:
                    amount_received = st.number_input("வாடிக்கையாளரிடம் பெற்றது (Received Amount ₹)", min_value=0.0, step=100.0)

                remarks = st.text_input("விவரக் குறிப்பு (எ.கா: எடை, ஸ்கீம், லோன் எண்)")
                add_btn = st.form_submit_button("நடவடிக்கையை பட்டியலில் சேர் (Add Transaction)")

                if add_btn:
                    if amount_paid > 0 or amount_received > 0:
                        st.session_state.transactions_cart.append({
                            "நடவடிக்கை": txn_type,
                            "பணியாளர்": staff,
                            "செலுத்தியது (Paid ₹)": amount_paid,
                            "பெற்றது (Received ₹)": amount_received,
                            "குறிப்புகள்": remarks
                        })
                        st.success("நடவடிக்கை சேர்க்கப்பட்டது!")
                        st.rerun()
                    else:
                        st.error("செலுத்திய அல்லது பெற்ற தொகையை உள்ளிடவும்.")

            # நடப்பு நடவடிக்கைகள் அட்டவணை & கணக்கீடு
            if st.session_state.transactions_cart:
                st.write("### நடப்பு வருகையின் நடவடிக்கைகள் பட்டியல்:")
                df_cart = pd.DataFrame(st.session_state.transactions_cart)
                st.dataframe(df_cart, use_container_width=True)

                total_paid = df_cart["செலுத்தியது (Paid ₹)"].sum()
                total_received = df_cart["பெற்றது (Received ₹)"].sum()
                net_amount = total_paid - total_received

                c1, c2, c3 = st.columns(3)
                c1.metric("மொத்த பட்டுவாடா (Total Paid)", f"₹{total_paid:,.2f}")
                c2.metric("மொத்த வரவு (Total Received)", f"₹{total_received:,.2f}")
                if net_amount > 0:
                    c3.metric("நிகர பட்டுவாடா (Net Cash to Customer)", f"₹{net_amount:,.2f}", delta_color="normal")
                else:
                    c3.metric("நிகர வசூல் (Net Cash from Customer)", f"₹{abs(net_amount):,.2f}", delta_color="inverse")

                if st.button("பணக் கணக்கீடு மற்றும் OTP பிரிவிற்குச் செல் ➔"):
                    st.session_state.current_visit["net_amount"] = net_amount
                    st.session_state.current_visit["total_paid"] = total_paid
                    st.session_state.current_visit["total_received"] = total_received
                    st.session_state.current_visit["step"] = "CASH_OTP"
                    st.rerun()

        # படி 3: Denomination & OTP Verification
        elif st.session_state.current_visit["step"] == "CASH_OTP":
            visit = st.session_state.current_visit
            st.subheader("படி 3: பண நோட்டு விவரங்கள் (Cash Denomination) & OTP")
            st.info(f"இறுதி நிகர தொகை: **₹{abs(visit['net_amount']):,.2f}** " + ("(வாடிக்கையாளருக்கு வழங்க வேண்டும்)" if visit['net_amount'] > 0 else "(வாடிக்கையாளரிடம் பெற வேண்டும்)"))

            col_den1, col_den2 = st.columns(2)
            with col_den1:
                st.write("**நோட்டு விவரங்கள் (Denomination Count)**")
                n500 = st.number_input("₹500 நோட்டுகள்", min_value=0, step=1)
                n200 = st.number_input("₹200 நோட்டுகள்", min_value=0, step=1)
                n100 = st.number_input("₹100 நோட்டுகள்", min_value=0, step=1)
                n50 = st.number_input("₹50 நோட்டுகள்", min_value=0, step=1)
                tally_total = (n500 * 500) + (n200 * 200) + (n100 * 100) + (n50 * 50)
                st.write(f"**எண்ணப்பட்ட மொத்தத் தொகை:** ₹{tally_total:,.2f}")

            with col_den2:
                st.write("**OTP சரிபார்ப்பு (SMS OTP Verification)**")
                st.write(f"வாடிக்கையாளர் மொபைல் எண்: **{visit['mobile']}**")
                if st.button("OTP அனுப்புக (Send OTP)"):
                    st.session_state.generated_otp = "1234"  # மாதிரி OTP
                    st.success("OTP வாடிக்கையாளர் மொபைலுக்கு அனுப்பப்பட்டது! (டெமோ OTP: 1234)")

                entered_otp = st.text_input("OTP உள்ளிடவும் (4 இலக்க எண்)")
                if st.button("OTP சரிபார் (Verify OTP)"):
                    if entered_otp == "1234":
                        if tally_total == abs(visit['net_amount']):
                            visit['otp_verified'] = True
                            st.session_state.current_visit["step"] = "DOC_UPLOAD"
                            st.success("பணக் கணக்கு டேலி ஆனது மற்றும் OTP வெற்றிகரமாகச் சரிபார்க்கப்பட்டது!")
                            st.rerun()
                        else:
                            st.error(f"நோட்டு விவரங்களின் கூட்டுத்தொகை (₹{tally_total}) நிகர தொகையுடன் (₹{abs(visit['net_amount'])}) ஒத்துப்போகவில்லை!")
                    else:
                        st.error("தவறான OTP!")

        # படி 4: ஆவணங்கள் பதிவேற்றம் & தணிக்கையருக்கு அனுப்புதல்
        elif st.session_state.current_visit["step"] == "DOC_UPLOAD":
            visit = st.session_state.current_visit
            st.subheader("படி 4: ஆவணங்கள் பதிவேற்றம் (Document Upload)")
            st.write("அடமானப் படிவங்கள், நகைப் படங்கள் மற்றும் வாடிக்கையாளர் ஆவணங்களை இணைக்கவும்.")

            uploaded_files = st.file_uploader(
                "ஆவணங்களைத் தேர்ந்தெடுக்கவும் (Pledge Form / Ornament Photos / KYC)", 
                accept_multiple_files=True
            )

            if st.button("பரிவர்த்தனையை நிறைவு செய்து தணிக்கையருக்கு அனுப்புக (Submit to Auditor)"):
                if uploaded_files:
                    # தணிக்கையர் வரிசைக்கு அனுப்புதல்
                    st.session_state.audit_queue.append({
                        "visit_no": visit["visit_no"],
                        "customer_name": visit["customer_name"],
                        "branch": st.session_state.branch,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "net_amount": visit["net_amount"],
                        "transactions": st.session_state.transactions_cart,
                        "documents": [f.name for f in uploaded_files]
                    })
                    st.success("அனைத்து நடவடிக்கைகளும் சேமிக்கப்பட்டு தணிக்கையருக்கு (Auditor) அனுப்பப்பட்டது!")
                    
                    # புதிய வாடிக்கையாளருக்காக ரீசெட் செய்தல்
                    st.session_state.current_visit = None
                    st.session_state.transactions_cart = []
                    st.button("அடுத்த வாடிக்கையாளர் வருகையைத் தொடங்கு")
                else:
                    st.error("குறைந்தது ஒரு ஆவணமாவது இணைக்கப்பட வேண்டும்.")
