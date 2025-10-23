#!/usr/bin/env python3
"""
Analyze POET and CPOP using Ross Cameron methodology
"""
import sys
import os
import json
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

def analyze_stock(symbol):
    """Analyze a single stock using Ross Cameron criteria"""
    print(f"\n🔍 ANALYZING {symbol}")
    print("="*50)
    
    try:
        import yfinance as yf
        
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period='10d')
        
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
        
        print(f"📊 BASIC INFO:")
        print(f"   Company: {company_name}")
        print(f"   Sector: {sector}")
        print(f"   Industry: {industry}")
        print(f"   Current Price: ${current_price:.2f}")
        print(f"   Previous Close: ${prev_close:.2f}")
        print(f"   Gap: {gap_percent:+.2f}%")
        print(f"   Volume: {current_volume:,}")
        print(f"   Avg Volume: {avg_volume:,.0f}")
        print(f"   Relative Volume: {relative_volume:.1f}x")
        print(f"   Float: {float_shares:,} shares")
        print(f"   Market Cap: ${market_cap:,}")
        print(f"   Week Range: ${week_low:.2f} - ${week_high:.2f}")
        print(f"   Position in Range: {price_range_position:.1f}%")
        
        # Ross Cameron 5 Pillars Analysis
        print(f"\n🎯 ROSS CAMERON 5 PILLARS ANALYSIS:")
        
        pillars = {}
        total_score = 0
        
        # Pillar 1: High Relative Volume (20 points)
        if relative_volume >= 5.0:
            volume_score = 20
            volume_grade = "A+"
        elif relative_volume >= 3.0:
            volume_score = 18
            volume_grade = "A"
        elif relative_volume >= 2.0:
            volume_score = 15
            volume_grade = "B"
        elif relative_volume >= 1.5:
            volume_score = 10
            volume_grade = "C"
        else:
            volume_score = 0
            volume_grade = "F"
        
        pillars['volume'] = {
            'score': volume_score,
            'grade': volume_grade,
            'value': relative_volume,
            'status': '✅' if volume_score >= 15 else '❌'
        }
        total_score += volume_score
        print(f"   1. Volume: {pillars['volume']['status']} {relative_volume:.1f}x ({volume_grade}) - {volume_score}/20")
        
        # Pillar 2: Significant Price Change (20 points)
        abs_gap = abs(gap_percent)
        if abs_gap >= 20.0:
            gap_score = 20
            gap_grade = "A+"
        elif abs_gap >= 10.0:
            gap_score = 18
            gap_grade = "A"
        elif abs_gap >= 4.0:
            gap_score = 15
            gap_grade = "B"
        elif abs_gap >= 2.0:
            gap_score = 10
            gap_grade = "C"
        else:
            gap_score = 0
            gap_grade = "F"
        
        pillars['gap'] = {
            'score': gap_score,
            'grade': gap_grade,
            'value': gap_percent,
            'status': '✅' if gap_score >= 15 else '❌'
        }
        total_score += gap_score
        print(f"   2. Gap: {pillars['gap']['status']} {gap_percent:+.1f}% ({gap_grade}) - {gap_score}/20")
        
        # Pillar 3: Low Float (20 points)
        if float_shares == 0:
            float_score = 10  # Unknown float gets partial credit
            float_grade = "?"
            float_status = "⚠️"
        elif float_shares <= 10_000_000:  # 10M
            float_score = 20
            float_grade = "A+"
            float_status = "✅"
        elif float_shares <= 20_000_000:  # 20M
            float_score = 18
            float_grade = "A"
            float_status = "✅"
        elif float_shares <= 50_000_000:  # 50M
            float_score = 15
            float_grade = "B"
            float_status = "✅"
        elif float_shares <= 100_000_000:  # 100M
            float_score = 10
            float_grade = "C"
            float_status = "❌"
        else:
            float_score = 0
            float_grade = "F"
            float_status = "❌"
        
        pillars['float'] = {
            'score': float_score,
            'grade': float_grade,
            'value': float_shares,
            'status': float_status
        }
        total_score += float_score
        print(f"   3. Float: {pillars['float']['status']} {float_shares:,} shares ({float_grade}) - {float_score}/20")
        
        # Pillar 4: Price Range (20 points)
        if 2.0 <= current_price <= 20.0:
            price_score = 20
            price_grade = "A+"
            price_status = "✅"
        elif 1.0 <= current_price <= 30.0:
            price_score = 15
            price_grade = "B"
            price_status = "✅"
        elif 0.5 <= current_price <= 50.0:
            price_score = 10
            price_grade = "C"
            price_status = "❌"
        else:
            price_score = 0
            price_grade = "F"
            price_status = "❌"
        
        pillars['price'] = {
            'score': price_score,
            'grade': price_grade,
            'value': current_price,
            'status': price_status
        }
        total_score += price_score
        print(f"   4. Price Range: {pillars['price']['status']} ${current_price:.2f} ({price_grade}) - {price_score}/20")
        
        # Pillar 5: Sector Preference (20 points)
        preferred_sectors = ['Healthcare', 'Technology', 'Communication Services', 'Biotechnology']
        preferred_industries = ['Biotechnology', 'Software', 'Semiconductors', 'Internet Content & Information']
        
        if sector in preferred_sectors or industry in preferred_industries:
            sector_score = 20
            sector_grade = "A+"
            sector_status = "✅"
        elif sector in ['Consumer Discretionary', 'Industrials']:
            sector_score = 15
            sector_grade = "B"
            sector_status = "✅"
        elif sector in ['Financial Services', 'Energy']:
            sector_score = 10
            sector_grade = "C"
            sector_status = "❌"
        else:
            sector_score = 5
            sector_grade = "D"
            sector_status = "❌"
        
        pillars['sector'] = {
            'score': sector_score,
            'grade': sector_grade,
            'value': f"{sector} / {industry}",
            'status': sector_status
        }
        total_score += sector_score
        print(f"   5. Sector: {pillars['sector']['status']} {sector} ({sector_grade}) - {sector_score}/20")
        
        # Overall Ross Cameron Grade
        if total_score >= 90:
            overall_grade = "A+"
            recommendation = "STRONG BUY"
            rec_color = "🟢"
        elif total_score >= 80:
            overall_grade = "A"
            recommendation = "BUY"
            rec_color = "🟢"
        elif total_score >= 70:
            overall_grade = "B"
            recommendation = "BUY"
            rec_color = "🟡"
        elif total_score >= 60:
            overall_grade = "C"
            recommendation = "HOLD"
            rec_color = "🟡"
        elif total_score >= 50:
            overall_grade = "D"
            recommendation = "AVOID"
            rec_color = "🔴"
        else:
            overall_grade = "F"
            recommendation = "SELL"
            rec_color = "🔴"
        
        print(f"\n🏆 ROSS CAMERON SCORE: {total_score}/100 ({overall_grade})")
        print(f"🎯 RECOMMENDATION: {rec_color} {recommendation}")
        
        # Risk Assessment
        print(f"\n⚠️ RISK ASSESSMENT:")
        risks = []
        
        if relative_volume < 2.0:
            risks.append("Low volume - may lack momentum")
        if abs_gap < 4.0:
            risks.append("Small gap - limited catalyst")
        if float_shares > 50_000_000:
            risks.append("High float - harder to move")
        if current_price > 20.0:
            risks.append("High price - limited retail interest")
        if price_range_position > 90:
            risks.append("Near week high - potential resistance")
        elif price_range_position < 10:
            risks.append("Near week low - potential support test")
        
        if not risks:
            risks.append("Low risk setup - good Ross Cameron candidate")
        
        for risk in risks:
            print(f"   • {risk}")
        
        # Trading Setup
        if total_score >= 70:
            print(f"\n💰 TRADING SETUP:")
            
            # Entry price (current or slight pullback)
            entry_price = current_price * 0.99 if gap_percent > 0 else current_price * 1.01
            
            # Stop loss (2-3% below entry for longs, above for shorts)
            if gap_percent > 0:  # Long setup
                stop_loss = entry_price * 0.97
                take_profit = entry_price * 1.06  # 2:1 R/R
                position_type = "LONG"
            else:  # Short setup
                stop_loss = entry_price * 1.03
                take_profit = entry_price * 0.94  # 2:1 R/R
                position_type = "SHORT"
            
            risk_per_share = abs(entry_price - stop_loss)
            reward_per_share = abs(take_profit - entry_price)
            risk_reward = reward_per_share / risk_per_share if risk_per_share > 0 else 0
            
            # Position sizing (2% account risk)
            account_value = 100000  # $100K demo account
            risk_amount = account_value * 0.02  # 2% risk
            shares = int(risk_amount / risk_per_share) if risk_per_share > 0 else 0
            
            print(f"   Position: {position_type}")
            print(f"   Entry: ${entry_price:.2f}")
            print(f"   Stop Loss: ${stop_loss:.2f}")
            print(f"   Take Profit: ${take_profit:.2f}")
            print(f"   Risk/Reward: 1:{risk_reward:.1f}")
            print(f"   Shares: {shares:,}")
            print(f"   Risk Amount: ${risk_amount:,.0f}")
        
        # Return analysis data
        return {
            'symbol': symbol,
            'company_name': company_name,
            'sector': sector,
            'industry': industry,
            'current_price': current_price,
            'gap_percent': gap_percent,
            'relative_volume': relative_volume,
            'float_shares': float_shares,
            'market_cap': market_cap,
            'pillars': pillars,
            'total_score': total_score,
            'overall_grade': overall_grade,
            'recommendation': recommendation,
            'risks': risks,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error analyzing {symbol}: {e}")
        return None

def main():
    """Main analysis function"""
    print("🚀 POET & CPOP ROSS CAMERON ANALYSIS")
    print("="*60)
    print(f"⏰ Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S EST')}")
    
    symbols = ['POET', 'CPOP']
    results = {}
    
    for symbol in symbols:
        result = analyze_stock(symbol)
        if result:
            results[symbol] = result
    
    # Comparison Summary
    if len(results) > 1:
        print(f"\n🏆 COMPARISON SUMMARY")
        print("="*60)
        
        sorted_results = sorted(results.items(), key=lambda x: x[1]['total_score'], reverse=True)
        
        for i, (symbol, data) in enumerate(sorted_results, 1):
            print(f"{i}. {symbol}: {data['total_score']}/100 ({data['overall_grade']}) - {data['recommendation']}")
            print(f"   ${data['current_price']:.2f} ({data['gap_percent']:+.1f}%) | {data['relative_volume']:.1f}x vol | {data['float_shares']:,} float")
        
        # Best candidate
        best_symbol, best_data = sorted_results[0]
        print(f"\n🥇 BEST ROSS CAMERON CANDIDATE: {best_symbol}")
        print(f"   Score: {best_data['total_score']}/100 ({best_data['overall_grade']})")
        print(f"   Recommendation: {best_data['recommendation']}")
    
    # Save results
    results_file = '/home/ubuntu/momentum_trader/poet_cpop_analysis.json'
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'symbols_analyzed': list(results.keys()),
            'results': results
        }, f, indent=2)
    
    print(f"\n💾 Analysis saved to: {results_file}")
    print(f"🎯 Analysis complete!")

if __name__ == "__main__":
    main()

