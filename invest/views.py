from django.shortcuts import render, redirect, get_object_or_404
from django.views import View

from django.contrib.auth import logout
from django.utils.crypto import get_random_string
from django.conf import settings
from django.core.mail import send_mail

from django.views.generic import ListView, FormView, DeleteView
from django.db import transaction
from django.utils import timezone
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
import random, string
import re

from .utils import *
from decimal import Decimal
from django.contrib import messages
from decimal import Decimal, ROUND_HALF_UP
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView

from django.db.models import Sum
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

from .models import (
    Investor, Wallet, Investment, Stock,
    PortfolioHolding, Trade, PasswordResetToken,
    Loan, InterestHistory, LiquidityPool, System_User
)

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum

from .forms import (
    LoginForm, InvestorLendForm, BorrowForm, BuyStockForm,
    SellStockForm, SignUpForm, ResetForm, PasswordResetForm
)


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

# =========================
# SIGNUP
# =========================
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
            
            # Check if the investor exists in the Investor model
            if not Investor.objects.filter(username=username).exists():
                form.add_error('username', "This Investor email does not exist.")
                return render(request, self.template_name, {'form': form})
                
            # Create the account if all checks pass
            new_account = form.save(commit=False)
            new_account.set_password(password_hash)
            new_account.save()
            return redirect('login')
        else:
            # If the form is not valid, render the template with the form and errors
            return render(request, self.template_name, {'form': form})

# =========================
# LOGOUT
# =========================
class LogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)  # Use logout directly
        return redirect('login')  # Redirect to the login page or another appropriate page


# =========================
# PASSWORD RESET
# =========================
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


# =========================
# PASSWORD RESET CONFIRM
# =========================
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


from decimal import Decimal
from django.http import JsonResponse
from django.views import View

from .models import LiquidityPool, InterestHistory
from .utils import MachineLearningModel, InterestRate


class InterestRateEngineView(View):
    """
    Runs the ML model and stores the predicted
    interest rate in InterestHistory.

    This view is intended to be executed every
    60 seconds by APScheduler/Celery/Cron.
    """

    def get(self, request):

        liquidity = LiquidityPool.objects.first()

        if liquidity is None:
            return JsonResponse({
                "status": "error",
                "message": "Liquidity Pool not found."
            })

        # Ensure the model exists
        MachineLearningModel()

        predictor = InterestRate()

        predicted_rate = predictor.predict(
            liquidity.total_available,
            liquidity.total_borrowed,
            liquidity.total_invested,
            liquidity.total_collateral,
            liquidity.current_interest_rate
        )

        # Save a new history record
        InterestHistory.objects.create(
            interest_rate=Decimal(str(predicted_rate)),
            liquidity=liquidity.total_available
        )

        # Keep only the most recent 1440 records
        history = InterestHistory.objects.order_by("-timestamp")

        if history.count() > 1440:
            for record in history[1440:]:
                record.delete()

        deviation = round(
            predicted_rate -
            float(liquidity.current_interest_rate),
            2
        )

        return JsonResponse({

            "status": "success",

            "current_rate": float(
                liquidity.current_interest_rate
            ),

            "predicted_rate": predicted_rate,

            "deviation": deviation

        })
        

        
from django.views.generic import TemplateView
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum

from .models import (
    System_User,
    Investor,
    Wallet,
    Investment,
    Loan,
    Stock,
    LiquidityPool,
    InterestHistory
)


class DashboardView(TemplateView):

    template_name = "dashboard.html"

    def get(self, request):

        username = request.session.get("username")

        if not username:
            return redirect("login")

        try:

            user = System_User.objects.get(
                username=username
            )

        except System_User.DoesNotExist:

            return redirect("login")

        investor = get_object_or_404(
            Investor,
            username=username
        )

        wallet, created = Wallet.objects.get_or_create(
            investor=investor
        )

        total_invested = Investment.objects.filter(
            investor=investor
        ).aggregate(
            total=Sum("amount")
        )["total"] or 0

        total_loan = Loan.objects.filter(
            borrower=investor
        ).aggregate(
            total=Sum("principal")
        )["total"] or 0

        recent_investments = Investment.objects.filter(
            investor=investor
        ).order_by(
            "-start_date"
        )[:5]

        recent_loans = Loan.objects.filter(
            borrower=investor
        ).order_by(
            "-start_date"
        )[:5]

        stocks = Stock.objects.all()

        liquidity = LiquidityPool.objects.first()

        graph = InterestHistory.objects.order_by(
            "timestamp"
        )

        current_rate = 0
        predicted_rate = 0
        deviation = 0

        if liquidity:

            current_rate = float(
                liquidity.current_interest_rate
            )

        if graph.exists():

            latest_prediction = graph.last()

            predicted_rate = float(
                latest_prediction.interest_rate
            )

            deviation = round(
                predicted_rate - current_rate,
                2
            )

        context = {

            "user": user,

            "investor": investor,

            "phone_number": investor.phone_number,

            "wallet": wallet,

            "total_invested": total_invested,

            "total_loan": total_loan,

            "recent_investments": recent_investments,

            "recent_loans": recent_loans,

            "stocks": stocks,

            "liquidity": liquidity,

            "interest_history": graph,

            "current_rate": current_rate,

            "predicted_rate": predicted_rate,

            "deviation": deviation,

            "graph_labels": [

                item.timestamp.strftime("%H:%M:%S")

                for item in graph

            ],

            "graph_values": [

                float(item.interest_rate)

                for item in graph

            ],

            "stock_labels": [

                stock.stock_name

                for stock in stocks

            ],

            "stock_values": [

                float(stock.current_price)

                for stock in stocks

            ]

        }

        return render(
            request,
            self.template_name,
            context
        )
        
