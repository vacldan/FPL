import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
from datetime import datetime

# Konfigurace stránky
st.set_page_config(
    page_title="FPL Predictor - Live Data",
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
    .live-indicator {
        background: linear-gradient(45deg, #ff6b6b, #ee5a24);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# API funkce pro načítání dat z FPL
@st.cache_data(ttl=300)
def fetch_fpl_data():
    """Načte základní data z FPL API"""
    try:
        base_url = "https://fantasy.premierleague.com/api/"
        response = requests.get(f"{base_url}bootstrap-static/", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Chyba při načítání dat z FPL API: {e}")
        return None

@st.cache_data(ttl=300)
def fetch_fixtures_data():
    """Načte data o zápasech"""
    try:
        base_url = "https://fantasy.premierleague.com/api/"
        response = requests.get(f"{base_url}fixtures/", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Chyba při načítání fixtures z FPL API: {e}")
        return None

def process_players_data(fpl_data):
    """Zpracuje data hráčů z FPL API - zaměřeno na novou sezónu 2025/26"""
    if not fpl_data:
        return pd.DataFrame()
    
    players = []
    teams = {team['id']: team['name'] for team in fpl_data['teams']}
    positions = {pos['id']: pos['singular_name'] for pos in fpl_data['element_types']}
    
    for player in fpl_data['elements']:
        # Pro novou sezónu se zaměřujeme na aktuální formu a očekávání
        form_score = float(player['form']) if player['form'] else 0
        
        # Predikce založená na formě a ceně (vyšší cena = vyšší očekávání)
        price_factor = (player['now_cost'] / 10.0) / 15.0
        predicted_points = form_score + (price_factor * 3)
        
        players.append({
            'id': player['id'],
            'name': f"{player['first_name']} {player['second_name']}",
            'web_name': player['web_name'],
            'team': teams.get(player['team'], 'Unknown'),
            'team_code': player['team_code'],
            'position': positions.get(player['element_type'], 'Unknown'),
            'price': player['now_cost'] / 10.0,
            'form': form_score,
            'selected_by_percent': float(player['selected_by_percent']),
            'predicted_points': predicted_points,
            'minutes': player['minutes'],
            'news': player['news'] if player['news'] else '',
            'chance_of_playing_this_round': player['chance_of_playing_this_round'],
            'chance_of_playing_next_round': player['chance_of_playing_next_round'],
            'transfers_in': player['transfers_in'],
            'transfers_out': player['transfers_out'],
            'status': player['status'],
            'goals_scored': player['goals_scored'],
            'assists': player['assists'],
            'clean_sheets': player['clean_sheets'],
            'bonus': player['bonus'],
            'total_points': player['total_points']
        })
    
    return pd.DataFrame(players)

def process_fixtures_data(fixtures_data, teams_dict):
    """Zpracuje data o zápasech"""
    if not fixtures_data:
        return pd.DataFrame()
    
    fixtures = []
    for fixture in fixtures_data[:20]:
        if fixture['finished']:
            continue
            
        home_team = teams_dict.get(fixture['team_h'], 'Unknown')
        away_team = teams_dict.get(fixture['team_a'], 'Unknown')
        
        home_difficulty = fixture['team_h_difficulty']
        away_difficulty = fixture['team_a_difficulty']  
        avg_difficulty = (home_difficulty + away_difficulty) / 2
        
        fixtures.append({
            'id': fixture['id'],
            'gameweek': fixture['event'],
            'home_team': home_team,
            'away_team': away_team,
            'home_team_id': fixture['team_h'],
            'away_team_id': fixture['team_a'],
            'difficulty': round(avg_difficulty),
            'home_difficulty': home_difficulty,
            'away_difficulty': away_difficulty,
            'kickoff_time': fixture['kickoff_time'],
            'finished': fixture['finished'],
            'started': fixture['started']
        })
    
    return pd.DataFrame(fixtures)

def get_current_gameweek(fpl_data):
    """Najde aktuální gameweek"""
    if not fpl_data:
        return 1
    
    current_gw = 1
    for event in fpl_data['events']:
        if event['is_current']:
            current_gw = event['id']
            break
        elif event['is_next']:
            current_gw = event['id']
            break
    
    return current_gw

def get_position_color(position):
    colors = {
        'Goalkeeper': '#eab308',
        'Defender': '#3b82f6', 
        'Midfielder': '#22c55e',
        'Forward': '#ef4444'
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

def create_ai_team(players_df, fixtures_df, current_gw, budget=100.0):
    """Vytvoří AI doporučený tým podle strategie"""
    
    # Filtrace dostupných hráčů (bez zraněných)
    available_players = players_df[
        (players_df['status'] != 'i') &  # Ne zranění
        (players_df['chance_of_playing_this_round'].isna() | (players_df['chance_of_playing_this_round'] >= 75))
    ].copy()
    
    # AI strategie pro výběr hráčů
    available_players['ai_score'] = (
        available_players['predicted_points'] * 0.4 +
        available_players['form'] * 0.25 +
        (available_players['price'] * 0.1) +  # Prémiové hráči mají bonus
        ((100 - available_players['selected_by_percent']) / 100 * 0.15) +  # Differential bonus
        (available_players['transfers_in'] / 100000 * 0.1)  # Transfer trend bonus
    )
    
    team = {
        'GK': [],
        'DEF': [],
        'MID': [],
        'FWD': []
    }
    
    used_budget = 0
    selected_teams = set()  # Max 3 z jednoho týmu
    
    # Výběr 1 premium goalkeepera + 1 budget
    gks = available_players[available_players['position'] == 'Goalkeeper'].sort_values('ai_score', ascending=False)
    if not gks.empty:
        # Premium GK
        premium_gk = gks[(gks['price'] >= 4.5) & (gks['price'] <= 6.0)].iloc[0] if len(gks[(gks['price'] >= 4.5) & (gks['price'] <= 6.0)]) > 0 else gks.iloc[0]
        team['GK'].append(premium_gk)
        used_budget += premium_gk['price']
        selected_teams.add(premium_gk['team'])
        
        # Budget GK
        budget_gk = gks[(gks['price'] <= 4.5) & (~gks['team'].isin(selected_teams))].iloc[0] if len(gks[(gks['price'] <= 4.5) & (~gks['team'].isin(selected_teams))]) > 0 else gks.iloc[-1]
        team['GK'].append(budget_gk)
        used_budget += budget_gk['price']
        selected_teams.add(budget_gk['team'])
    
    # Výběr 5 obránců (mix premium + budget)
    defenders = available_players[available_players['position'] == 'Defender'].sort_values('ai_score', ascending=False)
    def_count = 0
    for _, defender in defenders.iterrows():
        if def_count >= 5:
            break
        if defender['team'] in selected_teams and len([t for t in selected_teams if t == defender['team']]) >= 3:
            continue
        if used_budget + defender['price'] <= budget - 30:  # Nechej 30m na zbytek
            team['DEF'].append(defender)
            used_budget += defender['price']
            selected_teams.add(defender['team']) 
            def_count += 1
    
    # Výběr 5 záložníků (focus na predikci)
    midfielders = available_players[available_players['position'] == 'Midfielder'].sort_values('ai_score', ascending=False)
    mid_count = 0
    for _, midfielder in midfielders.iterrows():
        if mid_count >= 5:
            break
        if midfielder['team'] in selected_teams and len([t for t in selected_teams if t == midfielder['team']]) >= 3:
            continue
        if used_budget + midfielder['price'] <= budget - 15:  # Nechej 15m na útočníky
            team['MID'].append(midfielder)
            used_budget += midfielder['price']
            selected_teams.add(midfielder['team'])
            mid_count += 1
    
    # Výběr 3 útočníků
    forwards = available_players[available_players['position'] == 'Forward'].sort_values('ai_score', ascending=False)
    fwd_count = 0
    for _, forward in forwards.iterrows():
        if fwd_count >= 3:
            break
        if forward['team'] in selected_teams and len([t for t in selected_teams if t == forward['team']]) >= 3:
            continue
        if used_budget + forward['price'] <= budget + 0.5:  # Malá tolerance
            team['FWD'].append(forward)
            used_budget += forward['price']
            selected_teams.add(forward['team'])
            fwd_count += 1
    
    return team, used_budget

def get_player_next_fixtures(player_team, fixtures_df, current_gw, count=4):
    """Získá následující fixtures pro hráče"""
    team_fixtures = fixtures_df[
        ((fixtures_df['home_team'] == player_team) | (fixtures_df['away_team'] == player_team)) &
        (fixtures_df['gameweek'] >= current_gw) &
        (fixtures_df['gameweek'] <= current_gw + count - 1)
    ].sort_values('gameweek')
    
    fixtures_info = []
    for _, fixture in team_fixtures.iterrows():
        is_home = fixture['home_team'] == player_team
        opponent = fixture['away_team'] if is_home else fixture['home_team']
        difficulty = fixture['home_difficulty'] if is_home else fixture['away_difficulty']
        
        fixtures_info.append({
            'gw': fixture['gameweek'],
            'opponent': opponent[:3].upper(),
            'is_home': is_home,
            'difficulty': difficulty
        })
    
    return fixtures_info

def create_gameweek_strategy(current_gw):
    """Vytvoří strategii pro následující 4 gameweeks"""
    strategies = [
        {
            'gw': current_gw,
            'title': 'AKTUÁLNÍ GW - Základní sestava',
            'captain': 'Nejlepší predikce + fixture',
            'transfers': '0 FT - Hodnotit výkonnost',
            'strategy': 'Hrát hlavní sestavu, sledovat výkonnost hráčů a injury updates',
            'risk_level': '🟢 Bezpečný',
            'focus': 'Stabilní začátek'
        },
        {
            'gw': current_gw + 1,
            'title': 'REAKCE na výsledky',
            'captain': 'Nejlepší fixture + forma',
            'transfers': '1 FT - Vyměnit neúspěšného',
            'strategy': 'Reagovat na GW1 výsledky, vyměnit hráče který nedostal minuty nebo je zraněný',
            'risk_level': '🟡 Střední',
            'focus': 'Optimalizace sestavy'
        },
        {
            'gw': current_gw + 2,
            'title': 'FIXTURE zaměření',
            'captain': 'Premium vs slabý tým',
            'transfers': '2 FT - Dvojitý přestup',
            'strategy': 'Zaměřit se na týmy s nejlepšími fixtures, možná dvojitá výměna pro lepší kombinaci',
            'risk_level': '🟡 Střední',
            'focus': 'Fixture využití'
        },
        {
            'gw': current_gw + 3,
            'title': 'WILDCARD rozhodnutí',
            'captain': 'Konsistentní performer',
            'transfers': 'Buď WC nebo bank transfer',
            'strategy': 'Pokud máme 4+ problémové hráče, aktivovat Wildcard. Jinak bankovat transfer pro GW5',
            'risk_level': '🔴 Rozhodující',
            'focus': 'Dlouhodobá strategie'
        }
    ]
    return strategies

def main():
    # Header s live indikátorem
    st.markdown("""
    <div style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 10px; margin-bottom: 2rem;'>
        <h1 style='color: white; text-align: center; margin: 0;'>⚽ FPL Predictor</h1>
        <p style='color: #e2e8f0; text-align: center; margin: 0.5rem 0 0 0;'>Sezóna 2025/26 - Čerstvý start!</p>
        <div style='text-align: center;'>
            <span class='live-indicator'>🔴 LIVE DATA</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Načtení dat
    with st.spinner('Načítám aktuální data z FPL API...'):
        fpl_data = fetch_fpl_data()
        fixtures_raw = fetch_fixtures_data()
        
    if not fpl_data:
        st.error("Nepodařilo se načíst data z FPL API. Zkuste to později.")
        return
    
    # Zpracování dat
    players_df = process_players_data(fpl_data)
    teams_dict = {team['id']: team['name'] for team in fpl_data['teams']}
    fixtures_df = process_fixtures_data(fixtures_raw, teams_dict) if fixtures_raw else pd.DataFrame()
    current_gw = get_current_gameweek(fpl_data)
    
    # Info panel s aktuálními statistikami pro novou sezónu
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Aktuální GW", current_gw)
    with col2:
        st.metric("Celkem hráčů", len(players_df))
    with col3:
        avg_price = players_df['price'].mean()
        st.metric("Průměrná cena", f"£{avg_price:.1f}m")
    with col4:
        last_update = datetime.now().strftime("%H:%M")
        st.metric("Poslední update", last_update)
    
    # Info o nové sezóně
    st.info("🆕 **Nová sezóna 2025/26** - Všichni hráči začínají s čistým štítem! Predikce jsou založené na formě z předsezóny a ceně hráčů.")

    # Sidebar s navigací
    st.sidebar.title("📊 Navigace")
    selected_tab = st.sidebar.selectbox(
        "Vyberte sekci:",
        ["Predikce bodů", "AI Doporučený tým", "Top hráči podle ceny", "Fixture analýza", "Transfer trendy", "Týmová analýza"]
    )

    # Tab: Predikce bodů
    if selected_tab == "Predikce bodů":
        st.header("🎯 Nejlepší hráči pro start sezóny 2025/26")
        st.markdown(f"**Gameweek {current_gw}** - Seřazeno podle formy a ceny (vyšší cena = vyšší očekávání)")

        # Filtry
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            search_term = st.text_input("🔍 Hledat hráče:", placeholder="Zadejte jméno hráče...")
        with col2:
            position_filter = st.selectbox(
                "Pozice:",
                ["Všechny pozice", "Goalkeeper", "Defender", "Midfielder", "Forward"]
            )
        with col3:
            max_price = st.number_input("Max cena (£m):", min_value=3.0, max_value=15.0, value=15.0, step=0.5)

        # Filtrování dat
        filtered_df = players_df.copy()
        if search_term:
            filtered_df = filtered_df[
                filtered_df['name'].str.contains(search_term, case=False) | 
                filtered_df['web_name'].str.contains(search_term, case=False)
            ]
        if position_filter != "Všechny pozice":
            filtered_df = filtered_df[filtered_df['position'] == position_filter]
        
        filtered_df = filtered_df[filtered_df['price'] <= max_price]
        filtered_df = filtered_df.sort_values('predicted_points', ascending=False)

        # Zobrazení top hráčů
        st.subheader(f"📈 Top {min(20, len(filtered_df))} hráčů pro novou sezónu")
        
        for idx, (_, player) in enumerate(filtered_df.head(20).iterrows()):
            with st.container():
                col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 1])
                
                with col1:
                    news_indicator = "🚨" if player['news'] else ""
                    injury_risk = ""
                    if player['chance_of_playing_this_round'] and player['chance_of_playing_this_round'] < 100:
                        injury_risk = f" ⚠️ {player['chance_of_playing_this_round']}%"
                    
                    status_icon = ""
                    if player['status'] == 'd':
                        status_icon = " 🤕"
                    elif player['status'] == 'i':
                        status_icon = " 🚑"
                    elif player['status'] == 's':
                        status_icon = " ⛔"
                    
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, {get_position_color(player['position'])}22 0%, {get_position_color(player['position'])}44 100%); 
                                padding: 1rem; border-radius: 8px; border-left: 4px solid {get_position_color(player['position'])};'>
                        <h4 style='margin: 0; color: white;'>{news_indicator} {player['name']} {injury_risk} {status_icon}</h4>
                        <p style='margin: 0; color: #cbd5e1;'>{player['team']} • {player['position']}</p>
                        {f"<small style='color: #fbbf24;'>📰 {player['news']}</small>" if player['news'] else ""}
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.metric("Predikce", f"{player['predicted_points']:.1f}")
                with col3:
                    st.metric("Forma", f"{player['form']:.1f}")
                with col4:
                    st.metric("Cena", format_price(player['price']))
                with col5:
                    st.metric("Vlastnictví", f"{player['selected_by_percent']:.1f}%")
                with col6:
                    net_transfers = player['transfers_in'] - player['transfers_out']
                    st.metric("Transfer trend", f"{net_transfers:,}")

                if player['total_points'] > 0 or player['goals_scored'] > 0 or player['assists'] > 0:
                    col7, col8, col9, col10 = st.columns(4)
                    with col7:
                        st.caption(f"⚽ Góly: {player['goals_scored']}")
                    with col8:
                        st.caption(f"🎯 Asistence: {player['assists']}")
                    with col9:
                        st.caption(f"🛡️ Clean sheets: {player['clean_sheets']}")
                    with col10:
                        st.caption(f"📊 Body: {player['total_points']}")
                else:
                    st.caption("📋 Nová sezóna - statistiky se budou aktualizovat po prvních zápasech")
                
                st.divider()

        # Value analysis chart pro novou sezónu
        if not filtered_df.empty:
            st.subheader("📊 Analýza hodnoty za peníze - Start sezóny 2025/26")
            
            filtered_df['value_per_million'] = filtered_df['predicted_points'] / filtered_df['price']
            top_value = filtered_df.nlargest(15, 'value_per_million')
            
            fig = px.scatter(
                top_value,
                x='price',
                y='predicted_points',
                size='selected_by_percent',
                color='position',
                hover_name='name',
                hover_data={'team': True, 'form': True, 'transfers_in': True},
                title="Cena vs Predikované body - Nová sezóna (velikost = vlastnictví %)",
                labels={'price': 'Cena (£m)', 'predicted_points': 'Predikované body'}
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white')
            )
            st.plotly_chart(fig, use_container_width=True)

    # Tab: AI Doporučený tým
    elif selected_tab == "AI Doporučený tým":
        st.header("🤖 AI Doporučený tým pro sezónu 2025/26")
        st.markdown("AI vytvořilo optimální tým na základě predikce, formy, ceny a diferenciálu")
        
        # Vytvoření AI týmu
        ai_team, total_cost = create_ai_team(players_df, fixtures_df, current_gw)
        
        # Info o týmu
        st.info(f"💰 **Celkový rozpočet: £{total_cost:.1f}m / £100.0m** • Zbývá: £{100.0-total_cost:.1f}m")
        
        # Formace display
        st.markdown("""
        <div style='background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                    padding: 2rem; border-radius: 15px; margin: 2rem 0; position: relative;'>
            <div style='position: absolute; top: 0; left: 0; right: 0; bottom: 0; 
                        background: url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 100 60\'%3E%3Crect width=\'100\' height=\'60\' fill=\'%2322c55e\' opacity=\'0.3\'/%3E%3Cline x1=\'50\' y1=\'0\' x2=\'50\' y2=\'60\' stroke=\'white\' stroke-width=\'0.2\' opacity=\'0.5\'/%3E%3Ccircle cx=\'50\' cy=\'30\' r=\'8\' fill=\'none\' stroke=\'white\' stroke-width=\'0.2\' opacity=\'0.5\'/%3E%3C/svg%3E") center/cover;
                        border-radius: 15px;'></div>
            <h2 style='text-align: center; color: white; position: relative; z-index: 1; margin-bottom: 2rem;'>
                ⚽ Formace 3-5-2
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Zobrazení hráčů podle pozic
        positions = [
            ('🥅 Brankáři', ai_team.get('GK', []), '#eab308'),
            ('🛡️ Obránci', ai_team.get('DEF', []), '#3b82f6'), 
            ('⚡ Záložníci', ai_team.get('MID', []), '#22c55e'),
            ('🎯 Útočníci', ai_team.get('FWD', []), '#ef4444')
        ]
        
        for pos_name, players, color in positions:
            if players:
                st.subheader(pos_name)
                
                # Zobrazení hlavních hráčů vs lavička
                if pos_name == '🥅 Brankáři':
                    main_players = players[:1]  # 1 hlavní
                    bench_players = players[1:]  # 1 na lavičku
                elif pos_name == '🛡️ Obránci':
                    main_players = players[:3]  # 3 hlavní
                    bench_players = players[3:]  # 2 na lavičku
                elif pos_name == '⚡ Záložníci':
                    main_players = players[:5]  # 5 hlavní (možnost rotace)
                    bench_players = []
                else:  # Útočníci
                    main_players = players[:2]  # 2 hlavní
                    bench_players = players[2:]  # 1 na lavičku
                
                # Hlavní sestava
                if main_players:
                    st.markdown("**Hlavní sestava:**")
                    cols = st.columns(len(main_players))
                    for i, player in enumerate(main_players):
                        with cols[i]:
                            # Fixtures pro hráče
                            fixtures = get_player_next_fixtures(player['team'], fixtures_df, current_gw, 4)
                            fixtures_display = ""
                            for fix in fixtures[:4]:
                                diff_color = '#22c55e' if fix['difficulty'] <= 2 else '#eab308' if fix['difficulty'] == 3 else '#ef4444'
                                home_away = '🏠' if fix['is_home'] else '✈️'
                                fixtures_display += f"""
                                <div style='text-align: center; margin: 0.2rem 0;'>
                                    <small style='color: {diff_color}; font-weight: bold;'>
                                        GW{fix['gw']}: {fix['opponent']} {home_away}
                                    </small>
                                </div>
                                """
                            
                            st.markdown(f"""
                            <div style='background: linear-gradient(135deg, {color}22 0%, {color}44 100%); 
                                        padding: 1rem; border-radius: 10px; text-align: center; margin: 0.5rem 0;
                                        border: 2px solid {color};'>
                                <h4 style='color: white; margin: 0;'>{player['web_name']}</h4>
                                <p style='color: #cbd5e1; margin: 0.5rem 0; font-size: 0.9rem;'>{player['team']}</p>
                                <p style='color: #10b981; font-weight: bold; margin: 0;'>£{player['price']:.1f}m</p>
                                <small style='color: #a78bfa;'>Predikce: {player['predicted_points']:.1f} | Forma: {player['form']:.1f}</small>
                                {fixtures_display}
                            </div>
                            """, unsafe_allow_html=True)
                
                # Lavička
                if bench_players:
                    st.markdown("**Lavička:**")
                    bench_cols = st.columns(len(bench_players))
                    for i, player in enumerate(bench_players):
                        with bench_cols[i]:
                            st.markdown(f"""
                            <div style='background: linear-gradient(135deg, #6b728022 0%, #6b728044 100%); 
                                        padding: 0.8rem; border-radius: 8px; text-align: center; margin: 0.5rem 0;
                                        border: 1px solid #6b7280;'>
                                <h5 style='color: #d1d5db; margin: 0;'>{player['web_name']}</h5>
                                <p style='color: #9ca3af; margin: 0.3rem 0; font-size: 0.8rem;'>{player['team']}</p>
                                <p style='color: #6b7280; font-weight: bold; margin: 0; font-size: 0.9rem;'>£{player['price']:.1f}m</p>
                            </div>
                            """, unsafe_allow_html=True)
        
        # Kapitán doporučení
        st.subheader("👑 Kapitán doporučení")
        
        # Najdi nejlepší kapitánské volby
        all_players = []
        for pos_players in ai_team.values():
            all_players.extend(pos_players)
        
        captain_candidates = sorted(all_players, key=lambda x: x['predicted_points'], reverse=True)[:3]
        
        col1, col2, col3 = st.columns(3)
        for i, candidate in enumerate(captain_candidates):
            with [col1, col2, col3][i]:
                risk_level = ["🟢 Bezpečný", "🟡 Střední", "🔴 Risky"][i]
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%); 
                            padding: 1rem; border-radius: 10px; text-align: center;'>
                    <h4 style='color: #92400e; margin: 0;'>👑 {candidate['web_name']}</h4>
                    <p style='color: #b45309; margin: 0.5rem 0;'>{candidate['team']} • £{candidate['price']:.1f}m</p>
                    <p style='color: #92400e; font-weight: bold; margin: 0;'>
                        Predikce (C): {candidate['predicted_points']*2:.1f} bodů
                    </p>
                    <small style='color: #b45309;'>{risk_level}</small>
                </div>
                """, unsafe_allow_html=True)
        
        # Strategie pro následující 4 GW
        st.subheader("📋 AI Strategie pro následující 4 Gameweeks")
        
        strategies = create_gameweek_strategy(current_gw)
        
        for strategy in strategies:
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #1f2937 0%, #374151 100%); 
                        padding: 1.5rem; border-radius: 12px; margin: 1rem 0;
                        border-left: 5px solid #6366f1;'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;'>
                    <h4 style='color: white; margin: 0;'>GW{strategy['gw']}: {strategy['title']}</h4>
                    <span style='background: rgba(99, 102, 241, 0.2); color: #a5b4fc; 
                                 padding: 0.3rem 0.8rem; border-radius: 15px; font-size: 0.8rem;'>
                        {strategy['risk_level']}
                    </span>
                </div>
                
                <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;'>
                    <div>
                        <strong style='color: #fbbf24;'>👑 Kapitán:</strong>
                        <p style='color: #e5e7eb; margin: 0.3rem 0;'>{strategy['captain']}</p>
                    </div>
                    <div>
                        <strong style='color: #10b981;'>🔄 Transfery:</strong>
                        <p style='color: #e5e7eb; margin: 0.3rem 0;'>{strategy['transfers']}</p>
                    </div>
                </div>
                
                <div style='margin-bottom: 1rem;'>
                    <strong style='color: #8b5cf6;'>🎯 Strategie:</strong>
                    <p style='color: #e5e7eb; margin: 0.5rem 0;'>{strategy['strategy']}</p>
                </div>
                
                <div style='text-align: center; background: rgba(139, 92, 246, 0.1); 
                            padding: 0.5rem; border-radius: 8px;'>
                    <strong style='color: #c4b5fd;'>Zaměření: {strategy['focus']}</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Key insights
        st.subheader("💡 Klíčové poznatky AI strategie")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style='background: linear-gradient(135deg, #059669 0%, #10b981 100%); 
                        padding: 1rem; border-radius: 10px;'>
                <h4 style='color: white; margin: 0 0 1rem 0;'>✅ Výhody tohoto týmu</h4>
                <ul style='color: #d1fae5; margin: 0; padding-left: 1.2rem;'>
                    <li>Balanced rozpočet - žádné risiko</li>
                    <li>Mix premium + differential hráčů</li>
                    <li>Dobré fixtures pro prvních 4 GW</li>
                    <li>Flexibility pro rotace</li>
                    <li>Silná lavička pro emergency</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style='background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%); 
                        padding: 1rem; border-radius: 10px;'>
                <h4 style='color: white; margin: 0 0 1rem 0;'>⚠️ Rizika a pozornost</h4>
                <ul style='color: #fecaca; margin: 0; padding-left: 1.2rem;'>
                    <li>Sleduj injury news před GW</li>
                    <li>Rotation risk u některých hráčů</li>
                    <li>Fixture swing od GW3</li>
                    <li>Nová sezóna = nepředvídatelnost</li>
                    <li>Transfer trendy můžou ovlivnit ceny</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

    # Tab: Top hráči podle ceny
    elif selected_tab == "Top hráči podle ceny":
        st.header("💰 Nejlepší value za peníze - Nový start!")
        st.markdown("Založeno na ceně, formě a transferové aktivitě pro sezónu 2025/26")
        
        price_ranges = [
            ("Budget (£3.5-5.5m)", 3.5, 5.5),
            ("Mid-range (£5.5-8.0m)", 5.5, 8.0),
            ("Premium (£8.0-12.0m)", 8.0, 12.0),
            ("Super premium (£12.0+)", 12.0, 20.0)
        ]
        
        for category, min_price, max_price in price_ranges:
            st.subheader(category)
            
            category_players = players_df[
                (players_df['price'] >= min_price) & 
                (players_df['price'] < max_price)
            ].copy()
            
            if not category_players.empty:
                category_players['value_score'] = (
                    category_players['predicted_points'] * 0.5 +
                    category_players['form'] * 0.3 +
                    (100 - category_players['selected_by_percent']) / 100 * 0.2
                )
                
                top_category = category_players.nlargest(5, 'value_score')
                
                for _, player in top_category.iterrows():
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    
                    with col1:
                        st.markdown(f"""
                        <div style='background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                                    padding: 0.8rem; border-radius: 8px; color: white;'>
                            <strong>{player['name']}</strong><br>
                            <small>{player['team']} • {player['position']}</small>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.metric("Cena", format_price(player['price']))
                    with col3:
                        st.metric("Predikce", f"{player['predicted_points']:.1f}")
                    with col4:
                        st.metric("Vlastnictví", f"{player['selected_by_percent']:.1f}%")
            else:
                st.info("Žádní hráči v této kategorii.")

    # Tab: Fixture analýza
    elif selected_tab == "Fixture analýza":
        st.header("📅 Analýza nadcházejících zápasů")
        
        if fixtures_df.empty:
            st.warning("Data o zápasech nejsou k dispozici.")
            return
        
        current_fixtures = fixtures_df[fixtures_df['gameweek'] == current_gw]
        
        if not current_fixtures.empty:
            st.subheader(f"⚽ Zápasy Gameweek {current_gw}")
            
            for _, fixture in current_fixtures.iterrows():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                difficulty_color = get_difficulty_color(fixture['difficulty'])
                
                with col1:
                    kickoff = fixture['kickoff_time']
                    if kickoff:
                        kickoff_time = datetime.fromisoformat(kickoff.replace('Z', '+00:00')).strftime('%d.%m %H:%M')
                    else:
                        kickoff_time = "TBD"
                    
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #1e293b 0%, #334155 100%); 
                                padding: 1rem; border-radius: 8px; border-left: 4px solid {difficulty_color};'>
                        <h4 style='color: white; margin: 0;'>{fixture['home_team']} vs {fixture['away_team']}</h4>
                        <p style='color: #cbd5e1; margin: 0.5rem 0 0 0;'>
                            {kickoff_time} • Obtížnost: {fixture['difficulty']}/5
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if fixture['difficulty'] <= 2:
                        st.success("✅ Snadný")
                    elif fixture['difficulty'] >= 4:
                        st.error("❌ Těžký")
                    else:
                        st.info("➖ Střední")
                
                with col3:
                    st.caption(f"🏠 Doma: {fixture['home_difficulty']}")
                    st.caption(f"✈️ Venku: {fixture['away_difficulty']}")

        # Team fixture difficulty
        st.subheader("📊 Obtížnost fixtures podle týmů")
        
        if not fixtures_df.empty:
            team_difficulty = []
            next_5_fixtures = fixtures_df[fixtures_df['gameweek'].between(current_gw, current_gw + 4)]
            
            for team_id, team_name in teams_dict.items():
                home_fixtures = next_5_fixtures[next_5_fixtures['home_team_id'] == team_id]
                away_fixtures = next_5_fixtures[next_5_fixtures['away_team_id'] == team_id]
                
                home_diff = home_fixtures['home_difficulty'].mean() if not home_fixtures.empty else 0
                away_diff = away_fixtures['away_difficulty'].mean() if not away_fixtures.empty else 0
                
                avg_difficulty = (home_diff + away_diff) / 2 if (home_diff > 0 or away_diff > 0) else 0
                
                if avg_difficulty > 0:
                    team_difficulty.append({
                        'team': team_name,
                        'avg_difficulty': avg_difficulty,
                        'fixtures_count': len(home_fixtures) + len(away_fixtures)
                    })
            
            if team_difficulty:
                difficulty_df = pd.DataFrame(team_difficulty)
                difficulty_df = difficulty_df.sort_values('avg_difficulty')
                
                fig = px.bar(
                    difficulty_df.head(10),
                    x='avg_difficulty',
                    y='team',
                    orientation='h',
                    title=f"Nejsnadnější fixtures pro GW {current_gw}-{current_gw + 4}",
                    color='avg_difficulty',
                    color_continuous_scale='RdYlGn_r'
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white')
                )
                st.plotly_chart(fig, use_container_width=True)

    # Tab: Transfer trendy
    elif selected_tab == "Transfer trendy":
        st.header("🔄 Transfer trendy a vlastnictví")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Nejvíce přiváděni")
            most_transferred_in = players_df.nlargest(10, 'transfers_in')
            
            for _, player in most_transferred_in.iterrows():
                st.metric(
                    f"{player['name']} ({player['team']})",
                    f"{player['transfers_in']:,}",
                    delta=f"£{player['price']:.1f}m"
                )
        
        with col2:
            st.subheader("📉 Nejvíce odváděni")
            most_transferred_out = players_df.nlargest(10, 'transfers_out')
            
            for _, player in most_transferred_out.iterrows():
                st.metric(
                    f"{player['name']} ({player['team']})",
                    f"-{player['transfers_out']:,}",
                    delta=f"£{player['price']:.1f}m"
                )

        # Transfer trends visualization  
        st.subheader("📊 Transfer aktivita")
        
        active_transfers = players_df[
            (players_df['transfers_in'] > 50000) | (players_df['transfers_out'] > 50000)
        ].copy()
        
        if not active_transfers.empty:
            active_transfers['net_transfers'] = active_transfers['transfers_in'] - active_transfers['transfers_out']
            
            fig = px.bar(
                active_transfers.nlargest(15, 'net_transfers', keep='all'),
                x='net_transfers',
                y='name',
                orientation='h',
                title="Čisté transfery (IN - OUT)",
                color='net_transfers',
                color_continuous_scale='RdYlGn'
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white')
            )
            st.plotly_chart(fig, use_container_width=True)

    # Tab: Týmová analýza
    elif selected_tab == "Týmová analýza":
        st.header("🏟️ Analýza podle týmů")
        
        team_stats = []
        for team_id, team_name in teams_dict.items():
            team_players = players_df[players_df['team'] == team_name]
            
            if not team_players.empty:
                total_value = team_players['price'].sum()
                avg_prediction = team_players['predicted_points'].mean()
                top_player = team_players.loc[team_players['predicted_points'].idxmax()]
                most_selected = team_players.loc[team_players['selected_by_percent'].idxmax()]
                
                team_stats.append({
                    'team': team_name,
                    'total_value': total_value,
                    'avg_prediction': avg_prediction,
                    'players_count': len(team_players),
                    'top_player': top_player['name'],
                    'top_prediction': top_player['predicted_points'],
                    'most_selected': most_selected['name'],
                    'highest_selection': most_selected['selected_by_percent']
                })
        
        if team_stats:
            team_df = pd.DataFrame(team_stats)
            team_df = team_df.sort_values('avg_prediction', ascending=False)
            
            st.subheader("🏆 Nejslibněji vypadající týmy pro sezónu 2025/26")
            
            fig = px.bar(
                team_df.head(10),
                x='team',
                y='avg_prediction',
                title="Průměrná predikce bodů všech hráčů týmu",
                color='avg_prediction',
                color_continuous_scale='viridis'
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("📋 Detaily týmů - Potenciál pro novou sezónu")
            
            display_df = team_df[['team', 'avg_prediction', 'total_value', 'top_player', 'top_prediction', 'most_selected', 'highest_selection']].copy()
            display_df.columns = ['Tým', 'Průměrná predikce', 'Celková hodnota (£m)', 'Nejslibněji', 'Predikce top hráče', 'Nejvíc vlastněný', 'Vlastnictví %']
            display_df['Průměrná predikce'] = display_df['Průměrná predikce'].round(1)
            display_df['Celková hodnota (£m)'] = display_df['Celková hodnota (£m)'].round(1)
            display_df['Predikce top hráče'] = display_df['Predikce top hráče'].round(1)
            display_df['Vlastnictví %'] = display_df['Vlastnictví %'].round(1)
            
            st.dataframe(display_df, use_container_width=True)

    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align: center; color: #64748b; padding: 2rem;'>
        <p>🏆 FPL Predictor - Sezóna 2025/26</p>
        <p>🆕 Čerstvý start! Všichni hráči začínají s nulou</p>
        <p>Poslední update: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')} • Data se aktualizují každých 5 minut</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
