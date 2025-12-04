import streamlit as st
import json
import os
import pandas as pd

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Hardware Sales Catalog", layout="wide", page_icon="🛍️")

# --- CUSTOM CSS (DARK TECH THEME) ---
st.markdown("""
<style>
    /* Global Background & Text */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    
    /* SEARCH RESULT CARD (Grid Item) */
    .result-card {
        background-color: #1e1e1e;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 15px;
        height: 100%;
        transition: transform 0.2s;
        cursor: pointer;
    }
    .result-card:hover {
        border-color: #00e5ff;
        background-color: #262730;
        transform: translateY(-5px);
    }
    .result-title {
        font-size: 1.1em;
        font-weight: bold;
        color: #fff;
        margin-bottom: 5px;
    }
    .result-sub {
        font-size: 0.9em;
        color: #aaa;
        margin-bottom: 10px;
    }

    /* Full Model Card Container */
    .model-card-full {
        background-color: #1e1e1e;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    /* Header Styling */
    h1, h2, h3 {
        color: #00e5ff !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Badges/Tags */
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
    
    /* Special Status Tags */
    .tag-blue { border-color: #00e5ff; color: #00e5ff; background-color: rgba(0, 229, 255, 0.1); }
    .tag-green { border-color: #00ff00; color: #00ff00; background-color: rgba(0, 255, 0, 0.1); }
    .tag-red { border-color: #ff4b4b; color: #ff4b4b; background-color: rgba(255, 75, 75, 0.1); }
    .tag-orange { border-color: #e67e22; color: #e67e22; background-color: rgba(230, 126, 34, 0.1); }
    .tag-purple { border-color: #9b59b6; color: #9b59b6; background-color: rgba(155, 89, 182, 0.1); }
    
    /* Section Headers inside Card */
    .card-section-header {
        color: #888;
        font-size: 0.8em;
        text-transform: uppercase;
        margin-top: 15px;
        margin-bottom: 8px;
        border-bottom: 1px solid #333;
        padding-bottom: 2px;
        font-weight: bold;
    }

    /* Warning Box */
    .warning-box {
        background-color: #2d1b1b;
        border-left: 4px solid #ff4b4b;
        padding: 15px;
        margin-top: 20px;
        border-radius: 5px;
        font-size: 0.95em;
        color: #ffcccb;
    }
    
    /* PDF Links */
    .pdf-link a {
        color: #00e5ff;
        text-decoration: none;
        font-weight: bold;
    }
    .pdf-link a:hover { text-decoration: underline; }

    /* Warning Text Small */
    .warn-text {
        font-size: 0.8em;
        color: #ffcc00;
        font-style: italic;
        margin-left: 5px;
    }
</style>
""", unsafe_allow_html=True)

DB_FILE = "hardware_db.json"

# --- STATE MANAGEMENT ---
# We use this to track which model is currently "Open"
if 'selected_model_id' not in st.session_state:
    st.session_state.selected_model_id = None

def set_model(model_id):
    st.session_state.selected_model_id = model_id

def clear_model():
    st.session_state.selected_model_id = None

# --- HELPER: LOGIC FOR RAM STATUS ---
def get_ram_status(row):
    status_str = str(row.get('ram_soldered', '')).lower()
    slots_str = str(row.get('ram_slots', '')).lower()
    
    if "soldered" in slots_str or "no slots" in slots_str or slots_str.strip().startswith("0"):
        if "1 slot" in slots_str or "+" in slots_str or "partial" in status_str:
             return "orange", "🟠 Partial"
        return "red", "🔴 Soldered"

    if "partial" in status_str:
        return "orange", "🟠 Partial"
    
    if "yes" in status_str or "soldered" in status_str:
        return "red", "🔴 Soldered"
        
    return "green", "🟢 Upgradable"

# --- HELPER: PORT ICONS ---
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

# --- DATA LOADER ---
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
            item['display_name'] = f"{brand} {m_name}" 
            # Unique ID for state logic
            item['id'] = f"{brand}_{m_name}"
            item['search_blob'] = f"{brand} {m_name} {specs.get('cpu','')} {specs.get('gpu','')} {specs.get('power_pn','')} {specs.get('modem_pn','')} {specs.get('type','')}".lower()
            flat.append(item)
    return flat

# --- MAIN APP ---
st.title("🛍️ Hardware Sales Catalog")

data = load_data()
if not data:
    st.info("👋 Database is empty. Add models via hardware.py")
    st.stop()

df = pd.DataFrame(data)

# === SIDEBAR (FILTERS) ===
st.sidebar.header("🔍 Filter Catalog")

# 1. Search
search_text = st.sidebar.text_input("🔎 Search (Text)", placeholder="e.g. 7420, RTX...")

# 2. Filters
all_brands = sorted(list(set(df['brand'])))
sel_brands = st.sidebar.multiselect("Manufacturer", all_brands)

all_types = sorted(list(set(df['type'])))
sel_types = st.sidebar.multiselect("Device Type", all_types)

st.sidebar.divider()

# 3. Toggles
feature_options = ["WWAN (LTE/5G)", "eSIM Support", "Dedicated GPU", "Upgradable RAM"]
sel_features = st.sidebar.multiselect("Must Have Features", feature_options)

st.sidebar.divider()

# --- REFRESH ---
if st.sidebar.button("🔄 Force Refresh DB"):
    st.cache_data.clear()
    st.rerun()

