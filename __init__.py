"""
Core module for the Momentum Trading Strategy Tool
"""

from .logger import setup_logger, get_logger
from .database import DatabaseManager
from .exceptions import (
    MomentumTraderError,
    DataFetchError,
    AnalysisError,
    ConfigurationError
)

__all__ = [
    'setup_logger',
    'get_logger', 
    'DatabaseManager',
    'MomentumTraderError',
    'DataFetchError',
    'AnalysisError',
    'ConfigurationError'
]

