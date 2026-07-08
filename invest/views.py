from django.shortcuts import render, redirect, get_object_or_404
from django.views import View

from django.contrib.auth import logout
from django.utils.crypto import get_random_string
from django.conf import settings
from django.core.mail import send_mail

from django.views.generic import ListView, FormView, DeleteView
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
import random, string
import re


from decimal import Decimal
from django.contrib import messages
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


# =========================
# DASHBOARD
# =========================
class DashboardView(View):
    def get(self, request):
        username = request.session.get('username')
        if not username:
            return redirect('login')

        investor = Investor.objects.filter(username=username).first()
        if not investor:
            return redirect('login')

        user = System_User.objects.get(username=username)


        context = {
            'last_name': investor.last_name,
            'user': user,
        }

        return render(request, 'dashboard.html', context)


# ====================================================
# TEMPORARY INTEREST RATE ENGINE
# Updates every 10 seconds
# ====================================================

def update_interest_rate():

    liquidity = LiquidityPool.objects.first()

    if not liquidity:

        liquidity = LiquidityPool.objects.create(
            total_available=1000000,
            current_interest_rate=10
        )


    latest = InterestHistory.objects.order_by(
        '-timestamp'
    ).first()


    now = timezone.now()


    if latest:

        elapsed = (
            now - latest.timestamp
        ).total_seconds()


        if elapsed < 10:
            return


    current_rate = float(
        liquidity.current_interest_rate
    )


    liquidity_amount = float(
        liquidity.total_available
    )


    # smooth movement

    if liquidity_amount < 1000000:

        movement=.25

    elif liquidity_amount>3000000:

        movement=-.20

    else:

        movement=.05


    noise=random.uniform(
        -.10,
        .10
    )


    new_rate=round(
        current_rate+
        movement+
        noise,
        2
    )


    new_rate=max(
        5,
        min(
            new_rate,
            20
        )
    )


    liquidity.current_interest_rate=new_rate

    liquidity.save()


    InterestHistory.objects.create(

        interest_rate=new_rate,

        liquidity=liquidity.total_available

    )


# ====================================================
# DASHBOARD
# ====================================================


class DashboardView(TemplateView):


    def get(self,request):


        username=request.session.get(
            'username'
        )
        if not username:

            return redirect(
                'login'
            )


        try:

            user=System_User.objects.get(
                username=username
            )

        except System_User.DoesNotExist:

            return redirect(
                'login'
            )


        # TEMPORARY
        # until Investor links to System_User

        investor = get_object_or_404(Investor, username=username)


        if not investor:

            return redirect(
                'login'
            )


        wallet,created=Wallet.objects.get_or_create(

            investor=investor
        )


        total_invested=Investment.objects.filter(

            investor=investor
        ).aggregate(

            Sum(
                'amount'
            )

        )['amount__sum'] or 0



        total_loan=Loan.objects.filter(

            borrower=investor
        ).aggregate(

            Sum(
                'principal'
            )

        )['principal__sum'] or 0



        recent_investments=Investment.objects.filter(

            investor=investor

        ).order_by(

            '-start_date'

        )[:5]



        recent_loans=Loan.objects.filter(

            borrower=investor

        ).order_by(

            '-due_date'

        )[:5]



        stocks=Stock.objects.all()



        liquidity=LiquidityPool.objects.first()


        update_interest_rate()


        graph=InterestHistory.objects.filter(

            timestamp__gte=

            timezone.now()

            -

            timedelta(
                hours=24
            )

        ).order_by(

            'timestamp'

        )



        context={

            'phone_number': investor.phone_number,
            'investor': investor,
            'wallet': wallet,
            'total_invested': total_invested,
            'total_loan': total_loan,
            'recent_investments': recent_investments,
            'recent_loans': recent_loans,
            'stocks': stocks,
            'liquidity': liquidity,
            'interest_history': graph,
            'user': user,
            'graph_labels':[

                x.timestamp.strftime(
                    "%H:%M:%S"
                )

                for x in graph

            ],
            'graph_values':[

                float(
                    x.interest_rate
                )

                for x in graph

            ],

            'stock_labels':[

                x.symbol
                for x in stocks

            ],

            'stock_values':[

                float(
                    x.current_price
                )

                for x in stocks

            ]

        }


        return render(request, 'dashboard.html', context)



# ====================================================
# AJAX GRAPH UPDATE
# ====================================================


def dashboard_graph_data(request):

    update_interest_rate()
    graph=InterestHistory.objects.filter(

        timestamp__gte=

        timezone.now()

        -

        timedelta(
            hours=24
        )

    ).order_by(
        'timestamp'
    )


    stocks=Stock.objects.all()


    return JsonResponse({

        'time':[

            x.timestamp.strftime(
                "%H:%M:%S"
            )

            for x in graph

        ],

        'rate':[

            float(
                x.interest_rate
            )

            for x in graph

        ],

        'stocks':[

            x.symbol

            for x in stocks

        ],

        'stock_prices':[

            float(
                x.current_price
            )

            for x in stocks

        ]

    })    

