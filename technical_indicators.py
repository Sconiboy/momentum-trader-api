"""
Technical Indicators - Core technical analysis calculations
Implements MACD, EMAs, RSI, and other indicators used in Ross Cameron's methodology
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import ta
from scipy import signal

from ..core.logger import get_logger

logger = get_logger(__name__)

@dataclass
class MACDResult:
    """MACD calculation result"""
    macd_line: float
    signal_line: float
    histogram: float
    is_bullish: bool
    is_bearish: bool
    crossover_signal: str  # 'bullish', 'bearish', 'none'
    
@dataclass
class EMAResult:
    """EMA calculation result"""
    ema_9: float
    ema_20: float
    ema_50: float
    ema_200: float
    trend_direction: str  # 'bullish', 'bearish', 'sideways'
    price_above_ema9: bool
    price_above_ema20: bool
    golden_cross: bool  # 50 EMA above 200 EMA
    death_cross: bool   # 50 EMA below 200 EMA

@dataclass
class RSIResult:
    """RSI calculation result"""
    rsi: float
    is_overbought: bool  # RSI > 70
    is_oversold: bool    # RSI < 30
    momentum_direction: str  # 'bullish', 'bearish', 'neutral'

@dataclass
class VolumeIndicators:
    """Volume-based indicators"""
    volume_sma_20: float
    relative_volume: float
    volume_trend: str  # 'increasing', 'decreasing', 'stable'
    volume_breakout: bool  # Volume > 2x average
    
@dataclass
class TechnicalSignals:
    """Combined technical analysis signals"""
    macd: MACDResult
    ema: EMAResult
    rsi: RSIResult
    volume: VolumeIndicators
    overall_signal: str  # 'strong_buy', 'buy', 'hold', 'sell', 'strong_sell'
    signal_strength: float  # 0-100
    entry_signal: bool
    exit_signal: bool

class TechnicalIndicators:
    """Calculate technical indicators for Ross Cameron's methodology"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Ross Cameron's preferred settings
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.rsi_period = 14
        self.volume_sma_period = 20
        
        logger.info("Technical Indicators initialized with Ross Cameron settings")
    
    def calculate_all_indicators(self, 
                               price_data: pd.DataFrame,
                               current_price: float,
                               current_volume: int) -> TechnicalSignals:
        """
        Calculate all technical indicators for a stock
        
        Args:
            price_data: DataFrame with OHLCV data
            current_price: Current stock price
            current_volume: Current volume
            
        Returns:
            TechnicalSignals object with all indicators
        """
        try:
            # Ensure we have enough data
            if len(price_data) < 50:
                logger.warning("Insufficient data for technical analysis")
                return self._create_default_signals()
            
            # Calculate individual indicators
            macd_result = self.calculate_macd(price_data, current_price)
            ema_result = self.calculate_emas(price_data, current_price)
            rsi_result = self.calculate_rsi(price_data)
            volume_result = self.calculate_volume_indicators(price_data, current_volume)
            
            # Determine overall signal
            overall_signal, signal_strength = self._calculate_overall_signal(
                macd_result, ema_result, rsi_result, volume_result
            )
            
            # Determine entry/exit signals
            entry_signal = self._is_entry_signal(macd_result, ema_result, rsi_result, volume_result)
            exit_signal = self._is_exit_signal(macd_result, ema_result, rsi_result)
            
            return TechnicalSignals(
                macd=macd_result,
                ema=ema_result,
                rsi=rsi_result,
                volume=volume_result,
                overall_signal=overall_signal,
                signal_strength=signal_strength,
                entry_signal=entry_signal,
                exit_signal=exit_signal
            )
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return self._create_default_signals()
    
    def calculate_macd(self, price_data: pd.DataFrame, current_price: float) -> MACDResult:
        """Calculate MACD indicator"""
        try:
            close_prices = price_data['close'].values
            
            # Calculate MACD using ta library
            macd_line = ta.trend.MACD(pd.Series(close_prices), 
                                    window_fast=self.macd_fast,
                                    window_slow=self.macd_slow).iloc[-1]
            
            signal_line = ta.trend.MACDSignal(pd.Series(close_prices),
                                            window_fast=self.macd_fast,
                                            window_slow=self.macd_slow,
                                            window_sign=self.macd_signal).iloc[-1]
            
            histogram = macd_line - signal_line
            
            # Determine signals
            is_bullish = macd_line > signal_line and histogram > 0
            is_bearish = macd_line < signal_line and histogram < 0
            
            # Check for crossovers (need at least 2 periods)
            if len(close_prices) >= 2:
                macd_prev = ta.trend.MACD(pd.Series(close_prices[:-1]), 
                                        window_fast=self.macd_fast,
                                        window_slow=self.macd_slow).iloc[-1]
                signal_prev = ta.trend.MACDSignal(pd.Series(close_prices[:-1]),
                                                window_fast=self.macd_fast,
                                                window_slow=self.macd_slow,
                                                window_sign=self.macd_signal).iloc[-1]
                
                # Bullish crossover: MACD crosses above signal
                if macd_prev <= signal_prev and macd_line > signal_line:
                    crossover_signal = 'bullish'
                # Bearish crossover: MACD crosses below signal
                elif macd_prev >= signal_prev and macd_line < signal_line:
                    crossover_signal = 'bearish'
                else:
                    crossover_signal = 'none'
            else:
                crossover_signal = 'none'
            
            return MACDResult(
                macd_line=macd_line,
                signal_line=signal_line,
                histogram=histogram,
                is_bullish=is_bullish,
                is_bearish=is_bearish,
                crossover_signal=crossover_signal
            )
            
        except Exception as e:
            logger.warning(f"Error calculating MACD: {e}")
            return MACDResult(0, 0, 0, False, False, 'none')
    
    def calculate_emas(self, price_data: pd.DataFrame, current_price: float) -> EMAResult:
        """Calculate Exponential Moving Averages"""
        try:
            close_prices = pd.Series(price_data['close'].values)
            
            # Calculate EMAs
            ema_9 = ta.trend.EMAIndicator(close_prices, window=9).ema_indicator().iloc[-1]
            ema_20 = ta.trend.EMAIndicator(close_prices, window=20).ema_indicator().iloc[-1]
            ema_50 = ta.trend.EMAIndicator(close_prices, window=50).ema_indicator().iloc[-1]
            ema_200 = ta.trend.EMAIndicator(close_prices, window=200).ema_indicator().iloc[-1]
            
            # Determine trend direction
            if ema_9 > ema_20 > ema_50 > ema_200:
                trend_direction = 'bullish'
            elif ema_9 < ema_20 < ema_50 < ema_200:
                trend_direction = 'bearish'
            else:
                trend_direction = 'sideways'
            
            # Price position relative to EMAs
            price_above_ema9 = current_price > ema_9
            price_above_ema20 = current_price > ema_20
            
            # Golden/Death cross detection
            golden_cross = ema_50 > ema_200
            death_cross = ema_50 < ema_200
            
            return EMAResult(
                ema_9=ema_9,
                ema_20=ema_20,
                ema_50=ema_50,
                ema_200=ema_200,
                trend_direction=trend_direction,
                price_above_ema9=price_above_ema9,
                price_above_ema20=price_above_ema20,
                golden_cross=golden_cross,
                death_cross=death_cross
            )
            
        except Exception as e:
            logger.warning(f"Error calculating EMAs: {e}")
            return EMAResult(0, 0, 0, 0, 'sideways', False, False, False, False)
    
    def calculate_rsi(self, price_data: pd.DataFrame) -> RSIResult:
        """Calculate RSI indicator"""
        try:
            close_prices = pd.Series(price_data['close'].values)
            
            # Calculate RSI
            rsi = ta.momentum.RSIIndicator(close_prices, window=self.rsi_period).rsi().iloc[-1]
            
            # Determine conditions
            is_overbought = rsi > 70
            is_oversold = rsi < 30
            
            # Momentum direction
            if rsi > 60:
                momentum_direction = 'bullish'
            elif rsi < 40:
                momentum_direction = 'bearish'
            else:
                momentum_direction = 'neutral'
            
            return RSIResult(
                rsi=rsi,
                is_overbought=is_overbought,
                is_oversold=is_oversold,
                momentum_direction=momentum_direction
            )
            
        except Exception as e:
            logger.warning(f"Error calculating RSI: {e}")
            return RSIResult(50, False, False, 'neutral')
    
    def calculate_volume_indicators(self, price_data: pd.DataFrame, current_volume: int) -> VolumeIndicators:
        """Calculate volume-based indicators"""
        try:
            volumes = price_data['volume'].values
            
            # Volume SMA
            volume_sma_20 = np.mean(volumes[-self.volume_sma_period:])
            
            # Relative volume
            relative_volume = current_volume / volume_sma_20 if volume_sma_20 > 0 else 1.0
            
            # Volume trend (last 5 periods)
            if len(volumes) >= 5:
                recent_avg = np.mean(volumes[-5:])
                previous_avg = np.mean(volumes[-10:-5]) if len(volumes) >= 10 else volume_sma_20
                
                if recent_avg > previous_avg * 1.2:
                    volume_trend = 'increasing'
                elif recent_avg < previous_avg * 0.8:
                    volume_trend = 'decreasing'
                else:
                    volume_trend = 'stable'
            else:
                volume_trend = 'stable'
            
            # Volume breakout (Ross Cameron's 2x rule)
            volume_breakout = relative_volume >= 2.0
            
            return VolumeIndicators(
                volume_sma_20=volume_sma_20,
                relative_volume=relative_volume,
                volume_trend=volume_trend,
                volume_breakout=volume_breakout
            )
            
        except Exception as e:
            logger.warning(f"Error calculating volume indicators: {e}")
            return VolumeIndicators(0, 1.0, 'stable', False)
    
    def _calculate_overall_signal(self, 
                                macd: MACDResult, 
                                ema: EMAResult, 
                                rsi: RSIResult, 
                                volume: VolumeIndicators) -> Tuple[str, float]:
        """Calculate overall signal strength and direction"""
        try:
            score = 0
            max_score = 100
            
            # MACD signals (25 points)
            if macd.crossover_signal == 'bullish':
                score += 25
            elif macd.crossover_signal == 'bearish':
                score -= 25
            elif macd.is_bullish:
                score += 15
            elif macd.is_bearish:
                score -= 15
            
            # EMA trend signals (25 points)
            if ema.trend_direction == 'bullish':
                score += 25
            elif ema.trend_direction == 'bearish':
                score -= 25
            
            # Price above EMAs (15 points)
            if ema.price_above_ema9 and ema.price_above_ema20:
                score += 15
            elif not ema.price_above_ema9 and not ema.price_above_ema20:
                score -= 15
            
            # RSI momentum (15 points)
            if rsi.momentum_direction == 'bullish' and not rsi.is_overbought:
                score += 15
            elif rsi.momentum_direction == 'bearish' and not rsi.is_oversold:
                score -= 15
            elif rsi.is_oversold:  # Potential reversal
                score += 10
            elif rsi.is_overbought:  # Potential reversal
                score -= 10
            
            # Volume confirmation (20 points)
            if volume.volume_breakout:
                score += 20
            elif volume.volume_trend == 'increasing':
                score += 10
            elif volume.volume_trend == 'decreasing':
                score -= 10
            
            # Normalize score to 0-100
            signal_strength = max(0, min(100, (score + max_score) / 2))
            
            # Determine overall signal
            if signal_strength >= 80:
                overall_signal = 'strong_buy'
            elif signal_strength >= 65:
                overall_signal = 'buy'
            elif signal_strength >= 35:
                overall_signal = 'hold'
            elif signal_strength >= 20:
                overall_signal = 'sell'
            else:
                overall_signal = 'strong_sell'
            
            return overall_signal, signal_strength
            
        except Exception as e:
            logger.warning(f"Error calculating overall signal: {e}")
            return 'hold', 50.0
    
    def _is_entry_signal(self, 
                        macd: MACDResult, 
                        ema: EMAResult, 
                        rsi: RSIResult, 
                        volume: VolumeIndicators) -> bool:
        """Determine if current conditions represent an entry signal"""
        try:
            # Ross Cameron's entry criteria
            entry_conditions = [
                macd.crossover_signal == 'bullish',  # MACD bullish crossover
                ema.price_above_ema9,  # Price above 9 EMA
                not rsi.is_overbought,  # Not overbought
                volume.volume_breakout,  # High volume confirmation
                ema.trend_direction in ['bullish', 'sideways']  # Favorable trend
            ]
            
            # Need at least 3 out of 5 conditions
            return sum(entry_conditions) >= 3
            
        except Exception as e:
            logger.warning(f"Error determining entry signal: {e}")
            return False
    
    def _is_exit_signal(self, 
                       macd: MACDResult, 
                       ema: EMAResult, 
                       rsi: RSIResult) -> bool:
        """Determine if current conditions represent an exit signal"""
        try:
            # Ross Cameron's exit criteria
            exit_conditions = [
                macd.crossover_signal == 'bearish',  # MACD bearish crossover
                not ema.price_above_ema9,  # Price below 9 EMA
                rsi.is_overbought,  # Overbought condition
                ema.trend_direction == 'bearish'  # Bearish trend
            ]
            
            # Need at least 2 out of 4 conditions
            return sum(exit_conditions) >= 2
            
        except Exception as e:
            logger.warning(f"Error determining exit signal: {e}")
            return False
    
    def _create_default_signals(self) -> TechnicalSignals:
        """Create default signals when calculation fails"""
        return TechnicalSignals(
            macd=MACDResult(0, 0, 0, False, False, 'none'),
            ema=EMAResult(0, 0, 0, 0, 'sideways', False, False, False, False),
            rsi=RSIResult(50, False, False, 'neutral'),
            volume=VolumeIndicators(0, 1.0, 'stable', False),
            overall_signal='hold',
            signal_strength=50.0,
            entry_signal=False,
            exit_signal=False
        )
    
    def get_fibonacci_levels(self, high: float, low: float) -> Dict[str, float]:
        """Calculate Fibonacci retracement levels"""
        try:
            diff = high - low
            
            levels = {
                '0%': high,
                '23.6%': high - (diff * 0.236),
                '38.2%': high - (diff * 0.382),
                '50%': high - (diff * 0.5),
                '61.8%': high - (diff * 0.618),
                '78.6%': high - (diff * 0.786),
                '100%': low
            }
            
            return levels
            
        except Exception as e:
            logger.warning(f"Error calculating Fibonacci levels: {e}")
            return {}
    
    def detect_divergence(self, price_data: pd.DataFrame) -> Dict[str, bool]:
        """Detect bullish/bearish divergence between price and RSI"""
        try:
            if len(price_data) < 20:
                return {'bullish_divergence': False, 'bearish_divergence': False}
            
            close_prices = pd.Series(price_data['close'].values)
            rsi_values = ta.momentum.RSIIndicator(close_prices, window=self.rsi_period).rsi()
            
            # Find recent peaks and troughs
            price_peaks = signal.find_peaks(close_prices.values, distance=5)[0]
            price_troughs = signal.find_peaks(-close_prices.values, distance=5)[0]
            rsi_peaks = signal.find_peaks(rsi_values.values, distance=5)[0]
            rsi_troughs = signal.find_peaks(-rsi_values.values, distance=5)[0]
            
            bullish_divergence = False
            bearish_divergence = False
            
            # Check for bullish divergence (price makes lower low, RSI makes higher low)
            if len(price_troughs) >= 2 and len(rsi_troughs) >= 2:
                recent_price_trough = price_troughs[-1]
                prev_price_trough = price_troughs[-2]
                
                for rsi_trough in rsi_troughs[-2:]:
                    if abs(rsi_trough - recent_price_trough) <= 3:  # Close in time
                        for prev_rsi_trough in rsi_troughs[-3:-1]:
                            if abs(prev_rsi_trough - prev_price_trough) <= 3:
                                if (close_prices.iloc[recent_price_trough] < close_prices.iloc[prev_price_trough] and
                                    rsi_values.iloc[rsi_trough] > rsi_values.iloc[prev_rsi_trough]):
                                    bullish_divergence = True
                                    break
            
            # Check for bearish divergence (price makes higher high, RSI makes lower high)
            if len(price_peaks) >= 2 and len(rsi_peaks) >= 2:
                recent_price_peak = price_peaks[-1]
                prev_price_peak = price_peaks[-2]
                
                for rsi_peak in rsi_peaks[-2:]:
                    if abs(rsi_peak - recent_price_peak) <= 3:  # Close in time
                        for prev_rsi_peak in rsi_peaks[-3:-1]:
                            if abs(prev_rsi_peak - prev_price_peak) <= 3:
                                if (close_prices.iloc[recent_price_peak] > close_prices.iloc[prev_price_peak] and
                                    rsi_values.iloc[rsi_peak] < rsi_values.iloc[prev_rsi_peak]):
                                    bearish_divergence = True
                                    break
            
            return {
                'bullish_divergence': bullish_divergence,
                'bearish_divergence': bearish_divergence
            }
            
        except Exception as e:
            logger.warning(f"Error detecting divergence: {e}")
            return {'bullish_divergence': False, 'bearish_divergence': False}

