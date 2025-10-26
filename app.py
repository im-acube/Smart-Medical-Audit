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
    page_title="MediAudit",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
        /* Hero Banner */
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
        
        /* Sidebar */
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
        
        /* Equal Size Cards */
        .equal-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-left: 4px solid #3b82f6;
            margin-bottom: 1rem;
            min-height: 200px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            min-height: 150px;
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
        
        /* Savings Highlight */
        .savings-card {
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            border: 3px solid #f59e0b;
            padding: 2rem;
            border-radius: 12px;
            text-align: center;
        }
        
        .savings-value {
            font-size: 3.5rem;
            font-weight: 800;
            color: #92400e;
        }
        
        /* Audit Categories */
        .audit-category {
            background: #fff7ed;
            border: 2px solid #fb923c;
            padding: 1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            min-height: 120px;
        }
        
        .audit-category-pass {
            background: #d1fae5;
            border: 2px solid #10b981;
        }
        
        .audit-category-fail {
            background: #fee2e2;
            border: 2px solid #ef4444;
        }
        
        /* Negotiation */
        .negotiation-card {
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            border: 3px solid #f59e0b;
            padding: 1.5rem;
            border-radius: 12px;
            margin: 1rem 0;
        }
        
        /* WhatsApp Float */
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
        
        /* Chatbot */
        .chatbot-float {
            position: fixed;
            bottom: 100px;
            right: 30px;
            z-index: 1000;
        }
        
        .chatbot-button {
            background: #3b82f6;
            color: white;
            padding: 15px 20px;
            border-radius: 50px;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
            cursor: pointer;
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
    </style>
""", unsafe_allow_html=True)

# WhatsApp & Chatbot Float Buttons
st.markdown("""
    <div class="whatsapp-float">
        <a href="https://wa.me/917877797505?text=Hi%20MediAudit,%20I%20need%20help%20with%20my%20medical%20bill" 
           target="_blank" class="whatsapp-button">
            💬 Chat on WhatsApp
        </a>
    </div>
    <div class="chatbot-float">
        <div class="chatbot-button" onclick="alert('Chatbot: Hi! How can I help you today?\\n\\n1. Start an audit\\n2. Check audit status\\n3. Contact support\\n\\nCall us: +91 7877797505')">
            🤖 Need Help?
        </div>
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
    # Logo
    if os.path.exists("logo.png"):
        st.image("logo.png", width=150)
    else:
        st.markdown("### 🏥 MediAudit")
    
    st.markdown("*Your Partner Against Unfair Bills*")
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
    st.markdown("📱 +91 7877797505")
    st.markdown("📧 support@mediaudit.com")

# Main content
if user_type == "🏠 Home":
    st.markdown("""
        <div class="hero-banner">
            <h1>🏥 MediAudit</h1>
            <p>Your Expert Partner Against Unfair Hospital Bills</p>
        </div>
    """, unsafe_allow_html=True)
    
    # What is MediAudit
    st.markdown("### 🛡️ What is MediAudit?")
    st.markdown("""
        <div class="equal-card">
            <p style="font-size: 1.1rem; line-height: 1.8;">
                Your expert partner against unfair hospital bills. We blend advanced <strong>AI analysis</strong> 
                with <strong>human medical auditing expertise</strong> to find and fix costly errors, 
                ensuring you only pay what's fair.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Start Free Audit CTA
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Your Free Audit Now", use_container_width=True, type="primary"):
            st.session_state.user_type_selector = "👤 Patient Portal"
            st.rerun()
    
    st.markdown("---")
    
    # What We Audit For - Equal Sized Cards
    st.markdown("### 🎯 What We Audit For - 5 Types of Overcharges")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown("""
            <div class="equal-card" style="text-align: center;">
                <h3>💊</h3>
                <h4 style="font-size: 1rem;">Inflated Consumables</h4>
                <p style="font-size: 0.85rem;">Overpriced syringes, gloves, masks, and basic supplies</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="equal-card" style="text-align: center;">
                <h3>🔄</h3>
                <h4 style="font-size: 1rem;">Duplicate Billing</h4>
                <p style="font-size: 0.85rem;">Same service charged multiple times incorrectly</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class="equal-card" style="text-align: center;">
                <h3>📈</h3>
                <h4 style="font-size: 1rem;">Upcoding</h4>
                <p style="font-size: 0.85rem;">Basic service billed as premium procedure</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
            <div class="equal-card" style="text-align: center;">
                <h3>📦</h3>
                <h4 style="font-size: 1rem;">Unbundling</h4>
                <p style="font-size: 0.85rem;">Package services split to inflate total cost</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown("""
            <div class="equal-card" style="text-align: center;">
                <h3>⚠️</h3>
                <h4 style="font-size: 1rem;">Other Overcharges</h4>
                <p style="font-size: 0.85rem;">Rate violations, unauthorized charges, and more</p>
            </div>
        """, unsafe_handle_html=True)
    
    st.markdown("---")
    
    # Our Services
    st.markdown("### 💼 Our Services")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div class="equal-card">
                <h3>🆓 FREE Bill Audit</h3>
                <p>✓ AI-powered analysis</p>
                <p>✓ Detect all 5 overcharge types</p>
                <p>✓ Detailed audit report</p>
                <p>✓ CGHS rate comparison</p>
                <p>✓ Instant results</p>
                <p>✓ No hidden charges</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="negotiation-card" style="min-height: 200px;">
                <h3>🤝 Expert Negotiation Service</h3>
                <p>✓ We negotiate on your behalf</p>
                <p>✓ Deal with hospital billing dept</p>
                <p>✓ Get overcharges reduced/removed</p>
                <p>✓ Success-based pricing only</p>
                <p style="font-weight: 700; color: #92400e; margin-top: 1rem;">
                    Pay only when we save you money!
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    # Platform Impact
    st.markdown("### 📊 Our Impact")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-value">₹2.4Cr</div>
                <div class="metric-label">Total Savings</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-value">50K+</div>
                <div class="metric-label">Bills Audited</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-value">22%</div>
                <div class="metric-label">Avg Savings</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-value">24/7</div>
                <div class="metric-label">Support</div>
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
            contact_number = st.text_input("Contact Number", placeholder="+91 7877797505")
            email = st.text_input("Email", placeholder="patient@email.com")
        
        # Enterprise Linking
        st.markdown("---")
        col1, col2 = st.columns([2, 1])
        with col1:
            employer_id = st.text_input("Employer/Enterprise ID (Optional)", 
                                       placeholder="Enter your company's enterprise ID to link",
                                       help="If your employer uses MediAudit for employee benefits, enter the ID here")
        with col2:
            if st.button("🔗 Link to Enterprise", use_container_width=True):
                if employer_id:
                    st.success(f"✓ Linked to Enterprise: {employer_id}")
                else:
                    st.warning("Please enter Employer ID")
        
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
            st.info("**We Check For:**\n- Inflated Consumables\n- Duplicate Billing\n- Upcoding\n- Unbundling\n- Other Overcharges")
        
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
                # Audit Progress
                st.markdown("### 🔍 Auditing Your Bill...")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                audit_steps = [
                    ("Checking for Inflated Consumables...", 20),
                    ("Detecting Duplicate Billing...", 40),
                    ("Analyzing for Upcoding...", 60),
                    ("Checking Unbundling Practices...", 80),
                    ("Scanning for Other Overcharges...", 100)
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
                    "Unbundling": 0,
                    "Other Overcharges": 0
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
                        
                        if amount > rate * 1.15:
                            status = "Overcharged"
                            savings = amount - rate
                            potential_savings += savings
                            
                            if any(word in item for word in ['syringe', 'glove', 'mask', 'cotton', 'bandage', 'gauze']):
                                overcharge_type = "Inflated Consumables"
                                overcharge_types["Inflated Consumables"] += 1
                            elif amount > rate * 2:
                                overcharge_type = "Upcoding"
                                overcharge_types["Upcoding"] += 1
                            else:
                                overcharge_type = "Other Overcharges"
                                overcharge_types["Other Overcharges"] += 1
                            
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
                
                # Store audit
                st.session_state.current_audit = {
                    'patient_name': patient_name,
                    'hospital': hospital,
                    'contact': contact_number,
                    'email': email,
                    'employer_id': employer_id if employer_id else None,
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                    'results_df': results_df,
                    'total_billed': total_billed,
                    'total_standard': total_standard,
                    'potential_savings': potential_savings,
                    'flagged_count': flagged_count,
                    'alerts': alerts,
                    'overcharge_types': overcharge_types
                }
                
                st.success("✅ Audit Complete!")
                st.markdown("---")
                
                # MAIN FOCUS: Total Bill and Savings
                st.markdown("### 💰 Your Bill Summary")
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown(f"""
                        <div class="metric-card" style="min-height: 180px;">
                            <h4 style="color: #64748b; margin-bottom: 1rem;">Total Bill Amount</h4>
                            <div class="metric-value">₹{total_billed:,.0f}</div>
                            <p style="color: #64748b; margin-top: 1rem; font-size: 0.9rem;">{len(results_df)} items checked</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                        <div class="savings-card" style="min-height: 180px;">
                            <h4 style="color: #92400e; margin-bottom: 1rem;">Potential Savings</h4>
                            <div class="savings-value">₹{potential_savings:,.0f}</div>
                            <p style="color: #92400e; margin-top: 1rem; font-size: 0.9rem; font-weight: 600;">{flagged_count} items with errors found</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                # Overcharge Analysis - 5 Types
                st.markdown("### 🔍 Overcharge Analysis (5 Types)")
                
                col1, col2, col3, col4, col5 = st.columns(5)
                
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
                
                with col5:
                    status_class = "audit-category-pass" if overcharge_types["Other Overcharges"] == 0 else "audit-category-fail"
                    st.markdown(f"""
                        <div class="audit-category {status_class}">
                            <h4>⚠️ Other Overcharges</h4>
                            <p>Found: {overcharge_types["Other Overcharges"]}</p>
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
                            <p><strong>Total Bill:</strong> ₹{total_billed:,.0f}</p>
                            <p><strong>Potential Savings:</strong> ₹{potential_savings:,.0f}</p>
                            <p>Our experts can negotiate with {hospital} on your behalf</p>
                            <p style="font-weight: 700; font-size: 1.1rem; color: #92400e; margin-top: 1rem;">
                                Success-based pricing - You pay only when we save you money!
                            </p>
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
                                'total_billed': total_billed,
                                'potential_savings': potential_savings,
                                'status': 'Pending',
                                'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                                'audit_data': st.session_state.current_audit
                            }
                            st.session_state.negotiation_requests.append(negotiation_request)
                            st.success("✅ Negotiation request submitted! Our team will resolve this in 1-3 business days.")
                            st.balloons()
                    
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
            # Demo audit with 5 types of overcharges
            demo_patient_name = "Demo Patient"
            demo_hospital = "Apollo Hospital"
            
            st.markdown("### 🔍 Running Demo Audit...")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            audit_steps = [
                ("Checking for Inflated Consumables...", 20),
                ("Detecting Duplicate Billing...", 40),
                ("Analyzing for Upcoding...", 60),
                ("Checking Unbundling Practices...", 80),
                ("Scanning for Other Overcharges...", 100)
            ]
            
            for step, progress in audit_steps:
                status_text.text(step)
                progress_bar.progress(progress)
                time.sleep(0.8)
            
            status_text.empty()
            progress_bar.empty()
            
            # Demo results
            overcharge_types = {
                "Inflated Consumables": 2,
                "Duplicate Billing": 1,
                "Upcoding": 1,
                "Unbundling": 0,
                "Other Overcharges": 1
            }
            
            total_billed = 85000
            potential_savings = 18000
            total_standard = 67000
            flagged_count = 5
            
            demo_results = [
                {"Service": "Room Rent", "Billed (₹)": 8500, "Standard (₹)": 4000, 
                 "Status": "Overcharged", "Type": "Upcoding", "Comments": "Save ₹4,500"},
                {"Service": "Surgical Gloves", "Billed (₹)": 4500, "Standard (₹)": 800, 
                 "Status": "Overcharged", "Type": "Inflated Consumables", "Comments": "Save ₹3,700"},
                {"Service": "Blood Test - CBC", "Billed (₹)": 3000, "Standard (₹)": 1500, 
                 "Status": "Overcharged", "Type": "Duplicate Billing", "Comments": "Save ₹1,500"},
                {"Service": "Injection Syringe Pack", "Billed (₹)": 2500, "Standard (₹)": 500, 
                 "Status": "Overcharged", "Type": "Inflated Consumables", "Comments": "Save ₹2,000"},
                {"Service": "Admin Processing Fee", "Billed (₹)": 6300, "Standard (₹)": 0, 
                 "Status": "Overcharged", "Type": "Other Overcharges", "Comments": "Save ₹6,300"}
            ]
            
            results_df = pd.DataFrame(demo_results)
            
            st.session_state.current_audit = {
                'patient_name': demo_patient_name,
                'hospital': demo_hospital,
                'contact': '+91 7877797505',
                'email': 'demo@mediaudit.com',
                'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'results_df': results_df,
                'total_billed': total_billed,
                'total_standard': total_standard,
                'potential_savings': potential_savings,
                'flagged_count': flagged_count,
                'overcharge_types': overcharge_types,
                'is_demo': True
            }
            
            st.success("✅ Demo Audit Complete!")
            st.markdown("---")
            
            # Demo Results
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown(f"""
                    <div class="metric-card" style="min-height: 180px;">
                        <h4 style="color: #64748b; margin-bottom: 1rem;">Total Bill Amount</h4>
                        <div class="metric-value">₹{total_billed:,.0f}</div>
                        <p style="color: #64748b; margin-top: 1rem; font-size: 0.9rem;">8 items checked</p>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                    <div class="savings-card" style="min-height: 180px;">
                        <h4 style="color: #92400e; margin-bottom: 1rem;">Potential Savings</h4>
                        <div class="savings-value">₹{potential_savings:,.0f}</div>
                        <p style="color: #92400e; margin-top: 1rem; font-size: 0.9rem; font-weight: 600;">{flagged_count} items with errors found</p>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("### 🔍 Demo Overcharge Analysis")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.markdown(f"""
                    <div class="audit-category audit-category-fail">
                        <h4>💊 Inflated Consumables</h4>
                        <p>Found: 2</p>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                    <div class="audit-category audit-category-fail">
                        <h4>🔄 Duplicate Billing</h4>
                        <p>Found: 1</p>
                    </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                    <div class="audit-category audit-category-fail">
                        <h4>📈 Upcoding</h4>
                        <p>Found: 1</p>
                    </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                    <div class="audit-category audit-category-pass">
                        <h4>📦 Unbundling</h4>
                        <p>Found: 0</p>
                    </div>
                """, unsafe_allow_html=True)
            
            with col5:
                st.markdown(f"""
                    <div class="audit-category audit-category-fail">
                        <h4>⚠️ Other</h4>
                        <p>Found: 1</p>
                    </div>
                """, unsafe_allow_html=True)
            
            st.dataframe(results_df, use_container_width=True)
    
    with tabs[1]:
        st.markdown("### 🗂️ Bill Queue & Payment")
        
        if not st.session_state.bill_queue:
            st.info("📭 No bills in queue. Audit a bill and add it to queue!")
        else:
            total_queue = sum([b['total_billed'] for b in st.session_state.bill_queue])
            
            st.markdown(f"""
                <div class="equal-card" style="background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%); border-color: #fb923c;">
                    <h3>📋 {len(st.session_state.bill_queue)} Bills in Queue</h3>
                    <p style="font-size: 1.5rem; font-weight: 700; color: #1e3a8a;">Total: ₹{total_queue:,.0f}</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Display queued bills
            for idx, bill in enumerate(st.session_state.bill_queue):
                is_demo = bill.get('is_demo', False)
                demo_badge = " 🎭 DEMO" if is_demo else ""
                
                with st.expander(f"Bill #{idx+1}{demo_badge}: {bill['patient_name']} - {bill['hospital']} (₹{bill['total_billed']:,.0f})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Total Bill:** ₹{bill['total_billed']:,.0f}")
                        st.write(f"**Potential Savings:** ₹{bill['potential_savings']:,.0f}")
                    with col2:
                        st.write(f"**Date:** {bill['date']}")
                        st.write(f"**Errors Found:** {bill['flagged_count']}")
                    
                    st.dataframe(bill['results_df'], use_container_width=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if not is_demo:
                            if st.button(f"💰 Pay Bill #{idx+1}", key=f"pay_{idx}", use_container_width=True):
                                st.session_state.payment_bills = [bill]
                                st.session_state.show_payment = True
                                st.rerun()
                        else:
                            st.button(f"💰 Pay Demo", key=f"pay_{idx}", use_container_width=True, disabled=True)
                    
                    with col2:
                        if st.button(f"🗑️ Remove", key=f"remove_{idx}", use_container_width=True):
                            st.session_state.bill_queue.pop(idx)
                            st.rerun()
            
            st.markdown("---")
            
            non_demo_bills = [b for b in st.session_state.bill_queue if not b.get('is_demo', False)]
            
            col1, col2 = st.columns(2)
            with col1:
                if non_demo_bills:
                    if st.button("💳 Pay All Bills Together", use_container_width=True, type="primary"):
                        st.session_state.payment_bills = non_demo_bills
                        st.session_state.show_payment = True
                        st.rerun()
                else:
                    st.button("💳 Pay All", use_container_width=True, disabled=True)
            
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
            total_savings_potential = sum([bill['potential_savings'] for bill in payment_bills])
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                    <div class="metric-card">
                        <h4>Total Amount to Pay</h4>
                        <div class="metric-value">₹{total_payment:,.0f}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                    <div class="savings-card">
                        <h4>Potential Savings</h4>
                        <div class="savings-value" style="font-size: 2.5rem;">₹{total_savings_potential:,.0f}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown(f"### Select Payment Method")
            
            payment_method = st.radio(
                "Choose your preferred payment option",
                ["💳 Credit/Debit Card", "📱 UPI Payment", "💼 EMI Options", "🛒 Buy Now Pay Later (BNPL)"],
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
                
            elif payment_method == "📱 UPI Payment":
                upi_id = st.text_input("UPI ID", placeholder="yourname@paytm")
                st.info("📱 You'll receive a payment request on your UPI app")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("**Google Pay**")
                with col2:
                    st.markdown("**PhonePe**")
                with col3:
                    st.markdown("**Paytm**")
                
            elif payment_method == "💼 EMI Options":
                st.markdown("### 📊 Convert to EMI - Medical Bill Payment")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    bill_amount_emi = st.number_input("Bill Amount (₹)", min_value=1000, 
                                                value=int(total_payment), step=1000, disabled=True)
                
                with col2:
                    emi_tenure = st.selectbox("Tenure", 
                                            ["3 months", "6 months", "9 months", "12 months", "18 months", "24 months"])
                
                with col3:
                    interest_rate = st.number_input("Interest Rate (% p.a.)", min_value=0.0, max_value=30.0, value=12.0)
                
                # Calculate EMI
                tenure_months = int(emi_tenure.split()[0])
                monthly_rate = interest_rate / (12 * 100)
                
                if monthly_rate > 0:
                    emi_amount = (bill_amount_emi * monthly_rate * (1 + monthly_rate)**tenure_months) / ((1 + monthly_rate)**tenure_months - 1)
                else:
                    emi_amount = bill_amount_emi / tenure_months
                
                total_payment_emi = emi_amount * tenure_months
                total_interest = total_payment_emi - bill_amount_emi
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">₹{emi_amount:,.0f}</div>
                            <div class="metric-label">Monthly EMI</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">₹{total_payment_emi:,.0f}</div>
                            <div class="metric-label">Total Payment</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">₹{total_interest:,.0f}</div>
                            <div class="metric-label">Total Interest</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("#### 🏦 EMI Partners")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("""
                        <div class="equal-card">
                            <h4>Bajaj Finserv</h4>
                            <p>✓ 0% for 3 months</p>
                            <p>✓ Instant approval</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("""
                        <div class="equal-card">
                            <h4>HDFC Bank</h4>
                            <p>✓ Flexible tenure</p>
                            <p>✓ Low interest rates</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown("""
                        <div class="equal-card">
                            <h4>Credit Card EMI</h4>
                            <p>✓ Quick conversion</p>
                            <p>✓ No paperwork</p>
                        </div>
                    """, unsafe_allow_html=True)
            
            elif payment_method == "🛒 Buy Now Pay Later (BNPL)":
                st.markdown("### 🛒 Buy Now Pay Later Options")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("""
                        <div class="equal-card">
                            <h4>LazyPay</h4>
                            <p>✓ Pay in 30 days</p>
                            <p>✓ No interest</p>
                            <p>✓ Instant approval</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("""
                        <div class="equal-card">
                            <h4>Simpl</h4>
                            <p>✓ Split into 3 parts</p>
                            <p>✓ Zero interest</p>
                            <p>✓ Auto-approval</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown("""
                        <div class="equal-card">
                            <h4>ZestMoney</h4>
                            <p>✓ Up to 3 months</p>
                            <p>✓ Low processing fee</p>
                            <p>✓ Digital KYC</p>
                        </div>
                    """, unsafe_allow_html=True)
            
            # Final payment button
            st.markdown("---")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                agree = st.checkbox("I agree to the Terms & Conditions and authorize this payment")
            
            with col2:
                if st.button("💳 Pay Now", use_container_width=True, type="primary", disabled=not agree):
                    with st.spinner("Processing payment..."):
                        time.sleep(2)
                    
                    for bill in payment_bills:
                        payment_record = bill.copy()
                        payment_record['payment_date'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        payment_record['payment_method'] = payment_method
                        payment_record['payment_status'] = 'Completed'
                        st.session_state.payment_history.append(payment_record)
                    
                    st.session_state.bill_queue = [b for b in st.session_state.bill_queue if b not in payment_bills]
                    st.session_state.show_payment = False
                    
                    st.success("✅ Payment Successful!")
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
    
    with tabs[2]:
        st.markdown("### 🤝 Negotiation Requests")
        
        if not st.session_state.negotiation_requests:
            st.info("📭 No negotiation requests yet.")
        else:
            for idx, req in enumerate(st.session_state.negotiation_requests):
                status_color = {'Pending': '🟡', 'In Progress': '🔵', 'Completed': '🟢'}
                
                with st.expander(f"{status_color.get(req['status'], '⚪')} Request #{req['id']} ({req['status']})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Patient:** {req['patient_name']}")
                        st.write(f"**Hospital:** {req['hospital']}")
                        st.write(f"**Total Bill:** ₹{req['total_billed']:,.0f}")
                    
                    with col2:
                        st.write(f"**Potential Savings:** ₹{req['potential_savings']:,.0f}")
                        st.write(f"**Status:** {req['status']}")
                        st.write(f"**Date:** {req['date']}")
                    
                    st.markdown("---")
                    
                    if req['status'] == 'Pending':
                        st.info("📞 Our expert team has taken up your case and will resolve this in 1-3 business days. We'll keep you updated!")
                    elif req['status'] == 'In Progress':
                        st.warning("🔄 Our team is actively negotiating with the hospital.")
                    elif req['status'] == 'Completed':
                        actual_saved = req.get('actual_saved', req['potential_savings'] * 0.85)
                        st.success(f"✅ Success! Actual Savings: ₹{actual_saved:,.0f}")
    
    with tabs[3]:
        st.markdown("### 📋 Payment History")
        
        if not st.session_state.payment_history:
            st.info("📭 No payment history yet.")
        else:
            for record in st.session_state.payment_history:
                st.markdown(f"**{record['date']}** - {record['hospital']} - ₹{record['total_billed']:,.0f} - {record['payment_status']}")

# Footer
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("**MediAudit**")
    st.markdown("*Against Unfair Bills*")

with col2:
    st.markdown("**Services**")
    st.markdown("• Free Audit")
    st.markdown("• Negotiation")

with col3:
    st.markdown("**Links**")
    st.markdown("• Privacy Policy")
    st.markdown("• Terms")

with col4:
    st.markdown("**Contact**")
    st.markdown("📱 +91 7877797505")
    st.markdown("📧 support@mediaudit.com")1:
                    st.markdown(f"""
                        <div class="metric-card" style="
