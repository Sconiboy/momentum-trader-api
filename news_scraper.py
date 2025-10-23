"""
News Scraper - Collects news from multiple financial sources
Focuses on catalyst detection for momentum trading
"""
import requests
import feedparser
import newspaper
from newspaper import Article
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import time
import re
import json

from ..core.logger import get_logger

logger = get_logger(__name__)

@dataclass
class NewsArticle:
    """Represents a news article"""
    title: str
    content: str
    url: str
    source: str
    published_date: datetime
    symbols_mentioned: List[str]
    sentiment_score: Optional[float] = None
    catalyst_type: Optional[str] = None
    relevance_score: Optional[float] = None
    summary: Optional[str] = None

@dataclass
class NewsAnalysisResult:
    """Result of news analysis for a symbol"""
    symbol: str
    articles: List[NewsArticle]
    total_articles: int
    positive_articles: int
    negative_articles: int
    neutral_articles: int
    avg_sentiment: float
    catalyst_detected: bool
    catalyst_types: List[str]
    news_momentum_score: float  # 0-100
    latest_catalyst_time: Optional[datetime]

class NewsScraperManager:
    """Manages news scraping from multiple sources"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # News sources configuration
        self.news_sources = {
            'yahoo_finance': {
                'base_url': 'https://finance.yahoo.com/rss/headline',
                'type': 'rss',
                'enabled': True
            },
            'marketwatch': {
                'base_url': 'https://feeds.marketwatch.com/marketwatch/topstories/',
                'type': 'rss', 
                'enabled': True
            },
            'seeking_alpha': {
                'base_url': 'https://seekingalpha.com/api/sa/combined/',
                'type': 'api',
                'enabled': False  # Requires API key
            },
            'benzinga': {
                'base_url': 'https://www.benzinga.com/feed',
                'type': 'rss',
                'enabled': True
            },
            'finviz_news': {
                'base_url': 'https://finviz.com/news.ashx',
                'type': 'scrape',
                'enabled': True
            }
        }
        
        # Catalyst keywords for different types
        self.catalyst_keywords = {
            'earnings': [
                'earnings', 'eps', 'quarterly results', 'revenue beat', 'revenue miss',
                'guidance', 'outlook', 'profit', 'loss', 'beat estimates', 'miss estimates'
            ],
            'fda_approval': [
                'fda approval', 'fda cleared', 'clinical trial', 'phase 1', 'phase 2', 'phase 3',
                'drug approval', 'medical device', 'breakthrough therapy', 'fast track'
            ],
            'merger_acquisition': [
                'merger', 'acquisition', 'buyout', 'takeover', 'deal', 'acquired by',
                'merge with', 'strategic partnership', 'joint venture'
            ],
            'contract_award': [
                'contract', 'awarded', 'government contract', 'defense contract',
                'partnership', 'agreement', 'deal signed', 'collaboration'
            ],
            'product_launch': [
                'product launch', 'new product', 'innovation', 'patent', 'technology',
                'breakthrough', 'revolutionary', 'first-of-its-kind'
            ],
            'analyst_upgrade': [
                'upgrade', 'price target', 'analyst', 'buy rating', 'outperform',
                'overweight', 'strong buy', 'raised target'
            ],
            'short_squeeze': [
                'short squeeze', 'short interest', 'heavily shorted', 'gamma squeeze',
                'retail investors', 'reddit', 'wallstreetbets'
            ]
        }
        
        # Request headers to avoid blocking
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        logger.info("News Scraper Manager initialized")
    
    def get_news_for_symbol(self, symbol: str, hours_back: int = 24) -> NewsAnalysisResult:
        """
        Get news analysis for a specific symbol
        
        Args:
            symbol: Stock symbol to analyze
            hours_back: How many hours back to search for news
            
        Returns:
            NewsAnalysisResult with comprehensive analysis
        """
        try:
            logger.info(f"Getting news for {symbol} (last {hours_back} hours)")
            
            # Collect articles from all sources
            all_articles = []
            
            # Search general financial news
            general_articles = self._scrape_general_news(hours_back)
            all_articles.extend(general_articles)
            
            # Search symbol-specific news
            symbol_articles = self._search_symbol_news(symbol, hours_back)
            all_articles.extend(symbol_articles)
            
            # Filter articles mentioning the symbol
            relevant_articles = self._filter_articles_by_symbol(all_articles, symbol)
            
            # Analyze articles for catalysts and sentiment
            analyzed_articles = []
            for article in relevant_articles:
                analyzed_article = self._analyze_article(article, symbol)
                if analyzed_article:
                    analyzed_articles.append(analyzed_article)
            
            # Create analysis result
            result = self._create_analysis_result(symbol, analyzed_articles)
            
            logger.info(f"Found {len(analyzed_articles)} relevant articles for {symbol}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting news for {symbol}: {e}")
            return self._create_empty_result(symbol)
    
    def _scrape_general_news(self, hours_back: int) -> List[NewsArticle]:
        """Scrape general financial news from RSS feeds"""
        articles = []
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        try:
            for source_name, config in self.news_sources.items():
                if not config['enabled'] or config['type'] != 'rss':
                    continue
                
                try:
                    logger.debug(f"Scraping {source_name}")
                    
                    # Parse RSS feed
                    feed = feedparser.parse(config['base_url'])
                    
                    for entry in feed.entries[:20]:  # Limit to recent articles
                        try:
                            # Parse publication date
                            pub_date = self._parse_date(entry.get('published', ''))
                            if pub_date and pub_date < cutoff_time:
                                continue
                            
                            # Extract article content
                            article_url = entry.get('link', '')
                            title = entry.get('title', '')
                            summary = entry.get('summary', '')
                            
                            # Get full article content if possible
                            content = self._extract_article_content(article_url)
                            if not content:
                                content = summary
                            
                            article = NewsArticle(
                                title=title,
                                content=content,
                                url=article_url,
                                source=source_name,
                                published_date=pub_date or datetime.now(),
                                symbols_mentioned=[]
                            )
                            
                            articles.append(article)
                            
                        except Exception as e:
                            logger.warning(f"Error processing article from {source_name}: {e}")
                            continue
                    
                    # Rate limiting
                    time.sleep(1)
                    
                except Exception as e:
                    logger.warning(f"Error scraping {source_name}: {e}")
                    continue
            
            logger.info(f"Scraped {len(articles)} general articles")
            return articles
            
        except Exception as e:
            logger.error(f"Error in general news scraping: {e}")
            return []
    
    def _search_symbol_news(self, symbol: str, hours_back: int) -> List[NewsArticle]:
        """Search for news specific to a symbol"""
        articles = []
        
        try:
            # Search Yahoo Finance for symbol-specific news
            yahoo_articles = self._search_yahoo_symbol_news(symbol, hours_back)
            articles.extend(yahoo_articles)
            
            # Search Google News for symbol
            google_articles = self._search_google_news(symbol, hours_back)
            articles.extend(google_articles)
            
            logger.info(f"Found {len(articles)} symbol-specific articles for {symbol}")
            return articles
            
        except Exception as e:
            logger.error(f"Error searching symbol news for {symbol}: {e}")
            return []
    
    def _search_yahoo_symbol_news(self, symbol: str, hours_back: int) -> List[NewsArticle]:
        """Search Yahoo Finance for symbol news"""
        articles = []
        
        try:
            # Yahoo Finance news URL for specific symbol
            url = f"https://finance.yahoo.com/quote/{symbol}/news"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return articles
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find news articles (Yahoo's structure may change)
            news_items = soup.find_all('div', class_='Ov(h)')
            
            for item in news_items[:10]:  # Limit results
                try:
                    title_elem = item.find('h3')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    link_elem = title_elem.find('a')
                    article_url = link_elem.get('href', '') if link_elem else ''
                    
                    # Make URL absolute
                    if article_url.startswith('/'):
                        article_url = f"https://finance.yahoo.com{article_url}"
                    
                    # Extract summary
                    summary_elem = item.find('p')
                    summary = summary_elem.get_text(strip=True) if summary_elem else ''
                    
                    article = NewsArticle(
                        title=title,
                        content=summary,
                        url=article_url,
                        source='yahoo_finance_symbol',
                        published_date=datetime.now(),  # Yahoo doesn't always show dates
                        symbols_mentioned=[symbol]
                    )
                    
                    articles.append(article)
                    
                except Exception as e:
                    logger.warning(f"Error parsing Yahoo article: {e}")
                    continue
            
            return articles
            
        except Exception as e:
            logger.warning(f"Error searching Yahoo news for {symbol}: {e}")
            return []
    
    def _search_google_news(self, symbol: str, hours_back: int) -> List[NewsArticle]:
        """Search Google News for symbol (simplified approach)"""
        articles = []
        
        try:
            # Note: This is a simplified approach. In production, you'd want to use
            # Google News API or a more sophisticated scraping method
            
            search_query = f"{symbol} stock news"
            # This is a placeholder - actual implementation would require
            # proper Google News API integration or RSS feed parsing
            
            logger.debug(f"Google News search for {symbol} not fully implemented")
            return articles
            
        except Exception as e:
            logger.warning(f"Error searching Google News for {symbol}: {e}")
            return []
    
    def _extract_article_content(self, url: str) -> Optional[str]:
        """Extract full article content from URL"""
        try:
            if not url:
                return None
            
            # Use newspaper3k to extract article content
            article = Article(url)
            article.download()
            article.parse()
            
            return article.text
            
        except Exception as e:
            logger.debug(f"Could not extract content from {url}: {e}")
            return None
    
    def _filter_articles_by_symbol(self, articles: List[NewsArticle], symbol: str) -> List[NewsArticle]:
        """Filter articles that mention the symbol"""
        relevant_articles = []
        
        try:
            symbol_variations = [
                symbol.upper(),
                symbol.lower(),
                f"${symbol.upper()}",
                f"${symbol.lower()}"
            ]
            
            for article in articles:
                # Check if symbol is mentioned in title or content
                text_to_search = f"{article.title} {article.content}".lower()
                
                symbol_mentioned = False
                for variation in symbol_variations:
                    if variation.lower() in text_to_search:
                        symbol_mentioned = True
                        break
                
                if symbol_mentioned:
                    # Add symbol to mentioned list if not already there
                    if symbol.upper() not in article.symbols_mentioned:
                        article.symbols_mentioned.append(symbol.upper())
                    relevant_articles.append(article)
            
            return relevant_articles
            
        except Exception as e:
            logger.error(f"Error filtering articles: {e}")
            return articles
    
    def _analyze_article(self, article: NewsArticle, symbol: str) -> Optional[NewsArticle]:
        """Analyze article for catalysts and sentiment"""
        try:
            # Detect catalyst type
            catalyst_type = self._detect_catalyst_type(article)
            article.catalyst_type = catalyst_type
            
            # Calculate relevance score
            relevance_score = self._calculate_relevance_score(article, symbol)
            article.relevance_score = relevance_score
            
            # Generate summary if content is long
            if len(article.content) > 500:
                article.summary = article.content[:500] + "..."
            else:
                article.summary = article.content
            
            return article
            
        except Exception as e:
            logger.warning(f"Error analyzing article: {e}")
            return article
    
    def _detect_catalyst_type(self, article: NewsArticle) -> Optional[str]:
        """Detect what type of catalyst the article represents"""
        try:
            text = f"{article.title} {article.content}".lower()
            
            # Check for each catalyst type
            for catalyst_type, keywords in self.catalyst_keywords.items():
                for keyword in keywords:
                    if keyword.lower() in text:
                        return catalyst_type
            
            return None
            
        except Exception:
            return None
    
    def _calculate_relevance_score(self, article: NewsArticle, symbol: str) -> float:
        """Calculate how relevant the article is to the symbol"""
        try:
            score = 0.0
            text = f"{article.title} {article.content}".lower()
            symbol_lower = symbol.lower()
            
            # Symbol mentions in title (high weight)
            if symbol_lower in article.title.lower():
                score += 50
            
            # Symbol mentions in content
            symbol_count = text.count(symbol_lower)
            score += min(symbol_count * 10, 30)  # Max 30 points
            
            # Catalyst detection bonus
            if article.catalyst_type:
                score += 20
            
            # Recency bonus (newer articles get higher scores)
            hours_old = (datetime.now() - article.published_date).total_seconds() / 3600
            if hours_old <= 1:
                score += 10
            elif hours_old <= 6:
                score += 5
            
            return min(score, 100)
            
        except Exception:
            return 50.0  # Default score
    
    def _create_analysis_result(self, symbol: str, articles: List[NewsArticle]) -> NewsAnalysisResult:
        """Create comprehensive news analysis result"""
        try:
            if not articles:
                return self._create_empty_result(symbol)
            
            # Count sentiment (placeholder - will be enhanced in sentiment analyzer)
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            
            # Detect catalysts
            catalyst_types = []
            catalyst_detected = False
            latest_catalyst_time = None
            
            for article in articles:
                # Sentiment counting (basic)
                if article.sentiment_score:
                    if article.sentiment_score > 0.1:
                        positive_count += 1
                    elif article.sentiment_score < -0.1:
                        negative_count += 1
                    else:
                        neutral_count += 1
                else:
                    neutral_count += 1
                
                # Catalyst detection
                if article.catalyst_type:
                    catalyst_detected = True
                    if article.catalyst_type not in catalyst_types:
                        catalyst_types.append(article.catalyst_type)
                    
                    if not latest_catalyst_time or article.published_date > latest_catalyst_time:
                        latest_catalyst_time = article.published_date
            
            # Calculate average sentiment
            sentiment_scores = [a.sentiment_score for a in articles if a.sentiment_score is not None]
            avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0.0
            
            # Calculate news momentum score
            news_momentum_score = self._calculate_news_momentum_score(
                articles, catalyst_detected, len(catalyst_types)
            )
            
            return NewsAnalysisResult(
                symbol=symbol,
                articles=articles,
                total_articles=len(articles),
                positive_articles=positive_count,
                negative_articles=negative_count,
                neutral_articles=neutral_count,
                avg_sentiment=avg_sentiment,
                catalyst_detected=catalyst_detected,
                catalyst_types=catalyst_types,
                news_momentum_score=news_momentum_score,
                latest_catalyst_time=latest_catalyst_time
            )
            
        except Exception as e:
            logger.error(f"Error creating analysis result: {e}")
            return self._create_empty_result(symbol)
    
    def _calculate_news_momentum_score(self, articles: List[NewsArticle], 
                                     catalyst_detected: bool, 
                                     catalyst_count: int) -> float:
        """Calculate news momentum score (0-100)"""
        try:
            score = 0.0
            
            # Article count score (30 points max)
            article_count = len(articles)
            score += min(article_count * 5, 30)
            
            # Catalyst detection score (40 points max)
            if catalyst_detected:
                score += 20 + min(catalyst_count * 10, 20)
            
            # Recency score (20 points max)
            recent_articles = [a for a in articles 
                             if (datetime.now() - a.published_date).total_seconds() < 3600]  # Last hour
            score += min(len(recent_articles) * 5, 20)
            
            # Relevance score (10 points max)
            avg_relevance = np.mean([a.relevance_score for a in articles if a.relevance_score])
            score += (avg_relevance / 100) * 10 if avg_relevance else 0
            
            return min(score, 100)
            
        except Exception:
            return 0.0
    
    def _create_empty_result(self, symbol: str) -> NewsAnalysisResult:
        """Create empty result when no news found"""
        return NewsAnalysisResult(
            symbol=symbol,
            articles=[],
            total_articles=0,
            positive_articles=0,
            negative_articles=0,
            neutral_articles=0,
            avg_sentiment=0.0,
            catalyst_detected=False,
            catalyst_types=[],
            news_momentum_score=0.0,
            latest_catalyst_time=None
        )
    
    def _parse_date(self, date_string: str) -> Optional[datetime]:
        """Parse various date formats"""
        try:
            if not date_string:
                return None
            
            # Try common formats
            formats = [
                '%a, %d %b %Y %H:%M:%S %Z',
                '%a, %d %b %Y %H:%M:%S %z',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%SZ'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_string, fmt)
                except ValueError:
                    continue
            
            # If all else fails, try feedparser's built-in parsing
            import time
            parsed_time = feedparser._parse_date(date_string)
            if parsed_time:
                return datetime(*parsed_time[:6])
            
            return None
            
        except Exception:
            return None