from django.http import JsonResponse
from .models import InterestHistory, LiquidityPool, Stock


def dashboard_graph_data(request):
    """
    Returns live dashboard data for AJAX updates.
    """

    liquidity = LiquidityPool.objects.first()

    graph = InterestHistory.objects.order_by("timestamp")

    stocks = Stock.objects.all()

    graph_labels = [
        item.timestamp.strftime("%H:%M:%S")
        for item in graph
    ]

    graph_values = [
        float(item.interest_rate)
        for item in graph
    ]

    liquidity_values = [
        float(item.liquidity)
        for item in graph
    ]

    stock_labels = [
        stock.stock_name
        for stock in stocks
    ]

    stock_values = [
        float(stock.current_price)
        for stock in stocks
    ]

    current_rate = (
        float(liquidity.current_interest_rate)
        if liquidity else 0
    )

    predicted_rate = (
        graph_values[-1]
        if graph_values else current_rate
    )

    deviation = round(
        predicted_rate - current_rate,
        2
    )

    return JsonResponse({

        "graph_labels": graph_labels,

        "graph_values": graph_values,

        "liquidity": liquidity_values,

        "current_rate": current_rate,

        "predicted_rate": predicted_rate,

        "deviation": deviation,

        "stock_labels": stock_labels,

        "stock_values": stock_values,

        "samples": len(graph_values),

        "latest_time": (
            graph_labels[-1]
            if graph_labels else ""
        )

    })
    

def calculate_daily_compound(principal, annual_rate, days):
    """
    annual_rate is a percentage e.g. 12 means 12%
    days is investment duration.
    """

    principal = Decimal(principal)
    annual_rate = Decimal(annual_rate)

    daily_rate = (annual_rate / Decimal("100")) / Decimal("365")

    accrued = principal * ((Decimal("1") + daily_rate) ** days)

    return accrued.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )
    

class InvestorLendView(FormView):

    template_name = "lend_money.html"
    form_class = InvestorLendForm

    def dispatch(self, request, *args, **kwargs):

        if not request.session.get("username"):
            return redirect("login")

        return super().dispatch(request, *args, **kwargs)

    def get_investor(self):

        return get_object_or_404(
            Investor,
            username=self.request.session["username"]
        )

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        investor = self.get_investor()

        context["wallet"] = Wallet.objects.get(
            investor=investor
        )

        latest_interest = InterestHistory.objects.first()

        if latest_interest:
            context["interest_rate"] = latest_interest.interest_rate
        else:
            context["interest_rate"] = Decimal("0.00")

        return context

    @transaction.atomic
    def form_valid(self, form):

        investor = self.get_investor()

        wallet = Wallet.objects.select_for_update().get(
            investor=investor
        )

        liquidity = LiquidityPool.objects.select_for_update().first()

        interest_record = InterestHistory.objects.first()

        if interest_record is None:

            messages.error(
                self.request,
                "No interest rate available."
            )

            return redirect("lend-money")

        annual_rate = interest_record.interest_rate

        amount = form.cleaned_data["amount"]

        duration = form.cleaned_data["duration_days"]

        if wallet.available_balance < amount:

            messages.error(
                self.request,
                "Insufficient wallet balance."
            )

            return redirect("lend-money")

        amount_accrued = calculate_daily_compound(
            amount,
            annual_rate,
            duration
        )

        wallet.available_balance -= amount
        wallet.locked_balance += amount
        wallet.invested_amount += amount
        wallet.save()

        liquidity.total_available += amount
        liquidity.total_invested += amount
        liquidity.save()

        Investment.objects.create(

            investor=investor,

            amount=amount,

            interest_rate=annual_rate,

            duration_days=duration,

            amount_accrued=amount_accrued
        )

        messages.success(

            self.request,

            f"Your investment of KSh {amount:,.2f} has been created successfully. "
            f"It will grow to KSh {amount_accrued:,.2f} after {duration} days."

        )

        return redirect("lend-money")

