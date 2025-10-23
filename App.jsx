import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert.jsx'
import { 
  TrendingUp, 
  TrendingDown, 
  Volume2, 
  Target, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  DollarSign,
  BarChart3,
  Zap,
  Star,
  Activity,
  Bell,
  Settings,
  RefreshCw,
  Eye,
  Filter,
  Search
} from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts'
import './App.css'

// Sample data for demonstration
const sampleStocks = [
  {
    symbol: 'GITS',
    name: 'Global Interactive Technologies',
    price: 3.84,
    change: 135.58,
    volume: '46.2M',
    relativeVolume: 47.56,
    float: '1.3M',
    rossScore: 97.0,
    grade: 'A+',
    compositeScore: 88.6,
    recommendation: 'STRONG BUY',
    risk: 'MEDIUM',
    entry: 3.88,
    stopLoss: 3.65,
    takeProfit: 4.34,
    pillars: {
      volume: 100,
      priceChange: 100,
      float: 100,
      catalyst: 85,
      priceRange: 100
    },
    alerts: ['🔥 EXCEPTIONAL SETUP', '🚀 MASSIVE VOLUME', '🎯 PERFECT ROSS SETUP'],
    sector: 'Communication Services',
    lastUpdate: '2 min ago'
  },
  {
    symbol: 'NVAX',
    name: 'Novavax Inc',
    price: 12.45,
    change: 15.8,
    volume: '8.2M',
    relativeVolume: 4.2,
    float: '78M',
    rossScore: 85.0,
    grade: 'B+',
    compositeScore: 85.0,
    recommendation: 'STRONG BUY',
    risk: 'LOW',
    entry: 12.57,
    stopLoss: 11.83,
    takeProfit: 14.07,
    pillars: {
      volume: 100,
      priceChange: 100,
      float: 60,
      catalyst: 85,
      priceRange: 80
    },
    alerts: ['📈 BIOTECH CATALYST', '✅ LOW RISK'],
    sector: 'Biotechnology',
    lastUpdate: '5 min ago'
  },
  {
    symbol: 'MEME',
    name: 'Meme Stock Corp',
    price: 4.67,
    change: 89.3,
    volume: '25.1M',
    relativeVolume: 25.8,
    float: '15M',
    rossScore: 95.0,
    grade: 'A+',
    compositeScore: 86.9,
    recommendation: 'STRONG BUY',
    risk: 'MEDIUM',
    entry: 4.72,
    stopLoss: 4.30,
    takeProfit: 5.56,
    pillars: {
      volume: 100,
      priceChange: 100,
      float: 90,
      catalyst: 85,
      priceRange: 100
    },
    alerts: ['⚡ MEME PUMP', '⚠️ OVERBOUGHT'],
    sector: 'Entertainment',
    lastUpdate: '1 min ago'
  },
  {
    symbol: 'TSLA',
    name: 'Tesla Inc',
    price: 245.30,
    change: 8.7,
    volume: '45.2M',
    relativeVolume: 2.3,
    float: '800M',
    rossScore: 69.0,
    grade: 'D',
    compositeScore: 73.1,
    recommendation: 'BUY',
    risk: 'MEDIUM',
    entry: 247.75,
    stopLoss: 225.68,
    takeProfit: 291.91,
    pillars: {
      volume: 100,
      priceChange: 100,
      float: 30,
      catalyst: 85,
      priceRange: 30
    },
    alerts: ['🔋 EV MOMENTUM'],
    sector: 'Automotive',
    lastUpdate: '3 min ago'
  }
]

const chartData = [
  { time: '9:30', price: 1.63, volume: 2.1 },
  { time: '10:00', price: 2.45, volume: 8.5 },
  { time: '10:30', price: 3.12, volume: 15.2 },
  { time: '11:00', price: 3.84, volume: 46.2 },
  { time: '11:30', price: 4.12, volume: 38.7 },
  { time: '12:00', price: 3.95, volume: 25.3 }
]

