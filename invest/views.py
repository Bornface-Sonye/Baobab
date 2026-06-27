from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, FormView, DeleteView
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
import random, string
import re

from .models import (
    Investor, Asset, AssetCategory,
    PortfolioHolding, Trade, PasswordResetToken,
    TradeIssue, TradeResolution, System_User
)

from .forms import (
    LoginForm, TradeForm, DepositForm, WithdrawalForm,
    IssueForm, SignUpForm, ResetForm, PasswordResetForm
)

# =========================
# SESSION CHECK HELPER
# =========================
def get_investor(request):
    username = request.session.get("username")
    if not username:
        return None
    return Investor.objects.filter(username=username).first()


# =========================
# LOGIN
# =========================
class LoginView(View):
    def get(self, request):
        form = LoginForm()
        return render(request, "login.html", {"form": form})

    def post(self, request):
        form = LoginForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            user = System_User.objects.filter(username=username).first()

            if user:
                request.session["username"] = username
                return redirect("dashboard")

            messages.error(request, "Invalid login")
        return render(request, "login.html", {"form": form})


class SignUpView(View):
    template_name = 'signup.html'

    def get(self, request):
        form = SignUpForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = SignUpForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password_hash = form.cleaned_data['password_hash']

            # Check if username already exists in System_User model
            if System_User.objects.filter(username=username).exists():
                form.add_error('username', "This username has already been used in the system!")
                return render(request, self.template_name, {'form': form})
            if self.is_investor_username(username):
                # Check if the investor exists in the Lecturer model
                if not Investor.objects.filter(username=username).exists():
                    form.add_error('username', "This Investor email does not exist.")
                    return render(request, self.template_name, {'form': form})
            else:
                form.add_error('username', "Invalid username format. Please enter a valid Investor Email.")
                return render(request, self.template_name, {'form': form})

            # Create the account if all checks pass
            new_account = form.save(commit=False)
            new_account.set_password(password_hash)
            new_account.save()
            return redirect('login')
        else:
            # If the form is not valid, render the template with the form and errors
            return render(request, self.template_name, {'form': form})

    def is_investor_username(self, username):
        # Check if the username is in the investor email format
        return bool(re.match(r'^[a-zA-Z0-9]{1,15}@investor\.co\.ke$', username))

class LogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)  # Use logout directly
        return redirect('login')  # Redirect to the login page or another appropriate page

class ResetPasswordView(View):
    template_name = 'reset_password.html'
    form_class = PasswordResetForm

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']  # This is the email address
            user = System_User.objects.filter(username=username).first()
            if user:
                try:
                    # Generate a unique token
                    token = get_random_string(length=32)
                    # Save the token to the database
                    PasswordResetToken.objects.create(username=user, token=token)
                    # Generate the reset link
                    reset_link = request.build_absolute_uri(f'/reset-password/{token}/')
                    # Send password reset email
                    send_mail(
                        'Reset Your Password',
                        f'Click the link to reset your password: {reset_link}',
                        settings.EMAIL_HOST_USER,
                        [user.username],  # Use the username as the email address
                        fail_silently=False,
                    )
                    success_message = f"A password reset link has been sent to {user.username}."
                    return render(request, self.template_name, {'form': form, 'success_message': success_message})
                except Exception as e:
                    error_message = f"An error occurred: {str(e)} or Email Address does not exist in our records"
                    return render(request, self.template_name, {'form': form, 'error_message': error_message})
            else:
                error_message = "Email Address does not exist in our records."
                return render(request, self.template_name, {'form': form, 'error_message': error_message})

        return render(request, self.template_name, {'form': form})


class ResetPasswordConfirmView(View):
    template_name = 'reset_password_confirm.html'

    def get(self, request, token):
        form = ResetForm()
        password_reset_token = PasswordResetToken.objects.filter(token=token).first()

        if not password_reset_token or password_reset_token.is_expired():
            error_message = "Token is invalid or expired."
            return render(request, self.template_name, {'form': form, 'token': token, 'error_message': error_message})

        return render(request, self.template_name, {'form': form, 'token': token})

    def post(self, request, token):
        form = ResetForm(request.POST)
        password_reset_token = PasswordResetToken.objects.filter(token=token).first()

        if not password_reset_token or password_reset_token.is_expired():
            error_message = "Token is invalid or expired."
            return render(request, self.template_name, {'form': form, 'token': token, 'error_message': error_message})

        if form.is_valid():
            # Get user related to the token
            user = get_object_or_404(System_User, username=password_reset_token.username)
            form.save(user)  # Save the password to the user

            # Delete the token for security
            password_reset_token.delete()

            # Success message
            messages.success(request, "Your password has been reset successfully.")
            return render(request, self.template_name, {'form': form, 'token': token})

        # If form is not valid, show errors
        return render(request, self.template_name, {'form': form, 'token': token, 'error_message': "Invalid form submission."})


