import os
import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="XORA Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# PROFESSIONAL UI / CSS
# ============================================================

st.markdown(
    """
    <style>
        /* ====================================================
           GLOBAL
           ==================================================== */

        .stApp {
            background: #0b0f14;
            color: #e8edf3;
        }

        .main .block-container {
            max-width: 1450px;
            padding-top: 1.5rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3 {
            color: #f4f7fa !important;
            letter-spacing: -0.4px;
        }

        [data-testid="stCaptionContainer"] p {
            color: #7f8b98 !important;
        }

        hr {
            border-color: #1d2731 !important;
        }

        /* ====================================================
           SIDEBAR
           ==================================================== */

        section[data-testid="stSidebar"] {
            background: #080c11;
            border-right: 1px solid #1b232d;
        }

        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            color: #8a96a3;
        }

        section[data-testid="stSidebar"] .stRadio label {
            color: #b9c3cd !important;
        }

        /* ====================================================
           HEADER
           ==================================================== */

        .xora-brand {
            font-size: 2.25rem;
            font-weight: 750;
            color: #ffffff;
            letter-spacing: -1px;
            line-height: 1.1;
            margin-bottom: 0.35rem;
        }

        .xora-subtitle {
            color: #7f8b98;
            font-size: 0.94rem;
            margin-bottom: 0.25rem;
        }

        .live-badge {
            display: inline-block;
            color: #39d98a;
            background: rgba(46, 204, 113, 0.08);
            border: 1px solid rgba(46, 204, 113, 0.28);
            border-radius: 999px;
            padding: 0.35rem 0.75rem;
            font-size: 0.72rem;
            font-weight: 650;
            letter-spacing: 0.5px;
        }

        /* ====================================================
           KPI CARDS
           ==================================================== */

        div[data-testid="stMetric"] {
            background: #11171e;
            border: 1px solid #202a35;
            border-radius: 12px;
            padding: 1rem 1.1rem;
            min-height: 105px;
        }

        div[data-testid="stMetricLabel"] {
            color: #7f8b99 !important;
        }

        div[data-testid="stMetricValue"] {
            color: #f5f7fa !important;
        }

        div[data-testid="stMetricDelta"] {
            color: #71808e !important;
        }

        /* ====================================================
           NATIVE CONTAINERS / CARDS
           ==================================================== */

        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: #10161d;
            border-color: #202a35 !important;
            border-radius: 12px;
        }

        /* ====================================================
           TABLES
           ==================================================== */

        div[data-testid="stDataFrame"] {
            border: 1px solid #202a35;
            border-radius: 10px;
            overflow: hidden;
        }

        /* ====================================================
           INPUTS / BUTTONS
           ==================================================== */

        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div {
            background: #11171e;
            border-color: #27313d;
        }

        .stButton > button {
            border-radius: 8px;
            border: 1px solid #27313d;
            background: #11171e;
            color: #dce3e9;
        }

        .stButton > button:hover {
            border-color: #3b4856;
            color: #ffffff;
        }

        /* ====================================================
           ALERTS
           ==================================================== */

        div[data-testid="stAlert"] {
            border-radius: 10px;
        }

        /* ====================================================
           FOOTER
           ==================================================== */

        .footer-note {
            color: #4e5a66;
            text-align: center;
            font-size: 0.72rem;
            padding-top: 2rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# DATABASE CONNECTION
# ============================================================

DATABASE_URL = os.getenv("NEON_STRING")

if not DATABASE_URL:
    try:
        DATABASE_URL = st.secrets["NEON_STRING"]
    except Exception:
        DATABASE_URL = None

if not DATABASE_URL:
    st.error("NEON_STRING is not configured.")
    st.stop()


def get_connection():
    return psycopg2.connect(DATABASE_URL)


@st.cache_data(ttl=300)
def load_table(table_name):
    allowed_tables = {
        "bounty_current",
        "bounty_history",
        "leaderboard_current",
        "leaderboard_history",
    }

    if table_name not in allowed_tables:
        raise ValueError("Invalid table name.")

    conn = get_connection()

    try:
        return pd.read_sql(
            f"SELECT * FROM {table_name}",
            conn,
        )
    finally:
        conn.close()


# ============================================================
# LOAD DATA
# ============================================================

try:
    bounty_current = load_table("bounty_current")
    bounty_history = load_table("bounty_history")
    leaderboard_current = load_table("leaderboard_current")
    leaderboard_history = load_table("leaderboard_history")

except Exception as error:
    st.error(f"Database connection failed: {error}")
    st.stop()


# ============================================================
# DATA HELPERS
# ============================================================

def numeric_series(df, column):
    if column not in df.columns:
        return pd.Series(dtype="float64")

    return pd.to_numeric(
        df[column],
        errors="coerce",
    )


def numeric_sum(df, column):
    values = numeric_series(df, column).dropna()

    return float(values.sum()) if not values.empty else 0.0


def numeric_mean(df, column):
    values = numeric_series(df, column).dropna()

    return float(values.mean()) if not values.empty else 0.0


def numeric_count(df, column):
    values = numeric_series(df, column).dropna()

    return int(values.sum()) if not values.empty else 0


def style_chart(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            color="#aab4bf"
        ),
        margin=dict(
            l=20,
            r=20,
            t=55,
            b=25,
        ),
        title_font=dict(
            size=15,
            color="#e8edf2",
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
        ),
    )

    fig.update_xaxes(
        gridcolor="#1d2731",
        zerolinecolor="#1d2731",
    )

    fig.update_yaxes(
        gridcolor="#1d2731",
        zerolinecolor="#1d2731",
    )

    return fig


def safe_columns(df, columns):
    return [
        column
        for column in columns
        if column in df.columns
    ]


def show_table(df, columns):
    columns = safe_columns(
        df,
        columns,
    )

    if columns:
        st.dataframe(
            df[columns],
            width="stretch",
            hide_index=True,
        )
    else:
        st.info(
            "No displayable columns are available."
        )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("### ⚡ XORA")

    st.caption(
        "Intelligence Platform"
    )

    page = st.radio(
        "NAVIGATION",
        [
            "Overview",
            "Bounty Intelligence",
            "Contributor Intelligence",
            "Historical Intelligence",
            "Pipeline",
        ],
    )

    st.divider()

    if st.button(
        "↻  Refresh Data",
        width="stretch",
    ):
        st.cache_data.clear()
        st.rerun()

    st.divider()

    st.caption(
        "DATA SOURCE"
    )

    st.write(
        "Neon PostgreSQL"
    )


# ============================================================
# GLOBAL HEADER
# ============================================================

header_left, header_right = st.columns(
    [5, 1]
)

with header_left:

    st.markdown(
        '<div class="xora-brand">'
        'XORA Intelligence'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="xora-subtitle">'
        'Automated bounty, contributor and marketplace intelligence'
        '</div>',
        unsafe_allow_html=True,
    )

with header_right:

    st.markdown(
        '<div style="text-align:right; padding-top:8px;">'
        '<span class="live-badge">'
        '● LIVE DATA'
        '</span>'
        '</div>',
        unsafe_allow_html=True,
    )


st.divider()


# ============================================================
# OVERVIEW
# ============================================================

if page == "Overview":

    st.header(
        "Executive Overview"
    )

    st.caption(
        "Current marketplace activity, reward distribution "
        "and contributor performance."
    )

    total_bounties = len(
        bounty_current
    )

    total_xrp = numeric_sum(
        bounty_current,
        "reward_xrp",
    )

    total_xora = numeric_sum(
        bounty_current,
        "reward_xora",
    )

    contributors = len(
        leaderboard_current
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Current Bounties",
        f"{total_bounties:,}",
        help=(
            "Number of records in the latest "
            "bounty snapshot."
        ),
    )

    c2.metric(
        "XRP Rewards",
        f"{total_xrp:,.2f}",
        help=(
            "Total XRP reward value currently "
            "listed across bounties."
        ),
    )

    c3.metric(
        "XORA Rewards",
        f"{total_xora:,.2f}",
        help=(
            "Total XORA reward value currently "
            "listed across bounties."
        ),
    )

    c4.metric(
        "Contributors",
        f"{contributors:,}",
        help=(
            "Number of contributors in the "
            "current leaderboard snapshot."
        ),
    )

    st.subheader(
        "Marketplace Distribution"
    )

    left, right = st.columns(2)

    with left:

        if "status" in bounty_current.columns:

            status_counts = (
                bounty_current["status"]
                .fillna("Unknown")
                .astype(str)
                .value_counts()
                .reset_index()
            )

            status_counts.columns = [
                "Status",
                "Count",
            ]

            fig = px.bar(
                status_counts,
                x="Status",
                y="Count",
                title="Bounties by Status",
            )

            st.plotly_chart(
                style_chart(fig),
                width="stretch",
                config={
                    "displayModeBar": False
                },
            )

    with right:

        if "category" in bounty_current.columns:

            category_counts = (
                bounty_current["category"]
                .fillna("Unknown")
                .astype(str)
                .value_counts()
                .reset_index()
            )

            category_counts.columns = [
                "Category",
                "Count",
            ]

            fig = px.bar(
                category_counts,
                x="Category",
                y="Count",
                title="Bounties by Category",
            )

            st.plotly_chart(
                style_chart(fig),
                width="stretch",
                config={
                    "displayModeBar": False
                },
            )

    st.subheader(
        "Current Marketplace"
    )

    show_table(
        bounty_current,
        [
            "task_id",
            "title",
            "category",
            "reward_xrp",
            "reward_xora",
            "status",
            "spots_left",
        ],
    )


# ============================================================
# BOUNTY INTELLIGENCE
# ============================================================

elif page == "Bounty Intelligence":

    st.header(
        "Bounty Intelligence"
    )

    st.caption(
        "Explore current bounty opportunities, rewards, "
        "availability and task requirements."
    )

    filtered = bounty_current.copy()

    f1, f2, f3 = st.columns(3)

    with f1:

        if "category" in filtered.columns:

            categories = sorted(
                filtered["category"]
                .dropna()
                .astype(str)
                .unique()
            )

            selected_categories = st.multiselect(
                "Category",
                categories,
            )

            if selected_categories:

                filtered = filtered[
                    filtered["category"]
                    .astype(str)
                    .isin(
                        selected_categories
                    )
                ]

    with f2:

        if "status" in filtered.columns:

            statuses = sorted(
                filtered["status"]
                .dropna()
                .astype(str)
                .unique()
            )

            selected_statuses = st.multiselect(
                "Status",
                statuses,
            )

            if selected_statuses:

                filtered = filtered[
                    filtered["status"]
                    .astype(str)
                    .isin(
                        selected_statuses
                    )
                ]

    with f3:

        search = st.text_input(
            "Search",
            placeholder="Search bounty title...",
        )

        if search and "title" in filtered.columns:

            filtered = filtered[
                filtered["title"]
                .fillna("")
                .astype(str)
                .str.contains(
                    search,
                    case=False,
                    na=False,
                )
            ]

    st.divider()

    total_xrp = numeric_sum(
        filtered,
        "reward_xrp",
    )

    total_xora = numeric_sum(
        filtered,
        "reward_xora",
    )

    avg_xrp = numeric_mean(
        filtered,
        "reward_xrp",
    )

    avg_xora = numeric_mean(
        filtered,
        "reward_xora",
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Matching Bounties",
        f"{len(filtered):,}",
    )

    c2.metric(
        "Total XRP",
        f"{total_xrp:,.2f}",
    )

    c3.metric(
        "Total XORA",
        f"{total_xora:,.2f}",
    )

    c4.metric(
        "Avg XRP Reward",
        f"{avg_xrp:,.2f}",
    )

    st.subheader(
        "Reward Analysis"
    )

    reward_summary = pd.DataFrame(
        {
            "Asset": [
                "XRP",
                "XORA",
            ],
            "Total": [
                total_xrp,
                total_xora,
            ],
        }
    )

    fig = px.bar(
        reward_summary,
        x="Asset",
        y="Total",
        title="Total Available Rewards",
    )

    st.plotly_chart(
        style_chart(fig),
        width="stretch",
        config={
            "displayModeBar": False
        },
    )

    if avg_xora > 0:

        st.caption(
            f"Average XORA reward per matching bounty: "
            f"{avg_xora:,.2f}"
        )

    st.subheader(
        "Bounty Opportunities"
    )

    show_table(
        filtered,
        [
            "task_id",
            "title",
            "category",
            "reward_xrp",
            "reward_xora",
            "reward_label",
            "status",
            "task_status",
            "claimed_count",
            "spots_left",
            "submitted_count",
            "approved_count",
            "paid_count",
            "difficulty",
        ],
    )


# ============================================================
# CONTRIBUTOR INTELLIGENCE
# ============================================================

elif page == "Contributor Intelligence":

    st.header(
        "Contributor Intelligence"
    )

    st.caption(
        "Monitor contributor rankings, completion activity "
        "and reward performance."
    )

    contributors = (
        leaderboard_current.copy()
    )

    if contributors.empty:

        st.warning(
            "No leaderboard data available."
        )

    else:

        if "rank" in contributors.columns:

            contributors["rank"] = pd.to_numeric(
                contributors["rank"],
                errors="coerce",
            )

            contributors = contributors.sort_values(
                "rank",
                na_position="last",
            )

        total_completed = numeric_sum(
            contributors,
            "completed",
        )

        total_approved = numeric_sum(
            contributors,
            "approved_count",
        )

        total_paid_xrp = numeric_sum(
            contributors,
            "paid_xrp",
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Contributors",
            f"{len(contributors):,}",
        )

        c2.metric(
            "Completed",
            f"{total_completed:,.0f}",
        )

        c3.metric(
            "Approved",
            f"{total_approved:,.0f}",
        )

        c4.metric(
            "Paid XRP",
            f"{total_paid_xrp:,.2f}",
        )

        st.subheader(
            "Contributor Performance"
        )

        chart_data = contributors.copy()

        if "approved_count" in chart_data.columns:

            chart_data[
                "approved_count"
            ] = pd.to_numeric(
                chart_data["approved_count"],
                errors="coerce",
            ).fillna(0)

            name_column = (
                "name"
                if "name" in chart_data.columns
                else "pseudo_code"
            )

            fig = px.bar(
                chart_data.sort_values(
                    "approved_count",
                    ascending=True,
                ),
                x="approved_count",
                y=name_column,
                orientation="h",
                title=(
                    "Approved Contributions "
                    "by Contributor"
                ),
            )

            st.plotly_chart(
                style_chart(fig),
                width="stretch",
                config={
                    "displayModeBar": False
                },
            )

        st.subheader(
            "Leaderboard"
        )

        show_table(
            contributors,
            [
                "rank",
                "pseudo_code",
                "name",
                "role",
                "approved_count",
                "completed",
                "approved_xrp",
                "approved_xora",
                "paid_xrp",
                "paid_xora",
                "total_xrp",
                "total_xora",
            ],
        )


# ============================================================
# HISTORICAL INTELLIGENCE
# ============================================================

elif page == "Historical Intelligence":

    st.header(
        "Historical Intelligence"
    )

    st.caption(
        "Historical snapshots captured by the "
        "automated data pipeline."
    )

    c1, c2 = st.columns(2)

    c1.metric(
        "Bounty History Records",
        f"{len(bounty_history):,}",
    )

    c2.metric(
        "Leaderboard History Records",
        f"{len(leaderboard_history):,}",
    )

    st.subheader(
        "Bounty Activity Over Time"
    )

    if (
        not bounty_history.empty
        and "snapshot_at" in bounty_history.columns
    ):

        history = bounty_history.copy()

        history["snapshot_at"] = pd.to_datetime(
            history["snapshot_at"],
            errors="coerce",
        )

        history = history.dropna(
            subset=[
                "snapshot_at"
            ],
        )

        if not history.empty:

            timeline = (
                history
                .assign(
                    Date=history[
                        "snapshot_at"
                    ].dt.date
                )
                .groupby(
                    "Date"
                )
                .size()
                .reset_index(
                    name="Changes"
                )
            )

            fig = px.line(
                timeline,
                x="Date",
                y="Changes",
                markers=True,
                title="Bounty Changes Captured",
            )

            st.plotly_chart(
                style_chart(fig),
                width="stretch",
                config={
                    "displayModeBar": False
                },
            )

        else:

            st.info(
                "No valid historical bounty "
                "timestamps are available."
            )

    else:

        st.info(
            "Bounty history is not available yet."
        )

    st.subheader(
        "Contributor Ranking History"
    )

    if not leaderboard_history.empty:

        history = (
            leaderboard_history.copy()
        )

        if "snapshot_at" in history.columns:

            history["snapshot_at"] = pd.to_datetime(
                history["snapshot_at"],
                errors="coerce",
            )

        if "name" in history.columns:

            names = sorted(
                history["name"]
                .dropna()
                .astype(str)
                .unique()
            )

            if names:

                selected_name = st.selectbox(
                    "Contributor",
                    names,
                )

                contributor_history = history[
                    history["name"]
                    .astype(str)
                    == selected_name
                ].sort_values(
                    "snapshot_at"
                    if "snapshot_at"
                    in history.columns
                    else "name"
                )

                if "rank" in contributor_history.columns:

                    contributor_history[
                        "rank"
                    ] = pd.to_numeric(
                        contributor_history[
                            "rank"
                        ],
                        errors="coerce",
                    )

                if (
                    "snapshot_at"
                    in contributor_history.columns
                    and "rank"
                    in contributor_history.columns
                ):

                    fig = px.line(
                        contributor_history,
                        x="snapshot_at",
                        y="rank",
                        markers=True,
                        title=(
                            "Leaderboard Position — "
                            f"{selected_name}"
                        ),
                    )

                    fig.update_yaxes(
                        autorange="reversed"
                    )

                    st.plotly_chart(
                        style_chart(fig),
                        width="stretch",
                        config={
                            "displayModeBar": False
                        },
                    )

                else:

                    st.info(
                        "Ranking history does not contain "
                        "the required timestamp/rank fields."
                    )

            else:

                st.info(
                    "No contributor history names "
                    "are available."
                )

        else:

            st.info(
                "Contributor name data "
                "is not available."
            )

    else:

        st.info(
            "Leaderboard history is not available yet."
        )


# ============================================================
# PIPELINE
# ============================================================

elif page == "Pipeline":

    st.header(
        "Data Pipeline"
    )

    st.caption(
        "Automated extraction, persistence and "
        "intelligence architecture."
    )

    # --------------------------------------------------------
    # Architecture
    # --------------------------------------------------------

    st.subheader(
        "Architecture"
    )

    architecture = pd.DataFrame(
        {
            "Layer": [
                "Source",
                "Extraction",
                "Automation",
                "Persistence",
                "Intelligence",
                "Delivery",
            ],
            "Component": [
                "XORA Marketplace",
                "Python Data Extraction",
                "GitHub Actions",
                "Neon PostgreSQL",
                "Streamlit Analytics",
                "Public Dashboard",
            ],
        }
    )

    st.dataframe(
        architecture,
        width="stretch",
        hide_index=True,
    )

    # --------------------------------------------------------
    # Pipeline Components
    # --------------------------------------------------------

    st.subheader(
        "Pipeline Components"
    )

    p1, p2, p3 = st.columns(3)

    with p1:

        with st.container(
            border=True
        ):

            st.markdown(
                "### Collection"
            )

            st.write(
                "Automated extraction of bounty "
                "and contributor marketplace data."
            )

    with p2:

        with st.container(
            border=True
        ):

            st.markdown(
                "### Persistence"
            )

            st.write(
                "Current-state and historical "
                "records are persisted in "
                "Neon PostgreSQL."
            )

    with p3:

        with st.container(
            border=True
        ):

            st.markdown(
                "### Analytics"
            )

            st.write(
                "Interactive intelligence views "
                "transform raw marketplace data "
                "into usable insights."
            )

    # --------------------------------------------------------
    # Database Layer
    # --------------------------------------------------------

    st.subheader(
        "Database Layer"
    )

    table_info = pd.DataFrame(
        {
            "Table": [
                "bounty_current",
                "bounty_history",
                "leaderboard_current",
                "leaderboard_history",
            ],
            "Purpose": [
                "Latest bounty state",
                "Bounty changes over time",
                "Latest contributor rankings",
                "Contributor ranking history",
            ],
            "Records": [
                len(bounty_current),
                len(bounty_history),
                len(leaderboard_current),
                len(leaderboard_history),
            ],
        }
    )

    st.dataframe(
        table_info,
        width="stretch",
        hide_index=True,
    )

    # --------------------------------------------------------
    # Pipeline Status
    # --------------------------------------------------------

    st.subheader(
        "Pipeline Status"
    )

    s1, s2, s3 = st.columns(3)

    s1.metric(
        "Database",
        "Connected",
    )

    s2.metric(
        "Current Bounty Records",
        f"{len(bounty_current):,}",
    )

    s3.metric(
        "Current Contributors",
        f"{len(leaderboard_current):,}",
    )

    st.success(
        "Dashboard connected successfully "
        "to Neon PostgreSQL."
    )

    st.caption(
        "Sensitive backend contributor identifiers "
        "are not exposed through the public dashboard."
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    '<div class="footer-note">'
    'XORA Intelligence · Automated Marketplace Intelligence'
    '</div>',
    unsafe_allow_html=True,
)