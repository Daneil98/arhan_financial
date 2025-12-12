from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from ledger.tasks import *

User = get_user_model()

@receiver(post_save, sender=User)
def legderAccount_created_handler(sender, instance, created, **kwargs):
    if created:
        account_data = {
            "event": "ledger.ledgerAccount.created",
            "id": str(instance.id),
            "external_account_id": instance.external_account_id,
            "created_at": instance.date_joined.isoformat(),
        }
        publish_ledgerAccount_created.delay(account_data)
        

@receiver(post_save, sender=User)
def transaction_created_handler(sender, data, **kwargs):
    if not kwargs.get('created', False):
        transaction_data = {
            "event": "arhan_financial.transaction.created",
            "id": str(data.id),
            "reference": str(data.reference),
            "description": str(data.description),
            "created_at": data.created_at.isoformat(),
            "is_reconciled": str(data.is_reconciled)
        }
        publish_transaction_created.delay(transaction_data)
        

@receiver(post_save, sender=User)
def ledgerEntry_created_handler(sender, data, created, **kwargs):
    if created:
        entry_data = {
            "id": str(data.id),
            "transaction": str(data.txn),
            "ledger_account": str(data.payer_account),
            "entry_type": str(data.entry_type),
            "amount": str(data.amount),
            "currency": str(data.currency),
            "created_at": data.created_at.isoformat(),
        }
        publish_ledgerEntry_created.delay(entry_data)   