class InvestorLendView(FormView):
    
    def get(self, request):
        username = request.session.get('username')
        if not username:
            return redirect('login')

        investor = get_object_or_404(Investor, username=username)
        form = InvestorLendForm
        liquidity=LiquidityPool.objects.first()
        wallet=Wallet.objects.get(
            investor=investor
        )
        
        amount=form.cleaned_data[
            'amount'
        ]

        duration=form.cleaned_data[
            'duration_days'
        ]
        
        if wallet.available_balance<amount:

            messages.error(
                self.request,
                "Insufficient wallet balance"
            )

            return redirect(
                'lend_money'
            )
            
        interest=liquidity.current_interest_rate


        expected_return=amount + (
            amount *
            Decimal(
                interest/100
            )
        )


        wallet.available_balance-=amount

        wallet.locked_balance+=amount

        wallet.save()


        liquidity.total_available+=amount
        liquidity.total_invested+=amount

        liquidity.save()


        # Pass the necessary information to the template
        form = InvestorLendForm()

        return render(request, 'lend_money.html', {
            'form': form,
            'amount': amount,
            'duration_days': duration,
        })

    def post(self, request):
        username = request.session.get('username')
        if not username:
            return redirect('login')

        investor = get_object_or_404(Investor, username=username)
        form = InvestorLendForm
        liquidity=LiquidityPool.objects.first()
        wallet=Wallet.objects.get(
            investor=investor
        )
        
        amount=form.cleaned_data[
            'amount'
        ]

        duration=form.cleaned_data[
            'duration_days'
        ]
        
        if wallet.available_balance<amount:

            messages.error(
                self.request,
                "Insufficient wallet balance"
            )

            return redirect(
                'lend_money'
            )
            
        interest=liquidity.current_interest_rate


        expected_return=amount + (
            amount *
            Decimal(
                interest/100
            )
        )


        wallet.available_balance-=amount

        wallet.locked_balance+=amount

        wallet.save()


        liquidity.total_available+=amount
        liquidity.total_invested+=amount

        liquidity.save()
        form = InvestorLendForm(request.POST)

        if form.is_valid():
            Investment.objects.create(

            investor=investor,

            amount=amount,

            interest_rate=interest,

            duration_days=duration,

            expected_return=expected_return,

            end_date=timezone.now()+timezone.timedelta(
                days=duration
            )
        )
            messages.success(

            self.request,

            f"Investment successful at {interest}% interest"

        )
            messages.success(request, "Lecturer successfully assigned to the complaint.")
            return redirect('cod-complaints')
           

        return render(request, 'lend_money.html', {
            'form': form,
        })


class InvestorBorrowView(FormView):
    
    def get(self, request):
        username = request.session.get('username')
        if not username:
            return redirect('login')

        form = BorrowForm(
            request.POST,
            interest_rate=interest_rate
        )
        template_name = 'borrow_money.html'
        investor = get_object_or_404(Investor, username=username)
        wallet=Wallet.objects.get(
            investor=investor
        )

        liquidity = LiquidityPool.objects.first()

        interest_rate = liquidity.current_interest_rate
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


        expected_return=amount + (
            amount *
            Decimal(
                interest_rate/100
            )
        )


        wallet.available_balance-=amount

        wallet.locked_balance+=amount

        wallet.save()


        liquidity.total_available+=amount
        liquidity.total_invested+=amount

        liquidity.save()


        # Pass the necessary information to the template
        form = InvestorLendForm()

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
        liquidity=LiquidityPool.objects.first()
        wallet=Wallet.objects.get(
            investor=investor
        )
        
        amount=form.cleaned_data[
            'amount'
        ]

        duration=form.cleaned_data[
            'duration_days'
        ]
        
        if wallet.available_balance<amount:

            messages.error(
                self.request,
                "Insufficient wallet balance"
            )

            return redirect(
                self.template_name
            )
            
        interest=liquidity.current_interest_rate


        expected_return=amount + (
            amount *
            Decimal(
                interest/100
            )
        )


        wallet.available_balance-=amount

        wallet.locked_balance+=amount

        wallet.save()


        liquidity.total_available+=amount
        liquidity.total_invested+=amount

        liquidity.save()
        form = InvestorLendForm(request.POST)

        if form.is_valid():
            loan = form.save(
                commit=False
            )

            principal = form.cleaned_data[
                'principal'
            ]

            collateral = form.cleaned_data[
                'collateral'
            ]

            if wallet is None:

                messages.error(
                    request,
                    "Wallet does not exist"
                )

                return redirect(
                    self.template_name
                )

            if wallet.collateral_balance < collateral:

                messages.error(
                    request,
                    "Insufficient collateral balance"
                )

                return redirect(
                    self.template_name
                )
            if self.liquidity.total_available < principal:

                messages.error(
                    request,
                    "System currently has insufficient funds"
                )

                return redirect(
                    self.template_name
                )

            loan.borrower = investor

            loan.interest_rate = self.interest_rate

            loan.due_date = (
                timezone.now() +
                timedelta(
                    days=loan.duration_days
                )
            )

            loan.save()

            wallet.available_balance += principal

            wallet.borrowed_balance += principal

            wallet.collateral_balance -= collateral

            wallet.save()

            self.liquidity.total_available -= principal

            self.liquidity.total_borrowed += principal

            self.liquidity.save()

            messages.success(
                request,
                "Loan approved successfully"
            )

            return redirect(
                self.template_name
            )

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
