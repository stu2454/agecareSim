# New version of app.py: Only uses data from the new Excel sheet

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Set page config
st.set_page_config(page_title="Aged Care Sector Performance Dashboard", layout="wide")

# Load GEM star ratings real-world data
@st.cache_data
def load_star_ratings():
    try:
        return pd.read_excel(
            "star-ratings-quarterly-data-extract-february-2025.xlsx",
            sheet_name=None,
            engine="openpyxl"
        )
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return {}

# Load data
sheets = load_star_ratings()
star_ratings = sheets.get("Star Ratings", pd.DataFrame())
detailed_data = sheets.get("Detailed data", pd.DataFrame())

st.title("🔍 Aged Care Sector Performance Dashboard")

# Sidebar filters
with st.sidebar:
    st.header("Filter Services")
    if 'State/Territory' in star_ratings.columns:
        states = star_ratings['State/Territory'].unique().tolist()
        selected_state = st.selectbox("State/Territory", options=["All"] + sorted(states))
    else:
        selected_state = "All"

# Filtered data
filtered_star = star_ratings.copy()
if selected_state != "All" and 'State/Territory' in filtered_star.columns:
    filtered_star = filtered_star[filtered_star['State/Territory'] == selected_state]

filtered_detailed = detailed_data.copy()
if selected_state != "All" and 'State/Territory' in filtered_detailed.columns:
    filtered_detailed = filtered_detailed[filtered_detailed['State/Territory'] == selected_state]

# Tab layout
tabs = st.tabs(["Introduction", "Overall Star Ratings", "Detailed Quality Indicators"])

# Introduction Tab
with tabs[0]:
    st.header("Welcome to the Aged Care Sector Performance Dashboard")
    st.markdown("""
    This dashboard presents real-world data on aged care service performance in Australia.

    **Data Sources:**
    - Star Ratings summary for residential aged care services
    - Detailed Quality Indicators: falls, restraint use, weight loss, medication management

    **Purpose:**
    - Support sector monitoring, regulatory intelligence, and quality improvement.
    """)

# Overall Star Ratings
with tabs[1]:
    st.subheader("Overall Star Ratings Distribution")
    if not filtered_star.empty:
        rating_counts = filtered_star['Overall Star Rating'].value_counts().sort_index()
        fig = px.bar(rating_counts, x=rating_counts.index, y=rating_counts.values,
                     labels={'x': 'Overall Star Rating', 'y': 'Number of Services'},
                     title="Distribution of Overall Star Ratings")
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(filtered_star[['Service Name', 'State/Territory', 'Overall Star Rating', 'Compliance rating', 'Staffing rating']])
    else:
        st.warning("No data available for selected filter.")

# Detailed Quality Indicators
with tabs[2]:
    st.subheader("Detailed Quality Indicators")
    if not filtered_detailed.empty:
        indicators = [col for col in filtered_detailed.columns if any(keyword in col.lower() for keyword in ['fall', 'weight', 'restraint', 'medication', 'injur'])]
        if indicators:
            selected_indicator = st.selectbox("Select Indicator", options=indicators)
            fig = px.histogram(filtered_detailed, x=selected_indicator,
                               nbins=20, title=f"Distribution of {selected_indicator} Rates")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(filtered_detailed[['Service Name', 'State/Territory', selected_indicator]])
        else:
            st.warning("No recognised indicators found in detailed data.")
    else:
        st.warning("No detailed quality data available.")

