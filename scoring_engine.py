"""
Scoring Engine - Comprehensive scoring system combining all analysis components
Implements Ross Cameron's methodology with AI enhancements
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import math

from ..core.logger import get_logger

logger = get_logger(__name__)

@dataclass
class ComponentScore:
    """Individual component score"""
    component: str
    raw_score: float  # 0-100
    weight: float     # 0-1
    weighted_score: float  # raw_score * weight
    confidence: float # 0-1
    details: Dict[str, Any]

@dataclass
class CompositeScore:
    """Complete composite score for a stock"""
    symbol: str
    overall_score: float  # 0-100
    component_scores: List[ComponentScore]
    confidence_level: float  # 0-1
    risk_level: str  # 'low', 'medium', 'high'
    signal_strength: str  # 'weak', 'moderate', 'strong', 'very_strong'
    recommendation: str  # 'strong_buy', 'buy', 'hold', 'sell', 'strong_sell'
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    position_size: Optional[float]
    time_horizon: str  # 'scalp', 'day_trade', 'swing', 'position'
    urgency: str  # 'immediate', 'high', 'medium', 'low'
    
@dataclass
class RossScore:
    """Ross Cameron specific scoring"""
    pillar_1_volume: float    # High relative volume (0-100)
    pillar_2_price_change: float  # Significant price change (0-100)
    pillar_3_float: float     # Low float (0-100)
    pillar_4_catalyst: float  # News catalyst (0-100)
    pillar_5_price_range: float  # Price under $20 (0-100)
    overall_ross_score: float # Combined Ross Cameron score
    ross_grade: str          # A+, A, B+, B, C+, C, D, F

class ScoringEngine:
    """Comprehensive scoring engine for momentum trading"""
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Component weights (must sum to 1.0)
        self.component_weights = {
            'fundamental': 0.25,  # Float, price range, sector
            'technical': 0.30,    # MACD, EMA, RSI, patterns
            'news_sentiment': 0.25,  # News sentiment and catalysts
            'volume_momentum': 0.20  # Volume and momentum indicators
        }
        
        # Ross Cameron pillar weights
        self.ross_pillar_weights = {
            'volume': 0.25,      # High relative volume
            'price_change': 0.20, # Significant price change
            'float': 0.25,       # Low float
            'catalyst': 0.20,    # News catalyst
            'price_range': 0.10  # Price under $20
        }
        
        # Risk thresholds
        self.risk_thresholds = {
            'low': {'max_rsi': 70, 'min_volume_ratio': 2.0, 'max_volatility': 0.15},
            'medium': {'max_rsi': 80, 'min_volume_ratio': 1.5, 'max_volatility': 0.25},
            'high': {'max_rsi': 90, 'min_volume_ratio': 1.0, 'max_volatility': 0.50}
        }
        
        logger.info("Scoring Engine initialized")
    
    def calculate_composite_score(self, symbol: str, 
                                fundamental_data: Dict,
                                technical_data: Dict,
                                news_data: Dict,
                                market_data: Dict) -> CompositeScore:
        """
        Calculate comprehensive composite score
        
        Args:
            symbol: Stock symbol
            fundamental_data: Fundamental analysis results
            technical_data: Technical analysis results
            news_data: News sentiment and catalyst data
            market_data: Current market data (price, volume, etc.)
            
        Returns:
            CompositeScore with complete analysis
        """
        try:
            logger.info(f"Calculating composite score for {symbol}")
            
            # Calculate individual component scores
            fundamental_score = self._calculate_fundamental_score(fundamental_data, market_data)
            technical_score = self._calculate_technical_score(technical_data, market_data)
            news_score = self._calculate_news_score(news_data)
            momentum_score = self._calculate_momentum_score(market_data, technical_data)
            
            # Create component score objects
            component_scores = [
                ComponentScore(
                    component='fundamental',
                    raw_score=fundamental_score['score'],
                    weight=self.component_weights['fundamental'],
                    weighted_score=fundamental_score['score'] * self.component_weights['fundamental'],
                    confidence=fundamental_score['confidence'],
                    details=fundamental_score['details']
                ),
                ComponentScore(
                    component='technical',
                    raw_score=technical_score['score'],
                    weight=self.component_weights['technical'],
                    weighted_score=technical_score['score'] * self.component_weights['technical'],
                    confidence=technical_score['confidence'],
                    details=technical_score['details']
                ),
                ComponentScore(
                    component='news_sentiment',
                    raw_score=news_score['score'],
                    weight=self.component_weights['news_sentiment'],
                    weighted_score=news_score['score'] * self.component_weights['news_sentiment'],
                    confidence=news_score['confidence'],
                    details=news_score['details']
                ),
                ComponentScore(
                    component='volume_momentum',
                    raw_score=momentum_score['score'],
                    weight=self.component_weights['volume_momentum'],
                    weighted_score=momentum_score['score'] * self.component_weights['volume_momentum'],
                    confidence=momentum_score['confidence'],
                    details=momentum_score['details']
                )
            ]
            
            # Calculate overall score
            overall_score = sum(cs.weighted_score for cs in component_scores)
            
            # Calculate confidence level
            confidence_level = np.mean([cs.confidence for cs in component_scores])
            
            # Determine risk level
            risk_level = self._determine_risk_level(technical_data, market_data, news_data)
            
            # Determine signal strength
            signal_strength = self._determine_signal_strength(overall_score, confidence_level)
            
            # Generate recommendation
            recommendation = self._generate_recommendation(overall_score, risk_level, confidence_level)
            
            # Calculate entry/exit points
            entry_price, stop_loss, take_profit = self._calculate_entry_exit_points(
                market_data, technical_data, risk_level
            )
            
            # Determine time horizon
            time_horizon = self._determine_time_horizon(technical_data, news_data, overall_score)
            
            # Determine urgency
            urgency = self._determine_urgency(news_data, technical_data, overall_score)
            
            return CompositeScore(
                symbol=symbol,
                overall_score=overall_score,
                component_scores=component_scores,
                confidence_level=confidence_level,
                risk_level=risk_level,
                signal_strength=signal_strength,
                recommendation=recommendation,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=None,  # Will be calculated by PositionSizer
                time_horizon=time_horizon,
                urgency=urgency
            )
            
        except Exception as e:
            logger.error(f"Error calculating composite score for {symbol}: {e}")
            return self._create_default_score(symbol)
    
    def calculate_ross_cameron_score(self, symbol: str,
                                   fundamental_data: Dict,
                                   technical_data: Dict,
                                   news_data: Dict,
                                   market_data: Dict) -> RossScore:
        """
        Calculate Ross Cameron specific 5-pillar score
        
        Returns:
            RossScore with detailed pillar analysis
        """
        try:
            logger.info(f"Calculating Ross Cameron score for {symbol}")
            
            # Pillar 1: High Relative Volume
            volume_score = self._calculate_volume_pillar_score(market_data)
            
            # Pillar 2: Significant Price Change
            price_change_score = self._calculate_price_change_pillar_score(market_data)
            
            # Pillar 3: Low Float
            float_score = self._calculate_float_pillar_score(fundamental_data)
            
            # Pillar 4: News Catalyst
            catalyst_score = self._calculate_catalyst_pillar_score(news_data)
            
            # Pillar 5: Price Range (under $20)
            price_range_score = self._calculate_price_range_pillar_score(market_data)
            
            # Calculate overall Ross Cameron score
            overall_ross_score = (
                volume_score * self.ross_pillar_weights['volume'] +
                price_change_score * self.ross_pillar_weights['price_change'] +
                float_score * self.ross_pillar_weights['float'] +
                catalyst_score * self.ross_pillar_weights['catalyst'] +
                price_range_score * self.ross_pillar_weights['price_range']
            ) * 100
            
            # Assign Ross Cameron grade
            ross_grade = self._assign_ross_grade(overall_ross_score)
            
            return RossScore(
                pillar_1_volume=volume_score * 100,
                pillar_2_price_change=price_change_score * 100,
                pillar_3_float=float_score * 100,
                pillar_4_catalyst=catalyst_score * 100,
                pillar_5_price_range=price_range_score * 100,
                overall_ross_score=overall_ross_score,
                ross_grade=ross_grade
            )
            
        except Exception as e:
            logger.error(f"Error calculating Ross Cameron score: {e}")
            return self._create_default_ross_score()
    
    def _calculate_fundamental_score(self, fundamental_data: Dict, market_data: Dict) -> Dict:
        """Calculate fundamental analysis score"""
        try:
            score = 0.0
            confidence = 0.0
            details = {}
            
            # Float analysis (30 points)
            float_shares = fundamental_data.get('float_shares', 0)
            if float_shares > 0:
                if float_shares <= 10_000_000:  # Under 10M is excellent
                    float_score = 30
                elif float_shares <= 20_000_000:  # 10-20M is good
                    float_score = 25
                elif float_shares <= 50_000_000:  # 20-50M is fair
                    float_score = 15
                else:  # Over 50M is poor
                    float_score = 5
                score += float_score
                confidence += 0.3
                details['float_score'] = float_score
                details['float_shares'] = float_shares
            
            # Price range analysis (20 points)
            current_price = market_data.get('current_price', 0)
            if current_price > 0:
                if 2 <= current_price <= 10:  # Ross Cameron sweet spot
                    price_score = 20
                elif 1 <= current_price <= 20:  # Acceptable range
                    price_score = 15
                elif current_price <= 50:  # Higher but tradeable
                    price_score = 10
                else:  # Too expensive
                    price_score = 0
                score += price_score
                confidence += 0.2
                details['price_score'] = price_score
                details['current_price'] = current_price
            
            # Sector analysis (15 points)
            sector = fundamental_data.get('sector', '').lower()
            target_sectors = ['healthcare', 'biotechnology', 'technology', 'crypto', 'ai']
            if any(target in sector for target in target_sectors):
                sector_score = 15
            else:
                sector_score = 8  # Neutral for other sectors
            score += sector_score
            confidence += 0.15
            details['sector_score'] = sector_score
            details['sector'] = sector
            
            # Market cap analysis (10 points)
            market_cap = fundamental_data.get('market_cap', 0)
            if market_cap > 0:
                if market_cap <= 300_000_000:  # Small cap (under 300M)
                    mcap_score = 10
                elif market_cap <= 2_000_000_000:  # Mid cap
                    mcap_score = 7
                else:  # Large cap
                    mcap_score = 3
                score += mcap_score
                confidence += 0.1
                details['market_cap_score'] = mcap_score
                details['market_cap'] = market_cap
            
            # Shares outstanding analysis (10 points)
            shares_outstanding = fundamental_data.get('shares_outstanding', 0)
            if shares_outstanding > 0:
                if shares_outstanding <= 50_000_000:  # Low share count
                    shares_score = 10
                elif shares_outstanding <= 100_000_000:  # Medium share count
                    shares_score = 7
                else:  # High share count
                    shares_score = 3
                score += shares_score
                confidence += 0.1
                details['shares_score'] = shares_score
                details['shares_outstanding'] = shares_outstanding
            
            # Short interest analysis (15 points)
            short_interest = fundamental_data.get('short_interest_percent', 0)
            if short_interest >= 20:  # High short interest (squeeze potential)
                short_score = 15
            elif short_interest >= 10:  # Medium short interest
                short_score = 10
            elif short_interest >= 5:  # Low short interest
                short_score = 5
            else:  # Very low short interest
                short_score = 2
            score += short_score
            confidence += 0.15
            details['short_score'] = short_score
            details['short_interest'] = short_interest
            
            return {
                'score': min(100, score),
                'confidence': min(1.0, confidence),
                'details': details
            }
            
        except Exception as e:
            logger.warning(f"Error in fundamental scoring: {e}")
            return {'score': 50, 'confidence': 0.5, 'details': {}}
    
    def _calculate_technical_score(self, technical_data: Dict, market_data: Dict) -> Dict:
        """Calculate technical analysis score"""
        try:
            score = 0.0
            confidence = 0.0
            details = {}
            
            # MACD analysis (25 points)
            macd_line = technical_data.get('macd_line', 0)
            macd_signal = technical_data.get('macd_signal', 0)
            macd_histogram = technical_data.get('macd_histogram', 0)
            
            if macd_line > macd_signal and macd_histogram > 0:  # Bullish MACD
                macd_score = 25
            elif macd_line > macd_signal:  # MACD line above signal
                macd_score = 15
            elif macd_histogram > 0:  # Positive histogram
                macd_score = 10
            else:  # Bearish MACD
                macd_score = 0
            
            score += macd_score
            confidence += 0.25
            details['macd_score'] = macd_score
            details['macd_bullish'] = macd_line > macd_signal
            
            # EMA alignment (20 points)
            current_price = market_data.get('current_price', 0)
            ema_9 = technical_data.get('ema_9', 0)
            ema_20 = technical_data.get('ema_20', 0)
            
            if current_price > ema_9 > ema_20:  # Perfect bullish alignment
                ema_score = 20
            elif current_price > ema_9:  # Price above short EMA
                ema_score = 15
            elif current_price > ema_20:  # Price above long EMA
                ema_score = 10
            else:  # Bearish alignment
                ema_score = 0
            
            score += ema_score
            confidence += 0.2
            details['ema_score'] = ema_score
            details['ema_alignment'] = 'bullish' if current_price > ema_9 > ema_20 else 'bearish'
            
            # RSI analysis (15 points)
            rsi = technical_data.get('rsi', 50)
            if 40 <= rsi <= 60:  # Neutral RSI (good for entry)
                rsi_score = 15
            elif 30 <= rsi <= 70:  # Acceptable RSI range
                rsi_score = 12
            elif rsi > 70:  # Overbought (momentum but risky)
                rsi_score = 8
            elif rsi < 30:  # Oversold (potential reversal)
                rsi_score = 10
            else:  # Extreme levels
                rsi_score = 5
            
            score += rsi_score
            confidence += 0.15
            details['rsi_score'] = rsi_score
            details['rsi'] = rsi
            
            # Support/Resistance analysis (15 points)
            support_levels = technical_data.get('support_levels', [])
            resistance_levels = technical_data.get('resistance_levels', [])
            
            if support_levels and resistance_levels:
                # Check if price is near support (bullish) or resistance (bearish)
                nearest_support = max([s for s in support_levels if s <= current_price], default=0)
                nearest_resistance = min([r for r in resistance_levels if r >= current_price], default=float('inf'))
                
                support_distance = (current_price - nearest_support) / current_price if nearest_support > 0 else 1
                resistance_distance = (nearest_resistance - current_price) / current_price if nearest_resistance < float('inf') else 1
                
                if support_distance <= 0.02:  # Within 2% of support
                    sr_score = 15
                elif resistance_distance >= 0.05:  # 5%+ room to resistance
                    sr_score = 12
                else:
                    sr_score = 8
            else:
                sr_score = 8  # Neutral if no levels available
            
            score += sr_score
            confidence += 0.15
            details['support_resistance_score'] = sr_score
            
            # Pattern analysis (15 points)
            patterns = technical_data.get('patterns_detected', [])
            bullish_patterns = ['abcd_bullish', 'cup_and_handle', 'ascending_triangle', 'bull_flag']
            
            pattern_score = 0
            for pattern in patterns:
                if any(bp in pattern.lower() for bp in bullish_patterns):
                    pattern_score += 5  # 5 points per bullish pattern
            
            pattern_score = min(15, pattern_score)  # Cap at 15 points
            score += pattern_score
            confidence += 0.15
            details['pattern_score'] = pattern_score
            details['patterns'] = patterns
            
            # Volume confirmation (10 points)
            volume_ratio = market_data.get('relative_volume', 1.0)
            if volume_ratio >= 3.0:  # 3x+ volume
                volume_conf_score = 10
            elif volume_ratio >= 2.0:  # 2x+ volume
                volume_conf_score = 8
            elif volume_ratio >= 1.5:  # 1.5x+ volume
                volume_conf_score = 5
            else:  # Low volume
                volume_conf_score = 0
            
            score += volume_conf_score
            confidence += 0.1
            details['volume_confirmation_score'] = volume_conf_score
            
            return {
                'score': min(100, score),
                'confidence': min(1.0, confidence),
                'details': details
            }
            
        except Exception as e:
            logger.warning(f"Error in technical scoring: {e}")
            return {'score': 50, 'confidence': 0.5, 'details': {}}
    
    def _calculate_news_score(self, news_data: Dict) -> Dict:
        """Calculate news sentiment and catalyst score"""
        try:
            score = 0.0
            confidence = 0.0
            details = {}
            
            # Sentiment analysis (40 points)
            avg_sentiment = news_data.get('avg_sentiment', 0.0)
            sentiment_confidence = news_data.get('sentiment_confidence', 0.5)
            
            # Convert sentiment (-1 to 1) to score (0 to 40)
            sentiment_score = (avg_sentiment + 1) * 20  # Maps -1->0, 0->20, 1->40
            
            score += sentiment_score
            confidence += sentiment_confidence * 0.4
            details['sentiment_score'] = sentiment_score
            details['avg_sentiment'] = avg_sentiment
            
            # Catalyst detection (35 points)
            catalyst_score = news_data.get('catalyst_score', 0.0)
            catalyst_confidence = news_data.get('catalyst_confidence', 0.5)
            
            # Scale catalyst score to 35 points
            scaled_catalyst_score = (catalyst_score / 100) * 35
            
            score += scaled_catalyst_score
            confidence += catalyst_confidence * 0.35
            details['catalyst_score'] = scaled_catalyst_score
            details['raw_catalyst_score'] = catalyst_score
            
            # News momentum (15 points)
            news_momentum = news_data.get('news_momentum_score', 0.0)
            momentum_score = (news_momentum / 100) * 15
            
            score += momentum_score
            confidence += 0.15
            details['momentum_score'] = momentum_score
            
            # Recency bonus (10 points)
            latest_catalyst_time = news_data.get('latest_catalyst_time')
            if latest_catalyst_time:
                hours_since = (datetime.now() - latest_catalyst_time).total_seconds() / 3600
                if hours_since <= 1:  # Within 1 hour
                    recency_score = 10
                elif hours_since <= 6:  # Within 6 hours
                    recency_score = 7
                elif hours_since <= 24:  # Within 24 hours
                    recency_score = 4
                else:  # Older news
                    recency_score = 1
            else:
                recency_score = 0
            
            score += recency_score
            confidence += 0.1
            details['recency_score'] = recency_score
            
            return {
                'score': min(100, score),
                'confidence': min(1.0, confidence),
                'details': details
            }
            
        except Exception as e:
            logger.warning(f"Error in news scoring: {e}")
            return {'score': 50, 'confidence': 0.5, 'details': {}}
    
    def _calculate_momentum_score(self, market_data: Dict, technical_data: Dict) -> Dict:
        """Calculate volume and momentum score"""
        try:
            score = 0.0
            confidence = 0.0
            details = {}
            
            # Relative volume (40 points)
            relative_volume = market_data.get('relative_volume', 1.0)
            if relative_volume >= 10.0:  # 10x+ volume
                vol_score = 40
            elif relative_volume >= 5.0:  # 5x+ volume
                vol_score = 35
            elif relative_volume >= 3.0:  # 3x+ volume
                vol_score = 30
            elif relative_volume >= 2.0:  # 2x+ volume
                vol_score = 20
            elif relative_volume >= 1.5:  # 1.5x+ volume
                vol_score = 10
            else:  # Low volume
                vol_score = 0
            
            score += vol_score
            confidence += 0.4
            details['volume_score'] = vol_score
            details['relative_volume'] = relative_volume
            
            # Price change momentum (30 points)
            price_change_percent = market_data.get('price_change_percent', 0.0)
            abs_change = abs(price_change_percent)
            
            if abs_change >= 20:  # 20%+ move
                change_score = 30
            elif abs_change >= 10:  # 10%+ move
                change_score = 25
            elif abs_change >= 5:  # 5%+ move
                change_score = 20
            elif abs_change >= 2:  # 2%+ move
                change_score = 10
            else:  # Small move
                change_score = 0
            
            # Bonus for positive moves
            if price_change_percent > 0:
                change_score *= 1.2  # 20% bonus for upward moves
            
            score += min(30, change_score)
            confidence += 0.3
            details['price_change_score'] = min(30, change_score)
            details['price_change_percent'] = price_change_percent
            
            # Gap analysis (20 points)
            gap_percent = market_data.get('gap_percent', 0.0)
            abs_gap = abs(gap_percent)
            
            if abs_gap >= 10:  # 10%+ gap
                gap_score = 20
            elif abs_gap >= 5:  # 5%+ gap
                gap_score = 15
            elif abs_gap >= 2:  # 2%+ gap
                gap_score = 10
            else:  # Small or no gap
                gap_score = 0
            
            # Bonus for gap ups
            if gap_percent > 0:
                gap_score *= 1.1  # 10% bonus for gap ups
            
            score += min(20, gap_score)
            confidence += 0.2
            details['gap_score'] = min(20, gap_score)
            details['gap_percent'] = gap_percent
            
            # Volatility analysis (10 points)
            volatility = technical_data.get('volatility', 0.0)
            if 0.1 <= volatility <= 0.3:  # Optimal volatility range
                vol_score = 10
            elif 0.05 <= volatility <= 0.5:  # Acceptable range
                vol_score = 7
            else:  # Too low or too high
                vol_score = 3
            
            score += vol_score
            confidence += 0.1
            details['volatility_score'] = vol_score
            details['volatility'] = volatility
            
            return {
                'score': min(100, score),
                'confidence': min(1.0, confidence),
                'details': details
            }
            
        except Exception as e:
            logger.warning(f"Error in momentum scoring: {e}")
            return {'score': 50, 'confidence': 0.5, 'details': {}}
    
    def _calculate_volume_pillar_score(self, market_data: Dict) -> float:
        """Calculate Ross Cameron Volume Pillar score"""
        relative_volume = market_data.get('relative_volume', 1.0)
        
        if relative_volume >= 5.0:  # 5x+ volume
            return 1.0
        elif relative_volume >= 3.0:  # 3x+ volume
            return 0.9
        elif relative_volume >= 2.0:  # 2x+ volume (Ross minimum)
            return 0.8
        elif relative_volume >= 1.5:  # 1.5x+ volume
            return 0.6
        else:  # Below Ross criteria
            return 0.2
    
    def _calculate_price_change_pillar_score(self, market_data: Dict) -> float:
        """Calculate Ross Cameron Price Change Pillar score"""
        price_change = abs(market_data.get('price_change_percent', 0.0))
        
        if price_change >= 20:  # 20%+ move
            return 1.0
        elif price_change >= 10:  # 10%+ move
            return 0.9
        elif price_change >= 5:  # 5%+ move
            return 0.8
        elif price_change >= 4:  # 4%+ move (Ross minimum)
            return 0.7
        else:  # Below Ross criteria
            return 0.3
    
    def _calculate_float_pillar_score(self, fundamental_data: Dict) -> float:
        """Calculate Ross Cameron Float Pillar score"""
        float_shares = fundamental_data.get('float_shares', 0)
        
        if float_shares <= 10_000_000:  # Under 10M (excellent)
            return 1.0
        elif float_shares <= 20_000_000:  # 10-20M (good)
            return 0.9
        elif float_shares <= 30_000_000:  # 20-30M (Ross maximum)
            return 0.8
        elif float_shares <= 50_000_000:  # 30-50M (acceptable)
            return 0.6
        else:  # Over 50M (poor)
            return 0.2
    
    def _calculate_catalyst_pillar_score(self, news_data: Dict) -> float:
        """Calculate Ross Cameron Catalyst Pillar score"""
        catalyst_detected = news_data.get('catalyst_detected', False)
        catalyst_score = news_data.get('catalyst_score', 0.0)
        
        if not catalyst_detected:
            return 0.1
        
        # Scale catalyst score to 0-1
        normalized_score = catalyst_score / 100
        
        # Boost for high-impact catalysts
        catalyst_types = news_data.get('catalyst_types', [])
        high_impact_types = ['fda_approval', 'merger_acquisition', 'earnings_beat']
        
        if any(cat in high_impact_types for cat in catalyst_types):
            normalized_score *= 1.2
        
        return min(1.0, normalized_score)
    
    def _calculate_price_range_pillar_score(self, market_data: Dict) -> float:
        """Calculate Ross Cameron Price Range Pillar score"""
        current_price = market_data.get('current_price', 0)
        
        if 2 <= current_price <= 10:  # Ross sweet spot
            return 1.0
        elif 1 <= current_price <= 20:  # Acceptable range
            return 0.8
        elif current_price <= 50:  # Higher but tradeable
            return 0.6
        else:  # Too expensive
            return 0.2
    
    def _assign_ross_grade(self, score: float) -> str:
        """Assign Ross Cameron letter grade"""
        if score >= 95:
            return 'A+'
        elif score >= 90:
            return 'A'
        elif score >= 85:
            return 'B+'
        elif score >= 80:
            return 'B'
        elif score >= 75:
            return 'C+'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def _determine_risk_level(self, technical_data: Dict, market_data: Dict, news_data: Dict) -> str:
        """Determine overall risk level"""
        try:
            risk_factors = 0
            
            # Technical risk factors
            rsi = technical_data.get('rsi', 50)
            if rsi > 80:  # Highly overbought
                risk_factors += 2
            elif rsi > 70:  # Overbought
                risk_factors += 1
            
            # Volume risk
            relative_volume = market_data.get('relative_volume', 1.0)
            if relative_volume < 1.5:  # Low volume
                risk_factors += 1
            
            # Volatility risk
            volatility = technical_data.get('volatility', 0.0)
            if volatility > 0.4:  # High volatility
                risk_factors += 2
            elif volatility > 0.25:  # Medium volatility
                risk_factors += 1
            
            # News risk
            negative_articles = news_data.get('negative_articles', 0)
            total_articles = news_data.get('total_articles', 1)
            if negative_articles / total_articles > 0.3:  # 30%+ negative news
                risk_factors += 1
            
            # Price risk
            current_price = market_data.get('current_price', 0)
            if current_price > 50:  # High price
                risk_factors += 1
            
            if risk_factors >= 4:
                return 'high'
            elif risk_factors >= 2:
                return 'medium'
            else:
                return 'low'
                
        except Exception:
            return 'medium'
    
    def _determine_signal_strength(self, overall_score: float, confidence: float) -> str:
        """Determine signal strength"""
        adjusted_score = overall_score * confidence
        
        if adjusted_score >= 80:
            return 'very_strong'
        elif adjusted_score >= 70:
            return 'strong'
        elif adjusted_score >= 60:
            return 'moderate'
        else:
            return 'weak'
    
    def _generate_recommendation(self, overall_score: float, risk_level: str, confidence: float) -> str:
        """Generate trading recommendation"""
        try:
            adjusted_score = overall_score * confidence
            
            # Risk-adjusted thresholds
            if risk_level == 'low':
                strong_buy_threshold = 75
                buy_threshold = 65
                sell_threshold = 35
            elif risk_level == 'medium':
                strong_buy_threshold = 80
                buy_threshold = 70
                sell_threshold = 40
            else:  # high risk
                strong_buy_threshold = 85
                buy_threshold = 75
                sell_threshold = 45
            
            if adjusted_score >= strong_buy_threshold:
                return 'strong_buy'
            elif adjusted_score >= buy_threshold:
                return 'buy'
            elif adjusted_score >= sell_threshold:
                return 'hold'
            elif adjusted_score >= 25:
                return 'sell'
            else:
                return 'strong_sell'
                
        except Exception:
            return 'hold'
    
    def _calculate_entry_exit_points(self, market_data: Dict, technical_data: Dict, risk_level: str) -> Tuple[float, float, float]:
        """Calculate entry, stop loss, and take profit points"""
        try:
            current_price = market_data.get('current_price', 0)
            if current_price <= 0:
                return None, None, None
            
            # Entry price (current price or slightly above for momentum)
            entry_price = current_price * 1.01  # 1% above current for momentum entry
            
            # Stop loss based on risk level and support
            support_levels = technical_data.get('support_levels', [])
            if support_levels:
                nearest_support = max([s for s in support_levels if s < current_price], default=current_price * 0.95)
                stop_loss = nearest_support * 0.98  # 2% below support
            else:
                # Default stop loss based on risk level
                if risk_level == 'low':
                    stop_loss = current_price * 0.95  # 5% stop
                elif risk_level == 'medium':
                    stop_loss = current_price * 0.92  # 8% stop
                else:  # high risk
                    stop_loss = current_price * 0.90  # 10% stop
            
            # Take profit based on resistance and risk/reward ratio
            resistance_levels = technical_data.get('resistance_levels', [])
            if resistance_levels:
                nearest_resistance = min([r for r in resistance_levels if r > current_price], default=current_price * 1.15)
                take_profit = nearest_resistance * 0.98  # 2% below resistance
            else:
                # Default take profit for 2:1 risk/reward
                risk_amount = entry_price - stop_loss
                take_profit = entry_price + (risk_amount * 2)
            
            return entry_price, stop_loss, take_profit
            
        except Exception as e:
            logger.warning(f"Error calculating entry/exit points: {e}")
            return None, None, None
    
    def _determine_time_horizon(self, technical_data: Dict, news_data: Dict, overall_score: float) -> str:
        """Determine optimal time horizon for the trade"""
        try:
            # Check for scalping conditions
            volatility = technical_data.get('volatility', 0.0)
            relative_volume = technical_data.get('relative_volume', 1.0)
            
            if volatility > 0.3 and relative_volume > 5.0:
                return 'scalp'  # High volatility + volume = scalp opportunity
            
            # Check for day trading conditions
            catalyst_urgency = news_data.get('urgency_level', 'low')
            if catalyst_urgency in ['urgent', 'high'] and overall_score > 75:
                return 'day_trade'
            
            # Check for swing trading conditions
            if overall_score > 70:
                return 'swing'
            
            # Default to position trading
            return 'position'
            
        except Exception:
            return 'day_trade'
    
    def _determine_urgency(self, news_data: Dict, technical_data: Dict, overall_score: float) -> str:
        """Determine urgency level for taking action"""
        try:
            urgency_factors = 0
            
            # News urgency
            catalyst_urgency = news_data.get('urgency_level', 'low')
            if catalyst_urgency == 'urgent':
                urgency_factors += 3
            elif catalyst_urgency == 'high':
                urgency_factors += 2
            elif catalyst_urgency == 'medium':
                urgency_factors += 1
            
            # Technical urgency
            rsi = technical_data.get('rsi', 50)
            if rsi > 75:  # Momentum building
                urgency_factors += 1
            
            relative_volume = technical_data.get('relative_volume', 1.0)
            if relative_volume > 5.0:  # High volume
                urgency_factors += 2
            elif relative_volume > 3.0:
                urgency_factors += 1
            
            # Score urgency
            if overall_score > 85:
                urgency_factors += 2
            elif overall_score > 75:
                urgency_factors += 1
            
            if urgency_factors >= 5:
                return 'immediate'
            elif urgency_factors >= 3:
                return 'high'
            elif urgency_factors >= 1:
                return 'medium'
            else:
                return 'low'
                
        except Exception:
            return 'medium'
    
    def _create_default_score(self, symbol: str) -> CompositeScore:
        """Create default score when calculation fails"""
        return CompositeScore(
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
    
    def _create_default_ross_score(self) -> RossScore:
        """Create default Ross Cameron score when calculation fails"""
        return RossScore(
            pillar_1_volume=50.0,
            pillar_2_price_change=50.0,
            pillar_3_float=50.0,
            pillar_4_catalyst=50.0,
            pillar_5_price_range=50.0,
            overall_ross_score=50.0,
            ross_grade='C'
        )

