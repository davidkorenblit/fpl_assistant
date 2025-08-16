"""
Fixture Analyzer for FPL Assistant - FIXED VERSION
Smart caching, batch analysis ואופטימיזציה של ביצועים
"""

import pandas as pd
import numpy as np
import logging
import time
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta


class FixtureAnalyzer:
    """Analyzes fixture difficulty with smart caching and batch processing"""

    def __init__(self, fixtures_file: str = "current_fixtures.csv", teams_file: str = "current_teams.csv"):
        """Initialize Fixture Analyzer with smart caching"""

        self.logger = logging.getLogger(__name__)

        # Smart cache system
        self.smart_cache = {
            'fixtures': {},
            'teams': {},
            'batch_analysis': {},
            'gameweek_cache': {},
            'cache_timeout': 900,  # 15 minutes
            'last_cache_clean': time.time()
        }

        # Data hashes for cache invalidation
        self.data_hashes = {
            'fixtures_hash': None,
            'teams_hash': None
        }

        # Load and validate data
        self.fixtures_df = None
        self.teams_df = None
        self._load_and_validate_data(fixtures_file, teams_file)

        # Teams lookup for fast access
        self.teams_lookup = {}
        if not self.teams_df.empty:
            self._build_teams_lookup()

        # Current gameweek detection
        self.current_gameweek = self._detect_current_gameweek()
        self.logger.info(f"Fixture analyzer ready - Current gameweek: {self.current_gameweek}")

    def _load_and_validate_data(self, fixtures_file: str, teams_file: str):
        """Load data with validation and error handling"""

        # Load fixtures
        try:
            self.fixtures_df = pd.read_csv(fixtures_file)
            if not self.fixtures_df.empty:
                self._clean_fixtures_data()
                # Create fixtures hash for cache invalidation
                fixtures_str = str(len(self.fixtures_df)) + str(self.fixtures_df.columns.tolist())
                self.data_hashes['fixtures_hash'] = hashlib.md5(fixtures_str.encode()).hexdigest()
                self.logger.info(f"Loaded {len(self.fixtures_df)} fixtures")
            else:
                self.logger.warning("Fixtures file is empty")
        except Exception as e:
            self.logger.error(f"Error loading fixtures from {fixtures_file}: {e}")
            self.fixtures_df = pd.DataFrame()

        # Load teams
        try:
            self.teams_df = pd.read_csv(teams_file)
            if not self.teams_df.empty:
                # Create teams hash for cache invalidation
                teams_str = str(len(self.teams_df)) + str(self.teams_df.columns.tolist())
                self.data_hashes['teams_hash'] = hashlib.md5(teams_str.encode()).hexdigest()
                self.logger.info(f"Loaded {len(self.teams_df)} teams")
            else:
                self.logger.warning("Teams file is empty")
        except Exception as e:
            self.logger.error(f"Error loading teams from {teams_file}: {e}")
            self.teams_df = pd.DataFrame()

    def _clean_fixtures_data(self):
        """Clean and validate fixtures data with better error handling"""

        if self.fixtures_df.empty:
            return

        # Store original count
        original_count = len(self.fixtures_df)

        # Filter out finished games
        if 'finished' in self.fixtures_df.columns:
            self.fixtures_df = self.fixtures_df[self.fixtures_df['finished'] == False]

        # Ensure required columns exist with safe defaults
        required_cols = {
            'team_h': 0,
            'team_a': 0,
            'event': 1,
            'team_h_difficulty': 3,
            'team_a_difficulty': 3
        }

        for col, default_val in required_cols.items():
            if col not in self.fixtures_df.columns:
                self.fixtures_df[col] = default_val
                self.logger.warning(f"Missing column {col}, using default value {default_val}")

        # Fill NaN values safely
        numeric_columns = ['team_h_difficulty', 'team_a_difficulty', 'event', 'team_h', 'team_a']
        for col in numeric_columns:
            if col in self.fixtures_df.columns:
                self.fixtures_df[col] = pd.to_numeric(self.fixtures_df[col], errors='coerce')
                self.fixtures_df[col] = self.fixtures_df[col].fillna(required_cols.get(col, 0))

        # Remove invalid fixtures (missing essential data)
        valid_mask = (
            (self.fixtures_df['team_h'] > 0) &
            (self.fixtures_df['team_a'] > 0) &
            (self.fixtures_df['event'] >= 1)
        )
        self.fixtures_df = self.fixtures_df[valid_mask]

        # Sort by gameweek for efficient access
        self.fixtures_df = self.fixtures_df.sort_values('event').reset_index(drop=True)

        cleaned_count = len(self.fixtures_df)
        self.logger.info(f"Cleaned fixtures: {original_count} → {cleaned_count} ({original_count - cleaned_count} removed)")

    def _build_teams_lookup(self):
        """Build optimized team lookup dictionary"""

        self.teams_lookup = {}

        for _, team in self.teams_df.iterrows():
            team_id = team.get('id', 0)
            if team_id <= 0:
                continue

            self.teams_lookup[team_id] = {
                'name': team.get('name', 'Unknown'),
                'strength_overall_home': team.get('strength_overall_home', 1000),
                'strength_overall_away': team.get('strength_overall_away', 1000),
                'strength_attack_home': team.get('strength_attack_home', 1000),
                'strength_attack_away': team.get('strength_attack_away', 1000),
                'strength_defence_home': team.get('strength_defence_home', 1000),
                'strength_defence_away': team.get('strength_defence_away', 1000)
            }

    def _detect_current_gameweek(self) -> int:
        """Detect current gameweek with better logic"""

        if self.fixtures_df.empty:
            return 1

        try:
            # Find first unfinished gameweek
            unfinished = self.fixtures_df[self.fixtures_df.get('finished', False) == False]
            if not unfinished.empty:
                return int(unfinished['event'].min())

            # Fallback to last gameweek + 1
            return int(self.fixtures_df['event'].max()) + 1
        except Exception:
            return 1

    def _generate_cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""

        content = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(content.encode()).hexdigest()

    def _is_cache_valid(self, cache_key: str, cache_dict: str = 'fixtures') -> bool:
        """Check if cache entry is valid"""

        cache_store = self.smart_cache.get(cache_dict, {})

        if cache_key not in cache_store:
            return False

        timestamp, _ = cache_store[cache_key]
        return time.time() - timestamp < self.smart_cache['cache_timeout']

    def _get_from_cache(self, cache_key: str, cache_dict: str = 'fixtures'):
        """Get value from cache if valid"""

        if self._is_cache_valid(cache_key, cache_dict):
            return self.smart_cache[cache_dict][cache_key][1]
        return None

    def _store_in_cache(self, cache_key: str, value, cache_dict: str = 'fixtures'):
        """Store value in cache with timestamp"""

        if cache_dict not in self.smart_cache:
            self.smart_cache[cache_dict] = {}

        self.smart_cache[cache_dict][cache_key] = (time.time(), value)

    def _clean_expired_cache(self):
        """Clean expired cache entries"""

        current_time = time.time()

        # Only clean every 5 minutes
        if current_time - self.smart_cache['last_cache_clean'] < 300:
            return

        for cache_dict in ['fixtures', 'teams', 'batch_analysis', 'gameweek_cache']:
            if cache_dict in self.smart_cache:
                expired_keys = []
                for key, (timestamp, _) in self.smart_cache[cache_dict].items():
                    if current_time - timestamp > self.smart_cache['cache_timeout']:
                        expired_keys.append(key)

                for key in expired_keys:
                    del self.smart_cache[cache_dict][key]

        self.smart_cache['last_cache_clean'] = current_time

    def analyze_team_fixtures(self, team_id: int, gameweeks_ahead: int = 5) -> Dict:
        """Analyze fixtures for a specific team with smart caching"""

        # Generate cache key
        cache_key = self._generate_cache_key(team_id, gameweeks_ahead, self.current_gameweek)

        # Check cache first
        cached_result = self._get_from_cache(cache_key, 'fixtures')
        if cached_result is not None:
            return cached_result

        # Clean cache periodically
        self._clean_expired_cache()

        if self.fixtures_df.empty:
            result = self._empty_fixture_result(team_id)
            self._store_in_cache(cache_key, result, 'fixtures')
            return result

        # Get fixtures for team in next N gameweeks
        end_gameweek = self.current_gameweek + gameweeks_ahead

        # Optimized fixture filtering
        team_fixtures = self.fixtures_df[
            (self.fixtures_df['event'] >= self.current_gameweek) &
            (self.fixtures_df['event'] < end_gameweek) &
            ((self.fixtures_df['team_h'] == team_id) | (self.fixtures_df['team_a'] == team_id))
        ]

        if team_fixtures.empty:
            result = self._empty_fixture_result(team_id)
            self._store_in_cache(cache_key, result, 'fixtures')
            return result

        # Analyze fixtures efficiently
        result = self._analyze_team_fixtures_optimized(team_id, team_fixtures, gameweeks_ahead)

        # Cache the result
        self._store_in_cache(cache_key, result, 'fixtures')

        return result

    def _analyze_team_fixtures_optimized(self, team_id: int, team_fixtures: pd.DataFrame, gameweeks_ahead: int) -> Dict:
        """Optimized fixture analysis for single team"""

        fixtures_analysis = []
        total_difficulty = 0
        home_games = 0
        double_gameweeks = 0

        # Count fixtures per gameweek efficiently
        gameweek_counts = team_fixtures['event'].value_counts()
        double_gameweeks = len(gameweek_counts[gameweek_counts > 1])

        # Process each fixture
        for _, fixture in team_fixtures.iterrows():
            is_home = fixture['team_h'] == team_id
            opponent_id = fixture['team_a'] if is_home else fixture['team_h']
            difficulty = fixture['team_h_difficulty'] if is_home else fixture['team_a_difficulty']

            if is_home:
                home_games += 1

            # Convert difficulty (1-5 scale, where 1=easy) to 0-1 scale (1=easy)
            normalized_difficulty = max(0, min(1, (6 - difficulty) / 4))
            total_difficulty += normalized_difficulty

            # Get opponent name from lookup
            opponent_name = self.teams_lookup.get(opponent_id, {}).get('name', 'Unknown')

            fixture_info = {
                'gameweek': int(fixture['event']),
                'opponent_id': int(opponent_id),
                'opponent_name': opponent_name,
                'is_home': is_home,
                'difficulty_raw': int(difficulty),
                'difficulty_normalized': round(normalized_difficulty, 3),
                'venue': 'H' if is_home else 'A'
            }
            fixtures_analysis.append(fixture_info)

        # Calculate metrics
        num_fixtures = len(fixtures_analysis)
        avg_difficulty = total_difficulty / max(1, num_fixtures)
        home_ratio = home_games / max(1, num_fixtures)

        # Double gameweek bonus (more fixtures = better)
        dgw_bonus = min(0.3, double_gameweeks * 0.15)

        # Get team name from lookup
        team_name = self.teams_lookup.get(team_id, {}).get('name', 'Unknown')

        return {
            'team_id': team_id,
            'team_name': team_name,
            'gameweeks_analyzed': gameweeks_ahead,
            'fixtures_count': num_fixtures,
            'upcoming_fixtures': fixtures_analysis,
            'avg_difficulty': round(avg_difficulty, 3),
            'home_games_ratio': round(home_ratio, 3),
            'double_gameweek_count': double_gameweeks,
            'double_gameweek_bonus': round(dgw_bonus, 3),
            'fixture_difficulty_score': round(avg_difficulty, 3)
        }

    def _empty_fixture_result(self, team_id: int = 0) -> Dict:
        """Return empty result when no fixtures found"""

        team_name = self.teams_lookup.get(team_id, {}).get('name', 'Unknown')

        return {
            'team_id': team_id,
            'team_name': team_name,
            'gameweeks_analyzed': 0,
            'fixtures_count': 0,
            'upcoming_fixtures': [],
            'avg_difficulty': 0.5,  # Neutral
            'home_games_ratio': 0.5,
            'double_gameweek_count': 0,
            'double_gameweek_bonus': 0.0,
            'fixture_difficulty_score': 0.5
        }

    def calculate_fixture_difficulty_score(self, team_id: int, gameweeks_ahead: int = 5) -> float:
        """Calculate fixture difficulty score with caching"""

        analysis = self.analyze_team_fixtures(team_id, gameweeks_ahead)
        return analysis['fixture_difficulty_score']

    def batch_analyze_all_teams(self, gameweeks_ahead: int = 5) -> Dict[int, Dict]:
        """Batch analyze all teams for better performance"""

        cache_key = self._generate_cache_key('batch_all', gameweeks_ahead, self.current_gameweek)

        # Check cache first
        cached_result = self._get_from_cache(cache_key, 'batch_analysis')
        if cached_result is not None:
            return cached_result

        if self.fixtures_df.empty or not self.teams_lookup:
            return {}

        # Get all relevant fixtures in one go
        end_gameweek = self.current_gameweek + gameweeks_ahead
        relevant_fixtures = self.fixtures_df[
            (self.fixtures_df['event'] >= self.current_gameweek) &
            (self.fixtures_df['event'] < end_gameweek)
        ]

        if relevant_fixtures.empty:
            return {}

        # Process all teams in batch
        team_analyses = {}

        for team_id in self.teams_lookup.keys():
            # Filter fixtures for this team
            team_fixtures = relevant_fixtures[
                (relevant_fixtures['team_h'] == team_id) |
                (relevant_fixtures['team_a'] == team_id)
            ]

            if not team_fixtures.empty:
                analysis = self._analyze_team_fixtures_optimized(team_id, team_fixtures, gameweeks_ahead)
                team_analyses[team_id] = analysis
            else:
                team_analyses[team_id] = self._empty_fixture_result(team_id)

        # Cache the batch result
        self._store_in_cache(cache_key, team_analyses, 'batch_analysis')

        self.logger.info(f"Batch analyzed {len(team_analyses)} teams for {gameweeks_ahead} gameweeks")
        return team_analyses

    def get_best_fixture_teams(self, gameweeks_ahead: int = 5, top_n: int = 5) -> List[Dict]:
        """Get teams with best fixtures using batch analysis"""

        # Use batch analysis for efficiency
        all_analyses = self.batch_analyze_all_teams(gameweeks_ahead)

        team_fixture_scores = []
        for analysis in all_analyses.values():
            if analysis['fixtures_count'] > 0:
                team_fixture_scores.append({
                    'team_id': analysis['team_id'],
                    'team_name': analysis['team_name'],
                    'fixture_score': analysis['fixture_difficulty_score'],
                    'fixtures_count': analysis['fixtures_count'],
                    'dgw_bonus': analysis['double_gameweek_bonus'],
                    'home_ratio': analysis['home_games_ratio']
                })

        # Sort by combined score (fixture difficulty + DGW bonus)
        team_fixture_scores.sort(key=lambda x: x['fixture_score'] + x['dgw_bonus'], reverse=True)

        return team_fixture_scores[:top_n]

    def get_worst_fixture_teams(self, gameweeks_ahead: int = 5, top_n: int = 5) -> List[Dict]:
        """Get teams with worst fixtures using batch analysis"""

        # Use batch analysis for efficiency
        all_analyses = self.batch_analyze_all_teams(gameweeks_ahead)

        team_fixture_scores = []
        for analysis in all_analyses.values():
            if analysis['fixtures_count'] > 0:
                team_fixture_scores.append({
                    'team_id': analysis['team_id'],
                    'team_name': analysis['team_name'],
                    'fixture_score': analysis['fixture_difficulty_score'],
                    'fixtures_count': analysis['fixtures_count'],
                    'dgw_bonus': analysis['double_gameweek_bonus'],
                    'home_ratio': analysis['home_games_ratio']
                })

        # Sort by fixture score (lower = harder fixtures)
        team_fixture_scores.sort(key=lambda x: x['fixture_score'])

        return team_fixture_scores[:top_n]

    def get_gameweek_fixtures(self, gameweek: int) -> Dict:
        """Get fixtures for specific gameweek with caching"""

        cache_key = self._generate_cache_key('gameweek', gameweek)

        # Check cache first
        cached_result = self._get_from_cache(cache_key, 'gameweek_cache')
        if cached_result is not None:
            return cached_result

        if self.fixtures_df.empty:
            result = {'gameweek': gameweek, 'fixtures': [], 'total_games': 0}
            self._store_in_cache(cache_key, result, 'gameweek_cache')
            return result

        gw_fixtures = self.fixtures_df[self.fixtures_df['event'] == gameweek]

        fixtures_list = []
        for _, fixture in gw_fixtures.iterrows():
            home_team = self.teams_lookup.get(fixture['team_h'], {}).get('name', 'Unknown')
            away_team = self.teams_lookup.get(fixture['team_a'], {}).get('name', 'Unknown')

            fixtures_list.append({
                'home_team': home_team,
                'away_team': away_team,
                'kickoff_time': fixture.get('kickoff_time'),
                'home_difficulty': int(fixture.get('team_h_difficulty', 3)),
                'away_difficulty': int(fixture.get('team_a_difficulty', 3))
            })

        result = {
            'gameweek': gameweek,
            'fixtures': fixtures_list,
            'total_games': len(fixtures_list)
        }

        # Cache the result
        self._store_in_cache(cache_key, result, 'gameweek_cache')

        return result

    def get_home_away_advantage(self, team_id: int, is_home: bool = True) -> float:
        """Calculate home/away advantage with caching"""

        cache_key = self._generate_cache_key('advantage', team_id, is_home)

        # Check cache first
        cached_result = self._get_from_cache(cache_key, 'teams')
        if cached_result is not None:
            return cached_result

        if team_id not in self.teams_lookup:
            result = 0.5  # Neutral
            self._store_in_cache(cache_key, result, 'teams')
            return result

        team_data = self.teams_lookup[team_id]

        if is_home:
            home_strength = team_data['strength_overall_home']
            away_strength = team_data['strength_overall_away']
        else:
            home_strength = team_data['strength_overall_away']
            away_strength = team_data['strength_overall_home']

        # Normalize strength difference to 0-1 scale
        strength_diff = (home_strength - away_strength) / 200.0  # Typical range is ~200
        advantage = 0.5 + max(-0.25, min(0.25, strength_diff))  # Cap between 0.25-0.75

        result = round(advantage, 3)

        # Cache the result
        self._store_in_cache(cache_key, result, 'teams')

        return result

    def get_position_fixture_impact(self, position: str) -> float:
        """Get position-specific fixture impact multiplier"""

        position_impacts = {
            'GK': 0.6,  # Goalkeepers less affected by easy fixtures
            'DEF': 0.8,  # Defenders moderately affected
            'MID': 1.0,  # Midfielders fully affected
            'FWD': 1.2  # Forwards most affected by easy fixtures
        }
        return position_impacts.get(position, 1.0)

    def integrate_with_momentum(self, player_data: Dict, momentum_score: float) -> float:
        """Integrate fixture analysis with momentum score"""

        if momentum_score <= 0:
            return momentum_score

        team_id = player_data.get('team', 0)
        position = player_data.get('position', 'MID')

        if team_id == 0:
            return momentum_score

        # Get fixture analysis (will use cache if available)
        fixture_analysis = self.analyze_team_fixtures(team_id)

        # Calculate fixture bonus
        difficulty_score = fixture_analysis['fixture_difficulty_score']
        home_ratio = fixture_analysis['home_games_ratio']
        dgw_bonus = fixture_analysis['double_gameweek_bonus']

        # Position-specific impact
        position_multiplier = self.get_position_fixture_impact(position)

        # Home advantage bonus
        home_advantage = self.get_home_away_advantage(team_id, True)
        home_bonus = (home_ratio - 0.5) * (home_advantage - 0.5) * 0.2

        # Calculate total fixture bonus
        fixture_bonus = (
            (difficulty_score - 0.5) * 0.15 +  # Easy fixtures bonus
            home_bonus +  # Home games bonus
            dgw_bonus  # Double gameweek bonus
        ) * position_multiplier

        # Cap fixture bonus to prevent extreme values
        fixture_bonus = max(-0.2, min(0.3, fixture_bonus))

        # Apply fixture bonus to momentum
        enhanced_momentum = momentum_score * (1 + fixture_bonus)
        enhanced_momentum = max(0.0, min(1.0, enhanced_momentum))

        return round(enhanced_momentum, 4)

    def get_fixture_insights(self, team_id: int) -> Dict:
        """Get detailed fixture insights for a team"""

        analysis = self.analyze_team_fixtures(team_id, 8)  # Look 8 weeks ahead

        if analysis['fixtures_count'] == 0:
            return {'message': 'No upcoming fixtures found'}

        insights = {
            'team_name': analysis['team_name'],
            'short_term_difficulty': self.calculate_fixture_difficulty_score(team_id, 3),
            'medium_term_difficulty': self.calculate_fixture_difficulty_score(team_id, 5),
            'long_term_difficulty': self.calculate_fixture_difficulty_score(team_id, 8),
            'home_advantage': self.get_home_away_advantage(team_id, True),
            'away_performance': self.get_home_away_advantage(team_id, False),
            'fixture_rating': self._get_fixture_rating(analysis),
            'key_fixtures': self._identify_key_fixtures(analysis),
            'recommendations': self._generate_fixture_recommendations(analysis)
        }

        return insights

    def _get_fixture_rating(self, analysis: Dict) -> str:
        """Get overall fixture rating"""

        score = analysis['fixture_difficulty_score']
        dgw_bonus = analysis['double_gameweek_bonus']
        home_ratio = analysis['home_games_ratio']

        total_score = score + dgw_bonus + (home_ratio - 0.5) * 0.2

        if total_score >= 0.8:
            return "Excellent"
        elif total_score >= 0.65:
            return "Good"
        elif total_score >= 0.45:
            return "Average"
        elif total_score >= 0.3:
            return "Difficult"
        else:
            return "Very Difficult"

    def _identify_key_fixtures(self, analysis: Dict) -> List[Dict]:
        """Identify key fixtures (very easy or very hard)"""

        key_fixtures = []

        for fixture in analysis['upcoming_fixtures']:
            difficulty = fixture['difficulty_normalized']

            if difficulty >= 0.8:  # Very easy
                key_fixtures.append({
                    'gameweek': fixture['gameweek'],
                    'opponent': fixture['opponent_name'],
                    'venue': fixture['venue'],
                    'type': 'Easy',
                    'note': 'Great opportunity for points'
                })
            elif difficulty <= 0.2:  # Very hard
                key_fixtures.append({
                    'gameweek': fixture['gameweek'],
                    'opponent': fixture['opponent_name'],
                    'venue': fixture['venue'],
                    'type': 'Difficult',
                    'note': 'Consider avoiding captain or transfers'
                })

        return key_fixtures

    def _generate_fixture_recommendations(self, analysis: Dict) -> List[str]:
        """Generate fixture-based recommendations"""

        recommendations = []

        score = analysis['fixture_difficulty_score']
        dgw_count = analysis['double_gameweek_count']
        home_ratio = analysis['home_games_ratio']

        if score >= 0.7:
            recommendations.append("Excellent fixture run - consider captain options")
        elif score <= 0.3:
            recommendations.append("Difficult fixtures ahead - avoid new transfers")

        if dgw_count > 0:
            recommendations.append(f"Double gameweek advantage ({dgw_count} DGWs)")

        if home_ratio >= 0.7:
            recommendations.append("Strong home advantage period")
        elif home_ratio <= 0.3:
            recommendations.append("Mostly away fixtures - reduced expectations")

        if not recommendations:
            recommendations.append("Balanced fixture schedule")

        return recommendations

    def get_fixture_difficulty_matrix(self, gameweeks_ahead: int = 8) -> pd.DataFrame:
        """Get fixture difficulty matrix for all teams"""

        cache_key = self._generate_cache_key('difficulty_matrix', gameweeks_ahead, self.current_gameweek)

        # Check cache first
        cached_result = self._get_from_cache(cache_key, 'batch_analysis')
        if cached_result is not None:
            return cached_result

        # Use batch analysis
        all_analyses = self.batch_analyze_all_teams(gameweeks_ahead)

        if not all_analyses:
            result = pd.DataFrame()
            self._store_in_cache(cache_key, result, 'batch_analysis')
            return result

        # Create matrix
        matrix_data = []
        for analysis in all_analyses.values():
            if analysis['fixtures_count'] > 0:
                matrix_data.append({
                    'team_id': analysis['team_id'],
                    'team_name': analysis['team_name'],
                    'fixture_difficulty': analysis['fixture_difficulty_score'],
                    'fixtures_count': analysis['fixtures_count'],
                    'home_ratio': analysis['home_games_ratio'],
                    'dgw_count': analysis['double_gameweek_count'],
                    'overall_rating': analysis['fixture_difficulty_score'] + analysis['double_gameweek_bonus']
                })

        result = pd.DataFrame(matrix_data).sort_values('overall_rating', ascending=False)

        # Cache the result
        self._store_in_cache(cache_key, result, 'batch_analysis')

        return result

    def get_transfer_recommendations_by_fixtures(self, min_difficulty_score: float = 0.7) -> Dict:
        """Get transfer recommendations based on fixtures"""

        cache_key = self._generate_cache_key('transfer_recs', min_difficulty_score, self.current_gameweek)

        # Check cache first
        cached_result = self._get_from_cache(cache_key, 'batch_analysis')
        if cached_result is not None:
            return cached_result

        # Get fixture difficulty for all teams
        difficulty_matrix = self.get_fixture_difficulty_matrix()

        if difficulty_matrix.empty:
            result = {'transfer_in_teams': [], 'avoid_teams': []}
            self._store_in_cache(cache_key, result, 'batch_analysis')
            return result

        # Teams to target for transfers
        good_fixture_teams = difficulty_matrix[
            difficulty_matrix['overall_rating'] >= min_difficulty_score
        ]

        # Teams to avoid
        bad_fixture_teams = difficulty_matrix[
            difficulty_matrix['overall_rating'] <= 0.4
        ]

        result = {
            'transfer_in_teams': good_fixture_teams.to_dict('records'),
            'avoid_teams': bad_fixture_teams.to_dict('records'),
            'analysis_summary': {
                'teams_analyzed': len(difficulty_matrix),
                'good_fixture_teams': len(good_fixture_teams),
                'poor_fixture_teams': len(bad_fixture_teams),
                'avg_difficulty_score': difficulty_matrix['fixture_difficulty'].mean(),
                'best_team': difficulty_matrix.iloc[0]['team_name'] if not difficulty_matrix.empty else None,
                'worst_team': difficulty_matrix.iloc[-1]['team_name'] if not difficulty_matrix.empty else None
            }
        }

        # Cache the result
        self._store_in_cache(cache_key, result, 'batch_analysis')

        return result

    def clear_cache(self):
        """Clear all cached data"""

        for cache_type in ['fixtures', 'teams', 'batch_analysis', 'gameweek_cache']:
            self.smart_cache[cache_type] = {}

        self.logger.info("All fixture caches cleared")

    def get_cache_statistics(self) -> Dict:
        """Get cache statistics and performance metrics"""

        cache_stats = {}
        total_items = 0

        for cache_type in ['fixtures', 'teams', 'batch_analysis', 'gameweek_cache']:
            cache_size = len(self.smart_cache.get(cache_type, {}))
            cache_stats[f'{cache_type}_cache_size'] = cache_size
            total_items += cache_size

        return {
            'cache_statistics': cache_stats,
            'total_cached_items': total_items,
            'cache_timeout_minutes': self.smart_cache['cache_timeout'] / 60,
            'current_gameweek': self.current_gameweek,
            'teams_loaded': len(self.teams_lookup),
            'fixtures_loaded': len(self.fixtures_df) if not self.fixtures_df.empty else 0,
            'data_hashes': self.data_hashes
        }

    def validate_data_integrity(self) -> Dict:
        """Validate data integrity and return report"""

        report = {
            'fixtures_valid': not self.fixtures_df.empty,
            'teams_valid': not self.teams_df.empty,
            'teams_lookup_built': len(self.teams_lookup) > 0,
            'current_gameweek_detected': self.current_gameweek > 0,
            'issues': [],
            'warnings': []
        }

        # Check fixtures data
        if self.fixtures_df.empty:
            report['issues'].append("No fixtures data loaded")
        else:
            # Check for required columns
            required_cols = ['team_h', 'team_a', 'event']
            missing_cols = [col for col in required_cols if col not in self.fixtures_df.columns]
            if missing_cols:
                report['issues'].append(f"Missing fixture columns: {missing_cols}")

            # Check data quality
            invalid_fixtures = self.fixtures_df[
                (self.fixtures_df['team_h'] <= 0) |
                (self.fixtures_df['team_a'] <= 0) |
                (self.fixtures_df['event'] <= 0)
            ]
            if len(invalid_fixtures) > 0:
                report['warnings'].append(f"{len(invalid_fixtures)} fixtures have invalid data")

        # Check teams data
        if self.teams_df.empty:
            report['issues'].append("No teams data loaded")
        elif len(self.teams_lookup) == 0:
            report['issues'].append("Teams lookup not built")

        # Check gameweek detection
        if self.current_gameweek <= 0:
            report['warnings'].append("Current gameweek detection failed")

        report['overall_status'] = 'valid' if not report['issues'] else 'invalid'

        return report


