import streamlit as st
import pandas as pd
import pdfplumber
import easyocr
from PIL import Image
import numpy as np
import cv2
import plotly.express as px

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Smart Medical Audit", page_icon="💊", layout="wide")

# ---------- SIDEBAR ----------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/a/ac/Hospital_Cross.png", width=100)
st.sidebar.markdown("<h2 style='color:#2563EB;'>Smart Medical Audit</h2>", unsafe_allow_html=True)
st.sidebar.markdown("""
Analyze, verify, and visualize medical bills.  
Supports Excel, PDFs, and Image uploads.
""")
st.sidebar.markdown("---")
st.sidebar.markdown("**Powered by Streamlit • OCR + Audit Engine**")

# ---------- OCR SETUP ----------
reader = easyocr.Reader(['en'], gpu=False)

# ---------- HELPER FUNCTIONS ----------

def load_reference_data():
    """Load CGHS and insurance reference data."""
    try:
        cghs = pd.read_csv("cghs_rates.csv")
        excl = pd.read_csv("insurer_exclusions.csv")
        return cghs, excl
    except:
        st.warning("⚠️ Reference files missing — skipping audit comparison.")
        return pd.DataFrame(), pd.DataFrame()


def read_excel_or_csv(file):
    """Handle Excel/CSV upload."""
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
    """Extract text lines from a PDF."""
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
    """Run OCR on an uploaded image."""
    try:
        img = Image.open(file).convert('RGB')
        img_array = np.array(img)
        img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        result = reader.readtext(img_cv)
        data = []
        for (bbox, text, prob) in result:
            data.append({"Detected Text": text, "Confidence": round(prob, 2)})
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"OCR Error: {e}")
        return pd.DataFrame()


def audit_bills(df, cghs, exclusions):
    """Detect overcharges and exclusions."""
    if df.empty or cghs.empty:
        return df, []

    alerts = []
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
        if not exclusions.empty and service.lower() in exclusions["Excluded_Service"].str.lower().values:
            df.at[i, "Audit_Flag"] = "Excluded"
            alerts.append(f"🚫 {service} is excluded by insurer")
    return df, alerts


def show_charts(df):
    """Visual analytics dashboard."""
    if "Amount" in df.columns:
        st.subheader("📊 Billing Summary")
        fig = px.bar(df, x="Service", y="Amount", color="Audit_Flag",
                     color_discrete_map={"Overcharged": "#F87171", "Excluded": "#FBBF24", "": "#60A5FA"})
        st.plotly_chart(fig, use_container_width=True)

# ---------- MAIN ----------
st.title("💊 Smart Medical Bill Auditor")
uploaded_file = st.file_uploader("Upload your bill (Excel, PDF, or Image)", type=["xlsx", "csv", "pdf", "png", "jpg", "jpeg"])

if uploaded_file:
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
        st.success("✅ File successfully processed!")
        st.dataframe(df.head(20))

        cghs, exclusions = load_reference_data()

        if "Service" in df.columns and "Amount" in df.columns:
            audited_df, alerts = audit_bills(df, cghs, exclusions)
            st.subheader("🔍 Audit Results")
            st.dataframe(audited_df)

            if alerts:
                st.warning("⚠️ Audit Alerts:")
                for a in alerts:
                    st.write(a)

            show_charts(audited_df)
        else:
            st.info("📋 Detected text will need manual structuring for audit (OCR mode).")
else:
    st.info("Please upload your medical bill to start auditing.")

# ---------- FOOTER ----------
st.markdown("""
---
🌐 **Smart Medical Audit © 2025**  
Transparency. Accuracy. Trust.
""")