from decimal import Decimal
from datetime import timedelta

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic.edit import FormView

class InvestorBorrowView(FormView):

    template_name = "borrow_money.html"
    form_class = BorrowForm

    def dispatch(self, request, *args, **kwargs):

        if not request.session.get("username"):
            return redirect("login")

        return super().dispatch(request, *args, **kwargs)

    def get_investor(self):

        return get_object_or_404(
            Investor,
            username=self.request.session["username"]
        )

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        investor = self.get_investor()

        wallet = Wallet.objects.get(
            investor=investor
        )

        liquidity = LiquidityPool.objects.first()

        interest_history = InterestHistory.objects.first()

        context["wallet"] = wallet
        context["liquidity"] = liquidity

        context["interest_rate"] = (
            interest_history.interest_rate
            if interest_history
            else Decimal("0.00")
        )

        return context

    @transaction.atomic
    def form_valid(self, form):

        investor = self.get_investor()

        wallet = Wallet.objects.select_for_update().get(
            investor=investor
        )

        liquidity = LiquidityPool.objects.select_for_update().first()

        interest_history = InterestHistory.objects.first()

        if interest_history is None:

            messages.error(
                self.request,
                "No interest rate has been configured."
            )

            return redirect("borrow-money")

        annual_rate = interest_history.interest_rate

        principal = form.cleaned_data["principal"]

        duration = form.cleaned_data["duration_days"]

        # Check liquidity
        if liquidity.total_available < principal:

            messages.error(
                self.request,
                "The liquidity pool currently has insufficient funds."
            )

            return redirect("borrow-money")

        # Calculate compounded repayment
        amount_due = calculate_daily_compound(
            principal,
            annual_rate,
            duration
        )

        # Interest payable (collateral)
        interest_amount = (
            amount_due - principal
        ).quantize(
            Decimal("0.01")
        )

        # Verify collateral
        if wallet.available_balance < interest_amount:

            messages.error(
                self.request,
                (
                    "Your available wallet balance is too low to "
                    "cover the required loan collateral "
                    f"(KSh {interest_amount:,.2f})."
                )
            )

            return redirect("borrow-money")

        # ------------------------------------
        # Lock the collateral (interest)
        # ------------------------------------

        wallet.available_balance -= interest_amount

        wallet.locked_balance += interest_amount

        # ------------------------------------
        # Credit borrowed money
        # ------------------------------------

        wallet.available_balance += principal

        wallet.borrowed_balance += principal

        wallet.save()

        # ------------------------------------
        # Update Liquidity Pool
        # ------------------------------------

        liquidity.total_available -= principal

        liquidity.total_borrowed += principal

        liquidity.total_collateral += interest_amount

        liquidity.save()

        # ------------------------------------
        # Save Loan
        # ------------------------------------

        Loan.objects.create(

            borrower=investor,

            principal=principal,

            collateral=interest_amount,

            interest_rate=annual_rate,

            amount_due=amount_due,

            duration_days=duration,

            due_date=timezone.now() + timedelta(
                days=duration
            )

        )

        messages.success(

            self.request,

            (
                f"Loan approved successfully.\n\n"
                f"Borrowed Amount: KSh {principal:,.2f}\n"
                f"Interest (Locked Collateral): KSh {interest_amount:,.2f}\n"
                f"Total Repayment: KSh {amount_due:,.2f}\n"
                f"Repayment Period: {duration} day(s)."
            )

        )

        return redirect("borrow-money")

