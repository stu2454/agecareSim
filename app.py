# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Load data (assumes local CSV for now)
df = pd.read_csv("simulated_aged_care_claims_balanced.csv", parse_dates=['Service_Date'])

st.set_page_config(page_title="Aged Care Fraud-Risk Intelligence Dashboard", layout="wide")
st.title("🔍 Aged Care Fraud-Risk Intelligence Dashboard")

# Sidebar filters
with st.sidebar:
    st.header("Filter Data")
    selected_region = st.selectbox("Region", options=["All"] + sorted(df['Region'].unique().tolist()))
    selected_item = st.selectbox("Item Code", options=["All"] + sorted(df['Item_Code'].unique().tolist()))

# Filter data
filtered_df = df.copy()
if selected_region != "All":
    filtered_df = filtered_df[filtered_df['Region'] == selected_region]
if selected_item != "All":
    filtered_df = filtered_df[filtered_df['Item_Code'] == selected_item]

# Tab layout
tabs = st.tabs(["Introduction", "Time Series", "Benchmarking", "Weekend Patterns", "Average Anomaly Score Profile", "Provider Drilldown"])

# Introduction Tab
with tabs[0]:
    st.header("Welcome to the Fraud-Risk Intelligence Dashboard")
    st.markdown("""
    This dashboard provides a simulated view of potential fraud-risk indicators in aged care service claims.

    **Purpose:**
    - To demonstrate the use of data analytics for detecting anomalous patterns in provider behaviour.
    - To support regulatory intelligence through visual inspection and statistical indicators.

    **Data Generation:**
    - The data represents simulated claims over a 6-month period.
    - Claims are more frequent on weekdays, reflecting real-world service patterns.
    - Each claim includes a calculated **anomaly score** based on deviation from expected service hours.

    **Analysis Overview:**
    - **Time Series:** Visualise trends in claim volume and value.
    - **Benchmarking:** Compare claimed hours to expected benchmarks by service type.
    - **Weekend Patterns:** Identify unusual claiming behaviour on weekends.
    - **Anomaly Score Profile:** Spot providers with consistent over- or under-claiming patterns.
    - **Drilldown:** Examine individual provider behaviour over time.

    Use the sidebar to filter by region and item type, and click through the tabs to explore.
    """)

# Time Series Anomaly Plot
with tabs[1]:
    st.subheader("Claimed Amount Over Time with Anomaly Score")
    daily_claims = filtered_df.groupby("Service_Date")["Claimed_Amount"].sum().reset_index()
    fig = px.line(daily_claims, x="Service_Date", y="Claimed_Amount", title="Total Claimed Amount Over Time")
    st.plotly_chart(fig, use_container_width=True)

# Boxplot: Claimed vs Expected Hours
with tabs[2]:
    st.subheader("Claimed Hours vs Expected Benchmark")
    fig = px.box(filtered_df, x="Item_Code", y="Claimed_Hours", points="all",
                 color="Region", title="Claimed Hours Distribution by Item Code")
    st.plotly_chart(fig, use_container_width=True)

# Weekend claims heatmap
with tabs[3]:
    st.subheader("Claim Frequency by Day of Week")
    weekday_counts = filtered_df["Day_of_Week"].value_counts().reindex([
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]).reset_index()
    weekday_counts.columns = ["Day", "Count"]
    fig = px.bar(weekday_counts, x="Day", y="Count", color="Count",
                 title="Service Claims by Day of Week")
    st.plotly_chart(fig, use_container_width=True)

# Radar chart of anomaly scores
with tabs[4]:
    st.subheader("Top Providers by Average Anomaly Score")
    st.markdown("""
    **What does this mean?**

    Each provider's "average anomaly score" is the mean of all claim-level anomaly scores.
    - A higher score indicates consistent over-claiming relative to expected hours.
    - A lower or negative score may indicate under-claiming or conservative practices.

    This metric is useful for identifying providers whose claiming patterns consistently deviate from expected benchmarks.
    """)
    provider_scores = filtered_df.groupby("Provider_ID")["Anomaly_Score"].mean().reset_index()
    top_n = st.slider("Select number of top providers to display:", min_value=3, max_value=20, value=5)
    top_providers = provider_scores.sort_values(by="Anomaly_Score", ascending=False).head(top_n)
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=top_providers['Anomaly_Score'],
                                  theta=top_providers['Provider_ID'],
                                  fill='toself', name='Avg Anomaly'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True)),
                      showlegend=False,
                      title=f"Top {top_n} Providers by Average Anomaly Score")
    st.plotly_chart(fig, use_container_width=True)

# Drilldown
with tabs[5]:
    st.subheader("Drilldown by Provider")
    selected_provider = st.selectbox("Select Provider", options=sorted(filtered_df['Provider_ID'].unique()))
    drill = filtered_df[filtered_df['Provider_ID'] == selected_provider].copy()
    drill['Anomaly_Score_Positive'] = drill['Anomaly_Score'].apply(lambda x: abs(x))
    fig = px.scatter(drill, x="Service_Date", y="Claimed_Amount", color="Item_Code",
                     size="Anomaly_Score_Positive", title=f"Claims for {selected_provider}")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(drill.sort_values("Service_Date", ascending=False))
