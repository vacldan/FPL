# streamlit_app.py – FPL AI Asistent
import requests
import pandas as pd
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="FPL AI Asistent", layout="wide")

# === API načítání ===
@st.cache_data
def load_bootstrap_data():
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    try:
        res = requests.get(url)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"❗ Nepodařilo se načíst data z bootstrap API: {e}")
        return {}

@st.cache_data
def load_event_data(event_id):
    url = f"https://fantasy.premierleague.com/api/event/{event_id}/live/"
    try:
        res = requests.get(url)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.warning(f"⚠️ Chyba při načítání GW{event_id}: {e}")
        return {"elements": []}

@st.cache_data
def load_fixtures():
    url = "https://fantasy.premierleague.com/api/fixtures/"
    try:
        res = requests.get(url)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"❗ Nelze načíst rozpis zápasů: {e}")
        return []

@st.cache_data
def load_current_gw():
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    try:
        res = requests.get(url)
        res.raise_for_status()
        events = res.json().get("events", [])
        for e in events:
            if e["is_current"]:
                return e["id"]
    except Exception as e:
        st.warning(f"Nelze zjistit aktuální GW: {e}")
    return 1

# === FUNKCE ===
def get_team_difficulty(start_gw, end_gw):
    fixtures = pd.DataFrame(load_fixtures())
    bootstrap = load_bootstrap_data()
    if bootstrap and not fixtures.empty:
        teams = pd.DataFrame(bootstrap['teams'])
        team_id_to_name = teams.set_index("id")["name"].to_dict()
        fixtures['team_a'] = fixtures['team_a'].map(team_id_to_name)
        fixtures['team_h'] = fixtures['team_h'].map(team_id_to_name)
        fixtures['event'] = fixtures['event'].fillna(0).astype(int)
        upcoming = fixtures[fixtures['event'].between(start_gw, end_gw)]
        matrix = pd.DataFrame(index=team_id_to_name.values(), columns=range(start_gw, end_gw + 1))

        for _, row in upcoming.iterrows():
            for team, diff in [(row['team_h'], row['team_h_difficulty']),
                               (row['team_a'], row['team_a_difficulty'])]:
                if team in matrix.index:
                    matrix.at[team, row['event']] = diff

        avg_fdr = matrix.mean(axis=1).to_dict()
        return avg_fdr
    return {}

def get_top_players():
    current_gw = load_current_gw()
    start_gw = current_gw + 1
    end_gw = current_gw + 4

    bootstrap = load_bootstrap_data()
    if not bootstrap:
        return pd.DataFrame(), start_gw, end_gw
    players = pd.DataFrame(bootstrap.get('elements', []))
    teams = pd.DataFrame(bootstrap.get('teams', []))
    total_points = {}
    for gw in range(1, current_gw + 1):
        data = load_event_data(gw)
        if not data or "elements" not in data or not data["elements"]:
            continue
        for entry in data["elements"]:
            pid = entry.get("id")
            pts = entry.get("stats", {}).get("total_points", 0)
            if pid is not None:
                total_points[pid] = total_points.get(pid, 0) + pts

    if players.empty:
        return pd.DataFrame(), start_gw, end_gw

    players["total_points_so_far"] = players["id"].map(total_points)
    players = players.dropna(subset=["total_points_so_far"])
    players["name"] = players['first_name'] + " " + players['second_name']
    players["team"] = players['team'].map(teams.set_index("id")["name"])

    avg_fdr = get_team_difficulty(start_gw, end_gw)
    players['avg_fdr'] = players['team'].map(avg_fdr)
    players['base_points'] = players['points_per_game'].astype(float)
    players['adjusted'] = players['base_points'] / players['avg_fdr']

    for i, gw in enumerate(range(start_gw, end_gw + 1)):
        weight = [0.95, 1.05, 1.0, 1.1][i] if i < 4 else 1.0
        players[f"predicted_gw{gw}"] = players["adjusted"] * weight

    players["predicted_total"] = sum(players[f"predicted_gw{gw}"] for gw in range(start_gw, end_gw + 1))

    return players.sort_values("predicted_total", ascending=False), start_gw, end_gw

# === UI ===
tabs = st.tabs([
    "Top 20 hráčů", "Přestupový asistent", "AI tým",
    "Live predikce", "Chip plánovač", "FDR kalkulátor"
])

with tabs[0]:
    st.title("⚽ FPL – Top 20 hráčů")
    df, start_gw, end_gw = get_top_players()
    if df.empty:
        st.warning("❗ Data nejsou dostupná.")
    else:
        st.success("Hotovo!")
        view_option = st.radio("Zobrazit dle:", ["Historické body", "Predikce (GW{}–GW{})".format(start_gw, end_gw), "Obojí"])
        if view_option == "Historické body":
            st.dataframe(df[["name", "team", "total_points_so_far", "goals_scored", "assists", "selected_by_percent"]], use_container_width=True)
        elif view_option.startswith("Predikce"):
            cols = ["name", "team"] + [f"predicted_gw{gw}" for gw in range(start_gw, end_gw + 1)] + ["predicted_total"]
            st.dataframe(df[cols], use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)

with tabs[2]:
    st.title("🤖 AI predikovaný tým")
    df, start_gw, end_gw = get_top_players()
    if df.empty:
        st.warning("❗ Data nejsou dostupná.")
    else:
        top_team = df.head(11).reset_index(drop=True)

        st.markdown("#### 🧮 Predikce bodů")
        for gw in range(start_gw, end_gw + 1):
            st.write(f"**GW{gw}**", top_team[["name", "team", f"predicted_gw{gw}"]])

        st.markdown("---")
        st.markdown("#### 🧤 Vizualizace sestavy (graficky)")
        formation = {
            'Goalkeeper': [top_team.iloc[0]],
            'Defenders': [top_team.iloc[1], top_team.iloc[2], top_team.iloc[3]],
            'Midfielders': [top_team.iloc[4], top_team.iloc[5], top_team.iloc[6], top_team.iloc[7]],
            'Forwards': [top_team.iloc[8], top_team.iloc[9], top_team.iloc[10]]
        }

        col1, col2, col3 = st.columns([1, 4, 1])
        with col2:
            for group in formation:
                st.subheader(group)
                for player in formation[group]:
                    st.markdown(f"**{player['name']}** – {player['team']} | {player['predicted_total']:.1f} pts")

        st.markdown("### 🔁 Doporučení kroků")
        for gw in range(start_gw, end_gw + 1):
            st.markdown(f"**GW{gw}** – Sleduj dostupnost hráčů, rozpis a bonusy. Prioritizuj kapitána s nízkým FDR a vysokým `predicted_gw{gw}`.")
