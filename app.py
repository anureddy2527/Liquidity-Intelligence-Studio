

import os
import random
import string

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

try:
    from snowflake.snowpark import Session
    from snowflake.snowpark.context import get_active_session
except Exception:  # pragma: no cover - optional dependency path
    Session = None
    get_active_session = None


st.set_page_config(
    page_title="Liquidity Intelligence Studio",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)


def build_demo_lcr_data():
    return pd.DataFrame(
        [
            {"DAY_NUMBER": 1, "LCR": 1.18, "HQLA": 125000000, "TOTAL_NET_CASH_OUTFLOWS": 106000000},
            {"DAY_NUMBER": 2, "LCR": 1.16, "HQLA": 123500000, "TOTAL_NET_CASH_OUTFLOWS": 107000000},
            {"DAY_NUMBER": 3, "LCR": 1.14, "HQLA": 122000000, "TOTAL_NET_CASH_OUTFLOWS": 108000000},
            {"DAY_NUMBER": 4, "LCR": 1.12, "HQLA": 121000000, "TOTAL_NET_CASH_OUTFLOWS": 109000000},
            {"DAY_NUMBER": 5, "LCR": 1.10, "HQLA": 120000000, "TOTAL_NET_CASH_OUTFLOWS": 110000000},
        ]
    )


def build_demo_hqla_breakdown():
    return pd.DataFrame(
        [
            {"CATEGORY": "Cash", "AMOUNT": 42000000},
            {"CATEGORY": "Government Bonds", "AMOUNT": 36000000},
            {"CATEGORY": "Corporate Bonds", "AMOUNT": 25000000},
            {"CATEGORY": "Central Bank Eligible", "AMOUNT": 22000000},
        ]
    )


def build_demo_what_if_data():
    return pd.DataFrame(
        [
            {"WHAT_IF_ID": 101, "WHAT_IF_NAME": "Reduce HQLA outflows", "REF_TBL": "CASH_OUTFLOWS", "COL": "OUTFLOW_AMOUNT", "VAL": 0.95, "FACTOR": 0.95},
            {"WHAT_IF_ID": 102, "WHAT_IF_NAME": "Increase inflows", "REF_TBL": "CASH_INFLOWS", "COL": "INFLOW_AMOUNT", "VAL": 1.10, "FACTOR": 1.10},
        ]
    )


def build_demo_forecast_data():
    return pd.DataFrame(
        [
            {"DAY": 1, "LCR_FORECAST": 1.18},
            {"DAY": 7, "LCR_FORECAST": 1.15},
            {"DAY": 14, "LCR_FORECAST": 1.12},
            {"DAY": 21, "LCR_FORECAST": 1.10},
            {"DAY": 30, "LCR_FORECAST": 1.08},
        ]
    )


def build_demo_risk_grid():
    return pd.DataFrame(
        [
            {"CATEGORY": "Funding Mix", "RISK_SCORE": 32},
            {"CATEGORY": "Collateral Haircuts", "RISK_SCORE": 48},
            {"CATEGORY": "Outflow Concentration", "RISK_SCORE": 57},
            {"CATEGORY": "Market Volatility", "RISK_SCORE": 41},
        ]
    )


def build_live_dashboard_snapshot():
    return {
        "lcr": 1.18,
        "hqla": 125000000,
        "outflows": 106000000,
        "status": "Healthy",
        "timestamp": "Live demo feed",
    }


def build_live_alerts():
    return pd.DataFrame(
        [
            {"SEVERITY": "Info", "MESSAGE": "Liquidity buffer remains above the regulatory floor."},
            {"SEVERITY": "Watch", "MESSAGE": "Short-term funding mix is trending tighter."},
            {"SEVERITY": "Info", "MESSAGE": "HQLA composition is diversified across core assets."},
        ]
    )


def build_connection_status_message(session_source, has_credentials=False):
    if session_source in {"active-session", "configured-connection"}:
        return "Live Snowflake connectivity is enabled and the dashboard is drawing from the live dataset."
    return "The dashboard is currently running in a polished analytics demo mode with curated liquidity metrics, scenario models, and executive-ready visuals."


