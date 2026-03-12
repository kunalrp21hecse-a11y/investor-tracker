import streamlit as st
import pdfplumber
import pandas as pd
import plotly.express as px
import re

st.set_page_config(page_title="Financial Document Analyzer", layout="wide")

st.title("📊 Universal Financial Document Analyzer")

st.write(
"""
Upload any financial document (annual report, earnings release, credit rating report, transcript).
The tool extracts financial metrics and creates an interactive dashboard automatically.
"""
)

uploaded_file = st.file_uploader(
    "Upload Financial Document",
    type=["pdf","txt"]
)

# -----------------------------
# TEXT EXTRACTION
# -----------------------------

def extract_text_from_pdf(file):

    text = ""

    with pdfplumber.open(file) as pdf:

        for page in pdf.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text

    return text


# -----------------------------
# FINANCIAL DATA EXTRACTION
# -----------------------------

def extract_financial_metrics(text):

    metrics = {}

    patterns = {

        "Revenue": r"(Revenue|Total Revenue).*?([\d,]+\s?(million|billion|crore|bn)?)",
        "Net Profit": r"(Net Profit|Net Income).*?([\d,]+\s?(million|billion|crore|bn)?)",
        "EBITDA": r"(EBITDA).*?([\d,]+\s?(million|billion|crore|bn)?)",
        "EPS": r"(EPS|Earnings Per Share).*?([\d\.]+)",
        "Debt": r"(Total Debt).*?([\d,]+\s?(million|billion|crore|bn)?)",
        "Cash Flow": r"(Cash Flow).*?([\d,]+\s?(million|billion|crore|bn)?)"

    }

    for metric, pattern in patterns.items():

        match = re.search(pattern, text, re.IGNORECASE)

        if match:

            metrics[metric] = match.group(2)

        else:

            metrics[metric] = "Not detected"

    return metrics


# -----------------------------
# SIMPLE SENTIMENT ANALYSIS
# -----------------------------

positive_words = ["growth","strong","increase","improvement","profit"]
negative_words = ["decline","loss","risk","decrease","weak"]

def sentiment_score(text):

    text = text.lower()

    pos = sum(word in text for word in positive_words)
    neg = sum(word in text for word in negative_words)

    return pos - neg


# -----------------------------
# DASHBOARD
# -----------------------------

if uploaded_file:

    if uploaded_file.type == "application/pdf":

        text = extract_text_from_pdf(uploaded_file)

    else:

        text = uploaded_file.read().decode()

    metrics = extract_financial_metrics(text)

    sentiment = sentiment_score(text)

    st.subheader("Key Financial Metrics")

    col1,col2,col3 = st.columns(3)

    col1.metric("Revenue", metrics["Revenue"])
    col2.metric("Net Profit", metrics["Net Profit"])
    col3.metric("EBITDA", metrics["EBITDA"])

    col1,col2,col3 = st.columns(3)

    col1.metric("EPS", metrics["EPS"])
    col2.metric("Debt", metrics["Debt"])
    col3.metric("Cash Flow", metrics["Cash Flow"])

    st.subheader("Document Sentiment")

    if sentiment > 0:
        st.success("Positive tone detected")

    elif sentiment < 0:
        st.error("Negative tone detected")

    else:
        st.info("Neutral tone detected")

    # Convert metrics to dataframe

    df = pd.DataFrame(
        list(metrics.items()),
        columns=["Metric","Value"]
    )

    st.subheader("Metrics Table")

    st.dataframe(df)

    # Visualization

    numeric_values = []

    labels = []

    for k,v in metrics.items():

        number = re.findall(r"\d+", str(v))

        if number:

            numeric_values.append(int(number[0]))
            labels.append(k)

    if numeric_values:

        chart_df = pd.DataFrame({
            "Metric": labels,
            "Value": numeric_values
        })

        fig = px.bar(
            chart_df,
            x="Metric",
            y="Value",
            title="Extracted Financial Metrics"
        )

        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Raw Extracted Text")

    st.text_area(
        "Document Text Preview",
        text[:3000],
        height=300
    )
