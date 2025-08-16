#!/usr/bin/env python3

import os
import sys
import shutil
from pathlib import Path


def backup_old_system():
    backup_dir = Path("old_system_backup")
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    backup_dir.mkdir()

    old_files = [
        'data_fetcher.py', 'DataManager.py', 'MomentumAnalyzer.py',
        'MomentumIntegration.py', 'DecisionEngine.py', 'FixtureAnalyzer.py',
        'MomentumVisualizer.py', 'ReportGenerator.py'
    ]

    for file in old_files:
        if os.path.exists(file):
            shutil.copy2(file, backup_dir / file)
            print(f"📦 גיבוי {file}")


def create_unified_files():
    files_content = {
        'standard_player_schema.py': '''from dataclasses import dataclass
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

GLOBAL_SEED = 42''',

        'central_cache.py': '''import time
import hashlib
from typing import Any, Optional

class CentralCache:
    def __init__(self, timeout: int = 1800):
        self.cache = {}
        self.timeout = timeout

    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            timestamp, data = self.cache[key]
            if time.time() - timestamp < self.timeout:
                return data
            else:
                del self.cache[key]
        return None

    def set(self, key: str, value: Any):
        self.cache[key] = (time.time(), value)

    def clear(self):
        self.cache.clear()

    def make_key(self, *args, **kwargs) -> str:
        content = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(content.encode()).hexdigest()

cache = CentralCache()''',

        'requirements.txt': '''requests>=2.25.0
pandas>=1.3.0
numpy>=1.21.0'''
    }

    for filename, content in files_content.items():
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ נוצר {filename}")


def install_requirements():
    try:
        import subprocess
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ הותקנו תלויות")
    except:
        print("⚠️  התקן ידנית: pip install requests pandas numpy")


def test_system():
    try:
        from main import UnifiedFPLSystem
        system = UnifiedFPLSystem()
        print("✅ המערכת הממוזגת עובדת")
        return True
    except Exception as e:
        print(f"❌ שגיאה במערכת: {e}")
        return False


def main():
    print("🔧 התקנת מערכת FPL Assistant ממוזגת")
    print("=" * 45)

    print("\n1. גיבוי מערכת ישנה...")
    backup_old_system()

    print("\n2. יצירת קבצי עזר...")
    create_unified_files()

    print("\n3. התקנת תלויות...")
    install_requirements()

    print("\n4. בדיקת מערכת...")
    if test_system():
        print("\n🎉 ההתקנה הושלמה בהצלחה!")
        print("\nהפעל: python unified_main_system.py")
    else:
        print("\n❌ ההתקנה נכשלה")
        print("בדוק שכל הקבצים קיימים")


if __name__ == "__main__":
    main()