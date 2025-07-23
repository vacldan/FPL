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
@st.cache_data(ttl=300)  # Cache na 5 minut
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
    """Zpracuje data hráčů z FPL API"""
    if not fpl_data:
        return pd.DataFrame()
    
    players = []
    teams = {team['id']: team['name'] for team in fpl_data['teams']}
    positions = {pos['id']: pos['singular_name'] for pos in fpl_data['element_types']}
    
    for player in fpl_data['elements']:
        # Výpočet predikovaných bodů na základě formy a průměru
        form_score = float(player['form']) if player['form'] else 0
        avg_points = float(player['points_per_game']) if player['points_per_game'] else 0
        predicted_points = (form_score * 0.6 + avg_points * 0.4)
        
        players.append({
            'id': player['id'],
            'name': f"{player['first_name']} {player['second_name']}",
            'web_name': player['web_name'],
            'team': teams.get(player['team'], 'Unknown'),
            'team_code': player['team_code'],
            'position': positions.get(player['element_type'], 'Unknown'),
            'price': player['now_cost'] / 10.0,  # Cena je v desetinách
            'total_points': player['total_points'],
            'form': form_score,
            'selected_by_percent': float(player['selected_by_percent']),
            'predicted_points': predicted_points,
            'points_per_game': avg_points,
            'goals_scored': player['goals_scored'],
            'assists': player['assists'],
            'clean_sheets': player['clean_sheets'],
            'minutes': player['minutes'],
            'bonus': player['bonus'],
            'value_form': float(player['value_form']) if player['value_form'] else 0,
            'value_season': float(player['value_season']) if player['value_season'] else 0,
            'transfers_in': player['transfers_in'],
            'transfers_out': player['transfers_out'],
            'news': player['news'] if player['news'] else '',
            'chance_of_playing_this_round': player['chance_of_playing_this_round'],
            'chance_of_playing_next_round': player['chance_of_playing_next_round']
        })
    
    return pd.DataFrame(players)

def process_fixtures_data(fixtures_data, teams_dict):
    """Zpracuje data o zápasech"""
    if not fixtures_data:
        return pd.DataFrame()
    
    fixtures = []
    for fixture in fixtures_data[:20]:  # Prvních 20 zápasů
        if fixture['finished']:
            continue  # Přeskočíme dokončené zápasy
            
        home_team = teams_dict.get(fixture['team_h'], 'Unknown')
        away_team = teams_dict.get(fixture['team_a'], 'Unknown')
        
        # Výpočet obtížnosti na základě síly týmů
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

# Pomocné funkce
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

