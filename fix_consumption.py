"""
Fix consumption calculation to exclude current reading from history
"""

def fix_consumption_calc():
    file_path = "streamlit_app.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find and replace lines 833-837
    # Old: limit=2 and using history[1]
    # New: limit=10 and loop through to skip current reading
    
    old_lines = [
        "                        # Fetch previous reading\n",
        "                        history = db.get_historical_readings(meter_id, limit=2)\n",
        "                        prev_reading = 0\n",
        "                        if len(history) > 1:\n",
        "                            prev_reading = history[1]['reading_value']\n"
    ]
    
    new_lines = [
        "                        # Fetch previous reading (excluding current one)\n",
        "                        history = db.get_historical_readings(meter_id, limit=10)\n",
        "                        prev_reading = 0\n",
        "                        \n",
        "                        # Find the previous reading (skip the current one if it's already in history)\n",
        "                        for h in history:\n",
        "                            # Skip if this is the current reading (same ID)\n",
        "                            if h.get('id') == r.get('id'):\n",
        "                                continue\n",
        "                            # This is a previous reading\n",
        "                            prev_reading = h['reading_value']\n",
        "                            break\n"
    ]
    
    # Find the starting line (search for the pattern)
    start_idx = None
    for i in range(len(lines) - 5):
        if (lines[i].strip() == "# Fetch previous reading" and
            "limit=2" in lines[i+1]):
            start_idx = i
            break
    
    if start_idx is None:
        print("❌ Could not find the target lines to replace")
        return False
    
    # Replace the lines
    lines[start_idx:start_idx+5] = new_lines
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("✅ Successfully fixed consumption calculation")
    print(f"   Updated lines {start_idx+1} to {start_idx+len(new_lines)}")
    return True

if __name__ == "__main__":
    fix_consumption_calc()
