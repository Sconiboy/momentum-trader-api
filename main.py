"""
Main entry point for the AI-Accelerated Momentum Trading Strategy Tool
"""
import sys
import os
import argparse
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import get_config
from src.core.logger import setup_logger, get_logger, TradeLogger
from src.core.database import DatabaseManager
from src.core.exceptions import MomentumTraderError

def setup_application():
    """Initialize the application"""
    config = get_config()
    
    # Setup logging
    logger = setup_logger(
        name="momentum_trader",
        log_file=config.LOG_FILE,
        level=config.LOG_LEVEL
    )
    
    # Initialize database
    db_manager = DatabaseManager(config.data.DATABASE_URL)
    
    logger.info("=" * 60)
    logger.info("AI-Accelerated Momentum Trading Strategy Tool")
    logger.info("Inspired by Ross Cameron's Trading Methodology")
    logger.info("=" * 60)
    logger.info(f"Application started at {datetime.now()}")
    logger.info(f"Configuration loaded: {config}")
    
    return config, logger, db_manager

def run_screening_mode():
    """Run the stock screening mode"""
    config, logger, db_manager = setup_application()
    
    logger.info("Starting stock screening mode...")
    
    try:
        # Import screening modules (will be created in next phases)
        from src.screening.stock_screener import StockScreener
        from src.data.finviz_scraper import FinvizScraper
        
        # Initialize components
        screener = StockScreener(config, db_manager)
        finviz_scraper = FinvizScraper(config)
        
        # Run screening
        results = screener.run_screening()
        
        logger.info(f"Screening completed. Found {len(results)} candidates")
        
        # Display results
        for result in results:
            logger.info(f"Candidate: {result['symbol']} - Price: ${result['price']:.2f} - "
                       f"Float: {result['float_shares']:,} - Score: {result['score']:.2f}")
        
    except ImportError as e:
        logger.warning(f"Screening modules not yet implemented: {e}")
        logger.info("Please complete Phase 2 and 3 to enable screening functionality")
    except Exception as e:
        logger.error(f"Error in screening mode: {e}")
        raise

def run_analysis_mode(symbol: str):
    """Run analysis mode for a specific symbol"""
    config, logger, db_manager = setup_application()
    
    logger.info(f"Starting analysis mode for {symbol}...")
    
    try:
        # Import analysis modules (will be created in next phases)
        from src.analysis.technical_analyzer import TechnicalAnalyzer
        from src.analysis.pattern_detector import PatternDetector
        from src.signals.signal_generator import SignalGenerator
        
        # Initialize components
        tech_analyzer = TechnicalAnalyzer(config)
        pattern_detector = PatternDetector(config)
        signal_generator = SignalGenerator(config, db_manager)
        
        # Run analysis
        analysis_result = tech_analyzer.analyze_symbol(symbol)
        patterns = pattern_detector.detect_patterns(symbol)
        signals = signal_generator.generate_signals(symbol, analysis_result, patterns)
        
        logger.info(f"Analysis completed for {symbol}")
        logger.info(f"Technical indicators: {analysis_result}")
        logger.info(f"Patterns detected: {patterns}")
        logger.info(f"Signals generated: {signals}")
        
    except ImportError as e:
        logger.warning(f"Analysis modules not yet implemented: {e}")
        logger.info("Please complete Phase 4, 5, and 6 to enable analysis functionality")
    except Exception as e:
        logger.error(f"Error in analysis mode: {e}")
        raise

def run_web_mode():
    """Run the web interface mode"""
    config, logger, db_manager = setup_application()
    
    logger.info("Starting web interface mode...")
    
    try:
        # Import web modules (will be created in Phase 7)
        from src.web.app import create_app
        
        # Create and run Flask app
        app = create_app(config, db_manager)
        app.run(
            host=config.HOST,
            port=config.PORT,
            debug=config.DEBUG
        )
        
    except ImportError as e:
        logger.warning(f"Web modules not yet implemented: {e}")
        logger.info("Please complete Phase 7 to enable web interface functionality")
    except Exception as e:
        logger.error(f"Error in web mode: {e}")
        raise

def run_backtest_mode(start_date: str, end_date: str):
    """Run backtesting mode"""
    config, logger, db_manager = setup_application()
    
    logger.info(f"Starting backtest mode from {start_date} to {end_date}...")
    
    try:
        # Import backtesting modules (will be created in Phase 8)
        from src.analysis.backtester import Backtester
        
        # Initialize backtester
        backtester = Backtester(config, db_manager)
        
        # Run backtest
        results = backtester.run_backtest(start_date, end_date)
        
        logger.info(f"Backtest completed")
        logger.info(f"Results: {results}")
        
    except ImportError as e:
        logger.warning(f"Backtesting modules not yet implemented: {e}")
        logger.info("Please complete Phase 8 to enable backtesting functionality")
    except Exception as e:
        logger.error(f"Error in backtest mode: {e}")
        raise

def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(
        description="AI-Accelerated Momentum Trading Strategy Tool"
    )
    
    parser.add_argument(
        'mode',
        choices=['screen', 'analyze', 'web', 'backtest'],
        help='Operation mode'
    )
    
    parser.add_argument(
        '--symbol',
        type=str,
        help='Stock symbol for analysis mode'
    )
    
    parser.add_argument(
        '--start-date',
        type=str,
        help='Start date for backtesting (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--end-date',
        type=str,
        help='End date for backtesting (YYYY-MM-DD)'
    )
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'screen':
            run_screening_mode()
        elif args.mode == 'analyze':
            if not args.symbol:
                print("Error: --symbol is required for analyze mode")
                sys.exit(1)
            run_analysis_mode(args.symbol.upper())
        elif args.mode == 'web':
            run_web_mode()
        elif args.mode == 'backtest':
            if not args.start_date or not args.end_date:
                print("Error: --start-date and --end-date are required for backtest mode")
                sys.exit(1)
            run_backtest_mode(args.start_date, args.end_date)
            
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except MomentumTraderError as e:
        print(f"Application error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

