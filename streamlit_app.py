import React, { useState, useEffect } from 'react';
import { Search, TrendingUp, Users, Calendar, Star, Target, BarChart3, Zap } from 'lucide-react';

// Aktuální data pro sezónu 2025/26 s betting odds insights
const mockPlayers = [
  { 
    id: 1, 
    name: "Mohamed Salah", 
    team: "Liverpool", 
    position: "Midfielder", 
    price: 14.5, 
    total_points: 344, 
    form: 9.1, 
    selected_by_percent: 63.4, 
    predicted_points: 13.8, // Zvýšeno - Golden Boot winner 29 goals + 18 assists
    next5fixtures: [
      { points: 9.2, opponent: "BOU", isHome: true, gw: 1 },    // Easy home vs Bournemouth
      { points: 12.8, opponent: "new", isHome: false, gw: 2 },  // Good fixture away
      { points: 8.1, opponent: "ARS", isHome: true, gw: 3 },    // Big game vs Arsenal
      { points: 10.5, opponent: "bur", isHome: false, gw: 4 },  // vs promoted side
      { points: 12.1, opponent: "EVE", isHome: true, gw: 5 }    // Home derby
    ]
  },
  { 
    id: 2, 
    name: "Erling Haaland", 
    team: "Man City", 
    position: "Forward", 
    price: 14.0, 
    total_points: 181, 
    form: 7.3, 
    selected_by_percent: 45.8, 
    predicted_points: 11.2, // Betting favorite 1.0 odds pro Golden Boot
    next5fixtures: [
      { points: 5.8, opponent: "wol", isHome: false, gw: 1 },   // Away at Wolves - tough start
      { points: 11.5, opponent: "TOT", isHome: true, gw: 2 },   // Home vs Spurs
      { points: 13.8, opponent: "bri", isHome: false, gw: 3 },  // Away vs Brighton - should score
      { points: 9.2, opponent: "MUN", isHome: true, gw: 4 },    // Derby at home
      { points: 11.8, opponent: "ARS", isHome: false, gw: 5 }   // Big away game
    ]
  },
  { 
    id: 3, 
    name: "Alexander Isak", 
    team: "Newcastle", 
    position: "Forward", 
    price: 10.5, 
    total_points: 211, 
    form: 8.6, 
    selected_by_percent: 38.2, 
    predicted_points: 12.8, // Excellent value - 23 goals last season, 8.5 odds for Golden Boot
    next5fixtures: [
      { points: 10.1, opponent: "AVL", isHome: false, gw: 1 },  // Away at Villa
      { points: 9.2, opponent: "LIV", isHome: true, gw: 2 },    // Big home game vs Liverpool
      { points: 12.1, opponent: "lee", isHome: false, gw: 3 },  // Away vs promoted Leeds
      { points: 8.3, opponent: "WOL", isHome: true, gw: 4 },    // Home vs Wolves
      { points: 11.2, opponent: "bou", isHome: false, gw: 5 }   // Away vs Bournemouth
    ]
  },
  { 
    id: 4, 
    name: "Cole Palmer", 
    team: "Chelsea", 
    position: "Midfielder", 
    price: 10.5, 
    total_points: 198, 
    form: 7.9, 
    selected_by_percent: 32.7, 
    predicted_points: 10.1, // Consistent performer, good fixtures
    next5fixtures: [
      { points: 8.8, opponent: "CRY", isHome: true, gw: 1 },    // Home vs Palace
      { points: 9.9, opponent: "whu", isHome: false, gw: 2 },   // Away vs West Ham
      { points: 7.2, opponent: "FUL", isHome: true, gw: 3 },    // Home vs Fulham
      { points: 11.8, opponent: "BRE", isHome: false, gw: 4 },  // Away vs Brentford
      { points: 9.5, opponent: "mun", isHome: false, gw: 5 }    // Away vs Man United
    ]
  },
  { 
    id: 5, 
    name: "Bukayo Saka", 
    team: "Arsenal", 
    position: "Midfielder", 
    price: 10.0, 
    total_points: 165, 
    form: 7.2, 
    selected_by_percent: 29.8, 
    predicted_points: 9.5, // Solid but tough early fixtures
    next5fixtures: [
      { points: 9.8, opponent: "mun", isHome: false, gw: 1 },   // Away vs Man United - tough
      { points: 8.1, opponent: "BRI", isHome: true, gw: 2 },    // Home vs Brighton
      { points: 8.9, opponent: "liv", isHome: false, gw: 3 },   // Away vs Liverpool - very tough
      { points: 7.2, opponent: "NFO", isHome: false, gw: 4 },   // Away vs Forest
      { points: 11.8, opponent: "MCI", isHome: true, gw: 5 }    // Home vs City - big game
    ]
  },
  { 
    id: 6, 
    name: "Florian Wirtz", 
    team: "Liverpool", 
    position: "Midfielder", 
    price: 8.5, 
    total_points: 0, 
    form: 8.0, 
    selected_by_percent: 15.3, 
    predicted_points: 8.8, // New signing uncertainty
    next5fixtures: [
      { points: 7.5, opponent: "BOU", isHome: true, gw: 1 },    // Rotation risk with Salah
      { points: 9.8, opponent: "new", isHome: false, gw: 2 },   // Could start if rested Salah
      { points: 6.5, opponent: "ARS", isHome: true, gw: 3 },    // Big game - likely benched
      { points: 9.2, opponent: "bur", isHome: false, gw: 4 },   // Good opportunity vs promoted
      { points: 10.1, opponent: "EVE", isHome: true, gw: 5 }    // Derby - could be rotated in
    ]
  },
  { 
    id: 7, 
    name: "Bryan Mbeumo", 
    team: "Brentford", 
    position: "Midfielder", 
    price: 8.0, 
    total_points: 234, 
    form: 8.4, 
    selected_by_percent: 42.1, 
    predicted_points: 9.8, // 20 goals last season, great value
    next5fixtures: [
      { points: 8.8, opponent: "nfo", isHome: false, gw: 1 },   // Away vs Forest
      { points: 7.9, opponent: "AVL", isHome: false, gw: 2 },   // Away vs Villa
      { points: 10.5, opponent: "SUN", isHome: true, gw: 3 },   // Home vs promoted Sunderland
      { points: 7.1, opponent: "CHE", isHome: true, gw: 4 },    // Home vs Chelsea
      { points: 9.2, opponent: "FUL", isHome: false, gw: 5 }    // Away vs Fulham
    ]
  },
  { 
    id: 8, 
    name: "Jarrod Bowen", 
    team: "West Ham", 
    position: "Forward", 
    price: 8.0, 
    total_points: 156, 
    form: 7.5, 
    selected_by_percent: 18.9, 
    predicted_points: 8.1, // Consistent but not explosive
    next5fixtures: [
      { points: 7.8, opponent: "sun", isHome: false, gw: 1 },   // Away vs Sunderland
      { points: 8.5, opponent: "CHE", isHome: true, gw: 2 },    // Home vs Chelsea
      { points: 6.9, opponent: "nfo", isHome: false, gw: 3 },   // Away vs Forest
      { points: 9.2, opponent: "TOT", isHome: false, gw: 4 },   // Away vs Spurs
      { points: 7.4, opponent: "cry", isHome: false, gw: 5 }    // Away vs Palace
    ]
  }
];

