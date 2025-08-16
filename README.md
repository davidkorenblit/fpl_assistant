# FPL Assistant

A comprehensive Fantasy Premier League (FPL) analysis and team management system built in Python.

## Features

### Core Functionality
- **Squad Builder**: Automatically builds optimal FPL squads within budget constraints
- **Player Analysis**: Advanced momentum-based player scoring and recommendations
- **Captain Recommendations**: Smart captain selection from your current squad
- **Transfer Analysis**: Detailed transfer recommendations with budget planning
- **HTML Reports**: Beautiful, detailed reports with all analysis data

### Squad Management
- **Import Squad**: Load your existing squad from text files
- **Export Squad**: Save your current squad to text files
- **Wild Card Mode**: Build completely new squads
- **Transfer Planning**: Get specific transfer recommendations from imported squads

## Installation

### Requirements
- Python 3.7+
- Required packages: `requests`, `pandas`, `numpy`

### Setup
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the system:
   ```bash
   python unified_main_system.py
   ```

## Usage

### Main Menu Options

1. **Full Analysis + Squad Building**: Creates optimal squad and generates HTML report
2. **Captain Recommendations**: Get captain suggestions from current squad
3. **Transfer Recommendations**: Interactive transfer planning tool
4. **Player Search**: Quick analysis of any player
5. **System Status**: View system information and validation
6. **Exit**: Close the application
7. **Squad Management**: Import/export squads and specialized analysis

### Squad File Format

When importing/exporting squads, use this format:
```
GK: Alisson - Liverpool - 5.5
DEF: Van Dijk - Liverpool - 6.0
DEF: Robertson - Liverpool - 6.0
MID: Salah - Liverpool - 13.0
MID: De Bruyne - Man City - 9.5
MID: Son - Tottenham - 10.0
MID: Rashford - Man Utd - 6.5
FWD: Haaland - Man City - 15.0
FWD: Kane - Tottenham - 11.5
FWD: Watkins - Aston Villa - 9.0
DEF: White - Arsenal - 4.5
DEF: Burn - Newcastle - 4.5
DEF: Mitchell - Crystal Palace - 4.0
MID: Andreas - Fulham - 5.0
GK: Henderson - Nottm Forest - 4.0
```

### Squad Management Features

#### 7.1 Wild Card Mode
- Build a completely new squad using the full system analysis
- Same as option 1 but accessed through squad management menu

#### 7.2 Import Squad + Transfer Analysis
- Load your existing squad from a text file
- Get detailed transfer recommendations
- Analyze specific transfer scenarios with budget planning

#### 7.3 Import Squad + Captain Analysis
- Load your existing squad from a text file
- Get captain recommendations specifically for your imported team

#### 7.4 Export Current Squad
- Save your current squad to a text file
- Choose custom filename or use auto-generated timestamp

## System Architecture

### Core Components

- **UnifiedDataManager**: Fetches and processes FPL API data
- **UnifiedSquadBuilder**: Builds optimal squads with formation constraints
- **UnifiedAnalysisEngine**: Analyzes players using momentum scoring
- **UnifiedReportGenerator**: Creates HTML reports
- **SimpleFPLSystem**: Main system orchestrator

### Key Features

- **Momentum Scoring**: Advanced player analysis considering form, fixtures, and value
- **Smart Caching**: Efficient data management with automatic caching
- **Budget Management**: Precise budget tracking and constraint handling
- **Formation Validation**: Ensures valid FPL squad formations (GK:2, DEF:5, MID:5, FWD:3)
- **Team Limits**: Respects 3-player limit per team

## Data Sources

- **FPL Official API**: Real-time player data, prices, and statistics
- **Automatic Updates**: System fetches latest data on each run

## Output Files

### HTML Reports
- Generated in `fpl_reports/` directory
- Include squad composition, captain options, and top players
- Responsive design with team colors and styling

### Squad Export Files
- Text files with `.txt` extension
- Timestamped filenames for organization
- Human-readable format for easy editing

## Configuration

### Default Settings
- Budget: £100.0M
- Formation: 4-4-2
- Cache timeout: 30 minutes
- Report language: Hebrew (RTL support)

### Customization
- Budget can be adjusted per analysis
- Transfer budget configurable
- Player filtering thresholds adjustable

## Error Handling

- Comprehensive error messages in Hebrew
- Graceful handling of API failures
- Data validation and format checking
- Safe file operations with encoding support

## Performance

- Smart caching reduces API calls
- Optimized data processing
- Efficient memory usage
- Fast squad generation (typically 2-5 seconds)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational and personal use. Please respect FPL's terms of service when using their API.

## Support

For issues or questions:
1. Check the system status (option 5)
2. Verify internet connection for API access
3. Ensure all required files are present
4. Check Python version compatibility

## Version History

- **v1.0**: Initial release with core functionality
- **v1.1**: Added squad import/export features
- **v1.2**: Enhanced transfer analysis and captain recommendations

---

**Note**: This tool is designed to assist with FPL decision-making. Always verify recommendations with current player news and your own analysis before making transfers.
