import streamlit as st
import json
import os
import pandas as pd
import re

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Hardware Catalog", layout="wide", page_icon="🛍️")

# --- 2. CUSTOM CSS (BRANDED + DROPDOWN FIX) ---
st.markdown("""
<style>
    /* --- BRAND PALETTE --- 
       Blue:   #29B6F6
       Green:  #66BB6A
       Pink:   #EC407A
       Yellow: #FFA726
    */

    /* Global Settings */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    
    /* --- DROPDOWN MENU FIX --- */
    /* Force dropdown options to have a contrasting background */
    div[data-baseweb="popover"], div[data-baseweb="menu"] {
        background-color: #262730 !important; /* Dark grey background */
        border: 1px solid #444 !important;
    }
    
    /* Dropdown text color */
    div[data-baseweb="select"] ul li {
        color: #fff !important;
    }
    
    /* Hover effect in dropdown */
    div[data-baseweb="select"] ul li:hover {
        background-color: #29B6F6 !important; /* Brand Blue on hover */
        color: #fff !important;
    }
    
    /* Selected items tags in multiselect */
    .stMultiSelect span[data-baseweb="tag"] {
        background-color: rgba(41, 182, 246, 0.2) !important; /* Light Brand Blue */
        border: 1px solid #29B6F6 !important;
    }

    /* --- HERO SECTION --- */
    .hero-container {
        text-align: center;
        padding: 40px 20px 20px 20px;
        background: linear-gradient(180deg, #161b22 0%, #0e1117 100%);
        border-bottom: 1px solid #30363d;
        margin-bottom: 30px;
        border-radius: 0 0 20px 20px;
    }
    
    /* BRANDED GRADIENT TITLE */
    .hero-title {
        font-size: 3em;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #29B6F6, #EC407A);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }
    .hero-subtitle {
        color: #8b949e;
        font-size: 1.1em;
        margin-bottom: 30px;
    }

    /* SEARCH INPUT STYLE */
    div[data-testid="stTextInput"] input {
        border-radius: 50px;
        text-align: center;
        font-size: 1.2em;
        padding: 15px;
        border: 2px solid #30363d;
        background-color: #0d1117;
        transition: border-color 0.3s, box-shadow 0.3s;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #29B6F6; 
        box-shadow: 0 0 15px rgba(41, 182, 246, 0.3);
    }

    /* PRODUCT CARD */
    .product-card-container {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 15px;
        padding: 20px;
        height: 100%; 
        min-height: 220px; 
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
    }
    
    .product-card-container:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
        border-color: #EC407A; 
    }
    
    .card-brand { color: #8b949e; font-size: 0.8em; text-transform: uppercase; letter-spacing: 1px; }
    .card-model { color: #ffffff; font-size: 1.3em; font-weight: bold; margin: 5px 0; }
    
    /* TAGS */
    .spec-tag {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 12px;
        background-color: #21262d;
        color: #c9d1d9;
        font-size: 0.75em;
        margin-right: 5px;
        margin-bottom: 5px;
        border: 1px solid #30363d;
        white-space: nowrap; 
        font-weight: 600;
    }
    
    .ram-ok { color: #66BB6A; border-color: #66BB6A; background: rgba(102, 187, 106, 0.1); }
    .ram-warn { color: #FFA726; border-color: #FFA726; background: rgba(255, 167, 38, 0.1); }
    .ram-bad { color: #EC407A; border-color: #EC407A; background: rgba(236, 64, 122, 0.1); }
    .wwan-tag { color: #29B6F6; border-color: #29B6F6; background: rgba(41, 182, 246, 0.1); }

    /* DETAIL VIEW STYLES */
    .card-section-header {
        color: #29B6F6;
        font-size: 0.9em;
        text-transform: uppercase;
        margin-top: 15px;
        margin-bottom: 8px;
        border-bottom: 1px solid #333;
        padding-bottom: 2px;
        font-weight: bold;
    }
    
    h1, h2, h3 { color: #29B6F6 !important; }

    .tag {
        display: inline-flex;
        align-items: center;
        background-color: #262730;
        color: #ddd;
        padding: 4px 10px;
        border-radius: 15px;
        font-size: 0.85em;
        font-weight: 500;
        margin-right: 6px;
        margin-bottom: 6px;
        border: 1px solid #444;
    }
    .tag-icon { margin-right: 5px; }
    .tag-blue { border-color: #29B6F6; color: #29B6F6; background-color: rgba(41, 182, 246, 0.1); }
    .tag-green { border-color: #66BB6A; color: #66BB6A; background-color: rgba(102, 187, 106, 0.1); }
    .tag-red { border-color: #EC407A; color: #EC407A; background-color: rgba(236, 64, 122, 0.1); }
    .tag-orange { border-color: #FFA726; color: #FFA726; background-color: rgba(255, 167, 38, 0.1); }
    .tag-purple { border-color: #AB47BC; color: #AB47BC; background-color: rgba(171, 71, 188, 0.1); }

    .warning-box {
        background-color: #2d1b1b;
        border-left: 4px solid #EC407A;
        padding: 15px;
        margin-top: 20px;
        border-radius: 5px;
        font-size: 0.95em;
        color: #ffcccb;
    }
</style>
""", unsafe_allow_html=True)

