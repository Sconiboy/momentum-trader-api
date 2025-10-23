"""
Alpha Vantage data client for additional market data
Free tier: 500 requests per day, 5 requests per minute
"""
import requests
import pandas as pd
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os

from ..core.logger import get_logger
from ..core.exceptions import DataFetchError, APIError

logger = get_logger(__name__)

class AlphaVantageClient:
    """Client for fetching data from Alpha Vantage API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ALPHA_VANTAGE_API_KEY')
        self.base_url = "https://www.alphavantage.co/query"
        self.last_request_time = 0
        self.min_request_interval = 12  # 5 requests per minute = 12 seconds between requests
        
        if not self.api_key:
            logger.warning("Alpha Vantage API key not provided. Some features will be limited.")
        else:
            logger.info("Alpha Vantage client initialized")
    
    def _make_request(self, params: Dict[str, str]) -> Dict[str, Any]:
        """
        Make a rate-limited request to Alpha Vantage API
        
        Args:
            params: Request parameters
            
        Returns:
            JSON response data
        """
        if not self.api_key:
            raise APIError("Alpha Vantage API key not configured")
        
        # Rate limiting
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            logger.info(f"Rate limiting: sleeping for {sleep_time:.1f} seconds")
            time.sleep(sleep_time)
        
        # Add API key to parameters
        params['apikey'] = self.api_key
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            self.last_request_time = time.time()
            
            data = response.json()
            
            # Check for API errors
            if 'Error Message' in data:
                raise APIError(f"Alpha Vantage API error: {data['Error Message']}")
            
            if 'Note' in data:
                raise APIError(f"Alpha Vantage rate limit: {data['Note']}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise APIError(f"Failed to fetch data from Alpha Vantage: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            raise APIError(f"Invalid response from Alpha Vantage: {e}")
    
    def get_intraday_data(self, symbol: str, interval: str = "5min") -> pd.DataFrame:
        """
        Get intraday stock data
        
        Args:
            symbol: Stock ticker symbol
            interval: Time interval (1min, 5min, 15min, 30min, 60min)
            
        Returns:
            DataFrame with intraday OHLCV data
        """
        try:
            params = {
                'function': 'TIME_SERIES_INTRADAY',
                'symbol': symbol.upper(),
                'interval': interval,
                'outputsize': 'compact'  # Last 100 data points
            }
            
            data = self._make_request(params)
            
            # Extract time series data
            time_series_key = f'Time Series ({interval})'
            if time_series_key not in data:
                raise DataFetchError(f"No intraday data found for {symbol}")
            
            time_series = data[time_series_key]
            
            # Convert to DataFrame
            df_data = []
            for timestamp, values in time_series.items():
                row = {
                    'datetime': pd.to_datetime(timestamp),
                    'open': float(values['1. open']),
                    'high': float(values['2. high']),
                    'low': float(values['3. low']),
                    'close': float(values['4. close']),
                    'volume': int(values['5. volume']),
                    'symbol': symbol.upper()
                }
                df_data.append(row)
            
            df = pd.DataFrame(df_data)
            df = df.sort_values('datetime').reset_index(drop=True)
            
            logger.info(f"Retrieved {len(df)} intraday records for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching intraday data for {symbol}: {e}")
            raise DataFetchError(f"Failed to fetch intraday data for {symbol}: {e}")
    
    def get_daily_data(self, symbol: str, outputsize: str = "compact") -> pd.DataFrame:
        """
        Get daily stock data
        
        Args:
            symbol: Stock ticker symbol
            outputsize: 'compact' (last 100 days) or 'full' (20+ years)
            
        Returns:
            DataFrame with daily OHLCV data
        """
        try:
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': symbol.upper(),
                'outputsize': outputsize
            }
            
            data = self._make_request(params)
            
            # Extract time series data
            if 'Time Series (Daily)' not in data:
                raise DataFetchError(f"No daily data found for {symbol}")
            
            time_series = data['Time Series (Daily)']
            
            # Convert to DataFrame
            df_data = []
            for date, values in time_series.items():
                row = {
                    'date': pd.to_datetime(date),
                    'open': float(values['1. open']),
                    'high': float(values['2. high']),
                    'low': float(values['3. low']),
                    'close': float(values['4. close']),
                    'volume': int(values['5. volume']),
                    'symbol': symbol.upper()
                }
                df_data.append(row)
            
            df = pd.DataFrame(df_data)
            df = df.sort_values('date').reset_index(drop=True)
            
            logger.info(f"Retrieved {len(df)} daily records for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching daily data for {symbol}: {e}")
            raise DataFetchError(f"Failed to fetch daily data for {symbol}: {e}")
    
    def get_company_overview(self, symbol: str) -> Dict[str, Any]:
        """
        Get company overview and fundamental data
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with company information
        """
        try:
            params = {
                'function': 'OVERVIEW',
                'symbol': symbol.upper()
            }
            
            data = self._make_request(params)
            
            if not data or 'Symbol' not in data:
                raise DataFetchError(f"No overview data found for {symbol}")
            
            # Extract relevant information for our strategy
            overview = {
                'symbol': data.get('Symbol', ''),
                'name': data.get('Name', ''),
                'description': data.get('Description', ''),
                'exchange': data.get('Exchange', ''),
                'currency': data.get('Currency', ''),
                'country': data.get('Country', ''),
                'sector': data.get('Sector', ''),
                'industry': data.get('Industry', ''),
                'market_cap': self._safe_float(data.get('MarketCapitalization', 0)),
                'shares_outstanding': self._safe_float(data.get('SharesOutstanding', 0)),
                'pe_ratio': self._safe_float(data.get('PERatio', 0)),
                'peg_ratio': self._safe_float(data.get('PEGRatio', 0)),
                'book_value': self._safe_float(data.get('BookValue', 0)),
                'dividend_per_share': self._safe_float(data.get('DividendPerShare', 0)),
                'dividend_yield': self._safe_float(data.get('DividendYield', 0)),
                'eps': self._safe_float(data.get('EPS', 0)),
                'revenue_per_share': self._safe_float(data.get('RevenuePerShareTTM', 0)),
                'profit_margin': self._safe_float(data.get('ProfitMargin', 0)),
                'operating_margin': self._safe_float(data.get('OperatingMarginTTM', 0)),
                'return_on_assets': self._safe_float(data.get('ReturnOnAssetsTTM', 0)),
                'return_on_equity': self._safe_float(data.get('ReturnOnEquityTTM', 0)),
                'revenue_ttm': self._safe_float(data.get('RevenueTTM', 0)),
                'gross_profit_ttm': self._safe_float(data.get('GrossProfitTTM', 0)),
                'ebitda': self._safe_float(data.get('EBITDA', 0)),
                'beta': self._safe_float(data.get('Beta', 0)),
                '52_week_high': self._safe_float(data.get('52WeekHigh', 0)),
                '52_week_low': self._safe_float(data.get('52WeekLow', 0)),
                '50_day_ma': self._safe_float(data.get('50DayMovingAverage', 0)),
                '200_day_ma': self._safe_float(data.get('200DayMovingAverage', 0)),
                'analyst_target_price': self._safe_float(data.get('AnalystTargetPrice', 0)),
                'timestamp': datetime.now()
            }
            
            logger.info(f"Retrieved overview for {symbol}: {overview['name']}")
            return overview
            
        except Exception as e:
            logger.error(f"Error fetching overview for {symbol}: {e}")
            raise DataFetchError(f"Failed to fetch overview for {symbol}: {e}")
    
    def search_symbols(self, keywords: str) -> List[Dict[str, str]]:
        """
        Search for symbols by keywords
        
        Args:
            keywords: Search keywords
            
        Returns:
            List of matching symbols with basic info
        """
        try:
            params = {
                'function': 'SYMBOL_SEARCH',
                'keywords': keywords
            }
            
            data = self._make_request(params)
            
            if 'bestMatches' not in data:
                return []
            
            results = []
            for match in data['bestMatches']:
                result = {
                    'symbol': match.get('1. symbol', ''),
                    'name': match.get('2. name', ''),
                    'type': match.get('3. type', ''),
                    'region': match.get('4. region', ''),
                    'market_open': match.get('5. marketOpen', ''),
                    'market_close': match.get('6. marketClose', ''),
                    'timezone': match.get('7. timezone', ''),
                    'currency': match.get('8. currency', ''),
                    'match_score': match.get('9. matchScore', '')
                }
                results.append(result)
            
            logger.info(f"Found {len(results)} symbols for keywords: {keywords}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching symbols for {keywords}: {e}")
            return []
    
    def get_top_gainers_losers(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get top gainers and losers
        
        Returns:
            Dictionary with top_gainers, top_losers, and most_actively_traded
        """
        try:
            params = {
                'function': 'TOP_GAINERS_LOSERS'
            }
            
            data = self._make_request(params)
            
            result = {
                'top_gainers': [],
                'top_losers': [],
                'most_actively_traded': []
            }
            
            # Process each category
            for category in ['top_gainers', 'top_losers', 'most_actively_traded']:
                if category in data:
                    for item in data[category]:
                        processed_item = {
                            'ticker': item.get('ticker', ''),
                            'price': self._safe_float(item.get('price', 0)),
                            'change_amount': self._safe_float(item.get('change_amount', 0)),
                            'change_percentage': item.get('change_percentage', '').replace('%', ''),
                            'volume': self._safe_int(item.get('volume', 0))
                        }
                        result[category].append(processed_item)
            
            logger.info("Retrieved top gainers/losers data")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching top gainers/losers: {e}")
            return {'top_gainers': [], 'top_losers': [], 'most_actively_traded': []}
    
    def _safe_float(self, value: Any) -> float:
        """Safely convert value to float"""
        try:
            if value == 'None' or value is None or value == '':
                return 0.0
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def _safe_int(self, value: Any) -> int:
        """Safely convert value to int"""
        try:
            if value == 'None' or value is None or value == '':
                return 0
            return int(float(value))
        except (ValueError, TypeError):
            return 0
    
    def get_api_status(self) -> Dict[str, Any]:
        """
        Check API status and remaining quota
        
        Returns:
            Dictionary with API status information
        """
        if not self.api_key:
            return {'status': 'no_api_key', 'message': 'API key not configured'}
        
        try:
            # Make a simple request to check status
            params = {
                'function': 'TIME_SERIES_INTRADAY',
                'symbol': 'AAPL',
                'interval': '5min',
                'outputsize': 'compact'
            }
            
            data = self._make_request(params)
            
            if 'Error Message' in data:
                return {'status': 'error', 'message': data['Error Message']}
            elif 'Note' in data:
                return {'status': 'rate_limited', 'message': data['Note']}
            else:
                return {'status': 'ok', 'message': 'API is working'}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

