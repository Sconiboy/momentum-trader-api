#!/usr/bin/env python3
"""
Analyze SQFT using Ross Cameron methodology
"""
import sys
import os
import json
from datetime import datetime, timedelta

def analyze_sqft():
    """Analyze SQFT using Ross Cameron criteria"""
    symbol = "SQFT"
    print(f"🔍 ANALYZING {symbol} - ROSS CAMERON METHODOLOGY")
    print("="*60)
    
    try:
        import yfinance as yf
        
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period='20d')  # Get more data for better analysis
        
        if len(hist) < 2:
            print(f"❌ {symbol}: Insufficient data")
            return None
        
        # Get current data
        current_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2]
        current_volume = hist['Volume'].iloc[-1]
        avg_volume = hist['Volume'][:-1].mean()  # Exclude today
        
        # Calculate metrics
        gap_percent = ((current_price - prev_close) / prev_close) * 100
        relative_volume = current_volume / avg_volume if avg_volume > 0 else 0
        
        # Get company info
        company_name = info.get('longName', info.get('shortName', 'Unknown'))
        float_shares = info.get('floatShares', info.get('sharesOutstanding', 0))
        market_cap = info.get('marketCap', 0)
        sector = info.get('sector', 'Unknown')
        industry = info.get('industry', 'Unknown')
        
        # Calculate additional metrics
        week_high = hist['High'].max()
        week_low = hist['Low'].min()
        price_range_position = ((current_price - week_low) / (week_high - week_low)) * 100 if week_high != week_low else 50
        
        # Calculate volatility
        returns = hist['Close'].pct_change().dropna()
        volatility = returns.std() * 100
        
        # Calculate momentum indicators
        if len(hist) >= 5:
            sma_5 = hist['Close'].rolling(5).mean().iloc[-1]
            price_vs_sma5 = ((current_price - sma_5) / sma_5) * 100
        else:
            sma_5 = current_price
            price_vs_sma5 = 0
        
        print(f"📊 COMPANY OVERVIEW:")
        print(f"   Company: {company_name}")
        print(f"   Sector: {sector}")
        print(f"   Industry: {industry}")
        print(f"   Exchange: {info.get('exchange', 'Unknown')}")
        print(f"   Country: {info.get('country', 'Unknown')}")
        
        print(f"\n💰 PRICE ACTION:")
        print(f"   Current Price: ${current_price:.2f}")
        print(f"   Previous Close: ${prev_close:.2f}")
        print(f"   Gap: {gap_percent:+.2f}%")
        print(f"   20-Day Range: ${week_low:.2f} - ${week_high:.2f}")
        print(f"   Position in Range: {price_range_position:.1f}%")
        print(f"   Daily Volatility: {volatility:.1f}%")
        print(f"   vs 5-Day SMA: {price_vs_sma5:+.1f}%")
        
        print(f"\n📊 VOLUME ANALYSIS:")
        print(f"   Current Volume: {current_volume:,}")
        print(f"   Average Volume: {avg_volume:,.0f}")
        print(f"   Relative Volume: {relative_volume:.1f}x")
        
        # Volume trend analysis
        if len(hist) >= 5:
            recent_vol = hist['Volume'].iloc[-5:].mean()
            older_vol = hist['Volume'].iloc[-10:-5].mean() if len(hist) >= 10 else recent_vol
            vol_trend = ((recent_vol - older_vol) / older_vol) * 100 if older_vol > 0 else 0
            print(f"   Volume Trend (5d): {vol_trend:+.1f}%")
        
        print(f"\n🏢 FUNDAMENTALS:")
        print(f"   Float: {float_shares:,} shares")
        print(f"   Market Cap: ${market_cap:,}")
        print(f"   Enterprise Value: ${info.get('enterpriseValue', 0):,}")
        print(f"   Book Value: ${info.get('bookValue', 0):.2f}")
        print(f"   P/E Ratio: {info.get('trailingPE', 'N/A')}")
        
        # Ross Cameron 5 Pillars Analysis
        print(f"\n🎯 ROSS CAMERON 5 PILLARS ANALYSIS:")
        print("="*50)
        
        pillars = {}
        total_score = 0
        
        # Pillar 1: High Relative Volume (20 points)
        if relative_volume >= 20.0:
            volume_score = 20
            volume_grade = "A+"
            volume_comment = "🚀 EXPLOSIVE volume breakout!"
        elif relative_volume >= 10.0:
            volume_score = 19
            volume_grade = "A+"
            volume_comment = "🔥 EXCEPTIONAL volume breakout!"
        elif relative_volume >= 5.0:
            volume_score = 18
            volume_grade = "A"
            volume_comment = "💪 Strong volume breakout"
        elif relative_volume >= 3.0:
            volume_score = 16
            volume_grade = "B+"
            volume_comment = "👍 Good volume increase"
        elif relative_volume >= 2.0:
            volume_score = 14
            volume_grade = "B"
            volume_comment = "✅ Adequate volume"
        elif relative_volume >= 1.5:
            volume_score = 10
            volume_grade = "C"
            volume_comment = "⚠️ Below average volume"
        else:
            volume_score = 0
            volume_grade = "F"
            volume_comment = "❌ Poor volume"
        
        pillars['volume'] = {
            'score': volume_score,
            'grade': volume_grade,
            'value': relative_volume,
            'status': '✅' if volume_score >= 14 else '❌',
            'comment': volume_comment
        }
        total_score += volume_score
        print(f"   1. 📊 VOLUME: {pillars['volume']['status']} {relative_volume:.1f}x ({volume_grade}) - {volume_score}/20")
        print(f"      {volume_comment}")
        
        # Pillar 2: Significant Price Change (20 points)
        abs_gap = abs(gap_percent)
        if abs_gap >= 50.0:
            gap_score = 20
            gap_grade = "A+"
            gap_comment = "🚀 EXPLOSIVE price movement!"
        elif abs_gap >= 30.0:
            gap_score = 19
            gap_grade = "A+"
            gap_comment = "🔥 MASSIVE price movement!"
        elif abs_gap >= 20.0:
            gap_score = 18
            gap_grade = "A"
            gap_comment = "💪 Strong price movement"
        elif abs_gap >= 10.0:
            gap_score = 16
            gap_grade = "B+"
            gap_comment = "👍 Good price movement"
        elif abs_gap >= 4.0:
            gap_score = 14
            gap_grade = "B"
            gap_comment = "✅ Adequate price movement"
        elif abs_gap >= 2.0:
            gap_score = 10
            gap_grade = "C"
            gap_comment = "⚠️ Small price movement"
        else:
            gap_score = 0
            gap_grade = "F"
            gap_comment = "❌ Minimal price movement"
        
        pillars['gap'] = {
            'score': gap_score,
            'grade': gap_grade,
            'value': gap_percent,
            'status': '✅' if gap_score >= 14 else '❌',
            'comment': gap_comment
        }
        total_score += gap_score
        print(f"   2. 📈 GAP: {pillars['gap']['status']} {gap_percent:+.1f}% ({gap_grade}) - {gap_score}/20")
        print(f"      {gap_comment}")
        
        # Pillar 3: Low Float (20 points)
        if float_shares == 0:
            float_score = 10  # Unknown float gets partial credit
            float_grade = "?"
            float_status = "⚠️"
            float_comment = "❓ Float unknown - needs verification"
        elif float_shares <= 2_000_000:  # 2M
            float_score = 20
            float_grade = "A+"
            float_status = "✅"
            float_comment = "🚀 ULTRA small float - explosive potential!"
        elif float_shares <= 5_000_000:  # 5M
            float_score = 19
            float_grade = "A+"
            float_status = "✅"
            float_comment = "🔥 PERFECT small float!"
        elif float_shares <= 10_000_000:  # 10M
            float_score = 18
            float_grade = "A"
            float_status = "✅"
            float_comment = "💪 Excellent small float"
        elif float_shares <= 20_000_000:  # 20M
            float_score = 16
            float_grade = "B+"
            float_status = "✅"
            float_comment = "👍 Good float size"
        elif float_shares <= 50_000_000:  # 50M
            float_score = 14
            float_grade = "B"
            float_status = "✅"
            float_comment = "✅ Acceptable float"
        elif float_shares <= 100_000_000:  # 100M
            float_score = 10
            float_grade = "C"
            float_status = "❌"
            float_comment = "⚠️ High float - harder to move"
        else:
            float_score = 0
            float_grade = "F"
            float_status = "❌"
            float_comment = "❌ Massive float - avoid"
        
        pillars['float'] = {
            'score': float_score,
            'grade': float_grade,
            'value': float_shares,
            'status': float_status,
            'comment': float_comment
        }
        total_score += float_score
        print(f"   3. 🏢 FLOAT: {pillars['float']['status']} {float_shares:,} shares ({float_grade}) - {float_score}/20")
        print(f"      {float_comment}")
        
        # Pillar 4: Price Range (20 points)
        if 2.0 <= current_price <= 20.0:
            price_score = 20
            price_grade = "A+"
            price_status = "✅"
            price_comment = "🎯 PERFECT Ross Cameron price range!"
        elif 1.0 <= current_price <= 30.0:
            price_score = 16
            price_grade = "B+"
            price_status = "✅"
            price_comment = "👍 Good price range"
        elif 0.5 <= current_price <= 50.0:
            price_score = 12
            price_grade = "B"
            price_status = "✅"
            price_comment = "✅ Acceptable price range"
        elif current_price <= 100.0:
            price_score = 8
            price_grade = "C"
            price_status = "❌"
            price_comment = "⚠️ High price - limited retail appeal"
        else:
            price_score = 0
            price_grade = "F"
            price_status = "❌"
            price_comment = "❌ Too expensive for momentum trading"
        
        pillars['price'] = {
            'score': price_score,
            'grade': price_grade,
            'value': current_price,
            'status': price_status,
            'comment': price_comment
        }
        total_score += price_score
        print(f"   4. 💰 PRICE: {pillars['price']['status']} ${current_price:.2f} ({price_grade}) - {price_score}/20")
        print(f"      {price_comment}")
        
        # Pillar 5: Sector Preference (20 points)
        preferred_sectors = ['Healthcare', 'Technology', 'Communication Services', 'Biotechnology']
        preferred_industries = ['Biotechnology', 'Software', 'Semiconductors', 'Internet Content & Information', 
                              'Medical Devices', 'Pharmaceuticals', 'Real Estate Services', 'Real Estate Development']
        
        if sector in preferred_sectors or industry in preferred_industries:
            sector_score = 20
            sector_grade = "A+"
            sector_status = "✅"
            sector_comment = "🎯 PREFERRED sector for momentum!"
        elif sector in ['Consumer Discretionary', 'Industrials', 'Real Estate']:
            sector_score = 16
            sector_grade = "B+"
            sector_status = "✅"
            sector_comment = "👍 Good sector for momentum"
        elif sector in ['Consumer Staples', 'Utilities']:
            sector_score = 12
            sector_grade = "B"
            sector_status = "✅"
            sector_comment = "✅ Neutral sector"
        elif sector in ['Financial Services', 'Energy']:
            sector_score = 8
            sector_grade = "C"
            sector_status = "❌"
            sector_comment = "⚠️ Less preferred sector"
        else:
            sector_score = 5
            sector_grade = "D"
            sector_status = "❌"
            sector_comment = "❌ Avoid this sector"
        
        pillars['sector'] = {
            'score': sector_score,
            'grade': sector_grade,
            'value': f"{sector} / {industry}",
            'status': sector_status,
            'comment': sector_comment
        }
        total_score += sector_score
        print(f"   5. 🏭 SECTOR: {pillars['sector']['status']} {sector} ({sector_grade}) - {sector_score}/20")
        print(f"      {sector_comment}")
        
        # Overall Ross Cameron Grade
        print(f"\n🏆 ROSS CAMERON FINAL SCORE")
        print("="*50)
        
        if total_score >= 95:
            overall_grade = "A+"
            recommendation = "STRONG BUY"
            rec_color = "🟢"
            rec_comment = "🚀 EXCEPTIONAL Ross Cameron setup!"
        elif total_score >= 85:
            overall_grade = "A"
            recommendation = "STRONG BUY"
            rec_color = "🟢"
            rec_comment = "🔥 Outstanding momentum candidate"
        elif total_score >= 75:
            overall_grade = "B+"
            recommendation = "BUY"
            rec_color = "🟢"
            rec_comment = "💪 Strong Ross Cameron candidate"
        elif total_score >= 65:
            overall_grade = "B"
            recommendation = "BUY"
            rec_color = "🟡"
            rec_comment = "👍 Good momentum candidate"
        elif total_score >= 55:
            overall_grade = "C"
            recommendation = "HOLD"
            rec_color = "🟡"
            rec_comment = "⚠️ Mixed signals - proceed with caution"
        elif total_score >= 45:
            overall_grade = "D"
            recommendation = "AVOID"
            rec_color = "🔴"
            rec_comment = "❌ Poor setup - avoid"
        else:
            overall_grade = "F"
            recommendation = "SELL"
            rec_color = "🔴"
            rec_comment = "🚫 Terrible setup - stay away"
        
        print(f"   TOTAL SCORE: {total_score}/100")
        print(f"   GRADE: {overall_grade}")
        print(f"   RECOMMENDATION: {rec_color} {recommendation}")
        print(f"   COMMENT: {rec_comment}")
        
        # Risk Assessment
        print(f"\n⚠️ RISK ASSESSMENT:")
        print("="*30)
        risks = []
        strengths = []
        
        if relative_volume < 2.0:
            risks.append("🔴 Low volume - may lack momentum")
        elif relative_volume >= 5.0:
            strengths.append("🟢 Exceptional volume confirms strong interest")
        else:
            strengths.append("🟢 Good volume confirms move")
            
        if abs_gap < 4.0:
            risks.append("🔴 Small gap - limited catalyst")
        elif abs_gap >= 20.0:
            strengths.append("🟢 Massive gap shows powerful catalyst")
        else:
            strengths.append("🟢 Significant gap shows catalyst")
            
        if float_shares > 50_000_000:
            risks.append("🔴 High float - harder to move")
        elif float_shares > 0 and float_shares <= 10_000_000:
            strengths.append("🟢 Small float - explosive potential")
        elif float_shares > 0 and float_shares <= 20_000_000:
            strengths.append("🟢 Good float size - easier to move")
            
        if current_price > 50.0:
            risks.append("🔴 High price - limited retail interest")
        elif 2.0 <= current_price <= 20.0:
            strengths.append("🟢 Perfect price range for retail traders")
        elif current_price < 1.0:
            risks.append("🔴 Very low price - potential delisting risk")
            
        if price_range_position > 95:
            risks.append("🔴 Near highs - potential resistance")
        elif price_range_position < 5:
            risks.append("🔴 Near lows - potential support test")
        else:
            strengths.append("🟢 Good position in trading range")
            
        if volatility > 20:
            risks.append("🔴 Extreme volatility - very high risk")
        elif volatility > 10:
            risks.append("🟡 High volatility - increased risk")
        elif volatility < 2:
            risks.append("🔴 Low volatility - may lack momentum")
        else:
            strengths.append("🟢 Healthy volatility level")
        
        print("   STRENGTHS:")
        for strength in strengths:
            print(f"     • {strength}")
        
        print("   RISKS:")
        for risk in risks:
            print(f"     • {risk}")
        
        if not risks:
            print("     • 🟢 Low risk setup - excellent candidate")
        
        # Trading Setup
        if total_score >= 65:
            print(f"\n💰 TRADING SETUP RECOMMENDATION:")
            print("="*40)
            
            # Entry price (current or slight pullback)
            if gap_percent > 0:  # Long setup
                entry_price = current_price * 0.995  # Slight pullback entry
                stop_loss = entry_price * 0.95  # 5% stop
                take_profit = entry_price * 1.10  # 10% target (2:1 R/R)
                position_type = "LONG"
            else:  # Short setup
                entry_price = current_price * 1.005  # Slight bounce entry
                stop_loss = entry_price * 1.05  # 5% stop
                take_profit = entry_price * 0.90  # 10% target (2:1 R/R)
                position_type = "SHORT"
            
            risk_per_share = abs(entry_price - stop_loss)
            reward_per_share = abs(take_profit - entry_price)
            risk_reward = reward_per_share / risk_per_share if risk_per_share > 0 else 0
            
            # Position sizing (2% account risk)
            account_value = 100000  # $100K demo account
            risk_amount = account_value * 0.02  # 2% risk
            shares = int(risk_amount / risk_per_share) if risk_per_share > 0 else 0
            position_value = shares * entry_price
            
            print(f"   POSITION TYPE: {position_type}")
            print(f"   ENTRY PRICE: ${entry_price:.2f}")
            print(f"   STOP LOSS: ${stop_loss:.2f} ({abs((stop_loss/entry_price-1)*100):.1f}%)")
            print(f"   TAKE PROFIT: ${take_profit:.2f} ({abs((take_profit/entry_price-1)*100):.1f}%)")
            print(f"   RISK/REWARD: 1:{risk_reward:.1f}")
            print(f"   SHARES: {shares:,}")
            print(f"   POSITION VALUE: ${position_value:,.0f}")
            print(f"   RISK AMOUNT: ${risk_amount:,.0f}")
            
            # Time horizon
            if total_score >= 90:
                time_horizon = "Scalp Trade (5-30min)"
            elif total_score >= 80:
                time_horizon = "Day Trade (30min - 4hrs)"
            elif total_score >= 70:
                time_horizon = "Swing Trade (1-5 days)"
            else:
                time_horizon = "Position Trade (1-2 weeks)"
            
            print(f"   TIME HORIZON: {time_horizon}")
            
            # Additional notes
            if relative_volume >= 10:
                print(f"   📝 NOTE: Exceptional volume - watch for continuation")
            if float_shares <= 5_000_000:
                print(f"   📝 NOTE: Small float - potential for explosive moves")
            if abs_gap >= 20:
                print(f"   📝 NOTE: Large gap - watch for follow-through or reversal")
        
        # Save analysis
        analysis_data = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'company_name': company_name,
            'sector': sector,
            'industry': industry,
            'current_price': current_price,
            'gap_percent': gap_percent,
            'relative_volume': relative_volume,
            'float_shares': float_shares,
            'market_cap': market_cap,
            'volatility': volatility,
            'price_range_position': price_range_position,
            'pillars': pillars,
            'total_score': total_score,
            'overall_grade': overall_grade,
            'recommendation': recommendation,
            'strengths': strengths,
            'risks': risks
        }
        
        # Save to file
        results_file = '/home/ubuntu/momentum_trader/sqft_analysis.json'
        with open(results_file, 'w') as f:
            json.dump(analysis_data, f, indent=2)
        
        print(f"\n💾 Analysis saved to: {results_file}")
        print(f"🎯 SQFT analysis complete!")
        
        return analysis_data
        
    except Exception as e:
        print(f"❌ Error analyzing SQFT: {e}")
        return None

if __name__ == "__main__":
    analyze_sqft()

