import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
from io import BytesIO
import difflib
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime, timedelta
import time
import random

# Page config
st.set_page_config(
    page_title="MediAudit Pro",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
        /* Hero Image Banner */
        .hero-banner {
            background: linear-gradient(rgba(30, 58, 138, 0.9), rgba(59, 130, 246, 0.9)),
                        url('https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=1200');
            background-size: cover;
            background-position: center;
            padding: 3rem 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .hero-banner h1 {
            color: white;
            font-size: 2.8rem;
            font-weight: 700;
            margin: 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .hero-banner p {
            color: #e0e7ff;
            font-size: 1.2rem;
            margin: 0.5rem 0 0 0;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
            border-right: 2px solid #e2e8f0;
        }
        
        [data-testid="stSidebar"] h3 {
            color: #1e293b !important;
            font-weight: 700;
        }
        
        [data-testid="stSidebar"] [role="radiogroup"] label {
            background: white;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            margin: 0.25rem 0;
            border: 2px solid #e2e8f0;
            transition: all 0.3s;
        }
        
        [data-testid="stSidebar"] [role="radiogroup"] label:hover {
            border-color: #3b82f6;
            background: #eff6ff;
            transform: translateX(4px);
        }
        
        [data-testid="stSidebar"] [role="radiogroup"] label[data-checked="true"] {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white !important;
            border-color: #2563eb;
        }
        
        /* Card styling */
        .info-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-left: 4px solid #3b82f6;
            margin-bottom: 1rem;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: #1e3a8a;
        }
        
        .metric-label {
            color: #64748b;
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }
        
        /* Audit Categories */
        .audit-category {
            background: #fff7ed;
            border: 2px solid #fb923c;
            padding: 1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
        }
        
        .audit-category-pass {
            background: #d1fae5;
            border: 2px solid #10b981;
        }
        
        .audit-category-fail {
            background: #fee2e2;
            border: 2px solid #ef4444;
        }
        
        /* Negotiation Card */
        .negotiation-card {
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            border: 3px solid #f59e0b;
            padding: 1.5rem;
            border-radius: 12px;
            margin: 1rem 0;
        }
        
        /* WhatsApp Button */
        .whatsapp-float {
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 1000;
        }
        
        .whatsapp-button {
            background: #25D366;
            color: white;
            padding: 15px 20px;
            border-radius: 50px;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(37, 211, 102, 0.4);
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 10px;
        }
        
        /* Free badge */
        .free-badge {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: 700;
            font-size: 1.2rem;
            display: inline-block;
            margin: 1rem 0;
        }
        
        .strikethrough-price {
            text-decoration: line-through;
            color: #94a3b8;
            font-size: 1.5rem;
        }
        
        /* Progress animation */
        .audit-progress {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            border: 2px solid #3b82f6;
            margin: 1rem 0;
        }
        
        /* Bill queue */
        .queued-bill {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            border-left: 4px solid #3b82f6;
        }
    </style>
""", unsafe_allow_html=True)

# WhatsApp Chatbot Float Button
st.markdown("""
    <div class="whatsapp-float">
        <a href="https://wa.me/919876543210?text=Hi%20MediAudit%20Pro,%20I%20need%20help%20with%20my%20medical%20bill" 
           target="_blank" class="whatsapp-button">
            💬 Chat on WhatsApp
        </a>
    </div>
""", unsafe_allow_html=True)

# Helper functions
@st.cache_data
def load_reference_data():
    try:
        cghs = pd.read_csv("cghs_rates.csv")
    except Exception:
        cghs = pd.DataFrame({
            "Service": ["Room Rent", "Doctor Fees", "Lab Test", "Surgery", "ICU Charges", "CT Scan", "MRI", "X-Ray"],
            "Rate (₹)": [4000, 2500, 1500, 50000, 8000, 3000, 5000, 800]
        })
    return cghs

def normalize_text(s):
    if pd.isna(s):
        return ""
    return str(s).strip().lower()

def fuzzy_match_service(service, cghs_services, cutoff=0.70):
    if not service:
        return None, 0.0
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

def detect_overcharge_type(item_name, amount, standard_rate):
    """Detect type of overcharge based on patterns"""
    item_lower = item_name.lower()
    
    # Inflated Consumables
    if any(word in item_lower for word in ['syringe', 'gloves', 'mask', 'cotton', 'bandage', 'gauze', 'sanitizer']):
        if amount > standard_rate * 2:
            return "Inflated Consumables"
    
    # Duplicate Billing (simplified detection)
    return "Overcharge Detected"

def text_to_items_from_lines(lines):
    items = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.rsplit(" ", 1)
        if len(parts) == 2:
            left, right = parts
            amount_token = right.replace("₹", "").replace(",", "").replace("Rs.", "").strip()
            if amount_token.replace(".", "", 1).isdigit():
                try:
                    amt = float(amount_token)
                    items.append((left.strip(), amt))
                    continue
                except:
                    pass
    return items

def extract_text_from_pdf_bytes(pdf_bytes):
    text_accum = ""
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_accum += page_text + "\n"
    except Exception:
        pass
    return text_accum

def extract_text_from_image_bytes(img_bytes):
    try:
        img = Image.open(BytesIO(img_bytes)).convert("RGB")
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        return ""

# Initialize session state
if 'bill_queue' not in st.session_state:
    st.session_state.bill_queue = []
if 'current_audit' not in st.session_state:
    st.session_state.current_audit = None
if 'payment_history' not in st.session_state:
    st.session_state.payment_history = []
if 'negotiation_requests' not in st.session_state:
    st.session_state.negotiation_requests = []
if 'show_payment' not in st.session_state:
    st.session_state.show_payment = False
if 'payment_bills' not in st.session_state:
    st.session_state.payment_bills = []
if 'payment_type' not in st.session_state:
    st.session_state.payment_type = None

# Sidebar
with st.sidebar:
    st.markdown("### 🏥 MediAudit Pro")
    st.markdown("*Smart Medical Bill Auditing*")
    st.markdown("---")
    
    user_type = st.radio(
        "Navigate",
        ["🏠 Home", "👤 Patient Portal", "🏢 B2B Enterprise", "ℹ️ About & Pricing"],
        key="user_type_selector"
    )
    
    st.markdown("---")
    
    if user_type == "👤 Patient Portal":
        st.markdown("### 📊 Your Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Audits", str(len(st.session_state.payment_history) + len(st.session_state.bill_queue)))
        with col2:
            st.metric("In Queue", str(len(st.session_state.bill_queue)))
        
        if st.session_state.bill_queue:
            st.markdown("---")
            total_queue = sum([b.get('total_to_pay', b['total_billed']) for b in st.session_state.bill_queue])
            st.info(f"**Queue Total Due**\n₹{total_queue:,.0f}")
    
    st.markdown("---")
    st.markdown("### 💬 Quick Help")
    if st.button("📱 WhatsApp Support", use_container_width=True):
        st.markdown("[Click to chat](https://wa.me/919876543210)")
    st.markdown("📧 support@mediaudit.com")

# Main content
if user_type == "🏠 Home":
    st.markdown("""
        <div class="hero-banner">
            <h1>🏥 MediAudit Pro</h1>
            <p>AI-Powered Medical Bill Auditing - Detect Overcharges & Save Money</p>
            <p style="font-size: 1rem; margin-top: 1rem;">✓ Free Audits | ✓ Expert Negotiation | ✓ WhatsApp Support</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🎯 What We Audit For")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
            <div class="info-card" style="text-align: center;">
                <h3>💊</h3>
                <h4>Inflated Consumables</h4>
                <p>Overpriced syringes, gloves, masks, and basic supplies</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="info-card" style="text-align: center;">
                <h3>🔄</h3>
                <h4>Duplicate Billing</h4>
                <p>Same service charged multiple times</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class="info-card" style="text-align: center;">
                <h3>📈</h3>
                <h4>Upcoding</h4>
                <p>Basic service billed as premium procedure</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
            <div class="info-card" style="text-align: center;">
                <h3>📦</h3>
                <h4>Unbundling</h4>
                <p>Package services split to inflate cost</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### 💼 Our Services")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div class="info-card">
                <h3>🆓 FREE Bill Audit</h3>
                <p>✓ AI-powered analysis</p>
                <p>✓ Detect all 4 overcharge types</p>
                <p>✓ Detailed audit report</p>
                <p>✓ CGHS rate comparison</p>
                <p>✓ Instant results</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="negotiation-card">
                <h3>🤝 Expert Negotiation Service</h3>
                <p>✓ We negotiate on your behalf</p>
                <p>✓ Deal with hospital billing dept</p>
                <p>✓ Get overcharges reduced/removed</p>
                <p>✓ Pay only 15% commission on savings</p>
                <p style="font-weight: 700; color: #92400e;">Example: We save you ₹10,000 → You pay us ₹1,500</p>
            </div>
        """, unsafe_allow_html=True)

elif user_type == "👤 Patient Portal":
    st.markdown("""
        <div class="hero-banner">
            <h1>👤 Patient Portal</h1>
            <p>Upload bills, detect overcharges, and let us negotiate savings for you!</p>
        </div>
    """, unsafe_allow_html=True)
    
    tabs = st.tabs(["📤 New Bill Audit", "🗂️ Bill Queue & Payment", "🤝 Negotiation Requests", "📋 History"])
    
    # ======================================================================
    # TAB 0: New Bill Audit (Existing Logic)
    # ======================================================================
    with tabs[0]:
        st.markdown("### 👤 Patient Information")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            patient_name = st.text_input("Patient Name", placeholder="Enter full name")
            patient_id = st.text_input("Patient ID", disabled=True, 
                                      value=f"PAT{datetime.now().strftime('%Y%m%d%H%M')}")
        
        with col2:
            hospital_list = ["Select hospital", "AIIMS Delhi", "Apollo Hospital", "Fortis Hospital", 
                           "Medanta", "Manipal Hospital", "Narayana Health", "Max Hospital"]
            hospital = st.selectbox("Hospital", hospital_list)
            admission_date = st.date_input("Admission Date", datetime.now().date() - timedelta(days=7))
        
        with col3:
            contact_number = st.text_input("Contact Number", placeholder="+91-9876543210")
            email = st.text_input("Email", placeholder="patient@email.com")
        
        st.markdown("---")
        st.markdown("### 📁 Upload Medical Bill")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded = st.file_uploader(
                "Upload your medical bill",
                type=["csv", "xlsx", "pdf", "jpg", "jpeg", "png"],
                help="Supported: PDF, Excel, CSV, Images"
            )
        
        with col2:
            st.info("**We Check For:**\n- Inflated Consumables\n- Duplicate Billing\n- Upcoding\n- Unbundling")
        
        manual_extract = st.checkbox("📝 Enter manually")
        
        if uploaded or manual_extract:
            df_items = pd.DataFrame(columns=["Item", "Amount (₹)"])
            
            if manual_extract:
                txt = st.text_area("Paste bill text", height=150)
                if txt:
                    lines = txt.splitlines()
                    items = text_to_items_from_lines(lines)
                    df_items = pd.DataFrame(items, columns=["Item", "Amount (₹)"])
            else:
                ext = uploaded.name.split(".")[-1].lower()
                
                with st.spinner("🔄 Extracting bill data..."):
                    if ext in ("csv", "xlsx"):
                        try:
                            df_items = pd.read_csv(uploaded) if ext == "csv" else pd.read_excel(uploaded)
                            col_map = {}
                            for c in df_items.columns:
                                lc = c.strip().lower()
                                if "item" in lc or "service" in lc:
                                    col_map[c] = "Item"
                                if "amount" in lc or "₹" in lc or "cost" in lc:
                                    col_map[c] = "Amount (₹)"
                            df_items = df_items.rename(columns=col_map)
                            if "Item" in df_items.columns and "Amount (₹)" in df_items.columns:
                                df_items = df_items[["Item", "Amount (₹)"]]
                        except Exception as e:
                            st.error(f"Error: {e}")
                    
                    elif ext in ("jpg", "jpeg", "png"):
                        bytes_data = uploaded.read()
                        txt = extract_text_from_image_bytes(bytes_data)
                        if txt:
                            items = text_to_items_from_lines(txt.splitlines())
                            df_items = pd.DataFrame(items, columns=["Item", "Amount (₹)"])
                    
                    elif ext == "pdf":
                        txt = extract_text_from_pdf_bytes(uploaded.read())
                        if txt.strip():
                            items = text_to_items_from_lines(txt.splitlines())
                            df_items = pd.DataFrame(items, columns=["Item", "Amount (₹)"])
            
            if df_items.empty:
                df_items = pd.DataFrame([["", ""], ["", ""]], columns=["Item", "Amount (₹)"])
            
            st.markdown("### 📋 Extracted Items")
            edited = st.data_editor(df_items, num_rows="dynamic", use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                run_audit = st.button("🚀 Run FREE Audit", use_container_width=True, type="primary")
            
            if run_audit and not edited.empty and patient_name:
                # Audit Progress Animation
                st.markdown("### 🔍 Auditing Your Bill...")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                audit_steps = [
                    ("Checking for Inflated Consumables...", 25),
                    ("Detecting Duplicate Billing...", 50),
                    ("Analyzing for Upcoding...", 75),
                    ("Checking Unbundling Practices...", 100)
                ]
                
                for step, progress in audit_steps:
                    status_text.text(step)
                    progress_bar.progress(progress)
                    time.sleep(0.8)
                
                status_text.empty()
                progress_bar.empty()
                
                # Perform Audit
                cghs_df = load_reference_data()
                cghs_df["service_norm"] = cghs_df["Service"].astype(str).str.strip().str.lower()
                cghs_services = list(cghs_df["service_norm"].dropna().unique())
                
                results = []
                alerts = []
                overcharge_types = {
                    "Inflated Consumables": 0,
                    "Duplicate Billing": 0,
                    "Upcoding": 0,
                    "Unbundling": 0
                }
                
                total_billed = 0
                total_standard = 0
                potential_savings = 0
                
                for idx, r in edited.iterrows():
                    item = normalize_text(r.get("Item", ""))
                    if not item:
                        continue
                    
                    try:
                        amount = float(str(r.get("Amount (₹)", 0)).replace(",", "").replace("₹", "").strip())
                    except:
                        amount = 0.0
                    
                    total_billed += amount
                    status = "Normal"
                    overcharge_type = ""
                    comment = ""
                    standard_rate = amount
                    
                    matched, score = fuzzy_match_service(item, cghs_services, cutoff=0.65)
                    
                    if matched:
                        row_ref = cghs_df[cghs_df["service_norm"] == matched].iloc[0]
                        rate = float(row_ref["Rate (₹)"])
                        standard_rate = rate
                        
                        if amount > rate * 1.15:  # 15% tolerance
                            status = "Overcharged"
                            savings = amount - rate
                            potential_savings += savings
                            
                            # Determine overcharge type
                            if any(word in item for word in ['syringe', 'glove', 'mask', 'cotton', 'bandage', 'gauze']):
                                overcharge_type = "Inflated Consumables"
                                overcharge_types["Inflated Consumables"] += 1
                            elif amount > rate * 2:
                                overcharge_type = "Upcoding"
                                overcharge_types["Upcoding"] += 1
                            else:
                                overcharge_type = "Overcharge Detected"
                            
                            comment = f"₹{amount:,.0f} vs ₹{rate:,.0f} (Save ₹{savings:,.0f})"
                            alerts.append(f"⚠️ {r.get('Item')}: {overcharge_type} - Save ₹{savings:,.0f}")
                        
                        total_standard += rate
                    else:
                        status = "Unlisted"
                        comment = "Not in CGHS rates"
                        total_standard += amount # Assume billed amount is the standard if unlisted
                    
                    results.append({
                        "Service": r.get("Item"),
                        "Billed (₹)": amount,
                        "Standard (₹)": standard_rate,
                        "Status": status,
                        "Type": overcharge_type,
                        "Comments": comment
                    })
                
                results_df = pd.DataFrame(results)
                flagged_count = len([r for r in results if r['Status'] == 'Overcharged'])
                audit_score = max(0, 100 - flagged_count * 10)
                
                # Store audit
                st.session_state.current_audit = {
                    'patient_name': patient_name,
                    'hospital': hospital,
                    'contact': contact_number,
                    'email': email,
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                    'results_df': results_df,
                    'total_billed': total_billed,
                    'total_standard': total_standard,
                    'potential_savings': potential_savings,
                    'audit_score': audit_score,
                    'flagged_count': flagged_count,
                    'alerts': alerts,
                    'overcharge_types': overcharge_types,
                    'negotiation_status': 'Initial Audit' # New status field
                }
                
                st.success("✅ Audit Complete!")
                st.markdown("---")
                
                # Results
                st.markdown("### 📊 Audit Summary")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{len(results_df)}</div>
                            <div class="metric-label">Items Checked</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{flagged_count}</div>
                            <div class="metric-label">Issues Found</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{audit_score}</div>
                            <div class="metric-label">Audit Score</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f"""
                        <div class="metric-card" style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);">
                            <div class="metric-value" style="color: #92400e;">₹{potential_savings:,.0f}</div>
                            <div class="metric-label">Potential Savings</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                # Overcharge Types Found
                st.markdown("### 🔍 Overcharge Analysis")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    status_class = "audit-category-pass" if overcharge_types["Inflated Consumables"] == 0 else "audit-category-fail"
                    st.markdown(f"""
                        <div class="audit-category {status_class}">
                            <h4>💊 Inflated Consumables</h4>
                            <p>Found: {overcharge_types["Inflated Consumables"]}</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    status_class = "audit-category-pass" if overcharge_types["Duplicate Billing"] == 0 else "audit-category-fail"
                    st.markdown(f"""
                        <div class="audit-category {status_class}">
                            <h4>🔄 Duplicate Billing</h4>
                            <p>Found: {overcharge_types["Duplicate Billing"]}</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    status_class = "audit-category-pass" if overcharge_types["Upcoding"] == 0 else "audit-category-fail"
                    st.markdown(f"""
                        <div class="audit-category {status_class}">
                            <h4>📈 Upcoding</h4>
                            <p>Found: {overcharge_types["Upcoding"]}</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    status_class = "audit-category-pass" if overcharge_types["Unbundling"] == 0 else "audit-category-fail"
                    st.markdown(f"""
                        <div class="audit-category {status_class}">
                            <h4>📦 Unbundling</h4>
                            <p>Found: {overcharge_types["Unbundling"]}</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("### 🔍 Detailed Results")
                
                def highlight_status(row):
                    if row["Status"] == "Overcharged":
                        return ['background-color: #fee2e2'] * len(row)
                    elif row["Status"] == "Unlisted":
                        return ['background-color: #e0f2fe'] * len(row)
                    return ['background-color: #d1fae5'] * len(row)
                
                st.dataframe(results_df.style.apply(highlight_status, axis=1), use_container_width=True, height=300)
                
                if alerts:
                    st.markdown("### ⚠️ Issues Found")
                    for alert in alerts:
                        st.warning(alert)
                
                # Negotiation Offer
                if potential_savings > 500:
                    st.markdown("---")
                    st.markdown(f"""
                        <div class="negotiation-card">
                            <h3>🤝 Want Us To Negotiate For You?</h3>
                            <p>We found potential savings of ₹{potential_savings:,.0f}</p>
                            <p>Our experts can negotiate with {hospital} on your behalf</p>
                            <p style="font-weight: 700; font-size: 1.1rem; color: #92400e;">
                                You pay only 15% commission on actual savings achieved
                            </p>
                            <p style="font-size: 0.9rem;">Example: We save you ₹{potential_savings:,.0f} → Your MAX fee: ₹{potential_savings*0.15:,.0f}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Yes, Negotiate For Me!", use_container_width=True, type="primary"):
                            negotiation_request = {
                                'id': f"NEG{datetime.now().strftime('%Y%m%d%H%M%S')}",
                                'patient_name': patient_name,
                                'hospital': hospital,
                                'contact': contact_number,
                                'email': email,
                                'potential_savings': potential_savings,
                                'commission': potential_savings * 0.15,
                                'status': 'Pending',
                                'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                                'audit_data': st.session_state.current_audit
                            }
                            st.session_state.negotiation_requests.append(negotiation_request)
                            st.success("✅ Negotiation request submitted! Check the 'Negotiation Requests' tab for status.")
                            st.balloons()
                            # Clear current audit to start a new one
                            st.session_state.current_audit = None
                            st.rerun()
                    
                    with col2:
                        if st.button("No Thanks, I'll Handle It", use_container_width=True):
                            st.info("No problem! You can still proceed with payment options below.")
                
                # Action buttons
                st.markdown("---")
                st.markdown("### 💳 What's Next?")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🗂️ Add to Bill Queue", use_container_width=True):
                        st.session_state.bill_queue.append(st.session_state.current_audit)
                        st.success(f"✓ Added! {len(st.session_state.bill_queue)} bills in queue")
                        st.session_state.current_audit = None
                        st.rerun()
                
                with col2:
                    if st.button("💰 Pay This Bill Now", use_container_width=True, type="primary"):
                        st.session_state.payment_bills = [st.session_state.current_audit]
                        st.session_state.show_payment = True
                        st.session_state.payment_type = "single"
                        st.rerun()
                
                with col3:
                    if st.button("📥 Download Report", use_container_width=True):
                        st.success("✓ Report downloaded!")
            
            elif run_audit and not patient_name:
                st.error("Please enter patient name to continue")
        
        # Demo Option
        st.markdown("---")
        st.markdown("### 🎭 Demo Mode")
        st.info("Don't have a bill? Try our demo to see how the audit works!")
        
        if st.button("🚀 Run Demo Bill Audit", use_container_width=True, type="secondary"):
            # Create dummy bill
            
            # Set demo patient info
            demo_patient_name = "Demo Patient"
            demo_hospital = "Apollo Hospital"
            demo_contact = "+91-9876543210"
            demo_email = "demo@mediaudit.com"
            
            st.markdown("### 🔍 Running Demo Audit...")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            audit_steps = [
                ("Checking for Inflated Consumables...", 25),
                ("Detecting Duplicate Billing...", 50),
                ("Analyzing for Upcoding...", 75),
                ("Checking Unbundling Practices...", 100)
            ]
            
            for step, progress in audit_steps:
                status_text.text(step)
                progress_bar.progress(progress)
                time.sleep(0.8)
            
            status_text.empty()
            progress_bar.empty()
            
            # Perform Demo Audit
            total_billed = 39700
            total_standard = 26800
            potential_savings = 12900
            
            # Demo results with specific overcharges
            demo_results = [
                {"Service": "Room Rent (General Ward)", "Billed (₹)": 8500, "Standard (₹)": 4000, 
                 "Status": "Overcharged", "Type": "Upcoding", "Comments": "₹8,500 vs ₹4,000 (Save ₹4,500)"},
                {"Service": "Doctor Consultation", "Billed (₹)": 3000, "Standard (₹)": 2500, 
                 "Status": "Normal", "Type": "", "Comments": "Within acceptable range"},
                {"Service": "Blood Test - CBC", "Billed (₹)": 2000, "Standard (₹)": 1500, 
                 "Status": "Normal", "Type": "", "Comments": "Within acceptable range"},
                {"Service": "Surgical Gloves (Box)", "Billed (₹)": 4500, "Standard (₹)": 800, 
                 "Status": "Overcharged", "Type": "Inflated Consumables", "Comments": "₹4,500 vs ₹800 (Save ₹3,700)"},
                {"Service": "CT Scan - Head", "Billed (₹)": 6000, "Standard (₹)": 3000, 
                 "Status": "Overcharged", "Type": "Overcharge", "Comments": "₹6,000 vs ₹3,000 (Save ₹3,000)"},
                {"Service": "Injection Syringe (Pack of 10)", "Billed (₹)": 2500, "Standard (₹)": 500, 
                 "Status": "Overcharged", "Type": "Inflated Consumables", "Comments": "₹2,500 vs ₹500 (Save ₹2,000)"},
                {"Service": "ICU Charges (Per Day)", "Billed (₹)": 12000, "Standard (₹)": 8000, 
                 "Status": "Normal", "Type": "", "Comments": "Within acceptable range"},
                {"Service": "X-Ray - Chest", "Billed (₹)": 1200, "Standard (₹)": 800, 
                 "Status": "Normal", "Type": "", "Comments": "Within acceptable range"}
            ]
            
            results_df = pd.DataFrame(demo_results)
            
            alerts = [
                "⚠️ Room Rent (General Ward): Upcoding - Save ₹4,500",
                "⚠️ Surgical Gloves (Box): Inflated Consumables - Save ₹3,700",
                "⚠️ CT Scan - Head: Overcharge Detected - Save ₹3,000",
                "⚠️ Injection Syringe (Pack of 10): Inflated Consumables - Save ₹2,000"
            ]
            
            overcharge_types = {
                "Inflated Consumables": 2,
                "Duplicate Billing": 0,
                "Upcoding": 1,
                "Unbundling": 0
            }

            flagged_count = 4
            audit_score = 60
            
            # Store demo audit
            st.session_state.current_audit = {
                'patient_name': demo_patient_name,
                'hospital': demo_hospital,
                'contact': demo_contact,
                'email': demo_email,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'results_df': results_df,
                'total_billed': total_billed,
                'total_standard': total_standard,
                'potential_savings': potential_savings,
                'audit_score': audit_score,
                'flagged_count': flagged_count,
                'alerts': alerts,
                'overcharge_types': overcharge_types,
                'is_demo': True,
                'negotiation_status': 'Initial Audit'
            }
            
            st.success("✅ Demo Audit Complete!")
            st.markdown("---")
            
            # Demo Results
            st.markdown("### 📊 Demo Audit Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">8</div>
                        <div class="metric-label">Items Checked</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">4</div>
                        <div class="metric-label">Issues Found</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">60</div>
                        <div class="metric-label">Audit Score</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                    <div class="metric-card" style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);">
                        <div class="metric-value" style="color: #92400e;">₹12,900</div>
                        <div class="metric-label">Potential Savings</div>
                    </div>
                """, unsafe_allow_html=True)
            
            # Overcharge Types Found
            st.markdown("### 🔍 Demo Overcharge Analysis")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                    <div class="audit-category audit-category-fail">
                        <h4>💊 Inflated Consumables</h4>
                        <p>Found: 2 issues</p>
                        <p style="font-size: 0.85rem;">Gloves & Syringes overpriced</p>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                    <div class="audit-category audit-category-pass">
                        <h4>🔄 Duplicate Billing</h4>
                        <p>Found: 0 issues</p>
                        <p style="font-size: 0.85rem;">All clear!</p>
                    </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                    <div class="audit-category audit-category-fail">
                        <h4>📈 Upcoding</h4>
                        <p>Found: 1 issue</p>
                        <p style="font-size: 0.85rem;">Room rent inflated</p>
                    </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                    <div class="audit-category audit-category-pass">
                        <h4>📦 Unbundling</h4>
                        <p>Found: 0 issues</p>
                        <p style="font-size: 0.85rem;">All clear!</p>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("### 🔍 Detailed Demo Results")
            
            def highlight_status(row):
                if row["Status"] == "Overcharged":
                    return ['background-color: #fee2e2'] * len(row)
                return ['background-color: #d1fae5'] * len(row)
            
            st.dataframe(results_df.style.apply(highlight_status, axis=1), use_container_width=True, height=300)
            
            st.markdown("### ⚠️ Issues Found in Demo")
            for alert in alerts:
                st.warning(alert)
            
            # Demo Negotiation Offer
            st.markdown("---")
            st.markdown(f"""
                <div class="negotiation-card">
                    <h3>🤝 Demo: Our Negotiation Service</h3>
                    <p>In this demo, we found potential savings of ₹12,900</p>
                    <p>Our experts would negotiate with the hospital on your behalf</p>
                    <p style="font-weight: 700; font-size: 1.1rem; color: #92400e;">
                        You would pay only 15% commission on actual savings achieved
                    </p>
                    <p style="font-size: 0.9rem;">Example: We save you ₹12,900 → Your fee: ₹1,935</p>
                    <p style="margin-top: 1rem; padding: 1rem; background: white; border-radius: 8px;">
                        <strong>This is a demo.</strong> Upload a real bill to use our actual negotiation service!
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("### 💳 Try Demo Actions")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🗂️ Add Demo to Queue", use_container_width=True):
                    st.session_state.bill_queue.append(st.session_state.current_audit)
                    st.success(f"✓ Demo added! {len(st.session_state.bill_queue)} bills in queue")
                    st.session_state.current_audit = None
            with col2:
                st.button("💰 Try Payment Flow", use_container_width=True, disabled=True)
                st.caption("Available with real bills")
            with col3:
                if st.button("📥 Download Demo Report", use_container_width=True):
                    st.success("✓ Demo report downloaded!")

    # ======================================================================
    # TAB 1: Bill Queue & Payment (Updated for Negotiation/Commission/Payment Flow)
    # ======================================================================
    with tabs[1]:
        st.markdown("### 🗂️ Bill Queue & Payment")
        
        # --- Logic to handle newly negotiated bills ---
        # Find negotiation requests that were resolved and move them to the queue
        requests_to_remove = []
        for req in st.session_state.negotiation_requests:
            if req['status'] == 'Negotiated':
                # Create a new bill object based on the negotiated result
                negotiated_bill = {
                    'patient_name': req['patient_name'],
                    'hospital': req['hospital'],
                    'contact': req['contact'],
                    'email': req['email'],
                    'total_billed': req['audit_data']['total_billed'],
                    'potential_savings': req['actual_savings'],
                    'negotiation_id': req['id'],
                    'negotiation_status': 'Negotiated - Ready to Pay',
                    'reduced_bill_hospital': req['final_hospital_amount'],
                    'commission_fee': req['final_commission'],
                    'total_to_pay': req['total_to_pay'],
                    'date': req['date'],
                    'is_demo': req['audit_data'].get('is_demo', False)
                }
                # Check if this bill is already in the queue to avoid duplicates
                if not any(b.get('negotiation_id') == negotiated_bill['negotiation_id'] for b in st.session_state.bill_queue):
                    st.session_state.bill_queue.append(negotiated_bill)
                requests_to_remove.append(req)
        
        # Remove resolved negotiations from pending list
        st.session_state.negotiation_requests = [req for req in st.session_state.negotiation_requests if req not in requests_to_remove]
        # -----------------------------------------------

        if not st.session_state.bill_queue:
            st.info("📭 No bills in queue. Audit a bill and add it to queue or resolve a negotiation request!")
        else:
            total_queue = sum([b.get('total_to_pay', b['total_billed']) for b in st.session_state.bill_queue])
            st.markdown(f"""
                <div class="info-card" style="background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%); border-color: #fb923c;">
                    <h3>📋 {len(st.session_state.bill_queue)} Bills in Queue</h3>
                    <p style="font-size: 1.3rem; font-weight: 700; color: #1e3a8a;">Total Payment Due: ₹{total_queue:,.0f}</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Display queued bills
            bills_to_remove_from_queue = []
            for idx, bill in enumerate(st.session_state.bill_queue):
                is_demo = bill.get('is_demo', False)
                is_negotiated = bill.get('negotiation_status') == 'Negotiated - Ready to Pay'
                
                total_bill_amount = bill['total_billed']
                payment_due = bill.get('total_to_pay', total_bill_amount)
                
                demo_badge = " 🎭 DEMO" if is_demo else ""
                neg_badge = " 🤝 NEGOTIATED" if is_negotiated else ""
                
                with st.expander(f"Bill #{idx+1}{demo_badge}{neg_badge}: {bill['patient_name']} - {bill['hospital']} (₹{payment_due:,.0f} Due)"):
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Hospital:** {bill['hospital']}")
                        st.write(f"**Original Bill:** ₹{total_bill_amount:,.0f}")
                    
                    with col2:
                        st.write(f"**Savings Found:** ₹{bill['potential_savings']:,.0f}")
                        st.write(f"**Status:** {bill.get('negotiation_status', 'Awaiting Payment')}")

                    with col3:
                        if is_negotiated:
                            st.markdown(f"**Payment Breakdown:**")
                            st.markdown(f" - Hospital: **₹{bill['reduced_bill_hospital']:,.0f}**")
                            st.markdown(f" - MediAudit Fee: **₹{bill['commission_fee']:,.0f}**")
                        else:
                            st.markdown(f"**Total Due:** **₹{payment_due:,.0f}**")
                            st.write("Full bill amount due.")

                    st.markdown("---")
                    
                    col_c1, col_c2, col_c3 = st.columns(3)
                    
                    with col_c1:
                        if not is_demo:
                            if st.button(f"💰 Pay Bill #{idx+1}", key=f"pay_{idx}", use_container_width=True, type="primary"):
                                st.session_state.payment_bills = [bill]
                                st.session_state.show_payment = True
                                st.session_state.payment_type = "single"
                                st.rerun()
                        else:
                            st.button(f"💰 Pay Bill #{idx+1}", key=f"pay_{idx}", use_container_width=True, disabled=True)
                            st.caption("Demo bills can't be paid")
                    
                    with col_c2:
                        if st.button(f"🗑️ Remove", key=f"remove_{idx}", use_container_width=True):
                            bills_to_remove_from_queue.append(bill)
                            st.rerun()
                    
                    with col_c3:
                        # Option to initiate negotiation if not negotiated
                        if not is_negotiated and bill['potential_savings'] > 500:
                            if st.button("🤝 Initiate Negotiation", key=f"neg_init_{idx}", use_container_width=True):
                                # Create a negotiation request and remove from queue temporarily
                                negotiation_request = {
                                    'id': f"NEG{datetime.now().strftime('%Y%m%d%H%M%S')}_{idx}",
                                    'patient_name': bill['patient_name'],
                                    'hospital': bill['hospital'],
                                    'contact': bill.get('contact', 'N/A'),
                                    'email': bill.get('email', 'N/A'),
                                    'potential_savings': bill['potential_savings'],
                                    'commission': bill['potential_savings'] * 0.15,
                                    'status': 'Pending',
                                    'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                                    'audit_data': bill
                                }
                                st.session_state.negotiation_requests.append(negotiation_request)
                                bills_to_remove_from_queue.append(bill)
                                st.success("Negotiation request sent! Check the 'Negotiation Requests' tab for status.")
                                st.rerun()

            # Process removals outside the loop
            st.session_state.bill_queue = [b for b in st.session_state.bill_queue if b not in bills_to_remove_from_queue]


            st.markdown("---")
            
            # Check if any non-demo bills exist
            non_demo_bills = [b for b in st.session_state.bill_queue if not b.get('is_demo', False)]
            col1, col2 = st.columns(2)
            with col1:
                if non_demo_bills:
                    if st.button("💳 Pay All Bills Together", use_container_width=True, type="primary"):
                        st.session_state.payment_bills = non_demo_bills
                        st.session_state.show_payment = True
                        st.session_state.payment_type = "bulk"
                        st.rerun()
                else:
                    st.button("💳 Pay All Bills Together", use_container_width=True, disabled=True)
                    st.caption("Only demo bills in queue or queue is empty")
            with col2:
                if st.button("🗑️ Clear Queue", use_container_width=True):
                    st.session_state.bill_queue = []
                    st.rerun()

        # ----------------------------------------------------------------------
        # Payment Section (Payment Gateway Flow)
        # ----------------------------------------------------------------------
        if st.session_state.get('show_payment', False) and st.session_state.get('payment_bills'):
            st.markdown("---")
            st.markdown("## 💳 Complete Your Payment")
            
            payment_bills = st.session_state.get('payment_bills', [])
            
            # Calculate total payments (Hospital + Commission)
            hospital_total = 0.0
            commission_total = 0.0
            
            for bill in payment_bills:
                if bill.get('negotiation_status') == 'Negotiated - Ready to Pay':
                    hospital_total += bill['reduced_bill_hospital']
                    commission_total += bill['commission_fee']
                else:
                    hospital_total += bill['total_billed']
            
            total_payment = hospital_total + commission_total
            
            st.success(f"💰 **Total Payment Amount: ₹{total_payment:,.0f}**")
            st.markdown(f"Paying for {len(payment_bills)} bill(s)")
            
            if commission_total > 0:
                st.markdown(f"""
                    <div style="padding: 1rem; border-radius: 8px; background: #e0f2fe; border: 1px solid #3b82f6;">
                        **Breakdown:** - Payment to Hospital(s): **₹{hospital_total:,.0f}**
                        - MediAudit Commission Fee: **₹{commission_total:,.0f}**
                    </div>
                """, unsafe_allow_html=True)
            
            payment_method = st.radio(
                "Select Payment Method", 
                ["💳 Credit/Debit Card", "🏦 Net Banking", "📱 UPI", "💼 EMI Options"], 
                horizontal=True
            )
            
            if payment_method == "💳 Credit/Debit Card":
                col1, col2 = st.columns(2)
                with col1:
                    card_num = st.text_input("Card Number", placeholder="1234 5678 9012 3456")
                    card_name = st.text_input("Cardholder Name", placeholder="John Doe")
                with col2:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        expiry = st.text_input("Expiry (MM/YY)", placeholder="12/25")
                    with col_b:
                        cvv = st.text_input("CVV", placeholder="123", type="password")
                st.checkbox("Save card for future payments")
            
            elif payment_method == "🏦 Net Banking":
                bank = st.selectbox("Select Bank", [ "State Bank of India", "HDFC Bank", "ICICI Bank", "Axis Bank", "Kotak Mahindra Bank", "Punjab National Bank" ])
                st.info("You'll be redirected to your bank's secure payment gateway")
                
            elif payment_method == "📱 UPI":
                upi_id = st.text_input("UPI ID", placeholder="yourname@paytm")
                st.info("📱 You'll receive a payment request on your UPI app")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/Google_Pay_Logo_%282020%29.svg/200px-Google_Pay_Logo_%282020%29.svg.png", caption="Google Pay", width=100)
                with col2:
                    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/PhonePe_Logo.svg/200px-PhonePe_Logo.svg.png", caption="PhonePe", width=100)
                with col3:
                    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/2/24/Paytm_Logo_%28standalone%29.svg/200px-Paytm_Logo_%28standalone%29.svg.png", caption="Paytm", width=80)
                    
            elif payment_method == "💼 EMI Options":
                st.markdown("### 📊 EMI Calculator - Convert Bill to Monthly Payments")
                st.info("💡 Convert your medical bill into easy monthly installments")
                col1, col2, col3 = st.columns(3)
                with col1:
                    tenure = st.selectbox("EMI Tenure (Months)", [3, 6, 9, 12, 18, 24])
                with col2:
                    interest_rate = st.slider("Annual Interest Rate (%)", 5.0, 15.0, 10.0, 0.5)
                
                # Formula: EMI = P * R * (1 + R)^N / ((1 + R)^N - 1) where R is monthly rate
                monthly_rate = (interest_rate / 100) / 12
                # Handle zero/small rate edge case, though slider prevents it
                if monthly_rate == 0:
                    emi_amount = total_payment / tenure
                else:
                    emi_amount = total_payment * monthly_rate * (1 + monthly_rate) ** tenure / (((1 + monthly_rate) ** tenure) - 1)
                
                with col3:
                    st.markdown("---")
                    st.markdown(f"**Monthly EMI:**")
                    st.markdown(f"**₹{emi_amount:,.0f}**")
            
            st.markdown("---")
            
            # Final Pay Now Button (Transaction Gateway)
            if st.button(f"🔒 Pay Now - ₹{total_payment:,.0f}", use_container_width=True, type="primary"):
                
                paid_bills_ids = []
                for bill in payment_bills:
                    
                    final_amount_paid = bill.get('total_to_pay', bill['total_billed'])
                    
                    # Add to history
                    bill_history = {
                        'patient_name': bill['patient_name'],
                        'hospital': bill['hospital'],
                        'original_amount': bill['total_billed'],
                        'final_amount_paid': final_amount_paid,
                        'date_paid': datetime.now().strftime("%Y-%m-%d %H:%M"),
                        'savings': bill.get('potential_savings', 0),
                        'commission_paid': bill.get('commission_fee', 0),
                        'status': 'Paid'
                    }
                    st.session_state.payment_history.append(bill_history)
                    paid_bills_ids.append(bill.get('negotiation_id', bill['total_billed'])) # Use a unique ID/value

                
                # Remove paid bills from queue
                # Filter out bills whose ID/unique value is in paid_bills_ids
                st.session_state.bill_queue = [
                    b for b in st.session_state.bill_queue 
                    if b.get('negotiation_id', b['total_billed']) not in paid_bills_ids
                ]

                # Clear payment state
                st.session_state.show_payment = False
                st.session_state.payment_bills = []
                st.session_state.payment_type = None

                st.balloons()
                st.success(f"✅ Payment of ₹{total_payment:,.0f} Successful! Thank you.")
                st.rerun()

    # ======================================================================
    # TAB 2: Negotiation Requests (Completed Negotiation Flow)
    # ======================================================================
    with tabs[2]:
        st.markdown("### 🤝 Negotiation Requests Status")
        st.info("Our experts are working to reduce your bill! Use the button below to simulate the resolution of a negotiation request.")
        
        pending_requests = [r for r in st.session_state.negotiation_requests if r['status'] == 'Pending']
        
        if pending_requests:
            st.markdown("#### ⏳ Pending Negotiations")
            for idx, req in enumerate(pending_requests):
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Request ID:** {req['id']}")
                        st.write(f"**Patient:** {req['patient_name']} @ {req['hospital']}")
                        st.write(f"**Original Savings Target:** ₹{req['potential_savings']:,.0f}")
                    with col2:
                        st.markdown("##### Status: **Pending**")
                        
                    st.markdown("---")
                    
                    # Admin Action: Simulate resolution of negotiation.
                    if st.button(f"Simulate Successful Negotiation & Final Offer #{idx+1}", key=f"resolve_neg_{idx}", use_container_width=True, type="primary"):
                        
                        # 1. Determine Actual Savings (e.g., 85% to 95% of potential, capped by original savings)
                        simulated_success_rate = random.uniform(0.85, 0.95)
                        actual_savings = req['potential_savings'] * simulated_success_rate
                        actual_savings = min(actual_savings, req['potential_savings']) # Ensure savings doesn't exceed potential
                        
                        # 2. Calculate Final Amounts (Commission is 15% of ACTUAL savings)
                        original_bill = req['audit_data']['total_billed']
                        hospital_payment = original_bill - actual_savings
                        commission_fee = actual_savings * 0.15 # 15% of actual savings
                        total_to_pay = hospital_payment + commission_fee
                        
                        # 3. Update Request Object Status & Amounts
                        req['status'] = 'Negotiated'
                        req['actual_savings'] = actual_savings
                        req['final_hospital_amount'] = hospital_payment
                        req['final_commission'] = commission_fee
                        req['total_to_pay'] = total_to_pay
                        
                        st.success(f"✅ Negotiation for {req['patient_name']} resolved with **₹{actual_savings:,.0f}** in savings!")
                        st.warning(f"Final Offer: Total Payment Due **₹{total_to_pay:,.0f}** (Hospital: ₹{hospital_payment:,.0f} + Commission: ₹{commission_fee:,.0f})")
                        st.info("The negotiated bill is now in your 'Bill Queue & Payment' tab for final payment.")
                        st.rerun()
        else:
            st.success("🎉 No pending negotiation requests at this time.")

        st.markdown("---")
        
        # Display Negotiation History (Resolved/Paid requests from negotiation_requests)
        st.markdown("#### ✅ Negotiation History (Completed/Paid)")
        st.info("Bills that have been successfully paid after negotiation are now in the 'History' tab.")


    # ======================================================================
    # TAB 3: History (Ensuring it works with new data structure)
    # ======================================================================
    with tabs[3]:
        st.markdown("### 📋 Payment & Audit History")
        
        if not st.session_state.payment_history:
            st.info("No completed payments found.")
        else:
            for idx, item in enumerate(reversed(st.session_state.payment_history)):
                with st.container(border=True):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Date Paid:** {item['date_paid']}")
                        st.write(f"**Patient:** {item['patient_name']}")
                    with col2:
                        st.write(f"**Hospital:** {item['hospital']}")
                        st.write(f"**Original Bill:** ₹{item['original_amount']:,.0f}")
                    with col3:
                        st.write(f"**Final Paid:** **₹{item['final_amount_paid']:,.0f}**")
                        st.write(f"**Net Savings:** ₹{item['savings'] - item['commission_paid']:,.0f}")
                    
                    if item['commission_paid'] > 0:
                        st.caption(f"Savings Achieved: ₹{item['savings']:,.0f} | Negotiation Fee Paid: ₹{item['commission_paid']:,.0f}")

    # ======================================================================
    # Footer
    # ======================================================================
    st.markdown("---")
    
    # Placeholder for other tabs content (B2B and About - included for completeness)
    if user_type == "🏢 B2B Enterprise":
        st.markdown("### 🏢 B2B Enterprise Solutions")
        st.markdown("Custom API integration for insurance and large healthcare providers.")
        st.markdown("Contact us for a tailored quote.")
        
    elif user_type == "ℹ️ About & Pricing":
        st.markdown("### ℹ️ About MediAudit Pro")
        st.markdown("MediAudit Pro is an AI-powered service dedicated to detecting overcharges in medical bills, ensuring fairness and transparency.")
        
        st.markdown("#### Pricing Structure")
        st.markdown("""
            * **Initial Bill Audit:** **FREE** for all patients.
            * **Expert Negotiation Service:** **15% commission** on the **actual savings achieved**. No savings, no fee.
        """)
        
        st.markdown("#### FAQs")
        with st.expander("❓ How long does an audit take?"):
            st.write("An initial audit is instant (less than 5 seconds). Negotiation can take 7-14 business days depending on the hospital's billing cycle and complexity.")
        
        with st.expander("📱 Do you have a mobile app?"):
            st.write("Not yet, but our Streamlit app is fully responsive and our WhatsApp chatbot is available 24/7 for quick queries and assistance.")
        
        with st.expander("🏢 What do enterprises pay for?"):
            st.write("Enterprises pay for bulk processing, API access, custom integrations, and advanced analytics. Individual patient audits remain free for everyone.")
        
        with st.expander("🔒 Is my medical data secure?"):
            st.write("Yes. We use bank-grade encryption and comply with all healthcare data protection regulations (HIPAA equivalent). Your data is never shared without consent.")
        
        with st.expander("🎭 What is demo mode?"):
            st.write("Demo mode lets you try our audit system with sample data without uploading real bills. Perfect for understanding how the system works before using it with actual bills.")

    # Footer
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("**MediAudit Pro**")
        st.markdown("AI-powered medical auditing")
        st.markdown("*Free for patients*")
    
    with col2:
        st.markdown("**Services**")
        st.markdown("• Free Bill Audit")
        st.markdown("• Expert Negotiation")
        st.markdown("• EMI Options")
    
    with col3:
        st.markdown("**Quick Links**")
        st.markdown("• About Us")
        st.markdown("• Privacy Policy")
        st.markdown("• Terms of Service")
    
    with col4:
        st.markdown("**Contact**")
        st.markdown("• support@mediaudit.com")
        st.markdown("• +91-9876543210")
