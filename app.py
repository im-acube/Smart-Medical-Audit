import streamlit as st
import pandas as pd
import re
from PIL import Image
import pytesseract
import pdfplumber
import altair as alt
import plotly.express as px

# ------------------------------
# PAGE CONFIG
# ------------------------------
st.set_page_config(
    page_title="💊 MediAudit",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------
# CUSTOM CSS FOR COLORFUL UI
# ------------------------------
st.markdown("""
<style>
body {
    background-color: #f5f5f5;
    font-family: 'Arial', sans-serif;
}
h1, h2, h3 {
    color: #4B8BBE;
}
.stButton>button {
    background-color: #4B8BBE;
    color: white;
    border-radius: 8px;
    font-weight: bold;
}
.stMetric-value {
    font-weight: bold;
    color: #2E8B57;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------
# SIDEBAR: Patient & Policy Info
# ------------------------------
st.sidebar.image("logo.png", width=120)
st.sidebar.title("👤 Patient & Policy Info")
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
st.sidebar.info("Enter patient & policy details. These appear in audit summary.")

# ------------------------------
# HEADER
# ------------------------------
st.title("💊 MediAudit: Smart Medical Bill Auditor")
st.markdown("Automated claim validation platform for India’s health insurance ecosystem.")
st.markdown("---")

# ------------------------------
# FILE UPLOAD
# ------------------------------
st.header("Step 1: Upload Medical Bill")
uploaded_file = st.file_uploader(
    "Upload your medical bill (Excel, CSV, Image, PDF)", 
    type=["csv", "xlsx", "png", "jpg", "jpeg", "pdf"]
)

# ------------------------------
# FILE TO DATAFRAME FUNCTIONS
# ------------------------------
def image_to_dataframe(image_file):
    img = Image.open(image_file)
    text = pytesseract.image_to_string(img)
    lines = [line for line in text.split("\n") if line.strip() != ""]
    data = []
    for line in lines:
        parts = line.split()
        if len(parts) >= 2:
            item = " ".join(parts[:-1])
            amount = parts[-1].replace("₹","").replace(",","")
            if amount.replace(".","").isdigit():
                data.append([item, float(amount)])
    return pd.DataFrame(data, columns=["Item","Amount (₹)"])

def pdf_to_dataframe(pdf_file):
    data = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            for line in text.split("\n"):
                parts = line.split()
                if len(parts) >= 2:
                    item = " ".join(parts[:-1])
                    amount = parts[-1].replace("₹","").replace(",","")
                    if amount.replace(".","").isdigit():
                        data.append([item, float(amount)])
    return pd.DataFrame(data, columns=["Item","Amount (₹)"])

# ------------------------------
# LOAD DATA
# ------------------------------
if uploaded_file:
    if uploaded_file.name.endswith((".csv", ".xlsx")):
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    elif uploaded_file.name.endswith((".png", ".jpg", ".jpeg")):
        df = image_to_dataframe(uploaded_file)
    elif uploaded_file.name.endswith(".pdf"):
        df = pdf_to_dataframe(uploaded_file)
    st.success("✅ File uploaded successfully!")
    st.dataframe(df)
else:
    st.info("No file uploaded. Click below to load sample bill for demo.")
    if st.button("📄 Load Sample Bill"):
        sample_data = {
            'Item': ['Room Rent', 'Doctor Fees', 'Medicine A', 'Medicine B', 'Lab Test'],
            'Amount (₹)': [5000, 3000, 1200, 800, 2500]
        }
        df = pd.DataFrame(sample_data)
        st.dataframe(df)

st.markdown("---")
st.header("Step 2: Run Audit")

# ------------------------------
# AUDIT FUNCTION
# ------------------------------
def audit_medical_bill(dataframe, claim_amt=None):
    alerts = []
    total = dataframe['Amount (₹)'].sum()

    # Room Rent Cap
    if any(dataframe['Item'].str.contains('room', flags=re.IGNORECASE)):
        rent = dataframe[dataframe['Item'].str.contains('room', flags=re.IGNORECASE)]['Amount (₹)'].sum()
        if rent > 4000:
            alerts.append(("Room Rent", f"Exceeds daily limit (₹4000): Claimed ₹{rent}"))

    # Doctor Fees Cap
    if any(dataframe['Item'].str.contains('doctor', flags=re.IGNORECASE)):
        doc_fee = dataframe[dataframe['Item'].str.contains('doctor', flags=re.IGNORECASE)]['Amount (₹)'].sum()
        if doc_fee > 2500:
            alerts.append(("Doctor Fees", f"Exceeds coverage cap (₹2500): Claimed ₹{doc_fee}"))

    # Medicine proportion
    med_sum = dataframe[dataframe['Item'].str.contains('medicine', flags=re.IGNORECASE)]['Amount (₹)'].sum()
    if med_sum / total > 0.4:
        alerts.append(("Medicine Costs", f"Unusually high: {round((med_sum / total)*100,2)}% of total"))

    # Claim verification
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

        # --------------------------
        # METRICS CARDS
        # --------------------------
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Bill Amount (₹)", f"{total:,}")
        col2.metric("Claimed Amount (₹)", f"{claim_amount:,}")
        col3.metric("Alerts Found", len(alerts))

        # --------------------------
        # BILL COMPOSITION CHARTS
        # --------------------------
        st.subheader("Bill Composition")

        # Altair Bar Chart
        chart = alt.Chart(df).mark_bar().encode(
            x='Item',
            y='Amount (₹)',
            color=alt.Color('Item', scale=alt.Scale(scheme='tableau10')),
            tooltip=['Item','Amount (₹)']
        )
        st.altair_chart(chart, use_container_width=True)

        # Optional Plotly Pie Chart
        fig = px.pie(df, names='Item', values='Amount (₹)', 
                     color_discrete_sequence=px.colors.qualitative.Set2,
                     title='Cost Distribution')
        st.plotly_chart(fig, use_container_width=True)

        # --------------------------
        # ALERTS
        # --------------------------
        st.subheader("Audit Findings")
        if alerts:
            for title, msg in alerts:
                with st.expander(f"⚠️ {title}"):
                    if "exceeds" in msg.lower():
                        st.error(msg)
                    elif "high" in msg.lower():
                        st.warning(msg)
                    else:
                        st.info(msg)
        else:
            st.success("✅ No anomalies detected! Bill within norms.")

st.markdown("---")
st.caption("Prototype for Medical Bill Auditing – by Aqib Ahmed.")
