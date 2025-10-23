#!/usr/bin/env python3
"""
Test script to verify all data sources are working correctly
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.config import get_config
from src.core.logger import setup_logger
from src.data.data_manager import DataManager
from src.core.database import DatabaseManager

def test_yahoo_finance():
    """Test Yahoo Finance data source"""
    print("\n" + "="*50)
    print("TESTING YAHOO FINANCE")
    print("="*50)
    
    try:
        from src.data.yahoo_finance_client import YahooFinanceClient
        
        client = YahooFinanceClient()
        
        # Test with GITS (the stock we analyzed)
        print("Testing with GITS...")
        stock_info = client.get_stock_info('GITS')
        
        print(f"Symbol: {stock_info['symbol']}")
        print(f"Company: {stock_info['company_name']}")
        print(f"Current Price: ${stock_info['current_price']:.2f}")
        print(f"Volume: {stock_info['volume']:,}")
        print(f"Relative Volume: {stock_info['relative_volume']:.2f}x")
        print(f"Float Shares: {stock_info['float_shares']:,}")
        print(f"Market Cap: ${stock_info['market_cap']:,}")
        print(f"Sector: {stock_info['sector']}")
        print(f"Gap %: {stock_info['gap_percentage']:.2f}%")
        
        # Test historical data
        print("\nTesting historical data...")
        hist_data = client.get_stock_data('GITS', period='5d')
        print(f"Retrieved {len(hist_data)} historical records")
        
        print("✅ Yahoo Finance: WORKING")
        return True
        
    except Exception as e:
        print(f"❌ Yahoo Finance: FAILED - {e}")
        return False

def test_finviz_scraper():
    """Test Finviz scraper"""
    print("\n" + "="*50)
    print("TESTING FINVIZ SCRAPER")
    print("="*50)
    
    try:
        from src.data.finviz_scraper import FinvizScraper
        
        scraper = FinvizScraper()
        
        # Test with GITS
        print("Testing with GITS...")
        stock_data = scraper.get_stock_data('GITS')
        
        print(f"Symbol: {stock_data['symbol']}")
        print(f"Current Price: ${stock_data.get('current_price', 'N/A')}")
        print(f"Float Shares: {stock_data.get('float_shares', 'N/A'):,}")
        print(f"Relative Volume: {stock_data.get('relative_volume', 'N/A')}")
        print(f"Sector: {stock_data.get('sector', 'N/A')}")
        
        # Test screener
        print("\nTesting stock screener...")
        results = scraper.screen_stocks()
        print(f"Found {len(results)} stocks in screener")
        
        if results:
            print("Sample results:")
            for i, stock in enumerate(results[:3]):
                print(f"  {i+1}. {stock['symbol']} - ${stock['price']:.2f} - {stock['sector']}")
        
        # Test top gainers
        print("\nTesting top gainers...")
        gainers = scraper.get_top_gainers(5)
        print(f"Found {len(gainers)} top gainers")
        
        if gainers:
            print("Top gainers:")
            for i, stock in enumerate(gainers):
                print(f"  {i+1}. {stock['symbol']} - ${stock['price']:.2f} (+{stock['change_percent']:.2f}%)")
        
        print("✅ Finviz Scraper: WORKING")
        return True
        
    except Exception as e:
        print(f"❌ Finviz Scraper: FAILED - {e}")
        return False

def test_alpha_vantage():
    """Test Alpha Vantage (if API key available)"""
    print("\n" + "="*50)
    print("TESTING ALPHA VANTAGE")
    print("="*50)
    
    try:
        from src.data.alpha_vantage_client import AlphaVantageClient
        
        client = AlphaVantageClient()
        
        if not client.api_key:
            print("⚠️  Alpha Vantage: NO API KEY - Skipping")
            return True
        
        # Test API status
        status = client.get_api_status()
        print(f"API Status: {status}")
        
        if status['status'] == 'ok':
            # Test symbol search
            print("Testing symbol search...")
            results = client.search_symbols('GITS')
            print(f"Found {len(results)} search results")
            
            print("✅ Alpha Vantage: WORKING")
        else:
            print(f"⚠️  Alpha Vantage: {status['message']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Alpha Vantage: FAILED - {e}")
        return False

def test_data_manager():
    """Test the unified Data Manager"""
    print("\n" + "="*50)
    print("TESTING DATA MANAGER")
    print("="*50)
    
    try:
        config = get_config()
        db_manager = DatabaseManager()
        data_manager = DataManager(config, db_manager)
        
        # Test comprehensive stock data
        print("Testing comprehensive stock data for GITS...")
        stock_data = data_manager.get_comprehensive_stock_data('GITS')
        
        print(f"Symbol: {stock_data.symbol}")
        print(f"Current Price: ${stock_data.current_price:.2f}")
        print(f"Float Shares: {stock_data.float_shares:,}")
        print(f"Relative Volume: {stock_data.relative_volume:.2f}x")
        print(f"Gap %: {stock_data.gap_percentage:.2f}%")
        print(f"Sector: {stock_data.sector}")
        
        # Test Ross Cameron criteria
        criteria = stock_data.meets_ross_criteria(config)
        score = stock_data.calculate_score(config)
        
        print(f"\nRoss Cameron Criteria Check:")
        for criterion, passed in criteria.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {criterion.replace('_', ' ').title()}: {passed}")
        
        print(f"\nOverall Score: {score}/100")
        
        # Test data source status
        print("\nData Source Status:")
        status = data_manager.get_data_source_status()
        for source, state in status.items():
            emoji = "✅" if state == 'available' else "⚠️" if state == 'not_configured' else "❌"
            print(f"  {emoji} {source.replace('_', ' ').title()}: {state}")
        
        print("✅ Data Manager: WORKING")
        return True
        
    except Exception as e:
        print(f"❌ Data Manager: FAILED - {e}")
        return False

def test_ross_criteria_screening():
    """Test Ross Cameron criteria screening"""
    print("\n" + "="*50)
    print("TESTING ROSS CAMERON SCREENING")
    print("="*50)
    
    try:
        config = get_config()
        db_manager = DatabaseManager()
        data_manager = DataManager(config, db_manager)
        
        print("Running Ross Cameron criteria screening...")
        print("This may take a few minutes...")
        
        candidates = data_manager.screen_stocks_ross_criteria()
        
        print(f"\nFound {len(candidates)} stocks meeting Ross Cameron criteria:")
        print("-" * 80)
        print(f"{'Symbol':<8} {'Price':<8} {'Float':<12} {'RelVol':<8} {'Gap%':<8} {'Score':<6} {'Sector'}")
        print("-" * 80)
        
        for stock in candidates[:10]:  # Show top 10
            print(f"{stock.symbol:<8} ${stock.current_price:<7.2f} {stock.float_shares/1000000:<11.1f}M {stock.relative_volume:<7.1f}x {stock.gap_percentage:<7.1f}% {stock.calculate_score(config):<6.0f} {stock.sector[:20]}")
        
        if len(candidates) > 10:
            print(f"... and {len(candidates) - 10} more")
        
        print("✅ Ross Cameron Screening: WORKING")
        return True
        
    except Exception as e:
        print(f"❌ Ross Cameron Screening: FAILED - {e}")
        return False

def main():
    """Run all tests"""
    print("AI-Accelerated Momentum Trading Strategy Tool")
    print("Data Sources Test Suite")
    print("=" * 60)
    
    # Setup logging
    logger = setup_logger(level="WARNING")  # Reduce log noise during testing
    
    # Run tests
    tests = [
        ("Yahoo Finance", test_yahoo_finance),
        ("Finviz Scraper", test_finviz_scraper),
        ("Alpha Vantage", test_alpha_vantage),
        ("Data Manager", test_data_manager),
        ("Ross Criteria Screening", test_ross_criteria_screening)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except KeyboardInterrupt:
            print(f"\n⚠️  Test interrupted by user")
            break
        except Exception as e:
            print(f"❌ {test_name}: UNEXPECTED ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:<30} {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Data sources are ready for Phase 3.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()

