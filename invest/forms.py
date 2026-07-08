from django import forms
from .models import (
    Investor, Trade, Investment, Loan, Stock, PortfolioHolding,
    System_User
)

from decimal import Decimal
from django.core.exceptions import ValidationError
import random
import string

# =========================
# LOGIN FORM
# =========================

class SignUpForm(forms.ModelForm):
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password', 'class': 'form-control'})
    )
    class Meta:
        model = System_User
        fields = ['username', 'password_hash']
        labels = {
            'username': 'Username',
            'password_hash': 'Password',
            'confirm_password': 'Confirm Password',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Username eg awaliaro@mmust.ac.ke'}),
            'password_hash': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter Password'}),
            'confirm_password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password_hash")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Password and confirm password do not match")

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.set_password(self.cleaned_data["password_hash"])
        if commit:
            instance.save()
        return instance
    
# =========================
# LOGIN FORM
# =========================
    
class LoginForm(forms.Form):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your Username:'})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password:'})
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")
        return cleaned_data


class PasswordResetForm(forms.Form):
    username = forms.EmailField(
        label='Username',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email address(Username)'})
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not System_User.objects.filter(username=username).exists():
            raise forms.ValidationError("This Username is not associated with any account.")
        return username

class ResetForm(forms.Form):  # Use forms.Form instead of ModelForm
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control'}),
        label="Password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password', 'class': 'form-control'}),
        label="Confirm Password"
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Password and confirm password do not match.")

    def save(self, user, commit=True):
        # Use user object and set password
        user.set_password(self.cleaned_data["password"])  # Hash password and set it
        if commit:
            user.save()
        return user


class InvestorLendForm(forms.Form):

    amount = forms.DecimalField(

        label="Amount",

        max_digits=15,

        decimal_places=2,

        min_value=Decimal("100"),

        widget=forms.NumberInput(
            attrs={
                "class":"form-control",
                "placeholder":"Enter amount to invest"
            }
        )
    )

    duration_days = forms.IntegerField(

        label="Investment Duration",

        min_value=1,

        widget=forms.NumberInput(
            attrs={
                "class":"form-control",
                "placeholder":"Enter duration in days"
            }
        )
    )

    def clean_amount(self):

        amount = self.cleaned_data["amount"]

        if amount <= 0:

            raise ValidationError(
                "Investment amount must be greater than zero."
            )

        return amount


class BorrowForm(forms.ModelForm):

    class Meta:

        model = Loan

        fields = [
            "principal",
            "duration_days",
        ]

        widgets = {

            "principal": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter amount to borrow",
                    "min": "100"
                }
            ),

            "duration_days": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter loan duration (days)",
                    "min": "1"
                }
            ),

        }

        labels = {

            "principal": "Loan Amount",

            "duration_days": "Loan Duration (Days)",

        }

        help_texts = {

            "principal": "Enter the amount you wish to borrow.",

            "duration_days": "Enter the repayment period in days.",

        }

    def __init__(self, *args, **kwargs):

        self.interest_rate = kwargs.pop(
            "interest_rate",
            Decimal("0.00")
        )

        super().__init__(*args, **kwargs)

    def clean_principal(self):

        principal = self.cleaned_data["principal"]

        if principal <= 0:

            raise ValidationError(
                "Loan amount must be greater than zero."
            )

        if principal < Decimal("100"):

            raise ValidationError(
                "Minimum loan amount is KSh 100."
            )

        return principal

    def clean_duration_days(self):

        duration = self.cleaned_data["duration_days"]

        if duration <= 0:

            raise ValidationError(
                "Loan duration must be greater than zero."
            )

        if duration > 3650:

            raise ValidationError(
                "Loan duration cannot exceed 3650 days."
            )

        return duration

    def clean(self):

        cleaned_data = super().clean()

        principal = cleaned_data.get("principal")

        duration = cleaned_data.get("duration_days")

        if principal and duration:

            if duration < 1:

                raise ValidationError(
                    "Invalid loan duration."
                )

        return cleaned_data


class BuyStockForm(forms.Form):

    stock = forms.ModelChoiceField(

        queryset=Stock.objects.all(),

        empty_label="Select Stock",

        widget=forms.Select(
            attrs={
                'class':'form-control'
            }
        )
    )


    quantity=forms.IntegerField(

        min_value=1,

        widget=forms.NumberInput(
            attrs={
                'class':'form-control',
                'placeholder':'Enter quantity'
            }
        )
    )


class SellStockForm(forms.Form):

    stock = forms.ModelChoiceField(
        queryset=PortfolioHolding.objects.none(),

        empty_label="Select Stock",

        widget=forms.Select(
            attrs={
                'class':'form-control'
            }
        )
    )

    quantity=forms.IntegerField(

        min_value=1,

        widget=forms.NumberInput(
            attrs={
                'class':'form-control',
                'placeholder':'Quantity to sell'
            }
        )
    )

    def __init__(self,*args,**kwargs):

        investor=kwargs.pop(
            'investor',
            None
        )

        super().__init__(
            *args,
            **kwargs
        )

        if investor:

            self.fields[
                'stock'
            ].queryset=PortfolioHolding.objects.filter(
                investor=investor
            )
# =========================
# PASSWORD RESET REQUEST
# =========================
class PasswordResetForm(forms.Form):
    username = forms.CharField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email'
        })
    )


# =========================
# RESET PASSWORD FORM
# =========================
class ResetForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password")
        p2 = cleaned.get("confirm_password")

        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match")
        return cleaned