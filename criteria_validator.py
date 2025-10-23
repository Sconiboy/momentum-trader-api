"""
Criteria Validator - Validates stocks against Ross Cameron's 5 pillars
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import re

from ..core.logger import get_logger
from ..data.data_manager import StockData

logger = get_logger(__name__)

@dataclass
class ValidationResult:
    """Result of criteria validation"""
    symbol: str
    passed: bool
    score: float
    criteria_results: Dict[str, bool]
    details: Dict[str, Any]
    timestamp: datetime
    
    def get_summary(self) -> str:
        """Get a human-readable summary"""
        passed_count = sum(self.criteria_results.values())
        total_count = len(self.criteria_results)
        
        status = "✅ PASSED" if self.passed else "❌ FAILED"
        return f"{self.symbol}: {status} ({passed_count}/{total_count} criteria, Score: {self.score:.0f})"

class CriteriaValidator:
    """Validates stocks against Ross Cameron's trading criteria"""
    
    def __init__(self, config):
        self.config = config
        logger.info("Criteria Validator initialized")
    
    def validate_stock(self, stock_data: StockData, news_items: List[Dict] = None) -> ValidationResult:
        """
        Validate a stock against all Ross Cameron criteria
        
        Args:
            stock_data: StockData object with stock information
            news_items: Optional list of news items for catalyst validation
            
        Returns:
            ValidationResult with detailed validation results
        """
        try:
            criteria_results = {}
            details = {}
            
            # 1. High Relative Volume (Pillar 1)
            volume_result, volume_details = self._validate_relative_volume(stock_data)
            criteria_results['high_relative_volume'] = volume_result
            details['volume'] = volume_details
            
            # 2. Significant Price Change (Pillar 2) 
            price_change_result, price_change_details = self._validate_price_change(stock_data)
            criteria_results['significant_price_change'] = price_change_result
            details['price_change'] = price_change_details
            
            # 3. Low Float (Pillar 3)
            float_result, float_details = self._validate_float(stock_data)
            criteria_results['low_float'] = float_result
            details['float'] = float_details
            
            # 4. News Catalyst (Pillar 4)
            catalyst_result, catalyst_details = self._validate_news_catalyst(stock_data, news_items)
            criteria_results['news_catalyst'] = catalyst_result
            details['catalyst'] = catalyst_details
            
            # 5. Price Under $20 (Modified from Ross's $10 to our $2-20 range)
            price_range_result, price_range_details = self._validate_price_range(stock_data)
            criteria_results['price_range'] = price_range_result
            details['price_range'] = price_range_details
            
            # Additional criteria for enhanced filtering
            sector_result, sector_details = self._validate_target_sector(stock_data)
            criteria_results['target_sector'] = sector_result
            details['sector'] = sector_details
            
            # Calculate overall score
            score = self._calculate_score(criteria_results, details, stock_data)
            
            # Determine if stock passes (need at least 4 of 5 core pillars)
            core_pillars = ['high_relative_volume', 'significant_price_change', 'low_float', 'news_catalyst', 'price_range']
            core_passed = sum(criteria_results[pillar] for pillar in core_pillars)
            passed = core_passed >= 4
            
            result = ValidationResult(
                symbol=stock_data.symbol,
                passed=passed,
                score=score,
                criteria_results=criteria_results,
                details=details,
                timestamp=datetime.now()
            )
            
            logger.info(f"Validated {stock_data.symbol}: {result.get_summary()}")
            return result
            
        except Exception as e:
            logger.error(f"Error validating {stock_data.symbol}: {e}")
            # Return failed result
            return ValidationResult(
                symbol=stock_data.symbol,
                passed=False,
                score=0.0,
                criteria_results={},
                details={'error': str(e)},
                timestamp=datetime.now()
            )
    
    def _validate_relative_volume(self, stock_data: StockData) -> Tuple[bool, Dict[str, Any]]:
        """Validate relative volume (Pillar 1)"""
        min_relative_volume = self.config.trading.MIN_RELATIVE_VOLUME
        preferred_relative_volume = self.config.trading.PREFERRED_RELATIVE_VOLUME
        
        relative_volume = stock_data.relative_volume
        
        # Basic requirement: 2x+ relative volume
        passed = relative_volume >= min_relative_volume
        
        details = {
            'relative_volume': relative_volume,
            'min_required': min_relative_volume,
            'preferred': preferred_relative_volume,
            'actual_volume': stock_data.volume,
            'avg_volume': stock_data.avg_volume,
            'is_preferred': relative_volume >= preferred_relative_volume
        }
        
        return passed, details
    
    def _validate_price_change(self, stock_data: StockData) -> Tuple[bool, Dict[str, Any]]:
        """Validate significant price change (Pillar 2)"""
        min_gap = self.config.trading.MIN_GAP_PERCENTAGE
        
        gap_percentage = abs(stock_data.gap_percentage)
        
        # Basic requirement: 4%+ gap
        passed = gap_percentage >= min_gap
        
        details = {
            'gap_percentage': stock_data.gap_percentage,
            'abs_gap_percentage': gap_percentage,
            'min_required': min_gap,
            'current_price': stock_data.current_price,
            'is_gapper': gap_percentage >= min_gap,
            'gap_direction': 'up' if stock_data.gap_percentage > 0 else 'down'
        }
        
        return passed, details
    
    def _validate_float(self, stock_data: StockData) -> Tuple[bool, Dict[str, Any]]:
        """Validate low float (Pillar 3)"""
        max_float = self.config.trading.MAX_FLOAT
        preferred_max_float = self.config.trading.PREFERRED_MAX_FLOAT
        
        float_shares = stock_data.float_shares
        
        # Basic requirement: under 30M shares
        passed = 0 < float_shares <= max_float
        
        details = {
            'float_shares': float_shares,
            'max_allowed': max_float,
            'preferred_max': preferred_max_float,
            'is_preferred': 0 < float_shares <= preferred_max_float,
            'float_millions': float_shares / 1_000_000 if float_shares > 0 else 0
        }
        
        return passed, details
    
    def _validate_news_catalyst(self, stock_data: StockData, news_items: List[Dict] = None) -> Tuple[bool, Dict[str, Any]]:
        """Validate news catalyst (Pillar 4)"""
        
        # For now, we'll use heuristics based on volume and price movement
        # In Phase 5, we'll enhance this with actual news sentiment analysis
        
        # Strong volume + gap suggests news catalyst
        has_strong_volume = stock_data.relative_volume >= 5.0
        has_significant_gap = abs(stock_data.gap_percentage) >= 10.0
        
        # Heuristic: if both volume and gap are strong, likely has catalyst
        catalyst_likely = has_strong_volume and has_significant_gap
        
        # Check for news items if provided
        has_recent_news = False
        news_count = 0
        if news_items:
            news_count = len(news_items)
            has_recent_news = news_count > 0
        
        # Pass if either heuristic suggests catalyst OR we have recent news
        passed = catalyst_likely or has_recent_news
        
        details = {
            'has_strong_volume': has_strong_volume,
            'has_significant_gap': has_significant_gap,
            'catalyst_likely': catalyst_likely,
            'has_recent_news': has_recent_news,
            'news_count': news_count,
            'relative_volume': stock_data.relative_volume,
            'gap_percentage': stock_data.gap_percentage
        }
        
        return passed, details
    
    def _validate_price_range(self, stock_data: StockData) -> Tuple[bool, Dict[str, Any]]:
        """Validate price range (Modified Pillar 5)"""
        min_price = self.config.trading.MIN_PRICE
        max_price = self.config.trading.MAX_PRICE
        
        current_price = stock_data.current_price
        
        # Basic requirement: $2-20 range
        passed = min_price <= current_price <= max_price
        
        details = {
            'current_price': current_price,
            'min_price': min_price,
            'max_price': max_price,
            'in_range': passed,
            'sweet_spot': 3.0 <= current_price <= 15.0  # Sweet spot within range
        }
        
        return passed, details
    
    def _validate_target_sector(self, stock_data: StockData) -> Tuple[bool, Dict[str, Any]]:
        """Validate target sector (Additional criteria)"""
        target_sectors = self.config.trading.TARGET_SECTORS
        
        stock_sector = stock_data.sector.lower() if stock_data.sector else ''
        stock_industry = stock_data.industry.lower() if stock_data.industry else ''
        
        # Check if sector or industry matches any target
        sector_match = False
        matched_sectors = []
        
        for target in target_sectors:
            target_lower = target.lower()
            if (target_lower in stock_sector or 
                target_lower in stock_industry or
                stock_sector in target_lower or
                stock_industry in target_lower):
                sector_match = True
                matched_sectors.append(target)
        
        details = {
            'stock_sector': stock_data.sector,
            'stock_industry': stock_data.industry,
            'target_sectors': target_sectors,
            'matched_sectors': matched_sectors,
            'sector_match': sector_match
        }
        
        return sector_match, details
    
    def _calculate_score(self, criteria_results: Dict[str, bool], details: Dict[str, Any], stock_data: StockData) -> float:
        """Calculate overall score for the stock"""
        
        # Base score from criteria (10 points each)
        base_score = sum(criteria_results.values()) * 10
        
        # Bonus points for exceptional characteristics
        bonus_score = 0
        
        # Float bonus
        if details['float']['is_preferred']:
            bonus_score += 15
        elif details['float']['float_shares'] <= self.config.trading.MAX_FLOAT:
            bonus_score += 10
        
        # Volume bonus
        if details['volume']['is_preferred']:
            bonus_score += 15
        elif details['volume']['relative_volume'] >= self.config.trading.MIN_RELATIVE_VOLUME:
            bonus_score += 10
        
        # Gap bonus
        gap_pct = abs(details['price_change']['gap_percentage'])
        if gap_pct >= 20:
            bonus_score += 15
        elif gap_pct >= 10:
            bonus_score += 10
        elif gap_pct >= self.config.trading.MIN_GAP_PERCENTAGE:
            bonus_score += 5
        
        # Price range bonus
        if details['price_range']['sweet_spot']:
            bonus_score += 5
        
        # Sector bonus
        if details['sector']['sector_match']:
            bonus_score += 10
        
        # Catalyst strength bonus
        if details['catalyst']['catalyst_likely']:
            bonus_score += 10
        
        # Volume magnitude bonus
        if stock_data.volume > stock_data.avg_volume * 10:
            bonus_score += 5
        
        total_score = min(base_score + bonus_score, 100)  # Cap at 100
        return total_score
    
    def validate_multiple_stocks(self, stocks_data: List[StockData], news_data: Dict[str, List[Dict]] = None) -> List[ValidationResult]:
        """
        Validate multiple stocks
        
        Args:
            stocks_data: List of StockData objects
            news_data: Optional dictionary mapping symbols to news items
            
        Returns:
            List of ValidationResult objects
        """
        results = []
        
        for stock_data in stocks_data:
            try:
                news_items = news_data.get(stock_data.symbol, []) if news_data else None
                result = self.validate_stock(stock_data, news_items)
                results.append(result)
            except Exception as e:
                logger.error(f"Error validating {stock_data.symbol}: {e}")
                continue
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x.score, reverse=True)
        
        logger.info(f"Validated {len(results)} stocks")
        return results
    
    def get_criteria_summary(self) -> Dict[str, Any]:
        """Get summary of all validation criteria"""
        return {
            'ross_cameron_pillars': {
                '1_high_relative_volume': {
                    'description': 'Volume significantly above average',
                    'minimum': f"{self.config.trading.MIN_RELATIVE_VOLUME}x average",
                    'preferred': f"{self.config.trading.PREFERRED_RELATIVE_VOLUME}x average"
                },
                '2_significant_price_change': {
                    'description': 'Large gap up or down from previous close',
                    'minimum': f"{self.config.trading.MIN_GAP_PERCENTAGE}% gap",
                    'preferred': "10%+ gap"
                },
                '3_low_float': {
                    'description': 'Limited shares available for trading',
                    'maximum': f"{self.config.trading.MAX_FLOAT:,} shares",
                    'preferred': f"{self.config.trading.PREFERRED_MAX_FLOAT:,} shares"
                },
                '4_news_catalyst': {
                    'description': 'Recent news driving price movement',
                    'detection': 'High volume + gap or recent news items'
                },
                '5_price_range': {
                    'description': 'Affordable price range for momentum trading',
                    'range': f"${self.config.trading.MIN_PRICE}-${self.config.trading.MAX_PRICE}",
                    'sweet_spot': "$3-$15"
                }
            },
            'additional_criteria': {
                'target_sectors': {
                    'description': 'Focus sectors with high momentum potential',
                    'sectors': self.config.trading.TARGET_SECTORS
                }
            },
            'scoring': {
                'base_points': '10 points per criteria met',
                'bonus_points': 'Up to 15 bonus points for exceptional characteristics',
                'maximum_score': 100,
                'passing_threshold': '4 of 5 core pillars must pass'
            }
        }

