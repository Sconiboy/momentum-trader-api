"""
Signal Generator - Main coordinator for generating trading signals
Combines all analysis components using Ross Cameron methodology
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..core.logger import get_logger
from .scoring_engine import ScoringEngine, CompositeScore, RossScore

logger = get_logger(__name__)

@dataclass
class TradingSignal:
    """Complete trading signal with all analysis"""
    symbol: str
    signal_id: str
    timestamp: datetime
    
    # Scores
    composite_score: CompositeScore
    ross_score: RossScore
    
    # Signal details
    signal_type: str  # 'buy', 'sell', 'hold'
    signal_strength: str  # 'weak', 'moderate', 'strong', 'very_strong'
    confidence: float  # 0-1
    
    # Trading details
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    position_size: Optional[float]
    risk_reward_ratio: Optional[float]
    
    # Timing
    time_horizon: str  # 'scalp', 'day_trade', 'swing', 'position'
    urgency: str  # 'immediate', 'high', 'medium', 'low'
    expiry_time: Optional[datetime]
    
    # Analysis breakdown
    fundamental_analysis: Dict
    technical_analysis: Dict
    news_analysis: Dict
    market_data: Dict
    
    # Alerts and notes
    alerts: List[str]
    notes: str
    risk_warnings: List[str]

@dataclass
class SignalSummary:
    """Summary of multiple signals"""
    total_signals: int
    strong_buy_signals: int
    buy_signals: int
    hold_signals: int
    sell_signals: int
    avg_confidence: float
    top_signals: List[TradingSignal]
    risk_distribution: Dict[str, int]

class SignalGenerator:
    """Main signal generation engine"""
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Initialize scoring engine
        self.scoring_engine = ScoringEngine(config)
        
        # Signal thresholds
        self.signal_thresholds = {
            'strong_buy': 80,
            'buy': 65,
            'hold': 45,
            'sell': 30,
            'strong_sell': 0
        }
        
        # Risk limits
        self.risk_limits = {
            'max_position_risk': 0.02,  # 2% of portfolio per position
            'max_portfolio_risk': 0.06,  # 6% total portfolio risk
            'max_correlation': 0.7,     # Maximum correlation between positions
        }
        
        logger.info("Signal Generator initialized")
    
    def generate_signal(self, symbol: str,
                       fundamental_data: Dict,
                       technical_data: Dict,
                       news_data: Dict,
                       market_data: Dict,
                       portfolio_data: Optional[Dict] = None) -> TradingSignal:
        """
        Generate comprehensive trading signal for a symbol
        
        Args:
            symbol: Stock symbol
            fundamental_data: Fundamental analysis results
            technical_data: Technical analysis results
            news_data: News sentiment and catalyst data
            market_data: Current market data
            portfolio_data: Current portfolio information (optional)
            
        Returns:
            TradingSignal with complete analysis
        """
        try:
            logger.info(f"Generating signal for {symbol}")
            
            # Calculate composite score
            composite_score = self.scoring_engine.calculate_composite_score(
                symbol, fundamental_data, technical_data, news_data, market_data
            )
            
            # Calculate Ross Cameron score
            ross_score = self.scoring_engine.calculate_ross_cameron_score(
                symbol, fundamental_data, technical_data, news_data, market_data
            )
            
            # Determine signal type
            signal_type = self._determine_signal_type(composite_score.overall_score)
            
            # Calculate risk/reward ratio
            risk_reward_ratio = self._calculate_risk_reward_ratio(
                composite_score.entry_price,
                composite_score.stop_loss,
                composite_score.take_profit
            )
            
            # Calculate position size
            position_size = self._calculate_position_size(
                composite_score, market_data, portfolio_data
            )
            
            # Determine expiry time
            expiry_time = self._calculate_expiry_time(composite_score.time_horizon)
            
            # Generate alerts and warnings
            alerts = self._generate_alerts(composite_score, ross_score, market_data)
            risk_warnings = self._generate_risk_warnings(composite_score, market_data)
            
            # Generate notes
            notes = self._generate_analysis_notes(composite_score, ross_score)
            
            # Create signal ID
            signal_id = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            return TradingSignal(
                symbol=symbol,
                signal_id=signal_id,
                timestamp=datetime.now(),
                composite_score=composite_score,
                ross_score=ross_score,
                signal_type=signal_type,
                signal_strength=composite_score.signal_strength,
                confidence=composite_score.confidence_level,
                entry_price=composite_score.entry_price,
                stop_loss=composite_score.stop_loss,
                take_profit=composite_score.take_profit,
                position_size=position_size,
                risk_reward_ratio=risk_reward_ratio,
                time_horizon=composite_score.time_horizon,
                urgency=composite_score.urgency,
                expiry_time=expiry_time,
                fundamental_analysis=fundamental_data,
                technical_analysis=technical_data,
                news_analysis=news_data,
                market_data=market_data,
                alerts=alerts,
                notes=notes,
                risk_warnings=risk_warnings
            )
            
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}")
            return self._create_default_signal(symbol)
    
    def generate_batch_signals(self, symbols: List[str],
                             data_dict: Dict[str, Dict]) -> List[TradingSignal]:
        """
        Generate signals for multiple symbols
        
        Args:
            symbols: List of stock symbols
            data_dict: Dictionary containing all data for each symbol
            
        Returns:
            List of TradingSignal objects
        """
        try:
            logger.info(f"Generating batch signals for {len(symbols)} symbols")
            
            signals = []
            
            for symbol in symbols:
                try:
                    symbol_data = data_dict.get(symbol, {})
                    
                    signal = self.generate_signal(
                        symbol=symbol,
                        fundamental_data=symbol_data.get('fundamental', {}),
                        technical_data=symbol_data.get('technical', {}),
                        news_data=symbol_data.get('news', {}),
                        market_data=symbol_data.get('market', {}),
                        portfolio_data=symbol_data.get('portfolio')
                    )
                    
                    signals.append(signal)
                    
                except Exception as e:
                    logger.warning(f"Error generating signal for {symbol}: {e}")
                    continue
            
            # Sort signals by overall score
            signals.sort(key=lambda x: x.composite_score.overall_score, reverse=True)
            
            logger.info(f"Generated {len(signals)} signals successfully")
            return signals
            
        except Exception as e:
            logger.error(f"Error in batch signal generation: {e}")
            return []
    
    def create_signal_summary(self, signals: List[TradingSignal]) -> SignalSummary:
        """Create summary of multiple signals"""
        try:
            if not signals:
                return SignalSummary(0, 0, 0, 0, 0, 0.0, [], {})
            
            # Count signal types
            strong_buy_count = len([s for s in signals if s.composite_score.recommendation == 'strong_buy'])
            buy_count = len([s for s in signals if s.composite_score.recommendation == 'buy'])
            hold_count = len([s for s in signals if s.composite_score.recommendation == 'hold'])
            sell_count = len([s for s in signals if s.composite_score.recommendation in ['sell', 'strong_sell']])
            
            # Calculate average confidence
            avg_confidence = np.mean([s.confidence for s in signals])
            
            # Get top signals (top 10 or all if less than 10)
            top_signals = signals[:min(10, len(signals))]
            
            # Risk distribution
            risk_distribution = {
                'low': len([s for s in signals if s.composite_score.risk_level == 'low']),
                'medium': len([s for s in signals if s.composite_score.risk_level == 'medium']),
                'high': len([s for s in signals if s.composite_score.risk_level == 'high'])
            }
            
            return SignalSummary(
                total_signals=len(signals),
                strong_buy_signals=strong_buy_count,
                buy_signals=buy_count,
                hold_signals=hold_count,
                sell_signals=sell_count,
                avg_confidence=avg_confidence,
                top_signals=top_signals,
                risk_distribution=risk_distribution
            )
            
        except Exception as e:
            logger.error(f"Error creating signal summary: {e}")
            return SignalSummary(0, 0, 0, 0, 0, 0.0, [], {})
    
    def filter_signals_by_criteria(self, signals: List[TradingSignal],
                                 min_score: float = 70,
                                 max_risk: str = 'medium',
                                 min_confidence: float = 0.7,
                                 required_catalysts: List[str] = None) -> List[TradingSignal]:
        """Filter signals based on specific criteria"""
        try:
            filtered_signals = []
            
            risk_order = {'low': 1, 'medium': 2, 'high': 3}
            max_risk_level = risk_order.get(max_risk, 2)
            
            for signal in signals:
                # Score filter
                if signal.composite_score.overall_score < min_score:
                    continue
                
                # Risk filter
                signal_risk_level = risk_order.get(signal.composite_score.risk_level, 2)
                if signal_risk_level > max_risk_level:
                    continue
                
                # Confidence filter
                if signal.confidence < min_confidence:
                    continue
                
                # Catalyst filter
                if required_catalysts:
                    signal_catalysts = signal.news_analysis.get('catalyst_types', [])
                    if not any(cat in signal_catalysts for cat in required_catalysts):
                        continue
                
                filtered_signals.append(signal)
            
            logger.info(f"Filtered {len(signals)} signals to {len(filtered_signals)} based on criteria")
            return filtered_signals
            
        except Exception as e:
            logger.error(f"Error filtering signals: {e}")
            return signals
    
    def get_ross_cameron_signals(self, signals: List[TradingSignal],
                               min_ross_score: float = 80) -> List[TradingSignal]:
        """Get signals that meet Ross Cameron criteria"""
        try:
            ross_signals = []
            
            for signal in signals:
                # Check Ross Cameron score
                if signal.ross_score.overall_ross_score < min_ross_score:
                    continue
                
                # Check individual pillars
                pillars_passed = 0
                
                # Pillar 1: Volume (minimum 2x)
                if signal.ross_score.pillar_1_volume >= 80:  # 2x+ volume
                    pillars_passed += 1
                
                # Pillar 2: Price change (minimum 4%)
                if signal.ross_score.pillar_2_price_change >= 70:  # 4%+ change
                    pillars_passed += 1
                
                # Pillar 3: Float (under 30M)
                if signal.ross_score.pillar_3_float >= 80:  # Good float
                    pillars_passed += 1
                
                # Pillar 4: Catalyst
                if signal.ross_score.pillar_4_catalyst >= 70:  # Strong catalyst
                    pillars_passed += 1
                
                # Pillar 5: Price range (under $20)
                if signal.ross_score.pillar_5_price_range >= 80:  # Good price range
                    pillars_passed += 1
                
                # Require at least 4 out of 5 pillars
                if pillars_passed >= 4:
                    ross_signals.append(signal)
            
            # Sort by Ross Cameron score
            ross_signals.sort(key=lambda x: x.ross_score.overall_ross_score, reverse=True)
            
            logger.info(f"Found {len(ross_signals)} signals meeting Ross Cameron criteria")
            return ross_signals
            
        except Exception as e:
            logger.error(f"Error filtering Ross Cameron signals: {e}")
            return []
    
    def _determine_signal_type(self, overall_score: float) -> str:
        """Determine signal type based on overall score"""
        if overall_score >= self.signal_thresholds['strong_buy']:
            return 'strong_buy'
        elif overall_score >= self.signal_thresholds['buy']:
            return 'buy'
        elif overall_score >= self.signal_thresholds['hold']:
            return 'hold'
        elif overall_score >= self.signal_thresholds['sell']:
            return 'sell'
        else:
            return 'strong_sell'
    
    def _calculate_risk_reward_ratio(self, entry: Optional[float],
                                   stop_loss: Optional[float],
                                   take_profit: Optional[float]) -> Optional[float]:
        """Calculate risk/reward ratio"""
        try:
            if not all([entry, stop_loss, take_profit]):
                return None
            
            risk = entry - stop_loss
            reward = take_profit - entry
            
            if risk <= 0:
                return None
            
            return reward / risk
            
        except Exception:
            return None
    
    def _calculate_position_size(self, composite_score: CompositeScore,
                               market_data: Dict,
                               portfolio_data: Optional[Dict]) -> Optional[float]:
        """Calculate appropriate position size"""
        try:
            if not portfolio_data:
                return None
            
            account_value = portfolio_data.get('account_value', 0)
            if account_value <= 0:
                return None
            
            # Risk-based position sizing
            risk_per_trade = self.risk_limits['max_position_risk']
            
            # Adjust risk based on signal quality
            if composite_score.confidence_level > 0.8 and composite_score.overall_score > 85:
                risk_per_trade *= 1.5  # Increase risk for high-confidence signals
            elif composite_score.confidence_level < 0.6:
                risk_per_trade *= 0.5  # Decrease risk for low-confidence signals
            
            # Adjust risk based on risk level
            if composite_score.risk_level == 'high':
                risk_per_trade *= 0.5
            elif composite_score.risk_level == 'low':
                risk_per_trade *= 1.2
            
            # Calculate position size
            if composite_score.entry_price and composite_score.stop_loss:
                risk_per_share = composite_score.entry_price - composite_score.stop_loss
                if risk_per_share > 0:
                    max_risk_amount = account_value * risk_per_trade
                    position_size = max_risk_amount / risk_per_share
                    
                    # Ensure position doesn't exceed reasonable limits
                    max_position_value = account_value * 0.1  # Max 10% of account in one position
                    max_shares_by_value = max_position_value / composite_score.entry_price
                    
                    return min(position_size, max_shares_by_value)
            
            return None
            
        except Exception as e:
            logger.warning(f"Error calculating position size: {e}")
            return None
    
    def _calculate_expiry_time(self, time_horizon: str) -> Optional[datetime]:
        """Calculate when the signal expires"""
        try:
            now = datetime.now()
            
            if time_horizon == 'scalp':
                return now + timedelta(minutes=30)
            elif time_horizon == 'day_trade':
                return now + timedelta(hours=6)
            elif time_horizon == 'swing':
                return now + timedelta(days=5)
            elif time_horizon == 'position':
                return now + timedelta(days=30)
            else:
                return now + timedelta(hours=24)
                
        except Exception:
            return None
    
    def _generate_alerts(self, composite_score: CompositeScore,
                        ross_score: RossScore,
                        market_data: Dict) -> List[str]:
        """Generate alerts for the signal"""
        alerts = []
        
        try:
            # High-score alerts
            if composite_score.overall_score >= 90:
                alerts.append("🔥 EXCEPTIONAL SETUP - Very high composite score!")
            elif composite_score.overall_score >= 80:
                alerts.append("⭐ STRONG SETUP - High composite score")
            
            # Ross Cameron alerts
            if ross_score.overall_ross_score >= 90:
                alerts.append("🎯 PERFECT ROSS CAMERON SETUP - All pillars strong!")
            elif ross_score.ross_grade in ['A+', 'A']:
                alerts.append(f"📈 EXCELLENT ROSS SETUP - Grade: {ross_score.ross_grade}")
            
            # Volume alerts
            relative_volume = market_data.get('relative_volume', 1.0)
            if relative_volume >= 10:
                alerts.append(f"🚀 MASSIVE VOLUME - {relative_volume:.1f}x average!")
            elif relative_volume >= 5:
                alerts.append(f"📊 HIGH VOLUME - {relative_volume:.1f}x average")
            
            # Price movement alerts
            price_change = market_data.get('price_change_percent', 0)
            if abs(price_change) >= 20:
                alerts.append(f"💥 MAJOR MOVE - {price_change:+.1f}% price change!")
            elif abs(price_change) >= 10:
                alerts.append(f"📈 SIGNIFICANT MOVE - {price_change:+.1f}% price change")
            
            # Catalyst alerts
            catalyst_types = composite_score.component_scores[2].details.get('catalyst_types', [])  # News component
            high_impact_catalysts = ['fda_approval', 'merger_acquisition', 'earnings_beat']
            if any(cat in high_impact_catalysts for cat in catalyst_types):
                alerts.append("🎯 HIGH-IMPACT CATALYST DETECTED")
            
            # Urgency alerts
            if composite_score.urgency == 'immediate':
                alerts.append("⚡ IMMEDIATE ACTION REQUIRED")
            elif composite_score.urgency == 'high':
                alerts.append("🔔 HIGH URGENCY - Act soon")
            
            return alerts
            
        except Exception as e:
            logger.warning(f"Error generating alerts: {e}")
            return ["⚠️ Alert generation error"]
    
    def _generate_risk_warnings(self, composite_score: CompositeScore,
                              market_data: Dict) -> List[str]:
        """Generate risk warnings"""
        warnings = []
        
        try:
            # High risk level warning
            if composite_score.risk_level == 'high':
                warnings.append("⚠️ HIGH RISK TRADE - Use smaller position size")
            
            # Overbought warning
            rsi = market_data.get('rsi', 50)
            if rsi > 80:
                warnings.append("⚠️ HIGHLY OVERBOUGHT - Risk of pullback")
            elif rsi > 70:
                warnings.append("⚠️ OVERBOUGHT CONDITIONS - Monitor closely")
            
            # Low confidence warning
            if composite_score.confidence_level < 0.6:
                warnings.append("⚠️ LOW CONFIDENCE SIGNAL - Consider waiting")
            
            # High volatility warning
            volatility = market_data.get('volatility', 0)
            if volatility > 0.4:
                warnings.append("⚠️ HIGH VOLATILITY - Expect large price swings")
            
            # Price level warning
            current_price = market_data.get('current_price', 0)
            if current_price > 50:
                warnings.append("⚠️ HIGH PRICE STOCK - Increased risk")
            
            # Gap warning
            gap_percent = market_data.get('gap_percent', 0)
            if abs(gap_percent) > 15:
                warnings.append("⚠️ LARGE GAP - Risk of gap fill")
            
            return warnings
            
        except Exception as e:
            logger.warning(f"Error generating risk warnings: {e}")
            return ["⚠️ Risk assessment error"]
    
    def _generate_analysis_notes(self, composite_score: CompositeScore,
                               ross_score: RossScore) -> str:
        """Generate analysis notes"""
        try:
            notes = []
            
            # Overall assessment
            notes.append(f"Overall Score: {composite_score.overall_score:.1f}/100")
            notes.append(f"Ross Cameron Grade: {ross_score.ross_grade}")
            notes.append(f"Confidence: {composite_score.confidence_level:.1%}")
            notes.append(f"Risk Level: {composite_score.risk_level.title()}")
            
            # Component breakdown
            notes.append("\\nComponent Scores:")
            for component in composite_score.component_scores:
                notes.append(f"• {component.component.title()}: {component.raw_score:.1f}/100")
            
            # Ross Cameron pillars
            notes.append("\\nRoss Cameron Pillars:")
            notes.append(f"• Volume: {ross_score.pillar_1_volume:.1f}/100")
            notes.append(f"• Price Change: {ross_score.pillar_2_price_change:.1f}/100")
            notes.append(f"• Float: {ross_score.pillar_3_float:.1f}/100")
            notes.append(f"• Catalyst: {ross_score.pillar_4_catalyst:.1f}/100")
            notes.append(f"• Price Range: {ross_score.pillar_5_price_range:.1f}/100")
            
            # Trading details
            if composite_score.entry_price:
                notes.append(f"\\nEntry: ${composite_score.entry_price:.2f}")
            if composite_score.stop_loss:
                notes.append(f"Stop Loss: ${composite_score.stop_loss:.2f}")
            if composite_score.take_profit:
                notes.append(f"Take Profit: ${composite_score.take_profit:.2f}")
            
            return "\\n".join(notes)
            
        except Exception as e:
            logger.warning(f"Error generating analysis notes: {e}")
            return "Analysis notes generation error"
    
    def _create_default_signal(self, symbol: str) -> TradingSignal:
        """Create default signal when generation fails"""
        from .scoring_engine import CompositeScore, RossScore, ComponentScore
        
        default_composite = CompositeScore(
            symbol=symbol,
            overall_score=50.0,
            component_scores=[],
            confidence_level=0.5,
            risk_level='medium',
            signal_strength='weak',
            recommendation='hold',
            entry_price=None,
            stop_loss=None,
            take_profit=None,
            position_size=None,
            time_horizon='day_trade',
            urgency='low'
        )
        
        default_ross = RossScore(
            pillar_1_volume=50.0,
            pillar_2_price_change=50.0,
            pillar_3_float=50.0,
            pillar_4_catalyst=50.0,
            pillar_5_price_range=50.0,
            overall_ross_score=50.0,
            ross_grade='C'
        )
        
        return TradingSignal(
            symbol=symbol,
            signal_id=f"{symbol}_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(),
            composite_score=default_composite,
            ross_score=default_ross,
            signal_type='hold',
            signal_strength='weak',
            confidence=0.5,
            entry_price=None,
            stop_loss=None,
            take_profit=None,
            position_size=None,
            risk_reward_ratio=None,
            time_horizon='day_trade',
            urgency='low',
            expiry_time=None,
            fundamental_analysis={},
            technical_analysis={},
            news_analysis={},
            market_data={},
            alerts=["⚠️ Signal generation error"],
            notes="Error in signal generation",
            risk_warnings=["⚠️ Signal reliability unknown"]
        )

