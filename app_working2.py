# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Set page config FIRST
st.set_page_config(page_title="Aged Care Fraud-Risk Intelligence Dashboard", layout="wide")

# Load simulation data
@st.cache_data
def load_simulation_data():
    return pd.read_csv("simulated_aged_care_claims_balanced.csv", parse_dates=['Service_Date'])

# Load GEM star ratings real-world data
@st.cache_data
def load_gem_data():
    try:
        return pd.read_excel("star-ratings-quarterly-data-extract-february-2025.xlsx", sheet_name="Detailed data")
    except Exception as e:
        return None

# Load data
df = load_simulation_data()
gem_data = load_gem_data()

# Merge based on synthetic provider names for demonstration purposes
if gem_data is not None and not gem_data.empty:
    gem_data_sample = gem_data.sample(n=min(len(df['Provider_ID'].unique()), len(gem_data))).reset_index(drop=True)
    provider_mapping = dict(zip(df['Provider_ID'].unique(), gem_data_sample['Service Name']))
    df['Real_Provider_Name'] = df['Provider_ID'].map(provider_mapping)
    df['Compliance_Rating'] = gem_data_sample['Compliance Rating']
    df['Staffing_Rating'] = gem_data_sample['Staffing Rating']
else:
    df['Real_Provider_Name'] = df['Provider_ID']
    df['Compliance_Rating'] = "Unknown"
    df['Staffing_Rating'] = "Unknown"

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
    This dashboard integrates **simulated claims data** with **real-world compliance ratings** from the Australian aged care sector.

    **Purpose:**
    - Demonstrate anomaly detection and regulatory risk profiling.

    **Data Sources:**
    - Simulated claims generated for a 6-month period.
    - Real provider compliance and staffing ratings from GEM.

    **Analysis Overview:**
    - Time series trend inspection.
    - Benchmarking against expected service hours.
    - Weekend behaviour patterns.
    - Anomaly risk profiling augmented by compliance ratings.
    - Provider drilldowns linking anomalies with real-world performance.
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

    This plot ranks providers by the average size of anomalies in their claims, now cross-referenced with compliance ratings.
    """)
    provider_scores = filtered_df.groupby("Real_Provider_Name")["Anomaly_Score"].mean().reset_index()
    top_n = st.slider("Select number of top providers to display:", min_value=3, max_value=20, value=5)
    top_providers = provider_scores.sort_values(by="Anomaly_Score", ascending=False).head(top_n)
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=top_providers['Anomaly_Score'],
                                  theta=top_providers['Real_Provider_Name'],
                                  fill='toself', name='Avg Anomaly'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True)),
                      showlegend=False,
                      title=f"Top {top_n} Providers by Average Anomaly Score")
    st.plotly_chart(fig, use_container_width=True)

# Drilldown
with tabs[5]:
    st.subheader("Drilldown by Provider")
    selected_provider = st.selectbox("Select Provider", options=sorted(filtered_df['Real_Provider_Name'].unique()))
    drill = filtered_df[filtered_df['Real_Provider_Name'] == selected_provider].copy()
    drill['Anomaly_Score_Positive'] = drill['Anomaly_Score'].apply(lambda x: abs(x))
    st.markdown(f"**Compliance Rating:** {drill['Compliance_Rating'].iloc[0]} | **Staffing Rating:** {drill['Staffing_Rating'].iloc[0]}")
    fig = px.scatter(drill, x="Service_Date", y="Claimed_Amount", color="Item_Code",
                     size="Anomaly_Score_Positive", title=f"Claims for {selected_provider}")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(drill.sort_values("Service_Date", ascending=False))
