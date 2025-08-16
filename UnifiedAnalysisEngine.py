import random
from typing import List, Dict, Optional
from standard_player_schema import StandardPlayer, GLOBAL_SEED
from central_cache import cache

random.seed(GLOBAL_SEED)


class UnifiedAnalysisEngine:
    def __init__(self):
        # Randomizer thresholds - ערכים מוכחים שעובדים (balanced profile)
        self.randomizer_thresholds = {
            0.9: 0.45,  # 45% chance for exceptional players
            0.8: 0.30,  # 30% chance for high momentum
            0.7: 0.18,  # 18% chance for good momentum
            0.6: 0.12,  # 12% chance for decent momentum
            0.0: 0.06  # 6% baseline chance
        }

        # Ownership-based modifiers (balanced approach)
        self.ownership_modifiers = {
            'very_low': 0.15,  # <5% ownership - differential bonus
            'low': 0.08,  # 5-15% ownership - moderate bonus
            'medium': 0.0,  # 15-30% ownership - neutral
            'high': -0.05,  # 30-50% ownership - small penalty
            'very_high': -0.10  # >50% ownership - template penalty
        }

        # Multi-objective weights
        self.analysis_weights = {
            'momentum': 0.4,
            'value': 0.25,
            'fixtures': 0.20,
            'form': 0.15
        }

    def analyze_player(self, player: StandardPlayer) -> Dict:
        """ניתוח שחקן בסיסי ויעיל"""
        cache_key = f"player_analysis_{player.player_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        selected, level = self._apply_randomizer(player)
        multi_score = self._calculate_multi_objective_score(player)

        result = {
            'player': player.to_dict(),
            'momentum_level': level,
            'selected': selected,
            'recommendation': self._get_recommendation(player, selected),
            'captain_score': self._calculate_captain_score(player),
            'transfer_priority': self._calculate_transfer_priority(player),
            'multi_objective_score': multi_score,
            'ownership_category': self._get_ownership_category(player.selected_by_percent),
            'value_rating': self._calculate_value_rating(player)
        }

        cache.set(cache_key, result)
        return result

    def _apply_randomizer(self, player: StandardPlayer) -> tuple:
        """Randomizer פשוט ויעיל עם ownership consideration"""
        base_momentum = player.momentum_score
        ownership_category = self._get_ownership_category(player.selected_by_percent)
        ownership_modifier = self.ownership_modifiers.get(ownership_category, 0.0)

        for threshold, base_chance in self.randomizer_thresholds.items():
            if base_momentum >= threshold:
                adjusted_chance = base_chance + ownership_modifier
                adjusted_chance = max(0.02, min(0.60, adjusted_chance))

                selected = random.random() < adjusted_chance
                level = self._get_momentum_level(base_momentum)
                return selected, level

        return False, 'very_low'

    def get_captain_options(self, squad_players: List[StandardPlayer]) -> List[Dict]:
        """המלצות קפטן מתוך הסגל הקיים - פיצ'ר חיוני!"""
        if not squad_players:
            return []

        # סנן רק שחקנים תוקפניים מהסגל
        attacking_players = [p for p in squad_players
                             if p.position in ['MID', 'FWD'] and p.momentum_score >= 0.5]

        if not attacking_players:
            # אם אין תוקפנים טובים, קח את הכל
            attacking_players = [p for p in squad_players if p.position in ['MID', 'FWD']]

        captain_options = []
        for player in attacking_players:
            analysis = self.analyze_player(player)
            captain_options.append(analysis)

        # מיין לפי captain score
        captain_options.sort(key=lambda x: x['captain_score'], reverse=True)

        # החזר top 5 או פחות
        return captain_options[:5]

    def get_transfer_targets(self, all_players: List[StandardPlayer],
                             current_squad: List[StandardPlayer] = None,
                             player_to_sell: StandardPlayer = None,
                             available_budget: float = 2.0) -> List[Dict]:
        """המלצות חילופים חכמות - מכירה + קנייה"""

        # אם לא נבחר שחקן למכירה, הצג את השחקנים הזמינים
        if player_to_sell is None:
            return {"available_to_sell": self._get_sellable_players(current_squad)}

        # חישוב תקציב אמיתי
        real_budget = available_budget + player_to_sell.price

        # שחקנים זמינים (לא בסגל הנוכחי)
        if current_squad:
            current_ids = {p.player_id for p in current_squad}
            available_players = [p for p in all_players if p.player_id not in current_ids]
        else:
            available_players = all_players

        # סנן לפי תקציב אמיתי ועמדה דומה
        target_position = player_to_sell.position
        affordable_players = [p for p in available_players
                              if p.price <= real_budget and
                              p.momentum_score >= 0.6 and
                              (p.position == target_position or self._is_position_compatible(p.position,
                                                                                             target_position))]

        transfer_targets = []
        for player in affordable_players:
            analysis = self.analyze_player(player)
            if analysis['selected'] or analysis['multi_objective_score'] >= 0.7:
                # הוסף השוואה עם השחקן הנמכר
                analysis['comparison'] = self._compare_players(player_to_sell, player)
                analysis['price_difference'] = player.price - player_to_sell.price
                analysis['budget_remaining'] = real_budget - player.price
                transfer_targets.append(analysis)

        # מיין לפי transfer priority
        transfer_targets.sort(key=lambda x: x['transfer_priority'], reverse=True)

        return {
            'selling_player': player_to_sell.to_dict(),
            'real_budget': real_budget,
            'targets': transfer_targets[:10]
        }

    def _get_sellable_players(self, current_squad: List[StandardPlayer]) -> List[Dict]:
        """רשימת שחקנים שאפשר למכור מהסגל"""
        if not current_squad:
            return []

        sellable = []
        for player in current_squad:
            analysis = self.analyze_player(player)
            # מיין לפי מי הכי כדאי למכור (momentum נמוך, value נמוך)
            sell_priority = 1.0 - (analysis['multi_objective_score'] * 0.7 + analysis['value_rating'] * 0.3)

            sellable.append({
                'player': player.to_dict(),
                'analysis': analysis,
                'sell_priority': sell_priority,
                'reasoning': self._get_sell_reasoning(player, analysis)
            })

        # מיין לפי עדיפות מכירה (גבוה = כדאי למכור)
        return sorted(sellable, key=lambda x: x['sell_priority'], reverse=True)

    def _is_position_compatible(self, new_position: str, old_position: str) -> bool:
        """בדיקה אם עמדות תואמות להחלפה"""
        # אפשר החלפה בין MID/FWD לעתים
        if old_position == 'MID' and new_position == 'FWD':
            return True
        if old_position == 'FWD' and new_position == 'MID':
            return True
        return False

    def _compare_players(self, old_player: StandardPlayer, new_player: StandardPlayer) -> Dict:
        """השוואה בין שחקן ישן לחדש"""
        momentum_diff = new_player.momentum_score - old_player.momentum_score
        points_diff = new_player.total_points - old_player.total_points
        form_diff = new_player.form - old_player.form if new_player.form and old_player.form else 0

        return {
            'momentum_improvement': round(momentum_diff, 3),
            'points_difference': int(points_diff),
            'form_improvement': round(form_diff, 1),
            'recommendation': self._get_transfer_recommendation(momentum_diff, new_player.price - old_player.price)
        }

    def _get_transfer_recommendation(self, momentum_diff: float, price_diff: float) -> str:
        """המלצה להעברה"""
        if momentum_diff > 0.15:
            return "EXCELLENT UPGRADE - שיפור משמעותי"
        elif momentum_diff > 0.05:
            return "GOOD UPGRADE - שיפור טוב"
        elif momentum_diff > -0.05:
            if price_diff < -1.0:
                return "SIDEWAYS MOVE - חוסך כסף"
            else:
                return "SIDEWAYS MOVE - שיפור קל"
        else:
            return "QUESTIONABLE - בדוק שוב"

    def _get_sell_reasoning(self, player: StandardPlayer, analysis: Dict) -> str:
        """נימוק למכירת השחקן"""
        reasons = []

        if player.momentum_score < 0.5:
            reasons.append("Momentum נמוך")
        if player.form < 3.0:
            reasons.append("Form חלש")
        if analysis['value_rating'] < 0.4:
            reasons.append("Value נמוך")
        if player.selected_by_percent > 50:
            reasons.append("Ownership גבוה מדי")
        if player.chance_of_playing < 80:
            reasons.append("סיכון רוטציה")

        if not reasons:
            reasons.append("ביצועים סבירים")

        return " | ".join(reasons[:3])  # מקסימום 3 סיבות

    def get_value_picks(self, players: List[StandardPlayer], max_price: float = 7.0) -> List[Dict]:
        """Value picks תחת מחיר מסוים"""
        budget_players = [p for p in players if p.price <= max_price]

        value_picks = []
        for player in budget_players:
            analysis = self.analyze_player(player)
        if analysis['value_rating'] >= 0.7:
            analysis['recommendation'] = analysis.get('recommendation', 'Value Pick')
            value_picks.append(analysis)

        return sorted(value_picks, key=lambda x: x['value_rating'], reverse=True)[:10]

    def get_top_players(self, players: List[StandardPlayer], limit: int = 20) -> List[Dict]:
        """שחקנים מובילים לפי multi-objective score"""
        analyzed_players = [self.analyze_player(p) for p in players]
        sorted_players = sorted(analyzed_players,
                                key=lambda x: x['multi_objective_score'],
                                reverse=True)
        return sorted_players[:limit]

    def get_position_leaders(self, players: List[StandardPlayer], position: str, limit: int = 5) -> List[Dict]:
        """מובילים לפי עמדה"""
        position_players = [p for p in players if p.position == position]
        analyzed_players = [self.analyze_player(p) for p in position_players]
        sorted_players = sorted(analyzed_players,
                                key=lambda x: x['multi_objective_score'],
                                reverse=True)
        return sorted_players[:limit]

    def quick_analysis(self, player_name: str, all_players: List[StandardPlayer]) -> Dict:
        """ניתוח מהיר של שחקן בודד"""
        for player in all_players:
            if player_name.lower() in player.name.lower():
                return self.analyze_player(player)
        return {"error": f"שחקן {player_name} לא נמצא"}

    def _calculate_multi_objective_score(self, player: StandardPlayer) -> float:
        """Multi-objective score משופר"""
        try:
            momentum_score = player.momentum_score or 0.0
            price = max(player.price, 4.0)  # מינימום מחיר

            value_score = min(1.0, momentum_score / (price / 10.0))
            form_score = min(1.0, (player.form or 0.0) / 10.0) if player.form and player.form > 0 else 0.5
            fixture_score = 0.7  # ברירת מחדל - יכול להשתלב עם FixtureAnalyzer

            multi_score = (
                    momentum_score * self.analysis_weights['momentum'] +
                    value_score * self.analysis_weights['value'] +
                    fixture_score * self.analysis_weights['fixtures'] +
                    form_score * self.analysis_weights['form']
            )

            return round(multi_score, 4)
        except Exception as e:
            return (player.momentum_score or 0.0) * 0.8

    def _calculate_captain_score(self, player: StandardPlayer) -> float:
        """חישוב ציון קפטן פשוט ויעיל"""
        try:
            if player.position not in ['MID', 'FWD']:
                return 0.0

            momentum = player.momentum_score or 0.0
            points = player.total_points or 0
            form = player.form or 0.0

            # ציון בסיסי
            base_score = (
                    momentum * 0.4 +
                    min(points / 200.0, 1.0) * 0.3 +
                    min(form / 10.0, 1.0) * 0.2
            )

            # בונוס לשחקנים יקרים (צפויים לבצע)
            if player.price >= 10.0:
                base_score += 0.05

            # בונוס לform חם
            if form >= 6.0:
                base_score += 0.1

            return min(1.0, max(0.0, base_score))
        except Exception as e:
            return 0.0

    def _calculate_transfer_priority(self, player: StandardPlayer) -> float:
        """עדיפות להעברה - value + momentum + form"""
        try:
            momentum = player.momentum_score or 0.0
            price = max(player.price, 4.0)
            form = player.form or 0.0

            # Value factor
            value_factor = momentum / (price / 8.0)

            # Form bonus
            form_bonus = min(0.1, form / 50.0)

            # Ownership bonus for differentials
            ownership_bonus = 0.0
            ownership = player.selected_by_percent or 0.0
            if ownership < 10:
                ownership_bonus = 0.15
            elif ownership < 20:
                ownership_bonus = 0.08

            transfer_priority = (
                    momentum * 0.5 +
                    value_factor * 0.3 +
                    form_bonus +
                    ownership_bonus
            )

            return min(1.0, max(0.0, transfer_priority))
        except Exception as e:
            return (player.momentum_score or 0.0) * 0.7

    def _calculate_value_rating(self, player: StandardPlayer) -> float:
        """דירוג value - ביצועים למחיר"""
        try:
            if player.price <= 0:
                return 0.0

            ppm = (player.total_points or 0) / player.price  # Points per million
            mpm = (player.momentum_score or 0.0) / (player.price / 10.0)  # Momentum per million

            value_rating = (ppm / 30.0 * 0.6 + mpm * 0.4)
            return min(1.0, max(0.0, value_rating))
        except Exception as e:
            return 0.5

    def _get_ownership_category(self, ownership_pct: float) -> str:
        """קטגוריית ownership"""
        if ownership_pct is None:
            ownership_pct = 0.0

        if ownership_pct < 5.0:
            return 'very_low'
        elif ownership_pct < 15.0:
            return 'low'
        elif ownership_pct < 30.0:
            return 'medium'
        elif ownership_pct < 50.0:
            return 'high'
        else:
            return 'very_high'

    def _get_momentum_level(self, score: float) -> str:
        """רמת momentum"""
        if score is None:
            score = 0.0

        if score >= 0.9:
            return 'exceptional'
        elif score >= 0.8:
            return 'high'
        elif score >= 0.7:
            return 'medium'
        elif score >= 0.6:
            return 'low'
        else:
            return 'very_low'

    def _get_recommendation(self, player: StandardPlayer, selected: bool) -> str:
        """המלצה פשוטה וברורה"""
        momentum = player.momentum_score or 0.0
        ownership = player.selected_by_percent or 0.0

        if not selected:
            if momentum > 0.7:
                return 'MONITOR - פוטנציאל גבוה'
            elif momentum > 0.5:
                return 'HOLD - אופציה סבירה'
            else:
                return 'AVOID - מדדים חלשים'

        # שחקנים נבחרים
        if momentum >= 0.9:
            if ownership < 15:
                return 'STRONG BUY - Differential מעולה'
            else:
                return 'STRONG BUY - בחירה מעולה'
        elif momentum >= 0.8:
            return 'BUY - בחירה טובה'
        elif momentum >= 0.7:
            return 'CONSIDER - שקול'
        else:
            return 'MONITOR - עקוב'

    def validate_analysis_system(self) -> Dict:
        """וולידציה של המערכת המנוקה"""
        return {
            'system_status': 'simplified_and_functional',
            'core_features': [
                'Enhanced momentum calculation',
                'Multi-objective player scoring',
                'Captain recommendations from squad',
                'Transfer targets by budget',
                'Value picks analysis',
                'Quick player lookup'
            ],
            'removed_complexity': [
                'Risk profiles system',
                'Advanced ownership strategies',
                'Complex profile fitting',
                'Unnecessary analytical layers'
            ],
            'randomizer_enhanced': True,
            'ownership_logic': True,
            'captain_selection': True,
            'transfer_recommendations': True
        }