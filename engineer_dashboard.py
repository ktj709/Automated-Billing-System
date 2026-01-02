"""
Streamlit Dashboard for Billing System Testing
"""
import streamlit as st
import json
from datetime import datetime, timedelta
from services import DatabaseService, TariffRules
from utils.sample_data import SampleDataGenerator

st.set_page_config(page_title="Engineer Dashboard", page_icon="👷", layout="wide")

st.title("👷 Engineer Dashboard")
st.markdown("### Meter Reading & Field Operations")
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

# Main Content Tabs - Engineer Features (Field Operations)
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Overview",
    "📋 Meter Readings",
    "➕ Add Reading",
    "💰 Generate Bill"
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


# Tab 2: Meter Readings (was tab7)
with tab2:
Already replaced above
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

# Tab 2: Meter Readings History
with tab2:
    st.header("📋 Meter Readings History")
    
    meter_filter = st.text_input("Filter by Meter ID", value="METER001")
    
    try:
        readings = db.get_historical_readings(meter_filter, limit=50)
        
        if readings:
            import pandas as pd
            df = pd.DataFrame(readings)
            df['reading_date'] = pd.to_datetime(df['reading_date'])
            df = df.sort_values('reading_date', ascending=False)
            
            st.dataframe(df, use_container_width=True)
            
            # Download option
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

# Tab 3: Add New Reading
with tab3:
    st.header("➕ Add New Meter Reading")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("➕ Add New Reading")
        
        with st.form("add_reading"):
            meter_id = st.text_input("Meter ID", value="METER001")
            customer_id = st.text_input("Customer ID", value="CUST001")
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

# Tab 4: Generate Bill
with tab4:
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

# Footer
st.markdown("---")
st.markdown("👷 **Engineer Dashboard** | Meter Reading & Field Operations | v2.0")

