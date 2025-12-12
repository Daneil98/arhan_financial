from celery import shared_task
from .models import *
from django.core.exceptions import ObjectDoesNotExist
import requests
from django.shortcuts import get_object_or_404
from kombu import Exchange, Queue
from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

headers = {
        'Content-Type': 'application/json',
    }


# Define exchanges for outbound events
from celery import current_app
account_exchange = Exchange("account_service", type="topic")


#CONSUMER TASKS
@shared_task(name="consume.account_service.customer.created", bind=True, acks_late=True)
@transaction.atomic
def consume_customer_created(self, data):   #GOOD
    user_id_value = data.get("id")
    email_value = data.get("email")
    username = data.get("username")
    user, created = User.objects.get_or_create(
        id=user_id_value,
        defaults={
            'username': username, # or whatever unique field you use
            'email': email_value,
            'is_active': True
        }
    )
    Account.objects.get_or_create(
        user_id=user_id_value,
        role = "customer"
    )
    print(f"Created service account for customer {user_id_value}")
    
    
@shared_task(name="consume.account_service.staff.created", bind=True, acks_late=True)
def consume_staff_created(self, data):   #GOOD
    user_id_value = data.get("id")
    email_value = data.get("email")
    username = data.get("username")
    user, created = User.objects.get_or_create(
        id=user_id_value,
        defaults={
            'username': username, # or whatever unique field you use
            'email': email_value,
            'is_active': True
        }
    )
    Account.objects.get_or_create(
        user_id=user_id_value,
        role = "staff"
    )
    print(f"Created service account for staff {user_id_value}")

@shared_task(name="consume.account_service.user.logged_in", bind=True, acks_late=True)
def consume_user_logged_in(self, data):
    user_id_value = data.get("user_id")
    try:
        if Account.objects.filter(user_id=user_id_value).exists():
            print(f"customer {user_id_value} has logged in.")
    except ObjectDoesNotExist:
        print(f"No account found for user {user_id_value}")
        
@shared_task(name="consume.account_service.account.created", bind=True)
def consume_ledger_account_created(self, data, acks_late=True):
    """
    When a new ledger account is created, link it to the user in identity DB.
    """
    user_id_value = data.get("user_id")
    ledger_account_id = data.get("ledger_account_id")

    try:
        profile = Account.objects.get(user_id=user_id_value)
        if profile.ledger_id:
            print(f"[idempotent-skip] User {user_id_value} already linked to ledger {profile.ledger_id}")
            return

        profile.ledger_id = ledger_account_id
        profile.save()

        print(f"Linked user {user_id_value} → ledger account {ledger_account_id}")

    except profile.DoesNotExist:
        print(f"No profile found for user {user_id_value}")     

     
     
# PRODUCER TASKS

def _publish_event(task_self, event_data, routing_key):
    """Internal helper to encapsulate the publishing logic and error handling."""
    
    # Using 'account_exchange' defined above
    exchange = account_exchange
    
    try:
        with current_app.connection() as conn:
            producer = conn.Producer(serializer='json')
            producer.publish(
                event_data,
                exchange=exchange,
                routing_key=routing_key,
                retry=True,
                retry_policy={'max_retries': 5, 'interval_start': 0, 'interval_step': 2}
            )
        print(f"Published event: {routing_key} -> {event_data}")
    except Exception as exc:
        # Retry the task if publishing fails (e.g., broker down)
        raise task_self.retry(exc=exc, countdown=60)
        
@shared_task(name="publish.account_service.account.created", bind=True)
def publish_account_created(self, account_data):
    event_data = {
        "event": "account_service.account.created",
        'id': str(account_data['id']),
        "account_id": str(account_data['external_id']),
        "user_id": str(account_data['user_id']),
        "created_at": account_data['created_at'],
    }
    _publish_event(self, event_data, "account_service.account.created")

@shared_task(name="publish.account_service.SavingsAccount.created", bind=True)
def publish_savingsAccount_created(self, acc_data):
    """
    event_data = {
        "event": "account_service.savings_account.created",
        "user_id": str(acc_data['user_id']),
        "account": str(acc_data['account_number']),
        "balance": str(acc_data['balance']),
        "interest_rate": str(acc_data['interest_rate']),
        "currency": str(acc_data['currency']),
        "active": str(acc_data['active']), # Assuming this field is appropriate for saving account status
        "created_at": acc_data['created_at'],
    }
    """
    event_data = {
        "event": "account_service.savings_account.created",
        "data": acc_data,
    }
    _publish_event(self, event_data, "account_service.savings_account.created")