# Hlavní aplikace
def main():
    # Header s live indikátorem
    st.markdown("""
    <div style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 10px; margin-bottom: 2rem;'>
        <h1 style='color: white; text-align: center; margin: 0;'>⚽ FPL Predictor</h1>
        <p style='color: #e2e8f0; text-align: center; margin: 0.5rem 0 0 0;'>Live data ze seasonky 2024/25</p>
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
    
    # Info panel s aktuálními statistikami
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

    # Sidebar s navigací
    st.sidebar.title("📊 Navigace")
    selected_tab = st.sidebar.selectbox(
        "Vyberte sekci:",
        ["Predikce bodů", "Top hráči podle ceny", "Fixture analýza", "Transfer trendy", "Týmová analýza"]
    )

    # Tab: Predikce bodů
    if selected_tab == "Predikce bodů":
        st.header("🎯 Nejlepší hráči podle predikce")
        st.markdown(f"**Gameweek {current_gw}** - Seřazeno podle formy a průměru bodů")

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
        
        # Seřazení podle predikovaných bodů
        filtered_df = filtered_df.sort_values('predicted_points', ascending=False)

        # Zobrazení top hráčů
        st.subheader(f"📈 Top {min(20, len(filtered_df))} hráčů")
        
        for idx, (_, player) in enumerate(filtered_df.head(20).iterrows()):
            with st.container():
                # Main player info
                col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 1])
                
                with col1:
                    # News indicator
                    news_indicator = "🚨" if player['news'] else ""
                    injury_risk = ""
                    if player['chance_of_playing_this_round'] and player['chance_of_playing_this_round'] < 100:
                        injury_risk = f" ⚠️ {player['chance_of_playing_this_round']}%"
                    
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, {get_position_color(player['position'])}22 0%, {get_position_color(player['position'])}44 100%); 
                                padding: 1rem; border-radius: 8px; border-left: 4px solid {get_position_color(player['position'])};'>
                        <h4 style='margin: 0; color: white;'>{news_indicator} {player['name']} {injury_risk}</h4>
                        <p style='margin: 0; color: #cbd5e1;'>{player['team']} • {player['position']}</p>
                        {f"<small style='color: #fbbf24;'>📰 {player['news']}</small>" if player['news'] else ""}
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.metric("Predikovaná forma", f"{player['predicted_points']:.1f}")
                with col3:
                    st.metric("Aktuální forma", f"{player['form']:.1f}")
                with col4:
                    st.metric("Cena", format_price(player['price']))
                with col5:
                    st.metric("Vlastnictví", f"{player['selected_by_percent']:.1f}%")
                with col6:
                    st.metric("Celkem bodů", f"{player['total_points']}")

                # Detailed stats
                col7, col8, col9, col10 = st.columns(4)
                with col7:
                    st.caption(f"⚽ Góly: {player['goals_scored']}")
                with col8:
                    st.caption(f"🎯 Asistence: {player['assists']}")
                with col9:
                    st.caption(f"🛡️ Clean sheets: {player['clean_sheets']}")
                with col10:
                    st.caption(f"⏱️ Minuty: {player['minutes']}")
                
                st.divider()

        # Value analysis chart
        if not filtered_df.empty:
            st.subheader("📊 Analýza hodnoty za peníze")
            
            # Value per million calculation
            filtered_df['value_per_million'] = filtered_df['predicted_points'] / filtered_df['price']
            top_value = filtered_df.nlargest(15, 'value_per_million')
            
            fig = px.scatter(
                top_value,
                x='price',
                y='predicted_points',
                size='selected_by_percent',
                color='position',
                hover_name='name',
                hover_data={'team': True, 'total_points': True},
                title="Cena vs Predikované body (velikost = vlastnictví %)",
                labels={'price': 'Cena (£m)', 'predicted_points': 'Predikované body'}
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white')
            )
            st.plotly_chart(fig, use_container_width=True)

    # Tab: Top hráči podle ceny
    elif selected_tab == "Top hráči podle ceny":
        st.header("💰 Nejlepší value za peníze")
        
        # Value categories
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
                (players_df['price'] < max_price) &
                (players_df['minutes'] > 500)  # Jen hráči s dostatečnými minutami
            ].copy()
            
            if not category_players.empty:
                # Value calculation
                category_players['value_score'] = (
                    category_players['predicted_points'] * 0.4 +
                    category_players['total_points'] / 10 * 0.3 +
                    (100 - category_players['selected_by_percent']) / 100 * 0.3  # Bonus za low ownership
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
                        st.metric("Body/zápas", f"{player['points_per_game']:.1f}")
                    with col4:
                        st.metric("Vlastnictví", f"{player['selected_by_percent']:.1f}%")
            else:
                st.info("Žádní hráči v této kategorii s dostatečnými minutami.")

    # Tab: Fixture analýza
    elif selected_tab == "Fixture analýza":
        st.header("📅 Analýza nadcházejících zápasů")
        
        if fixtures_df.empty:
            st.warning("Data o zápasech nejsou k dispozici.")
            return
        
        # Current gameweek fixtures
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
            # Calculate average difficulty for each team
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
        
        # Most transferred in/out
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Nejvíce přiváděni")
            most_transferred_in = players_df.nlargest(10, 'transfers_in')
            
            for _, player in most_transferred_in.iterrows():
                delta_color = "normal"
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
        
        # Get players with significant transfer activity
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
        
        # Team performance analysis
        team_stats = []
        for team_id, team_name in teams_dict.items():
            team_players = players_df[players_df['team'] == team_name]
            
            if not team_players.empty:
                team_stats.append({
                    'team': team_name,
                    'total_points': team_players['total_points'].sum(),
                    'avg_price': team_players['price'].mean(),
                    'players_count': len(team_players),
                    'top_scorer': team_players.loc[team_players['total_points'].idxmax(), 'name'],
                    'top_scorer_points': team_players['total_points'].max(),
                    'most_selected': team_players.loc[team_players['selected_by_percent'].idxmax(), 'name'],
                    'highest_selection': team_players['selected_by_percent'].max()
                })
        
        if team_stats:
            team_df = pd.DataFrame(team_stats)
            team_df = team_df.sort_values('total_points', ascending=False)
            
            # Top teams by total points
            st.subheader("🏆 Nejlepší týmy podle celkových bodů")
            
            fig = px.bar(
                team_df.head(10),
                x='team',
                y='total_points',
                title="Celkové body všech hráčů týmu",
                color='total_points',
                color_continuous_scale='viridis'
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Team details table
            st.subheader("📋 Detaily týmů")
            
            display_df = team_df[['team', 'total_points', 'avg_price', 'top_scorer', 'top_scorer_points', 'most_selected', 'highest_selection']].copy()
            display_df.columns = ['Tým', 'Celkem bodů', 'Průměrná cena', 'Nejlepší střelec', 'Body nejlepšího', 'Nejvíc vlastněný', 'Vlastnictví %']
            display_df['Průměrná cena'] = display_df['Průměrná cena'].round(1)
            display_df['Vlastnictví %'] = display_df['Vlastnictví %'].round(1)
            
            st.dataframe(display_df, use_container_width=True)

    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align: center; color: #64748b; padding: 2rem;'>
        <p>🏆 FPL Predictor - Live Data z FPL API</p>
        <p>Poslední update: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
        <p><small>Data se aktualizují každých 5 minut</small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
