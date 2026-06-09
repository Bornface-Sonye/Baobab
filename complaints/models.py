from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password
from datetime import timedelta


# =========================
# INVESTOR (was Student)
# =========================
class Investor(models.Model):
    investor_id = models.CharField(primary_key=True, max_length=50)
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)

    cash_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)]
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username


# =========================
# ASSET CATEGORY (was Course)
# =========================
class AssetCategory(models.Model):
    code = models.CharField(primary_key=True, max_length=20)
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


# =========================
# ASSET (was Unit)
# =========================
class Asset(models.Model):
    asset_code = models.CharField(primary_key=True, max_length=20)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(AssetCategory, on_delete=models.CASCADE)

    current_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    def __str__(self):
        return self.asset_code


# =========================
# PORTFOLIO HOLDING (was Result)
# =========================
class PortfolioHolding(models.Model):
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)

    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        validators=[MinValueValidator(0)]
    )

    average_buy_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('investor', 'asset')

    @property
    def market_value(self):
        return self.quantity * self.asset.current_price

    @property
    def profit_loss(self):
        return self.market_value - (self.quantity * self.average_buy_price)

    def __str__(self):
        return f"{self.investor} - {self.asset}"


# =========================
# TRADE (BUY/SELL)
# =========================
class Trade(models.Model):
    TRADE_TYPES = [
        ('BUY', 'BUY'),
        ('SELL', 'SELL'),
    ]

    investor = models.ForeignKey(Investor, on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)

    trade_type = models.CharField(max_length=10, choices=TRADE_TYPES)
    quantity = models.DecimalField(max_digits=15, decimal_places=4)

    price = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")

    def __str__(self):
        return f"{self.trade_type} {self.asset} by {self.investor}"


# =========================
# INVESTMENT ORDER ISSUE (was Complaint)
# =========================
class TradeIssue(models.Model):
    issue_id = models.CharField(primary_key=True, max_length=100)
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE)
    trade = models.ForeignKey(Trade, on_delete=models.CASCADE)

    issue_type = models.CharField(
        max_length=50,
        choices=[
            ('FAILED_ORDER', 'FAILED_ORDER'),
            ('WRONG_PRICE', 'WRONG_PRICE'),
            ('MISSING_FUNDS', 'MISSING_FUNDS'),
            ('OTHER', 'OTHER')
        ]
    )

    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.issue_id


# =========================
# RESOLUTION (was Response)
# =========================
class TradeResolution(models.Model):
    issue = models.OneToOneField(TradeIssue, on_delete=models.CASCADE)

    resolver = models.CharField(max_length=100)  # admin/broker name

    status = models.CharField(
        max_length=50,
        choices=[
            ('PENDING', 'PENDING'),
            ('RESOLVED', 'RESOLVED'),
            ('REJECTED', 'REJECTED')
        ]
    )

    comment = models.TextField(blank=True)
    resolved_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.issue.issue_id} - {self.status}"


# =========================
# USER AUTH (was System_User)
# =========================
class SystemUser(models.Model):
    username = models.CharField(primary_key=True, max_length=50)
    password_hash = models.CharField(max_length=128)

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)


# =========================
# PASSWORD RESET
# =========================
class PasswordResetToken(models.Model):
    user = models.ForeignKey(SystemUser, on_delete=models.CASCADE)
    token = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10)