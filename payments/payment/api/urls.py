from django.urls import path, include
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


app_name = 'payment_api'


urlpatterns = [
    
    path('internal_transfer/', views.InternalTransferAPIView.as_view(), name='internal_transfer'),      #Good
    path('card_payment/', views.CardPaymentAPIView.as_view(), name='card_payment'),               #Goo
    path('external_bank_transfer/', views.ExternalBankTransferAPIView.as_view()),    #Good

#    path('debit_account/', views.debit_account),                   #Good    
#    path('credit_account/', views.credit_account),                 #Good
    #path('internal_transfer/', views.internal_transfer),           #Good
]