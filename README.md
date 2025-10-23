# AI-Accelerated Momentum Trading Strategy Tool

An intelligent trading tool inspired by Ross Cameron's momentum trading methodology, enhanced with AI capabilities for automated stock screening, technical analysis, and signal generation.

## Overview

This tool combines news sentiment analysis with technical analysis to identify high-probability momentum trading setups. It focuses on low-float stocks with strong catalysts in target sectors (Healthcare, Cryptocurrency, AI) using proven technical patterns like ABCD formations and MACD confirmations.

## Key Features

### Core Strategy Components
- **Low Float Focus**: Targets stocks under 20-30M float for high volatility
- **Price Range**: $2-20 per share sweet spot
- **Volume Analysis**: 2x+ relative volume with gap detection
- **Sector Targeting**: Healthcare, Crypto, AI focus
- **News-Driven**: Real-time catalyst detection

### Technical Analysis
- **ABCD Pattern Detection**: Automated pattern recognition
- **MACD Confirmation**: Entry/exit signal validation
- **Moving Average Analysis**: 9 EMA, 20 EMA trend confirmation
- **Risk Management**: Automated stop-loss and profit targets

### AI Enhancements
- **Real-time News Processing**: Multi-source sentiment analysis
- **Pattern Recognition**: Advanced technical pattern detection
- **Signal Scoring**: Comprehensive probability scoring
- **Automated Screening**: Continuous market monitoring

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd momentum_trader
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

## Usage

### Stock Screening Mode
```bash
python src/main.py screen
```
Continuously monitors the market for stocks meeting Ross Cameron criteria.

### Individual Stock Analysis
```bash
python src/main.py analyze --symbol GITS
```
Performs comprehensive technical and fundamental analysis on a specific stock.

### Web Interface
```bash
python src/main.py web
```
Launches the web dashboard for real-time monitoring and analysis.

### Backtesting
```bash
python src/main.py backtest --start-date 2024-01-01 --end-date 2024-12-31
```
Tests the strategy against historical data.

## Strategy Criteria

### Ross Cameron's 5 Pillars
1. **High Relative Volume** (2x+ average)
2. **Significant Price Change** (4%+ gap)
3. **Low Float** (under 20-30M shares)
4. **News Catalyst** (FDA, partnerships, etc.)
5. **Price Under $20** (focus on $2-20 range)

### Technical Confirmation
- **ABCD Patterns**: A-B impulse, B-C retracement, C-D extension
- **MACD Positive**: Above zero line with bullish crossover
- **EMA Alignment**: Price above 9 EMA and 20 EMA
- **Volume Confirmation**: Strong volume on breakouts

### Risk Management
- **Stop Loss**: 5-15% below entry (typically 10-15 cents)
- **Profit Targets**: $0.20 scalps, $0.10 and $1.00 tiers
- **Position Sizing**: 1-2% of account per trade
- **Quick Cuts**: Exit on MACD negative signals

## Project Structure

```
momentum_trader/
├── src/
│   ├── core/           # Core utilities (logging, database, exceptions)
│   ├── data/           # Data acquisition and APIs
│   ├── analysis/       # Technical analysis and pattern detection
│   ├── screening/      # Stock screening and filtering
│   ├── signals/        # Signal generation and scoring
│   ├── web/           # Web interface and dashboard
│   └── main.py        # Main application entry point
├── config/            # Configuration management
├── tests/             # Unit tests
├── logs/              # Application logs
├── docs/              # Documentation
└── requirements.txt   # Python dependencies
```

## Development Phases

- [x] **Phase 1**: Project setup and core architecture
- [ ] **Phase 2**: Data acquisition and API integration
- [ ] **Phase 3**: Stock screening and fundamental analysis
- [ ] **Phase 4**: Technical analysis and pattern recognition
- [ ] **Phase 5**: News sentiment analysis and catalyst detection
- [ ] **Phase 6**: Signal generation and scoring system
- [ ] **Phase 7**: Web interface and dashboard
- [ ] **Phase 8**: Testing, validation and deployment

## API Requirements

### Required APIs
- **Financial Data**: Polygon.io, Alpaca, or IEX Cloud
- **News Data**: News API or similar service
- **Market Data**: Real-time price and volume feeds

### Optional APIs
- **Social Sentiment**: StockTwits, Twitter
- **Fundamental Data**: Financial Modeling Prep
- **Options Data**: CBOE or similar

## Configuration

Key configuration options in `config/config.py`:

```python
# Trading criteria
MIN_PRICE = 2.0
MAX_PRICE = 20.0
MAX_FLOAT = 30_000_000
MIN_RELATIVE_VOLUME = 2.0

# Technical settings
MACD_FAST = 12
MACD_SLOW = 26
EMA_SHORT = 9
EMA_LONG = 20

# Risk management
DEFAULT_STOP_LOSS_PERCENT = 0.05
SMALL_SCALP_TARGET = 0.20
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Disclaimer

This tool is for educational and research purposes only. Trading involves substantial risk of loss. Past performance does not guarantee future results. Always do your own research and consider consulting with a financial advisor before making trading decisions.

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Ross Cameron and Warrior Trading for the foundational methodology
- The open-source trading and financial analysis community
- Contributors and testers of this project

