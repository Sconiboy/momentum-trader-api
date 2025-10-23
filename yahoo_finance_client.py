"""
Yahoo Finance data client using yfinance library
Free data source - no API key required
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time

from ..core.logger import get_logger
from ..core.exceptions import DataFetchError

logger = get_logger(__name__)

class YahooFinanceClient:
    """Client for fetching data from Yahoo Finance using yfinance"""
    
    def __init__(self):
        self.session = None
        logger.info("Yahoo Finance client initialized")
    
    def get_stock_data(self, symbol: str, period: str = "1mo", interval: str = "1d") -> pd.DataFrame:
        """
        Get historical stock data for a symbol
        
        Args:
            symbol: Stock ticker symbol
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                raise DataFetchError(f"No data found for symbol {symbol}")
            
            # Standardize column names
            data.columns = [col.lower().replace(' ', '_') for col in data.columns]
            data.reset_index(inplace=True)
            
            # Add symbol column
            data['symbol'] = symbol.upper()
            
            logger.info(f"Retrieved {len(data)} records for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            raise DataFetchError(f"Failed to fetch data for {symbol}: {e}")
    
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get detailed stock information and fundamentals
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with stock information
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info:
                raise DataFetchError(f"No info found for symbol {symbol}")
            
            # Extract key information for our strategy
            stock_info = {
                'symbol': symbol.upper(),
                'company_name': info.get('longName', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'market_cap': info.get('marketCap', 0),
                'shares_outstanding': info.get('sharesOutstanding', 0),
                'float_shares': info.get('floatShares', 0),
                'current_price': info.get('currentPrice', 0),
                'previous_close': info.get('previousClose', 0),
                'volume': info.get('volume', 0),
                'avg_volume': info.get('averageVolume', 0),
                'day_high': info.get('dayHigh', 0),
                'day_low': info.get('dayLow', 0),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'beta': info.get('beta', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'earnings_date': info.get('earningsDate', []),
                'exchange': info.get('exchange', ''),
                'currency': info.get('currency', 'USD'),
                'timestamp': datetime.now()
            }
            
            # Calculate relative volume if possible
            if stock_info['avg_volume'] > 0:
                stock_info['relative_volume'] = stock_info['volume'] / stock_info['avg_volume']
            else:
                stock_info['relative_volume'] = 0
            
            # Calculate gap percentage
            if stock_info['previous_close'] > 0:
                gap_percent = ((stock_info['current_price'] - stock_info['previous_close']) / 
                              stock_info['previous_close']) * 100
                stock_info['gap_percentage'] = gap_percent
            else:
                stock_info['gap_percentage'] = 0
            
            logger.info(f"Retrieved info for {symbol}: {stock_info['company_name']}")
            return stock_info
            
        except Exception as e:
            logger.error(f"Error fetching info for {symbol}: {e}")
            raise DataFetchError(f"Failed to fetch info for {symbol}: {e}")
    
    def get_multiple_stocks_data(self, symbols: List[str], period: str = "1mo") -> Dict[str, pd.DataFrame]:
        """
        Get data for multiple stocks
        
        Args:
            symbols: List of stock ticker symbols
            period: Data period
            
        Returns:
            Dictionary mapping symbols to their data
        """
        results = {}
        
        for symbol in symbols:
            try:
                data = self.get_stock_data(symbol, period)
                results[symbol] = data
                
                # Add small delay to avoid rate limiting
                time.sleep(0.1)
                
            except DataFetchError as e:
                logger.warning(f"Failed to get data for {symbol}: {e}")
                continue
        
        logger.info(f"Retrieved data for {len(results)}/{len(symbols)} symbols")
        return results
    
    def get_multiple_stocks_info(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get info for multiple stocks
        
        Args:
            symbols: List of stock ticker symbols
            
        Returns:
            Dictionary mapping symbols to their info
        """
        results = {}
        
        for symbol in symbols:
            try:
                info = self.get_stock_info(symbol)
                results[symbol] = info
                
                # Add small delay to avoid rate limiting
                time.sleep(0.1)
                
            except DataFetchError as e:
                logger.warning(f"Failed to get info for {symbol}: {e}")
                continue
        
        logger.info(f"Retrieved info for {len(results)}/{len(symbols)} symbols")
        return results
    
    def get_intraday_data(self, symbol: str, interval: str = "1m", period: str = "1d") -> pd.DataFrame:
        """
        Get intraday data for a symbol
        
        Args:
            symbol: Stock ticker symbol
            interval: Data interval (1m, 2m, 5m, 15m, 30m)
            period: Data period (1d, 5d)
            
        Returns:
            DataFrame with intraday OHLCV data
        """
        try:
            # Validate interval for intraday
            valid_intervals = ["1m", "2m", "5m", "15m", "30m", "60m", "90m"]
            if interval not in valid_intervals:
                raise ValueError(f"Invalid interval {interval}. Must be one of {valid_intervals}")
            
            data = self.get_stock_data(symbol, period=period, interval=interval)
            
            logger.info(f"Retrieved {len(data)} intraday records for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching intraday data for {symbol}: {e}")
            raise DataFetchError(f"Failed to fetch intraday data for {symbol}: {e}")
    
    def search_symbols(self, query: str) -> List[Dict[str, str]]:
        """
        Search for stock symbols (limited functionality with yfinance)
        
        Args:
            query: Search query
            
        Returns:
            List of symbol information
        """
        # Note: yfinance doesn't have a built-in search function
        # This is a placeholder for potential future implementation
        logger.warning("Symbol search not implemented with yfinance")
        return []
    
    def get_trending_stocks(self) -> List[str]:
        """
        Get trending stocks (limited functionality with yfinance)
        
        Returns:
            List of trending stock symbols
        """
        # Note: yfinance doesn't provide trending stocks directly
        # We'll implement this through other sources like Finviz
        logger.warning("Trending stocks not available through yfinance")
        return []
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate if a symbol exists and has data
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            True if symbol is valid, False otherwise
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Check if we got meaningful data
            if not info or 'symbol' not in info:
                return False
            
            # Try to get some recent data
            data = ticker.history(period="5d")
            return not data.empty
            
        except Exception:
            return False

