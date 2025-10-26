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

# --- Configuration ---

# Global contact information
whatsapp_number = "919876543210"
mobile_number_display = "+91 9876543210"
# Using a publicly hosted URL for maximum robustness in displaying the logo
logo_fallback_url = "https://i.imgur.com/gK1qW8k.png" 

# Page config
st.set_page_config(
    page_title="MediAudit Pro",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Polishing and Alignment ---
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
        
        /* Card styling - Ensures all cards in a row are same height (Crucial for homepage alignment) */
        .info-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-left: 4px solid #3b82f6;
            margin-bottom: 1rem;
            height: 100%; /* Key for equal height */
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            text-align: center;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            height: 100%;
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
        
        /* Negotiation Card */
        .negotiation-card {
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            border: 3px solid #f59e0b;
            padding: 1.5rem;
            border-radius: 12px;
            margin: 1rem 0;
            height: 100%;
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
    </style>
""", unsafe_allow_html=True)

# WhatsApp Chatbot Float Button
st.markdown(f"""
    <div class="whatsapp-float">
        <a href="https://wa.me/{whatsapp_number}?text=Hi%20MediAudit%20Pro,%20I%20need%20help%20with%20my%20medical%20bill" 
           target="_blank" class="whatsapp-button">
            💬 Chat on WhatsApp
        </a>
    </div>
""", unsafe_allow_html=True)

# --- Helper Functions ---

@st.cache_data
def load_reference_data():
    """Loads placeholder CGHS rate data."""
    # Placeholder for standard rates for demo purposes
    return pd.DataFrame({
        "Service": ["Room Rent", "Doctor Fees", "Lab Test", "Surgery", "ICU Charges", "CT Scan", "MRI", "X-Ray"],
        "Rate (₹)": [4000, 2500, 1500, 50000, 8000, 3000, 5000, 800]
    })

def normalize_text(s):
    """Normalize text for fuzzy matching."""
    if pd.isna(s): return ""
    return str(s).strip().lower()

def fuzzy_match_service(service, cghs_services, cutoff=0.70):
    """Fuzzy matches a billed service against known standard rates."""
    if not service: return None, 0.0
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
    """Basic extraction of service/amount pairs from raw text lines."""
    items = []
    for line in lines:
        line = line.strip()
        if not line: continue
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

def extract_bill_items(uploaded, manual_txt):
    """A robust placeholder for bill item extraction."""
    if manual_txt:
        items = text_to_items_from_lines(manual_txt.splitlines())
        if items:
            return pd.DataFrame(items, columns=["Item", "Amount (₹)"])
    
    # Placeholder for file processing (actual implementation requires full setup)
    if uploaded:
        # Simulate extraction from file
        return pd.DataFrame([
            ["Room Rent (Single)", 9000.0], 
            ["Doctor Consultation", 3500.0], 
            ["Surgical Consumables", 5000.0], 
            ["Lab Test (Full Panel)", 1800.0]
        ], columns=["Item", "Amount (₹)"])
        
    return pd.DataFrame(columns=["Item", "Amount (₹)"])

def detect_overcharge_type(item_name, amount, standard_rate):
    """Detect type of overcharge based on patterns"""
    item_lower = item_name.lower()
    
    # Inflated Consumables
    if any(word in item_lower for word in ['syringe', 'gloves', 'mask', 'cotton', 'bandage', 'gauze', 'consumables']):
        if standard_rate > 0 and amount > standard_rate * 1.5:
             return "Inflated Consumables"
    
    # Upcoding (if the difference is huge)
    if standard_rate > 0 and amount > standard_rate * 2:
         return "Upcoding / Excessive Charge"
    
    return "Other Overcharging"

# --- Session State Initialization ---
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
if 'payment_data' not in st.session_state:
    st.session_state.payment_data = {}
if 'bill_queue' not in st.session_state:
    st.session_state.bill_queue = []

# --- Sidebar ---
with st.sidebar:
    # Robust HTML approach for logo display
    logo_html = f"""
    <div style="text-align: center; margin-bottom: 1rem;">
        <img src="{logo_fallback_url}" alt="MediAudit Pro Logo" style="width: 100%; max-width: 180px; height: auto; border-radius: 8px;">
        <p style="font-size: 1rem; color: #334155; margin-top: 0.5rem; font-weight: 500;">Smart Medical Bill Auditing</p>
    </div>
    """
    st.markdown(logo_html, unsafe_allow_html=True)
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
            st.metric("Total Audits", str(len(st.session_state.payment_history) + len(st.session_state.negotiation_requests) + len(st.session_state.bill_queue)))
        with col2:
            st.metric("Cases in Negotiation", str(len([r for r in st.session_state.negotiation_requests if r['status'] == 'Pending'])))
    
    st.markdown("---")
    st.markdown("### 💬 Quick Help")
    st.text_area("Your message...", height=70, disabled=True, 
                 placeholder="Chatbot in beta. Use WhatsApp for urgent queries.")
    st.button("Send", use_container_width=True, disabled=True)
    st.markdown("---")
    st.markdown(f"**Mobile:** {mobile_number_display}")
    st.markdown("📧 support@mediaudit.com")

# --- Main Content ---

if user_type == "🏠 Home":
    st.markdown("""
        <div class="hero-banner">
            <h1>🏥 MediAudit Pro</h1>
            <p>AI-Powered Medical Bill Auditing - Detect Overcharges & Save Money</p>
            <p style="font-size: 1rem; margin-top: 1rem;">✓ Free Audits | ✓ Expert Negotiation | ✓ WhatsApp Support</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 💡 What is MediAudit?")
    st.info("Your expert partner against unfair hospital bills. We blend advanced AI analysis with human medical auditing expertise to find and fix costly errors, ensuring you only pay what's fair.")
    
    col_btn, _ = st.columns([1, 4])
    with col_btn:
        if st.button("🚀 Start your free audit now", use_container_width=True, type="primary"):
            st.session_state.user_type_selector = "👤 Patient Portal"
            st.rerun()

    st.markdown("---")
    st.markdown("### 🎯 Types of Overcharging We Audit For")
    
    # 5 columns for 5 overcharge types
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown("""
            <div class="info-card" style="border-left: 4px solid #ef4444;">
                <h3>💊 Inflated Consumables</h3>
                <p>Overpriced syringes, gloves, masks, and basic supplies.</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="info-card" style="border-left: 4px solid #f97316;">
                <h3>🔄 Duplicate Billing</h3>
                <p>Charging for the same service or item multiple times.</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class="info-card" style="border-left: 4px solid #eab308;">
                <h3>📈 Upcoding</h3>
                <p>Billing a basic service as a more expensive, premium procedure.</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
            <div class="info-card" style="border-left: 4px solid #22c55e;">
                <h3>📦 Unbundling</h3>
                <p>Splitting package services into separate billable items to inflate cost.</p>
            </div>
        """, unsafe_allow_html=True)

    with col5: 
        st.markdown("""
            <div class="info-card" style="border-left: 4px solid #14b8a6;">
                <h3>❓ Other Overcharging</h3>
                <p>Any item or service billed at an unusually high price not matching standard rates.</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 💼 Our Services")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div class="info-card" style="border-left: 4px solid #06b6d4;">
                <h3>🆓 FREE Bill Audit</h3>
                <p>✓ AI-powered analysis</p>
                <p>✓ Detect all 5 overcharge types</p>
                <p>✓ Detailed audit report</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="negotiation-card">
                <h3>🤝 Expert Negotiation Service</h3>
                <p>✓ We negotiate with the hospital on your behalf.</p>
                <p>✓ Get overcharges reduced or removed.</p>
                <p style="font-weight: 700; font-size: 1.1rem; color: #92400e;">
                    You pay only on **actual savings achieved**.
                </p>
                <p style="font-size: 0.9rem;">We charge a success fee based on the amount we save you.</p>
            </div>
        """, unsafe_allow_html=True)

# --- Patient Portal ---
elif user_type == "👤 Patient Portal":
    
    # 1. Check for active payment session FIRST
    if st.session_state.get('show_payment', False):
        # ----------------------------------------------------------------------
        # --- Payment Gateway Section (FIXED: Moved to the top of the tab) ---
        # ----------------------------------------------------------------------
        st.markdown("---")
        st.markdown("## 💳 Complete Your Payment")
        
        payment_bills = st.session_state.get('payment_bills', [])
        
        # Logic to set payment totals (for negotiation flow or direct payment)
        pd_data = st.session_state.get('payment_data', {})
        if 'total_to_pay' in pd_data:
            # From resolved negotiation
            total_payment = pd_data['total_to_pay']
            hospital_total = pd_data['hospital_total']
            commission_total = pd_data['commission_total']
            source = 'Negotiated'
        else:
            # Direct payment after audit (Original Bill) or from queue
            total_payment = sum([bill['total_billed'] for bill in payment_bills])
            hospital_total = total_payment
            commission_total = 0.0
            source = 'Original'
        
        st.success(f"💰 **Total Payment Amount: ₹{total_payment:,.0f}**")
        
        # Bill summary display
        st.markdown(f"""
            <div style="padding: 1rem; border-radius: 8px; background: #e0f2fe; border: 1px solid #3b82f6;">
                <h4>Payment Breakdown ({source})</h4>
                <p>Payment to Hospital: **₹{hospital_total:,.0f}**</p>
                <p>MediAudit Success Fee: **₹{commission_total:,.0f}**</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Payment Methods
        payment_method = st.radio(
            "Select Payment Method",
            ["💳 Credit/Debit Card", "📱 UPI", "💼 EMI Options", "🛍️ Buy Now Pay Later (BNPL)"], 
            horizontal=True
        )
        
        if payment_method == "💳 Credit/Debit Card":
            col1, col2 = st.columns(2)
            with col1: st.text_input("Card Number", placeholder="1234 5678 9012 3456", key="cc_num")
            with col2: st.text_input("CVV", placeholder="123", type="password", key="cc_cvv")
            st.text_input("Card Holder Name", key="cc_name")
        elif payment_method == "📱 UPI":
             st.text_input("UPI ID", placeholder="yourname@bank", key="upi_id")
        
        st.markdown("---")
        
        # Final Pay Now Button
        if st.button(f"🔒 Complete Secure Payment - ₹{total_payment:,.0f}", use_container_width=True, type="primary"):
            
            # Create history record
            for bill in payment_bills:
                bill_history = {
                    'patient_name': bill.get('patient_name', 'N/A'),
                    'hospital': bill.get('hospital', 'N/A'),
                    'original_amount': bill.get('total_billed', 0),
                    'final_amount_paid': total_payment,
                    'date_paid': datetime.now().strftime("%Y-%m-%d %H:%M"),
                    'savings': bill.get('potential_savings', 0),
                    'commission_paid': commission_total
                }
                st.session_state.payment_history.append(bill_history)
                
                # Remove paid bills from the queue
                st.session_state.bill_queue = [b for b in st.session_state.bill_queue if b.get('date') != bill.get('date') or b.get('hospital') != bill.get('hospital')]

            # If from negotiation, remove from active requests
            if pd_data.get('source') == 'negotiation':
                st.session_state.negotiation_requests = [r for r in st.session_state.negotiation_requests if r['id'] != pd_data['negotiation_id']]

            # Clear payment state
            st.session_state.show_payment = False
            st.session_state.payment_data = {}
            st.session_state.payment_bills = []

            st.balloons()
            st.success(f"✅ Payment of ₹{total_payment:,.0f} Successful! Redirecting to Home...")
            time.sleep(1) # Add a small delay for the user to see the success message
            st.rerun() # IMPORTANT: Rerun to clear payment view and show patient portal tabs
            
        return # Exit the patient portal logic if in payment mode

    # 2. If not in payment mode, proceed with tabs
    
    st.markdown("""
        <div class="hero-banner">
            <h1>👤 Patient Portal</h1>
            <p>Upload bills, detect overcharges, and let us negotiate savings for you!</p>
        </div>
    """, unsafe_allow_html=True)
    
    tabs = st.tabs(["📤 New Bill Audit", "🗂️ Bill Queue", "🤝 Negotiation Requests", "📋 History"])
    
    # --- New Bill Audit Tab ---
    with tabs[0]: 
        
        # Ensure audit summary is cleared when starting a fresh audit
        if st.session_state.current_audit is None:
            # Reset payment/audit state when starting a new audit
            st.session_state.show_payment = False
            st.session_state.payment_data = {}

        st.markdown("### 👤 Patient and Bill Information")
        
        col1, col2 = st.columns(2)
        with col1:
            patient_name = st.text_input("Patient Name", value="Jane Doe", key="audit_patient_name")
            hospital = st.text_input("Hospital Name", value="City General Hospital", key="audit_hospital_name")
        with col2:
            bill_date = st.date_input("Bill Date", value=datetime.now() - timedelta(days=5), key="audit_bill_date")
            total_billed = st.number_input("Total Billed Amount (₹)", min_value=100.0, value=150000.0, step=100.0, key="audit_total_billed")

        st.markdown("### 📝 Upload or Enter Bill Details")
        col1, col2 = st.columns(2)
        
        uploaded_file = col1.file_uploader("Upload Bill (PDF, JPEG, PNG)", type=["pdf", "png", "jpg", "jpeg"], key="audit_upload")
        manual_text = col2.text_area("Or enter bill line items manually (e.g., Room Rent 9000)", key="audit_manual_text", height=150)
        
        cghs_rates = load_reference_data()
        cghs_services = cghs_rates['Service'].str.lower().tolist()
        
        if st.button("🔬 Run Free Audit", type="primary"):
            st.session_state.current_audit = None # Clear previous audit first
            
            with st.spinner("Analyzing bill for overcharges..."):
                time.sleep(2) # Simulate AI processing time
                
                df_items = extract_bill_items(uploaded_file, manual_text)
                
                if df_items.empty:
                    st.warning("Could not extract line items. Please enter them manually or upload a clearer document.")
                else:
                    df_items['Standard Match'], _ = zip(*df_items['Item'].apply(
                        lambda x: fuzzy_match_service(normalize_text(x), cghs_services)
                    ))
                    
                    df_items = pd.merge(df_items, cghs_rates, left_on='Standard Match', right_on='Service', how='left')
                    df_items['Standard Rate (₹)'] = df_items['Rate (₹)'].fillna(0)
                    df_items['Overcharge (₹)'] = df_items.apply(
                        lambda row: max(0, row['Amount (₹)'] - row['Standard Rate (₹)']) if row['Standard Rate (₹)'] > 0 else 0, 
                        axis=1
                    )
                    df_items['Charge Type'] = df_items.apply(
                        lambda row: detect_overcharge_type(row['Item'], row['Amount (₹)'], row['Standard Rate (₹)']) if row['Overcharge (₹)'] > 0 else 'Standard Charge',
                        axis=1
                    )

                    total_savings = df_items['Overcharge (₹)'].sum()
                    
                    st.session_state.current_audit = {
                        'patient_name': patient_name,
                        'hospital': hospital,
                        'date': bill_date.strftime("%Y-%m-%d"),
                        'total_billed': total_billed,
                        'potential_savings': round(total_savings, 2),
                        'df_details': df_items.drop(columns=['Rate (₹)']),
                        'charge_types': df_items['Charge Type'].value_counts().to_dict()
                    }
                    st.success("✅ Audit Complete! See the summary below.")
        
        # --- Display Audit Summary (if available) ---
        if st.session_state.current_audit:
            audit = st.session_state.current_audit
            st.markdown("---")
            st.markdown("### 📊 Audit Summary")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f'<div class="metric-card"><div class="metric-label">Total Billed</div><div class="metric-value">₹{audit["total_billed"]:,.0f}</div></div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div class="metric-card" style="border-left: 4px solid #f59e0b;"><div class="metric-label">Potential Savings</div><div class="metric-value" style="color:#f59e0b;">₹{audit["potential_savings"]:,.0f}</div></div>', unsafe_allow_html=True)
            with col3:
                st.markdown(f'<div class="metric-card"><div class="metric-label">Estimated Fair Value</div><div class="metric-value">₹{audit["total_billed"] - audit["potential_savings"]:,.0f}</div></div>', unsafe_allow_html=True)
            
            st.markdown("#### Detailed Line Item Audit")
            st.dataframe(audit['df_details'], use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            # Negotiation and Payment Section (Direct Flow)
            if audit['potential_savings'] > 500:
                st.markdown(f"""
                    <div class="negotiation-card">
                        <h3>🤝 Expert Negotiation Service</h3>
                        <p>We found potential savings of **₹{audit['potential_savings']:,.0f}** on your **₹{audit['total_billed']:,.0f}** bill.</p>
                        <p>Our experts can negotiate with the hospital on your behalf. You pay only on actual savings achieved (15% of the saving amount).</p>
                    </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("✅ Yes, Negotiate For Me!", use_container_width=True, type="primary"):
                        # FIX: Negotiation Request Submission
                        negotiation_request = {'id': f"NEG{datetime.now().timestamp():.0f}", 'patient_name': audit['patient_name'], 'hospital': audit['hospital'], 'potential_savings': audit['potential_savings'], 'status': 'Pending', 'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'audit_data': audit}
                        st.session_state.negotiation_requests.append(negotiation_request)
                        st.session_state.current_audit = None # Clear audit state
                        st.success("✅ **Success!** Our team has taken up your case and is reviewing the bill.")
                        st.balloons()
                        st.rerun() # IMPORTANT: Rerun to update state
                
                with col2:
                    if st.button("💰 Proceed to Payment (Original Bill)", use_container_width=True):
                        st.session_state.payment_bills = [st.session_state.current_audit]
                        st.session_state.current_audit = None
                        st.session_state.show_payment = True # Set payment flag
                        st.rerun() # IMPORTANT: Rerun to go to payment view
                
                with col3:
                     if st.button("➕ Add to Bill Queue", use_container_width=True):
                        st.session_state.bill_queue.append(st.session_state.current_audit)
                        st.session_state.current_audit = None
                        st.success("✅ Bill added to queue for later payment.")
                        st.rerun()
            else:
                st.info("No significant overcharges found. You can proceed with the original bill payment.")
                if st.button("💰 Proceed to Bill Payment", use_container_width=True, type="primary"):
                    st.session_state.payment_bills = [st.session_state.current_audit]
                    st.session_state.current_audit = None
                    st.session_state.show_payment = True # Set payment flag
                    st.rerun() # IMPORTANT: Rerun to go to payment view
    
    # --- Bill Queue Tab ---
    with tabs[1]: 
        st.markdown("### 🗂️ Bill Queue")
        
        if not st.session_state.bill_queue:
            st.info("📭 No bills in queue. Audit a bill and add it to queue to pay multiple bills together!")
        else:
            total_queue = sum([b['total_billed'] for b in st.session_state.bill_queue])
            
            st.markdown(f"#### Total amount in queue: **₹{total_queue:,.0f}**")
            
            for idx, bill in enumerate(st.session_state.bill_queue):
                with st.container(border=True):
                    st.markdown(f"**{bill['hospital']}** - Patient: *{bill['patient_name']}*")
                    st.markdown(f"Bill Date: {bill['date']} | Billed Amount: **₹{bill['total_billed']:,.0f}** | Savings Potential: ₹{bill['potential_savings']:,.0f}")
                    
                    col_pay, col_remove = st.columns(2)
                    with col_pay:
                        if st.button(f"💳 Pay Bill #{idx+1}", key=f"pay_single_queue_{idx}", use_container_width=True, type="secondary"):
                            st.session_state.payment_bills = [bill]
                            st.session_state.show_payment = True
                            st.rerun()
                    with col_remove:
                        if st.button(f"🗑️ Remove #{idx+1}", key=f"remove_queue_{idx}", use_container_width=True):
                            st.session_state.bill_queue.pop(idx)
                            st.success("Bill removed from queue.")
                            st.rerun()
                            
            st.markdown("---")
            # Multi-pay button
            if st.button("💳 Pay All Bills Together", use_container_width=True, type="primary"):
                st.session_state.payment_bills = st.session_state.bill_queue
                st.session_state.show_payment = True
                st.rerun() # IMPORTANT: Rerun to go to payment view
    
    # --- Negotiation Requests Tab ---
    with tabs[2]: 
        st.markdown("### 🤝 Active Negotiation Requests")
        
        pending_requests = [r for r in st.session_state.negotiation_requests if r['status'] == 'Pending']
        resolved_requests = [r for r in st.session_state.negotiation_requests if r['status'] == 'Resolved']
        
        st.markdown("#### ⏳ Negotiations in Progress")
        if pending_requests:
            for idx, req in enumerate(pending_requests):
                with st.container(border=True):
                    st.markdown(f"**Case ID: {req['id']}** | Hospital: {req['hospital']}")
                    st.markdown(f"Original Billed: **₹{req['audit_data']['total_billed']:,.0f}** | Potential Savings: **₹{req['potential_savings']:,.0f}**")
                    st.info(f"Status: **{req['status']}** - Our team is in talks with the hospital. Estimated resolution: { (datetime.now() + timedelta(days=random.randint(5,15))).strftime('%Y-%m-%d') }")
                    
                    # Simulated Resolution Button
                    if st.button(f"Simulate Final Offer for {req['id']}", key=f"resolve_neg_{idx}"):
                        actual_savings = int(req['potential_savings'] * random.uniform(0.7, 0.9))
                        total_billed = req['audit_data']['total_billed']
                        hospital_payment = total_billed - actual_savings
                        commission_fee = actual_savings * 0.15 
                        total_to_pay = hospital_payment + commission_fee
                        
                        req['status'] = 'Resolved'
                        req['actual_savings'] = actual_savings
                        req['final_hospital_amount'] = hospital_payment
                        req['final_commission'] = commission_fee
                        req['total_to_pay'] = total_to_pay
                        st.success(f"✅ Negotiation resolved! Final offer ready.")
                        st.rerun() # IMPORTANT: Rerun to update resolved state
        else:
            st.info("No active negotiations.")

        st.markdown("---")
        st.markdown("#### ✅ Resolved Negotiations - Ready for Payment")
        if resolved_requests:
            for idx, req in enumerate(resolved_requests):
                with st.container(border=True):
                    st.markdown(f"**Case ID: {req['id']}** | Hospital: {req['hospital']}")
                    st.markdown(f"Original Bill: ₹{req['audit_data']['total_billed']:,.0f} | **Savings Achieved: ₹{req['actual_savings']:,.0f}**")
                    st.success(f"Final Amount Due (Hospital + Fee): **₹{req['total_to_pay']:,.0f}**")
                    
                    if st.button(f"💳 Pay Negotiated Bill - ₹{req['total_to_pay']:,.0f}", key=f"pay_neg_final_{idx}", type="primary"):
                        # FIX: Payment state setting for negotiation flow
                        st.session_state.payment_data = {
                            'source': 'negotiation', 'negotiation_id': req['id'],
                            'bill': req['audit_data'], 'total_to_pay': req['total_to_pay'],
                            'hospital_total': req['final_hospital_amount'], 'commission_total': req['final_commission']
                        }
                        st.session_state.payment_bills = [req['audit_data']] # Use the original bill data for history tracking
                        st.session_state.show_payment = True
                        st.rerun() # IMPORTANT: Rerun to go to payment view
        else:
            st.info("No resolved negotiations pending payment.")

    # --- History Tab ---
    with tabs[3]:
        st.markdown("### 📋 Payment and Audit History")
        if not st.session_state.payment_history:
            st.info("No completed payments yet. Your history will appear here once you've paid a bill or resolved a negotiation.")
        else:
            df_history = pd.DataFrame(st.session_state.payment_history)
            
            total_saved = df_history['savings'].sum()
            total_paid = df_history['final_amount_paid'].sum()
            
            col1, col2 = st.columns(2)
            with col1:
                 st.markdown(f'<div class="metric-card" style="border-left: 4px solid #10b981;"><div class="metric-label">Total Savings Achieved</div><div class="metric-value" style="color:#10b981;">₹{total_saved:,.0f}</div></div>', unsafe_allow_html=True)
            with col2:
                 st.markdown(f'<div class="metric-card" style="border-left: 4px solid #3b82f6;"><div class="metric-label">Total Amount Processed</div><div class="metric-value">₹{total_paid:,.0f}</div></div>', unsafe_allow_html=True)

            st.markdown("---")
            st.dataframe(
                df_history.rename(columns={
                    'original_amount': 'Original Amount (₹)',
                    'final_amount_paid': 'Final Paid (₹)',
                    'savings': 'Savings (₹)',
                    'commission_paid': 'Fee Paid (₹)',
                    'date_paid': 'Date Paid'
                }),
                use_container_width=True,
                hide_index=True,
                column_order=['hospital', 'patient_name', 'Date Paid', 'Original Amount (₹)', 'Savings (₹)', 'Final Paid (₹)', 'Fee Paid (₹)']
            )

# --- B2B Enterprise Section ---
elif user_type == "🏢 B2B Enterprise":
    st.markdown("""
        <div class="hero-banner" style="background: linear-gradient(rgba(17, 94, 89, 0.9), rgba(5, 150, 105, 0.9)), url('https://images.unsplash.com/photo-1542880034-7ce0e1d09e3e?w=1200');">
            <h1>🏢 B2B Enterprise Solutions</h1>
            <p>Custom Auditing and Analytics for TPAs, Insurers, and Large Corporations</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📈 Real-Time Claim Analytics")
    st.info("Access bulk processing, custom CGHS/ECHS rate cards, and deep-dive analytics for thousands of claims.")

    # Simulated B2B Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-card" style="border-left: 4px solid #059669;"><div class="metric-label">Claims Processed YTD</div><div class="metric-value">2,500+</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card" style="border-left: 4px solid #10b981;"><div class="metric-label">Potential Fraud Detected</div><div class="metric-value">₹1.2 Cr</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card" style="border-left: 4px solid #34d399;"><div class="metric-label">Avg. Audit Turnaround</div><div class="metric-value">4 Hours</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📧 Contact Our Sales Team")
    st.text_area("Your Company Name, Contact Details, and Inquiry...", height=150, key="b2b_inquiry")
    st.button("Submit Enterprise Inquiry", type="primary")
    
# --- About & Pricing Section ---
elif user_type == "ℹ️ About & Pricing":
    st.markdown("""
        <div class="hero-banner" style="background: linear-gradient(rgba(107, 33, 163, 0.9), rgba(168, 85, 247, 0.9)), url('https://images.unsplash.com/photo-1506126613408-e3170a4a8247?w=1200');">
            <h1>ℹ️ About & Pricing</h1>
            <p>Transparency is our promise.</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### How Our Pricing Works (For Patients)")
    st.markdown("""
        <div style="background: #f3f4f6; padding: 1.5rem; border-radius: 12px; margin-bottom: 2rem; border: 1px dashed #9ca3af;">
            <h4 style="color: #6d28d9;">1. Free Audit Always</h4>
            <p>Our AI-powered bill audit and detailed report are **100% free** for every patient. No hidden charges.</p>
            
            <h4 style="color: #6d28d9;">2. Success-Based Negotiation Fee</h4>
            <p>If we find overcharges and you choose our negotiation service, we charge a success fee only on the actual savings achieved.</p>
            
            <p style="font-size: 1.1rem; font-weight: 700;">Our Fee: 15% of the savings we recover for you.</p>
            
            <p>If we don't save you money, you pay nothing for the negotiation service.</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Common Questions")
    
    with st.expander("❓ Is the bill audit really free?"):
        st.write("Yes, the initial audit report detailing potential overcharges is completely free for individual patients. We only charge a commission if you opt for our negotiation service AND we successfully save you money.")
    
    with st.expander("⏱️ How long does the negotiation process take?"):
        st.write("Negotiations typically take between 5 to 15 days, depending on the hospital and complexity of the bill. We keep you updated every step of the way.")
    
    with st.expander("💬 How do I contact the support team?"):
        st.write(f"You can reach our support team via WhatsApp at **{mobile_number_display}** or email at support@mediaudit.com. Our team. Available 24/7 for quick queries and assistance.")
        
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
    st.markdown(f"• **Mobile:** {mobile_number_display}")
    st.markdown("• Email: support@mediaudit.com")