# =========================
# DASHBOARD
# =========================
class DashboardView(View):
    def get(self, request):
        investor = get_investor(request)
        if not investor:
            return redirect("login")

        holdings = PortfolioHolding.objects.filter(investor=investor)

        total_value = sum([h.market_value for h in holdings])
        total_profit = sum([h.profit_loss for h in holdings])

        context = {
            "investor": investor,
            "holdings": holdings,
            "total_value": total_value,
            "total_profit": total_profit,
        }
        return render(request, "dashboard.html", context)


# =========================
# ASSET LIST
# =========================
class AssetListView(ListView):
    model = Asset
    template_name = "assets.html"
    context_object_name = "assets"


# =========================
# BUY / SELL TRADE
# =========================
class TradeView(FormView):
    template_name = "trade.html"
    form_class = TradeForm

    def form_valid(self, form):
        investor = get_investor(self.request)
        if not investor:
            return redirect("login")

        trade = form.save(commit=False)
        trade.investor = investor
        trade.price = trade.asset.current_price

        with transaction.atomic():
            if trade.trade_type == "BUY":
                cost = trade.quantity * trade.price

                if investor.cash_balance < cost:
                    messages.error(self.request, "Insufficient balance")
                    return self.form_invalid(form)

                investor.cash_balance -= cost
                investor.save()

                holding, created = PortfolioHolding.objects.get_or_create(
                    investor=investor,
                    asset=trade.asset,
                    defaults={
                        "quantity": trade.quantity,
                        "average_buy_price": trade.price
                    }
                )

                if not created:
                    total_qty = holding.quantity + trade.quantity
                    holding.average_buy_price = (
                        (holding.quantity * holding.average_buy_price +
                         trade.quantity * trade.price) / total_qty
                    )
                    holding.quantity = total_qty
                    holding.save()

            elif trade.trade_type == "SELL":
                holding = PortfolioHolding.objects.filter(
                    investor=investor,
                    asset=trade.asset
                ).first()

                if not holding or holding.quantity < trade.quantity:
                    messages.error(self.request, "Not enough assets")
                    return self.form_invalid(form)

                holding.quantity -= trade.quantity
                holding.save()

                investor.cash_balance += trade.quantity * trade.price
                investor.save()

        trade.save()
        messages.success(self.request, "Trade executed")
        return redirect("dashboard")


# =========================
# TRADE ISSUE (was Complaint)
# =========================
class IssueView(FormView):
    template_name = "issue.html"
    form_class = IssueForm

    def form_valid(self, form):
        investor = get_investor(self.request)
        if not investor:
            return redirect("login")

        issue = form.save(commit=False)
        issue.investor = investor
        issue.issue_id = "ISS" + ''.join(random.choices(string.digits, k=6))
        issue.save()

        messages.success(self.request, "Issue submitted")
        return redirect("dashboard")


# =========================
# RESOLVE ISSUE
# =========================
class ResolveIssueView(FormView):
    template_name = "resolve_issue.html"
    form_class = IssueForm

    def form_valid(self, form):
        issue = get_object_or_404(TradeIssue, pk=self.kwargs["pk"])

        resolution = TradeResolution.objects.create(
            issue=issue,
            resolver="ADMIN",
            status=form.cleaned_data.get("status"),
            comment=form.cleaned_data.get("comment", "")
        )

        issue.delete()
        messages.success(self.request, "Issue resolved")
        return redirect("dashboard")


# =========================
# PORTFOLIO VIEW
# =========================
class PortfolioView(View):
    def get(self, request):
        investor = get_investor(request)
        if not investor:
            return redirect("login")

        holdings = PortfolioHolding.objects.filter(investor=investor)

        return render(request, "portfolio.html", {
            "holdings": holdings,
            "investor": investor
        })


# =========================
# TRADE HISTORY
# =========================
class TradeHistoryView(ListView):
    model = Trade
    template_name = "trades.html"
    context_object_name = "trades"

    def get_queryset(self):
        investor = get_investor(self.request)
        return Trade.objects.filter(investor=investor).order_by("-timestamp")


# =========================
# DEPOSIT FUNDS
# =========================
class DepositView(FormView):
    form_class = DepositForm
    template_name = "deposit.html"

    def form_valid(self, form):
        investor = get_investor(self.request)
        amount = form.cleaned_data["amount"]

        investor.cash_balance += amount
        investor.save()

        messages.success(self.request, "Deposit successful")
        return redirect("dashboard")


# =========================
# WITHDRAW FUNDS
# =========================
class WithdrawalView(FormView):
    form_class = WithdrawalForm
    template_name = "withdraw.html"

    def form_valid(self, form):
        investor = get_investor(self.request)
        amount = form.cleaned_data["amount"]

        if investor.cash_balance < amount:
            messages.error(self.request, "Insufficient balance")
            return self.form_invalid(form)

        investor.cash_balance -= amount
        investor.save()

        messages.success(self.request, "Withdrawal successful")
        return redirect("dashboard")