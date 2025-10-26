import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
from io import BytesIO
import difflib
from datetime import datetime, timedelta
import time
import random

# --- Configuration ---

# Global contact information
whatsapp_number = "917877797505"
mobile_number_display = "+91 7877797505"
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
        
        /* Negotiation Card */
        .negotiation-card {
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            border: 3px solid #f59e0b;
            padding: 1.5rem;
            border-radius: 12px;
            margin: 1rem 0;
            height: 100%; /* Key for equal height on services */
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

# --- Sidebar (Robust Logo Fix) ---
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
            st.metric("Total Audits", str(len(st.session_state.payment_history) + len(st.session_state.negotiation_requests)))
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
    
    # 5 columns for 5 overcharge types (Ensures boxes are aligned and equal size)
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
    st.markdown("""
        <div class="hero-banner">
            <h1>👤 Patient Portal</h1>
            <p>Upload bills, detect overcharges, and let us negotiate savings for you!</p>
        </div>
    """, unsafe_allow_html=True)
    
    tabs = st.tabs(["📤 New Bill Audit", "🤝 Negotiation Requests", "📋 History"])
    
    with tabs[0]: # New Bill Audit
        # Reset payment/audit state when starting a new audit
        st.session_state.show_payment = False
        st.session_state.current_audit = None
        st.session_state.payment_data = {}
        
        st.markdown("### 👤 Patient and Bill Information")
        col1, col2, col3, col4 = st.columns(4) 
        
        with col1:
            patient_name = st.text_input("Patient Name", placeholder="Enter full name", key="p_name")
            patient_id = st.text_input("Patient ID", disabled=True, value=f"PAT{datetime.now().strftime('%Y%m%d%H%M')}")
        
        with col2:
            hospital_list = ["Select hospital", "AIIMS Delhi", "Apollo Hospital", "Fortis Hospital", "Medanta", "Manipal Hospital", "Max Hospital"]
            hospital = st.selectbox("Hospital", hospital_list, key="p_hospital")
            admission_date = st.date_input("Admission Date", datetime.now().date() - timedelta(days=7), key="p_date")
        
        with col3:
            contact_number = st.text_input("Contact Number", placeholder=mobile_number_display, value=mobile_number_display, key="p_contact")
            email = st.text_input("Email", placeholder="patient@email.com", key="p_email")
        
        with col4:
            employer_id = st.text_input("Employer ID (Optional)", placeholder="Link to enterprise", key="p_employer_id")
            st.caption("Connects your audit to your company's benefits plan.")
        
        st.markdown("---")
        st.markdown("### 📁 Upload or Enter Bill Details")
        
        col_upload, col_info = st.columns([2, 1])
        
        with col_upload:
            uploaded = st.file_uploader(
                "Upload your medical bill (PDF, Excel, CSV, Images)",
                type=["csv", "xlsx", "pdf", "jpg", "jpeg", "png"],
            )
            manual_txt = st.text_area("Or, paste bill text here (e.g., 'Syringe 1500\\nRoom Rent 9000'):", height=100)
        
        with col_info:
            st.info(f"**We Check For Overcharge Types:**\n- Inflated Consumables\n- Duplicate Billing\n- Upcoding\n- Unbundling\n- Other Overcharging")

        df_items = extract_bill_items(uploaded, manual_txt)
        
        if not df_items.empty:
            st.markdown("### 📋 Extracted Items (Edit if necessary)")
            edited = st.data_editor(df_items, num_rows="dynamic", use_container_width=True)
            
            if st.button("🚀 Run FREE Audit", use_container_width=True, type="primary"):
                if not patient_name or hospital == "Select hospital":
                    st.error("Please fill in Patient Name and select a Hospital.")
                else:
                    # --- Audit Logic Simulation ---
                    try:
                        # Attempt to calculate total from edited data
                        total_billed = edited['Amount (₹)'].astype(float).sum()
                    except:
                        # Fallback for bad data entry
                        total_billed = 45000.0
                        
                    potential_savings = int(total_billed * random.uniform(0.15, 0.35))
                    flagged_count = random.randint(3, 8)
                    
                    # Store audit results
                    st.session_state.current_audit = {
                        'patient_name': patient_name, 'hospital': hospital, 'contact': contact_number, 'email': email, 'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                        'results_df': edited, 'total_billed': total_billed, 'potential_savings': potential_savings, 'flagged_count': flagged_count,
                        'overcharge_types': {"Inflated Consumables": 2, "Duplicate Billing": 0, "Upcoding": 1, "Unbundling": 0, "Other Overcharging": 1},
                        'alerts': [f"⚠️ Found potential savings on {edited.iloc[i%len(edited)]['Item']}" for i in range(flagged_count)]
                    }
                    st.success("✅ Audit Complete!")
                    st.rerun()

        # --- Display Audit Summary (if available) ---
        if st.session_state.current_audit:
            audit = st.session_state.current_audit
            st.markdown("---")
            st.markdown("### 📊 Audit Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""<div class="metric-card" style="background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%);"><div class="metric-value" style="color: #00838f;">₹{audit['total_billed']:,.0f}</div><div class="metric-label">Total Billed Amount</div></div>""", unsafe_allow_html=True)
            with col2:
                st.markdown(f"""<div class="metric-card" style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);"><div class="metric-value" style="color: #92400e;">₹{audit['potential_savings']:,.0f}</div><div class="metric-label">Possible Savings</div></div>""", unsafe_allow_html=True)
            with col3:
                st.markdown(f"""<div class="metric-card"><div class="metric-value">{len(audit['results_df'])}</div><div class="metric-label">Items Checked</div></div>""", unsafe_allow_html=True)
            with col4:
                st.markdown(f"""<div class="metric-card"><div class="metric-value" style="font-size: 2rem;">{audit['flagged_count']}</div><div class="metric-label" style="font-size: 0.8rem;">Items with Errors</div></div>""", unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Negotiation and Payment Section (Direct Flow)
            if audit['potential_savings'] > 500:
                st.markdown(f"""
                    <div class="negotiation-card">
                        <h3>🤝 Expert Negotiation Service</h3>
                        <p>We found potential savings of **₹{audit['potential_savings']:,.0f}** on your **₹{audit['total_billed']:,.0f}** bill.</p>
                        <p>Our experts can negotiate on your behalf. You pay only on actual savings achieved.</p>
                    </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Yes, Negotiate For Me!", use_container_width=True, type="primary"):
                        negotiation_request = {'id': f"NEG{datetime.now().timestamp():.0f}", 'patient_name': audit['patient_name'], 'hospital': audit['hospital'], 'potential_savings': audit['potential_savings'], 'status': 'Pending', 'date': audit['date'], 'audit_data': audit}
                        st.session_state.negotiation_requests.append(negotiation_request)
                        st.success("✅ **Success!** Our team has taken up your case and will resolve it in **1 to 3 business days**.")
                        st.session_state.current_audit = None
                        st.balloons()
                        st.rerun()
                
                with col2:
                    if st.button("💰 No Thanks, Proceed to Bill Payment", use_container_width=True):
                        st.session_state.show_payment = True
                        st.session_state.payment_bills = [st.session_state.current_audit]
                        st.session_state.current_audit = None
                        st.rerun()
            else:
                st.info("No significant overcharges found. You can proceed with the original bill payment.")
                if st.button("💰 Proceed to Bill Payment", use_container_width=True, type="primary"):
                    st.session_state.show_payment = True
                    st.session_state.payment_bills = [st.session_state.current_audit]
                    st.session_state.current_audit = None
                    st.rerun()
                
    with tabs[1]: # Negotiation Requests
        st.markdown("### 🤝 Active Negotiation Requests")
        
        pending_requests = [r for r in st.session_state.negotiation_requests if r['status'] == 'Pending']
        resolved_requests = [r for r in st.session_state.negotiation_requests if r['status'] == 'Resolved']
        
        st.markdown("#### ⏳ Negotiations in Progress")
        if pending_requests:
            for idx, req in enumerate(pending_requests):
                with st.container(border=True):
                    total_billed = req['audit_data']['total_billed']
                    possible_savings = req['potential_savings']
                    st.write(f"**Case ID:** {req['id']} | **Patient:** {req['patient_name']}")
                    st.info(f"Status: Our team is negotiating. Possible Savings: **₹{possible_savings:,.0f}**")
                    
                    # Simulated Resolution Button
                    if st.button(f"Simulate Final Offer for {req['patient_name']}", key=f"resolve_neg_{idx}"):
                        actual_savings = int(possible_savings * random.uniform(0.7, 0.9))
                        hospital_payment = total_billed - actual_savings
                        commission_fee = actual_savings * 0.15 
                        total_to_pay = hospital_payment + commission_fee
                        
                        req['status'] = 'Resolved'
                        req['actual_savings'] = actual_savings
                        req['final_hospital_amount'] = hospital_payment
                        req['final_commission'] = commission_fee
                        req['total_to_pay'] = total_to_pay
                        st.success(f"✅ Negotiation resolved! Final offer ready.")
                        st.rerun()
        else:
            st.info("No active negotiations.")

        st.markdown("#### ✅ Resolved Negotiations - Ready for Payment")
        if resolved_requests:
            for idx, req in enumerate(resolved_requests):
                with st.container(border=True):
                    st.write(f"**Case ID:** {req['id']} | **Patient:** {req['patient_name']}")
                    st.write(f"**Total Savings Achieved:** **₹{req['actual_savings']:,.0f}**")
                    st.markdown(f"**Final Total Payment:** **₹{req['total_to_pay']:,.0f}**")
                    
                    if st.button(f"💳 Pay Negotiated Bill - ₹{req['total_to_pay']:,.0f}", key=f"pay_neg_final_{idx}", type="primary"):
                        st.session_state.payment_data = {
                            'source': 'negotiation', 'negotiation_id': req['id'],
                            'bill': req['audit_data'], 'total_to_pay': req['total_to_pay'],
                            'hospital_total': req['final_hospital_amount'], 'commission_total': req['final_commission']
                        }
                        st.session_state.show_payment = True
                        st.rerun()
        else:
            st.info("No resolved negotiations awaiting payment.")

    with tabs[2]: # History
        st.markdown("### 📋 Completed Payments & Audits")
        if not st.session_state.payment_history:
            st.info("No completed payments found.")
        else:
            for idx, item in enumerate(reversed(st.session_state.payment_history)):
                with st.container(border=True):
                    col1, col2, col3 = st.columns(3)
                    with col1: st.write(f"**Date Paid:** {item['date_paid']}"); st.write(f"**Patient:** {item['patient_name']}")
                    with col2: st.write(f"**Hospital:** {item['hospital']}"); st.write(f"**Original Bill:** ₹{item['original_amount']:,.0f}")
                    with col3: st.write(f"**Final Paid:** **₹{item['final_amount_paid']:,.0f}**")
                    if item['commission_paid'] > 0: st.caption(f"Savings Achieved: ₹{item['savings']:,.0f} | Fee: ₹{item['commission_paid']:,.0f}")


# ----------------------------------------------------------------------
# --- Payment Gateway Section (CENTRALIZED) ---
# ----------------------------------------------------------------------

if st.session_state.get('show_payment', False):
    st.markdown("---")
    st.markdown("## 💳 Complete Your Payment")
    
    # Logic to set payment totals
    pd_data = st.session_state.get('payment_data', {})
    if 'total_to_pay' not in pd_data:
        # Direct payment after audit (Original Bill)
        audit = st.session_state.payment_bills[0]
        total_payment = audit['total_billed']
        hospital_total = audit['total_billed']
        commission_total = 0.0
        potential_savings = audit['potential_savings']
    else:
        # From resolved negotiation
        total_payment = pd_data['total_to_pay']
        hospital_total = pd_data['hospital_total']
        commission_total = pd_data['commission_total']
        potential_savings = pd_data['bill']['potential_savings']

    st.success(f"💰 **Total Payment Amount: ₹{total_payment:,.0f}**")
    
    # Bill summary display
    if commission_total > 0:
        st.markdown(f"""
            <div style="padding: 1rem; border-radius: 8px; background: #e0f2fe; border: 1px solid #3b82f6;">
                <h4>Payment Breakdown</h4>
                <p>Reduced Payment to Hospital: **₹{hospital_total:,.0f}**</p>
                <p>MediAudit Success Fee (15% of savings): **₹{commission_total:,.0f}**</p>
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
    elif payment_method == "📱 UPI":
        st.text_input("Enter UPI ID", placeholder="patient@upi", key="upi_id")
        st.button("Generate QR Code", key="upi_qr", type="secondary")
    elif payment_method == "💼 EMI Options":
        st.selectbox("Select Bank/NBFC", ["HDFC Bank", "ICICI Bank", "Axis Bank"], key="emi_bank")
        st.warning(f"Estimated Monthly EMI: **₹{total_payment / 6:.0f}** (for 6 months, subject to interest)")
    elif payment_method == "🛍️ Buy Now Pay Later (BNPL)":
        st.selectbox("Select Partner", ["Simpl", "Slice", "Lazypay"], key="bnpl_partner")
        st.info(f"Pay in 30 days. Required down payment: **₹{total_payment * 0.1:.0f}**")
    
    st.markdown("---")
    
    # Final Pay Now Button
    if st.button(f"🔒 Complete Secure Payment - ₹{total_payment:,.0f}", use_container_width=True, type="primary"):
        
        # Create history record
        bill_history = {
            'patient_name': pd_data.get('bill', st.session_state.payment_bills[0])['patient_name'],
            'hospital': pd_data.get('bill', st.session_state.payment_bills[0])['hospital'],
            'original_amount': pd_data.get('bill', st.session_state.payment_bills[0])['total_billed'],
            'final_amount_paid': total_payment,
            'date_paid': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'savings': potential_savings,
            'commission_paid': commission_total
        }
        st.session_state.payment_history.append(bill_history)
        
        # If from negotiation, remove from active requests
        if pd_data.get('source') == 'negotiation':
            st.session_state.negotiation_requests = [r for r in st.session_state.negotiation_requests if r['id'] != pd_data['negotiation_id']]

        # Clear payment state
        st.session_state.show_payment = False
        st.session_state.payment_data = {}
        st.session_state.payment_bills = []

        st.balloons()
        st.success(f"✅ Payment of ₹{total_payment:,.0f} Successful! Thank you.")
        st.rerun()

# --- Footer ---
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
    st.markdown(f"• {mobile_number_display}")
