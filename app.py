# app.py
import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
from io import BytesIO
import difflib
import plotly.express as px
import os

# Optional: if you want to use pdf->images fallback uncomment and install pdf2image & poppler
# from pdf2image import convert_from_bytes

st.set_page_config(page_title="Smart Medical Audit", page_icon="🏥", layout="wide")

# ---------------------------
# Helper / Utility functions
# ---------------------------
@st.cache_data
def load_reference_data():
    """Load CGHS and exclusions from repo CSV files (same names used earlier)."""
    try:
        cghs = pd.read_csv("cghs_rates.csv")
    except Exception:
        cghs = pd.DataFrame({"Service": ["Room Rent", "Doctor Fees", "Lab Test"], "Rate (₹)": [4000, 2500, 1500]})
        st.warning("Could not load cghs_rates.csv from repo — using default sample rates.")
    try:
        exclusions = pd.read_csv("insurer_exclusions.csv")
    except Exception:
        exclusions = pd.DataFrame({"Services": [], "Excluded_Service": []})
        st.warning("Could not load insurer_exclusions.csv from repo — exclusions disabled.")
    return cghs, exclusions

def normalize_text(s):
    if pd.isna(s):
        return ""
    return str(s).strip().lower()

def fuzzy_match_service(service, cghs_services, cutoff=0.75):
    """Return the best match from cghs_services (list) using difflib ratio threshold."""
    if not service:
        return None, 0.0
    # difflib returns sequences; we calculate ratio manually
    best = None
    best_score = 0.0
    for cand in cghs_services:
        score = difflib.SequenceMatcher(None, service, cand).ratio()
        if score > best_score:
            best_score = score
            best = cand
    if best_score >= cutoff:
        return best, best_score
    return None, best_score

def text_to_items_from_lines(lines):
    """Parse text lines into (item, amount) pairs with heuristics."""
    items = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # try to split last token as amount
        parts = line.rsplit(" ", 1)
        if len(parts) == 2:
            left, right = parts
            # clean amount token
            amount_token = right.replace("₹", "").replace(",", "").replace("Rs.", "").strip()
            # allow decimals
            if amount_token.replace(".", "", 1).isdigit():
                try:
                    amt = float(amount_token)
                    items.append((left.strip(), amt))
                    continue
                except:
                    pass
        # fallback: find any number token in line
        tokens = line.split()
        for t in reversed(tokens):
            tt = t.replace("₹", "").replace(",", "").replace("Rs.", "")
            if tt.replace(".", "", 1).isdigit():
                try:
                    amt = float(tt)
                    item_name = " ".join(tokens[:tokens.index(t)])
                    items.append((item_name.strip(), amt))
                    break
                except:
                    pass
    return items

def extract_text_from_image_bytes(img_bytes):
    """Use pytesseract to extract text from image bytes."""
    try:
        img = Image.open(BytesIO(img_bytes)).convert("RGB")
    except Exception as e:
        st.error(f"Unable to open image: {e}")
        return ""
    try:
        text = pytesseract.image_to_string(img)
    except Exception as e:
        st.error(f"Tesseract error: {e}")
        text = ""
    return text

def extract_text_from_pdf_bytes(pdf_bytes):
    """First try pdfplumber text extraction; if empty, optionally try converting pages to images (if pdf2image & poppler installed)."""
    text_accum = ""
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_accum += page_text + "\n"
    except Exception as e:
        st.info("pdfplumber couldn't parse PDF pages as text; trying OCR fallback if available.")
        text_accum = ""

    # If no textual content found, attempt OCR fallback via images (if pdf2image is available)
    if not text_accum.strip():
        try:
            from pdf2image import convert_from_bytes
            images = convert_from_bytes(pdf_bytes)
            for img in images:
                text_accum += pytesseract.image_to_string(img) + "\n"
        except Exception:
            # can't fallback — maybe poppler or pdf2image missing
            pass

    return text_accum

# ---------------------------
# UI and main flow
# ---------------------------
# Header + style
st.markdown(
    """
    <style>
        .title { font-size:34px; color:#03496b; font-weight:700; }
        .subtitle { color:#0466c8; }
        .card { background: #fff; border-radius:10px; padding:14px; box-shadow: 0 1px 6px rgba(0,0,0,0.08); }
    </style>
    """, unsafe_allow_html=True)

col_logo, col_title = st.columns([0.12, 0.88])
with col_logo:
    # show logo if available
    if os.path.exists("logo.png"):
        st.image("logo.png", width=110)
with col_title:
    st.markdown('<div class="title">🏥 Smart Medical Audit — AI OCR (Tesseract)</div>', unsafe_allow_html=True)
    st.caption("Upload a bill (PDF / Image / Excel). App will extract charges and audit against CGHS & insurer exclusions.")

