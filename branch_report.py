import streamlit as st
import pandas as pd
from datetime import datetime

def show_branch_daily_transaction_report(supabase_client):
    """அட்மின் மட்டும் பார்க்கக்கூடிய கிளை தினசரி பரிவர்த்தனை ரிப்போர்ட் ஃபங்ஷன்"""
    st.subheader("📊 கிளை வாரியான தினசரி பரிவர்த்தனை ரிப்போர்ட் (Admin Report)")
    
    col1, col2 = st.columns(2)
    with col1:
        selected_branch_id = st.selectbox("கிளையைத் தேர்ந்தெடுக்கவும் (Select Branch)", options=[11, 12, 13], format_func=lambda x: f"Branch ID: {x}")
    with col2:
        report_date = st.date_input("தேதியைத் தேர்ந்தெடுக்கவும் (Select Date)", value=datetime.today())

    if st.button("🔍 ரிப்போர்ட் காட்டு (Generate Report)", type="primary"):
        try:
            formatted_date = report_date.strftime("%Y-%m-%d")
            
            # Supabase-ல் இருந்து தரவுகளை எடுத்தல்
            res = (
                supabase_client.table("transactions") # உங்கள் டேட்டாபேஸ் அட்டவணைப் பெயர்
                .select("*")
                .eq("branch_id", int(selected_branch_id))
                .gte("created_at", f"{formatted_date}T00:00:00")
                .lte("created_at", f"{formatted_date}T23:59:59")
                .execute()
            )
            
            if not res.data:
                st.warning(f"⚠️ {formatted_date} அன்று இந்த கிளையில் எந்தப் பரிவர்த்தனையும் நடைபெறவில்லை.")
                return

            df = pd.DataFrame(res.data)
            st.success(f"🎉 மொத்தம் {len(df)} பரிவர்த்தனைகள் கண்டறியப்பட்டன!")
            
            display_columns = {
                "id": "Trans ID",
                "transaction_type": "பரிவர்த்தனை வகை",
                "customer_name": "வாடிக்கையாளர் பெயர்",
                "amount": "தொகை (₹)",
                "paid_amount": "கொடுத்தது / வாங்கியது",
                "payment_mode": "பணம் செலுத்திய முறை",
                "upi_ref_number": "UPI / Bank Ref No",
                "denomination_details": "நோட்டுகள் விவரம்",
                "staff_name": "செய்த பணியாளர்"
            }
            
            available_cols = [col for col in display_columns.keys() if col in df.columns]
            report_df = df[available_cols].rename(columns=display_columns)
            
            st.dataframe(report_df, use_container_width=True)
            
            if "தொகை (₹)" in report_df.columns:
                total_sum = report_df["தொகை (₹)"].sum()
                st.metric(label="💰 அந்த நாளின் மொத்தப் பரிவர்த்தனைத் தொகை", value=f"₹ {total_sum:,.2f}")
                
            csv = report_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 இந்த ரிப்போர்ட்டை பதிவிறக்கு (Download CSV)",
                data=csv,
                file_name=f"branch_{selected_branch_id}_report_{formatted_date}.csv",
                mime="text/csv",
            )

        except Exception as e:
            st.error(f"ரிப்போர்ட் உருவாக்குவதில் பிழை: {e}")