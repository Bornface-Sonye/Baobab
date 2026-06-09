import re
from django.core.exceptions import ValidationError


# =========================
# WALLET / TRANSACTION REFERENCE VALIDATION
# =========================
def validate_transaction_ref(value):
    """
    Format: TXN-ABC123456
    Used for deposits, withdrawals, and trade references.
    """
    pattern = r'^TXN-[A-Z0-9]{6,10}$'

    if not re.match(pattern, str(value)):
        raise ValidationError(
            f'{value} is not a valid transaction reference (e.g. TXN-AB12CD34)'
        )


# =========================
# KENYAN PHONE NUMBER VALIDATION (M-PESA READY)
# =========================
def validate_kenyan_phone_number(value):
    """
    Accepts:
    - 0798073204
    - +254798073404
    - 254798073404
    """
    value_str = str(value)

    pattern = r'^(?:\+254|254|0)?7\d{8}$'

    if not re.match(pattern, value_str):
        raise ValidationError(
            f'{value} is not a valid Kenyan phone number. '
            f'Use 0798073204 or +254798073404 format.'
        )


# =========================
# INVESTMENT AMOUNT VALIDATION
# =========================
def validate_investment_amount(value):
    """
    Ensures users cannot trade with invalid amounts.
    """
    try:
        value = float(value)
    except:
        raise ValidationError("Amount must be numeric")

    if value <= 0:
        raise ValidationError("Amount must be greater than zero")

    if value < 10:
        raise ValidationError("Minimum investment amount is 10")