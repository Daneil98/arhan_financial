import jwt, time
from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import datetime, timedelta

# Assumes api_client.py is in the same directory. Adjust import if needed.
from .client_api import IdentityClient, AccountClient, PaymentClient
from .forms import *
from .models import User

# --- Helper Function ---
def get_token(request):
    """Retrieve the JWT token from the user session."""
    return request.session.get('token')

def check_session(request):
    """
    Checks if token exists AND is not expired.
    Returns (True, token) or (False, None).
    """
    token = request.session.get('access_token') # Standardized Key Name
    
    # 1. Check Existence
    if not token:
        print("[⛔] Check Session: No token found in session.")
        return False, None

    # 2. Check Expiration
    try:
        # verify_signature=False because we just want to read the date.
        # The backend API handles the security verification.
        payload = jwt.decode(token, options={"verify_signature": False})
        exp_timestamp = payload.get('exp')
        
        if exp_timestamp and time.time() > exp_timestamp:
            print("[⛔] Check Session: Token Expired.")
            request.session.flush()
            return False, None
            
    except jwt.DecodeError:
        print("[⛔] Check Session: Token Corrupted/Invalid.")
        request.session.flush()
        return False, None
    except Exception as e:
        print(f"[⛔] Check Session Error: {e}")
        return False, None
        
    return True, token

# ==========================================
# 1. AUTHENTICATION VIEWS (Identity Service)
# ==========================================

def index(request):
    return render(request, 'index.html')

def login_view(request):
    # Check if already logged in
    is_valid, _ = check_session(request)
    if is_valid:
        return redirect('dashboard')

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            
            try:
                client = IdentityClient()
                response = client.login(username, password)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # 🟢 ROBUST TOKEN EXTRACTION
                    # Checks for 'access' (SimpleJWT default) OR 'access_token'
                    access_token = data.get("access") or data.get("access_token")
                    refresh_token = data.get("refresh") or data.get("refresh_token")

                    if not access_token:
                        messages.error(request, "Login successful but server returned no token.")
                        print(f"[❌] API Response missing token: {data.keys()}")
                        return render(request, 'registration/login.html', {'form': form})

                    # 🟢 STANDARDIZED SESSION KEYS
                    request.session['access_token'] = access_token
                    request.session['refresh_token'] = refresh_token
                    request.session['username'] = username
                    request.session.save() # Force save
                    
                    print(f"[✅] Login Success. Token saved. Redirecting...")
                    return redirect('dashboard')
                else:
                    messages.error(request, "Invalid Credentials")
            except Exception as e:
                print(f"[❌] Login Exception: {e}")
                messages.error(request, "Service unavailable.")
    else:
        form = LoginForm()
            
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    token = request.session.get('access_token')
    refresh = request.session.get('refresh_token')

    if token:
        try:
            client = IdentityClient(token)
            client.logout({"refresh": refresh} if refresh else {})
        except Exception as e:
            print(f"[⚠️] API Logout failed (non-critical): {e}")

    request.session.flush()
    messages.info(request, "Logged out.")
    return redirect('login')

def customer_register_view(request):
    
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Construct data dictionary from form inputs
            data = {
                "username": str(form.cleaned_data["username"]),
                "email": str(form.cleaned_data["email"]),
                "password": str(form.cleaned_data["password2"]),
                "first_name": str(form.cleaned_data["first_name"]),
                "last_name": str(form.cleaned_data["last_name"]),
                "phone": str(form.cleaned_data["phone"]),
                "sex": str(form.cleaned_data["sex"]),
            }
            
            client = IdentityClient()
            response = client.customer_register(data)
            
            if response.status_code == 201 or response.status_code == 200:
                User.objects.create(username=data["username"], role="customer")
                messages.success(request, "Registration successful! Please login.")
                return redirect('login')
            else:
                print(f"[❌] Status: {response.status_code}")
                print(f"[❌] Body: {response.text}") # Print raw HTML/Text to terminal

                # Check if content is actually JSON before parsing
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', str(error_data))
                except ValueError:
                    # If it's not JSON, it's likely an HTML error page or raw text
                    error_msg = f"Server Error ({response.status_code}). Check logs."

                messages.error(request, f"Registration Failed: {error_msg}")
        else:
            messages.error(request, "Please correct the error(s) below.")
    else:
        form = UserRegistrationForm()        
    return render(request, 'customer_webportal/register.html', {'form': form})




