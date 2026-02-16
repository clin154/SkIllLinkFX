from django.apps import AppConfig

class TradingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'trading'
    verbose_name = 'SkillLink_FX Trading Platform'

    def ready(self):
        # Import signals (if you create signals.py later)
        # import trading.signals
        pass