from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta
import json
import random
import uuid

from .models import (
    Trader, Market, TradingSignal, TechnicalIndicator, 
    Trade, AnalysisReport, EducationalContent
)

# =============================================================================
# AI MARKET DEFINITIONS – used by Markets, Analysis, and Signals
# =============================================================================
AI_MARKETS = {
    'forex': [
        {'symbol': 'EURUSD', 'name': 'Euro/US Dollar', 'market_type': 'forex', 'basePrice': 1.0925, 'volatility': 0.12},
        {'symbol': 'GBPUSD', 'name': 'British Pound/US Dollar', 'market_type': 'forex', 'basePrice': 1.2650, 'volatility': 0.15},
        {'symbol': 'USDJPY', 'name': 'US Dollar/Japanese Yen', 'market_type': 'forex', 'basePrice': 149.75, 'volatility': 0.35},
        {'symbol': 'AUDUSD', 'name': 'Australian Dollar/US Dollar', 'market_type': 'forex', 'basePrice': 0.6575, 'volatility': 0.13},
        {'symbol': 'USDCAD', 'name': 'US Dollar/Canadian Dollar', 'market_type': 'forex', 'basePrice': 1.3450, 'volatility': 0.11},
        {'symbol': 'USDCHF', 'name': 'US Dollar/Swiss Franc', 'market_type': 'forex', 'basePrice': 0.8985, 'volatility': 0.10},
        {'symbol': 'NZDUSD', 'name': 'New Zealand Dollar/US Dollar', 'market_type': 'forex', 'basePrice': 0.6150, 'volatility': 0.14},
    ],
    'crypto': [
        {'symbol': 'BTCUSD', 'name': 'Bitcoin/US Dollar', 'market_type': 'crypto', 'basePrice': 48250, 'volatility': 2.1},
        {'symbol': 'ETHUSD', 'name': 'Ethereum/US Dollar', 'market_type': 'crypto', 'basePrice': 3200, 'volatility': 2.5},
        {'symbol': 'BNBUSD', 'name': 'Binance Coin/US Dollar', 'market_type': 'crypto', 'basePrice': 380, 'volatility': 1.9},
        {'symbol': 'XRPUSD', 'name': 'Ripple/US Dollar', 'market_type': 'crypto', 'basePrice': 0.58, 'volatility': 1.7},
        {'symbol': 'ADAUSD', 'name': 'Cardano/US Dollar', 'market_type': 'crypto', 'basePrice': 0.45, 'volatility': 1.8},
        {'symbol': 'SOLUSD', 'name': 'Solana/US Dollar', 'market_type': 'crypto', 'basePrice': 95, 'volatility': 2.2},
        {'symbol': 'DOGEUSD', 'name': 'Dogecoin/US Dollar', 'market_type': 'crypto', 'basePrice': 0.12, 'volatility': 2.4},
    ],
    'stocks': [
        {'symbol': 'AAPL', 'name': 'Apple Inc.', 'market_type': 'stocks', 'basePrice': 175.80, 'volatility': 0.65},
        {'symbol': 'MSFT', 'name': 'Microsoft Corporation', 'market_type': 'stocks', 'basePrice': 328.50, 'volatility': 0.55},
        {'symbol': 'GOOGL', 'name': 'Alphabet Inc.', 'market_type': 'stocks', 'basePrice': 142.30, 'volatility': 0.60},
        {'symbol': 'AMZN', 'name': 'Amazon.com Inc.', 'market_type': 'stocks', 'basePrice': 178.20, 'volatility': 0.70},
        {'symbol': 'TSLA', 'name': 'Tesla Inc.', 'market_type': 'stocks', 'basePrice': 172.50, 'volatility': 1.20},
        {'symbol': 'META', 'name': 'Meta Platforms Inc.', 'market_type': 'stocks', 'basePrice': 485.90, 'volatility': 0.80},
        {'symbol': 'NVDA', 'name': 'NVIDIA Corporation', 'market_type': 'stocks', 'basePrice': 895.00, 'volatility': 1.10},
    ],
    'indices': [
        {'symbol': 'SPX', 'name': 'S&P 500 Index', 'market_type': 'indices', 'basePrice': 4950, 'volatility': 0.35},
        {'symbol': 'IXIC', 'name': 'Nasdaq Composite', 'market_type': 'indices', 'basePrice': 15680, 'volatility': 0.45},
        {'symbol': 'DJI', 'name': 'Dow Jones Industrial Average', 'market_type': 'indices', 'basePrice': 38750, 'volatility': 0.30},
        {'symbol': 'FTSE', 'name': 'FTSE 100', 'market_type': 'indices', 'basePrice': 7650, 'volatility': 0.40},
        {'symbol': 'DAX', 'name': 'DAX 40', 'market_type': 'indices', 'basePrice': 17850, 'volatility': 0.42},
        {'symbol': 'NIKKEI', 'name': 'Nikkei 225', 'market_type': 'indices', 'basePrice': 38200, 'volatility': 0.55},
    ],
    'commodities': [
        {'symbol': 'XAUUSD', 'name': 'Gold/US Dollar', 'market_type': 'commodities', 'basePrice': 2030, 'volatility': 0.50},
        {'symbol': 'XAGUSD', 'name': 'Silver/US Dollar', 'market_type': 'commodities', 'basePrice': 24.50, 'volatility': 0.80},
        {'symbol': 'USOIL', 'name': 'US Crude Oil', 'market_type': 'commodities', 'basePrice': 78.50, 'volatility': 0.90},
        {'symbol': 'UKOIL', 'name': 'Brent Crude Oil', 'market_type': 'commodities', 'basePrice': 82.30, 'volatility': 0.85},
        {'symbol': 'NGAS', 'name': 'Natural Gas', 'market_type': 'commodities', 'basePrice': 2.15, 'volatility': 1.10},
    ]
}

