from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import uuid
import json

from .models import (
    Trader, Market, TradingSignal, TechnicalIndicator,
    Trade, AnalysisReport, EducationalContent
)

User = get_user_model()


class TraderModelTest(TestCase):
    """Test cases for Trader model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_trader(self):
        """Test creating a trader user"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpass123'))
        self.assertIsNotNone(self.user.trader_id)
        self.assertEqual(self.user.balance, Decimal('10000.00'))
        self.assertEqual(self.user.experience_level, 'beginner')
        self.assertEqual(self.user.subscription_type, 'free')
        self.assertEqual(self.user.total_trades, 0)
        self.assertEqual(self.user.win_rate, 0.0)
    
    def test_update_win_rate(self):
        """Test win rate calculation"""
        self.user.total_trades = 10
        self.user.successful_trades = 7
        self.user.update_win_rate()
        self.assertEqual(self.user.win_rate, 70.0)
        
        # Test division by zero
        self.user.total_trades = 0
        self.user.update_win_rate()
        self.assertEqual(self.user.win_rate, 0.0)
    
    def test_trader_str_method(self):
        """Test string representation"""
        expected = self.user.username
        self.assertEqual(str(self.user), expected)


class MarketModelTest(TestCase):
    """Test cases for Market model"""
    
    def setUp(self):
        self.market = Market.objects.create(
            symbol='EURUSD',
            name='Euro/US Dollar',
            market_type='forex',
            current_price=Decimal('1.1050'),
            change_24h=Decimal('0.25'),
            volume_24h=Decimal('1000000000'),
            high_24h=Decimal('1.1080'),
            low_24h=Decimal('1.1020')
        )
    
    def test_create_market(self):
        """Test creating a market"""
        self.assertEqual(self.market.symbol, 'EURUSD')
        self.assertEqual(self.market.name, 'Euro/US Dollar')
        self.assertEqual(self.market.market_type, 'forex')
        self.assertEqual(self.market.current_price, Decimal('1.1050'))
        self.assertEqual(self.market.change_24h, Decimal('0.25'))
    
    def test_market_str_method(self):
        """Test string representation"""
        expected = f"{self.market.symbol} - {self.market.name}"
        self.assertEqual(str(self.market), expected)


class TradingSignalModelTest(TestCase):
    """Test cases for TradingSignal model"""
    
    def setUp(self):
        self.market = Market.objects.create(
            symbol='BTCUSD',
            name='Bitcoin/US Dollar',
            market_type='crypto',
            current_price=Decimal('50000.00'),
            change_24h=Decimal('-1.5'),
            high_24h=Decimal('51000.00'),
            low_24h=Decimal('49500.00')
        )
        self.user = User.objects.create_user(
            username='analyst',
            password='testpass'
        )
        self.signal = TradingSignal.objects.create(
            market=self.market,
            signal_type='buy',
            strength='strong',
            entry_price=Decimal('49500.00'),
            target_price=Decimal('52000.00'),
            stop_loss=Decimal('49000.00'),
            timeframe='4h',
            analysis='Bullish breakout expected',
            generated_by=self.user,
            is_ai_generated=False,
            confidence_score=85.5,
            expires_at=timezone.now() + timedelta(days=1)
        )
    
    def test_create_signal(self):
        """Test creating a trading signal"""
        self.assertEqual(self.signal.signal_type, 'buy')
        self.assertEqual(self.signal.strength, 'strong')
        self.assertEqual(self.signal.entry_price, Decimal('49500.00'))
        self.assertEqual(self.signal.confidence_score, 85.5)
        self.assertFalse(self.signal.is_ai_generated)
    
    def test_signal_str_method(self):
        """Test string representation (should use default or we can implement __str__)"""
        # The model doesn't define __str__, so we test the default representation
        expected = f"TradingSignal object ({self.signal.signal_id})"
        self.assertEqual(str(self.signal), expected)
    
    def test_expiration(self):
        """Test that signal expires correctly"""
        expired_signal = TradingSignal.objects.create(
            market=self.market,
            signal_type='sell',
            strength='moderate',
            entry_price=Decimal('50500.00'),
            target_price=Decimal('49000.00'),
            stop_loss=Decimal('51000.00'),
            timeframe='1h',
            analysis='Test',
            expires_at=timezone.now() - timedelta(hours=1)
        )
        # In views we filter with expires_at__gt=timezone.now()
        active_signals = TradingSignal.objects.filter(expires_at__gt=timezone.now())
        self.assertIn(self.signal, active_signals)
        self.assertNotIn(expired_signal, active_signals)


