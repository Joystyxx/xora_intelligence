import os
import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2

from dotenv import load_dotenv


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

st.set_page_config(
    page_title="XORA Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
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
        "leaderboard_history"
    }

    if table_name not in allowed_tables:
        raise ValueError("Invalid table name.")

    conn = get_connection()

    try:
        return pd.read_sql(
            f"SELECT * FROM {table_name}",
            conn
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

    st.error(
        f"Database connection failed: {error}"
    )

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("⚡ XORA")
st.sidebar.caption("Intelligence Platform")

page = st.sidebar.radio(
    "Navigate",
    [
        "Overview",
        "Bounty Intelligence",
        "Contributor Intelligence",
        "Historical Intelligence",
        "Pipeline"
    ]
)

st.sidebar.divider()

if st.sidebar.button(
    "🔄 Refresh Data",
    use_container_width=True
):
    st.cache_data.clear()
    st.rerun()

st.sidebar.caption("Data source: Neon PostgreSQL")


# ============================================================
# OVERVIEW
# ============================================================

if page == "Overview":

    st.title("XORA Intelligence")

    st.caption(
        "Automated bounty, contributor and marketplace intelligence"
    )

    st.success("● LIVE DATA")

    st.divider()

    # --------------------------------------------------------
    # OVERVIEW METRICS
    # --------------------------------------------------------

    total_bounties = len(
        bounty_current
    )

    total_xrp = pd.to_numeric(
        bounty_current.get("reward_xrp"),
        errors="coerce"
    ).fillna(0).sum()

    total_xora = pd.to_numeric(
        bounty_current.get("reward_xora"),
        errors="coerce"
    ).fillna(0).sum()

    top_contributor = "N/A"

    if not leaderboard_current.empty:

        ranked = leaderboard_current.sort_values(
            "rank"
        )

        top_contributor = str(
            ranked.iloc[0]["name"]
        )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Current Bounties",
        f"{total_bounties:,}"
    )

    col2.metric(
        "XRP Rewards",
        f"{total_xrp:,.2f}"
    )

    col3.metric(
        "XORA Rewards",
        f"{total_xora:,.2f}"
    )

    col4.metric(
        "Top Contributor",
        top_contributor
    )

    # --------------------------------------------------------
    # MARKETPLACE OVERVIEW
    # --------------------------------------------------------

    st.subheader("Marketplace Overview")

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
                "Count"
            ]

            fig = px.bar(
                status_counts,
                x="Status",
                y="Count",
                title="Bounties by Status"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
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
                "Count"
            ]

            fig = px.bar(
                category_counts,
                x="Category",
                y="Count",
                title="Bounties by Category"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    # --------------------------------------------------------
    # CURRENT BOUNTIES
    # --------------------------------------------------------

    st.subheader("Current Bounties")

    display_columns = [
        "task_id",
        "title",
        "category",
        "reward_xrp",
        "reward_xora",
        "status",
        "spots_left"
    ]

    display_columns = [
        column
        for column in display_columns
        if column in bounty_current.columns
    ]

    st.dataframe(
        bounty_current[display_columns],
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# BOUNTY INTELLIGENCE
# ============================================================

elif page == "Bounty Intelligence":

    st.title("Bounty Intelligence")

    st.caption(
        "Explore active bounties, rewards, availability and task performance."
    )

    st.divider()

    filtered = bounty_current.copy()

    col1, col2, col3 = st.columns(3)

    with col1:

        if "category" in filtered.columns:

            categories = sorted(
                filtered["category"]
                .dropna()
                .astype(str)
                .unique()
            )

            selected_categories = st.multiselect(
                "Category",
                categories
            )

            if selected_categories:

                filtered = filtered[
                    filtered["category"]
                    .astype(str)
                    .isin(selected_categories)
                ]

    with col2:

        if "status" in filtered.columns:

            statuses = sorted(
                filtered["status"]
                .dropna()
                .astype(str)
                .unique()
            )

            selected_status = st.multiselect(
                "Status",
                statuses
            )

            if selected_status:

                filtered = filtered[
                    filtered["status"]
                    .astype(str)
                    .isin(selected_status)
                ]

    with col3:

        search = st.text_input(
            "Search bounty",
            placeholder="Search title..."
        )

        if search:

            filtered = filtered[
                filtered["title"]
                .fillna("")
                .astype(str)
                .str.contains(
                    search,
                    case=False,
                    na=False
                )
            ]

    st.metric(
        "Matching Bounties",
        f"{len(filtered):,}"
    )

    display_columns = [
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
        "difficulty"
    ]

    display_columns = [
        column
        for column in display_columns
        if column in filtered.columns
    ]

    st.dataframe(
        filtered[display_columns],
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Reward Distribution")

    reward_data = filtered.copy()

    reward_data["reward_xrp"] = pd.to_numeric(
        reward_data["reward_xrp"],
        errors="coerce"
    ).fillna(0)

    reward_data["reward_xora"] = pd.to_numeric(
        reward_data["reward_xora"],
        errors="coerce"
    ).fillna(0)

    reward_summary = pd.DataFrame({
        "Asset": [
            "XRP",
            "XORA"
        ],
        "Total": [
            reward_data["reward_xrp"].sum(),
            reward_data["reward_xora"].sum()
        ]
    })

    fig = px.bar(
        reward_summary,
        x="Asset",
        y="Total",
        title="Total Available Rewards"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# CONTRIBUTOR INTELLIGENCE
# ============================================================

elif page == "Contributor Intelligence":

    st.title("Contributor Intelligence")

    st.caption(
        "Monitor contributor rankings, activity and performance."
    )

    st.divider()

    contributors = leaderboard_current.copy()

    if contributors.empty:

        st.warning(
            "No leaderboard data available."
        )

    else:

        contributors = contributors.sort_values(
            "rank"
        )

        total_completed = pd.to_numeric(
            contributors["completed"],
            errors="coerce"
        ).fillna(0).sum()

        total_approved = pd.to_numeric(
            contributors["approved_count"],
            errors="coerce"
        ).fillna(0).sum()

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Contributors",
            f"{len(contributors):,}"
        )

        col2.metric(
            "Total Completed",
            f"{total_completed:,.0f}"
        )

        col3.metric(
            "Total Approved",
            f"{total_approved:,.0f}"
        )

        st.subheader(
            "Contributor Performance"
        )

        chart_data = contributors.copy()

        chart_data["approved_count"] = pd.to_numeric(
            chart_data["approved_count"],
            errors="coerce"
        ).fillna(0)

        fig = px.bar(
            chart_data.sort_values(
                "approved_count",
                ascending=True
            ),
            x="approved_count",
            y="name",
            orientation="h",
            title="Approved Contributions"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.subheader("Leaderboard")

        display_columns = [
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
            "total_xora"
        ]

        display_columns = [
            column
            for column in display_columns
            if column in contributors.columns
        ]

        st.dataframe(
            contributors[display_columns],
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# HISTORICAL INTELLIGENCE
# ============================================================

elif page == "Historical Intelligence":

    st.title("Historical Intelligence")

    st.caption(
        "Track bounty and contributor changes captured over time."
    )

    st.divider()

    col1, col2 = st.columns(2)

    col1.metric(
        "Bounty History Records",
        f"{len(bounty_history):,}"
    )

    col2.metric(
        "Leaderboard Snapshots",
        f"{len(leaderboard_history):,}"
    )

    st.subheader(
        "Bounty Changes Over Time"
    )

    if (
        not bounty_history.empty
        and "snapshot_at" in bounty_history.columns
    ):

        history_copy = bounty_history.copy()

        history_copy["snapshot_at"] = pd.to_datetime(
            history_copy["snapshot_at"],
            errors="coerce"
        )

        timeline = (
            history_copy
            .dropna(
                subset=["snapshot_at"]
            )
            .groupby(
                history_copy[
                    "snapshot_at"
                ].dt.date
            )
            .size()
            .reset_index(
                name="Changes"
            )
        )

        timeline.columns = [
            "Date",
            "Changes"
        ]

        fig = px.line(
            timeline,
            x="Date",
            y="Changes",
            markers=True,
            title="Bounty Changes Captured"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.info(
            "No bounty history available yet."
        )

    st.subheader(
        "Contributor Ranking History"
    )

    if not leaderboard_history.empty:

        history = leaderboard_history.copy()

        history["snapshot_at"] = pd.to_datetime(
            history["snapshot_at"],
            errors="coerce"
        )

        contributor_names = sorted(
            history["name"]
            .dropna()
            .astype(str)
            .unique()
        )

        if contributor_names:

            selected_name = st.selectbox(
                "Contributor",
                contributor_names
            )

            contributor_history = history[
                history["name"].astype(str)
                == selected_name
            ].sort_values(
                "snapshot_at"
            )

            contributor_history["rank"] = pd.to_numeric(
                contributor_history["rank"],
                errors="coerce"
            )

            fig = px.line(
                contributor_history,
                x="snapshot_at",
                y="rank",
                markers=True,
                title=f"Leaderboard Position: {selected_name}"
            )

            fig.update_yaxes(
                autorange="reversed"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    else:

        st.info(
            "No leaderboard history available yet."
        )


# ============================================================
# PIPELINE
# ============================================================

elif page == "Pipeline":

    st.title("Data Pipeline")

    st.caption(
        "Monitor the collection, persistence and analytics architecture."
    )

    st.divider()

    st.subheader(
        "XORA Intelligence Architecture"
    )

    st.markdown(
        """
        **XORA Marketplace**

        ↓

        **Python Data Extraction**

        ↓

        **GitHub Actions Automation**

        ↓

        **Neon PostgreSQL**

        ↓

        **Streamlit Intelligence Layer**

        ↓

        **Public Interactive Dashboard**
        """
    )

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:

        st.subheader("Collection")

        st.write(
            "Automated extraction of bounty and contributor data."
        )

    with col2:

        st.subheader("Persistence")

        st.write(
            "Current-state and historical records stored in PostgreSQL."
        )

    with col3:

        st.subheader("Analytics")

        st.write(
            "Interactive intelligence layer for monitoring rewards, "
            "bounties and contributor performance."
        )

    st.divider()

    st.subheader(
        "Database Tables"
    )

    table_info = pd.DataFrame({
        "Table": [
            "bounty_current",
            "bounty_history",
            "leaderboard_current",
            "leaderboard_history"
        ],
        "Purpose": [
            "Latest bounty state",
            "Bounty changes over time",
            "Latest contributor rankings",
            "Contributor ranking history"
        ],
        "Records": [
            len(bounty_current),
            len(bounty_history),
            len(leaderboard_current),
            len(leaderboard_history)
        ]
    })

    st.dataframe(
        table_info,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    st.success(
        "Dashboard connected successfully to Neon PostgreSQL."
    )

    st.caption(
        "Sensitive backend contributor identifiers are not exposed "
        "through the public dashboard."
    )