# ==========================================
# 2. ACCOUNT VIEWS (Account Service)
# ==========================================

def dashboard_view(request):
    print("--- DASHBOARD START ---")
    
    # 1. Local Session Check
    is_valid, token = check_session(request)
    if not is_valid:
        print("[↪️] Redirecting to login (Session Invalid)")
        return redirect('login')

    # 2. Remote API Check (Account Service)
    try:
        account_client = AccountClient(token)
        account_response = account_client.dashboard()

        if account_response.status_code != 200:
            print(f"[↪️] Redirecting to login (API rejected token: {account_response.status_code})")
            messages.error(request, "Session expired (API).")
            return redirect('logout') # Use logout to clear bad session
            
        dashboard_data = account_response.json()
        
    except Exception as e:
        print(f"[❌] Dashboard API Crash: {e}")
        messages.error(request, "Could not connect to Account Service.")
        return render(request, 'customer_webportal/dashboard.html', {'dashboard_data': {}})

    # 3. Fetch Transactions (Payment Service)
    try:
        payment_client = PaymentClient(token)
        payment_response = payment_client.transfer_history()
        
        my_account_number = str(dashboard_data.get('account_number'))
        total_income = 0.0
        total_expense = 0.0
        recent_transactions = []

        if payment_response.status_code == 200:
            # Handle paginated or flat list results
            p_data = payment_response.json()
            raw_list = p_data.get('data', p_data) if isinstance(p_data, dict) else p_data
            if not isinstance(raw_list, list): raw_list = []

            for t in raw_list:
                amount = float(t.get('amount', 0.0))
                # Safely get sender/recipient, checking if they are dicts or strings
                sender_val = t.get('sender')
                recipient_val = t.get('recipient')
                
                # If sender is a dict {id: "...", ...}, get ID, else assume string
                payer_id = str(sender_val.get('account_number') if isinstance(sender_val, dict) else sender_val)
                payee_id = str(recipient_val.get('account_number') if isinstance(recipient_val, dict) else recipient_val)

                if payee_id == my_account_number:
                    total_income += amount
                elif payer_id == my_account_number:
                    total_expense += amount

            # Sort and Slice
            raw_list.sort(key=lambda x: x.get('date', ''), reverse=True)
            recent_transactions = raw_list[:5]
            
            # Date Formatting
            from datetime import datetime
            for t in recent_transactions:
                raw_date = t.get('date')
                if raw_date:
                    try:
                        dt = datetime.fromisoformat(raw_date.replace('Z', '+00:00'))
                        t['date'] = dt.strftime('%b %d, %I:%M %p')
                    except:
                        pass

        dashboard_data.update({
            'total_income': total_income,
            'total_expense': total_expense,
            'recent_transactions': recent_transactions
        })

    except Exception as e:
        print(f"[⚠️] Transaction History Error: {e}")
        # Don't crash dashboard if history fails, just show 0s
        dashboard_data.update({'recent_transactions': []})

    return render(request, 'customer_webportal/dashboard.html', {'dashboard_data': dashboard_data})


def create_bank_account_view(request):
    is_valid, token = check_session(request)
    if not is_valid:
        return redirect('login')
        
    form = BankAccountForm(request.POST)
    if request.method == "POST":
        if form.is_valid():
            data = {
                    "PIN": form.cleaned_data["PIN"],
                }
            
            client = AccountClient(token)
            response = client.create_bank_account(data)
            
            if response.status_code == 201 or response.status_code == 200:
                messages.success(request, "Bank account created successfully.")
                return redirect('dashboard')
            else:
                messages.error(request, "Failed to create account.")
        else:
            messages.error(request, "Please correct the error(s) below.")
    else:
        form = BankAccountForm()

    return render(request, 'customer_webportal/create_bank_account.html', {'form': form})


def account_detail_view(request):
    is_valid, token = check_session(request)
    if not is_valid:
        return redirect('login')
        
    client = AccountClient(token)
    
    # Fetch Bank Account Data
    response = client.bank_account_details()
    context = {}
    if response.status_code == 200:
        raw_data = response.json()

        # Clean keys for the template
        context = {
            'id': raw_data.get('id'),
            'number': raw_data.get('account number'), # Renamed for easy access
            'balance': raw_data.get('balance'),
            'rate': raw_data.get('interest rate'),
            'created_at': raw_data.get('created_at'),
        }
        return render(request, 'customer_webportal/bank_account.html', {'context': context})
    else:
        messages.error(request, "Could not load bank account data.")
        return render(request, 'customer_webportal/bank_account.html', {'context': context})
     


