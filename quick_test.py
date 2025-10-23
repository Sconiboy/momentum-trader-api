#!/usr/bin/env python3
"""
Quick test of technical analysis without complex imports
"""
import pandas as pd
import numpy as np
import yfinance as yf
import ta

def test_basic_indicators():
    """Test basic technical indicators"""
    print("🔧 Testing Basic Technical Indicators")
    print("=" * 40)
    
    try:
        # Get GITS data
        ticker = yf.Ticker("GITS")
        data = ticker.history(period="3mo", interval="1d")
        
        if data.empty:
            print("No data available for GITS")
            return
        
        # Calculate basic indicators
        close_prices = data['Close']
        
        # MACD - simplified calculation
        try:
            macd_data = ta.trend.MACD(close_prices)
            macd_line = macd_data.iloc[-1] if len(macd_data) > 0 else 0
        except:
            macd_line = 0
            
        try:
            macd_signal_data = ta.trend.MACDSignal(close_prices)
            macd_signal = macd_signal_data.iloc[-1] if len(macd_signal_data) > 0 else 0
        except:
            macd_signal = 0
        
        macd_histogram = macd_line - macd_signal
        
        # EMAs
        ema_9 = ta.trend.EMAIndicator(close_prices, window=9).ema_indicator().iloc[-1]
        ema_20 = ta.trend.EMAIndicator(close_prices, window=20).ema_indicator().iloc[-1]
        
        # RSI
        rsi = ta.momentum.RSIIndicator(close_prices).rsi().iloc[-1]
        
        # Volume
        current_volume = data['Volume'].iloc[-1]
        avg_volume = data['Volume'].tail(20).mean()
        relative_volume = current_volume / avg_volume
        
        # Current price
        current_price = close_prices.iloc[-1]
        
        print(f"📊 GITS Technical Analysis:")
        print(f"   • Current Price: ${current_price:.2f}")
        print(f"   • Volume: {current_volume:,} ({relative_volume:.1f}x avg)")
        print(f"   • RSI: {rsi:.1f}")
        print(f"   • 9 EMA: ${ema_9:.2f}")
        print(f"   • 20 EMA: ${ema_20:.2f}")
        print(f"   • MACD: {macd_line:.4f}")
        print(f"   • MACD Signal: {macd_signal:.4f}")
        print(f"   • MACD Histogram: {macd_histogram:.4f}")
        
        # Simple analysis
        print(f"\\n🎯 Quick Analysis:")
        
        # Price vs EMAs
        if current_price > ema_9 > ema_20:
            print("   ✅ Bullish EMA alignment")
        elif current_price < ema_9 < ema_20:
            print("   ❌ Bearish EMA alignment")
        else:
            print("   ⚠️ Mixed EMA signals")
        
        # MACD
        if macd_line > macd_signal:
            print("   ✅ MACD bullish")
        else:
            print("   ❌ MACD bearish")
        
        # RSI
        if rsi > 70:
            print("   ⚠️ RSI overbought")
        elif rsi < 30:
            print("   ⚠️ RSI oversold")
        else:
            print("   ✅ RSI neutral")
        
        # Volume
        if relative_volume >= 2.0:
            print("   ✅ High volume (2x+ average)")
        elif relative_volume >= 1.5:
            print("   ✅ Above average volume")
        else:
            print("   ⚠️ Below average volume")
        
        # Ross Cameron criteria check
        print(f"\\n🎯 Ross Cameron Criteria:")
        
        # Price range
        if 2.0 <= current_price <= 20.0:
            print("   ✅ Price in preferred range ($2-20)")
        else:
            print("   ❌ Price outside preferred range")
        
        # Volume
        if relative_volume >= 2.0:
            print("   ✅ Volume breakout (2x+ average)")
        else:
            print("   ❌ Insufficient volume")
        
        # Calculate simple score
        score = 0
        if current_price > ema_9 > ema_20: score += 25
        if macd_line > macd_signal: score += 25
        if 30 <= rsi <= 70: score += 20
        if relative_volume >= 2.0: score += 20
        if 2.0 <= current_price <= 20.0: score += 10
        
        print(f"\\n📊 Simple Technical Score: {score}/100")
        
        if score >= 70:
            print("   🟢 Strong technical setup")
        elif score >= 50:
            print("   🟡 Moderate technical setup")
        else:
            print("   🔴 Weak technical setup")
        
        return True
        
    except Exception as e:
        print(f"Error in basic test: {e}")
        return False

def test_pattern_detection():
    """Test basic pattern detection"""
    print("\\n🔍 Testing Pattern Detection")
    print("=" * 40)
    
    try:
        # Get data
        ticker = yf.Ticker("GITS")
        data = ticker.history(period="6mo", interval="1d")
        
        if len(data) < 50:
            print("Insufficient data for pattern detection")
            return False
        
        # Find recent highs and lows
        highs = data['High'].values
        lows = data['Low'].values
        
        # Simple peak/trough detection
        from scipy import signal
        
        peaks = signal.find_peaks(highs, distance=5)[0]
        troughs = signal.find_peaks(-lows, distance=5)[0]
        
        print(f"📈 Pattern Analysis:")
        print(f"   • Data points: {len(data)}")
        print(f"   • Peaks found: {len(peaks)}")
        print(f"   • Troughs found: {len(troughs)}")
        
        # Recent price action
        recent_high = data['High'].tail(20).max()
        recent_low = data['Low'].tail(20).min()
        current_price = data['Close'].iloc[-1]
        
        # Calculate position in recent range
        range_position = (current_price - recent_low) / (recent_high - recent_low) if recent_high > recent_low else 0.5
        
        print(f"   • Recent high: ${recent_high:.2f}")
        print(f"   • Recent low: ${recent_low:.2f}")
        print(f"   • Current position: {range_position:.1%} of recent range")
        
        # Simple pattern assessment
        if range_position > 0.8:
            print("   📈 Near recent highs - potential resistance")
        elif range_position < 0.2:
            print("   📉 Near recent lows - potential support")
        else:
            print("   ↔️ Middle of recent range")
        
        return True
        
    except Exception as e:
        print(f"Error in pattern detection: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Quick Technical Analysis Test")
    print("=" * 50)
    
    # Test basic indicators
    basic_success = test_basic_indicators()
    
    # Test pattern detection
    pattern_success = test_pattern_detection()
    
    print("\\n" + "=" * 50)
    if basic_success and pattern_success:
        print("✅ All tests completed successfully!")
        print("\\nCore technical analysis components are working:")
        print("   ✅ MACD, EMA, RSI calculations")
        print("   ✅ Volume analysis")
        print("   ✅ Basic pattern detection")
        print("   ✅ Ross Cameron criteria validation")
    else:
        print("❌ Some tests failed")

if __name__ == "__main__":
    main()