DB_FILE = "hardware_db.json"

# --- 3. STATE MANAGEMENT ---
if 'selected_model_id' not in st.session_state:
    st.session_state.selected_model_id = None

def set_model(model_id):
    st.session_state.selected_model_id = model_id

def clear_model():
    st.session_state.selected_model_id = None

# --- 4. HELPERS ---
def get_ram_status_details(row):
    status_str = str(row.get('ram_soldered', '')).lower()
    slots_str = str(row.get('ram_slots', '')).lower()
    
    if "soldered" in slots_str or "no slots" in slots_str or slots_str.strip().startswith("0"):
        if "1 slot" in slots_str or "+" in slots_str or "partial" in status_str:
             return "orange", "🟠 Partial"
        return "red", "🔴 Soldered"

    if "partial" in status_str: return "orange", "🟠 Partial"
    if "yes" in status_str or "soldered" in status_str: return "red", "🔴 Soldered"
    return "green", "🟢 Upgradable"

def get_ram_status_class(row):
    color, _ = get_ram_status_details(row)
    if color == "orange": return "ram-warn", "Partial"
    if color == "red": return "ram-bad", "Soldered"
    return "ram-ok", "Upgradable"

def format_ports_with_icons(ports_text):
    if not ports_text: return ""
    icon_map = {
        "USB-C": "🔌", "Thunderbolt": "⚡", "HDMI": "🖥️", "DisplayPort": "📺",
        "RJ45": "🌐", "Ethernet": "🌐", "USB-A": "🖱️", "USB 3": "🖱️",
        "Headphone": "🎧", "Audio": "🎧", "SD Card": "💾", "Smart Card": "💳"
    }
    fmt = ports_text
    for k, i in icon_map.items():
        if k in fmt: fmt = fmt.replace(k, f"{i} {k}")
    return fmt

def format_cpu_preview(cpu_text):
    if not cpu_text: return "CPU: N/A"
    clean = re.sub(r'\(.*?\)', '', str(cpu_text))
    words = clean.split()
    short = " ".join(words[:4])
    return f"CPU: {short}..."

@st.cache_data
def load_data():
    if not os.path.exists(DB_FILE): return []
    with open(DB_FILE, "r", encoding="utf-8") as f:
        try: raw = json.load(f)
        except: return []
    
    flat = []
    for brand, models in raw.items():
        for m_name, specs in models.items():
            item = specs.copy()
            item['brand'] = brand
            item['model'] = m_name
            item['id'] = f"{brand}_{m_name}"
            item['search_blob'] = f"{brand} {m_name} {specs.get('cpu','')} {specs.get('gpu','')} {specs.get('type','')}".lower()
            flat.append(item)
    return flat

# --- 5. MAIN APP LOGIC ---

data = load_data()
if not data:
    st.error("⚠️ Database is empty. Please run hardware.py to add items.")
    st.stop()

df = pd.DataFrame(data)

# ==========================================================
#                   CENTRAL HERO & SEARCH
# ==========================================================