# load refs
cghs_df, exclusions_df = load_reference_data()
cghs_df["service_norm"] = cghs_df["Service"].astype(str).str.strip().str.lower()

# Patient card inputs
st.markdown("### 👤 Patient & Policy Details")
pcol1, pcol2, pcol3 = st.columns([1,1,1])
with pcol1:
    patient_name = st.text_input("Patient Name")
    hospital_list = ["Select hospital"] + sorted([
        "AIIMS Delhi","Apollo Hospital","Fortis Hospital","Medanta","Manipal Hospital","Narayana Health","Max Hospital"
    ])
    hospital = st.selectbox("Hospital", hospital_list)
with pcol2:
    # auto-fill city/state if known
    hospital_map = {
        "AIIMS Delhi": ("New Delhi", "Delhi"),
        "Apollo Hospital": ("Chennai","Tamil Nadu"),
        "Fortis Hospital": ("Bangalore","Karnataka"),
        "Medanta": ("Gurugram","Haryana"),
        "Manipal Hospital": ("Bengaluru","Karnataka"),
        "Narayana Health": ("Kolkata","West Bengal"),
        "Max Hospital": ("Dehradun","Uttarakhand")
    }
    city, state = ("", "")
    if hospital in hospital_map:
        city, state = hospital_map[hospital]
    st.text_input("City", value=city, disabled=True)
    st.text_input("State", value=state, disabled=True)
with pcol3:
    insurer = st.selectbox("Insurance Provider", ["Select insurer","Star Health","HDFC ERGO","ICICI Lombard","Care Health","New India Assurance"])
    policy_number = st.text_input("Policy Number")

st.markdown("---")

# File uploader
st.markdown("### 📁 Upload Bill (Excel CSV, PDF, JPG/PNG)")
uploaded = st.file_uploader("Upload bill file", type=["csv","xlsx","pdf","jpg","jpeg","png"])

# Option: user can paste extracted text manually if OCR fails
manual_extract = st.checkbox("Paste bill text manually (if OCR fails)")

