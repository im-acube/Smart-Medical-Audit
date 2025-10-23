import streamlit as st
import pandas as pd
import pdfplumber
import easyocr
from PIL import Image
import numpy as np
import io
import os

st.set_page_config(page_title="Smart Medical Audit", page_icon="💊", layout="wide")

st.title("💊 Smart Medical Audit Dashboard")
st.markdown("##### Automated Hospital Bill Audit using Built-in CGHS Rates and Exclusions")

# ------------------ Load Reference Files ------------------
@st.cache_data
def load_reference_data():
    try:
        cghs = pd.read_excel("cghs_rates.xlsx")
        exclusions = pd.read_excel("insurer_exclusions.xlsx")
        st.success("✅ Loaded CGHS and Exclusion Data from repository.")
        return cghs, exclusions
    except Exception as e:
        st.error(f"❌ Error loading reference data: {e}")
        return pd.DataFrame(), pd.DataFrame()

cghs_df, exclusions_df = load_reference_data()

# ------------------ Helper Functions ------------------
def extract_text_from_pdf(pdf_bytes):
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def extract_text_from_image(image_bytes):
    reader = easyocr.Reader(["en"])
    img = Image.open(io.BytesIO(image_bytes))
    result = reader.readtext(np.array(img))
    text = " ".join([r[1] for r in result])
    return text

def audit_bills(bill_df, cghs_df, exclusions_df):
    alerts = []
    audit_results = []
    total_items = len(bill_df)
    flagged_items = 0

    for _, row in bill_df.iterrows():
        service = str(row["Item"]).strip()
        amount = float(row["Amount (₹)"])
        flag = "✅ OK"
        comment = ""

        # Exclusion check
        if not exclusions_df.empty:
            excluded_services = exclusions_df[exclusions_df["Excluded_Service"].str.lower() == "yes"]["Services"].str.lower().values
            if service.lower() in excluded_services:
                flag = "❌ Excluded"
                comment = "Service not covered by insurer"

        # Overcharge check
        match = cghs_df[cghs_df["Service"].str.lower() == service.lower()]
        if not match.empty:
            rate = float(match["Rate (₹)"].values[0])
            if amount > rate:
                flag = "⚠️ Overcharged"
                comment = f"Charged ₹{amount}, CGHS Rate ₹{rate}"
                flagged_items += 1
        elif match.empty and flag == "✅ OK":
            flag = "ℹ️ Not Found"
            comment = "Service not found in CGHS list"

        audit_results.append([service, amount, flag, comment])

    audit_df = pd.DataFrame(audit_results, columns=["Service", "Amount (₹)", "Audit Flag", "Comment"])
    audit_score = round(((total_items - flagged_items) / total_items) * 100, 2)
    return audit_df, flagged_items, audit_score


# ------------------ Upload Bill ------------------
st.sidebar.header("📤 Upload Hospital Bill")
bill_file = st.sidebar.file_uploader("Upload Patient Bill (Excel/PDF/Image)", type=["xlsx", "xls", "pdf", "png", "jpg", "jpeg"])

# ------------------ Main Logic ------------------
if bill_file is not None:
    file_name = bill_file.name
    st.success(f"✅ Uploaded: {file_name}")

    if file_name.endswith(".pdf"):
        text = extract_text_from_pdf(bill_file.read())
        st.text_area("📄 Extracted PDF Text", text, height=200)
        st.warning("⚠️ PDF format detected — extraction might not be fully structured.")
        bill_df = pd.DataFrame()
    elif file_name.endswith((".png", ".jpg", ".jpeg")):
        text = extract_text_from_image(bill_file.read())
        st.text_area("🖼 Extracted OCR Text", text, height=200)
        st.warning("⚠️ Image OCR accuracy may vary — check extracted data.")
        bill_df = pd.DataFrame()
    else:
        bill_df = pd.read_excel(bill_file)

    if not bill_df.empty:
        # Extract basic patient info if columns exist
        st.subheader("👩‍⚕️ Patient Information")
        patient_info_cols = [col for col in bill_df.columns if "Patient" in col or "Hospital" in col or "Insurer" in col]
        if patient_info_cols:
            st.write(bill_df[patient_info_cols].head(1))
        else:
            with st.expander("Add Patient Details Manually"):
                name = st.text_input("Patient Name")
                age = st.text_input("Age")
                hospital = st.text_input("Hospital Name")
                insurer = st.text_input("Insurance Provider")
                admission = st.date_input("Admission Date")
                discharge = st.date_input("Discharge Date")

        # Run audit
        st.subheader("🩺 Bill Audit Results")
        audited_df, flagged, audit_score = audit_bills(bill_df, cghs_df, exclusions_df)

        def highlight_rows(row):
            if "Overcharged" in row["Audit Flag"]:
                return ["background-color: #ffcccc"] * len(row)
            elif "Excluded" in row["Audit Flag"]:
                return ["background-color: #ffe699"] * len(row)
            elif "Not Found" in row["Audit Flag"]:
                return ["background-color: #d9e1f2"] * len(row)
            else:
                return ["background-color: #e2efda"] * len(row)

        st.dataframe(audited_df.style.apply(highlight_rows, axis=1), use_container_width=True)

        st.markdown(f"""
        ### 📊 Audit Summary  
        - **Total Items:** {len(bill_df)}  
        - **Flagged Items:** {flagged}  
        - **Audit Score:** {audit_score}%  
        """)

        if audit_score < 90:
            st.error("⚠️ Potential overcharges or exclusions found.")
        else:
            st.success("✅ Bill appears compliant.")

else:
    st.info("👈 Upload a hospital bill to begin automatic auditing.")
