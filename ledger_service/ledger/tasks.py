# ledger/tasks.py
import decimal
from celery import shared_task
from django.db import transaction
from django.db.models import Q
from kombu import Exchange, Queue
from ledger.models import *
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from ledger.models import *
import time


User = get_user_model()

headers = {
        'Content-Type': 'application/json',
    }

# Define exchanges for outbound events
from celery import current_app
ledger_exchange = Exchange("ledger", type="topic")


#CONSUMERS
@shared_task(name="consume.ledger.customer.created", bind=True, acks_late=True)
@transaction.atomic
def consume_customer_created(self, data):
    user_id_value = data.get("id")
    email_value = data.get("email")
    username = data.get("username")
    first_name = data.get("first_name", "")
    last_name = data.get("last_name", "")
    user, created = User.objects.get_or_create(
        id=user_id_value,
        defaults={
            'username': username, # or whatever unique field you use
            'email': email_value,
            'is_active': True,
            'first_name': first_name,
            'last_name': last_name,
        }
    )

    print(f"Created service account for customer {user_id_value}")


@shared_task(name="consume.ledger.user.logged_in", bind=True, acks_late=True)
def consume_user_logged_in(self, data):
    user_id_value = data.get("user_id")
    try:
        if LedgerAccount.objects.filter(user_id=user_id_value).exists():
            print(f"customer {user_id_value} has logged in.")
    except ObjectDoesNotExist:
        print(f"No account found for user {user_id_value}")


@shared_task(name="consume.ledger.BankAccount.created", bind=True, acks_late=True)
def consume_BankAccount_created(self, data):
    user_id_value = data.get("user_id")
    currency = data.get("currency")
    account_number = data.get("account_number")
    if LedgerAccount.objects.filter(Q (user_id=user_id_value) & Q(account_number=account_number)).exists():
        print(f"customer {user_id_value} already has an account.")
    else:
        LedgerAccount.objects.create(user_id=user_id_value, currency=currency, account_number=account_number)
        
        
@shared_task(name="consume.ledger.loan.updated", bind=True, acks_late=True)
def consume_loan_updated(self, data):
    """
    Handles loan.updated events.

    Expected payload:
    {
        "loan_id": "...",
        "external_id": "...",   # customer ledger account UUID
        "amount": "5000.00",
        "currency": "USD",
        "status": "Approved",
        "user_id": "...",
        "loan_status": "Approved"
    }
    """

    # 1. REQUIRED FIELDS VALIDATION
    required = ["payee_id", "amount", "currency",]
    for field in required:
        if field not in data:
            print(f"[loan_updated] Missing required field: {field}")
            return

    payer_id = data["payer_id"]
    loan_id = data["loan_id"]
    payee_id = data["payee_id"]
    amount = decimal.Decimal(data["amount"])
    currency = data["currency"]
    loan_status = data.get("loan_status")

    # Only process accounting when loan is approved
    if loan_status != "Approved":
        print(f"[loan_updated] Loan {loan_id} not approved — skipping ledger posting.")
        return

    # 3. LEDGER POSTING — DOUBLE-ENTRY MANDATORY
    txn_ref = f"loan_disbursement_{loan_id}"

    with transaction.atomic():
        # Idempotency: do not duplicate postings
        txn, created = Transaction.objects.get_or_create(
            reference=txn_ref,
            user_id = payee_id,
            defaults={"description": f"Loan disbursement for loan {loan_id}"}
        )

        if not created:
            print(f"[idempotent-skip] Transaction {txn_ref} already exists.")
            return

        # Lookup customer loan ledger account
        try:
            loan_account = LedgerAccount.objects.get(
                user_id=payee_id
            )
        except LedgerAccount.DoesNotExist:
            print(f"[loan_updated] LedgerAccount missing for user_id={payee_id}")
            return
        
        payer = LedgerAccount.objects.get(user_id=payer_id)
        payee = LedgerAccount.objects.get(user_id=payee_id)


        # DOUBLE ENTRY POSTING
        # Loan Account increases → DEBIT
        LedgerEntry.objects.create(
            transaction=txn,
            user_id=payee_id,
            ledger_account=payee,
            entry_type="DEBIT",
            amount=amount,
            currency=currency,
        )
        
        # Internal Reserve decreases → CREDIT
        LedgerEntry.objects.create(
            transaction=txn,
            user_id=payer_id,
            ledger_account=payer,
            entry_type="CREDIT",
            amount=amount,
            currency=currency,
        )

    print(f"[loan_updated] Ledger transaction {txn_ref} recorded successfully.")