# === FILTERING LOGIC ===
filtered_df = df.copy()

if sel_brands: filtered_df = filtered_df[filtered_df['brand'].isin(sel_brands)]
if sel_types: filtered_df = filtered_df[filtered_df['type'].isin(sel_types)]

if "WWAN (LTE/5G)" in sel_features:
    filtered_df = filtered_df[filtered_df['has_wwan'] == True]
if "eSIM Support" in sel_features:
    filtered_df = filtered_df[filtered_df['has_esim'] == True]
if "Dedicated GPU" in sel_features:
    gpu_kw = "NVIDIA|AMD|Radeon|RTX|Quadro|Discrete|Dedicated"
    filtered_df = filtered_df[filtered_df['gpu'].astype(str).str.contains(gpu_kw, case=False, na=False)]
if "Upgradable RAM" in sel_features:
    def is_upgradable_check(row):
        color, _ = get_ram_status(row)
        return color != "red"
    mask = filtered_df.apply(is_upgradable_check, axis=1)
    filtered_df = filtered_df[mask]

if search_text:
    filtered_df = filtered_df[filtered_df['search_blob'].str.contains(search_text.lower())]


# ========================================================
#                MAIN CONTENT LOGIC
# ========================================================

# If a model is selected, show DETAILS VIEW
if st.session_state.selected_model_id:
    # Find the model data
    selected_row = df[df['id'] == st.session_state.selected_model_id]
    
    if not selected_row.empty:
        row = selected_row.iloc[0]
        
        # --- BACK BUTTON ---
        if st.button("🔙 Back to Search Results"):
            clear_model()
            st.rerun()

        # --- RENDER SINGLE MODEL VIEW (From previous code) ---
        
        # BADGES
        badges = []
        icon_type = "💻" if "Laptop" in row['type'] else "🖥️"
        badges.append(f"<span class='tag'><span class='tag-icon'>{icon_type}</span>{row['type']}</span>")
        if row.get('has_wwan'): badges.append("<span class='tag tag-blue'><span class='tag-icon'>📡</span>WWAN Ready</span>")
        if row.get('has_esim'): badges.append("<span class='tag tag-green'><span class='tag-icon'>📲</span>eSIM</span>")
        
        ram_color, ram_text = get_ram_status(row)
        if ram_color == "red": badges.append(f"<span class='tag tag-red'><span class='tag-icon'>🔒</span>{ram_text}</span>")
        elif ram_color == "orange": badges.append(f"<span class='tag tag-orange'><span class='tag-icon'>⚠️</span>{ram_text}</span>")
        else: badges.append(f"<span class='tag tag-green'><span class='tag-icon'>🛠️</span>{ram_text}</span>")

        storage_text = str(row.get('storage_slots', ''))
        if "Soldered" in storage_text or "eMMC" in storage_text: badges.append("<span class='tag tag-red'><span class='tag-icon'>🔒</span>Soldered Storage</span>")
        else: badges.append("<span class='tag tag-green'><span class='tag-icon'>💾</span>Upgradable Storage</span>")

        if "TPM" in str(row.get('security_tpm', '')): badges.append("<span class='tag tag-purple'><span class='tag-icon'>🛡️</span>TPM</span>")
        
        badges_html = "".join(badges)

        # HERO
        st.markdown(f"""
        <div class="hero-card">
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

# ========================================================
# ELSE: SHOW SEARCH RESULTS GRID (Default View)
# ========================================================
else:
    st.subheader(f"🔎 Found {len(filtered_df)} models matching your criteria")
    
    if filtered_df.empty:
        st.warning("No models match the current filters.")
    else:
        # Display as a grid using columns
        cols_per_row = 2 # You can change this to 3 for smaller cards
        
        # Iterate through rows and create grid
        for i in range(0, len(filtered_df), cols_per_row):
            cols = st.columns(cols_per_row)
            # Loop for each column in the row
            for j in range(cols_per_row):
                if i + j < len(filtered_df):
                    row = filtered_df.iloc[i + j]
                    with cols[j]:
                        # Create a "mini card" visual
                        with st.container(border=True):
                            st.markdown(f"<div style='font-size: 1.2em; font-weight: bold; color: #00e5ff;'>{row['brand']} {row['model']}</div>", unsafe_allow_html=True)
                            st.caption(row.get('sub_model', ''))
                            
                            # Mini Badges
                            mini_badges = []
                            if row.get('has_wwan'): mini_badges.append("📡 WWAN")
                            if row.get('has_esim'): mini_badges.append("📲 eSIM")
                            if "NVIDIA" in str(row.get('gpu', '')) or "Discrete" in str(row.get('gpu', '')): mini_badges.append("🎮 GPU")
                            
                            # RAM Status color
                            r_color, _ = get_ram_status(row)
                            ram_dot = "🟢" if r_color == "green" else ("🟠" if r_color == "orange" else "🔴")
                            
                            st.markdown(f"**CPU:** {row.get('cpu')}")
                            st.markdown(f"**RAM:** {ram_dot} Max {row.get('ram_max')}")
                            
                            if mini_badges:
                                st.caption(" | ".join(mini_badges))
                            
                            # The Button is the "Link"
                            if st.button(f"👉 View Details", key=f"btn_{row['id']}"):
                                set_model(row['id'])
                                st.rerun()