if st.session_state.selected_model_id is None:
    
    # 1. HERO BLOCK
    st.markdown("""
        <div class="hero-container">
            <div class="hero-title">IT HARDWARE HUB</div>
            <div class="hero-subtitle">Internal Catalog & Specifications</div>
        </div>
    """, unsafe_allow_html=True)

    # 2. CENTRAL SEARCH BAR
    c1, c2, c3 = st.columns([1, 6, 1])
    with c2:
        search_query = st.text_input("🔍 Search Catalog", placeholder="e.g. Dell 5420, i7, 32GB...", label_visibility="collapsed")

    # 3. HORIZONTAL FILTERS
    st.write("")
    f_col1, f_col2, f_col3 = st.columns([1, 1, 1])
    
    with f_col1:
        all_brands = sorted(df['brand'].unique())
        sel_brand = st.multiselect("🏷️ Brand", all_brands, placeholder="All Brands")
        
    with f_col2:
        all_types = sorted(df['type'].unique())
        sel_type = st.multiselect("💻 Device Type", all_types, placeholder="All Types")

    with f_col3:
        sel_features = st.multiselect("✨ Features", ["WWAN (SIM)", "eSIM", "Upgradable RAM", "Dedicated GPU"], placeholder="Any Feature")

    st.markdown("---")

    # 4. FILTERING LOGIC
    filtered_df = df.copy()

    if search_query:
        filtered_df = filtered_df[filtered_df['search_blob'].str.contains(search_query.lower())]
    if sel_brand:
        filtered_df = filtered_df[filtered_df['brand'].isin(sel_brand)]
    if sel_type:
        filtered_df = filtered_df[filtered_df['type'].isin(sel_type)]
    if "WWAN (SIM)" in sel_features:
        filtered_df = filtered_df[filtered_df['has_wwan'] == True]
    if "eSIM" in sel_features:
        filtered_df = filtered_df[filtered_df['has_esim'] == True]
    if "Dedicated GPU" in sel_features:
         gpu_kw = "NVIDIA|AMD|Radeon|RTX|Quadro|Discrete"
         filtered_df = filtered_df[filtered_df['gpu'].astype(str).str.contains(gpu_kw, case=False, na=False)]
    if "Upgradable RAM" in sel_features:
        def check_ram(r):
            cls, _ = get_ram_status_class(r)
            return cls != "ram-bad"
        filtered_df = filtered_df[filtered_df.apply(check_ram, axis=1)]

    # --- SORTING (Alphabetical) ---
    filtered_df = filtered_df.sort_values(by=['brand', 'model'])

    # 5. RESULTS GRID
    if filtered_df.empty:
        st.warning("😕 No results found.")
    else:
        st.caption(f"Models Found: {len(filtered_df)}")
        
        cols_per_row = 3
        rows = [filtered_df.iloc[i:i + cols_per_row] for i in range(0, len(filtered_df), cols_per_row)]

        for row_items in rows:
            cols = st.columns(cols_per_row)
            for idx, (index, item) in enumerate(row_items.iterrows()):
                with cols[idx]:
                    ram_cls, ram_txt = get_ram_status_class(item)
                    cpu_preview = format_cpu_preview(item.get('cpu'))
                    
                    wwan_badge = ""
                    if item.get('has_wwan'):
                        wwan_badge = f'<span class="spec-tag wwan-tag">📡 4G/5G</span>'

                    # CARD HTML
                    card_html = (
                        f'<div class="product-card-container">'
                        f'<div>'
                        f'<div class="card-brand">{item["brand"]}</div>'
                        f'<div class="card-model">{item["model"]}</div>'
                        f'<div style="font-size: 0.9em; color: #aaa; margin-bottom: 10px;">{item.get("sub_model", "")}</div>'
                        f'</div>'
                        f'<div>'
                        f'<span class="spec-tag" title="{item.get("cpu")}">{cpu_preview}</span>'
                        f'<span class="spec-tag {ram_cls}">RAM: {ram_txt}</span>'
                        f'{wwan_badge}'
                        f'</div>'
                        f'</div>'
                    )
                    
                    st.markdown(card_html, unsafe_allow_html=True)
                    
                    if st.button(f"View Details ➜", key=f"btn_{item['id']}", use_container_width=True):
                        set_model(item['id'])
                        st.rerun()
            st.write("")

