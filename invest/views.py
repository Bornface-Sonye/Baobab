from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, FormView, DeleteView
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
import random, string

from .models import (
    Investor, Asset, AssetCategory,
    PortfolioHolding, Trade,
    TradeIssue, TradeResolution
)

from .forms import (
    LoginForm, TradeForm, DepositForm, WithdrawalForm,
    IssueForm
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

            investor = Investor.objects.filter(username=username).first()

            if investor:
                request.session["username"] = username
                return redirect("dashboard")

            messages.error(request, "Invalid login")
        return render(request, "login.html", {"form": form})


class LogoutView(View):
    def get(self, request):
        request.session.flush()
        return redirect("login")


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