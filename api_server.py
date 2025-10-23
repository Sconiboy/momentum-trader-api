#!/usr/bin/env python3
"""
FastAPI backend for Momentum Trader Pro
Serves live Ross Cameron stock analysis
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import yfinance as yf
from datetime import datetime
import uvicorn
import os

app = FastAPI(title="Momentum Trader Pro API", version="1.0.0")

# CORS configuration - allow frontend to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StockAnalysis(BaseModel):
    symbol: str
    company: str
    price: float
    change: float
    volume: str
    relativeVolume: float
    float: str
    rossScore: int
    grade: str
    recommendation: str
    pillars: Dict[str, int]

def analyze_stock_live(symbol: str) -> Optional[StockAnalysis]:
    """Analyze a stock using Ross Cameron methodology with live data"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period='10d')
        
        if len(hist) < 2:
            return None
        
        # Get current data
        current_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2]
        current_volume = hist['Volume'].iloc[-1]
        avg_volume = hist['Volume'][:-1].mean()
        
        # Calculate metrics
        gap_percent = ((current_price - prev_close) / prev_close) * 100
        relative_volume = current_volume / avg_volume if avg_volume > 0 else 0
        
        # Get company info
        company_name = info.get('longName', info.get('shortName', symbol))
        float_shares = info.get('floatShares', info.get('sharesOutstanding', 0))
        
        # Format float for display
        if float_shares >= 1_000_000:
            float_display = f"{float_shares / 1_000_000:.2f}M"
        elif float_shares >= 1_000:
            float_display = f"{float_shares / 1_000:.0f}K"
        else:
            float_display = str(float_shares)
        
        # Format volume for display
        if current_volume >= 1_000_000:
            volume_display = f"{current_volume / 1_000_000:.1f}M"
        elif current_volume >= 1_000:
            volume_display = f"{current_volume / 1_000:.0f}K"
        else:
            volume_display = str(int(current_volume))
        
        # Ross Cameron 5 Pillars Scoring
        pillars = {}
        total_score = 0
        
        # Pillar 1: Volume (20 points max)
        if relative_volume >= 10.0:
            volume_score = 100
        elif relative_volume >= 5.0:
            volume_score = 90
        elif relative_volume >= 3.0:
            volume_score = 80
        elif relative_volume >= 2.0:
            volume_score = 70
        elif relative_volume >= 1.5:
            volume_score = 50
        else:
            volume_score = 0
        pillars['volume'] = volume_score
        total_score += volume_score * 0.20
        
        # Pillar 2: Gap (20 points max)
        abs_gap = abs(gap_percent)
        if abs_gap >= 30.0:
            gap_score = 100
        elif abs_gap >= 20.0:
            gap_score = 90
        elif abs_gap >= 10.0:
            gap_score = 80
        elif abs_gap >= 4.0:
            gap_score = 70
        elif abs_gap >= 2.0:
            gap_score = 50
        else:
            gap_score = 0
        pillars['gap'] = gap_score
        total_score += gap_score * 0.20
        
        # Pillar 3: Float (20 points max)
        if float_shares == 0:
            float_score = 50
        elif float_shares <= 5_000_000:
            float_score = 100
        elif float_shares <= 10_000_000:
            float_score = 90
        elif float_shares <= 20_000_000:
            float_score = 80
        elif float_shares <= 50_000_000:
            float_score = 70
        elif float_shares <= 100_000_000:
            float_score = 50
        else:
            float_score = 0
        pillars['float'] = float_score
        total_score += float_score * 0.20
        
        # Pillar 4: Price Range (20 points max)
        if 2.0 <= current_price <= 20.0:
            price_score = 100
        elif 1.0 <= current_price <= 30.0:
            price_score = 80
        elif 0.5 <= current_price <= 50.0:
            price_score = 60
        elif current_price <= 100.0:
            price_score = 40
        else:
            price_score = 0
        pillars['price'] = price_score
        total_score += price_score * 0.20
        
        # Pillar 5: Sector (20 points max)
        sector = info.get('sector', 'Unknown')
        industry = info.get('industry', 'Unknown')
        preferred_sectors = ['Healthcare', 'Technology', 'Communication Services']
        preferred_industries = ['Biotechnology', 'Software', 'Semiconductors']
        
        if sector in preferred_sectors or industry in preferred_industries:
            sector_score = 100
        elif sector in ['Consumer Discretionary', 'Industrials', 'Real Estate']:
            sector_score = 80
        elif sector in ['Consumer Staples', 'Utilities']:
            sector_score = 60
        else:
            sector_score = 25
        pillars['sector'] = sector_score
        total_score += sector_score * 0.20
        
        # Overall grade and recommendation
        ross_score = int(total_score)
        
        if ross_score >= 90:
            grade = "A+"
            recommendation = "STRONG BUY"
        elif ross_score >= 85:
            grade = "A"
            recommendation = "STRONG BUY"
        elif ross_score >= 75:
            grade = "B+"
            recommendation = "BUY"
        elif ross_score >= 65:
            grade = "B"
            recommendation = "BUY"
        elif ross_score >= 55:
            grade = "C"
            recommendation = "HOLD"
        else:
            grade = "D"
            recommendation = "AVOID"
        
        return StockAnalysis(
            symbol=symbol,
            company=company_name,
            price=round(current_price, 2),
            change=round(gap_percent, 2),
            volume=volume_display,
            relativeVolume=round(relative_volume, 1),
            float=float_display,
            rossScore=ross_score,
            grade=grade,
            recommendation=recommendation,
            pillars=pillars
        )
        
    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return None

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "Momentum Trader Pro API",
        "version": "1.0.0",
        "description": "AI-Accelerated Ross Cameron Stock Analysis",
        "endpoints": {
            "/stocks": "Get top Ross Cameron candidates",
            "/stocks/{symbol}": "Get analysis for specific stock",
            "/health": "Health check"
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/stocks", response_model=List[StockAnalysis])
async def get_stocks(symbols: str = "GITS,CPOP,CLBR,SQFT"):
    """
    Get Ross Cameron analysis for multiple stocks
    
    Query params:
    - symbols: Comma-separated list of stock symbols (default: GITS,CPOP,CLBR,SQFT)
    """
    symbol_list = [s.strip().upper() for s in symbols.split(',')]
    results = []
    
    for symbol in symbol_list:
        analysis = analyze_stock_live(symbol)
        if analysis:
            results.append(analysis)
    
    # Sort by Ross score descending
    results.sort(key=lambda x: x.rossScore, reverse=True)
    
    return results

@app.get("/stocks/{symbol}", response_model=StockAnalysis)
async def get_stock(symbol: str):
    """
    Get Ross Cameron analysis for a specific stock
    
    Path params:
    - symbol: Stock ticker symbol (e.g., GITS, CPOP)
    """
    symbol = symbol.upper()
    analysis = analyze_stock_live(symbol)
    
    if not analysis:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found or insufficient data")
    
    return analysis

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print("🚀 Starting Momentum Trader Pro API Server...")
    print("📊 Live Ross Cameron Stock Analysis")
    print(f"🔗 API will be available at: http://0.0.0.0:{port}")
    print(f"📖 API docs at: http://0.0.0.0:{port}/docs")
    print("")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )

