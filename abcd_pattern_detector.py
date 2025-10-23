"""
ABCD Pattern Detector - Ross Cameron's favorite breakout pattern
Detects ABCD patterns for precise entry and exit timing
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from scipy import signal
import math

from ..core.logger import get_logger

logger = get_logger(__name__)

@dataclass
class ABCDPoint:
    """Represents a point in the ABCD pattern"""
    index: int
    price: float
    timestamp: pd.Timestamp
    point_type: str  # 'A', 'B', 'C', 'D'

@dataclass
class ABCDPattern:
    """Complete ABCD pattern"""
    point_a: ABCDPoint
    point_b: ABCDPoint
    point_c: ABCDPoint
    point_d: Optional[ABCDPoint]
    pattern_type: str  # 'bullish', 'bearish'
    completion_ratio: float  # How complete the pattern is (0-1)
    fibonacci_ratio_ab_cd: float  # AB/CD ratio
    fibonacci_ratio_bc_cd: float  # BC/CD ratio
    is_valid: bool
    confidence: float  # 0-100
    projected_target: Optional[float]
    stop_loss_level: Optional[float]
    entry_price: Optional[float]
    pattern_strength: str  # 'weak', 'moderate', 'strong'

@dataclass
class ABCDAnalysis:
    """Complete ABCD analysis result"""
    patterns_found: List[ABCDPattern]
    active_pattern: Optional[ABCDPattern]
    potential_patterns: List[ABCDPattern]  # Incomplete patterns
    entry_signals: List[Dict[str, Any]]
    exit_signals: List[Dict[str, Any]]
    pattern_summary: Dict[str, int]

class ABCDPatternDetector:
    """Detects ABCD patterns in price data using Ross Cameron's methodology"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # ABCD pattern parameters
        self.min_pattern_length = 10  # Minimum bars for pattern
        self.max_pattern_length = 50  # Maximum bars for pattern
        self.fibonacci_tolerance = 0.1  # 10% tolerance for Fibonacci ratios
        self.min_retracement = 0.382  # Minimum retracement for C point
        self.max_retracement = 0.786  # Maximum retracement for C point
        
        # Ideal Fibonacci ratios for ABCD patterns
        self.ideal_ab_cd_ratio = 1.0  # AB = CD (1:1 ratio)
        self.ideal_bc_cd_ratio = 0.618  # BC = 61.8% of CD
        
        logger.info("ABCD Pattern Detector initialized")
    
    def analyze_abcd_patterns(self, price_data: pd.DataFrame) -> ABCDAnalysis:
        """
        Analyze price data for ABCD patterns
        
        Args:
            price_data: DataFrame with OHLCV data
            
        Returns:
            ABCDAnalysis with all detected patterns
        """
        try:
            if len(price_data) < self.min_pattern_length:
                logger.warning("Insufficient data for ABCD pattern analysis")
                return self._create_empty_analysis()
            
            # Find swing points (peaks and troughs)
            swing_points = self._find_swing_points(price_data)
            
            if len(swing_points) < 3:
                logger.info("Not enough swing points for ABCD patterns")
                return self._create_empty_analysis()
            
            # Detect complete patterns
            complete_patterns = self._detect_complete_patterns(swing_points, price_data)
            
            # Detect potential/incomplete patterns
            potential_patterns = self._detect_potential_patterns(swing_points, price_data)
            
            # Find active pattern (most recent and relevant)
            active_pattern = self._find_active_pattern(complete_patterns, potential_patterns)
            
            # Generate entry/exit signals
            entry_signals = self._generate_entry_signals(complete_patterns, potential_patterns, price_data)
            exit_signals = self._generate_exit_signals(complete_patterns, price_data)
            
            # Create pattern summary
            pattern_summary = self._create_pattern_summary(complete_patterns, potential_patterns)
            
            return ABCDAnalysis(
                patterns_found=complete_patterns,
                active_pattern=active_pattern,
                potential_patterns=potential_patterns,
                entry_signals=entry_signals,
                exit_signals=exit_signals,
                pattern_summary=pattern_summary
            )
            
        except Exception as e:
            logger.error(f"Error analyzing ABCD patterns: {e}")
            return self._create_empty_analysis()
    
    def _find_swing_points(self, price_data: pd.DataFrame) -> List[ABCDPoint]:
        """Find significant swing highs and lows"""
        try:
            high_prices = price_data['high'].values
            low_prices = price_data['low'].values
            timestamps = price_data.index
            
            # Find peaks (swing highs)
            peak_indices = signal.find_peaks(high_prices, 
                                           distance=3,  # Minimum distance between peaks
                                           prominence=np.std(high_prices) * 0.5)[0]
            
            # Find troughs (swing lows)
            trough_indices = signal.find_peaks(-low_prices,
                                             distance=3,  # Minimum distance between troughs
                                             prominence=np.std(low_prices) * 0.5)[0]
            
            # Combine and sort swing points
            swing_points = []
            
            # Add peaks
            for idx in peak_indices:
                swing_points.append(ABCDPoint(
                    index=idx,
                    price=high_prices[idx],
                    timestamp=timestamps[idx],
                    point_type='peak'
                ))
            
            # Add troughs
            for idx in trough_indices:
                swing_points.append(ABCDPoint(
                    index=idx,
                    price=low_prices[idx],
                    timestamp=timestamps[idx],
                    point_type='trough'
                ))
            
            # Sort by index
            swing_points.sort(key=lambda x: x.index)
            
            logger.debug(f"Found {len(swing_points)} swing points")
            return swing_points
            
        except Exception as e:
            logger.warning(f"Error finding swing points: {e}")
            return []
    
    def _detect_complete_patterns(self, swing_points: List[ABCDPoint], price_data: pd.DataFrame) -> List[ABCDPattern]:
        """Detect complete ABCD patterns"""
        patterns = []
        
        try:
            # Need at least 4 swing points for a complete pattern
            if len(swing_points) < 4:
                return patterns
            
            # Look for ABCD patterns in recent swing points
            for i in range(len(swing_points) - 3):
                for j in range(i + 1, min(i + 8, len(swing_points) - 2)):  # Limit search range
                    for k in range(j + 1, min(j + 8, len(swing_points) - 1)):
                        for l in range(k + 1, min(k + 8, len(swing_points))):
                            
                            # Check if indices are within reasonable range
                            if swing_points[l].index - swing_points[i].index > self.max_pattern_length:
                                continue
                            
                            pattern = self._validate_abcd_pattern(
                                swing_points[i], swing_points[j], 
                                swing_points[k], swing_points[l]
                            )
                            
                            if pattern and pattern.is_valid:
                                patterns.append(pattern)
            
            # Sort by confidence and recency
            patterns.sort(key=lambda x: (x.confidence, x.point_d.index if x.point_d else 0), reverse=True)
            
            # Remove overlapping patterns (keep best ones)
            filtered_patterns = self._filter_overlapping_patterns(patterns)
            
            logger.info(f"Detected {len(filtered_patterns)} complete ABCD patterns")
            return filtered_patterns
            
        except Exception as e:
            logger.warning(f"Error detecting complete patterns: {e}")
            return []
    
    def _detect_potential_patterns(self, swing_points: List[ABCDPoint], price_data: pd.DataFrame) -> List[ABCDPattern]:
        """Detect potential/incomplete ABCD patterns (ABC completed, waiting for D)"""
        patterns = []
        
        try:
            # Need at least 3 swing points for potential pattern
            if len(swing_points) < 3:
                return patterns
            
            current_price = price_data['close'].iloc[-1]
            
            # Look for ABC patterns that could complete
            for i in range(len(swing_points) - 2):
                for j in range(i + 1, min(i + 6, len(swing_points) - 1)):
                    for k in range(j + 1, min(j + 6, len(swing_points))):
                        
                        # Check if pattern is recent enough
                        if len(price_data) - swing_points[k].index > 20:  # Not too old
                            continue
                        
                        # Validate ABC portion
                        abc_pattern = self._validate_abc_pattern(
                            swing_points[i], swing_points[j], swing_points[k], current_price
                        )
                        
                        if abc_pattern and abc_pattern.completion_ratio >= 0.75:
                            patterns.append(abc_pattern)
            
            # Sort by completion ratio and recency
            patterns.sort(key=lambda x: (x.completion_ratio, x.point_c.index), reverse=True)
            
            logger.info(f"Detected {len(patterns)} potential ABCD patterns")
            return patterns[:5]  # Keep top 5
            
        except Exception as e:
            logger.warning(f"Error detecting potential patterns: {e}")
            return []
    
    def _validate_abcd_pattern(self, point_a: ABCDPoint, point_b: ABCDPoint, 
                              point_c: ABCDPoint, point_d: ABCDPoint) -> Optional[ABCDPattern]:
        """Validate if four points form a valid ABCD pattern"""
        try:
            # Determine pattern type based on point sequence
            if ((point_a.point_type == 'trough' and point_b.point_type == 'peak' and 
                 point_c.point_type == 'trough' and point_d.point_type == 'peak') or
                (point_a.point_type == 'peak' and point_b.point_type == 'trough' and 
                 point_c.point_type == 'peak' and point_d.point_type == 'trough')):
                
                pattern_type = 'bullish' if point_a.point_type == 'trough' else 'bearish'
                
                # Calculate pattern metrics
                ab_distance = abs(point_b.price - point_a.price)
                bc_distance = abs(point_c.price - point_b.price)
                cd_distance = abs(point_d.price - point_c.price)
                
                # Calculate Fibonacci ratios
                ab_cd_ratio = cd_distance / ab_distance if ab_distance > 0 else 0
                bc_cd_ratio = bc_distance / cd_distance if cd_distance > 0 else 0
                
                # Calculate retracement ratios
                if pattern_type == 'bullish':
                    bc_retracement = bc_distance / ab_distance if ab_distance > 0 else 0
                else:
                    bc_retracement = bc_distance / ab_distance if ab_distance > 0 else 0
                
                # Validate pattern criteria
                is_valid = self._is_valid_abcd_ratios(ab_cd_ratio, bc_cd_ratio, bc_retracement)
                
                # Calculate confidence
                confidence = self._calculate_pattern_confidence(ab_cd_ratio, bc_cd_ratio, bc_retracement)
                
                # Calculate targets and stops
                projected_target = self._calculate_target_price(point_a, point_b, point_c, point_d, pattern_type)
                stop_loss_level = self._calculate_stop_loss(point_c, point_d, pattern_type)
                entry_price = point_d.price
                
                # Determine pattern strength
                pattern_strength = self._determine_pattern_strength(confidence, ab_cd_ratio, bc_cd_ratio)
                
                return ABCDPattern(
                    point_a=point_a,
                    point_b=point_b,
                    point_c=point_c,
                    point_d=point_d,
                    pattern_type=pattern_type,
                    completion_ratio=1.0,
                    fibonacci_ratio_ab_cd=ab_cd_ratio,
                    fibonacci_ratio_bc_cd=bc_cd_ratio,
                    is_valid=is_valid,
                    confidence=confidence,
                    projected_target=projected_target,
                    stop_loss_level=stop_loss_level,
                    entry_price=entry_price,
                    pattern_strength=pattern_strength
                )
            
            return None
            
        except Exception as e:
            logger.warning(f"Error validating ABCD pattern: {e}")
            return None
    
    def _validate_abc_pattern(self, point_a: ABCDPoint, point_b: ABCDPoint, 
                             point_c: ABCDPoint, current_price: float) -> Optional[ABCDPattern]:
        """Validate ABC portion and project potential D point"""
        try:
            # Check if ABC forms valid sequence
            if ((point_a.point_type == 'trough' and point_b.point_type == 'peak' and point_c.point_type == 'trough') or
                (point_a.point_type == 'peak' and point_b.point_type == 'trough' and point_c.point_type == 'peak')):
                
                pattern_type = 'bullish' if point_a.point_type == 'trough' else 'bearish'
                
                # Calculate AB and BC distances
                ab_distance = abs(point_b.price - point_a.price)
                bc_distance = abs(point_c.price - point_b.price)
                
                # Calculate retracement
                bc_retracement = bc_distance / ab_distance if ab_distance > 0 else 0
                
                # Check if retracement is within valid range
                if self.min_retracement <= bc_retracement <= self.max_retracement:
                    
                    # Project D point based on ideal ratios
                    projected_cd_distance = ab_distance * self.ideal_ab_cd_ratio
                    
                    if pattern_type == 'bullish':
                        projected_d_price = point_c.price + projected_cd_distance
                    else:
                        projected_d_price = point_c.price - projected_cd_distance
                    
                    # Calculate how close current price is to projected D
                    price_diff = abs(current_price - projected_d_price)
                    max_diff = ab_distance * 0.2  # 20% tolerance
                    
                    completion_ratio = max(0, 1 - (price_diff / max_diff)) if max_diff > 0 else 0
                    
                    # Calculate confidence for ABC portion
                    confidence = self._calculate_abc_confidence(bc_retracement, completion_ratio)
                    
                    # Create projected D point
                    projected_d = ABCDPoint(
                        index=len(point_c.timestamp) if hasattr(point_c.timestamp, '__len__') else point_c.index + 5,
                        price=projected_d_price,
                        timestamp=point_c.timestamp,
                        point_type='peak' if pattern_type == 'bullish' else 'trough'
                    )
                    
                    return ABCDPattern(
                        point_a=point_a,
                        point_b=point_b,
                        point_c=point_c,
                        point_d=projected_d,
                        pattern_type=pattern_type,
                        completion_ratio=completion_ratio,
                        fibonacci_ratio_ab_cd=self.ideal_ab_cd_ratio,
                        fibonacci_ratio_bc_cd=bc_distance / projected_cd_distance if projected_cd_distance > 0 else 0,
                        is_valid=completion_ratio >= 0.75,
                        confidence=confidence,
                        projected_target=self._calculate_target_price(point_a, point_b, point_c, projected_d, pattern_type),
                        stop_loss_level=self._calculate_stop_loss(point_c, projected_d, pattern_type),
                        entry_price=projected_d_price,
                        pattern_strength=self._determine_pattern_strength(confidence, self.ideal_ab_cd_ratio, bc_distance / projected_cd_distance if projected_cd_distance > 0 else 0)
                    )
            
            return None
            
        except Exception as e:
            logger.warning(f"Error validating ABC pattern: {e}")
            return None
    
    def _is_valid_abcd_ratios(self, ab_cd_ratio: float, bc_cd_ratio: float, bc_retracement: float) -> bool:
        """Check if ratios are within valid ABCD pattern ranges"""
        try:
            # AB:CD ratio should be close to 1.0 (ideal) or 0.618/1.618 (Fibonacci)
            ab_cd_valid = (abs(ab_cd_ratio - 1.0) <= self.fibonacci_tolerance or
                          abs(ab_cd_ratio - 0.618) <= self.fibonacci_tolerance or
                          abs(ab_cd_ratio - 1.618) <= self.fibonacci_tolerance)
            
            # BC retracement should be between 38.2% and 78.6%
            retracement_valid = self.min_retracement <= bc_retracement <= self.max_retracement
            
            return ab_cd_valid and retracement_valid
            
        except Exception:
            return False
    
    def _calculate_pattern_confidence(self, ab_cd_ratio: float, bc_cd_ratio: float, bc_retracement: float) -> float:
        """Calculate confidence score for ABCD pattern"""
        try:
            confidence = 0
            
            # AB:CD ratio score (40 points max)
            if abs(ab_cd_ratio - 1.0) <= 0.05:  # Very close to 1:1
                confidence += 40
            elif abs(ab_cd_ratio - 1.0) <= self.fibonacci_tolerance:
                confidence += 30
            elif abs(ab_cd_ratio - 0.618) <= self.fibonacci_tolerance or abs(ab_cd_ratio - 1.618) <= self.fibonacci_tolerance:
                confidence += 25
            
            # BC retracement score (30 points max)
            if abs(bc_retracement - 0.618) <= 0.05:  # Close to golden ratio
                confidence += 30
            elif abs(bc_retracement - 0.5) <= 0.05:  # Close to 50%
                confidence += 25
            elif self.min_retracement <= bc_retracement <= self.max_retracement:
                confidence += 20
            
            # BC:CD ratio score (30 points max)
            if abs(bc_cd_ratio - 0.618) <= 0.05:
                confidence += 30
            elif abs(bc_cd_ratio - 0.5) <= 0.1:
                confidence += 20
            elif 0.3 <= bc_cd_ratio <= 0.8:
                confidence += 15
            
            return min(confidence, 100)
            
        except Exception:
            return 0
    
    def _calculate_abc_confidence(self, bc_retracement: float, completion_ratio: float) -> float:
        """Calculate confidence for ABC portion of pattern"""
        try:
            confidence = 0
            
            # Retracement quality (50 points max)
            if abs(bc_retracement - 0.618) <= 0.05:
                confidence += 50
            elif abs(bc_retracement - 0.5) <= 0.05:
                confidence += 40
            elif self.min_retracement <= bc_retracement <= self.max_retracement:
                confidence += 30
            
            # Completion ratio (50 points max)
            confidence += completion_ratio * 50
            
            return min(confidence, 100)
            
        except Exception:
            return 0
    
    def _calculate_target_price(self, point_a: ABCDPoint, point_b: ABCDPoint, 
                               point_c: ABCDPoint, point_d: ABCDPoint, pattern_type: str) -> float:
        """Calculate price target based on ABCD pattern"""
        try:
            cd_distance = abs(point_d.price - point_c.price)
            
            if pattern_type == 'bullish':
                # Target is D + extension
                target = point_d.price + (cd_distance * 0.618)  # 61.8% extension
            else:
                # Target is D - extension
                target = point_d.price - (cd_distance * 0.618)  # 61.8% extension
            
            return target
            
        except Exception:
            return point_d.price
    
    def _calculate_stop_loss(self, point_c: ABCDPoint, point_d: ABCDPoint, pattern_type: str) -> float:
        """Calculate stop loss level"""
        try:
            if pattern_type == 'bullish':
                # Stop below C point
                return point_c.price * 0.98  # 2% below C
            else:
                # Stop above C point
                return point_c.price * 1.02  # 2% above C
                
        except Exception:
            return point_d.price
    
    def _determine_pattern_strength(self, confidence: float, ab_cd_ratio: float, bc_cd_ratio: float) -> str:
        """Determine pattern strength based on various factors"""
        try:
            if confidence >= 80 and abs(ab_cd_ratio - 1.0) <= 0.1:
                return 'strong'
            elif confidence >= 60:
                return 'moderate'
            else:
                return 'weak'
                
        except Exception:
            return 'weak'
    
    def _find_active_pattern(self, complete_patterns: List[ABCDPattern], 
                           potential_patterns: List[ABCDPattern]) -> Optional[ABCDPattern]:
        """Find the most relevant active pattern"""
        try:
            # Prefer complete patterns with high confidence
            for pattern in complete_patterns:
                if pattern.confidence >= 70 and pattern.pattern_strength in ['strong', 'moderate']:
                    return pattern
            
            # Fall back to potential patterns
            for pattern in potential_patterns:
                if pattern.completion_ratio >= 0.8 and pattern.confidence >= 60:
                    return pattern
            
            # Return best available pattern
            if complete_patterns:
                return complete_patterns[0]
            elif potential_patterns:
                return potential_patterns[0]
            
            return None
            
        except Exception:
            return None
    
    def _generate_entry_signals(self, complete_patterns: List[ABCDPattern], 
                               potential_patterns: List[ABCDPattern], 
                               price_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generate entry signals based on ABCD patterns"""
        signals = []
        
        try:
            current_price = price_data['close'].iloc[-1]
            
            # Check complete patterns for entry opportunities
            for pattern in complete_patterns:
                if pattern.confidence >= 60:
                    # Entry signal if price is near D point
                    price_diff = abs(current_price - pattern.point_d.price)
                    entry_tolerance = abs(pattern.point_d.price - pattern.point_c.price) * 0.1
                    
                    if price_diff <= entry_tolerance:
                        signals.append({
                            'type': 'entry',
                            'pattern_type': pattern.pattern_type,
                            'entry_price': pattern.entry_price,
                            'target_price': pattern.projected_target,
                            'stop_loss': pattern.stop_loss_level,
                            'confidence': pattern.confidence,
                            'pattern_strength': pattern.pattern_strength,
                            'signal_strength': 'strong' if pattern.confidence >= 80 else 'moderate'
                        })
            
            # Check potential patterns for anticipated entries
            for pattern in potential_patterns:
                if pattern.completion_ratio >= 0.8:
                    signals.append({
                        'type': 'anticipated_entry',
                        'pattern_type': pattern.pattern_type,
                        'entry_price': pattern.entry_price,
                        'target_price': pattern.projected_target,
                        'stop_loss': pattern.stop_loss_level,
                        'confidence': pattern.confidence,
                        'completion_ratio': pattern.completion_ratio,
                        'signal_strength': 'moderate'
                    })
            
            return signals
            
        except Exception as e:
            logger.warning(f"Error generating entry signals: {e}")
            return []
    
    def _generate_exit_signals(self, complete_patterns: List[ABCDPattern], 
                              price_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generate exit signals based on ABCD patterns"""
        signals = []
        
        try:
            current_price = price_data['close'].iloc[-1]
            
            for pattern in complete_patterns:
                if pattern.projected_target and pattern.stop_loss_level:
                    
                    # Check if target is reached
                    if pattern.pattern_type == 'bullish' and current_price >= pattern.projected_target:
                        signals.append({
                            'type': 'take_profit',
                            'reason': 'target_reached',
                            'exit_price': pattern.projected_target,
                            'pattern_type': pattern.pattern_type,
                            'signal_strength': 'strong'
                        })
                    elif pattern.pattern_type == 'bearish' and current_price <= pattern.projected_target:
                        signals.append({
                            'type': 'take_profit',
                            'reason': 'target_reached',
                            'exit_price': pattern.projected_target,
                            'pattern_type': pattern.pattern_type,
                            'signal_strength': 'strong'
                        })
                    
                    # Check if stop loss is hit
                    if pattern.pattern_type == 'bullish' and current_price <= pattern.stop_loss_level:
                        signals.append({
                            'type': 'stop_loss',
                            'reason': 'stop_hit',
                            'exit_price': pattern.stop_loss_level,
                            'pattern_type': pattern.pattern_type,
                            'signal_strength': 'strong'
                        })
                    elif pattern.pattern_type == 'bearish' and current_price >= pattern.stop_loss_level:
                        signals.append({
                            'type': 'stop_loss',
                            'reason': 'stop_hit',
                            'exit_price': pattern.stop_loss_level,
                            'pattern_type': pattern.pattern_type,
                            'signal_strength': 'strong'
                        })
            
            return signals
            
        except Exception as e:
            logger.warning(f"Error generating exit signals: {e}")
            return []
    
    def _create_pattern_summary(self, complete_patterns: List[ABCDPattern], 
                               potential_patterns: List[ABCDPattern]) -> Dict[str, int]:
        """Create summary statistics of detected patterns"""
        try:
            summary = {
                'total_complete_patterns': len(complete_patterns),
                'total_potential_patterns': len(potential_patterns),
                'bullish_complete': len([p for p in complete_patterns if p.pattern_type == 'bullish']),
                'bearish_complete': len([p for p in complete_patterns if p.pattern_type == 'bearish']),
                'bullish_potential': len([p for p in potential_patterns if p.pattern_type == 'bullish']),
                'bearish_potential': len([p for p in potential_patterns if p.pattern_type == 'bearish']),
                'strong_patterns': len([p for p in complete_patterns if p.pattern_strength == 'strong']),
                'high_confidence_patterns': len([p for p in complete_patterns if p.confidence >= 80])
            }
            
            return summary
            
        except Exception:
            return {}
    
    def _filter_overlapping_patterns(self, patterns: List[ABCDPattern]) -> List[ABCDPattern]:
        """Remove overlapping patterns, keeping the best ones"""
        try:
            if not patterns:
                return []
            
            filtered = []
            
            for pattern in patterns:
                # Check if this pattern overlaps with any already filtered pattern
                overlaps = False
                
                for existing in filtered:
                    # Check if patterns overlap in time
                    if (pattern.point_a.index <= existing.point_d.index and 
                        pattern.point_d.index >= existing.point_a.index):
                        overlaps = True
                        break
                
                if not overlaps:
                    filtered.append(pattern)
            
            return filtered
            
        except Exception:
            return patterns
    
    def _create_empty_analysis(self) -> ABCDAnalysis:
        """Create empty analysis result"""
        return ABCDAnalysis(
            patterns_found=[],
            active_pattern=None,
            potential_patterns=[],
            entry_signals=[],
            exit_signals=[],
            pattern_summary={}
        )

