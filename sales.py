import streamlit as st
import json
import os
import pandas as pd
import re

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Hardware Catalog", layout="wide", page_icon="🛍️")

# --- 2. CUSTOM CSS (COLORFUL DARK THEME) ---
st.markdown("""
<style>
    /* 1. BACKGROUND WITH BRAND COLORS */
    .stApp {
        background-color: #0e1117; /* Deep base color */
        /* Subtle Gradient Glows (Blue Top-Left, Pink Bottom-Right) */
        background-image: 
            radial-gradient(circle at 0% 0%, rgba(41, 182, 246, 0.15) 0%, transparent 50%), 
            radial-gradient(circle at 100% 100%, rgba(236, 64, 122, 0.15) 0%, transparent 50%);
        background-attachment: fixed;
        color: #e6edf3;
    }
    
    /* Global text color force */
    p, h1, h2, h3, h4, h5, h6, span, div, label, li, .stMarkdown {
        color: #e6edf3 !important;
    }

    /* 2. SEARCH BAR & INPUTS */
    div[data-testid="stTextInput"] input {
        background-color: #010409 !important; /* Pitch Black for contrast */
        border: 1px solid #30363d !important;
        color: #ffffff !important; /* Bright White */
        border-radius: 50px;
    }
    div[data-testid="stTextInput"] input::placeholder {
        color: #8b949e !important;
    }
    
    /* 3. DROPDOWN MENUS (Fixed Visibility) */
    .stSelectbox div[data-baseweb="select"] > div,
    .stMultiSelect div[data-baseweb="select"] > div {
        background-color: #010409 !important;
        border-color: #30363d !important;
        color: #ffffff !important;
    }
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
    }
    div[data-baseweb="option"], li[role="option"] {
        background-color: #161b22 !important;
        color: #e6edf3 !important;
    }
    li[role="option"]:hover, li[role="option"][aria-selected="true"] {
        background-color: #29B6F6 !important;
        color: #ffffff !important;
    }
    
    /* 4. PRODUCT CARDS (Glass Effect) */
    .product-card-container {
        background-color: rgba(22, 27, 34, 0.7); /* Semi-transparent dark */
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        height: 100%;
        min-height: 220px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: transform 0.2s, border-color 0.2s;
        backdrop-filter: blur(5px);
    }
    .product-card-container:hover {
        border-color: #29B6F6;
        transform: translateY(-5px);
        background-color: rgba(22, 27, 34, 0.9);
    }
    
    .card-brand { color: #8b949e !important; font-size: 0.85em; text-transform: uppercase; font-weight: bold; }
    .card-model { color: #ffffff !important; font-size: 1.3em; font-weight: bold; margin: 5px 0; }
    .sub-model { color: #8b949e !important; font-size: 0.9em; margin-bottom: 10px; }
    
    /* 5. TAGS & BADGES */
    .spec-tag {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 6px;
        background-color: rgba(255, 255, 255, 0.05);
        color: #c9d1d9 !important;
        font-size: 0.8em;
        margin-right: 6px;
        margin-bottom: 6px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .ram-ok { color: #3fb950 !important; border-color: #3fb950; } 
    .ram-warn { color: #d29922 !important; border-color: #d29922; }
    .ram-bad { color: #f85149 !important; border-color: #f85149; }
    .wwan-tag { color: #58a6ff !important; border-color: #58a6ff; }
    
    /* 6. HERO HEADER */
    .hero-container {
        text-align: center;
        padding: 40px 20px;
        background-color: rgba(22, 27, 34, 0.5);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 30px;
        border-radius: 0 0 20px 20px;
    }
    .hero-title {
        /* Gradient Text */
        background: linear-gradient(90deg, #29B6F6, #EC407A);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3em;
        font-weight: 800;
        margin-bottom: 10px;
    }
    
    /* 7. DETAIL VIEW HEADERS */
    .card-section-header {
        color: #29B6F6 !important;
        border-bottom: 1px solid #30363d;
        padding-bottom: 5px;
        margin-top: 20px;
        font-weight: bold;
        text-transform: uppercase;
        font-size: 0.9em;
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
             return "orange", "RAM: Partial"
        return "red", "RAM: Soldered"

    if "partial" in status_str: return "orange", "RAM: Partial"
    if "yes" in status_str or "soldered" in status_str: return "red", "RAM: Soldered"
    return "green", "RAM: Upgradable"

def get_ram_status_class(row):
    color, _ = get_ram_status_details(row)
    if color == "orange": return "ram-warn"
    if color == "red": return "ram-bad"
    return "ram-ok"

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
            <div style="color: #8b949e; font-size: 1.1em;">Internal Catalog & Specifications</div>
        </div>
    """, unsafe_allow_html=True)

    # 2. CENTRAL SEARCH BAR
    c1, c2, c3 = st.columns([1, 6, 1])
    with c2:
        search_query = st.text_input("🔍 Search Catalog", placeholder="Search by Model, CPU, Features...", label_visibility="collapsed")

    # 3. HORIZONTAL FILTERS
    st.write("")
    f_col1, f_col2, f_col3 = st.columns([1, 1, 1])
    
    with f_col1:
        all_brands = sorted(df['brand'].unique())
        sel_brand = st.multiselect("🏷️ Brand", all_brands, placeholder="Filter by Brand")
        
    with f_col2:
        all_types = sorted(df['type'].unique())
        sel_type = st.multiselect("💻 Type", all_types, placeholder="Filter by Type")

    with f_col3:
        sel_features = st.multiselect("✨ Features", ["WWAN (SIM)", "eSIM", "Upgradable RAM", "Dedicated GPU"], placeholder="Filter by Feature")

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
            cls, _ = get_ram_status_details(r)
            return cls != "red"
        filtered_df = filtered_df[filtered_df.apply(check_ram, axis=1)]

    # --- SORTING ---
    filtered_df = filtered_df.sort_values(by=['brand', 'model'])

    # 5. RESULTS GRID
    if filtered_df.empty:
        st.warning("😕 No results found matching your criteria.")
    else:
        st.caption(f"Models Found: {len(filtered_df)}")
        
        cols_per_row = 3
        rows = [filtered_df.iloc[i:i + cols_per_row] for i in range(0, len(filtered_df), cols_per_row)]

        for row_items in rows:
            cols = st.columns(cols_per_row)
            for idx, (index, item) in enumerate(row_items.iterrows()):
                with cols[idx]:
                    # --- RAM TEXT & COLOR LOGIC ---
                    _, ram_text = get_ram_status_details(item)
                    ram_cls = get_ram_status_class(item)
                    
                    cpu_preview = format_cpu_preview(item.get('cpu'))
                    
                    wwan_badge = ""
                    if item.get('has_wwan'):
                        wwan_badge = f'<span class="spec-tag wwan-tag">📡 4G/5G</span>'

                    # --- FIXED CARD HTML (NO INDENTATION) ---
                    card_html = (
                        f'<div class="product-card-container">'
                        f'<div>'
                        f'<div class="card-brand">{item["brand"]}</div>'
                        f'<div class="card-model">{item["model"]}</div>'
                        f'<div class="sub-model">{item.get("sub_model", "")}</div>'
                        f'</div>'
                        f'<div>'
                        f'<span class="spec-tag" title="{item.get("cpu")}">{cpu_preview}</span>'
                        f'<span class="spec-tag {ram_cls}">{ram_text}</span>'
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
#         DETAIL VIEW
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
        badges.append(f"<span class='spec-tag'>{icon_type} {row['type']}</span>")
        if row.get('has_wwan'): badges.append("<span class='spec-tag wwan-tag'>📡 WWAN Ready</span>")
        if row.get('has_esim'): badges.append("<span class='spec-tag ram-ok'>📲 eSIM</span>")
        
        ram_color, ram_text = get_ram_status_details(row)
        if ram_color == "red": badges.append(f"<span class='spec-tag ram-bad'>🔒 {ram_text}</span>")
        elif ram_color == "orange": badges.append(f"<span class='spec-tag ram-warn'>⚠️ {ram_text}</span>")
        else: badges.append(f"<span class='spec-tag ram-ok'>🛠️ {ram_text}</span>")

        storage_text = str(row.get('storage_slots', ''))
        if "Soldered" in storage_text or "eMMC" in storage_text: badges.append("<span class='spec-tag ram-bad'>🔒 Soldered Storage</span>")
        else: badges.append("<span class='spec-tag ram-ok'>💾 Upgradable Storage</span>")

        if "TPM" in str(row.get('security_tpm', '')): badges.append("<span class='spec-tag' style='border-color: #a371f7; color: #a371f7 !important;'>🛡️ TPM</span>")
        
        badges_html = "".join(badges)

        # HEADER
        st.markdown(f"""
        <div style="margin-bottom: 20px;">
            <h1 style="margin-bottom: 5px; color: white !important;">{row['brand']} {row['model']}</h1>
            <div style="color: #8b949e; margin-bottom: 15px; font-size: 1.1em;">{row.get('sub_model', '')}</div>
            <div>{badges_html}</div>
        </div>
        """, unsafe_allow_html=True)

        if row.get('support_os'): st.caption(f"💻 **OS Support:** {row.get('support_os')}")

        # DETAILS GRID
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="card-section-header" style="color: #29B6F6 !important;">🛠 HARDWARE</div>', unsafe_allow_html=True)
            st.markdown(f"**🧠 CPU:** {row.get('cpu')}")
            if row.get('gpu'): st.markdown(f"**🎮 GPU:** {row.get('gpu')}")
            st.markdown(f"**💾 RAM:** {row.get('ram_max')} ({row.get('ram_type')})")
            st.caption(f"Status: {ram_text} | Slots: {row.get('ram_slots')}")
            st.markdown(f"**💿 Storage:** {row.get('storage_slots')}")
            if row.get('security_tpm'): st.markdown(f"**🔒 Security:** {row.get('security_tpm')}")

        with col2:
            st.markdown('<div class="card-section-header" style="color: #29B6F6 !important;">🖥️ DISPLAY & BODY</div>', unsafe_allow_html=True)
            if row.get('screen_options'): st.markdown(f"**📺 Screen:** {row.get('screen_options')}")
            if row.get('webcam'): st.markdown(f"**📷 Cam:** {row.get('webcam')}")
            if row.get('biometrics'): st.markdown(f"**👆 Bio:** {row.get('biometrics')}")
            if row.get('weight'): st.markdown(f"**⚖️ Weight:** {row.get('weight')}")
            if row.get('ports'): 
                st.markdown("**🔌 Ports:**")
                st.markdown(format_ports_with_icons(row.get('ports')))

        with col3:
            st.markdown('<div class="card-section-header" style="color: #29B6F6 !important;">📡 CONNECTIVITY</div>', unsafe_allow_html=True)
            if row.get('wifi_bt'): st.markdown(f"**📶 WiFi:** {row.get('wifi_bt')}")
            wwan_check = f"**🌐 WWAN:** {'✅ Yes' if row.get('has_wwan') else '❌ No'}"
            if row.get('has_wwan'): wwan_check += " <span style='color:#d29922; font-size: 0.8em;'>⚠️ Check Antennas</span>"
            st.markdown(wwan_check, unsafe_allow_html=True)
            sim_check = f"**📇 SIM:** {row.get('sim_slot_type') if row.get('has_wwan') else 'N/A'}"
            if row.get('has_wwan'): sim_check += " <span style='color:#d29922; font-size: 0.8em;'>⚠️ Check Port</span>"
            st.markdown(sim_check, unsafe_allow_html=True)
            if row.get('has_wwan') and row.get('modem_pn'): st.code(f"Modem P/N: {row.get('modem_pn')}", language="text")
            st.markdown('<div class="card-section-header" style="color: #29B6F6 !important;">⚡ POWER</div>', unsafe_allow_html=True)
            st.markdown(f"**🔌 Adapter:** {row.get('power_watts')} ({row.get('power_connector')})")
            if row.get('power_pn'): st.code(f"P/N: {row.get('power_pn')}", language="text")
            st.markdown(f"**🔋 Battery:** {row.get('battery_info')}")

        if row.get('wwan_modules'):
            st.markdown("### 📋 WWAN Compatible Modules")
            # --- TABLE FILTERING LOGIC ---
            df_modules = pd.DataFrame(row['wwan_modules'])
            
            # Columns to KEEP
            desired_cols = ["module_name", "part_number", "esim_support", "tray_pn"]
            
            # Ensure columns exist before selecting
            final_cols = [c for c in desired_cols if c in df_modules.columns]
            
            st.dataframe(df_modules[final_cols], use_container_width=True, hide_index=True)

        if row.get('expert_notes'):
            st.markdown(f"""<div class="warning-box" style="background-color: #2d1b1b; padding: 10px; border-radius: 5px; color: #ffcccb !important;"><strong>⚠️ CONSULTANT NOTES:</strong><br>{row.get('expert_notes')}</div>""", unsafe_allow_html=True)

        if row.get('pdf_links'):
            st.write("")
            st.markdown("### 📄 Documentation")
            for link in row['pdf_links']: st.markdown(f"- {link}")

    else:
        st.error("Model not found in database.")
        if st.button("Back"):
            clear_model()
            st.rerun()