const portfolioData = [
  { name: 'Available Cash', value: 80000, color: '#22c55e' },
  { name: 'Positions', value: 20000, color: '#3b82f6' }
]

function App() {
  const [selectedStock, setSelectedStock] = useState(sampleStocks[0])
  const [isLive, setIsLive] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(new Date())

  useEffect(() => {
    const interval = setInterval(() => {
      if (isLive) {
        setLastUpdate(new Date())
      }
    }, 30000) // Update every 30 seconds

    return () => clearInterval(interval)
  }, [isLive])

  const getRecommendationColor = (recommendation) => {
    switch (recommendation) {
      case 'STRONG BUY': return 'bg-green-500'
      case 'BUY': return 'bg-green-400'
      case 'HOLD': return 'bg-yellow-500'
      case 'SELL': return 'bg-red-400'
      case 'STRONG SELL': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'LOW': return 'bg-green-500'
      case 'MEDIUM': return 'bg-yellow-500'
      case 'HIGH': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const getGradeColor = (grade) => {
    if (grade.startsWith('A')) return 'text-green-500'
    if (grade.startsWith('B')) return 'text-blue-500'
    if (grade.startsWith('C')) return 'text-yellow-500'
    return 'text-red-500'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-slate-100 to-slate-200 text-slate-900">
      {/* Header */}
      <header className="border-b border-slate-300 bg-white/90 backdrop-blur-sm shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Zap className="h-8 w-8 text-blue-400" />
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                  Momentum Trader Pro
                </h1>
              </div>
              <Badge variant="outline" className="text-green-400 border-green-400">
                AI-Enhanced Ross Cameron Strategy
              </Badge>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${isLive ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`} />
                <span className="text-sm text-slate-400">
                  {isLive ? 'Live' : 'Paused'} • Updated {lastUpdate.toLocaleTimeString()}
                </span>
              </div>
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsLive(!isLive)}
                className="border-slate-600 hover:bg-slate-700"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${isLive ? 'animate-spin' : ''}`} />
                {isLive ? 'Pause' : 'Resume'}
              </Button>
              
              <Button variant="outline" size="sm" className="border-slate-600 hover:bg-slate-700">
                <Settings className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-6">
        <Tabs defaultValue="dashboard" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 bg-slate-800 border-slate-700">
            <TabsTrigger value="dashboard" className="data-[state=active]:bg-blue-600">
              <BarChart3 className="h-4 w-4 mr-2" />
              Dashboard
            </TabsTrigger>
            <TabsTrigger value="screener" className="data-[state=active]:bg-blue-600">
              <Filter className="h-4 w-4 mr-2" />
              Screener
            </TabsTrigger>
            <TabsTrigger value="analysis" className="data-[state=active]:bg-blue-600">
              <Activity className="h-4 w-4 mr-2" />
              Analysis
            </TabsTrigger>
            <TabsTrigger value="portfolio" className="data-[state=active]:bg-blue-600">
              <DollarSign className="h-4 w-4 mr-2" />
              Portfolio
            </TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            {/* Market Overview */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-slate-400">Active Signals</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-green-400">12</div>
                  <p className="text-xs text-slate-500">+3 from yesterday</p>
                </CardContent>
              </Card>
              
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-slate-400">Strong Buy</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-blue-400">3</div>
                  <p className="text-xs text-slate-500">A+ grade setups</p>
                </CardContent>
              </Card>
              
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-slate-400">Avg Ross Score</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-purple-400">84.2</div>
                  <p className="text-xs text-slate-500">Above 80 threshold</p>
                </CardContent>
              </Card>
              
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-slate-400">Portfolio Value</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-yellow-400">$100,000</div>
                  <p className="text-xs text-slate-500">+$2,450 today</p>
                </CardContent>
              </Card>
            </div>

            {/* Top Signals */}
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Star className="h-5 w-5 text-yellow-400" />
                  <span>Top Ross Cameron Signals</span>
                </CardTitle>
                <CardDescription>
                  Live signals ranked by Ross Cameron methodology
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {sampleStocks.slice(0, 3).map((stock, index) => (
                    <div 
                      key={stock.symbol}
                      className="flex items-center justify-between p-4 rounded-lg bg-slate-700/50 hover:bg-slate-700 transition-colors cursor-pointer"
                      onClick={() => setSelectedStock(stock)}
                    >
                      <div className="flex items-center space-x-4">
                        <div className="text-center">
                          <div className="text-lg font-bold">{index + 1}</div>
                        </div>
                        
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="font-bold text-lg">{stock.symbol}</span>
                            <Badge className={getGradeColor(stock.grade)} variant="outline">
                              {stock.grade}
                            </Badge>
                          </div>
                          <div className="text-sm text-slate-400">{stock.name}</div>
                        </div>
                      </div>
                      
                      <div className="text-right">
                        <div className="flex items-center space-x-2">
                          <span className="text-lg font-bold">${stock.price}</span>
                          <span className={`text-sm ${stock.change > 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {stock.change > 0 ? '+' : ''}{stock.change.toFixed(1)}%
                          </span>
                        </div>
                        <div className="text-sm text-slate-400">Vol: {stock.volume}</div>
                      </div>
                      
                      <div className="text-right">
                        <div className="text-lg font-bold text-blue-400">{stock.rossScore}/100</div>
                        <Badge className={getRecommendationColor(stock.recommendation)} variant="default">
                          {stock.recommendation}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Screener Tab */}
          <TabsContent value="screener" className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold">Ross Cameron Stock Screener</h2>
              <div className="flex items-center space-x-2">
                <Button variant="outline" size="sm" className="border-slate-600">
                  <Search className="h-4 w-4 mr-2" />
                  Search
                </Button>
                <Button variant="outline" size="sm" className="border-slate-600">
                  <Filter className="h-4 w-4 mr-2" />
                  Filters
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4">
              {sampleStocks.map((stock) => (
                <Card key={stock.symbol} className="bg-slate-800 border-slate-700 hover:border-blue-500 transition-colors">
                  <CardContent className="p-6">
                    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                      {/* Stock Info */}
                      <div className="space-y-2">
                        <div className="flex items-center space-x-2">
                          <span className="text-xl font-bold">{stock.symbol}</span>
                          <Badge className={getGradeColor(stock.grade)} variant="outline">
                            Ross {stock.grade}
                          </Badge>
                        </div>
                        <div className="text-sm text-slate-400">{stock.name}</div>
                        <div className="text-sm text-slate-500">{stock.sector}</div>
                        
                        <div className="flex items-center space-x-4 mt-4">
                          <div>
                            <div className="text-2xl font-bold">${stock.price}</div>
                            <div className={`text-sm ${stock.change > 0 ? 'text-green-400' : 'text-red-400'}`}>
                              {stock.change > 0 ? '+' : ''}{stock.change.toFixed(1)}%
                            </div>
                          </div>
                          <div>
                            <div className="text-sm text-slate-400">Volume</div>
                            <div className="font-semibold">{stock.volume}</div>
                            <div className="text-xs text-blue-400">{stock.relativeVolume}x avg</div>
                          </div>
                        </div>
                      </div>

                      {/* Ross Cameron Pillars */}
                      <div className="space-y-3">
                        <h4 className="font-semibold text-slate-300">Ross Cameron Pillars</h4>
                        <div className="space-y-2">
                          <div className="flex justify-between items-center">
                            <span className="text-sm">Volume</span>
                            <span className="text-sm font-semibold">{stock.pillars.volume}/100</span>
                          </div>
                          <Progress value={stock.pillars.volume} className="h-2" />
                          
                          <div className="flex justify-between items-center">
                            <span className="text-sm">Price Change</span>
                            <span className="text-sm font-semibold">{stock.pillars.priceChange}/100</span>
                          </div>
                          <Progress value={stock.pillars.priceChange} className="h-2" />
                          
                          <div className="flex justify-between items-center">
                            <span className="text-sm">Float</span>
                            <span className="text-sm font-semibold">{stock.pillars.float}/100</span>
                          </div>
                          <Progress value={stock.pillars.float} className="h-2" />
                        </div>
                      </div>

                      {/* Scores */}
                      <div className="space-y-3">
                        <h4 className="font-semibold text-slate-300">Scores & Risk</h4>
                        <div className="space-y-3">
                          <div className="text-center p-3 rounded-lg bg-slate-700">
                            <div className="text-2xl font-bold text-blue-400">{stock.rossScore}</div>
                            <div className="text-sm text-slate-400">Ross Score</div>
                          </div>
                          
                          <div className="text-center p-3 rounded-lg bg-slate-700">
                            <div className="text-xl font-bold text-purple-400">{stock.compositeScore}</div>
                            <div className="text-sm text-slate-400">Composite</div>
                          </div>
                          
                          <div className="flex justify-center">
                            <Badge className={getRiskColor(stock.risk)} variant="default">
                              {stock.risk} RISK
                            </Badge>
                          </div>
                        </div>
                      </div>

                      {/* Trading Setup */}
                      <div className="space-y-3">
                        <h4 className="font-semibold text-slate-300">Trading Setup</h4>
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span className="text-sm text-slate-400">Entry:</span>
                            <span className="font-semibold">${stock.entry}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-slate-400">Stop:</span>
                            <span className="font-semibold text-red-400">${stock.stopLoss}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-slate-400">Target:</span>
                            <span className="font-semibold text-green-400">${stock.takeProfit}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-slate-400">R/R:</span>
                            <span className="font-semibold">1:2.0</span>
                          </div>
                        </div>
                        
                        <Badge className={`${getRecommendationColor(stock.recommendation)} w-full justify-center`} variant="default">
                          {stock.recommendation}
                        </Badge>
                      </div>
                    </div>

                    {/* Alerts */}
                    {stock.alerts.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-slate-700">
                        <div className="flex flex-wrap gap-2">
                          {stock.alerts.map((alert, index) => (
                            <Badge key={index} variant="outline" className="text-yellow-400 border-yellow-400">
                              {alert}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* Analysis Tab */}
          <TabsContent value="analysis" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Price Chart */}
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <TrendingUp className="h-5 w-5 text-green-400" />
                    <span>{selectedStock.symbol} Price Action</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis dataKey="time" stroke="#9CA3AF" />
                      <YAxis stroke="#9CA3AF" />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: '#1F2937', 
                          border: '1px solid #374151',
                          borderRadius: '8px'
                        }} 
                      />
                      <Line 
                        type="monotone" 
                        dataKey="price" 
                        stroke="#3B82F6" 
                        strokeWidth={3}
                        dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Volume Chart */}
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Volume2 className="h-5 w-5 text-purple-400" />
                    <span>Volume Analysis</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis dataKey="time" stroke="#9CA3AF" />
                      <YAxis stroke="#9CA3AF" />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: '#1F2937', 
                          border: '1px solid #374151',
                          borderRadius: '8px'
                        }} 
                      />
                      <Bar dataKey="volume" fill="#8B5CF6" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>

            {/* Detailed Analysis */}
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Target className="h-5 w-5 text-blue-400" />
                  <span>{selectedStock.symbol} Detailed Analysis</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="space-y-4">
                    <h4 className="font-semibold text-slate-300">Fundamental Analysis</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Float:</span>
                        <span className="font-semibold">{selectedStock.float}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Sector:</span>
                        <span className="font-semibold">{selectedStock.sector}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Price Range:</span>
                        <span className="font-semibold text-green-400">Optimal</span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h4 className="font-semibold text-slate-300">Technical Analysis</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-slate-400">RSI:</span>
                        <span className="font-semibold text-yellow-400">83.5</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">MACD:</span>
                        <span className="font-semibold text-green-400">Bullish</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">EMA Alignment:</span>
                        <span className="font-semibold text-green-400">Bullish</span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h4 className="font-semibold text-slate-300">News & Sentiment</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Sentiment:</span>
                        <span className="font-semibold text-green-400">Very Bullish</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Catalysts:</span>
                        <span className="font-semibold text-blue-400">4 Detected</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Timing:</span>
                        <span className="font-semibold text-green-400">Optimal</span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Portfolio Tab */}
          <TabsContent value="portfolio" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Portfolio Overview */}
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle>Portfolio Overview</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-green-400">$100,000</div>
                      <div className="text-sm text-slate-400">Total Value</div>
                    </div>
                    
                    <ResponsiveContainer width="100%" height={200}>
                      <PieChart>
                        <Pie
                          data={portfolioData}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={80}
                          paddingAngle={5}
                          dataKey="value"
                        >
                          {portfolioData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip 
                          formatter={(value) => [`$${value.toLocaleString()}`, 'Value']}
                          contentStyle={{ 
                            backgroundColor: '#1F2937', 
                            border: '1px solid #374151',
                            borderRadius: '8px'
                          }} 
                        />
                      </PieChart>
                    </ResponsiveContainer>
                    
                    <div className="space-y-2">
                      {portfolioData.map((item, index) => (
                        <div key={index} className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <div 
                              className="w-3 h-3 rounded-full" 
                              style={{ backgroundColor: item.color }}
                            />
                            <span className="text-sm">{item.name}</span>
                          </div>
                          <span className="font-semibold">${item.value.toLocaleString()}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Risk Management */}
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <AlertTriangle className="h-5 w-5 text-yellow-400" />
                    <span>Risk Management</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between mb-2">
                        <span className="text-sm text-slate-400">Portfolio Risk</span>
                        <span className="text-sm font-semibold">4.0%</span>
                      </div>
                      <Progress value={40} className="h-2" />
                      <div className="text-xs text-slate-500 mt-1">Max: 6.0%</div>
                    </div>
                    
                    <div>
                      <div className="flex justify-between mb-2">
                        <span className="text-sm text-slate-400">Position Risk</span>
                        <span className="text-sm font-semibold">2.0%</span>
                      </div>
                      <Progress value={100} className="h-2" />
                      <div className="text-xs text-slate-500 mt-1">Max: 2.0%</div>
                    </div>
                    
                    <div className="pt-4 border-t border-slate-700">
                      <div className="text-sm text-slate-400 mb-2">Risk Metrics</div>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-xs text-slate-500">Max Drawdown:</span>
                          <span className="text-xs font-semibold">-3.2%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-xs text-slate-500">Win Rate:</span>
                          <span className="text-xs font-semibold text-green-400">68%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-xs text-slate-500">Avg R/R:</span>
                          <span className="text-xs font-semibold text-blue-400">1:2.1</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Recent Alerts */}
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Bell className="h-5 w-5 text-blue-400" />
                    <span>Recent Alerts</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <Alert className="border-green-500/20 bg-green-500/10">
                      <CheckCircle className="h-4 w-4 text-green-400" />
                      <AlertTitle className="text-green-400">Strong Buy Signal</AlertTitle>
                      <AlertDescription className="text-slate-300">
                        GITS triggered A+ Ross Cameron setup
                      </AlertDescription>
                    </Alert>
                    
                    <Alert className="border-blue-500/20 bg-blue-500/10">
                      <Activity className="h-4 w-4 text-blue-400" />
                      <AlertTitle className="text-blue-400">Volume Breakout</AlertTitle>
                      <AlertDescription className="text-slate-300">
                        NVAX showing 4.2x average volume
                      </AlertDescription>
                    </Alert>
                    
                    <Alert className="border-yellow-500/20 bg-yellow-500/10">
                      <Clock className="h-4 w-4 text-yellow-400" />
                      <AlertTitle className="text-yellow-400">Market Open</AlertTitle>
                      <AlertDescription className="text-slate-300">
                        Pre-market scan completed: 12 signals
                      </AlertDescription>
                    </Alert>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

export default App

