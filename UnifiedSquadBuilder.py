import random
from typing import List, Dict
from standard_player_schema import StandardPlayer, GLOBAL_SEED
from central_cache import cache

random.seed(GLOBAL_SEED)


class UnifiedSquadBuilder:
    def __init__(self, budget: float = 100.0):
        self.budget = budget
        self.formation = {'GK': 1, 'DEF': 4, 'MID': 4, 'FWD': 2}
        self.bench_formation = {'GK': 1, 'DEF': 1, 'MID': 1, 'FWD': 1}

    def build_squad(self, all_players: List[StandardPlayer]) -> Dict:
        cache_key = f"squad_{self.budget}_{len(all_players)}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        players_by_position = self._group_by_position(all_players)

        starting_xi = []
        bench = []
        total_cost = 0
        used_teams = {}  # מעקב על קבוצות משותף לכל הסגל

        for position, count in self.formation.items():
            position_players = self._sort_players(players_by_position[position])
            selected = self._select_players(position_players, count, self.budget - total_cost, used_teams)
            starting_xi.extend(selected)
            total_cost += sum(p.price for p in selected)

        for position, count in self.bench_formation.items():
            remaining_players = [p for p in players_by_position[position]
                                 if p not in starting_xi]
            selected = self._select_players(remaining_players, count, self.budget - total_cost, used_teams)
            bench.extend(selected)
            total_cost += sum(p.price for p in selected)

        captain = self._select_captain(starting_xi)

        result = {
            'starting_xi': [p.to_dict() for p in starting_xi],
            'bench': [p.to_dict() for p in bench],
            'captain': captain.to_dict() if captain else None,
            'total_cost': round(total_cost, 1),
            'formation': '4-4-2',
            'valid': self._validate_squad(starting_xi + bench)
        }

        cache.set(cache_key, result)
        return result

    def _group_by_position(self, players: List[StandardPlayer]) -> Dict:
        groups = {'GK': [], 'DEF': [], 'MID': [], 'FWD': []}
        for p in players:
            try:
                if (p.position in groups and
                        p.chance_of_playing is not None and
                        p.chance_of_playing >= 75 and
                        p.price > 0):
                    groups[p.position].append(p)
            except:
                continue
        return groups

    def _sort_players(self, players: List[StandardPlayer]) -> List[StandardPlayer]:
        try:
            return sorted(players, key=lambda p: (p.momentum_score or 0) / max(p.price, 4.0), reverse=True)
        except:
            return sorted(players, key=lambda p: p.momentum_score or 0, reverse=True)

    def _select_players(self, players: List[StandardPlayer], count: int, budget: float, used_teams: Dict) -> List[StandardPlayer]:
        selected = []

        for player in players:
            try:
                if len(selected) >= count:
                    break
                if used_teams.get(player.team_name, 0) >= 3:
                    continue
                current_cost = sum(getattr(p, 'price', 4.0) for p in selected)
                if current_cost + getattr(player, 'price', 4.0) > budget:
                    continue

                selected.append(player)
                used_teams[player.team_name] = used_teams.get(player.team_name, 0) + 1
            except:
                continue

        while len(selected) < count and players:
            try:
                remaining = [p for p in players if p not in selected]
                if not remaining:
                    break
                cheapest = min(remaining, key=lambda p: getattr(p, 'price', 99.0))
                current_cost = sum(getattr(p, 'price', 4.0) for p in selected)
                if current_cost + getattr(cheapest, 'price', 4.0) <= budget:
                    selected.append(cheapest)
                    used_teams[cheapest.team_name] = used_teams.get(cheapest.team_name, 0) + 1
                else:
                    break
            except:
                break

        return selected

    def _select_captain(self, players: List[StandardPlayer]) -> StandardPlayer:
        try:
            attacking = [p for p in players if getattr(p, 'position', 'MID') in ['MID', 'FWD']]
            if attacking:
                return max(attacking, key=lambda p: (getattr(p, 'momentum_score', 0) +
                                                     getattr(p, 'total_points', 0) / 200.0))
            return max(players, key=lambda p: getattr(p, 'momentum_score', 0)) if players else None
        except:
            return players[0] if players else None

    def _validate_squad(self, squad: List[StandardPlayer]) -> bool:
        if len(squad) != 15:
            return False
        positions = {'GK': 0, 'DEF': 0, 'MID': 0, 'FWD': 0}
        teams = {}

        for p in squad:
            positions[p.position] += 1
            teams[p.team_name] = teams.get(p.team_name, 0) + 1

        return (positions == {'GK': 2, 'DEF': 5, 'MID': 5, 'FWD': 3} and
                all(count <= 3 for count in teams.values()))