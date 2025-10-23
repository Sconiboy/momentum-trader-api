"""
Finviz web scraper for stock screening and data extraction
Free data source - no API key required
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, quote

from ..core.logger import get_logger
from ..core.exceptions import DataFetchError

logger = get_logger(__name__)

class FinvizScraper:
    """Web scraper for Finviz.com data"""
    
    def __init__(self):
        self.base_url = "https://finviz.com"
        self.session = requests.Session()
        
        # Set headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        logger.info("Finviz scraper initialized")
    
    def get_stock_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get detailed stock data for a specific symbol
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with stock data
        """
        try:
            url = f"{self.base_url}/quote.ashx?t={symbol.upper()}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract stock data from the page
            stock_data = {
                'symbol': symbol.upper(),
                'timestamp': datetime.now()
            }
            
            # Get company name
            title_element = soup.find('title')
            if title_element:
                title_text = title_element.get_text()
                # Extract company name from title
                if ' - ' in title_text:
                    stock_data['company_name'] = title_text.split(' - ')[0].replace(symbol.upper(), '').strip()
            
            # Extract data from the fundamental table
            table = soup.find('table', class_='snapshot-table2')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    for i in range(0, len(cells), 2):
                        if i + 1 < len(cells):
                            key = cells[i].get_text().strip()
                            value = cells[i + 1].get_text().strip()
                            
                            # Map Finviz keys to our standardized keys
                            mapped_data = self._map_finviz_data(key, value)
                            stock_data.update(mapped_data)
            
            # Get sector and industry information
            sector_info = self._extract_sector_industry(soup)
            stock_data.update(sector_info)
            
            # Get current price from the page
            price_info = self._extract_price_info(soup)
            stock_data.update(price_info)
            
            logger.info(f"Retrieved Finviz data for {symbol}")
            return stock_data
            
        except Exception as e:
            logger.error(f"Error scraping Finviz data for {symbol}: {e}")
            raise DataFetchError(f"Failed to scrape Finviz data for {symbol}: {e}")
    
    def screen_stocks(self, filters: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """
        Screen stocks using Finviz screener
        
        Args:
            filters: Dictionary of screening filters
            
        Returns:
            List of stocks matching the criteria
        """
        try:
            # Default filters for Ross Cameron style screening
            default_filters = {
                'sh_price_u20': '',  # Price under $20
                'sh_price_o2': '',   # Price over $2
                'sh_relvol_o2': '',  # Relative volume over 2
                'sh_float_u50': ''   # Float under 50M (closest to our 20-30M target)
            }
            
            if filters:
                default_filters.update(filters)
            
            # Build screener URL
            filter_params = '&'.join([f"{k}={v}" for k, v in default_filters.items()])
            url = f"{self.base_url}/screener.ashx?v=111&{filter_params}"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the screener results table
            results = []
            table = soup.find('table', {'id': 'screener-table'}) or soup.find('table', class_='table-light')
            
            if table:
                rows = table.find_all('tr')[1:]  # Skip header row
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 11:  # Ensure we have enough columns
                        try:
                            stock_data = {
                                'symbol': cells[1].get_text().strip(),
                                'company': cells[2].get_text().strip(),
                                'sector': cells[3].get_text().strip(),
                                'industry': cells[4].get_text().strip(),
                                'country': cells[5].get_text().strip(),
                                'market_cap': self._parse_market_cap(cells[6].get_text().strip()),
                                'pe_ratio': self._safe_float(cells[7].get_text().strip()),
                                'price': self._safe_float(cells[8].get_text().strip()),
                                'change': self._safe_float(cells[9].get_text().strip().replace('%', '')),
                                'volume': self._parse_volume(cells[10].get_text().strip()),
                                'timestamp': datetime.now()
                            }
                            results.append(stock_data)
                        except Exception as e:
                            logger.warning(f"Error parsing row: {e}")
                            continue
            
            logger.info(f"Found {len(results)} stocks in Finviz screener")
            return results
            
        except Exception as e:
            logger.error(f"Error running Finviz screener: {e}")
            raise DataFetchError(f"Failed to run Finviz screener: {e}")
    
    def get_top_gainers(self, count: int = 50) -> List[Dict[str, Any]]:
        """
        Get top gaining stocks from Finviz
        
        Args:
            count: Number of top gainers to retrieve
            
        Returns:
            List of top gaining stocks
        """
        try:
            url = f"{self.base_url}/screener.ashx?v=111&s=ta_topgainers"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            table = soup.find('table', {'id': 'screener-table'}) or soup.find('table', class_='table-light')
            
            if table:
                rows = table.find_all('tr')[1:count+1]  # Skip header, limit to count
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 11:
                        try:
                            stock_data = {
                                'symbol': cells[1].get_text().strip(),
                                'company': cells[2].get_text().strip(),
                                'sector': cells[3].get_text().strip(),
                                'price': self._safe_float(cells[8].get_text().strip()),
                                'change_percent': self._safe_float(cells[9].get_text().strip().replace('%', '')),
                                'volume': self._parse_volume(cells[10].get_text().strip()),
                                'market_cap': self._parse_market_cap(cells[6].get_text().strip()),
                                'timestamp': datetime.now()
                            }
                            results.append(stock_data)
                        except Exception as e:
                            logger.warning(f"Error parsing gainer row: {e}")
                            continue
            
            logger.info(f"Retrieved {len(results)} top gainers from Finviz")
            return results
            
        except Exception as e:
            logger.error(f"Error getting top gainers: {e}")
            return []
    
    def get_news(self, symbol: str = None) -> List[Dict[str, Any]]:
        """
        Get news for a specific symbol or general market news
        
        Args:
            symbol: Stock ticker symbol (optional)
            
        Returns:
            List of news articles
        """
        try:
            if symbol:
                url = f"{self.base_url}/quote.ashx?t={symbol.upper()}"
            else:
                url = f"{self.base_url}/news.ashx"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            news_items = []
            
            # Find news table
            news_table = soup.find('table', {'id': 'news-table'})
            if news_table:
                rows = news_table.find_all('tr')
                
                for row in rows:
                    try:
                        cells = row.find_all('td')
                        if len(cells) >= 2:
                            # Extract timestamp
                            time_cell = cells[0].get_text().strip()
                            
                            # Extract headline and link
                            link_cell = cells[1].find('a')
                            if link_cell:
                                headline = link_cell.get_text().strip()
                                link = link_cell.get('href', '')
                                
                                # Make link absolute if relative
                                if link.startswith('/'):
                                    link = urljoin(self.base_url, link)
                                
                                news_item = {
                                    'headline': headline,
                                    'link': link,
                                    'timestamp': time_cell,
                                    'symbol': symbol.upper() if symbol else None,
                                    'source': 'Finviz',
                                    'scraped_at': datetime.now()
                                }
                                news_items.append(news_item)
                    except Exception as e:
                        logger.warning(f"Error parsing news row: {e}")
                        continue
            
            logger.info(f"Retrieved {len(news_items)} news items")
            return news_items
            
        except Exception as e:
            logger.error(f"Error getting news: {e}")
            return []
    
    def _map_finviz_data(self, key: str, value: str) -> Dict[str, Any]:
        """Map Finviz data keys to our standardized format"""
        mapping = {
            'Market Cap': 'market_cap',
            'P/E': 'pe_ratio',
            'Forward P/E': 'forward_pe',
            'PEG': 'peg_ratio',
            'P/S': 'price_to_sales',
            'P/B': 'price_to_book',
            'P/C': 'price_to_cash',
            'P/FCF': 'price_to_fcf',
            'EPS (ttm)': 'eps_ttm',
            'EPS next Y': 'eps_next_year',
            'EPS next Q': 'eps_next_quarter',
            'EPS this Y': 'eps_this_year',
            'Sales Y/Y TTM': 'sales_growth_yoy',
            'EPS Y/Y TTM': 'eps_growth_yoy',
            'Sales Q/Q': 'sales_growth_qq',
            'EPS Q/Q': 'eps_growth_qq',
            'Insider Own': 'insider_ownership',
            'Insider Trans': 'insider_transactions',
            'Inst Own': 'institutional_ownership',
            'Inst Trans': 'institutional_transactions',
            'Float': 'float_shares',
            'Shs Outstand': 'shares_outstanding',
            'Shs Float': 'float_shares',
            'Short Float': 'short_float_percent',
            'Short Ratio': 'short_ratio',
            'Short Interest': 'short_interest',
            'ROA': 'return_on_assets',
            'ROE': 'return_on_equity',
            'ROI': 'return_on_investment',
            'Curr R': 'current_ratio',
            'Quick R': 'quick_ratio',
            'LTDebt/Eq': 'long_term_debt_to_equity',
            'Debt/Eq': 'debt_to_equity',
            'Gross M': 'gross_margin',
            'Oper M': 'operating_margin',
            'Profit M': 'profit_margin',
            'Perf Week': 'performance_week',
            'Perf Month': 'performance_month',
            'Perf Quart': 'performance_quarter',
            'Perf Half': 'performance_half_year',
            'Perf Year': 'performance_year',
            'Perf YTD': 'performance_ytd',
            'Beta': 'beta',
            'ATR': 'average_true_range',
            'Volatility': 'volatility',
            'RSI (14)': 'rsi',
            'Rel Volume': 'relative_volume',
            'Avg Volume': 'average_volume',
            'Volume': 'volume',
            'Price': 'current_price',
            'Change': 'price_change_percent',
            '52W High': 'fifty_two_week_high',
            '52W Low': 'fifty_two_week_low',
            'SMA20': 'sma_20_distance',
            'SMA50': 'sma_50_distance',
            'SMA200': 'sma_200_distance',
            'Dividend': 'dividend_yield',
            'Dividend %': 'dividend_yield',
            'Payout': 'payout_ratio',
            'Employees': 'employee_count'
        }
        
        result = {}
        if key in mapping:
            standardized_key = mapping[key]
            
            # Parse the value based on the key type
            if 'percent' in standardized_key or key in ['Change', 'Short Float', 'Insider Own', 'Inst Own']:
                result[standardized_key] = self._parse_percentage(value)
            elif 'shares' in standardized_key or key in ['Float', 'Shs Outstand', 'Shs Float', 'Volume', 'Avg Volume']:
                result[standardized_key] = self._parse_volume(value)
            elif 'market_cap' in standardized_key:
                result[standardized_key] = self._parse_market_cap(value)
            elif key in ['Employees']:
                result[standardized_key] = self._safe_int(value)
            else:
                result[standardized_key] = self._safe_float(value)
        
        return result
    
    def _extract_sector_industry(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract sector and industry information"""
        result = {}
        
        # Look for sector/industry links
        links = soup.find_all('a')
        for link in links:
            href = link.get('href', '')
            text = link.get_text().strip()
            
            if 'screener.ashx?v=111&f=sec_' in href:
                result['sector'] = text
            elif 'screener.ashx?v=111&f=ind_' in href:
                result['industry'] = text
        
        return result
    
    def _extract_price_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract current price and change information"""
        result = {}
        
        # Look for price information in various locations
        price_elements = soup.find_all(['span', 'td'], class_=re.compile(r'.*price.*|.*quote.*'))
        
        for element in price_elements:
            text = element.get_text().strip()
            if '$' in text and len(text) < 20:  # Likely a price
                try:
                    price = float(text.replace('$', '').replace(',', ''))
                    result['current_price'] = price
                    break
                except ValueError:
                    continue
        
        return result
    
    def _parse_percentage(self, value: str) -> float:
        """Parse percentage value"""
        try:
            return float(value.replace('%', '').replace(',', ''))
        except (ValueError, AttributeError):
            return 0.0
    
    def _parse_volume(self, value: str) -> int:
        """Parse volume value with K, M, B suffixes"""
        try:
            value = value.replace(',', '').upper()
            if 'K' in value:
                return int(float(value.replace('K', '')) * 1000)
            elif 'M' in value:
                return int(float(value.replace('M', '')) * 1000000)
            elif 'B' in value:
                return int(float(value.replace('B', '')) * 1000000000)
            else:
                return int(float(value))
        except (ValueError, AttributeError):
            return 0
    
    def _parse_market_cap(self, value: str) -> float:
        """Parse market cap value with K, M, B suffixes"""
        try:
            value = value.replace(',', '').replace('$', '').upper()
            if 'K' in value:
                return float(value.replace('K', '')) * 1000
            elif 'M' in value:
                return float(value.replace('M', '')) * 1000000
            elif 'B' in value:
                return float(value.replace('B', '')) * 1000000000
            else:
                return float(value)
        except (ValueError, AttributeError):
            return 0.0
    
    def _safe_float(self, value: str) -> float:
        """Safely convert string to float"""
        try:
            if value == '-' or value == '' or value.lower() == 'n/a':
                return 0.0
            return float(value.replace('%', '').replace(',', '').replace('$', ''))
        except (ValueError, AttributeError):
            return 0.0
    
    def _safe_int(self, value: str) -> int:
        """Safely convert string to int"""
        try:
            if value == '-' or value == '' or value.lower() == 'n/a':
                return 0
            return int(float(value.replace(',', '')))
        except (ValueError, AttributeError):
            return 0

