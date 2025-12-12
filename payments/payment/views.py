from django.shortcuts import render
from .models import PaymentRequest
from .tasks import publish_payment_completed

# Create your views here.

def complete_payment(payment: PaymentRequest):
    payment.status = "SUCCESS"
    payment.save()

    publish_payment_completed({
        "event": "payment.completed",
        "reference": payment.reference,
        "payer_account_id": str(payment.payer_account_id),
        "payee_account_id": str(payment.payee_account_id),
        "amount": str(payment.amount),
        "currency": payment.currency,
    })