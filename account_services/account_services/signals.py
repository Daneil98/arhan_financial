from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from account_service.tasks import *
from account_service.models import Loan, Card, IT_Tickets

@receiver(post_save, sender=SavingsAccount)
def savingsAccount_created_handler(sender, instance, created, **kwargs):

    if created:
        user_data = {
            "event": "account_service.savings.created",
            "user_id": str(instance.id),
            "balance": instance.balance,
            "interest_rate": instance.interest_rate,
            "created_at": instance.date_joined.isoformat(),
        }
        publish_account_created.delay(user_data)
        
@receiver(post_save, sender=CurrentAccount)
def currentAccount_created_handler(sender, instance, created, **kwargs):

    if created:
        user_data = {
            "event": "account_service.current.created",
            "user_id": str(instance.user_id),
            "balance": instance.balance,
            "interest_rate": instance.interest_rate,
            "created_at": instance.date_joined.isoformat(),
        }
        publish_account_created.delay(user_data)
                
                
@receiver(post_save, sender=Loan)
def loan_applied_handler(sender, instance, **kwargs):
    if not kwargs.get('created', False):
        loan_data = {
            "event": "account_service.loan.applied",
            "user_id": str(instance.id),
            "account": str(instance.account),
            "amount": str(instance.amount),
            "duration": str(instance.duration),
            "loan_status": str(instance.loan_status),
            "start_date": instance.start_date.isoformat(),
            #"end_date": instance.end_date,
            
        }
        publish_loan_applied.delay(loan_data)
        
@receiver(post_save, sender=Loan)
def loan_updated_handler(sender, instance, **kwargs):
    if not kwargs.get('updated', False):
        loan_data = {
            "event": "account_service.loan.updated",
            "user_id": str(instance.id),
            "account": str(instance.account),
            "amount": str(instance.amount),
            "duration": str(instance.duration),
            "loan_status": str(instance.loan_status),
            "start_date": instance.start_date.isoformat(),
            "end_date": instance.end_date,
            
        }
        publish_loan_applied.delay(loan_data)

@receiver(post_save, sender=Card)
def card_created_handler(sender, instance, **kwargs):
    if not kwargs.get('created', False):
        loan_data = {
            "event": "account_service.card.created",
            "user_id": str(instance.id),
            "account": str(instance.account),
            "full_name": str(instance.get_full_name()),
            "card_number": instance.card_number,
            "expiration_date": instance.expiration_date,
            "cvv": instance.cvv,
            "created_at": instance.created_at,
        }
        publish_card_created.delay(loan_data)   
        
@receiver(post_save, sender=Card)
def card_verified(sender, instance, **kwargs):
    if not kwargs.get('created', False):
        check = {
            "event": "account_service.verify.card",
            "user_id": str(instance.id),
            "data": str(instance.data)
        }
        publish_verify_card.delay(check)
        

@receiver(post_save, sender=IT_Tickets)
def ticket_created_handler(sender, instance, created, **kwargs):
    if created:
        ticket_data = {
            "event": "Identity_service.ticket.created",
            "user_id": str(instance.id),
            "email": instance.email,
            "full_name": instance.get_full_name(),
            "created_at": instance.date_joined.isoformat(),
        }
        publish_ticket_created.delay(ticket_data)   

@receiver(post_save, sender=IT_Tickets)
def ticket_updated_handler(sender, instance, **kwargs):
    if not kwargs.get('created', False):
        ticket_data = {
            "event": "Identity_service.ticket.updated",
            "user_id": str(instance.id),
            "email": instance.email,
            "full_name": instance.get_full_name(),
            "updated_at": instance.last_login.isoformat() if instance.last_login else None,
        }
        publish_ticket_updated.delay(ticket_data)
