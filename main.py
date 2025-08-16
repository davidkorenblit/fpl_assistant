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
    """Simple and efficient FPL system with essential features"""

    def __init__(self):
        self.data_manager = UnifiedDataManager()
        self.squad_builder = UnifiedSquadBuilder()
        self.analysis_engine = UnifiedAnalysisEngine()
        self.report_generator = UnifiedReportGenerator()
        self.current_squad = None
        self.all_players = None

    def load_data(self):
        """Load data - only once"""
        if self.all_players is None:
            print("📊 Loading data...")
            self.all_players = self.data_manager.fetch_and_process_data()
            if self.all_players:
                print(f"✅ Loaded {len(self.all_players)} players")
            else:
                print("❌ Error loading data")
        return bool(self.all_players)

    def run_full_analysis(self, budget: float = 100.0) -> str:
        """Full analysis + report"""
        try:
            if not self.load_data():
                return "❌ Data not loaded"

            print("🏗️ Building squad...")
            self.squad_builder.budget = budget
            squad_data = self.squad_builder.build_squad(self.all_players)

            if not squad_data.get('valid'):
                return "❌ No valid squad built"

            # Save current squad
            self.current_squad = []
            for player_dict in squad_data['starting_xi'] + squad_data['bench']:
                for player in self.all_players:
                    if player.player_id == player_dict['player_id']:
                        self.current_squad.append(player)
                        break

            print("🔍 Analyzing players...")
            top_analysis = self.analysis_engine.get_top_players(self.all_players, 20)

            # Captain from current squad
            captain_options = self.analysis_engine.get_captain_options(self.current_squad)

            # Transfer recommendations for report
            transfer_data = self.analysis_engine.get_transfer_targets(self.all_players, self.current_squad)
            transfer_targets = transfer_data.get('available_to_sell', [])[:6]

            print("📋 Generating report...")
            report_path = self.report_generator.generate_html_report(
                squad_data, top_analysis, captain_options, transfer_targets
            )

            print(f"✅ Report generated: {report_path}")
            return report_path

        except Exception as e:
            return f"❌ Error: {str(e)}"

    def get_captain_recommendations(self) -> List[Dict]:
        """Captain recommendations from current squad"""
        if not self.current_squad:
            print("⚠️ Run full analysis first to build squad")
            return []

        return self.analysis_engine.get_captain_options(self.current_squad)

    def get_transfer_recommendations(self) -> Dict:
        """Transfer recommendations - Step 1: Select player to sell"""
        if not self.current_squad:
            return {"error": "Run full analysis first to build squad"}

        if not self.load_data():
            return {"error": "Data not loaded"}

        # Get list of players to sell
        transfer_data = self.analysis_engine.get_transfer_targets(
            self.all_players, self.current_squad
        )

        return transfer_data

    def execute_transfer_analysis(self, player_to_sell_id: int, available_budget: float = 2.0) -> Dict:
        """Transfer recommendations - Step 2: Replacement analysis"""
        if not self.current_squad or not self.all_players:
            return {"error": "Data not available"}

        # Find player to sell
        player_to_sell = None
        for player in self.current_squad:
            if player.player_id == player_to_sell_id:
                player_to_sell = player
                break

        if not player_to_sell:
            return {"error": "Player not found in squad"}

        # Get replacement recommendations
        return self.analysis_engine.get_transfer_targets(
            self.all_players, self.current_squad, player_to_sell, available_budget
        )

    def quick_player_search(self, player_name: str) -> Dict:
        """Quick player search"""
        if not self.load_data():
            return {"error": "Data not loaded"}

        return self.analysis_engine.quick_analysis(player_name, self.all_players)

    def get_value_picks(self, max_price: float = 7.0) -> List[Dict]:
        """Value picks under certain price"""
        if not self.load_data():
            return []

        return self.analysis_engine.get_value_picks(self.all_players, max_price)

    def get_system_status(self) -> Dict:
        """System status"""
        return {
            'data_loaded': self.all_players is not None,
            'players_count': len(self.all_players) if self.all_players else 0,
            'squad_built': self.current_squad is not None,
            'squad_size': len(self.current_squad) if self.current_squad else 0,
            'system_validation': self.analysis_engine.validate_analysis_system()
        }

    # ==================== New additions - Existing squad management ====================

    def parse_squad_file(self, filepath: str) -> List[StandardPlayer]:
        """Parse squad file to StandardPlayer objects list"""
        try:
            if not os.path.exists(filepath):
                print(f"❌ File {filepath} does not exist")
                return []

            if not self.load_data():
                print("❌ Player data not loaded")
                return []

            squad_players = []

            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            print(f"📖 Reading {len(lines)} lines from file...")

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                try:
                    # Format: "POSITION: Player Name - Team - Price"
                    if ':' not in line or '-' not in line:
                        print(f"⚠️ Line {line_num} incorrect format: {line}")
                        continue

                    parts = line.split(':')
                    if len(parts) != 2:
                        print(f"⚠️ Line {line_num} - format issue: {line}")
                        continue

                    position = parts[0].strip()
                    player_info = parts[1].strip()

                    # Parse: "Player Name - Team - Price"
                    info_parts = player_info.split(' - ')
                    if len(info_parts) != 3:
                        print(f"⚠️ Line {line_num} - player details issue: {player_info}")
                        continue

                    player_name = info_parts[0].strip()
                    team_name = info_parts[1].strip()
                    try:
                        price = float(info_parts[2].strip())
                    except ValueError:
                        print(f"⚠️ Line {line_num} - invalid price: {info_parts[2]}")
                        continue

                    # Search player in database
                    found_player = self._find_player_in_database(player_name, team_name, position, price)
                    if found_player:
                        squad_players.append(found_player)
                        print(f"✅ Found: {found_player.name} ({found_player.position}) - {found_player.team_name}")
                    else:
                        print(f"❌ Not found: {player_name} ({position}) - {team_name}")

                except Exception as e:
                    print(f"❌ Error in line {line_num}: {e}")
                    continue

            print(f"✅ Loaded {len(squad_players)} players from {len(lines)} lines")
            return squad_players

        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return []

    def _find_player_in_database(self, player_name: str, team_name: str, position: str, price: float) -> StandardPlayer:
        """Find player in database by name, team, position and price"""
        if not self.all_players:
            return None

        # Exact search
        for player in self.all_players:
            if (player.name.lower() == player_name.lower() and
                    player.team_name.lower() == team_name.lower() and
                    player.position == position and
                    abs(player.price - price) < 0.1):
                return player

        # Partial search - name and position only
        for player in self.all_players:
            if (player_name.lower() in player.name.lower() and
                    player.position == position and
                    abs(player.price - price) < 0.5):
                return player

        # Broader search - name only
        for player in self.all_players:
            if player_name.lower() in player.name.lower():
                return player

        return None

    def export_current_squad(self, filepath: str = None) -> str:
        """Export current squad to text file"""
        try:
            if not self.current_squad:
                return "❌ No current squad to export - run full analysis first"

            if filepath is None:
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filepath = f"my_squad_{timestamp}.txt"

            # Organize players by position
            positions_order = ['GK', 'DEF', 'MID', 'FWD']
            organized_squad = {pos: [] for pos in positions_order}

            for player in self.current_squad:
                if player.position in organized_squad:
                    organized_squad[player.position].append(player)

            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                from datetime import datetime
                f.write("# FPL Squad Export\n")
                f.write(f"# Generated: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
                f.write("# Format: POSITION: Player Name - Team - Price\n\n")

                for position in positions_order:
                    players = organized_squad[position]
                    if players:
                        for player in players:
                            f.write(f"{position}: {player.name} - {player.team_name} - {player.price:.1f}\n")

            print(f"✅ Squad exported to file: {filepath}")
            return filepath

        except Exception as e:
            return f"❌ Export error: {e}"

    def get_captain_from_imported_squad(self, squad_players: List[StandardPlayer]) -> List[Dict]:
        """Captain recommendations from imported squad"""
        if not squad_players:
            return []

        return self.analysis_engine.get_captain_options(squad_players)

    def get_transfers_from_imported_squad(self, squad_players: List[StandardPlayer]) -> Dict:
        """Transfer recommendations from imported squad"""
        if not squad_players:
            return {"error": "No players in imported squad"}

        if not self.load_data():
            return {"error": "Data not loaded"}

        return self.analysis_engine.get_transfer_targets(self.all_players, squad_players)

    def execute_imported_transfer_analysis(self, squad_players: List[StandardPlayer],
                                           player_to_sell_id: int, available_budget: float = 2.0) -> Dict:
        """Replacement recommendations for imported squad"""
        if not squad_players or not self.all_players:
            return {"error": "Data not available"}

        # Find player to sell
        player_to_sell = None
        for player in squad_players:
            if player.player_id == player_to_sell_id:
                player_to_sell = player
                break

        if not player_to_sell:
            return {"error": "Player not found in imported squad"}

        return self.analysis_engine.get_transfer_targets(
            self.all_players, squad_players, player_to_sell, available_budget
        )


def main():
    print("🚀 FPL Assistant - Simple and Efficient System")
    print("=" * 50)

    system = SimpleFPLSystem()

    while True:
        print("\n📋 Menu:")
        print("1. Full Analysis + Squad Building")
        print("2. Captain Recommendations")
        print("3. Transfer Recommendations")
        print("4. Player Search")
        print("5. System Status")
        print("6. Exit")
        print("7. Squad Management")  # New addition

        choice = input("\nSelect (1-7): ").strip()

        if choice == '1':
            budget = input("Budget [100]: ").strip()
            budget = float(budget) if budget else 100.0

            result = system.run_full_analysis(budget)

            if result.endswith('.html'):
                open_browser = input("Open report? (y/n): ").strip().lower()
                if open_browser != 'n':
                    webbrowser.open(f'file://{Path(result).absolute()}')
            else:
                print(result)

        elif choice == '2':
            print("\n👑 Captain recommendations from current squad:")
            captain_options = system.get_captain_recommendations()

            if not captain_options:
                print("❌ No captain recommendations - run full analysis first")
            else:
                for i, option in enumerate(captain_options, 1):
                    player = option['player']
                    print(f"{i}. {player['name']} ({player['position']}) - {player['team_name']}")
                    print(f"   💰 Price: £{player['price']:.1f}M")
                    print(f"   🎯 Captain Score: {option['captain_score']:.3f}")
                    print(f"   📊 Momentum: {player['momentum_score']:.3f}")
                    print(f"   📋 Recommendation: {option['recommendation']}")
                    print()

        elif choice == '3':
            print("\n🔄 Transfer recommendations:")
            transfer_data = system.get_transfer_recommendations()

            if "error" in transfer_data:
                print(f"❌ {transfer_data['error']}")
            elif "available_to_sell" in transfer_data:
                # Step 1: Select player to sell
                sellable = transfer_data["available_to_sell"]
                print("📋 Select player to sell (recommended to sell from top):")

                for i, sell_option in enumerate(sellable[:10], 1):
                    player = sell_option['player']
                    analysis = sell_option['analysis']
                    print(f"{i}. {player['name']} ({player['position']}) - £{player['price']:.1f}M")
                    print(f"   🎯 Momentum: {player['momentum_score']:.3f}")
                    print(f"   📊 Sell reasons: {sell_option['reasoning']}")
                    print()

                try:
                    sell_choice = int(input("Select player number to sell (0 to cancel): ")) - 1
                    if sell_choice >= 0 and sell_choice < len(sellable):
                        selected_player = sellable[sell_choice]
                        player_id = selected_player['player']['player_id']

                        budget_str = input("Additional budget [2.0]: ").strip()
                        budget = float(budget_str) if budget_str else 2.0

                        # Step 2: Replacement recommendations
                        replacement_data = system.execute_transfer_analysis(player_id, budget)

                        if "error" in replacement_data:
                            print(f"❌ {replacement_data['error']}")
                        else:
                            selling = replacement_data['selling_player']
                            targets = replacement_data['targets']
                            real_budget = replacement_data['real_budget']

                            print(f"\n💰 Selling: {selling['name']} (£{selling['price']:.1f}M)")
                            print(f"💳 Real budget: £{real_budget:.1f}M")
                            print(f"\n🎯 Recommended replacements:")

                            if not targets:
                                print("❌ No suitable replacements in this budget")
                            else:
                                for i, target in enumerate(targets[:8], 1):
                                    player = target['player']
                                    comp = target['comparison']
                                    print(f"{i}. {player['name']} ({player['position']}) - £{player['price']:.1f}M")
                                    print(f"   🔄 Price change: {target['price_difference']:+.1f}M")
                                    print(f"   💰 Remaining: £{target['budget_remaining']:.1f}M")
                                    print(f"   📈 Momentum improvement: {comp['momentum_improvement']:+.3f}")
                                    print(f"   🎯 Recommendation: {comp['recommendation']}")
                                    print(f"   📊 Ownership: {player['selected_by_percent']:.1f}%")
                                    print()

                except ValueError:
                    print("❌ Invalid selection")
            else:
                print("❌ Data not available")

        elif choice == '4':
            player_name = input("Player name: ").strip()
            if player_name:
                result = system.quick_player_search(player_name)
                if 'error' in result:
                    print(f"❌ {result['error']}")
                else:
                    player = result['player']
                    print(f"\n⚽ {player['name']} ({player['position']}) - {player['team_name']}")
                    print(f"💰 Price: £{player['price']:.1f}M")
                    print(f"🎯 Momentum: {player['momentum_score']:.3f}")
                    print(f"📊 Multi-Score: {result['multi_objective_score']:.3f}")
                    print(f"💎 Value Rating: {result['value_rating']:.3f}")
                    print(f"📈 Ownership: {player['selected_by_percent']:.1f}% ({result['ownership_category']})")
                    print(f"📋 Recommendation: {result['recommendation']}")
                    print(f"✅ Selected: {'Yes' if result['selected'] else 'No'}")

        elif choice == '5':
            status = system.get_system_status()
            print("\n🔍 System Status:")
            print(f"📊 Data loaded: {'✅' if status['data_loaded'] else '❌'}")
            print(f"👥 Number of players: {status['players_count']}")
            print(f"🏆 Squad built: {'✅' if status['squad_built'] else '❌'}")
            print(f"📋 Players in squad: {status['squad_size']}")

            validation = status['system_validation']
            print(f"\n🎯 Active features:")
            for feature in validation['core_features']:
                print(f"✅ {feature}")

        elif choice == '6':
            print("👋 Exiting...")
            break

        # ==================== New addition - Option 7 ====================
        elif choice == '7':
            while True:
                print("\n📂 Squad Management:")
                print("7.1. Wild Card - Build completely new squad")
                print("7.2. Import squad from file + Transfer recommendations")
                print("7.3. Import squad from file + Captain recommendations")
                print("7.4. Export current squad to file")
                print("7.0. Back to main menu")

                sub_choice = input("\nSelect (7.1-7.4 or 7.0): ").strip()

                if sub_choice == '7.1':
                    print("\n🃏 Wild Card - Building completely new squad:")
                    budget = input("Budget [100]: ").strip()
                    budget = float(budget) if budget else 100.0

                    result = system.run_full_analysis(budget)

                    if result.endswith('.html'):
                        open_browser = input("Open report? (y/n): ").strip().lower()
                        if open_browser != 'n':
                            webbrowser.open(f'file://{Path(result).absolute()}')
                    else:
                        print(result)

                elif sub_choice == '7.2':
                    print("\n📂 Import squad + Transfer recommendations:")
                    filepath = input("Squad file path: ").strip()

                    if filepath:
                        imported_squad = system.parse_squad_file(filepath)

                        if imported_squad:
                            print(f"\n✅ Imported {len(imported_squad)} players")

                            # Transfer recommendations
                            transfer_data = system.get_transfers_from_imported_squad(imported_squad)

                            if "error" in transfer_data:
                                print(f"❌ {transfer_data['error']}")
                            elif "available_to_sell" in transfer_data:
                                sellable = transfer_data["available_to_sell"]
                                print("\n📋 Players recommended to sell:")

                                for i, sell_option in enumerate(sellable[:8], 1):
                                    player = sell_option['player']
                                    print(f"{i}. {player['name']} ({player['position']}) - £{player['price']:.1f}M")
                                    print(f"   🎯 Momentum: {player['momentum_score']:.3f}")
                                    print(f"   📊 Sell reasons: {sell_option['reasoning']}")
                                    print()

                                # Option to analyze replacements
                                analyze_choice = input("Want to analyze replacements for specific player? (y/n): ").strip().lower()
                                if analyze_choice == 'y':
                                    try:
                                        sell_choice = int(input("Select player number to sell: ")) - 1
                                        if 0 <= sell_choice < len(sellable):
                                            player_id = sellable[sell_choice]['player']['player_id']
                                            budget_str = input("Additional budget [2.0]: ").strip()
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

                                                print(f"\n💰 Selling: {selling['name']} (£{selling['price']:.1f}M)")
                                                print(f"💳 Real budget: £{real_budget:.1f}M")
                                                print(f"\n🎯 Recommended replacements:")

                                                if not targets:
                                                    print("❌ No suitable replacements")
                                                else:
                                                    for i, target in enumerate(targets[:5], 1):
                                                        player = target['player']
                                                        comp = target['comparison']
                                                        print(
                                                            f"{i}. {player['name']} ({player['position']}) - £{player['price']:.1f}M")
                                                        print(f"   🔄 Price change: {target['price_difference']:+.1f}M")
                                                        print(
                                                            f"   📈 Momentum improvement: {comp['momentum_improvement']:+.3f}")
                                                        print(f"   🎯 Recommendation: {comp['recommendation']}")
                                                        print()
                                    except ValueError:
                                        print("❌ Invalid selection")
                        else:
                            print("❌ Could not load players from file")

                elif sub_choice == '7.3':
                    print("\n📂 Import squad + Captain recommendations:")
                    filepath = input("Squad file path: ").strip()

                    if filepath:
                        imported_squad = system.parse_squad_file(filepath)

                        if imported_squad:
                            print(f"\n✅ Imported {len(imported_squad)} players")

                            # Captain recommendations
                            captain_options = system.get_captain_from_imported_squad(imported_squad)

                            if not captain_options:
                                print("❌ No captain recommendations from imported squad")
                            else:
                                print("\n👑 Captain recommendations from imported squad:")
                                for i, option in enumerate(captain_options, 1):
                                    player = option['player']
                                    print(f"{i}. {player['name']} ({player['position']}) - {player['team_name']}")
                                    print(f"   💰 Price: £{player['price']:.1f}M")
                                    print(f"   🎯 Captain Score: {option['captain_score']:.3f}")
                                    print(f"   📊 Momentum: {player['momentum_score']:.3f}")
                                    print(f"   📋 Recommendation: {option['recommendation']}")
                                    print()
                        else:
                            print("❌ Could not load players from file")

                elif sub_choice == '7.4':
                    print("\n📤 Export current squad:")
                    custom_path = input("File path [Enter for default]: ").strip()

                    if custom_path:
                        result = system.export_current_squad(custom_path)
                    else:
                        result = system.export_current_squad()

                    print(result)

                elif sub_choice == '7.0':
                    break

                else:
                    print("❌ Invalid selection")

        else:
            print("❌ Invalid selection")


if __name__ == "__main__":
    from datetime import datetime

    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Program interrupted")
    except Exception as e:
        print(f"❌ Error: {e}")