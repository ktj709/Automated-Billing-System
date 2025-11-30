"""
Modern Admin Dashboard - STANDALONE DEMO
Run this file separately to preview the modern design
Command: streamlit run modern_dashboard_demo.py
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Page config
st.set_page_config(page_title="Modern Dashboard Demo", layout="wide")

# Mock Data (simulating your database)
MOCK_PENDING_READINGS = [
    {'meter_id': 'METER101', 'customer_id': 'CUST001', 'reading_value': 1289, 'estimated_consumption': 86, 'reading_date': '2025-11-30'},
    {'meter_id': 'METER204', 'customer_id': 'CUST002', 'reading_value': 960, 'estimated_consumption': 70, 'reading_date': '2025-11-29'},
    {'meter_id': 'METER305', 'customer_id': 'CUST003', 'reading_value': 700, 'estimated_consumption': 270, 'reading_date': '2025-11-28'},
    {'meter_id': 'METER402', 'customer_id': 'CUST004', 'reading_value': 1570, 'estimated_consumption': 20, 'reading_date': '2025-11-27'},
    {'meter_id': 'METER895', 'customer_id': 'CUST005', 'reading_value': 2100, 'estimated_consumption': 150, 'reading_date': '2025-11-26'},
]

# Modern CSS
st.markdown("""
<style>
/* Top Metrics Cards */
.metric-card {
    background: white;
    padding: 24px;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    text-align: center;
    transition: all 0.3s ease;
    border-left: 4px solid #4A90E2;
}
.metric-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 6px 16px rgba(0,0,0,0.15);
}
.metric-value {
    font-size: 42px;
    font-weight: 700;
    color: #4A90E2;
    margin: 12px 0;
    font-family: 'Segoe UI', sans-serif;
}
.metric-label {
    font-size: 13px;
    color: #6c757d;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    font-weight: 600;
}
.metric-icon {
    font-size: 32px;
    margin-bottom: 8px;
}

/* Section Headers */
.section-header {
    font-size: 16px;
    font-weight: 700;
    color: #2c3e50;
    margin: 24px 0 16px 0;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding: 12px;
    background: #F8F9FA;
    border-radius: 8px;
}

/* Status Box */
.status-box {
    background: white;
    padding: 24px;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.status-item {
    padding: 12px 0;
    border-bottom: 1px solid #eee;
    font-size: 14px;
    color: #495057;
}
.status-item:last-child {
    border-bottom: none;
}

/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Header
col_header, col_spacer, col_user = st.columns([5, 3, 2])
with col_header:
    st.markdown("# ⚡ Blessings Electric Billing AI")
with col_user:
    st.markdown("👤 **[Admin]** [Logout]")

st.markdown("---")

# Top 4 Metrics
pending_count = len(MOCK_PENDING_READINGS)
invoices_count = 5
overdue_count = 7

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-icon">⚡</div>
        <div class="metric-label">Total Meters</div>
        <div class="metric-value">120</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-icon">📋</div>
        <div class="metric-label">New Readings</div>
        <div class="metric-value">{pending_count}</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-icon">📄</div>
        <div class="metric-label">Invoices to Send</div>
        <div class="metric-value">{invoices_count}</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #D9534F;">
        <div class="metric-icon">🔴</div>
        <div class="metric-label">Overdue</div>
        <div class="metric-value" style="color: #D9534F;">{overdue_count}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Main Content Area
col_main, col_sidebar = st.columns([2.5, 1])

with col_main:
    st.markdown('<div class="section-header">📊 Review New Readings</div>', unsafe_allow_html=True)
    
    # Create table data
    df_data = []
    for reading in MOCK_PENDING_READINGS:
        apt_num = reading['meter_id'].replace('METER', '')
        usage = reading['estimated_consumption']
        amount = usage * 7.5  # Rate per kWh
        
        df_data.append({
            'Apt': apt_num,
            'New Reading': f"{reading['reading_value']}",
            'Usage': f"{usage}",
            'Amount': f"₹{amount:.0f}"
        })
    
    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Action buttons
    st.markdown("**Actions:**")
    cols = st.columns(len(MOCK_PENDING_READINGS))
    
    for idx, reading in enumerate(MOCK_PENDING_READINGS):
        with cols[idx]:
            apt_num = reading['meter_id'].replace('METER', '')
            if st.button(f"✓ APPROVE", key=f"approve_{idx}", type="primary", use_container_width=True):
                st.success(f"✅ Apartment {apt_num} approved for billing!")
                st.balloons()
            
            if st.button(f"✗ REJECT", key=f"reject_{idx}", use_container_width=True):
                st.warning(f"❌ Apartment {apt_num} rejected")
    
    # View All button
    st.markdown("")
    if st.button("[ View All Readings ]", use_container_width=True):
        st.info("Would show all readings in your actual app")

with col_sidebar:
    st.markdown('<div class="section-header">⚡ Quick Actions</div>', unsafe_allow_html=True)
    
    if st.button("➕ Create New Customer", key="qa1", use_container_width=True, type="primary"):
        st.info("Opens customer creation form")
    
    if st.button("📊 Generate Monthly Bills", key="qa2", use_container_width=True, type="primary"):
        st.info("Generates bills for all customers")
    
    if st.button("💳 View Payments", key="qa3", use_container_width=True, type="primary"):
        st.info("Shows payment history")
    
    if st.button("📈 Print Reports", key="qa4", use_container_width=True, type="primary"):
        st.info("Generates PDF reports")
    
    # Status Box
    st.markdown('<br><div class="section-header">📊 Simple Status Box</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="status-box">
        <div class="status-item">• <strong>Payments This Month:</strong> ₹2,45,000</div>
        <div class="status-item">• <strong>Total Outstanding:</strong> ₹75,000</div>
        <div class="status-item">• <strong>Overdue Accounts:</strong> 7</div>
        <div class="status-item">• <strong>Notes from Field:</strong> 3</div>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")
st.caption("© Blessings Electric Billing AI | Billing Cycle: Nov 2025")

# Info box
st.markdown("<br>", unsafe_allow_html=True)
st.info("""
**📌 This is a DEMO of the modern dashboard design**

✨ **Features shown:**
- Top 4 KPI metric cards with hover effects
- Clean readings review table
- Approve/Reject action buttons
- Quick actions sidebar
- Status box with key metrics
- Modern card-based design with professional styling

🎯 **To integrate this into your app:**
Once you approve this design, I can help integrate it into your main `streamlit_app.py`
""")
