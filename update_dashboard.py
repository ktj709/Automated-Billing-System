"""
Script to add Fixed & Maintenance charges column to the Admin Dashboard
"""
import re

def update_streamlit_app():
    """Update streamlit_app.py to add Fixed charges column and proper bill calculation"""
    
    file_path = "streamlit_app.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Update table header columns (line 789)
    old_header = '''                # Table Header
                h1, h2, h3, h4, h5, h6, h7, h8 = st.columns([1.2, 0.8, 0.8, 1.5, 1, 1, 1, 1.5])
                h1.markdown("**Unit ID**")
                h2.markdown("**Flat**")
                h3.markdown("**Floor**")
                h4.markdown("**Client Name**")
                h5.markdown("**Meter ID**")
                h6.markdown("**Reading**")
                h7.markdown("**Est. (₹)**")
                h8.markdown("**Actions**")'''
    
    new_header = '''                # Table Header
                h1, h2, h3, h4, h5, h6, h7, h8, h9 = st.columns([1, 0.7, 0.7, 1.3, 0.9, 0.9, 1, 1, 1.3])
                h1.markdown("**Unit ID**")
                h2.markdown("**Flat**")
                h3.markdown("**Floor**")
                h4.markdown("**Client Name**")
                h5.markdown("**Meter ID**")
                h6.markdown("**Reading**")
                h7.markdown("**Fixed (₹)**")
                h8.markdown("**Est. (₹)**")
                h9.markdown("**Actions**")'''
    
    content = content.replace(old_header, new_header)
    
    # 2. Update loop columns (line 801)
    old_loop_cols = '''                for i, r in enumerate(display_readings[:5]):  # Show top 5
                    c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([1.2, 0.8, 0.8, 1.5, 1, 1, 1, 1.5])'''
    
    new_loop_cols = '''                for i, r in enumerate(display_readings[:5]):  # Show top 5
                    c1, c2, c3, c4, c5, c6, c7, c8, c9 = st.columns([1, 0.7, 0.7, 1.3, 0.9, 0.9, 1, 1, 1.3])'''
    
    content = content.replace(old_loop_cols, new_loop_cols)
    
    # 3. Update bill calculation logic (lines 811-816)
    old_calculation = '''                    reading_val = r.get("reading_value")
                    
                    # Calculate estimated bill (simple logic)
                    prev_reading = 0 # TODO: Fetch previous reading
                    usage = reading_val - prev_reading if reading_val else 0
                    energy_amount = (usage or 0) * 7.5  # Approx rate'''
    
    new_calculation = '''                    reading_val = r.get("reading_value")
                    
                    # Get flat info for tariff calculation
                    flat_info = next((f for f in flats if f.get('meter_id') == meter_id), {})
                    tariff_type = flat_info.get('type', 'residential')
                    
                    # Calculate Fixed Charges
                    try:
                        tariff = TariffRules.get_tariff_by_type(tariff_type)
                        fixed_charges = tariff.get("fixed_charges", {})
                        connected_load = 5.0
                        total_fixed = (
                            fixed_charges.get("motor_charges", 0) +
                            fixed_charges.get("common_area_maintenance", 0) +
                            (fixed_charges.get("grid_charges_per_kw", 0) * connected_load)
                        )
                    except Exception:
                        total_fixed = 0.0
                    
                    # Calculate estimated bill using TariffRules
                    try:
                        # Fetch previous reading (excluding current one)
                        history = db.get_historical_readings(meter_id, limit=10)
                        prev_reading = 0
                        
                        # Find the previous reading (skip the current one if it's already in history)
                        for h in history:
                            # Skip if this is the current reading (same ID)
                            if h.get('id') == r.get('id'):
                                continue
                            # This is a previous reading
                            prev_reading = h['reading_value']
                            break
                        
                        # Calculate consumption
                        consumption = reading_val - prev_reading
                        if consumption < 0:
                            consumption = 0
                        
                        # Use TariffRules to calculate complete bill
                        bill_calc = TariffRules.calculate_total_bill(
                            consumption_kwh=consumption,
                            connected_load_kw=connected_load,
                            tariff_type=tariff_type
                        )
                        est_amount = bill_calc['amount_payable']
                    except Exception:
                        est_amount = 0.0'''
    
    content = content.replace(old_calculation, new_calculation)
    
    # 4. Update display columns (lines 828-833)
    old_display = '''                    with c6:
                        st.write(f"{reading_val}")
                    with c7:
                        st.write(f"₹{energy_amount:.0f}")

                    with c8:'''
    
    new_display = '''                    with c6:
                        st.write(f"{reading_val}")
                    with c7:
                        st.write(f"₹{total_fixed:,.0f}")
                    with c8:
                        st.write(f"₹{est_amount:,.0f}")

                    with c9:'''
    
    content = content.replace(old_display, new_display)
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Successfully updated streamlit_app.py")
    print("Changes made:")
    print("  - Added 'Fixed (₹)' column to table header")
    print("  - Updated bill calculation to use TariffRules")
    print("  - Added fixed charges calculation")
    print("  - Updated column display logic")

if __name__ == "__main__":
    update_streamlit_app()
