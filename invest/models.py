from django.db import models
from datetime import date
from django.utils import timezone
import random
import string
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password
from .validators import validate_kenyan_phone_number
from django.core.validators import MinValueValidator, MaxValueValidator

# =========================
# INVESTOR (was Student)
# =========================
class Investor(models.Model):
    national_id_no = models.DecimalField(primary_key=True, max_digits=8, help_text="Enter National Identification Number in the format 35033637")
    email_address = models.EmailField(max_length=200, help_text="Please Enter Investor Email Address")
    username = models.EmailField(unique=True, max_length=200, help_text="Enter a valid Username")
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=13, validators=[validate_kenyan_phone_number], help_text="Enter phone number in the format 0798073204 or +254798073404")

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
# USER AUTH (System_User)
# =========================
class System_User(models.Model):
    username = models.CharField(primary_key=True, unique=True, max_length=50, help_text="Enter a valid Username")
    password_hash = models.CharField(max_length=128, help_text="Enter a valid password")  # Store hashed password

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)

    def clean(self):
        # Custom validation for password field
        if len(self.password_hash) < 8:
            raise ValidationError("Password must be at least 8 characters long.")

    def __str__(self):
        return self.username   


# =========================
# PASSWORD RESET
# =========================
class PasswordResetToken(models.Model):
    user = models.ForeignKey(System_User, on_delete=models.CASCADE)
    token = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10)