import streamlit as st
import pandas as pd
import pdfplumber
import easyocr
import cv2
from PIL import Image
import numpy as np
import plotly.express as px
import time

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Smart Medical Audit Dashboard", page_icon="💊", layout="wide")

# ---------- SIDEBAR ----------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/a/ac/Hospital_Cross.png", width=80)
st.sidebar.markdown("<h2 style='color:#2563EB;'>Smart Medical Audit</h2>", unsafe_allow_html=True)
st.sidebar.write("Audit hospital bills using AI + OCR")
st.sidebar.markdown("---")
st.sidebar.info("Upload a patient’s bill (Excel / PDF / Image) to begin auditing.")

# ---------- OCR SETUP ----------
reader = easyocr.Reader(['en'], gpu=False)

# ---------- HELPER FUNCTIONS ----------
def load_reference_data():
    """Load CGHS and insurer reference datasets."""
    try:
        cghs = pd.read_csv("cghs_rates.csv")
        excl = pd.read_csv("insurer_exclusions.csv")
        return cghs, excl
    except:
        return pd.DataFrame(), pd.DataFrame()

def read_excel_or_csv(file):
    """Read Excel or CSV bills."""
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
    """Extract text lines from PDF using pdfplumber."""
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
    """Perform OCR extraction from uploaded image."""
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
    """Flag overcharges and excluded services."""
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

def show_summary(patient_name, hospital_name, audit_score, total_bill):
    """Display top KPIs."""
    st.markdown("### 🏥 Patient & Hospital Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Patient", patient_name)
    c2.metric("Hospital", hospital_name)
    c3.metric("Total Bill (₹)", f"{total_bill:,.2f}")
    c4.metric("Audit Score", f"{audit_score} / 100")

def show_visuals(df):
    """Show visualization of billed vs. allowed services."""
    if "Service" in df.columns and "Amount" in df.columns:
        fig = px.bar(df, x="Service", y="Amount", color="Audit_Flag",
                     color_discrete_map={"Overcharged": "#F87171", "Excluded": "#FBBF24", "": "#60A5FA"},
                     title="Billing Overview by Service")
        st.plotly_chart(fig, use_container_width=True)

# ---------- MAIN DASHBOARD ----------
st.title("💊 Smart Medical Audit Dashboard")

# --- Patient & Hospital Details ---
st.markdown("### 🧾 Enter Patient & Hospital Details")
col1, col2, col3 = st.columns(3)
patient_name = col1.text_input("Patient Name", "John Doe")
hospital_name = col2.text_input("Hospital Name", "CityCare Hospital")
bill_date = col3.date_input("Bill Date")

uploaded_file = st.file_uploader("📂 Upload Medical Bill (Excel, PDF, or Image)", type=["xlsx", "csv", "pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    with st.spinner("Processing the file..."):
        time.sleep(1)
        ext = uploaded_file.name.split(".")[-1].lower()
        if ext in ["xlsx", "csv"]:
            df = read_excel_or_csv(uploaded_file)
        elif ext == "pdf":
            df = read_pdf(uploaded_file)
        elif ext in ["jpg", "jpeg", "png"]:
            df = read_image(uploaded_file)
        else:
            st.error("Unsupported file format.")
            df = pd.DataFrame()

    if not df.empty:
        st.success("✅ File processed successfully!")
        st.dataframe(df.head(20))

        cghs, exclusions = load_reference_data()

        if "Service" in df.columns and "Amount" in df.columns:
            audited_df, alerts, audit_score = audit_bills(df, cghs, exclusions)

            total_bill = audited_df["Amount"].sum()
            show_summary(patient_name, hospital_name, audit_score, total_bill)

            st.markdown("### 🔍 Detailed Audit Report")
            st.dataframe(audited_df)

            if alerts:
                st.warning("⚠️ Alerts and Observations")
                for alert in alerts:
                    st.write(alert)
            else:
                st.info("✅ No irregularities detected. Bill appears compliant.")

            show_visuals(audited_df)
        else:
            st.info("OCR extraction complete. Please structure text manually for audit.")
else:
    st.info("Please upload a bill to start the audit.")

# ---------- FOOTER ----------
st.markdown("""
---
**Smart Medical Audit © 2025**  
Empowering transparency in healthcare billing.
""")