def resolve_snowflake_config(state=None, env=None, secrets=None):
    env = env or os.environ
    secrets = secrets or {}
    streamlit_secrets = getattr(st, "secrets", {})
    if isinstance(streamlit_secrets, dict):
        secrets = {**streamlit_secrets, **secrets}
    nested = secrets.get("snowflake") if isinstance(secrets.get("snowflake"), dict) else {}
    config = {
        "account": (state or {}).get("sf_account") or env.get("SNOWFLAKE_ACCOUNT") or secrets.get("account") or nested.get("account") or secrets.get("SNOWFLAKE_ACCOUNT"),
        "user": (state or {}).get("sf_user") or env.get("SNOWFLAKE_USER") or secrets.get("user") or nested.get("user") or secrets.get("SNOWFLAKE_USER"),
        "password": (state or {}).get("sf_password") or env.get("SNOWFLAKE_PASSWORD") or secrets.get("password") or nested.get("password") or secrets.get("SNOWFLAKE_PASSWORD"),
        "warehouse": (state or {}).get("sf_warehouse") or env.get("SNOWFLAKE_WAREHOUSE") or secrets.get("warehouse") or nested.get("warehouse") or secrets.get("SNOWFLAKE_WAREHOUSE"),
        "database": (state or {}).get("sf_database") or env.get("SNOWFLAKE_DATABASE") or secrets.get("database") or nested.get("database") or secrets.get("SNOWFLAKE_DATABASE"),
        "schema": (state or {}).get("sf_schema") or env.get("SNOWFLAKE_SCHEMA") or secrets.get("schema") or nested.get("schema") or secrets.get("SNOWFLAKE_SCHEMA"),
        "role": (state or {}).get("sf_role") or env.get("SNOWFLAKE_ROLE") or secrets.get("role") or nested.get("role") or secrets.get("SNOWFLAKE_ROLE"),
    }
    return {k: v for k, v in config.items() if v is not None}


def get_snowflake_session(state=None):
    if get_active_session is None:
        return None, "Snowpark is unavailable in this environment"

    try:
        session = get_active_session()
        if session is not None:
            return session, "active-session"
    except Exception:
        pass

    try:
        if Session is None:
            return None, "Snowflake session connector is unavailable"

        state = state or {}
        secret_map = resolve_snowflake_config(state)
        if all(secret_map.values()):
            account_candidates = []
            account = secret_map.get("account")
            if account:
                raw = str(account).strip()
                account_candidates.append(raw)
                account_candidates.append(raw.replace("-", ""))
                if "." not in raw and ".snowflakecomputing.com" not in raw:
                    account_candidates.append(f"{raw}.snowflakecomputing.com")
                    account_candidates.append(f"{raw}.us-east-1.azure.snowflakecomputing.com")
            for candidate in account_candidates or [None]:
                attempt = dict(secret_map)
                if candidate:
                    attempt["account"] = candidate
                try:
                    session = Session.builder.configs(attempt).create()
                    return session, "configured-connection"
                except Exception as exc:
                    last_error = exc
            return None, f"connection failed: {last_error}"
    except Exception as exc:
        return None, f"connection failed: {exc}"

    return None, "demo-mode"


for key, default in {
    "sf_account": os.getenv("SNOWFLAKE_ACCOUNT", ""),
    "sf_user": os.getenv("SNOWFLAKE_USER", ""),
    "sf_password": os.getenv("SNOWFLAKE_PASSWORD", ""),
    "sf_warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", ""),
    "sf_database": os.getenv("SNOWFLAKE_DATABASE", ""),
    "sf_schema": os.getenv("SNOWFLAKE_SCHEMA", ""),
    "sf_role": os.getenv("SNOWFLAKE_ROLE", ""),
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

if "sf_session" not in st.session_state:
    st.session_state.sf_session = None
if "sf_session_source" not in st.session_state:
    st.session_state.sf_session_source = "demo-mode"

session = st.session_state.sf_session
session_source = st.session_state.sf_session_source
if session is None:
    session, session_source = get_snowflake_session(st.session_state)
    if session is not None:
        st.session_state.sf_session = session
        st.session_state.sf_session_source = session_source
    else:
        st.session_state.sf_session_source = session_source

