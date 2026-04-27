"""
app.py
Chess Analytics Platform — Streamlit Dashboard
Connecté à BigQuery marts
"""

import os
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from google.cloud import bigquery
from dotenv import load_dotenv

# ─── Config ───────────────────────────────────────────
load_dotenv()

PROJECT_ID = "chess-analytics-platform"

# Authentification — local vs Streamlit Cloud
def get_bigquery_client():
    try:
        # Streamlit Cloud — utilise les secrets
        from google.oauth2 import service_account
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        return bigquery.Client(project=PROJECT_ID, credentials=credentials)
    except Exception:
        # Local — utilise le fichier JSON
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./credentials/service_account.json"
        return bigquery.Client(project=PROJECT_ID)

client = get_bigquery_client()

# ─── Page config ──────────────────────────────────────
st.set_page_config(
    page_title="Chess Analytics Platform",
    page_icon="♟",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS custom ───────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #1E1E2E;
        border-radius: 8px;
        padding: 16px;
        border-left: 4px solid #7C3AED;
    }
    .stMetric { background: #1E1E2E; border-radius: 8px; padding: 12px; }
</style>
""", unsafe_allow_html=True)

# ─── Data loading ─────────────────────────────────────
@st.cache_data(ttl=3600)
def load_player_stats():
    query = f"""
    SELECT * FROM `{PROJECT_ID}.chess_staging.mart_player_stats`
    ORDER BY total_games_all DESC
    """
    return client.query(query).to_dataframe()

@st.cache_data(ttl=3600)
def load_elo_progression():
    query = f"""
    SELECT * FROM `{PROJECT_ID}.chess_staging.mart_elo_progression`
    ORDER BY username, time_class, game_date
    """
    return client.query(query).to_dataframe()

@st.cache_data(ttl=3600)
def load_opening_analysis():
    query = f"""
    SELECT * FROM `{PROJECT_ID}.chess_staging.mart_opening_analysis`
    ORDER BY total_games DESC
    """
    return client.query(query).to_dataframe()

# ─── Sidebar ──────────────────────────────────────────
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/b/b4/Chess_piece_-_Black_pawn.png/240px-Chess_piece_-_Black_pawn.png", width=60)
st.sidebar.title("♟ Chess Analytics")
st.sidebar.markdown("**Modern Data Stack Pipeline**")
st.sidebar.markdown("---")

page = st.sidebar.selectbox(
    "Navigation",
    ["🏠 Overview", "📈 ELO Progression", "♟ Opening Analysis", "🏆 Player Comparison"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Stack**")
st.sidebar.markdown("Chess.com API · BigQuery · dbt · Airflow · Streamlit")
st.sidebar.markdown("**Data**")
st.sidebar.markdown("Jan — Mar 2025 · 5 top players")

# ─── Load data ────────────────────────────────────────
with st.spinner("Loading data from BigQuery..."):
    df_players = load_player_stats()
    df_elo = load_elo_progression()
    df_openings = load_opening_analysis()

# ════════════════════════════════════════════════════
# PAGE 1 — OVERVIEW
# ════════════════════════════════════════════════════
if page == "🏠 Overview":
    st.title("♟ Chess Analytics Platform")
    st.markdown("Real-time analytics on top Chess.com players · Jan–Mar 2025")
    st.markdown("---")

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Games", f"{df_players['total_games_all'].sum():,}")
    with col2:
        st.metric("Players Tracked", len(df_players))
    with col3:
        best_wr = df_players.loc[df_players['blitz_win_rate_pct'].idxmax()]
        st.metric("Best Win Rate (Blitz)", f"{best_wr['blitz_win_rate_pct']:.1f}%", best_wr['username'])
    with col4:
        top_rating = df_players.loc[df_players['peak_rating'].idxmax()]
        st.metric("Highest Peak Rating", f"{top_rating['peak_rating']:,}", top_rating['username'])

    st.markdown("---")

    # Player stats table
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Player Statistics")
        display_cols = ['username', 'title', 'country_code', 'peak_rating',
                       'blitz_rating', 'rapid_rating', 'total_games_all',
                       'blitz_win_rate_pct', 'rapid_win_rate_pct']
        st.dataframe(
            df_players[display_cols].rename(columns={
                'username': 'Player',
                'title': 'Title',
                'country_code': 'Country',
                'peak_rating': 'Peak Rating',
                'blitz_rating': 'Blitz',
                'rapid_rating': 'Rapid',
                'total_games_all': 'Total Games',
                'blitz_win_rate_pct': 'Blitz WR%',
                'rapid_win_rate_pct': 'Rapid WR%',
            }),
            use_container_width=True,
            hide_index=True,
        )

    with col2:
        st.subheader("Games by Player")
        fig = px.pie(
            df_players,
            values='total_games_all',
            names='username',
            color_discrete_sequence=px.colors.qualitative.Set2,
            hole=0.4,
        )
        fig.update_layout(
            showlegend=True,
            margin=dict(t=0, b=0, l=0, r=0),
            height=300,
        )
        st.plotly_chart(fig, use_container_width=True)

    # Win rate comparison
    st.subheader("Win Rate by Format")
    wr_data = df_players[['username', 'blitz_win_rate_pct', 'rapid_win_rate_pct', 'bullet_win_rate_pct']].melt(
        id_vars='username',
        var_name='format',
        value_name='win_rate'
    )
    wr_data['format'] = wr_data['format'].str.replace('_win_rate_pct', '').str.capitalize()

    fig = px.bar(
        wr_data.dropna(),
        x='username',
        y='win_rate',
        color='format',
        barmode='group',
        labels={'win_rate': 'Win Rate (%)', 'username': 'Player', 'format': 'Format'},
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════
# PAGE 2 — ELO PROGRESSION
# ════════════════════════════════════════════════════
elif page == "📈 ELO Progression":
    st.title("📈 ELO Rating Progression")
    st.markdown("Daily rating evolution · Jan–Mar 2025")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        selected_players = st.multiselect(
            "Select Players",
            options=df_elo['username'].unique().tolist(),
            default=df_elo['username'].unique().tolist()[:3]
        )
    with col2:
        selected_format = st.selectbox(
            "Format",
            options=df_elo['time_class'].unique().tolist(),
            index=0
        )

    filtered = df_elo[
        (df_elo['username'].isin(selected_players)) &
        (df_elo['time_class'] == selected_format)
    ]

    if not filtered.empty:
        fig = px.line(
            filtered,
            x='game_date',
            y='closing_rating',
            color='username',
            title=f"ELO Progression — {selected_format.capitalize()}",
            labels={'closing_rating': 'Rating', 'game_date': 'Date', 'username': 'Player'},
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_layout(height=450, hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)

        # Daily rating change
        st.subheader("Daily Rating Change")
        fig2 = px.bar(
            filtered,
            x='game_date',
            y='rating_change',
            color='username',
            barmode='group',
            labels={'rating_change': 'Rating Change', 'game_date': 'Date'},
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig2.add_hline(y=0, line_dash="dash", line_color="gray")
        fig2.update_layout(height=300)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No data for selected filters.")


# ════════════════════════════════════════════════════
# PAGE 3 — OPENING ANALYSIS
# ════════════════════════════════════════════════════
elif page == "♟ Opening Analysis":
    st.title("♟ Opening Repertoire Analysis")
    st.markdown("Win rates by opening · minimum 3 games")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        sel_player = st.selectbox("Player", df_openings['username'].unique())
    with col2:
        sel_format = st.selectbox("Format", df_openings['time_class'].unique())
    with col3:
        sel_color = st.selectbox("Color", ['white', 'black'])

    filtered = df_openings[
        (df_openings['username'] == sel_player) &
        (df_openings['time_class'] == sel_format) &
        (df_openings['player_color'] == sel_color)
    ].sort_values('total_games', ascending=False).head(15)

    if not filtered.empty:
        fig = px.bar(
            filtered,
            x='win_rate_pct',
            y='opening_slug',
            orientation='h',
            color='win_rate_pct',
            color_continuous_scale='RdYlGn',
            title=f"Top 15 Openings — {sel_player} ({sel_color}, {sel_format})",
            labels={'win_rate_pct': 'Win Rate (%)', 'opening_slug': 'Opening'},
            text='total_games',
        )
        fig.update_traces(texttemplate='%{text} games', textposition='outside')
        fig.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for selected filters.")


# ════════════════════════════════════════════════════
# PAGE 4 — PLAYER COMPARISON
# ════════════════════════════════════════════════════
elif page == "🏆 Player Comparison":
    st.title("🏆 Player Comparison")
    st.markdown("Head-to-head statistics")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        player1 = st.selectbox("Player 1", df_players['username'].tolist(), index=0)
    with col2:
        player2 = st.selectbox("Player 2", df_players['username'].tolist(), index=1)

    p1 = df_players[df_players['username'] == player1].iloc[0]
    p2 = df_players[df_players['username'] == player2].iloc[0]

    st.markdown("---")

    metrics = [
        ("Peak Rating", "peak_rating", ""),
        ("Blitz Rating", "blitz_rating", ""),
        ("Rapid Rating", "rapid_rating", ""),
        ("Total Games", "total_games_all", ""),
        ("Blitz Win Rate", "blitz_win_rate_pct", "%"),
        ("Rapid Win Rate", "rapid_win_rate_pct", "%"),
    ]

    col1, col2, col3 = st.columns([2, 1, 2])

    with col2:
        st.markdown(f"### VS")

    for label, col, suffix in metrics:
        c1, c2, c3 = st.columns([2, 1, 2])
        v1 = p1[col]
        v2 = p2[col]

        if pd.notna(v1) and pd.notna(v2):
            winner = "←" if v1 > v2 else ("→" if v2 > v1 else "=")
            with c1:
                delta = f"+{v1-v2:.1f}{suffix}" if v1 > v2 else f"{v1-v2:.1f}{suffix}"
                st.metric(f"{player1}", f"{v1:.0f}{suffix}", delta if v1 != v2 else None)
            with c2:
                st.markdown(f"<div style='text-align:center;padding-top:20px;font-size:20px'>{winner}<br><small>{label}</small></div>", unsafe_allow_html=True)
            with c3:
                delta2 = f"+{v2-v1:.1f}{suffix}" if v2 > v1 else f"{v2-v1:.1f}{suffix}"
                st.metric(f"{player2}", f"{v2:.0f}{suffix}", delta2 if v1 != v2 else None)