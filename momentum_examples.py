"""
דוגמאות שימוש למערכת המומנטום FPL Assistant
קובץ זה מכיל דוגמאות מעשיות לשימוש במערכת
"""

from MomentumIntegration import MomentumIntegration
from MomentumAnalyzer import MomentumAnalyzer
from MomentumVisualizer import MomentumVisualizer


def example_1_quick_player_analysis():
    """דוגמה 1: ניתוח מהיר של שחקן"""
    print("🎯 EXAMPLE 1: Quick Player Analysis")
    print("=" * 50)

    # Initialize system
    system = MomentumIntegration()

    if not system.system_ready:
        print("❌ System not ready")
        return

    # Analyze specific players
    players_to_analyze = ['Haaland', 'Salah', 'Son', 'Van Dijk', 'Alisson']

    print("Analyzing top players...")
    for player_name in players_to_analyze:
        analysis = system.analyze_player(player_name)
        if analysis:
            momentum = analysis['momentum_score']
            selected = analysis.get('randomizer_selected', False)
            recommendation = analysis.get('recommendation', {}).get('status', 'Unknown')

            status_icon = "✅" if selected else "❌"
            momentum_icon = "🔥" if momentum >= 0.8 else "📈" if momentum >= 0.6 else "📉"

            print(f"{status_icon} {player_name:<12} | {momentum:.3f} {momentum_icon} | {recommendation}")
        else:
            print(f"❌ {player_name:<12} | Not found")


def example_2_team_comparison():
    """דוגמה 2: השוואת קבוצות מובילות"""
    print("\n⚽ EXAMPLE 2: Top Teams Comparison")
    print("=" * 50)

    system = MomentumIntegration()

    if not system.system_ready:
        print("❌ System not ready")
        return

    # Compare top teams
    teams = ['Manchester City', 'Arsenal', 'Liverpool', 'Chelsea']
    comparison_results = []

    for team in teams:
        analysis = system.analyze_team_detailed(team)
        if analysis and 'error' not in analysis:
            summary = analysis['summary']
            comparison_results.append({
                'team': team,
                'avg_momentum': summary.get('average_momentum', 0),
                'selected_count': summary.get('selected_players_count', 0),
                'defensive_score': summary.get('team_defensive_score', 0)
            })

    # Sort by average momentum
    comparison_results.sort(key=lambda x: x['avg_momentum'], reverse=True)

    print("Team Rankings by Momentum:")
    for i, team_data in enumerate(comparison_results, 1):
        print(f"{i}. {team_data['team']:<18} | Momentum: {team_data['avg_momentum']:.3f} | "
              f"Selected: {team_data['selected_count']} | Defense: {team_data['defensive_score']:.3f}")


def example_3_position_leaders():
    """דוגמה 3: מובילי עמדות"""
    print("\n🏆 EXAMPLE 3: Position Leaders")
    print("=" * 50)

    analyzer = MomentumAnalyzer()

    if analyzer.all_players_data is None:
        print("❌ No data available")
        return

    print("Top 3 players by position based on momentum:")

    for position in ['GK', 'DEF', 'MID', 'FWD']:
        leaders = analyzer.get_position_momentum_leaders(position, 3)

        print(f"\n{position}:")
        for i, player in enumerate(leaders, 1):
            momentum = player['momentum_score']
            selected = player.get('randomizer_selected', False)
            price = player['current_price']

            icon = "⭐" if selected else "  "
            print(f"{icon}{i}. {player['player_name']:<15} | {momentum:.3f} | £{price:.1f}M")


def example_4_value_picks():
    """דוגמה 4: זיהוי value picks"""
    print("\n💰 EXAMPLE 4: Value Picks Analysis")
    print("=" * 50)

    system = MomentumIntegration()

    if not system.system_ready:
        print("❌ System not ready")
        return

    # Budget categories
    budget_categories = [
        {"name": "Budget Gems", "max_price": 6.0, "min_momentum": 0.7},
        {"name": "Mid-Range Value", "max_price": 8.0, "min_momentum": 0.75},
        {"name": "Premium Targets", "max_price": 15.0, "min_momentum": 0.8}
    ]

    for category in budget_categories:
        print(f"\n{category['name']} (≤£{category['max_price']:.1f}M, momentum ≥{category['min_momentum']}):")

        recommendations = system.get_quick_recommendations(
            max_price=category['max_price'],
            min_momentum=category['min_momentum']
        )

        if recommendations:
            for i, player in enumerate(recommendations[:5], 1):
                print(f"  {i}. {player['player_name']:<15} ({player['position']}) | "
                      f"£{player['current_price']:>4.1f}M | {player['momentum_score']:.3f}")
        else:
            print("  No players found in this category")


