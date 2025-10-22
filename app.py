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
st.sidebar.markdown("<h1 style='color:#3B82F6;'>💊 Smart Medical Audit</h1>", unsafe_allow_html=True)

# Try loading logo
try:
    st.sidebar.image("logo.png", width=120)
except:
    st.sidebar.info("Upload logo.png for sidebar branding")

st.sidebar.markdown("""
**Features:**
- Upload Excel, PDF, or Image bills  
- Detect overcharges automatically  
- OCR for image-based bills  
- Works with insurance exclusions  
""")

st.sidebar.markdown("---")
st.sidebar.caption("Developed for case competition • 2025")

# ---------- FILE UPLOAD ----------
st.title("🧾 Medical Bill Audit Prototype")
uploaded_file = st.file_uploader("Upload your medical bill (Excel, PDF, or Image)", type=["xlsx", "csv", "pdf", "png", "jpg", "jpeg"])

# ---------- OCR Setup ----------
reader = easyocr.Reader(['en'], gpu=False)

# ---------- UTILITY FUNCTIONS ----------

def load_reference_data():
    try:
        cghs = pd.read_csv("cghs_rates.csv")
        excl = pd.read_csv("insurer_exclusions.csv")
        return cghs, excl
    except:
        st.error("Missing reference files: cghs_rates.csv or insurer_exclusions.csv")
        return pd.DataFrame(), pd.DataFrame()


def excel_to_dataframe(file):
    try:
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        return df
    except Exception as e:
        st.error(f"Error reading Excel: {e}")
        return pd.DataFrame()


def pdf_to_dataframe(file):
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


def image_to_dataframe(uploaded_file):
    try:
        img = Image.open(uploaded_file).convert('RGB')
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


def highlight_overcharge(row, cghs):
    if "Service" in row and "Amount" in row:
        ref = cghs[cghs["Service"] == row["Service"]]
        if not ref.empty and row["Amount"] > ref["Rate"].values[0]:
            return "background-color: #FECACA"
    return ""

# ---------- MAIN LOGIC ----------
if uploaded_file:
    file_type = uploaded_file.name.split('.')[-1].lower()

    if file_type in ["xlsx", "csv"]:
        df = excel_to_dataframe(uploaded_file)
    elif file_type == "pdf":
        df = pdf_to_dataframe(uploaded_file)
    elif file_type in ["jpg", "jpeg", "png"]:
        df = image_to_dataframe(uploaded_file)
    else:
        st.error("Unsupported file format.")
        df = pd.DataFrame()

    if not df.empty:
        st.success(f"✅ Successfully processed your {file_type.upper()} file!")
        st.dataframe(df.head(20))

        cghs, exclusions = load_reference_data()

        if not cghs.empty and "Service" in df.columns and "Amount" in df.columns:
            styled = df.style.apply(lambda x: highlight_overcharge(x, cghs), axis=1)
            st.subheader("🔍 Audit Results")
            st.dataframe(styled)

            # Visualization
            if "Amount" in df.columns:
                fig = px.bar(df, x=df.index, y="Amount", title="Billing Overview", color_discrete_sequence=["#3B82F6"])
                st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Please upload a medical bill to start auditing.")

# ---------- FOOTER ----------
st.markdown("""
---
**Smart Medical Audit © 2025**  
Empowering patients through transparent billing.
""")