def generate_ai_signals():
    """Generate realistic AI trading signals for all markets."""
    signals = []
    signal_types = ['buy', 'sell', 'neutral']
    strengths = ['weak', 'moderate', 'strong', 'very_strong']
    
    for category, markets in AI_MARKETS.items():
        for market in markets:
            # Randomise but keep plausible
            signal_type = random.choices(
                signal_types, 
                weights=[0.4, 0.4, 0.2]  # 40% buy, 40% sell, 20% neutral
            )[0]
            
            strength = random.choices(
                strengths,
                weights=[0.2, 0.3, 0.3, 0.2]
            )[0]
            
            # Base price with slight variation
            price = market['basePrice'] * (1 + random.uniform(-0.01, 0.01))
            
            # Determine decimals based on price
            decimals = 2 if price < 10 else 0 if price > 1000 else 2
            if market['symbol'] in ['BTCUSD', 'ETHUSD']:
                decimals = 0
            elif market['symbol'] in ['XRPUSD', 'ADAUSD', 'DOGEUSD']:
                decimals = 4
            elif market['symbol'] in ['EURUSD', 'GBPUSD', 'AUDUSD', 'USDCAD', 'USDCHF', 'NZDUSD']:
                decimals = 4
            elif market['symbol'] in ['USDJPY']:
                decimals = 2
                
            # Entry, target, stop
            if signal_type == 'buy':
                entry = round(price * (1 - random.uniform(0.001, 0.005)), decimals)
                target = round(price * (1 + random.uniform(0.01, 0.03)), decimals)
                stop = round(price * (1 - random.uniform(0.005, 0.015)), decimals)
            elif signal_type == 'sell':
                entry = round(price * (1 + random.uniform(0.001, 0.005)), decimals)
                target = round(price * (1 - random.uniform(0.01, 0.03)), decimals)
                stop = round(price * (1 + random.uniform(0.005, 0.015)), decimals)
            else:  # neutral
                entry = round(price, decimals)
                target = round(price * (1 + random.uniform(0.005, 0.015)), decimals)
                stop = round(price * (1 - random.uniform(0.005, 0.015)), decimals)
            
            # Confidence score
            if strength == 'very_strong':
                confidence = random.randint(80, 95)
            elif strength == 'strong':
                confidence = random.randint(70, 85)
            elif strength == 'moderate':
                confidence = random.randint(55, 70)
            else:
                confidence = random.randint(40, 55)
            
            # Risk/Reward ratio
            if signal_type == 'buy':
                risk = abs(entry - stop)
                reward = abs(target - entry)
            elif signal_type == 'sell':
                risk = abs(entry - stop)
                reward = abs(entry - target)
            else:
                risk = abs(entry - stop)
                reward = abs(target - entry)
            
            rr_ratio = round(reward / risk, 2) if risk > 0 else 1.0
            
            # Expiry (today + random hours)
            expires_at = timezone.now() + timedelta(hours=random.randint(6, 48))
            
            # Generate random 24h change
            change_24h = round(random.uniform(-2.0, 2.0), 2)
            
            # Create a signal dictionary (simulates a TradingSignal instance)
            signal = {
                'signal_id': str(uuid.uuid4()),
                'market': {
                    'symbol': market['symbol'],
                    'name': market['name'],
                    'market_type': market['market_type'],
                    'get_market_type_display': lambda: market['market_type'].title(),
                    'change_24h': change_24h,
                },
                'signal_type': signal_type,
                'get_signal_type_display': lambda: signal_type.upper(),
                'strength': strength,
                'get_strength_display': lambda: strength.replace('_', ' ').title(),
                'entry_price': entry,
                'target_price': target,
                'stop_loss': stop,
                'timeframe': random.choice(['1h', '4h', '1d', '1w']),
                'analysis': generate_analysis_text(signal_type, strength, market['symbol']),
                'is_ai_generated': True,
                'confidence_score': confidence,
                'expires_at': expires_at,
                'rr_ratio': rr_ratio,
            }
            signals.append(signal)
    
    return signals

