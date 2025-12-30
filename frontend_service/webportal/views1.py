import jwt, time
from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import datetime, timedelta
# Assumes api_client.py is in the same directory. Adjust import if needed.
from .client_api import IdentityClient, AccountClient, PaymentClient, BankClient
from .forms import *
from .models import User




# ==========================================
# THIS VIEW IS FOR STAFF FUNCTIONS
# ==========================================

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
        print("Check Session: No token found in session.")
        return False, None

    # 2. Check Expiration
    try:
        # verify_signature=False because we just want to read the date.
        # The backend API handles the security verification.
        payload = jwt.decode(token, options={"verify_signature": False})
        exp_timestamp = payload.get('exp')
        
        if exp_timestamp and time.time() > exp_timestamp:
            print("Check Session: Token Expired.")
            request.session.flush()
            return False, None
            
    except jwt.DecodeError:
        print("Check Session: Token Corrupted/Invalid.")
        request.session.flush()
        return False, None
    except Exception as e:
        print(f"Check Session Error: {e}")
        return False, None
        
    return True, token


# ==========================================
# 1. AUTHENTICATION VIEWS (Identity Service)
# ==========================================

def index(request):
    return render(request, 'index.html')


def staff_login_view(request):
    # Check if already logged in
    is_valid, _ = check_session(request)
    if is_valid:
        return redirect('staff_dashboard')

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            
            try:
                # Use the correct client method for staff login
                client = IdentityClient()
                response = client.login(username, password) # Ensure this method exists!
                
                if response.status_code == 200:
                    data = response.json()
                    
                    #DEBUG PRINT
                    print(f"DEBUG: Staff Login Success. Keys: {data.keys()}")

                    # 1. Extract Token (Handle variations)
                    access_token = data.get("access_token") or data.get("access")
                    refresh_token = data.get("refresh_token") or data.get("refresh")
                    
                    if not access_token:
                        messages.error(request, "Login failed: No access token received.")
                        return render(request, 'staff_webportal/login.html', {'form': form})

                    # 2. SAVE TO SESSION 
                    # You MUST use 'access_token' to match check_session()
                    request.session['access_token'] = access_token
                    request.session['refresh_token'] = refresh_token
                    request.session['username'] = username
                    request.session['is_staff'] = True # Useful flag
                    
                    # Force save to be safe
                    request.session.modified = True
                    
                    messages.success(request, f"Welcome Staff {username}")
                    return redirect('staff_dashboard')
                else:
                    messages.error(request, "Invalid Staff Credentials")
            except Exception as e:
                print(f"Staff Login Error: {e}")
                messages.error(request, "System Error")
    else:
        form = LoginForm()
        
    return render(request, 'staff_webportal/login.html', {'form': form})


def logout_view(request):
    token = request.session.get('access_token')
    refresh = request.session.get('refresh_token')

    if token:
        try:
            client = IdentityClient(token)
            client.logout({"refresh": refresh} if refresh else {})
        except Exception as e:
            print(f"API Logout failed (non-critical): {e}")

    request.session.flush()
    messages.info(request, "Logged out.")
    return redirect('staff_login')


def staff_register_view(request):
    form = UserRegistrationForm(request.POST)    
    
    if request.method == "POST":
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
            response = client.staff_register(data)

            if response.status_code == 201 or response.status_code == 200:
                User.objects.create(username=data["username"], role="staff")
                messages.success(request, "Registration successful! Please login.")
                return redirect('staff_login')
            else:
                print(f"Status: {response.status_code}")
                print(f"Body: {response.text}") # Print raw HTML/Text to terminal

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
    return render(request, 'staff_webportal/register.html', {'form': form})


# ==========================================
# 2. ACCOUNT VIEWS (Account Service)
# ==========================================


