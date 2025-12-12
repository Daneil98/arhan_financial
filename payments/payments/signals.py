from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from payment.tasks import *

User = get_user_model()


@receiver(pre_save, sender=PaymentRequest)
def set_payment_reference(sender, instance, **kwargs):
    if not instance.reference:
        instance.reference = uuid.uuid4().hex
        
        
@receiver(post_save, sender=PaymentRequest)
def publish_payment_event(sender, instance, created, **kwargs):
    if created and instance.status == "COMPLETED":
        publish_event("payment.payment.completed", {
            "reference": str(instance.reference),
            "payer_account_id": str(instance.payer_account.id),
            "payee_account_id": str(instance.payee_account.id),
            "amount": str(instance.amount),
            "currency": instance.currency,
        })