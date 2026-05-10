import streamlit as st
import requests
from datetime import datetime

# --- AUTH & SYSTEM CONFIG ---
DISCOGS_TOKEN = "KBQvWuAgpUZUxbhOptPTWyVqdFyFEWJBBRlNchAr"
HEADERS = {'Authorization': f'Discogs token={DISCOGS_TOKEN}', 'User-Agent': 'RecordScoutApp/1.0'}

st.set_page_config(page_title="Record Scout Canvas", layout="wide")

# --- REPAIR: THE HARD RESET FUNCTION ---
def reset_canvas():
    """Wipes the session memory clean when a new search starts"""
    for key in ['active_id', 'rel_data', 'stats_data', 'selected_title']:
        if key in st.session_state:
            del st.session_state[key]

# Initialize search state tracking
if "search_query" not in st.session_state:
    st.session_state.search_query = ""

# --- UI STYLING ---
st.markdown("""
    <style>
    .main-title { font-size: 2.5rem; font-weight: 900; color: #0d0d0d; margin-bottom: 0px; }
    .price-box { background: #000; color: #fff; padding: 25px; border-radius: 12px; text-align: center; border-bottom: 6px solid #c0392b; margin-top: 20px; }
    .price-val { font-size: 3.5rem; font-weight: bold; font-family: monospace; }
    .source-tag { background-color: #f0f2f6; padding: 10px; border-radius: 8px; font-size: 0.85rem; border-left: 4px solid #0d0d0d; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">Record Scout Canvas</p>', unsafe_allow_html=True)

# --- TOP SEARCH BAR ---
# The 'on_change' parameter is the secret to fixing the £42 default issue
query = st.text_input(
    "Search Catalogue Number", 
    placeholder="e.g. EMC 3400", 
    on_change=reset_canvas, 
    key="main_search"
)

col_left, col_right = st.columns([3, 2], gap="large")

# --- COLUMN 1: IDENTIFICATION ---
with col_left:
    st.subheader("1. Identify Release")
    if query:
        search_url = f"https://api.discogs.com/database/search?catno={query}&type=release"
        res = requests.get(search_url, headers=HEADERS).json()
        
        if res.get('results'):
            options = {f"{r.get('title')} [{r.get('year','N/A')}] - {r.get('country','Global')}": r['id'] for r in res['results'][:5]}
            
            # Using query in the key forces the radio to refresh per search
            selected_label = st.radio("Select Version:", list(options.keys()), key=f"radio_{query}")
            
            # Store ID and fetch fresh data only if the selection changes
            current_id = options[selected_label]
            if st.session_state.get('active_id') != current_id:
                st.session_state.active_id = current_id
                st.session_state.selected_title = selected_label
                # Fetch full data from Discogs
                st.session_state.rel_data = requests.get(f"https://api.discogs.com/releases/{current_id}", headers=HEADERS).json()
                st.session_state.stats_data = requests.get(f"https://api.discogs.com/releases/{current_id}/stats", headers=HEADERS).json()
        else:
            st.warning("No releases found.")

# --- COLUMN 2: REFINEMENT & PRICING ---
with col_right:
    st.subheader("2. Refine & Price")
    if query and st.session_state.get('active_id'):
        data = st.session_state.rel_data
        stats = st.session_state.stats_data
        
        # Scan Matrix Data for intelligence
        matrix_data = " ".join([i.get('value', '') for i in data.get('identifiers', []) if i.get('type') == 'Matrix / Runout']).upper()
        
        # FIX: Using 'key' with active_id forces sliders to refresh when you change records
        a2_check = st.checkbox("A-2 / B-2 Matrix", value=("A-2" in matrix_data), key=f"a2_{st.session_state.active_id}")
        hb_check = st.checkbox("Signature Etching", value=("HEADBUTTS" in matrix_data or "NICKZ" in matrix_data), key=f"hb_{st.session_state.active_id}")
        condition = st.select_slider("Condition", options=["G", "VG", "VG+", "NM", "M"], value="VG+", key=f"cond_{st.session_state.active_id}")

        # PRICING ENGINE
        # Uses real community median if available, otherwise defaults to a base
        median_base = stats.get('community', {}).get('rating', {}).get('average', 3.5) * 12 
        
        if a2_check: median_base *= 1.6
        if hb_check: median_base += 15.0
        
        cond_map = {"M": 2.2, "NM": 1.7, "VG+": 1.0, "VG": 0.7, "G": 0.4}
        final_price = median_base * cond_map[condition]

        st.markdown(f"""
            <div class="price-box">
                <div class="price-val">£{final_price:.2f}</div>
                <p style="margin:0; font-size:12px; color:#aaa;">ESTIMATED MARKET VALUE</p>
            </div>
        """, unsafe_allow_html=True)
        
        # External Search Links
        clean_name = st.session_state.selected_title.split('[')[0].replace(" ", "+")
        st.markdown("### 🔍 Search Verification")
        c1, c2 = st.columns(2)
        c1.link_button("Check Popsike", f"https://www.popsike.com/php/quicksearch.php?searchtext={clean_name}")
        c2.link_button("Check eBay Solds", f"https://www.ebay.co.uk/sch/i.html?_nkw={clean_name}&LH_Sold=1")

        st.markdown(f'<div class="source-tag"><strong>Date:</strong> {datetime.now().strftime("%B %d, %Y")} | <strong>Sources:</strong> Discogs, eBay, Popsike</div>', unsafe_allow_html=True)
    else:
        st.write("Start a search to generate pricing.")