def example_5_transfer_targets():
    """דוגמה 5: זיהוי מטרות transfer"""
    print("\n🔄 EXAMPLE 5: Transfer Targets by Position")
    print("=" * 50)

    system = MomentumIntegration()

    if not system.system_ready:
        print("❌ System not ready")
        return

    # Get transfer targets for each position
    for position in ['GK', 'DEF', 'MID', 'FWD']:
        print(f"\n{position} Transfer Targets:")

        # Get recommendations for this position
        recommendations = system.get_quick_recommendations(
            position=position,
            min_momentum=0.65
        )

        if recommendations:
            # Show top 3 with different criteria
            for i, player in enumerate(recommendations[:3], 1):
                momentum = player['momentum_score']
                price = player['current_price']
                points = player['total_points']

                # Calculate simple value score
                value_score = momentum * 0.6 + (points / 200.0) * 0.4

                print(f"  {i}. {player['player_name']:<15} | £{price:>4.1f}M | "
                      f"Mom: {momentum:.3f} | Pts: {points:>3.0f} | Value: {value_score:.3f}")
        else:
            print("  No suitable targets found")


def example_6_captain_candidates():
    """דוגמה 6: מועמדים לקפטן"""
    print("\n👑 EXAMPLE 6: Captain Candidates Analysis")
    print("=" * 50)

    system = MomentumIntegration()

    if not system.system_ready:
        print("❌ System not ready")
        return

    # Get high momentum attacking players
    attacking_positions = ['MID', 'FWD']
    captain_candidates = []

    for position in attacking_positions:
        recommendations = system.get_quick_recommendations(
            position=position,
            min_momentum=0.75
        )
        captain_candidates.extend(recommendations[:3])  # Top 3 from each position

    # Sort by momentum score
    captain_candidates.sort(key=lambda x: x['momentum_score'], reverse=True)

    print("Top Captain Candidates (high momentum attacking players):")

    for i, player in enumerate(captain_candidates[:8], 1):
        momentum = player['momentum_score']
        price = player['current_price']
        form = player.get('form', 0)

        # Captain appeal score
        captain_score = momentum * 0.5 + float(form) / 10.0 * 0.3 + min(1.0, player['total_points'] / 150.0) * 0.2

        ownership = player.get('selected_by_percent', 'N/A')
        differential = " (DIFF)" if isinstance(ownership, (int, float)) and ownership < 15 else ""

        print(f"  {i}. {player['player_name']:<15} ({player['position']}) | "
              f"Mom: {momentum:.3f} | Form: {form} | Score: {captain_score:.3f}{differential}")


def example_7_team_builder():
    """דוגמה 7: בניית קבוצה מבוססת מומנטום"""
    print("\n🏗️ EXAMPLE 7: Momentum-Based Team Builder")
    print("=" * 50)

    system = MomentumIntegration()

    if not system.system_ready:
        print("❌ System not ready")
        return

    # Team constraints
    formation = {'GK': 1, 'DEF': 4, 'MID': 4, 'FWD': 2}  # 4-4-2 starting formation
    budget = 100.0

    selected_team = []
    total_cost = 0

    print(
        f"Building team with £{budget:.1f}M budget in {'-'.join(str(formation[pos]) for pos in ['DEF', 'MID', 'FWD'])} formation:")

    # Select players for each position
    for position, needed in formation.items():
        print(f"\nSelecting {needed} {position}(s):")

        # Get recommendations for this position
        available_budget = budget - total_cost
        max_price_per_player = available_budget / (sum(formation.values()) - len(selected_team))

        recommendations = system.get_quick_recommendations(
            position=position,
            max_price=max_price_per_player * 1.5,  # Allow some flexibility
            min_momentum=0.6
        )

        position_selections = []
        for player in recommendations:
            if len(position_selections) >= needed:
                break
            if total_cost + player['current_price'] <= budget:
                position_selections.append(player)
                total_cost += player['current_price']

                print(f"  ✅ {player['player_name']:<15} | £{player['current_price']:>4.1f}M | "
                      f"Mom: {player['momentum_score']:.3f}")

        selected_team.extend(position_selections)

        if len(position_selections) < needed:
            print(f"  ⚠️ Only found {len(position_selections)}/{needed} suitable players for {position}")

    print(f"\n📊 TEAM SUMMARY:")
    print(f"Total players: {len(selected_team)}/11")
    print(f"Total cost: £{total_cost:.1f}M")
    print(f"Remaining budget: £{budget - total_cost:.1f}M")

    if len(selected_team) == 11:
        avg_momentum = sum(p['momentum_score'] for p in selected_team) / len(selected_team)
        print(f"Average momentum: {avg_momentum:.3f}")

        # Export team sheet
        player_names = [p['player_name'] for p in selected_team]
        system.export_team_sheet(player_names, 'momentum_team.txt')


