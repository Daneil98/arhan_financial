from django.urls import path
from . import views, views1
from django.contrib.auth import views as auth_views




urlpatterns = [
    path('', views.index, name ='index'),
    path('login/', views.login_view, name='login'),
    path('staff/login/', views1.staff_login_view, name='staff_login'),
    path('staff/logged_out/', views1.logout_view, name='staff_logout'),
    path('logged_out/', views.logout_view, name='logout'),
    
    path('password_change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('staff/dashboard/', views1.staff_dashboard_view, name='staff_dashboard'),

    path('activity/', views.activity_view, name='activity'),
    path('staff/activity/', views1.staff_activity_view, name='staff_activity'),
    path('analytics/', views.analytics_view, name='analytics'),
    
    
    path('customer/register/', views.customer_register_view, name='customer_register'),
    path('staff/register/', views1.staff_register_view, name='staff_register'),

    path('bank/create_account/', views.create_bank_account_view, name='create_bank_account'),
    path('card/request/', views.create_card_view, name='card_request'),
    path('card/view/', views.view_card_view, name='view_cards'),
    path('block/card/', views.block_card_view, name='block_card'),
    path('bank/account/', views.account_detail_view, name='bank_account'),
    path('block/account/', views.block_account_view, name='block_account'),
    path('staff/block/account/', views1.staff_block_account, name='staff_block_account'),
    
    path('loan/apply/', views.loan_apply_view, name='loan_apply'),
    path('loan/detail/', views.loan_detail_view, name='loan_detail'),
    path('loan/search/', views1.loan_search_view, name='loan_search'),
    path('loans/<str:account_number>/', views1.loan_detail_view, name='loan_detail_specific'),

    path('ticket/create/', views.create_ticket_view, name='create_ticket'),  
    path('tickets/search/', views1.search_ticket_view, name='search_ticket'),
    path('tickets/<str:ticket_id>/', views1.ticket_detail_view, name='ticket_detail'),
    
    path('payment/internal_transfer/', views.internal_transfer_view, name='internal_transfer'),
    path('payment/card/', views.card_payment_view, name='card_payment'),  
    path('transactions/', views.transaction_history_view, name='transactions'),
    
    path('bank/ledger_records/', views1.bank_ledger_records_view, name='bank_ledger_records'),
    path('bank/transaction_history/', views1.bank_transaction_history_view, name='bank_transaction_history'),
    
]