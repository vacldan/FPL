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
        return {"elements": {}}

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

# === FUNKCE ===
def get_top_players(gw_start=1, gw_end=5):
    bootstrap = load_bootstrap_data()
    if not bootstrap:
        return pd.DataFrame()
    players = pd.DataFrame(bootstrap.get('elements', []))
    teams = pd.DataFrame(bootstrap.get('teams', []))
    total_points = {}
    for gw in range(gw_start, gw_end + 1):
        data = load_event_data(gw)
        for p_id, entry in data.get("elements", {}).items():
            pid = int(p_id)
            pts = entry.get("stats", {}).get("total_points", 0)
            total_points[pid] = total_points.get(pid, 0) + pts
    if players.empty:
        return pd.DataFrame()
    players["points_gw1_5"] = players["id"].map(total_points)
    players = players.dropna(subset=["points_gw1_5"])
    players["name"] = players['first_name'] + " " + players['second_name']
    players["team"] = players['team'].map(teams.set_index("id")["name"])
    return players.sort_values("points_gw1_5", ascending=False).head(20)[
        ["name", "team", "points_gw1_5", "goals_scored", "assists", "selected_by_percent"]
    ]

# === UI ===
tabs = st.tabs([
    "Top 20 hráčů", "Přestupový asistent", "AI tým",
    "Live predikce", "Chip plánovač", "FDR kalkulátor"
])

# === 1. TOP HRÁČI ===
with tabs[0]:
    st.title("⚽ FPL – Top 20 hráčů po 5 kolech")
    df = get_top_players()
    if df.empty:
        st.warning("❗ Data nejsou dostupná. Zkuste znovu později nebo lokálně.")
    else:
        st.success("Hotovo!")
        st.dataframe(df, use_container_width=True)

# === 2. TRANSFER OPTIMIZER ===
with tabs[1]:
    st.header("Přestupový asistent")
    name = st.text_input("Zadej jméno hráče pro srovnání")
    bootstrap = load_bootstrap_data()
    if name and bootstrap:
        players = pd.DataFrame(bootstrap['elements'])
        players['name'] = players['first_name'] + " " + players['second_name']
        match = players[players['name'].str.contains(name, case=False)]
        if not match.empty:
            st.dataframe(match[["name", "now_cost", "points_per_game", "goals_scored", "assists"]])
        else:
            st.warning("Hráč nenalezen.")

# === 3. AI TEAM ===
with tabs[2]:
    st.header("AI doporučený tým pro nadcházejících 5 kol")
    ai_team = [
        "Areola", "Trippier", "Gabriel", "Estupiñán",
        "Salah", "Palmer", "Saka", "Foden",
        "Haaland (C)", "Isak", "João Pedro"
    ]
    st.markdown("### 🧠 AI Výběr 11 hráčů:")
    for player in ai_team:
        st.write(f"- {player}")
    st.markdown("### 📅 Doporučené kroky na dalších 5 týdnů")
    st.markdown("""
    1. **GW6**: Pokud má Palmer těžký los, vyměň ho za Bowen.
    2. **GW7**: Použij 1 FT na obranu – Trippier -> Porro (lepší losy).
    3. **GW8**: Zvaž aktivaci **Wildcard**, pokud budou zranění.
    4. **GW9**: Kapitán Salah místo Haalanda (slabý soupeř doma).
    5. **GW10**: Přidej levného obránce s rostoucí formou (např. Kabore).
    """)

# === 4. LIVE PREDIKCE ===
with tabs[3]:
    st.header("Predikce bodů pro další kolo (simulace)")
    bootstrap = load_bootstrap_data()
    if bootstrap:
        players = pd.DataFrame(bootstrap['elements'])
        players['name'] = players['first_name'] + " " + players['second_name']
        players['predicted_points'] = players['points_per_game'].astype(float) * 0.95
        top_preds = players.sort_values('predicted_points', ascending=False).head(15)
        st.dataframe(top_preds[["name", "now_cost", "predicted_points"]])
    else:
        st.error("Nelze načíst data pro predikce.")

# === 5. CHIP PLÁNOVAČ ===
with tabs[4]:
    st.header("Chip plánovač")
    st.markdown("""
    🧮 Doporučení použití chipů:
    - **Wildcard**: ideální kolem GW8–GW9 před přetížením rozpisu.
    - **Bench Boost**: GW11 nebo GW15 s plnou lavičkou.
    - **Triple Captain**: čekej na dvojité kolo City/Liverpool.
    - **Free Hit**: použij při blank Gameweeku (např. GW29).

    📅 Dnes: {today}
    """.format(today=datetime.today().strftime('%d.%m.%Y')))

# === 6. FDR KALKULÁTOR ===
with tabs[5]:
    st.header("Fixture Difficulty Rating (FDR) vizualizace")
    fixtures = pd.DataFrame(load_fixtures())
    bootstrap = load_bootstrap_data()
    if bootstrap and not fixtures.empty:
        teams = pd.DataFrame(bootstrap['teams'])
        team_id_to_name = teams.set_index("id")["name"].to_dict()
        fixtures['team_a'] = fixtures['team_a'].map(team_id_to_name)
        fixtures['team_h'] = fixtures['team_h'].map(team_id_to_name)
        fixtures['event'] = fixtures['event'].fillna(0).astype(int)
        upcoming = fixtures[fixtures['event'] <= 10]

        st.subheader("📊 Heatmapa obtížnosti rozpisu (GW1–10)")
        team_list = sorted(teams['name'].unique())
        matrix = pd.DataFrame(index=team_list, columns=range(1, 11))

        for _, row in upcoming.iterrows():
            for team, opp, diff in [(row['team_h'], row['team_a'], row['team_h_difficulty']),
                                    (row['team_a'], row['team_h'], row['team_a_difficulty'])]:
                if team in matrix.index:
                    matrix.at[team, row['event']] = diff

        fig, ax = plt.subplots(figsize=(14, 10))
        sns.heatmap(matrix.astype(float), cmap="YlOrRd", linewidths=0.5, annot=True, fmt=".0f", cbar_kws={'label': 'FDR'})
        st.pyplot(fig)

        st.subheader("🎯 Doporučení hráčů podle FDR + forma")
        players = pd.DataFrame(bootstrap['elements'])
        players['name'] = players['first_name'] + " " + players['second_name']
        players['team'] = players['team'].map(team_id_to_name)
        players = players[['name', 'team', 'points_per_game', 'now_cost']]
        team_fdr = matrix.apply(pd.to_numeric, errors='coerce').mean(axis=1).to_dict()
        players['avg_fdr'] = players['team'].map(team_fdr)
        players['score'] = players['points_per_game'].astype(float) / players['avg_fdr']
        top_combined = players.sort_values('score', ascending=False).head(15)
        st.dataframe(top_combined[['name', 'team', 'points_per_game', 'avg_fdr', 'score']])
    else:
        st.warning("❗ FDR data nejsou dostupná.")
