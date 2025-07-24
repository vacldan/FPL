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

def create_ai_team(players_df, fixtures_df, current_gw, budget=100.0):
    """Vytvoří AI doporučený tým podle oficiálních FPL pravidel 2025/26"""
    
    # Oficiální FPL pravidla:
    # - £100m budget
    # - 15 hráčů: 2 GK, 5 DEF, 5 MID, 3 FWD
    # - Max 3 z jednoho týmu
    # - Starting XI: 1 GK, min 3 DEF, min 2 MID, min 1 FWD, max 11 celkem
    
    # Filtrace dostupných hráčů (bez zraněných a suspendovaných)
    available_players = players_df[
        (players_df['status'] == 'a') &  # Pouze available hráči
        (players_df['chance_of_playing_this_round'].isna() | (players_df['chance_of_playing_this_round'] >= 75))
    ].copy()
    
    if available_players.empty:
        # Fallback pokud nejsou dostupní hráči
        available_players = players_df.copy()
    
    # AI skóring pro optimální výběr
    available_players['ai_score'] = (
        available_players['predicted_points'] * 0.35 +  # Predikovaná výkonnost
        available_players['form'] * 0.25 +               # Aktuální forma
        (available_players['price'] * 0.15) +            # Prémiové hráči bonus
        ((100 - available_players['selected_by_percent']) / 100 * 0.15) + # Differential bonus
        (available_players['transfers_in'] / 50000 * 0.1)  # Transfer trend
    )
    
    team = {
        'GK': [],
        'DEF': [],
        'MID': [],
        'FWD': []
    }
    
    used_budget = 0.0
    team_counts = {}  # Počítadlo hráčů z každého týmu (max 3)
    
    def can_add_player(player, position, max_count):
        """Kontrola, zda lze přidat hráče podle FPL pravidel"""
        # Kontrola rozpočtu
        if used_budget + player['price'] > budget:
            return False
        
        # Kontrola max hráčů z týmu (max 3)
        current_from_team = team_counts.get(player['team'], 0)
        if current_from_team >= 3:
            return False
            
        # Kontrola max hráčů na pozici
        if len(team[position]) >= max_count:
            return False
            
        return True
    
    # 1. BRANKÁŘI (2 hráči: 1 premium + 1 budget)
    goalkeepers = available_players[available_players['position'] == 'Goalkeeper'].sort_values('ai_score', ascending=False)
    
    # Premium GK (£4.5-6.0m)
    premium_gks = goalkeepers[(goalkeepers['price'] >= 4.5) & (goalkeepers['price'] <= 6.0)]
    if not premium_gks.empty:
        for _, gk in premium_gks.iterrows():
            if can_add_player(gk, 'GK', 2):
                team['GK'].append(gk)
                used_budget += gk['price']
                team_counts[gk['team']] = team_counts.get(gk['team'], 0) + 1
                break
    
    # Budget GK (£4.0-4.5m)
    budget_gks = goalkeepers[(goalkeepers['price'] <= 4.5) & (~goalkeepers['team'].isin([p['team'] for p in team['GK']]))]
    if not budget_gks.empty:
        for _, gk in budget_gks.iterrows():
            if can_add_player(gk, 'GK', 2):
                team['GK'].append(gk)
                used_budget += gk['price']
                team_counts[gk['team']] = team_counts.get(gk['team'], 0) + 1
                break
    
    # 2. OBRÁNCI (5 hráčů: mix cen)
    defenders = available_players[available_players['position'] == 'Defender'].sort_values('ai_score', ascending=False)
    
    target_def_budget = 25.0  # Cílový rozpočet na obránce
    for _, defender in defenders.iterrows():
        if len(team['DEF']) >= 5:
            break
        if can_add_player(defender, 'DEF', 5):
            # Kontrola, aby nepřekročili rozpočet na obránce
            if sum(p['price'] for p in team['DEF']) + defender['price'] <= target_def_budget:
                team['DEF'].append(defender)
                used_budget += defender['price']
                team_counts[defender['team']] = team_counts.get(defender['team'], 0) + 1
    
    # 3. ZÁLOŽNÍCI (5 hráčů: focus na prémiové)
    midfielders = available_players[available_players['position'] == 'Midfielder'].sort_values('ai_score', ascending=False)
    
    target_mid_budget = 50.0  # Nejvíc peněz jde do záložníků
    for _, midfielder in midfielders.iterrows():
        if len(team['MID']) >= 5:
            break
        if can_add_player(midfielder, 'MID', 5):
            remaining_budget = budget - used_budget - 15.0  # Nechej 15m na útočníky
            if midfielder['price'] <= remaining_budget:
                team['MID'].append(midfielder)
                used_budget += midfielder['price']
                team_counts[midfielder['team']] = team_counts.get(midfielder['team'], 0) + 1
    
    # 4. ÚTOČNÍCI (3 hráči)
    forwards = available_players[available_players['position'] == 'Forward'].sort_values('ai_score', ascending=False)
    
    for _, forward in forwards.iterrows():
        if len(team['FWD']) >= 3:
            break
        if can_add_player(forward, 'FWD', 3):
            remaining_budget = budget - used_budget + 0.5  # Tolerance 0.5m
            if forward['price'] <= remaining_budget:
                team['FWD'].append(forward)
                used_budget += forward['price']
                team_counts[forward['team']] = team_counts.get(forward['team'], 0) + 1
    
    # Kontrola kompletnosti týmu podle FPL pravidel
    if len(team['GK']) < 2 or len(team['DEF']) < 5 or len(team['MID']) < 5 or len(team['FWD']) < 3:
        st.error("⚠️ Nepodařilo se vytvořit kompletní tým podle FPL pravidel. Zkuste to znovu.")
    
    return team, used_budget

