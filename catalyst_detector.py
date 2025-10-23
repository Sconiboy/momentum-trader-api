"""
Catalyst Detector - Identifies and analyzes trading catalysts
Focuses on Ross Cameron's preferred catalyst types
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import re

from ..core.logger import get_logger
from .news_scraper import NewsArticle, NewsAnalysisResult

logger = get_logger(__name__)

@dataclass
class CatalystEvent:
    """Represents a detected catalyst event"""
    catalyst_type: str
    confidence: float  # 0-100
    impact_level: str  # 'high', 'medium', 'low'
    timing: str       # 'immediate', 'short_term', 'medium_term'
    description: str
    keywords_matched: List[str]
    article_source: str
    detected_time: datetime
    expected_price_impact: str  # 'bullish', 'bearish', 'neutral'
    
@dataclass
class CatalystAnalysis:
    """Complete catalyst analysis for a symbol"""
    symbol: str
    catalysts_detected: List[CatalystEvent]
    primary_catalyst: Optional[CatalystEvent]
    catalyst_score: float  # 0-100 (overall catalyst strength)
    momentum_potential: str  # 'high', 'medium', 'low'
    trading_recommendation: str  # 'strong_buy', 'buy', 'hold', 'avoid'
    risk_level: str  # 'high', 'medium', 'low'
    time_sensitivity: str  # 'urgent', 'moderate', 'low'

class CatalystDetector:
    """Detects and analyzes trading catalysts from news"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Ross Cameron's preferred catalyst types with detailed patterns
        self.catalyst_patterns = {
            'fda_approval': {
                'keywords': [
                    'fda approval', 'fda approved', 'fda cleared', 'fda clearance',
                    'breakthrough therapy', 'fast track designation', 'orphan drug',
                    'clinical trial success', 'phase 3 results', 'nda approval',
                    'biologics license', 'medical device approval', 'drug approval'
                ],
                'impact_level': 'high',
                'timing': 'immediate',
                'price_impact': 'bullish',
                'sector_focus': ['healthcare', 'biotech', 'pharmaceutical']
            },
            
            'earnings_beat': {
                'keywords': [
                    'earnings beat', 'beat estimates', 'exceeded expectations',
                    'revenue beat', 'eps beat', 'strong earnings', 'record earnings',
                    'quarterly results beat', 'guidance raised', 'outlook raised'
                ],
                'impact_level': 'high',
                'timing': 'immediate',
                'price_impact': 'bullish',
                'sector_focus': ['all']
            },
            
            'merger_acquisition': {
                'keywords': [
                    'merger', 'acquisition', 'buyout', 'takeover bid', 'acquired by',
                    'merge with', 'strategic acquisition', 'cash offer', 'tender offer',
                    'deal announced', 'acquisition agreement', 'merger agreement'
                ],
                'impact_level': 'high',
                'timing': 'immediate',
                'price_impact': 'bullish',
                'sector_focus': ['all']
            },
            
            'contract_award': {
                'keywords': [
                    'contract awarded', 'government contract', 'defense contract',
                    'military contract', 'federal contract', 'contract win',
                    'partnership agreement', 'strategic partnership', 'collaboration deal',
                    'supply agreement', 'licensing deal', 'distribution agreement'
                ],
                'impact_level': 'medium',
                'timing': 'short_term',
                'price_impact': 'bullish',
                'sector_focus': ['defense', 'technology', 'healthcare']
            },
            
            'product_launch': {
                'keywords': [
                    'product launch', 'new product', 'product announcement',
                    'innovation', 'breakthrough technology', 'patent granted',
                    'revolutionary product', 'first-of-its-kind', 'game changer',
                    'market launch', 'commercial launch', 'product release'
                ],
                'impact_level': 'medium',
                'timing': 'medium_term',
                'price_impact': 'bullish',
                'sector_focus': ['technology', 'healthcare', 'consumer']
            },
            
            'analyst_upgrade': {
                'keywords': [
                    'analyst upgrade', 'price target raised', 'buy rating',
                    'outperform rating', 'strong buy', 'overweight rating',
                    'target price increase', 'analyst positive', 'bullish call',
                    'recommendation upgrade', 'coverage initiated'
                ],
                'impact_level': 'medium',
                'timing': 'immediate',
                'price_impact': 'bullish',
                'sector_focus': ['all']
            },
            
            'short_squeeze': {
                'keywords': [
                    'short squeeze', 'heavily shorted', 'short interest',
                    'gamma squeeze', 'retail investors', 'social media buzz',
                    'reddit mention', 'wallstreetbets', 'meme stock',
                    'short covering', 'squeeze potential', 'high short interest'
                ],
                'impact_level': 'high',
                'timing': 'immediate',
                'price_impact': 'bullish',
                'sector_focus': ['all']
            },
            
            'insider_activity': {
                'keywords': [
                    'insider buying', 'insider purchase', 'ceo bought',
                    'director purchase', 'executive buying', 'insider accumulation',
                    'form 4 filing', 'significant purchase', 'insider confidence'
                ],
                'impact_level': 'medium',
                'timing': 'short_term',
                'price_impact': 'bullish',
                'sector_focus': ['all']
            },
            
            'crypto_ai_catalyst': {
                'keywords': [
                    'artificial intelligence', 'ai breakthrough', 'machine learning',
                    'blockchain', 'cryptocurrency', 'bitcoin', 'ethereum',
                    'nft', 'defi', 'web3', 'metaverse', 'quantum computing',
                    'ai partnership', 'crypto adoption', 'digital transformation'
                ],
                'impact_level': 'high',
                'timing': 'immediate',
                'price_impact': 'bullish',
                'sector_focus': ['technology', 'crypto', 'ai']
            }
        }
        
        # Negative catalysts (bearish)
        self.negative_catalysts = {
            'earnings_miss': {
                'keywords': [
                    'earnings miss', 'missed estimates', 'below expectations',
                    'revenue miss', 'eps miss', 'weak earnings', 'disappointing results',
                    'guidance lowered', 'outlook cut', 'profit warning'
                ],
                'impact_level': 'high',
                'price_impact': 'bearish'
            },
            
            'regulatory_issues': {
                'keywords': [
                    'fda rejection', 'regulatory setback', 'investigation',
                    'sec investigation', 'lawsuit', 'legal issues', 'compliance issues',
                    'regulatory delay', 'approval denied', 'warning letter'
                ],
                'impact_level': 'high',
                'price_impact': 'bearish'
            },
            
            'management_issues': {
                'keywords': [
                    'ceo resignation', 'management change', 'executive departure',
                    'accounting irregularities', 'fraud allegations', 'insider selling',
                    'board changes', 'leadership crisis', 'governance issues'
                ],
                'impact_level': 'medium',
                'price_impact': 'bearish'
            }
        }
        
        # Time sensitivity indicators
        self.urgency_indicators = {
            'immediate': [
                'breaking', 'just announced', 'urgent', 'alert', 'now',
                'today', 'this morning', 'moments ago', 'developing'
            ],
            'short_term': [
                'this week', 'coming days', 'soon', 'shortly', 'upcoming',
                'expected', 'anticipated', 'planned'
            ],
            'medium_term': [
                'next month', 'next quarter', 'later this year', 'future',
                'long term', 'eventually', 'over time'
            ]
        }
        
        logger.info("Catalyst Detector initialized")
    
    def detect_catalysts(self, news_result: NewsAnalysisResult) -> CatalystAnalysis:
        """
        Detect and analyze catalysts from news articles
        
        Args:
            news_result: NewsAnalysisResult to analyze
            
        Returns:
            CatalystAnalysis with detected catalysts
        """
        try:
            logger.info(f"Detecting catalysts for {news_result.symbol}")
            
            detected_catalysts = []
            
            # Analyze each article for catalysts
            for article in news_result.articles:
                article_catalysts = self._analyze_article_for_catalysts(article)
                detected_catalysts.extend(article_catalysts)
            
            # Remove duplicates and rank by confidence
            unique_catalysts = self._deduplicate_catalysts(detected_catalysts)
            ranked_catalysts = sorted(unique_catalysts, key=lambda x: x.confidence, reverse=True)
            
            # Identify primary catalyst
            primary_catalyst = ranked_catalysts[0] if ranked_catalysts else None
            
            # Calculate overall catalyst score
            catalyst_score = self._calculate_catalyst_score(ranked_catalysts)
            
            # Assess momentum potential
            momentum_potential = self._assess_momentum_potential(ranked_catalysts, news_result)
            
            # Generate trading recommendation
            trading_recommendation = self._generate_trading_recommendation(
                ranked_catalysts, catalyst_score, momentum_potential
            )
            
            # Assess risk level
            risk_level = self._assess_risk_level(ranked_catalysts, news_result)
            
            # Determine time sensitivity
            time_sensitivity = self._determine_time_sensitivity(ranked_catalysts)
            
            return CatalystAnalysis(
                symbol=news_result.symbol,
                catalysts_detected=ranked_catalysts,
                primary_catalyst=primary_catalyst,
                catalyst_score=catalyst_score,
                momentum_potential=momentum_potential,
                trading_recommendation=trading_recommendation,
                risk_level=risk_level,
                time_sensitivity=time_sensitivity
            )
            
        except Exception as e:
            logger.error(f"Error detecting catalysts: {e}")
            return self._create_empty_analysis(news_result.symbol)
    
    def _analyze_article_for_catalysts(self, article: NewsArticle) -> List[CatalystEvent]:
        """Analyze a single article for catalyst events"""
        catalysts = []
        
        try:
            text = f"{article.title} {article.content}".lower()
            
            # Check positive catalysts
            for catalyst_type, config in self.catalyst_patterns.items():
                matched_keywords = []
                confidence = 0
                
                for keyword in config['keywords']:
                    if keyword.lower() in text:
                        matched_keywords.append(keyword)
                        confidence += 10  # Base confidence per keyword
                
                if matched_keywords:
                    # Boost confidence based on title vs content
                    title_matches = sum(1 for kw in matched_keywords if kw.lower() in article.title.lower())
                    if title_matches > 0:
                        confidence += title_matches * 20  # Title matches are more important
                    
                    # Boost confidence based on recency
                    hours_old = (datetime.now() - article.published_date).total_seconds() / 3600
                    if hours_old <= 1:
                        confidence += 20
                    elif hours_old <= 6:
                        confidence += 10
                    
                    # Determine timing
                    timing = self._determine_catalyst_timing(text, config['timing'])
                    
                    # Create catalyst event
                    catalyst = CatalystEvent(
                        catalyst_type=catalyst_type,
                        confidence=min(100, confidence),
                        impact_level=config['impact_level'],
                        timing=timing,
                        description=f"{catalyst_type.replace('_', ' ').title()} detected in {article.source}",
                        keywords_matched=matched_keywords,
                        article_source=article.source,
                        detected_time=datetime.now(),
                        expected_price_impact=config['price_impact']
                    )
                    
                    catalysts.append(catalyst)
            
            # Check negative catalysts
            for catalyst_type, config in self.negative_catalysts.items():
                matched_keywords = []
                confidence = 0
                
                for keyword in config['keywords']:
                    if keyword.lower() in text:
                        matched_keywords.append(keyword)
                        confidence += 15  # Negative catalysts get higher base confidence
                
                if matched_keywords:
                    # Title boost
                    title_matches = sum(1 for kw in matched_keywords if kw.lower() in article.title.lower())
                    confidence += title_matches * 25
                    
                    # Recency boost
                    hours_old = (datetime.now() - article.published_date).total_seconds() / 3600
                    if hours_old <= 1:
                        confidence += 25
                    
                    catalyst = CatalystEvent(
                        catalyst_type=catalyst_type,
                        confidence=min(100, confidence),
                        impact_level=config['impact_level'],
                        timing='immediate',  # Negative news usually immediate
                        description=f"{catalyst_type.replace('_', ' ').title()} detected in {article.source}",
                        keywords_matched=matched_keywords,
                        article_source=article.source,
                        detected_time=datetime.now(),
                        expected_price_impact=config['price_impact']
                    )
                    
                    catalysts.append(catalyst)
            
            return catalysts
            
        except Exception as e:
            logger.warning(f"Error analyzing article for catalysts: {e}")
            return []
    
    def _determine_catalyst_timing(self, text: str, default_timing: str) -> str:
        """Determine timing of catalyst based on text analysis"""
        try:
            # Check for urgency indicators
            for timing, indicators in self.urgency_indicators.items():
                for indicator in indicators:
                    if indicator in text:
                        return timing
            
            return default_timing
            
        except Exception:
            return default_timing
    
    def _deduplicate_catalysts(self, catalysts: List[CatalystEvent]) -> List[CatalystEvent]:
        """Remove duplicate catalysts and keep highest confidence ones"""
        try:
            if not catalysts:
                return []
            
            # Group by catalyst type
            catalyst_groups = {}
            for catalyst in catalysts:
                if catalyst.catalyst_type not in catalyst_groups:
                    catalyst_groups[catalyst.catalyst_type] = []
                catalyst_groups[catalyst.catalyst_type].append(catalyst)
            
            # Keep highest confidence catalyst from each group
            unique_catalysts = []
            for catalyst_type, group in catalyst_groups.items():
                best_catalyst = max(group, key=lambda x: x.confidence)
                unique_catalysts.append(best_catalyst)
            
            return unique_catalysts
            
        except Exception:
            return catalysts
    
    def _calculate_catalyst_score(self, catalysts: List[CatalystEvent]) -> float:
        """Calculate overall catalyst score"""
        try:
            if not catalysts:
                return 0.0
            
            score = 0.0
            
            # Base score from catalyst count
            score += len(catalysts) * 10  # 10 points per catalyst
            
            # Confidence-weighted score
            confidence_sum = sum(c.confidence for c in catalysts)
            score += confidence_sum / len(catalysts) * 0.5  # Average confidence contribution
            
            # Impact level bonus
            high_impact_count = len([c for c in catalysts if c.impact_level == 'high'])
            medium_impact_count = len([c for c in catalysts if c.impact_level == 'medium'])
            
            score += high_impact_count * 20  # 20 points per high impact
            score += medium_impact_count * 10  # 10 points per medium impact
            
            # Timing bonus (immediate catalysts are more valuable)
            immediate_count = len([c for c in catalysts if c.timing == 'immediate'])
            score += immediate_count * 15  # 15 points per immediate catalyst
            
            # Bullish vs bearish balance
            bullish_count = len([c for c in catalysts if c.expected_price_impact == 'bullish'])
            bearish_count = len([c for c in catalysts if c.expected_price_impact == 'bearish'])
            
            if bullish_count > bearish_count:
                score += (bullish_count - bearish_count) * 5  # Bonus for net bullish catalysts
            
            return min(100, score)
            
        except Exception:
            return 0.0
    
    def _assess_momentum_potential(self, catalysts: List[CatalystEvent], 
                                 news_result: NewsAnalysisResult) -> str:
        """Assess momentum potential based on catalysts"""
        try:
            if not catalysts:
                return 'low'
            
            # High momentum indicators
            high_impact_catalysts = [c for c in catalysts if c.impact_level == 'high']
            immediate_catalysts = [c for c in catalysts if c.timing == 'immediate']
            bullish_catalysts = [c for c in catalysts if c.expected_price_impact == 'bullish']
            
            # High momentum conditions
            if (len(high_impact_catalysts) >= 2 or 
                (len(high_impact_catalysts) >= 1 and len(immediate_catalysts) >= 2) or
                (len(bullish_catalysts) >= 3 and news_result.news_momentum_score >= 70)):
                return 'high'
            
            # Medium momentum conditions
            if (len(high_impact_catalysts) >= 1 or 
                len(immediate_catalysts) >= 2 or
                (len(bullish_catalysts) >= 2 and news_result.news_momentum_score >= 50)):
                return 'medium'
            
            return 'low'
            
        except Exception:
            return 'low'
    
    def _generate_trading_recommendation(self, catalysts: List[CatalystEvent], 
                                       catalyst_score: float, 
                                       momentum_potential: str) -> str:
        """Generate trading recommendation based on catalyst analysis"""
        try:
            if not catalysts:
                return 'hold'
            
            bullish_catalysts = [c for c in catalysts if c.expected_price_impact == 'bullish']
            bearish_catalysts = [c for c in catalysts if c.expected_price_impact == 'bearish']
            high_confidence_catalysts = [c for c in catalysts if c.confidence >= 70]
            
            # Strong buy conditions
            if (catalyst_score >= 80 and 
                momentum_potential == 'high' and 
                len(bullish_catalysts) >= 2 and 
                len(bearish_catalysts) == 0 and
                len(high_confidence_catalysts) >= 1):
                return 'strong_buy'
            
            # Buy conditions
            if (catalyst_score >= 60 and 
                momentum_potential in ['high', 'medium'] and 
                len(bullish_catalysts) > len(bearish_catalysts)):
                return 'buy'
            
            # Avoid conditions
            if (len(bearish_catalysts) > len(bullish_catalysts) or
                catalyst_score < 30):
                return 'avoid'
            
            return 'hold'
            
        except Exception:
            return 'hold'
    
    def _assess_risk_level(self, catalysts: List[CatalystEvent], 
                         news_result: NewsAnalysisResult) -> str:
        """Assess risk level based on catalysts"""
        try:
            if not catalysts:
                return 'medium'
            
            bearish_catalysts = [c for c in catalysts if c.expected_price_impact == 'bearish']
            high_impact_catalysts = [c for c in catalysts if c.impact_level == 'high']
            uncertain_catalysts = [c for c in catalysts if c.confidence < 50]
            
            # High risk conditions
            if (len(bearish_catalysts) >= 1 or 
                len(uncertain_catalysts) >= 2 or
                news_result.negative_articles > news_result.positive_articles):
                return 'high'
            
            # Low risk conditions
            if (len(bearish_catalysts) == 0 and 
                len(high_impact_catalysts) >= 1 and
                news_result.positive_articles >= news_result.negative_articles * 2):
                return 'low'
            
            return 'medium'
            
        except Exception:
            return 'medium'
    
    def _determine_time_sensitivity(self, catalysts: List[CatalystEvent]) -> str:
        """Determine time sensitivity for trading action"""
        try:
            if not catalysts:
                return 'low'
            
            immediate_catalysts = [c for c in catalysts if c.timing == 'immediate']
            high_confidence_immediate = [c for c in immediate_catalysts if c.confidence >= 70]
            
            # Urgent conditions
            if (len(high_confidence_immediate) >= 1 or 
                len(immediate_catalysts) >= 2):
                return 'urgent'
            
            # Moderate conditions
            if (len(immediate_catalysts) >= 1 or 
                any(c.timing == 'short_term' and c.confidence >= 80 for c in catalysts)):
                return 'moderate'
            
            return 'low'
            
        except Exception:
            return 'low'
    
    def _create_empty_analysis(self, symbol: str) -> CatalystAnalysis:
        """Create empty catalyst analysis"""
        return CatalystAnalysis(
            symbol=symbol,
            catalysts_detected=[],
            primary_catalyst=None,
            catalyst_score=0.0,
            momentum_potential='low',
            trading_recommendation='hold',
            risk_level='medium',
            time_sensitivity='low'
        )

