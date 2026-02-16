from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Trader, Market, TradingSignal, TechnicalIndicator, 
    Trade, AnalysisReport, EducationalContent
)

@admin.register(Trader)
class TraderAdmin(UserAdmin):
    list_display = ('username', 'email', 'experience_level', 'subscription_type', 'balance', 'win_rate')
    list_filter = ('experience_level', 'subscription_type', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Trading Profile', {
            'fields': ('trader_id', 'balance', 'experience_level', 'subscription_type', 
                      'profile_picture', 'bio', 'total_trades', 'successful_trades', 'win_rate')
        }),
    )

@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'market_type', 'current_price', 'change_24h', 'last_updated')
    list_filter = ('market_type',)
    search_fields = ('symbol', 'name')
    readonly_fields = ('last_updated',)

@admin.register(TradingSignal)
class TradingSignalAdmin(admin.ModelAdmin):
    list_display = ('signal_id', 'market', 'signal_type', 'strength', 'entry_price', 
                   'confidence_score', 'created_at', 'expires_at')
    list_filter = ('signal_type', 'strength', 'is_ai_generated', 'market__market_type')
    search_fields = ('market__symbol', 'market__name')
    readonly_fields = ('signal_id', 'created_at')

@admin.register(TechnicalIndicator)
class TechnicalIndicatorAdmin(admin.ModelAdmin):
    list_display = ('market', 'indicator_name', 'value', 'signal', 'timeframe', 'last_updated')
    list_filter = ('signal', 'indicator_name', 'timeframe')
    search_fields = ('market__symbol', 'market__name')

@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ('trade_id', 'trader', 'market', 'trade_type', 'entry_price', 
                   'status', 'profit_loss', 'opened_at')
    list_filter = ('status', 'trade_type', 'market__market_type')
    search_fields = ('trader__username', 'market__symbol')
    readonly_fields = ('trade_id', 'opened_at')

@admin.register(AnalysisReport)
class AnalysisReportAdmin(admin.ModelAdmin):
    list_display = ('report_id', 'trader', 'report_type', 'title', 'sentiment', 'created_at')
    list_filter = ('report_type', 'sentiment')
    search_fields = ('title', 'trader__username', 'market__symbol')
    readonly_fields = ('report_id', 'created_at', 'updated_at')

@admin.register(EducationalContent)
class EducationalContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'content_type', 'difficulty_level', 'author', 'views', 'published', 'created_at')
    list_filter = ('content_type', 'difficulty_level', 'published')
    search_fields = ('title', 'content')
    readonly_fields = ('content_id', 'created_at', 'updated_at', 'views')