def block_account_view(request):
    is_valid, token = check_session(request)
    if not is_valid:
        return redirect('login')
    
    form = BlockAccountForm(request.POST)
    if request.method == "POST":
        if form.is_valid():
            data = {
                "account_number": form.cleaned_data["account_number"],
                "pin": form.cleaned_data["pin"], # e.g., VERVE, MASTERCARD
            }
            
            client = AccountClient(token)
        
            response = client.block_account(data)
            context = {}
            if response.status_code == 200:
                context['bank_acc_data'] = response.json()
            else:
                messages.error(request, "Could not block the account.")
        else:
            messages.error(request, "Please correct the error(s) below.")
    else:
        form = BlockAccountForm()
    return render(request, 'customer_webportal/block_account.html', {'form': form, 'context': context})
    
def create_card_view(request):
    """View to request a new card"""
    is_valid, token = check_session(request)
    if not is_valid:
        return redirect('login')
    
    form = CardForm(request.POST)
    if request.method == "POST":
        if form.is_valid():
            data = {
                "pin": form.cleaned_data["pin"], 
            }
            
            client = AccountClient(token)
            response = client.create_card(data)
            
            if response.status_code == 200 or response.status_code == 201:
                messages.success(request, "Card creation initiated.")
                return redirect('dashboard')
            else:
                messages.error(request, f"Error: {response.text}")
        else:
            messages.error(request, "Please correct the error(s) below.")
    else:
        form = CardForm()
        
    return render(request, 'customer_webportal/create_card.html', {'form': form})

def view_card_view(request):
    """View to see all registered cards"""
    is_valid, token = check_session(request)
    if not is_valid:
        return redirect('login')
        
    client = AccountClient(token)
    
    response = client.view_cards()

    if response.status_code == 200:
        # 2. Extract the list (Handle standard list or DRF 'results' pagination)
        item = response.json()
        #item = api_data.get('data')
        

        # Create a clean dictionary for EACH card
        card_obj = {
            'expiry_date': item.get('expiry_date'),
            'card_number': item.get('card_number'),
            'cvv': item.get('cvv'),
            'card_type': item.get('card_type'),
            'status': item.get('active'),
        }


        # 4. Pass the LIST (plural) to the template
        return render(request, 'customer_webportal/cards.html', {'card': card_obj})
    else:
        return render(request, 'customer_webportal/cards.html', {'card': []})
    
     
def block_card_view(request):
    """View to block a card"""
    is_valid, token = check_session(request)
    if not is_valid:
        return redirect('login')
        
    form = BlockCardForm(request.POST)
    if request.method == "POST":
        if form.is_valid():
            data = {
                "pin": form.cleaned_data["pin"], 
            }
            
            client = AccountClient(token)
            response = client.block_card(data)
            
            if response.status_code == 200:
                messages.success(request, "Card blocked successfully.")
                return redirect('dashboard')
            else:
                messages.error(request, f"Error: {response.text}")
        else:
            messages.error(request, "Please correct the error(s) below.")
    else:
        form = BlockCardForm()
        
    return render(request, 'customer_webportal/block_card.html', {'form': form})

def loan_apply_view(request):
    is_valid, token = check_session(request)
    if not is_valid:
        return redirect('login')
    
    form = LoanApplicationForm(request.POST)
    
    if request.method == "POST":
        if form.is_valid():
            data = {
                "amount": str(form.cleaned_data["amount"]),
                "duration": str(form.cleaned_data["duration"]),
            }
            
            client = AccountClient(token)
            response = client.loan_apply(data)
            
            if response.status_code == 200 or response.status_code == 201:
                messages.success(request, "Loan application submitted.")
                return redirect('dashboard')
            else:
                messages.error(request, "Loan application failed.")
        else:
            messages.error(request, "Please correct the error(s) below.")
    else:
        form = LoanApplicationForm()  
    return render(request, 'customer_webportal/loan_apply.html', {'form': form})


