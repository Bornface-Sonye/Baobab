from django.db import models
from datetime import date
from django.utils import timezone
import random
import string
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password
from .validators import validate_kenyan_id, validate_kenyan_phone_number
from django.core.validators import MinValueValidator, MaxValueValidator

# models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from .validators import validate_kenyan_phone_number, validate_kenyan_id


# ===========================================
# INVESTOR
# ===========================================

class Investor(models.Model):

    national_id_no = models.CharField(
        max_length=8,
        unique=True,
        validators=[validate_kenyan_id]
    )

    phone_number = models.CharField(
        max_length=13,
        unique=True,
        validators=[validate_kenyan_phone_number]
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.national_id_no


# ===========================================
# WALLET
# ===========================================

class Wallet(models.Model):

    investor=models.ForeignKey(
        Investor,
        on_delete=models.CASCADE
    )

    available_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    locked_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    borrowed_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    collateral_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    def __str__(self):
        return f"{self.investor.username} Wallet"


# ===========================================
# LIQUIDITY POOL
# ===========================================

class LiquidityPool(models.Model):

    total_available=models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=1000000
    )

    total_borrowed=models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    total_invested=models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    total_collateral=models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    current_interest_rate=models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10
    )



# ===========================================
# INVESTMENT
# ===========================================

class Investment(models.Model):

    STATUS = (
        ('ACTIVE','ACTIVE'),
        ('MATURED','MATURED'),
        ('RELEASED','RELEASED')
    )

    investor=models.ForeignKey(
        Investor,
        on_delete=models.CASCADE
    )

    amount=models.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    interest_rate=models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    duration_days=models.IntegerField()

    expected_return=models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    status=models.CharField(
        max_length=20,
        choices=STATUS,
        default='ACTIVE'
    )

    start_date=models.DateTimeField(
        auto_now_add=True
    )

    end_date=models.DateTimeField()


# ===========================================
# LOAN
# ===========================================

class Loan(models.Model):

    STATUS = (
        ('ACTIVE','ACTIVE'),
        ('PAID','PAID'),
        ('OVERDUE','OVERDUE'),
        ('LIQUIDATED','LIQUIDATED')
    )

    borrower=models.ForeignKey(
        Investor,
        on_delete=models.CASCADE
    )

    principal=models.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    collateral=models.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    interest_rate=models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    amount_due=models.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    duration_days=models.IntegerField()

    due_date=models.DateTimeField()

    status=models.CharField(
        max_length=20,
        choices=STATUS,
        default='ACTIVE'
    )



# ===========================================
# LOAN TRACKER
# ===========================================

class LoanTracker(models.Model):

    loan=models.ForeignKey(
        Loan,
        on_delete=models.CASCADE
    )

    investment=models.ForeignKey(
        Investment,
        on_delete=models.CASCADE
    )

    amount_allocated=models.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    profit_generated=models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    remaining_balance=models.DecimalField(
        max_digits=15,
        decimal_places=2
    )



# ===========================================
# STOCK
# ===========================================

class Stock(models.Model):

    symbol=models.CharField(
        max_length=20,
        unique=True
    )

    name=models.CharField(
        max_length=200
    )

    current_price=models.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    available_units=models.IntegerField()

    def __str__(self):

        return self.symbol



# ===========================================
# PORTFOLIO
# ===========================================

class PortfolioHolding(models.Model):

    FUND_SOURCE = (

        ('OWN','OWN'),
        ('BORROWED','BORROWED')
    )

    investor=models.ForeignKey(
        Investor,
        on_delete=models.CASCADE
    )

    stock=models.ForeignKey(
        Stock,
        on_delete=models.CASCADE
    )

    quantity=models.IntegerField()

    average_buy_price=models.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    fund_source=models.CharField(
        max_length=20,
        choices=FUND_SOURCE
    )


# ===========================================
# TRADE
# ===========================================

class Trade(models.Model):

    TYPES = (
        ('BUY','BUY'),
        ('SELL','SELL')
    )

    investor=models.ForeignKey(
        Investor,
        on_delete=models.CASCADE
    )

    stock=models.ForeignKey(
        Stock,
        on_delete=models.CASCADE
    )

    trade_type=models.CharField(
        max_length=20,
        choices=TYPES
    )

    quantity=models.IntegerField()

    price=models.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    created_at=models.DateTimeField(
        auto_now_add=True
    )


# ===========================================
# INTEREST HISTORY
# ===========================================

class InterestHistory(models.Model):

    interest_rate=models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    liquidity=models.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    timestamp=models.DateTimeField(
        auto_now_add=True
    )

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
    username = models.ForeignKey(System_User, on_delete=models.CASCADE)
    token = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Token for {self.username}"

    def is_expired(self):
        expiration_time = self.created_at + timedelta(minutes=5)
        return timezone.now() > expiration_time