const mockFixtures = [
  { id: 1, home_team: "Liverpool", away_team: "Bournemouth", difficulty: 2, gameweek: 1, date: "15 Aug" },
  { id: 2, home_team: "Aston Villa", away_team: "Newcastle", difficulty: 3, gameweek: 1, date: "16 Aug" },
  { id: 3, home_team: "Chelsea", away_team: "Crystal Palace", difficulty: 2, gameweek: 1, date: "17 Aug" },
  { id: 4, home_team: "Man United", away_team: "Arsenal", difficulty: 4, gameweek: 1, date: "17 Aug" },
  { id: 5, home_team: "Tottenham", away_team: "Burnley", difficulty: 2, gameweek: 1, date: "16 Aug" }
];

const FPLPredictor = () => {
  const [activeTab, setActiveTab] = useState('predictions');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedPosition, setSelectedPosition] = useState('all');
  const [isLoading, setIsLoading] = useState(false);

  const filteredPlayers = mockPlayers.filter(player => 
    player.name.toLowerCase().includes(searchTerm.toLowerCase()) &&
    (selectedPosition === 'all' || player.position.toLowerCase().includes(selectedPosition.toLowerCase()))
  );

  const getPositionColor = (position) => {
    switch (position) {
      case 'Forward': return 'bg-red-100 text-red-800';
      case 'Midfielder': return 'bg-green-100 text-green-800';
      case 'Defender': return 'bg-blue-100 text-blue-800';
      case 'Goalkeeper': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getDifficultyColor = (difficulty) => {
    if (difficulty <= 2) return 'bg-green-500';
    if (difficulty === 3) return 'bg-yellow-500';
    if (difficulty === 4) return 'bg-orange-500';
    return 'bg-red-500';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      {/* Header */}
      <div className="bg-white/10 backdrop-blur-md border-b border-white/20">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
                <BarChart3 className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">FPL Predictor</h1>
                <p className="text-purple-200 text-sm">Gameweek 1 • 2025/26 Season</p>
              </div>
            </div>
            <div className="flex space-x-2">
              <button className="px-4 py-2 bg-white/20 text-white rounded-lg hover:bg-white/30 transition-colors">
                <Zap className="w-4 h-4 inline mr-2" />
                Live Update
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-6 py-8">
        {/* Navigation Tabs */}
        <div className="flex space-x-1 mb-8 bg-white/10 backdrop-blur-md p-1 rounded-xl">
          {[
            { id: 'predictions', label: 'Predikce bodů', icon: TrendingUp },
            { id: 'myteam', label: 'Můj doporučený tým', icon: Target },
            { id: 'fixtures', label: 'Fixture analýza', icon: Calendar },
            { id: 'captain', label: 'Doporučení kapitána', icon: Star },
            { id: 'transfers', label: 'Transfer tips', icon: Users }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 px-6 py-3 rounded-lg transition-all duration-200 ${
                activeTab === tab.id
                  ? 'bg-white text-purple-900 shadow-lg'
                  : 'text-white hover:bg-white/10'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              <span className="font-medium">{tab.label}</span>
            </button>
          ))}
        </div>

        {/* My Team Tab */}
        {activeTab === 'myteam' && (
          <div className="space-y-6">
            {/* Formation Display */}
            <div className="bg-gradient-to-r from-green-900/50 via-green-800/30 to-green-900/50 rounded-2xl p-8 border border-green-500/30 relative overflow-hidden">
              <div className="absolute inset-0 opacity-10">
                <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-32 h-32 bg-white rounded-full"></div>
                <div className="absolute bottom-0 left-0 w-full h-1 bg-white"></div>
                <div className="absolute top-0 left-0 w-full h-1 bg-white"></div>
                <div className="absolute top-0 left-0 w-1 h-full bg-white"></div>
                <div className="absolute top-0 right-0 w-1 h-full bg-white"></div>
              </div>
              
              <h2 className="text-2xl font-bold text-white mb-6 text-center relative z-10">
                Doporučená sestava (3-5-2) • £100.0m
              </h2>
              
              {/* Formation Layout */}
              <div className="relative z-10 space-y-8">
                {/* Forwards */}
                <div className="flex justify-center space-x-12">
                  {[
                    { name: "Isak", price: "10.5", team: "NEW", next5: [
                      { points: 9.1, opponent: "FUL", isHome: true },
                      { points: 8.7, opponent: "whu", isHome: false },
                      { points: 11.3, opponent: "BUR", isHome: true },
                      { points: 7.5, opponent: "liv", isHome: true },
                      { points: 10.2, opponent: "bre", isHome: false }
                    ]},
                    { name: "Bowen", price: "8.0", team: "WHU", next5: [
                      { points: 7.2, opponent: "bou", isHome: false },
                      { points: 8.9, opponent: "NEW", isHome: true },
                      { points: 6.4, opponent: "tot", isHome: false },
                      { points: 9.1, opponent: "SUN", isHome: true },
                      { points: 7.8, opponent: "BUR", isHome: false }
                    ]}
                  ].map((player, i) => (
                    <div key={i} className="text-center">
                      <div className="w-16 h-16 bg-red-600 rounded-full flex items-center justify-center mb-2 border-2 border-white">
                        <span className="text-white font-bold text-xs">{player.team}</span>
                      </div>
                      <div className="text-white font-semibold text-sm">{player.name}</div>
                      <div className="text-green-300 text-xs mb-3">£{player.price}m</div>
                      {/* Enhanced prediction bars */}
                      <div className="grid grid-cols-5 gap-1">
                        {player.next5.map((fixture, j) => (
                          <div key={j} className="text-center">
                            <div className="text-xs font-medium text-gray-300 mb-1">
                              {fixture.isHome 
                                ? fixture.opponent.toUpperCase() 
                                : fixture.opponent.toLowerCase()
                              }
                            </div>
                            <div 
                              className={`h-4 w-4 rounded-md mx-auto mb-1 ${
                                fixture.points >= 10 ? 'bg-green-500' : 
                                fixture.points >= 7 ? 'bg-yellow-500' : 
                                fixture.points >= 5 ? 'bg-orange-500' : 'bg-red-500'
                              }`}
                            ></div>
                            <div className="text-xs font-semibold text-white">{fixture.points}</div>
                            <div className="text-xs text-purple-300 font-medium">
                              GW{fixture.gw}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* Midfielders */}
                <div className="flex justify-center space-x-6">
                  {[
                    { name: "Salah", price: "14.5", team: "LIV", next5: [
                      { points: 8.5, opponent: "SUN", isHome: true },
                      { points: 12.1, opponent: "bre", isHome: false },
                      { points: 7.2, opponent: "MUN", isHome: true },
                      { points: 9.8, opponent: "new", isHome: false },
                      { points: 11.4, opponent: "BUR", isHome: true }
                    ]},
                    { name: "Palmer", price: "10.5", team: "CHE", next5: [
                      { points: 8.3, opponent: "BRI", isHome: true },
                      { points: 9.7, opponent: "SUN", isHome: false },
                      { points: 6.8, opponent: "ars", isHome: false },
                      { points: 11.2, opponent: "LEE", isHome: true },
                      { points: 9.1, opponent: "EVE", isHome: false }
                    ]},
                    { name: "Saka", price: "10.0", team: "ARS", next5: [
                      { points: 11.2, opponent: "BUR", isHome: true },
                      { points: 7.8, opponent: "lee", isHome: false },
                      { points: 9.4, opponent: "CHE", isHome: true },
                      { points: 6.7, opponent: "mci", isHome: true },
                      { points: 10.3, opponent: "SUN", isHome: false }
                    ]},
                    { name: "Wirtz", price: "8.5", team: "LIV", next5: [
                      { points: 7.8, opponent: "SUN", isHome: true },
                      { points: 10.5, opponent: "bre", isHome: false },
                      { points: 6.2, opponent: "MUN", isHome: true },
                      { points: 8.9, opponent: "new", isHome: false },
                      { points: 9.7, opponent: "BUR", isHome: true }
                    ]},
                    { name: "Mbeumo", price: "8.0", team: "BRE", next5: [
                      { points: 8.1, opponent: "cry", isHome: false },
                      { points: 7.3, opponent: "LIV", isHome: true },
                      { points: 9.8, opponent: "LEE", isHome: false },
                      { points: 6.5, opponent: "mci", isHome: false },
                      { points: 8.9, opponent: "new", isHome: true }
                    ]}
                  ].map((player, i) => (
                    <div key={i} className="text-center">
                      <div className="w-14 h-14 bg-green-600 rounded-full flex items-center justify-center mb-2 border-2 border-white">
                        <span className="text-white font-bold text-xs">{player.team}</span>
                      </div>
                      <div className="text-white font-semibold text-sm">{player.name}</div>
                      <div className="text-green-300 text-xs mb-3">£{player.price}m</div>
                      {/* Enhanced prediction bars */}
                      <div className="grid grid-cols-5 gap-1">
                        {player.next5.map((fixture, j) => (
                          <div key={j} className="text-center">
                            <div className="text-xs font-medium text-gray-300 mb-1">
                              {fixture.isHome 
                                ? fixture.opponent.toUpperCase() 
                                : fixture.opponent.toLowerCase()
                              }
                            </div>
                            <div 
                              className={`h-4 w-4 rounded-md mx-auto mb-1 ${
                                fixture.points >= 10 ? 'bg-green-500' : 
                                fixture.points >= 7 ? 'bg-yellow-500' : 
                                fixture.points >= 5 ? 'bg-orange-500' : 'bg-red-500'
                              }`}
                            ></div>
                            <div className="text-xs font-semibold text-white">{fixture.points}</div>
                            <div className="text-xs text-gray-400">
                              {fixture.isHome ? '🏠' : '✈️'}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* Defenders */}
                <div className="flex justify-center space-x-12">
                  {[
                    { name: "Gabriel", price: "6.0", team: "ARS", next5: [
                      { points: 6.2, opponent: "mun", isHome: false, gw: 1 },
                      { points: 7.8, opponent: "BRI", isHome: true, gw: 2 },
                      { points: 5.1, opponent: "liv", isHome: false, gw: 3 },
                      { points: 8.3, opponent: "NFO", isHome: false, gw: 4 },
                      { points: 6.9, opponent: "MCI", isHome: true, gw: 5 }
                    ]},
                    { name: "Ait-Nouri", price: "5.5", team: "MCI", next5: [
                      { points: 7.1, opponent: "wol", isHome: false, gw: 1 },
                      { points: 8.4, opponent: "TOT", isHome: true, gw: 2 },
                      { points: 6.7, opponent: "bri", isHome: false, gw: 3 },
                      { points: 9.2, opponent: "MUN", isHome: true, gw: 4 },
                      { points: 7.6, opponent: "ARS", isHome: false, gw: 5 }
                    ]},
                    { name: "Esteve", price: "4.0", team: "BUR", next5: [
                      { points: 4.2, opponent: "TOT", isHome: false, gw: 1 },
                      { points: 3.8, opponent: "sun", isHome: false, gw: 2 },
                      { points: 5.6, opponent: "MUN", isHome: false, gw: 3 },
                      { points: 4.1, opponent: "LIV", isHome: true, gw: 4 },
                      { points: 5.3, opponent: "NFO", isHome: false, gw: 5 }
                    ]}
                  ].map((player, i) => (
                    <div key={i} className="text-center">
                      <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mb-2 border-2 border-white">
                        <span className="text-white font-bold text-sm">{player.team}</span>
                      </div>
                      <div className="text-white font-semibold text-sm">{player.name}</div>
                      <div className="text-green-300 text-xs mb-3">£{player.price}m</div>
                      {/* Enhanced prediction bars */}
                      <div className="grid grid-cols-5 gap-1">
                        {player.next5.map((fixture, j) => (
                          <div key={j} className="text-center">
                            <div className="text-xs font-medium text-gray-300 mb-1">
                              {fixture.isHome 
                                ? fixture.opponent.toUpperCase() 
                                : fixture.opponent.toLowerCase()
                              }
                            </div>
                            <div 
                              className={`h-4 w-4 rounded-md mx-auto mb-1 ${
                                fixture.points >= 10 ? 'bg-green-500' : 
                                fixture.points >= 7 ? 'bg-yellow-500' : 
                                fixture.points >= 5 ? 'bg-orange-500' : 'bg-red-500'
                              }`}
                            ></div>
                            <div className="text-xs font-semibold text-white">{fixture.points}</div>
                            <div className="text-xs text-purple-300 font-medium">
                              GW{fixture.gw}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* Goalkeeper */}
                <div className="flex justify-center">
                  <div className="text-center">
                    <div className="w-20 h-20 bg-yellow-600 rounded-full flex items-center justify-center mb-2 border-2 border-white">
                      <span className="text-white font-bold text-sm">EVE</span>
                    </div>
                    <div className="text-white font-semibold text-sm">Pickford</div>
                    <div className="text-green-300 text-xs mb-3">£5.0m</div>
                    {/* Enhanced prediction bars */}
                    <div className="grid grid-cols-5 gap-1">
                      {[
                        { points: 5.8, opponent: "BRI", isHome: true, gw: 1 },
                        { points: 6.4, opponent: "tot", isHome: false, gw: 2 },
                        { points: 4.9, opponent: "WOL", isHome: true, gw: 3 },
                        { points: 7.1, opponent: "AVL", isHome: false, gw: 4 },
                        { points: 6.2, opponent: "LIV", isHome: false, gw: 5 }
                      ].map((fixture, j) => (
                        <div key={j} className="text-center">
                          <div className="text-xs font-medium text-gray-300 mb-1">
                            {fixture.isHome 
                              ? fixture.opponent.toUpperCase() 
                              : fixture.opponent.toLowerCase()
                            }
                          </div>
                          <div 
                            className={`h-4 w-4 rounded-md mx-auto mb-1 ${
                              fixture.points >= 10 ? 'bg-green-500' : 
                              fixture.points >= 7 ? 'bg-yellow-500' : 
                              fixture.points >= 5 ? 'bg-orange-500' : 'bg-red-500'
                            }`}
                          ></div>
                          <div className="text-xs font-semibold text-white">{fixture.points}</div>
                          <div className="text-xs text-purple-300 font-medium">
                            GW{fixture.gw}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Bench */}
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20">
              <h3 className="text-lg font-bold text-white mb-4 text-center">🪑 Lavička</h3>
              <div className="flex justify-center space-x-8">
                {[
                  { name: "Kelleher", price: "4.5", team: "BRE", pos: "GK" },
                  { name: "Esteve", price: "4.0", team: "BUR", pos: "DEF" },
                  { name: "Mundle", price: "5.0", team: "SUN", pos: "MID" },
                  { name: "Archer", price: "4.5", team: "SOU", pos: "FWD" }
                ].map((player, i) => (
                  <div key={i} className="text-center">
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-2 border-2 border-gray-300 ${
                      player.pos === 'GK' ? 'bg-yellow-500' :
                      player.pos === 'DEF' ? 'bg-blue-500' :
                      player.pos === 'MID' ? 'bg-green-500' : 'bg-red-500'
                    }`}>
                      <span className="text-white font-bold text-xs">{player.team}</span>
                    </div>
                    <div className="text-white font-medium text-sm">{player.name}</div>
                    <div className="text-gray-400 text-xs">£{player.price}m</div>
                    <div className="text-gray-500 text-xs">{player.pos}</div>
                  </div>
                ))}
              </div>
              <div className="text-center mt-4">
                <span className="text-purple-200 text-sm">Levní hráči z nováčků: Burnley, Leeds, Sunderland</span>
              </div>
            </div>

            {/* Team Value Breakdown */}
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20">
              <h3 className="text-lg font-bold text-white mb-4">💰 Rozpis rozpočtu</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-yellow-400">£9.5m</div>
                  <div className="text-sm text-gray-300">Brankáři</div>
                  <div className="text-xs text-gray-400">Pickford + Kelleher</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-400">£19.5m</div>
                  <div className="text-sm text-gray-300">Obránci</div>
                  <div className="text-xs text-gray-400">3 + 2 na lavičce</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-400">£57.5m</div>
                  <div className="text-sm text-gray-300">Záložníci</div>
                  <div className="text-xs text-gray-400">5 + 1 na lavičce</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-400">£23.0m</div>
                  <div className="text-sm text-gray-300">Útočníci</div>
                  <div className="text-xs text-gray-400">2 + 1 na lavičce</div>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-white/20 text-center">
                <span className="text-lg font-bold text-white">Celkem: £100.0m / £100.0m</span>
                <div className="text-green-400 text-sm">✓ Rozpočet vyčerpán</div>
              </div>
            </div>

            {/* Strategy for 5 Gameweeks */}
            <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 overflow-hidden">
              <div className="p-6 border-b border-white/20">
                <h2 className="text-xl font-bold text-white mb-2">Strategie na 5 gameweeks dopředu</h2>
                <p className="text-purple-200">Plánované tahy a reasoning</p>
              </div>
              
              <div className="divide-y divide-white/10">
                {/* GW1 */}
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-white font-bold text-sm">1</div>
                      <h3 className="text-lg font-semibold text-white">Gameweek 1 (15. srpna)</h3>
                    </div>
                    <span className="text-green-400 font-semibold">START SEZÓNY</span>
                  </div>
                  <div className="bg-white/5 rounded-lg p-4">
                    <h4 className="text-white font-medium mb-2">💡 Strategie:</h4>
                    <p className="text-purple-200 text-sm mb-3">Začínáme s balanced týmem. Salah (C) vs Sunderland, Isak vs Fulham, Palmer vs Brighton. Formace 3-5-2 pro maximální záložníky.</p>
                    <div className="flex space-x-4 text-sm">
                      <span className="text-green-400">✓ Kapitán: Salah</span>
                      <span className="text-blue-400">→ Žádné transfery</span>
                    </div>
                  </div>
                </div>

                {/* GW2 */}
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold text-sm">2</div>
                      <h3 className="text-lg font-semibold text-white">Gameweek 2</h3>
                    </div>
                    <span className="text-blue-400 font-semibold">VYHODNOCENÍ</span>
                  </div>
                  <div className="bg-white/5 rounded-lg p-4">
                    <h4 className="text-white font-medium mb-2">🔄 Plán:</h4>
                    <p className="text-purple-200 text-sm mb-3">Sledujeme formu po GW1. Pokud Wirtz nedostává minuty (rotace s Salah), zvážíme transfer. Haaland má lepší fixtures od GW2.</p>
                    <div className="flex space-x-4 text-sm">
                      <span className="text-orange-400">? Kapitán: Salah/Isak</span>
                      <span className="text-yellow-400">⚠ Možný transfer: Wirtz → jiný</span>
                    </div>
                  </div>
                </div>

                {/* GW3 */}
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center text-white font-bold text-sm">3</div>
                      <h3 className="text-lg font-semibold text-white">Gameweek 3</h3>
                    </div>
                    <span className="text-purple-400 font-semibold">ADAPTACE</span>
                  </div>
                  <div className="bg-white/5 rounded-lg p-4">
                    <h4 className="text-white font-medium mb-2">🎯 Akce:</h4>
                    <p className="text-purple-200 text-sm mb-3">Přidáváme Haalanda pokud má dobré fixtures. Možná OUT: Wirtz (pokud nedostává minuty), IN: proven Premier League hráč.</p>
                    <div className="flex space-x-4 text-sm">
                      <span className="text-green-400">→ IN: Haaland (pokud má formu)</span>
                      <span className="text-red-400">← OUT: Mbeumo/Wirtz (podle formy)</span>
                    </div>
                  </div>
                </div>

                {/* GW4 */}
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center text-white font-bold text-sm">4</div>
                      <h3 className="text-lg font-semibold text-white">Gameweek 4</h3>
                    </div>
                    <span className="text-yellow-400 font-semibold">OPTIMALIZACE</span>
                  </div>
                  <div className="bg-white/5 rounded-lg p-4">
                    <h4 className="text-white font-medium mb-2">⚡ Zaměření:</h4>
                    <p className="text-purple-200 text-sm mb-3">Fixture swing týden - sledujeme, kdo má nejlepší zápasy v GW5-8. Připravujeme se na první busy period.</p>
                    <div className="flex space-x-4 text-sm">
                      <span className="text-blue-400">📊 Analýza fixtures GW5-8</span>
                      <span className="text-green-400">💰 Bank transfer pro GW5</span>
                    </div>
                  </div>
                </div>

                {/* GW5 */}
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-red-500 rounded-full flex items-center justify-center text-white font-bold text-sm">5</div>
                      <h3 className="text-lg font-semibold text-white">Gameweek 5</h3>
                    </div>
                    <span className="text-red-400 font-semibold">PRVNÍ WILDCARD?</span>
                  </div>
                  <div className="bg-white/5 rounded-lg p-4">
                    <h4 className="text-white font-medium mb-2">🃏 Rozhodnutí:</h4>
                    <p className="text-purple-200 text-sm mb-3">Buď používáme první Wildcard pro major restructure, nebo pokračujeme s 1FT. Závisí na tom, kolik hráčů nedává výsledky.</p>
                    <div className="flex space-x-4 text-sm">
                      <span className="text-red-400">🃏 Wildcard (pokud 4+ změn)</span>
                      <span className="text-blue-400">📈 Nebo standard 1FT</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Key Principles */}
            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-gradient-to-r from-blue-500/20 to-cyan-500/20 rounded-xl p-6 border border-blue-500/30">
                <h3 className="text-blue-400 font-semibold text-lg mb-4 flex items-center">
                  <Target className="w-5 h-5 mr-2" />
                  Klíčové principy
                </h3>
                <ul className="space-y-2 text-blue-100 text-sm">
                  <li>• Vždy vlastnit Salaha (nejkonzistentnější)</li>
                  <li>• Rotovat mezi Haaland/Isak podle fixtures</li>
                  <li>• Využívat nováčky - Sunderland, Burnley, Leeds</li>
                  <li>• Double Liverpool když mají dobré fixtures</li>
                </ul>
              </div>

              <div className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-xl p-6 border border-purple-500/30">
                <h3 className="text-purple-400 font-semibold text-lg mb-4 flex items-center">
                  <Zap className="w-5 h-5 mr-2" />
                  Chip strategie
                </h3>
                <ul className="space-y-2 text-purple-100 text-sm">
                  <li>• Wildcard 1: GW5-8 (podle potřeby)</li>
                  <li>• Triple Captain: vs nováčci v DGW</li>
                  <li>• Bench Boost: GW1 nebo DGW</li>
                  <li>• Free Hit: proti bad fixtures</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Predictions Tab */}
        {activeTab === 'predictions' && (
          <div className="space-y-6">
            {/* Filters */}
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20">
              <div className="flex flex-col md:flex-row gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <input
                      type="text"
                      placeholder="Hledat hráče..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full pl-10 pr-4 py-3 bg-white/20 border border-white/30 rounded-lg text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </div>
                </div>
                <select
                  value={selectedPosition}
                  onChange={(e) => setSelectedPosition(e.target.value)}
                  className="px-4 py-3 bg-white/20 border border-white/30 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="all">Všechny pozice</option>
                  <option value="goalkeeper">Brankář</option>
                  <option value="defender">Obránce</option>
                  <option value="midfielder">Záložník</option>
                  <option value="forward">Útočník</option>
                </select>
              </div>
            </div>

            {/* Top Predictions */}
            <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 overflow-hidden">
              <div className="p-6 border-b border-white/20">
                <h2 className="text-xl font-bold text-white mb-2">Top predikce na Gameweek 1</h2>
                <p className="text-purple-200">Hráči s nejvyšší predikovanými body pro start sezóny 2025/26</p>
              </div>
              
              <div className="divide-y divide-white/10">
                {filteredPlayers
                  .sort((a, b) => b.predicted_points - a.predicted_points)
                  .slice(0, 10)
                  .map((player, index) => (
                  <div key={player.id} className="p-6 hover:bg-white/5 transition-colors">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="flex-shrink-0">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                            index < 3 ? 'bg-gradient-to-r from-yellow-400 to-yellow-600 text-yellow-900' : 'bg-white/20 text-white'
                          }`}>
                            {index + 1}
                          </div>
                        </div>
                        <div className="flex-1">
                          <h3 className="font-semibold text-white">{player.name}</h3>
                          <div className="flex items-center space-x-3 mt-1">
                            <span className="text-purple-200 text-sm">{player.team}</span>
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPositionColor(player.position)}`}>
                              {player.position}
                            </span>
                          </div>
                          {/* 5 fixtures prediction bar */}
                          <div className="mt-3">
                            <div className="text-xs text-purple-200 mb-2">Příštích 5 zápasů:</div>
                            <div className="grid grid-cols-5 gap-2">
                              {player.next5fixtures.map((fixture, i) => (
                                <div key={i} className="text-center">
                                  <div className="text-xs font-medium text-gray-300 mb-1">
                                    {fixture.isHome 
                                      ? fixture.opponent.toUpperCase() 
                                      : fixture.opponent.toLowerCase()
                                    }
                                  </div>
                                  <div 
                                    className={`h-6 rounded-md mb-1 ${
                                      fixture.points >= 10 ? 'bg-green-500' : 
                                      fixture.points >= 7 ? 'bg-yellow-500' : 
                                      fixture.points >= 5 ? 'bg-orange-500' : 'bg-red-500'
                                    }`}
                                    style={{ opacity: Math.max(0.6, fixture.points / 15) }}
                                  ></div>
                                  <div className="text-xs font-semibold text-white">{fixture.points}</div>
                                  <div className="text-xs text-purple-300 font-medium">
                                    GW{fixture.gw}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-6">
                        <div className="text-center">
                          <div className="text-2xl font-bold text-green-400">{player.predicted_points}</div>
                          <div className="text-xs text-purple-200">Predikce</div>
                        </div>
                        <div className="text-center">
                          <div className="text-white font-semibold">{player.form}</div>
                          <div className="text-xs text-purple-200">Forma</div>
                        </div>
                        <div className="text-center">
                          <div className="text-white font-semibold">£{player.price}m</div>
                          <div className="text-xs text-purple-200">Cena</div>
                        </div>
                        <div className="text-center">
                          <div className="text-white font-semibold">{player.selected_by_percent}%</div>
                          <div className="text-xs text-purple-200">Vlastnictví</div>
                        </div>
                        <div className="text-center">
                          <div className="text-white font-semibold">{player.total_points}</div>
                          <div className="text-xs text-purple-200">Celkem</div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Captain Recommendations Tab */}
        {activeTab === 'captain' && (
          <div className="space-y-6">
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20">
              <h2 className="text-xl font-bold text-white mb-4">Doporučení kapitána pro Gameweek 1</h2>
              
              <div className="bg-gradient-to-r from-yellow-400/20 to-yellow-600/20 rounded-xl p-4 mb-6 border border-yellow-500/30">
                <div className="flex items-center space-x-2 text-yellow-200">
                  <Star className="w-4 h-4" />
                  <span className="text-sm font-medium">Nová sezóna 2025/26 - Začínáme od nuly!</span>
                </div>
              </div>
              
              <div className="grid gap-4">
                {mockPlayers.slice(0, 3).map((player, index) => (
                  <div key={player.id} className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-xl p-6 border border-white/20">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="w-12 h-12 bg-gradient-to-r from-yellow-400 to-yellow-600 rounded-full flex items-center justify-center">
                          <Target className="w-6 h-6 text-yellow-900" />
                        </div>
                        <div>
                          <h3 className="font-bold text-white text-lg">{player.name}</h3>
                          <p className="text-purple-200">{player.team} • {player.position}</p>
                        </div>
                      </div>
                      
                      <div className="text-right">
                        <div className="text-3xl font-bold text-green-400">{(player.predicted_points * 2).toFixed(1)}</div>
                        <div className="text-purple-200 text-sm">Očekávané body (C)</div>
                      </div>
                    </div>
                    
                    <div className="mt-4 pt-4 border-t border-white/20">
                      <div className="grid grid-cols-3 gap-4 text-center">
                        <div>
                          <div className="text-white font-semibold">{player.form}/10</div>
                          <div className="text-xs text-purple-200">Forma</div>
                        </div>
                        <div>
                          <div className="text-white font-semibold">{player.selected_by_percent}%</div>
                          <div className="text-xs text-purple-200">Vlastnictví</div>
                        </div>
                        <div>
                          <div className="text-green-400 font-semibold">
                            {index === 0 ? 'Bezpečné' : index === 1 ? 'Balanced' : 'Risky'}
                          </div>
                          <div className="text-xs text-purple-200">Riziko</div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Fixtures Tab */}
        {activeTab === 'fixtures' && (
          <div className="space-y-6">
            <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 overflow-hidden">
              <div className="p-6 border-b border-white/20">
                <h2 className="text-xl font-bold text-white mb-2">Fixture analýza - Gameweek 1</h2>
                <p className="text-purple-200">První kolo sezóny 2025/26 - nováčci vs. velikáni</p>
              </div>
              
              <div className="divide-y divide-white/10">
                {mockFixtures.map((fixture) => (
                  <div key={fixture.id} className="p-6 hover:bg-white/5 transition-colors">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="text-white font-semibold text-lg">
                          {fixture.home_team} vs {fixture.away_team}
                        </div>
                        <div className={`w-4 h-4 rounded-full ${getDifficultyColor(fixture.difficulty)}`}></div>
                        <span className="text-purple-200 text-sm">
                          Obtížnost: {fixture.difficulty}/5
                        </span>
                      </div>
                      
                      <div className="flex space-x-4">
                        {fixture.difficulty <= 2 && (
                          <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-sm">
                            ✓ Doporučeno
                          </span>
                        )}
                        {fixture.difficulty >= 4 && (
                          <span className="px-3 py-1 bg-red-500/20 text-red-400 rounded-full text-sm">
                            ⚠ Opatrně
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Transfers Tab */}
        {activeTab === 'transfers' && (
          <div className="space-y-6">
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20">
              <h2 className="text-xl font-bold text-white mb-4">Transfer doporučení pro sezónu 2025/26</h2>
              <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4 mb-6">
                <div className="flex items-center space-x-2 text-blue-200">
                  <Zap className="w-4 h-4" />
                  <span className="text-sm font-medium">Novinky: 2x všechny chipy každou polovinu sezóny!</span>
                </div>
              </div>
              
              <div className="grid md:grid-cols-2 gap-6">
                {/* Transfer In */}
                <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-6">
                  <h3 className="text-green-400 font-semibold text-lg mb-4 flex items-center">
                    <TrendingUp className="w-5 h-5 mr-2" />
                    Transfer IN
                  </h3>
                  
                  <div className="space-y-3">
                    {/* Top predicted players NOT in current team */}
                    <div className="flex items-center justify-between bg-white/10 rounded-lg p-3">
                      <div>
                        <div className="text-white font-medium">Erling Haaland</div>
                        <div className="text-green-200 text-sm">Man City • £14.0m</div>
                      </div>
                      <div className="text-green-400 font-semibold">
                        11.8 pts
                      </div>
                    </div>
                    <div className="flex items-center justify-between bg-white/10 rounded-lg p-3">
                      <div>
                        <div className="text-white font-medium">Son Heung-min</div>
                        <div className="text-green-200 text-sm">Tottenham • £9.5m</div>
                      </div>
                      <div className="text-green-400 font-semibold">
                        9.4 pts
                      </div>
                    </div>
                    <div className="flex items-center justify-between bg-white/10 rounded-lg p-3">
                      <div>
                        <div className="text-white font-medium">Morgan Rogers</div>
                        <div className="text-green-200 text-sm">Aston Villa • £7.0m</div>
                      </div>
                      <div className="text-green-400 font-semibold">
                        8.8 pts
                      </div>
                    </div>
                  </div>
                </div>

                {/* Transfer Out */}
                <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6">
                  <h3 className="text-red-400 font-semibold text-lg mb-4 flex items-center">
                    <TrendingUp className="w-5 h-5 mr-2 rotate-180" />
                    Transfer OUT
                  </h3>
                  
                  <div className="space-y-3">
                    {/* Players from current team with poor fixtures/form */}
                    <div className="flex items-center justify-between bg-white/10 rounded-lg p-3">
                      <div>
                        <div className="text-white font-medium">Florian Wirtz</div>
                        <div className="text-red-200 text-sm">Liverpool • Rotace riziko</div>
                      </div>
                      <div className="text-red-400 font-semibold">
                        6.2 pts
                      </div>
                    </div>
                    <div className="flex items-center justify-between bg-white/10 rounded-lg p-3">
                      <div>
                        <div className="text-white font-medium">Maxime Esteve</div>
                        <div className="text-red-200 text-sm">Burnley • Těžké fixtures</div>
                      </div>
                      <div className="text-red-400 font-semibold">
                        4.2 pts
                      </div>
                    </div>
                    <div className="flex items-center justify-between bg-white/10 rounded-lg p-3">
                      <div>
                        <div className="text-white font-medium">Bryan Mbeumo</div>
                        <div className="text-red-200 text-sm">Brentford • Transfer spekulace</div>
                      </div>
                      <div className="text-red-400 font-semibold">
                        6.5 pts
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FPLPredictor;
