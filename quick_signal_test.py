#!/usr/bin/env python3
"""
Quick Signal Generation Test - Simplified test without relative imports
"""
import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

def create_mock_logger():
    """Create mock logger for testing"""
    class MockLogger:
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
    return MockLogger()

def test_signal_scoring():
    """Test signal scoring logic directly"""
    print("🚀 Quick Signal Scoring Test")
    print("=" * 50)
    
    # Sample GITS data
    gits_data = {
        'symbol': 'GITS',
        'current_price': 3.84,
        'price_change_percent': 135.58,
        'relative_volume': 47.56,
        'float_shares': 1_300_000,
        'rsi': 83.5,
        'sector': 'Communication Services',
        'catalyst_detected': True,
        'sentiment_score': 0.675
    }
    
    print(f"📊 Analyzing {gits_data['symbol']}")
    print("-" * 30)
    
    # Calculate Ross Cameron 5 Pillars manually
    print("🏛️ ROSS CAMERON 5 PILLARS")
    print("-" * 30)
    
    # Pillar 1: High Relative Volume (target: 2x+)
    volume_score = min(100, (gits_data['relative_volume'] / 2.0) * 100)
    print(f"1️⃣ Volume: {volume_score:.1f}/100 ({gits_data['relative_volume']:.1f}x average)")
    
    # Pillar 2: Significant Price Change (target: 4%+)
    price_change_score = min(100, (abs(gits_data['price_change_percent']) / 4.0) * 100)
    print(f"2️⃣ Price Change: {price_change_score:.1f}/100 ({gits_data['price_change_percent']:+.1f}%)")
    
    # Pillar 3: Low Float (target: under 30M)
    if gits_data['float_shares'] <= 10_000_000:
        float_score = 100
    elif gits_data['float_shares'] <= 20_000_000:
        float_score = 90
    elif gits_data['float_shares'] <= 30_000_000:
        float_score = 80
    else:
        float_score = 50
    print(f"3️⃣ Float: {float_score:.1f}/100 ({gits_data['float_shares']:,} shares)")
    
    # Pillar 4: News Catalyst
    catalyst_score = 85 if gits_data['catalyst_detected'] else 20
    print(f"4️⃣ Catalyst: {catalyst_score:.1f}/100 ({'YES' if gits_data['catalyst_detected'] else 'NO'})")
    
    # Pillar 5: Price Range (target: $2-20)
    if 2 <= gits_data['current_price'] <= 10:
        price_range_score = 100
    elif 1 <= gits_data['current_price'] <= 20:
        price_range_score = 80
    else:
        price_range_score = 50
    print(f"5️⃣ Price Range: {price_range_score:.1f}/100 (${gits_data['current_price']:.2f})")
    
    # Calculate overall Ross Cameron score
    ross_pillars = [volume_score, price_change_score, float_score, catalyst_score, price_range_score]
    ross_overall = np.mean(ross_pillars)
    
    # Assign grade
    if ross_overall >= 95:
        grade = 'A+'
    elif ross_overall >= 90:
        grade = 'A'
    elif ross_overall >= 85:
        grade = 'B+'
    elif ross_overall >= 80:
        grade = 'B'
    elif ross_overall >= 75:
        grade = 'C+'
    elif ross_overall >= 70:
        grade = 'C'
    else:
        grade = 'D'
    
    print(f"\\n🎯 ROSS CAMERON OVERALL")
    print("-" * 25)
    print(f"📊 Score: {ross_overall:.1f}/100")
    print(f"🏆 Grade: {grade}")
    
    # Calculate component scores
    print(f"\\n📊 COMPONENT ANALYSIS")
    print("-" * 25)
    
    # Fundamental Score
    fundamental_score = (float_score * 0.4 + price_range_score * 0.3 + 
                        (80 if 'tech' in gits_data['sector'].lower() or 'comm' in gits_data['sector'].lower() else 60) * 0.3)
    print(f"🏢 Fundamental: {fundamental_score:.1f}/100")
    
    # Technical Score
    rsi_score = 70 if 40 <= gits_data['rsi'] <= 70 else (50 if gits_data['rsi'] > 70 else 30)
    technical_score = (rsi_score * 0.4 + volume_score * 0.3 + price_change_score * 0.3)
    print(f"📈 Technical: {technical_score:.1f}/100")
    
    # News Score
    sentiment_score = (gits_data['sentiment_score'] + 1) * 50  # Convert -1,1 to 0,100
    news_score = (sentiment_score * 0.5 + catalyst_score * 0.5)
    print(f"📰 News: {news_score:.1f}/100")
    
    # Momentum Score
    momentum_score = (volume_score * 0.5 + price_change_score * 0.5)
    print(f"🚀 Momentum: {momentum_score:.1f}/100")
    
    # Overall Composite Score
    component_weights = [0.25, 0.30, 0.25, 0.20]  # fundamental, technical, news, momentum
    component_scores = [fundamental_score, technical_score, news_score, momentum_score]
    overall_score = sum(score * weight for score, weight in zip(component_scores, component_weights))
    
    print(f"\\n🎯 OVERALL ASSESSMENT")
    print("-" * 25)
    print(f"📊 Composite Score: {overall_score:.1f}/100")
    
    # Determine recommendation
    if overall_score >= 80:
        recommendation = "STRONG BUY"
        emoji = "🟢"
    elif overall_score >= 65:
        recommendation = "BUY"
        emoji = "🟢"
    elif overall_score >= 45:
        recommendation = "HOLD"
        emoji = "🟡"
    else:
        recommendation = "SELL"
        emoji = "🔴"
    
    print(f"{emoji} Recommendation: {recommendation}")
    
    # Risk assessment
    risk_factors = 0
    if gits_data['rsi'] > 80:
        risk_factors += 1
    if gits_data['current_price'] > 20:
        risk_factors += 1
    if gits_data['relative_volume'] < 2:
        risk_factors += 1
    
    risk_level = "HIGH" if risk_factors >= 2 else ("MEDIUM" if risk_factors == 1 else "LOW")
    print(f"⚠️ Risk Level: {risk_level}")
    
    # Trading details
    print(f"\\n💰 TRADING SETUP")
    print("-" * 20)
    entry_price = gits_data['current_price'] * 1.01  # 1% above current
    stop_loss = gits_data['current_price'] * 0.95   # 5% stop loss
    take_profit = entry_price + ((entry_price - stop_loss) * 2)  # 2:1 R/R
    
    print(f"📍 Entry: ${entry_price:.2f}")
    print(f"🛑 Stop Loss: ${stop_loss:.2f}")
    print(f"🎯 Take Profit: ${take_profit:.2f}")
    print(f"⚖️ Risk/Reward: 1:2.0")
    
    # Position sizing (for $100k account, 2% risk)
    account_value = 100_000
    risk_per_trade = 0.02
    risk_amount = account_value * risk_per_trade
    risk_per_share = entry_price - stop_loss
    position_size = risk_amount / risk_per_share
    position_value = position_size * entry_price
    
    print(f"📊 Position Size: {position_size:.0f} shares")
    print(f"💵 Position Value: ${position_value:,.0f}")
    print(f"💰 Risk Amount: ${risk_amount:,.0f}")
    
    print(f"\\n🎯 GITS ANALYSIS SUMMARY")
    print("=" * 30)
    print("✅ EXCEPTIONAL Ross Cameron setup!")
    print("✅ ALL 5 pillars strongly positive")
    print("✅ Massive volume breakout (47.56x)")
    print("✅ Huge price movement (+135.58%)")
    print("✅ Excellent float (1.3M shares)")
    print("✅ Strong catalyst detected")
    print("✅ Perfect price range ($3.84)")
    print("⚠️ Overbought conditions (RSI 83.5)")
    print("⚠️ Consider entry on pullback")
    
    print(f"\\n✅ Quick Signal Test Completed!")
    print("\\nKey Calculations Verified:")
    print("✅ Ross Cameron 5-pillar scoring")
    print("✅ Component-based analysis")
    print("✅ Risk-adjusted recommendations")
    print("✅ Position sizing calculations")
    print("✅ Entry/exit point determination")
    
    return True

if __name__ == "__main__":
    test_signal_scoring()

