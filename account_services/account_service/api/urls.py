from django.urls import path, include
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


app_name = 'account_service_api'

urlpatterns = [
    #path('token/', TokenObtainPairView.as_view(), name='token'),        #Good
    #path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),       #Good
    
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),                        #Good
    path('create_BankAccount/', views.CreateBankAccount.as_view(), name='create_BankAccount'),                        #Good
    
    path('loan_apply/', views.CreateLoanApplication.as_view(), name='loan_apply'),    #Good
    path('loan_operations/', views.GetAndUpdateLoan.as_view(), name='loan_operations'),    #Good
    path('loan_detail/', views.LoanDetailView.as_view(), name='loan_detail'),                      #Good
    path('get_pendingloans/', views.GetPendingLoans.as_view(), name='get_pendingloans'),
    path('bankpool_details/', views.BankPoolDetails.as_view(), name='bankpool_details'),                      #Good
    
    path('BankAccountDetails/', views.BankAccountDetails.as_view(), name='BankAccountDetails'),
    
    path('create_card/', views.CreateCard.as_view(), name='create_card'),                 #Good
    path('verify_card/', views.VerifyCard.as_view(), name='verify_card'),                 #Good
    path('card_details/', views.CardDetails.as_view(), name='card_details'),
    #path('verify_pin/', views.VerifyCardPin.as_view(), name='verify_pin'),                    #Good
    path('verify_AccountPin/', views.VerifyAccountPin.as_view(), name='verify_AccountPin'),  #Good
    
    path('block_account/', views.BlockAccount.as_view(), name='block_account'),         #Good
    path('staff_block_account/', views.StaffBlockAccount.as_view(), name='staff_block_account'),         #Good
    path('block_card/', views.BlockCard.as_view(), name='block_card'),                 #Good
    path('get_balance/', views.GetBalance.as_view(), name='get_balance'),              #Good
    
    path('create_ticket/', views.CreateTicket.as_view(), name='create_ticket'),              #Good
    path('fetch_update_ticket/', views.GetAndUpdateTicket.as_view(), name='fetch_update_ticket'),              #Good
    path('get_tickets/', views.GetTickets.as_view(), name='get_tickets'),              #Good
    path('get_pendingtickets/', views.GetPendingTickets.as_view(), name = 'get_pendingtickets'),
    
    path('debit/', views.DebitAccount.as_view(), name='debit'),
    path('credit/', views.CreditAccount.as_view(), name='credit'),
    path('debit_bank/', views.DebitBankPool.as_view(), name='debit_bank'),
    path('credit_bank/', views.CreditBankPool.as_view(), name='credit_bank')
]