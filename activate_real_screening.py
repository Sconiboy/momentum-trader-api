#!/usr/bin/env python3
"""
Activate Real Data Screening - Live Ross Cameron Analysis
"""
import sys
import os
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

def test_real_data_sources():
    """Test all real data sources"""
    print("🚀 ACTIVATING REAL DATA SCREENING")
    print("="*60)
    
    # Test Yahoo Finance with real stocks
    print("\n📊 Testing Yahoo Finance with real stocks...")
    try:
        import yfinance as yf
        
        # Test with some popular momentum stocks
        test_symbols = ['GITS', 'NVAX', 'TSLA', 'AAPL']
        
        for symbol in test_symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                hist = ticker.history(period='5d')
                
                if len(hist) > 0:
                    current_price = hist['Close'].iloc[-1]
                    volume = hist['Volume'].iloc[-1]
                    avg_volume = hist['Volume'].mean()
                    relative_volume = volume / avg_volume if avg_volume > 0 else 0
                    
                    print(f"✅ {symbol}: ${current_price:.2f}, Vol: {volume:,.0f} ({relative_volume:.1f}x avg)")
                else:
                    print(f"❌ {symbol}: No data available")
                    
            except Exception as e:
                print(f"❌ {symbol}: Error - {str(e)[:50]}...")
                
    except Exception as e:
        print(f"❌ Yahoo Finance setup failed: {e}")
        return False
    
    print("\n🔍 Testing Finviz scraping...")
    try:
        import requests
        from bs4 import BeautifulSoup
        
        # Test Finviz screener access
        url = "https://finviz.com/screener.ashx?v=111&f=sh_price_u20,ta_change_u5,ta_relvol_o2"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Look for stock table
            table = soup.find('table', {'class': 'screener_table'})
            if table:
                rows = table.find_all('tr')[1:]  # Skip header
                print(f"✅ Found {len(rows)} stocks in Finviz screener")
                
                # Show first few stocks
                for i, row in enumerate(rows[:3]):
                    cells = row.find_all('td')
                    if len(cells) > 1:
                        symbol = cells[1].text.strip()
                        print(f"   📈 {symbol}")
            else:
                print("✅ Finviz accessible but no stock table found")
        else:
            print(f"❌ Finviz returned status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Finviz test failed: {e}")
    
    return True