# Integration helper function
def enhance_player_with_fixtures(player_data: Dict, fixture_analyzer: 'FixtureAnalyzer') -> Dict:
    """Helper function to enhance player data with fixture analysis"""

    enhanced_player = player_data.copy()

    team_id = player_data.get('team', 0)
    position = player_data.get('position', 'MID')
    momentum_score = player_data.get('momentum_score', 0)

    if team_id > 0 and momentum_score > 0:
        # Get fixture analysis (uses cache internally)
        fixture_analysis = fixture_analyzer.analyze_team_fixtures(team_id)

        # Enhance momentum with fixtures
        enhanced_momentum = fixture_analyzer.integrate_with_momentum(player_data, momentum_score)

        # Add fixture data to player
        enhanced_player.update({
            'fixture_difficulty_score': fixture_analysis['fixture_difficulty_score'],
            'upcoming_fixtures': fixture_analysis['upcoming_fixtures'][:3],  # Next 3 fixtures
            'home_games_ratio': fixture_analysis['home_games_ratio'],
            'double_gameweek_bonus': fixture_analysis['double_gameweek_bonus'],
            'enhanced_momentum': enhanced_momentum,
            'fixture_rating': fixture_analyzer._get_fixture_rating(fixture_analysis)
        })

    return enhanced_player


def analyze_fixtures() -> bool:
    """Main function to analyze fixtures with performance logging"""

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        start_time = time.time()
        analyzer = FixtureAnalyzer()

        if analyzer.fixtures_df.empty:
            logging.error("No fixture data available")
            return False

        # Validate data integrity
        validation = analyzer.validate_data_integrity()
        if validation['overall_status'] == 'invalid':
            logging.error(f"Data validation failed: {validation['issues']}")
            return False

        # Test batch analysis performance
        batch_start = time.time()
        batch_results = analyzer.batch_analyze_all_teams()
        batch_time = time.time() - batch_start

        total_time = time.time() - start_time

        logging.info(f"Fixture analyzer ready with {len(analyzer.fixtures_df)} fixtures")
        logging.info(f"Batch analyzed {len(batch_results)} teams in {batch_time:.2f}s")
        logging.info(f"Total initialization time: {total_time:.2f}s")

        # Log cache statistics
        cache_stats = analyzer.get_cache_statistics()
        logging.info(f"Cache system ready with {cache_stats['total_cached_items']} items")

        return True

    except Exception as e:
        logging.error(f"Error in fixture analysis: {e}")
        return False


if __name__ == "__main__":
    success = analyze_fixtures()
    exit(0 if success else 1)