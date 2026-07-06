import string
import random



from .models import ( Borrowed,
Disburse, Payment)

# utils.py

import os
import pandas as pd
import numpy as np
import joblib

from django.conf import settings
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
from .models import (
    LiquidityPool,
    InterestHistory,
    Loan,
    Investment,
    Investor
)



def generate_number():
    """Generate a random 10-character alphanumeric number."""
    letters = string.ascii_uppercase
    digits = string.digits
    no = ''.join(random.choice(letters + digits) for _ in range(10))
    return no

        
def unique_disbursement_number():
    """Generate a unique disbursement number not already in use."""
    while True:
        disbursement_no = generate_number()
        if not Disburse.objects.filter(disbursement_no=disbursement_no).exists():
            return disbursement_no
        
def unique_transaction_number():
    """Generate a unique transaction number not already in use."""
    while True:
        transaction_no = generate_number()
        if not Borrowed.objects.filter(transaction_no=transaction_no).exists():
            return transaction_no
        
def unique_payment_number():
    """Generate a unique Payment number not already in use."""
    while True:
        payment_no = generate_number()
        if not Payment.objects.filter(payment_no=payment_no).exists():
            return payment_no