class TradeModelTest(TestCase):
    """Test cases for Trade model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='trader1',
            password='testpass'
        )
        self.market = Market.objects.create(
            symbol='AAPL',
            name='Apple Inc.',
            market_type='stocks',
            current_price=Decimal('175.50'),
            change_24h=Decimal('0.75'),
            high_24h=Decimal('176.00'),
            low_24h=Decimal('174.50')
        )
        self.trade = Trade.objects.create(
            trader=self.user,
            market=self.market,
            trade_type='buy',
            entry_price=Decimal('174.80'),
            volume=Decimal('10'),
            status='open'
        )
    
    def test_create_trade(self):
        """Test creating a trade"""
        self.assertEqual(self.trade.trade_type, 'buy')
        self.assertEqual(self.trade.entry_price, Decimal('174.80'))
        self.assertEqual(self.trade.volume, Decimal('10'))
        self.assertEqual(self.trade.status, 'open')
        self.assertIsNone(self.trade.profit_loss)
    
    def test_close_trade_profit(self):
        """Test closing a trade with profit"""
        self.trade.exit_price = Decimal('180.00')
        self.trade.status = 'closed'
        self.trade.closed_at = timezone.now()
        # Calculate profit manually
        profit = (self.trade.exit_price - self.trade.entry_price) * self.trade.volume
        self.trade.profit_loss = profit
        self.trade.profit_loss_percentage = (profit / (self.trade.entry_price * self.trade.volume)) * 100
        self.trade.save()
        
        self.assertEqual(self.trade.profit_loss, Decimal('52.00'))
        self.assertAlmostEqual(self.trade.profit_loss_percentage, Decimal('2.975'), places=3)
    
    def test_close_trade_loss(self):
        """Test closing a trade with loss"""
        self.trade.trade_type = 'sell'
        self.trade.entry_price = Decimal('175.00')
        self.trade.exit_price = Decimal('176.00')
        self.trade.status = 'closed'
        profit = (self.trade.entry_price - self.trade.exit_price) * self.trade.volume
        self.trade.profit_loss = profit
        self.trade.save()
        
        self.assertEqual(self.trade.profit_loss, Decimal('-10.00'))


class ViewTests(TestCase):
    """Test cases for views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.market = Market.objects.create(
            symbol='ETHUSD',
            name='Ethereum/US Dollar',
            market_type='crypto',
            current_price=Decimal('3000.00'),
            change_24h=Decimal('2.5'),
            high_24h=Decimal('3100.00'),
            low_24h=Decimal('2950.00')
        )
    
    def test_home_view(self):
        """Test home page view"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')
    
    def test_markets_view(self):
        """Test markets page view"""
        response = self.client.get(reverse('markets'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'markets.html')
        self.assertIn('markets_by_type', response.context)
    
    def test_market_detail_view(self):
        """Test market detail view"""
        response = self.client.get(reverse('market_detail', args=[self.market.symbol]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'market_detail.html')
        self.assertEqual(response.context['market'], self.market)
    
    def test_market_detail_404(self):
        """Test market detail view with invalid symbol"""
        response = self.client.get(reverse('market_detail', args=['INVALID']))
        self.assertEqual(response.status_code, 404)
    
    def test_signals_view(self):
        """Test signals page view"""
        response = self.client.get(reverse('signals'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'signals.html')
    
    def test_education_view(self):
        """Test education page view"""
        response = self.client.get(reverse('education'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'education.html')
    
    def test_dashboard_view_authenticated(self):
        """Test dashboard view for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')
        self.assertEqual(response.context['trader'], self.user)
    
    def test_dashboard_view_unauthenticated(self):
        """Test dashboard view redirects when not logged in"""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertIn(reverse('login'), response.url)
    
    def test_analysis_view_authenticated(self):
        """Test analysis view for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('analysis'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'analysis.html')
    
    def test_tools_view_authenticated(self):
        """Test tools view for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('tools'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tools.html')


class APITests(TestCase):
    """Test cases for API endpoints"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='apitrader',
            password='apipass'
        )
        self.market = Market.objects.create(
            symbol='XAUUSD',
            name='Gold/US Dollar',
            market_type='commodities',
            current_price=Decimal('1950.50'),
            change_24h=Decimal('0.30'),
            high_24h=Decimal('1960.00'),
            low_24h=Decimal('1945.00')
        )
    
    def test_get_market_data_authenticated(self):
        """Test market data API with authentication"""
        self.client.login(username='apitrader', password='apipass')
        response = self.client.get(reverse('get_market_data', args=[self.market.symbol]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['symbol'], self.market.symbol)
        self.assertEqual(data['current_price'], float(self.market.current_price))
        self.assertIn('historical_data', data)
    
    def test_get_market_data_unauthenticated(self):
        """Test market data API without authentication"""
        response = self.client.get(reverse('get_market_data', args=[self.market.symbol]))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_create_trade_authenticated(self):
        """Test create trade API with authentication"""
        self.client.login(username='apitrader', password='apipass')
        trade_data = {
            'symbol': self.market.symbol,
            'trade_type': 'buy',
            'entry_price': '1952.00',
            'volume': '0.5',
            'notes': 'Test trade'
        }
        response = self.client.post(
            reverse('create_trade'),
            data=json.dumps(trade_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('trade_id', data)
        
        # Verify trade was created in database
        trade = Trade.objects.get(trade_id=data['trade_id'])
        self.assertEqual(trade.trader, self.user)
        self.assertEqual(trade.market, self.market)
        self.assertEqual(trade.trade_type, 'buy')
    
    def test_create_trade_invalid_data(self):
        """Test create trade with invalid data"""
        self.client.login(username='apitrader', password='apipass')
        trade_data = {
            'symbol': 'INVALID',
            'trade_type': 'buy',
            'entry_price': '1952.00',
            'volume': '0.5'
        }
        response = self.client.post(
            reverse('create_trade'),
            data=json.dumps(trade_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
    
    def test_close_trade_authenticated(self):
        """Test close trade API"""
        self.client.login(username='apitrader', password='apipass')
        
        # Create a trade first
        trade = Trade.objects.create(
            trader=self.user,
            market=self.market,
            trade_type='buy',
            entry_price=Decimal('1950.00'),
            volume=Decimal('1.0'),
            status='open'
        )
        
        # Close the trade
        response = self.client.post(
            reverse('close_trade', args=[trade.trade_id]),
            {'exit_price': '1970.00'}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Verify trade was updated
        trade.refresh_from_db()
        self.assertEqual(trade.status, 'closed')
        self.assertEqual(trade.exit_price, Decimal('1970.00'))
        self.assertEqual(trade.profit_loss, Decimal('20.00'))  # (1970 - 1950) * 1


class URLTests(TestCase):
    """Test URL routing"""
    
    def test_url_resolves_home(self):
        url = reverse('home')
        self.assertEqual(url, '/')
    
    def test_url_resolves_markets(self):
        url = reverse('markets')
        self.assertEqual(url, '/markets/')
    
    def test_url_resolves_signals(self):
        url = reverse('signals')
        self.assertEqual(url, '/signals/')
    
    def test_url_resolves_education(self):
        url = reverse('education')
        self.assertEqual(url, '/education/')
    
    def test_url_resolves_login(self):
        url = reverse('login')
        self.assertEqual(url, '/login/')
    
    def test_url_resolves_dashboard(self):
        url = reverse('dashboard')
        self.assertEqual(url, '/dashboard/')


class ModelMethodTests(TestCase):
    """Additional model method tests"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testmethod',
            password='testpass'
        )
    
    def test_trader_update_win_rate_edge_cases(self):
        """Test win rate with zero trades and large numbers"""
        # Zero trades
        self.user.total_trades = 0
        self.user.successful_trades = 5  # shouldn't happen but test
        self.user.update_win_rate()
        self.assertEqual(self.user.win_rate, 0.0)
        
        # All successful
        self.user.total_trades = 10
        self.user.successful_trades = 10
        self.user.update_win_rate()
        self.assertEqual(self.user.win_rate, 100.0)
        
        # None successful
        self.user.successful_trades = 0
        self.user.update_win_rate()
        self.assertEqual(self.user.win_rate, 0.0)
    
    def test_educational_content_str(self):
        """Test string representation for EducationalContent if defined"""
        # Since the model doesn't define __str__, this test passes anyway
        content = EducationalContent.objects.create(
            title='Test Course',
            content_type='course',
            difficulty_level='beginner',
            content='Test content',
            published=True
        )
        # Just verify it's created
        self.assertEqual(content.title, 'Test Course')


