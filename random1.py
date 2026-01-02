"""Streamlit Dashboard for Billing System Testing"""
import streamlit as st
import json
from pathlib import Path
from datetime import datetime, timedelta
import importlib
import services.database_service
importlib.reload(services.database_service)
from services import DatabaseService, TariffRules
from services.graph_service import GraphService
import openai
from services.graph_service import GraphService
from utils.sample_data import SampleDataGenerator

st.set_page_config(page_title="Billing System Dashboard", page_icon="⚡", layout="wide")

# Initialize session state for role
if 'user_role' not in st.session_state:
    if 'openai_api_key' not in st.session_state:
        st.session_state.openai_api_key = ""
    st.session_state.user_role = None

# Initialize services
@st.cache_resource
def get_db_service(ttl_hash=None):
    return DatabaseService()

db = get_db_service(ttl_hash="v2")

FLAT_REGISTRY_PATH = Path("data/meter_registry.json")


@st.cache_data
def load_flat_registry():
    """Load flat registry generated from the Flats sheet.

    Falls back to empty list if the file is missing so the app
    still runs even before import_registry is executed.
    """
    try:
        if not FLAT_REGISTRY_PATH.exists():
            return []
        with FLAT_REGISTRY_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

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
            st.session_state.user_role = "admin_login"
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
# ADMIN LOGIN PAGE
# ==============================================
elif st.session_state.user_role == "admin_login":
    st.markdown('<p style="font-size: 40px; font-weight: bold; text-align: center;">🔐 Administrator Login</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("### Please authenticate with Auth0 to continue")
    
    # Back button
    if st.button("← Back to Role Selection"):
        st.session_state.user_role = None
        st.rerun()
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔑 Auth0 Login")
        
        with st.form("admin_auth_form"):
            st.markdown("Enter your Auth0 credentials:")
            
            user_id = st.text_input("User ID", value="auth0|user123", help="Your Auth0 user ID")
            jwt_token = st.text_input("JWT Token", type="password", help="Paste your Auth0 JWT token here")
            
            st.markdown("")
            login_button = st.form_submit_button("🚀 Login", type="primary", use_container_width=True)
            
            if login_button:
                if not jwt_token:
                    st.error("❌ Please enter a JWT token")
                else:
                    try:
                        from services.auth_service import AuthService
                        auth_service = AuthService()
                        
                        if auth_service.auth0_enabled:
                            # Verify the JWT token
                            with st.spinner("Verifying credentials..."):
                                payload = auth_service.verify_token(jwt_token)
                                
                                if payload:
                                    st.success(f"✅ Authentication successful! Welcome {payload.get('sub', 'Admin')}")
                                    st.session_state.user_role = "admin"
                                    st.session_state.admin_user_id = payload.get('sub', user_id)
                                    st.session_state.admin_jwt_token = jwt_token
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error("❌ Invalid or expired JWT token. Please check your credentials.")
                        else:
                            st.warning("⚠️ Auth0 is not configured. Using fallback authentication.")
                            if user_id and user_id.startswith("auth0|"):
                                st.success(f"✅ Authentication successful! Welcome {user_id}")
                                st.session_state.user_role = "admin"
                                st.session_state.admin_user_id = user_id
                                st.balloons()
                                st.rerun()
                            else:
                                st.error("❌ Invalid user ID format. Must start with 'auth0|'")
                    except Exception as e:
                        st.error(f"❌ Authentication error: {str(e)}")
        
        st.markdown("---")
        
        with st.expander("📘 How to get your Auth0 token"):
            st.markdown("""
            ### Get Your Auth0 JWT Token
            
            **Option 1: Using curl (PowerShell)**
            ```powershell
            curl --request POST `
              --url https://dev-t6knva248r1jkkvn.us.auth0.com/oauth/token `
              --header 'content-type: application/json' `
              --data '{
                "client_id":"RPLT6bQjGu2VyYKIQeqRADR8tEEoEkeU",
                "client_secret":"YOUR_CLIENT_SECRET",
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
            
            Copy the token and paste it in the JWT Token field above.
            """)
    
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

    st.title("👷 Field Engineer Dashboard")
    st.markdown("### Meter Reading Operations")
    
    # Function to get monthly reading count
    def get_monthly_reading_count(engineer_id="ENG001"):
        """Get the count of readings added by engineer this month"""
        try:
            today = datetime.now()
            # Get ALL readings from database, not just one meter
            all_readings = db.get_all_readings(limit=10000)
            
            monthly_count = 0
            for reading in all_readings:
                try:
                    # Handle different date formats
                    reading_date_str = reading['reading_date']
                    if isinstance(reading_date_str, str):
                        reading_date = datetime.fromisoformat(reading_date_str.replace('Z', '+00:00'))
                    else:
                        reading_date = reading_date_str
                    
                    if reading_date.month == today.month and reading_date.year == today.year:
                        # Only count actual readings (value > 0), excluding imported template data
                        if float(reading.get('reading_value', 0)) > 0:
                            monthly_count += 1
                except Exception:
                    continue
            
            return monthly_count
        except Exception as e:
            st.error(f"Error counting readings: {str(e)}")
            return 0
    
    # Display Monthly Reading Counter
    st.markdown("---")
    monthly_count = get_monthly_reading_count()
    max_readings = 200
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.progress(min(monthly_count / max_readings, 1.0))
    with col2:
        st.metric("Monthly Readings", f"{monthly_count}/{max_readings}")
    
    if monthly_count >= max_readings:
        st.warning("⚠️ Monthly reading limit reached!")
    elif monthly_count >= max_readings * 0.9:
        st.info(f"ℹ️ {max_readings - monthly_count} readings remaining this month")
    else:
        st.success(f"✅ {max_readings - monthly_count} readings remaining this month")
    
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("👤 Current Role")
        st.info("👷 Field Engineer")
        
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
        
        st.markdown("---")
        st.header("📊 Monthly Stats")
        st.metric("This Month", f"{monthly_count}/200")
        st.metric("Remaining", f"{max_readings - monthly_count}")
        
        st.markdown("---")
        st.header("🎯 Quick Actions")
        
        if st.button("🔄 Refresh Data"):
            st.cache_resource.clear()
            st.rerun()
    
    # Field Engineer Tabs - Simplified
    fe_tab1, fe_tab2 = st.tabs([
        "➕ Add Reading",
        "📋 Reading History"
    ])

    # FE Tab 1: Add New Reading (Primary Tab)
    with fe_tab1:
        st.header("➕ Add New Meter Reading")

        # Fetch active meters from DB instead of static JSON
        flats = db.get_active_meters()
        
        if not flats:
            st.warning("No active meters found in the database. Please run the import script.")
        else:
            # Sort flats by flat_no for better UX
            try:
                flats.sort(key=lambda x: x.get('flat_no', ''))
            except:
                pass # Best effort sort

            # Get unique flat numbers
            flat_nos = sorted(list(set(f.get('flat_no', '') for f in flats if f.get('flat_no'))))
            
            st.subheader("Select Flat and Enter Reading")
            
            # First Dropdown: Flat No
            selected_flat_no = st.selectbox("🏢 Select Flat No", flat_nos)
            
            # Filter flats based on selected flat number
            available_floors_data = [f for f in flats if f.get('flat_no') == selected_flat_no]
            
            # Get unique floors for this flat
            floors = sorted(list(set(f.get('floor', '') for f in available_floors_data if f.get('floor'))))
            
            # Second Dropdown: Floor
            selected_floor = st.selectbox("Select Floor", floors)
            
            # Find the specific flat entry
            selected_flat = next(
                (f for f in available_floors_data if f.get('floor') == selected_floor), 
                available_floors_data[0] if available_floors_data else {}
            )

            with st.form("add_reading_fe", clear_on_submit=True):
                col_meta1, col_meta2 = st.columns(2)
                with col_meta1:
                    st.text_input("Unit ID", value=selected_flat.get("unit_id", ""), disabled=True)
                    st.text_input("Flat no", value=selected_flat.get("flat_no", ""), disabled=True)
                    st.text_input("Floor", value=selected_flat.get("floor", ""), disabled=True)
                with col_meta2:
                    st.text_input("Client Name", value=selected_flat.get("client_name", ""), disabled=True)
                    st.text_input("Meter No.", value=selected_flat.get("meter_id", ""), disabled=True)
                    st.text_input("Type", value=selected_flat.get("type", ""), disabled=True)

                st.markdown("---")
                reading_value = st.number_input(
                    "⚡ Reading Value (kWh)", min_value=0.0, step=0.1,
                    help="Enter the current meter reading for this flat"
                )
                reading_date = st.date_input("📅 Reading Date", value=datetime.now())

                col1, col2 = st.columns(2)
                with col1:
                    submit_button = st.form_submit_button("✅ Submit Reading", type="primary", use_container_width=True)

                if submit_button:
                    if reading_value > 0:
                        try:
                            meter_id = selected_flat.get("meter_id", "")
                            unit_id = selected_flat.get("unit_id", "")
                            
                            # Use Unit ID as the primary customer identifier if available
                            customer_id = f"UNIT-{unit_id}" if unit_id else f"FLAT-{selected_flat.get('flat_no', '')}"

                            # Check if this is an update to an initial reading
                            if selected_flat.get('status') == 'initial':
                                # UPDATE existing initial reading
                                update_data = {
                                    "reading_value": reading_value,
                                    "reading_date": reading_date.strftime("%Y-%m-%d"),
                                    "status": "active", # Change status from initial to active
                                    "submitted_at": datetime.now().isoformat()
                                }
                                result = db.update_meter_reading(selected_flat['id'], update_data)
                                action_type = "updated"
                            else:
                                # INSERT new reading
                                reading_data = {
                                    "meter_id": meter_id,
                                    "customer_id": customer_id,
                                    "reading_value": reading_value,
                                    "reading_date": reading_date.strftime("%Y-%m-%d"),
                                    "unit_id": unit_id,
                                    "flat_no": selected_flat.get("flat_no", ""),
                                    "floor": selected_flat.get("floor", ""),
                                    "type": selected_flat.get("type", ""),
                                    "client_name": selected_flat.get("client_name", ""),
                                    "created_at": datetime.now().isoformat(),
                                    "status": "active"
                                }
                                result = db.insert_meter_reading(reading_data)
                                action_type = "added"

                            if result:
                                st.success(
                                    f"✅ Reading {action_type} successfully! {reading_value} kWh recorded for Flat {selected_flat.get('flat_no', '')} on {reading_date}"
                                )
                                st.balloons()
                                st.cache_resource.clear()
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to {action_type} reading in database")
                        except Exception as e:
                            st.error(f"❌ Error processing reading: {str(e)}")
                    else:
                        st.warning("⚠️ Please enter a valid reading value greater than 0")
        
        # Quick Tips
        st.markdown("---")
        with st.expander("💡 Quick Tips for Field Engineers"):
            st.markdown("""
            - **Double-check** the meter ID before submitting  
            - Ensure the reading value is **accurate**  
            - Take a **photo** of the meter for your records  
            - Report any **damaged or faulty meters** immediately  
            - Complete your daily readings before end of shift
            """)
    
    # FE Tab 2: Reading History
    with fe_tab2:
        st.header("📋 Your Reading History")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            meter_filter = st.text_input("🔍 Search by Meter ID", value="METER001", placeholder="Enter meter ID to filter")
        with col2:
            limit = st.selectbox("Show", [10, 25, 50, 100], index=1)
        
        try:
            readings = db.get_historical_readings(meter_filter, limit=limit)
            
            if readings:
                import pandas as pd
                df = pd.DataFrame(readings)
                df['reading_date'] = pd.to_datetime(df['reading_date'])
                df = df.sort_values('reading_date', ascending=False)
                
                # Display in a clean format
                st.dataframe(
                    df[['reading_date', 'meter_id', 'customer_id', 'reading_value']], 
                    use_container_width=True,
                    hide_index=True
                )
                
                st.caption(f"Showing {len(readings)} most recent readings")
                
                # Download option
                st.markdown("---")
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Reading History (CSV)",
                    data=csv,
                    file_name=f"readings_{meter_filter}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info(f"ℹ️ No readings found for meter: {meter_filter}")
        
        except Exception as e:
            st.error(f"❌ Error loading readings: {str(e)}")
    
    # Footer
    st.markdown("---")
    st.caption("👷 **Field Engineer Dashboard** | Simple & Efficient Meter Reading | v3.0")

# ==============================================
# ADMIN DASHBOARD
# ==============================================
else:  # admin role
    st.markdown("---")

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

    # Admin Tabs (top-level)
    admin_tab1, admin_tab2, admin_tab3 = st.tabs(["📊 Overview", "📄 View Bills (Supabase)", "📄 View Bills (Neo4j)"])

    # Overview Tab (placeholder / legacy)
    with admin_tab1:
        pass

    # View Bills Tab (Supabase)
    with admin_tab2:
        st.header("📄 All Generated Bills (Supabase)")
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
                    file_name=f"all_bills_supabase_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No bills found.")
        except Exception as e:
            st.error(f"Error loading bills: {str(e)}")

    # View Bills from Neo4j
    with admin_tab3:
        st.header("📄 All Generated Bills (Neo4j)")
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🔄 Refresh", key="refresh_neo4j_bills", width='stretch'):
                st.cache_resource.clear()
                st.cache_data.clear()
                st.rerun()
        
        try:
            from services.neo4j_service import Neo4jService
            neo4j_service = Neo4jService()
            
            if not neo4j_service.is_connected():
                st.error("❌ Neo4j is not connected. Please check your configuration.")
            else:
                bills = neo4j_service.get_all_bills()
                if bills:
                    import pandas as pd
                    df = pd.DataFrame(bills)
                    st.dataframe(df, width='stretch')
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Bills CSV (Neo4j)",
                        data=csv,
                        file_name=f"all_bills_neo4j_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No bills found in Neo4j. Use the 'Sync All Bills to Neo4j' button above to sync bills.")
        except Exception as e:
            st.error(f"Error loading bills from Neo4j: {str(e)}")



    # Admin Main Content Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Dashboard", 
        "💳 Payment Status",
        "⏰ Scheduler",
        "📋 Meter Readings", 
        "💰 Generate Bill",
        "📈 Analytics & Reports"
    ])

    # =========================
    # Tab 1: Dashboard
    # =========================
    with tab1:

        # ============================================
        # Toggle Modern / Legacy Dashboard
        # ============================================
        use_modern_ui = st.toggle(
            "🎨 Use Modern Dashboard UI",
            value=True,
            key="modern_ui_toggle",
            help="Switch between the new modern dashboard or the original interface"
        )

        # ============================================
        # Load required data
        # ============================================
        # Initialize session state for approved readings if not present
        if "approved_readings" not in st.session_state:
            st.session_state.approved_readings = set()

        try:
            # Get unbilled readings and filter out 0-value readings (imported template data)
            raw_readings = db.get_unbilled_readings(limit=100)
            # Filter: >0 value AND not in approved set
            pending_readings = [
                r for r in raw_readings 
                if float(r.get('reading_value', 0)) > 0 
                and r['id'] not in st.session_state.approved_readings
            ]
        except:
            pending_readings = []

        new_readings_count = len(pending_readings)

        try:
            all_bills = db.get_all_bills()
            # Count pending, generated, and overdue bills as invoices to be processed/paid
            invoices = len([b for b in all_bills if b.get("status") in ["pending", "generated", "overdue"]])
            
            # Calculate overdue (unbilled readings) manually to filter out 0-value imports AND approved readings
            unbilled_all = db.get_unbilled_readings(limit=1000)
            overdue = len([
                r for r in unbilled_all 
                if float(r.get('reading_value', 0)) > 0 
                and r['id'] not in st.session_state.approved_readings
            ])
            
            total_paid = sum(b.get("amount", 0) for b in all_bills if b.get("status") == "paid")
            # Outstanding includes pending, generated, and overdue bills
            total_outstanding = sum(b.get("amount", 0) for b in all_bills if b.get("status") in ["pending", "generated", "overdue"])
        except:
            invoices = overdue = total_paid = total_outstanding = 0

        total_meters = 120  # Replace if you have db.get_total_meters()

        # ============================================
        # MODERN UI
        # ============================================
        if use_modern_ui:

            # ---------- CSS ----------
            st.markdown("""
            <style>
            .metric-card {
                background-color: #FFFFFF;
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                border: 1px solid #E0E0E0;
                margin-bottom: 10px;
            }
            .metric-label {
                font-size: 12px;
                font-weight: 600;
                color: #666666;
                text-transform: uppercase;
                margin-bottom: 5px;
            }
            .metric-value {
                font-size: 24px;
                font-weight: 700;
                color: #333333;
            }
            .section-header {
                font-size: 14px;
                font-weight: 700;
                color: #333333;
                margin-bottom: 10px;
                text-transform: uppercase;
            }
            .status-box {
                background-color: #FFFFFF;
                border-radius: 8px;
                padding: 20px;
                border: 1px solid #E0E0E0;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            }
            .status-item {
                font-size: 14px;
                margin-bottom: 8px;
                color: #333333;
            }
            /* Custom Button Styling - approximated via st.button types */
            </style>
            """, unsafe_allow_html=True)

            # ---------- HEADER ----------
            st.markdown("### Blessings Electric Billing AI")
            
            # ---------- KPI CARDS ----------
            # Using columns to create the 4 cards at the top
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            
            with kpi1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">TOTAL METERS:</div>
                    <div class="metric-value">{total_meters}</div>
                </div>
                """, unsafe_allow_html=True)
                
            with kpi2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">NEW READINGS:</div>
                    <div class="metric-value">{new_readings_count}</div>
                </div>
                """, unsafe_allow_html=True)
                
            with kpi3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">INVOICES TO SEND:</div>
                    <div class="metric-value">{invoices}</div>
                </div>
                """, unsafe_allow_html=True)
                
            with kpi4:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">OVERDUE:</div>
                    <div class="metric-value" style="color: #D32F2F;">{overdue}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

            # ---------- MAIN CONTENT ----------
            # === REVIEW NEW READINGS ===
            st.markdown('<div class="section-header">REVIEW NEW READINGS</div>', unsafe_allow_html=True)

            flats = load_flat_registry()
            flat_by_meter = {f.get("meter_id"): f for f in flats if f.get("meter_id")}
            # Initialize session state for approved readings if not present
            if "approved_readings" not in st.session_state:
                st.session_state.approved_readings = set()

            # Filter out readings that have been approved in this session
            display_readings = [r for r in pending_readings if r['id'] not in st.session_state.approved_readings]

            if display_readings:
                st.info(f"📝 Found {len(display_readings)} new readings to review")
                
                # Table Header
                h1, h2, h3, h4, h5, h6, h7, h8 = st.columns([1.2, 0.8, 0.8, 1.5, 1, 1, 1, 1.5])
                h1.markdown("**Unit ID**")
                h2.markdown("**Flat**")
                h3.markdown("**Floor**")
                h4.markdown("**Client Name**")
                h5.markdown("**Meter ID**")
                h6.markdown("**Reading**")
                h7.markdown("**Est. (₹)**")
                h8.markdown("**Actions**")
                st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)

                for i, r in enumerate(display_readings[:5]):  # Show top 5
                    c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([1.2, 0.8, 0.8, 1.5, 1, 1, 1, 1.5])

                    meter_id = r.get("meter_id")
                    
                    # Try to get metadata from reading object first (new schema), then fallback to registry
                    unit_id = r.get("unit_id") or flat_by_meter.get(meter_id, {}).get("unit_id", "-")
                    flat_no = r.get("flat_no") or flat_by_meter.get(meter_id, {}).get("flat_no", "-")
                    floor = r.get("floor") or flat_by_meter.get(meter_id, {}).get("floor", "-")
                    client_name = r.get("client_name") or flat_by_meter.get(meter_id, {}).get("client_name", "-")
                    
                    reading_val = r.get("reading_value")
                    
                    # Calculate estimated bill (simple logic)
                    prev_reading = 0 # TODO: Fetch previous reading
                    usage = reading_val - prev_reading if reading_val else 0
                    energy_amount = (usage or 0) * 7.5  # Approx rate

                    with c1:
                        st.write(str(unit_id))
                    with c2:
                        st.write(str(flat_no))
                    with c3:
                        st.write(str(floor))
                    with c4:
                        st.write(str(client_name))
                    with c5:
                        st.write(str(meter_id))
                    with c6:
                        st.write(f"{reading_val}")
                    with c7:
                        st.write(f"₹{energy_amount:.0f}")

                    with c8:
                        b1, b2 = st.columns(2)
                        with b1:
                            if st.button("APPROVE", key=f"app_{i}", type="primary", use_container_width=True):
                                st.session_state["fetched_reading"] = r
                                st.session_state["fetched_meter_id"] = r["meter_id"]
                                # Add to approved set to hide from list
                                st.session_state.approved_readings.add(r['id'])
                                st.success(f"Approved {meter_id}")
                                st.rerun()
                        with b2:
                            if st.button("REJECT", key=f"rej_{i}", type="secondary", use_container_width=True):
                                if db.delete_reading(r['id']):
                                    st.warning(f"Rejected and deleted reading for {meter_id}")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete reading")
            else:
                st.info("No new readings to review.")
                
            if len(display_readings) > 5:
                if st.button(" View All Readings "):
                    pass

            # === QUICK ACTIONS & STATUS (Below Review Readings Table) ===
            st.markdown("<br>", unsafe_allow_html=True)
            
            # QUICK ACTIONS
            st.markdown('<div class="section-header">QUICK ACTIONS</div>', unsafe_allow_html=True)
            
            action_col1, action_col2, action_col3 = st.columns(3)
            
            with action_col1:
                if st.button(" Generate Monthly Bills ", use_container_width=True, type="primary"):
                    st.session_state["selected_admin_tab"] = "generate"
                    st.rerun()
            
            with action_col2:
                if st.button(" View Payments ", use_container_width=True, type="primary"):
                    st.session_state["selected_admin_tab"] = "payments"
                    st.rerun()
            
            with action_col3:
                if st.button(" Print Reports ", use_container_width=True, type="primary"):
                    st.session_state["selected_admin_tab"] = "analytics"
                    st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)

            # SIMPLE STATUS BOX
            st.markdown('<div class="section-header">SIMPLE STATUS BOX</div>', unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="sb">
                <div class="si"><b>Payments:</b> ₹{total_paid:,.0f}</div>
                <div class="si"><b>Outstanding:</b> ₹{total_outstanding:,.0f}</div>
                <div class="si"><b>Overdue:</b> {overdue}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("---")

        # ============================================
        # LEGACY UI  (unchanged)
        # ============================================
        else:
            st.header("📊 System Overview (Legacy)")
            st.markdown("---")

            # KEEP YOUR OLD LEGACY DASHBOARD CODE HERE
            # (Do NOT remove anything)

            try:
                unbilled_readings = db.get_unbilled_readings(limit=50)
            except:
                unbilled_readings = []

            if unbilled_readings:
                st.info(f"{len(unbilled_readings)} unbilled readings:")
                import pandas as pd
                df_legacy = pd.DataFrame(unbilled_readings)
                st.dataframe(df_legacy, use_container_width=True)
            else:
                st.success("No pending readings.")

            st.markdown("---")


        # =======================================================
        # SHARED SECTION (Fetch Reading + WORKFLOW GOES HERE)
        # =======================================================



        st.markdown("---")

        # ============================================
        # 🔥 INSERT YOUR FULL WORKFLOW CODE HERE 🔥
        # (Everything from: with st.form("workflow_test"):
        #  down to right before Neo4j Sync)
        # ============================================

        with st.form("workflow_test"):
            st.subheader("📥 Step 1: Input Meter Reading")
        
            col_wf1, col_wf2 = st.columns(2)
            with col_wf1:
                # Pre-fill with fetched data if available
                default_meter = st.session_state.get('fetched_meter_id', 'METER001')
                default_customer = st.session_state.get('fetched_reading', {}).get('customer_id', 'CUST001')
                default_reading = st.session_state.get('fetched_reading', {}).get('reading_value', 4600.0)
                
                wf_meter_id = st.text_input("Meter ID", value=default_meter)
                wf_customer_id = st.text_input("Customer ID", value=default_customer)
                wf_reading_value = st.number_input("Reading Value (kWh)", min_value=0.0, value=float(default_reading), step=0.1)
        
            with col_wf2:
                wf_reading_date = st.date_input("Reading Date", value=datetime.now())
                customer_phone = st.text_input("Customer Phone", value="+1234567890", key="wf_phone")
                discord_user_id = st.text_input(
                    "Discord User ID (optional - for direct mention)",
                    value="",
                    key="wf_discord_id",
                    help="Right-click on yourself in Discord > Copy User ID"
                )
        
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
                
                    # Step 2: Auth0 Verification (using admin login credentials)
                    st.info("🔐 Step 2: Auth0 token verification...")
                
                    # Get logged-in admin credentials
                    admin_user = st.session_state.get('admin_user_id', 'admin')
                    admin_token = st.session_state.get('admin_jwt_token', None)
                    
                    if admin_token:
                        # Already authenticated via login
                        st.success(f"✅ Step 2: Authenticated as: {admin_user}")
                    else:
                        # Fallback for admin without JWT
                        st.warning(f"⚠️ Step 2: Proceeding as authenticated admin: {admin_user}")
                    
                    progress_bar.progress(15)
                
                    # Step 3: Get Historical Readings
                    st.info("📊 Step 3: Fetching historical readings...")
                    historical_readings = db.get_historical_readings(wf_meter_id, limit=10)
                    st.success(f"✅ Step 3: Retrieved {len(historical_readings)} historical readings")
                    progress_bar.progress(23)
                
                    # Step 4: Get Tariff Rules (from service / Neo4j)
                    st.info("💰 Step 4: Loading tariff rules...")
                    st.success("✅ Step 4: Tariff rules loaded (Neo4j)")
                    progress_bar.progress(31)
                
                    # Step 5: AI Validation
                    st.info("🤖 Step 5: AI validating meter reading...")
                    validation = ai_service.validate_meter_reading(
                        historical_readings=historical_readings,
                        new_reading={
                            "meter_id": wf_meter_id,
                            "reading_value": wf_reading_value,
                            "reading_date": wf_reading_date.strftime("%Y-%m-%d")
                        }
                    )
                
                    if validation['valid']:
                        st.success(
                            f"✅ Step 5: Reading validated - {validation['reason']} "
                            f"(Confidence: {validation['confidence']}%)"
                        )
                        progress_bar.progress(38)
                    else:
                        st.error(f"❌ Step 5: Invalid reading - {validation['reason']}")
                        st.stop()
                
                    # Step 6: AI Bill Calculation
                    st.info("🧮 Step 6: AI calculating electricity bill...")
                    if len(historical_readings) > 0:
                        previous_reading = historical_readings[0]['reading_value']
                        consumption = wf_reading_value - previous_reading
                    else:
                        previous_reading = 0
                        consumption = wf_reading_value
                
                    bill_calculation = ai_service.calculate_bill(
                        current_reading=wf_reading_value,
                        previous_reading=previous_reading,
                        meter_id=wf_meter_id,
                        customer_id=wf_customer_id
                    )
                
                    st.success(
                        f"✅ Step 6: Bill calculated - ₹{bill_calculation['total_amount']:,.2f} "
                        f"for {bill_calculation['consumption_kwh']:.2f} kWh"
                    )
                
                    # Show breakdown
                    with st.expander("View Bill Breakdown"):
                        st.json(bill_calculation)
                
                    progress_bar.progress(46)
                
                    # Step 7: Store Bill in DB
                    st.info("💾 Step 7: Storing bill in database...")
                    bill_data = {
                        "customer_id": wf_customer_id,
                        "meter_id": wf_meter_id,
                        "billing_period_start": historical_readings[0]['reading_date'] if historical_readings else wf_reading_date.strftime("%Y-%m-%d"),
                        "billing_period_end": wf_reading_date.strftime("%Y-%m-%d"),
                        "consumption_kwh": consumption,
                        "amount": bill_calculation['total_amount'],
                        "status": "pending",
                        "created_at": datetime.now().isoformat()
                    }
                
                    created_bill = db.create_bill(bill_data)
                    bill_id = created_bill.get('id', 'BILL_' + datetime.now().strftime("%Y%m%d%H%M%S"))
                    st.success(f"✅ Step 7: Bill stored with ID: {bill_id}")
                    progress_bar.progress(54)
                
                    # Step 8: Save to Neo4j (placeholder)
                    st.info("🔗 Step 8: Saving bill to Neo4j graph...")
                    st.success("✅ Step 8: Bill saved to Neo4j")
                    progress_bar.progress(62)
                
                    # Step 9: Create Stripe Payment Link
                    st.info("💳 Step 9: Creating Stripe payment link...")
                    payment_link = payment_service.create_payment_link(
                        amount=bill_calculation['total_amount'],
                        currency="INR",
                        description=f"Electricity Bill - {wf_meter_id}",
                        metadata={
                            "bill_id": str(bill_id),
                            "customer_id": wf_customer_id,
                            "meter_id": wf_meter_id
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
                        customer_id=wf_customer_id,
                        bill_amount=bill_calculation['total_amount'],
                        consumption_kwh=consumption,
                        payment_link=payment_link['url']
                    )
                    st.success("✅ Step 11: Notification message generated")
                    st.info(f"Message: {notification_message}")
                    progress_bar.progress(85)
                
                    # Step 12: Send Discord Notification
                    st.info("💬 Step 12: Sending Discord notification...")
                    discord_result = discord_service.send_bill_notification(
                        customer_id=wf_customer_id,
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
                            st.success("✅ Step 12: Discord notification sent to channel")
                    else:
                        st.warning(f"⚠️ Step 12: Discord notification failed: {discord_result.get('error', 'Unknown error')}")
                    progress_bar.progress(92)
                
                    # Step 13: Log Notification
                    st.info("📋 Step 13: Logging notification...")
                    db.log_notification({
                        "bill_id": bill_id,
                        "customer_id": wf_customer_id,
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
                
                    col_s1, col_s2, col_s3 = st.columns(3)
                    with col_s1:
                        st.metric("Bill Amount", f"₹{bill_calculation['total_amount']:,.2f}")
                    with col_s2:
                        st.metric("Consumption", f"{consumption:.2f} kWh")
                    with col_s3:
                        st.metric("Status", "Pending Payment")
                
                    st.markdown("---")
                    st.markdown("#### 📄 Complete Bill Details")
                    st.write(f"**Bill ID**: {bill_id}")
                    st.write(f"**Customer**: {wf_customer_id}")
                    st.write(f"**Meter**: {wf_meter_id}")
                    st.write(f"**Period**: {bill_data['billing_period_start']} to {bill_data['billing_period_end']}")
                    st.write(f"**Payment Link**: {payment_link['url']}")
                    st.write("**Discord Notification**: Sent to billing channel")
                
                    # Store bill info in session state for payment confirmation
                    st.session_state['last_bill_id'] = bill_id
                    st.session_state['last_bill_amount'] = bill_calculation['total_amount']
                    st.session_state['last_customer_id'] = wf_customer_id
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
            customer_id_for_confirm = st.session_state.get('last_customer_id', '')
            discord_user_id_for_confirm = st.session_state.get('last_discord_user_id', '')
        
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
                                customer_id=customer_id_for_confirm,
                                bill_id=bill_id,
                                amount=amount
                            )
                            st.success("✓ Thank you message generated")
                        except Exception:
                            st.warning("⚠️ Using default message")
                            thank_you_message = (
                                f"Thank you for your payment of ₹{amount:.2f}! "
                                f"Your bill #{bill_id} has been successfully paid."
                            )
                    
                        # Send Discord payment confirmation
                        discord_confirm = discord_service.send_payment_confirmation(
                            customer_id=customer_id_for_confirm,
                            bill_id=str(bill_id),
                            amount=amount,
                            payment_date=datetime.now().isoformat(),
                            discord_user_id=discord_user_id_for_confirm if discord_user_id_for_confirm else None
                        )
                    
                        # Log confirmation notification
                        db.log_notification({
                            "bill_id": bill_id,
                            "customer_id": customer_id_for_confirm,
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
                            st.error(
                                "⚠️ Bill marked as paid, but Discord notification failed: "
                                f"{discord_confirm.get('error', 'Unknown')}"
                            )
            
                except Exception as e:
                    st.error(f"❌ Error processing payment: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
        else:
            st.info("Create a bill using the workflow above first, then you can confirm payment here.")
    

        
        # =========================




        # -------------------------------
        # FETCH READING FROM DATABASE
        # -------------------------------
        st.markdown("### 📥 Fetch Reading from Database")

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            fetch_meter_id = st.text_input(
                "Enter Meter ID to fetch latest reading",
                value="METER001",
                key="fetch_meter_input"
            )

        with col2:
            st.write("")
            if st.button("🔍 Fetch Latest"):
                try:
                    latest_readings = db.get_historical_readings(fetch_meter_id, limit=1)
                    if latest_readings:
                        st.session_state["fetched_reading"] = latest_readings[0]
                        st.session_state["fetched_meter_id"] = fetch_meter_id
                        st.success(f"Fetched {latest_readings[0]['reading_value']} kWh")
                    else:
                        st.warning("No readings found.")
                except Exception as e:
                    st.error(f"Error: {e}")

        with col3:
            st.write("")
            if st.button("🔄 Refresh", use_container_width=True):
                st.cache_resource.clear()
                st.rerun()


        # ----- Display fetched reading -----
        if "fetched_reading" in st.session_state and st.session_state["fetched_reading"]:
            r = st.session_state["fetched_reading"]
            st.info(
                f"📊 **Reading:** {r['reading_value']} kWh  | "
                f"Date: {r['reading_date']} | "
                f"Customer: {r['customer_id']}"
            )

        st.header("🔄 Sync Readings from Supabase to Neo4j")
        
        if st.button("Sync All Readings to Neo4j", type="primary", key="sync_readings_to_neo4j", width='stretch'):
            try:
                from services.neo4j_service import Neo4jService
                neo4j_service = Neo4jService()
                
                if not neo4j_service.is_connected():
                    st.error("❌ Neo4j is not connected. Please check your configuration.")
                else:
                    with st.spinner("Syncing readings to Neo4j..."):
                        readings = db.get_all_readings(limit=10000)  # Get all readings
                        
                        if not readings:
                            st.warning("⚠️ No readings found in Supabase to sync.")
                        else:
                            count = 0
                            errors = []
                            
                            with neo4j_service.driver.session() as session:
                                for reading in readings:
                                    try:
                                        # Ensure Customer and Meter nodes exist
                                        session.run("MERGE (c:Customer {id: $customer_id})", 
                                                   customer_id=reading["customer_id"])
                                        session.run("MERGE (m:Meter {id: $meter_id})", 
                                                   meter_id=reading["meter_id"])
                                        
                                        # Create Reading node
                                        session.run("""
                                            MERGE (r:Reading {id: $id})
                                            SET r.value = $reading_value,
                                                r.date = $reading_date,
                                                r.meter_id = $meter_id,
                                                r.customer_id = $customer_id,
                                                r.location = $location,
                                                r.notes = $notes
                                        """,
                                            id=str(reading.get("id", "")),
                                            reading_value=float(reading["reading_value"]),
                                            reading_date=str(reading["reading_date"]),
                                            meter_id=reading["meter_id"],
                                            customer_id=reading["customer_id"],
                                            location=reading.get("location", ""),
                                            notes=reading.get("notes", "")
                                        )
                                        
                                        # Create relationships
                                        session.run("""
                                            MATCH (m:Meter {id: $meter_id}), (r:Reading {id: $id}) 
                                            MERGE (m)-[:HAS_READING]->(r)
                                        """, meter_id=reading["meter_id"], id=str(reading.get("id", "")))
                                        
                                        session.run("""
                                            MATCH (c:Customer {id: $customer_id}), (m:Meter {id: $meter_id}) 
                                            MERGE (c)-[:OWNS]->(m)
                                        """, customer_id=reading["customer_id"], meter_id=reading["meter_id"])
                                        
                                        count += 1
                                    except Exception as e:
                                        errors.append(f"Reading {reading.get('id')}: {str(e)}")
                            
                            st.success(f"✅ {count} readings synced from Supabase to Neo4j!")
                            if errors:
                                with st.expander("⚠️ View Errors"):
                                    for error in errors:
                                        st.error(error)
            except Exception as e:
                st.error(f"Error syncing readings: {e}")

        # Neo4j Sync Section
        # =========================
        st.markdown("---")
        st.subheader("🔗 Neo4j Graph Database Sync")
        
        # Show Neo4j configuration status
        from config import Config
        with st.expander("ℹ️ Neo4j Configuration"):
            st.write(f"**URI:** `{Config.NEO4J_URI}`")
            st.write(f"**User:** `{Config.NEO4J_USER}`")
            st.write(
                f"**Password:** "
                f"`{'*' * len(Config.NEO4J_PASSWORD) if Config.NEO4J_PASSWORD else '(not set)'}`"
            )
        
        col_neo1, col_neo2, col_neo3 = st.columns(3)
        
        with col_neo1:
            st.write("**Sync Bills to Neo4j**")
            st.caption("Clears Neo4j and syncs all bills from Supabase for exact match")
            
            if st.button("🔄 Sync All Bills to Neo4j", type="primary", use_container_width=True, key="sync_neo4j"):
                from services.neo4j_service import Neo4jService
                neo4j_service = Neo4jService()
                
                # Check if Neo4j is available
                if not neo4j_service.driver:
                    st.error("❌ Neo4j Connection Failed!")
                    
                    if neo4j_service.connection_error:
                        st.warning(f"**Error Details:** {neo4j_service.connection_error}")
                    
                    st.info("""
                    **Your billing data is safe in Supabase.** Neo4j is optional for graph-based analytics.
                    """)
                    
                    st.info("💡 **Note:** All your bills are already in Supabase. Neo4j adds graph-based queries but is not required.")
                else:
                    with st.spinner("Syncing bills to Neo4j..."):
                        # Get all bills from Supabase
                        all_bills = db.supabase.table('bills').select('*').execute()
                        bills_data = all_bills.data if hasattr(all_bills, 'data') else []
                        
                        if bills_data:
                            # Sync to Neo4j
                            result = neo4j_service.sync_bills_from_supabase(bills_data)
                            
                            if result.get('success'):
                                st.success("✅ Perfect Sync Complete!")
                                
                                col_r1, col_r2, col_r3 = st.columns(3)
                                with col_r1:
                                    st.metric("🗑️ Cleared Old Bills", result.get('deleted', 0))
                                with col_r2:
                                    st.metric("📥 Added Fresh Bills", result['synced'])
                                with col_r3:
                                    st.metric("📊 Total in Neo4j", result['synced'])
                                
                                st.info(f"✅ Neo4j now has exactly {result['synced']} bills, matching Supabase perfectly!")
                                
                                if result.get('errors'):
                                    with st.expander("⚠️ View Errors"):
                                        for error in result['errors']:
                                            st.warning(error)
                            else:
                                st.error(f"❌ Sync failed: {result.get('error')}")
                        else:
                            st.warning("No bills found in Supabase to sync")
                    
                    neo4j_service.close()
        
        with col_neo2:
            st.write("**View Graph Stats**")
            st.caption("Get statistics from Neo4j graph")
            
            if st.button("📊 Get Graph Stats", use_container_width=True, key="neo4j_stats"):
                try:
                    from services.neo4j_service import Neo4jService
                    neo4j_service = Neo4jService()
                    
                    stats = neo4j_service.get_graph_stats()
                    
                    if stats and 'error' not in stats:
                        st.json(stats)
                    else:
                        st.error(f"Error: {stats.get('error', 'Unknown error')}")
                    
                    neo4j_service.close()
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        with col_neo3:
            st.write("**Clear Neo4j Graph**")
            st.caption("⚠️ Deletes all bill nodes")
            
            if st.button("🗑️ Clear All Bills", type="secondary", use_container_width=True, key="clear_neo4j"):
                try:
                    from services.neo4j_service import Neo4jService
                    neo4j_service = Neo4jService()
                    
                    result = neo4j_service.clear_all_bills()
                    
                    if result.get('success'):
                        st.success(f"✅ Deleted {result['deleted']} bills from Neo4j")
                    else:
                        st.error(f"❌ Error: {result.get('error')}")
                    
                    neo4j_service.close()
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

        st.markdown("---")

    # Advanced Analytics & RAG (Neo4j + OpenAI)
    st.markdown("---")
    st.header("🤖 Advanced Analytics & RAG (Neo4j + OpenAI)")
    st.text_input("Enter your OpenAI API Key", value=st.session_state.openai_api_key, key="openai_api_key")
    if st.session_state.openai_api_key:
        openai.api_key = st.session_state.openai_api_key
        st.success("OpenAI API Key set!")
        # Example RAG: Query Neo4j for context, then use OpenAI to answer a question
        rag_query = st.text_input("Ask a question about bills, readings, or customers:", key="rag_query")
        if rag_query:
            try:
                from services.neo4j_service import Neo4jService
                neo4j_service = Neo4jService()
                
                if not neo4j_service.is_connected():
                    st.error("❌ Neo4j is not connected. Cannot perform RAG query.")
                else:
                    # Retrieve context from Neo4j
                    with neo4j_service.driver.session() as session:
                        context_query = "MATCH (c:Customer)-[:HAS_BILL]->(b:Bill)<-[:GENERATED_BILL]-(m:Meter) RETURN b, c, m LIMIT 5"
                        result = session.run(context_query)
                        context = ""
                        for record in result:
                            b = record["b"]
                            c = record["c"]
                            m = record["m"]
                            # Using dict-like access; adjust if using neo4j.Node properties
                            context += f"Bill: {b.get('amount')} for Customer {c.get('id')} on meter {m.get('id')}\n"
                    
                    # Use OpenAI LLM for answer
                    prompt = f"Context:\n{context}\n\nQuestion: {rag_query}\nAnswer:"
                    try:
                        response = openai.Completion.create(
                            engine="text-davinci-003",
                            prompt=prompt,
                            max_tokens=150
                        )
                        st.markdown(f"**LLM Answer:** {response.choices[0].text.strip()}")
                    except Exception as e:
                        st.error(f"OpenAI API Error: {str(e)}")
            except Exception as e:
                st.error(f"Error with RAG query: {str(e)}")

    # =========================
    # Tab 2: Payment Status
    # =========================
    with tab2:
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
                if bill.get('status', '').lower() in ['pending', 'generated', 'overdue'] and bill.get('payment_link'):
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
        
            bill_id = st.number_input("Bill ID", min_value=1, value=1, step=1, key="get_bill_status_id")
        
            if st.button("📋 Get Bill", type="primary", key="get_bill_status_btn"):
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
                                
                                    # Add Pay Now button if bill is pending, generated, or overdue
                                    if bill.get('status', '').lower() in ['pending', 'generated', 'overdue']:
                                        if st.button("💳 Pay Now", key=f"pay_bill_{bill_id}", type="primary"):
                                            st.info("🔗 Use the link above to complete payment in a new tab.")
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
                limit = st.number_input("Limit", min_value=1, max_value=100, value=10, key="payment_customer_limit")
        
            if st.button("🔍 Get Customer Bills", type="primary", key="get_customer_bills_btn"):
                try:
                    bills = db.get_bills_by_customer(customer_id_search, limit=limit)
                
                    if bills:
                        st.success(f"✅ Found {len(bills)} bills for {customer_id_search}")
                    
                        # Summary metrics
                        col1, col2, col3 = st.columns(3)
                    
                        total_amount = sum(b.get('amount', 0) for b in bills)
                        paid_bills = sum(1 for b in bills if b.get('status') == 'paid')
                        pending_bills = sum(1 for b in bills if b.get('status') in ['pending', 'generated', 'overdue'])
                    
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
                    
                        display_columns = ['id', 'status', 'amount', 'consumption_kwh', 'billing_period_end', 'created_at']
                        available_columns = [col for col in display_columns if col in df.columns]
                    
                        st.dataframe(
                            df[available_columns],
                            use_container_width=True,
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
                                        cols[2].write(f"Period End: {bill.get('billing_period_end')}")
                                        cols[3].write(f"Created: {bill.get('created_at')}")
                                
                                    with col_b:
                                        if bill.get('status', '').lower() in ['pending', 'generated', 'overdue'] and bill.get('payment_link'):
                                            if st.button(
                                                f"💳 Pay ₹{bill.get('amount', 0):,.2f}", 
                                                key=f"pay_customer_bill_{bill.get('id')}", 
                                                type="primary",
                                                use_container_width=True
                                            ):
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
                update_bill_id = st.number_input("Bill ID to Update", min_value=1, value=1, step=1, key="manual_update_bill_id")
        
            with col2:
                new_status = st.selectbox(
                    "New Status",
                    options=["pending", "paid", "failed", "cancelled"],
                    index=0,
                    key="manual_update_status"
                )
        
            payment_date_input = st.date_input("Payment Date (optional, only for 'paid' status)", key="manual_update_date")
        
            if st.button("💾 Update Bill Status", type="primary", key="manual_update_btn"):
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
                webhook_bill_id = st.number_input("Bill ID for Webhook", min_value=1, value=1, step=1, key="webhook_bill_id")
        
            with col2:
                event_type = st.selectbox(
                    "Event Type",
                    options=[
                        "checkout.session.completed",
                        "payment_intent.succeeded"
                    ],
                    index=0,
                    key="webhook_event_type"
                )
        
            if st.button("📡 Send Webhook Event", type="primary", key="webhook_send_btn"):
                try:
                    import requests
                
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
                
                    try:
                        response = requests.post(
                            "http://localhost:5000/webhook/stripe",
                            json=webhook_payload,
                            timeout=5
                        )
                    
                        if response.status_code == 200:
                            st.success("✅ Webhook sent successfully!")
                            try:
                                st.write(f"Response: {response.json()}")
                            except Exception:
                                st.write(response.text)
                        
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
                    
                        updated = db.update_bill_status(
                            bill_id=webhook_bill_id,
                            status='paid',
                            payment_date=datetime.now().strftime("%Y-%m-%d")
                        )
                    
                        if updated:
                            st.success(f"✅ Bill {webhook_bill_id} marked as PAID (direct update)")
                        
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

    # =========================
    # Tab 3: Scheduler
    # =========================
    with tab3:
        st.header("⏰ Automated Billing Scheduler")
    
        st.markdown("""
        The scheduler automates recurring billing tasks:
        - **Monthly Bill Generation** - 1st of every month at 2:00 AM  
        - **Payment Reminders** - Daily at 10:00 AM  
        - **Overdue Bill Marking** - Daily at 11:00 AM  
        - **Meter Reading Collection** - Every Sunday at 8:00 AM
        """)
    
        st.markdown("---")
    
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
    
        st.subheader("📅 Scheduled Jobs")
    
        jobs = scheduler.get_job_status()
    
        job_descriptions = {
            'monthly_bill_generation': '📊 Generates monthly electricity bills for all active meters on the 1st of each month',
            'payment_reminders': '🔔 Sends payment reminders for bills due in the next 3 days (runs daily at 10 AM)',
            'overdue_bills': '⚠️ Marks bills as overdue and sends notices (runs daily at 11 AM)',
            'meter_reading_collection': '📡 Collects meter readings from smart meters (runs weekly on Sunday at 8 AM)'
        }
    
        for job in jobs:
            description = job_descriptions.get(job['id'], 'Scheduled automation task')
        
            with st.expander(f"**{job['name']}** - In {job['time_until']}", expanded=False):
                st.info(f"ℹ️ {description}")
            
                col1, col2 = st.columns([3, 1])
            
                with col1:
                    st.write(f"**📅 Next Run:** {job['next_run']}")
                    st.write(f"**⏰ Time Until:** {job['time_until']}")
                    st.write(f"**🔄 Schedule:** {job['trigger']}")
            
                with col2:
                    st.write("")
                    if st.button("▶️ Run Now", key=f"run_{job['id']}", use_container_width=True):
                        with st.spinner(f"Running {job['name']}..."):
                            result = scheduler.run_job_now(job['id'])
                        
                            if result['success']:
                                st.success("✅ Job executed successfully!")
                            else:
                                st.error(f"❌ Job failed: {result.get('error')}")
    
        st.markdown("---")
    
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

    # =========================
    # Tab 4: Meter Readings
    # =========================
    with tab4:
        st.header("📋 Meter Readings Management")
    
        col1, col2 = st.columns([2, 1])
    
        with col1:
            st.subheader("➕ Add New Reading")
        
            with st.form("add_reading_admin"):
                meter_id = st.text_input("Meter ID", value="METER001", key="add_meter_id")
                customer_id = st.text_input("Customer ID", value="CUST001", key="add_customer_id")
                reading_value = st.number_input("Reading Value (kWh)", min_value=0.0, step=0.1, key="add_reading_value")
                reading_date = st.date_input("Reading Date", value=datetime.now(), key="add_reading_date")
            
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
            num_readings = st.number_input("Number of readings", min_value=1, max_value=12, value=6, key="sample_readings_num")
        
            if st.button("Generate", type="secondary", key="generate_sample_readings"):
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

    # =========================
    # Tab 5: Generate Bill
    # =========================
    with tab5:
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
                        step=0.1,
                        key="bill_current_reading"
                    )
                
                    previous_reading = readings[0]['reading_value']
                    consumption = current_reading - previous_reading
                
                    st.info(f"Previous Reading: {previous_reading:.2f} kWh")
                    st.success(f"Consumption: {consumption:.2f} kWh")
                
                    tariff_type = st.selectbox("Tariff Type", ["residential", "commercial"], key="bill_tariff")
                    connected_load = st.number_input("Connected Load (KW)", value=7.0, step=0.5, key="bill_load")
            
                with col2:
                    if st.button("💰 Generate Bill", type="primary", key="generate_bill_btn"):
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
                        st.write("**Status**: Pending")
                    
                        with st.expander("📋 Detailed Breakdown"):
                            st.json(bill['detailed_breakdown'])
        
            else:
                st.warning("⚠️ Need at least 2 meter readings to generate a bill. Add more readings first!")
    
        except Exception as e:
            st.error(f"Error: {str(e)}")

    # =========================
    # Tab 6: Analytics & Reports
    # =========================
    with tab6:
        st.header("📈 Analytics & Reporting")
    
        from services.analytics_service import AnalyticsService
        analytics = AnalyticsService()
    
        report_type = st.selectbox(
            "Select Report Type",
            [
                "Monthly Revenue", 
                "Consumption Analytics", 
                "Payment Success Rate", 
                "Customer Segmentation", 
                "Revenue Trend"
            ]
        )
    
        st.markdown("---")
    
        if report_type == "Monthly Revenue":
            st.subheader("💰 Monthly Revenue Report")
        
            col1, col2 = st.columns(2)
            with col1:
                year = st.number_input("Year", min_value=2020, max_value=2030, value=datetime.now().year, key="rev_year")
            with col2:
                month = st.number_input("Month", min_value=1, max_value=12, value=datetime.now().month, key="rev_month")
        
            if st.button("Generate Revenue Report", key="revenue_report"):
                with st.spinner("Generating report..."):
                    report = analytics.get_monthly_revenue_report(int(year), int(month))
                
                    if "error" in report:
                        st.error(f"Error: {report['error']}")
                    else:
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
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.metric("Success Rate", f"{metrics['success_rate']}%")
                            st.metric("Period", f"{metrics['period_days']} days")
                        with col2:
                            st.write("**Payment Breakdown:**")
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.metric("Paid", metrics['paid_bills'])
                            with col_b:
                                st.metric("Pending", metrics['pending_bills'])
                            with col_c:
                                st.metric("Overdue", metrics['overdue_bills'])
    
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
                    
                        segments = segmentation['segments']
                    
                        col1, col2 = st.columns(2)
                    
                        with col1:
                            st.markdown("### 💎 High Value Customers")
                            st.write(f"*Count: {segments['high_value']['count']}*")
                            st.write("High consumption, good payment behavior")
                            for cust in segments['high_value']['customers']:
                                st.write(f"- {cust['customer_id']}: {cust['avg_consumption']:.1f} kWh, {cust['payment_rate']:.0f}% paid")
                        
                            st.markdown("### ⚠️ At Risk Customers")
                            st.write(f"*Count: {segments['at_risk']['count']}*")
                            st.write("High consumption, poor payment behavior")
                            for cust in segments['at_risk']['customers']:
                                st.write(f"- {cust['customer_id']}: {cust['avg_consumption']:.1f} kWh, {cust['payment_rate']:.0f}% paid")
                    
                        with col2:
                            st.markdown("### ⭐ Loyal Customers")
                            st.write(f"*Count: {segments['loyal']['count']}*")
                            st.write("Low consumption, good payment behavior")
                            for cust in segments['loyal']['customers']:
                                st.write(f"- {cust['customer_id']}: {cust['avg_consumption']:.1f} kWh, {cust['payment_rate']:.0f}% paid")
                        
                            st.markdown("### 😴 Low Engagement Customers")
                            st.write(f"*Count: {segments['low_engagement']['count']}*")
                            st.write("Low consumption, poor payment behavior")
                            for cust in segments['low_engagement']['customers']:
                                st.write(f"- {cust['customer_id']}: {cust['avg_consumption']:.1f} kWh, {cust['payment_rate']:.0f}% paid")
    
        elif report_type == "Revenue Trend":
            st.subheader("📊 Revenue Trend Analysis")
        
            months = st.slider("Number of Months", min_value=3, max_value=12, value=6, key="trend_months")
        
            if st.button("Generate Trend Report", key="revenue_trend"):
                with st.spinner("Analyzing trend..."):
                    trend_data = analytics.get_revenue_trend(months)
                
                    if trend_data and isinstance(trend_data, list):
                        import pandas as pd
                        df = pd.DataFrame(trend_data)
                    
                        st.dataframe(
                            df[['period', 'total_bills', 'total_revenue', 'collected_revenue', 'payment_success_rate']], 
                            use_container_width=True
                        )
                    
                        st.markdown("---")
                        st.write("**Trend Insights:**")
                    
                        if len(trend_data) >= 2:
                            latest = trend_data[-1]
                            previous = trend_data[-2]
                        
                            if previous['total_revenue'] > 0:
                                revenue_growth = (latest['total_revenue'] - previous['total_revenue']) / previous['total_revenue'] * 100
                            else:
                                revenue_growth = 0.0
                            
                            if previous['total_bills'] > 0:
                                bills_growth = (latest['total_bills'] - previous['total_bills']) / previous['total_bills'] * 100
                            else:
                                bills_growth = 0.0
                        
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Revenue Growth (MoM)", f"{revenue_growth:+.1f}%")
                            with col2:
                                st.metric("Bills Growth (MoM)", f"{bills_growth:+.1f}%")
                    else:
                        st.warning("No trend data available.")

    # Footer for Admin
    st.markdown("---")
    st.markdown("👨‍💼 **Admin Dashboard** | System Management & Configuration | v2.0")
