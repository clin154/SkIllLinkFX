from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from django.views.generic.edit import CreateView
from . import views
from .forms import TraderCreationForm

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('markets/', views.markets, name='markets'),
    path('market/<str:symbol>/', views.market_detail, name='market_detail'),
    path('signals/', views.signals, name='signals'),
    path('education/', views.education, name='education'),
    path('education/<uuid:content_id>/', views.education_detail, name='education_detail'),
    
    # Protected pages
    path('dashboard/', views.dashboard, name='dashboard'),
    path('analysis/', views.analysis, name='analysis'),
    path('tools/', views.tools, name='tools'),
    path('profile/', views.profile, name='profile'),
    
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', CreateView.as_view(
        template_name='registration/register.html',
        form_class=TraderCreationForm,
        success_url=reverse_lazy('login')
    ), name='register'),
    
    # API endpoints
    path('api/market/<str:symbol>/', views.get_market_data, name='get_market_data'),
    path('api/trade/create/', views.create_trade, name='create_trade'),
    path('api/trade/<uuid:trade_id>/close/', views.close_trade, name='close_trade'),
    path('api/update-experience/', views.update_experience, name='update_experience'),
    path('api/deposit/', views.deposit, name='deposit'),      # ✅ new deposit endpoint
    path('api/withdraw/', views.withdraw, name='withdraw'),   # ✅ new withdraw endpoint
]