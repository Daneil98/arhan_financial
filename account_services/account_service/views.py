from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .decorators import *
from .models import *
from .forms import *
from .generator import *
# Create your views here.

"""@login_required
@customer_required
def dashboard_c(request):
    #username = customer_id_data.username
    #first_name = customer_id_data.first_name
    #last_name = customer_id_data.last_name
    user = request.user
    savings_account = SavingsAccount.objects.filter(id=user).first()
    current_account = CurrentAccount.objects.filter(id=user).first()
    card = Card.objects.filter(id=user).first()
    loan = Loan.objects.filter(external_id=user).first()

    data = {
        'savings_account': savings_account if savings_account else None,
        'current_account': current_account if current_account else None,
        'card': card if card else None,
        'loan': loan if loan else None,
    }          

    return render(request, 'Identity_service/dashboard_c.html', {'data': data})


@login_required
@customer_required
def create_savings_account(request):
    user = request.user
    form = SavingsAccountForm(request.POST)
    
    if request.method == 'POST':
        if SavingsAccount.objects.filter(id = user):
            messages.error(request, 'You already have a savings account')
        
        initial_data = {'customer': user, 'balance': 0.00, 'interest_rate': 1.50}
        form = SavingsAccountForm(request.POST, initial=initial_data)
        if form.is_valid():
            savings_account = form.save(commit=False)
            savings_account.id = user
            savings_account.save()
            messages.success(request, 'Savings account created successfully.')
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
@customer_required
def create_current_account(request):
    user = request.user
    form = CurrentAccountForm(request.POST)
    
    if request.method == 'POST':
        if CurrentAccount.objects.filter(id = user).exists():
            messages.error(request, 'You already have a savings account')
        
        initial_data = {'customer': user, 'balance': 0.00, 'interest_rate': 1.00}
        form = CurrentAccountForm(request.POST, initial=initial_data)
        if form.is_valid():
            savings_account = form.save(commit=False)
            savings_account.id = user
            savings_account.save()
            messages.success(request, 'Savings account created successfully.')
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
@customer_required
def view_savings_account(request):
    user = request.user
    savings_account = get_object_or_404(SavingsAccount, id=user)
    return render(request, 'Identity_service/view_savings_account.html', {'savings_account': savings_account})  


@login_required
@customer_required
@account_officer_required
def loan_details(request):
    user = request.user
    loan_details = get_object_or_404(Loan, external_id=user)
    return render(request, 'Identity_service/view_loan_details.html', {'loan detaills': loan_details})
    

@login_required
@customer_required
def view_current_account(request):
    user = request.user
    current_account = get_object_or_404(CurrentAccount, id=user)
    return render(request, 'Identity_service/view_current_account.html', {'current_account': current_account})

@login_required
@customer_required
def create_card(request):
    user = request.user
    form = CreateCardForm(request.POST)
    
    if request.method == 'POST':
        if form.is_valid():
            card = form.cleaned_data
            card.customer = user
            card.card_number = generate_card_number()
            card.cvv = generate_cvv()
            card.expiry_date = datetime.date.today() + datetime.timedelta(days=3*365)
            card.card_type = form.cleaned_data['card_type']
            card.save()
            messages.success(request, 'Card created successfully.')
        else:
            messages.error(request, 'Error creating card.')
        
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
@customer_required
def loan_application(request):
    form = LoanApplicationForm(request.POST)
    
    if request.method == 'POST':
        if form.is_valid():
            loan = form.save(commit=False)
            loan.customer = request.user
            loan.loan_status = 'pending'
            loan.save()
            messages.success(request, 'Loan application submitted successfully.')
        else:
            messages.error(request, 'Error submitting loan application.')
    return render(request, 'Identity_service/loan_application.html', {'form': form})


@login_required
@IT_Staff_required
def dashbard_it(request):
    tickets = IT_Tickets.objects.filter(taken=False).all()
    unresolved = IT_Tickets.objects.filter(resolved=False).all()
    
    untaken = tickets.count()
    no_unresolved = unresolved.count()
    return render(request, 'Identity_service/dashboard_it.html',
                  {'tickets': tickets, 'unresolved': unresolved,
                   'untaken': untaken, 'no_unresolved': no_unresolved})
    
    
def handle_ticket(request, id):
    ticket = get_object_or_404(IT_Tickets, id=id)
    
    form = HandlingTicketForm(request='POST' or None)
    
    if request.method == 'POST':
        if form.is_valid():
            ticket.taken = form.cleaned_data['taken']
            ticket.resolved = form.cleaned_data['resolved']
            ticket.remarks = form.cleaned_data['remarks']
            ticket.save()
            messages.success(request, 'Ticket updated successfully.')
        else:
            raise ValueError('Ticket Data Not Valid')
        
    return render(request, 'Identity_register/IT_ticket.html', {'ticket': ticket, 'form': form})
"""
