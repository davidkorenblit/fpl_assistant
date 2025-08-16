"""
Ownership Weights Module for FPL Assistant
Implements anti-template logic and ownership-based adjustments based on research findings
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from central_cache import cache


class OwnershipWeights:
    """
    Handles ownership-based adjustments and anti-template logic
    Based on FPL research about ownership patterns and optimal strategies
    """

    def __init__(self):
        # Ownership thresholds and modifiers based on research
        self.ownership_brackets = {
            'template': {'min': 50.0, 'modifier': -0.12, 'risk': 'high'},
            'popular': {'min': 30.0, 'modifier': -0.06, 'risk': 'medium'},
            'medium': {'min': 15.0, 'modifier': 0.0, 'risk': 'low'},
            'differential': {'min': 5.0, 'modifier': 0.08, 'risk': 'medium'},
            'contrarian': {'min': 0.0, 'modifier': 0.15, 'risk': 'high'}
        }

        # Position-specific ownership impact
        self.position_ownership_impact = {
            'GK': 0.6,  # Goalkeepers less affected by ownership patterns
            'DEF': 0.8,  # Defenders moderately affected
            'MID': 1.0,  # Midfielders fully affected
            'FWD': 1.2  # Forwards most affected by ownership trends
        }

        # Gameweek-specific modifiers (some GWs favor differentials more)
        self.gameweek_modifiers = {
            'early_season': 0.8,  # GW 1-6: Lower differential value
            'mid_season': 1.0,  # GW 7-25: Standard differential value
            'run_in': 1.3,  # GW 26-35: Higher differential value
            'final_stretch': 1.5  # GW 36-38: Maximum differential value
        }

    def calculate_ownership_adjustment(self, ownership_pct: float, position: str = 'MID',
                                       gameweek: int = 20) -> Dict:
        """
        Calculate ownership-based adjustment for player selection probability

        Args:
            ownership_pct: Player ownership percentage
            position: Player position (affects impact magnitude)
            gameweek: Current gameweek (affects differential value)

        Returns:
            Dict with adjustment details
        """

        # Determine ownership bracket
        bracket = self._get_ownership_bracket(ownership_pct)

        # Get base modifier
        base_modifier = self.ownership_brackets[bracket]['modifier']

        # Apply position-specific impact
        position_multiplier = self.position_ownership_impact.get(position, 1.0)

        # Apply gameweek modifier for differentials
        gameweek_multiplier = self._get_gameweek_multiplier(gameweek)

        # Calculate final adjustment
        if bracket in ['differential', 'contrarian']:
            # Boost differentials more in later gameweeks
            final_modifier = base_modifier * position_multiplier * gameweek_multiplier
        else:
            # Template penalties less affected by gameweek
            final_modifier = base_modifier * position_multiplier

        # Cap the adjustment to prevent extreme values
        final_modifier = max(-0.2, min(0.25, final_modifier))

        return {
            'ownership_bracket': bracket,
            'base_modifier': base_modifier,
            'position_multiplier': position_multiplier,
            'gameweek_multiplier': gameweek_multiplier,
            'final_modifier': final_modifier,
            'risk_level': self.ownership_brackets[bracket]['risk'],
            'recommendation': self._get_ownership_recommendation(bracket, ownership_pct)
        }

    def _get_ownership_bracket(self, ownership_pct: float) -> str:
        """Determine ownership bracket for given percentage"""
        if ownership_pct >= 50.0:
            return 'template'
        elif ownership_pct >= 30.0:
            return 'popular'
        elif ownership_pct >= 15.0:
            return 'medium'
        elif ownership_pct >= 5.0:
            return 'differential'
        else:
            return 'contrarian'

    def _get_gameweek_multiplier(self, gameweek: int) -> float:
        """Get gameweek-based multiplier for differential value"""
        if gameweek <= 6:
            return self.gameweek_modifiers['early_season']
        elif gameweek <= 25:
            return self.gameweek_modifiers['mid_season']
        elif gameweek <= 35:
            return self.gameweek_modifiers['run_in']
        else:
            return self.gameweek_modifiers['final_stretch']

    def _get_ownership_recommendation(self, bracket: str, ownership_pct: float) -> str:
        """Get recommendation based on ownership bracket"""
        recommendations = {
            'template': f'Template pick ({ownership_pct:.1f}%) - High safety, low differential value',
            'popular': f'Popular pick ({ownership_pct:.1f}%) - Moderate safety, limited upside',
            'medium': f'Balanced pick ({ownership_pct:.1f}%) - Good middle ground',
            'differential': f'Differential ({ownership_pct:.1f}%) - Higher risk, potential for gains',
            'contrarian': f'Contrarian pick ({ownership_pct:.1f}%) - High risk, high reward potential'
        }
        return recommendations[bracket]

    def analyze_team_ownership_balance(self, team_players: List[Dict]) -> Dict:
        """
        Analyze ownership balance across a team
        Helps optimize mix of template vs differential picks
        """

        if not team_players:
            return {'error': 'No players provided'}

        ownership_distribution = {
            'template': 0,
            'popular': 0,
            'medium': 0,
            'differential': 0,
            'contrarian': 0
        }

        total_ownership = 0
        risk_factors = []

        for player in team_players:
            ownership = player.get('selected_by_percent', 0)
            bracket = self._get_ownership_bracket(ownership)
            ownership_distribution[bracket] += 1
            total_ownership += ownership

            # Track risk factors
            if bracket == 'template' and ownership > 60:
                risk_factors.append(f"Very high template risk: {player.get('name', 'Unknown')} ({ownership:.1f}%)")
            elif bracket == 'contrarian' and ownership < 2:
                risk_factors.append(f"Very high contrarian risk: {player.get('name', 'Unknown')} ({ownership:.1f}%)")

        avg_ownership = total_ownership / len(team_players)

        # Calculate balance score (closer to 1.0 = better balance)
        balance_score = self._calculate_balance_score(ownership_distribution, len(team_players))

        # Generate recommendations
        recommendations = self._generate_balance_recommendations(ownership_distribution, balance_score)

        return {
            'ownership_distribution': ownership_distribution,
            'average_ownership': round(avg_ownership, 2),
            'balance_score': round(balance_score, 3),
            'risk_factors': risk_factors,
            'recommendations': recommendations,
            'team_strategy': self._classify_team_strategy(ownership_distribution, avg_ownership)
        }

    def _calculate_balance_score(self, distribution: Dict, total_players: int) -> float:
        """Calculate how balanced the ownership distribution is"""

        # Ideal distribution (based on research): some template, mostly medium, some differentials
        ideal_ratios = {
            'template': 0.2,  # 20% template for safety
            'popular': 0.2,  # 20% popular picks
            'medium': 0.4,  # 40% medium ownership
            'differential': 0.15,  # 15% differentials
            'contrarian': 0.05  # 5% contrarian picks
        }

        # Calculate deviation from ideal
        total_deviation = 0
        for bracket, ideal_ratio in ideal_ratios.items():
            actual_ratio = distribution[bracket] / total_players
            deviation = abs(actual_ratio - ideal_ratio)
            total_deviation += deviation

        # Convert to balance score (lower deviation = higher score)
        balance_score = max(0, 1 - (total_deviation / 2))
        return balance_score

    def _generate_balance_recommendations(self, distribution: Dict, balance_score: float) -> List[str]:
        """Generate recommendations for improving ownership balance"""

        recommendations = []

        if balance_score >= 0.8:
            recommendations.append("Excellent ownership balance - good mix of safety and differentials")
        elif balance_score >= 0.6:
            recommendations.append("Good ownership balance with room for minor improvements")
        else:
            recommendations.append("Ownership balance needs improvement")

        # Specific recommendations based on distribution
        if distribution['template'] >= 5:
            recommendations.append("Consider reducing template picks to increase differential potential")
        elif distribution['template'] == 0:
            recommendations.append("Consider adding 1-2 template picks for safety")

        if distribution['differential'] + distribution['contrarian'] >= 6:
            recommendations.append("High differential count - ensure strong underlying stats")
        elif distribution['differential'] + distribution['contrarian'] <= 1:
            recommendations.append("Consider adding differentials for potential rank gains")

        return recommendations

    def _classify_team_strategy(self, distribution: Dict, avg_ownership: float) -> str:
        """Classify overall team strategy based on ownership patterns"""

        template_heavy = distribution['template'] >= 4
        differential_heavy = distribution['differential'] + distribution['contrarian'] >= 5

        if template_heavy:
            return "Template Heavy - Safe but limited upside"
        elif differential_heavy:
            return "Differential Heavy - High risk, high reward"
        elif avg_ownership < 20:
            return "Contrarian Strategy - Very risky but potential for big gains"
        elif avg_ownership > 40:
            return "Template Strategy - Very safe but limited differential value"
        else:
            return "Balanced Strategy - Good mix of safety and opportunity"

    def get_optimal_ownership_targets(self, position: str, budget_tier: str) -> Dict:
        """
        Get optimal ownership targets for specific position and budget tier
        Based on research findings about successful ownership strategies
        """

        # Research-based optimal ownership ranges
        optimal_ranges = {
            'premium': {  # >£9.0M players
                'GK': {'min': 15, 'max': 40, 'sweet_spot': 25},
                'DEF': {'min': 20, 'max': 50, 'sweet_spot': 35},
                'MID': {'min': 25, 'max': 60, 'sweet_spot': 40},
                'FWD': {'min': 30, 'max': 70, 'sweet_spot': 50}
            },
            'mid': {  # £6.0-9.0M players
                'GK': {'min': 5, 'max': 25, 'sweet_spot': 15},
                'DEF': {'min': 10, 'max': 35, 'sweet_spot': 20},
                'MID': {'min': 15, 'max': 45, 'sweet_spot': 30},
                'FWD': {'min': 20, 'max': 50, 'sweet_spot': 35}
            },
            'budget': {  # <£6.0M players
                'GK': {'min': 2, 'max': 15, 'sweet_spot': 8},
                'DEF': {'min': 5, 'max': 25, 'sweet_spot': 12},
                'MID': {'min': 3, 'max': 20, 'sweet_spot': 10},
                'FWD': {'min': 5, 'max': 30, 'sweet_spot': 15}
            }
        }

        targets = optimal_ranges.get(budget_tier, {}).get(position, {})

        if not targets:
            return {'error': f'No targets defined for {position} in {budget_tier} tier'}

        return {
            'position': position,
            'budget_tier': budget_tier,
            'optimal_range': f"{targets['min']}-{targets['max']}%",
            'sweet_spot': f"{targets['sweet_spot']}%",
            'strategy_notes': self._get_strategy_notes(position, budget_tier)
        }

    def _get_strategy_notes(self, position: str, budget_tier: str) -> List[str]:
        """Get strategy notes for position/budget combination"""

        notes = {
            'premium': {
                'GK': ['Premium GKs should have moderate ownership', 'Avoid very high ownership unless exceptional'],
                'DEF': ['Premium defenders can have higher ownership', 'Look for attacking returns'],
                'MID': ['Premium mids are ownership-flexible', 'Focus on underlying stats over ownership'],
                'FWD': ['Premium forwards often high ownership', 'Template picks acceptable if stats support']
            },
            'mid': {
                'GK': ['Mid-price GKs ideal for differentials', 'Look for good fixtures and low ownership'],
                'DEF': ['Mid-price defenders excellent for balance', 'Moderate ownership often optimal'],
                'MID': ['Mid-price mids perfect for differentials', 'Target 15-30% ownership range'],
                'FWD': ['Mid-price forwards great value', 'Can afford higher ownership if delivering']
            },
            'budget': {
                'GK': ['Budget GKs should be low ownership', 'Enable funds elsewhere'],
                'DEF': ['Budget defenders for rotation', 'Very low ownership acceptable'],
                'MID': ['Budget mids rare but powerful', 'Extreme differentials can pay off'],
                'FWD': ['Budget forwards for bench mainly', 'Ownership less important']
            }
        }

        return notes.get(budget_tier, {}).get(position, ['No specific notes available'])

    def simulate_ownership_impact(self, base_score: float, ownership_adjustments: List[Dict]) -> Dict:
        """
        Simulate impact of different ownership strategies on team performance
        """

        scenarios = {
            'template_heavy': sum(adj['final_modifier'] for adj in ownership_adjustments if
                                  adj['ownership_bracket'] in ['template', 'popular']),
            'balanced': sum(adj['final_modifier'] for adj in ownership_adjustments) / len(ownership_adjustments),
            'differential_heavy': sum(adj['final_modifier'] for adj in ownership_adjustments if
                                      adj['ownership_bracket'] in ['differential', 'contrarian'])
        }

        results = {}
        for strategy, impact in scenarios.items():
            adjusted_score = base_score * (1 + impact)
            results[strategy] = {
                'adjusted_score': round(adjusted_score, 4),
                'impact': round(impact, 4),
                'performance_change': f"{impact * 100:+.1f}%"
            }

        return {
            'base_score': base_score,
            'scenarios': results,
            'recommended_strategy': max(results.keys(), key=lambda k: results[k]['adjusted_score'])
        }

    def get_ownership_insights(self) -> Dict:
        """Get insights about ownership strategy from research"""

        return {
            'key_principles': [
                'Very low ownership (<5%) players offer highest differential potential',
                'Template players (>50%) provide safety but limit rank gains',
                'Optimal range for most players is 15-35% ownership',
                'Late season favors differential strategies more heavily',
                'Position affects ownership impact (FWD > MID > DEF > GK)'
            ],
            'strategy_guidelines': [
                'Early season: Prioritize safety with 2-3 template picks',
                'Mid season: Balance safety and differentials (60/40 split)',
                'Late season: Increase differential exposure for rank climbing',
                'Always maintain 1-2 premium template picks for stability'
            ],
            'common_mistakes': [
                'Too many template picks (>40% of team)',
                'Chasing very low ownership without strong stats',
                'Ignoring ownership when making captain choices',
                'Not adjusting strategy based on current rank'
            ]
        }