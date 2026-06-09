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



# =========================
# TRADE FORM (BUY / SELL)
# =========================
class TradeForm(forms.ModelForm):

    class Meta:
        model = Trade
        fields = ['asset', 'trade_type', 'quantity']
        widgets = {
            'asset': forms.Select(attrs={'class': 'form-control'}),
            'trade_type': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean_quantity(self):
        qty = self.cleaned_data.get("quantity")
        if qty <= 0:
            raise forms.ValidationError("Quantity must be greater than 0")
        return qty


# =========================
# DEPOSIT FORM
# =========================
class DepositForm(forms.Form):
    amount = forms.DecimalField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


# =========================
# WITHDRAW FORM
# =========================
class WithdrawalForm(forms.Form):
    amount = forms.DecimalField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


# =========================
# ISSUE FORM (like complaint system)
# =========================
class IssueForm(forms.ModelForm):

    class Meta:
        model = TradeIssue
        fields = ['issue_type', 'description']
        widgets = {
            'issue_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
        }

    def generate_issue_id(self):
        return "ISS" + ''.join(random.choices(string.digits, k=6))

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.issue_id:
            instance.issue_id = self.generate_issue_id()
        if commit:
            instance.save()
        return instance


# =========================
# ISSUE RESOLUTION FORM
# =========================
class IssueResolutionForm(forms.Form):
    status = forms.ChoiceField(
        choices=[
            ('PENDING', 'PENDING'),
            ('RESOLVED', 'RESOLVED'),
            ('REJECTED', 'REJECTED'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3
        })
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