import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
import time

# -----------------------------------------
# CONFIG
# -----------------------------------------

HEADERS = {"User-Agent": "Mozilla/5.0"}

FINOLOGY_URL = "https://ticker.finology.in/investor"
STOCKEDGE_URL = "https://web.stockedge.com/top-investor-portfolios"
TRENDLYNE_URL = "https://trendlyne.com/portfolio/superstar-shareholders/index/individual/"

# -----------------------------------------
# SCRAPER FUNCTIONS
# -----------------------------------------

def scrape_finology(investor):
    results = []
    
    try:
        r = requests.get(FINOLOGY_URL, headers=HEADERS)
        soup = BeautifulSoup(r.text,"html.parser")

        links = soup.find_all("a")

        investor_url = None

        for link in links:
            if investor.lower() in link.text.lower():
                investor_url = "https://ticker.finology.in" + link["href"]
                break

        if not investor_url:
            return results

        page = requests.get(investor_url, headers=HEADERS)
        soup = BeautifulSoup(page.text,"html.parser")

        rows = soup.select("table tbody tr")

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 4:
                continue

            results.append({
                "Source":"Finology",
                "Investor":investor,
                "Company":cols[0].text.strip(),
                "Holding":cols[1].text.strip(),
                "Shares":cols[2].text.strip(),
                "Value":cols[3].text.strip()
            })

    except:
        pass

    return results


def scrape_stockedge(investor):
    results = []

    try:
        r = requests.get(STOCKEDGE_URL, headers=HEADERS)
        soup = BeautifulSoup(r.text,"html.parser")

        links = soup.find_all("a")

        investor_url = None

        for link in links:
            if investor.lower() in link.text.lower():
                investor_url = "https://web.stockedge.com" + link["href"]
                break

        if not investor_url:
            return results

        page = requests.get(investor_url, headers=HEADERS)
        soup = BeautifulSoup(page.text,"html.parser")

        rows = soup.select("table tbody tr")

        for row in rows:
            cols = row.find_all("td")

            if len(cols) < 4:
                continue

            results.append({
                "Source":"StockEdge",
                "Investor":investor,
                "Company":cols[0].text.strip(),
                "Holding":cols[1].text.strip(),
                "Shares":cols[2].text.strip(),
                "Value":cols[3].text.strip()
            })

    except:
        pass

    return results


def scrape_trendlyne(investor):
    results = []

    try:
        r = requests.get(TRENDLYNE_URL, headers=HEADERS)
        soup = BeautifulSoup(r.text,"html.parser")

        links = soup.find_all("a")

        investor_url = None

        for link in links:
            if investor.lower() in link.text.lower():
                investor_url = "https://trendlyne.com" + link["href"]
                break

        if not investor_url:
            return results

        page = requests.get(investor_url, headers=HEADERS)
        soup = BeautifulSoup(page.text,"html.parser")

        tables = soup.find_all("table")

        for table in tables:

            rows = table.select("tbody tr")

            for row in rows:

                cols = row.find_all("td")

                if len(cols) < 4:
                    continue

                results.append({
                    "Source":"Trendlyne",
                    "Investor":investor,
                    "Company":cols[0].text.strip(),
                    "Holding":cols[1].text.strip(),
                    "Shares":cols[2].text.strip(),
                    "Value":cols[3].text.strip()
                })

    except:
        pass

    return results


def scrape_all_sources(investor):

    data = []

    data.extend(scrape_finology(investor))
    time.sleep(1)

    data.extend(scrape_stockedge(investor))
    time.sleep(1)

    data.extend(scrape_trendlyne(investor))

    return pd.DataFrame(data)

# -----------------------------------------
# STREAMLIT UI
# -----------------------------------------

st.set_page_config(page_title="Investor Portfolio Dashboard", layout="wide")

st.title("📊 Super Investor Portfolio Tracker")

investor_name = st.text_input("Enter Investor Name", "Radhakishan Damani")

if st.button("Fetch Portfolio"):

    with st.spinner("Scraping investor portfolio..."):

        df = scrape_all_sources(investor_name)

    if df.empty:
        st.error("No data found for this investor.")
    else:

        st.success("Portfolio Data Loaded")

        st.dataframe(df, use_container_width=True)

        # -----------------------------------------
        # CLEAN VALUE COLUMN
        # -----------------------------------------

        df_chart = df.copy()

        df_chart["Value_clean"] = (
            df_chart["Value"]
            .str.replace("Cr","")
            .str.replace(",","")
            .astype(float, errors="ignore")
        )

        # -----------------------------------------
        # CHARTS
        # -----------------------------------------

        col1, col2 = st.columns(2)

        with col1:

            fig = px.pie(
                df_chart,
                names="Company",
                values="Value_clean",
                title="Portfolio Allocation"
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:

            fig2 = px.bar(
                df_chart,
                x="Company",
                y="Value_clean",
                color="Source",
                title="Holdings by Value"
            )

            st.plotly_chart(fig2, use_container_width=True)

        # -----------------------------------------
        # DOWNLOAD OPTION
        # -----------------------------------------

        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Portfolio CSV",
            csv,
            "portfolio.csv",
            "text/csv"
        )
