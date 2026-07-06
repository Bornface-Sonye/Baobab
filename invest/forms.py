from django import forms
from .models import (
    Investor, Asset, Trade,
    TradeIssue, TradeResolution,
    System_User
)

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


# forms.py

from django import forms
from django.core.exceptions import ValidationError
from .models import Investment


class InvestorLendForm(forms.Form):

    amount = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=100,
        widget=forms.NumberInput(
            attrs={
                'class':'form-control',
                'placeholder':'Enter amount'
            }
        )
    )

    duration_days = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(
            attrs={
                'class':'form-control',
                'placeholder':'Duration in days'
            }
        )
    )

    def clean_amount(self):

        amount=self.cleaned_data['amount']

        if amount<=0:
            raise ValidationError(
                "Amount must be greater than zero"
            )

        return amount


from django import forms
from decimal import Decimal
from .models import Loan


class BorrowForm(forms.ModelForm):

    class Meta:
        model = Loan

        fields = [
            'principal',
            'collateral',
            'duration_days'
        ]

        widgets = {

            'principal': forms.NumberInput(
                attrs={
                    'placeholder': 'Enter amount to borrow',
                    'class': 'form-control'
                }
            ),

            'collateral': forms.NumberInput(
                attrs={
                    'placeholder': 'Enter collateral amount',
                    'class': 'form-control'
                }
            ),

            'duration_days': forms.NumberInput(
                attrs={
                    'placeholder': 'Loan period in days',
                    'class': 'form-control'
                }
            )

        }

    def __init__(self, *args, **kwargs):

        self.interest_rate = kwargs.pop(
            'interest_rate',
            Decimal('10')
        )

        super().__init__(*args, **kwargs)

    def clean(self):

        cleaned_data = super().clean()

        principal = cleaned_data.get(
            'principal'
        )

        collateral = cleaned_data.get(
            'collateral'
        )

        if principal and collateral:

            interest_amount = (
                principal *
                self.interest_rate /
                Decimal('100')
            )

            if collateral < interest_amount:

                raise forms.ValidationError(
                    f"Collateral cannot cover interest amount of Ksh {interest_amount}"
                )

        return cleaned_data
    
from django import forms
from .models import Stock


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
    
from django import forms
from .models import PortfolioHolding


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