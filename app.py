"""
Claims Timeliness Dashboard
A Streamlit application for analyzing health insurance claims processing timeliness.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
from data_generator import generate_claims_data, get_summary_stats

# Page configuration
st.set_page_config(
    page_title="Claims Timeliness Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data(n_claims: int = 5000, seed: int = 42) -> pd.DataFrame:
    """Load and cache the claims data."""
    df = generate_claims_data(n_claims=n_claims, seed=seed)
    # Convert date columns to datetime for filtering
    for col in ['first_service_date', 'last_service_date', 'received_date', 'paid_date']:
        df[col] = pd.to_datetime(df[col])
    return df


def create_timeliness_gauge(value: float, title: str, threshold: float = 90) -> go.Figure:
    """Create a gauge chart for timeliness metrics."""
    color = "green" if value >= threshold else "orange" if value >= threshold * 0.8 else "red"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 16}},
        number={'suffix': '%', 'font': {'size': 32}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, threshold * 0.8], 'color': '#ffebee'},
                {'range': [threshold * 0.8, threshold], 'color': '#fff3e0'},
                {'range': [threshold, 100], 'color': '#e8f5e9'}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': threshold
            }
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def create_trend_chart(df: pd.DataFrame, date_col: str, metric_col: str, title: str) -> go.Figure:
    """Create a trend line chart."""
    trend_data = df.groupby(df[date_col].dt.to_period('M')).agg({
        metric_col: 'mean'
    }).reset_index()
    trend_data[date_col] = trend_data[date_col].astype(str)

    fig = px.line(
        trend_data,
        x=date_col,
        y=metric_col,
        title=title,
        markers=True
    )
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Days",
        hovermode="x unified"
    )
    return fig


def create_distribution_chart(df: pd.DataFrame, col: str, title: str, bins: int = 30) -> go.Figure:
    """Create a histogram with distribution."""
    fig = px.histogram(
        df,
        x=col,
        nbins=bins,
        title=title,
        color_discrete_sequence=['#1f77b4']
    )
    fig.update_layout(
        xaxis_title="Days",
        yaxis_title="Count",
        bargap=0.1
    )
    return fig


def main():
    # Sidebar
    st.sidebar.image("https://img.icons8.com/color/96/000000/health-checkup.png", width=80)
    st.sidebar.title("Claims Timeliness")
    st.sidebar.markdown("---")

    # Data generation options
    st.sidebar.subheader("Data Settings")
    n_claims = st.sidebar.slider("Number of Claims", 1000, 10000, 5000, 500)
    seed = st.sidebar.number_input("Random Seed", 1, 100, 42)

    # Load data
    with st.spinner("Generating claims data..."):
        df = load_data(n_claims=n_claims, seed=seed)

    # Filters
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filters")

    # Date range filter
    min_date = df['first_service_date'].min().date()
    max_date = df['first_service_date'].max().date()
    date_range = st.sidebar.date_input(
        "Service Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # Claim type filter
    claim_types = ['All'] + list(df['claim_type'].unique())
    selected_claim_type = st.sidebar.selectbox("Claim Type", claim_types)

    # Network status filter
    network_options = ['All'] + list(df['network_status'].unique())
    selected_network = st.sidebar.selectbox("Network Status", network_options)

    # Group filter
    groups = ['All'] + sorted(df['group_id'].unique().tolist())
    selected_group = st.sidebar.selectbox("Group", groups)

    # Package filter
    packages = ['All'] + list(df['package'].unique())
    selected_package = st.sidebar.selectbox("Package", packages)

    # Claim status filter
    statuses = ['All'] + list(df['claim_status'].unique())
    selected_status = st.sidebar.selectbox("Claim Status", statuses)

    # Apply filters
    filtered_df = df.copy()

    if len(date_range) == 2:
        filtered_df = filtered_df[
            (filtered_df['first_service_date'].dt.date >= date_range[0]) &
            (filtered_df['first_service_date'].dt.date <= date_range[1])
        ]

    if selected_claim_type != 'All':
        filtered_df = filtered_df[filtered_df['claim_type'] == selected_claim_type]

    if selected_network != 'All':
        filtered_df = filtered_df[filtered_df['network_status'] == selected_network]

    if selected_group != 'All':
        filtered_df = filtered_df[filtered_df['group_id'] == selected_group]

    if selected_package != 'All':
        filtered_df = filtered_df[filtered_df['package'] == selected_package]

    if selected_status != 'All':
        filtered_df = filtered_df[filtered_df['claim_status'] == selected_status]

    # Get unique claims for claim-level metrics
    claims_df = filtered_df.groupby('claim_id').first().reset_index()

    # Main content
    st.title("📊 Claims Timeliness Dashboard")
    st.markdown("Monitor and analyze health insurance claims processing performance")

    # Summary metrics
    st.markdown("### Key Performance Indicators")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Total Claims",
            f"{claims_df['claim_id'].nunique():,}",
            help="Number of unique claims"
        )

    with col2:
        st.metric(
            "Total Billed",
            f"${filtered_df['billed_amount'].sum():,.0f}",
            help="Total billed amount"
        )

    with col3:
        st.metric(
            "Total Paid",
            f"${filtered_df['paid_amount'].sum():,.0f}",
            help="Total paid amount"
        )

    with col4:
        avg_processing = claims_df['days_to_process'].mean()
        st.metric(
            "Avg Processing Days",
            f"{avg_processing:.1f}",
            delta=f"{avg_processing - 14:.1f} vs target" if avg_processing > 14 else f"{14 - avg_processing:.1f} under target",
            delta_color="inverse"
        )

    with col5:
        avg_turnaround = claims_df['total_turnaround_days'].mean()
        st.metric(
            "Avg Turnaround Days",
            f"{avg_turnaround:.1f}",
            help="From service to payment"
        )

    st.markdown("---")

    # Timeliness Gauges
    st.markdown("### Timeliness Compliance")
    gauge_col1, gauge_col2, gauge_col3, gauge_col4 = st.columns(4)

    with gauge_col1:
        pct_14_days = claims_df['processed_within_14_days'].mean() * 100
        fig = create_timeliness_gauge(pct_14_days, "Processed ≤14 Days", 85)
        st.plotly_chart(fig, use_container_width=True)

    with gauge_col2:
        pct_30_days = claims_df['processed_within_30_days'].mean() * 100
        fig = create_timeliness_gauge(pct_30_days, "Processed ≤30 Days", 95)
        st.plotly_chart(fig, use_container_width=True)

    with gauge_col3:
        pct_received_30 = claims_df['received_within_30_days'].mean() * 100
        fig = create_timeliness_gauge(pct_received_30, "Received ≤30 Days", 90)
        st.plotly_chart(fig, use_container_width=True)

    with gauge_col4:
        pct_timely = claims_df['timely_filing'].mean() * 100
        fig = create_timeliness_gauge(pct_timely, "Timely Filing", 98)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Trends",
        "📊 Distribution",
        "🏢 By Segment",
        "💰 Financial",
        "📋 Claims Detail"
    ])

    with tab1:
        st.markdown("### Processing Time Trends")

        trend_col1, trend_col2 = st.columns(2)

        with trend_col1:
            # Average processing time trend
            monthly_processing = claims_df.groupby(
                claims_df['paid_date'].dt.to_period('M')
            ).agg({
                'days_to_process': 'mean',
                'claim_id': 'count'
            }).reset_index()
            monthly_processing['paid_date'] = monthly_processing['paid_date'].astype(str)

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=monthly_processing['paid_date'],
                y=monthly_processing['days_to_process'],
                mode='lines+markers',
                name='Avg Processing Days',
                line=dict(color='#1f77b4', width=2)
            ))
            fig.add_hline(y=14, line_dash="dash", line_color="red",
                         annotation_text="14-Day Target")
            fig.update_layout(
                title="Average Processing Days Over Time",
                xaxis_title="Month",
                yaxis_title="Days",
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)

        with trend_col2:
            # Compliance rate trend
            monthly_compliance = claims_df.groupby(
                claims_df['paid_date'].dt.to_period('M')
            ).agg({
                'processed_within_14_days': 'mean',
                'processed_within_30_days': 'mean'
            }).reset_index()
            monthly_compliance['paid_date'] = monthly_compliance['paid_date'].astype(str)
            monthly_compliance['processed_within_14_days'] *= 100
            monthly_compliance['processed_within_30_days'] *= 100

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=monthly_compliance['paid_date'],
                y=monthly_compliance['processed_within_14_days'],
                mode='lines+markers',
                name='≤14 Days',
                line=dict(color='#2ca02c', width=2)
            ))
            fig.add_trace(go.Scatter(
                x=monthly_compliance['paid_date'],
                y=monthly_compliance['processed_within_30_days'],
                mode='lines+markers',
                name='≤30 Days',
                line=dict(color='#1f77b4', width=2)
            ))
            fig.add_hline(y=85, line_dash="dash", line_color="red",
                         annotation_text="85% Target")
            fig.update_layout(
                title="Compliance Rate Trend",
                xaxis_title="Month",
                yaxis_title="Percentage",
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)

        # Volume trend
        st.markdown("### Claims Volume Trend")
        monthly_volume = claims_df.groupby(
            claims_df['received_date'].dt.to_period('M')
        ).size().reset_index(name='claim_count')
        monthly_volume['received_date'] = monthly_volume['received_date'].astype(str)

        fig = px.bar(
            monthly_volume,
            x='received_date',
            y='claim_count',
            title="Monthly Claims Volume",
            color_discrete_sequence=['#1f77b4']
        )
        fig.update_layout(xaxis_title="Month", yaxis_title="Number of Claims")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown("### Processing Time Distribution")

        dist_col1, dist_col2 = st.columns(2)

        with dist_col1:
            fig = px.histogram(
                claims_df,
                x='days_to_process',
                nbins=50,
                title="Distribution of Processing Days",
                color_discrete_sequence=['#1f77b4']
            )
            fig.add_vline(x=14, line_dash="dash", line_color="red",
                         annotation_text="14-Day Target")
            fig.add_vline(x=30, line_dash="dash", line_color="orange",
                         annotation_text="30-Day Target")
            fig.update_layout(xaxis_title="Days to Process", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)

        with dist_col2:
            fig = px.histogram(
                claims_df,
                x='days_to_receive',
                nbins=50,
                title="Distribution of Days to Receive",
                color_discrete_sequence=['#2ca02c']
            )
            fig.add_vline(x=30, line_dash="dash", line_color="red",
                         annotation_text="30-Day Target")
            fig.update_layout(xaxis_title="Days to Receive", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)

        # Box plot comparison
        st.markdown("### Processing Time by Category")

        box_col1, box_col2 = st.columns(2)

        with box_col1:
            fig = px.box(
                claims_df,
                x='claim_type',
                y='days_to_process',
                title="Processing Days by Claim Type",
                color='claim_type'
            )
            fig.update_layout(showlegend=False, xaxis_title="Claim Type", yaxis_title="Days")
            st.plotly_chart(fig, use_container_width=True)

        with box_col2:
            fig = px.box(
                claims_df,
                x='network_status',
                y='days_to_process',
                title="Processing Days by Network Status",
                color='network_status'
            )
            fig.update_layout(showlegend=False, xaxis_title="Network Status", yaxis_title="Days")
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown("### Performance by Segment")

        seg_col1, seg_col2 = st.columns(2)

        with seg_col1:
            # By Group
            group_perf = claims_df.groupby('group_id').agg({
                'days_to_process': 'mean',
                'processed_within_14_days': 'mean',
                'claim_id': 'count'
            }).reset_index()
            group_perf.columns = ['Group', 'Avg Processing Days', '14-Day Compliance', 'Claim Count']
            group_perf['14-Day Compliance'] = (group_perf['14-Day Compliance'] * 100).round(1)
            group_perf = group_perf.sort_values('Avg Processing Days')

            fig = px.bar(
                group_perf,
                x='Group',
                y='Avg Processing Days',
                title="Average Processing Days by Group",
                color='Avg Processing Days',
                color_continuous_scale='RdYlGn_r'
            )
            fig.add_hline(y=14, line_dash="dash", line_color="red")
            st.plotly_chart(fig, use_container_width=True)

        with seg_col2:
            # By Package
            package_perf = claims_df.groupby('package').agg({
                'days_to_process': 'mean',
                'processed_within_14_days': 'mean',
                'claim_id': 'count'
            }).reset_index()
            package_perf.columns = ['Package', 'Avg Processing Days', '14-Day Compliance', 'Claim Count']
            package_perf['14-Day Compliance'] = (package_perf['14-Day Compliance'] * 100).round(1)

            fig = px.bar(
                package_perf,
                x='Package',
                y='14-Day Compliance',
                title="14-Day Compliance by Package",
                color='14-Day Compliance',
                color_continuous_scale='RdYlGn',
                text='14-Day Compliance'
            )
            fig.add_hline(y=85, line_dash="dash", line_color="red")
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)

        # Heatmap of performance
        st.markdown("### Performance Heatmap")
        heatmap_data = claims_df.groupby(['group_id', 'claim_type']).agg({
            'days_to_process': 'mean'
        }).reset_index()
        heatmap_pivot = heatmap_data.pivot(index='group_id', columns='claim_type', values='days_to_process')

        fig = px.imshow(
            heatmap_pivot,
            title="Average Processing Days: Group vs Claim Type",
            color_continuous_scale='RdYlGn_r',
            aspect='auto'
        )
        fig.update_layout(xaxis_title="Claim Type", yaxis_title="Group")
        st.plotly_chart(fig, use_container_width=True)

        # State performance
        st.markdown("### Performance by Provider State")
        state_perf = claims_df.groupby('provider_state').agg({
            'days_to_process': 'mean',
            'claim_id': 'count'
        }).reset_index()
        state_perf.columns = ['State', 'Avg Processing Days', 'Claim Count']

        fig = px.bar(
            state_perf.sort_values('Avg Processing Days'),
            x='State',
            y='Avg Processing Days',
            title="Average Processing Days by Provider State",
            color='Avg Processing Days',
            color_continuous_scale='RdYlGn_r'
        )
        fig.add_hline(y=14, line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.markdown("### Financial Analysis")

        fin_col1, fin_col2 = st.columns(2)

        with fin_col1:
            # Financial summary by status
            status_financial = filtered_df.groupby('claim_status').agg({
                'billed_amount': 'sum',
                'allowed_amount': 'sum',
                'paid_amount': 'sum',
                'claim_id': 'nunique'
            }).reset_index()
            status_financial.columns = ['Status', 'Billed', 'Allowed', 'Paid', 'Claims']

            fig = px.bar(
                status_financial,
                x='Status',
                y=['Billed', 'Allowed', 'Paid'],
                title="Financial Summary by Claim Status",
                barmode='group'
            )
            st.plotly_chart(fig, use_container_width=True)

        with fin_col2:
            # Payment ratio analysis
            payment_ratio = filtered_df.groupby('claim_type').agg({
                'billed_amount': 'sum',
                'paid_amount': 'sum'
            }).reset_index()
            payment_ratio['Payment Ratio'] = (payment_ratio['paid_amount'] / payment_ratio['billed_amount'] * 100).round(1)

            fig = px.bar(
                payment_ratio,
                x='claim_type',
                y='Payment Ratio',
                title="Payment Ratio by Claim Type",
                color='Payment Ratio',
                color_continuous_scale='Greens',
                text='Payment Ratio'
            )
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig.update_layout(xaxis_title="Claim Type", yaxis_title="Payment Ratio (%)")
            st.plotly_chart(fig, use_container_width=True)

        # Denial analysis
        st.markdown("### Denial Analysis")
        denied_claims = filtered_df[filtered_df['claim_status'] == 'Denied']

        if len(denied_claims) > 0:
            denial_col1, denial_col2 = st.columns(2)

            with denial_col1:
                denial_reasons = denied_claims.groupby('denial_reason').size().reset_index(name='count')
                fig = px.pie(
                    denial_reasons,
                    values='count',
                    names='denial_reason',
                    title="Denial Reasons Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)

            with denial_col2:
                denial_by_type = denied_claims.groupby('claim_type').size().reset_index(name='count')
                fig = px.bar(
                    denial_by_type,
                    x='claim_type',
                    y='count',
                    title="Denials by Claim Type",
                    color='claim_type'
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No denied claims in the current filter selection.")

        # Monthly financial trend
        st.markdown("### Monthly Financial Trend")
        monthly_financial = filtered_df.groupby(
            filtered_df['paid_date'].dt.to_period('M')
        ).agg({
            'billed_amount': 'sum',
            'paid_amount': 'sum'
        }).reset_index()
        monthly_financial['paid_date'] = monthly_financial['paid_date'].astype(str)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=monthly_financial['paid_date'],
            y=monthly_financial['billed_amount'],
            mode='lines+markers',
            name='Billed',
            line=dict(color='#ff7f0e', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=monthly_financial['paid_date'],
            y=monthly_financial['paid_amount'],
            mode='lines+markers',
            name='Paid',
            line=dict(color='#2ca02c', width=2)
        ))
        fig.update_layout(
            title="Monthly Billed vs Paid Amounts",
            xaxis_title="Month",
            yaxis_title="Amount ($)",
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab5:
        st.markdown("### Claims Detail View")

        # Summary statistics
        st.markdown("#### Filter Summary")
        summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
        with summary_col1:
            st.metric("Filtered Claims", f"{claims_df['claim_id'].nunique():,}")
        with summary_col2:
            st.metric("Total Lines", f"{len(filtered_df):,}")
        with summary_col3:
            st.metric("Unique Members", f"{filtered_df['member_id'].nunique():,}")
        with summary_col4:
            st.metric("Unique Providers", f"{filtered_df['provider_id'].nunique():,}")

        st.markdown("---")

        # Search and filter for detail view
        search_col1, search_col2 = st.columns(2)
        with search_col1:
            claim_search = st.text_input("Search Claim ID", "")
        with search_col2:
            member_search = st.text_input("Search Member ID", "")

        detail_df = filtered_df.copy()
        if claim_search:
            detail_df = detail_df[detail_df['claim_id'].str.contains(claim_search, case=False)]
        if member_search:
            detail_df = detail_df[detail_df['member_id'].str.contains(member_search, case=False)]

        # Display options
        show_cols = st.multiselect(
            "Select columns to display",
            options=detail_df.columns.tolist(),
            default=['claim_id', 'line_number', 'member_id', 'claim_type', 'first_service_date',
                    'received_date', 'paid_date', 'days_to_process', 'billed_amount',
                    'paid_amount', 'claim_status']
        )

        # Sort options
        sort_col1, sort_col2 = st.columns(2)
        with sort_col1:
            sort_by = st.selectbox("Sort by", show_cols, index=show_cols.index('days_to_process') if 'days_to_process' in show_cols else 0)
        with sort_col2:
            sort_order = st.radio("Order", ["Descending", "Ascending"], horizontal=True)

        # Apply sorting
        ascending = sort_order == "Ascending"
        display_df = detail_df[show_cols].sort_values(sort_by, ascending=ascending)

        # Display dataframe
        st.dataframe(
            display_df.head(1000),
            use_container_width=True,
            hide_index=True
        )

        st.caption(f"Showing {min(1000, len(display_df)):,} of {len(display_df):,} records")

        # Download option
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Data as CSV",
            data=csv,
            file_name=f"claims_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <p>Claims Timeliness Dashboard | Demo Application with Synthetic Data</p>
            <p>Built with Streamlit</p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
