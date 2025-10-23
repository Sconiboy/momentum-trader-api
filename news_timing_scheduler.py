"""
News Timing Scheduler - Automated screening based on news release patterns
Implements Ross Cameron's strategy of checking 1-2 minutes after each hour
when news typically drops (4 AM - 10 AM EST)
"""
import schedule
import time
from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Optional, Callable, Any
import threading
from dataclasses import dataclass

from ..core.logger import get_logger
from ..core.exceptions import MomentumTraderError

logger = get_logger(__name__)

@dataclass
class NewsCheckSchedule:
    """Configuration for news checking schedule"""
    start_hour: int = 4  # 4 AM EST
    end_hour: int = 10   # 10 AM EST
    check_delay_minutes: int = 1  # Check 1 minute after the hour
    timezone: str = "US/Eastern"
    enabled: bool = True
    
    def get_check_times(self) -> List[str]:
        """Get list of scheduled check times"""
        times = []
        for hour in range(self.start_hour, self.end_hour + 1):
            check_time = f"{hour:02d}:{self.check_delay_minutes:02d}"
            times.append(check_time)
        return times

class NewsTimingScheduler:
    """Schedules automated screening based on news release timing patterns"""
    
    def __init__(self, config, screening_engine, data_manager):
        self.config = config
        self.screening_engine = screening_engine
        self.data_manager = data_manager
        
        # Schedule configuration
        self.schedule_config = NewsCheckSchedule()
        
        # Timezone setup
        self.eastern_tz = pytz.timezone(self.schedule_config.timezone)
        
        # Tracking
        self.is_running = False
        self.scheduler_thread = None
        self.last_check_results = {}
        self.check_history = []
        
        # Callbacks for different events
        self.callbacks = {
            'news_detected': [],
            'high_volume_detected': [],
            'new_gapper_detected': [],
            'screening_complete': []
        }
        
        logger.info("News Timing Scheduler initialized")
    
    def start_scheduler(self):
        """Start the automated news timing scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        try:
            # Clear any existing schedule
            schedule.clear()
            
            # Set up hourly checks
            self._setup_hourly_checks()
            
            # Start the scheduler in a separate thread
            self.is_running = True
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            
            logger.info(f"News timing scheduler started - checking at: {', '.join(self.schedule_config.get_check_times())}")
            
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            self.is_running = False
            raise MomentumTraderError(f"Failed to start scheduler: {e}")
    
    def stop_scheduler(self):
        """Stop the automated scheduler"""
        self.is_running = False
        schedule.clear()
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        logger.info("News timing scheduler stopped")
    
    def _setup_hourly_checks(self):
        """Set up scheduled checks for each hour"""
        for hour in range(self.schedule_config.start_hour, self.schedule_config.end_hour + 1):
            check_time = f"{hour:02d}:{self.schedule_config.check_delay_minutes:02d}"
            
            # Schedule the check
            schedule.every().day.at(check_time).do(
                self._perform_scheduled_check,
                hour=hour,
                check_time=check_time
            )
            
            logger.info(f"Scheduled news check at {check_time} EST")
    
    def _run_scheduler(self):
        """Main scheduler loop"""
        logger.info("Scheduler thread started")
        
        while self.is_running:
            try:
                # Check if we're in market hours (extended hours for news)
                if self._is_news_hours():
                    schedule.run_pending()
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _is_news_hours(self) -> bool:
        """Check if we're currently in news monitoring hours"""
        now = datetime.now(self.eastern_tz)
        current_hour = now.hour
        
        # Check if it's a weekday and within news hours
        is_weekday = now.weekday() < 5  # Monday = 0, Friday = 4
        is_news_time = self.schedule_config.start_hour <= current_hour <= self.schedule_config.end_hour
        
        return is_weekday and is_news_time and self.schedule_config.enabled
    
    def _perform_scheduled_check(self, hour: int, check_time: str):
        """Perform the scheduled news and momentum check"""
        try:
            logger.info(f"🔍 Performing scheduled check at {check_time} EST (Hour {hour})")
            
            check_start_time = datetime.now()
            
            # 1. Quick scan for new high-volume movers
            volume_movers = self._scan_volume_movers()
            
            # 2. Check for new gappers since last scan
            new_gappers = self._scan_new_gappers()
            
            # 3. Scan custom Finviz scanner for fresh candidates
            custom_scanner_results = self._scan_custom_finviz()
            
            # 4. Check for fresh news on existing watchlist
            news_updates = self._check_watchlist_news()
            
            # 5. Run full Ross Cameron screening on new candidates
            ross_candidates = self._screen_ross_candidates(
                volume_movers + new_gappers + custom_scanner_results
            )
            
            # Compile results
            check_results = {
                'timestamp': check_start_time,
                'hour': hour,
                'check_time': check_time,
                'volume_movers': volume_movers,
                'new_gappers': new_gappers,
                'custom_scanner_results': custom_scanner_results,
                'news_updates': news_updates,
                'ross_candidates': ross_candidates,
                'total_candidates': len(ross_candidates),
                'processing_time': (datetime.now() - check_start_time).total_seconds()
            }
            
            # Store results
            self.last_check_results = check_results
            self.check_history.append(check_results)
            
            # Trigger callbacks for significant findings
            self._trigger_callbacks(check_results)
            
            # Log summary
            self._log_check_summary(check_results)
            
        except Exception as e:
            logger.error(f"Error in scheduled check at {check_time}: {e}")
    
    def _scan_volume_movers(self) -> List[Dict[str, Any]]:
        """Scan for stocks with unusual volume activity"""
        try:
            # Get market movers data
            movers = self.data_manager.get_market_movers()
            
            # Filter for high relative volume
            volume_movers = []
            for stock in movers.get('most_active', []):
                if (stock.get('relative_volume', 0) >= 3.0 and 
                    stock.get('price', 0) >= 2.0 and 
                    stock.get('price', 0) <= 20.0):
                    volume_movers.append({
                        'symbol': stock['symbol'],
                        'price': stock['price'],
                        'volume': stock.get('volume', 0),
                        'relative_volume': stock.get('relative_volume', 0),
                        'change_percent': stock.get('change_percent', 0),
                        'detection_type': 'volume_mover'
                    })
            
            return volume_movers[:10]  # Top 10
            
        except Exception as e:
            logger.warning(f"Error scanning volume movers: {e}")
            return []
    
    def _scan_new_gappers(self) -> List[Dict[str, Any]]:
        """Scan for new stocks gapping up/down"""
        try:
            # Get top gainers (potential gap ups)
            movers = self.data_manager.get_market_movers()
            
            new_gappers = []
            for stock in movers.get('top_gainers', []):
                change_pct = stock.get('change_percent', 0)
                if (abs(change_pct) >= 10.0 and  # Significant gap
                    stock.get('price', 0) >= 2.0 and 
                    stock.get('price', 0) <= 20.0):
                    new_gappers.append({
                        'symbol': stock['symbol'],
                        'price': stock['price'],
                        'change_percent': change_pct,
                        'volume': stock.get('volume', 0),
                        'gap_direction': 'up' if change_pct > 0 else 'down',
                        'detection_type': 'new_gapper'
                    })
            
            return new_gappers[:15]  # Top 15
            
        except Exception as e:
            logger.warning(f"Error scanning new gappers: {e}")
            return []
    
    def _scan_custom_finviz(self) -> List[Dict[str, Any]]:
        """Scan the custom Finviz scanner for fresh candidates"""
        try:
            from .finviz_custom_scanner import FinvizCustomScanner
            
            custom_scanner = FinvizCustomScanner()
            candidates = custom_scanner.get_ross_cameron_candidates()
            
            # Add detection type
            for candidate in candidates:
                candidate['detection_type'] = 'custom_scanner'
            
            return candidates[:20]  # Top 20
            
        except Exception as e:
            logger.warning(f"Error scanning custom Finviz: {e}")
            return []
    
    def _check_watchlist_news(self) -> List[Dict[str, Any]]:
        """Check for fresh news on watchlist stocks"""
        try:
            # Get current watchlist (would be stored in database)
            watchlist = self._get_current_watchlist()
            
            news_updates = []
            for symbol in watchlist:
                try:
                    news_items = self.data_manager.get_news_for_symbol(symbol)
                    
                    # Check for news in the last hour
                    recent_news = [
                        news for news in news_items 
                        if self._is_recent_news(news, hours=1)
                    ]
                    
                    if recent_news:
                        news_updates.append({
                            'symbol': symbol,
                            'news_count': len(recent_news),
                            'latest_headline': recent_news[0].get('headline', ''),
                            'detection_type': 'news_update'
                        })
                        
                except Exception as e:
                    logger.warning(f"Error checking news for {symbol}: {e}")
                    continue
            
            return news_updates
            
        except Exception as e:
            logger.warning(f"Error checking watchlist news: {e}")
            return []
    
    def _screen_ross_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run full Ross Cameron screening on candidates"""
        try:
            if not candidates:
                return []
            
            # Extract unique symbols
            symbols = list(set([c['symbol'] for c in candidates if c.get('symbol')]))
            
            # Get comprehensive data for each symbol
            ross_candidates = []
            for symbol in symbols[:25]:  # Limit to avoid rate limits
                try:
                    stock_data = self.data_manager.get_comprehensive_stock_data(symbol)
                    
                    # Validate against Ross Cameron criteria
                    from .criteria_validator import CriteriaValidator
                    validator = CriteriaValidator(self.config)
                    
                    validation_result = validator.validate_stock(stock_data)
                    
                    if validation_result.passed or validation_result.score >= 70:
                        candidate_info = {
                            'symbol': symbol,
                            'validation_result': validation_result,
                            'stock_data': stock_data,
                            'detection_sources': [c['detection_type'] for c in candidates if c['symbol'] == symbol]
                        }
                        ross_candidates.append(candidate_info)
                        
                except Exception as e:
                    logger.warning(f"Error screening candidate {symbol}: {e}")
                    continue
            
            # Sort by score
            ross_candidates.sort(key=lambda x: x['validation_result'].score, reverse=True)
            
            return ross_candidates
            
        except Exception as e:
            logger.warning(f"Error screening Ross candidates: {e}")
            return []
    
    def _get_current_watchlist(self) -> List[str]:
        """Get current watchlist symbols"""
        # This would typically come from database
        # For now, return some common momentum stocks
        return ['GITS', 'TSLA', 'NVDA', 'AMD', 'MRNA', 'BNTX', 'SPCE']
    
    def _is_recent_news(self, news_item: Dict[str, Any], hours: int = 1) -> bool:
        """Check if news item is recent"""
        try:
            # This would need to parse the news timestamp
            # For now, assume all news from current scan is recent
            return True
        except Exception:
            return False
    
    def _trigger_callbacks(self, check_results: Dict[str, Any]):
        """Trigger appropriate callbacks based on check results"""
        try:
            # News detected callback
            if check_results['news_updates']:
                for callback in self.callbacks['news_detected']:
                    callback(check_results['news_updates'])
            
            # High volume detected callback
            if check_results['volume_movers']:
                for callback in self.callbacks['high_volume_detected']:
                    callback(check_results['volume_movers'])
            
            # New gapper detected callback
            if check_results['new_gappers']:
                for callback in self.callbacks['new_gapper_detected']:
                    callback(check_results['new_gappers'])
            
            # Screening complete callback
            for callback in self.callbacks['screening_complete']:
                callback(check_results)
                
        except Exception as e:
            logger.warning(f"Error triggering callbacks: {e}")
    
    def _log_check_summary(self, check_results: Dict[str, Any]):
        """Log a summary of the check results"""
        summary = (
            f"📊 Check Summary ({check_results['check_time']} EST):\n"
            f"   • Volume Movers: {len(check_results['volume_movers'])}\n"
            f"   • New Gappers: {len(check_results['new_gappers'])}\n"
            f"   • Custom Scanner: {len(check_results['custom_scanner_results'])}\n"
            f"   • News Updates: {len(check_results['news_updates'])}\n"
            f"   • Ross Candidates: {len(check_results['ross_candidates'])}\n"
            f"   • Processing Time: {check_results['processing_time']:.1f}s"
        )
        
        if check_results['ross_candidates']:
            summary += f"\n   🎯 Top Candidate: {check_results['ross_candidates'][0]['symbol']} (Score: {check_results['ross_candidates'][0]['validation_result'].score:.0f})"
        
        logger.info(summary)
    
    def add_callback(self, event_type: str, callback: Callable):
        """Add a callback for specific events"""
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
            logger.info(f"Added callback for {event_type}")
        else:
            raise ValueError(f"Unknown event type: {event_type}")
    
    def get_schedule_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        return {
            'is_running': self.is_running,
            'schedule_config': self.schedule_config,
            'next_check_times': self.schedule_config.get_check_times(),
            'is_news_hours': self._is_news_hours(),
            'last_check': self.last_check_results.get('timestamp'),
            'total_checks_today': len([c for c in self.check_history if c['timestamp'].date() == datetime.now().date()]),
            'current_eastern_time': datetime.now(self.eastern_tz).strftime('%Y-%m-%d %H:%M:%S %Z')
        }
    
    def get_check_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent check history"""
        return self.check_history[-limit:] if self.check_history else []
    
    def manual_check(self) -> Dict[str, Any]:
        """Perform a manual check outside of schedule"""
        logger.info("🔍 Performing manual news timing check")
        
        current_hour = datetime.now(self.eastern_tz).hour
        check_time = datetime.now(self.eastern_tz).strftime('%H:%M')
        
        self._perform_scheduled_check(current_hour, check_time)
        
        return self.last_check_results
    
    def update_schedule_config(self, **kwargs):
        """Update schedule configuration"""
        for key, value in kwargs.items():
            if hasattr(self.schedule_config, key):
                setattr(self.schedule_config, key, value)
                logger.info(f"Updated schedule config: {key} = {value}")
        
        # Restart scheduler if running
        if self.is_running:
            self.stop_scheduler()
            self.start_scheduler()