def activity_view(request):
    if not check_session(request):
        return redirect('login')
    
    return render(request, 'customer_webportal/activity.html')


def loan_detail_view(request):
    is_valid, token = check_session(request)
    if not is_valid:
        return redirect('login')
    
    client = AccountClient(token)
    
    response = client.loan_detail()
    loan_response = response.json() if response.status_code == 200 else {}
    loan =  {    
        'amount': loan_response.get('amount'),
        'amount_repayable': loan_response.get('amount_repayable'),
        'monthly_repayment': loan_response.get('monthly_repayment'),
        'interest_rate': loan_response.get('interest_rate'),
        'duration': loan_response.get('duration'),
        'status': loan_response.get('loan_status'),
    }
    return render(request, 'customer_webportal/loan_detail.html', {'loan': loan})



def create_ticket_view(request):
    is_valid, token = check_session(request)
    if not is_valid:
        return redirect('login')
    
    client = AccountClient(token)
    
    form = CreateTicketForm(request.POST)
    # Handle New Ticket Creation
    if request.method == "POST":
        if form.is_valid():
            data = {
                "complaint": form.cleaned_data["complaint"],
                "subject": form.cleaned_data["subject"],
            }
            client.create_ticket(data)
            messages.success(request, "Ticket created.")
            return redirect('dashboard')
    else:
        form = CreateTicketForm()
    return render(request, 'customer_webportal/create_ticket.html', {'form': form})


# ==========================================
# 3. PAYMENT VIEWS (Payment Service)
# ==========================================


def internal_transfer_view(request):
    is_valid, token = check_session(request)
    if not is_valid:
        return redirect('login')
    
    form = InternalTransferForm(request.POST)
    if request.method == "POST":
        if form.is_valid():
            data = {
                "payee_account_id": str(form.cleaned_data.get("payee_account_id")),
                "amount": float(form.cleaned_data.get("amount")),
                "pin": form.cleaned_data.get("pin"),
            }
            
            client = PaymentClient(token)
            response = client.internal_transfer(data)
            
            if response.status_code == 200:
                messages.success(request, "Transfer successful!")
                return redirect('dashboard')
            else:
                # Try to get specific error message from API
                try:
                    err = response.json().get('error', 'Transfer failed')
                except:
                    err = "Transfer failed"
                messages.error(request, err)
        else:
            messages.error(request, "Please correct the error(s) below.")
    else:
        form = InternalTransferForm()    
    return render(request, 'customer_webportal/internal_transfer.html', {'form': form})


def card_payment_view(request):
    is_valid, token = check_session(request)
    if not is_valid:
        return redirect('login')
    
    form = CardPaymentForm(request.POST)
    if request.method == "POST":
        if form.is_valid():
            data = {
                "payee_account_id": str(form.cleaned_data.get("payee_account_id")),
                "amount": float(form.cleaned_data.get("amount")),
                "card_number": str(form.cleaned_data.get("card_number")),
                "cvv": str(form.cleaned_data.get("cvv")),
                "pin": form.cleaned_data.get("pin"),
            }
            
            client = PaymentClient(token)
            response = client.card_payment(data)
            
            if response.status_code == 200:
                messages.success(request, "Transfer successful!")
                return redirect('dashboard')
            else:
                # Try to get specific error message from API
                try:
                    err = response.json().get('error', 'Transfer failed')
                except:
                    err = "Transfer failed"
                messages.error(request, err)
        else:
            messages.error(request, "Please correct the error(s) below.")
    else:
        form = CardPaymentForm()    
    return render(request, 'customer_webportal/card_payment.html', {'form': form})


