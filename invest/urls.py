from django.urls import path
from . import views

urlpatterns = [
    # =========================
    # AUTH
    # =========================
    path('register/', views.SignUpView.as_view(), name='signup'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset-password'),
    path('reset-password/<str:token>/', views.ResetPasswordConfirmView.as_view(), name='reset-password'),

    # =========================
    # DASHBOARD
    # =========================
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    
    # =========================
    # INVESTMENT
    # =========================
    path('lend/', views.InvestorLendView.as_view(), name='lend-money'),
    path('borrow/', views.InvestorBorrowView.as_view(), name='borrow-money'),
    
    # =========================
    # STOCK
    # =========================
    path('buy/', views.BuyStockView.as_view(), name='buy-stock'),
    path('sell/', views.SellStockView.as_view(), name='sell-stock'),



]