def get_optimal_formation(team):
    """Určí optimální formaci pro starting XI podle AI skóre"""
    all_outfield = []
    
    # Seřaď všechny hráče mimo brankáře podle AI skóre
    for pos in ['DEF', 'MID', 'FWD']:
        for player in team.get(pos, []):
            all_outfield.append((player, pos))
    
    all_outfield.sort(key=lambda x: x[0]['ai_score'], reverse=True)
    
    # FPL pravidla pro starting XI: min 3 DEF, min 2 MID, min 1 FWD
    formation = {
        'GK': team['GK'][:1],  # Nejlepší brankář
        'DEF': [],
        'MID': [],
        'FWD': []
    }
    
    # Postupně přidávej nejlepší hráče respektujíc minimální požadavky
    def_count = mid_count = fwd_count = 0
    
    for player, pos in all_outfield:
        total_selected = def_count + mid_count + fwd_count
        
        if total_selected >= 10:  # Max 10 outfield hráčů
            break
            
        if pos == 'DEF' and def_count < 5:
            formation['DEF'].append(player)
            def_count += 1
        elif pos == 'MID' and mid_count < 5:
            formation['MID'].append(player)
            mid_count += 1
        elif pos == 'FWD' and fwd_count < 3:
            formation['FWD'].append(player)
            fwd_count += 1
    
    # Zajisti minimální požadavky (3 DEF, 2 MID, 1 FWD)
    if def_count < 3 or mid_count < 2 or fwd_count < 1:
        st.warning("⚠️ Formace nesplňuje FPL minimální požadavky")
    
    return formation

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