# ==========================================================
#         DETAIL VIEW (BRANDED LAYOUT)
# ==========================================================
else:
    selected_row = df[df['id'] == st.session_state.selected_model_id]
    
    if not selected_row.empty:
        row = selected_row.iloc[0]
        
        if st.button("⬅️ Back to Search"):
            clear_model()
            st.rerun()

        # BADGES
        badges = []
        icon_type = "💻" if "Laptop" in row['type'] else "🖥️"
        badges.append(f"<span class='tag'><span class='tag-icon'>{icon_type}</span>{row['type']}</span>")
        if row.get('has_wwan'): badges.append("<span class='tag tag-blue'><span class='tag-icon'>📡</span>WWAN Ready</span>")
        if row.get('has_esim'): badges.append("<span class='tag tag-green'><span class='tag-icon'>📲</span>eSIM</span>")
        
        ram_color, ram_text = get_ram_status_details(row)
        if ram_color == "red": badges.append(f"<span class='tag tag-red'><span class='tag-icon'>🔒</span>{ram_text}</span>")
        elif ram_color == "orange": badges.append(f"<span class='tag tag-orange'><span class='tag-icon'>⚠️</span>{ram_text}</span>")
        else: badges.append(f"<span class='tag tag-green'><span class='tag-icon'>🛠️</span>{ram_text}</span>")

        storage_text = str(row.get('storage_slots', ''))
        if "Soldered" in storage_text or "eMMC" in storage_text: badges.append("<span class='tag tag-red'><span class='tag-icon'>🔒</span>Soldered Storage</span>")
        else: badges.append("<span class='tag tag-green'><span class='tag-icon'>💾</span>Upgradable Storage</span>")

        if "TPM" in str(row.get('security_tpm', '')): badges.append("<span class='tag tag-purple'><span class='tag-icon'>🛡️</span>TPM</span>")
        
        badges_html = "".join(badges)

        # HEADER
        st.markdown(f"""
        <div style="margin-bottom: 20px;">
            <h1 style="margin-bottom: 5px;">{row['brand']} {row['model']}</h1>
            <div style="color: #aaa; margin-bottom: 15px; font-size: 1.1em;">{row.get('sub_model', '')}</div>
            <div>{badges_html}</div>
        </div>
        """, unsafe_allow_html=True)

        if row.get('support_os'): st.caption(f"💻 **OS Support:** {row.get('support_os')}")

        # DETAILS GRID
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="card-section-header">🛠 HARDWARE</div>', unsafe_allow_html=True)
            st.markdown(f"**🧠 CPU:** {row.get('cpu')}")
            if row.get('gpu'): st.markdown(f"**🎮 GPU:** {row.get('gpu')}")
            st.markdown(f"**💾 RAM:** {row.get('ram_max')} ({row.get('ram_type')})")
            st.caption(f"Status: {ram_text} | Slots: {row.get('ram_slots')}")
            st.markdown(f"**💿 Storage:** {row.get('storage_slots')}")
            if row.get('security_tpm'): st.markdown(f"**🔒 Security:** {row.get('security_tpm')}")

        with col2:
            st.markdown('<div class="card-section-header">🖥️ DISPLAY & BODY</div>', unsafe_allow_html=True)
            if row.get('screen_options'): st.markdown(f"**📺 Screen:** {row.get('screen_options')}")
            if row.get('webcam'): st.markdown(f"**📷 Cam:** {row.get('webcam')}")
            if row.get('biometrics'): st.markdown(f"**👆 Bio:** {row.get('biometrics')}")
            if row.get('weight'): st.markdown(f"**⚖️ Weight:** {row.get('weight')}")
            if row.get('ports'): 
                st.markdown("**🔌 Ports:**")
                st.markdown(format_ports_with_icons(row.get('ports')))

        with col3:
            st.markdown('<div class="card-section-header">📡 CONNECTIVITY</div>', unsafe_allow_html=True)
            if row.get('wifi_bt'): st.markdown(f"**📶 WiFi:** {row.get('wifi_bt')}")
            wwan_check = f"**🌐 WWAN:** {'✅ Yes' if row.get('has_wwan') else '❌ No'}"
            if row.get('has_wwan'): wwan_check += " <span class='warn-text'>⚠️ Check Antennas</span>"
            st.markdown(wwan_check, unsafe_allow_html=True)
            sim_check = f"**📇 SIM:** {row.get('sim_slot_type') if row.get('has_wwan') else 'N/A'}"
            if row.get('has_wwan'): sim_check += " <span class='warn-text'>⚠️ Check Port</span>"
            st.markdown(sim_check, unsafe_allow_html=True)
            if row.get('has_wwan') and row.get('modem_pn'): st.code(f"Modem P/N: {row.get('modem_pn')}", language="text")
            st.markdown('<div class="card-section-header">⚡ POWER</div>', unsafe_allow_html=True)
            st.markdown(f"**🔌 Adapter:** {row.get('power_watts')} ({row.get('power_connector')})")
            if row.get('power_pn'): st.code(f"P/N: {row.get('power_pn')}", language="text")
            st.markdown(f"**🔋 Battery:** {row.get('battery_info')}")

        if row.get('wwan_modules'):
            st.markdown("### 📋 Compatible Modules")
            st.dataframe(pd.DataFrame(row['wwan_modules']), use_container_width=True, hide_index=True)

        if row.get('expert_notes'):
            st.markdown(f"""<div class="warning-box"><strong>⚠️ CONSULTANT NOTES:</strong><br>{row.get('expert_notes')}</div>""", unsafe_allow_html=True)

        if row.get('pdf_links'):
            st.write("")
            st.markdown("### 📄 Documentation")
            for link in row['pdf_links']: st.markdown(f"- {link}")

    else:
        st.error("Model not found in database.")
        if st.button("Back"):
            clear_model()
            st.rerun()