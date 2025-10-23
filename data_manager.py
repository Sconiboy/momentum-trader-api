"""
Data Manager - Coordinates all data sources and provides unified interface
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import asyncio
import concurrent.futures
from dataclasses import dataclass

from ..core.logger import get_logger
from ..core.exceptions import DataFetchError
from ..core.database import DatabaseManager
from .yahoo_finance_client import YahooFinanceClient
from .alpha_vantage_client import AlphaVantageClient
from .finviz_scraper import FinvizScraper

logger = get_logger(__name__)

@dataclass
class StockData:
    """Standardized stock data structure"""
    symbol: str
    current_price: float
    volume: int
    relative_volume: float
    market_cap: float
    float_shares: int
    sector: str
    industry: str
    gap_percentage: float
    pe_ratio: float
    beta: float
    avg_volume: int
    day_high: float
    day_low: float
    fifty_two_week_high: float
    fifty_two_week_low: float
    timestamp: datetime
    
    def meets_ross_criteria(self, config) -> Dict[str, bool]:
        """Check if stock meets Ross Cameron criteria"""
        criteria = {
            'price_range': config.trading.MIN_PRICE <= self.current_price <= config.trading.MAX_PRICE,
            'float_size': 0 < self.float_shares <= config.trading.MAX_FLOAT,
            'relative_volume': self.relative_volume >= config.trading.MIN_RELATIVE_VOLUME,
            'gap_percentage': abs(self.gap_percentage) >= config.trading.MIN_GAP_PERCENTAGE,
            'has_volume': self.volume > 0,
            'target_sector': any(sector.lower() in self.sector.lower() for sector in config.trading.TARGET_SECTORS) if self.sector else False
        }
        return criteria
    
    def calculate_score(self, config) -> float:
        """Calculate a score based on Ross Cameron criteria"""
        criteria = self.meets_ross_criteria(config)
        
        # Base score from criteria
        score = sum(criteria.values()) * 10
        
        # Bonus points for exceptional characteristics
        if self.float_shares > 0 and self.float_shares <= config.trading.PREFERRED_MAX_FLOAT:
            score += 15  # Preferred float range
        
        if self.relative_volume >= config.trading.PREFERRED_RELATIVE_VOLUME:
            score += 10  # High relative volume
        
        if abs(self.gap_percentage) >= 10:
            score += 10  # Large gap
        
        if self.volume > self.avg_volume * 5:
            score += 5  # Very high volume
        
        return min(score, 100)  # Cap at 100

class DataManager:
    """Manages all data sources and provides unified interface"""
    
    def __init__(self, config, db_manager: DatabaseManager):
        self.config = config
        self.db_manager = db_manager
        
        # Initialize data sources
        self.yahoo_client = YahooFinanceClient()
        self.alpha_vantage_client = AlphaVantageClient(None)  # No API key for now
        self.finviz_scraper = FinvizScraper()
        
        logger.info("Data Manager initialized with all data sources")
    
    def get_comprehensive_stock_data(self, symbol: str) -> StockData:
        """
        Get comprehensive stock data from multiple sources
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            StockData object with combined information
        """
        try:
            # Start with Yahoo Finance as primary source
            yahoo_info = self.yahoo_client.get_stock_info(symbol)
            
            # Enhance with Finviz data
            try:
                finviz_data = self.finviz_scraper.get_stock_data(symbol)
                # Merge Finviz data into Yahoo data
                for key, value in finviz_data.items():
                    if key not in yahoo_info or yahoo_info[key] == 0:
                        yahoo_info[key] = value
            except Exception as e:
                logger.warning(f"Could not get Finviz data for {symbol}: {e}")
            
            # Create standardized StockData object
            stock_data = StockData(
                symbol=yahoo_info.get('symbol', symbol.upper()),
                current_price=yahoo_info.get('current_price', 0),
                volume=yahoo_info.get('volume', 0),
                relative_volume=yahoo_info.get('relative_volume', 0),
                market_cap=yahoo_info.get('market_cap', 0),
                float_shares=yahoo_info.get('float_shares', 0),
                sector=yahoo_info.get('sector', ''),
                industry=yahoo_info.get('industry', ''),
                gap_percentage=yahoo_info.get('gap_percentage', 0),
                pe_ratio=yahoo_info.get('pe_ratio', 0),
                beta=yahoo_info.get('beta', 0),
                avg_volume=yahoo_info.get('avg_volume', 0),
                day_high=yahoo_info.get('day_high', 0),
                day_low=yahoo_info.get('day_low', 0),
                fifty_two_week_high=yahoo_info.get('fifty_two_week_high', 0),
                fifty_two_week_low=yahoo_info.get('fifty_two_week_low', 0),
                timestamp=datetime.now()
            )
            
            # Save to database
            self._save_stock_data_to_db(stock_data)
            
            logger.info(f"Retrieved comprehensive data for {symbol}")
            return stock_data
            
        except Exception as e:
            logger.error(f"Error getting comprehensive data for {symbol}: {e}")
            raise DataFetchError(f"Failed to get comprehensive data for {symbol}: {e}")
    
    def screen_stocks_ross_criteria(self) -> List[StockData]:
        """
        Screen stocks using Ross Cameron criteria across multiple sources
        
        Returns:
            List of StockData objects meeting the criteria
        """
        try:
            candidates = []
            
            # Get candidates from Finviz screener
            logger.info("Screening stocks using Finviz...")
            finviz_filters = {
                'sh_price_u20': '',  # Price under $20
                'sh_price_o2': '',   # Price over $2
                'sh_relvol_o2': '',  # Relative volume over 2
                'sh_float_u50': ''   # Float under 50M
            }
            
            finviz_results = self.finviz_scraper.screen_stocks(finviz_filters)
            
            # Get top gainers as additional candidates
            top_gainers = self.finviz_scraper.get_top_gainers(20)
            
            # Combine and deduplicate
            all_candidates = finviz_results + top_gainers
            unique_symbols = list(set([stock['symbol'] for stock in all_candidates]))
            
            logger.info(f"Found {len(unique_symbols)} unique candidate symbols")
            
            # Get comprehensive data for each candidate
            for symbol in unique_symbols[:50]:  # Limit to avoid rate limits
                try:
                    stock_data = self.get_comprehensive_stock_data(symbol)
                    
                    # Check if meets Ross criteria
                    criteria = stock_data.meets_ross_criteria(self.config)
                    if sum(criteria.values()) >= 4:  # At least 4 out of 6 criteria
                        candidates.append(stock_data)
                        logger.info(f"Added candidate: {symbol} (score: {stock_data.calculate_score(self.config)})")
                    
                except Exception as e:
                    logger.warning(f"Error processing candidate {symbol}: {e}")
                    continue
            
            # Sort by score
            candidates.sort(key=lambda x: x.calculate_score(self.config), reverse=True)
            
            # Save screening results to database
            self._save_screening_results_to_db(candidates)
            
            logger.info(f"Screening completed. Found {len(candidates)} qualifying stocks")
            return candidates
            
        except Exception as e:
            logger.error(f"Error in stock screening: {e}")
            raise DataFetchError(f"Stock screening failed: {e}")
    
    def get_historical_data(self, symbol: str, period: str = "1mo", interval: str = "1d") -> pd.DataFrame:
        """
        Get historical price data for technical analysis
        
        Args:
            symbol: Stock ticker symbol
            period: Data period
            interval: Data interval
            
        Returns:
            DataFrame with historical OHLCV data
        """
        try:
            # Primary source: Yahoo Finance
            data = self.yahoo_client.get_stock_data(symbol, period, interval)
            
            if data.empty:
                # Fallback to Alpha Vantage if available
                if self.alpha_vantage_client.api_key:
                    if interval in ['1d', 'daily']:
                        data = self.alpha_vantage_client.get_daily_data(symbol)
                    else:
                        data = self.alpha_vantage_client.get_intraday_data(symbol, interval)
            
            logger.info(f"Retrieved {len(data)} historical records for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            raise DataFetchError(f"Failed to get historical data for {symbol}: {e}")
    
    def get_intraday_data(self, symbol: str, interval: str = "5m") -> pd.DataFrame:
        """
        Get intraday data for real-time analysis
        
        Args:
            symbol: Stock ticker symbol
            interval: Data interval (1m, 5m, 15m, 30m)
            
        Returns:
            DataFrame with intraday OHLCV data
        """
        try:
            # Try Yahoo Finance first
            data = self.yahoo_client.get_intraday_data(symbol, interval)
            
            if data.empty and self.alpha_vantage_client.api_key:
                # Fallback to Alpha Vantage
                av_interval = interval.replace('m', 'min')
                data = self.alpha_vantage_client.get_intraday_data(symbol, av_interval)
            
            logger.info(f"Retrieved {len(data)} intraday records for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error getting intraday data for {symbol}: {e}")
            raise DataFetchError(f"Failed to get intraday data for {symbol}: {e}")
    
    def get_news_for_symbol(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get news for a specific symbol
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            List of news articles
        """
        try:
            news_items = []
            
            # Get news from Finviz
            finviz_news = self.finviz_scraper.get_news(symbol)
            news_items.extend(finviz_news)
            
            # TODO: Add other news sources when available
            
            logger.info(f"Retrieved {len(news_items)} news items for {symbol}")
            return news_items
            
        except Exception as e:
            logger.error(f"Error getting news for {symbol}: {e}")
            return []
    
    def get_market_movers(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get market movers (gainers, losers, most active)
        
        Returns:
            Dictionary with market movers data
        """
        try:
            movers = {
                'top_gainers': [],
                'top_losers': [],
                'most_active': []
            }
            
            # Get from Finviz
            finviz_gainers = self.finviz_scraper.get_top_gainers(25)
            movers['top_gainers'] = finviz_gainers
            
            # Get from Alpha Vantage if available
            if self.alpha_vantage_client.api_key:
                try:
                    av_movers = self.alpha_vantage_client.get_top_gainers_losers()
                    movers['top_losers'] = av_movers.get('top_losers', [])
                    movers['most_active'] = av_movers.get('most_actively_traded', [])
                except Exception as e:
                    logger.warning(f"Could not get Alpha Vantage movers: {e}")
            
            logger.info("Retrieved market movers data")
            return movers
            
        except Exception as e:
            logger.error(f"Error getting market movers: {e}")
            return {'top_gainers': [], 'top_losers': [], 'most_active': []}
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate if a symbol exists and has data
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            True if symbol is valid, False otherwise
        """
        try:
            # Try Yahoo Finance first
            if self.yahoo_client.validate_symbol(symbol):
                return True
            
            # Try getting basic info from Finviz
            finviz_data = self.finviz_scraper.get_stock_data(symbol)
            return bool(finviz_data.get('current_price', 0) > 0)
            
        except Exception:
            return False
    
    def _save_stock_data_to_db(self, stock_data: StockData):
        """Save stock data to database"""
        try:
            data_dict = {
                'symbol': stock_data.symbol,
                'timestamp': stock_data.timestamp,
                'open_price': None,  # Not available in current data
                'high_price': stock_data.day_high,
                'low_price': stock_data.day_low,
                'close_price': stock_data.current_price,
                'volume': stock_data.volume,
                'relative_volume': stock_data.relative_volume,
                'market_cap': stock_data.market_cap,
                'float_shares': stock_data.float_shares,
                'sector': stock_data.sector
            }
            
            self.db_manager.save_stock_data([data_dict])
            
        except Exception as e:
            logger.warning(f"Could not save stock data to database: {e}")
    
    def _save_screening_results_to_db(self, candidates: List[StockData]):
        """Save screening results to database"""
        try:
            results = []
            for stock in candidates:
                result = {
                    'symbol': stock.symbol,
                    'timestamp': stock.timestamp,
                    'price': stock.current_price,
                    'volume': stock.volume,
                    'relative_volume': stock.relative_volume,
                    'float_shares': stock.float_shares,
                    'gap_percentage': stock.gap_percentage,
                    'sector': stock.sector,
                    'news_catalyst': '',  # TODO: Add news catalyst detection
                    'score': stock.calculate_score(self.config)
                }
                results.append(result)
            
            self.db_manager.save_screening_results(results)
            
        except Exception as e:
            logger.warning(f"Could not save screening results to database: {e}")
    
    def get_data_source_status(self) -> Dict[str, str]:
        """
        Get status of all data sources
        
        Returns:
            Dictionary with status of each data source
        """
        status = {
            'yahoo_finance': 'available',
            'finviz': 'available',
            'alpha_vantage': 'not_configured'
        }
        
        # Check Alpha Vantage status
        if self.alpha_vantage_client.api_key:
            av_status = self.alpha_vantage_client.get_api_status()
            status['alpha_vantage'] = av_status['status']
        
        return status