def staff_dashboard_view(request):
    """
    Main Admin Dashboard showing Bank Liquidity and System Activity
    """
    is_valid, token = check_session(request)
    if not is_valid:
        return redirect('staff_login')
    
    # Optional: Verify user is_staff here if your auth system supports it
    # if not request.session.get('is_staff'): return redirect('dashboard')

    client = AccountClient(token)
    payment_client = PaymentClient(token)

    # 1. Fetch System-Wide Data
    # Assuming endpoints exist, or we aggregate from lists
    # For this example, we mock the "Bank Pool" or fetch the main ledger account
    
    # Placeholder: In a real app, you might have client.get_bank_stats()
    # Here we calculate from recent history for demonstration
    response = client.get_bankpool_details()
    balance = response.json()
    bank_balance = float(balance.get('total_funds'))
    
    trans_response = payment_client.general_history() # Admin endpoint to get ALL transactions
    transactions = trans_response.json().get('data', []) if trans_response.status_code == 200 else []

    # 2. Calculate Dashboard Metrics
    total_inflow = float(0.0)
    total_outflow = float(0.0)
    
    # Calculate flows (logic depends on your transaction model)
    for t in transactions:
        amount = float(t.get('amount', 0.0))
        # Simple logic: If 'internal' transfer, it's neutral. 
        # If 'deposit', it's inflow. If 'withdrawal', it's outflow.
        # Adjust this logic based on your specific transaction types.
        t_type = t.get('transaction_type', '').lower()
        if 'deposit' in t_type:
            total_inflow += amount
        elif 'withdraw' in t_type:
            total_outflow += amount


    bank_pool_balance = bank_balance + (total_inflow - total_outflow)

    # Pending Action Counts 
    loans_response = client.get_pending_loans()

    if loans_response.status_code == 200:
        pending_loans = loans_response.json()
    else:
        pending_loans = 0
    
    tickets_response = client.get_pending_tickets()
    
    if tickets_response.status_code == 200:
        pending_tickets = tickets_response.json()
    else:
        pending_tickets = 0

    context = {
        'bank_balance': bank_pool_balance,
        'total_inflow': total_inflow,
        'total_outflow': total_outflow,
        'recent_transactions': transactions[:8], # Show top 8
        'pending_loans': pending_loans,
        'open_tickets': pending_tickets,
        'user': request.user.username 
    }

    return render(request, 'staff_webportal/staff_dashboard.html', context)
    



def loan_search_view(request):
    is_valid, token = check_session(request)
    if not is_valid:
        return redirect('staff_login')
    

    form = GetLoanForm(request.POST)
    if request.method == "POST":
        if form.is_valid():
            account_number = str(form.cleaned_data.get('account_number'))
            
            if account_number:
                return redirect('loan_detail_specific', account_number=account_number)
        else:
            messages.error(request, "Please enter a valid Account Number")

    return render(request, 'staff_webportal/loan_search.html', {'form': form})


def search_ticket_view(request):
    is_valid, token = check_session(request)
    if not is_valid:
        return redirect('staff_login')

    form = GetTicketForm(request.POST)
    if request.method == "POST":
        if form.is_valid():
            ticket_id = str(form.cleaned_data.get('ticket_id'))
            
            if ticket_id:
                return redirect('ticket_detail', ticket_id=ticket_id)
        else:
            messages.error(request, "Please enter a valid Ticket ID")

    return render(request, 'staff_webportal/search_ticket.html', {'form': form})


def loan_detail_view(request, account_number):
    is_valid, token = check_session(request)
    if not is_valid:
        return redirect('staff_login')

    client = AccountClient(token)

    response = client.search_loan(account_number)
    
    if response.status_code != 200:
        messages.error(request, "Loan not found.")
        return redirect('loan_search')
        
    loan = response.json()

    loan_data = loan.get('data')

    if request.method == "POST":
        form = UpdateLoanForm(request.POST)
        if form.is_valid():

            data = {
                "account_number": account_number,
                "status": form.cleaned_data.get("status"),
            }
            
            update_resp = client.update_loan(data)
            
            if update_resp.status_code == 200:
                messages.success(request, "Loan updated successfully.")
                return redirect('loan_search')
            else:
                messages.error(request, "Failed to update loan.")
    else:

        initial_data = {
            'amount': loan_data.get('amount'),
            'status': loan_data.get('status')
        }
        form = UpdateLoanForm(initial=initial_data)

    return render(request, 'staff_webportal/loan_update.html', {
        'form': form, 
        'loan': loan_data})


