"""
Billing System - Role Selection Landing Page
"""
import streamlit as st

st.set_page_config(
    page_title="Billing System",
    page_icon="⚡",
    layout="centered"
)

# Custom CSS
st.markdown("""
<style>
    .big-font {
        font-size: 50px !important;
        font-weight: bold;
        text-align: center;
    }
    .role-card {
        padding: 30px;
        border-radius: 10px;
        border: 2px solid #ddd;
        text-align: center;
        margin: 20px 0;
        transition: all 0.3s;
    }
    .role-card:hover {
        border-color: #4CAF50;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<p class="big-font">⚡ Electricity Billing System</p>', unsafe_allow_html=True)
st.markdown("---")

# Welcome message
st.markdown("### Welcome! Please select your role to continue:")
st.markdown("")
st.markdown("")

# Two columns for role selection
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🔧 Field Engineer")
    st.markdown("""
    **Access to:**
    - Submit meter readings
    - View reading history
    - Generate basic bills
    - Field operations tools
    """)
    st.markdown("")
    if st.button("🔧 Enter as Field Engineer", type="primary", use_container_width=True):
        st.switch_page("engineer_dashboard.py")

with col2:
    st.markdown("### 👨‍💼 Administrator")
    st.markdown("""
    **Access to:**
    - Full workflow testing
    - Bill validation & processing
    - Auth0 authentication
    - Payment management
    - Analytics & reports
    - System scheduler
    """)
    if st.button("👨‍💼 Enter as Administrator", type="primary", use_container_width=True):
        st.switch_page("admin_dashboard.py")

st.markdown("---")
st.markdown("")
st.markdown("")

# Info boxes
col_a, col_b = st.columns(2)

with col_a:
    with st.expander("ℹ️ For Field Engineers"):
        st.write("""
        As a Field Engineer, you can:
        - Record meter readings from the field
        - View historical data for meters
        - Generate customer bills
        - Access field operation tools
        
        Your readings will be automatically stored in the database 
        for admin processing and validation.
        """)

with col_b:
    with st.expander("ℹ️ For Administrators"):
        st.write("""
        As an Administrator, you have access to:
        - Complete billing workflow (13 steps)
        - AI-powered validation and calculations
        - Payment status tracking
        - Stripe integration
        - Discord notifications
        - System analytics and reports
        - Automated scheduler management
        """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>Made with ❤️ using Streamlit | Billing System v2.0</p>
        <p style='font-size: 12px; color: gray;'>
            🔒 Secure • ⚡ Fast • 📊 Reliable
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

