"""Fix indentation in streamlit_app.py"""

with open('streamlit_app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the admin if block and add 4 spaces to tabs 2-6 content
fixed_lines = []
in_admin_tabs = False
indent_level = 0

for i, line in enumerate(lines):
    # Check if we're entering admin block
    if i > 50 and 'if st.session_state.user_role == "Admin":' in line:
        in_admin_tabs = True
        fixed_lines.append(line)
        continue
    
    # Check if we're leaving admin block
    if 'elif st.session_state.user_role == "Engineer":' in line:
        in_admin_tabs = False
        fixed_lines.append(line)
        continue
    
    # If in admin block and line starts with 'with tab', we need to indent its content
    if in_admin_tabs:
        # Lines starting with 'with tab' (except tab1 which is already indented)
        if line.startswith('with tab') and not line.startswith('    with tab1'):
            # Add 4 spaces to make it '    with tab'
            fixed_lines.append('    ' + line)
        # Content lines that follow 'with tab' also need indentation
        elif not line.startswith(' ') and line.strip() and i > 84:
            # Check if previous line was 'with tab' or we're in a tab block
            if i > 0 and ('with tab' in lines[i-1] or not lines[i-1].strip().startswith('# Tab ')):
                # Add 4 spaces
                fixed_lines.append('    ' + line)
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    else:
        fixed_lines.append(line)

# Write back
with open('streamlit_app.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print("✅ Fixed indentation")