@shared_task(name="consume.ledger.payment.completed", bind=True, acks_late=True)
def consume_payment_completed(self, data):
    """
    Consumer task: handles payment.completed events.
    """

    ref = data.get("reference")
    payer_user_id = data.get("payer_user_id")
    payee_user_id = data.get("payee_user_id")
    #payer_id = data.get("payer_account_id")
    #payee_id = data.get("payee_account_id")
    amount = decimal.Decimal(data.get("amount"))
    currency = data.get("currency")

    with transaction.atomic():
        txn, created = Transaction.objects.get_or_create(
            reference=ref,
            user_id = payer_user_id,
            description="Payment completed via event"
        )
        if not created:
            print(f"[idempotent-skip] Transaction {ref} already exists.")
            return

        payer = LedgerAccount.objects.get(user_id=payer_user_id)
        payee = LedgerAccount.objects.get(user_id=payee_user_id)

        LedgerEntry.objects.create(
            user_id = payer_user_id,
            transaction=txn,
            ledger_account=payer,
            entry_type="DEBIT",
            amount=amount,
            currency=currency,
        )
        LedgerEntry.objects.create(
            transaction=txn,
            user_id=payee_user_id,
            ledger_account=payee,
            entry_type="CREDIT",
            amount=amount,
            currency=currency,
        )
        # 2. STOP THE CLOCK
        end_time = time.time()
        
        # 3. CALCULATE DURATION
        start_time = data.get("initiated_at_ts")
        
        if start_time:
            # Calculate difference
            duration = end_time - float(start_time)
            
            # Convert to milliseconds for easier reading
            duration_ms = duration * 1000
            
            print(f"==========================================")
            print(f"[⏱️] END-TO-END TRANSACTION TIME: {duration_ms:.2f} ms")
            print(f"==========================================")
        else:
            print("[⚠️] No timestamp found in event data")

        print(f"Recorded ledger transaction {ref} successfully.")


@shared_task(name="consume.ledger.card.charge", bind=True, acks_late=True)
def consume_card_charge(self, data):
    """
    Consumer task: handles card.charge events.
    """
    ref = data.get("reference")
    payer_user_id = data.get("payer_user_id")
    payee_user_id = data.get("payee_user_id")
    #payer_id = data.get("payer_account_id")
    #payee_id = data.get("payee_account_id")
    amount = decimal.Decimal(data.get("amount"))
    currency = data.get("currency")

    with transaction.atomic():
        txn, created = Transaction.objects.get_or_create(
            reference=ref,
            user_id = payer_user_id,
            description="Payment completed via event"
        )
        if not created:
            print(f"[idempotent-skip] Transaction {ref} already exists.")
            return

        payer = LedgerAccount.objects.get(user_id=payer_user_id)
        payee = LedgerAccount.objects.get(user_id=payee_user_id)

        LedgerEntry.objects.create(
            user_id = payer_user_id,
            transaction=txn,
            ledger_account=payer,
            entry_type="DEBIT",
            amount=amount,
            currency=currency,
        )
        LedgerEntry.objects.create(
            transaction=txn,
            user_id=payee_user_id,
            ledger_account=payee,
            entry_type="CREDIT",
            amount=amount,
            currency=currency,
        )

    print(f"Recorded ledger transaction {ref} successfully.")




#PRODUCERS
def _publish_event(task_self, event_data, routing_key):
    """Internal helper to encapsulate the publishing logic and error handling."""
    
    # Using 'account_exchange' defined above
    exchange = ledger_exchange
    
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
        raise task_self.retry(exc=exc)


@shared_task(name="publish.ledger.account.created", bind=True)
def publish_ledgerAccount_created(self, account_data):
    event_data = {
        "event": "ledger.account.created",
        "id": str(account_data.user_id),
        "ledger_account_id": account_data.ledger_id,
        "created_at": account_data.created_at.isoformat(),
    }
    _publish_event(self, event_data, routing_key="ledger.account.created")
    
@shared_task(name="publish.ledger.entry.created", bind=True)
def publish_ledgerEntry_created(self, data):
    event_data = {
        "event": "ledger.entry.created",
        "id": str(data.id),
        "transaction": str(data.txn),
        "ledger_account": str(data.payer_account),
        "entry_type": str(data.entry_type),
        "amount": str(data.amount),
        "currency": str(data.currency),
        "created_at": data.created_at.isoformat(),
    }
    _publish_event(self, event_data, "ledger.entry.created")
    

@shared_task(name="publish.ledger.transaction.created", bind=True)
def publish_transaction_created(self, data):
    event_data = {
        "event": "ledger.transaction.created",
        "id": str(data.id),
        "reference": str(data.reference),
        "description": str(data.description),
        "created_at": data.created_at.isoformat(),
        "is_reconciled": str(data.is_reconciled)
    }
    _publish_event(self, event_data, "ledger.transaction.created")
    