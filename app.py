import streamlit as st
import pandas as pd
import pdfplumber
import easyocr
from PIL import Image
import io

st.set_page_config(page_title="Smart Medical Audit", page_icon="💊", layout="wide")

st.title("💊 Smart Medical Audit Dashboard")
st.markdown("### Automated Bill Audit using CGHS Rates and Insurer Exclusions")

# ------------------ Upload Section ------------------
st.sidebar.header("📤 Upload Required Files")

bill_file = st.sidebar.file_uploader("Upload Hospital Bill (Excel/PDF/Image)", type=["xlsx", "xls", "pdf", "png", "jpg", "jpeg"])
cghs_file = st.sidebar.file_uploader("Upload CGHS Rate List (Excel)", type=["xlsx", "xls"])
exclusion_file = st.sidebar.file_uploader("Upload Insurer Exclusions (Excel)", type=["xlsx", "xls"])

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

        # Check exclusions
        if not exclusions_df.empty:
            excluded_services = exclusions_df[exclusions_df["Excluded_Service"].str.lower() == "yes"]["Services"].str.lower().values
            if service.lower() in excluded_services:
                flag = "❌ Excluded Service"
                comment = "Service not covered by insurer"

        # Check overcharging
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


# ------------------ Process Section ------------------
if bill_file and cghs_file and exclusion_file:
    st.success("✅ All files uploaded successfully!")

    # Read Excel files
    cghs = pd.read_excel(cghs_file)
    exclusions = pd.read_excel(exclusion_file)

    if bill_file.name.endswith(".pdf"):
        text = extract_text_from_pdf(bill_file.read())
        st.text_area("Extracted PDF Text", text, height=200)
        st.warning("⚠️ PDF parsing is text-based — use Excel for structured analysis.")
        bill_df = pd.DataFrame()  # placeholder
    elif bill_file.name.endswith((".png", ".jpg", ".jpeg")):
        text = extract_text_from_image(bill_file.read())
        st.text_area("Extracted Image Text", text, height=200)
        st.warning("⚠️ OCR results may vary — please verify extracted data.")
        bill_df = pd.DataFrame()
    else:
        bill_df = pd.read_excel(bill_file)

    if not bill_df.empty:
        st.subheader("📋 Uploaded Bill Preview")
        st.dataframe(bill_df, use_container_width=True)

        audited_df, flagged, audit_score = audit_bills(bill_df, cghs, exclusions)

        st.subheader("🩺 Audit Results")
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
        ### 🧾 Audit Summary  
        - **Total Services:** {len(bill_df)}  
        - **Flagged Items:** {flagged}  
        - **Audit Score:** {audit_score}%  
        """)

        if audit_score < 90:
            st.error("⚠️ Significant discrepancies detected. Please review flagged items.")
        else:
            st.success("✅ Bill appears compliant with CGHS rates and insurer policies.")

else:
    st.info("👈 Upload all three files (Bill, CGHS Rate List, and Exclusions) to begin audit.")
