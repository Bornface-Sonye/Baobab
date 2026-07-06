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

]

