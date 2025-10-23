"""
Configuration management for the Momentum Trading Strategy Tool
"""
import os
from dataclasses import dataclass
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class TradingConfig:
    """Core trading strategy configuration"""
    
    # Price and float criteria (Ross Cameron style)
    MIN_PRICE: float = 2.0
    MAX_PRICE: float = 20.0
    MAX_FLOAT: int = 30_000_000  # 30M shares
    PREFERRED_MAX_FLOAT: int = 20_000_000  # 20M shares
    
    # Volume criteria
    MIN_RELATIVE_VOLUME: float = 2.0
    PREFERRED_RELATIVE_VOLUME: float = 5.0
    MIN_GAP_PERCENTAGE: float = 4.0
    
    # Target sectors
    TARGET_SECTORS: List[str] = None
    
    def __post_init__(self):
        if self.TARGET_SECTORS is None:
            self.TARGET_SECTORS = [
                "Healthcare",
                "Biotechnology", 
                "Pharmaceuticals",
                "Cryptocurrency",
                "Artificial Intelligence",
                "Technology",
                "Software",
                "Internet Content & Information"
            ]

@dataclass
class TechnicalConfig:
    """Technical analysis configuration"""
    
    # MACD settings
    MACD_FAST: int = 12
    MACD_SLOW: int = 26
    MACD_SIGNAL: int = 9
    
    # Moving averages
    EMA_SHORT: int = 9
    EMA_LONG: int = 20
    SMA_50: int = 50
    SMA_200: int = 200
    
    # RSI settings
    RSI_PERIOD: int = 14
    RSI_OVERBOUGHT: float = 70.0
    RSI_OVERSOLD: float = 30.0
    
    # ABCD pattern settings
    FIBONACCI_LEVELS: List[float] = None
    MIN_PATTERN_BARS: int = 10
    MAX_PATTERN_BARS: int = 50
    
    def __post_init__(self):
        if self.FIBONACCI_LEVELS is None:
            self.FIBONACCI_LEVELS = [0.382, 0.5, 0.618]

@dataclass
class RiskConfig:
    """Risk management configuration"""
    
    # Stop loss settings
    DEFAULT_STOP_LOSS_PERCENT: float = 0.05  # 5%
    MAX_STOP_LOSS_PERCENT: float = 0.15  # 15%
    
    # Profit targets
    SMALL_SCALP_TARGET: float = 0.20  # $0.20
    TIER_1_TARGET: float = 0.10  # $0.10
    TIER_2_TARGET: float = 1.00  # $1.00
    
    # Position sizing
    MAX_POSITION_SIZE_PERCENT: float = 0.02  # 2% of account
    DEFAULT_POSITION_SIZE_PERCENT: float = 0.01  # 1% of account

@dataclass
class DataConfig:
    """Data source configuration"""
    
    # API Keys (from environment variables)
    POLYGON_API_KEY: str = os.getenv('POLYGON_API_KEY', '')
    ALPACA_API_KEY: str = os.getenv('ALPACA_API_KEY', '')
    ALPACA_SECRET_KEY: str = os.getenv('ALPACA_SECRET_KEY', '')
    IEX_API_KEY: str = os.getenv('IEX_API_KEY', '')
    
    # Data refresh intervals (in seconds)
    REAL_TIME_REFRESH: int = 5
    SCREENING_REFRESH: int = 60
    NEWS_REFRESH: int = 30
    
    # Database settings
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///momentum_trader.db')
    
    # Web scraping settings
    FINVIZ_BASE_URL: str = "https://finviz.com"
    STOCKTWITS_BASE_URL: str = "https://stocktwits.com"
    
    # News sources
    NEWS_SOURCES: List[str] = None
    
    def __post_init__(self):
        if self.NEWS_SOURCES is None:
            self.NEWS_SOURCES = [
                "https://www.prnewswire.com",
                "https://www.businesswire.com",
                "https://finance.yahoo.com",
                "https://www.marketwatch.com"
            ]

@dataclass
class AppConfig:
    """Main application configuration"""
    
    # Flask settings
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    HOST: str = os.getenv('HOST', '0.0.0.0')
    PORT: int = int(os.getenv('PORT', 5000))
    
    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = 'logs/momentum_trader.log'
    
    # Component configurations
    trading: TradingConfig = None
    technical: TechnicalConfig = None
    risk: RiskConfig = None
    data: DataConfig = None
    
    def __post_init__(self):
        if self.trading is None:
            self.trading = TradingConfig()
        if self.technical is None:
            self.technical = TechnicalConfig()
        if self.risk is None:
            self.risk = RiskConfig()
        if self.data is None:
            self.data = DataConfig()

# Global configuration instance
config = AppConfig()

def get_config() -> AppConfig:
    """Get the global configuration instance"""
    return config

def update_config(**kwargs) -> None:
    """Update configuration values"""
    global config
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            raise ValueError(f"Unknown configuration key: {key}")