class BuyStockView(FormView):
    
    def get(self, request):
        username = request.session.get('username')
        if not username:
            return redirect('login')

        form = BorrowForm(
            request.POST
        )
        template_name = 'buy_stock.html'
        investor = get_object_or_404(Investor, username=username)
        wallet=Wallet.objects.get(
            investor=investor
        )

        amount=form.cleaned_data['amount']
        duration=form.cleaned_data['duration_days']
        
        if wallet.available_balance<amount:

            messages.error(
                self.request,
                "Insufficient wallet balance"
            )

            return redirect(
                self.template_name
            )


        wallet.available_balance-=amount

        wallet.locked_balance+=amount

        wallet.save()

        # Pass the necessary information to the template
        form = BuyStockForm()

        return render(request, template_name, {
            'form': form,
            'amount': amount,
            'duration_days': duration,
        })

    def post(self, request):
        username = request.session.get('username')
        if not username:
            return redirect('login')

        investor = get_object_or_404(Investor, username=username)

        wallet=Wallet.objects.get(
            investor=investor
        )
         
        form = BuyStockForm(request.POST)
        template_name = 'buy_stock.html'

        if form.is_valid():
            stock=form.cleaned_data[
                'stock'
            ]

            quantity=form.cleaned_data[
                'quantity'
            ]

            total_price=(
                stock.current_price*
                quantity
            )


            if quantity>stock.shares:

                return render(
                    request,
                    template_name,
                    {
                    'form':form,
                    'wallet':wallet,
                    'error':
                    'Not enough stock available'
                    }
                )


            if wallet.available_balance<total_price:

                return render(
                    request,
                    'buy_stock.html',
                    {
                    'form':form,
                    'wallet':wallet,
                    'error':
                    'Insufficient balance'
                    }
                )


            with transaction.atomic():

                wallet.available_balance-=total_price
                wallet.save()


                stock.shares-=quantity
                stock.save()


                portfolio=PortfolioHolding.objects.filter(
                    investor=investor,
                    stock=stock
                ).first()


                if portfolio:

                    old_total=(
                        portfolio.quantity*
                        portfolio.average_buy_price
                    )

                    new_total=(
                        quantity*
                        stock.current_price
                    )

                    total_quantity=(
                        portfolio.quantity+
                        quantity
                    )

                    portfolio.average_buy_price=(
                        (
                        old_total+
                        new_total
                        )/
                        total_quantity
                    )

                    portfolio.quantity=(
                        total_quantity
                    )

                    portfolio.save()

                else:

                    PortfolioHolding.objects.create(

                        investor=investor,

                        stock=stock,

                        quantity=quantity,

                        average_buy_price=stock.current_price,

                        fund_source='OWN'
                    )


                Trade.objects.create(

                    investor=investor,

                    stock=stock,

                    trade_type='BUY',

                    quantity=quantity,

                    price=stock.current_price
                )


            return render(
                request,
                'buy_stock.html',
                {
                'form':BuyStockForm(),
                'wallet':wallet,
                'success':
                'Stock purchased successfully'
                }
            )
            
class SellStockView(FormView):
    
    def get(self, request):
        username = request.session.get('username')
        if not username:
            return redirect('login')

        form = BorrowForm(
            request.POST
        )
        template_name = 'buy_stock.html'
        investor = get_object_or_404(Investor, username=username)
        wallet=Wallet.objects.get(
            investor=investor
        )

        amount=form.cleaned_data['amount']
        duration=form.cleaned_data['duration_days']
        
        if wallet.available_balance<amount:

            messages.error(
                self.request,
                "Insufficient wallet balance"
            )

            return redirect(
                self.template_name
            )


        wallet.available_balance-=amount

        wallet.locked_balance+=amount

        wallet.save()

        # Pass the necessary information to the template
        form = BuyStockForm()

        return render(request, template_name, {
            'form': form,
            'amount': amount,
            'duration_days': duration,
        })

    def post(self, request):
        username = request.session.get('username')
        if not username:
            return redirect('login')

        investor = get_object_or_404(Investor, username=username)

        wallet=Wallet.objects.get(
            investor=investor
        )
        form=SellStockForm(
            request.POST,
            investor=investor
        )

        template_name = 'buy_stock.html'

        if form.is_valid():
            portfolio=form.cleaned_data[
                'stock'
            ]

            quantity=form.cleaned_data[
                'quantity'
            ]

            if quantity>portfolio.quantity:

                return render(
                    request,
                    template_name,
                    {
                        'form':form,
                        'wallet':wallet,
                        'error':
                        'Insufficient stock quantity'
                    }
                )

            stock=portfolio.stock

            total_sale=(
                stock.current_price*
                quantity
            )

            with transaction.atomic():

                wallet.available_balance+=(
                    total_sale
                )

                wallet.save()

                stock.available_units+=(
                    quantity
                )

                stock.save()

                portfolio.quantity-=(
                    quantity
                )

                if portfolio.quantity==0:

                    portfolio.delete()

                else:

                    portfolio.save()


                Trade.objects.create(

                    investor=investor,

                    stock=stock,

                    trade_type='SELL',

                    quantity=quantity,

                    price=stock.current_price
                )


            return render(
                request,
                template_name,
                {
                    'form':SellStockForm(
                        investor=investor
                    ),
                    'wallet':wallet,
                    'success':
                    'Stock sold successfully'
                }
            )
