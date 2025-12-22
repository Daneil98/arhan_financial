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
    If expired, clears session and returns False.
    """
    token = request.session.get('token')
    
    # 1. First check: Does token exist?
    if not token:
        return False

    try:
        # 2. Decode the token to read the payload
        # We use verify_signature=False because we just want to read the 'exp' date.
        # The actual API backends will verify the signature security.
        payload = jwt.decode(token, options={"verify_signature": False})
        
        # 3. Check Expiration
        # 'exp' is a timestamp (seconds since epoch)
        exp_timestamp = payload.get('exp')
        
        current_timestamp = time.time()
        
        if exp_timestamp and current_timestamp > exp_timestamp:
            # Token is expired!
            print("DEBUG: Token expired. Clearing session.")
            request.session.flush()  # Delete the dead token
            return False
            
    except jwt.DecodeError:
        # Token is malformed
        print("DEBUG: Token decode failed.")
        request.session.flush()
        return False
        
    # Token exists and is not expired
    return True


# ==========================================
# 1. AUTHENTICATION VIEWS (Identity Service)
# ==========================================

def index(request):
    return render(request, 'index.html')


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            
            try:
                client = IdentityClient()
                response = client.login(username, password)
                
                # views.py (Inside login_view)

                if response.status_code == 200:
                    data = response.json()
                    
                    # --- DEBUGGING LINES ---
                    print(f"DEBUG: Full API Response: {data}") 
                    
                    token = data.get("access_token")
                    print(f"DEBUG: Extracted Token: {token}")
                    # -----------------------

                    if not token:
                        print("ERROR: Token is None! Check the API response keys.")
                        messages.error(request, "Login succeeded but no token was found.")
                        return render(request, 'registration/login.html', {'form': form})

                    request.session['token'] = token
                    request.session['username'] = username
                    request.session.save() 
                    
                    return redirect('staff_webportal/dashboard')
            except Exception as e:
                print(f"DEBUG: Error {e}")
                messages.error(request, "Service unavailable.")
        else:
            messages.error(request, "Invalid form data.")
            
    else:
        form = LoginForm()
            
    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    # 1. Retrieve the tokens from the user's session
    # (Assuming you saved them here when they logged in)
    access_token = request.session.get('access_token')
    refresh_token = request.session.get('refresh_token')

    if access_token and refresh_token:
        try:
            # Initialize client with access token for authentication headers
            client = IdentityClient(access_token)
            
            # 2. Call the API to blacklist the token
            # You must pass the refresh_token to the function
            client.logout(refresh_token=refresh_token)
            
        except Exception as e:
            # If the API fails (e.g., token already expired), we still want to 
            # log the user out of the frontend, so we just log the error and move on.
            print(f"API Logout failed: {e}")

    # 3. Clear the Django session (This logs them out of the frontend)
    request.session.flush()
    messages.info(request, "You have been logged out.")
    return redirect('index') # Redirect to login, not 'logged_out' usually


def staff_register_view(request):
    form = UserRegistrationForm(request.POST)    
    
    if request.method == "POST":
        if form.is_valid():
            # Construct data dictionary from form inputs
            data = {
                "username": form.cleaned_data["username"],
                "email": form.cleaned_data["email"],
                "password": form.cleaned_data["password"],
                "first_name": form.cleaned_data["first_name"],
                "last_name": form.cleaned_data["last_name"],
                "phone": form.cleaned_data["phone"],
                "sex": form.cleaned_data["sex"],
                # Add other fields required by your customer_register serializer
            }
        
            client = IdentityClient()
            response = client.staff_register(data)
            
            User.objects.create(username=data["username"], role="staff")
            
            if response.status_code == 201 or response.status_code == 200:
                messages.success(request, "Registration successful! Please login.")
                return redirect('login')
            else:
                # Pass API error message to frontend
                error_msg = response.json().get('detail', 'Registration failed.')
                messages.error(request, f"Error: {error_msg}")
                
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
    if not check_session(request):
        return redirect('login')
    
    # Optional: Verify user is_staff here if your auth system supports it
    # if not request.session.get('is_staff'): return redirect('dashboard')

    token = get_token(request)
    client = AccountClient(token)
    payment_client = PaymentClient(token)

    # 1. Fetch System-Wide Data
    # Assuming endpoints exist, or we aggregate from lists
    # For this example, we mock the "Bank Pool" or fetch the main ledger account
    
    # Placeholder: In a real app, you might have client.get_bank_stats()
    # Here we calculate from recent history for demonstration
    response = client.get_bankpool_details()
    bank_balance = response.json.get('total_funds')
    
    trans_response = payment_client.general_history() # Admin endpoint to get ALL transactions
    transactions = trans_response.json().get('data', []) if trans_response.status_code == 200 else []

    # 2. Calculate Dashboard Metrics
    total_inflow = 0.0
    total_outflow = 0.0
    
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
    if not check_session(request):
        return redirect('login')

    if request.method == "POST":

        loan_id = request.POST.get('loan_id')
        
        if loan_id:

            return redirect('loan_detail', loan_id=loan_id)
        else:
            messages.error(request, "Please enter a valid Loan ID")

    return render(request, 'staff_webportal/search_loan.html')



def loan_detail_view(request, loan_id):
    if not check_session(request):
        return redirect('login')

    token = get_token(request)
    client = AccountClient(token)


    response = client.loan_detail(loan_id)
    
    if response.status_code != 200:
        messages.error(request, "Loan not found.")
        return redirect('loan_search')
        
    loan_data = response.json()

    if isinstance(loan_data, list) and loan_data:
        loan_data = loan_data[0]


    if request.method == "POST":
        form = UpdateLoanForm(request.POST)
        if form.is_valid():

            data = {
                "loan_id": loan_id,
                "status": form.cleaned_data.get("status"),
                "amount": form.cleaned_data.get("amount")
            }
            
            update_resp = client.update_loan(data)
            
            if update_resp.status_code == 200:
                messages.success(request, "Loan updated successfully.")
                return redirect('loan_detail', loan_id=loan_id)
            else:
                messages.error(request, "Failed to update loan.")
    else:

        initial_data = {
            'amount': loan_data.get('amount'),
            'status': loan_data.get('status')
        }
        form = UpdateLoanForm(initial=initial_data)

    return render(request, 'staff_webportal/loan_detail.html', {
        'form': form, 
        'loan': loan_data
    })



def search_ticket_view(request):
    if not check_session(request):
        return redirect('login')


    if request.method == "POST":
        ticket_id = request.POST.get('ticket_id')
        
        if ticket_id:

            return redirect('ticket_detail', ticket_id=ticket_id)
        else:
            messages.error(request, "Please enter a valid Ticket ID")

    return render(request, 'staff_webportal/search_ticket.html')



def ticket_detail_view(request, ticket_id):
    if not check_session(request):
        return redirect('login')

    token = get_token(request)
    client = AccountClient(token)

    response = client.get_ticket(ticket_id=ticket_id) 
    
    if response.status_code != 200:
        messages.error(request, "Ticket not found.")
        return redirect('search_ticket')
        
    ticket_data = response.json()

    if isinstance(ticket_data, list) and ticket_data:
        ticket_data = ticket_data[0]


    if request.method == "POST":
        form = UpdateTicketForm(request.POST)
        if form.is_valid():
            data = {
                "ticket_id": ticket_id, 
                "complaint": form.cleaned_data.get("remarks"), 
                "subject": ticket_data.get("subject"),
            }
            
            update_resp = client.update_ticket(data)
            
            if update_resp.status_code == 200:
                messages.success(request, "Reply posted successfully.")
                return redirect('ticket_detail', ticket_id=ticket_id) 
            else:
                messages.error(request, "Failed to update ticket.")
    else:
        form = UpdateTicketForm()

    context = {
        'form': form, 
        'ticket': ticket_data
    }
    return render(request, 'staff_webportal/ticket_detail.html', context)



def staff_activity_view(request):
    if not check_session(request):
        return redirect('login')

    return render(request, 'staff_webportal/staff_activity.html')




def staff_block_account(request):
    if not check_session(request):
        return redirect('login')
    
    token = get_token(request)
    
    account_client = AccountClient(token)
    
    
    if request.method == 'POST':
        form = StaffBlockAccountForm(request.POST)
        if form.is_valid():
            data = {
                'account_number': form.cleaned_data['account_number'],
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
    if not check_session(request):
        return redirect('login')
        
    token = get_token(request)
    client = BankClient(token)
    
    response = client.get_bank_records()
    
    # Initialize empty lists
    debits = []
    credits = []

    if response.status_code == 200:
        data = response.json()
        # Extract the specific lists based on your API logic
        debits = data.get('debit_data', [])
        credits = data.get('credit_data', [])
    
    context = {
        'debits': debits,
        'credits': credits
    }
    
    return render(request, 'staff_webportal/ledger_logs.html', context)



def bank_transaction_history_view(request):
    """Perhaps for Admins or Auditors"""
    if not check_session(request):
        return redirect('login')
        
    token = get_token(request)
    client = BankClient(token)
    
    response = client.get_transactions()
    transactions = response.json() if response.status_code == 200 else []
    
    return render(request, 'app/bank_transactions.html', {'transactions': transactions})