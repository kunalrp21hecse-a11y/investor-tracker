# ================================================================
# 📈 SUPERSTAR INVESTOR PORTFOLIO TRACKER
# ================================================================
# HOW IT WORKS:
# 1. You type any investor name (e.g. "Rakesh Jhunjhunwala")
# 2. This app searches Trendlyne for their portfolio
# 3. Scrapes the real holdings data
# 4. Displays it as a beautiful interactive dashboard
#
# TO RUN LOCALLY:
#   pip install -r requirements.txt
#   streamlit run app.py
#
# TO HOST FREE ONLINE:
#   1. Upload this file to GitHub
#   2. Go to share.streamlit.io
#   3. Connect your GitHub repo → Done! Live link instantly
# ================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from bs4 import BeautifulSoup
import time
import random
import re

# ── PAGE SETUP ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Investor Portfolio Tracker",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── BEAUTIFUL DARK STYLING ───────────────────────────────────────
st.markdown("""
<style>
/* Import a beautiful font */
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

/* Dark background everywhere */
html, body, [class*="css"], .stApp {
    background-color: #060a12 !important;
    color: #e8eaf0 !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* Main title styling */
.main-title {
    font-family: 'Syne', sans-serif;
    font-size: 3.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #00ff87, #60efff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0;
    line-height: 1.1;
}

.subtitle {
    color: #5a6478;
    font-size: 1.05rem;
    margin-top: 8px;
    font-family: 'DM Sans', sans-serif;
}

/* Search box */
.stTextInput > div > div > input {
    background: #0d1421 !important;
    border: 2px solid #1a2540 !important;
    border-radius: 14px !important;
    color: #e8eaf0 !important;
    font-size: 1.1rem !important;
    padding: 16px 20px !important;
    font-family: 'Syne', sans-serif !important;
    transition: border-color 0.3s;
}
.stTextInput > div > div > input:focus {
    border-color: #00ff87 !important;
    box-shadow: 0 0 0 3px rgba(0,255,135,0.15) !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #00ff87, #00d4ff) !important;
    color: #060a12 !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 14px 32px !important;
    font-family: 'Syne', sans-serif !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    width: 100%;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 30px rgba(0,255,135,0.4) !important;
}

/* Metric cards */
div[data-testid="metric-container"] {
    background: linear-gradient(145deg, #0d1421, #111827) !important;
    border: 1px solid #1e2d45 !important;
    border-radius: 16px !important;
    padding: 20px !important;
}
div[data-testid="metric-container"] label {
    color: #5a6478 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}
div[data-testid="metric-container"] div[data-testid="metric-value"] {
    color: #00ff87 !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
}

/* Section headers */
.section-header {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #00ff87;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    border-left: 3px solid #00ff87;
    padding-left: 12px;
    margin: 28px 0 16px;
}

/* Investor chips (saved list) */
.investor-chip {
    display: inline-block;
    background: #0d1421;
    border: 1px solid #1e2d45;
    border-radius: 20px;
    padding: 6px 16px;
    font-size: 0.85rem;
    color: #60efff;
    margin: 4px;
    cursor: pointer;
}

/* Warning box */
.stWarning {
    background: #1a1200 !important;
    border: 1px solid #f59e0b !important;
    border-radius: 10px !important;
}

/* Hide Streamlit watermark */
footer {visibility: hidden;}
#MainMenu {visibility: hidden;}

/* Dataframe */
.stDataFrame {
    border: 1px solid #1e2d45 !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}
</style>
""", unsafe_allow_html=True)


# ── SCRAPING FUNCTIONS ────────────────────────────────────────────

# A list of browser headers so websites don't block us
HEADERS_LIST = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9",
    }
]

def get_headers():
    """Pick a random browser header each time"""
    return random.choice(HEADERS_LIST)

def name_to_slug(name: str) -> str:
    """
    Convert investor name to URL format
    Example: "Rakesh Jhunjhunwala" → "rakesh-jhunjhunwala"
    """
    name = name.lower().strip()
    name = re.sub(r'[^a-z0-9\s]', '', name)   # remove special chars
    name = re.sub(r'\s+', '-', name)            # spaces → dashes
    return name