def example_8_gameweek_strategy():
    """דוגמה 8: אסטרטגיית gameweek"""
    print("\n📅 EXAMPLE 8: Gameweek Strategy Analysis")
    print("=" * 50)

    system = MomentumIntegration()

    if not system.system_ready:
        print("❌ System not ready")
        return

    # Different gameweek strategies
    strategies = [
        {
            "name": "Safe Captain Strategy",
            "criteria": {"min_momentum": 0.8, "max_price": None},
            "description": "High momentum players regardless of price"
        },
        {
            "name": "Differential Strategy",
            "criteria": {"min_momentum": 0.7, "max_price": 8.0},
            "description": "Lower-owned, good momentum, affordable players"
        },
        {
            "name": "Premium Strategy",
            "criteria": {"min_momentum": 0.75, "max_price": None},
            "description": "Focus on premium players with good momentum"
        }
    ]

    for strategy in strategies:
        print(f"\n🎯 {strategy['name']}:")
        print(f"   {strategy['description']}")

        recommendations = system.get_quick_recommendations(**strategy['criteria'])

        if recommendations:
            # Group by position
            by_position = {}
            for player in recommendations:
                pos = player['position']
                if pos not in by_position:
                    by_position[pos] = []
                by_position[pos].append(player)

            for position in ['GK', 'DEF', 'MID', 'FWD']:
                if position in by_position:
                    top_player = by_position[position][0]  # Best in position
                    print(f"   {position}: {top_player['player_name']} "
                          f"(£{top_player['current_price']:.1f}M, {top_player['momentum_score']:.3f})")


def example_9_visualization_showcase():
    """דוגמה 9: הדגמת ויזואליזציות"""
    print("\n🎨 EXAMPLE 9: Visualization Showcase")
    print("=" * 50)

    try:
        visualizer = MomentumVisualizer()

        if visualizer.analyzer.all_players_data is None:
            print("❌ No data available for visualization")
            return

        print("Generating sample visualizations...")

        # 1. Momentum distribution
        print("1. Creating momentum distribution plot...")
        visualizer.plot_momentum_distribution_by_position()

        # 2. Top players
        print("2. Creating top players plot...")
        visualizer.plot_top_momentum_players(limit=10)

        # 3. Price vs momentum
        print("3. Creating price vs momentum scatter plot...")
        visualizer.plot_momentum_vs_price_scatter()

        print("✅ Visualization showcase complete!")

    except ImportError:
        print("❌ Visualization libraries not available (matplotlib, seaborn)")
    except Exception as e:
        print(f"❌ Error in visualization: {e}")


def example_10_full_workflow():
    """דוגמה 10: workflow מלא מתחילה לסוף"""
    print("\n🔄 EXAMPLE 10: Complete FPL Momentum Workflow")
    print("=" * 50)

    system = MomentumIntegration()

    if not system.system_ready:
        print("❌ System not ready")
        return

    print("Running complete FPL momentum analysis workflow...")

    # Step 1: League overview
    print("\n📊 Step 1: League Overview")
    overview = system.get_league_momentum_overview()
    if 'error' not in overview:
        stats = overview['league_stats']
        print(f"  • Total players analyzed: {stats['total_players']}")
        print(f"  • Players selected by randomizer: {stats['selected_players']}")
        print(f"  • Selection rate: {stats['selection_rate']:.1%}")

    # Step 2: Position analysis
    print("\n🎯 Step 2: Position Leaders")
    analyzer = MomentumAnalyzer()
    for position in ['GK', 'DEF', 'MID', 'FWD']:
        leaders = analyzer.get_position_momentum_leaders(position, 1)
        if leaders:
            top_player = leaders[0]
            print(f"  • {position}: {top_player['player_name']} ({top_player['momentum_score']:.3f})")

    # Step 3: Team recommendations
    print("\n⚽ Step 3: Top Team Recommendations")
    teams = ['Manchester City', 'Arsenal', 'Liverpool']
    for team in teams:
        analysis = system.analyze_team_detailed(team)
        if analysis and 'error' not in analysis:
            summary = analysis['summary']
            print(f"  • {team}: {summary.get('average_momentum', 0):.3f} avg momentum, "
                  f"{summary.get('selected_players_count', 0)} selected")

    # Step 4: Transfer suggestions
    print("\n🔄 Step 4: Top Transfer Targets")
    all_recommendations = system.get_quick_recommendations(min_momentum=0.8)
    if all_recommendations:
        for i, player in enumerate(all_recommendations[:5], 1):
            print(f"  {i}. {player['player_name']} ({player['position']}) - "
                  f"£{player['current_price']:.1f}M | {player['momentum_score']:.3f}")

    # Step 5: Save full analysis
    print("\n💾 Step 5: Saving Complete Analysis")
    try:
        results = system.run_full_analysis(save_results=True)
        print("  ✅ Full analysis saved to momentum_output/")
    except Exception as e:
        print(f"  ❌ Error saving analysis: {e}")

    print("\n🎉 Complete workflow finished!")


