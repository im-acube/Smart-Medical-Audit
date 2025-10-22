import streamlit as st
import pandas as pd
import re
import altair as alt

# ------------------------------
# PAGE CONFIGURATION
# ------------------------------
st.set_page_config(
    page_title="💊 MediAudit",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------
# SIDEBAR: PATIENT & POLICY DETAILS
# ------------------------------
st.sidebar.header("👤 Patient & Policy Info")
patient_name = st.sidebar.text_input("Patient Name")
patient_age = st.sidebar.number_input("Age", min_value=0, max_value=120, value=30)
hospital_name = st.sidebar.text_input("Hospital Name")

insurance_provider = st.sidebar.selectbox(
    "Medical Insurance Provider",
    ["Select", "HDFC ERGO", "ICICI Lombard", "Star Health", "Care Health", "New India Assurance", "Other"]
)
policy_number = st.sidebar.text_input("Policy Number")
claim_amount = st.sidebar.number_input("Claimed Amount (₹)", min_value=0, step=1000)

st.sidebar.markdown("---")
st.sidebar.info("Enter patient & policy details. These will appear in the audit summary.")

# ------------------------------
# MAIN PAGE: HEADER & UPLOAD
# ------------------------------
st.title("💊 MediAudit: Smart Medical Bill Auditor")
st.markdown("Automated claim validation platform for India’s health insurance ecosystem.")
st.markdown("---")

st.header("Step 1: Upload Medical Bill")
uploaded_file = st.file_uploader("Upload CSV/Excel file", type=["csv", "xlsx"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    st.success("✅ File uploaded successfully!")
    st.dataframe(df)
else:
    st.info("No file? Use sample data below.")
    if st.button("📄 Load Sample Bill"):
        data = {
            'Item': ['Room Rent', 'Doctor Fees', 'Medicine A', 'Medicine B', 'Lab Test'],
            'Amount (₹)': [5000, 3000, 1200, 800, 2500]
        }
        df = pd.DataFrame(data)
        st.dataframe(df)

st.markdown("---")
st.header("Step 2: Run Audit")

# ------------------------------
# AUDIT FUNCTION
# ------------------------------
def audit_medical_bill(dataframe, claim_amt=None):
    alerts = []
    total = dataframe['Amount (₹)'].sum()

    # Rule 1: Room Rent Cap
    if any(dataframe['Item'].str.contains('room', flags=re.IGNORECASE)):
        rent = dataframe[dataframe['Item'].str.contains('room', flags=re.IGNORECASE)]['Amount (₹)'].sum()
        if rent > 4000:
            alerts.append(("Room Rent", f"Exceeds daily limit (₹4000): Claimed ₹{rent}"))

    # Rule 2: Doctor Fees
    if any(dataframe['Item'].str.contains('doctor', flags=re.IGNORECASE)):
        doc_fee = dataframe[dataframe['Item'].str.contains('doctor', flags=re.IGNORECASE)]['Amount (₹)'].sum()
        if doc_fee > 2500:
            alerts.append(("Doctor Fees", f"Exceeds coverage cap (₹2500): Claimed ₹{doc_fee}"))

    # Rule 3: Medicine Proportion
    med_sum = dataframe[dataframe['Item'].str.contains('medicine', flags=re.IGNORECASE)]['Amount (₹)'].sum()
    if med_sum / total > 0.4:
        alerts.append(("Medicine Costs", f"Unusually high: {round((med_sum / total)*100, 2)}% of total"))

    # Rule 4: Claim Verification
    if claim_amt and total > claim_amt:
        alerts.append(("Claim Amount", f"Total bill ₹{total} exceeds claimed amount ₹{claim_amt}"))

    return alerts, total

# ------------------------------
# RUN AUDIT
# ------------------------------
if st.button("🔍 Run Audit"):
    if 'df' not in locals():
        st.error("Please upload or load a bill first.")
    else:
        alerts, total = audit_medical_bill(df, claim_amount)

        # Metrics cards
        col1, col2, col3 = st.columns([1,1,1])
        col1.metric("Total Bill Amount (₹)", f"{total:,}")
        col2.metric("Claimed Amount (₹)", f"{claim_amount:,}")
        col3.metric("Alerts Found", len(alerts))

        # Interactive Bar Chart for item-wise amounts
        st.subheader("Bill Composition")
        chart = alt.Chart(df).mark_bar().encode(
            x='Item',
            y='Amount (₹)',
            color='Item',
            tooltip=['Item', 'Amount (₹)']
        )
        st.altair_chart(chart, use_container_width=True)

        # Expandable alert details
        st.subheader("Audit Findings")
        if alerts:
            for title, msg in alerts:
                with st.expander(f"⚠️ {title}"):
                    st.warning(msg)
        else:
            st.success("✅ No anomalies detected! Bill within norms.")

st.markdown("---")
st.caption("Prototype for Medical Bill Auditing – polished, professional layout for case competition demo.")