def fetch_trendlyne_portfolio(investor_name: str) -> pd.DataFrame:
    """
    Fetches real portfolio data from Trendlyne.
    Steps:
    1. Convert name to URL slug
    2. Try the direct portfolio page
    3. If that fails, search the superstar investors list
    4. Parse the HTML table
    5. Return as a clean DataFrame
    """
    slug = name_to_slug(investor_name)

    # ── STEP 1: Try direct URL ──────────────────────────────
    url = f"https://trendlyne.com/portfolio/superstar-shareholders/{slug}/"

    try:
        time.sleep(random.uniform(1.5, 3.0))  # Be polite, don't hammer the server
        response = requests.get(url, headers=get_headers(), timeout=15)

        if response.status_code == 200:
            df = parse_trendlyne_html(response.text, investor_name)
            if not df.empty:
                return df

    except requests.RequestException:
        pass  # If this fails, we'll try the search below

    # ── STEP 2: Search the superstar list ───────────────────
    search_url = "https://trendlyne.com/portfolio/superstar-shareholders/"
    try:
        time.sleep(random.uniform(1.5, 3.0))
        response = requests.get(search_url, headers=get_headers(), timeout=15)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Find all investor links
            keywords = investor_name.lower().split()
            for a_tag in soup.find_all('a', href=True):
                href = a_tag.get('href', '')
                link_text = a_tag.get_text(strip=True).lower()
                # Check if all words from the name appear in the link text
                if '/portfolio/superstar-shareholders/' in href and \
                   all(word in link_text for word in keywords):
                    full_url = f"https://trendlyne.com{href}" if href.startswith('/') else href
                    # Now fetch that investor's actual page
                    time.sleep(random.uniform(1.0, 2.0))
                    resp2 = requests.get(full_url, headers=get_headers(), timeout=15)
                    if resp2.status_code == 200:
                        df = parse_trendlyne_html(resp2.text, investor_name)
                        if not df.empty:
                            return df
    except requests.RequestException:
        pass

    return pd.DataFrame()  # Return empty if nothing found

def parse_trendlyne_html(html: str, investor_name: str) -> pd.DataFrame:
    """
    Parses the HTML from a Trendlyne portfolio page.
    Finds the holdings table and extracts all data from it.
    """
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')

    if not table:
        return pd.DataFrame()

    # Get column headers
    headers = [th.get_text(strip=True) for th in table.find_all('th')]
    if not headers:
        return pd.DataFrame()

    # Get all data rows
    rows = []
    tbody = table.find('tbody')
    if tbody:
        for tr in tbody.find_all('tr'):
            cells = [td.get_text(strip=True) for td in tr.find_all('td')]
            if cells:
                rows.append(cells)

    if not rows:
        return pd.DataFrame()

    # Build DataFrame - handle if row length doesn't match headers
    df = pd.DataFrame(rows, columns=headers[:len(rows[0])])
    df['Investor'] = investor_name
    return df

def fetch_screener_portfolio(investor_name: str) -> pd.DataFrame:
    """
    Fetches portfolio from Screener.in as a fallback.
    Screener has investor portfolio pages too.
    """
    slug = name_to_slug(investor_name)
    url = f"https://www.screener.in/investors/{slug}/"

    try:
        time.sleep(random.uniform(1.5, 2.5))
        response = requests.get(url, headers=get_headers(), timeout=15)

        if response.status_code == 200 and 'Page not found' not in response.text:
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table')

            if table:
                headers = [th.get_text(strip=True) for th in table.find_all('th')]
                rows = []
                for tr in table.find('tbody').find_all('tr'):
                    cells = [td.get_text(strip=True) for td in tr.find_all('td')]
                    if cells:
                        rows.append(cells)

                if rows and headers:
                    df = pd.DataFrame(rows, columns=headers[:len(rows[0])])
                    df['Investor'] = investor_name
                    df['Source'] = 'Screener.in'
                    return df

    except requests.RequestException:
        pass

    return pd.DataFrame()