def create_transfer_strategy(current_gw, team, fixtures_df):
    """Vytvoří transfer strategii pro následující gameweeks"""
    
    # FPL 2025/26 pravidla:
    # - 1 free transfer každý GW
    # - Můžeš "bankovat" max 5 FT
    # - Extra transfery = -4 body každý
    # - 2x Wildcard (do 29.12 a po 29.12)
    # - 2x každý chip v každé půlce sezóny
    # - GW16: Bonus 5 FT kvůli AFCON
    
    strategies = []
    
    for i in range(4):
        gw = current_gw + i
        
        if gw == current_gw:
            # Aktuální GW
            strategies.append({
                'gw': gw,
                'title': 'ZAČÁTEK SEZÓNY',
                'transfers': '0 FT - Hodnocení výkonnosti',
                'captain_logic': 'Nejlepší fixture + forma',
                'strategy': 'Sleduj výkonnost všech hráčů, injury news a rotace. Žádné panické změny!',
                'risk': '🟢 Bezpečný',
                'focus': 'Stabilita a pozorování',
                'chips': 'Žádné - šetři na později',
                'key_moves': ['Kapitán na nejlepší fixture', 'Sleduj injury news', 'Žádné transfery']
            })
            
        elif gw == current_gw + 1:
            # GW2
            strategies.append({
                'gw': gw,
                'title': 'PRVNÍ REAKCE',
                'transfers': '1 FT - Výměna neúspěšného',
                'captain_logic': 'Stejný kapitán pokud dobře, jinak change',
                'strategy': 'Jeden transfer na výměnu hráče, který nedostal minuty nebo má injury. Zatím žádné větší změny.',
                'risk': '🟡 Opatrný',
                'focus': 'Drobné opravy',
                'chips': 'Možná Bench Boost pokud máš silnou lavičku',
                'key_moves': ['OUT: Non-starter nebo injured', 'IN: Nailed starter', 'Kapitán podle fixtures']
            })
            
        elif gw == current_gw + 2:
            # GW3
            strategies.append({
                'gw': gw,
                'title': 'FIXTURE SWING',
                'transfers': '1-2 FT - Fixture optimalizace',
                'captain_logic': 'Premium vs slabý opponent',
                'strategy': 'Zaměř se na týmy s nejlepšími fixtures pro GW3-6. Možná double transfer pokud máš 2 FT.',
                'risk': '🟡 Střední',
                'focus': 'Fixture exploitation',
                'chips': 'Možná Triple Captain na premium vs promoted team',
                'key_moves': ['IN: Dobré fixtures', 'OUT: Těžké fixtures', 'Kapitán na diferenciál']
            })
            
        elif gw == current_gw + 3:
            # GW4
            strategies.append({
                'gw': gw,
                'title': 'STRATEGICKÉ ROZHODNUTÍ',
                'transfers': 'Wildcard NEBO bank transfer',
                'captain_logic': 'Konzistentní performer',
                'strategy': 'Pokud máš 4+ problémových hráčů, aktivuj první Wildcard. Jinak bank transfer pro GW5.',
                'risk': '🔴 Kritický',
                'focus': 'Dlouhodobé plánování',
                'chips': 'První Wildcard pokud je potřeba major restructure',
                'key_moves': ['Rozhodnutí o WC', 'Nebo bank FT', 'Příprava na fixture swing']
            })
    
    return strategies

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

