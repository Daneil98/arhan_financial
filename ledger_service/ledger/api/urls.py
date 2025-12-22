from django.urls import path, include
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


app_name = 'ledger_api'

urlpatterns = [
    path("accounts/", views.create_ledgerAccount.as_view()),
    path("entries/", views.create_ledgerEntry.as_view()),
    path("transactions/", views.create_transaction.as_view()),
    
    path("ledger_logs/", views.BankLogs.as_view()),
    path("transaction_logs/", views.TransactionLogs.as_view()),
]