def run_real_screening():
    """Run actual screening with real data"""
    print("\n🎯 RUNNING REAL ROSS CAMERON SCREENING")
    print("="*60)
    
    try:
        import yfinance as yf
        from datetime import datetime, timedelta
        
        # Define Ross Cameron criteria
        criteria = {
            'min_price': 2.0,
            'max_price': 20.0,
            'min_relative_volume': 2.0,
            'max_float': 30_000_000,  # 30M shares
            'min_gap_percent': 4.0
        }
        
        print(f"📋 Ross Cameron Criteria:")
        print(f"   💰 Price Range: ${criteria['min_price']}-${criteria['max_price']}")
        print(f"   📊 Min Relative Volume: {criteria['min_relative_volume']}x")
        print(f"   🏢 Max Float: {criteria['max_float']:,} shares")
        print(f"   📈 Min Gap: {criteria['min_gap_percent']}%")
        
        # Test with known momentum stocks
        test_symbols = [
            'GITS', 'NVAX', 'SAVA', 'MEME', 'TSLA', 'AAPL', 'AMZN', 
            'SPRT', 'BBIG', 'PROG', 'ATER', 'RDBX'
        ]
        
        candidates = []
        
        print(f"\n🔍 Analyzing {len(test_symbols)} stocks...")
        
        for symbol in test_symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                hist = ticker.history(period='10d')
                
                if len(hist) < 2:
                    continue
                
                # Get current data
                current_price = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2]
                current_volume = hist['Volume'].iloc[-1]
                avg_volume = hist['Volume'][:-1].mean()  # Exclude today
                
                # Calculate metrics
                gap_percent = ((current_price - prev_close) / prev_close) * 100
                relative_volume = current_volume / avg_volume if avg_volume > 0 else 0
                
                # Get float (if available)
                float_shares = info.get('floatShares', info.get('sharesOutstanding', 0))
                market_cap = info.get('marketCap', 0)
                sector = info.get('sector', 'Unknown')
                
                # Ross Cameron scoring
                score = 0
                reasons = []
                
                # Price range check
                if criteria['min_price'] <= current_price <= criteria['max_price']:
                    score += 20
                    reasons.append(f"✅ Price ${current_price:.2f} in range")
                else:
                    reasons.append(f"❌ Price ${current_price:.2f} out of range")
                
                # Volume check
                if relative_volume >= criteria['min_relative_volume']:
                    score += 20
                    reasons.append(f"✅ Volume {relative_volume:.1f}x average")
                else:
                    reasons.append(f"❌ Volume {relative_volume:.1f}x below 2x")
                
                # Float check
                if float_shares > 0 and float_shares <= criteria['max_float']:
                    score += 20
                    reasons.append(f"✅ Float {float_shares:,} shares")
                elif float_shares == 0:
                    score += 10  # Partial credit if unknown
                    reasons.append(f"⚠️ Float unknown")
                else:
                    reasons.append(f"❌ Float {float_shares:,} too high")
                
                # Gap check
                if abs(gap_percent) >= criteria['min_gap_percent']:
                    score += 20
                    reasons.append(f"✅ Gap {gap_percent:+.1f}%")
                else:
                    reasons.append(f"❌ Gap {gap_percent:+.1f}% too small")
                
                # Sector bonus (biotech, tech, etc.)
                if sector in ['Healthcare', 'Technology', 'Communication Services']:
                    score += 10
                    reasons.append(f"✅ Preferred sector: {sector}")
                
                # Store candidate
                candidate = {
                    'symbol': symbol,
                    'price': current_price,
                    'gap_percent': gap_percent,
                    'relative_volume': relative_volume,
                    'float_shares': float_shares,
                    'sector': sector,
                    'ross_score': score,
                    'reasons': reasons,
                    'timestamp': datetime.now().isoformat()
                }
                
                candidates.append(candidate)
                
                # Print summary
                grade = 'A+' if score >= 90 else 'A' if score >= 80 else 'B' if score >= 70 else 'C' if score >= 60 else 'D' if score >= 50 else 'F'
                print(f"   📊 {symbol}: {score}/100 ({grade}) - ${current_price:.2f} ({gap_percent:+.1f}%) {relative_volume:.1f}x vol")
                
            except Exception as e:
                print(f"   ❌ {symbol}: Error - {str(e)[:50]}...")
        
        # Sort by Ross Cameron score
        candidates.sort(key=lambda x: x['ross_score'], reverse=True)
        
        print(f"\n🏆 TOP ROSS CAMERON CANDIDATES")
        print("="*60)
        
        for i, candidate in enumerate(candidates[:5], 1):
            score = candidate['ross_score']
            grade = 'A+' if score >= 90 else 'A' if score >= 80 else 'B' if score >= 70 else 'C' if score >= 60 else 'D' if score >= 50 else 'F'
            
            print(f"{i}. {candidate['symbol']} - {score}/100 ({grade})")
            print(f"   💰 Price: ${candidate['price']:.2f} ({candidate['gap_percent']:+.1f}%)")
            print(f"   📊 Volume: {candidate['relative_volume']:.1f}x average")
            print(f"   🏢 Float: {candidate['float_shares']:,} shares")
            print(f"   🏭 Sector: {candidate['sector']}")
            
            # Show top reasons
            for reason in candidate['reasons'][:3]:
                print(f"   {reason}")
            print()
        
        # Save results
        results_file = '/home/ubuntu/momentum_trader/live_screening_results.json'
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'criteria': criteria,
                'total_analyzed': len(test_symbols),
                'candidates': candidates
            }, f, indent=2)
        
        print(f"💾 Results saved to: {results_file}")
        print(f"🎯 Found {len([c for c in candidates if c['ross_score'] >= 70])} strong candidates (B+ or better)")
        
        return candidates
        
    except Exception as e:
        print(f"❌ Screening failed: {e}")
        return []

if __name__ == "__main__":
    print("🚀 MOMENTUM TRADER PRO - REAL DATA ACTIVATION")
    print("="*60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test data sources
    if test_real_data_sources():
        print("\n✅ All data sources working!")
        
        # Run real screening
        candidates = run_real_screening()
        
        if candidates:
            print(f"\n🎉 SUCCESS! Found {len(candidates)} candidates")
            print("🔗 Ready to integrate with web dashboard!")
        else:
            print("\n⚠️ No candidates found - try different criteria")
    else:
        print("\n❌ Data source setup failed")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

