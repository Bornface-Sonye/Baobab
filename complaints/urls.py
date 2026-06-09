from django.urls import path
from . import views

urlpatterns = [
    # =========================
    # AUTH
    # =========================
    path('register/', views.SignUpView.as_view(), name='signup'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    # =========================
    # DASHBOARD
    # =========================
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('portfolio/', views.PortfolioView.as_view(), name='portfolio'),

    # =========================
    # ASSETS (MARKET)
    # =========================
    path('assets/', views.AssetListView.as_view(), name='assets'),

    # =========================
    # TRADING SYSTEM
    # =========================
    path('trade/', views.TradeView.as_view(), name='trade'),
    path('trades/history/', views.TradeHistoryView.as_view(), name='trade-history'),

    # =========================
    # WALLET OPERATIONS
    # =========================
    path('deposit/', views.DepositView.as_view(), name='deposit'),
    path('withdraw/', views.WithdrawalView.as_view(), name='withdraw'),

    # =========================
    # SUPPORT / ISSUES
    # =========================
    path('issue/', views.IssueView.as_view(), name='issue'),
    path('issues/resolve/<int:pk>/', views.ResolveIssueView.as_view(), name='resolve-issue'),

    # =========================
    # PASSWORD RESET
    # =========================
    path('reset-password/', views.PasswordResetView.as_view(), name='reset-password'),
    path('reset-password/<str:token>/', views.ResetPasswordConfirmView.as_view(), name='reset-password-confirm'),
]