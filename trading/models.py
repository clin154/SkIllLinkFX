from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid

class Trader(AbstractUser):
    trader_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=10000.00)
    experience_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
            ('expert', 'Expert')
        ],
        default='beginner'
    )
    subscription_type = models.CharField(
        max_length=20,
        choices=[
            ('free', 'Free'),
            ('basic', 'Basic'),
            ('pro', 'Professional'),
            ('vip', 'VIP')
        ],
        default='free'
    )
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True)
    total_trades = models.IntegerField(default=0)
    successful_trades = models.IntegerField(default=0)
    win_rate = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date_joined']
    
    def update_win_rate(self):
        if self.total_trades > 0:
            self.win_rate = (self.successful_trades / self.total_trades) * 100
        else:
            self.win_rate = 0.0
        self.save()

class Market(models.Model):
    symbol = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    market_type = models.CharField(
        max_length=20,
        choices=[
            ('forex', 'Forex'),
            ('crypto', 'Cryptocurrency'),
            ('stocks', 'Stocks'),
            ('indices', 'Indices'),
            ('commodities', 'Commodities')
        ]
    )
    current_price = models.DecimalField(max_digits=12, decimal_places=4)
    change_24h = models.DecimalField(max_digits=8, decimal_places=2)
    volume_24h = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    high_24h = models.DecimalField(max_digits=12, decimal_places=4)
    low_24h = models.DecimalField(max_digits=12, decimal_places=4)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['market_type', 'symbol']
    
    def __str__(self):
        return f"{self.symbol} - {self.name}"

class TradingSignal(models.Model):
    signal_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    market = models.ForeignKey(Market, on_delete=models.CASCADE, related_name='signals')
    signal_type = models.CharField(
        max_length=10,
        choices=[
            ('buy', 'Buy'),
            ('sell', 'Sell'),
            ('neutral', 'Neutral')
        ]
    )
    strength = models.CharField(
        max_length=20,
        choices=[
            ('weak', 'Weak'),
            ('moderate', 'Moderate'),
            ('strong', 'Strong'),
            ('very_strong', 'Very Strong')
        ]
    )
    entry_price = models.DecimalField(max_digits=12, decimal_places=4)
    target_price = models.DecimalField(max_digits=12, decimal_places=4)
    stop_loss = models.DecimalField(max_digits=12, decimal_places=4)
    timeframe = models.CharField(max_length=20)
    analysis = models.TextField()
    generated_by = models.ForeignKey(Trader, on_delete=models.SET_NULL, null=True, blank=True)
    is_ai_generated = models.BooleanField(default=False)
    confidence_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['market', 'signal_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['confidence_score']),
        ]

class TechnicalIndicator(models.Model):
    market = models.ForeignKey(Market, on_delete=models.CASCADE, related_name='indicators')
    indicator_name = models.CharField(max_length=50)
    value = models.DecimalField(max_digits=12, decimal_places=4)
    signal = models.CharField(
        max_length=10,
        choices=[
            ('bullish', 'Bullish'),
            ('bearish', 'Bearish'),
            ('neutral', 'Neutral')
        ]
    )
    timeframe = models.CharField(max_length=20)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['market', 'indicator_name', 'timeframe']

class Trade(models.Model):
    trade_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    trader = models.ForeignKey(Trader, on_delete=models.CASCADE, related_name='trades')
    market = models.ForeignKey(Market, on_delete=models.CASCADE)
    trade_type = models.CharField(
        max_length=10,
        choices=[
            ('buy', 'Buy'),
            ('sell', 'Sell')
        ]
    )
    entry_price = models.DecimalField(max_digits=12, decimal_places=4)
    exit_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    volume = models.DecimalField(max_digits=12, decimal_places=4)
    status = models.CharField(
        max_length=20,
        choices=[
            ('open', 'Open'),
            ('closed', 'Closed'),
            ('pending', 'Pending')
        ],
        default='open'
    )
    profit_loss = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    profit_loss_percentage = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-opened_at']

class AnalysisReport(models.Model):
    report_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    trader = models.ForeignKey(Trader, on_delete=models.CASCADE, related_name='reports')
    market = models.ForeignKey(Market, on_delete=models.CASCADE, null=True, blank=True)
    report_type = models.CharField(
        max_length=50,
        choices=[
            ('daily', 'Daily Analysis'),
            ('weekly', 'Weekly Analysis'),
            ('monthly', 'Monthly Analysis'),
            ('technical', 'Technical Analysis'),
            ('fundamental', 'Fundamental Analysis')
        ]
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    summary = models.TextField()
    sentiment = models.CharField(
        max_length=20,
        choices=[
            ('bullish', 'Bullish'),
            ('bearish', 'Bearish'),
            ('neutral', 'Neutral'),
            ('mixed', 'Mixed')
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']

class EducationalContent(models.Model):
    content_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=200)
    content_type = models.CharField(
        max_length=20,
        choices=[
            ('article', 'Article'),
            ('video', 'Video'),
            ('tutorial', 'Tutorial'),
            ('course', 'Course'),
            ('ebook', 'E-Book')
        ]
    )
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced')
        ]
    )
    content = models.TextField()
    thumbnail = models.ImageField(upload_to='education/', blank=True, null=True)
    video_url = models.URLField(blank=True)
    duration = models.IntegerField(help_text="Duration in minutes", null=True, blank=True)
    author = models.ForeignKey(Trader, on_delete=models.SET_NULL, null=True, blank=True)
    views = models.IntegerField(default=0)
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Educational Content'