st.sidebar.subheader("Data source")
st.sidebar.caption("Connect Snowflake for live data, or continue with the curated demo experience.")
with st.sidebar.expander("Connect live data", expanded=False):
    st.text_input("Account", key="sf_account")
    st.text_input("User", key="sf_user")
    st.text_input("Password", key="sf_password", type="password")
    st.text_input("Warehouse", key="sf_warehouse")
    st.text_input("Database", key="sf_database")
    st.text_input("Schema", key="sf_schema")
    st.text_input("Role", key="sf_role")

    if st.button("Connect", use_container_width=True):
        session, session_source = get_snowflake_session(st.session_state)
        if session is not None:
            st.session_state.sf_session = session
            st.session_state.sf_session_source = session_source
            st.sidebar.success("Connected to Snowflake")
            st.rerun()
        else:
            st.session_state.sf_session = None
            st.session_state.sf_session_source = session_source
            st.sidebar.info("Live Snowflake access is unavailable right now. The dashboard remains fully interactive in curated demo mode.")

    if st.button("Use demo data", use_container_width=True):
        st.session_state.sf_session = None
        st.session_state.sf_session_source = "demo-mode"
        st.rerun()

db = "LIQUIDITY_RISK_DB"

connection_has_credentials = any(
    [
        st.session_state.get("sf_account"),
        st.session_state.get("sf_user"),
        st.session_state.get("sf_password"),
        st.session_state.get("sf_warehouse"),
        st.session_state.get("sf_database"),
        st.session_state.get("sf_schema"),
        st.session_state.get("sf_role"),
    ]
)
connection_status_message = build_connection_status_message(session_source, has_credentials=connection_has_credentials)
if session is None:
    st.sidebar.info(f"Analytics mode: Curated demo dashboard\n\n{connection_status_message}")
else:
    st.sidebar.success(f"Snowflake connection: {session_source}")

page = st.sidebar.selectbox(
    "Select Page",
    ["LCR Dashboard", "What-if Scenarios Complex", "Ask the Agent", "Executive Overview", "Real-Time Operations"],
)

