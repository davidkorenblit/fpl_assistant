#!/usr/bin/env python3

import os
import sys
import webbrowser
from pathlib import Path
from typing import Dict, List

from UnifiedDataManager import UnifiedDataManager
from UnifiedSquadBuilder import UnifiedSquadBuilder
from UnifiedAnalysisEngine import UnifiedAnalysisEngine
from UnifiedReportGenerator import UnifiedReportGenerator
from standard_player_schema import StandardPlayer


class SimpleFPLSystem:
    """מערכת FPL פשוטה ויעילה עם הפיצ'רים החיוניים"""

    def __init__(self):
        self.data_manager = UnifiedDataManager()
        self.squad_builder = UnifiedSquadBuilder()
        self.analysis_engine = UnifiedAnalysisEngine()
        self.report_generator = UnifiedReportGenerator()
        self.current_squad = None
        self.all_players = None

    def load_data(self):
        """טעינת נתונים - רק פעם אחת"""
        if self.all_players is None:
            print("📊 טוען נתונים...")
            self.all_players = self.data_manager.fetch_and_process_data()
            if self.all_players:
                print(f"✅ נטענו {len(self.all_players)} שחקנים")
            else:
                print("❌ שגיאה בטעינת נתונים")
        return bool(self.all_players)

    def run_full_analysis(self, budget: float = 100.0) -> str:
        """ניתוח מלא + דוח"""
        try:
            if not self.load_data():
                return "❌ לא נטענו נתונים"

            print("🏗️ בונה סגל...")
            self.squad_builder.budget = budget
            squad_data = self.squad_builder.build_squad(self.all_players)

            if not squad_data.get('valid'):
                return "❌ לא נבנה סגל תקין"

            # שמור את הסגל הנוכחי
            self.current_squad = []
            for player_dict in squad_data['starting_xi'] + squad_data['bench']:
                for player in self.all_players:
                    if player.player_id == player_dict['player_id']:
                        self.current_squad.append(player)
                        break

            print("🔍 מנתח שחקנים...")
            top_analysis = self.analysis_engine.get_top_players(self.all_players, 20)

            # קפטן מהסגל הנוכחי
            captain_options = self.analysis_engine.get_captain_options(self.current_squad)

            # המלצות החלפות לדוח
            transfer_data = self.analysis_engine.get_transfer_targets(self.all_players, self.current_squad)
            transfer_targets = transfer_data.get('available_to_sell', [])[:6]

            print("📋 יוצר דוח...")
            report_path = self.report_generator.generate_html_report(
                squad_data, top_analysis, captain_options, transfer_targets
            )

            print(f"✅ דוח נוצר: {report_path}")
            return report_path

        except Exception as e:
            return f"❌ שגיאה: {str(e)}"

    def get_captain_recommendations(self) -> List[Dict]:
        """המלצות קפטן מהסגל הנוכחי"""
        if not self.current_squad:
            print("⚠️ תחילה הרץ ניתוח מלא לבניית סגל")
            return []

        return self.analysis_engine.get_captain_options(self.current_squad)

    def get_transfer_recommendations(self) -> Dict:
        """המלצות חילופים - שלב 1: בחירת שחקן למכירה"""
        if not self.current_squad:
            return {"error": "תחילה הרץ ניתוח מלא לבניית סגל"}

        if not self.load_data():
            return {"error": "לא נטענו נתונים"}

        # קבל רשימת שחקנים למכירה
        transfer_data = self.analysis_engine.get_transfer_targets(
            self.all_players, self.current_squad
        )

        return transfer_data

    def execute_transfer_analysis(self, player_to_sell_id: int, available_budget: float = 2.0) -> Dict:
        """המלצות חילופים - שלב 2: ניתוח תחליפים"""
        if not self.current_squad or not self.all_players:
            return {"error": "נתונים לא זמינים"}

        # מצא את השחקן למכירה
        player_to_sell = None
        for player in self.current_squad:
            if player.player_id == player_to_sell_id:
                player_to_sell = player
                break

        if not player_to_sell:
            return {"error": "שחקן לא נמצא בסגל"}

        # קבל המלצות תחליפים
        return self.analysis_engine.get_transfer_targets(
            self.all_players, self.current_squad, player_to_sell, available_budget
        )

    def quick_player_search(self, player_name: str) -> Dict:
        """חיפוש מהיר של שחקן"""
        if not self.load_data():
            return {"error": "לא נטענו נתונים"}

        return self.analysis_engine.quick_analysis(player_name, self.all_players)

    def get_value_picks(self, max_price: float = 7.0) -> List[Dict]:
        """Value picks תחת מחיר מסוים"""
        if not self.load_data():
            return []

        return self.analysis_engine.get_value_picks(self.all_players, max_price)

    def get_system_status(self) -> Dict:
        """סטטוס המערכת"""
        return {
            'data_loaded': self.all_players is not None,
            'players_count': len(self.all_players) if self.all_players else 0,
            'squad_built': self.current_squad is not None,
            'squad_size': len(self.current_squad) if self.current_squad else 0,
            'system_validation': self.analysis_engine.validate_analysis_system()
        }

    # ==================== תוספות חדשות - ניהול הרכב קיים ====================

    def parse_squad_file(self, filepath: str) -> List[StandardPlayer]:
        """פרסור קובץ הרכב לרשימת StandardPlayer objects"""
        try:
            if not os.path.exists(filepath):
                print(f"❌ הקובץ {filepath} לא קיים")
                return []

            if not self.load_data():
                print("❌ לא נטענו נתוני שחקנים")
                return []

            squad_players = []

            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            print(f"📖 קורא {len(lines)} שורות מהקובץ...")

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    # פורמט: "POSITION: Player Name - Team - Price"
                    if ':' not in line or '-' not in line:
                        print(f"⚠️ שורה {line_num} לא בפורמט נכון: {line}")
                        continue

                    parts = line.split(':')
                    if len(parts) != 2:
                        print(f"⚠️ שורה {line_num} - בעיה בפורמט: {line}")
                        continue

                    position = parts[0].strip()
                    player_info = parts[1].strip()

                    # פרסור: "Player Name - Team - Price"
                    info_parts = player_info.split(' - ')
                    if len(info_parts) != 3:
                        print(f"⚠️ שורה {line_num} - בעיה בפרטי שחקן: {player_info}")
                        continue

                    player_name = info_parts[0].strip()
                    team_name = info_parts[1].strip()
                    try:
                        price = float(info_parts[2].strip())
                    except ValueError:
                        print(f"⚠️ שורה {line_num} - מחיר לא תקין: {info_parts[2]}")
                        continue

                    # חיפוש השחקן במאגר
                    found_player = self._find_player_in_database(player_name, team_name, position, price)
                    if found_player:
                        squad_players.append(found_player)
                        print(f"✅ נמצא: {found_player.name} ({found_player.position}) - {found_player.team_name}")
                    else:
                        print(f"❌ לא נמצא: {player_name} ({position}) - {team_name}")

                except Exception as e:
                    print(f"❌ שגיאה בשורה {line_num}: {e}")
                    continue

            print(f"✅ נטענו {len(squad_players)} שחקנים מתוך {len(lines)} שורות")
            return squad_players

        except Exception as e:
            print(f"❌ שגיאה בקריאת הקובץ: {e}")
            return []

    def _find_player_in_database(self, player_name: str, team_name: str, position: str, price: float) -> StandardPlayer:
        """מציאת שחקן במאגר על פי שם, קבוצה, עמדה ומחיר"""
        if not self.all_players:
            return None

        # חיפוש מדויק
        for player in self.all_players:
            if (player.name.lower() == player_name.lower() and
                    player.team_name.lower() == team_name.lower() and
                    player.position == position and
                    abs(player.price - price) < 0.1):
                return player

        # חיפוש חלקי - רק שם ועמדה
        for player in self.all_players:
            if (player_name.lower() in player.name.lower() and
                    player.position == position and
                    abs(player.price - price) < 0.5):
                return player

        # חיפוש רחב יותר - רק שם
        for player in self.all_players:
            if player_name.lower() in player.name.lower():
                return player

        return None

    def export_current_squad(self, filepath: str = None) -> str:
        """ייצוא הסגל הנוכחי לקובץ טקסט"""
        try:
            if not self.current_squad:
                return "❌ אין סגל נוכחי לייצוא - תחילה הרץ ניתוח מלא"

            if filepath is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filepath = f"my_squad_{timestamp}.txt"

            # ארגון השחקנים לפי עמדות
            positions_order = ['GK', 'DEF', 'MID', 'FWD']
            organized_squad = {pos: [] for pos in positions_order}

            for player in self.current_squad:
                if player.position in organized_squad:
                    organized_squad[player.position].append(player)

            # כתיבה לקובץ
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("# FPL Squad Export\n")
                f.write(f"# Generated: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
                f.write("# Format: POSITION: Player Name - Team - Price\n\n")

                for position in positions_order:
                    players = organized_squad[position]
                    if players:
                        for player in players:
                            f.write(f"{position}: {player.name} - {player.team_name} - {player.price:.1f}\n")

            print(f"✅ הסגל יוצא לקובץ: {filepath}")
            return filepath

        except Exception as e:
            return f"❌ שגיאה בייצוא: {e}"

    def get_captain_from_imported_squad(self, squad_players: List[StandardPlayer]) -> List[Dict]:
        """המלצות קפטן מהרכב מיובא"""
        if not squad_players:
            return []

        return self.analysis_engine.get_captain_options(squad_players)

    def get_transfers_from_imported_squad(self, squad_players: List[StandardPlayer]) -> Dict:
        """המלצות חילופים מהרכב מיובא"""
        if not squad_players:
            return {"error": "אין שחקנים בהרכב המיובא"}

        if not self.load_data():
            return {"error": "לא נטענו נתונים"}

        return self.analysis_engine.get_transfer_targets(self.all_players, squad_players)

    def execute_imported_transfer_analysis(self, squad_players: List[StandardPlayer],
                                           player_to_sell_id: int, available_budget: float = 2.0) -> Dict:
        """המלצות תחליפים להרכב מיובא"""
        if not squad_players or not self.all_players:
            return {"error": "נתונים לא זמינים"}

        # מצא את השחקן למכירה
        player_to_sell = None
        for player in squad_players:
            if player.player_id == player_to_sell_id:
                player_to_sell = player
                break

        if not player_to_sell:
            return {"error": "שחקן לא נמצא בהרכב המיובא"}

        return self.analysis_engine.get_transfer_targets(
            self.all_players, squad_players, player_to_sell, available_budget
        )


def main():
    print("🚀 FPL Assistant - מערכת פשוטה ויעילה")
    print("=" * 45)

    system = SimpleFPLSystem()

    while True:
        print("\n📋 תפריט:")
        print("1. ניתוח מלא + בניית סגל")
        print("2. המלצות קפטן מהסגל")
        print("3. המלצות חילופים")
        print("4. חיפוש שחקן")
        print("5. סטטוס מערכת")
        print("6. יציאה")
        print("7. ניהול הרכב קיים")  # תוספת חדשה

        choice = input("\nבחר (1-7): ").strip()

        if choice == '1':
            budget = input("תקציב [100]: ").strip()
            budget = float(budget) if budget else 100.0

            result = system.run_full_analysis(budget)

            if result.endswith('.html'):
                open_browser = input("לפתוח דוח? (y/n): ").strip().lower()
                if open_browser != 'n':
                    webbrowser.open(f'file://{Path(result).absolute()}')
            else:
                print(result)

        elif choice == '2':
            print("\n👑 המלצות קפטן מהסגל הנוכחי:")
            captain_options = system.get_captain_recommendations()

            if not captain_options:
                print("❌ אין המלצות קפטן - תחילה הרץ ניתוח מלא")
            else:
                for i, option in enumerate(captain_options, 1):
                    player = option['player']
                    print(f"{i}. {player['name']} ({player['position']}) - {player['team_name']}")
                    print(f"   💰 מחיר: £{player['price']:.1f}M")
                    print(f"   🎯 ציון קפטן: {option['captain_score']:.3f}")
                    print(f"   📊 Momentum: {player['momentum_score']:.3f}")
                    print(f"   📋 המלצה: {option['recommendation']}")
                    print()

        elif choice == '3':
            print("\n🔄 המלצות חילופים:")
            transfer_data = system.get_transfer_recommendations()

            if "error" in transfer_data:
                print(f"❌ {transfer_data['error']}")
            elif "available_to_sell" in transfer_data:
                # שלב 1: בחירת שחקן למכירה
                sellable = transfer_data["available_to_sell"]
                print("📋 בחר שחקן למכירה (מומלצים למכירה מלמעלה):")

                for i, sell_option in enumerate(sellable[:10], 1):
                    player = sell_option['player']
                    analysis = sell_option['analysis']
                    print(f"{i}. {player['name']} ({player['position']}) - £{player['price']:.1f}M")
                    print(f"   🎯 Momentum: {player['momentum_score']:.3f}")
                    print(f"   📊 סיבות למכירה: {sell_option['reasoning']}")
                    print()

                try:
                    sell_choice = int(input("בחר מספר שחקן למכירה (0 לביטול): ")) - 1
                    if sell_choice >= 0 and sell_choice < len(sellable):
                        selected_player = sellable[sell_choice]
                        player_id = selected_player['player']['player_id']

                        budget_str = input("כסף זמין נוסף [2.0]: ").strip()
                        budget = float(budget_str) if budget_str else 2.0

                        # שלב 2: המלצות תחליפים
                        replacement_data = system.execute_transfer_analysis(player_id, budget)

                        if "error" in replacement_data:
                            print(f"❌ {replacement_data['error']}")
                        else:
                            selling = replacement_data['selling_player']
                            targets = replacement_data['targets']
                            real_budget = replacement_data['real_budget']

                            print(f"\n💰 מוכר: {selling['name']} (£{selling['price']:.1f}M)")
                            print(f"💳 תקציב אמיתי: £{real_budget:.1f}M")
                            print(f"\n🎯 תחליפים מומלצים:")

                            if not targets:
                                print("❌ אין תחליפים מתאימים בתקציב הזה")
                            else:
                                for i, target in enumerate(targets[:8], 1):
                                    player = target['player']
                                    comp = target['comparison']
                                    print(f"{i}. {player['name']} ({player['position']}) - £{player['price']:.1f}M")
                                    print(f"   🔄 שינוי מחיר: {target['price_difference']:+.1f}M")
                                    print(f"   💰 יישאר: £{target['budget_remaining']:.1f}M")
                                    print(f"   📈 שיפור momentum: {comp['momentum_improvement']:+.3f}")
                                    print(f"   🎯 המלצה: {comp['recommendation']}")
                                    print(f"   📊 Ownership: {player['selected_by_percent']:.1f}%")
                                    print()

                except ValueError:
                    print("❌ בחירה לא תקינה")
            else:
                print("❌ נתונים לא זמינים")

        elif choice == '4':
            player_name = input("שם שחקן: ").strip()
            if player_name:
                result = system.quick_player_search(player_name)
                if 'error' in result:
                    print(f"❌ {result['error']}")
                else:
                    player = result['player']
                    print(f"\n⚽ {player['name']} ({player['position']}) - {player['team_name']}")
                    print(f"💰 מחיר: £{player['price']:.1f}M")
                    print(f"🎯 Momentum: {player['momentum_score']:.3f}")
                    print(f"📊 Multi-Score: {result['multi_objective_score']:.3f}")
                    print(f"💎 Value Rating: {result['value_rating']:.3f}")
                    print(f"📈 Ownership: {player['selected_by_percent']:.1f}% ({result['ownership_category']})")
                    print(f"📋 המלצה: {result['recommendation']}")
                    print(f"✅ נבחר: {'כן' if result['selected'] else 'לא'}")

        elif choice == '5':
            status = system.get_system_status()
            print("\n🔍 סטטוס מערכת:")
            print(f"📊 נתונים נטענו: {'✅' if status['data_loaded'] else '❌'}")
            print(f"👥 מספר שחקנים: {status['players_count']}")
            print(f"🏆 סגל נבנה: {'✅' if status['squad_built'] else '❌'}")
            print(f"📋 שחקנים בסגל: {status['squad_size']}")

            validation = status['system_validation']
            print(f"\n🎯 פיצ'רים פעילים:")
            for feature in validation['core_features']:
                print(f"✅ {feature}")

        elif choice == '6':
            print("👋 יציאה...")
            break

        # ==================== תוספת חדשה - אפשרות 7 ====================
        elif choice == '7':
            while True:
                print("\n📂 ניהול הרכב קיים:")
                print("7.1. Wild Card - הרכב חדש לגמרי")
                print("7.2. יבוא הרכב מקובץ + המלצות חילופים")
                print("7.3. יבוא הרכב מקובץ + המלצות קפטן")
                print("7.4. ייצא הרכב נוכחי לקובץ")
                print("7.0. חזרה לתפריט הראשי")

                sub_choice = input("\nבחר (7.1-7.4 או 7.0): ").strip()

                if sub_choice == '7.1':
                    print("\n🃏 Wild Card - בניית הרכב חדש לגמרי:")
                    budget = input("תקציב [100]: ").strip()
                    budget = float(budget) if budget else 100.0

                    result = system.run_full_analysis(budget)

                    if result.endswith('.html'):
                        open_browser = input("לפתוח דוח? (y/n): ").strip().lower()
                        if open_browser != 'n':
                            webbrowser.open(f'file://{Path(result).absolute()}')
                    else:
                        print(result)

                elif sub_choice == '7.2':
                    print("\n📂 יבוא הרכב + המלצות חילופים:")
                    filepath = input("נתיב קובץ ההרכב: ").strip()

                    if filepath:
                        imported_squad = system.parse_squad_file(filepath)

                        if imported_squad:
                            print(f"\n✅ יובאו {len(imported_squad)} שחקנים")

                            # המלצות חילופים
                            transfer_data = system.get_transfers_from_imported_squad(imported_squad)

                            if "error" in transfer_data:
                                print(f"❌ {transfer_data['error']}")
                            elif "available_to_sell" in transfer_data:
                                sellable = transfer_data["available_to_sell"]
                                print("\n📋 שחקנים מומלצים למכירה:")

                                for i, sell_option in enumerate(sellable[:8], 1):
                                    player = sell_option['player']
                                    print(f"{i}. {player['name']} ({player['position']}) - £{player['price']:.1f}M")
                                    print(f"   🎯 Momentum: {player['momentum_score']:.3f}")
                                    print(f"   📊 סיבות למכירה: {sell_option['reasoning']}")
                                    print()

                                # אפשרות לניתוח תחליפים
                                analyze_choice = input("רוצה לנתח תחליפים לשחקן ספציפי? (y/n): ").strip().lower()
                                if analyze_choice == 'y':
                                    try:
                                        sell_choice = int(input("בחר מספר שחקן למכירה: ")) - 1
                                        if 0 <= sell_choice < len(sellable):
                                            player_id = sellable[sell_choice]['player']['player_id']
                                            budget_str = input("כסף זמין נוסף [2.0]: ").strip()
                                            budget = float(budget_str) if budget_str else 2.0

                                            replacement_data = system.execute_imported_transfer_analysis(
                                                imported_squad, player_id, budget
                                            )

                                            if "error" in replacement_data:
                                                print(f"❌ {replacement_data['error']}")
                                            else:
                                                selling = replacement_data['selling_player']
                                                targets = replacement_data['targets']
                                                real_budget = replacement_data['real_budget']

                                                print(f"\n💰 מוכר: {selling['name']} (£{selling['price']:.1f}M)")
                                                print(f"💳 תקציב אמיתי: £{real_budget:.1f}M")
                                                print(f"\n🎯 תחליפים מומלצים:")

                                                if not targets:
                                                    print("❌ אין תחליפים מתאימים")
                                                else:
                                                    for i, target in enumerate(targets[:5], 1):
                                                        player = target['player']
                                                        comp = target['comparison']
                                                        print(
                                                            f"{i}. {player['name']} ({player['position']}) - £{player['price']:.1f}M")
                                                        print(f"   🔄 שינוי מחיר: {target['price_difference']:+.1f}M")
                                                        print(
                                                            f"   📈 שיפור momentum: {comp['momentum_improvement']:+.3f}")
                                                        print(f"   🎯 המלצה: {comp['recommendation']}")
                                                        print()
                                    except ValueError:
                                        print("❌ בחירה לא תקינה")
                        else:
                            print("❌ לא ניתן לטעון שחקנים מהקובץ")

                elif sub_choice == '7.3':
                    print("\n📂 יבוא הרכב + המלצות קפטן:")
                    filepath = input("נתיב קובץ ההרכב: ").strip()

                    if filepath:
                        imported_squad = system.parse_squad_file(filepath)

                        if imported_squad:
                            print(f"\n✅ יובאו {len(imported_squad)} שחקנים")

                            # המלצות קפטן
                            captain_options = system.get_captain_from_imported_squad(imported_squad)

                            if not captain_options:
                                print("❌ אין המלצות קפטן מההרכב המיובא")
                            else:
                                print("\n👑 המלצות קפטן מההרכב המיובא:")
                                for i, option in enumerate(captain_options, 1):
                                    player = option['player']
                                    print(f"{i}. {player['name']} ({player['position']}) - {player['team_name']}")
                                    print(f"   💰 מחיר: £{player['price']:.1f}M")
                                    print(f"   🎯 ציון קפטן: {option['captain_score']:.3f}")
                                    print(f"   📊 Momentum: {player['momentum_score']:.3f}")
                                    print(f"   📋 המלצה: {option['recommendation']}")
                                    print()
                        else:
                            print("❌ לא ניתן לטעון שחקנים מהקובץ")

                elif sub_choice == '7.4':
                    print("\n📤 ייצוא הרכב נוכחי:")
                    custom_path = input("נתיב קובץ [Enter לברירת מחדל]: ").strip()

                    if custom_path:
                        result = system.export_current_squad(custom_path)
                    else:
                        result = system.export_current_squad()

                    print(result)

                elif sub_choice == '7.0':
                    break

                else:
                    print("❌ בחירה לא תקינה")

        else:
            print("❌ בחירה לא תקינה")


if __name__ == "__main__":
    from datetime import datetime

    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 התוכנית הופסקה")
    except Exception as e:
        print(f"❌ שגיאה: {e}")