def run_all_examples():
    """הרץ את כל הדוגמאות"""
    print("🚀 RUNNING ALL FPL MOMENTUM EXAMPLES")
    print("=" * 60)

    examples = [
        example_1_quick_player_analysis,
        example_2_team_comparison,
        example_3_position_leaders,
        example_4_value_picks,
        example_5_transfer_targets,
        example_6_captain_candidates,
        example_7_team_builder,
        example_8_gameweek_strategy,
        example_9_visualization_showcase,
        example_10_full_workflow
    ]

    for i, example_func in enumerate(examples, 1):
        try:
            print(f"\n{'=' * 20} EXAMPLE {i} {'=' * 20}")
            example_func()
            print(f"✅ Example {i} completed successfully")
        except Exception as e:
            print(f"❌ Example {i} failed: {e}")

        if i < len(examples):
            input("\nPress Enter to continue to next example...")

    print(f"\n🎉 All {len(examples)} examples completed!")


def interactive_example_menu():
    """תפריט אינטראקטיבי לדוגמאות"""
    examples_map = {
        '1': ("Quick Player Analysis", example_1_quick_player_analysis),
        '2': ("Team Comparison", example_2_team_comparison),
        '3': ("Position Leaders", example_3_position_leaders),
        '4': ("Value Picks Analysis", example_4_value_picks),
        '5': ("Transfer Targets", example_5_transfer_targets),
        '6': ("Captain Candidates", example_6_captain_candidates),
        '7': ("Team Builder", example_7_team_builder),
        '8': ("Gameweek Strategy", example_8_gameweek_strategy),
        '9': ("Visualization Showcase", example_9_visualization_showcase),
        '10': ("Full Workflow", example_10_full_workflow),
        'all': ("Run All Examples", run_all_examples)
    }

    print("🎯 FPL MOMENTUM EXAMPLES MENU")
    print("=" * 40)

    for key, (name, _) in examples_map.items():
        print(f"{key:>3}. {name}")
    print("  0. Exit")

    while True:
        choice = input(f"\n🔢 Choose example (0-10, 'all'): ").strip()

        if choice == '0':
            print("👋 Goodbye!")
            break
        elif choice in examples_map:
            name, func = examples_map[choice]
            print(f"\n🚀 Running: {name}")
            try:
                func()
                print(f"✅ {name} completed!")
            except Exception as e:
                print(f"❌ Error in {name}: {e}")
        else:
            print("❌ Invalid choice. Please try again.")


if __name__ == "__main__":
    print("🎯 FPL MOMENTUM SYSTEM - EXAMPLES")
    print("=" * 50)
    print("This file contains practical examples of using the FPL Momentum System")
    print()

    # Ask user what they want to do
    print("Choose what to run:")
    print("1. Interactive menu")
    print("2. Run all examples")
    print("3. Quick demo (examples 1, 3, 4)")

    choice = input("\nYour choice (1-3): ").strip()

    if choice == '1':
        interactive_example_menu()
    elif choice == '2':
        run_all_examples()
    elif choice == '3':
        print("🚀 Running quick demo...")
        example_1_quick_player_analysis()
        example_3_position_leaders()
        example_4_value_picks()
        print("\n🎉 Quick demo completed!")
    else:
        print("Running interactive menu by default...")
        interactive_example_menu()