def clean_portfolio_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans up the raw scraped data so it's nice and consistent.
    - Removes % signs from numbers
    - Converts values to proper numbers
    - Fills in missing values
    """
    if df.empty:
        return df

    # Rename columns to standard names if needed
    col_map = {}
    for col in df.columns:
        lower = col.lower()
        if 'company' in lower or 'name' in lower:
            col_map[col] = 'Company'
        elif 'sector' in lower or 'industry' in lower:
            col_map[col] = 'Sector'
        elif 'value' in lower:
            col_map[col] = 'Value (Cr)'
        elif 'holding' in lower or '%' in lower or 'stake' in lower:
            col_map[col] = 'Holding %'
        elif 'share' in lower or 'quantity' in lower:
            col_map[col] = 'Shares'

    df = df.rename(columns=col_map)

    # Clean numeric columns
    for col in ['Value (Cr)', 'Holding %', 'Shares']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '').str.replace('%', '').str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Fill missing sectors
    if 'Sector' in df.columns:
        df['Sector'] = df['Sector'].fillna('Unknown').replace('', 'Unknown')

    # Remove rows with no company name
    if 'Company' in df.columns:
        df = df[df['Company'].str.strip() != '']
        df = df.dropna(subset=['Company'])

    return df.reset_index(drop=True)


# ── CHART FUNCTIONS ───────────────────────────────────────────────

CHART_COLORS = [
    '#00ff87', '#60efff', '#f59e0b', '#ec4899', '#a78bfa',
    '#34d399', '#fb7185', '#38bdf8', '#fbbf24', '#4ade80'
]

def make_pie_chart(df: pd.DataFrame):
    """Creates a donut pie chart of sector allocation"""
    if 'Sector' not in df.columns:
        return None

    if 'Value (Cr)' in df.columns:
        sector_data = df.groupby('Sector')['Value (Cr)'].sum().reset_index()
        value_col = 'Value (Cr)'
    else:
        sector_data = df.groupby('Sector').size().reset_index(name='Count')
        value_col = 'Count'

    fig = px.pie(
        sector_data,
        names='Sector',
        values=value_col,
        hole=0.5,
        color_discrete_sequence=CHART_COLORS,
    )
    fig.update_layout(
        paper_bgcolor='#060a12',
        plot_bgcolor='#060a12',
        font=dict(family='DM Sans', color='#e8eaf0'),
        legend=dict(
            font=dict(color='#8892a4'),
            bgcolor='rgba(0,0,0,0)'
        ),
        margin=dict(t=20, b=20, l=20, r=20),
        showlegend=True
    )
    fig.update_traces(
        textfont_color='#060a12',
        textfont_size=13,
        marker=dict(line=dict(color='#060a12', width=2))
    )
    return fig

def make_bar_chart(df: pd.DataFrame):
    """Creates a horizontal bar chart of top holdings"""
    if 'Company' not in df.columns:
        return None

    value_col = 'Value (Cr)' if 'Value (Cr)' in df.columns else \
                'Holding %' if 'Holding %' in df.columns else None
    if not value_col:
        return None

    top = df.dropna(subset=[value_col]).nlargest(12, value_col)

    fig = px.bar(
        top,
        x=value_col,
        y='Company',
        orientation='h',
        color=value_col,
        color_continuous_scale=['#0d1421', '#00ff87'],
    )
    fig.update_layout(
        paper_bgcolor='#060a12',
        plot_bgcolor='#0d1421',
        font=dict(family='DM Sans', color='#e8eaf0'),
        yaxis=dict(autorange='reversed', gridcolor='#1e2d45'),
        xaxis=dict(gridcolor='#1e2d45'),
        coloraxis_showscale=False,
        margin=dict(t=10, b=20, l=10, r=20),
        height=400
    )
    return fig

def make_treemap(df: pd.DataFrame):
    """Creates a treemap showing sectors → companies"""
    if 'Company' not in df.columns or 'Sector' not in df.columns:
        return None

    value_col = 'Value (Cr)' if 'Value (Cr)' in df.columns else \
                'Holding %' if 'Holding %' in df.columns else None
    if not value_col:
        return None

    plot_df = df.dropna(subset=[value_col]).copy()
    plot_df[value_col] = plot_df[value_col].abs()

    fig = px.treemap(
        plot_df,
        path=['Sector', 'Company'],
        values=value_col,
        color=value_col,
        color_continuous_scale=['#0d1421', '#00ff87', '#60efff'],
    )
    fig.update_layout(
        paper_bgcolor='#060a12',
        font=dict(family='DM Sans', color='#e8eaf0'),
        margin=dict(t=10, b=10, l=10, r=10),
        height=420
    )
    return fig


# ── SESSION STATE (remembers things between clicks) ───────────────
# This is how Streamlit "remembers" what you searched before
if 'saved_investors' not in st.session_state:
    st.session_state.saved_investors = {}  # dict of {name: dataframe}

if 'current_investor' not in st.session_state:
    st.session_state.current_investor = None

if 'current_df' not in st.session_state:
    st.session_state.current_df = pd.DataFrame()


# ══════════════════════════════════════════════════════════════════
# MAIN UI STARTS HERE
# ══════════════════════════════════════════════════════════════════

# ── TOP HEADER ────────────────────────────────────────────────────
st.markdown('<div class="main-title">Portfolio Tracker</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Type any superstar investor\'s name → get their real portfolio instantly</div>',
    unsafe_allow_html=True
)
st.markdown("<br>", unsafe_allow_html=True)

# ── SEARCH BAR ────────────────────────────────────────────────────
col_input, col_btn = st.columns([4, 1])

with col_input:
    investor_name = st.text_input(
        label="",
        placeholder="e.g. Rakesh Jhunjhunwala, Ashish Kacholia, Dolly Khanna...",
        key="search_input",
        label_visibility="collapsed"
    )

with col_btn:
    search_clicked = st.button("🔍 Fetch Portfolio", key="search_btn")

# Show some popular names as suggestions
st.markdown("""
<div style="color:#3d4f6b; font-size:0.85rem; margin-top:8px;">
💡 Try: <span style="color:#60efff">Rakesh Jhunjhunwala</span> &nbsp;·&nbsp;
<span style="color:#60efff">Ashish Kacholia</span> &nbsp;·&nbsp;
<span style="color:#60efff">Dolly Khanna</span> &nbsp;·&nbsp;
<span style="color:#60efff">Vijay Kedia</span> &nbsp;·&nbsp;
<span style="color:#60efff">Porinju Veliyath</span>
</div>
""", unsafe_allow_html=True)

# ── PREVIOUSLY SAVED INVESTORS ────────────────────────────────────
if st.session_state.saved_investors:
    st.markdown('<div class="section-header">📌 Saved Investors</div>', unsafe_allow_html=True)
    saved_cols = st.columns(min(len(st.session_state.saved_investors), 5))
    for i, saved_name in enumerate(list(st.session_state.saved_investors.keys())):
        with saved_cols[i % 5]:
            if st.button(f"📊 {saved_name}", key=f"saved_{saved_name}"):
                st.session_state.current_investor = saved_name
                st.session_state.current_df = st.session_state.saved_investors[saved_name]

# ── FETCHING LOGIC ────────────────────────────────────────────────
if search_clicked and investor_name.strip():
    with st.spinner(f"🔍 Searching for {investor_name}'s portfolio on Trendlyne..."):

        # Try Trendlyne first
        df = fetch_trendlyne_portfolio(investor_name.strip())

        if df.empty:
            st.info("Trendlyne didn't have it — trying Screener.in...")
            df = fetch_screener_portfolio(investor_name.strip())

        if not df.empty:
            # Clean up the data
            df = clean_portfolio_data(df)
            # Save to session state
            st.session_state.current_investor = investor_name.strip()
            st.session_state.current_df = df
            # Save to the "saved investors" list
            st.session_state.saved_investors[investor_name.strip()] = df
            st.success(f"✅ Found {len(df)} holdings for {investor_name}!")
        else:
            st.error(
                f"❌ Could not find portfolio for **{investor_name}**. "
                "Try a slightly different spelling, or check if they're listed on Trendlyne."
            )

# ── DASHBOARD DISPLAY ─────────────────────────────────────────────
df = st.session_state.current_df
investor_display = st.session_state.current_investor

if not df.empty and investor_display:
    st.markdown("---")

    # ── INVESTOR NAME BANNER ────────────────────────────────────
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #0d1421, #111827);
        border: 1px solid #1e2d45;
        border-radius: 16px;
        padding: 20px 28px;
        margin-bottom: 24px;
    ">
        <div style="font-family: 'Syne', sans-serif; font-size: 1.8rem; font-weight: 800;
                    color: #ffffff;">{investor_display}</div>
        <div style="color: #5a6478; margin-top: 4px; font-size:0.9rem;">
            📊 Portfolio Dashboard · Data from Trendlyne / Screener.in
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI CARDS ───────────────────────────────────────────────
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.metric("Total Holdings", f"{len(df)}")

    with kpi2:
        if 'Value (Cr)' in df.columns:
            total = df['Value (Cr)'].sum()
            st.metric("Portfolio Value", f"₹{total:,.1f} Cr")
        else:
            st.metric("Companies", f"{df['Company'].nunique() if 'Company' in df.columns else 'N/A'}")

    with kpi3:
        if 'Sector' in df.columns:
            st.metric("Sectors", f"{df['Sector'].nunique()}")
        else:
            st.metric("Sectors", "N/A")

    with kpi4:
        if 'Sector' in df.columns:
            top_sector = df['Sector'].value_counts().idxmax()
            st.metric("Top Sector", top_sector)
        else:
            st.metric("Top Sector", "N/A")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── CHARTS ROW 1: PIE + BAR ──────────────────────────────────
    if 'Sector' in df.columns or 'Company' in df.columns:
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.markdown('<div class="section-header">Sector Allocation</div>', unsafe_allow_html=True)
            pie_fig = make_pie_chart(df)
            if pie_fig:
                st.plotly_chart(pie_fig, use_container_width=True)
            else:
                st.info("Not enough data for sector chart")

        with chart_col2:
            st.markdown('<div class="section-header">Top Holdings</div>', unsafe_allow_html=True)
            bar_fig = make_bar_chart(df)
            if bar_fig:
                st.plotly_chart(bar_fig, use_container_width=True)
            else:
                st.info("Not enough data for top holdings chart")

    # ── TREEMAP ──────────────────────────────────────────────────
    if 'Sector' in df.columns and 'Company' in df.columns:
        st.markdown('<div class="section-header">Portfolio Treemap</div>', unsafe_allow_html=True)
        treemap_fig = make_treemap(df)
        if treemap_fig:
            st.plotly_chart(treemap_fig, use_container_width=True)

    # ── FULL TABLE ───────────────────────────────────────────────
    st.markdown('<div class="section-header">Full Holdings Table</div>', unsafe_allow_html=True)

    # Filter options
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        search_company = st.text_input("🔎 Filter by company", placeholder="Search company name...")
    with filter_col2:
        if 'Sector' in df.columns:
            sectors = ['All Sectors'] + sorted(df['Sector'].dropna().unique().tolist())
            sector_filter = st.selectbox("Filter by sector", sectors)
        else:
            sector_filter = 'All Sectors'

    # Apply filters
    display_df = df.copy()
    if search_company:
        if 'Company' in display_df.columns:
            display_df = display_df[
                display_df['Company'].str.contains(search_company, case=False, na=False)
            ]
    if sector_filter != 'All Sectors' and 'Sector' in display_df.columns:
        display_df = display_df[display_df['Sector'] == sector_filter]

    st.dataframe(display_df, use_container_width=True, height=400)

    # ── DOWNLOAD BUTTON ──────────────────────────────────────────
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Download as CSV",
        data=csv_data,
        file_name=f"{investor_display.replace(' ', '_')}_portfolio.csv",
        mime="text/csv"
    )

    # ── COMPARE WITH ANOTHER INVESTOR ───────────────────────────
    if len(st.session_state.saved_investors) > 1:
        st.markdown("---")
        st.markdown('<div class="section-header">Compare Investors</div>', unsafe_allow_html=True)

        compare_options = [n for n in st.session_state.saved_investors.keys()
                          if n != investor_display]
        if compare_options:
            compare_name = st.selectbox("Compare with:", compare_options)
            compare_df = st.session_state.saved_investors.get(compare_name, pd.DataFrame())

            if not compare_df.empty and 'Company' in df.columns and 'Company' in compare_df.columns:
                inv1_companies = set(df['Company'].str.lower())
                inv2_companies = set(compare_df['Company'].str.lower())
                common = inv1_companies & inv2_companies

                col_a, col_b, col_c = st.columns(3)
                col_a.metric(f"{investor_display} only", len(inv1_companies - inv2_companies))
                col_b.metric("Both hold", len(common))
                col_c.metric(f"{compare_name} only", len(inv2_companies - inv1_companies))

                if common:
                    st.markdown(f"**Stocks both investors hold:** {', '.join(list(common)[:10])}")

# ── EMPTY STATE (first load) ──────────────────────────────────────
elif not df.empty is False and not investor_display:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center; padding: 60px 20px; color:#3d4f6b;">
        <div style="font-size:4rem; margin-bottom:16px;">📈</div>
        <div style="font-family:'Syne',sans-serif; font-size:1.5rem;
                    color:#5a6478; font-weight:700;">
            Search any investor to get started
        </div>
        <div style="margin-top:10px; font-size:0.95rem;">
            Real portfolio data · Interactive charts · Compare investors
        </div>
    </div>
    """, unsafe_allow_html=True)
