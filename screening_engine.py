"""
Main Screening Engine - Coordinates all screening modules and strategies
Implements Ross Cameron's methodology with automated timing and validation
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import asyncio
from dataclasses import dataclass
import json

from ..core.logger import get_logger
from ..core.exceptions import MomentumTraderError
from ..core.database import DatabaseManager
from ..data.data_manager import DataManager, StockData
from .criteria_validator import CriteriaValidator, ValidationResult
from .finviz_custom_scanner import FinvizCustomScanner
from .news_timing_scheduler import NewsTimingScheduler

logger = get_logger(__name__)

@dataclass
class ScreeningResults:
    """Results from a screening session"""
    timestamp: datetime
    total_candidates: int
    passed_candidates: int
    top_candidates: List[Dict[str, Any]]
    screening_time: float
    data_sources: List[str]
    criteria_summary: Dict[str, int]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'total_candidates': self.total_candidates,
            'passed_candidates': self.passed_candidates,
            'top_candidates': self.top_candidates,
            'screening_time': self.screening_time,
            'data_sources': self.data_sources,
            'criteria_summary': self.criteria_summary
        }

class ScreeningEngine:
    """Main engine for stock screening using Ross Cameron methodology"""
    
    def __init__(self, config, db_manager: DatabaseManager, data_manager: DataManager):
        self.config = config
        self.db_manager = db_manager
        self.data_manager = data_manager
        
        # Initialize screening components
        self.criteria_validator = CriteriaValidator(config)
        self.finviz_scanner = FinvizCustomScanner()
        
        # News timing scheduler (initialized but not started by default)
        self.news_scheduler = NewsTimingScheduler(config, self, data_manager)
        
        # Screening state
        self.last_screening_results = None
        self.screening_history = []
        self.watchlist = set()
        
        # Performance tracking
        self.screening_stats = {
            'total_screenings': 0,
            'total_candidates_processed': 0,
            'total_candidates_passed': 0,
            'average_screening_time': 0.0,
            'best_score_today': 0.0,
            'best_candidate_today': None
        }
        
        logger.info("Screening Engine initialized")
    
    def run_full_screening(self, 
                          include_custom_scanner: bool = True,
                          include_market_movers: bool = True,
                          include_watchlist: bool = True,
                          max_candidates: int = 50) -> ScreeningResults:
        """
        Run a comprehensive screening session
        
        Args:
            include_custom_scanner: Include custom Finviz scanner results
            include_market_movers: Include market movers from data sources
            include_watchlist: Include current watchlist stocks
            max_candidates: Maximum number of candidates to process
            
        Returns:
            ScreeningResults with detailed findings
        """
        try:
            start_time = datetime.now()
            logger.info("🔍 Starting full Ross Cameron screening session")
            
            # Collect candidates from various sources
            all_candidates = []
            data_sources = []
            
            # 1. Custom Finviz Scanner
            if include_custom_scanner:
                try:
                    custom_candidates = self.finviz_scanner.get_ross_cameron_candidates()
                    all_candidates.extend(custom_candidates)
                    data_sources.append('finviz_custom_scanner')
                    logger.info(f"Added {len(custom_candidates)} candidates from custom Finviz scanner")
                except Exception as e:
                    logger.warning(f"Error getting custom scanner results: {e}")
            
            # 2. Market Movers
            if include_market_movers:
                try:
                    movers = self.data_manager.get_market_movers()
                    
                    # Process top gainers
                    for stock in movers.get('top_gainers', [])[:20]:
                        if self._is_valid_candidate(stock):
                            all_candidates.append({
                                'symbol': stock['symbol'],
                                'source': 'market_movers_gainers',
                                'initial_data': stock
                            })
                    
                    # Process most active
                    for stock in movers.get('most_active', [])[:15]:
                        if self._is_valid_candidate(stock):
                            all_candidates.append({
                                'symbol': stock['symbol'],
                                'source': 'market_movers_active',
                                'initial_data': stock
                            })
                    
                    data_sources.append('market_movers')
                    logger.info(f"Added market movers candidates")
                    
                except Exception as e:
                    logger.warning(f"Error getting market movers: {e}")
            
            # 3. Watchlist
            if include_watchlist and self.watchlist:
                for symbol in self.watchlist:
                    all_candidates.append({
                        'symbol': symbol,
                        'source': 'watchlist',
                        'initial_data': {}
                    })
                data_sources.append('watchlist')
                logger.info(f"Added {len(self.watchlist)} watchlist candidates")
            
            # Remove duplicates and limit
            unique_symbols = {}
            for candidate in all_candidates:
                symbol = candidate['symbol']
                if symbol not in unique_symbols:
                    unique_symbols[symbol] = candidate
            
            candidates_to_process = list(unique_symbols.values())[:max_candidates]
            
            logger.info(f"Processing {len(candidates_to_process)} unique candidates")
            
            # Process each candidate through full validation
            validated_candidates = []
            criteria_summary = {
                'high_relative_volume': 0,
                'significant_price_change': 0,
                'low_float': 0,
                'news_catalyst': 0,
                'price_range': 0,
                'target_sector': 0
            }
            
            for i, candidate in enumerate(candidates_to_process):
                try:
                    symbol = candidate['symbol']
                    logger.debug(f"Processing candidate {i+1}/{len(candidates_to_process)}: {symbol}")
                    
                    # Get comprehensive stock data
                    stock_data = self.data_manager.get_comprehensive_stock_data(symbol)
                    
                    # Get news for catalyst validation
                    news_items = self.data_manager.get_news_for_symbol(symbol)
                    
                    # Validate against Ross Cameron criteria
                    validation_result = self.criteria_validator.validate_stock(stock_data, news_items)
                    
                    # Update criteria summary
                    for criterion, passed in validation_result.criteria_results.items():
                        if criterion in criteria_summary and passed:
                            criteria_summary[criterion] += 1
                    
                    # Add to results if meets minimum threshold
                    if validation_result.score >= 50:  # Minimum score threshold
                        candidate_info = {
                            'symbol': symbol,
                            'score': validation_result.score,
                            'passed': validation_result.passed,
                            'validation_result': validation_result,
                            'stock_data': stock_data,
                            'news_count': len(news_items),
                            'source': candidate['source'],
                            'rank': len(validated_candidates) + 1
                        }
                        validated_candidates.append(candidate_info)
                    
                except Exception as e:
                    logger.warning(f"Error processing candidate {candidate['symbol']}: {e}")
                    continue
            
            # Sort by score (highest first)
            validated_candidates.sort(key=lambda x: x['score'], reverse=True)
            
            # Update rankings
            for i, candidate in enumerate(validated_candidates):
                candidate['rank'] = i + 1
            
            # Calculate results
            screening_time = (datetime.now() - start_time).total_seconds()
            passed_candidates = len([c for c in validated_candidates if c['passed']])
            
            # Create results object
            results = ScreeningResults(
                timestamp=start_time,
                total_candidates=len(candidates_to_process),
                passed_candidates=passed_candidates,
                top_candidates=validated_candidates[:20],  # Top 20
                screening_time=screening_time,
                data_sources=data_sources,
                criteria_summary=criteria_summary
            )
            
            # Store results
            self.last_screening_results = results
            self.screening_history.append(results)
            
            # Update statistics
            self._update_screening_stats(results)
            
            # Save to database
            self._save_screening_results(results)
            
            # Log summary
            self._log_screening_summary(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in full screening: {e}")
            raise MomentumTraderError(f"Screening failed: {e}")
    
    def run_quick_screening(self, symbols: List[str]) -> List[ValidationResult]:
        """
        Run quick screening on specific symbols
        
        Args:
            symbols: List of stock symbols to screen
            
        Returns:
            List of ValidationResult objects
        """
        try:
            logger.info(f"🔍 Running quick screening on {len(symbols)} symbols")
            
            results = []
            for symbol in symbols:
                try:
                    # Get stock data
                    stock_data = self.data_manager.get_comprehensive_stock_data(symbol)
                    
                    # Get news
                    news_items = self.data_manager.get_news_for_symbol(symbol)
                    
                    # Validate
                    validation_result = self.criteria_validator.validate_stock(stock_data, news_items)
                    results.append(validation_result)
                    
                except Exception as e:
                    logger.warning(f"Error in quick screening for {symbol}: {e}")
                    continue
            
            # Sort by score
            results.sort(key=lambda x: x.score, reverse=True)
            
            logger.info(f"Quick screening completed: {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error in quick screening: {e}")
            return []
    
    def start_automated_screening(self):
        """Start automated screening with news timing"""
        try:
            # Set up callbacks for automated actions
            self.news_scheduler.add_callback('screening_complete', self._handle_automated_screening_complete)
            self.news_scheduler.add_callback('high_volume_detected', self._handle_high_volume_alert)
            self.news_scheduler.add_callback('new_gapper_detected', self._handle_new_gapper_alert)
            
            # Start the scheduler
            self.news_scheduler.start_scheduler()
            
            logger.info("🤖 Automated screening started with news timing")
            
        except Exception as e:
            logger.error(f"Error starting automated screening: {e}")
            raise MomentumTraderError(f"Failed to start automated screening: {e}")
    
    def stop_automated_screening(self):
        """Stop automated screening"""
        self.news_scheduler.stop_scheduler()
        logger.info("🛑 Automated screening stopped")
    
    def add_to_watchlist(self, symbol: str):
        """Add symbol to watchlist"""
        self.watchlist.add(symbol.upper())
        logger.info(f"Added {symbol} to watchlist")
    
    def remove_from_watchlist(self, symbol: str):
        """Remove symbol from watchlist"""
        self.watchlist.discard(symbol.upper())
        logger.info(f"Removed {symbol} from watchlist")
    
    def get_watchlist(self) -> List[str]:
        """Get current watchlist"""
        return list(self.watchlist)
    
    def get_top_candidates(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top candidates from last screening"""
        if not self.last_screening_results:
            return []
        
        return self.last_screening_results.top_candidates[:limit]
    
    def get_screening_stats(self) -> Dict[str, Any]:
        """Get screening performance statistics"""
        return self.screening_stats.copy()
    
    def get_screening_history(self, limit: int = 10) -> List[ScreeningResults]:
        """Get recent screening history"""
        return self.screening_history[-limit:] if self.screening_history else []
    
    def _is_valid_candidate(self, stock: Dict[str, Any]) -> bool:
        """Quick validation for initial candidate filtering"""
        try:
            price = stock.get('price', 0)
            volume = stock.get('volume', 0)
            
            # Basic filters
            return (2.0 <= price <= 20.0 and 
                   volume > 100000)
        except Exception:
            return False
    
    def _handle_automated_screening_complete(self, check_results: Dict[str, Any]):
        """Handle completion of automated screening"""
        try:
            candidates_count = len(check_results.get('ross_candidates', []))
            
            if candidates_count > 0:
                logger.info(f"🎯 Automated screening found {candidates_count} Ross Cameron candidates")
                
                # Update best candidate tracking
                top_candidate = check_results['ross_candidates'][0]
                score = top_candidate['validation_result'].score
                
                if score > self.screening_stats['best_score_today']:
                    self.screening_stats['best_score_today'] = score
                    self.screening_stats['best_candidate_today'] = top_candidate['symbol']
                    
                    logger.info(f"🏆 New best candidate today: {top_candidate['symbol']} (Score: {score:.0f})")
            
        except Exception as e:
            logger.warning(f"Error handling automated screening completion: {e}")
    
    def _handle_high_volume_alert(self, volume_movers: List[Dict[str, Any]]):
        """Handle high volume detection"""
        try:
            for mover in volume_movers:
                symbol = mover['symbol']
                rel_vol = mover['relative_volume']
                
                logger.info(f"🔊 High volume alert: {symbol} ({rel_vol:.1f}x relative volume)")
                
                # Auto-add to watchlist if very high volume
                if rel_vol >= 10.0:
                    self.add_to_watchlist(symbol)
                    
        except Exception as e:
            logger.warning(f"Error handling high volume alert: {e}")
    
    def _handle_new_gapper_alert(self, new_gappers: List[Dict[str, Any]]):
        """Handle new gapper detection"""
        try:
            for gapper in new_gappers:
                symbol = gapper['symbol']
                change_pct = gapper['change_percent']
                
                logger.info(f"📈 New gapper alert: {symbol} ({change_pct:+.1f}%)")
                
                # Auto-add significant gappers to watchlist
                if abs(change_pct) >= 25.0:
                    self.add_to_watchlist(symbol)
                    
        except Exception as e:
            logger.warning(f"Error handling new gapper alert: {e}")
    
    def _update_screening_stats(self, results: ScreeningResults):
        """Update screening performance statistics"""
        self.screening_stats['total_screenings'] += 1
        self.screening_stats['total_candidates_processed'] += results.total_candidates
        self.screening_stats['total_candidates_passed'] += results.passed_candidates
        
        # Update average screening time
        total_time = (self.screening_stats['average_screening_time'] * 
                     (self.screening_stats['total_screenings'] - 1) + 
                     results.screening_time)
        self.screening_stats['average_screening_time'] = total_time / self.screening_stats['total_screenings']
        
        # Update best score today
        if results.top_candidates:
            top_score = results.top_candidates[0]['score']
            if top_score > self.screening_stats['best_score_today']:
                self.screening_stats['best_score_today'] = top_score
                self.screening_stats['best_candidate_today'] = results.top_candidates[0]['symbol']
    
    def _save_screening_results(self, results: ScreeningResults):
        """Save screening results to database"""
        try:
            # Save screening session
            session_data = {
                'timestamp': results.timestamp,
                'total_candidates': results.total_candidates,
                'passed_candidates': results.passed_candidates,
                'screening_time': results.screening_time,
                'data_sources': ','.join(results.data_sources),
                'criteria_summary': json.dumps(results.criteria_summary)
            }
            
            # Save individual candidate results
            candidate_results = []
            for candidate in results.top_candidates:
                candidate_data = {
                    'symbol': candidate['symbol'],
                    'timestamp': results.timestamp,
                    'score': candidate['score'],
                    'passed': candidate['passed'],
                    'rank': candidate['rank'],
                    'source': candidate['source'],
                    'price': candidate['stock_data'].current_price,
                    'volume': candidate['stock_data'].volume,
                    'relative_volume': candidate['stock_data'].relative_volume,
                    'float_shares': candidate['stock_data'].float_shares,
                    'gap_percentage': candidate['stock_data'].gap_percentage,
                    'sector': candidate['stock_data'].sector,
                    'news_catalyst': candidate['news_count'] > 0
                }
                candidate_results.append(candidate_data)
            
            # Save to database
            self.db_manager.save_screening_results(candidate_results)
            
        except Exception as e:
            logger.warning(f"Error saving screening results to database: {e}")
    
    def _log_screening_summary(self, results: ScreeningResults):
        """Log a summary of screening results"""
        summary = (
            f"📊 Screening Summary ({results.timestamp.strftime('%H:%M:%S')}):\n"
            f"   • Total Candidates: {results.total_candidates}\n"
            f"   • Passed Criteria: {results.passed_candidates}\n"
            f"   • Top Score: {results.top_candidates[0]['score']:.0f if results.top_candidates else 0}\n"
            f"   • Processing Time: {results.screening_time:.1f}s\n"
            f"   • Data Sources: {', '.join(results.data_sources)}"
        )
        
        if results.top_candidates:
            top_3 = results.top_candidates[:3]
            summary += "\n   🏆 Top 3 Candidates:"
            for i, candidate in enumerate(top_3, 1):
                summary += f"\n      {i}. {candidate['symbol']} (Score: {candidate['score']:.0f})"
        
        logger.info(summary)
    
    def export_results(self, format: str = 'json') -> str:
        """Export last screening results"""
        if not self.last_screening_results:
            return ""
        
        if format.lower() == 'json':
            return json.dumps(self.last_screening_results.to_dict(), indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def get_engine_status(self) -> Dict[str, Any]:
        """Get current engine status"""
        return {
            'last_screening': self.last_screening_results.timestamp if self.last_screening_results else None,
            'total_screenings': len(self.screening_history),
            'watchlist_size': len(self.watchlist),
            'automated_screening_active': self.news_scheduler.is_running,
            'screening_stats': self.screening_stats,
            'news_scheduler_status': self.news_scheduler.get_schedule_status()
        }