def format_price(price):
    """Formátuje cenu hráče"""
    return f"£{price:.1f}m"

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
        st.header("🤖 AI Doporučený tým - FPL pravidla 2025/26")
        st.markdown("**Oficiální pravidla:** £100m budget • 15 hráčů (2-5-5-3) • Max 3 z týmu • Starting XI respektuje FPL formaci")
        
        # Vytvoření AI týmu podle pravidel
        ai_team, total_cost = create_ai_team(players_df, fixtures_df, current_gw)
        
        # Kontrola pravidel
        team_summary = {
            'GK': len(ai_team.get('GK', [])),
            'DEF': len(ai_team.get('DEF', [])), 
            'MID': len(ai_team.get('MID', [])),
            'FWD': len(ai_team.get('FWD', []))
        }
        
        total_players = sum(team_summary.values())
        remaining_budget = 100.0 - total_cost
        
        # Status check
        if total_players == 15 and remaining_budget >= 0:
            status_color = "success"
            status_text = f"✅ Tým splňuje FPL pravidla!"
        else:
            status_color = "error" 
            status_text = f"⚠️ Problém s týmem: {total_players}/15 hráčů"
        
        # Info metriky
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💰 Rozpočet", f"£{total_cost:.1f}m")
        with col2:
            st.metric("💸 Zbývá", f"£{remaining_budget:.1f}m") 
        with col3:
            st.metric("👥 Hráči", f"{total_players}/15")
        with col4:
            st.metric("⚽ Formace", f"{team_summary['DEF']}-{team_summary['MID']}-{team_summary['FWD']}")
        
        if status_color == "success":
            st.success(status_text)
        else:
            st.error(status_text)
        
        # FPL pravidla reminder
        st.info("📋 **FPL 2025/26 Novinky:** 2x všechny chipy • Obránci body za 10 CBIT • GW16 bonus 5 FT (AFCON) • Defensive contributions")
        
        # Optimální starting XI podle FPL pravidel
        optimal_xi = get_optimal_formation(ai_team)
        
        st.subheader("🏟️ Starting XI (Optimální formace)")
        st.markdown("*Vybráno podle AI skóre s respektováním FPL minimálních požadavků*")
        
        # Zobrazení starting XI
        xi_positions = [
            ('🥅 Brankář', optimal_xi.get('GK', [])),
            ('🛡️ Obránci', optimal_xi.get('DEF', [])),
            ('⚡ Záložníci', optimal_xi.get('MID', [])),
            ('🎯 Útočníci', optimal_xi.get('FWD', []))
        ]
        
        for pos_name, players in xi_positions:
            if players:
                st.write(f"**{pos_name} ({len(players)})**")
                
                if len(players) <= 4:
                    cols = st.columns(len(players))
                else:
                    # Pro 5 záložníků - rozdělení
                    cols = st.columns(3) + st.columns(2) if len(players) == 5 else st.columns(len(players))
                
                for i, player in enumerate(players):
                    col_index = i if len(players) <= 4 else (i if i < 3 else i - 3)
                    with cols[col_index]:
                        # Fixtures preview
                        fixtures = get_player_next_fixtures(player['team'], fixtures_df, current_gw, 4)
                        
                        st.write(f"**{player['web_name']}** ⭐")
                        st.write(f"{player['team']} • £{player['price']:.1f}m")
                        st.write(f"AI skóre: {player['ai_score']:.1f}")
                        
                        # Fixtures s obtížností
                        if fixtures:
                            fixture_text = "**Fixtures:** "
                            for fix in fixtures[:3]:  # Prvních 3
                                home_away = "🏠" if fix['is_home'] else "✈️"  
                                difficulty_emoji = "🟢" if fix['difficulty'] <= 2 else "🟡" if fix['difficulty'] == 3 else "🔴"
                                fixture_text += f"GW{fix['gw']}: {fix['opponent']} {home_away}{difficulty_emoji} "
                            st.write(fixture_text)
                st.divider()
        
        # Lavička (zbývající hráči)
        st.subheader("🪑 Lavička")
        
        bench_players = []
        starting_players = set()
        
        # Vytvoř set starting hráčů
        for pos_players in optimal_xi.values():
            for player in pos_players:
                starting_players.add(player['id'])
        
        # Najdi hráče na lavičce
        for pos in ['GK', 'DEF', 'MID', 'FWD']:
            for player in ai_team.get(pos, []):
                if player['id'] not in starting_players:
                    bench_players.append((player, pos))
        
        if bench_players:
            bench_cols = st.columns(len(bench_players))
            for i, (player, pos) in enumerate(bench_players):
                with bench_cols[i]:
                    pos_emoji = {'GK': '🥅', 'DEF': '🛡️', 'MID': '⚡', 'FWD': '🎯'}[pos]
                    st.write(f"**{player['web_name']}** {pos_emoji}")
                    st.write(f"{player['team']} • £{player['price']:.1f}m")
                    st.caption("Lavička")
        
        # Kapitán doporučení
        st.subheader("👑 Kapitán & Vice-kapitán")
        
        # Najdi nejlepší kapitány ze starting XI
        starting_players_list = []
        for pos_players in optimal_xi.values():
            starting_players_list.extend(pos_players)
        
        captain_candidates = sorted(starting_players_list, key=lambda x: x['predicted_points'], reverse=True)[:3]
        
        col1, col2, col3 = st.columns(3)
        roles = ["👑 Kapitán", "🔸 Vice-kapitán", "🔹 3. volba"]
        
        for i, candidate in enumerate(captain_candidates):
            with [col1, col2, col3][i]:
                st.write(f"**{roles[i]}**")
                st.write(f"**{candidate['web_name']}**")
                st.write(f"{candidate['team']} • £{candidate['price']:.1f}m")
                st.write(f"**Predikce (C): {candidate['predicted_points']*2:.1f} bodů**")
                
                # Reason for captaincy
                if i == 0:
                    st.success("Nejvyšší predikce + forma")
                elif i == 1:
                    st.info("Backup v případě rotace")
                else:
                    st.warning("Differential pick")
        
        # Transfer strategie pro 4 GW
        st.subheader("🔄 Transfer plán na 4 gameweeks (FPL pravidla)")
        
        strategies = create_transfer_strategy(current_gw, ai_team, fixtures_df)
        
        for i, strategy in enumerate(strategies):
            with st.expander(f"GW{strategy['gw']}: {strategy['title']} {strategy['risk']}", expanded=(i==0)):
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**🔄 Transfery:** {strategy['transfers']}")
                    st.write(f"**👑 Kapitán:** {strategy['captain_logic']}")
                    st.write(f"**🎯 Zaměření:** {strategy['focus']}")
                
                with col2:
                    st.write(f"**💎 Chipy:** {strategy['chips']}")
                    st.write(f"**⚠️ Riziko:** {strategy['risk']}")
                
                st.write("**📋 Strategie:**")
                st.write(strategy['strategy'])
                
                if 'key_moves' in strategy:
                    st.write("**🎯 Klíčové kroky:**")
                    for move in strategy['key_moves']:
                        st.write(f"• {move}")
        
        # FPL pravidla a čipy pro 2025/26
        st.subheader("💎 Chip strategie - Nová pravidla 2025/26")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🔥 První polovina sezóny (GW1-19):**")
            st.write("• **Wildcard 1:** GW4-8 (pokud potřebuješ major changes)")
            st.write("• **Bench Boost:** GW2-3 (když máš silnou lavičku)")  
            st.write("• **Triple Captain:** vs nováčci (GW1-5)")
            st.write("• **Free Hit:** proti bad fixtures (GW6-10)")
            
        with col2:
            st.markdown("**❄️ Druhá polovina sezóny (GW20-38):**")
            st.write("• **Wildcard 2:** GW20-25 (po AFCON chaos)")
            st.write("• **Bench Boost:** Double gameweek (GW28-32)")
            st.write("• **Triple Captain:** DGW premium (GW30-35)")
            st.write("• **Free Hit:** Blank gameweek (GW25-30)")
        
        # AFCON warning
        st.warning("🚨 **AFCON Alert:** GW16 = 5 Free Transfers! Salah, Mbeumo, Sarr a další odjedou 21.12.-18.1.")
        
        # Team value breakdown
        st.subheader("💰 Analýza rozpočtu podle FPL pozic")
        
        if ai_team:
            position_costs = {}
            position_counts = {}
            
            for pos, players in ai_team.items():
                if players:
                    pos_names = {'GK': 'Brankáři', 'DEF': 'Obránci', 'MID': 'Záložníci', 'FWD': 'Útočníci'}
                    pos_name = pos_names[pos]
                    position_costs[pos_name] = sum(p['price'] for p in players)
                    position_counts[pos_name] = len(players)
            
            # Pie chart
            if position_costs:
                cost_df = pd.DataFrame([
                    {'Pozice': k, 'Cena': v, 'Počet': position_counts[k]} 
                    for k, v in position_costs.items()
                ])
                
                fig = px.pie(
                    cost_df,
                    values='Cena',
                    names='Pozice', 
                    title="Rozdělení £100m rozpočtu podle pozic",
                    color_discrete_sequence=['#eab308', '#3b82f6', '#22c55e', '#ef4444'],
                    hover_data=['Počet']
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white')
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabulka s detaily
                cost_df['Průměr na hráče'] = cost_df['Cena'] / cost_df['Počet']
                cost_df['Cena'] = cost_df['Cena'].round(1)
                cost_df['Průměr na hráče'] = cost_df['Průměr na hráče'].round(1)
                
                st.dataframe(cost_df, use_container_width=True)
        
        # FPL pravidla reminder
        st.subheader("📋 Připomenutí FPL pravidel 2025/26")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.success("**✅ Základní pravidla**")
            st.write("""
            • £100m budget celkem  
            • 15 hráčů: 2 GK, 5 DEF, 5 MID, 3 FWD  
            • Max 3 hráči z jednoho týmu  
            • Starting XI: min 3 DEF, 2 MID, 1 FWD  
            • 1 Free Transfer každý GW  
            • Max 5 FT v bance  
            """)
            
        with col2:
            st.info("**🆕 Novinky 2025/26**")
            st.write("""
            • 2x každý chip v každé půlce  
            • Defensive contributions body  
            • Lepší Fantasy assist definice  
            • GW16: Bonus 5 FT (AFCON)  
            • Elite global ligy (Top 1% a 10%)  
            • Adobe AI team badges  
            """)

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
                    st.
