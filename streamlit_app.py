import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="FPL Prediktor", layout="centered")
st.title("⚽ FPL – Top 20 hráčů po 5 kolech")

@st.cache_data
def load_bootstrap_data():
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

@st.cache_data
def load_event_data(event_id):
    url = f"https://fantasy.premierleague.com/api/event/{event_id}/live/"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def get_top_players(gw_start=1, gw_end=5):
    bootstrap = load_bootstrap_data()
    players = pd.DataFrame(bootstrap['elements'])
    teams = pd.DataFrame(bootstrap['teams'])

    total_points = {}
    for gw in range(gw_start, gw_end + 1):
        try:
            data = load_event_data(gw)
            for p_id, entry in data["elements"].items():
                pid = int(p_id)
                pts = entry["stats"].get("total_points", 0)
                total_points[pid] = total_points.get(pid, 0) + pts
        except:
            continue

    players["points_gw1_5"] = players["id"].map(total_points)
    players = players.dropna(subset=["points_gw1_5"])
    players["name"] = players["first_name"] + " " + players["second_name"]
    players["team"] = players["team"].map(teams.set_index("id")["name"])

    top = players.sort_values("points_gw1_5", ascending=False).head(20)
    return top[["name", "team", "points_gw1_5", "goals_scored", "assists", "selected_by_percent"]]

with st.spinner("🔄 Načítání dat..."):
    df = get_top_players()
    st.success("Hotovo!")
    st.dataframe(df.reset_index(drop=True), use_container_width=True)
