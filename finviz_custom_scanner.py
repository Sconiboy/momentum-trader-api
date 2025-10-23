"""
Finviz Custom Scanner Integration
Accesses user's custom Finviz scanners for enhanced stock screening
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
import re

from ..core.logger import get_logger
from ..core.exceptions import DataFetchError

logger = get_logger(__name__)

class FinvizCustomScanner:
    """Access and parse custom Finviz scanners"""
    
    def __init__(self, session_cookies: Dict[str, str] = None):
        """
        Initialize with optional session cookies for authenticated access
        
        Args:
            session_cookies: Dictionary of cookies for authenticated Finviz access
        """
        self.base_url = "https://finviz.com"
        self.session = requests.Session()
        
        # Set headers to mimic browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Add session cookies if provided
        if session_cookies:
            self.session.cookies.update(session_cookies)
        
        # Known custom scanner URLs (can be expanded)
        self.custom_scanners = {
            'up_20_percent': {
                'name': 's: up 20%',
                'url': 'screener.ashx?v=111&s=ta_topgainers&f=ah_change_u,sh_price_u30,ta_change_u20,ta_perf2_dup&ft=3&o=-change&ar=10',
                'description': 'Stocks up 20%+ with price under $30'
            }
        }
        
        logger.info("Finviz Custom Scanner initialized")
    
    def get_custom_scanner_results(self, scanner_key: str) -> List[Dict[str, Any]]:
        """
        Get results from a specific custom scanner
        
        Args:
            scanner_key: Key identifying the custom scanner
            
        Returns:
            List of stock data from the scanner
        """
        try:
            if scanner_key not in self.custom_scanners:
                raise ValueError(f"Unknown scanner key: {scanner_key}")
            
            scanner_info = self.custom_scanners[scanner_key]
            url = f"{self.base_url}/{scanner_info['url']}"
            
            logger.info(f"Accessing custom scanner: {scanner_info['name']}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Parse the results table
            results = self._parse_screener_table(soup)
            
            # Add scanner metadata
            for result in results:
                result['scanner_name'] = scanner_info['name']
                result['scanner_key'] = scanner_key
                result['scan_timestamp'] = datetime.now()
            
            logger.info(f"Retrieved {len(results)} results from {scanner_info['name']}")
            return results
            
        except Exception as e:
            logger.error(f"Error accessing custom scanner {scanner_key}: {e}")
            raise DataFetchError(f"Failed to access custom scanner: {e}")
    
    def get_up_20_percent_scanner(self) -> List[Dict[str, Any]]:
        """
        Get results from the 'up 20%' custom scanner
        Convenience method for the most useful Ross Cameron scanner
        
        Returns:
            List of stocks up 20%+ with additional filtering
        """
        return self.get_custom_scanner_results('up_20_percent')
    
    def get_all_custom_scanners(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get results from all available custom scanners
        
        Returns:
            Dictionary mapping scanner keys to their results
        """
        all_results = {}
        
        for scanner_key in self.custom_scanners.keys():
            try:
                results = self.get_custom_scanner_results(scanner_key)
                all_results[scanner_key] = results
            except Exception as e:
                logger.warning(f"Failed to get results from {scanner_key}: {e}")
                all_results[scanner_key] = []
        
        return all_results
    
    def _parse_screener_table(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse the Finviz screener results table"""
        results = []
        
        # Find the main results table
        table = soup.find('table', {'class': 'table-light'})
        if not table:
            # Try alternative table selectors
            table = soup.find('table')
            if not table:
                logger.warning("Could not find results table")
                return results
        
        # Find all data rows (skip header)
        rows = table.find_all('tr')[1:] if table.find_all('tr') else []
        
        for row in rows:
            try:
                cells = row.find_all('td')
                if len(cells) < 11:  # Ensure we have enough columns
                    continue
                
                # Extract data from each cell
                stock_data = {
                    'rank': self._safe_text(cells[0]),
                    'symbol': self._safe_text(cells[1]),
                    'company': self._safe_text(cells[2]),
                    'sector': self._safe_text(cells[3]),
                    'industry': self._safe_text(cells[4]),
                    'country': self._safe_text(cells[5]),
                    'market_cap': self._parse_market_cap(self._safe_text(cells[6])),
                    'pe_ratio': self._safe_float(self._safe_text(cells[7])),
                    'price': self._safe_float(self._safe_text(cells[8])),
                    'change_percent': self._parse_percentage(self._safe_text(cells[9])),
                    'volume': self._parse_volume(self._safe_text(cells[10])),
                    'timestamp': datetime.now()
                }
                
                # Only add if we have essential data
                if stock_data['symbol'] and stock_data['price'] > 0:
                    results.append(stock_data)
                    
            except Exception as e:
                logger.warning(f"Error parsing table row: {e}")
                continue
        
        return results
    
    def _safe_text(self, element) -> str:
        """Safely extract text from BeautifulSoup element"""
        if element is None:
            return ""
        
        # Handle both direct text and links
        if element.find('a'):
            return element.find('a').get_text().strip()
        else:
            return element.get_text().strip()
    
    def _safe_float(self, value: str) -> float:
        """Safely convert string to float"""
        try:
            if value == '-' or value == '' or value.lower() == 'n/a':
                return 0.0
            # Remove common formatting
            clean_value = value.replace('%', '').replace(',', '').replace('$', '')
            return float(clean_value)
        except (ValueError, AttributeError):
            return 0.0
    
    def _parse_percentage(self, value: str) -> float:
        """Parse percentage value"""
        try:
            clean_value = value.replace('%', '').replace(',', '')
            return float(clean_value)
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
                return float(value) if value and value != '-' else 0.0
        except (ValueError, AttributeError):
            return 0.0
    
    def add_custom_scanner(self, key: str, name: str, url: str, description: str = ""):
        """
        Add a new custom scanner configuration
        
        Args:
            key: Unique identifier for the scanner
            name: Display name of the scanner
            url: Finviz URL (relative to base_url)
            description: Optional description
        """
        self.custom_scanners[key] = {
            'name': name,
            'url': url,
            'description': description
        }
        logger.info(f"Added custom scanner: {name}")
    
    def get_scanner_info(self) -> Dict[str, Dict[str, str]]:
        """Get information about all available custom scanners"""
        return self.custom_scanners.copy()
    
    def validate_scanner_access(self) -> Dict[str, bool]:
        """
        Test access to all custom scanners
        
        Returns:
            Dictionary mapping scanner keys to access status
        """
        access_status = {}
        
        for scanner_key, scanner_info in self.custom_scanners.items():
            try:
                url = f"{self.base_url}/{scanner_info['url']}"
                response = self.session.get(url, timeout=10)
                access_status[scanner_key] = response.status_code == 200
            except Exception:
                access_status[scanner_key] = False
        
        return access_status
    
    def get_ross_cameron_candidates(self) -> List[Dict[str, Any]]:
        """
        Get the best Ross Cameron candidates from custom scanners
        
        Returns:
            List of stocks that are strong Ross Cameron candidates
        """
        try:
            # Get results from the up 20% scanner (best for Ross Cameron style)
            candidates = self.get_up_20_percent_scanner()
            
            # Filter for Ross Cameron criteria
            filtered_candidates = []
            
            for stock in candidates:
                # Basic filtering criteria
                if (stock['price'] >= 2.0 and stock['price'] <= 20.0 and  # Price range
                    stock['change_percent'] >= 20.0 and  # Strong momentum
                    stock['volume'] > 100000):  # Decent volume
                    
                    # Add Ross Cameron score
                    stock['ross_cameron_score'] = self._calculate_preliminary_score(stock)
                    filtered_candidates.append(stock)
            
            # Sort by change percentage (highest first)
            filtered_candidates.sort(key=lambda x: x['change_percent'], reverse=True)
            
            logger.info(f"Found {len(filtered_candidates)} Ross Cameron candidates")
            return filtered_candidates
            
        except Exception as e:
            logger.error(f"Error getting Ross Cameron candidates: {e}")
            return []
    
    def _calculate_preliminary_score(self, stock: Dict[str, Any]) -> float:
        """Calculate a preliminary Ross Cameron score based on available data"""
        score = 0.0
        
        # Price range score (prefer $3-15 range)
        if 3.0 <= stock['price'] <= 15.0:
            score += 20
        elif 2.0 <= stock['price'] <= 20.0:
            score += 15
        
        # Change percentage score
        change = stock['change_percent']
        if change >= 50:
            score += 25
        elif change >= 30:
            score += 20
        elif change >= 20:
            score += 15
        
        # Volume score (higher is better)
        volume = stock['volume']
        if volume >= 10000000:  # 10M+
            score += 20
        elif volume >= 5000000:  # 5M+
            score += 15
        elif volume >= 1000000:  # 1M+
            score += 10
        
        # Market cap score (prefer smaller caps)
        market_cap = stock['market_cap']
        if market_cap <= 100000000:  # Under 100M
            score += 15
        elif market_cap <= 500000000:  # Under 500M
            score += 10
        elif market_cap <= 2000000000:  # Under 2B
            score += 5
        
        # Sector bonus (prefer high-momentum sectors)
        sector = stock['sector'].lower()
        if any(keyword in sector for keyword in ['healthcare', 'technology', 'biotech', 'communication']):
            score += 10
        
        return min(score, 100)  # Cap at 100

