"""
Custom exceptions for the Momentum Trading Strategy Tool
"""

class MomentumTraderError(Exception):
    """Base exception for all momentum trader errors"""
    pass

class DataFetchError(MomentumTraderError):
    """Raised when data fetching fails"""
    pass

class AnalysisError(MomentumTraderError):
    """Raised when technical or fundamental analysis fails"""
    pass

class ConfigurationError(MomentumTraderError):
    """Raised when configuration is invalid"""
    pass

class PatternNotFoundError(AnalysisError):
    """Raised when expected trading pattern is not found"""
    pass

class InsufficientDataError(DataFetchError):
    """Raised when insufficient data is available for analysis"""
    pass

class APIError(DataFetchError):
    """Raised when API calls fail"""
    pass

class ValidationError(MomentumTraderError):
    """Raised when data validation fails"""
    pass

