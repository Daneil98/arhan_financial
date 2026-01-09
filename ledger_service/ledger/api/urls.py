from django.urls import path, include
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


app_name = 'ledger_api'

urlpatterns = [
    path("accounts/", views.create_ledgerAccount.as_view()),
    path("transactions/", views.create_transaction.as_view(), name='transactions'),
    
    path("ledger_logs/", views.BankLogs.as_view(), name='ledger_logs'),
]