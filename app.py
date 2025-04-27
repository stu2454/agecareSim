# app.py - Updated with Provider Drill-Down Tab and Tooltips

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Set Streamlit page config
st.set_page_config(page_title="Aged Care Sector Intelligence Dashboard", layout="wide")

# Define a consistent colour for bar and box plots
PRIMARY_COLOR = "#1f77b4"  # Plotly's default blue

# Function to load and preprocess data
@st.cache_data
def load_data():
    try:
        sheets = pd.read_excel(
            "star-ratings-quarterly-data-extract-february-2025.xlsx",
            sheet_name=None,
            engine="openpyxl"
        )
        star_ratings = sheets.get("Star Ratings", pd.DataFrame())
        detailed_data = sheets.get("Detailed data", pd.DataFrame())

        if not detailed_data.empty:
            detailed_data['[S] Registered Nurse Care Minutes - Actual'] = pd.to_numeric(detailed_data['[S] Registered Nurse Care Minutes - Actual'], errors='coerce')
            detailed_data['[S] Registered Nurse Care Minutes - Target'] = pd.to_numeric(detailed_data['[S] Registered Nurse Care Minutes - Target'], errors='coerce')
            detailed_data['[S] Total Care Minutes - Actual'] = pd.to_numeric(detailed_data['[S] Total Care Minutes - Actual'], errors='coerce')
            detailed_data['[S] Total Care Minutes - Target'] = pd.to_numeric(detailed_data['[S] Total Care Minutes - Target'], errors='coerce')

            detailed_data['RN Care Compliance %'] = (detailed_data['[S] Registered Nurse Care Minutes - Actual'] / detailed_data['[S] Registered Nurse Care Minutes - Target']).replace([float('inf'), -float('inf')], pd.NA) * 100
            detailed_data['Total Care Compliance %'] = (detailed_data['[S] Total Care Minutes - Actual'] / detailed_data['[S] Total Care Minutes - Target']).replace([float('inf'), -float('inf')], pd.NA) * 100

        return star_ratings, detailed_data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame()

# Load data
star_ratings, detailed_data = load_data()

# Sidebar filters
st.sidebar.header("Filter Options")
states = detailed_data['State/Territory'].dropna().unique().tolist() if not detailed_data.empty else []
selected_state = st.sidebar.selectbox("Select State/Territory", options=["All"] + sorted(states))

if selected_state != "All":
    filtered_providers = detailed_data[detailed_data['State/Territory'] == selected_state]['Provider Name'].dropna().unique().tolist()
else:
    filtered_providers = detailed_data['Provider Name'].dropna().unique().tolist()

selected_provider = st.sidebar.selectbox("Select Provider", options=["All"] + sorted(filtered_providers))

# Main layout with tabs
tabs = st.tabs([
    "Introduction",
    "Sector Overview",
    "Provider Profile Drill-Down",
    "Compare Providers",
    "Anomaly Detection",
    "Quality Measures Risk Radar",
    "Compliance Actions Tracker"
])

# Introduction
with tabs[0]:
    st.header("Welcome to the Aged Care Sector Intelligence Dashboard")
    st.markdown("""
    This tool provides sector-wide and provider-specific insights using:
    - Star Ratings
    - Resident Experience Surveys
    - Compliance Monitoring Data
    - Staffing Metrics
    - Quality Measures (Falls, Pressure Injuries, Medication Management)

    Designed to strengthen proactive regulation, provider benchmarking, and public sector stewardship.
    """)

# Sector Overview
with tabs[1]:
    st.subheader("Sector Overview")
    if not detailed_data.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            avg_rn_care = detailed_data['RN Care Compliance %'].mean()
            st.metric("Avg RN Care Compliance (%)", f"{avg_rn_care:.1f}%")
        with col2:
            avg_total_care = detailed_data['Total Care Compliance %'].mean()
            st.metric("Avg Total Care Compliance (%)", f"{avg_total_care:.1f}%")
        with col3:
            compliance_actions = detailed_data['Compliance rating'].value_counts().get('Non-compliant', 0)
            st.metric("Services with Non-Compliance", compliance_actions)

        st.markdown("### Staffing Compliance Distribution")
        fig = px.histogram(detailed_data, x='RN Care Compliance %', nbins=30, title='Distribution of RN Care Compliance %')
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Overall Star Ratings Distribution")
        if 'Overall Star Rating' in detailed_data.columns:
            fig2 = px.histogram(detailed_data, x='Overall Star Rating', nbins=5, title='Distribution of Overall Star Ratings')
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("No sector data available to display.")


