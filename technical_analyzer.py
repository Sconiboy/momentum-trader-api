"""
Technical Analyzer - Main coordinator for all technical analysis
Combines indicators, patterns, and signals for comprehensive analysis
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..core.logger import get_logger
from ..core.exceptions import MomentumTraderError
from .technical_indicators import TechnicalIndicators, TechnicalSignals
from .abcd_pattern_detector import ABCDPatternDetector, ABCDAnalysis

logger = get_logger(__name__)

@dataclass
class SupportResistanceLevel:
    """Support or resistance level"""
    price: float
    strength: float  # 0-100
    level_type: str  # 'support', 'resistance'
    touches: int
    last_touch: datetime
    is_current: bool

@dataclass
class TechnicalAnalysisResult:
    """Complete technical analysis result"""
    symbol: str
    timestamp: datetime
    current_price: float
    
    # Core indicators
    technical_signals: TechnicalSignals
    abcd_analysis: ABCDAnalysis
    
    # Support/Resistance
    support_levels: List[SupportResistanceLevel]
    resistance_levels: List[SupportResistanceLevel]
    nearest_support: Optional[float]
    nearest_resistance: Optional[float]
    
    # Entry/Exit recommendations
    entry_recommendation: Dict[str, Any]
    exit_recommendation: Dict[str, Any]
    position_sizing: Dict[str, Any]
    
    # Risk management
    stop_loss_price: Optional[float]
    take_profit_price: Optional[float]
    risk_reward_ratio: Optional[float]
    
    # Overall assessment
    technical_score: float  # 0-100
    trend_direction: str  # 'bullish', 'bearish', 'sideways'
    momentum_strength: str  # 'strong', 'moderate', 'weak'
    volatility_assessment: str  # 'high', 'medium', 'low'
    
    # Ross Cameron specific
    ross_cameron_setup: bool
    setup_quality: str  # 'excellent', 'good', 'fair', 'poor'
    entry_timing: str  # 'immediate', 'wait', 'avoid'

class TechnicalAnalyzer:
    """Main technical analysis coordinator"""
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Initialize analysis components
        self.technical_indicators = TechnicalIndicators()
        self.abcd_detector = ABCDPatternDetector()
        
        # Ross Cameron specific settings
        self.min_volume_multiplier = 2.0
        self.preferred_price_range = (2.0, 20.0)
        self.min_gap_percentage = 4.0
        
        logger.info("Technical Analyzer initialized")
    
    def analyze_stock(self, 
                     symbol: str,
                     price_data: pd.DataFrame,
                     current_price: float,
                     current_volume: int,
                     float_shares: Optional[float] = None) -> TechnicalAnalysisResult:
        """
        Perform comprehensive technical analysis on a stock
        
        Args:
            symbol: Stock symbol
            price_data: Historical OHLCV data
            current_price: Current stock price
            current_volume: Current volume
            float_shares: Number of float shares
            
        Returns:
            Complete technical analysis result
        """
        try:
            logger.info(f"Performing technical analysis for {symbol}")
            
            # Validate input data
            if len(price_data) < 20:
                raise MomentumTraderError(f"Insufficient data for {symbol}: {len(price_data)} bars")
            
            # Calculate technical indicators
            technical_signals = self.technical_indicators.calculate_all_indicators(
                price_data, current_price, current_volume
            )
            
            # Detect ABCD patterns
            abcd_analysis = self.abcd_detector.analyze_abcd_patterns(price_data)
            
            # Calculate support and resistance levels
            support_levels, resistance_levels = self._calculate_support_resistance(price_data, current_price)
            nearest_support, nearest_resistance = self._find_nearest_levels(
                current_price, support_levels, resistance_levels
            )
            
            # Generate entry/exit recommendations
            entry_recommendation = self._generate_entry_recommendation(
                technical_signals, abcd_analysis, current_price, nearest_support, nearest_resistance
            )
            exit_recommendation = self._generate_exit_recommendation(
                technical_signals, abcd_analysis, current_price, nearest_resistance, nearest_support
            )
            
            # Calculate position sizing
            position_sizing = self._calculate_position_sizing(
                current_price, nearest_support, float_shares, technical_signals
            )
            
            # Calculate risk management levels
            stop_loss_price, take_profit_price, risk_reward_ratio = self._calculate_risk_management(
                current_price, entry_recommendation, nearest_support, nearest_resistance, technical_signals
            )
            
            # Calculate overall technical score
            technical_score = self._calculate_technical_score(
                technical_signals, abcd_analysis, support_levels, resistance_levels
            )
            
            # Assess trend and momentum
            trend_direction = self._assess_trend_direction(technical_signals, abcd_analysis)
            momentum_strength = self._assess_momentum_strength(technical_signals, current_volume)
            volatility_assessment = self._assess_volatility(price_data)
            
            # Ross Cameron specific assessment
            ross_cameron_setup, setup_quality, entry_timing = self._assess_ross_cameron_setup(
                technical_signals, abcd_analysis, current_price, current_volume, float_shares
            )
            
            return TechnicalAnalysisResult(
                symbol=symbol,
                timestamp=datetime.now(),
                current_price=current_price,
                technical_signals=technical_signals,
                abcd_analysis=abcd_analysis,
                support_levels=support_levels,
                resistance_levels=resistance_levels,
                nearest_support=nearest_support,
                nearest_resistance=nearest_resistance,
                entry_recommendation=entry_recommendation,
                exit_recommendation=exit_recommendation,
                position_sizing=position_sizing,
                stop_loss_price=stop_loss_price,
                take_profit_price=take_profit_price,
                risk_reward_ratio=risk_reward_ratio,
                technical_score=technical_score,
                trend_direction=trend_direction,
                momentum_strength=momentum_strength,
                volatility_assessment=volatility_assessment,
                ross_cameron_setup=ross_cameron_setup,
                setup_quality=setup_quality,
                entry_timing=entry_timing
            )
            
        except Exception as e:
            logger.error(f"Error in technical analysis for {symbol}: {e}")
            raise MomentumTraderError(f"Technical analysis failed for {symbol}: {e}")
    
    def _calculate_support_resistance(self, price_data: pd.DataFrame, current_price: float) -> Tuple[List[SupportResistanceLevel], List[SupportResistanceLevel]]:
        """Calculate support and resistance levels"""
        try:
            support_levels = []
            resistance_levels = []
            
            # Use recent price data (last 50 bars)
            recent_data = price_data.tail(50)
            highs = recent_data['high'].values
            lows = recent_data['low'].values
            
            # Find significant levels using pivot points
            from scipy import signal
            
            # Find resistance levels (peaks)
            peak_indices = signal.find_peaks(highs, distance=3, prominence=np.std(highs) * 0.3)[0]
            for idx in peak_indices:
                if idx < len(recent_data):
                    price_level = highs[idx]
                    
                    # Count touches near this level
                    touches = self._count_touches(price_data, price_level, 'resistance')
                    
                    if touches >= 2:  # At least 2 touches to be significant
                        strength = min(100, touches * 20 + (100 - abs(current_price - price_level) / current_price * 100))
                        
                        resistance_levels.append(SupportResistanceLevel(
                            price=price_level,
                            strength=strength,
                            level_type='resistance',
                            touches=touches,
                            last_touch=recent_data.index[idx],
                            is_current=abs(current_price - price_level) / current_price < 0.02
                        ))
            
            # Find support levels (troughs)
            trough_indices = signal.find_peaks(-lows, distance=3, prominence=np.std(lows) * 0.3)[0]
            for idx in trough_indices:
                if idx < len(recent_data):
                    price_level = lows[idx]
                    
                    # Count touches near this level
                    touches = self._count_touches(price_data, price_level, 'support')
                    
                    if touches >= 2:  # At least 2 touches to be significant
                        strength = min(100, touches * 20 + (100 - abs(current_price - price_level) / current_price * 100))
                        
                        support_levels.append(SupportResistanceLevel(
                            price=price_level,
                            strength=strength,
                            level_type='support',
                            touches=touches,
                            last_touch=recent_data.index[idx],
                            is_current=abs(current_price - price_level) / current_price < 0.02
                        ))
            
            # Sort by strength
            support_levels.sort(key=lambda x: x.strength, reverse=True)
            resistance_levels.sort(key=lambda x: x.strength, reverse=True)
            
            return support_levels[:5], resistance_levels[:5]  # Keep top 5 each
            
        except Exception as e:
            logger.warning(f"Error calculating support/resistance: {e}")
            return [], []
    
    def _count_touches(self, price_data: pd.DataFrame, level: float, level_type: str) -> int:
        """Count how many times price touched a support/resistance level"""
        try:
            tolerance = level * 0.01  # 1% tolerance
            touches = 0
            
            if level_type == 'resistance':
                # Count times high price came close to level
                for high in price_data['high'].values:
                    if abs(high - level) <= tolerance:
                        touches += 1
            else:  # support
                # Count times low price came close to level
                for low in price_data['low'].values:
                    if abs(low - level) <= tolerance:
                        touches += 1
            
            return touches
            
        except Exception:
            return 0
    
    def _find_nearest_levels(self, current_price: float, 
                           support_levels: List[SupportResistanceLevel],
                           resistance_levels: List[SupportResistanceLevel]) -> Tuple[Optional[float], Optional[float]]:
        """Find nearest support and resistance levels"""
        try:
            nearest_support = None
            nearest_resistance = None
            
            # Find nearest support below current price
            for level in support_levels:
                if level.price < current_price:
                    if nearest_support is None or level.price > nearest_support:
                        nearest_support = level.price
            
            # Find nearest resistance above current price
            for level in resistance_levels:
                if level.price > current_price:
                    if nearest_resistance is None or level.price < nearest_resistance:
                        nearest_resistance = level.price
            
            return nearest_support, nearest_resistance
            
        except Exception:
            return None, None
    
    def _generate_entry_recommendation(self, technical_signals: TechnicalSignals,
                                     abcd_analysis: ABCDAnalysis,
                                     current_price: float,
                                     nearest_support: Optional[float],
                                     nearest_resistance: Optional[float]) -> Dict[str, Any]:
        """Generate entry recommendation"""
        try:
            recommendation = {
                'action': 'hold',
                'confidence': 0,
                'reasons': [],
                'entry_price': current_price,
                'timing': 'wait'
            }
            
            # Check technical signals
            if technical_signals.entry_signal:
                recommendation['reasons'].append('Technical entry signal triggered')
                recommendation['confidence'] += 30
            
            # Check MACD
            if technical_signals.macd.crossover_signal == 'bullish':
                recommendation['reasons'].append('MACD bullish crossover')
                recommendation['confidence'] += 25
            
            # Check EMA alignment
            if technical_signals.ema.price_above_ema9 and technical_signals.ema.trend_direction == 'bullish':
                recommendation['reasons'].append('Price above 9 EMA with bullish trend')
                recommendation['confidence'] += 20
            
            # Check volume
            if technical_signals.volume.volume_breakout:
                recommendation['reasons'].append('Volume breakout confirmed')
                recommendation['confidence'] += 20
            
            # Check ABCD patterns
            if abcd_analysis.entry_signals:
                for signal in abcd_analysis.entry_signals:
                    if signal['signal_strength'] in ['strong', 'moderate']:
                        recommendation['reasons'].append(f"ABCD {signal['pattern_type']} entry signal")
                        recommendation['confidence'] += 15
            
            # Check RSI
            if not technical_signals.rsi.is_overbought and technical_signals.rsi.momentum_direction == 'bullish':
                recommendation['reasons'].append('RSI shows bullish momentum without overbought')
                recommendation['confidence'] += 10
            
            # Determine action based on confidence
            if recommendation['confidence'] >= 70:
                recommendation['action'] = 'strong_buy'
                recommendation['timing'] = 'immediate'
            elif recommendation['confidence'] >= 50:
                recommendation['action'] = 'buy'
                recommendation['timing'] = 'immediate'
            elif recommendation['confidence'] >= 30:
                recommendation['action'] = 'weak_buy'
                recommendation['timing'] = 'wait_for_confirmation'
            
            return recommendation
            
        except Exception as e:
            logger.warning(f"Error generating entry recommendation: {e}")
            return {'action': 'hold', 'confidence': 0, 'reasons': [], 'timing': 'wait'}
    
    def _generate_exit_recommendation(self, technical_signals: TechnicalSignals,
                                    abcd_analysis: ABCDAnalysis,
                                    current_price: float,
                                    nearest_resistance: Optional[float],
                                    nearest_support: Optional[float]) -> Dict[str, Any]:
        """Generate exit recommendation"""
        try:
            recommendation = {
                'action': 'hold',
                'confidence': 0,
                'reasons': [],
                'exit_price': current_price,
                'urgency': 'low'
            }
            
            # Check technical exit signals
            if technical_signals.exit_signal:
                recommendation['reasons'].append('Technical exit signal triggered')
                recommendation['confidence'] += 30
            
            # Check MACD
            if technical_signals.macd.crossover_signal == 'bearish':
                recommendation['reasons'].append('MACD bearish crossover')
                recommendation['confidence'] += 25
            
            # Check EMA
            if not technical_signals.ema.price_above_ema9:
                recommendation['reasons'].append('Price below 9 EMA')
                recommendation['confidence'] += 20
            
            # Check RSI
            if technical_signals.rsi.is_overbought:
                recommendation['reasons'].append('RSI overbought')
                recommendation['confidence'] += 15
            
            # Check ABCD patterns
            if abcd_analysis.exit_signals:
                for signal in abcd_analysis.exit_signals:
                    if signal['type'] == 'take_profit':
                        recommendation['reasons'].append('ABCD pattern target reached')
                        recommendation['confidence'] += 20
                    elif signal['type'] == 'stop_loss':
                        recommendation['reasons'].append('ABCD pattern stop loss hit')
                        recommendation['confidence'] += 30
                        recommendation['urgency'] = 'high'
            
            # Check resistance levels
            if nearest_resistance and current_price >= nearest_resistance * 0.98:
                recommendation['reasons'].append('Approaching resistance level')
                recommendation['confidence'] += 15
            
            # Determine action
            if recommendation['confidence'] >= 60:
                recommendation['action'] = 'sell'
                recommendation['urgency'] = 'high' if recommendation['confidence'] >= 80 else 'medium'
            elif recommendation['confidence'] >= 40:
                recommendation['action'] = 'partial_sell'
                recommendation['urgency'] = 'medium'
            
            return recommendation
            
        except Exception as e:
            logger.warning(f"Error generating exit recommendation: {e}")
            return {'action': 'hold', 'confidence': 0, 'reasons': [], 'urgency': 'low'}
    
    def _calculate_position_sizing(self, current_price: float,
                                 nearest_support: Optional[float],
                                 float_shares: Optional[float],
                                 technical_signals: TechnicalSignals) -> Dict[str, Any]:
        """Calculate recommended position sizing"""
        try:
            # Base position size (conservative)
            base_position_value = 1000  # $1000 base position
            
            # Risk-based sizing
            if nearest_support:
                risk_per_share = current_price - nearest_support
                max_risk = base_position_value * 0.02  # 2% max risk
                max_shares = int(max_risk / risk_per_share) if risk_per_share > 0 else 0
            else:
                max_shares = int(base_position_value / current_price)
            
            # Adjust based on technical strength
            multiplier = 1.0
            if technical_signals.signal_strength >= 80:
                multiplier = 1.5
            elif technical_signals.signal_strength >= 60:
                multiplier = 1.2
            elif technical_signals.signal_strength <= 40:
                multiplier = 0.5
            
            recommended_shares = int(max_shares * multiplier)
            
            # Float consideration (don't take more than 0.1% of float)
            if float_shares:
                max_float_shares = int(float_shares * 0.001)  # 0.1% of float
                recommended_shares = min(recommended_shares, max_float_shares)
            
            return {
                'recommended_shares': max(1, recommended_shares),
                'position_value': recommended_shares * current_price,
                'risk_per_share': nearest_support and (current_price - nearest_support) or 0,
                'max_risk_amount': recommended_shares * (nearest_support and (current_price - nearest_support) or current_price * 0.05),
                'confidence_multiplier': multiplier
            }
            
        except Exception as e:
            logger.warning(f"Error calculating position sizing: {e}")
            return {'recommended_shares': 1, 'position_value': current_price}
    
    def _calculate_risk_management(self, current_price: float,
                                 entry_recommendation: Dict[str, Any],
                                 nearest_support: Optional[float],
                                 nearest_resistance: Optional[float],
                                 technical_signals: TechnicalSignals) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """Calculate stop loss, take profit, and risk/reward ratio"""
        try:
            stop_loss_price = None
            take_profit_price = None
            risk_reward_ratio = None
            
            # Calculate stop loss
            if nearest_support:
                stop_loss_price = nearest_support * 0.98  # 2% below support
            else:
                stop_loss_price = current_price * 0.95  # 5% stop loss
            
            # Calculate take profit
            if nearest_resistance:
                take_profit_price = nearest_resistance * 0.98  # Just below resistance
            else:
                # Use 2:1 risk/reward ratio
                risk = current_price - stop_loss_price
                take_profit_price = current_price + (risk * 2)
            
            # Calculate risk/reward ratio
            if stop_loss_price and take_profit_price:
                risk = current_price - stop_loss_price
                reward = take_profit_price - current_price
                risk_reward_ratio = reward / risk if risk > 0 else 0
            
            return stop_loss_price, take_profit_price, risk_reward_ratio
            
        except Exception as e:
            logger.warning(f"Error calculating risk management: {e}")
            return None, None, None
    
    def _calculate_technical_score(self, technical_signals: TechnicalSignals,
                                 abcd_analysis: ABCDAnalysis,
                                 support_levels: List[SupportResistanceLevel],
                                 resistance_levels: List[SupportResistanceLevel]) -> float:
        """Calculate overall technical score"""
        try:
            score = 0
            
            # Technical signals score (40 points)
            score += technical_signals.signal_strength * 0.4
            
            # ABCD patterns score (30 points)
            if abcd_analysis.active_pattern:
                score += abcd_analysis.active_pattern.confidence * 0.3
            
            # Support/Resistance score (20 points)
            if support_levels or resistance_levels:
                avg_strength = np.mean([level.strength for level in support_levels + resistance_levels])
                score += avg_strength * 0.2
            
            # Volume confirmation (10 points)
            if technical_signals.volume.volume_breakout:
                score += 10
            elif technical_signals.volume.volume_trend == 'increasing':
                score += 5
            
            return min(100, score)
            
        except Exception:
            return 50
    
    def _assess_trend_direction(self, technical_signals: TechnicalSignals, abcd_analysis: ABCDAnalysis) -> str:
        """Assess overall trend direction"""
        try:
            bullish_signals = 0
            bearish_signals = 0
            
            # EMA trend
            if technical_signals.ema.trend_direction == 'bullish':
                bullish_signals += 2
            elif technical_signals.ema.trend_direction == 'bearish':
                bearish_signals += 2
            
            # MACD
            if technical_signals.macd.is_bullish:
                bullish_signals += 1
            elif technical_signals.macd.is_bearish:
                bearish_signals += 1
            
            # ABCD patterns
            if abcd_analysis.active_pattern:
                if abcd_analysis.active_pattern.pattern_type == 'bullish':
                    bullish_signals += 1
                else:
                    bearish_signals += 1
            
            if bullish_signals > bearish_signals:
                return 'bullish'
            elif bearish_signals > bullish_signals:
                return 'bearish'
            else:
                return 'sideways'
                
        except Exception:
            return 'sideways'
    
    def _assess_momentum_strength(self, technical_signals: TechnicalSignals, current_volume: int) -> str:
        """Assess momentum strength"""
        try:
            strength_score = 0
            
            # Volume
            if technical_signals.volume.relative_volume >= 5:
                strength_score += 3
            elif technical_signals.volume.relative_volume >= 2:
                strength_score += 2
            elif technical_signals.volume.relative_volume >= 1.5:
                strength_score += 1
            
            # MACD histogram
            if abs(technical_signals.macd.histogram) > 0.1:
                strength_score += 2
            elif abs(technical_signals.macd.histogram) > 0.05:
                strength_score += 1
            
            # RSI momentum
            if technical_signals.rsi.momentum_direction == 'bullish' and technical_signals.rsi.rsi > 60:
                strength_score += 1
            elif technical_signals.rsi.momentum_direction == 'bearish' and technical_signals.rsi.rsi < 40:
                strength_score += 1
            
            if strength_score >= 5:
                return 'strong'
            elif strength_score >= 3:
                return 'moderate'
            else:
                return 'weak'
                
        except Exception:
            return 'weak'
    
    def _assess_volatility(self, price_data: pd.DataFrame) -> str:
        """Assess price volatility"""
        try:
            # Calculate recent volatility (last 20 periods)
            recent_data = price_data.tail(20)
            returns = recent_data['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)  # Annualized
            
            if volatility > 0.5:  # 50%+ annualized
                return 'high'
            elif volatility > 0.3:  # 30%+ annualized
                return 'medium'
            else:
                return 'low'
                
        except Exception:
            return 'medium'
    
    def _assess_ross_cameron_setup(self, technical_signals: TechnicalSignals,
                                 abcd_analysis: ABCDAnalysis,
                                 current_price: float,
                                 current_volume: int,
                                 float_shares: Optional[float]) -> Tuple[bool, str, str]:
        """Assess if this is a good Ross Cameron setup"""
        try:
            setup_score = 0
            max_score = 100
            
            # Price range (20 points)
            if self.preferred_price_range[0] <= current_price <= self.preferred_price_range[1]:
                setup_score += 20
            elif current_price < self.preferred_price_range[0] * 2 or current_price > self.preferred_price_range[1] * 0.5:
                setup_score += 10
            
            # Volume (25 points)
            if technical_signals.volume.relative_volume >= 5:
                setup_score += 25
            elif technical_signals.volume.relative_volume >= 3:
                setup_score += 20
            elif technical_signals.volume.relative_volume >= 2:
                setup_score += 15
            
            # Float size (15 points)
            if float_shares and float_shares <= 20_000_000:  # 20M or less
                setup_score += 15
            elif float_shares and float_shares <= 50_000_000:  # 50M or less
                setup_score += 10
            
            # Technical setup (25 points)
            if technical_signals.entry_signal:
                setup_score += 15
            if technical_signals.macd.crossover_signal == 'bullish':
                setup_score += 10
            
            # ABCD pattern (15 points)
            if abcd_analysis.active_pattern and abcd_analysis.active_pattern.confidence >= 70:
                setup_score += 15
            elif abcd_analysis.entry_signals:
                setup_score += 10
            
            # Determine setup quality
            setup_percentage = (setup_score / max_score) * 100
            
            if setup_percentage >= 80:
                setup_quality = 'excellent'
                entry_timing = 'immediate'
            elif setup_percentage >= 65:
                setup_quality = 'good'
                entry_timing = 'immediate'
            elif setup_percentage >= 50:
                setup_quality = 'fair'
                entry_timing = 'wait'
            else:
                setup_quality = 'poor'
                entry_timing = 'avoid'
            
            ross_cameron_setup = setup_percentage >= 50
            
            return ross_cameron_setup, setup_quality, entry_timing
            
        except Exception as e:
            logger.warning(f"Error assessing Ross Cameron setup: {e}")
            return False, 'poor', 'avoid'