if page == "LCR Dashboard":
    st.header("💼 Liquidity Intelligence Studio")
    st.markdown("A portfolio-ready Snowflake + Streamlit app for monitoring liquidity risk, simulating stress scenarios, and demonstrating modern data engineering skills.")

    if session is None:
        st.success(connection_status_message)
        st.caption("This portfolio-ready experience highlights liquidity-risk analytics, stress scenarios, and executive reporting in a polished demo format.")
        lcr_data = build_demo_lcr_data()
        hqla_breakdown = build_demo_hqla_breakdown()
    else:
        try:
            lcr_data = session.sql(f"""
            SELECT *
            FROM {db}.PRESENTATION.LCR
            WHERE created_timestamp IN (SELECT max(created_timestamp) FROM {db}.PRESENTATION.LCR)
            ORDER BY day_number
            """).to_pandas()
            hqla_breakdown = pd.DataFrame(
                [
                    {"CATEGORY": "Cash", "AMOUNT": 42000000},
                    {"CATEGORY": "Government Bonds", "AMOUNT": 36000000},
                    {"CATEGORY": "Corporate Bonds", "AMOUNT": 25000000},
                    {"CATEGORY": "Central Bank Eligible", "AMOUNT": 22000000},
                ]
            )
        except Exception as exc:
            st.warning(f"Live Snowflake query failed: {exc}")
            lcr_data = build_demo_lcr_data()
            hqla_breakdown = build_demo_hqla_breakdown()

    if not lcr_data.empty:
        today_data = lcr_data[lcr_data["DAY_NUMBER"] == 1].iloc[0] if len(lcr_data[lcr_data["DAY_NUMBER"] == 1]) > 0 else None

        if today_data is not None:
            st.subheader("📊 Executive Snapshot")
            lcr_value = float(today_data["LCR"])
            headroom = lcr_value - 1.0

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("LCR", f"{lcr_value:,.2f}", delta=f"{headroom:.2%} above floor")
            with col2:
                st.metric("HQLA", f"${today_data['HQLA']:,.0f}")
            with col3:
                st.metric("30-Day Net Cash Outflows", f"${today_data['TOTAL_NET_CASH_OUTFLOWS']:,.0f}")
            with col4:
                status = "Healthy" if lcr_value >= 1.1 else "Watch" if lcr_value >= 1.0 else "Critical"
                st.metric("Risk Status", status)

            st.subheader("📈 Executive Visual Summary")
            gauge_fig = go.Figure(
                go.Indicator(
                    mode="gauge+number+delta",
                    value=lcr_value,
                    domain={"x": [0, 1], "y": [0, 1]},
                    title={"text": "Current LCR Position"},
                    delta={"reference": 1.0, "increasing": {"color": "green"}, "decreasing": {"color": "red"}},
                    gauge={
                        "axis": {"range": [0, 1.4]},
                        "bar": {"color": "#2563eb"},
                        "steps": [
                            {"range": [0, 1.0], "color": "#fee2e2"},
                            {"range": [1.0, 1.2], "color": "#fef3c7"},
                            {"range": [1.2, 1.4], "color": "#dcfce7"},
                        ],
                        "threshold": {"line": {"color": "red", "width": 4}, "thickness": 0.75, "value": 1.0},
                    },
                )
            )
            gauge_fig.update_layout(height=320)
            st.plotly_chart(gauge_fig, use_container_width=True)

            st.markdown("### 🔍 What this dashboard shows")
            st.markdown("- Live or simulated liquidity metrics for regulatory compliance")
            st.markdown("- Trend visualization for LCR over time")
            st.markdown("- A scenario simulator for management discussions and stress testing")
            st.markdown("- A strong example of a Snowpark + Streamlit analytics product for interviews and portfolios")

            st.subheader("📈 LCR Trend")
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=lcr_data["DAY_NUMBER"],
                    y=lcr_data["LCR"],
                    mode="lines+markers",
                    name="LCR",
                    line=dict(color="#2563eb", width=3),
                    marker=dict(size=8),
                )
            )
            fig.add_hline(y=1.0, line_dash="dash", line_color="red", annotation_text="Regulatory Floor")
            fig.update_layout(height=450, hovermode="x unified", xaxis_title="Day Number", yaxis_title="LCR Ratio")
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("🧭 Control Tower")
            forecast_data = build_demo_forecast_data()
            forecast_fig = px.line(
                forecast_data,
                x="DAY",
                y="LCR_FORECAST",
                markers=True,
                title="30-Day LCR Forecast",
                labels={"DAY": "Day", "LCR_FORECAST": "Forecasted LCR"},
            )
            forecast_fig.add_hline(y=1.0, line_dash="dash", line_color="red", annotation_text="Floor")
            forecast_fig.update_layout(height=320)
            st.plotly_chart(forecast_fig, use_container_width=True)

            col_left, col_right = st.columns([1.1, 0.9])
            with col_left:
                st.subheader("🧾 HQLA Composition")
                bar_fig = px.bar(
                    hqla_breakdown,
                    x="CATEGORY",
                    y="AMOUNT",
                    color="CATEGORY",
                    title="High-Quality Liquid Assets Mix",
                )
                bar_fig.update_layout(height=350, showlegend=False)
                st.plotly_chart(bar_fig, use_container_width=True)

            with col_right:
                st.subheader("🧠 Risk Interpretation")
                if lcr_value >= 1.1:
                    st.success("The buffer above the regulatory floor looks comfortable and supports growth scenarios.")
                elif lcr_value >= 1.0:
                    st.warning("The balance sheet is compliant but close to the minimum threshold; contingency planning is advisable.")
                else:
                    st.error("The current profile breaches the minimum requirement and needs immediate remediation.")

                risk_grid = build_demo_risk_grid()
                risk_fig = px.scatter(
                    risk_grid,
                    x="CATEGORY",
                    y="RISK_SCORE",
                    size="RISK_SCORE",
                    color="RISK_SCORE",
                    title="Risk Watchlist",
                )
                risk_fig.update_layout(height=300, showlegend=False)
                st.plotly_chart(risk_fig, use_container_width=True)

                with st.expander("📋 View Raw Data", expanded=False):
                    display_df = lcr_data.copy()
                    display_df["TOTAL_NET_CASH_OUTFLOWS"] = display_df["TOTAL_NET_CASH_OUTFLOWS"].map(lambda x: f"${x:,.0f}")
                    display_df["HQLA"] = display_df["HQLA"].map(lambda x: f"${x:,.0f}")
                    st.dataframe(display_df, use_container_width=True)
    else:
        st.warning("No LCR data available. Please ensure the LCR table is populated.")

    if st.button("� Refresh Dashboard", type="primary", use_container_width=True):
        with st.spinner("Refreshing the latest liquidity metrics..."):
            try:
                st.rerun()
            except Exception as exc:
                st.error(f"Refresh failed: {exc}")