@shared_task(name="publish.account_service.currentAccount.created", bind=True)
def publish_currentAccount_created(self, acc_data):
    """
    event_data = {
        "event": "account_service.current_account.created",
        "user_id": str(acc_data['user_id']),
        "account": str(acc_data['account_number']),
        "balance": str(acc_data['balance']),
        "interest_rate": str(acc_data['interest_rate']),
        "currency": str(acc_data['currency']),
        "status": str(acc_data['active']), # Assuming this field is appropriate for current account status
        "created_at": acc_data['created_at'],
    }
    """
    event_data = {
        "event": "account_service.current_account.created",
        "data": acc_data,
    }
    _publish_event(self, event_data, "account_service.current_account.created")
    

@shared_task(name="publish.account_service.card.created", bind=True)
def publish_card_created(self, acc_data):
    event_data = {
        "event": "account_service.card.created",
        "data": acc_data,
    }
    _publish_event(self, event_data, "account_service.card.created")


@shared_task(name="publish.account_service.loan.applied", bind=True)
def publish_loan_applied(self, loan_data):
    """
    event_data = {
        "event": "account_service.loan.applied",
        "loan_id": str(loan_data['loan_id']),
        "external_id": str(loan_data['user_id']),
        "amount": str(loan_data['amount']),
        "currency": str(loan_data['currency']),
        "duration": str(loan_data['duration']),
        "loan_status": loan_data['loan_status'],
        "start_date": loan_data['start_date'],
        #"end_date": loan_data.end_date.isoformat(),
    }
    """
    event_data = {
        "event": "account_service.loan.applied",
        "data": loan_data,
    }
    _publish_event(self, event_data, "account_service.loan.applied")
    

@shared_task(name="publish.account_service.loan.updated", bind=True)
def publish_loan_updated(self, loan_data):
    """
    event_data = {
        "event": "account_service.loan.updated",
        "loan_id": str(loan_data['loan_id']),
        "external_id": str(loan_data['user_id']),
        "amount": str(loan_data['amount']),
        "currency": str(loan_data['currency']),
        "duration": str(loan_data['duration']),
        "loan_status": loan_data['loan_status'],
        "start_date": loan_data['start_date'],
        "end_date": loan_data['end_date'],
    }"""
    event_data = {
        "event": "account_service.loan.updated",
        "data": loan_data,
    }
    _publish_event(self, event_data, "account_service.loan.updated")


@shared_task(name="publish.account_service.verify.card", bind=True)
def publish_verify_card(self, card_data):
    event_data = {
        "event": "account_service.verify.card",
        "response": card_data
    }
    _publish_event(self, event_data, "account_service.verify.card")
    
    
@shared_task(name='publish.account_service.get.balance', bind=True)
def publish_get_balance(self, balance):
    event_data = {
        "event": "account_service.get.balance",
        "response": balance
    }
    _publish_event(self, event_data, "account_service.get.balance")
    
    
@shared_task(name="publish.account_service.verify.pin", bind=True)
def publish_verify_pin(self, data):
    """
    Publishes 'account_service.verify.pin' event asynchronously.
    """
    event_data = {
        "event": "account_service.verify.pin",
        "response": data
    }
    
    _publish_event(self, event_data, "account_service.verify.pin")

    
@shared_task(name="publish.account_service.block.card", bind=True)
def publish_block_card(self, data):
    """
    Publishes 'account_service.block.card' event asynchronously.
    """
    event_data = {
        "event": "account_service.block.card",
        "response": data
    }
    
    _publish_event(self, event_data, "account_service.block.card")    

@shared_task(name="publish.account_service.block.account", bind=True)
def publish_block_account(self, data):
    """
    Publishes 'account_service.block.account' event asynchronously.
    """
    event_data = {
        "event": "account_service.block.account",
        "response": data
    }
    
    _publish_event(self, event_data, "account_service.block.account")    
    
    
@shared_task(name="publish.account_service.ticket.created", bind=True)
def publish_ticket_created(self, ticket_data):
    
    #Publishes 'Identity_service.ticket.created' event to RabbitMQ.
    data = {
        "event": "account_service.ticket.created",
        "ticket_data": ticket_data
    }

    _publish_event(self, data, "account_service.ticket.created")
    
@shared_task(name="publish.account_service.ticket.updated", bind=True)
def publish_ticket_updated(self, ticket_data):
    
    #Publishes 'Identity_service.ticket.updated' event to RabbitMQ.
    data = {
        "event": "account_service.ticket.updated",
        "ticket_data": ticket_data
    }
    _publish_event(self, data, "account_service.ticket.updated")

