import pandas as pd
import numpy as np
import requests
import json
import os
import time
import random
from typing import Dict, List, Optional
from standard_player_schema import StandardPlayer, GLOBAL_SEED
from central_cache import cache

random.seed(GLOBAL_SEED)
np.random.seed(GLOBAL_SEED)


class UnifiedDataManager:
    def __init__(self):
        self.base_url = "https://fantasy.premierleague.com/api/"
        self.fixture_analyzer = None
        self._teams_cache = {}

    def fetch_and_process_data(self) -> List[StandardPlayer]:
        cache_key = "all_players_data"
        cached = cache.get(cache_key)
        if cached:
            return cached

        response = requests.get(f"{self.base_url}bootstrap-static/")
        data = response.json()

        teams = {t['id']: t['name'] for t in data['teams']}
        self._teams_cache = teams
        positions = {1: 'GK', 2: 'DEF', 3: 'MID', 4: 'FWD'}

        # Initialize fixture analyzer for enhanced momentum calculation
        self._initialize_fixture_analyzer()

        players = []
        for p in data['elements']:
            try:
                player = StandardPlayer(
                    player_id=int(p.get('id', 0)),
                    name=str(p.get('web_name', 'Unknown')),
                    position=positions.get(p.get('element_type', 3), 'MID'),
                    team_name=teams.get(p.get('team', 1), 'Unknown'),
                    price=float(p.get('now_cost', 40)) / 10.0,
                    total_points=int(p.get('total_points', 0)),
                    momentum_score=self._calculate_enhanced_momentum(p, positions.get(p.get('element_type', 3), 'MID')),
                    minutes=int(p.get('minutes', 0)),
                    form=float(p.get('form', 0)),
                    selected_by_percent=float(p.get('selected_by_percent', 0)),
                    goals_scored=int(p.get('goals_scored', 0)),
                    assists=int(p.get('assists', 0)),
                    clean_sheets=int(p.get('clean_sheets', 0)),
                    chance_of_playing=int(p.get('chance_of_playing_this_round') or 100)
                )
                players.append(player)
            except:
                continue

        cache.set(cache_key, players)
        return players

    def _initialize_fixture_analyzer(self):
        """Initialize fixture analyzer if available"""
        try:
            # Try to import and initialize FixtureAnalyzer if it exists
            import importlib
            if importlib.util.find_spec("FixtureAnalyzer"):
                from FixtureAnalyzer import FixtureAnalyzer
                self.fixture_analyzer = FixtureAnalyzer()
        except:
            self.fixture_analyzer = None

    def _calculate_enhanced_momentum(self, player_data: dict, position: str) -> float:
        """Enhanced momentum calculation with fixture integration and recency weighting"""
        try:
            # Base momentum calculation (existing logic)
            base_momentum = self._calculate_base_momentum(player_data, position)

            # Recency weighting - recent form gets higher weight
            recency_bonus = self._calculate_recency_bonus(player_data)

            # Fixture difficulty integration
            fixture_bonus = self._calculate_fixture_bonus(player_data)

            # Ownership adjustment (anti-template logic)
            ownership_adjustment = self._calculate_ownership_adjustment(player_data)

            # Combine all factors
            enhanced_momentum = base_momentum * (1 + recency_bonus) * (1 + fixture_bonus) * (1 + ownership_adjustment)

            return min(1.0, max(0.0, enhanced_momentum))

        except:
            return self._calculate_momentum(player_data)  # Fallback to original

    def _calculate_base_momentum(self, player_data: dict, position: str) -> float:
        """Original momentum calculation as base"""
        try:
            def safe_get(key, default=0):
                value = player_data.get(key, default)
                return float(value) if value is not None else default

            if position == 'FWD':
                score = (
                                safe_get('goals_scored') * 0.4 +
                                safe_get('assists') * 0.2 +
                                safe_get('expected_goals') * 0.2 +
                                safe_get('threat') / 100.0 * 0.2
                        ) / 20.0
            elif position == 'MID':
                score = (
                                safe_get('goals_scored') * 0.2 +
                                safe_get('assists') * 0.3 +
                                safe_get('creativity') / 100.0 * 0.3 +
                                safe_get('influence') / 100.0 * 0.2
                        ) / 15.0
            elif position == 'DEF':
                score = (
                                safe_get('clean_sheets') * 0.4 +
                                safe_get('goals_scored') * 0.2 +
                                safe_get('assists') * 0.2 +
                                safe_get('influence') / 100.0 * 0.2
                        ) / 12.0
            else:  # GK
                score = (
                                safe_get('clean_sheets') * 0.5 +
                                safe_get('saves') / 100.0 * 0.3 +
                                safe_get('bonus') * 0.2
                        ) / 10.0

            return min(1.0, max(0.0, score))
        except:
            return 0.1

    def _calculate_recency_bonus(self, player_data: dict) -> float:
        """Calculate recency bonus - recent performance gets higher weight"""
        try:
            # Form is recent performance indicator
            form = float(player_data.get('form', 0))

            # Points per game in recent fixtures
            total_points = float(player_data.get('total_points', 0))
            games_played = max(1, float(player_data.get('starts', 1)))
            ppg = total_points / games_played

            # Recent form bonus (form is average points in last 5 games)
            form_bonus = min(0.3, form / 20.0)  # Cap at 30% bonus

            # Consistency bonus for high PPG
            consistency_bonus = min(0.2, ppg / 30.0)  # Cap at 20% bonus

            return form_bonus + consistency_bonus

        except:
            return 0.0

    def _calculate_fixture_bonus(self, player_data: dict) -> float:
        """Calculate fixture difficulty bonus using FixtureAnalyzer"""
        try:
            if not self.fixture_analyzer:
                return 0.0

            team_id = player_data.get('team')
            if not team_id:
                return 0.0

            # Get fixture analysis for player's team
            fixture_analysis = self.fixture_analyzer.analyze_team_fixtures(team_id, 5)

            if fixture_analysis['fixtures_count'] == 0:
                return 0.0

            # Extract fixture factors
            difficulty_score = fixture_analysis['fixture_difficulty_score']
            home_ratio = fixture_analysis['home_games_ratio']
            dgw_bonus = fixture_analysis['double_gameweek_bonus']

            # Position-specific fixture impact
            position = {1: 'GK', 2: 'DEF', 3: 'MID', 4: 'FWD'}.get(
                player_data.get('element_type', 3), 'MID'
            )
            position_multiplier = self.fixture_analyzer.get_position_fixture_impact(position)

            # Calculate total fixture bonus
            fixture_bonus = (
                                    (difficulty_score - 0.5) * 0.15 +  # Easy fixtures bonus/penalty
                                    (home_ratio - 0.5) * 0.1 +  # Home advantage bonus
                                    dgw_bonus  # Double gameweek bonus
                            ) * position_multiplier

            # Cap fixture bonus
            return max(-0.2, min(0.3, fixture_bonus))

        except:
            return 0.0

    def _calculate_ownership_adjustment(self, player_data: dict) -> float:
        """Calculate ownership adjustment (anti-template logic)"""
        try:
            ownership = float(player_data.get('selected_by_percent', 0))

            # Anti-template bonus for low-owned players with good stats
            if ownership < 5.0:  # Very low ownership
                return 0.1  # 10% bonus for differentials
            elif ownership < 15.0:  # Low ownership
                return 0.05  # 5% bonus
            elif ownership > 50.0:  # Very high ownership
                return -0.05  # 5% penalty for template players
            elif ownership > 30.0:  # High ownership
                return -0.02  # 2% penalty
            else:
                return 0.0  # Neutral ownership

        except:
            return 0.0

    def _calculate_momentum(self, player_data: dict) -> float:
        """Original momentum calculation (fallback)"""
        try:
            element_type = player_data.get('element_type', 3)
            position = {1: 'GK', 2: 'DEF', 3: 'MID', 4: 'FWD'}.get(element_type, 'MID')

            def safe_get(key, default=0):
                value = player_data.get(key, default)
                return float(value) if value is not None else default

            if position == 'FWD':
                score = (
                                safe_get('goals_scored') * 0.4 +
                                safe_get('assists') * 0.2 +
                                safe_get('expected_goals') * 0.2 +
                                safe_get('threat') / 100.0 * 0.2
                        ) / 20.0
            elif position == 'MID':
                score = (
                                safe_get('goals_scored') * 0.2 +
                                safe_get('assists') * 0.3 +
                                safe_get('creativity') / 100.0 * 0.3 +
                                safe_get('influence') / 100.0 * 0.2
                        ) / 15.0
            elif position == 'DEF':
                score = (
                                safe_get('clean_sheets') * 0.4 +
                                safe_get('goals_scored') * 0.2 +
                                safe_get('assists') * 0.2 +
                                safe_get('influence') / 100.0 * 0.2
                        ) / 12.0
            else:  # GK
                score = (
                                safe_get('clean_sheets') * 0.5 +
                                safe_get('saves') / 100.0 * 0.3 +
                                safe_get('bonus') * 0.2
                        ) / 10.0

            return min(1.0, max(0.0, score))
        except:
            return 0.1

    def get_teams_data(self) -> Dict:
        """Get teams data for other components"""
        return self._teams_cache

    def get_enhanced_player_analysis(self, player_id: int) -> Dict:
        """Get detailed analysis for specific player"""
        try:
            response = requests.get(f"{self.base_url}element-summary/{player_id}/")
            data = response.json()

            # Get player's recent history
            history = data.get('history', [])

            if not history:
                return {'error': 'No history data'}

            # Analyze recent performance trends
            recent_points = [h.get('total_points', 0) for h in history[-5:]]
            recent_minutes = [h.get('minutes', 0) for h in history[-5:]]

            analysis = {
                'recent_form': sum(recent_points) / max(1, len(recent_points)),
                'recent_minutes': sum(recent_minutes) / max(1, len(recent_minutes)),
                'consistency': np.std(recent_points) if len(recent_points) > 1 else 0,
                'trending': self._calculate_trend(recent_points),
                'fixture_impact': self._get_player_fixture_impact(player_id)
            }

            return analysis

        except:
            return {'error': 'Failed to fetch player analysis'}

    def _calculate_trend(self, points_history: List[int]) -> str:
        """Calculate if player is trending up, down or stable"""
        if len(points_history) < 3:
            return 'insufficient_data'

        try:
            # Simple trend calculation
            first_half = sum(points_history[:len(points_history) // 2])
            second_half = sum(points_history[len(points_history) // 2:])

            if second_half > first_half * 1.2:
                return 'improving'
            elif second_half < first_half * 0.8:
                return 'declining'
            else:
                return 'stable'
        except:
            return 'stable'

    def _get_player_fixture_impact(self, player_id: int) -> Dict:
        """Get fixture impact for specific player"""
        try:
            if not self.fixture_analyzer:
                return {'impact': 'unknown'}

            # This would need player-to-team mapping
            # For now, return basic fixture impact
            return {'impact': 'moderate', 'confidence': 'medium'}

        except:
            return {'impact': 'unknown'}

    def validate_data_quality(self) -> Dict:
        """Validate the quality of fetched data"""
        try:
            players = self.fetch_and_process_data()

            if not players:
                return {'status': 'failed', 'error': 'No players loaded'}

            # Basic validation checks
            total_players = len(players)
            valid_prices = len([p for p in players if 4.0 <= p.price <= 15.0])
            valid_positions = len([p for p in players if p.position in ['GK', 'DEF', 'MID', 'FWD']])

            validation = {
                'status': 'success',
                'total_players': total_players,
                'valid_prices': valid_prices,
                'valid_positions': valid_positions,
                'price_coverage': valid_prices / total_players if total_players > 0 else 0,
                'position_coverage': valid_positions / total_players if total_players > 0 else 0,
                'enhancement_features': {
                    'fixture_analyzer': self.fixture_analyzer is not None,
                    'recency_weighting': True,
                    'ownership_adjustment': True
                }
            }

            return validation

        except Exception as e:
            return {'status': 'failed', 'error': str(e)}