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
    
    national_id_no = models.DecimalField(primary_key=True, max_digits=8, decimal_places=0, unique=True, validators=[validate_kenyan_id], help_text="Enter National Identification Number in the format 35033637")
    email_address = models.EmailField(max_length=200, help_text="Please Enter Investor Email Address")
    username = models.EmailField(unique=True, max_length=200, help_text="Enter a valid Username")
    first_name = models.CharField(max_length=150, help_text="Enter Your First Name")
    last_name = models.CharField(max_length=150, help_text="Enter Your Last Name")
    phone_number = models.CharField(max_length=15, validators=[validate_kenyan_phone_number], help_text="Enter phone number in the format 0798073204 or +254798073404")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.national_id_no


# ===========================================
# WALLET
# ===========================================

class Wallet(models.Model):

    investor=models.ForeignKey(Investor, on_delete=models.CASCADE, help_text="Please Enter Investor Email Address")
    available_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Please Enter Available Wallet Balance")
    locked_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Please Enter Locked Balance")
    borrowed_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Please Enter Borrowed Balance")
    collateral_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Please Enter Collateral Balance")

    def __str__(self):
        return f"{self.investor.last_name} Wallet"


# ===================================================================================================
# LIQUIDITY POOL: THIS TABLE IS UPDATED EVERY 10 SECONDS, IT UPDATES WITH THE GRAPH ON THE DASHBOARD
# ===================================================================================================

class LiquidityPool(models.Model):

    total_available=models.DecimalField(max_digits=15, decimal_places=2, default=1000000, help_text="Please Enter Total Available Amount")
    total_borrowed=models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Please Enter Total Amount Borrowed")
    total_invested=models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Please Enter Total Amount Invested")
    total_collateral=models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Please Enter Total Collateral Amount")
    current_interest_rate=models.DecimalField(max_digits=5, decimal_places=2, default=10, help_text="Please Enter Current Interest Rate")


# ===========================================
# INVESTMENT
# ===========================================

class Investment(models.Model):

    STATUS = (
        ('ACTIVE','ACTIVE'),
        ('MATURED','MATURED'),
        ('RELEASED','RELEASED')
    )

    investor=models.ForeignKey(Investor, on_delete=models.CASCADE, help_text="Please Enter Investor Email Address")
    amount=models.DecimalField(max_digits=15,decimal_places=2, help_text="Please Enter Amount Invested")
    interest_rate=models.DecimalField(max_digits=5, decimal_places=2, help_text="Please Enter Interest Rate for Investment")
    duration_days=models.IntegerField()
    expected_return=models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Please Enter Expected Return")
    status=models.CharField(max_length=20, choices=STATUS, default='ACTIVE', help_text="Please Select Investment Status")
    start_date=models.DateTimeField(auto_now_add=True)
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

    borrower=models.ForeignKey(Investor, on_delete=models.CASCADE, help_text="Please Select Investor")
    principal=models.DecimalField(max_digits=15, decimal_places=2, help_text="Please Enter Principal Amount")
    collateral=models.DecimalField(max_digits=15, decimal_places=2, help_text="Please Enter Collateral Amount")
    interest_rate=models.DecimalField(max_digits=5, decimal_places=2, help_text="Please Enter Interest Rate")
    amount_due=models.DecimalField(max_digits=15, decimal_places=2, help_text="Please Enter Amount Due")
    duration_days=models.IntegerField()
    due_date=models.DateTimeField()
    status=models.CharField(max_length=20, choices=STATUS, default='ACTIVE', help_text="Please Enter Loan Status")

'''
# ===========================================
# LOAN TRACKER
# ===========================================

class LoanTracker(models.Model):

    loan=models.ForeignKey(Loan, on_delete=models.CASCADE)
    investment=models.ForeignKey(Investment, on_delete=models.CASCADE)
    amount_allocated=models.DecimalField(max_digits=15, decimal_places=2)
    profit_generated=models.DecimalField(max_digits=15, decimal_places=2, default=0)
    remaining_balance=models.DecimalField(max_digits=15, decimal_places=2)
'''


# =========================
# STOCK     (Add symbol field) ; bank shares, eg Equity shares, KPLC shares
# =========================
class Stock(models.Model):
    stock_code = models.CharField(primary_key=True, max_length=20, help_text="Please Enter Stock Code")
    stock_name = models.CharField(max_length=200, help_text="Please Enter Stock Name")
    shares = models.IntegerField(help_text="Enter Number of Available Shares")
    current_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], help_text="Enter Price per Share")

    def __str__(self):
        return self.stock_name


# ===========================================
# PORTFOLIO
# ===========================================

class PortfolioHolding(models.Model):

    FUND_SOURCE = (

        ('OWN','OWN'),
        ('BORROWED','BORROWED')
    )

    investor=models.ForeignKey(Investor, on_delete=models.CASCADE, help_text="Please Select Investor")
    stock=models.ForeignKey(Stock, on_delete=models.CASCADE, help_text="Please Select Stock")
    quantity=models.IntegerField()
    average_buy_price=models.DecimalField(max_digits=15, decimal_places=2, help_text="Please Enter Average Buy Price")
    fund_source=models.CharField(max_length=20, choices=FUND_SOURCE, help_text="Please Select Fund Source")


# ===========================================
# TRADE
# ===========================================

class Trade(models.Model):

    TYPES = (
        ('BUY','BUY'),
        ('SELL','SELL')
    )

    investor=models.ForeignKey(Investor, on_delete=models.CASCADE, help_text="Please Select Investor")
    stock=models.ForeignKey(Stock, on_delete=models.CASCADE, help_text="Please Select Stock")
    trade_type=models.CharField(max_length=20, choices=TYPES, help_text="Please Select Trade Type")
    quantity=models.IntegerField()
    price=models.DecimalField(max_digits=15, decimal_places=2, help_text="Please Enter Trade Price")
    timestamp=models.DateTimeField(auto_now_add=True)


# =======================================================================================================
# INTEREST HISTORY: THIS IS UPDATE FROM THE GRAPH, AS GRAPH MOVES YOU RECORD THE INTEREST DEVIATIONS HERE
# =======================================================================================================

class InterestHistory(models.Model):

    interest_rate=models.DecimalField(max_digits=5, decimal_places=2, help_text="Please Enter Interest Rate")
    liquidity=models.DecimalField(max_digits=15, decimal_places=2, help_text="Please Enter Liquidity")
    timestamp=models.DateTimeField(auto_now_add=True)


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
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Token for {self.username}"

    def is_expired(self):
        expiration_time = self.timestamp + timedelta(minutes=5)
        return timezone.now() > expiration_time