from dataclasses import dataclass
from typing import Optional

@dataclass
class StandardPlayer:
    player_id: int
    name: str
    position: str
    team_name: str
    price: float
    total_points: int
    momentum_score: float
    minutes: int
    form: float
    selected_by_percent: float
    goals_scored: int = 0
    assists: int = 0
    clean_sheets: int = 0
    chance_of_playing: int = 100

    def to_dict(self) -> dict:
        return {
            'player_id': self.player_id,
            'name': self.name,
            'position': self.position,
            'team_name': self.team_name,
            'price': self.price,
            'total_points': self.total_points,
            'momentum_score': self.momentum_score,
            'minutes': self.minutes,
            'form': self.form,
            'selected_by_percent': self.selected_by_percent,
            'goals_scored': self.goals_scored,
            'assists': self.assists,
            'clean_sheets': self.clean_sheets,
            'chance_of_playing': self.chance_of_playing
        }

GLOBAL_SEED = 42