def generate_analysis_text(signal_type, strength, symbol):
    """Generate realistic analysis text for a signal."""
    templates = {
        'buy': [
            f"Bullish momentum building on {symbol}. RSI shows room for upside.",
            f"Breakout above key resistance. Target within reach.",
            f"Positive divergence on MACD. Expect continuation.",
            f"Strong institutional buying volume detected.",
            f"{symbol} is forming a bullish flag pattern. Look for entry.",
            f"Support held firmly. Next resistance at +{random.randint(1,3)}%.",
        ],
        'sell': [
            f"Bearish divergence on RSI. Rejection at resistance.",
            f"Break below support. Next target at -{random.randint(1,5)}%.",
            f"Rising volatility with increasing selling pressure.",
            f"Overbought conditions on multiple timeframes.",
            f"{symbol} failed to break resistance. Downside momentum increasing.",
            f"Lower highs and lower lows – downtrend intact.",
        ],
        'neutral': [
            f"Range‑bound market. Wait for breakout.",
            f"Low volatility, no clear directional bias.",
            f"Consolidation phase. Monitor key levels.",
            f"Mixed signals from indicators. Hold for now.",
            f"{symbol} is trading near fair value. No edge at current levels.",
            f"Volume declining – indecision in the market.",
        ]
    }
    base = random.choice(templates[signal_type])
    if strength == 'very_strong':
        base += " High conviction."
    elif strength == 'weak':
        base += " Low confidence, use tight stops."
    return base

