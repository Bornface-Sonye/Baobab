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

# =========================
# INVESTOR 
# =========================
class Investor(models.Model):
    national_id_no = models.DecimalField(primary_key=True, max_digits=8, decimal_places=0, unique=True, validators=[validate_kenyan_id], help_text="Enter National Identification Number in the format 35033637")
    email_address = models.EmailField(max_length=200, help_text="Please Enter Investor Email Address")
    username = models.EmailField(unique=True, max_length=200, help_text="Enter a valid Username")
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

# ======================================================================================================
# MONEY DISBURSED BY INVESTORS;;;;Interest rate is is filed from the interest rate at that specific time
# ======================================================================================================
class Disbursed(models.Model):
    disbursed_id = models.AutoField(primary_key=True, unique=True)
    disbursement_no = models.CharField(unique=True, max_length=30, help_text="Enter the Disbursement Number", blank=True)
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE)
    disbursed_amount = models.DecimalField(max_digits=15, decimal_places=2, help_text="Enter Amount Disbursed")
    interest_rate = models.DecimalField(max_digits=15, decimal_places=2, help_text="Enter Interest Rate")
    disbursement_date = models.DateField(help_text="Enter Date of Disbursement")

    def __str__(self):
        return f"Disbursement - {self.disbursement_no}"



# ===========================================
# MONEY AVAILABLE FOR BORROWING BY INVESTORS;;;;This is where machine learning will go over to calculate the interest at that specific time; amount available, interest rate per amount, inflation rate;
# ===========================================
class Amount(models.Model):
    amount_id = models.AutoField(primary_key=True, unique=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, help_text="Enter Amount Disbursed")
    interest_rate = models.DecimalField(max_digits=15, decimal_places=2, help_text="Enter Interest Rate")

    def __str__(self):
        return f"Amount - {self.total_amount}"
    

# ==============================
# MONEY BORROWED BY INVESTORS
# ==============================   
class Borrowed(models.Model):
    borrowed_id = models.AutoField(primary_key=True, unique=True)
    transaction_no = models.CharField(unique=True, max_length=30, help_text="Enter the Transaction Number", blank=True)
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE)
    borrowed_amount = models.DecimalField(max_digits=15, decimal_places=2, help_text="Enter Amount to Disburse")
    interest_rate = models.DecimalField(max_digits=15, decimal_places=2, help_text="Enter Interest Rate")
    TIME_TYPE_CHOICES = [
        ('hours', 'Hours'),
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years'),
    ]
    time_type = models.CharField(max_length=20, choices=TIME_TYPE_CHOICES)
    loan_duration = models.IntegerField(help_text="Loan Duration in Hrs/Days/Weeks/Months/Years")
    date_borrowed = models.DateField(help_text="Enter Date of Disbursement")
    

    def __str__(self):
        return f"Borrowing - {self.transaction_no}"


# ==============================
# MONEY PAID BY INVESTORS
# ==============================     
class Payment(models.Model):
    payment_id = models.AutoField(primary_key=True, unique=True)
    payment_no = models.CharField(max_length=30, help_text="Enter the Payment Number", blank=True)
    disbursement_no = models.ForeignKey(Disbursed, on_delete=models.CASCADE)
    transaction_no = models.ForeignKey(Borrowed, on_delete=models.CASCADE)
    payment_amount = models.DecimalField(max_digits=15, decimal_places=2, help_text="Enter Amount to Pay")
    payment_date = models.DateField(help_text="Enter Date of Payment")

    def __str__(self):
        return f"Payment - {self.payment_no}"
    
# ==============================
# LOAN BY INVESTOR
# ==============================    
class Loan(models.Model):
    loan_id = models.AutoField(primary_key=True, unique=True)
    payment_no = models.ForeignKey(Payment, on_delete=models.CASCADE)
    principal = models.DecimalField(max_digits=15, decimal_places=2, help_text="Enter Amount to Pay")
    loan_interest = models.DecimalField(max_digits=15, decimal_places=2, help_text="Interest Rate")
    amount_to_pay = models.DecimalField(max_digits=15, decimal_places=2, help_text="Total Amount")
    amount_paid =  models.DecimalField(max_digits=15, decimal_places=2, help_text="Total Paid")
    balance =  models.DecimalField(max_digits=15, decimal_places=2, help_text="Balance")
    collateral = models.DecimalField(max_digits=15, decimal_places=2, help_text="Enter Collateral Amount")
    loan_date = models.DateField(help_text="Enter Date of last Payment",default='2026-01-01')

    def __str__(self):
        return f"Loan - {self.payment_no}"


# =========================
# STOCK     (Add symbol field) ; bank shares, eg Equity shares, KPLC shares
# =========================
class Stock(models.Model):
    stock_code = models.CharField(primary_key=True, max_length=20)
    name = models.CharField(max_length=200)
    shares = models.IntegerField(help_text="Enter Number of Available Shares")
    current_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Enter Price per Share"
    )

    def __str__(self):
        return self.asset_code

# =========================
# TRADE (BUY/SELL) ===List All Shares/Stocks Bought and Sold
# =========================
class Trade(models.Model):
    TRADE_TYPES = [
        ('BUY', 'BUY'),
        ('SELL', 'SELL'),
    ]

    investor = models.ForeignKey(Investor, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    trade_type = models.CharField(max_length=10, choices=TRADE_TYPES)
    quantity = models.DecimalField(max_digits=15, decimal_places=4)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")

    def __str__(self):
        return f"{self.trade_type} {self.stock} by {self.investor}"

# =========================
# PORTFOLIO HOLDING
# =========================
class PortfolioHolding(models.Model):
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)

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
        unique_together = ('investor', 'stock')

    @property
    def market_value(self):
        return self.quantity * self.stock.current_price

    @property
    def profit_loss(self):
        return self.market_value - (self.quantity * self.average_buy_price)

    def __str__(self):
        return f"{self.investor} - {self.stock}"

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