def transaction_history_view(request):
    # 1. Check Session
    is_valid, token = check_session(request)
    if not is_valid:
        return redirect('login')

    
    # 2. Call the API (Instead of querying the DB)
    client = PaymentClient(token)
    response = client.transfer_history()

    history_data = []

    if response.status_code == 200:
        api_response = response.json()
        # The API returns a list of DICTIONARIES, not Objects
        if isinstance(api_response, dict):
            # Try common DRF keys, or look at your print output to find the right one
            payments = api_response.get('results') or api_response.get('data') or []
        else:
            # It's already a list
            payments = api_response


        history_data = []
        for payment in payments:
            raw_date = payment.get('date')
            formatted_date = raw_date  # Default fallback
            if raw_date:
                try:
                    dt_obj = datetime.fromisoformat(raw_date.replace('Z', '+00:00'))
                    # Added %I:%M %p for Time (Hour:Minute AM/PM)
                    formatted_date = dt_obj.strftime('%b %d, %Y - %H:%M') 
                except ValueError:
                    formatted_date = raw_date[:16].replace('T', ' ') # Fallback: 2025-12-09 18:23
            
            data = {
                # USE BRACKETS [] because 'payment' is a Dictionary
                'sender': payment.get('sender'), 
                'recipient': payment.get('recipient'),
                'amount': payment.get('amount'),
                'currency': payment.get('currency'),
                'payment_type': payment.get('payment_type'),
                'date': formatted_date,
                # Add status/invoice if your API sends them
                'status': payment.get('status'), 
            }
            history_data.append(data)
    else:
        messages.error(request, "Could not fetch transactions.")

    return render(request, 'customer_webportal/transactions.html', {'transactions': history_data})


def analytics_view(request):
    # 1. Security Check
    is_valid, token = check_session(request)
    if not is_valid:
        return redirect('login')
    
    # 2. Fetch User Account Info (To know "Who am I?")
    # We need this to verify if we are the sender or receiver
    account_client = AccountClient(token)
    account_response = account_client.dashboard()
    
    if account_response.status_code != 200:
        messages.error(request, "Could not load account details.")
        return redirect('dashboard')
        
    account_data = account_response.json()
    my_account_number = str(account_data.get('account_number'))

    # 3. Fetch All Transactions
    payment_client = PaymentClient(token)
    payment_response = payment_client.transfer_history()
    
    transactions = []
    if payment_response.status_code == 200:
        api_data = payment_response.json()
        transactions = api_data.get('results') or api_data.get('data') or []

    # 4. --- DATA AGGREGATION LOGIC ---
    
    total_income = 0.0
    total_expense = 0.0
    
    # Setup for Line Chart (Daily Spending - Last 7 Days)
    today = datetime.now()
    # Create a list of last 7 days strings like ['Dec 12', 'Dec 13'...]
    last_7_days = [(today - timedelta(days=i)).strftime('%b %d') for i in range(6, -1, -1)]
    # Initialize dictionary with 0 for all days to ensure the chart has no gaps
    daily_spending = {day: 0.0 for day in last_7_days}

    # Setup for Top Recipients
    recipient_counts = {}

    for t in transactions:
        amount = float(t.get('amount', 0.0))
        
        # Convert IDs to string for safe comparison
        payer_id = str(t.get('sender'))
        payee_id = str(t.get('recipient'))
        
        # --- LOGIC: INCOME VS EXPENSE ---
        if payee_id == my_account_number:
            # Money coming IN to me
            total_income += amount
            
        elif payer_id == my_account_number:
            # Money going OUT from me (Expense)
            total_expense += amount
            
            # --- CHART LOGIC (Only track expenses for the chart) ---
            # 1. Daily Spending Chart
            raw_date = t.get('date', '')
            try:
                # Parse ISO date "2025-12-19T..."
                dt_obj = datetime.fromisoformat(raw_date.replace('Z', ''))
                day_key = dt_obj.strftime('%b %d')
                
                # Only add if this date is within our 7-day window
                if day_key in daily_spending:
                    daily_spending[day_key] += amount
            except ValueError:
                pass # Skip if date format is weird

            # 2. Top Recipients Logic
            # Since I am the payer, the recipient is the 'payee_account_id'
            recipient = payee_id
            recipient_counts[recipient] = recipient_counts.get(recipient, 0) + amount

    # 5. Prepare Data for Template
    
    # Chart.js expects two separate lists: Labels and Data
    chart_labels = list(daily_spending.keys())
    chart_data = list(daily_spending.values())
    
    # Sort recipients by amount (High to Low) and take top 3
    top_recipients = sorted(recipient_counts.items(), key=lambda x: x[1], reverse=True)[:3]

    context = {
        'total_income': total_income,
        'total_expense': total_expense,
        'net_flow': total_income - total_expense,
        
        # Chart Data
        'chart_labels': chart_labels, 
        'chart_data': chart_data,
        
        # Lists
        'top_recipients': top_recipients
    }

    return render(request, 'customer_webportal/analytics.html', context)