# ---------- PUBLIC HOME PAGE ----------
def home(request):
    """Home page – public. If authenticated, redirect to dashboard."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    featured_markets = Market.objects.all()[:8]
    latest_signals = TradingSignal.objects.filter(
        expires_at__gt=timezone.now()
    ).order_by('-created_at')[:5]
    educational_content = EducationalContent.objects.filter(
        published=True
    ).order_by('-created_at')[:4]
    total_traders = Trader.objects.count()
    total_signals = TradingSignal.objects.filter(
        expires_at__gt=timezone.now()
    ).count()
    total_markets = Market.objects.count()
    context = {
        'featured_markets': featured_markets,
        'latest_signals': latest_signals,
        'educational_content': educational_content,
        'total_traders': total_traders,
        'total_signals': total_signals,
        'total_markets': total_markets,
    }
    return render(request, 'home.html', context)

# ---------- PROTECTED PAGES (require login) ----------
@login_required
def dashboard(request):
    trader = request.user
    
    # Get user's open trades
    open_trades = Trade.objects.filter(trader=trader, status='open').order_by('-opened_at')
    
    # Get user's recent closed trades (last 5)
    closed_trades = Trade.objects.filter(trader=trader, status='closed').order_by('-closed_at')[:5]
    
    # Get recent signals for user's favorite markets (or general)
    favorite_markets = trader.watchlist.all() if hasattr(trader, 'watchlist') else Market.objects.none()
    recent_signals = TradingSignal.objects.filter(
        market__in=favorite_markets,
        expires_at__gt=timezone.now()
    ).order_by('-created_at')[:5] if favorite_markets else TradingSignal.objects.filter(
        expires_at__gt=timezone.now()
    ).order_by('-created_at')[:5]
    
    # Calculate dashboard statistics
    total_trades = trader.total_trades
    successful_trades = trader.successful_trades
    win_rate = trader.win_rate
    
    # Total profit/loss from closed trades
    total_profit = Trade.objects.filter(
        trader=trader,
        status='closed'
    ).aggregate(total=Sum('profit_loss'))['total'] or 0
    
    # Get market data for sidebar
    markets = Market.objects.all()[:10]
    
    # Prepare performance chart data (last 6 months cumulative profit)
    today = timezone.now().date()
    chart_labels = []
    chart_data = []
    starting_balance = 10000  # initial account balance (could be taken from trader initial balance)
    for i in range(5, -1, -1):
        month_start = today - timedelta(days=30*i+15)  # approximate mid-month
        month_label = month_start.strftime('%b %Y')
        chart_labels.append(month_label)
        # Sum profit of trades closed up to this month
        month_end = today - timedelta(days=30*i)
        month_profit = Trade.objects.filter(
            trader=trader,
            status='closed',
            closed_at__lte=month_end
        ).aggregate(total=Sum('profit_loss'))['total'] or 0
        balance = starting_balance + month_profit
        chart_data.append(balance)
    
    context = {
        'trader': trader,
        'open_trades': open_trades,
        'closed_trades': closed_trades,
        'recent_signals': recent_signals,
        'total_trades': total_trades,
        'successful_trades': successful_trades,
        'win_rate': win_rate,
        'total_profit': total_profit,
        'markets': markets,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
    }
    return render(request, 'dashboard.html', context)

@login_required
def markets(request):
    market_type = request.GET.get('type', '')
    search_query = request.GET.get('q', '')
    markets_qs = Market.objects.all()
    if market_type:
        markets_qs = markets_qs.filter(market_type=market_type)
    if search_query:
        markets_qs = markets_qs.filter(
            Q(symbol__icontains=search_query) | Q(name__icontains=search_query)
        )
    market_types = Market.objects.values_list('market_type', flat=True).distinct()
    markets_by_type = {}
    for m_type in market_types:
        markets_by_type[m_type] = markets_qs.filter(market_type=m_type)
    context = {
        'markets_by_type': markets_by_type,
        'market_types': market_types,
        'selected_type': market_type,
        'search_query': search_query,
        'featured_markets': Market.objects.all()[:5],
    }
    return render(request, 'markets.html', context)

@login_required
def market_detail(request, symbol):
    market = get_object_or_404(Market, symbol=symbol)
    signals = TradingSignal.objects.filter(
        market=market,
        expires_at__gt=timezone.now()
    ).order_by('-created_at')
    indicators = TechnicalIndicator.objects.filter(market=market)
    reports = AnalysisReport.objects.filter(market=market)[:5]
    price_history = []
    current_price = float(market.current_price)
    for i in range(30, 0, -1):
        price_history.append({
            'date': f'Day {i}',
            'price': round(current_price * (0.95 + (i % 10) * 0.01), 4)
        })
    context = {
        'market': market,
        'signals': signals,
        'indicators': indicators,
        'reports': reports,
        'price_history': json.dumps(price_history),
    }
    return render(request, 'market_detail.html', context)

@login_required
def analysis(request):
    selected_market_symbol = request.GET.get('market', '')
    timeframe = request.GET.get('timeframe', '1h')
    markets_qs = Market.objects.all()
    selected_market_obj = None
    if selected_market_symbol:
        try:
            selected_market_obj = Market.objects.get(symbol=selected_market_symbol)
        except Market.DoesNotExist:
            selected_market_obj = None
    analysis_tools = [
        {'name': 'Technical Analysis', 'icon': 'fas fa-chart-line', 'description': 'Chart patterns and indicators'},
        {'name': 'Fundamental Analysis', 'icon': 'fas fa-balance-scale', 'description': 'Economic indicators'},
        {'name': 'Sentiment Analysis', 'icon': 'fas fa-brain', 'description': 'Market sentiment tools'},
        {'name': 'Risk Calculator', 'icon': 'fas fa-calculator', 'description': 'Position sizing calculator'},
        {'name': 'Backtesting', 'icon': 'fas fa-history', 'description': 'Test trading strategies'},
        {'name': 'AI Predictions', 'icon': 'fas fa-robot', 'description': 'AI-powered market predictions'},
    ]
    context = {
        'markets': markets_qs,
        'selected_market': selected_market_obj,
        'selected_market_symbol': selected_market_symbol,
        'timeframe': timeframe,
        'analysis_tools': analysis_tools,
    }
    return render(request, 'analysis.html', context)

@login_required
def signals(request):
    signal_type = request.GET.get('type', '')
    market_type = request.GET.get('market_type', '')
    strength = request.GET.get('strength', '')
    all_signals = generate_ai_signals()
    filtered_signals = all_signals
    if signal_type:
        filtered_signals = [s for s in filtered_signals if s['signal_type'] == signal_type]
    if market_type:
        filtered_signals = [s for s in filtered_signals if s['market']['market_type'] == market_type]
    if strength:
        filtered_signals = [s for s in filtered_signals if s['strength'] == strength]
    market_types = list(AI_MARKETS.keys())
    strength_choices = [
        ('weak', 'Weak'),
        ('moderate', 'Moderate'),
        ('strong', 'Strong'),
        ('very_strong', 'Very Strong'),
    ]
    context = {
        'signals': filtered_signals,
        'market_types': market_types,
        'strength_choices': strength_choices,
        'selected_filters': {
            'signal_type': signal_type,
            'market_type': market_type,
            'strength': strength,
        }
    }
    return render(request, 'signals.html', context)

@login_required
def education(request):
    content_type = request.GET.get('type', '')
    difficulty = request.GET.get('difficulty', '')
    content_qs = EducationalContent.objects.filter(published=True)
    if content_type:
        content_qs = content_qs.filter(content_type=content_type)
    if difficulty:
        content_qs = content_qs.filter(difficulty_level=difficulty)
    content_types = EducationalContent.objects.values_list('content_type', flat=True).distinct()
    context = {
        'content': content_qs,
        'content_types': content_types,
        'difficulty_levels': [
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced')
        ]
    }
    return render(request, 'education.html', context)

@login_required
def education_detail(request, content_id):
    content = get_object_or_404(EducationalContent, content_id=content_id)
    content.views += 1
    content.save(update_fields=['views'])
    related_content = EducationalContent.objects.filter(
        difficulty_level=content.difficulty_level,
        published=True
    ).exclude(content_id=content_id)[:4]
    context = {
        'content': content,
        'related_content': related_content,
    }
    return render(request, 'education_detail.html', context)

@login_required
def tools(request):
    context = {
        'tools': [
            {'name': 'Position Size Calculator', 'url': '#position-calculator'},
            {'name': 'Risk/Reward Calculator', 'url': '#risk-reward'},
            {'name': 'Pivot Point Calculator', 'url': '#pivot-points'},
            {'name': 'Fibonacci Calculator', 'url': '#fibonacci'},
            {'name': 'Margin Calculator', 'url': '#margin'},
            {'name': 'Economic Calendar', 'url': '#calendar'},
        ]
    }
    return render(request, 'tools.html', context)

@login_required
def profile(request):
    """User profile page – now using registration folder"""
    return render(request, 'registration/profile.html')

# ---------- API Views for AJAX requests ----------
@require_GET
@login_required
def get_market_data(request, symbol):
    """Get market data for charts – returns dynamic labels based on timeframe."""
    timeframe = request.GET.get('timeframe', '1d')
    
    try:
        market = Market.objects.get(symbol=symbol)
        current_price = float(market.current_price)
        change_24h = float(market.change_24h)
    except Market.DoesNotExist:
        # Generate plausible dummy data based on symbol
        if symbol == 'EURUSD':
            current_price = 1.0925
            change_24h = 0.32
        elif symbol == 'GBPUSD':
            current_price = 1.2650
            change_24h = 0.18
        elif symbol == 'USDJPY':
            current_price = 149.75
            change_24h = -0.25
        elif symbol == 'BTCUSD':
            current_price = 48250
            change_24h = -2.15
        elif symbol == 'AAPL':
            current_price = 175.80
            change_24h = 0.75
        elif symbol == 'SPX':
            current_price = 4950
            change_24h = 0.00
        elif symbol == 'XAUUSD':
            current_price = 2030
            change_24h = -0.45
        else:
            current_price = round(random.uniform(50, 500), 2)
            change_24h = round(random.uniform(-3.0, 3.0), 2)
    
    historical_data = []
    
    if timeframe in ['1m', '5m', '15m']:
        for i in range(30, 0, -1):
            variation = (random.random() - 0.5) * 0.02
            historical_data.append({
                'time': str(i),
                'open': round(current_price * (0.99 + variation), 2),
                'high': round(current_price * (1.01 + variation), 2),
                'low': round(current_price * (0.98 + variation), 2),
                'close': round(current_price * (1.00 + variation), 2),
            })
    elif timeframe == '1h':
        for i in range(24):
            variation = (random.random() - 0.5) * 0.02
            historical_data.append({
                'time': f'{i}:00',
                'open': round(current_price * (0.99 + variation), 2),
                'high': round(current_price * (1.01 + variation), 2),
                'low': round(current_price * (0.98 + variation), 2),
                'close': round(current_price * (1.00 + variation), 2),
            })
    elif timeframe == '4h':
        for i in range(0, 24, 4):
            variation = (random.random() - 0.5) * 0.02
            historical_data.append({
                'time': f'{i}:00',
                'open': round(current_price * (0.99 + variation), 2),
                'high': round(current_price * (1.01 + variation), 2),
                'low': round(current_price * (0.98 + variation), 2),
                'close': round(current_price * (1.00 + variation), 2),
            })
    elif timeframe in ['1d', '1w']:
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for i in range(7):
            variation = (random.random() - 0.5) * 0.02
            historical_data.append({
                'time': days[i],
                'open': round(current_price * (0.99 + variation), 2),
                'high': round(current_price * (1.01 + variation), 2),
                'low': round(current_price * (0.98 + variation), 2),
                'close': round(current_price * (1.00 + variation), 2),
            })
    elif timeframe == '1M':
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        for i in range(12):
            variation = (random.random() - 0.5) * 0.02
            historical_data.append({
                'time': months[i],
                'open': round(current_price * (0.99 + variation), 2),
                'high': round(current_price * (1.01 + variation), 2),
                'low': round(current_price * (0.98 + variation), 2),
                'close': round(current_price * (1.00 + variation), 2),
            })
    else:
        for i in range(30, 0, -1):
            variation = (random.random() - 0.5) * 0.02
            historical_data.append({
                'time': f'Day {i}',
                'open': round(current_price * (0.99 + variation), 2),
                'high': round(current_price * (1.01 + variation), 2),
                'low': round(current_price * (0.98 + variation), 2),
                'close': round(current_price * (1.00 + variation), 2),
            })
    
    data = {
        'symbol': symbol,
        'current_price': current_price,
        'change_24h': change_24h,
        'historical_data': historical_data,
    }
    return JsonResponse(data)

@require_POST
@login_required
def create_trade(request):
    try:
        data = json.loads(request.body)
        market = get_object_or_404(Market, symbol=data.get('symbol'))
        trade = Trade.objects.create(
            trader=request.user,
            market=market,
            trade_type=data.get('trade_type'),
            entry_price=data.get('entry_price'),
            volume=data.get('volume'),
            status='open',
            notes=data.get('notes', '')
        )
        request.user.total_trades += 1
        request.user.save()
        return JsonResponse({
            'success': True,
            'trade_id': str(trade.trade_id),
            'message': 'Trade created successfully'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_POST
@login_required
def close_trade(request, trade_id):
    try:
        trade = get_object_or_404(Trade, trade_id=trade_id, trader=request.user)
        if trade.status != 'open':
            return JsonResponse({'success': False, 'error': 'Trade is not open'}, status=400)
        exit_price = float(request.POST.get('exit_price'))
        if trade.trade_type == 'buy':
            profit_loss = (exit_price - float(trade.entry_price)) * float(trade.volume)
        else:
            profit_loss = (float(trade.entry_price) - exit_price) * float(trade.volume)
        profit_loss_percentage = (profit_loss / (float(trade.entry_price) * float(trade.volume))) * 100
        trade.exit_price = exit_price
        trade.profit_loss = profit_loss
        trade.profit_loss_percentage = profit_loss_percentage
        trade.status = 'closed'
        trade.closed_at = timezone.now()
        trade.save()
        if profit_loss > 0:
            request.user.successful_trades += 1
            request.user.balance += profit_loss
        else:
            request.user.balance += profit_loss
        request.user.update_win_rate()
        return JsonResponse({'success': True, 'message': 'Trade closed successfully', 'profit_loss': profit_loss})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# ---------- NEW: Deposit & Withdraw ----------
@login_required
@require_POST
def deposit(request):
    """Add funds to user's balance."""
    try:
        amount = float(request.POST.get('amount', 0))
        if amount <= 0:
            return JsonResponse({'success': False, 'error': 'Amount must be positive'}, status=400)
        
        user = request.user
        user.balance += amount
        user.save()
        
        return JsonResponse({
            'success': True,
            'new_balance': float(user.balance),
            'message': f'Successfully deposited ${amount:.2f}'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def withdraw(request):
    """Withdraw funds from user's balance."""
    try:
        amount = float(request.POST.get('amount', 0))
        if amount <= 0:
            return JsonResponse({'success': False, 'error': 'Amount must be positive'}, status=400)
        
        user = request.user
        if user.balance < amount:
            return JsonResponse({'success': False, 'error': 'Insufficient funds'}, status=400)
        
        user.balance -= amount
        user.save()
        
        return JsonResponse({
            'success': True,
            'new_balance': float(user.balance),
            'message': f'Successfully withdrew ${amount:.2f}'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# ---------- NEW: Update user experience level ----------
@require_POST
@login_required
def update_experience(request):
    """AJAX endpoint to save user's experience level from settings modal."""
    try:
        data = json.loads(request.body)
        experience = data.get('experience_level')
        # Validate against allowed choices
        valid_choices = [choice[0] for choice in Trader._meta.get_field('experience_level').choices]
        if experience in valid_choices:
            request.user.experience_level = experience
            request.user.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid experience level'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)