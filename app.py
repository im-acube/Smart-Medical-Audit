import streamlit as st
import pandas as pd
import pdfplumber
import easyocr
import cv2
from PIL import Image
import numpy as np
import plotly.express as px
import time

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="Smart Medical Audit", page_icon="💊", layout="wide")

# ---------------------- SIDEBAR ----------------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/a/ac/Hospital_Cross.png", width=80)
st.sidebar.markdown("<h2 style='color:#2563EB;'>Smart Medical Audit</h2>", unsafe_allow_html=True)
st.sidebar.write("AI-assisted billing and compliance checker")
st.sidebar.markdown("---")
st.sidebar.info("Upload patient bills (Excel, PDF, or Image) and generate automated audit reports.")

# ---------------------- OCR READER ----------------------
reader = easyocr.Reader(['en'], gpu=False)

# ---------------------- HELPER FUNCTIONS ----------------------
def load_reference_data():
    """Load CGHS and insurer exclusion datasets."""
    try:
        cghs = pd.read_csv("cghs_rates.csv")
        excl = pd.read_csv("insurer_exclusions.csv")
        return cghs, excl
    except:
        return pd.DataFrame(), pd.DataFrame()

def read_excel_or_csv(file):
    try:
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        return df
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return pd.DataFrame()

def read_pdf(file):
    data = []
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    for line in text.split("\n"):
                        data.append({"Extracted Line": line})
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return pd.DataFrame()

def read_image(file):
    try:
        img = Image.open(file).convert('RGB')
        img_np = np.array(img)
        img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        result = reader.readtext(img_cv)
        data = []
        for (bbox, text, prob) in result:
            data.append({"Detected Text": text, "Confidence": round(prob, 2)})
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"OCR Error: {e}")
        return pd.DataFrame()

def audit_bills(df, cghs, exclusions):
    """Flag overcharges and exclusions"""
    if df.empty or cghs.empty:
        return df, [], 0

    alerts = []
    overcharge_count = 0
    df["Audit_Flag"] = ""

    for i, row in df.iterrows():
        service = str(row.get("Service", "")).strip()
        amount = float(row.get("Amount", 0))
        ref = cghs[cghs["Service"].str.lower() == service.lower()]

        if not ref.empty:
            allowed = float(ref["Rate"].values[0])
            if amount > allowed:
                df.at[i, "Audit_Flag"] = "Overcharged"
                alerts.append(f"💰 {service} billed ₹{amount} vs CGHS ₹{allowed}")
                overcharge_count += 1

        if not exclusions.empty and service.lower() in exclusions["Excluded_Service"].str.lower().values:
            df.at[i, "Audit_Flag"] = "Excluded"
            alerts.append(f"🚫 {service} is excluded by insurer")

    audit_score = max(0, 100 - (overcharge_count * 10))
    return df, alerts, audit_score

def show_summary(patient, hospital, insurer, policy, claim, audit_score, total_bill):
    """Show key metrics"""
    st.markdown("### 🏥 Patient & Insurance Summary")
    c1, c2, c3 = st.columns(3)
    c1.metric("Patient Name", patient)
    c2.metric("Hospital", hospital)
    c3.metric("Insurance Provider", insurer)

    c4, c5, c6 = st.columns(3)
    c4.metric("Policy No.", policy)
    c5.metric("Claim ID", claim)
    c6.metric("Audit Score", f"{audit_score}/100")

    st.progress(audit_score / 100)
    st.caption(f"Total Billed Amount: ₹{total_bill:,.2f}")

def show_visuals(df):
    """Show bar chart"""
    if "Service" in df.columns and "Amount" in df.columns:
        fig = px.bar(
            df, x="Service", y="Amount", color="Audit_Flag",
            color_discrete_map={"Overcharged": "#EF4444", "Excluded": "#FACC15", "": "#60A5FA"},
            title="Service-wise Billing Overview"
        )
        st.plotly_chart(fig, use_container_width=True)

# ---------------------- MAIN APP ----------------------
st.title("💊 Smart Medical Audit Dashboard")

# --- Patient Information ---
st.markdown("### 🧾 Enter Patient & Insurance Details")
col1, col2, col3 = st.columns(3)
patient_name = col1.text_input("Patient Name", "John Doe")
hospital_name = col2.text_input("Hospital Name", "CityCare Hospital")
bill_date = col3.date_input("Bill Date")

col4, col5, col6 = st.columns(3)
insurance_provider = col4.text_input("Insurance Provider", "Star Health")
policy_number = col5.text_input("Policy Number", "POL12345")
claim_number = col6.text_input("Claim ID", "CLM67890")

st.markdown("---")

# --- File Upload ---
uploaded_file = st.file_uploader(
    "📂 Upload Bill (Excel, PDF, or Image)", type=["xlsx", "csv", "pdf", "png", "jpg", "jpeg"]
)

if uploaded_file:
    with st.spinner("Processing the uploaded bill..."):
        time.sleep(1)
        ext = uploaded_file.name.split(".")[-1].lower()
        if ext in ["xlsx", "csv"]:
            df = read_excel_or_csv(uploaded_file)
        elif ext == "pdf":
            df = read_pdf(uploaded_file)
        elif ext in ["jpg", "jpeg", "png"]:
            df = read_image(uploaded_file)
        else:
            st.error("Unsupported file type.")
            df = pd.DataFrame()

    if not df.empty:
        st.success("✅ File processed successfully!")
        st.dataframe(df.head(15))

        # --- Audit Button ---
        if st.button("🚀 Run Medical Audit"):
            with st.spinner("Running AI audit..."):
                cghs, exclusions = load_reference_data()
                audited_df, alerts, audit_score = audit_bills(df, cghs, exclusions)
                total_bill = audited_df["Amount"].sum() if "Amount" in audited_df.columns else 0
                time.sleep(2)

                show_summary(patient_name, hospital_name, insurance_provider, policy_number, claim_number, audit_score, total_bill)

                st.markdown("### 🧾 Detailed Audit Report")
                st.dataframe(audited_df)

                if alerts:
                    st.warning("⚠️ Audit Alerts & Observations")
                    for alert in alerts:
                        st.write(alert)
                else:
                    st.success("✅ No irregularities detected in this bill.")

                show_visuals(audited_df)
else:
    st.info("Please upload a file to start audit.")

# ---------------------- FOOTER ----------------------
st.markdown("""
---
**Smart Medical Audit © 2025**  
Empowering transparency and accountability in medical billing.
""")
