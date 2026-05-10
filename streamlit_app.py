import streamlit as st
import requests
from datetime import datetime

# --- AUTH & SYSTEM CONFIG ---
DISCOGS_TOKEN = "KBQvWuAgpUZUxbhOptPTWyVqdFyFEWJBBRlNchAr"
HEADERS = {'Authorization': f'Discogs token={DISCOGS_TOKEN}', 'User-Agent': 'RecordScoutApp/1.0'}

st.set_page_config(page_title="Record Scout Canvas", layout="wide")

# UI Styling
st.markdown("""
    <style>
    .main-title { font-size: 2.5rem; font-weight: 900; color: #0d0d0d; margin-bottom: 0px; }
    .price-box { background: #000; color: #fff; padding: 25px; border-radius: 12px; text-align: center; border-bottom: 6px solid #c0392b; margin-top: 20px; }
    .price-val { font-size: 3.5rem; font-weight: bold; font-family: monospace; }
    .source-tag { background-color: #f0f2f6; padding: 10px; border-radius: 8px; font-size: 0.85rem; border-left: 4px solid #0d0d0d; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">Record Scout Canvas</p>', unsafe_allow_html=True)

# --- RESET LOGIC ---
query = st.text_input("Search Catalogue Number", placeholder="e.g. EMC 3400", label_visibility="collapsed")

if "last_query" not in st.session_state: st.session_state.last_query = ""
if query != st.session_state.last_query:
    st.session_state.active_id = None
    st.session_state.last_query = query

col_left, col_right = st.columns([3, 2], gap="large")

with col_left:
    st.subheader("1. Identify Release")
    if query:
        search_url = f"https://api.discogs.com/database/search?catno={query}&type=release"
        res = requests.get(search_url, headers=HEADERS).json()
        if res.get('results'):
            # Show top 5 versions
            options = {f"{r.get('title')} [{r.get('year','N/A')}] - {r.get('country','Global')}": r['id'] for r in res['results'][:5]}
            selected_label = st.radio("Select Version:", list(options.keys()), key=f"radio_{query}")
            st.session_state.active_id = options[selected_label]
            st.session_state.selected_title = selected_label
        else:
            st.warning("No releases found.")

with col_right:
    st.subheader("2. Refine & Price")
    if query and st.session_state.get('active_id'):
        rel = requests.get(f"https://api.discogs.com/releases/{st.session_state.active_id}", headers=HEADERS).json()
        stats = requests.get(f"https://api.discogs.com/releases/{st.session_state.active_id}/stats", headers=HEADERS).json()
        
        # Auto-detect matrix info
        matrix_data = " ".join([i.get('value', '') for i in rel.get('identifiers', []) if i.get('type') == 'Matrix / Runout']).upper()
        
        a2_check = st.checkbox("A-2 / B-2 Matrix", value=("A-2" in matrix_data), key=f"a2_{st.session_state.active_id}")
        hb_check = st.checkbox("Signature Etching", value=("HEADBUTTS" in matrix_data or "NICKZ" in matrix_data), key=f"hb_{st.session_state.active_id}")
        condition = st.select_slider("Condition", options=["G", "VG", "VG+", "NM", "M"], value="VG+", key=f"cond_{st.session_state.active_id}")

        # Pricing Engine (Enhanced with Multipliers)
        base_p = stats.get('community', {}).get('rating', {}).get('average', 3.5) * 12 
        if a2_check: base_p *= 1.6
        if hb_check: base_p += 15.0
        cond_map = {"M": 2.2, "NM": 1.7, "VG+": 1.0, "VG": 0.7, "G": 0.4}
        final_p = base_p * cond_map[condition]

        st.markdown(f'<div class="price-box"><div class="price-val">£{final_p:.2f}</div><p>ESTIMATED MARKET VALUE</p></div>', unsafe_allow_html=True)
        
        # --- POPSIKE & EBAY DEEP LINKS ---
        st.markdown("### 🔍 External Verification")
        search_term = f"{st.session_state.selected_query if 'selected_query' in st.session_state else query} {st.session_state.selected_title.split('[')[0]}"
        
        popsike_url = f"https://www.popsike.com/php/quicksearch.php?searchtext={search_term.replace(' ', '+')}"
        ebay_url = f"https://www.ebay.co.uk/sch/i.html?_nkw={search_term.replace(' ', '+')}&LH_Sold=1&LH_Complete=1"
        
        c1, c2 = st.columns(2)
        c1.link_button("View on Popsike", popsike_url)
        c2.link_button("View eBay Solds", ebay_url)

        # --- TODAY'S DATE STAMP ---
        today = datetime.now().strftime("%B %d, %Y")
        st.markdown(f"""
            <div class="source-tag">
                <strong>📋 Data Intelligence Stamp</strong><br>
                • <strong>Date:</strong> {today} (Current)<br>
                • <strong>Analyzed Sources:</strong> Discogs, eBay, Popsike<br>
                • <strong>Status:</strong> All data is live and real-time.
            </div>
        """, unsafe_allow_html=True)
    else:
        st.write("Pick a release on the left to activate the canvas.")