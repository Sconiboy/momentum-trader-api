"""
Sentiment Analyzer - Analyzes sentiment of news articles
Uses multiple NLP approaches for robust sentiment detection
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import re
from datetime import datetime

# NLP libraries
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import nltk

from ..core.logger import get_logger
from .news_scraper import NewsArticle, NewsAnalysisResult

logger = get_logger(__name__)

@dataclass
class SentimentScore:
    """Comprehensive sentiment score"""
    compound_score: float  # -1 to 1 (overall sentiment)
    positive_score: float  # 0 to 1
    negative_score: float  # 0 to 1
    neutral_score: float   # 0 to 1
    confidence: float      # 0 to 1 (how confident we are)
    method_used: str       # Which method provided the score
    
@dataclass
class MarketSentiment:
    """Market-specific sentiment analysis"""
    bullish_score: float   # 0 to 100
    bearish_score: float   # 0 to 100
    uncertainty_score: float  # 0 to 100
    momentum_direction: str   # 'bullish', 'bearish', 'neutral'
    catalyst_strength: float  # 0 to 100
    urgency_level: str       # 'high', 'medium', 'low'

class SentimentAnalyzer:
    """Analyzes sentiment of financial news with market context"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Initialize VADER sentiment analyzer
        self.vader_analyzer = SentimentIntensityAnalyzer()
        
        # Download required NLTK data
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('vader_lexicon', quiet=True)
        except Exception as e:
            logger.warning(f"Could not download NLTK data: {e}")
        
        # Financial sentiment keywords
        self.bullish_keywords = [
            'beat', 'exceed', 'outperform', 'strong', 'growth', 'positive', 'upgrade',
            'buy', 'bullish', 'rally', 'surge', 'soar', 'breakthrough', 'success',
            'profit', 'revenue growth', 'expansion', 'partnership', 'deal', 'approval',
            'innovation', 'competitive advantage', 'market leader', 'record high'
        ]
        
        self.bearish_keywords = [
            'miss', 'disappoint', 'weak', 'decline', 'negative', 'downgrade',
            'sell', 'bearish', 'crash', 'plunge', 'drop', 'failure', 'loss',
            'revenue decline', 'layoffs', 'bankruptcy', 'investigation', 'lawsuit',
            'competition', 'market share loss', 'regulatory issues', 'recall'
        ]
        
        self.uncertainty_keywords = [
            'uncertain', 'volatile', 'unclear', 'pending', 'awaiting', 'potential',
            'possible', 'may', 'might', 'could', 'speculation', 'rumor',
            'investigation ongoing', 'under review', 'preliminary', 'unconfirmed'
        ]
        
        # Catalyst strength indicators
        self.high_impact_catalysts = [
            'fda approval', 'merger', 'acquisition', 'earnings beat', 'breakthrough',
            'partnership', 'contract award', 'clinical trial success', 'patent approval'
        ]
        
        self.medium_impact_catalysts = [
            'analyst upgrade', 'product launch', 'expansion', 'guidance raise',
            'insider buying', 'share buyback', 'dividend increase'
        ]
        
        logger.info("Sentiment Analyzer initialized")
    
    def analyze_article_sentiment(self, article: NewsArticle) -> SentimentScore:
        """
        Analyze sentiment of a single article
        
        Args:
            article: NewsArticle to analyze
            
        Returns:
            SentimentScore with comprehensive analysis
        """
        try:
            # Combine title and content for analysis
            text = f"{article.title}. {article.content}"
            
            # Clean text
            cleaned_text = self._clean_text(text)
            
            # Get sentiment from multiple methods
            vader_sentiment = self._get_vader_sentiment(cleaned_text)
            textblob_sentiment = self._get_textblob_sentiment(cleaned_text)
            financial_sentiment = self._get_financial_sentiment(cleaned_text)
            
            # Combine sentiments with weights
            compound_score = self._combine_sentiment_scores(
                vader_sentiment, textblob_sentiment, financial_sentiment
            )
            
            # Calculate component scores
            positive_score = max(0, compound_score)
            negative_score = max(0, -compound_score)
            neutral_score = 1 - abs(compound_score)
            
            # Calculate confidence based on agreement between methods
            confidence = self._calculate_confidence(
                vader_sentiment, textblob_sentiment, financial_sentiment
            )
            
            return SentimentScore(
                compound_score=compound_score,
                positive_score=positive_score,
                negative_score=negative_score,
                neutral_score=neutral_score,
                confidence=confidence,
                method_used='combined'
            )
            
        except Exception as e:
            logger.warning(f"Error analyzing article sentiment: {e}")
            return SentimentScore(0, 0, 0, 1, 0, 'error')
    
    def analyze_market_sentiment(self, articles: List[NewsArticle]) -> MarketSentiment:
        """
        Analyze overall market sentiment from multiple articles
        
        Args:
            articles: List of NewsArticle objects
            
        Returns:
            MarketSentiment with market-specific analysis
        """
        try:
            if not articles:
                return self._create_neutral_market_sentiment()
            
            # Analyze each article
            article_sentiments = []
            for article in articles:
                sentiment = self.analyze_article_sentiment(article)
                article.sentiment_score = sentiment.compound_score
                article_sentiments.append(sentiment)
            
            # Calculate aggregate scores
            bullish_score = self._calculate_bullish_score(articles, article_sentiments)
            bearish_score = self._calculate_bearish_score(articles, article_sentiments)
            uncertainty_score = self._calculate_uncertainty_score(articles, article_sentiments)
            
            # Determine momentum direction
            momentum_direction = self._determine_momentum_direction(
                bullish_score, bearish_score, uncertainty_score
            )
            
            # Calculate catalyst strength
            catalyst_strength = self._calculate_catalyst_strength(articles)
            
            # Determine urgency level
            urgency_level = self._determine_urgency_level(
                articles, bullish_score, bearish_score, catalyst_strength
            )
            
            return MarketSentiment(
                bullish_score=bullish_score,
                bearish_score=bearish_score,
                uncertainty_score=uncertainty_score,
                momentum_direction=momentum_direction,
                catalyst_strength=catalyst_strength,
                urgency_level=urgency_level
            )
            
        except Exception as e:
            logger.error(f"Error analyzing market sentiment: {e}")
            return self._create_neutral_market_sentiment()
    
    def enhance_news_analysis(self, news_result: NewsAnalysisResult) -> NewsAnalysisResult:
        """
        Enhance news analysis with detailed sentiment analysis
        
        Args:
            news_result: NewsAnalysisResult to enhance
            
        Returns:
            Enhanced NewsAnalysisResult with sentiment data
        """
        try:
            # Analyze sentiment for each article
            for article in news_result.articles:
                sentiment = self.analyze_article_sentiment(article)
                article.sentiment_score = sentiment.compound_score
            
            # Get market sentiment
            market_sentiment = self.analyze_market_sentiment(news_result.articles)
            
            # Update sentiment counts
            positive_count = len([a for a in news_result.articles if a.sentiment_score > 0.1])
            negative_count = len([a for a in news_result.articles if a.sentiment_score < -0.1])
            neutral_count = len(news_result.articles) - positive_count - negative_count
            
            # Update average sentiment
            sentiment_scores = [a.sentiment_score for a in news_result.articles if a.sentiment_score is not None]
            avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0.0
            
            # Update the result
            news_result.positive_articles = positive_count
            news_result.negative_articles = negative_count
            news_result.neutral_articles = neutral_count
            news_result.avg_sentiment = avg_sentiment
            
            # Enhance momentum score with sentiment
            sentiment_boost = market_sentiment.bullish_score * 0.3  # Up to 30 point boost
            news_result.news_momentum_score = min(100, news_result.news_momentum_score + sentiment_boost)
            
            return news_result
            
        except Exception as e:
            logger.error(f"Error enhancing news analysis: {e}")
            return news_result
    
    def _clean_text(self, text: str) -> str:
        """Clean text for sentiment analysis"""
        try:
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', '', text)
            
            # Remove extra whitespace
            text = re.sub(r'\\s+', ' ', text)
            
            # Remove special characters but keep punctuation
            text = re.sub(r'[^\\w\\s.,!?;:-]', '', text)
            
            return text.strip()
            
        except Exception:
            return text
    
    def _get_vader_sentiment(self, text: str) -> float:
        """Get sentiment using VADER"""
        try:
            scores = self.vader_analyzer.polarity_scores(text)
            return scores['compound']
        except Exception:
            return 0.0
    
    def _get_textblob_sentiment(self, text: str) -> float:
        """Get sentiment using TextBlob"""
        try:
            blob = TextBlob(text)
            return blob.sentiment.polarity
        except Exception:
            return 0.0
    
    def _get_financial_sentiment(self, text: str) -> float:
        """Get sentiment using financial keywords"""
        try:
            text_lower = text.lower()
            
            bullish_count = sum(1 for keyword in self.bullish_keywords if keyword in text_lower)
            bearish_count = sum(1 for keyword in self.bearish_keywords if keyword in text_lower)
            
            if bullish_count == 0 and bearish_count == 0:
                return 0.0
            
            total_keywords = bullish_count + bearish_count
            sentiment = (bullish_count - bearish_count) / total_keywords
            
            # Scale to -1 to 1 range
            return max(-1, min(1, sentiment))
            
        except Exception:
            return 0.0
    
    def _combine_sentiment_scores(self, vader: float, textblob: float, financial: float) -> float:
        """Combine sentiment scores from different methods"""
        try:
            # Weight the different methods
            # Financial keywords get highest weight for financial news
            weights = {
                'financial': 0.5,
                'vader': 0.3,
                'textblob': 0.2
            }
            
            combined = (
                financial * weights['financial'] +
                vader * weights['vader'] +
                textblob * weights['textblob']
            )
            
            return max(-1, min(1, combined))
            
        except Exception:
            return 0.0
    
    def _calculate_confidence(self, vader: float, textblob: float, financial: float) -> float:
        """Calculate confidence based on agreement between methods"""
        try:
            scores = [vader, textblob, financial]
            
            # Calculate standard deviation (lower = more agreement = higher confidence)
            std_dev = np.std(scores)
            
            # Convert to confidence (0-1)
            # Lower std_dev = higher confidence
            confidence = max(0, 1 - (std_dev / 1.0))  # Normalize by max possible std_dev
            
            return confidence
            
        except Exception:
            return 0.5
    
    def _calculate_bullish_score(self, articles: List[NewsArticle], sentiments: List[SentimentScore]) -> float:
        """Calculate bullish sentiment score"""
        try:
            if not articles:
                return 0.0
            
            bullish_score = 0.0
            
            # Base sentiment score
            positive_sentiments = [s.compound_score for s in sentiments if s.compound_score > 0]
            if positive_sentiments:
                bullish_score += np.mean(positive_sentiments) * 50  # Up to 50 points
            
            # Catalyst bonus
            catalyst_articles = [a for a in articles if a.catalyst_type]
            if catalyst_articles:
                bullish_score += len(catalyst_articles) * 5  # 5 points per catalyst
            
            # High-impact catalyst bonus
            high_impact_count = 0
            for article in articles:
                text = f"{article.title} {article.content}".lower()
                for catalyst in self.high_impact_catalysts:
                    if catalyst in text:
                        high_impact_count += 1
                        break
            
            bullish_score += high_impact_count * 10  # 10 points per high-impact catalyst
            
            # Recency bonus
            recent_articles = [a for a in articles 
                             if (datetime.now() - a.published_date).total_seconds() < 3600]
            bullish_score += len(recent_articles) * 2  # 2 points per recent article
            
            return min(100, bullish_score)
            
        except Exception:
            return 0.0
    
    def _calculate_bearish_score(self, articles: List[NewsArticle], sentiments: List[SentimentScore]) -> float:
        """Calculate bearish sentiment score"""
        try:
            if not articles:
                return 0.0
            
            bearish_score = 0.0
            
            # Base sentiment score
            negative_sentiments = [abs(s.compound_score) for s in sentiments if s.compound_score < 0]
            if negative_sentiments:
                bearish_score += np.mean(negative_sentiments) * 50  # Up to 50 points
            
            # Negative keyword count
            for article in articles:
                text = f"{article.title} {article.content}".lower()
                bearish_count = sum(1 for keyword in self.bearish_keywords if keyword in text)
                bearish_score += bearish_count * 3  # 3 points per bearish keyword
            
            # Recency bonus for negative news
            recent_negative = [a for a in articles 
                             if (datetime.now() - a.published_date).total_seconds() < 3600
                             and a.sentiment_score and a.sentiment_score < -0.1]
            bearish_score += len(recent_negative) * 5  # 5 points per recent negative article
            
            return min(100, bearish_score)
            
        except Exception:
            return 0.0
    
    def _calculate_uncertainty_score(self, articles: List[NewsArticle], sentiments: List[SentimentScore]) -> float:
        """Calculate uncertainty score"""
        try:
            if not articles:
                return 0.0
            
            uncertainty_score = 0.0
            
            # Neutral sentiment articles
            neutral_count = len([s for s in sentiments if abs(s.compound_score) <= 0.1])
            uncertainty_score += (neutral_count / len(sentiments)) * 30 if sentiments else 0
            
            # Uncertainty keywords
            for article in articles:
                text = f"{article.title} {article.content}".lower()
                uncertainty_count = sum(1 for keyword in self.uncertainty_keywords if keyword in text)
                uncertainty_score += uncertainty_count * 5  # 5 points per uncertainty keyword
            
            # Low confidence scores
            low_confidence_count = len([s for s in sentiments if s.confidence < 0.5])
            uncertainty_score += (low_confidence_count / len(sentiments)) * 20 if sentiments else 0
            
            return min(100, uncertainty_score)
            
        except Exception:
            return 0.0
    
    def _determine_momentum_direction(self, bullish: float, bearish: float, uncertainty: float) -> str:
        """Determine overall momentum direction"""
        try:
            if bullish > bearish + 20:  # Significant bullish bias
                return 'bullish'
            elif bearish > bullish + 20:  # Significant bearish bias
                return 'bearish'
            elif uncertainty > 50:  # High uncertainty
                return 'uncertain'
            else:
                return 'neutral'
                
        except Exception:
            return 'neutral'
    
    def _calculate_catalyst_strength(self, articles: List[NewsArticle]) -> float:
        """Calculate overall catalyst strength"""
        try:
            if not articles:
                return 0.0
            
            strength = 0.0
            
            # Count different types of catalysts
            catalyst_articles = [a for a in articles if a.catalyst_type]
            if not catalyst_articles:
                return 0.0
            
            # Base strength from catalyst count
            strength += len(catalyst_articles) * 10  # 10 points per catalyst
            
            # High-impact catalyst bonus
            for article in articles:
                text = f"{article.title} {article.content}".lower()
                for catalyst in self.high_impact_catalysts:
                    if catalyst in text:
                        strength += 20  # 20 points for high-impact
                        break
                else:
                    for catalyst in self.medium_impact_catalysts:
                        if catalyst in text:
                            strength += 10  # 10 points for medium-impact
                            break
            
            # Recency bonus
            recent_catalysts = [a for a in catalyst_articles 
                              if (datetime.now() - a.published_date).total_seconds() < 3600]
            strength += len(recent_catalysts) * 5  # 5 points per recent catalyst
            
            return min(100, strength)
            
        except Exception:
            return 0.0
    
    def _determine_urgency_level(self, articles: List[NewsArticle], 
                               bullish: float, bearish: float, catalyst_strength: float) -> str:
        """Determine urgency level for trading action"""
        try:
            # High urgency conditions
            if catalyst_strength >= 70:
                return 'high'
            
            if bullish >= 80 or bearish >= 80:
                return 'high'
            
            # Recent high-impact news
            recent_high_impact = 0
            for article in articles:
                if (datetime.now() - article.published_date).total_seconds() < 1800:  # 30 minutes
                    text = f"{article.title} {article.content}".lower()
                    for catalyst in self.high_impact_catalysts:
                        if catalyst in text:
                            recent_high_impact += 1
                            break
            
            if recent_high_impact >= 2:
                return 'high'
            
            # Medium urgency conditions
            if catalyst_strength >= 40 or bullish >= 60 or bearish >= 60:
                return 'medium'
            
            return 'low'
            
        except Exception:
            return 'low'
    
    def _create_neutral_market_sentiment(self) -> MarketSentiment:
        """Create neutral market sentiment when no data available"""
        return MarketSentiment(
            bullish_score=0.0,
            bearish_score=0.0,
            uncertainty_score=100.0,
            momentum_direction='neutral',
            catalyst_strength=0.0,
            urgency_level='low'
        )

