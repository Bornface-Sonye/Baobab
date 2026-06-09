from django.contrib import admin
from .models import (
    Investor, Asset, AssetCategory,
    PortfolioHolding, Trade,
    WalletTransaction, TradeIssue, TradeResolution
)

# =========================
# INVESTOR ADMIN
# =========================
@admin.register(Investor)
class InvestorAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'cash_balance')
    search_fields = ('username', 'email')


# =========================
# ASSET ADMIN (STOCKS / CRYPTO / FUNDS)
# =========================
@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol', 'current_price', 'category')
    list_filter = ('category',)
    search_fields = ('name', 'symbol')


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


# =========================
# PORTFOLIO HOLDINGS
# =========================
@admin.register(PortfolioHolding)
class PortfolioHoldingAdmin(admin.ModelAdmin):
    list_display = ('investor', 'asset', 'quantity', 'average_buy_price')
    list_filter = ('asset',)
    search_fields = ('investor__username', 'asset__name')


# =========================
# TRADE SYSTEM (BUY / SELL)
# =========================
@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ('investor', 'asset', 'trade_type', 'quantity', 'price', 'timestamp')
    list_filter = ('trade_type', 'asset')
    search_fields = ('investor__username', 'asset__name')


# =========================
# WALLET TRANSACTIONS
# =========================
@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('investor', 'amount', 'transaction_type', 'created_at')
    list_filter = ('transaction_type',)
    search_fields = ('investor__username',)


# =========================
# SUPPORT / ISSUES
# =========================
@admin.register(TradeIssue)
class TradeIssueAdmin(admin.ModelAdmin):
    list_display = ('issue_id', 'investor', 'issue_type', 'status')
    list_filter = ('status', 'issue_type')
    search_fields = ('issue_id', 'investor__username')


@admin.register(TradeResolution)
class TradeResolutionAdmin(admin.ModelAdmin):
    list_display = ('issue', 'status', 'resolver', 'created_at')
    list_filter = ('status',)
    search_fields = ('issue__issue_id',)


# =========================
# OPTIONAL: If you still use Django auth fallback
# =========================
from django.contrib.auth.models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_staff')
    search_fields = ('username', 'email')