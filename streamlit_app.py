import streamlit as st
import requests

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
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">Record Scout Canvas</p>', unsafe_allow_html=True)
st.write("Live Market Intelligence Generator")

query = st.text_input("Search Catalogue Number", placeholder="e.g. EMC 3400", label_visibility="collapsed")

col_left, col_right = st.columns([3, 2], gap="large")

with col_left:
    st.subheader("1. Identify Release")
    if query:
        search_url = f"https://api.discogs.com/database/search?catno={query}&type=release"
        res = requests.get(search_url, headers=HEADERS).json()
        if res.get('results'):
            options = {f"{r.get('title')} [{r.get('year','N/A')}] - {r.get('country','Global')}": r['id'] for r in res['results'][:8]}
            selected_label = st.radio("Select Version:", list(options.keys()))
            st.session_state.active_id = options[selected_label]
        else:
            st.warning("No releases found.")

with col_right:
    st.subheader("2. Refine & Price")
    if 'active_id' in st.session_state:
        rel = requests.get(f"https://api.discogs.com/releases/{st.session_state.active_id}", headers=HEADERS).json()
        stats = requests.get(f"https://api.discogs.com/releases/{st.session_state.active_id}/stats", headers=HEADERS).json()
        
        # Auto-detect matrix
        matrix_data = " ".join([i.get('value', '') for i in rel.get('identifiers', []) if i.get('type') == 'Matrix / Runout']).upper()
        
        a2_check = st.checkbox("A-2 / B-2 Matrix", value=("A-2" in matrix_data))
        hb_check = st.checkbox("Signature Etching", value=("HEADBUTTS" in matrix_data or "NICKZ" in matrix_data))
        inner_check = st.checkbox("Original Inner Sleeve", value=True)
        condition = st.select_slider("Condition", options=["G", "VG", "VG+", "NM", "M"], value="VG+")

        # Pricing Engine
        base_p = stats.get('community', {}).get('rating', {}).get('average', 3.5) * 12 
        if a2_check: base_p *= 1.6
        if hb_check: base_p += 15.0
        cond_map = {"M": 2.2, "NM": 1.7, "VG+": 1.0, "VG": 0.7, "G": 0.4}
        final_p = base_p * cond_map[condition]

        st.markdown(f'<div class="price-box"><div class="price-val">£{final_p:.2f}</div><p>ESTIMATED MARKET VALUE</p></div>', unsafe_allow_html=True)
    else:
        st.write("Pick a release to see pricing.")