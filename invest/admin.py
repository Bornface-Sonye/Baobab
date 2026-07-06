from django.contrib import admin
from .models import (
    Investor, Wallet, LiquidityPool,
    Investment, Loan, Stock, PortfolioHolding, Trade,
    InterestHistory, System_User, PasswordResetToken
)

# =========================
# INVESTOR ADMIN
# =========================
@admin.register(Investor)
class InvestorAdmin(admin.ModelAdmin):
    list_display = ('national_id_no', 'first_name', 'last_name')
    search_fields = ('national_id_no', 'phone_number')


# =========================
# WALLET
# =========================
@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('investor', 'available_balance', 'locked_balance')
    list_filter = ('locked_balance',)
    search_fields = ('investor', 'available_balance', 'locked_balance')

# =========================
# LIQUIDITY POOL
# =========================
@admin.register(LiquidityPool)
class LiquidityPoolAdmin(admin.ModelAdmin):
    list_display = ('total_available',)
    search_fields = ('total_available',)


# =========================
# INVESTMENT
# =========================
@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ('investor', 'amount', 'interest_rate', 'amount_accrued')
    list_filter = ('investor',)
    search_fields = ('investor', 'amount', 'interest_rate', 'amount_accrued')

# =========================
# LOAN
# =========================
@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('borrower', 'principal', 'interest_rate', 'amount_due')
    list_filter = ('borrower',)
    search_fields = ('borrower', 'principal', 'interest_rate', 'amount_due')
    
    
# =========================
# STOCK
# =========================
@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('stock_code', 'stock_name', 'shares', 'current_price')
    list_filter = ('shares',)
    search_fields = ('stock_code', 'stock_name')
  
# =========================
# STOCK
# =========================
@admin.register(PortfolioHolding)
class PortfolioHoldingAdmin(admin.ModelAdmin):
    list_display = ('investor', 'stock', 'quantity', 'average_buy_price')
    list_filter = ('investor', 'stock')
    search_fields = ('investor', 'stock')  

# =========================
# TRADE SYSTEM (BUY / SELL)
# =========================
@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ('investor', 'stock', 'trade_type', 'quantity', 'price', 'timestamp')
    list_filter = ('investor', 'stock')
    search_fields = ('investor', 'stock')


# =========================
# INTEREST HISTORY
# =========================
@admin.register(InterestHistory)
class InterestHistoryAdmin(admin.ModelAdmin):
    list_display = ('interest_rate', 'liquidity', 'timestamp')
    list_filter = ('interest_rate', 'liquidity')
    search_fields = ('interest_rate', 'liquidity')


# =========================
# SYSTEM USER
# =========================
@admin.register(System_User)
class System_UserAdmin(admin.ModelAdmin):
    list_display = ('username',)
    list_filter = ('username',)
    search_fields = ('username',)


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('username', 'token', 'timestamp')
    list_filter = ('username',)
    search_fields = ('username',)