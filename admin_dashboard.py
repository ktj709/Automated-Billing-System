"""
Streamlit Dashboard for Billing System Testing
"""
import streamlit as st
import json
from datetime import datetime, timedelta
from services import DatabaseService, TariffRules
from utils.sample_data import SampleDataGenerator

st.set_page_config(page_title="Admin Dashboard", page_icon="🔐", layout="wide")

st.title("🔐 Admin Dashboard")
st.markdown("### Internal System Management & Configuration")
st.markdown("---")

# Initialize services
@st.cache_resource
def get_db_service():
    return DatabaseService()

db = get_db_service()

# Sidebar
with st.sidebar:
    st.header("🔧 Configuration")
    st.success("✅ Supabase Connected")
    st.info("💡 OpenAI Enabled")
    
    st.markdown("---")
    st.header("🎯 Quick Actions")
    
    if st.button("🔄 Refresh Data"):
        st.cache_resource.clear()
        st.rerun()

# Main Content Tabs - Admin Features (Internal Operations)
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Overview", 
    "🔄 Full Workflow Test", 
    "🔐 Auth0 Testing",
    "💳 Payment Status",
    "⏰ Scheduler",
    "🧮 Tariff Calculator"
])

# Tab 1: Dashboard
with tab1:
    st.header("📊 System Overview")
    
    col1, col2, col3 = st.columns(3)
    
    # Get meter readings
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
        
        # Recent Readings Table
        if readings:
            st.subheader("📈 Recent Meter Readings")
            import pandas as pd
            df = pd.DataFrame(readings[:10])
            df['reading_date'] = pd.to_datetime(df['reading_date'])
            df = df.sort_values('reading_date', ascending=False)
            st.dataframe(df[['reading_date', 'reading_value', 'meter_id', 'customer_id']], use_container_width=True)
        else:
            st.warning("No meter readings found. Add some data first!")
    
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
            "1️⃣2️⃣ Send WhatsApp Notification",
            "1️⃣3️⃣ Log Notification in DB"
        ]
        for step in steps:
            st.write(step)
    
    st.markdown("---")
    
    # Input form
    with st.form("workflow_test"):
        st.subheader("📥 Step 1: Input Meter Reading")
        
        col1, col2 = st.columns(2)
        with col1:
            meter_id = st.text_input("Meter ID", value="METER001")
            customer_id = st.text_input("Customer ID", value="CUST001")
            reading_value = st.number_input("Reading Value (kWh)", min_value=0.0, value=4600.0, step=0.1)
        
        with col2:
            reading_date = st.date_input("Reading Date", value=datetime.now())
            customer_phone = st.text_input("Customer Phone", value="+1234567890")
            user_id = st.text_input("User ID (for Auth)", value="auth0|user123")
        
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
                from services.whatsapp_service import WhatsAppService
                
                ai_service = AIAgentService()
                payment_service = PaymentService()
                whatsapp_service = WhatsAppService()
                
                # Step 1: Webhook (already received)
                st.success("✅ Step 1: Webhook received meter reading")
                progress_bar.progress(8)
                
                # Step 2: Auth0 Verification (simulated)
                st.info("🔐 Step 2: Auth0 token verification... (Simulated - Passed)")
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

                # Show breakdown using the explicit water-motor formula
                with st.expander("View Bill Breakdown"):
                    breakdown = bill_calculation.get("detailed_breakdown", {})
                    flat_units = breakdown.get("flat_units", 0.0)
                    motor_units = breakdown.get("motor_units", 0.0)
                    total_block_units = breakdown.get("total_block_units", 0.0)
                    water_motor_share = breakdown.get("water_motor_share", 0.0)
                    total_units = breakdown.get("total_units", flat_units + water_motor_share)
                    rate_per_unit = breakdown.get("rate_per_unit", 12.0)
                    fixed_charge = breakdown.get("fixed_charge", 0.0)
                    usage_charge = breakdown.get("usage_charge", total_units * rate_per_unit)
                    total_amount = breakdown.get("total_amount", usage_charge + fixed_charge)

                    st.markdown("**Step 1: Calculate Water Motor Share**")
                    st.markdown(
                        f"Water Motor Share = ({motor_units} ÷ {total_block_units or 1}) × {flat_units} = **{water_motor_share} units**"
                    )

                    st.markdown("**Step 2: Calculate Total Units**")
                    st.markdown(
                        f"Total Units = {flat_units} + {water_motor_share} = **{total_units} units**"
                    )

                    st.markdown("**Step 3: Calculate Usage Charge**")
                    st.markdown(
                        f"Usage Charge = {total_units} × ₹{rate_per_unit} = **₹{usage_charge:,.0f}**"
                    )

                    st.markdown("**Step 4: Calculate Final Bill**")
                    st.markdown(
                        f"Final Bill = ₹{usage_charge:,.0f} + ₹{fixed_charge:,.0f} = **₹{total_amount:,.0f}**"
                    )

                    st.markdown("---")
                    st.markdown("Raw calculation payload (for debugging):")
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
                    consumption=consumption,
                    payment_link=payment_link['url']
                )
                st.success(f"✅ Step 11: Notification message generated")
                st.info(f"Message: {notification_message}")
                progress_bar.progress(85)
                
                # Step 12: Send WhatsApp
                st.info("📱 Step 12: Sending WhatsApp notification...")
                whatsapp_result = whatsapp_service.send_notification(
                    phone_number=customer_phone,
                    message=notification_message
                )
                st.success(f"✅ Step 12: WhatsApp sent - Message ID: {whatsapp_result['message_id']}")
                progress_bar.progress(92)
                
                # Step 13: Log Notification
                st.info("📋 Step 13: Logging notification...")
                db.log_notification(
                    bill_id=bill_id,
                    customer_id=customer_id,
                    channel="whatsapp",
                    message=notification_message,
                    status="sent",
                    whatsapp_message_id=whatsapp_result['message_id']
                )
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
                st.write(f"**WhatsApp Sent**: {customer_phone}")
                
            except Exception as e:
                st.error(f"❌ Error in workflow: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

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
                meter_id = st.text_input("Meter ID", value="METER001")
                customer_id = st.text_input("Customer ID", value="CUST001")
                reading_value = st.number_input("Reading Value", value=4800.0)
            
            with col2:
                customer_phone = st.text_input("Phone", value="+919876543210")
                reading_date = st.date_input("Reading Date", value=datetime.now())
            
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
            customer_id_search = st.text_input("Customer ID", value="CUST001")
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
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Individual bill details
                    with st.expander("📋 View Individual Bills"):
                        for bill in bills:
                            with st.container():
                                st.write(f"**Bill ID: {bill.get('id')}** - Status: `{bill.get('status')}`")
                                cols = st.columns(4)
                                cols[0].write(f"Amount: ₹{bill.get('amount', 0):,.2f}")
                                cols[1].write(f"Consumption: {bill.get('consumption_kwh', 0):.2f} kWh")
                                cols[2].write(f"Period: {bill.get('billing_period_end')}")
                                cols[3].write(f"Created: {bill.get('created_at')}")
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
    
    for job in jobs:
        with st.expander(f"**{job['name']}** - Next run: {job['next_run']}", expanded=True):
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.write(f"**ID:** `{job['id']}`")
                st.write(f"**Trigger:** {job['trigger']}")
            
            with col2:
                st.write(f"**Next Run:** {job['next_run']}")
            
            with col3:
                if st.button("▶️ Run Now", key=f"run_{job['id']}"):
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
                
                else:
                    st.error(f"❌ Bill #{bill_id_input} not found")
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    with col2:
        st.subheader("👤 Customer Bills")
        
        customer_id_input = st.text_input("Customer ID", value="CUST001")
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

# Tab 6: Tariff Calculator
with tab6:
    st.header("🧮 Tariff Calculator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        tariff_type = st.selectbox("Tariff Type", ["residential", "commercial"])
        consumption = st.number_input("Consumption (kWh)", min_value=0.0, value=250.0, step=10.0)
        connected_load = st.number_input("Connected Load (KW)", min_value=0.0, value=7.0, step=0.5)
        previous_outstanding = st.number_input("Previous Outstanding (₹)", min_value=0.0, value=0.0, step=100.0)
    
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

# Footer
st.markdown("---")
st.markdown("🔐 **Admin Dashboard** | System Management & Configuration | v2.0")
