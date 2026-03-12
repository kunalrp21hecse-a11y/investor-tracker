import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px

BASE_URL = "https://www.smallcase.com"
INVESTOR_INDEX = "https://www.smallcase.com/star-investors/"

headers = {
    "User-Agent": "Mozilla/5.0"
}

# ---------------------------------------
# FIND INVESTOR PAGE
# ---------------------------------------

def find_investor_page(investor_name):

    r = requests.get(INVESTOR_INDEX, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    links = soup.find_all("a")

    for link in links:

        text = link.text.strip().lower()

        if investor_name.lower() in text:
            return BASE_URL + link.get("href")

    return None


# ---------------------------------------
# SCRAPE PORTFOLIO
# ---------------------------------------

def scrape_portfolio(url, investor):

    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    rows = soup.select("table tbody tr")

    data = []

    for row in rows:

        cols = row.find_all("td")

        if len(cols) < 3:
            continue

        company = cols[0].text.strip()
        holding = cols[1].text.strip()
        allocation = cols[2].text.strip()

        data.append({
            "Investor": investor,
            "Company": company,
            "Holding %": holding,
            "Allocation %": allocation
        })

    return pd.DataFrame(data)


# ---------------------------------------
# STREAMLIT UI
# ---------------------------------------

st.set_page_config(page_title="Investor Portfolio Tracker", layout="wide")

st.title("📊 Super Investor Portfolio Dashboard")

investor_name = st.text_input(
    "Enter Investor Name",
    "Radhakishan Damani"
)

if st.button("Fetch Portfolio"):

    with st.spinner("Searching investor database..."):

        url = find_investor_page(investor_name)

    if not url:
        st.error("Investor not found.")
    else:

        st.success(f"Investor page found")

        df = scrape_portfolio(url, investor_name)

        if df.empty:
            st.error("No portfolio data detected")
        else:

            st.subheader("Portfolio Table")

            st.dataframe(df, use_container_width=True)

            # Clean numbers
            df["Allocation_clean"] = (
                df["Allocation %"]
                .str.replace("%","")
                .astype(float)
            )

            # PIE CHART
            st.subheader("Portfolio Allocation")

            fig = px.pie(
                df,
                names="Company",
                values="Allocation_clean",
                title="Portfolio Allocation"
            )

            st.plotly_chart(fig, use_container_width=True)

            # BAR CHART
            st.subheader("Holding Distribution")

            fig2 = px.bar(
                df,
                x="Company",
                y="Allocation_clean",
                title="Allocation by Company"
            )

            st.plotly_chart(fig2, use_container_width=True)

            # DOWNLOAD
            csv = df.to_csv(index=False).encode()

            st.download_button(
                "Download CSV",
                csv,
                "portfolio.csv",
                "text/csv"
            )
