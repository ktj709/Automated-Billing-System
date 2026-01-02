"""
Fix indentation for role-based dashboards in streamlit_app.py
"""

with open('streamlit_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Split by lines
lines = content.split('\n')

fixed_lines = []
in_admin_section = False
admin_tabs_content = False
skip_until_engineer = False

for i, line in enumerate(lines):
    # Detect admin section start
    if 'if st.session_state.user_role == "Admin":' in line:
        fixed_lines.append(line)
        in_admin_section = True
        continue
    
    # Detect engineer section start
    if 'elif st.session_state.user_role == "Engineer":' in line or (in_admin_section and '# ==================== ENGINEER' in line):
        in_admin_section = False
        skip_until_engineer = False
        # Remove 'elif', use 'else' instead
        if 'elif' in line:
            fixed_lines.append(line.replace('elif', 'else:  #'))
        else:
            fixed_lines.append('\n# ==================== ENGINEER DASHBOARD ====================')
            fixed_lines.append('else:  # Engineer role')
        continue
    
    # In admin section - add 4 spaces to lines that start tabs and their content
    if in_admin_section:
        # Tab declaration lines
        if line.strip().startswith('# Tab') or line.strip().startswith('with tab'):
            if not line.startswith('    '):
                fixed_lines.append('    ' + line)
                admin_tabs_content = True
            else:
                fixed_lines.append(line)
        # Content within admin tabs
        elif admin_tabs_content and line.strip():
            # Add indentation if not already indented enough
            if not line.startswith('        ') and not line.startswith('    #'):
                # Count current indentation
                indent_count = len(line) - len(line.lstrip())
                if indent_count < 8:  # Need at least 8 spaces in tab content
                    fixed_lines.append('        ' + line.lstrip())
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    else:
        fixed_lines.append(line)

# Write back
with open('streamlit_app.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(fixed_lines))

print("✅ Fixed indentation in streamlit_app.py")