# Provider Profile Drill-Down
# Provider Profile Drill-Down Tab
with tabs[2]:
    st.subheader("Provider Profile Drill-Down")

    if selected_provider != "All" and not detailed_data.empty:
        provider_data = detailed_data[detailed_data['Provider Name'] == selected_provider]

        if not provider_data.empty:
            # Summary tooltip
            unique_suburbs = provider_data['Service Suburb'].nunique()
            size_counts = provider_data['Size'].value_counts().to_dict()
            tooltip_text = f"Unique Suburbs: {unique_suburbs}\n"
            tooltip_text += f"Small: {size_counts.get('Small', 0)} | Medium: {size_counts.get('Medium', 0)} | Large: {size_counts.get('Large', 0)}"

            st.markdown(f"### Profile for {selected_provider} (Entries: {len(provider_data)})")
            st.caption(tooltip_text)

            # Key Metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Overall Star Rating", f"{int(provider_data['Overall Star Rating'].mean())}")
            with col2:
                st.metric("RN Care Compliance (%)", f"{int(provider_data['RN Care Compliance %'].mean())}%")
            with col3:
                st.metric("Total Care Compliance (%)", f"{int(provider_data['Total Care Compliance %'].mean())}%")

            # Average Quality Measures (Bar Chart)
            st.markdown("### Average Quality Measures (with Standard Error)")
            qm_fields = ['[QM] Pressure injuries*', '[QM] Restrictive practices', '[QM] Unplanned weight loss*',
                         '[QM] Falls and major injury - falls*', '[QM] Falls and major injury - major injury from a fall*',
                         '[QM] Medication management - polypharmacy', '[QM] Medication management - antipsychotic']

            if not provider_data[qm_fields].empty:
                qm_summary = provider_data[qm_fields].agg(['mean', 'sem']).T.reset_index()
                qm_summary.columns = ['Quality Indicator', 'Mean', 'SEM']

                fig_bar = px.bar(
                    qm_summary,
                    x='Quality Indicator',
                    y='Mean',
                    error_y='SEM',
                    title="Average Quality Indicators with Standard Error",
                    color_discrete_sequence=[PRIMARY_COLOR]
                )
                st.plotly_chart(fig_bar, use_container_width=True)

            # Quality Measures Distribution (Box Plot)
            st.markdown("### Quality Measures Distribution (Box Plot)")
            qm_melted_provider = provider_data[qm_fields].copy()
            qm_melted_provider['Service Name'] = provider_data['Service Name']
            qm_melted_provider = qm_melted_provider.melt(id_vars="Service Name", var_name="Quality Indicator", value_name="Value")
            qm_melted_provider['Tooltip'] = qm_melted_provider['Service Name']

            fig_box = px.box(
                qm_melted_provider,
                x="Quality Indicator",
                y="Value",
                points="all",
                hover_name="Tooltip",
                title="Provider Quality Measure Distributions"
            )
            fig_box.update_traces(marker_color=PRIMARY_COLOR, marker_outliercolor="red", marker_line_outliercolor="red")
            st.plotly_chart(fig_box, use_container_width=True)

            # Compliance History (only services with Decision Type present)
            compliance_columns = ['Service Name', 'Compliance rating', '[C] Decision type', '[C] Date Decision Applied', '[C] Date Decision Ends']
            compliance_data = provider_data[compliance_columns]
            compliance_filtered = compliance_data.dropna(subset=['[C] Decision type'], how='all')

            if not compliance_filtered.empty:
                st.markdown("### Compliance History")
                st.dataframe(compliance_filtered, use_container_width=True)
            else:
                st.info("No compliance history available for this provider.")

            # Provider Summary and Serious Concerns
            st.markdown("### Provider Summary")
            avg_star_rating = int(provider_data['Overall Star Rating'].mean())
            avg_rn_compliance = int(provider_data['RN Care Compliance %'].mean())
            avg_total_compliance = int(provider_data['Total Care Compliance %'].mean())

            flagged_services = provider_data[
                (provider_data['Overall Star Rating'] <= 2.0) |
                (provider_data['Compliance rating'] == 1) |
                (provider_data["Residents' Experience rating"] <= 2.0) |
                (provider_data['Staffing rating'] <= 2.0) |
                (provider_data['Quality Measures rating'] <= 2.0)
            ]

            if avg_star_rating >= 5 and avg_rn_compliance >= 100 and avg_total_compliance >= 100:
                summary = f"{selected_provider} demonstrates excellent performance with an average Overall Star Rating of {avg_star_rating}. RN Care Compliance averages {avg_rn_compliance}% and Total Care Compliance averages {avg_total_compliance}%, both exceeding expectations."
            elif avg_star_rating >= 3 and avg_rn_compliance >= 90 and avg_total_compliance >= 90:
                summary = f"{selected_provider} shows generally good performance with an average Overall Star Rating of {avg_star_rating}. RN Care Compliance averages {avg_rn_compliance}% and Total Care Compliance averages {avg_total_compliance}%."
            else:
                summary = f"{selected_provider} exhibits potential risks with an average Overall Star Rating of {avg_star_rating}. RN Care Compliance averages {avg_rn_compliance}% and Total Care Compliance averages {avg_total_compliance}%, indicating areas for urgent improvement."

            st.write(summary)

            if not flagged_services.empty:
                with st.container():
                    st.markdown(f"""
                    <div style='padding: 1rem; border: 2px solid #d9534f; border-radius: 10px; background-color: #d9534f; color: white;'>
                    <strong>⚠️ {len(flagged_services)} service(s) operated by {selected_provider} show serious quality concerns.</strong>
                    </div>
                    """, unsafe_allow_html=True)

                    # Highlight serious concerns in flagged table
                    def highlight_serious(val, col):
                        if col == 'Overall Star Rating' and val <= 2.0:
                            return 'background-color: #ff9999; font-weight: bold;'
                        elif col == 'Compliance rating' and val == 1:
                            return 'background-color: #ff9999; font-weight: bold;'
                        elif col == "Residents' Experience rating" and val <= 2.0:
                            return 'background-color: #ff9999; font-weight: bold;'
                        elif col == 'Staffing rating' and val <= 2.0:
                            return 'background-color: #ff9999; font-weight: bold;'
                        elif col == 'Quality Measures rating' and val <= 2.0:
                            return 'background-color: #ff9999; font-weight: bold;'
                        else:
                            return ''

                    # Inside the serious concerns warning container
                    styled_flagged = flagged_services[
                        ['Service Name', 'Overall Star Rating', 'Compliance rating', 
                        "Residents' Experience rating", 'Staffing rating', 'Quality Measures rating']
                    ].style.apply(
                        lambda x: [highlight_serious(v, x.name) for v in x], axis=0  # Apply red highlight where necessary
                    ).format({
                        'Overall Star Rating': "{:.0f}",
                        'Compliance rating': "{:.0f}",
                        "Residents' Experience rating": "{:.0f}",
                        'Staffing rating': "{:.0f}",
                        'Quality Measures rating': "{:.0f}",
                    }).set_properties(**{
                        'text-align': 'center'   # Centre-align all cell content
                    })

                    st.dataframe(styled_flagged, use_container_width=True)


        else:
            st.info("No data available for selected provider.")
    else:
        st.info("Please select a specific provider from the sidebar.")







# Compare Providers
with tabs[3]:
    st.subheader("Compare Providers")
    st.info("Side-by-side provider benchmarking will appear here.")

# Anomaly Detection
with tabs[4]:
    st.subheader("Anomaly Detection")
    st.info("Outliers and deviation detection will appear here.")

# Quality Measures Risk Radar
with tabs[5]:
    st.subheader("Quality Measures Risk Radar")
    st.info("Risk radar/spider plots for Quality Measures will appear here.")

# Compliance Actions Tracker
with tabs[6]:
    st.subheader("Compliance Actions Tracker")
    st.info("Compliance decision tracking and mapping will appear here.")

# Ready for further functionality expansion!