def ticket_detail_view(request, ticket_id):
    is_valid, token = check_session(request)
    if not is_valid:
        return redirect('staff_login')

    client = AccountClient(token)

    response = client.get_ticket(ticket_id) 
    
    if response.status_code != 200:
        messages.error(request, "Ticket not found.")
        return redirect('search_ticket')
        
    ticket = response.json()
    ticket_data = ticket.get('data')
    
    if request.method == "POST":
        form = UpdateTicketForm(request.POST)
        if form.is_valid():
            data = {
                "ticket_id": ticket_id, 
                "remarks": form.cleaned_data.get("remarks"), 
                "resolved": str(form.cleaned_data.get("resolved")),
            }
            
            update_resp = client.update_ticket(data)
            
            if update_resp.status_code == 200:
                messages.success(request, "Reply posted successfully.")
                return redirect('search_ticket') 
            else:
                messages.error(request, "Failed to update ticket.")
    else:
        form = UpdateTicketForm()

    context = {
        'form': form, 
        'ticket': ticket_data
    }
    return render(request, 'staff_webportal/ticket_update.html', context)


def staff_activity_view(request):
    is_valid, token = check_session(request)
    if not is_valid:
        return redirect('staff_login')

    return render(request, 'staff_webportal/staff_activity.html')


def staff_block_account(request):
    is_valid, token = check_session(request)
    if not is_valid:
        return redirect('staff_login')
    
    account_client = AccountClient(token)
    
    if request.method == 'POST':
        form = StaffBlockAccountForm(request.POST)
        if form.is_valid():
            data = {
                'account_number': str(form.cleaned_data['account_number']),
                'pin': form.cleaned_data['pin'],
            }
            response = account_client.block_account(data)
            if response.status_code == 200:
                messages.success(request, 'Account blocked successfully')
            else:
                messages.error(request, 'FAILURE to block account')
    else:
        form = StaffBlockAccountForm()
    
    return render(request, 'staff_webportal/staff_block_account.html', {'form': form})
        
    


# ==========================================
# 4. BANK/LEDGER VIEWS (Ledger Service)
# ==========================================



def bank_ledger_records_view(request):
    """View for Staff to see Master Ledger Records"""
    is_valid, token = check_session(request)
    if not is_valid:
        return redirect('staff_login')
        
    client = BankClient(token)
    
    response = client.get_bank_records()
    
    # Initialize empty lists
    debits = []
    credits = []

    if response.status_code == 200:
        data = response.json()

        debits = data.get('debit_data', [])
        credits = data.get('credit_data', [])
    
    context = {
        'debits': debits,
        'credits': credits
    }
    
    return render(request, 'staff_webportal/ledger_records.html', context)



def bank_transaction_history_view(request):
    """For Staff Auditors"""
    is_valid, token = check_session(request)
    if not is_valid:
        return redirect('staff_login')
    
    print(token)
    client = PaymentClient(token)
    transactions = [] # Default to empty list
    
    try:
        response = client.general_history()
        
        if response.status_code == 200:
            data = response.json()
            # Safely get the list using .get()
            # This prevents crashing if 'history' is missing or if data is empty
            transactions = data.get('data', [])
        else:
            messages.error(request, f"Error fetching logs: {response.status_code}")
            
    except Exception as e:
        messages.error(request, f"Connection Error: {str(e)}")
    
    return render(request, 'staff_webportal/bank_transactions.html', {'transactions': transactions})