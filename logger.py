"""
Logging configuration for the Momentum Trading Strategy Tool
"""
import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional

def setup_logger(
    name: str = "momentum_trader",
    log_file: str = "logs/momentum_trader.log",
    level: str = "INFO",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up a logger with both file and console handlers
    
    Args:
        name: Logger name
        log_file: Path to log file
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
        
    Returns:
        Configured logger instance
    """
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance
    
    Args:
        name: Logger name (defaults to momentum_trader)
        
    Returns:
        Logger instance
    """
    if name is None:
        name = "momentum_trader"
    
    return logging.getLogger(name)

class TradeLogger:
    """Specialized logger for trading activities"""
    
    def __init__(self, logger_name: str = "momentum_trader.trades"):
        self.logger = get_logger(logger_name)
        
        # Set up trade-specific file handler
        trade_log_file = f"logs/trades_{datetime.now().strftime('%Y%m%d')}.log"
        trade_handler = logging.FileHandler(trade_log_file)
        trade_handler.setLevel(logging.INFO)
        
        trade_formatter = logging.Formatter(
            '%(asctime)s - TRADE - %(message)s'
        )
        trade_handler.setFormatter(trade_formatter)
        
        self.logger.addHandler(trade_handler)
    
    def log_signal(self, symbol: str, signal_type: str, price: float, confidence: float, details: dict):
        """Log a trading signal"""
        message = f"SIGNAL - {symbol} - {signal_type} - Price: ${price:.2f} - Confidence: {confidence:.2f} - Details: {details}"
        self.logger.info(message)
    
    def log_entry(self, symbol: str, price: float, quantity: int, strategy: str):
        """Log a trade entry"""
        message = f"ENTRY - {symbol} - Price: ${price:.2f} - Quantity: {quantity} - Strategy: {strategy}"
        self.logger.info(message)
    
    def log_exit(self, symbol: str, price: float, quantity: int, pnl: float, reason: str):
        """Log a trade exit"""
        message = f"EXIT - {symbol} - Price: ${price:.2f} - Quantity: {quantity} - P&L: ${pnl:.2f} - Reason: {reason}"
        self.logger.info(message)
    
    def log_screening_result(self, symbols: list, criteria: dict, timestamp: datetime):
        """Log screening results"""
        message = f"SCREENING - Found {len(symbols)} candidates - Criteria: {criteria} - Symbols: {symbols}"
        self.logger.info(message)

