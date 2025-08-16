import os
from datetime import datetime
from typing import Dict, List
from pathlib import Path


class UnifiedReportGenerator:
    def __init__(self):
        self.output_dir = Path("fpl_reports")
        self.output_dir.mkdir(exist_ok=True)

    def generate_html_report(self, squad_data: Dict, analysis_data: List[Dict],
                             captain_options: List[Dict], transfer_targets: List[Dict]) -> str:

        html = f"""<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
    <meta charset="UTF-8">
    <title>דוח FPL Assistant</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }}
        .header {{ background: linear-gradient(45deg, #38003c, #00ff87); color: white; padding: 20px; text-align: center; border-radius: 10px; margin-bottom: 20px; }}
        .section {{ margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; }}
        .player-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin: 15px 0; }}
        .player-card {{ background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #38003c; }}
        .player-name {{ font-weight: bold; color: #38003c; margin-bottom: 5px; }}
        .player-stats {{ font-size: 0.9rem; color: #666; }}
        .formation {{ background: #00ff87; color: #38003c; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; margin-bottom: 15px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>דוח FPL Assistant</h1>
            <p>{datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>

        {self._generate_squad_section(squad_data)}
        {self._generate_captain_section(captain_options)}
        {self._generate_transfers_section(transfer_targets)}
        {self._generate_top_players_section(analysis_data)}
    </div>
</body>
</html>"""

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"fpl_report_{timestamp}.html"
        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)

        return str(filepath)

    def _generate_squad_section(self, squad_data: Dict) -> str:
        if not squad_data or not squad_data.get('starting_xi'):
            return '<div class="section"><h2>❌ לא נבנה סגל</h2></div>'

        starting_xi = squad_data['starting_xi']
        bench = squad_data.get('bench', [])
        captain = squad_data.get('captain', {})

        html = f"""
        <div class="section">
            <h2>🏆 ההרכב הפעיל</h2>
            <div class="formation">מערך: {squad_data.get('formation', '4-4-2')} | עלות: £{squad_data.get('total_cost', 0):.1f}M</div>
            <div class="player-grid">
        """

        for player in starting_xi:
            captain_icon = "👑" if player.get('player_id') == captain.get('player_id') else ""
            html += f"""
            <div class="player-card">
                <div class="player-name">{captain_icon} {player.get('name', 'Unknown')}</div>
                <div class="player-stats">
                    {player.get('position', '')} • {player.get('team_name', '')} • £{player.get('price', 0):.1f}M<br>
                    נקודות: {player.get('total_points', 0)} • מומנטום: {player.get('momentum_score', 0):.3f}
                </div>
            </div>
            """

        html += "</div></div>"

        if bench:
            html += '<div class="section"><h2>🪑 הספסל</h2><div class="player-grid">'
            for player in bench:
                html += f"""
                <div class="player-card">
                    <div class="player-name">{player.get('name', 'Unknown')}</div>
                    <div class="player-stats">
                        {player.get('position', '')} • {player.get('team_name', '')} • £{player.get('price', 0):.1f}M<br>
                        מומנטום: {player.get('momentum_score', 0):.3f}
                    </div>
                </div>
                """
            html += "</div></div>"

        return html

    def _generate_captain_section(self, captain_options: List[Dict]) -> str:
        if not captain_options:
            return '<div class="section"><h2>👑 אין אפשרויות קפטן</h2></div>'

        html = '<div class="section"><h2>👑 אפשרויות קפטן</h2><div class="player-grid">'

        for i, option in enumerate(captain_options[:3]):
            player = option.get('player', {})
            icon = "🏆" if i == 0 else f"{i + 1}."
            html += f"""
            <div class="player-card">
                <div class="player-name">{icon} {player.get('name', 'Unknown')}</div>
                <div class="player-stats">
                    {player.get('position', '')} • {player.get('team_name', '')}<br>
                    ציון קפטן: {option.get('captain_score', 0):.3f} • {option.get('recommendation', '')}
                </div>
            </div>
            """

        html += "</div></div>"
        return html

    def _generate_transfers_section(self, transfer_targets: List[Dict]) -> str:
        if not transfer_targets:
            return '<div class="section"><h2>🔄 אין החלפות מומלצות</h2></div>'

        html = '<div class="section"><h2>🔄 המלצות החלפות</h2><div class="player-grid">'

        for target in transfer_targets[:6]:
            player = target.get('player', {})
            html += f"""
            <div class="player-card">
                <div class="player-name">{player.get('name', 'Unknown')}</div>
                <div class="player-stats">
                    {player.get('position', '')} • {player.get('team_name', '')} • £{player.get('price', 0):.1f}M<br>
                    מומנטום: {player.get('momentum_score', 0):.3f} • {target.get('recommendation', '')}
                </div>
            </div>
            """

        html += "</div></div>"
        return html

    def _generate_top_players_section(self, analysis_data: List[Dict]) -> str:
        html = '<div class="section"><h2>⭐ שחקנים מובילים</h2><div class="player-grid">'

        for analysis in analysis_data[:8]:
            player = analysis.get('player', {})
            selected_icon = "✅" if analysis.get('selected') else ""
            html += f"""
            <div class="player-card">
                <div class="player-name">{selected_icon} {player.get('name', 'Unknown')}</div>
                <div class="player-stats">
                    {player.get('position', '')} • {player.get('team_name', '')} • £{player.get('price', 0):.1f}M<br>
                    מומנטום: {player.get('momentum_score', 0):.3f} • {analysis.get('momentum_level', '')}
                </div>
            </div>
            """

        html += "</div></div>"
        return html