# When user uploads or paste text:
if uploaded or manual_extract:
    df_items = pd.DataFrame(columns=["Item","Amount (₹)"])

    if manual_extract:
        txt = st.text_area("Paste extracted bill text here")
        if txt:
            lines = txt.splitlines()
            items = text_to_items_from_lines(lines)
            df_items = pd.DataFrame(items, columns=["Item","Amount (₹)"])
    else:
        ext = uploaded.name.split(".")[-1].lower()
        if ext in ("csv","xlsx"):
            try:
                if ext == "csv":
                    df_items = pd.read_csv(uploaded)
                else:
                    df_items = pd.read_excel(uploaded)
                # try to normalize columns
                cols_lower = [c.strip().lower() for c in df_items.columns]
                if "item" not in cols_lower or not any("amount" in c for c in cols_lower):
                    # attempt to find columns heuristically
                    st.warning("Uploaded table doesn't have expected 'Item' and 'Amount' columns; please check or use manual text.")
                else:
                    # rename common variants
                    col_map = {}
                    for c in df_items.columns:
                        lc = c.strip().lower()
                        if "item" in lc:
                            col_map[c] = "Item"
                        if "amount" in lc or "₹" in lc or "rs" in lc:
                            col_map[c] = "Amount (₹)"
                    df_items = df_items.rename(columns=col_map)[["Item","Amount (₹)"]]
            except Exception as e:
                st.error(f"Error reading table file: {e}")
        elif ext in ("jpg","jpeg","png"):
            bytes_data = uploaded.read()
            txt = extract_text_from_image_bytes(bytes_data)
            lines = txt.splitlines()
            items = text_to_items_from_lines(lines)
            df_items = pd.DataFrame(items, columns=["Item","Amount (₹)"])
        elif ext == "pdf":
            pdf_bytes = uploaded.read()
            txt = extract_text_from_pdf_bytes(pdf_bytes)
            if txt.strip():
                lines = txt.splitlines()
                items = text_to_items_from_lines(lines)
                df_items = pd.DataFrame(items, columns=["Item","Amount (₹)"])
            else:
                st.warning("PDF had no extractable text — OCR fallback will be attempted if pdf2image/poppler is available.")
                # attempt pdf2image fallback if installed
                try:
                    from pdf2image import convert_from_bytes
                    images = convert_from_bytes(pdf_bytes)
                    all_items = []
                    for img in images:
                        text = pytesseract.image_to_string(img)
                        lines = text.splitlines()
                        items = text_to_items_from_lines(lines)
                        all_items.extend(items)
                    df_items = pd.DataFrame(all_items, columns=["Item","Amount (₹)"])
                except Exception:
                    st.error("OCR fallback for scanned PDF failed (pdf2image/poppler not available). Consider converting PDF pages to images and uploading.")
        else:
            st.error("Unsupported file type.")

    if df_items.empty:
        st.info("No line items found yet. You can edit the table below or paste text manually.")
        # provide an editable empty table with two rows
        df_items = pd.DataFrame([["",""],["",""]], columns=["Item","Amount (₹)"])
    # show preview editable
    st.markdown("#### 📋 Extracted / Uploaded Line Items (edit if needed)")
    edited = st.data_editor(df_items, num_rows="dynamic")
    run_audit = st.button("🚀 Run Audit")

    if run_audit:
        # Normalize reference lists
        cghs_services = list(cghs_df["service_norm"].dropna().unique())
        exclusions_norm = []
        if not exclusions_df.empty:
            # earlier repo had "Services" and "Excluded_Service" mapping; build list of excluded service names
            if "Excluded_Service" in exclusions_df.columns and "Services" in exclusions_df.columns:
                exclusions_norm = exclusions_df[exclusions_df["Excluded_Service"].astype(str).str.lower() == "yes"]["Services"].astype(str).str.lower().tolist()
            else:
                # fallback: take first column as service names where second column indicates yes
                cols = list(exclusions_df.columns)
                if len(cols) == 2:
                    leftcol, rightcol = cols[0], cols[1]
                    exclusions_norm = exclusions_df[exclusions_df[rightcol].astype(str).str.lower() == "yes"][leftcol].astype(str).str.lower().tolist()
                else:
                    exclusions_norm = exclusions_df.iloc[:,0].astype(str).str.lower().tolist()

        # run audit row-by-row
        results = []
        alerts = []
        flagged_count = 0
        for idx, r in edited.iterrows():
            item = normalize_text(r.get("Item",""))
            amt_raw = r.get("Amount (₹)", 0)
            try:
                amount = float(str(amt_raw).replace(",","").replace("₹","").strip()) if str(amt_raw).strip() else 0.0
            except:
                amount = 0.0

            status = "Normal"
            comment = ""

            # exclusion check
            if item and item in exclusions_norm:
                status = "Excluded"
                comment = "Excluded by insurer"
                alerts.append(f"🚫 {r.get('Item')} appears in insurer exclusions.")
                flagged_count += 1
            else:
                # match to CGHS: try exact then fuzzy
                matched = None
                if item in cghs_services:
                    matched = item
                    score = 1.0
                else:
                    matched, score = fuzzy_match_service(item, cghs_services, cutoff=0.65)
                if matched:
                    # get rate
                    row_ref = cghs_df[cghs_df["service_norm"] == matched].iloc[0]
                    rate = float(row_ref["Rate (₹)"])
                    if amount > rate * 1.1:  # 10% tolerance
                        status = "Overcharged"
                        comment = f"Charged ₹{amount}, CGHS ₹{rate}"
                        alerts.append(f"⚠️ {r.get('Item')} billed ₹{amount} vs standard ₹{rate}.")
                        flagged_count += 1
                else:
                    status = "Unlisted"
                    comment = "Service not found in CGHS"
                    alerts.append(f"ℹ️ {r.get('Item')} not found in CGHS list.")
                    flagged_count += 1

            results.append({
                "Service": r.get("Item"),
                "Amount (₹)": amount,
                "Status": status,
                "Comment": comment
            })

        results_df = pd.DataFrame(results)
        total_items = len(results_df)
        audit_score = max(0, 100 - flagged_count * 8)

        # show summary
        st.markdown("## ✅ Audit Summary")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Line Items", total_items)
        c2.metric("Flagged Items", flagged_count)
        c3.metric("Audit Score", f"{audit_score}/100")

        # color coding
        def style_flag(row):
            s = row["Status"]
            if s == "Overcharged":
                return ["background-color:#ffe6e6"]*len(row)
            if s == "Excluded":
                return ["background-color:#fff2cc"]*len(row)
            if s == "Unlisted":
                return ["background-color:#e6f0ff"]*len(row)
            return ["background-color:#e8f7e8"]*len(row)

        st.markdown("### 🔍 Detailed Audit Results")
        st.dataframe(results_df.style.apply(style_flag, axis=1), use_container_width=True)

        # charts
        try:
            filtered = results_df[results_df["Status"]!="Unlisted"]
            if not filtered.empty:
                fig = px.bar(filtered, x="Service", y="Amount (₹)", color="Status",
                             color_discrete_map={"Overcharged":"#ff4d4f","Excluded":"#ffa940","Normal":"#36c57f"})
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.info("Not enough data to visualize.")

        st.markdown("### ⚠️ Alerts")
        if alerts:
            for a in alerts:
                st.write(a)
        else:
            st.write("No alerts — all items appear fine.")

        st.success("Audit complete. You can copy or download the table for records.")
else:
    st.info("Upload a bill (or paste bill text) to begin audit.")
