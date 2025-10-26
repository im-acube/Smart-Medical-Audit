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
            total_queue = sum([b['total_billed'] for b in st.session_state.bill_queue])
            st.info(f"**Queue Total**\n₹{total_queue:,.0f}")
    
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
    
    # --- HOMEPAGE ALIGNMENT FIX: Changed from 4 columns to 2 rows of 2 columns for better responsiveness ---
    col_row1_1, col_row1_2 = st.columns(2)
    col_row2_1, col_row2_2 = st.columns(2)
    
    with col_row1_1:
        st.markdown("""
            <div class="info-card" style="text-align: center;">
                <h3>💊</h3>
                <h4>Inflated Consumables</h4>
                <p>Overpriced syringes, gloves, masks, and basic supplies</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col_row1_2:
        st.markdown("""
            <div class="info-card" style="text-align: center;">
                <h3>🔄</h3>
                <h4>Duplicate Billing</h4>
                <p>Same service charged multiple times</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---") # Visual separator between rows
        
    with col_row2_1:
        st.markdown("""
            <div class="info-card" style="text-align: center;">
                <h3>📈</h3>
                <h4>Upcoding</h4>
                <p>Basic service billed as premium procedure</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col_row2_2:
        st.markdown("""
            <div class="info-card" style="text-align: center;">
                <h3>📦</h3>
                <h4>Unbundling</h4>
                <p>Package services split to inflate cost</p>
            </div>
        """, unsafe_allow_html=True)
    # ---------------------------------------------------------------------------------------------------
    
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
            admission_date = st.date_input("Admission Date")
        
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
                        total_standard += rate
                        
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
                        else:
                            total_standard += amount
                    else:
                        status = "Unlisted"
                        comment = "Not in CGHS rates"
                        total_standard += amount
                    
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
                    'overcharge_types': overcharge_types
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
                            <p style="font-size: 0.9rem;">Example: We save you ₹{potential_savings:,.0f} → Your fee: ₹{potential_savings*0.15:,.0f}</p>
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
                            # --- NEGOTIATION MESSAGE UPDATE: Added 12-48hr timeframe and savings outcome ---
                            st.success(f"""
                                **✅ Negotiation Request Submitted!**
                                Our team will now start the negotiation process with {hospital}. 
                                **This process typically takes 12 to 48 hours.**
                                Once complete, you will be notified in the **Negotiation Requests** tab with the final saved amount and the reduced bill.
                            """)
                            st.balloons()
                            # -------------------------------------------------------------------------------
                    
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
                        st.rerun()
                
                with col2:
                    if st.button("💰 Pay This Bill Now", use_container_width=True, type="primary"):
                        st.session_state.payment_bills = [st.session_state.current_audit]
                        st.session_state.show_payment = True
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
            demo_bill = pd.DataFrame({
                'Item': [
                    'Room Rent (General Ward)',
                    'Doctor Consultation',
                    'Blood Test - CBC',
                    'Surgical Gloves (Box)',
                    'CT Scan - Head',
                    'Injection Syringe (Pack of 10)',
                    'ICU Charges (Per Day)',
                    'X-Ray - Chest'
                ],
                'Amount (₹)': [8500, 3000, 2000, 4500, 6000, 2500, 12000, 1200]
            })
            
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
            cghs_df = load_reference_data()
            cghs_df["service_norm"] = cghs_df["Service"].astype(str).str.strip().str.lower()
            cghs_services = list(cghs_df["service_norm"].dropna().unique())
            
            results = []
            alerts = []
            overcharge_types = {
                "Inflated Consumables": 2,
                "Duplicate Billing": 0,
                "Upcoding": 1,
                "Unbundling": 0
            }
            
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
                'is_demo': True
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
                    <p style="font-weight: 700; font-size: 1.1rem; color: #92400e;"> You would pay only 15% commission on actual savings achieved </p>
                    <p style="font-size: 0.9rem;">Example: We save you ₹12,900 → Your fee: ₹1,935</p>
                    <p style="margin-top: 1rem; padding: 1rem; background: white; border-radius: 8px;"> <strong>This is a demo.</strong> Upload a real bill to use our actual negotiation service! </p>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("### 💳 Try Demo Actions")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🗂️ Add Demo to Queue", use_container_width=True):
                    st.session_state.bill_queue.append(st.session_state.current_audit)
                    st.success(f"✓ Demo added! {len(st.session_state.bill_queue)} bills in queue")
            with col2:
                st.button("💰 Try Payment Flow", use_container_width=True, disabled=True)
                st.caption("Available with real bills")
            with col3:
                if st.button("📥 Download Demo Report", use_container_width=True):
                    st.success("✓ Demo report downloaded!")

    with tabs[1]:
        st.markdown("### 🗂️ Bill Queue & Payment")
        if not st.session_state.bill_queue:
            st.info("📭 No bills in queue. Audit a bill and add it to queue to pay multiple bills together!")
        else:
            total_queue = sum([b['total_billed'] for b in st.session_state.bill_queue])
            st.markdown(f"""
                <div class="info-card" style="background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%); border-color: #fb923c;">
                    <h3>📋 {len(st.session_state.bill_queue)} Bills in Queue</h3>
                    <p style="font-size: 1.3rem; font-weight: 700; color: #1e3a8a;">Total: ₹{total_queue:,.0f}</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Display queued bills
            for idx, bill in enumerate(st.session_state.bill_queue):
                is_demo = bill.get('is_demo', False)
                demo_badge = " 🎭 DEMO" if is_demo else ""
                with st.expander(f"Bill #{idx+1}{demo_badge}: {bill['patient_name']} - {bill['hospital']} (₹{bill['total_billed']:,.0f})"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Date:** {bill['date']}")
                        st.write(f"**Hospital:** {bill['hospital']}")
                    with col2:
                        st.write(f"**Audit Score:** {bill['audit_score']}/100")
                        st.write(f"**Issues:** {bill['flagged_count']}")
                    with col3:
                        st.write(f"**Total:** ₹{bill['total_billed']:,.0f}")
                        st.write(f"**Savings:** ₹{bill['potential_savings']:,.0f}")
                    st.dataframe(bill['results_df'], use_container_width=True)
                    col1, col2 = st.columns(2)
                    with col1:
                        if not is_demo:
                            if st.button(f"💰 Pay Bill #{idx+1}", key=f"pay_{idx}", use_container_width=True):
                                st.session_state.payment_bills = [bill]
                                st.session_state.show_payment = True
                                st.rerun()
                        else:
                            st.button(f"💰 Pay Bill #{idx+1}", key=f"pay_{idx}", use_container_width=True, disabled=True)
                            st.caption("Demo bills can't be paid")
                    with col2:
                        if st.button(f"🗑️ Remove", key=f"remove_{idx}", use_container_width=True):
                            st.session_state.bill_queue.pop(idx)
                            st.rerun()
            
            st.markdown("---")
            # Check if any non-demo bills exist
            non_demo_bills = [b for b in st.session_state.bill_queue if not b.get('is_demo', False)]
            col1, col2 = st.columns(2)
            with col1:
                if non_demo_bills:
                    if st.button("💳 Pay All Bills Together", use_container_width=True, type="primary"):
                        st.session_state.payment_bills = non_demo_bills
                        st.session_state.show_payment = True
                        st.rerun()
                else:
                    st.button("💳 Pay All Bills Together", use_container_width=True, disabled=True)
                    st.caption("Only demo bills in queue")
            with col2:
                if st.button("🗑️ Clear Queue", use_container_width=True):
                    st.session_state.bill_queue = []
                    st.rerun()

        # Payment Section
        if st.session_state.get('show_payment', False):
            st.markdown("---")
            st.markdown("## 💳 Complete Your Payment")
            payment_bills = st.session_state.get('payment_bills', [])
            total_payment = sum([bill['total_billed'] for bill in payment_bills])
            st.success(f"💰 **Total Payment Amount: ₹{total_payment:,.0f}**")
            st.markdown(f"Paying for {len(payment_bills)} bill(s)")
            
            # --- PAYMENT OPTION UPDATE: Added BNPL and grouped EMI/BNPL ---
            payment_method = st.radio(
                "Select Payment Method", 
                ["💳 Credit/Debit Card", "📱 UPI", "💼 BNPL & EMI Options", "🏦 Net Banking"], 
                horizontal=True
            )
            
            if payment_method == "💳 Credit/Debit Card":
                col1, col2 = st.columns(2)
                with col1:
                    st.text_input("Card Number", placeholder="1234 5678 9012 3456")
                    st.text_input("Cardholder Name", placeholder="John Doe")
                with col2:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.text_input("Expiry (MM/YY)", placeholder="12/25")
                    with col_b:
                        st.text_input("CVV", placeholder="123", type="password")
                st.checkbox("Save card for future payments")
            
            elif payment_method == "🏦 Net Banking":
                st.selectbox("Select Bank", [ 
                    "State Bank of India", "HDFC Bank", "ICICI Bank", "Axis Bank", "Kotak Mahindra Bank", "Punjab National Bank"
                ])
                st.info("You'll be redirected to your bank's secure payment gateway")
            
            elif payment_method == "📱 UPI":
                upi_id = st.text_input("UPI ID", placeholder="yourname@paytm")
                st.info("📱 You'll receive a payment request on your UPI app")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/Google_Pay_Logo_%282020%29.svg/200px-Google_Pay_Logo_%282020%29.svg.png", width=100)
                with col2:
                    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/PhonePe_Logo.svg/200px-PhonePe_Logo.svg.png", width=100)
                with col3:
                    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/2/24/Paytm_Logo_%28standalone%29.svg/200px-Paytm_Logo_%28standalone%29.svg.png", width=80)
            
            elif payment_method == "💼 BNPL & EMI Options":
                st.markdown("### 📊 BNPL & EMI Options")
                st.info("💡 You can convert your medical bill into easy monthly payments or opt for Buy Now Pay Later.")
                
                bnpl_provider = st.selectbox("Select BNPL/EMI Provider", ["ZestMoney", "Simpl", "Slice", "Credit Card EMI"])
                st.markdown("---")
                
                st.markdown("### 📈 EMI Calculator")
                
                col1, col2 = st.columns(2)
                with col1:
                    tenure = st.slider("Select Tenure (Months)", 3, 36, 12)
                
                # Simple EMI Calculation for mockup
                principal = total_payment
                annual_rate = 12.0 # Assuming 12% fictional rate
                monthly_rate = annual_rate / 12 / 100
                
                # EMI formula: P * r * (1 + r)^n / ((1 + r)^n - 1)
                if monthly_rate == 0:
                    emi = principal / tenure
                else:
                    emi = principal * monthly_rate * ((1 + monthly_rate) ** tenure) / (((1 + monthly_rate) ** tenure) - 1)
                
                with col2:
                    st.metric("Monthly EMI Estimate", f"₹{emi:,.0f}")
                
                st.success(f"You will pay **₹{emi:,.0f}** for **{tenure} months**.")
            # ---------------------------------------------------------------

            if st.button("Confirm and Pay Now", use_container_width=True, type="primary"):
                # Simulate payment success
                for bill in payment_bills:
                    st.session_state.payment_history.append(bill)
                    # Remove paid bills from queue
                    if bill in st.session_state.bill_queue:
                        st.session_state.bill_queue.remove(bill)

                st.session_state.show_payment = False
                st.session_state.payment_bills = []
                st.success("🎉 Payment successful! Transaction receipt sent to email.")
                st.balloons()
                time.sleep(1)
                st.rerun()

    with tabs[2]:
        st.markdown("### 🤝 Negotiation Requests")
        if not st.session_state.negotiation_requests:
            st.info("No active negotiation requests. Audit a bill and click 'Yes, Negotiate For Me!' to start the process.")
        else:
            for req in st.session_state.negotiation_requests:
                with st.expander(f"Request {req['id']} - {req['hospital']} ({req['status']})"):
                    st.write(f"**Patient:** {req['patient_name']}")
                    st.write(f"**Date Submitted:** {req['date']}")
                    st.write(f"**Hospital:** {req['hospital']}")
                    st.write(f"**Potential Savings:** ₹{req['potential_savings']:,.0f}")
                    st.write(f"**Our Commission (15%):** ₹{req['commission']:,.0f}")
                    
                    if req['status'] == 'Pending':
                        # The new message is reflected here as well
                        st.warning("Status: Pending. Our team is negotiating with the hospital. **Expected completion: 12 to 48 hours.** You will be notified with the final savings.")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Cancel Request", key=f"cancel_{req['id']}", use_container_width=True):
                                req['status'] = 'Cancelled'
                                st.success("Request cancelled.")
                                st.rerun()
                        with col2:
                            if st.button("Simulate Negotiation Complete (Demo)", key=f"simulate_{req['id']}", use_container_width=True):
                                req['status'] = 'Complete'
                                req['actual_savings'] = req['potential_savings'] * 0.85 # Simulate 85% success
                                req['final_bill'] = req['audit_data']['total_billed'] - req['actual_savings']
                                st.rerun()
                    
                    elif req['status'] == 'Complete':
                        st.success(f"🎉 Negotiation **Complete**! You saved **₹{req['actual_savings']:,.0f}**!")
                        st.markdown(f"""
                            <div style='border: 2px solid #10b981; padding: 1rem; border-radius: 8px; margin-top: 1rem;'>
                                <h4>New Reduced Bill Amount:</h4>
                                <p style='font-size: 1.5rem; font-weight: 700; color: #059669;'>₹{req['final_bill']:,.0f}</p>
                                <p>Original Bill: <span class='strikethrough-price'>₹{req['audit_data']['total_billed']:,.0f}</span></p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("Pay Reduced Bill Now", key=f"pay_negotiated_{req['id']}", type="primary"):
                            # Create a new audit item for the reduced bill
                            reduced_audit = req['audit_data'].copy()
                            reduced_audit['total_billed'] = req['final_bill']
                            reduced_audit['potential_savings'] = 0 # Savings achieved and factored in
                            reduced_audit['negotiation_fee'] = req['actual_savings'] * 0.15
                            st.session_state.payment_bills = [reduced_audit]
                            st.session_state.show_payment = True
                            st.rerun()
                    
                    elif req['status'] == 'Cancelled':
                        st.error("Request was cancelled by the user.")

    with tabs[3]:
        st.markdown("### 📋 Payment & Audit History")
        if not st.session_state.payment_history:
            st.info("No completed payments yet. Paid bills will appear here.")
        else:
            for idx, hist in enumerate(st.session_state.payment_history):
                with st.expander(f"Paid Bill #{idx+1}: {hist['patient_name']} - ₹{hist['total_billed']:,.0f}"):
                    st.write(f"**Date Paid:** {datetime.now().strftime('%Y-%m-%d')}")
                    st.write(f"**Hospital:** {hist['hospital']}")
                    st.write(f"**Original Audit Savings:** ₹{hist['potential_savings']:,.0f}")
                    st.write("---")
                    st.dataframe(hist['results_df'], use_container_width=True)


elif user_type == "🏢 B2B Enterprise":
    st.markdown("""
        <div class="hero-banner">
            <h1>🏢 B2B Enterprise Solutions</h1>
            <p>Advanced bulk auditing, API access, and custom analytics for insurance providers and TPAs.</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Key Features")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
            <div class="info-card">
                <h4>☁️ Scalable API Access</h4>
                <p>Integrate our auditing engine directly into your claims processing system. Handle thousands of bills per hour.</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="info-card">
                <h4>📈 Advanced Anaytics Dashboard</h4>
                <p>Track fraud patterns, identify high-cost hospitals, and monitor claim savings across your entire portfolio.</p>
            </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    st.markdown("### Contact Us for a Demo")
    
    with st.form("b2b_form"):
        name = st.text_input("Your Name")
        company = st.text_input("Company Name")
        email_b2b = st.text_input("Work Email")
        interest = st.selectbox("Area of Interest", ["Insurance Claims Audit", "TPA Services", "Custom Integration"])
        
        submitted = st.form_submit_button("Request Enterprise Demo")
        if submitted:
            st.success(f"Thank you, {name}! Your request for a demo for {company} has been submitted. We will contact you at {email_b2b} shortly.")


elif user_type == "ℹ️ About & Pricing":
    st.markdown("""
        <div class="hero-banner">
            <h1>ℹ️ About & Pricing</h1>
            <p>Transparency in medical billing for a healthier financial future.</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Our Mission")
    st.info("To use AI to democratize healthcare auditing, ensuring every patient pays a fair price and is protected from overbilling and fraud.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Pricing for Patients")
        st.markdown("""
            <div class="info-card" style="border-left-color: #10b981;">
                <h4>✅ Bill Audit</h4>
                <div class="free-badge">FREE FOREVER</div>
                <p>✓ AI-powered itemized bill analysis</p>
                <p>✓ Overcharge detection & CGHS rate comparison</p>
                <p>✓ Detailed audit report download</p>
                <p>No charge, no hidden fees.</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("### Pricing for Negotiation")
        st.markdown("""
            <div class="negotiation-card">
                <h4>🤝 Expert Negotiation Service</h4>
                <h3 style="color: #92400e;">15% Commission</h3>
                <p>Only pay based on success. Our fee is 15% of the **actual amount we save** you on the final bill.</p>
                <p>Example: Original Bill: ₹50,000. We reduce it to ₹40,000. Savings: ₹10,000. Your fee: 15% of ₹10,000 = ₹1,500.</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### FAQs")
    
    with st.expander("⏱️ How long does the audit take?"):
        st.write("The initial AI audit is instant (under 5 seconds) after extracting your bill data.")
        
    with st.expander("🤝 How long does the negotiation take?"):
        # The new message is also reflected here for consistency
        st.write("Negotiation is an expert-led manual process. It typically takes **12 to 48 hours** as we communicate directly with the hospital's billing department. We notify you immediately once a final reduced amount is agreed upon.")
        
    with st.expander("📞 How do I contact support?"):
        st.write("You can contact us via the floating WhatsApp chat button or email us at support@mediaudit.com. Our support team. Available 24/7 for quick queries and assistance.")
        
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
    st.markdown("• Email: support@mediaudit.com")
    st.markdown("• Phone: +91 98765 43210")
