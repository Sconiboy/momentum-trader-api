"""
News Analysis module for the Momentum Trading Strategy Tool
"""

from .news_scraper import NewsScraperManager
from .sentiment_analyzer import SentimentAnalyzer
from .catalyst_detector import CatalystDetector

__all__ = [
    'NewsScraperManager',
    'SentimentAnalyzer', 
    'CatalystDetector'
]

