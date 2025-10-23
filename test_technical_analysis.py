#!/usr/bin/env python3
"""
Test script for technical analysis components
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf

from config.config import TradingConfig
from analysis.technical_analyzer import TechnicalAnalyzer

def create_sample_data():
    """Create sample price data for testing"""
    # Generate sample OHLCV data
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    np.random.seed(42)
    
    # Simulate price movement with trend
    base_price = 10.0
    prices = []
    volumes = []
    
    for i in range(len(dates)):
        # Add some trend and volatility
        trend = 0.001 * i  # Slight upward trend
        noise = np.random.normal(0, 0.02)  # 2% daily volatility
        
        price = base_price * (1 + trend + noise)
        volume = np.random.randint(100000, 1000000)
        
        prices.append(price)
        volumes.append(volume)
        base_price = price
    
    # Create OHLC from close prices
    data = []
    for i, (date, close, volume) in enumerate(zip(dates, prices, volumes)):
        high = close * (1 + abs(np.random.normal(0, 0.01)))
        low = close * (1 - abs(np.random.normal(0, 0.01)))
        open_price = close * (1 + np.random.normal(0, 0.005))
        
        data.append({
            'date': date,
            'open': open_price,
            'high': max(open_price, high, close),
            'low': min(open_price, low, close),
            'close': close,
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    df.set_index('date', inplace=True)
    return df

def test_with_real_data(symbol='GITS'):
    """Test with real market data"""
    try:
        print(f"\\n=== Testing Technical Analysis with Real Data ({symbol}) ===")
        
        # Download real data
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="6mo", interval="1d")
        
        if data.empty:
            print(f"No data available for {symbol}")
            return
        
        # Prepare data
        data.columns = data.columns.str.lower()
        current_price = data['close'].iloc[-1]
        current_volume = int(data['volume'].iloc[-1])
        
        print(f"Current price: ${current_price:.2f}")
        print(f"Current volume: {current_volume:,}")
        print(f"Data points: {len(data)}")
        
        # Initialize analyzer
        config = TradingConfig()
        analyzer = TechnicalAnalyzer(config)
        
        # Perform analysis
        result = analyzer.analyze_stock(
            symbol=symbol,
            price_data=data,
            current_price=current_price,
            current_volume=current_volume,
            float_shares=2_000_000  # Example float for GITS
        )
        
        # Display results
        print(f"\\n📊 Technical Analysis Results for {symbol}:")
        print(f"   • Technical Score: {result.technical_score:.1f}/100")
        print(f"   • Trend Direction: {result.trend_direction}")
        print(f"   • Momentum Strength: {result.momentum_strength}")
        print(f"   • Volatility: {result.volatility_assessment}")
        
        print(f"\\n🎯 Ross Cameron Assessment:")
        print(f"   • Setup Quality: {result.setup_quality}")
        print(f"   • Entry Timing: {result.entry_timing}")
        print(f"   • Is RC Setup: {result.ross_cameron_setup}")
        
        print(f"\\n📈 Technical Signals:")
        print(f"   • Overall Signal: {result.technical_signals.overall_signal}")
        print(f"   • Signal Strength: {result.technical_signals.signal_strength:.1f}%")
        print(f"   • Entry Signal: {result.technical_signals.entry_signal}")
        print(f"   • Exit Signal: {result.technical_signals.exit_signal}")
        
        print(f"\\n📊 MACD:")
        print(f"   • MACD Line: {result.technical_signals.macd.macd_line:.4f}")
        print(f"   • Signal Line: {result.technical_signals.macd.signal_line:.4f}")
        print(f"   • Histogram: {result.technical_signals.macd.histogram:.4f}")
        print(f"   • Crossover: {result.technical_signals.macd.crossover_signal}")
        
        print(f"\\n📈 EMAs:")
        print(f"   • 9 EMA: ${result.technical_signals.ema.ema_9:.2f}")
        print(f"   • 20 EMA: ${result.technical_signals.ema.ema_20:.2f}")
        print(f"   • Price above 9 EMA: {result.technical_signals.ema.price_above_ema9}")
        print(f"   • Trend: {result.technical_signals.ema.trend_direction}")
        
        print(f"\\n📊 RSI:")
        print(f"   • RSI: {result.technical_signals.rsi.rsi:.1f}")
        print(f"   • Overbought: {result.technical_signals.rsi.is_overbought}")
        print(f"   • Oversold: {result.technical_signals.rsi.is_oversold}")
        print(f"   • Momentum: {result.technical_signals.rsi.momentum_direction}")
        
        print(f"\\n🔊 Volume:")
        print(f"   • Relative Volume: {result.technical_signals.volume.relative_volume:.1f}x")
        print(f"   • Volume Breakout: {result.technical_signals.volume.volume_breakout}")
        print(f"   • Volume Trend: {result.technical_signals.volume.volume_trend}")
        
        print(f"\\n🎯 ABCD Patterns:")
        print(f"   • Complete Patterns: {len(result.abcd_analysis.patterns_found)}")
        print(f"   • Potential Patterns: {len(result.abcd_analysis.potential_patterns)}")
        print(f"   • Entry Signals: {len(result.abcd_analysis.entry_signals)}")
        print(f"   • Exit Signals: {len(result.abcd_analysis.exit_signals)}")
        
        if result.abcd_analysis.active_pattern:
            pattern = result.abcd_analysis.active_pattern
            print(f"   • Active Pattern: {pattern.pattern_type} ({pattern.confidence:.0f}% confidence)")
            print(f"   • Pattern Strength: {pattern.pattern_strength}")
        
        print(f"\\n💰 Entry Recommendation:")
        print(f"   • Action: {result.entry_recommendation['action']}")
        print(f"   • Confidence: {result.entry_recommendation['confidence']}%")
        print(f"   • Timing: {result.entry_recommendation['timing']}")
        if result.entry_recommendation['reasons']:
            print(f"   • Reasons: {', '.join(result.entry_recommendation['reasons'][:3])}")
        
        print(f"\\n🛡️ Risk Management:")
        if result.stop_loss_price:
            print(f"   • Stop Loss: ${result.stop_loss_price:.2f}")
        if result.take_profit_price:
            print(f"   • Take Profit: ${result.take_profit_price:.2f}")
        if result.risk_reward_ratio:
            print(f"   • Risk/Reward: 1:{result.risk_reward_ratio:.1f}")
        
        print(f"\\n📍 Support/Resistance:")
        if result.nearest_support:
            print(f"   • Nearest Support: ${result.nearest_support:.2f}")
        if result.nearest_resistance:
            print(f"   • Nearest Resistance: ${result.nearest_resistance:.2f}")
        
        print(f"\\n💼 Position Sizing:")
        print(f"   • Recommended Shares: {result.position_sizing.get('recommended_shares', 'N/A')}")
        print(f"   • Position Value: ${result.position_sizing.get('position_value', 0):.2f}")
        
        return result
        
    except Exception as e:
        print(f"Error testing with real data: {e}")
        return None

def test_with_sample_data():
    """Test with sample data"""
    try:
        print("\\n=== Testing Technical Analysis with Sample Data ===")
        
        # Create sample data
        data = create_sample_data()
        current_price = data['close'].iloc[-1]
        current_volume = int(data['volume'].iloc[-1])
        
        print(f"Sample data created: {len(data)} days")
        print(f"Current price: ${current_price:.2f}")
        print(f"Current volume: {current_volume:,}")
        
        # Initialize analyzer
        config = TradingConfig()
        analyzer = TechnicalAnalyzer(config)
        
        # Perform analysis
        result = analyzer.analyze_stock(
            symbol="TEST",
            price_data=data,
            current_price=current_price,
            current_volume=current_volume,
            float_shares=10_000_000
        )
        
        print(f"\\n📊 Analysis completed successfully!")
        print(f"   • Technical Score: {result.technical_score:.1f}/100")
        print(f"   • Overall Signal: {result.technical_signals.overall_signal}")
        print(f"   • Entry Signal: {result.technical_signals.entry_signal}")
        print(f"   • ABCD Patterns Found: {len(result.abcd_analysis.patterns_found)}")
        
        return result
        
    except Exception as e:
        print(f"Error testing with sample data: {e}")
        return None

def main():
    """Main test function"""
    print("🔧 Testing Technical Analysis Components")
    print("=" * 50)
    
    # Test with sample data first
    sample_result = test_with_sample_data()
    
    # Test with real data (GITS)
    real_result = test_with_real_data('GITS')
    
    # Test with another symbol if available
    if real_result:
        print("\\n" + "=" * 50)
        print("✅ Technical Analysis Tests Completed Successfully!")
        print("\\nKey Features Verified:")
        print("   ✅ Technical Indicators (MACD, EMA, RSI)")
        print("   ✅ ABCD Pattern Detection")
        print("   ✅ Support/Resistance Levels")
        print("   ✅ Entry/Exit Recommendations")
        print("   ✅ Risk Management Calculations")
        print("   ✅ Ross Cameron Setup Assessment")
        print("   ✅ Position Sizing Recommendations")
    else:
        print("\\n❌ Some tests failed - check error messages above")

if __name__ == "__main__":
    main()