elif page == "What-if Scenarios Complex":
    st.header("🔮 Scenario Studio")
    st.markdown("Model a few stress-test levers and immediately see how they influence liquidity resilience.")

    lcr_data = build_demo_lcr_data()
    if session is not None:
        try:
            lcr_data = session.sql(f"""
            SELECT *
            FROM {db}.PRESENTATION.LCR
            WHERE created_timestamp IN (SELECT max(created_timestamp) FROM {db}.PRESENTATION.LCR)
            ORDER BY day_number
            """).to_pandas()
        except Exception as exc:
            st.warning(f"Live data unavailable; using demo values: {exc}")

    baseline_lcr = float(lcr_data[lcr_data["DAY_NUMBER"] == 1].iloc[0]["LCR"]) if not lcr_data.empty else 1.18

    st.subheader("🎛️ Interactive Stress Test")
    col1, col2, col3 = st.columns(3)
    with col1:
        inflow_factor = st.slider("Inflow multiplier", 0.8, 1.3, 1.0, 0.05)
    with col2:
        outflow_factor = st.slider("Outflow multiplier", 0.8, 1.3, 1.0, 0.05)
    with col3:
        hqla_factor = st.slider("HQLA availability factor", 0.8, 1.2, 1.0, 0.05)

    simulated_lcr = max(0.5, baseline_lcr * (1 + (inflow_factor - 1) * 0.12 - (outflow_factor - 1) * 0.13 + (hqla_factor - 1) * 0.08))
    delta = simulated_lcr - baseline_lcr

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Baseline LCR", f"{baseline_lcr:.2f}")
    with col_b:
        st.metric("Simulated LCR", f"{simulated_lcr:.2f}", delta=f"{delta:.2f}")
    with col_c:
        st.metric("Stress View", "Comfortable" if simulated_lcr >= 1.1 else "Watch" if simulated_lcr >= 1.0 else "Critical")

    fig = go.Figure()
    fig.add_trace(go.Bar(x=["Baseline", "Stress Scenario"], y=[baseline_lcr, simulated_lcr], marker_color=["#94a3b8", "#2563eb"]))
    fig.update_layout(height=320, yaxis_title="LCR Ratio", xaxis_title="Scenario")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📚 Demo What-if Definitions")
    what_if_ids_df = build_demo_what_if_data()
    if session is not None:
        try:
            what_if_ids_df = session.table(f"{db}.RAW.WHAT_IF_DEFINITIONS_LOOKUP")\
                .select("WHAT_IF_ID", "WHAT_IF_NAME", "REF_TBL", "COL", "VAL", "FACTOR")\
                .distinct()\
                .order_by("WHAT_IF_ID", "REF_TBL", "COL")\
                .to_pandas()
        except Exception as exc:
            st.info(f"Live Snowflake definitions were not available, so the demo catalog is shown instead: {exc}")

    what_if_id = st.selectbox("Select a what-if definition", options=list(what_if_ids_df["WHAT_IF_ID"].tolist()))
    filtered_df = what_if_ids_df[what_if_ids_df["WHAT_IF_ID"] == what_if_id]
    st.dataframe(filtered_df, use_container_width=True)

    st.caption("This page is designed to look like a business-facing stress-testing product that would be impressive in a data portfolio or interview demo.")

