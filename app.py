from datetime import datetime
import random
import requests
import pandas as pd
import streamlit as st
from supabase import Client, create_client

# பக்க வடிவமைப்பு
st.set_page_config(page_title="Branch Operations System", layout="wide")

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
# 2. ஆவணப் பதிவேற்றம் & வருகை எண் உருவாக்கும் செயல்பாடுகள்
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
# 4. உள்நுழைவு திரை (சிறிய வடிவமைப்பு - Compact Center)
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
    # A. நிர்வாக மேலாண்மை திரை (ADMIN PANEL)
    # ----------------------------------------------------
    if st.session_state.user_role == "Admin":
        st.header("⚙️ நிர்வாக மேலாண்மை (Admin Control Panel)")
        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "🏢 புதிய கிளை சேர்த்தல் / மேலாண்மை",
                "👥 பணியாளர்கள் மேலாண்மை",
                "📥 வாடிக்கையாளர் மொத்தப் பதிவேற்றம் (Bulk Import)",
                "🗂️ வாடிக்கையாளர் பட்டியல் & மேலாண்மை (Customer Directory)",
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

            st.markdown("---")
            st.subheader("📋 ஏற்கனவே உள்ள கிளைகள் பட்டியல்")
            b_list_res = supabase.table("branches").select("id, branch_name, branch_code").order("id").execute()
            if b_list_res.data:
                st.dataframe(pd.DataFrame(b_list_res.data), use_container_width=True)

        with tab2:
            st.subheader("📋 பணியாளர்கள் பட்டியல் (Existing Users)")
            users_res = supabase.table("users").select("id, name, username, role, branch_id, is_active").order("id").execute()

            if users_res.data:
                user_table_data = []
                for u in users_res.data:
                    b_name = branch_id_to_name.get(u.get("branch_id"), "Head Office / None")
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
                        ["Branch Head / Cashier", "Staff", "Auditor", "Admin"],
                        key="admin_new_role",
                    )
                    b_selection = st.selectbox(
                        "கிளையைத் தேர்ந்தெடுக்கவும்",
                        options=list(branch_options.keys()) if branch_options else ["கிளைகள் இல்லை"],
                        key="admin_new_branch",
                    )

                    if st.form_submit_button("பயனாளரை உருவாக்கு (Create User)"):
                        if u_name.strip() and u_username.strip() and u_pass.strip():
                            b_id = branch_options.get(b_selection) if u_role not in ["Admin", "Auditor"] else None
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
                        roles_list = ["Branch Head / Cashier", "Staff", "Auditor", "Admin"]
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
                                    "branch_id": branch_options.get(edit_branch) if edit_role not in ["Admin", "Auditor"] else None,
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
            st.write("உங்கள் `Customer Report.xls` கோப்பை இங்கே பதிவேற்றினால், அதில் உள்ள கிளைக் குறியீடுகளுக்கு ஏற்ப வாடிக்கையாளர்கள் தானாகவே பிரிக்கப்பட்டு இணைக்கப்படுவர்.")

            uploaded_cust_file = st.file_uploader(
                "Customer Report Excel கோப்பைத் தேர்வு செய்யவும்",
                type=["xls", "xlsx", "csv"],
                key="admin_customer_report_uploader",
            )

            if uploaded_cust_file:
                try:
                    if uploaded_cust_file.name.endswith(".csv"):
                        df_raw = pd.read_csv(uploaded_cust_file, skiprows=2)
                    else:
                        df_raw = pd.read_excel(uploaded_cust_file, skiprows=2)

                    df_cust = df_raw.dropna(subset=["Full Name", "Mobile No"]).copy()
                    st.success(f"📊 மொத்த வாடிக்கையாளர்கள் கண்டறியப்பட்டனர்: **{len(df_cust)}**")

                    branch_counts = df_cust["Branch"].value_counts().to_dict()
                    st.write("**கிளை வாரியான விவரங்கள்:**")
                    st.json(branch_counts)

                    st.dataframe(df_cust.head(3), use_container_width=True)

                    if st.button("🚀 அனைத்து வாடிக்கையாளர்களையும் டேட்டாபேஸில் உடனே இணை (Start Bulk Upload)", type="primary", key="admin_start_bulk_upload_btn"):
                        with st.spinner("வாடிக்கையாளர் தரவுகள் டேட்டாபேஸில் பதிவேற்றப்படுகின்றன..."):
                            all_b = supabase.table("branches").select("id, branch_code").execute()
                            b_code_to_id = {b["branch_code"].strip().upper(): b["id"] for b in all_b.data} if all_b.data else {}

                            records_to_insert = []
                            seen_codes = set()

                            for idx, row in df_cust.iterrows():
                                b_code = str(row.get("Branch", "")).strip().upper()
                                target_branch_id = b_code_to_id.get(b_code)

                                raw_c_no = str(row.get("Customer No", "")).replace(".0", "").strip()
                                if not raw_c_no or raw_c_no == "0" or raw_c_no == "nan":
                                    c_code = f"{b_code}-0-{idx+1}"
                                else:
                                    c_code = f"{b_code}-{raw_c_no}"

                                if c_code in seen_codes:
                                    c_code = f"{c_code}-{idx+1}"
                                seen_codes.add(c_code)

                                mob1 = str(row.get("Mobile No", "")).replace(".0", "").strip()
                                mob2 = str(row.get("Secondary No", "")).replace(".0", "").strip() if pd.notna(row.get("Secondary No")) else ""
                                if not mob2 and pd.notna(row.get("Whatsapp No")):
                                    mob2 = str(row.get("Whatsapp No", "")).replace(".0", "").strip()

                                records_to_insert.append({
                                    "branch_id": target_branch_id,
                                    "customer_code": c_code,
                                    "name": str(row.get("Full Name", "")).strip(),
                                    "guardian_name": str(row.get("Guardian", "")).strip() if pd.notna(row.get("Guardian")) else "",
                                    "gender": str(row.get("Gender", "")).strip() if pd.notna(row.get("Gender")) else "Male",
                                    "mobile": mob1,
                                    "mobile2": mob2,
                                    "address": str(row.get("Comm Address", "")).strip() if pd.notna(row.get("Comm Address")) else "",
                                    "nominee_relation": str(row.get("Relation", "")).strip() if pd.notna(row.get("Relation")) else "",
                                    "is_active": True,
                                })

                            batch_size = 100
                            for i in range(0, len(records_to_insert), batch_size):
                                batch = records_to_insert[i : i + batch_size]
                                supabase.table("customers").upsert(batch, on_conflict="customer_code").execute()

                            st.success(f"✅ **{len(records_to_insert)} வாடிக்கையாளர்கள்** வெற்றிகரமாக டேட்டாபேஸில் இணைக்கப்பட்டுவிட்டனர்!")
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
                admin_search_q = st.text_input("வாடிக்கையாளர் பெயர் / மொபைல் / Customer Code தேடுக:", placeholder="எ.கா: MYL-1 அல்லது ரமேஷ்", key="admin_cust_search")

            cust_query = supabase.table("customers").select("id, customer_code, name, mobile, mobile2, guardian_name, gender, address, nominee_relation, branch_id, is_active").order("id", desc=True)

            if selected_b_filter != "அனைத்து கிளைகளும் (All Branches)":
                b_filter_id = branch_options.get(selected_b_filter)
                cust_query = cust_query.eq("branch_id", b_filter_id)

            if admin_search_q.strip():
                sq = admin_search_q.strip()
                cust_query = cust_query.or_(f"name.ilike.%{sq}%,mobile.ilike.%{sq}%,customer_code.ilike.%{sq}%")
            else:
                cust_query = cust_query.limit(200)

            res_view_custs = cust_query.execute()
            data_view = res_view_custs.data if res_view_custs.data else []

            st.write(f"📊 கண்டறியப்பட்ட வாடிக்கையாளர்கள்: **{len(data_view)}** (அதிகபட்சம் 200 பதிவுகள் ஒரே திரையில் காட்டப்படும்)")

            if data_view:
                table_list = []
                for cv in data_view:
                    table_list.append({
                        "ID": cv["id"],
                        "Customer Code": cv.get("customer_code", "-"),
                        "பெயர்": cv["name"],
                        "மொபைல்": cv.get("mobile", "-"),
                        "கார்டியன் பெயர்": cv.get("guardian_name", "-"),
                        "கிளை": branch_id_to_name.get(cv.get("branch_id"), "பொது"),
                        "நிலை": "🟢 Active" if cv.get("is_active", True) else "🔴 Inactive",
                        "முகவரி": cv.get("address", "-"),
                    })
                st.dataframe(pd.DataFrame(table_list), use_container_width=True)

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

    # ----------------------------------------------------
    # B. தணிக்கையர் திரை (AUDITOR DESK)
    # ----------------------------------------------------
    elif st.session_state.user_role == "Auditor":
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
    # C. கிளை செயல்பாடுகள் திரை (BRANCH FLOW)
    # ----------------------------------------------------
    else:
        st.header("📋 வாடிக்கையாளர் வருகை மற்றும் பரிவர்த்தனைகள்")

        staff_res = supabase.table("users").select("name").eq("branch_id", st.session_state.branch_id).eq("is_active", True).execute()
        current_staff_list = ["Walk-in (நேரடி வருகை)"] + [s["name"] for s in staff_res.data] if staff_res.data else ["Walk-in (நேரடி வருகை)"]

        # படி 1: வருகைப் பதிவு
        if st.session_state.current_visit is None:
            st.subheader("படி 1: வாடிக்கையாளர் வருகைப் பதிவு (Visit Token)")

            visit_type = st.radio(
                "வாடிக்கையாளர் வகை:",
                ["ஏற்கனவே உள்ள வாடிக்கையாளர் (Existing Customer)", "புதிய வாடிக்கையாளர் பதிவு (New Customer)"],
                horizontal=True,
            )

            # 1. பழைய வாடிக்கையாளர் தேடல்
            if "Existing" in visit_type:
                st.markdown("##### 🔍 வாடிக்கையாளர் தேடல்")
                search_query = st.text_input(
                    "பெயர் / மொபைல் எண் / Customer ID உள்ளிடவும்:", 
                    placeholder="எ.கா: ராம் அல்லது 98765...",
                    key="live_cust_search_input"
                )

                if len(search_query.strip()) >= 2:
                    q = search_query.strip()
                    
                    cust_filter_query = (
                        supabase.table("customers")
                        .select("*")
                        .eq("is_active", True)
                    )
                    
                    if st.session_state.user_role not in ["Admin", "Auditor"]:
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
                        
                        st.markdown("###### 🎯 பொருந்தும் வாடிக்கையாளர் பட்டியல் (டிராப்டவுனில் தேர்ந்தெடுக்கவும்):")
                        selected_label = st.selectbox(
                            "பொருந்தும் வாடிக்கையாளர் பட்டியல்",
                            options=list(cust_dropdown_dict.keys()),
                            label_visibility="collapsed",
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
                                st.write(f"🤝 **உறவுமுறை:** {selected_cust.get('nominee_relation', '-')}")

                            with c_col3:
                                st.write("")
                                st.write("")
                                if st.button("வருகையைத் தொடங்கு ➔", key=f"start_visit_{selected_cust['id']}", type="primary", use_container_width=True):
                                    v_num = generate_short_visit_no()
                                    st.session_state.current_visit = {
                                        "visit_no": v_num,
                                        "customer_id": selected_cust["id"],
                                        "customer_name": selected_cust["name"],
                                        "customer_code": selected_cust.get("customer_code", ""),
                                        "mobile": selected_cust.get("mobile", ""),
                                        "step": "TRANSACTIONS",
                                    }
                                    st.rerun()
                    else:
                        st.warning("உங்கள் கிளையில் பொருந்தும் வாடிக்கையாளர் விவரங்கள் எதுவும் இல்லை. புதிய வாடிக்கையாளராகப் பதிவு செய்யவும்.")

            # 2. புதிய வாடிக்கையாளர் பதிவு
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
                        new_aadhaar = st.text_input("ஆதார் எண்")
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
                                    "aadhaar": new_aadhaar.strip(),
                                    "address": new_address.strip(),
                                    "nominee_name": new_nominee.strip(),
                                    "nominee_relation": new_relation.strip(),
                                    "photo_url": photo_url,
                                    "is_active": True,
                                }
                                cust_insert_res = supabase.table("customers").insert(insert_data).execute()

                                if cust_insert_res.data:
                                    created_cust = cust_insert_res.data[0]
                                    v_num = generate_short_visit_no()
                                    st.session_state.current_visit = {
                                        "visit_no": v_num,
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

        # படி 2: வணிக நடவடிக்கைகள் (Cart)
        elif st.session_state.current_visit["step"] == "TRANSACTIONS":
            visit = st.session_state.current_visit
            st.success(f"வாடிக்கையாளர்: **{visit['customer_name']}** (வருகை எண்: {visit['visit_no']})")

            st.subheader("படி 2: வணிக நடவடிக்கைகள் சேர்த்தல்")
            with st.form("add_txn_form"):
                t_col1, t_col2, t_col3, t_col4 = st.columns(4)
                with t_col1:
                    txn_type = st.selectbox(
                        "நடவடிக்கை வகை",
                        [
                            "Pledge (நகைக் கடன்)",
                            "GL Release (அடமானம் மீட்டல்)",
                            "Part Payment (அசல் வரவு)",
                            "Interest Payment (வட்டி)",
                            "RD Open",
                            "RD Due",
                            "RD Closure",
                            "FD Open",
                            "FD Interest",
                            "FD Closure",
                            "GS (நகை விற்பனை)",
                            "GP (நகை வாங்குதல்)",
                            "Take Over",
                        ],
                    )
                with t_col2:
                    staff = st.selectbox("கையாண்ட பணியாளர் (Staff Attribution)", current_staff_list)
                with t_col3:
                    amount_paid = st.number_input("செலுத்தியது (Paid Amount ₹)", min_value=0.0, step=100.0)
                with t_col4:
                    amount_received = st.number_input("பெற்றது (Received Amount ₹)", min_value=0.0, step=100.0)

                remarks = st.text_input("விவரக் குறிப்பு (எடை, ஸ்கீம், லோன் எண்)")
                if st.form_submit_button("நடவடிக்கையை பட்டியலில் சேர்"):
                    if amount_paid > 0 or amount_received > 0:
                        st.session_state.transactions_cart.append({
                            "transaction_type": txn_type,
                            "staff_name": staff,
                            "paid_amount": float(amount_paid),
                            "received_amount": float(amount_received),
                            "remarks": remarks,
                        })
                        st.success("நடவடிக்கை சேர்க்கப்பட்டது!")
                        st.rerun()
                    else:
                        st.error("தொகையை உள்ளிடவும்.")

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
            st.info(
                f"நிகர தொகை: **₹{abs(visit['net_amount']):,.2f}** "
                + ("(வாடிக்கையாளருக்கு செலுத்த வேண்டியது)" if visit["net_amount"] > 0 else "(வாடிக்கையாளரிடம் பெற வேண்டியது)")
            )

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
                        if tally_total == abs(visit["net_amount"]):
                            visit["denomination"] = {
                                "500": n500,
                                "200": n200,
                                "100": n100,
                                "50": n50,
                            }
                            st.session_state.current_visit["step"] = "DOC_UPLOAD"
                            st.success("டேலி மற்றும் OTP வெற்றிகரமாகச் சரிபார்க்கப்பட்டது!")
                            st.rerun()
                        else:
                            st.error(f"நோட்டு கூட்டுத்தொகை (₹{tally_total}) நிகர தொகையுடன் (₹{abs(visit['net_amount'])}) ஒத்துப்போகவில்லை!")
                    else:
                        st.error("தவறான OTP!")

        # படி 4: Supabase-ல் ஆவணங்கள் பதிவேற்றம் & தணிக்கைக்கு சமர்ப்பித்தல்
        elif st.session_state.current_visit["step"] == "DOC_UPLOAD":
            visit = st.session_state.current_visit
            st.subheader("படி 4: ஆவணங்கள் பதிவேற்றம் & தணிக்கைக்கு சமர்ப்பித்தல்")

            uploaded_files = st.file_uploader("ஆவணங்களைத் தேர்ந்தெடுக்கவும் (Pledge Form / Photo / KYC)", accept_multiple_files=True)

            if st.button("பரிவர்த்தனையை நிறைவு செய்து தணிக்கையருக்கு அனுப்புக"):
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
                            st.button("அடுத்த வாடிக்கையாளர் வருகையைத் தொடங்கு")
                        except Exception as err:
                            st.error(f"பிழை ஏற்பட்டது: {err}")
                else:
                    st.error("குறைந்தது ஒரு ஆவணமாவது இணைக்கப்பட வேண்டும்.")
