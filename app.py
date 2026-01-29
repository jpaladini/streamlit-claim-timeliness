"""
Claims Timeliness Dashboard
A Streamlit application for analyzing health insurance claims processing timeliness.
Features interactive drill-down similar to Tableau's "Get Data" functionality.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from data_generator import generate_claims_data

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
    .drill-down-header {
        background-color: #e3f2fd;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data(n_claims: int = 5000, seed: int = 42) -> pd.DataFrame:
    """Load and cache the claims data."""
    df = generate_claims_data(n_claims=n_claims, seed=seed)
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


def display_drill_down_data(df: pd.DataFrame, title: str, key_prefix: str):
    """Display drill-down data with download option."""
    if len(df) == 0:
        st.info("No data to display for this selection.")
        return

    st.markdown(f"**{title}** ({len(df):,} records)")

    # Column selection for display
    default_cols = ['claim_id', 'member_id', 'claim_type', 'first_service_date',
                   'paid_date', 'days_to_process', 'billed_amount', 'paid_amount', 'claim_status']
    available_cols = [c for c in default_cols if c in df.columns]

    display_df = df[available_cols].head(500)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    if len(df) > 500:
        st.caption(f"Showing first 500 of {len(df):,} records")

    # Download button
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download Full Data",
        data=csv,
        file_name=f"drill_down_{key_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        key=f"download_{key_prefix}"
    )


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

    min_date = df['first_service_date'].min().date()
    max_date = df['first_service_date'].max().date()
    date_range = st.sidebar.date_input(
        "Service Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    claim_types = ['All'] + list(df['claim_type'].unique())
    selected_claim_type = st.sidebar.selectbox("Claim Type", claim_types)

    network_options = ['All'] + list(df['network_status'].unique())
    selected_network = st.sidebar.selectbox("Network Status", network_options)

    groups = ['All'] + sorted(df['group_id'].unique().tolist())
    selected_group = st.sidebar.selectbox("Group", groups)

    packages = ['All'] + list(df['package'].unique())
    selected_package = st.sidebar.selectbox("Package", packages)

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

    claims_df = filtered_df.groupby('claim_id').first().reset_index()

    # Main content
    st.title("📊 Claims Timeliness Dashboard")
    st.markdown("Monitor and analyze health insurance claims processing performance")
    st.info("💡 **Interactive Charts**: Click on any bar, point, or segment to drill down into the underlying data!")

    # Summary metrics
    st.markdown("### Key Performance Indicators")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Claims", f"{claims_df['claim_id'].nunique():,}")
    with col2:
        st.metric("Total Billed", f"${filtered_df['billed_amount'].sum():,.0f}")
    with col3:
        st.metric("Total Paid", f"${filtered_df['paid_amount'].sum():,.0f}")
    with col4:
        avg_processing = claims_df['days_to_process'].mean()
        st.metric("Avg Processing Days", f"{avg_processing:.1f}",
                 delta=f"{avg_processing - 14:.1f} vs target" if avg_processing > 14 else f"{14 - avg_processing:.1f} under target",
                 delta_color="inverse")
    with col5:
        st.metric("Avg Turnaround Days", f"{claims_df['total_turnaround_days'].mean():.1f}")

    st.markdown("---")

    # Timeliness Gauges
    st.markdown("### Timeliness Compliance")
    gauge_col1, gauge_col2, gauge_col3, gauge_col4 = st.columns(4)

    with gauge_col1:
        fig = create_timeliness_gauge(claims_df['processed_within_14_days'].mean() * 100, "Processed ≤14 Days", 85)
        st.plotly_chart(fig, use_container_width=True)
    with gauge_col2:
        fig = create_timeliness_gauge(claims_df['processed_within_30_days'].mean() * 100, "Processed ≤30 Days", 95)
        st.plotly_chart(fig, use_container_width=True)
    with gauge_col3:
        fig = create_timeliness_gauge(claims_df['received_within_30_days'].mean() * 100, "Received ≤30 Days", 90)
        st.plotly_chart(fig, use_container_width=True)
    with gauge_col4:
        fig = create_timeliness_gauge(claims_df['timely_filing'].mean() * 100, "Timely Filing", 98)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Trends", "📊 Distribution", "🏢 By Segment", "💰 Financial", "📋 Claims Detail"
    ])

    # ==================== TRENDS TAB ====================
    with tab1:
        st.markdown("### Processing Time Trends")
        st.caption("Click on any data point or bar to see underlying claims")

        trend_col1, trend_col2 = st.columns(2)

        with trend_col1:
            # Monthly processing trend
            claims_df['paid_month'] = claims_df['paid_date'].dt.to_period('M').astype(str)
            monthly_processing = claims_df.groupby('paid_month').agg({
                'days_to_process': 'mean',
                'claim_id': 'count'
            }).reset_index()

            fig = px.line(
                monthly_processing,
                x='paid_month',
                y='days_to_process',
                title="Average Processing Days Over Time",
                markers=True
            )
            fig.add_hline(y=14, line_dash="dash", line_color="red", annotation_text="14-Day Target")
            fig.update_layout(xaxis_title="Month", yaxis_title="Days")

            event = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="trend_processing")

            if event and event.selection and event.selection.points:
                selected_month = event.selection.points[0]['x']
                drill_data = claims_df[claims_df['paid_month'] == selected_month]
                with st.expander(f"📋 Claims for {selected_month}", expanded=True):
                    display_drill_down_data(drill_data, f"Claims paid in {selected_month}", "trend_proc")

        with trend_col2:
            # Compliance trend
            monthly_compliance = claims_df.groupby('paid_month').agg({
                'processed_within_14_days': 'mean',
                'processed_within_30_days': 'mean'
            }).reset_index()
            monthly_compliance['pct_14'] = monthly_compliance['processed_within_14_days'] * 100
            monthly_compliance['pct_30'] = monthly_compliance['processed_within_30_days'] * 100

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=monthly_compliance['paid_month'], y=monthly_compliance['pct_14'],
                                     mode='lines+markers', name='≤14 Days'))
            fig.add_trace(go.Scatter(x=monthly_compliance['paid_month'], y=monthly_compliance['pct_30'],
                                     mode='lines+markers', name='≤30 Days'))
            fig.add_hline(y=85, line_dash="dash", line_color="red", annotation_text="85% Target")
            fig.update_layout(title="Compliance Rate Trend", xaxis_title="Month", yaxis_title="Percentage")

            event2 = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="trend_compliance")

            if event2 and event2.selection and event2.selection.points:
                selected_month = event2.selection.points[0]['x']
                drill_data = claims_df[claims_df['paid_month'] == selected_month]
                with st.expander(f"📋 Claims for {selected_month}", expanded=True):
                    display_drill_down_data(drill_data, f"Claims paid in {selected_month}", "trend_comp")

        # Volume trend
        st.markdown("### Claims Volume Trend")
        claims_df['received_month'] = claims_df['received_date'].dt.to_period('M').astype(str)
        monthly_volume = claims_df.groupby('received_month').size().reset_index(name='claim_count')

        fig = px.bar(monthly_volume, x='received_month', y='claim_count',
                    title="Monthly Claims Volume", color_discrete_sequence=['#1f77b4'])
        fig.update_layout(xaxis_title="Month", yaxis_title="Number of Claims")

        event3 = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="volume_trend")

        if event3 and event3.selection and event3.selection.points:
            selected_month = event3.selection.points[0]['x']
            drill_data = claims_df[claims_df['received_month'] == selected_month]
            with st.expander(f"📋 Claims received in {selected_month}", expanded=True):
                display_drill_down_data(drill_data, f"Claims received in {selected_month}", "volume")

    # ==================== DISTRIBUTION TAB ====================
    with tab2:
        st.markdown("### Processing Time Distribution")
        st.caption("Click on histogram bars to see claims in that range")

        dist_col1, dist_col2 = st.columns(2)

        with dist_col1:
            fig = px.histogram(claims_df, x='days_to_process', nbins=30,
                              title="Distribution of Processing Days", color_discrete_sequence=['#1f77b4'])
            fig.add_vline(x=14, line_dash="dash", line_color="red", annotation_text="14-Day Target")
            fig.add_vline(x=30, line_dash="dash", line_color="orange", annotation_text="30-Day Target")
            fig.update_layout(xaxis_title="Days to Process", yaxis_title="Count")

            event = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="dist_process")

            if event and event.selection and event.selection.points:
                # Get the bin range from selection
                point = event.selection.points[0]
                if 'x' in point:
                    bin_start = point.get('x', 0)
                    # Approximate bin width
                    bin_width = (claims_df['days_to_process'].max() - claims_df['days_to_process'].min()) / 30
                    bin_end = bin_start + bin_width
                    drill_data = claims_df[(claims_df['days_to_process'] >= bin_start) &
                                          (claims_df['days_to_process'] < bin_end)]
                    with st.expander(f"📋 Claims with {int(bin_start)}-{int(bin_end)} processing days", expanded=True):
                        display_drill_down_data(drill_data, f"Claims in range", "dist_proc")

        with dist_col2:
            fig = px.histogram(claims_df, x='days_to_receive', nbins=30,
                              title="Distribution of Days to Receive", color_discrete_sequence=['#2ca02c'])
            fig.add_vline(x=30, line_dash="dash", line_color="red", annotation_text="30-Day Target")
            fig.update_layout(xaxis_title="Days to Receive", yaxis_title="Count")

            event2 = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="dist_receive")

            if event2 and event2.selection and event2.selection.points:
                point = event2.selection.points[0]
                if 'x' in point:
                    bin_start = point.get('x', 0)
                    bin_width = (claims_df['days_to_receive'].max() - claims_df['days_to_receive'].min()) / 30
                    bin_end = bin_start + bin_width
                    drill_data = claims_df[(claims_df['days_to_receive'] >= bin_start) &
                                          (claims_df['days_to_receive'] < bin_end)]
                    with st.expander(f"📋 Claims with {int(bin_start)}-{int(bin_end)} days to receive", expanded=True):
                        display_drill_down_data(drill_data, f"Claims in range", "dist_recv")

        # Box plots
        st.markdown("### Processing Time by Category")

        box_col1, box_col2 = st.columns(2)

        with box_col1:
            fig = px.box(claims_df, x='claim_type', y='days_to_process',
                        title="Processing Days by Claim Type", color='claim_type')
            fig.update_layout(showlegend=False, xaxis_title="Claim Type", yaxis_title="Days")

            event3 = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="box_type")

            if event3 and event3.selection and event3.selection.points:
                selected_type = event3.selection.points[0].get('x')
                if selected_type:
                    drill_data = claims_df[claims_df['claim_type'] == selected_type]
                    with st.expander(f"📋 {selected_type} Claims", expanded=True):
                        display_drill_down_data(drill_data, f"{selected_type} claims", "box_type")

        with box_col2:
            fig = px.box(claims_df, x='network_status', y='days_to_process',
                        title="Processing Days by Network Status", color='network_status')
            fig.update_layout(showlegend=False, xaxis_title="Network Status", yaxis_title="Days")

            event4 = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="box_network")

            if event4 and event4.selection and event4.selection.points:
                selected_network = event4.selection.points[0].get('x')
                if selected_network:
                    drill_data = claims_df[claims_df['network_status'] == selected_network]
                    with st.expander(f"📋 {selected_network} Claims", expanded=True):
                        display_drill_down_data(drill_data, f"{selected_network} claims", "box_net")

    # ==================== SEGMENT TAB ====================
    with tab3:
        st.markdown("### Performance by Segment")
        st.caption("Click on any bar to drill down into that segment's claims")

        seg_col1, seg_col2 = st.columns(2)

        with seg_col1:
            group_perf = claims_df.groupby('group_id').agg({
                'days_to_process': 'mean',
                'claim_id': 'count'
            }).reset_index()
            group_perf.columns = ['Group', 'Avg Processing Days', 'Claim Count']
            group_perf = group_perf.sort_values('Avg Processing Days')

            fig = px.bar(group_perf, x='Group', y='Avg Processing Days',
                        title="Average Processing Days by Group",
                        color='Avg Processing Days', color_continuous_scale='RdYlGn_r')
            fig.add_hline(y=14, line_dash="dash", line_color="red")

            event = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="seg_group")

            if event and event.selection and event.selection.points:
                selected_group = event.selection.points[0].get('x')
                if selected_group:
                    drill_data = claims_df[claims_df['group_id'] == selected_group]
                    with st.expander(f"📋 Claims for {selected_group}", expanded=True):
                        display_drill_down_data(drill_data, f"Group {selected_group} claims", "seg_grp")

        with seg_col2:
            package_perf = claims_df.groupby('package').agg({
                'processed_within_14_days': 'mean',
                'claim_id': 'count'
            }).reset_index()
            package_perf.columns = ['Package', '14-Day Compliance', 'Claim Count']
            package_perf['14-Day Compliance'] = (package_perf['14-Day Compliance'] * 100).round(1)

            fig = px.bar(package_perf, x='Package', y='14-Day Compliance',
                        title="14-Day Compliance by Package",
                        color='14-Day Compliance', color_continuous_scale='RdYlGn',
                        text='14-Day Compliance')
            fig.add_hline(y=85, line_dash="dash", line_color="red")
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')

            event2 = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="seg_package")

            if event2 and event2.selection and event2.selection.points:
                selected_pkg = event2.selection.points[0].get('x')
                if selected_pkg:
                    drill_data = claims_df[claims_df['package'] == selected_pkg]
                    with st.expander(f"📋 Claims for {selected_pkg} Package", expanded=True):
                        display_drill_down_data(drill_data, f"{selected_pkg} package claims", "seg_pkg")

        # Heatmap
        st.markdown("### Performance Heatmap")
        st.caption("Click on a cell to see claims for that Group/Claim Type combination")

        heatmap_data = claims_df.groupby(['group_id', 'claim_type']).agg({
            'days_to_process': 'mean'
        }).reset_index()
        heatmap_pivot = heatmap_data.pivot(index='group_id', columns='claim_type', values='days_to_process')

        fig = px.imshow(heatmap_pivot, title="Average Processing Days: Group vs Claim Type",
                       color_continuous_scale='RdYlGn_r', aspect='auto')
        fig.update_layout(xaxis_title="Claim Type", yaxis_title="Group")

        event3 = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="heatmap")

        if event3 and event3.selection and event3.selection.points:
            point = event3.selection.points[0]
            selected_group = heatmap_pivot.index[point.get('y', 0)]
            selected_type = heatmap_pivot.columns[point.get('x', 0)]
            drill_data = claims_df[(claims_df['group_id'] == selected_group) &
                                  (claims_df['claim_type'] == selected_type)]
            with st.expander(f"📋 {selected_group} - {selected_type} Claims", expanded=True):
                display_drill_down_data(drill_data, f"Claims for {selected_group} / {selected_type}", "heatmap")

        # State performance
        st.markdown("### Performance by Provider State")
        state_perf = claims_df.groupby('provider_state').agg({
            'days_to_process': 'mean',
            'claim_id': 'count'
        }).reset_index()
        state_perf.columns = ['State', 'Avg Processing Days', 'Claim Count']

        fig = px.bar(state_perf.sort_values('Avg Processing Days'), x='State', y='Avg Processing Days',
                    title="Average Processing Days by Provider State",
                    color='Avg Processing Days', color_continuous_scale='RdYlGn_r')
        fig.add_hline(y=14, line_dash="dash", line_color="red")

        event4 = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="seg_state")

        if event4 and event4.selection and event4.selection.points:
            selected_state = event4.selection.points[0].get('x')
            if selected_state:
                drill_data = claims_df[claims_df['provider_state'] == selected_state]
                with st.expander(f"📋 Claims for {selected_state}", expanded=True):
                    display_drill_down_data(drill_data, f"Claims from {selected_state}", "seg_state")

    # ==================== FINANCIAL TAB ====================
    with tab4:
        st.markdown("### Financial Analysis")
        st.caption("Click on chart elements to explore underlying claim data")

        fin_col1, fin_col2 = st.columns(2)

        with fin_col1:
            status_financial = filtered_df.groupby('claim_status').agg({
                'billed_amount': 'sum',
                'allowed_amount': 'sum',
                'paid_amount': 'sum',
                'claim_id': 'nunique'
            }).reset_index()
            status_financial.columns = ['Status', 'Billed', 'Allowed', 'Paid', 'Claims']

            fig = px.bar(status_financial, x='Status', y=['Billed', 'Allowed', 'Paid'],
                        title="Financial Summary by Claim Status", barmode='group')

            event = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="fin_status")

            if event and event.selection and event.selection.points:
                selected_status = event.selection.points[0].get('x')
                if selected_status:
                    drill_data = filtered_df[filtered_df['claim_status'] == selected_status]
                    with st.expander(f"📋 {selected_status} Claims", expanded=True):
                        display_drill_down_data(drill_data, f"{selected_status} claims", "fin_stat")

        with fin_col2:
            payment_ratio = filtered_df.groupby('claim_type').agg({
                'billed_amount': 'sum',
                'paid_amount': 'sum'
            }).reset_index()
            payment_ratio['Payment Ratio'] = (payment_ratio['paid_amount'] / payment_ratio['billed_amount'] * 100).round(1)

            fig = px.bar(payment_ratio, x='claim_type', y='Payment Ratio',
                        title="Payment Ratio by Claim Type",
                        color='Payment Ratio', color_continuous_scale='Greens', text='Payment Ratio')
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig.update_layout(xaxis_title="Claim Type", yaxis_title="Payment Ratio (%)")

            event2 = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="fin_ratio")

            if event2 and event2.selection and event2.selection.points:
                selected_type = event2.selection.points[0].get('x')
                if selected_type:
                    drill_data = filtered_df[filtered_df['claim_type'] == selected_type]
                    with st.expander(f"📋 {selected_type} Claims", expanded=True):
                        display_drill_down_data(drill_data, f"{selected_type} claims", "fin_type")

        # Denial analysis
        st.markdown("### Denial Analysis")
        denied_claims = filtered_df[filtered_df['claim_status'] == 'Denied']

        if len(denied_claims) > 0:
            denial_col1, denial_col2 = st.columns(2)

            with denial_col1:
                denial_reasons_df = denied_claims.groupby('denial_reason').size().reset_index(name='count')
                fig = px.pie(denial_reasons_df, values='count', names='denial_reason',
                            title="Denial Reasons Distribution")

                event3 = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="denial_pie")

                if event3 and event3.selection and event3.selection.points:
                    point_idx = event3.selection.points[0].get('pointIndex', 0)
                    if point_idx < len(denial_reasons_df):
                        selected_reason = denial_reasons_df.iloc[point_idx]['denial_reason']
                        drill_data = denied_claims[denied_claims['denial_reason'] == selected_reason]
                        with st.expander(f"📋 Claims denied for: {selected_reason}", expanded=True):
                            display_drill_down_data(drill_data, f"Denied claims", "denial_reason")

            with denial_col2:
                denial_by_type = denied_claims.groupby('claim_type').size().reset_index(name='count')
                fig = px.bar(denial_by_type, x='claim_type', y='count',
                            title="Denials by Claim Type", color='claim_type')
                fig.update_layout(showlegend=False)

                event4 = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="denial_type")

                if event4 and event4.selection and event4.selection.points:
                    selected_type = event4.selection.points[0].get('x')
                    if selected_type:
                        drill_data = denied_claims[denied_claims['claim_type'] == selected_type]
                        with st.expander(f"📋 Denied {selected_type} Claims", expanded=True):
                            display_drill_down_data(drill_data, f"Denied {selected_type}", "denial_bytype")
        else:
            st.info("No denied claims in the current filter selection.")

        # Monthly financial trend
        st.markdown("### Monthly Financial Trend")
        filtered_df['paid_month'] = filtered_df['paid_date'].dt.to_period('M').astype(str)
        monthly_financial = filtered_df.groupby('paid_month').agg({
            'billed_amount': 'sum',
            'paid_amount': 'sum'
        }).reset_index()

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=monthly_financial['paid_month'], y=monthly_financial['billed_amount'],
                                 mode='lines+markers', name='Billed', line=dict(color='#ff7f0e')))
        fig.add_trace(go.Scatter(x=monthly_financial['paid_month'], y=monthly_financial['paid_amount'],
                                 mode='lines+markers', name='Paid', line=dict(color='#2ca02c')))
        fig.update_layout(title="Monthly Billed vs Paid Amounts", xaxis_title="Month", yaxis_title="Amount ($)")

        event5 = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="fin_trend")

        if event5 and event5.selection and event5.selection.points:
            selected_month = event5.selection.points[0].get('x')
            if selected_month:
                drill_data = filtered_df[filtered_df['paid_month'] == selected_month]
                with st.expander(f"📋 Claims for {selected_month}", expanded=True):
                    display_drill_down_data(drill_data, f"Claims paid in {selected_month}", "fin_monthly")

    # ==================== CLAIMS DETAIL TAB ====================
    with tab5:
        st.markdown("### Claims Detail View")

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

        show_cols = st.multiselect(
            "Select columns to display",
            options=detail_df.columns.tolist(),
            default=['claim_id', 'line_number', 'member_id', 'claim_type', 'first_service_date',
                    'received_date', 'paid_date', 'days_to_process', 'billed_amount',
                    'paid_amount', 'claim_status']
        )

        sort_col1, sort_col2 = st.columns(2)
        with sort_col1:
            sort_by = st.selectbox("Sort by", show_cols,
                                   index=show_cols.index('days_to_process') if 'days_to_process' in show_cols else 0)
        with sort_col2:
            sort_order = st.radio("Order", ["Descending", "Ascending"], horizontal=True)

        display_df = detail_df[show_cols].sort_values(sort_by, ascending=(sort_order == "Ascending"))

        st.dataframe(display_df.head(1000), use_container_width=True, hide_index=True)
        st.caption(f"Showing {min(1000, len(display_df)):,} of {len(display_df):,} records")

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
        """<div style='text-align: center; color: #666;'>
        <p>Claims Timeliness Dashboard | Demo Application with Synthetic Data</p>
        <p>Built with Streamlit | Click any chart to drill down!</p>
        </div>""",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
