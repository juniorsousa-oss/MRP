from pathlib import Path
p=Path('app_mrp.py')
s=p.read_text(encoding='utf-8')

# Login: make the image/header proportion closer to the provided reference.
s=s.replace('"login_image_height": 210', '"login_image_height": 135')
s=s.replace('int(login_cfg.get("login_image_height") or 210)', 'int(login_cfg.get("login_image_height") or 135)')
s=s.replace('max(140, min(300, int(login_cfg.get("login_image_height") or 135)))', 'max(100, min(240, int(login_cfg.get("login_image_height") or 135)))')
s=s.replace('.setta-login-heading {{ text-align:center; padding: 24px 28px 4px; }}', '.setta-login-heading {{ text-align:center; padding: 18px 28px 7px; }}')
s=s.replace('.setta-login-title {{ color:{title_color}; font-size:1.55rem;', '.setta-login-title {{ color:{title_color}; font-size:1.4rem;')
s=s.replace('.setta-login-form-note {{ text-align:center; color:{text}; opacity:.62; font-size:.78rem; margin: 0 0 10px; }}', '.setta-login-form-note {{ text-align:center; color:{text}; opacity:.62; font-size:.78rem; margin: 2px 0 8px; }}')
s=s.replace('min_value=140, max_value=300, value=max(140, min(300, int(cfg.get("login_image_height") or 210)))', 'min_value=100, max_value=240, value=max(100, min(240, int(cfg.get("login_image_height") or 135)))')

# Authenticated screen: remove the duplicate MRP | SETTA title if present.
lines=[]
for line in s.splitlines():
    stripped=line.strip()
    if stripped.startswith('st.title(') and ('MRP | SETTA' in stripped or 'app_title' in stripped):
        continue
    if 'st.caption(UI_CONFIG["section_main_description"])' in line:
        indent=line[:len(line)-len(line.lstrip())]
        lines.append(indent+'st.markdown(f\'<div class="setta-main-description">{UI_CONFIG["section_main_description"]}</div>\', unsafe_allow_html=True)')
    else:
        lines.append(line)
s='\n'.join(lines)+'\n'

# Add compact spacing for the main description below the brand header.
if '.setta-main-description {' not in s:
    marker='      div.stButton > button[kind="primary"], div.stDownloadButton > button'
    css='      .setta-main-description { margin-top: -10px; margin-bottom: 12px; color: var(--setta-text); opacity: .78; font-size: .9rem; }\n'
    if marker in s:
        s=s.replace(marker, css+marker, 1)

p.write_text(s,encoding='utf-8')
# trigger visual refinement workflow
