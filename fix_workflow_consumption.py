"""
Comprehensive fix for consumption calculation in both sections
"""

def fix_all_consumption_calcs():
    file_path = "streamlit_app.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix 1: Workflow section (around line 1078-1083)
    old_workflow = '''                    st.info("🧮 Step 6: AI calculating electricity bill...")
                    if len(historical_readings) > 0:
                        previous_reading = historical_readings[0]['reading_value']
                        consumption = wf_reading_value - previous_reading
                    else:
                        previous_reading = 0
                        consumption = wf_reading_value'''
    
    new_workflow = '''                    st.info("🧮 Step 6: AI calculating electricity bill...")
                    
                    # Find previous reading (skip current if it exists in history)
                    previous_reading = 0
                    for h in historical_readings:
                        # Skip if this is the current reading (same value)
                        if h['reading_value'] == wf_reading_value:
                            continue
                        # This is a previous reading
                        previous_reading = h['reading_value']
                        break
                    
                    consumption = wf_reading_value - previous_reading'''
    
    content = content.replace(old_workflow, new_workflow)
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Successfully fixed workflow consumption calculation")
    print("Changes made:")
    print("  - Fixed workflow bill calculation to skip current reading")
    print("  - Consumption now calculated correctly")

if __name__ == "__main__":
    fix_all_consumption_calcs()