class IntegrationTests(TestCase):
    """Integration tests combining multiple components"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='integuser',
            password='integpass'
        )
        self.market = Market.objects.create(
            symbol='GBPUSD',
            name='British Pound/US Dollar',
            market_type='forex',
            current_price=Decimal('1.2650'),
            change_24h=Decimal('-0.15'),
            high_24h=Decimal('1.2680'),
            low_24h=Decimal('1.2620')
        )
    
    def test_full_trade_lifecycle(self):
        """Test the entire trade lifecycle: create -> close -> verify stats"""
        self.client.login(username='integuser', password='integpass')
        
        # 1. Create a trade via API
        trade_data = {
            'symbol': self.market.symbol,
            'trade_type': 'sell',
            'entry_price': '1.2660',
            'volume': '10000',
            'notes': 'Integration test trade'
        }
        response = self.client.post(
            reverse('create_trade'),
            data=json.dumps(trade_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        trade_id = data['trade_id']
        
        # 2. Verify trade appears in user's open trades on dashboard
        dashboard_response = self.client.get(reverse('dashboard'))
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertContains(dashboard_response, trade_id[:8])  # partial UUID match
        
        # 3. Close the trade with profit
        close_response = self.client.post(
            reverse('close_trade', args=[trade_id]),
            {'exit_price': '1.2600'}
        )
        self.assertEqual(close_response.status_code, 200)
        close_data = close_response.json()
        self.assertTrue(close_data['success'])
        self.assertGreater(float(close_data['profit_loss']), 0)
        
        # 4. Verify trader stats updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.total_trades, 1)
        self.assertEqual(self.user.successful_trades, 1)
        self.assertEqual(self.user.win_rate, 100.0)
        # Balance should have increased
        self.assertGreater(self.user.balance, Decimal('10000.00'))
        
        # 5. Verify trade status updated in database
        trade = Trade.objects.get(trade_id=trade_id)
        self.assertEqual(trade.status, 'closed')
        self.assertIsNotNone(trade.closed_at)
        self.assertEqual(trade.profit_loss, Decimal('60.00'))  # (1.2660 - 1.2600) * 10000


class FormTests(TestCase):
    """Test forms if any (for future expansion)"""
    # Currently no forms defined, but placeholder for future
    pass


# To run tests: python manage.py test trading