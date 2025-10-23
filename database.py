"""
Database management for the Momentum Trading Strategy Tool
"""
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from ..core.logger import get_logger
from .exceptions import MomentumTraderError

logger = get_logger(__name__)

class DatabaseManager:
    """Manages database operations for the trading tool"""
    
    def __init__(self, database_url: str = "sqlite:///momentum_trader.db"):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self._create_tables()
    
    def _create_tables(self):
        """Create necessary database tables"""
        
        # Stock data table
        stock_data_sql = """
        CREATE TABLE IF NOT EXISTS stock_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            open_price REAL,
            high_price REAL,
            low_price REAL,
            close_price REAL,
            volume INTEGER,
            relative_volume REAL,
            market_cap REAL,
            float_shares INTEGER,
            sector TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, timestamp)
        )
        """
        
        # Screening results table
        screening_results_sql = """
        CREATE TABLE IF NOT EXISTS screening_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            price REAL,
            volume INTEGER,
            relative_volume REAL,
            float_shares INTEGER,
            gap_percentage REAL,
            sector TEXT,
            news_catalyst TEXT,
            score REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # Technical analysis table
        technical_analysis_sql = """
        CREATE TABLE IF NOT EXISTS technical_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            timeframe TEXT NOT NULL,
            macd_line REAL,
            macd_signal REAL,
            macd_histogram REAL,
            rsi REAL,
            ema_9 REAL,
            ema_20 REAL,
            sma_50 REAL,
            sma_200 REAL,
            pattern_detected TEXT,
            pattern_confidence REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, timestamp, timeframe)
        )
        """
        
        # News and sentiment table
        news_sentiment_sql = """
        CREATE TABLE IF NOT EXISTS news_sentiment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            headline TEXT NOT NULL,
            source TEXT,
            published_at DATETIME,
            sentiment_score REAL,
            sentiment_label TEXT,
            relevance_score REAL,
            url TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # Trading signals table
        trading_signals_sql = """
        CREATE TABLE IF NOT EXISTS trading_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            signal_type TEXT NOT NULL,
            price REAL,
            confidence REAL,
            entry_price REAL,
            stop_loss REAL,
            target_price REAL,
            risk_reward_ratio REAL,
            status TEXT DEFAULT 'active',
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # Execute table creation
        with self.engine.connect() as conn:
            conn.execute(text(stock_data_sql))
            conn.execute(text(screening_results_sql))
            conn.execute(text(technical_analysis_sql))
            conn.execute(text(news_sentiment_sql))
            conn.execute(text(trading_signals_sql))
            conn.commit()
        
        logger.info("Database tables created successfully")
    
    @contextmanager
    def get_session(self):
        """Get a database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def save_stock_data(self, data: List[Dict[str, Any]]) -> bool:
        """Save stock data to database"""
        try:
            df = pd.DataFrame(data)
            df.to_sql('stock_data', self.engine, if_exists='append', index=False)
            logger.info(f"Saved {len(data)} stock data records")
            return True
        except Exception as e:
            logger.error(f"Error saving stock data: {e}")
            return False
    
    def save_screening_results(self, results: List[Dict[str, Any]]) -> bool:
        """Save screening results to database"""
        try:
            df = pd.DataFrame(results)
            df.to_sql('screening_results', self.engine, if_exists='append', index=False)
            logger.info(f"Saved {len(results)} screening results")
            return True
        except Exception as e:
            logger.error(f"Error saving screening results: {e}")
            return False
    
    def save_technical_analysis(self, analysis: List[Dict[str, Any]]) -> bool:
        """Save technical analysis results to database"""
        try:
            df = pd.DataFrame(analysis)
            df.to_sql('technical_analysis', self.engine, if_exists='append', index=False)
            logger.info(f"Saved {len(analysis)} technical analysis records")
            return True
        except Exception as e:
            logger.error(f"Error saving technical analysis: {e}")
            return False
    
    def save_news_sentiment(self, news_data: List[Dict[str, Any]]) -> bool:
        """Save news and sentiment data to database"""
        try:
            df = pd.DataFrame(news_data)
            df.to_sql('news_sentiment', self.engine, if_exists='append', index=False)
            logger.info(f"Saved {len(news_data)} news sentiment records")
            return True
        except Exception as e:
            logger.error(f"Error saving news sentiment: {e}")
            return False
    
    def save_trading_signal(self, signal: Dict[str, Any]) -> bool:
        """Save a trading signal to database"""
        try:
            df = pd.DataFrame([signal])
            df.to_sql('trading_signals', self.engine, if_exists='append', index=False)
            logger.info(f"Saved trading signal for {signal.get('symbol')}")
            return True
        except Exception as e:
            logger.error(f"Error saving trading signal: {e}")
            return False
    
    def get_latest_screening_results(self, limit: int = 50) -> pd.DataFrame:
        """Get latest screening results"""
        query = """
        SELECT * FROM screening_results 
        ORDER BY created_at DESC 
        LIMIT ?
        """
        return pd.read_sql(query, self.engine, params=[limit])
    
    def get_stock_data(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Get historical stock data for a symbol"""
        start_date = datetime.now() - timedelta(days=days)
        query = """
        SELECT * FROM stock_data 
        WHERE symbol = ? AND timestamp >= ?
        ORDER BY timestamp ASC
        """
        return pd.read_sql(query, self.engine, params=[symbol, start_date])
    
    def get_active_signals(self) -> pd.DataFrame:
        """Get active trading signals"""
        query = """
        SELECT * FROM trading_signals 
        WHERE status = 'active'
        ORDER BY created_at DESC
        """
        return pd.read_sql(query, self.engine)
    
    def update_signal_status(self, signal_id: int, status: str, notes: str = None) -> bool:
        """Update trading signal status"""
        try:
            with self.engine.connect() as conn:
                query = text("""
                UPDATE trading_signals 
                SET status = :status, notes = :notes
                WHERE id = :signal_id
                """)
                conn.execute(query, {
                    'status': status,
                    'notes': notes,
                    'signal_id': signal_id
                })
                conn.commit()
            logger.info(f"Updated signal {signal_id} status to {status}")
            return True
        except Exception as e:
            logger.error(f"Error updating signal status: {e}")
            return False
    
    def cleanup_old_data(self, days: int = 90) -> bool:
        """Clean up old data from database"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with self.engine.connect() as conn:
                # Clean up old stock data
                conn.execute(text("""
                DELETE FROM stock_data 
                WHERE created_at < :cutoff_date
                """), {'cutoff_date': cutoff_date})
                
                # Clean up old screening results
                conn.execute(text("""
                DELETE FROM screening_results 
                WHERE created_at < :cutoff_date
                """), {'cutoff_date': cutoff_date})
                
                # Clean up old technical analysis
                conn.execute(text("""
                DELETE FROM technical_analysis 
                WHERE created_at < :cutoff_date
                """), {'cutoff_date': cutoff_date})
                
                # Clean up old news sentiment
                conn.execute(text("""
                DELETE FROM news_sentiment 
                WHERE created_at < :cutoff_date
                """), {'cutoff_date': cutoff_date})
                
                conn.commit()
            
            logger.info(f"Cleaned up data older than {days} days")
            return True
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return False

