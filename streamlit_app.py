import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Konfigurace stránky
st.set_page_config(
    page_title="FPL Predictor",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS pro lepší vzhled
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    .stSelectbox > div > div > div {
        background-color: #1e293b;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .player-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        color: white;
    }
    .formation-field {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Data - kopie z původního React kódu
@st.cache_data
def load_players_data():
    players = [
        {
            "id": 1,
            "name": "Mohamed Salah",
            "team": "Liverpool",
            "position": "Midfielder",
            "price": 14.5,
            "total_points": 344,
            "form": 9.1,
            "selected_by_percent": 63.4,
            "predicted_points": 13.8,
            "next5fixtures": [
                {"points": 9.2, "opponent": "BOU", "isHome": True, "gw": 1},
                {"points": 12.8, "opponent": "new", "isHome": False, "gw": 2},
                {"points": 8.1, "opponent": "ARS", "isHome": True, "gw": 3},
                {"points": 10.5, "opponent": "bur", "isHome": False, "gw": 4},
                {"points": 12.1, "opponent": "EVE", "isHome": True, "gw": 5}
            ]
        },
        {
            "id": 2,
            "name": "Erling Haaland",
            "team": "Man City",
            "position": "Forward",
            "price": 14.0,
            "total_points": 181,
            "form": 7.3,
            "selected_by_percent": 45.8,
            "predicted_points": 11.2,
            "next5fixtures": [
                {"points": 5.8, "opponent": "wol", "isHome": False, "gw": 1},
                {"points": 11.5, "opponent": "TOT", "isHome": True, "gw": 2},
                {"points": 13.8, "opponent": "bri", "isHome": False, "gw": 3},
                {"points": 9.2, "opponent": "MUN", "isHome": True, "gw": 4},
                {"points": 11.8, "opponent": "ARS", "isHome": False, "gw": 5}
            ]
        },
        {
            "id": 3,
            "name": "Alexander Isak",
            "team": "Newcastle",
            "position": "Forward",
            "price": 10.5,
            "total_points": 211,
            "form": 8.6,
            "selected_by_percent": 38.2,
            "predicted_points": 12.8,
            "next5fixtures": [
                {"points": 10.1, "opponent": "AVL", "isHome": False, "gw": 1},
                {"points": 9.2, "opponent": "LIV", "isHome": True, "gw": 2},
                {"points": 12.1, "opponent": "lee", "isHome": False, "gw": 3},
                {"points": 8.3, "opponent": "WOL", "isHome": True, "gw": 4},
                {"points": 11.2, "opponent": "bou", "isHome": False, "gw": 5}
            ]
        },
        {
            "id": 4,
            "name": "Cole Palmer",
            "team": "Chelsea",
            "position": "Midfielder",
            "price": 10.5,
            "total_points": 198,
            "form": 7.9,
            "selected_by_percent": 32.7,
            "predicted_points": 10.1,
            "next5fixtures": [
                {"points": 8.8, "opponent": "CRY", "isHome": True, "gw": 1},
                {"points": 9.9, "opponent": "whu", "isHome": False, "gw": 2},
                {"points": 7.2, "opponent": "FUL", "isHome": True, "gw": 3},
                {"points": 11.8, "opponent": "BRE", "isHome": False, "gw": 4},
                {"points": 9.5, "opponent": "mun", "isHome": False, "gw": 5}
            ]
        },
        {
            "id": 5,
            "name": "Bukayo Saka",
            "team": "Arsenal",
            "position": "Midfielder",
            "price": 10.0,
            "total_points": 165,
            "form": 7.2,
            "selected_by_percent": 29.8,
            "predicted_points": 9.5,
            "next5fixtures": [
                {"points": 9.8, "opponent": "mun", "isHome": False, "gw": 1},
                {"points": 8.1, "opponent": "BRI", "isHome": True, "gw": 2},
                {"points": 8.9, "opponent": "liv", "isHome": False, "gw": 3},
                {"points": 7.2, "opponent": "NFO", "isHome": False, "gw": 4},
                {"points": 11.8, "opponent": "MCI", "isHome": True, "gw": 5}
            ]
        },
        {
            "id": 6,
            "name": "Florian Wirtz",
            "team": "Liverpool",
            "position": "Midfielder",
            "price": 8.5,
            "total_points": 0,
            "form": 8.0,
            "selected_by_percent": 15.3,
            "predicted_points": 8.8,
            "next5fixtures": [
                {"points": 7.5, "opponent": "BOU", "isHome": True, "gw": 1},
                {"points": 9.8, "opponent": "new", "isHome": False, "gw": 2},
                {"points": 6.5, "opponent": "ARS", "isHome": True, "gw": 3},
                {"points": 9.2, "opponent": "bur", "isHome": False, "gw": 4},
                {"points": 10.1, "opponent": "EVE", "isHome": True, "gw": 5}
            ]
        },
        {
            "id": 7,
            "name": "Bryan Mbeumo",
            "team": "Brentford",
            "position": "Midfielder",
            "price": 8.0,
            "total_points": 234,
            "form": 8.4,
            "selected_by_percent": 42.1,
            "predicted_points": 9.8,
            "next5fixtures": [
                {"points": 8.8, "opponent": "nfo", "isHome": False, "gw": 1},
                {"points": 7.9, "opponent": "AVL", "isHome": False, "gw": 2},
                {"points": 10.5, "opponent": "SUN", "isHome": True, "gw": 3},
                {"points": 7.1, "opponent": "CHE", "isHome": True, "gw": 4},
                {"points": 9.2, "opponent": "FUL", "isHome": False, "gw": 5}
            ]
        },
        {
            "id": 8,
            "name": "Jarrod Bowen",
            "team": "West Ham",
            "position": "Forward",
            "price": 8.0,
            "total_points": 156,
            "form": 7.5,
            "selected_by_percent": 18.9,
            "predicted_points": 8.1,
            "next5fixtures": [
                {"points": 7.8, "opponent": "sun", "isHome": False, "gw": 1},
                {"points": 8.5, "opponent": "CHE", "isHome": True, "gw": 2},
                {"points": 6.9, "opponent": "nfo", "isHome": False, "gw": 3},
                {"points": 9.2, "opponent": "TOT", "isHome": False, "gw": 4},
                {"points": 7.4, "opponent": "cry", "isHome": False, "gw": 5}
            ]
        }
    ]
    return pd.DataFrame(players)

@st.cache_data
def load_fixtures_data():
    fixtures = [
        {"id": 1, "home_team": "Liverpool", "away_team": "Bournemouth", "difficulty": 2, "gameweek": 1, "date": "15 Aug"},
        {"id": 2, "home_team": "Aston Villa", "away_team": "Newcastle", "difficulty": 3, "gameweek": 1, "date": "16 Aug"},
        {"id": 3, "home_team": "Chelsea", "away_team": "Crystal Palace", "difficulty": 2, "gameweek": 1, "date": "17 Aug"},
        {"id": 4, "home_team": "Man United", "away_team": "Arsenal", "difficulty": 4, "gameweek": 1, "date": "17 Aug"},
        {"id": 5, "home_team": "Tottenham", "away_team": "Burnley", "difficulty": 2, "gameweek": 1, "date": "16 Aug"}
    ]
    return pd.DataFrame(fixtures)

# Pomocné funkce
def get_position_color(position):
    colors = {
        'Forward': '#ef4444',
        'Midfielder': '#22c55e', 
        'Defender': '#3b82f6',
        'Goalkeeper': '#eab308'
    }
    return colors.get(position, '#6b7280')

def get_difficulty_color(difficulty):
    if difficulty <= 2:
        return '#22c55e'
    elif difficulty == 3:
        return '#eab308'
    elif difficulty == 4:
        return '#f97316'
    else:
        return '#ef4444'

# Hlavní aplikace
def main():
    # Header
    st.markdown("""
    <div style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 10px; margin-bottom: 2rem;'>
        <h1 style='color: white; text-align: center; margin: 0;'>⚽ FPL Predictor</h1>
        <p style='color: #e2e8f0; text-align: center; margin: 0.5rem 0 0 0;'>Gameweek 1 • Sezóna 2025/26</p>
    </div>
    """, unsafe_allow_html=True)

    # Načtení dat
    players_df = load_players_data()
    fixtures_df = load_fixtures_data()

    # Sidebar s navigací
    st.sidebar.title("📊 Navigace")
    selected_tab = st.sidebar.selectbox(
        "Vyberte sekci:",
        ["Predikce bodů", "Můj doporučený tým", "Fixture analýza", "Doporučení kapitána", "Transfer tips"]
    )

    # Tab: Predikce bodů
    if selected_tab == "Predikce bodů":
        st.header("🎯 Top predikce na Gameweek 1")
        st.markdown("Hráči s nejvyšší predikovanými body pro start sezóny 2025/26")

        # Filtry
        col1, col2 = st.columns([2, 1])
        with col1:
            search_term = st.text_input("🔍 Hledat hráče:", placeholder="Zadejte jméno hráče...")
        with col2:
            position_filter = st.selectbox(
                "Pozice:",
                ["Všechny pozice", "Goalkeeper", "Defender", "Midfielder", "Forward"]
            )

        # Filtrování dat
        filtered_df = players_df.copy()
        if search_term:
            filtered_df = filtered_df[filtered_df['name'].str.contains(search_term, case=False)]
        if position_filter != "Všechny pozice":
            filtered_df = filtered_df[filtered_df['position'] == position_filter]

        # Seřazení podle predikovaných bodů
        filtered_df = filtered_df.sort_values('predicted_points', ascending=False)

        # Zobrazení top hráčů
        for idx, player in filtered_df.iterrows():
            with st.container():
                col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 1])
                
                with col1:
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, {get_position_color(player['position'])}22 0%, {get_position_color(player['position'])}44 100%); 
                                padding: 1rem; border-radius: 8px; border-left: 4px solid {get_position_color(player['position'])};'>
                        <h4 style='margin: 0; color: white;'>{player['name']}</h4>
                        <p style='margin: 0; color: #cbd5e1;'>{player['team']} • {player['position']}</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.metric("Predikce", f"{player['predicted_points']:.1f}")
                with col3:
                    st.metric("Forma", f"{player['form']:.1f}")
                with col4:
                    st.metric("Cena", f"£{player['price']}m")
                with col5:
                    st.metric("Vlastnictví", f"{player['selected_by_percent']}%")
                with col6:
                    st.metric("Celkem", f"{player['total_points']}")

                # Fixtures prediction chart
                fixtures = player['next5fixtures']
                fixture_data = pd.DataFrame(fixtures)
                
                fig = px.bar(
                    fixture_data, 
                    x='gw', 
                    y='points',
                    title=f"Příštích 5 zápasů - {player['name']}",
                    color='points',
                    color_continuous_scale='RdYlGn',
                    height=200
                )
                fig.update_layout(
                    showlegend=False,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white')
                )
                st.plotly_chart(fig, use_container_width=True)
                
                st.divider()

    # Tab: Můj doporučený tým
    elif selected_tab == "Můj doporučený tým":
        st.header("⚽ Doporučená sestava (3-5-2) • £100.0m")
        
        # Formation visualization
        st.markdown("""
        <div class='formation-field'>
            <h3 style='text-align: center; color: white; margin-bottom: 2rem;'>Formace 3-5-2</h3>
        </div>
        """, unsafe_allow_html=True)

        # Team sections
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("🥅 Brankář")
            st.markdown("""
            <div class='player-card'>
                <h4>Pickford</h4>
                <p>Everton • £5.0m</p>
                <small>Predikce: 6.2 bodů</small>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.subheader("🛡️ Obránci")
            defenders = [
                {"name": "Gabriel", "team": "Arsenal", "price": "6.0"},
                {"name": "Ait-Nouri", "team": "Man City", "price": "5.5"},
                {"name": "Esteve", "team": "Burnley", "price": "4.0"}
            ]
            for defender in defenders:
                st.markdown(f"""
                <div class='player-card'>
                    <h5>{defender['name']}</h5>
                    <p>{defender['team']} • £{defender['price']}m</p>
                </div>
                """, unsafe_allow_html=True)

        with col3:
            st.subheader("⚡ Záložníci")
            midfielders = [
                {"name": "Salah", "team": "Liverpool", "price": "14.5"},
                {"name": "Palmer", "team": "Chelsea", "price": "10.5"},
                {"name": "Saka", "team": "Arsenal", "price": "10.0"},
                {"name": "Wirtz", "team": "Liverpool", "price": "8.5"},
                {"name": "Mbeumo", "team": "Brentford", "price": "8.0"}
            ]
            for midfielder in midfielders:
                st.markdown(f"""
                <div class='player-card'>
                    <h5>{midfielder['name']}</h5>
                    <p>{midfielder['team']} • £{midfielder['price']}m</p>
                </div>
                """, unsafe_allow_html=True)

        # Forwards
        st.subheader("🎯 Útočníci")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class='player-card'>
                <h4>Alexander Isak</h4>
                <p>Newcastle • £10.5m</p>
                <small>Predikce: 12.8 bodů</small>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class='player-card'>
                <h4>Jarrod Bowen</h4>
                <p>West Ham • £8.0m</p>
                <small>Predikce: 8.1 bodů</small>
            </div>
            """, unsafe_allow_html=True)

        # Budget breakdown
        st.subheader("💰 Rozpis rozpočtu")
        budget_data = {
            'Pozice': ['Brankáři', 'Obránci', 'Záložníci', 'Útočníci'],
            'Částka': [9.5, 19.5, 57.5, 23.0],
            'Hráči': ['Pickford + Kelleher', '3 + 2 na lavičce', '5 + 1 na lavičce', '2 + 1 na lavičce']
        }
        budget_df = pd.DataFrame(budget_data)
        
        fig = px.pie(
            budget_df, 
            values='Částka', 
            names='Pozice',
            title="Rozdělení rozpočtu podle pozic",
            color_discrete_sequence=['#eab308', '#3b82f6', '#22c55e', '#ef4444']
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        st.plotly_chart(fig, use_container_width=True)

        # Strategy for 5 gameweeks
        st.subheader("📈 Strategie na 5 gameweeks dopředu")
        
        strategy_data = [
            {"GW": 1, "Strategie": "START SEZÓNY", "Akce": "Salah (C) vs Sunderland, balanced tým", "Status": "🟢"},
            {"GW": 2, "Strategie": "VYHODNOCENÍ", "Akce": "Sledujeme formu po GW1, možný transfer Wirtz", "Status": "🟡"},
            {"GW": 3, "Strategie": "ADAPTACE", "Akce": "Přidáváme Haalanda, OUT Wirtz pokud nedostává minuty", "Status": "🟡"},
            {"GW": 4, "Strategie": "OPTIMALIZACE", "Akce": "Fixture swing týden, příprava na busy period", "Status": "🔵"},
            {"GW": 5, "Strategie": "PRVNÍ WILDCARD?", "Akce": "Buď Wildcard nebo standard 1FT", "Status": "🔴"}
        ]
        
        for strategy in strategy_data:
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #1e293b 0%, #334155 100%); 
                        padding: 1rem; margin: 0.5rem 0; border-radius: 8px; border-left: 4px solid #6366f1;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <h5 style='color: white; margin: 0;'>{strategy['Status']} GW{strategy['GW']} - {strategy['Strategie']}</h5>
                        <p style='color: #cbd5e1; margin: 0.5rem 0 0 0; font-size: 0.9rem;'>{strategy['Akce']}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Tab: Fixture analýza
    elif selected_tab == "Fixture analýza":
        st.header("📅 Fixture analýza - Gameweek 1")
        st.markdown("První kolo sezóny 2025/26 - nováčci vs. velikáni")

        for _, fixture in fixtures_df.iterrows():
            difficulty_color = get_difficulty_color(fixture['difficulty'])
            
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #1e293b 0%, #334155 100%); 
                            padding: 1rem; border-radius: 8px; border-left: 4px solid {difficulty_color};'>
                    <h4 style='color: white; margin: 0;'>{fixture['home_team']} vs {fixture['away_team']}</h4>
                    <p style='color: #cbd5e1; margin: 0.5rem 0 0 0;'>{fixture['date']} • Obtížnost: {fixture['difficulty']}/5</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if fixture['difficulty'] <= 2:
                    st.success("✅ Doporučeno")
                elif fixture['difficulty'] >= 4:
                    st.error("⚠️ Opatrně")
                else:
                    st.info("➖ Neutrální")

        # Fixture difficulty chart
        fig = px.bar(
            fixtures_df,
            x='home_team',
            y='difficulty',
            title="Obtížnost fixtures pro Gameweek 1",
            color='difficulty',
            color_continuous_scale='RdYlGn_r'
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        st.plotly_chart(fig, use_container_width=True)

    # Tab: Doporučení kapitána
    elif selected_tab == "Doporučení kapitána":
        st.header("👑 Doporučení kapitána pro Gameweek 1")
        st.info("Nová sezóna 2025/26 - Začínáme od nuly!")

        # Top 3 captain picks
        top_captains = players_df.nlargest(3, 'predicted_points')
        
        for idx, captain in top_captains.iterrows():
            captain_points = captain['predicted_points'] * 2  # Captain double points
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                risk_level = ["🟢 Bezpečné", "🟡 Balanced", "🔴 Risky"][idx] if idx < 3 else "🔴 Risky"
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%); 
                            padding: 1.5rem; border-radius: 12px; margin: 1rem 0;'>
                    <h3 style='color: #92400e; margin: 0;'>👑 {captain['name']}</h3>
                    <p style='color: #b45309; margin: 0.5rem 0;'>{captain['team']} • {captain['position']}</p>
                    <div style='display: flex; justify-content: space-between; margin-top: 1rem;'>
                        <div><strong>Forma:</strong> {captain['form']}/10</div>
                        <div><strong>Vlastnictví:</strong> {captain['selected_by_percent']}%</div>
                        <div><strong>Riziko:</strong> {risk_level}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.metric(
                    "Očekávané body (C)",
                    f"{captain_points:.1f}",
                    delta=f"+{captain_points - captain['predicted_points']:.1f}"
                )

        # Captain comparison chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Normální body',
            x=top_captains['name'],
            y=top_captains['predicted_points'],
            marker_color='lightblue'
        ))
        
        fig.add_trace(go.Bar(
            name='Kapitánské body',
            x=top_captains['name'],
            y=top_captains['predicted_points'] * 2,
            marker_color='gold'
        ))
        
        fig.update_layout(
            title="Porovnání kapitánských voleb",
            barmode='group',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        
        st.plotly_chart(fig, use_container_width=True)

    # Tab: Transfer tips
    elif selected_tab == "Transfer tips":
        st.header("🔄 Transfer doporučení pro sezónu 2025/26")
        st.info("Novinky: 2x všechny chipy každou polovinu sezóny!")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📈 Transfer IN")
            transfer_in = [
                {"name": "Erling Haaland", "team": "Man City", "price": "£14.0m", "points": "11.8 pts"},
                {"name": "Son Heung-min", "team": "Tottenham", "price": "£9.5m", "points": "9.4 pts"},
                {"name": "Morgan Rogers", "team": "Aston Villa", "price": "£7.0m", "points": "8.8 pts"}
            ]
            
            for player in transfer_in:
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #22c55e22 0%, #22c55e44 100%); 
                            padding: 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid #22c55e;'>
                    <h5 style='color: white; margin: 0;'>{player['name']}</h5>
                    <p style='color: #cbd5e1; margin: 0; font-size: 0.9rem;'>{player['team']} • {player['price']}</p>
                    <strong style='color: #22c55e;'>{player['points']}</strong>
                </div>
                """, unsafe_allow_html=True)

        with col2:
            st.subheader("📉 Transfer OUT")
            transfer_out = [
                {"name": "Florian Wirtz", "reason": "Liverpool • Rotace riziko", "points": "6.2 pts"},
                {"name": "Maxime Esteve", "reason": "Burnley • Těžké fixtures", "points": "4.2 pts"},
                {"name": "Bryan Mbeumo", "reason": "Brentford • Transfer spekulace", "points": "6.5 pts"}
            ]
            
            for player in transfer_out:
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #ef444422 0%, #ef444444 100%); 
                            padding: 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid #ef4444;'>
                    <h5 style='color: white; margin: 0;'>{player['name']}</h5>
                    <p style='color: #cbd5e1; margin: 0; font-size: 0.9rem;'>{player['reason']}</p>
                    <strong style='color: #ef4444;'>{player['points']}</strong>
                </div>
                """, unsafe_allow_html=True)

        # Transfer trends chart
        st.subheader("📊 Transfer trendy")
        
        # Mock transfer data
        transfer_data = pd.DataFrame({
            'Hráč': ['Haaland', 'Salah', 'Isak', 'Palmer', 'Saka', 'Wirtz'],
            'Transfer IN %': [25.3, 15.7, 18.9, 12.4, 8.9, 3.2],
            'Transfer OUT %': [5.1, 2.3, 4.7, 6.8, 7.2, 15.4]
        })
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Transfer IN %',
            x=transfer_data['Hráč'],
            y=transfer_data['Transfer IN %'],
            marker_color='#22c55e'
        ))
        
        fig.add_trace(go.Bar(
            name='Transfer OUT %',
            x=transfer_data['Hráč'],
            y=transfer_data['Transfer OUT %'],
            marker_color='#ef4444'
        ))
        
        fig.update_layout(
            title="Transfer activity pro top hráče",
            barmode='group',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # Chip strategy section
        st.subheader("🎯 Chip strategie")
        
        chip_strategy = [
            {"chip": "Wildcard 1", "timing": "GW5-8", "reason": "podle potřeby po fixture swingu"},
            {"chip": "Triple Captain", "timing": "vs nováčci", "reason": "v DGW proti slabým týmům"},
            {"chip": "Bench Boost", "timing": "GW1 nebo DGW", "reason": "když máme silnou lavičku"},
            {"chip": "Free Hit", "timing": "vs bad fixtures", "reason": "proti těžkým fixtures"}
        ]
        
        for chip in chip_strategy:
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); 
                        padding: 1rem; border-radius: 8px; margin: 0.5rem 0;'>
                <h5 style='color: white; margin: 0;'>🎯 {chip['chip']}</h5>
                <p style='color: #e0e7ff; margin: 0.5rem 0 0 0; font-size: 0.9rem;'>
                    <strong>Kdy:</strong> {chip['timing']} | <strong>Proč:</strong> {chip['reason']}
                </p>
            </div>
            """, unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #64748b; padding: 2rem;'>
        <p>🏆 FPL Predictor - Sezóna 2025/26</p>
        <p>Vytvořeno pro optimální Fantasy Premier League strategii</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