elif page == "Executive Overview":
    st.header("📊 Executive Overview")
    st.markdown("A multi-panel view for leadership-style liquidity monitoring and scenario storytelling.")

    lcr_data = build_demo_lcr_data()
    hqla_breakdown = build_demo_hqla_breakdown()

    if session is not None:
        try:
            lcr_data = session.sql(f"""
            SELECT *
            FROM {db}.PRESENTATION.LCR
            WHERE created_timestamp IN (SELECT max(created_timestamp) FROM {db}.PRESENTATION.LCR)
            ORDER BY day_number
            """).to_pandas()
        except Exception as exc:
            st.info(f"Live Snowflake data unavailable; using demo values: {exc}")

    today_data = lcr_data[lcr_data["DAY_NUMBER"] == 1].iloc[0] if not lcr_data.empty else None

    if today_data is not None:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("LCR", f"{today_data['LCR']:,.2f}")
        with col2:
            st.metric("HQLA", f"${today_data['HQLA']:,.0f}")
        with col3:
            st.metric("30-Day Outflows", f"${today_data['TOTAL_NET_CASH_OUTFLOWS']:,.0f}")
        with col4:
            status = "Healthy" if today_data['LCR'] >= 1.1 else "Watch" if today_data['LCR'] >= 1.0 else "Critical"
            st.metric("Status", status)

    st.subheader("📈 Multi-Dashboard Snapshot")
    col_left, col_right = st.columns(2)
    with col_left:
        trend_fig = px.line(
            lcr_data,
            x="DAY_NUMBER",
            y="LCR",
            title="LCR Trend",
            labels={"DAY_NUMBER": "Day Number", "LCR": "LCR Ratio"},
            markers=True,
        )
        trend_fig.add_hline(y=1.0, line_dash="dash", line_color="red", annotation_text="Floor")
        st.plotly_chart(trend_fig, use_container_width=True)

    with col_right:
        hqla_fig = px.pie(hqla_breakdown, values="AMOUNT", names="CATEGORY", title="HQLA Composition")
        st.plotly_chart(hqla_fig, use_container_width=True)

    st.subheader("🧠 Leadership Summary")
    st.markdown("- Liquidity remains above the regulatory threshold")
    st.markdown("- HQLA composition is diversified across core liquid assets")
    st.markdown("- The scenario simulator highlights how inflow and outflow changes affect resilience")
    st.caption("This executive-style overview is designed to make the app look more like a real enterprise dashboard for interviews and portfolio demos.")

elif page == "Real-Time Operations":
    st.header("⚡ Real-Time Operations Center")
    st.markdown("A live-ops style view that looks like a production monitoring dashboard for a finance data platform.")

    snapshot = build_live_dashboard_snapshot()
    alerts = build_live_alerts()

    st.subheader("📡 Current Signal")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("LCR", f"{snapshot['lcr']:.2f}")
    with col2:
        st.metric("HQLA", f"${snapshot['hqla']:,.0f}")
    with col3:
        st.metric("Net Outflows", f"${snapshot['outflows']:,.0f}")
    with col4:
        st.metric("Status", snapshot["status"])

    st.caption(f"Updated: {snapshot['timestamp']}")

    st.subheader("🚨 Operational Alerts")
    st.dataframe(alerts, use_container_width=True)

    st.subheader("📈 Streaming-style Trend")
    trend_df = build_demo_lcr_data().copy()
    trend_fig = px.line(
        trend_df,
        x="DAY_NUMBER",
        y="LCR",
        markers=True,
        title="Live liquidity trend",
        labels={"DAY_NUMBER": "Observation", "LCR": "LCR Ratio"},
    )
    trend_fig.update_layout(height=320)
    st.plotly_chart(trend_fig, use_container_width=True)

    st.markdown("### Why this is strong for a resume")
    st.markdown("- Demonstrates data engineering + dashboard design + business storytelling")
    st.markdown("- Shows how analytics can be packaged as a real-time operations experience")
    st.markdown("- Gives you a polished story for interviews, GitHub, and LinkedIn")

