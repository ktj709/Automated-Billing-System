"""
Streamlit Dashboard for Billing System Testing
"""
import streamlit as st
import json
from datetime import datetime, timedelta
from services import DatabaseService, TariffRules
from utils.sample_data import SampleDataGenerator

st.set_page_config(page_title="Billing System Dashboard", page_icon="⚡", layout="wide")

# Initialize session state for role
if 'user_role' not in st.session_state:
    st.session_state.user_role = None

# Initialize services
@st.cache_resource
def get_db_service():
    return DatabaseService()

db = get_db_service()

# ==============================================
# ROLE SELECTION PAGE
# ==============================================
if st.session_state.user_role is None:
    st.markdown('<p style="font-size: 50px; font-weight: bold; text-align: center;">⚡ Electricity Billing System</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("### Welcome! Please select your role to continue:")
    st.markdown("")
    st.markdown("")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔧 Field Engineer")
        st.markdown("")
        if st.button("🔧 Enter as Field Engineer", type="primary", width='stretch'):
            st.session_state.user_role = "field_engineer"
            st.rerun()

    with col2:
        st.markdown("### 👨‍💼 Administrator")
        st.markdown("")
        if st.button("👨‍💼 Enter as Administrator", type="primary", width='stretch'):
            st.session_state.user_role = "admin"
            st.rerun()
    
    st.markdown("---")
    st.markdown("")
    
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
    st.stop()

# ==============================================
# FIELD ENGINEER DASHBOARD
# ==============================================
elif st.session_state.user_role == "field_engineer":
    # Initialize field engineer session flag
    if 'fe_initialized' not in st.session_state:
        st.cache_resource.clear()
        st.cache_data.clear()
        st.session_state.fe_initialized = True
    
    st.title("🔧 Field Engineer Dashboard")
    st.markdown("### Meter Reading & Field Operations")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("👤 Current Role")
        st.info("🔧 Field Engineer")
        
        if st.button("🔄 Switch Role"):
            st.session_state.user_role = None
            # Reset initialization flags
            if 'fe_initialized' in st.session_state:
                del st.session_state.fe_initialized
            if 'admin_initialized' in st.session_state:
                del st.session_state.admin_initialized
            st.cache_resource.clear()
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        st.header("🔧 Configuration")
        st.success("✅ Supabase Connected")
        st.info("💡 OpenAI Enabled")
        
        st.markdown("---")
        st.header("🎯 Quick Actions")
        
        if st.button("🔄 Refresh Data"):
            st.cache_resource.clear()
            st.rerun()
    
    # Field Engineer Tabs
    fe_tab1, fe_tab2, fe_tab3, fe_tab4 = st.tabs([
        "📊 Overview",
        "📋 Meter Readings",
        "➕ Add Reading",
        "💰 Generate Bill"
    ])
    
    # FE Tab 1: Overview
    with fe_tab1:
        col_header1, col_header2 = st.columns([3, 1])
        
        with col_header1:
            st.header("📊 System Overview")
        
        with col_header2:
            st.write("")
            if st.button("🔄 Refresh", type="secondary", width='stretch', key="fe_refresh_overview"):
                st.cache_resource.clear()
                st.cache_data.clear()
                st.rerun()
        
        col1, col2, col3 = st.columns(3)
        
        try:
            readings = db.get_historical_readings("METER001", limit=100)
            
            with col1:
                st.metric("Total Readings", len(readings))
            
            with col2:
                if readings:
                    latest = readings[0]
                    st.metric("Latest Reading", f"{latest['reading_value']} kWh")
            
            with col3:
                if len(readings) >= 2:
                    consumption = readings[0]['reading_value'] - readings[1]['reading_value']
                    st.metric("Last Month Consumption", f"{consumption:.2f} kWh")
            
            st.markdown("---")
            
            if readings:
                st.subheader("📈 Recent Meter Readings")
                import pandas as pd
                df = pd.DataFrame(readings[:10])
                df['reading_date'] = pd.to_datetime(df['reading_date'])
                df = df.sort_values('reading_date', ascending=False)
                st.dataframe(df[['reading_date', 'reading_value', 'meter_id', 'customer_id']], width='stretch')
            else:
                st.warning("No meter readings found. Add some data first!")
        
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
    
    # FE Tab 2: Meter Readings History
    with fe_tab2:
        st.header("📋 Meter Readings History")
        
        col_filter1, col_filter2 = st.columns([3, 1])
        
        with col_filter1:
            meter_filter = st.text_input("Filter by Meter ID", value="METER001")
        
        with col_filter2:
            st.write("")
            st.write("")
            if st.button("🔄 Refresh", type="secondary", width='stretch', key="fe_refresh_readings"):
                st.cache_resource.clear()
                st.cache_data.clear()
                st.rerun()
        
        try:
            readings = db.get_historical_readings(meter_filter, limit=50)
            
            if readings:
                st.success(f"✅ Found {len(readings)} readings for {meter_filter}")
                st.caption(f"🕒 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                import pandas as pd
                df = pd.DataFrame(readings)
                df['reading_date'] = pd.to_datetime(df['reading_date'])
                df = df.sort_values('reading_date', ascending=False)
                
                st.dataframe(df, width='stretch')
                
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"meter_readings_{meter_filter}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info(f"No readings found for {meter_filter}")
        
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # FE Tab 3: Add New Reading
    with fe_tab3:
        st.header("➕ Add New Meter Reading")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            with st.form("add_reading"):
                col_a, col_b = st.columns(2)
                
                with col_a:
                    form_meter_id = st.text_input("Meter ID*", value="METER001", help="Enter the meter identification number")
                    form_customer_id = st.text_input("Customer ID*", value="CUST001", help="Enter customer identification number")
                    form_reading_value = st.number_input("Reading Value (kWh)*", min_value=0.0, value=0.0, step=0.1, help="Current meter reading in kWh - MUST be greater than 0")
                
                with col_b:
                    form_reading_date = st.date_input("Reading Date*", value=datetime.now())
                    form_location = st.text_input("Location (optional)", value="", placeholder="e.g., Building A, Floor 2")
                    form_notes = st.text_area("Notes (optional)", value="", placeholder="Any observations or issues", height=100)
                
                submitted = st.form_submit_button("✅ Submit Reading", type="primary", width='stretch')
                
                # Handle form submission INSIDE the form block
                if submitted:
                    if form_reading_value <= 0:
                        st.error("⚠️ Please enter a Reading Value greater than 0!")
                    else:
                        try:
                            historical = db.get_historical_readings(form_meter_id, limit=1)
                            if historical and form_reading_value < historical[0]['reading_value']:
                                st.error(f"⚠️ Error: Reading value ({form_reading_value} kWh) is lower than the last recorded reading ({historical[0]['reading_value']} kWh).")
                            else:
                                reading_data = {
                                    "meter_id": form_meter_id,
                                    "customer_id": form_customer_id,
                                    "reading_value": form_reading_value,
                                    "reading_date": form_reading_date.strftime("%Y-%m-%d"),
                                    "location": form_location,
                                    "notes": form_notes,
                                    "engineer_id": "FE001",  # Replace with actual engineer ID if available
                                    "unit": "kWh",
                                    "submitted_at": datetime.now().isoformat(),
                                    "status": "pending"
                                }
                                try:
                                    result = db.insert_meter_reading(reading_data)
                                    st.write(f"🔎 Debug: DB insert result: {result}")
                                    if not result or (isinstance(result, dict) and not result.get('id')):
                                        st.error("❌ Reading was not saved to the database. Please check DB connection and table schema.")
                                    else:
                                        st.success(f"✅ Reading submitted successfully!")
                                        st.info(f"📊 **Meter**: {form_meter_id} | **Reading**: {form_reading_value} kWh | **Date**: {form_reading_date.strftime('%Y-%m-%d')}")
                                        st.balloons()
                                        st.cache_resource.clear()
                                        st.cache_data.clear()
                                        st.rerun()
                                except Exception as db_exc:
                                    st.error(f"❌ DB Error: {db_exc}")
                        except Exception as e:
                            st.error(f"❌ Error submitting reading: {str(e)}")
        
        with col2:
            st.subheader("🎲 Generate Sample Data")
            num_readings = st.number_input("Number of readings", min_value=1, max_value=12, value=6)
            
            if st.button("Generate", type="secondary"):
                try:
                    readings = SampleDataGenerator.generate_meter_readings(
                        meter_id="METER001",
                        customer_id="CUST001",
                        num_months=num_readings,
                        base_consumption=200.0
                    )
                    
                    for reading in readings:
                        db.insert_meter_reading(reading)
                    
                    st.success(f"✅ Generated {len(readings)} readings")
                    st.cache_resource.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    # FE Tab 4: Generate Bill
    with fe_tab4:
        st.header("💰 Generate Electricity Bill")
        
        try:
            readings = db.get_historical_readings("METER001", limit=10)
            
            if len(readings) >= 2:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📝 Bill Details")
                    
                    current_reading = st.number_input(
                        "Current Reading (kWh)", 
                        min_value=readings[0]['reading_value'],
                        value=readings[0]['reading_value'] + 150,
                        step=0.1
                    )
                    
                    previous_reading = readings[0]['reading_value']
                    consumption = current_reading - previous_reading
                    
                    st.info(f"Previous Reading: {previous_reading:.2f} kWh")
                    st.success(f"Consumption: {consumption:.2f} kWh")
                    
                    tariff_type = st.selectbox("Tariff Type", ["residential", "commercial"])
                    connected_load = st.number_input("Connected Load (KW)", value=7.0, step=0.5)
                
                with col2:
                    if st.button("💰 Generate Bill", type="primary"):
                        bill = TariffRules.calculate_total_bill(
                            consumption_kwh=consumption,
                            connected_load_kw=connected_load,
                            tariff_type=tariff_type
                        )
                        
                        bill_data = {
                            "customer_id": "CUST001",
                            "meter_id": "METER001",
                            "billing_period_start": readings[0]['reading_date'],
                            "billing_period_end": datetime.now().strftime("%Y-%m-%d"),
                            "consumption_kwh": consumption,
                            "amount": bill['amount_payable'],
                            "status": "pending",
                            "created_at": datetime.now().isoformat()
                        }
                        
                        created_bill = db.create_bill(bill_data)
                        
                        st.success("✅ Bill Generated Successfully!")
                        st.markdown("---")
                        st.markdown("### 🧾 Bill Summary")
                        st.write(f"**Bill ID**: {created_bill.get('id', 'N/A')}")
                        st.write(f"**Consumption**: {consumption:.2f} kWh")
                        st.write(f"**Amount**: ₹{bill['amount_payable']:,.2f}")
                        st.write(f"**Status**: Pending")
                        
                        with st.expander("📋 Detailed Breakdown"):
                            st.json(bill['detailed_breakdown'])
            
            else:
                st.warning("⚠️ Need at least 2 meter readings to generate a bill. Add more readings first!")
        
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    st.markdown("---")
    st.markdown("👷 **Field Engineer Dashboard** | Meter Reading & Field Operations | v2.0")

# ==============================================
# ADMIN DASHBOARD
# ==============================================
else:  # admin role
    # Initialize admin session flag
    if 'admin_initialized' not in st.session_state:
        st.cache_resource.clear()
        st.cache_data.clear()
        st.session_state.admin_initialized = True

    st.title("👨‍💼 Admin Dashboard")
    st.markdown("### System Management & Configuration")
    st.markdown("---")

    # Sidebar
    with st.sidebar:
        st.header("👤 Current Role")
        st.success("👨‍💼 Administrator")

        if st.button("🔄 Switch Role"):
            st.session_state.user_role = None
            # Reset initialization flags
            if 'fe_initialized' in st.session_state:
                del st.session_state.fe_initialized
            if 'admin_initialized' in st.session_state:
                del st.session_state.admin_initialized
            st.cache_resource.clear()
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")
        st.header("🔧 Configuration")
        st.success("✅ Supabase Connected")
        st.info("💡 OpenAI Enabled")

        st.markdown("---")
        st.header("🎯 Quick Actions")

        if st.button("🔄 Refresh Data"):
            st.cache_resource.clear()
            st.rerun()

    # Admin Tabs
    admin_tab1, admin_tab2 = st.tabs(["📊 Overview", "📄 View Bills"])

    # Overview Tab (existing content)
    with admin_tab1:
        st.header("📊 System Overview")
        # ...existing admin overview/dashboard code...

    # View Bills Tab
    with admin_tab2:
        st.header("📄 All Generated Bills")
        try:
            bills = db.get_all_bills()
            if bills:
                import pandas as pd
                df = pd.DataFrame(bills)
                df['created_at'] = pd.to_datetime(df['created_at'])
                df = df.sort_values('created_at', ascending=False)
                st.dataframe(df, width='stretch')
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Bills CSV",
                    data=csv,
                    file_name=f"all_bills_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No bills found.")
        except Exception as e:
            st.error(f"Error loading bills: {str(e)}")

    # Admin Main Content Tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "📊 Dashboard", 
        "🔄 Full Workflow Test", 
        "🔐 Auth0 Testing",
        "💳 Payment Status",
        "⏰ Scheduler",
        "🧮 Tariff Calculator", 
        "📋 Meter Readings", 
        "💰 Generate Bill",
        "📈 Analytics & Reports"
    ])

    # Tab 1: Dashboard
    with tab1:
        st.header("📊 System Overview")
        
        # Meter filter and refresh
        col_filter1, col_filter2, col_filter3 = st.columns([2, 1, 1])
        
        with col_filter1:
            dashboard_meter = st.text_input("View readings for Meter ID:", value="METER001", key="dashboard_meter_filter")
        
        with col_filter2:
            st.write("")
            st.write("")
            if st.button("🔍 Load Readings", type="primary", width='stretch', key="dashboard_load"):
                st.cache_resource.clear()
                st.rerun()
        
        with col_filter3:
            st.write("")
            st.write("")
            if st.button("🔄 Refresh All", width='stretch', key="dashboard_refresh"):
                st.cache_resource.clear()
                st.rerun()
        
        st.markdown("---")
    
        col1, col2, col3 = st.columns(3)
    
        # Get meter readings
        try:
            readings = db.get_historical_readings(dashboard_meter, limit=100)
        
            with col1:
                st.metric("Total Readings", len(readings))
        
            with col2:
                if readings:
                    latest = readings[0]
                    st.metric("Latest Reading", f"{latest['reading_value']} kWh")
        
            with col3:
                if len(readings) >= 2:
                    consumption = readings[0]['reading_value'] - readings[1]['reading_value']
                    st.metric("Last Month Consumption", f"{consumption:.2f} kWh")
        
            st.markdown("---")
        
            # Recent Readings Table
            if readings:
                st.subheader(f"📈 Recent Meter Readings - {dashboard_meter}")
                import pandas as pd
                df = pd.DataFrame(readings[:10])
                df['reading_date'] = pd.to_datetime(df['reading_date'])
                df = df.sort_values('reading_date', ascending=False)
                st.dataframe(df[['reading_date', 'reading_value', 'meter_id', 'customer_id']], width='stretch')
                
                # Show last updated time
                st.caption(f"🕒 Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                st.warning(f"No meter readings found for {dashboard_meter}. Field engineers can add readings, or check the meter ID.")
    
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")

    # Tab 2: Full Workflow Test (Based on n8n)
    with tab2:
        st.header("🔄 Complete Workflow Test")
        st.markdown("### Testing all 13 steps from n8n workflow")
    
        # Show workflow steps
        with st.expander("📋 View Complete Workflow Steps", expanded=False):
            steps = [
                "1️⃣ Webhook - Receive meter reading",
                "2️⃣ Auth0 Token Verification",
                "3️⃣ Get Historical Readings from DB",
                "4️⃣ Get Tariff Rules from Neo4j",
                "5️⃣ AI Validation Agent - Validate reading",
                "6️⃣ AI Calculation Agent - Calculate bill",
                "7️⃣ Store Bill in Database",
                "8️⃣ Save Bill to Neo4j Graph",
                "9️⃣ Create Stripe Payment Link",
                "🔟 Update DB with Payment Info",
                "1️⃣1️⃣ AI Notification Agent - Generate message",
                "1️⃣2️⃣ Send Discord Notification",
                "1️⃣3️⃣ Log Notification in DB"
            ]
            for step in steps:
                st.write(step)
    
        st.markdown("---")
    
        # Option to fetch latest reading from database
        st.markdown("### 📥 Fetch Reading from Database")
        
        col_fetch1, col_fetch2, col_fetch3 = st.columns([2, 1, 1])
        
        with col_fetch1:
            fetch_meter_id = st.text_input("Enter Meter ID to fetch latest reading", value="METER001", key="fetch_meter_input")
        
        with col_fetch2:
            st.write("")
            st.write("")
            if st.button("🔍 Fetch Latest Reading", type="secondary", width='stretch'):
                try:
                    latest_readings = db.get_historical_readings(fetch_meter_id, limit=1)
                    if latest_readings:
                        st.session_state['fetched_reading'] = latest_readings[0]
                        st.session_state['fetched_meter_id'] = fetch_meter_id
                        st.success(f"✅ Fetched reading: {latest_readings[0]['reading_value']} kWh")
                    else:
                        st.warning(f"No readings found for {fetch_meter_id}")
                except Exception as e:
                    st.error(f"Error fetching: {str(e)}")
        
        with col_fetch3:
            st.write("")
            st.write("")
            if st.button("🔄 Refresh", width='stretch'):
                st.cache_resource.clear()
                st.rerun()
        
        # Display fetched reading
        if 'fetched_reading' in st.session_state and st.session_state.get('fetched_reading'):
            reading = st.session_state['fetched_reading']
            st.info(f"📊 **Latest Reading from DB:** {reading['reading_value']} kWh | Date: {reading['reading_date']} | Customer: {reading['customer_id']}")
        
        st.markdown("---")
        
        # Input form
        with st.form("workflow_test"):
            st.subheader("📥 Step 1: Input Meter Reading")
        
            col1, col2 = st.columns(2)
            with col1:
                # Pre-fill with fetched data if available
                default_meter = st.session_state.get('fetched_meter_id', 'METER001')
                default_customer = st.session_state.get('fetched_reading', {}).get('customer_id', 'CUST001')
                default_reading = st.session_state.get('fetched_reading', {}).get('reading_value', 4600.0)
                
                meter_id = st.text_input("Meter ID", value=default_meter, key="wf_meter_id")
                customer_id = st.text_input("Customer ID", value=default_customer, key="wf_customer_id")
                reading_value = st.number_input("Reading Value (kWh)", min_value=0.0, value=float(default_reading), step=0.1, key="wf_reading")
        
            with col2:
                reading_date = st.date_input("Reading Date", value=datetime.now(), key="wf_date")
                customer_phone = st.text_input("Customer Phone", value="+1234567890", key="wf_phone")
                discord_user_id = st.text_input("Discord User ID (optional - for direct mention)", value="", key="wf_discord_id", help="Right-click on yourself in Discord > Copy User ID")
                user_id = st.text_input("User ID (for Auth)", value="auth0|user123", key="wf_user_id")
                jwt_token = st.text_input("JWT Token (optional - for real Auth0 verification)", value="", type="password", key="wf_jwt_token")
        
            submit = st.form_submit_button("🚀 Run Complete Workflow", type="primary")
    
        if submit:
            # Progress tracking
            progress_bar = st.progress(0)
            status_container = st.container()
        
            with status_container:
                try:
                    # Import services
                    from services.ai_agent_service import AIAgentService
                    from services.payment_service import PaymentService
                    from services.discord_service import DiscordService
                    from services.auth_service import AuthService
                
                    ai_service = AIAgentService()
                    payment_service = PaymentService()
                    discord_service = DiscordService()
                    auth_service = AuthService()
                
                    # Step 1: Webhook (already received)
                    st.success("✅ Step 1: Webhook received meter reading")
                    progress_bar.progress(8)
                
                    # Step 2: Auth0 Verification
                    st.info("🔐 Step 2: Auth0 token verification...")
                
                    if jwt_token:
                        # Real JWT verification
                        if auth_service.auth0_enabled:
                            payload = auth_service.verify_token(jwt_token)
                            if payload:
                                st.success(f"✅ Step 2: Auth0 JWT verified - User: {payload.get('sub', 'Unknown')}")
                            else:
                                st.error("❌ Step 2: Invalid or expired JWT token")
                                st.stop()
                        else:
                            st.error("❌ Step 2: Auth0 not configured - Cannot verify JWT token")
                            st.info("💡 Configure AUTH0_DOMAIN and AUTH0_API_IDENTIFIER in .env to enable real verification")
                            st.stop()
                    else:
                        # Fallback to user_id validation
                        if user_id and user_id.startswith("auth0|"):
                            st.warning(f"⚠️ Step 2: Bypassing Auth0 (no JWT provided) - User: {user_id}")
                        else:
                            st.error("❌ Step 2: Invalid user ID format - must start with 'auth0|' or provide JWT token")
                            st.stop()
                        
                    progress_bar.progress(15)
                
                    # Step 3: Get Historical Readings
                    st.info("📊 Step 3: Fetching historical readings...")
                    historical_readings = db.get_historical_readings(meter_id, limit=10)
                    st.success(f"✅ Step 3: Retrieved {len(historical_readings)} historical readings")
                    progress_bar.progress(23)
                
                    # Step 4: Get Tariff Rules (from service)
                    st.info("💰 Step 4: Loading tariff rules...")
                    st.success("✅ Step 4: Tariff rules loaded (Neo4j simulated)")
                    progress_bar.progress(31)
                
                    # Step 5: AI Validation
                    st.info("🤖 Step 5: AI validating meter reading...")
                    validation = ai_service.validate_meter_reading(
                        historical_readings=historical_readings,
                        new_reading={
                            "meter_id": meter_id,
                            "reading_value": reading_value,
                            "reading_date": reading_date.strftime("%Y-%m-%d")
                        }
                    )
                
                    if validation['valid']:
                        st.success(f"✅ Step 5: Reading validated - {validation['reason']} (Confidence: {validation['confidence']}%)")
                        progress_bar.progress(38)
                    else:
                        st.error(f"❌ Step 5: Invalid reading - {validation['reason']}")
                        st.stop()
                
                    # Step 6: AI Bill Calculation
                    st.info("🧮 Step 6: AI calculating electricity bill...")
                    if len(historical_readings) > 0:
                        previous_reading = historical_readings[0]['reading_value']
                        consumption = reading_value - previous_reading
                    else:
                        previous_reading = 0
                        consumption = reading_value
                
                    bill_calculation = ai_service.calculate_bill(
                        current_reading=reading_value,
                        previous_reading=previous_reading,
                        meter_id=meter_id,
                        customer_id=customer_id
                    )
                
                    st.success(f"✅ Step 6: Bill calculated - ₹{bill_calculation['total_amount']:,.2f} for {bill_calculation['consumption_kwh']:.2f} kWh")
                
                    # Show breakdown
                    with st.expander("View Bill Breakdown"):
                        st.json(bill_calculation)
                
                    progress_bar.progress(46)
                
                    # Step 7: Store Bill in DB
                    st.info("💾 Step 7: Storing bill in database...")
                    bill_data = {
                        "customer_id": customer_id,
                        "meter_id": meter_id,
                        "billing_period_start": historical_readings[0]['reading_date'] if historical_readings else reading_date.strftime("%Y-%m-%d"),
                        "billing_period_end": reading_date.strftime("%Y-%m-%d"),
                        "consumption_kwh": consumption,
                        "amount": bill_calculation['total_amount'],
                        "status": "pending",
                        "created_at": datetime.now().isoformat()
                    }
                
                    created_bill = db.create_bill(bill_data)
                    bill_id = created_bill.get('id', 'BILL_' + datetime.now().strftime("%Y%m%d%H%M%S"))
                    st.success(f"✅ Step 7: Bill stored with ID: {bill_id}")
                    progress_bar.progress(54)
                
                    # Step 8: Save to Neo4j
                    st.info("🔗 Step 8: Saving bill to Neo4j graph...")
                    st.success("✅ Step 8: Bill saved to Neo4j (Simulated)")
                    progress_bar.progress(62)
                
                    # Step 9: Create Stripe Payment Link
                    st.info("💳 Step 9: Creating Stripe payment link...")
                    payment_link = payment_service.create_payment_link(
                        amount=bill_calculation['total_amount'],
                        currency="INR",
                        description=f"Electricity Bill - {meter_id}",
                        metadata={
                            "bill_id": str(bill_id),
                            "customer_id": customer_id,
                            "meter_id": meter_id
                        }
                    )
                    st.success(f"✅ Step 9: Payment link created: {payment_link['url']}")
                    progress_bar.progress(69)
                
                    # Step 10: Update DB with Payment Link
                    st.info("🔄 Step 10: Updating bill with payment link...")
                    db.update_bill_payment_info(bill_id, payment_link['url'], payment_link['id'])
                    st.success("✅ Step 10: Bill updated with payment information")
                    progress_bar.progress(77)
                
                    # Step 11: AI Notification Message
                    st.info("📝 Step 11: AI generating notification message...")
                    notification_message = ai_service.generate_notification_message(
                        customer_id=customer_id,
                        bill_amount=bill_calculation['total_amount'],
                        consumption_kwh=consumption,
                        payment_link=payment_link['url']
                    )
                    st.success(f"✅ Step 11: Notification message generated")
                    st.info(f"Message: {notification_message}")
                    progress_bar.progress(85)
                
                    # Step 12: Send Discord Notification
                    st.info("💬 Step 12: Sending Discord notification...")
                    discord_result = discord_service.send_bill_notification(
                        customer_id=customer_id,
                        bill_id=str(bill_id),
                        amount=bill_calculation['total_amount'],
                        due_date=bill_data['billing_period_end'],
                        payment_link=payment_link['url'],
                        discord_user_id=discord_user_id if discord_user_id else None
                    )
                    if discord_result.get('success'):
                        if discord_user_id:
                            st.success(f"✅ Step 12: Discord notification sent with mention to user {discord_user_id}")
                        else:
                            st.success(f"✅ Step 12: Discord notification sent to channel")
                    else:
                        st.warning(f"⚠️ Step 12: Discord notification failed: {discord_result.get('error', 'Unknown error')}")
                    progress_bar.progress(92)
                
                    # Step 13: Log Notification
                    st.info("📋 Step 13: Logging notification...")
                    db.log_notification({
                        "bill_id": bill_id,
                        "customer_id": customer_id,
                        "channel": "discord",
                        "message": notification_message,
                        "status": "sent" if discord_result.get('success') else "failed",
                        "sent_at": datetime.now().isoformat()
                    })
                    st.success("✅ Step 13: Notification logged")
                    progress_bar.progress(100)
                
                    # Final Summary
                    st.markdown("---")
                    st.success("### 🎉 Workflow Completed Successfully!")
                
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Bill Amount", f"₹{bill_calculation['total_amount']:,.2f}")
                    with col2:
                        st.metric("Consumption", f"{consumption:.2f} kWh")
                    with col3:
                        st.metric("Status", "Pending Payment")
                
                    st.markdown("---")
                    st.markdown("#### 📄 Complete Bill Details")
                    st.write(f"**Bill ID**: {bill_id}")
                    st.write(f"**Customer**: {customer_id}")
                    st.write(f"**Meter**: {meter_id}")
                    st.write(f"**Period**: {bill_data['billing_period_start']} to {bill_data['billing_period_end']}")
                    st.write(f"**Payment Link**: {payment_link['url']}")
                    st.write(f"**Discord Notification**: Sent to billing channel")
                
                    # Store bill info in session state for payment confirmation
                    st.session_state['last_bill_id'] = bill_id
                    st.session_state['last_bill_amount'] = bill_calculation['total_amount']
                    st.session_state['last_customer_id'] = customer_id
                    st.session_state['last_discord_user_id'] = discord_user_id
                
                except Exception as e:
                    st.error(f"❌ Error in workflow: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
    
        # Payment Confirmation Section (outside the form/submit block)
        st.markdown("---")
        st.markdown("### 💳 Payment Confirmation")
    
        if 'last_bill_id' in st.session_state and st.session_state.get('last_bill_id'):
            bill_id = st.session_state['last_bill_id']
            amount = st.session_state.get('last_bill_amount', 0)
            customer_id = st.session_state.get('last_customer_id', '')
            discord_user_id = st.session_state.get('last_discord_user_id', '')
        
            st.info(f"📄 Last created bill: **#{bill_id}** - Amount: **₹{amount:,.2f}**")
            st.write("After completing payment via Stripe, click below to send confirmation notification:")
        
            if st.button("✅ I've Paid This Bill", type="primary", key="confirm_payment_main"):
                try:
                    with st.spinner("Processing payment confirmation..."):
                        from services.ai_agent_service import AIAgentService
                        from services.discord_service import DiscordService
                    
                        ai_service = AIAgentService()
                        discord_service = DiscordService()
                    
                        # Mark bill as paid
                        db.update_bill_status(
                            bill_id=bill_id,
                            status='paid'
                        )
                        st.success("✓ Bill marked as paid")
                    
                        # Generate AI thank you message
                        try:
                            thank_you_message = ai_service.generate_payment_confirmation_message(
                                customer_id=customer_id,
                                bill_id=bill_id,
                                amount=amount
                            )
                            st.success("✓ Thank you message generated")
                        except Exception as e:
                            st.warning(f"⚠️ Using default message")
                            thank_you_message = f"Thank you for your payment of ₹{amount:.2f}! Your bill #{bill_id} has been successfully paid."
                    
                        # Send Discord payment confirmation
                        discord_confirm = discord_service.send_payment_confirmation(
                            customer_id=customer_id,
                            bill_id=str(bill_id),
                            amount=amount,
                            payment_date=datetime.now().isoformat(),
                            discord_user_id=discord_user_id if discord_user_id else None
                        )
                    
                        # Log confirmation notification
                        db.log_notification({
                            "bill_id": bill_id,
                            "customer_id": customer_id,
                            "channel": "discord",
                            "message": thank_you_message,
                            "status": "sent" if discord_confirm.get('success') else "failed",
                            "sent_at": datetime.now().isoformat()
                        })
                    
                        if discord_confirm.get('success'):
                            st.success("🎉 Payment confirmed! Discord notification sent.")
                            st.balloons()
                            # Clear the session state
                            st.session_state['last_bill_id'] = None
                        else:
                            st.error(f"⚠️ Bill marked as paid, but Discord notification failed: {discord_confirm.get('error', 'Unknown')}")
            
                except Exception as e:
                    st.error(f"❌ Error processing payment: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
        else:
            st.info("Create a bill using the workflow above first, then you can confirm payment here.")


    # Tab 3: Auth0 Testing
    with tab3:
        st.header("🔐 Auth0 Authentication Testing")
    
        from services.auth_service import AuthService
        from config import Config
    
        auth_service = AuthService()
    
        # Display configuration
        col1, col2 = st.columns(2)
    
        with col1:
            st.subheader("⚙️ Configuration")
            st.info(f"**Domain**: `{Config.AUTH0_DOMAIN}`")
            st.info(f"**API Identifier**: `{Config.AUTH0_API_IDENTIFIER}`")
        
            if auth_service.auth0_enabled:
                st.success("✅ Auth0 is enabled and configured")
            else:
                st.error("❌ Auth0 is not properly configured")
                st.warning("Check your .env file for AUTH0_DOMAIN and AUTH0_API_IDENTIFIER")
    
        with col2:
            st.subheader("📋 Client Credentials")
            st.code("""
    Client ID: RPLT6bQjGu2VyYKIQeqRADR8tEEoEkeU
    Client Secret: MYLP0sn...
    (from Auth0 Dashboard)
            """, language="text")
    
        st.markdown("---")
    
        # Get Token Section
        st.subheader("1️⃣ Get Access Token")
    
        with st.expander("📘 How to get a token", expanded=False):
            st.markdown("""
            **Option 1: Using curl (PowerShell)**
            ```powershell
            curl --request POST `
              --url https://dev-t6knva248r1jkkvn.us.auth0.com/oauth/token `
              --header 'content-type: application/json' `
              --data '{
                "client_id":"RPLT6bQjGu2VyYKIQeqRADR8tEEoEkeU",
                "client_secret":"MYLP0sn39jeJ-HJA9yzWuPxCvc5deOTTziHiR2yddeBilfF-3uDAq0aBojZXEU9b",
                "audience":"https://billing-api.example.com",
                "grant_type":"client_credentials"
              }'
            ```
        
            **Option 2: Using Python**
            ```python
            import requests
        
            response = requests.post(
                'https://dev-t6knva248r1jkkvn.us.auth0.com/oauth/token',
                json={
                    'client_id': 'RPLT6bQjGu2VyYKIQeqRADR8tEEoEkeU',
                    'client_secret': 'YOUR_SECRET',
                    'audience': 'https://billing-api.example.com',
                    'grant_type': 'client_credentials'
                }
            )
            token = response.json()['access_token']
            ```
            """)
    
        # Token input
        token_input = st.text_area(
            "Paste your Auth0 JWT token here:",
            height=150,
            placeholder="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ij...",
            help="Get a token using the curl command above"
        )
    
        # Load saved token
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("📁 Load Saved Token"):
                try:
                    with open('.auth0_token.txt', 'r') as f:
                        saved_token = f.read().strip()
                        st.session_state['auth_token'] = saved_token
                        st.success("✅ Loaded saved token")
                        st.rerun()
                except FileNotFoundError:
                    st.error("No saved token found")
    
        with col2:
            if token_input and st.button("💾 Save Token"):
                with open('.auth0_token.txt', 'w') as f:
                    f.write(token_input)
                st.success("✅ Token saved to .auth0_token.txt")
    
        # Use session state for token
        if 'auth_token' not in st.session_state and token_input:
            st.session_state['auth_token'] = token_input
    
        current_token = st.session_state.get('auth_token', token_input)
    
        if current_token:
            st.markdown("---")
            st.subheader("2️⃣ Verify Token")
        
            if st.button("🔍 Verify Token", type="primary"):
                try:
                    import requests
                    from jose import jwt
                
                    with st.spinner("Verifying token..."):
                        # Fetch public keys
                        jwks_url = f"https://{Config.AUTH0_DOMAIN}/.well-known/jwks.json"
                        jwks_response = requests.get(jwks_url, timeout=10)
                        jwks = jwks_response.json()
                    
                        # Decode header
                        unverified_header = jwt.get_unverified_header(current_token)
                    
                        # Find matching key
                        rsa_key = {}
                        for key in jwks["keys"]:
                            if key["kid"] == unverified_header["kid"]:
                                rsa_key = {
                                    "kty": key["kty"],
                                    "kid": key["kid"],
                                    "use": key["use"],
                                    "n": key["n"],
                                    "e": key["e"]
                                }
                                break
                    
                        if not rsa_key:
                            st.error("❌ No matching public key found")
                        else:
                            # Verify token
                            payload = jwt.decode(
                                current_token,
                                rsa_key,
                                algorithms=["RS256"],
                                audience=Config.AUTH0_API_IDENTIFIER,
                                issuer=f"https://{Config.AUTH0_DOMAIN}/"
                            )
                        
                            st.success("✅ Token Verified Successfully!")
                        
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Issuer", payload.get('iss', 'N/A').split('//')[1].split('/')[0])
                            with col2:
                                st.metric("Audience", "billing-api")
                            with col3:
                                from datetime import datetime
                                exp_time = datetime.fromtimestamp(payload.get('exp', 0))
                                st.metric("Expires", exp_time.strftime("%H:%M:%S"))
                        
                            st.json(payload)
                        
                except jwt.ExpiredSignatureError:
                    st.error("❌ Token has expired. Get a new one!")
                except jwt.JWTClaimsError as e:
                    st.error(f"❌ JWT Claims Error: {e}")
                except Exception as e:
                    st.error(f"❌ Verification failed: {str(e)}")
                    with st.expander("See error details"):
                        import traceback
                        st.code(traceback.format_exc())
        
            st.markdown("---")
            st.subheader("3️⃣ Test API Endpoint")
        
            st.info("💡 This simulates calling the /webhook/meter-reading endpoint with Auth0 authentication")
        
            with st.form("test_auth_api"):
                col1, col2 = st.columns(2)
                with col1:
                    meter_id = st.text_input("Meter ID", value="METER001", key="auth_meter_id")
                    customer_id = st.text_input("Customer ID", value="CUST001", key="auth_customer_id")
                    reading_value = st.number_input("Reading Value", value=4800.0, key="auth_reading")
            
                with col2:
                    customer_phone = st.text_input("Phone", value="+919876543210", key="auth_phone")
                    reading_date = st.date_input("Reading Date", value=datetime.now(), key="auth_date")
            
                if st.form_submit_button("🚀 Test Authenticated Request", type="primary"):
                    try:
                        # Verify token first
                        user_info = auth_service.verify_token(current_token)
                    
                        if not user_info:
                            st.error("❌ Invalid or expired token")
                        else:
                            st.success(f"✅ Token validated for: {user_info.get('sub')}")
                        
                            # Simulate the billing workflow
                            with st.spinner("Processing authenticated request..."):
                                from services.ai_agent_service import AIAgentService
                            
                                ai_service = AIAgentService()
                            
                                # Get historical data
                                historical = db.get_historical_readings(meter_id, limit=5)
                            
                                if historical:
                                    # Validate
                                    validation = ai_service.validate_meter_reading(
                                        historical_readings=historical,
                                        new_reading={
                                            "meter_id": meter_id,
                                            "reading_value": reading_value,
                                            "reading_date": reading_date.strftime("%Y-%m-%d")
                                        }
                                    )
                                
                                    if validation['valid']:
                                        # Calculate
                                        previous = historical[0]['reading_value']
                                        bill = ai_service.calculate_bill(
                                            current_reading=reading_value,
                                            previous_reading=previous,
                                            meter_id=meter_id,
                                            customer_id=customer_id
                                        )
                                    
                                        st.success("✅ Authenticated request processed successfully!")
                                    
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            st.metric("Consumption", f"{bill['consumption_kwh']:.2f} kWh")
                                        with col2:
                                            st.metric("Bill Amount", f"₹{bill['total_amount']:,.2f}")
                                        with col3:
                                            st.metric("Status", "✅ Validated")
                                    
                                        with st.expander("📋 Full Response"):
                                            st.json({
                                                "success": True,
                                                "authenticated_user": user_info.get('sub'),
                                                "validation": validation,
                                                "calculation": bill
                                            })
                                    else:
                                        st.warning(f"⚠️ Validation failed: {validation['reason']}")
                                else:
                                    st.error("No historical data found for meter")
                
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        with st.expander("See details"):
                            import traceback
                            st.code(traceback.format_exc())
    
        else:
            st.info("👆 Paste your Auth0 token above to start testing")

    # Tab 4: Payment Status
    with tab4:
        st.header("💳 Payment Status Management")
    
        st.markdown("""
        Track and manage bill payment status with Stripe integration.
        - View bill details and payment status
        - Get all bills for a customer
        - Update bill status manually
        - Simulate Stripe webhook events
        """)
    
        # Quick Pay Section
        st.markdown("### 💳 Quick Payment")
        col1, col2, col3 = st.columns([2, 2, 1])
    
        with col1:
            quick_bill_id = st.number_input("Enter Bill ID to Pay", min_value=1, value=1, step=1, key="quick_pay_bill_id")
    
        with col2:
            if st.button("🔍 Fetch Bill Details", type="secondary", key="quick_fetch"):
                try:
                    bill = db.get_bill_by_id(quick_bill_id)
                    if bill:
                        st.session_state['quick_pay_bill'] = bill
                    else:
                        st.error(f"Bill #{quick_bill_id} not found")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
        with col3:
            if 'quick_pay_bill' in st.session_state and st.session_state['quick_pay_bill']:
                bill = st.session_state['quick_pay_bill']
                if bill.get('status', '').lower() == 'pending' and bill.get('payment_link'):
                    st.markdown(f"[**💳 Pay ₹{bill.get('amount', 0):,.2f}**]({bill.get('payment_link')})")
                elif bill.get('status', '').lower() == 'paid':
                    st.success("✅ Already Paid")
    
        st.markdown("---")
    
        # Sub-tabs for payment features
        subtab1, subtab2, subtab3, subtab4 = st.tabs([
            "🔍 Get Bill Status",
            "👤 Customer Bills",
            "✏️ Update Status",
            "🎣 Webhook Simulator"
        ])
    
        # Subtab 1: Get Bill Status
        with subtab1:
            st.subheader("🔍 Get Bill Status by ID")
        
            bill_id = st.number_input("Bill ID", min_value=1, value=1, step=1)
        
            if st.button("📋 Get Bill", type="primary"):
                try:
                    bill = db.get_bill_by_id(bill_id)
                
                    if bill:
                        st.success(f"✅ Bill {bill_id} found")
                    
                        # Display bill info
                        col1, col2, col3, col4 = st.columns(4)
                    
                        with col1:
                            st.metric("Status", bill.get('status', 'N/A').upper())
                        with col2:
                            st.metric("Amount", f"₹{bill.get('amount', 0):,.2f}")
                        with col3:
                            st.metric("Consumption", f"{bill.get('consumption_kwh', 0):.2f} kWh")
                        with col4:
                            payment_date = bill.get('payment_date', 'Not paid')
                            st.metric("Payment Date", payment_date if payment_date != 'Not paid' else '⏳ Pending')
                    
                        st.markdown("---")
                    
                        # Full bill details
                        with st.expander("📄 Full Bill Details", expanded=True):
                            col1, col2 = st.columns(2)
                        
                            with col1:
                                st.write("**Customer Information:**")
                                st.write(f"Customer ID: `{bill.get('customer_id')}`")
                                st.write(f"Meter ID: `{bill.get('meter_id')}`")
                            
                                st.write("\n**Billing Period:**")
                                st.write(f"Start: {bill.get('billing_period_start')}")
                                st.write(f"End: {bill.get('billing_period_end')}")
                        
                            with col2:
                                st.write("**Payment Information:**")
                                if bill.get('payment_link'):
                                    st.write(f"Payment Link: [Click here]({bill.get('payment_link')})")
                                
                                    # Add Pay Now button if bill is pending
                                    if bill.get('status', '').lower() == 'pending':
                                        if st.button("💳 Pay Now", key=f"pay_bill_{bill_id}", type="primary"):
                                            st.info(f"🔗 Opening payment link...")
                                            st.markdown(f"[**Click here to pay ₹{bill.get('amount', 0):.2f}**]({bill.get('payment_link')})")
                                            st.success("💡 Click the link above to complete payment in a new tab")
                                else:
                                    st.write("Payment Link: Not available")
                            
                                st.write(f"Link ID: `{bill.get('payment_link_id', 'N/A')}`")
                            
                                st.write("\n**Timestamps:**")
                                st.write(f"Created: {bill.get('created_at')}")
                                st.write(f"Updated: {bill.get('updated_at', 'N/A')}")
                    
                        # JSON view
                        with st.expander("🔧 Raw JSON"):
                            st.json(bill)
                    else:
                        st.error(f"❌ Bill {bill_id} not found")
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
        # Subtab 2: Customer Bills
        with subtab2:
            st.subheader("👤 Get All Bills for Customer")
        
            col1, col2 = st.columns([3, 1])
        
            with col1:
                customer_id_search = st.text_input("Customer ID", value="CUST001", key="payment_customer_search")
            with col2:
                limit = st.number_input("Limit", min_value=1, max_value=100, value=10)
        
            if st.button("🔍 Get Customer Bills", type="primary"):
                try:
                    bills = db.get_bills_by_customer(customer_id_search, limit=limit)
                
                    if bills:
                        st.success(f"✅ Found {len(bills)} bills for {customer_id_search}")
                    
                        # Summary metrics
                        col1, col2, col3 = st.columns(3)
                    
                        total_amount = sum(b.get('amount', 0) for b in bills)
                        paid_bills = sum(1 for b in bills if b.get('status') == 'paid')
                        pending_bills = sum(1 for b in bills if b.get('status') == 'pending')
                    
                        with col1:
                            st.metric("Total Amount", f"₹{total_amount:,.2f}")
                        with col2:
                            st.metric("Paid Bills", f"{paid_bills}/{len(bills)}")
                        with col3:
                            st.metric("Pending Bills", pending_bills)
                    
                        st.markdown("---")
                    
                        # Bills table
                        import pandas as pd
                        df = pd.DataFrame(bills)
                    
                        # Format display columns
                        display_columns = ['id', 'status', 'amount', 'consumption_kwh', 'billing_period_end', 'created_at']
                        available_columns = [col for col in display_columns if col in df.columns]
                    
                        st.dataframe(
                            df[available_columns],
                            width='stretch',
                            hide_index=True
                        )
                    
                        # Individual bill details with payment option
                        with st.expander("📋 View Individual Bills & Pay"):
                            for bill in bills:
                                with st.container():
                                    col_a, col_b = st.columns([3, 1])
                                
                                    with col_a:
                                        st.write(f"**Bill ID: {bill.get('id')}** - Status: `{bill.get('status')}`")
                                        cols = st.columns(4)
                                        cols[0].write(f"Amount: ₹{bill.get('amount', 0):,.2f}")
                                        cols[1].write(f"Consumption: {bill.get('consumption_kwh', 0):.2f} kWh")
                                        cols[2].write(f"Period: {bill.get('billing_period_end')}")
                                        cols[3].write(f"Created: {bill.get('created_at')}")
                                
                                    with col_b:
                                        # Add payment button for pending bills
                                        if bill.get('status', '').lower() == 'pending' and bill.get('payment_link'):
                                            if st.button(f"💳 Pay ₹{bill.get('amount', 0):,.2f}", 
                                                       key=f"pay_customer_bill_{bill.get('id')}", 
                                                       type="primary",
                                                       width='stretch'):
                                                st.markdown(f"[**Click to Pay Now**]({bill.get('payment_link')})")
                                        elif bill.get('status', '').lower() == 'paid':
                                            st.success("✅ Paid")
                                
                                    st.markdown("---")
                    else:
                        st.warning(f"No bills found for customer {customer_id_search}")
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
        # Subtab 3: Update Status
        with subtab3:
            st.subheader("✏️ Manually Update Bill Status")
        
            st.info("⚠️ This is for testing/admin purposes. In production, status is updated automatically via Stripe webhooks.")
        
            col1, col2 = st.columns(2)
        
            with col1:
                update_bill_id = st.number_input("Bill ID to Update", min_value=1, value=1, step=1)
        
            with col2:
                new_status = st.selectbox(
                    "New Status",
                    options=["pending", "paid", "failed", "cancelled"],
                    index=0
                )
        
            payment_date_input = st.date_input("Payment Date (optional, only for 'paid' status)")
        
            if st.button("💾 Update Bill Status", type="primary"):
                try:
                    payment_date_str = payment_date_input.strftime("%Y-%m-%d") if new_status == "paid" else None
                
                    updated_bill = db.update_bill_status(
                        bill_id=update_bill_id,
                        status=new_status,
                        payment_date=payment_date_str
                    )
                
                    if updated_bill:
                        st.success(f"✅ Bill {update_bill_id} status updated to '{new_status}'")
                    
                        with st.expander("📄 Updated Bill Details"):
                            st.json(updated_bill)
                    else:
                        st.error(f"❌ Failed to update bill {update_bill_id}")
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
        # Subtab 4: Webhook Simulator
        with subtab4:
            st.subheader("🎣 Stripe Webhook Simulator")
        
            st.markdown("""
            Simulate Stripe webhook events to test payment status updates.
            This mimics what happens when a customer completes payment via Stripe.
            """)
        
            col1, col2 = st.columns(2)
        
            with col1:
                webhook_bill_id = st.number_input("Bill ID for Webhook", min_value=1, value=1, step=1)
        
            with col2:
                event_type = st.selectbox(
                    "Event Type",
                    options=[
                        "checkout.session.completed",
                        "payment_intent.succeeded"
                    ],
                    index=0
                )
        
            if st.button("📡 Send Webhook Event", type="primary"):
                try:
                    import requests
                
                    # Create mock webhook payload
                    webhook_payload = {
                        "type": event_type,
                        "data": {
                            "object": {
                                "metadata": {
                                    "bill_id": str(webhook_bill_id)
                                },
                                "payment_status": "paid" if event_type == "checkout.session.completed" else None,
                                "status": "succeeded" if event_type == "payment_intent.succeeded" else None
                            }
                        }
                    }
                
                    # Send to local webhook endpoint (if Flask is running)
                    try:
                        response = requests.post(
                            "http://localhost:5000/webhook/stripe",
                            json=webhook_payload,
                            timeout=5
                        )
                    
                        if response.status_code == 200:
                            st.success(f"✅ Webhook sent successfully!")
                            st.write(f"Response: {response.json()}")
                        
                            # Check updated bill
                            updated = db.get_bill_by_id(webhook_bill_id)
                            if updated and updated.get('status') == 'paid':
                                st.success(f"✅ Bill {webhook_bill_id} marked as PAID")
                                with st.expander("📄 Updated Bill"):
                                    st.json(updated)
                        else:
                            st.error(f"❌ Webhook failed: {response.status_code}")
                            st.write(response.text)
                        
                    except requests.exceptions.ConnectionError:
                        st.warning("⚠️ Flask server not running. Updating status directly...")
                    
                        # Direct database update as fallback
                        updated = db.update_bill_status(
                            bill_id=webhook_bill_id,
                            status='paid',
                            payment_date=datetime.now().strftime("%Y-%m-%d")
                        )
                    
                        if updated:
                            st.success(f"✅ Bill {webhook_bill_id} marked as PAID (direct update)")
                        
                            # Log the event
                            db.log_payment_event({
                                'bill_id': webhook_bill_id,
                                'event_type': event_type,
                                'payment_link_id': f"test_{webhook_bill_id}",
                                'stripe_event_id': f"evt_test_{int(datetime.now().timestamp())}",
                                'event_data': webhook_payload,
                                'received_at': datetime.now().isoformat()
                            })
                        
                            with st.expander("📄 Updated Bill"):
                                st.json(updated)
                        else:
                            st.error("❌ Failed to update bill status")
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    import traceback
                    with st.expander("See error details"):
                        st.code(traceback.format_exc())

    # Tab 5: Scheduler
    with tab5:
        st.header("⏰ Automated Billing Scheduler")
    
        st.markdown("""
        The scheduler automates recurring billing tasks:
        - **Monthly Bill Generation** - 1st of every month at 2:00 AM
        - **Payment Reminders** - Daily at 10:00 AM
        - **Overdue Bill Marking** - Daily at 11:00 AM
        - **Meter Reading Collection** - Every Sunday at 8:00 AM
        """)
    
        st.markdown("---")
    
        # Scheduler status
        from services import get_scheduler
    
        scheduler = get_scheduler()
    
        col1, col2 = st.columns(2)
    
        with col1:
            if scheduler.scheduler.running:
                st.success("🟢 Scheduler is running")
            else:
                st.warning("🟡 Scheduler is stopped")
                if st.button("▶️ Start Scheduler"):
                    scheduler.start()
                    st.rerun()
    
        with col2:
            if scheduler.scheduler.running:
                if st.button("⏹️ Stop Scheduler"):
                    scheduler.stop()
                    st.rerun()
    
        st.markdown("---")
    
        # Scheduled jobs
        st.subheader("📅 Scheduled Jobs")
    
        jobs = scheduler.get_job_status()
    
        # Job descriptions
        job_descriptions = {
            'monthly_bill_generation': '📊 Generates monthly electricity bills for all active meters on the 1st of each month',
            'payment_reminders': '🔔 Sends payment reminders for bills due in the next 3 days (runs daily at 10 AM)',
            'overdue_bills': '⚠️ Marks bills as overdue and sends notices (runs daily at 11 AM)',
            'meter_reading_collection': '📡 Collects meter readings from smart meters (runs weekly on Sunday at 8 AM)'
        }
    
        for job in jobs:
            # Get description
            description = job_descriptions.get(job['id'], 'Scheduled automation task')
        
            with st.expander(f"**{job['name']}** - In {job['time_until']}", expanded=False):
                # Description
                st.info(f"ℹ️ {description}")
            
                col1, col2 = st.columns([3, 1])
            
                with col1:
                    st.write(f"**📅 Next Run:** {job['next_run']}")
                    st.write(f"**⏰ Time Until:** {job['time_until']}")
                    st.write(f"**🔄 Schedule:** {job['trigger']}")
            
                with col2:
                    st.write("")
                    if st.button("▶️ Run Now", key=f"run_{job['id']}", width='stretch'):
                        with st.spinner(f"Running {job['name']}..."):
                            result = scheduler.run_job_now(job['id'])
                        
                            if result['success']:
                                st.success(f"✅ Job executed successfully!")
                            else:
                                st.error(f"❌ Job failed: {result.get('error')}")
    
        st.markdown("---")
    
        # Manual job triggers
        st.subheader("🎯 Manual Job Triggers")
    
        col1, col2 = st.columns(2)
    
        with col1:
            if st.button("📊 Generate Monthly Bills", type="primary"):
                with st.spinner("Generating bills for all active meters..."):
                    result = scheduler.run_job_now('monthly_bill_generation')
                    if result['success']:
                        st.success("✅ Monthly bills generated!")
                        st.info("Check logs for details on generated bills")
                    else:
                        st.error(f"❌ Failed: {result.get('error')}")
        
            if st.button("🔔 Send Payment Reminders"):
                with st.spinner("Sending payment reminders..."):
                    result = scheduler.run_job_now('payment_reminders')
                    if result['success']:
                        st.success("✅ Payment reminders sent!")
                    else:
                        st.error(f"❌ Failed: {result.get('error')}")
    
        with col2:
            if st.button("⚠️ Mark Overdue Bills"):
                with st.spinner("Marking overdue bills..."):
                    result = scheduler.run_job_now('overdue_bills')
                    if result['success']:
                        st.success("✅ Overdue bills marked!")
                    else:
                        st.error(f"❌ Failed: {result.get('error')}")
        
            if st.button("📡 Collect Meter Readings"):
                with st.spinner("Collecting meter readings..."):
                    result = scheduler.run_job_now('meter_reading_collection')
                    if result['success']:
                        st.success("✅ Meter readings collected!")
                    else:
                        st.error(f"❌ Failed: {result.get('error')}")
    
        st.markdown("---")
    
        st.info("""
        **💡 Tip:** The scheduler runs in the background when Flask app is running.
        Jobs execute automatically at their scheduled times. Use manual triggers for testing.
        """)

    # Tab 6: Payment Status
    with tab6:
        st.header("💳 Payment Status & Tracking")
    
        col1, col2 = st.columns(2)
    
        with col1:
            st.subheader("🔍 Check Bill Status")
        
            bill_id_input = st.number_input("Enter Bill ID", min_value=1, step=1, value=1)
        
            if st.button("🔍 Get Status", type="primary"):
                try:
                    bill = db.get_bill_by_id(bill_id_input)
                
                    if bill:
                        st.success(f"✅ Bill #{bill_id_input} Found")
                    
                        # Status indicator
                        status = bill.get('status', 'unknown').lower()
                        if status == 'paid':
                            st.success(f"### 💚 Status: PAID")
                        elif status == 'pending':
                            st.warning(f"### ⏳ Status: PENDING")
                        elif status == 'failed':
                            st.error(f"### ❌ Status: FAILED")
                        else:
                            st.info(f"### ℹ️ Status: {status.upper()}")
                    
                        # Bill details
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("Amount", f"₹{bill.get('amount', 0):,.2f}")
                        with col_b:
                            st.metric("Customer", bill.get('customer_id', 'N/A'))
                        with col_c:
                            st.metric("Meter", bill.get('meter_id', 'N/A'))
                    
                        # More details
                        with st.expander("📋 Full Bill Details", expanded=True):
                            st.write(f"**Consumption**: {bill.get('consumption_kwh', 0):.2f} kWh")
                            st.write(f"**Period**: {bill.get('billing_period_start', 'N/A')} to {bill.get('billing_period_end', 'N/A')}")
                            st.write(f"**Created**: {bill.get('created_at', 'N/A')}")
                        
                            if bill.get('payment_date'):
                                st.write(f"**Paid On**: {bill.get('payment_date')}")
                        
                            if bill.get('payment_link'):
                                st.write(f"**Payment Link**: {bill.get('payment_link')[:50]}...")
                                st.link_button("💳 Open Payment Link", bill.get('payment_link'))
                    
                        # Payment Confirmation for pending bills
                        if status == 'pending':
                            st.markdown("---")
                            st.markdown("### 💳 Confirm Payment")
                            st.info("After completing payment, click below to send confirmation notification")
                        
                            discord_user_id_confirm = st.text_input("Discord User ID (optional)", value="", key=f"discord_confirm_{bill_id_input}")
                        
                            if st.button("✅ I've Paid This Bill", type="primary", key=f"mark_paid_{bill_id_input}"):
                                try:
                                    with st.spinner("Processing payment confirmation..."):
                                        # Mark bill as paid
                                        db.update_bill_status(
                                            bill_id=bill_id_input,
                                            status='paid'
                                        )
                                    
                                        # Generate AI thank you message
                                        try:
                                            thank_you_message = ai_service.generate_payment_confirmation_message(
                                                customer_id=bill.get('customer_id'),
                                                bill_id=bill_id_input,
                                                amount=bill.get('amount', 0)
                                            )
                                        except Exception as e:
                                            st.write(f"⚠️ Using default message (AI unavailable)")
                                            thank_you_message = f"Thank you for your payment of ₹{bill.get('amount', 0):.2f}! Your bill #{bill_id_input} has been successfully paid."
                                    
                                        # Send Discord payment confirmation
                                        discord_confirm = discord_service.send_payment_confirmation(
                                            customer_id=bill.get('customer_id'),
                                            bill_id=str(bill_id_input),
                                            amount=bill.get('amount', 0),
                                            payment_date=datetime.now().isoformat(),
                                            discord_user_id=discord_user_id_confirm if discord_user_id_confirm else None
                                        )
                                    
                                        # Log confirmation notification
                                        db.log_notification({
                                            "bill_id": bill_id_input,
                                            "customer_id": bill.get('customer_id'),
                                            "channel": "discord",
                                            "message": thank_you_message,
                                            "status": "sent" if discord_confirm.get('success') else "failed",
                                            "sent_at": datetime.now().isoformat()
                                        })
                                    
                                        if discord_confirm.get('success'):
                                            st.success("🎉 Payment confirmed! Discord notification sent.")
                                            st.balloons()
                                            st.rerun()
                                        else:
                                            st.warning(f"⚠️ Bill marked as paid, but Discord notification failed: {discord_confirm.get('error', 'Unknown')}")
                                            st.rerun()
                            
                                except Exception as e:
                                    st.error(f"❌ Error processing payment: {str(e)}")
                                    import traceback
                                    st.code(traceback.format_exc())
                
                    else:
                        st.error(f"❌ Bill #{bill_id_input} not found")
            
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
        with col2:
            st.subheader("👤 Customer Bills")
        
            customer_id_input = st.text_input("Customer ID", value="CUST001", key="payment_customer_bills")
            num_bills = st.slider("Number of bills", 1, 20, 5)
        
            if st.button("📋 Get Bills", type="secondary"):
                try:
                    bills = db.get_bills_by_customer(customer_id_input, limit=num_bills)
                
                    if bills:
                        st.success(f"✅ Found {len(bills)} bills")
                    
                        for bill in bills:
                            status = bill.get('status', 'unknown').lower()
                            status_emoji = "💚" if status == 'paid' else "⏳" if status == 'pending' else "❌"
                        
                            with st.container():
                                col_x, col_y, col_z = st.columns([1, 2, 2])
                            
                                with col_x:
                                    st.write(f"{status_emoji} **#{bill.get('id')}**")
                                with col_y:
                                    st.write(f"₹{bill.get('amount', 0):,.2f}")
                                with col_z:
                                    st.write(f"{status.upper()}")
                            
                                st.caption(f"Created: {bill.get('created_at', 'N/A')[:10]}")
                                st.divider()
                    else:
                        st.warning(f"No bills found for {customer_id_input}")
            
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
        st.markdown("---")
    
        # Manual status update
        st.subheader("✏️ Update Bill Status (Manual)")
    
        with st.form("update_status"):
            col1, col2, col3 = st.columns(3)
        
            with col1:
                update_bill_id = st.number_input("Bill ID", min_value=1, step=1)
        
            with col2:
                new_status = st.selectbox("New Status", ["pending", "paid", "failed", "cancelled"])
        
            with col3:
                set_payment_date = st.checkbox("Set payment date to now")
        
            if st.form_submit_button("💾 Update Status", type="primary"):
                try:
                    payment_date = datetime.now().isoformat() if set_payment_date else None
                
                    updated_bill = db.update_bill_status(
                        bill_id=update_bill_id,
                        status=new_status,
                        payment_date=payment_date
                    )
                
                    st.success(f"✅ Bill #{update_bill_id} updated to {new_status.upper()}")
                
                    with st.expander("See updated bill"):
                        st.json(updated_bill)
                
                    st.rerun()
            
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
        st.markdown("---")
    
        # Webhook simulator
        st.subheader("🔗 Simulate Stripe Webhook")
        st.info("💡 This simulates what happens when a customer completes payment on Stripe")
    
        with st.form("simulate_webhook"):
            webhook_bill_id = st.number_input("Bill ID to mark as paid", min_value=1, step=1, value=1)
        
            if st.form_submit_button("🎬 Simulate Payment Success", type="primary"):
                try:
                    # Simulate webhook by updating status
                    db.update_bill_status(
                        bill_id=webhook_bill_id,
                        status='paid',
                        payment_date=datetime.now().isoformat()
                    )
                
                    st.balloons()
                    st.success(f"🎉 Payment simulated! Bill #{webhook_bill_id} marked as PAID")
                
                    # Show updated bill
                    updated = db.get_bill_by_id(webhook_bill_id)
                    if updated:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Status", updated.get('status', 'N/A').upper())
                        with col2:
                            st.metric("Paid On", updated.get('payment_date', 'N/A')[:19])
                
                    st.info("💡 In production, Stripe automatically sends this webhook when payment completes")
            
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
        st.markdown("---")
    
        # Setup instructions
        with st.expander("📘 How to Setup Real Stripe Webhooks"):
            st.markdown("""
            ### Production Webhook Setup
        
            1. **Deploy your app** to a public URL (or use ngrok for testing)
        
            2. **Add webhook in Stripe Dashboard**:
               - Go to: https://dashboard.stripe.com/webhooks
               - Click "Add endpoint"
               - URL: `https://your-domain.com/webhook/stripe`
               - Events to send: Select `checkout.session.completed`
        
            3. **Copy Webhook Signing Secret**:
               - After creating, click on the webhook
               - Copy the "Signing secret" (starts with `whsec_...`)
        
            4. **Update .env file**:
               ```
               STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxx
               ```
        
            5. **Test with real payment**:
               - Customer completes payment
               - Stripe sends webhook to your endpoint
               - Bill status automatically updates to "paid"
        
            ### Test Webhooks Locally with ngrok
        
            ```bash
            # Install ngrok: https://ngrok.com/download
        
            # Start your Flask app
            python app.py
        
            # In another terminal, expose port 5000
            ngrok http 5000
        
            # Use the ngrok URL in Stripe webhook settings
            # Example: https://abc123.ngrok.io/webhook/stripe
            ```
        
            ### Webhook Event Structure
        
            When payment succeeds, Stripe sends:
            ```json
            {
              "type": "checkout.session.completed",
              "data": {
                "object": {
                  "payment_status": "paid",
                  "metadata": {
                    "bill_id": "123",
                    "customer_id": "CUST001"
                  }
                }
              }
            }
            ```
        
            Your system automatically:
            ✅ Verifies the webhook signature  
            ✅ Extracts the bill_id  
            ✅ Updates bill status to "paid"  
            ✅ Sets payment_date  
            ✅ Logs the event  
            """)

    # Tab 7: Tariff Calculator
    with tab7:
        st.header("🧮 Tariff Calculator")
    
        col1, col2 = st.columns(2)
    
        with col1:
            tariff_type = st.selectbox("Tariff Type", ["residential", "commercial"], key="tariff_type_calc")
            consumption = st.number_input("Consumption (kWh)", min_value=0.0, value=250.0, step=10.0, key="consumption_calc")
            connected_load = st.number_input("Connected Load (KW)", min_value=0.0, value=7.0, step=0.5, key="load_calc")
            previous_outstanding = st.number_input("Previous Outstanding (₹)", min_value=0.0, value=0.0, step=100.0, key="outstanding_calc")
    
        with col2:
            if st.button("💡 Calculate Bill", type="primary"):
                bill = TariffRules.calculate_total_bill(
                    consumption_kwh=consumption,
                    connected_load_kw=connected_load,
                    tariff_type=tariff_type,
                    previous_outstanding=previous_outstanding
                )
            
                st.success(f"### Total Bill: ₹{bill['amount_payable']:,.2f}")
            
                # Breakdown
                st.markdown("#### 📋 Bill Breakdown")
            
                # Energy Charges
                with st.expander("⚡ Energy Charges", expanded=True):
                    for tier in bill['energy_charges']['tier_breakdown']:
                        st.write(f"**{tier['tier']}**: {tier['kwh']} kWh × ₹{tier['rate']} = ₹{tier['amount']:.2f}")
                    st.write(f"**Total Energy**: ₹{bill['energy_charges']['total']:.2f}")
            
                # Fixed Charges
                with st.expander("🔧 Fixed Charges"):
                    st.write(f"**Motor Charges**: ₹{bill['fixed_charges']['motor_charges']:.2f}")
                    st.write(f"**Grid Charges**: ₹{bill['fixed_charges']['grid_charges']:.2f}")
                    st.write(f"**Common Area**: ₹{bill['fixed_charges']['common_area_maintenance']:.2f}")
                    st.write(f"**Total Fixed**: ₹{bill['fixed_charges']['total']:.2f}")
            
                # Taxes
                with st.expander("💼 Taxes"):
                    st.write(f"**Electricity Duty**: ₹{bill['taxes']['electricity_duty']:.2f}")
                    st.write(f"**Tax on Sale**: ₹{bill['taxes']['tax_on_sale']:.2f}")
                    st.write(f"**Total Taxes**: ₹{bill['taxes']['total']:.2f}")
            
                st.info(f"Payment Due: {bill['payment_terms']['due_days']} days")

    # Tab 8: Meter Readings
    with tab8:
        st.header("📋 Meter Readings Management")
    
        col1, col2 = st.columns([2, 1])
    
        with col1:
            st.subheader("➕ Add New Reading")
        
            with st.form("add_reading"):
                meter_id = st.text_input("Meter ID", value="METER001", key="add_meter_id")
                customer_id = st.text_input("Customer ID", value="CUST001", key="add_customer_id")
                reading_value = st.number_input("Reading Value (kWh)", min_value=0.0, step=0.1)
                reading_date = st.date_input("Reading Date", value=datetime.now())
            
                if st.form_submit_button("✅ Add Reading", type="primary"):
                    try:
                        reading_data = {
                            "meter_id": meter_id,
                            "customer_id": customer_id,
                            "reading_value": reading_value,
                            "reading_date": reading_date.strftime("%Y-%m-%d"),
                            "created_at": datetime.now().isoformat()
                        }
                    
                        db.insert_meter_reading(reading_data)
                        st.success(f"✅ Reading added: {reading_value} kWh on {reading_date}")
                        st.cache_resource.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
        with col2:
            st.subheader("🎲 Generate Sample Data")
            num_readings = st.number_input("Number of readings", min_value=1, max_value=12, value=6)
        
            if st.button("Generate", type="secondary"):
                try:
                    readings = SampleDataGenerator.generate_meter_readings(
                        meter_id="METER001",
                        customer_id="CUST001",
                        num_months=num_readings,
                        base_consumption=200.0
                    )
                
                    for reading in readings:
                        db.insert_meter_reading(reading)
                
                    st.success(f"✅ Generated {len(readings)} readings")
                    st.cache_resource.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    # Tab 9: Generate Bill (moved from tab7)
    # Commenting out as we now have 8 tabs
    # with tab9:
        st.header("💰 Generate Electricity Bill")
    
        try:
            readings = db.get_historical_readings("METER001", limit=10)
        
            if len(readings) >= 2:
                col1, col2 = st.columns(2)
            
                with col1:
                    st.subheader("📝 Bill Details")
                
                    current_reading = st.number_input(
                        "Current Reading (kWh)", 
                        min_value=readings[0]['reading_value'],
                        value=readings[0]['reading_value'] + 150,
                        step=0.1
                    )
                
                    previous_reading = readings[0]['reading_value']
                    consumption = current_reading - previous_reading
                
                    st.info(f"Previous Reading: {previous_reading:.2f} kWh")
                    st.success(f"Consumption: {consumption:.2f} kWh")
                
                    tariff_type = st.selectbox("Tariff Type", ["residential", "commercial"], key="bill_tariff")
                    connected_load = st.number_input("Connected Load (KW)", value=7.0, step=0.5, key="bill_load")
            
                with col2:
                    if st.button("💰 Generate Bill", type="primary", key="generate_bill"):
                        # Calculate bill
                        bill = TariffRules.calculate_total_bill(
                            consumption_kwh=consumption,
                            connected_load_kw=connected_load,
                            tariff_type=tariff_type
                        )
                    
                        # Create bill record
                        bill_data = {
                            "customer_id": "CUST001",
                            "meter_id": "METER001",
                            "billing_period_start": readings[0]['reading_date'],
                            "billing_period_end": datetime.now().strftime("%Y-%m-%d"),
                            "consumption_kwh": consumption,
                            "amount": bill['amount_payable'],
                            "status": "pending",
                            "created_at": datetime.now().isoformat()
                        }
                    
                        created_bill = db.create_bill(bill_data)
                    
                        st.success("✅ Bill Generated Successfully!")
                    
                        # Display bill
                        st.markdown("---")
                        st.markdown("### 🧾 Bill Summary")
                        st.write(f"**Bill ID**: {created_bill.get('id', 'N/A')}")
                        st.write(f"**Consumption**: {consumption:.2f} kWh")
                        st.write(f"**Amount**: ₹{bill['amount_payable']:,.2f}")
                        st.write(f"**Status**: Pending")
                    
                        # Detailed breakdown
                        with st.expander("📋 Detailed Breakdown"):
                            st.json(bill['detailed_breakdown'])
        
            else:
                st.warning("⚠️ Need at least 2 meter readings to generate a bill. Add more readings first!")
    
        except Exception as e:
            st.error(f"Error: {str(e)}")

    # Tab 9: Analytics & Reports
    with tab9:
        st.header("📈 Analytics & Reporting")
    
        from services.analytics_service import AnalyticsService
        analytics = AnalyticsService()
    
        # Report Type Selection
        report_type = st.selectbox(
            "Select Report Type",
            ["Monthly Revenue", "Consumption Analytics", "Payment Success Rate", "Customer Segmentation", "Revenue Trend"]
        )
    
        st.markdown("---")
    
        if report_type == "Monthly Revenue":
            st.subheader("💰 Monthly Revenue Report")
        
            col1, col2 = st.columns(2)
            with col1:
                year = st.number_input("Year", min_value=2020, max_value=2030, value=datetime.now().year)
            with col2:
                month = st.number_input("Month", min_value=1, max_value=12, value=datetime.now().month)
        
            if st.button("Generate Revenue Report", key="revenue_report"):
                with st.spinner("Generating report..."):
                    report = analytics.get_monthly_revenue_report(int(year), int(month))
                
                    if "error" in report:
                        st.error(f"Error: {report['error']}")
                    else:
                        # Metrics
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Bills", report['total_bills'])
                        with col2:
                            st.metric("Total Revenue", f"₹{report['total_revenue']:,.2f}")
                        with col3:
                            st.metric("Collected", f"₹{report['collected_revenue']:,.2f}")
                        with col4:
                            st.metric("Success Rate", f"{report['payment_success_rate']}%")
                    
                        st.markdown("---")
                    
                        # Additional metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Pending Revenue", f"₹{report['pending_revenue']:,.2f}")
                        with col2:
                            st.metric("Average Bill", f"₹{report['average_bill']:,.2f}")
                        with col3:
                            st.metric("Max Bill", f"₹{report['max_bill']:,.2f}")
    
        elif report_type == "Consumption Analytics":
            st.subheader("⚡ Consumption Analytics")
        
            customer_filter = st.text_input("Customer ID (leave empty for all customers)", key="consumption_customer")
        
            if st.button("Analyze Consumption", key="consumption_analysis"):
                with st.spinner("Analyzing..."):
                    analytics_data = analytics.get_consumption_analytics(customer_filter if customer_filter else None)
                
                    if "error" in analytics_data:
                        st.error(f"Error: {analytics_data['error']}")
                    else:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Consumption", f"{analytics_data['total_consumption']:,.2f} kWh")
                        with col2:
                            st.metric("Average Consumption", f"{analytics_data['average_consumption']:,.2f} kWh")
                        with col3:
                            st.metric("Trend", analytics_data['trend'].upper())
                    
                        st.markdown("---")
                    
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Peak Consumption", f"{analytics_data['peak_consumption']:,.2f} kWh")
                        with col2:
                            st.metric("Low Consumption", f"{analytics_data['low_consumption']:,.2f} kWh")
                        with col3:
                            st.metric("Number of Bills", analytics_data['number_of_bills'])
    
        elif report_type == "Payment Success Rate":
            st.subheader("💳 Payment Success Rate")
        
            days = st.slider("Analysis Period (days)", min_value=7, max_value=365, value=30, key="payment_days")
        
            if st.button("Calculate Success Rate", key="payment_success"):
                with st.spinner("Calculating..."):
                    metrics = analytics.get_payment_success_rate(days)
                
                    if "error" in metrics:
                        st.error(f"Error: {metrics['error']}")
                    else:
                        # Success rate gauge
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.metric("Success Rate", f"{metrics['success_rate']}%")
                            st.metric("Period", f"{metrics['period_days']} days")
                        with col2:
                            # Payment breakdown
                            st.write("**Payment Breakdown:**")
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.metric("Paid", metrics['paid_bills'], delta_color="normal")
                            with col_b:
                                st.metric("Pending", metrics['pending_bills'], delta_color="off")
                            with col_c:
                                st.metric("Overdue", metrics['overdue_bills'], delta_color="inverse")
    
        elif report_type == "Customer Segmentation":
            st.subheader("👥 Customer Segmentation Analysis")
        
            if st.button("Analyze Segments", key="segment_analysis"):
                with st.spinner("Segmenting customers..."):
                    segmentation = analytics.get_customer_segmentation()
                
                    if "error" in segmentation:
                        st.error(f"Error: {segmentation['error']}")
                    else:
                        st.write(f"**Total Customers Analyzed**: {segmentation['total_customers']}")
                    
                        st.markdown("---")
                    
                        # Display segments
                        segments = segmentation['segments']
                    
                        col1, col2 = st.columns(2)
                    
                        with col1:
                            st.markdown("### 💎 High Value Customers")
                            st.write(f"*Count: {segments['high_value']['count']}*")
                            st.write("High consumption, good payment behavior")
                            if segments['high_value']['customers']:
                                for cust in segments['high_value']['customers']:
                                    st.write(f"- {cust['customer_id']}: {cust['avg_consumption']:.1f} kWh, {cust['payment_rate']:.0f}% paid")
                        
                            st.markdown("### ⚠️ At Risk Customers")
                            st.write(f"*Count: {segments['at_risk']['count']}*")
                            st.write("High consumption, poor payment behavior")
                            if segments['at_risk']['customers']:
                                for cust in segments['at_risk']['customers']:
                                    st.write(f"- {cust['customer_id']}: {cust['avg_consumption']:.1f} kWh, {cust['payment_rate']:.0f}% paid")
                    
                        with col2:
                            st.markdown("### ⭐ Loyal Customers")
                            st.write(f"*Count: {segments['loyal']['count']}*")
                            st.write("Low consumption, good payment behavior")
                            if segments['loyal']['customers']:
                                for cust in segments['loyal']['customers']:
                                    st.write(f"- {cust['customer_id']}: {cust['avg_consumption']:.1f} kWh, {cust['payment_rate']:.0f}% paid")
                        
                            st.markdown("### 😴 Low Engagement Customers")
                            st.write(f"*Count: {segments['low_engagement']['count']}*")
                            st.write("Low consumption, poor payment behavior")
                            if segments['low_engagement']['customers']:
                                for cust in segments['low_engagement']['customers']:
                                    st.write(f"- {cust['customer_id']}: {cust['avg_consumption']:.1f} kWh, {cust['payment_rate']:.0f}% paid")
    
        elif report_type == "Revenue Trend":
            st.subheader("📊 Revenue Trend Analysis")
        
            months = st.slider("Number of Months", min_value=3, max_value=12, value=6, key="trend_months")
        
            if st.button("Generate Trend Report", key="revenue_trend"):
                with st.spinner("Analyzing trend..."):
                    trend_data = analytics.get_revenue_trend(months)
                
                    if trend_data:
                        # Create a simple table
                        import pandas as pd
                        df = pd.DataFrame(trend_data)
                    
                        st.dataframe(df[['period', 'total_bills', 'total_revenue', 'collected_revenue', 'payment_success_rate']], 
                                    width='stretch')
                    
                        st.markdown("---")
                        st.write("**Trend Insights:**")
                    
                        # Calculate growth
                        if len(trend_data) >= 2:
                            latest = trend_data[-1]
                            previous = trend_data[-2]
                        
                            revenue_growth = ((latest['total_revenue'] - previous['total_revenue']) / previous['total_revenue'] * 100) if previous['total_revenue'] > 0 else 0
                            bills_growth = ((latest['total_bills'] - previous['total_bills']) / previous['total_bills'] * 100) if previous['total_bills'] > 0 else 0
                        
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Revenue Growth (MoM)", f"{revenue_growth:+.1f}%")
                            with col2:
                                st.metric("Bills Growth (MoM)", f"{bills_growth:+.1f}%")

    # Footer for Admin
    st.markdown("---")
    st.markdown("👨‍💼 **Admin Dashboard** | System Management & Configuration | v2.0")

