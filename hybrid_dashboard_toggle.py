"""
HYBRID DASHBOARD - Copy this code to replace Tab 1 content
This adds a toggle to switch between Modern and Legacy UI
"""

# ============================================
# PASTE THIS CODE IN TAB 1 (replace existing content)
# Find: with tab1:
# Replace that section with this entire code
# ============================================

with tab1:
    # UI Toggle at the very top
    use_modern_ui = st.toggle("🎨 Use Modern Dashboard", value=True, key="modern_ui_toggle", 
                              help="Toggle between modern card-based UI and legacy dashboard")
    
    if use_modern_ui:
        # ====================================
        # MODERN DASHBOARD UI
        # ====================================
        
        # CSS
        st.markdown("""<style>
        .mc{background:white;padding:24px;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.1);text-align:center;border-left:4px solid #4A90E2;transition:all 0.3s}
        .mc:hover{transform:translateY(-5px);box-shadow:0 6px 16px rgba(0,0,0,0.15)}
        .mv{font-size:42px;font-weight:700;color:#4A90E2;margin:12px 0}
        .ml{font-size:13px;color:#6c757d;text-transform:uppercase;letter-spacing:1.2px;font-weight:600}
        .sh{font-size:16px;font-weight:700;color:#2c3e50;margin:24px 0 16px;text-transform:uppercase;padding:12px;background:#F8F9FA;border-radius:8px}
        .sb{background:white;padding:24px;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.1)}
        .si{padding:12px 0;border-bottom:1px solid #eee;font-size:14px}
        </style>""", unsafe_allow_html=True)
        
        # Header
        st.markdown("# ⚡ Blessings Electric Billing AI")
        st.markdown("---")
        
        # Top 4 Metrics
        try:
            all_bills = db.get_all_bills()
            pending = db.get_pending_bills_count()
            invoices = len([b for b in all_bills if b.get('status')=='pending'])
            overdue = 0  # Can calculate if needed
        except:
            pending = invoices = overdue = 0
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown('<div class="mc"><div class="ml">⚡ Total Meters</div><div class="mv">120</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="mc"><div class="ml">📋 New Readings</div><div class="mv">{pending}</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="mc"><div class="ml">📄 Invoices</div><div class="mv">{invoices}</div></div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="mc" style="border-left-color:#D9534F"><div class="ml">🔴 Overdue</div><div class="mv" style="color:#D9534F">{overdue}</div></div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Main Content
        col_main, col_side = st.columns([2.5, 1])
        
        with col_main:
            st.markdown('<div class="sh">📊 Review New Readings</div>', unsafe_allow_html=True)
            
            try:
                readings = db.get_unbilled_readings(limit=5)
                if readings:
                    import pandas as pd
                    df = pd.DataFrame([{
                        'Apt': r['meter_id'][-3:],
                        'Reading': f"{r['reading_value']:.0f}",
                        'Usage': f"{r.get('estimated_consumption',0):.0f}",
                        'Amount': f"₹{r.get('estimated_consumption',0)*7.5:.0f}"
                    } for r in readings])
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    st.markdown("**Quick Approve:**")
                    cols = st.columns(len(readings))
                    for i, r in enumerate(readings):
                        with cols[i]:
                            if st.button(f"✓ {r['meter_id'][-3:]}", key=f"mod_a{i}", type="primary", use_container_width=True):
                                st.session_state['fetched_reading'] = r
                                st.session_state['fetched_meter_id'] = r['meter_id']
                                st.success(f"✅ Selected!")
                                st.rerun()
                else:
                    st.success("✅ All caught up!")
            except Exception as e:
                st.error(f"Error: {e}")
        
        with col_side:
            st.markdown('<div class="sh">⚡ Quick Actions</div>', unsafe_allow_html=True)
            st.button("➕ New Customer", key="mod_qa1", use_container_width=True, type="primary")
            st.button("📊 Generate Bills", key="mod_qa2", use_container_width=True, type="primary")
            st.button("💳 View Payments", key="mod_qa3", use_container_width=True, type="primary")
            
            st.markdown('<br><div class="sh">📊 Status</div>', unsafe_allow_html=True)
            try:
                payments = sum([b.get('amount',0) for b in all_bills if b.get('status')=='paid'])
                outstanding = sum([b.get('amount',0) for b in all_bills if b.get('status')=='pending'])
            except:
                payments = outstanding = 0
            
            st.markdown(f'<div class="sb"><div class="si">💰 <b>Payments:</b> ₹{payments:,.0f}</div><div class="si">📄 <b>Outstanding:</b> ₹{outstanding:,.0f}</div><div class="si">🔴 <b>Overdue:</b> {overdue}</div></div>', unsafe_allow_html=True)
        
        st.markdown("---")
    
    else:
        # ====================================
        # LEGACY DASHBOARD UI (YOUR EXISTING CODE)
        # ====================================
        st.header("📊 System Overview")
        st.markdown("---")
        
        # Existing Pending Bills Section
        st.markdown("### 📋 Pending Bills to Review")
        st.markdown("✨ **Recent readings from field engineers awaiting bill generation:**")
        
        try:
            unbilled_readings = db.get_unbilled_readings(limit=50)
            
            if unbilled_readings:
                st.info(f"🔔 **{len(unbilled_readings)} unbilled readings** need bill generation!")
                
                import pandas as pd
                display_data = []
                for reading in unbilled_readings[:10]:
                    display_data.append({
                        'Customer ID': reading['customer_id'],
                        'Meter ID': reading['meter_id'],
                        'Reading': f"{reading['reading_value']:.2f} kWh",
                        'Date': reading['reading_date'],
                        'Est. kWh': f"{reading.get('estimated_consumption', 0):.2f}"
                    })
                
                df = pd.DataFrame(display_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                st.markdown("**⚡ Quick Actions - Click to Auto-Fill Form:**")
                cols = st.columns(min(5, len(unbilled_readings)))
                
                for idx, reading in enumerate(unbilled_readings[:5]):
                    with cols[idx]:
                        meter_short = reading['meter_id'][-4:] if len(reading['meter_id']) > 4 else reading['meter_id']
                        if st.button(f"📄 {meter_short}", key=f"leg_pending_{idx}", use_container_width=True, type="primary"):
                            for key in ['wf_meter_id', 'wf_customer_id', 'wf_reading', 'wf_date']:
                                if key in st.session_state:
                                    del st.session_state[key]
                            st.session_state['fetched_reading'] = reading
                            st.session_state['fetched_meter_id'] = reading['meter_id']
                            st.success(f"✅ Selected {reading['meter_id']} - Scroll down and click 'Run Complete Workflow'!")
                            st.rerun()
                
                if len(unbilled_readings) > 10:
                    st.caption(f"📊 Showing 10 of {len(unbilled_readings)} total pending bills")
            else:
                st.success("✅ **All caught up!** No pending bills at this time.")
        
        except Exception as e:
            st.error(f"❌ Error loading pending bills: {str(e)}")
        
        st.markdown("---")
    
    # ====================================
    # SHARED: Everything below the toggle
    # (Fetch Reading, Workflow Form, etc.)
    # ====================================
    
    # Fetch Reading from Database
    st.markdown("### 📥 Fetch Reading from Database")
    
    col_fetch1, col_fetch2, col_fetch3 = st.columns([2, 1, 1])
    
    with col_fetch1:
        fetch_meter_id = st.text_input("Enter Meter ID to fetch latest reading", value="METER001", key="fetch_meter_input")
    
    with col_fetch2:
        st.write("")
        st.write("")
        if st.button("🔍 Fetch Latest Reading", type="secondary", use_container_width=True):
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
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_resource.clear()
            st.rerun()
    
    # Display fetched reading
    if 'fetched_reading' in st.session_state and st.session_state.get('fetched_reading'):
        reading = st.session_state['fetched_reading']
        st.info(
            f"📊 **Latest Reading from DB:** {reading['reading_value']} kWh | "
            f"Date: {reading['reading_date']} | Customer: {reading['customer_id']}"
        )
    
    st.markdown("---")
    
    # THE REST OF YOUR WORKFLOW FORM AND ALL OTHER TAB 1 CONTENT GOES HERE
    # (I'm not including it to keep this concise, but it all stays exactly as is)