elif page == "Ask the Agent":
    st.header("🤖 Ask the Liquidity Forecast Agent")
    st.markdown("Ask natural language questions about liquidity positions, LCR forecasts, HQLA composition, and more.")

    st.info("This experience works best when the app is running inside Snowflake with Cortex Analyst enabled. In demo mode, you can still explore a polished mock conversation experience.")

    # Initialize session state for chat history and conversation ID
    if "agent_messages" not in st.session_state:
        st.session_state.agent_messages = []
    if "agent_conversation_id" not in st.session_state:
        st.session_state.agent_conversation_id = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    
    # Sample questions as clickable buttons
    sample_questions = [
        "What's LCR today and headroom vs floor?",
        "Why did LCR move? What are top 3 causes?",
        "7/30 days - where's LCR heading?",
        "Intraday alerts: Any surprises now?",
        "DQ - is our data reliable today? Recon status? Any missing fields?",
        "Governance & overrides - who approved changes?"
    ]
    
    # Initialize pending question in session state
    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None
    
    with st.expander("💡 Sample Questions", expanded=False):
        for q in sample_questions:
            if st.button(q, key=f"sample_{q}", use_container_width=True):
                st.session_state.pending_question = q
                st.rerun()
    
    # Clear chat button
    if st.button("🗑️ Clear Chat", use_container_width=False):
        st.session_state.agent_messages = []
        st.session_state.agent_conversation_id = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        st.rerun()
    
    # Display chat history
    for message in st.session_state.agent_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input - check for pending question from sample buttons
    user_input = st.chat_input("Ask a question about liquidity...")
    
    # Use pending question if set
    if st.session_state.pending_question:
        user_input = st.session_state.pending_question
        st.session_state.pending_question = None
    
    if user_input:
        st.session_state.agent_messages.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                if session is None:
                    question = user_input.lower()
                    if "lcr" in question:
                        answer = (
                            "In demo mode, the latest liquidity profile shows an LCR of 1.18, which is comfortably above the 1.00 regulatory floor. "
                            "The main watch item is that the buffer is narrowing gradually over the forecast horizon."
                        )
                    elif "hqla" in question or "composition" in question:
                        answer = (
                            "The sample HQLA mix is led by cash and government bonds, with additional support from corporate and central-bank-eligible assets. "
                            "This is a strong example of a balance sheet that would be attractive for stress testing and executive review."
                        )
                    elif "what-if" in question or "scenario" in question or "stress" in question:
                        answer = (
                            "A mild increase in inflows and a decrease in outflows would improve the scenario outcome, while adverse funding conditions would compress the LCR buffer. "
                            "This is the kind of analysis that makes the scenario simulator useful for management discussions."
                        )
                    else:
                        answer = (
                            "I can help frame a liquidity answer in demo mode. The current dashboard suggests that liquidity remains healthy, but the margin above the floor should be monitored closely."
                        )

                    st.markdown(answer)
                    st.session_state.agent_messages.append({"role": "assistant", "content": answer})
                else:
                    try:
                        import json
                        import _snowflake

                        semantic_view = f"{db}.PUBLIC.LIQUIDITY_SV"
                        payload = {
                            "semantic_view": semantic_view,
                            "messages": [{"role": "user", "content": [{"type": "text", "text": user_input}]}],
                        }

                        response = _snowflake.send_snow_api_request(
                            "POST",
                            "/api/v2/cortex/analyst/message",
                            {},
                            {},
                            payload,
                            {},
                            120000,
                        )

                        content = ""
                        if response:
                            if isinstance(response, str):
                                try:
                                    result = json.loads(response)
                                    if isinstance(result, dict) and "answer" in result:
                                        content = result["answer"]
                                    else:
                                        content = result
                                except Exception:
                                    content = response
                            elif isinstance(response, dict):
                                content = response.get("answer") or response.get("content") or response
                            else:
                                content = str(response)

                        if content:
                            st.markdown(content)
                            st.session_state.agent_messages.append({"role": "assistant", "content": content})
                        else:
                            fallback = "No live response was generated. Please verify your Snowflake Cortex setup and semantic view."
                            st.info(fallback)
                            st.session_state.agent_messages.append({"role": "assistant", "content": fallback})
                    except Exception as exc:
                        fallback = f"Cortex Analyst is not available in this environment: {exc}"
                        st.warning(fallback)
                        st.session_state.agent_messages.append({"role": "assistant", "content": fallback})