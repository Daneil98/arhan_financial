#payment/tasks.py
import decimal
from celery import shared_task
from django.db import transaction
from decimal import Decimal
from kombu import Exchange, Queue
from payment.models import *
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .account_service_client import *
from datetime import datetime


User = get_user_model()

headers = {
        'Content-Type': 'application/json',
    }

# Define exchanges for outbound events
from celery import current_app

payment_exchange = Exchange("payment", type="topic")

#CONSUMERS
@shared_task(name="consume.payment.customer.created", bind=True, acks_late=True)
def consume_customer_created(self, data):
    user_id_value = data.get("id")
    email_value = data.get("email")
    username = data.get("username")
    role = data.get("role")
    user, created = User.objects.get_or_create(
        id=user_id_value,
        defaults={
            'username': username, # or whatever unique field you use
            'email': email_value,
            'is_active': True
        }
    )
    print(f"Created service account for customer {user_id_value}")
    
@shared_task(name="consume.payment.staff.created", bind=True, acks_late=True)
def consume_customer_created(self, data):
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
    print(f"Created service account for staff {user_id_value}")


@shared_task(name="consume.payment.user.logged_in", bind=True, acks_late=True)
def consume_user_logged_in(self, data):
    user_id_value = data.get("user_id")
    try:
        if PaymentAccount.objects.filter(user_id=user_id_value).exists():
            print(f"customer {user_id_value} has logged in.")
    except ObjectDoesNotExist:
        print(f"No account found for user {user_id_value}")

@shared_task(name="consume.payment.BankAccount.created", bind=True, acks_late=True)
def consume_BankAccount_created(self, data):
    user_id_value = data.get("user_id")
    currency = data.get("currency")
    account_number = data.get("account_number")
    if PaymentAccount.objects.filter(account_number=account_number).exists():
        print(f"customer {user_id_value} already has an account.")
    else:
        PaymentAccount.objects.create(user_id=user_id_value, currency=currency,
                                     account_number=account_number)


#PRODUCERS
def publish_event(task_self, event_data, routing_key):
    """Internal helper to encapsulate the publishing logic and error handling."""
    
    # Using 'account_exchange' defined above
    exchange = payment_exchange
    
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



@shared_task(name='consume.payment.loan.updated', bind=True)
def consume_loan_updated(self, data):
    print(f"[⚙️] Processing Loan data: {data}")

    # Extract Data (Safely)
    user_id = data["user_id"]
    loan_id = data["loan_id"]
    amount = data["amount"]
    duration = data["duration"]
    interest_rate = data["interest_rate"] 
    loan_status = data["status"]
    payer_id = 1
    payee_id = data['payee_account_id']

    
    if loan_status != 'approved':
        print("Loan has not been Approved")
        return 
    
    PaymentRequest.objects.create(
        payer_account_id = 1,
        payee_account_id = payee_id,
        amount=data['amount'],
        currency = "NGN",
        status = "PENDING",
        payment_type = "INTERNAL TRANSFER",
        # Store the task ID if needed later
    )
    
    #1. DEBIT THE BANKPOOL
    debit_result = debit_bank(user_id, amount)
    
    if debit_result.get("status") != "success":
        print(f"[❌] Debit Failed: {debit_result}")
        PaymentRequest.objects.filter(payer_account_id=payer_id, amount=amount, 
                                    status="PENDING").update(status="FAILED")
        return
    
    #2. CREDIT THE BORROWER
    credit_result = credit_account(user_id, payee_id, amount) 
    
    if credit_result.get("status") != "success":
        print(f"[❌] Credit Failed (Need Refund Logic): {credit_result}")
        # Ideally trigger a refund task here
        PaymentRequest.objects.filter(payer_account_id=1, amount=amount, status="PENDING").update(status="FAILED_NEEDS_REFUND")
        return
    
    
    # Update DB
    payment = PaymentRequest.objects.filter(payer_account_id=payer_id,
                                        amount=amount, status="PENDING").first()
    if payment:
        payment.status = "COMPLETED"
        payment.metadata = {'TYPE': 'LOAN DISBURSEMENT'}
        payment.processed_at = datetime.now()
        payment.save()       
        

    # Publish Event
    event_data = {
        "event": "payment.loan.updated",
        "payer_id": payer_id,
        "payee_id": user_id,
        "amount": amount,
        "reference": str(payment.id) if payment else "unknown",
        "currency": "NGN",
        "loan_status": loan_status,
        "loan_id": loan_id,
    }
        # 3. SUCCESS - UPDATE DB & PUBLISH
    print(f"[✅] Transfer Successful")
    
    # Assuming _publish_event is defined in this file
    publish_event(self, event_data, "payment.loan.updated")


@shared_task(name="publish.payment.loan.repayment", bind=True)
def loan_repayment(self, data):
    # Extract Data (Safely)
    user_id = data["user_id"]
    interest_rate = data["interest_rate"] 
    amount_to_repay = data["amount_to_repay"]
    loan_status = data["status"]
    payer_id = data['payer_account_id']
    payee_id = 1
    

    if loan_status != 'Approved':
        print("Loan has not been Approved")
        return 
    
    PaymentRequest.objects.create(
        payer_account_id = 1,
        payee_account_id = payee_id,
        amount=data['amount'],
        currency = "NGN",
        status = "PENDING",
        payment_type = "INTERNAL TRANSFER",
        # Store the task ID if needed later
    )
    
    #1. DEBIT THE BANKPOOL
    debit_result = debit_account(user_id, payer_id, amount_to_repay)
    
    if debit_result.get("status") != "success":
        print(f"[❌] Debit Failed: {debit_result}")
        PaymentRequest.objects.filter(payer_account_id=payer_id, amount=amount_to_repay, 
                                    status="PENDING").update(status="FAILED")
        return
    
    #2. CREDIT THE BORROWER
    credit_result = credit_bank(user_id, amount_to_repay) 
    
    if credit_result.get("status") != "success":
        print(f"[❌] Credit Failed (Need Refund Logic): {credit_result}")
        # Ideally trigger a refund task here
        PaymentRequest.objects.filter(payer_account_id=1, amount=amount_to_repay, status="PENDING").update(status="FAILED_NEEDS_REFUND")
        return
    
    
    # Update DB
    payment = PaymentRequest.objects.filter(payer_account_id=payer_id,
                                        amount=amount_to_repay, status="PENDING").first()
    if payment:
        payment.status = "COMPLETED"
        payment.metadata = {'TYPE': 'LOAN REPAYMENT'}
        payment.processed_at = datetime.now()
        payment.save()       
        

    # Publish Event
    event_data = {
        "event": "payment.payment.completed",
        "payer_user_id": user_id,
        "payee_user_id": payee_id,
        "amount": amount_to_repay,
        "reference": str(payment.id) if payment else "unknown",
        "currency": "NGN",
    }
    
    # Assuming _publish_event is defined in this file
    publish_event(self, event_data, "payment.loan.repayment")



@shared_task(name="publish.payment.payment.completed", bind=True)
def process_internal_transfer(self, data):
    print(f"[⚙️] Processing Transfer: {data}")
    
    # Extract Data (Safely)
    user_id = data["user_id"]
    payer_id = data["payer_account_id"]
    payee_id = data["payee_account_id"]
    amount = data["amount"]
    pin = data["pin"]
    payment_id = data['payment_id'] 
    
    # 1. VERIFY PIN
    # We call the helper API function, not local DB
    pin_response = verify_pin(user_id, payer_id, pin)
    
    if not pin_response.get("data", {}).get("validity", False):
        print(f"[⛔] Invalid PIN for {payer_id}")
        # Update your local PaymentRequest model to FAILED
        PaymentRequest.objects.filter(payer_account_id=payer_id, amount=amount, 
                                      status="PENDING").update(status="FAILED")
        return

    # 2. DEBIT PAYER (API CALL)
    debit_result = debit_account(user_id, payer_id, amount)
    
    if debit_result.get("status") != "success":
        print(f"[❌] Debit Failed: {debit_result}")
        PaymentRequest.objects.filter(payer_account_id=payer_id, amount=amount, 
                                    status="PENDING").update(status="FAILED")
        return

    # 3. CREDIT PAYEE (API CALL)
    # Note: In a real app, if this fails, you must REVERSE the debit (Refund).
    credit_result = credit_account(user_id, payee_id, amount) 
    
    if credit_result.get("status") != "success":
        print(f"[❌] Credit Failed (Need Refund Logic): {credit_result}")
        # Ideally a refund task here, but no need since atomic transaction
        PaymentRequest.objects.filter(payer_account_id=payer_id, amount=amount, status="PENDING").update(status="FAILED_NEEDS_REFUND")
        return

    # 4. SUCCESS - UPDATE DB & PUBLISH
    payer = get_object_or_404(PaymentAccount, account_number=data['payer_account_id'])
    payee = get_object_or_404(PaymentAccount, account_number=data['payee_account_id'])
    
    
    # Update only the Transaction Status locally
    try:
        payment = PaymentRequest.objects.select_for_update().get(id=payment_id)
        payment.status = "COMPLETED"
        payment.metadata = {'TYPE': 'USER INTERNAL TRANSFER'}
        payment.processed_at = datetime.now()
        payment.save() 
    except:
        # If not found, Retry in 1 second.
        # This handles the race condition perfectly.
        print(f"[⏳] Payment record not found yet. Retrying...")
        raise self.retry(countdown=1, max_retries=5)

    # Publish Event
    event_data = {
        "event": "payment.payment.completed",
        "payer_user_id": payer.user_id,
        "payee_user_id": payee.user_id,
        "amount": amount,
        "reference": str(payment.id) ,
        "currency": "NGN",
        "initiated_at_ts": data.get("initiated_at_ts") 
    }
    
    # Assuming _publish_event is defined in this file
    publish_event(self, event_data, "payment.payment.completed")
    print(f"[✅] Transfer Successful")
    

@shared_task(name="publish.payment.card.charge", bind=True)
def initiate_card_payment(self, data):
    print(f"[🚀] TASK STARTED. Processing for User ID: {data.get('user_id')}")
    # Extract Data (Safely)
    user_id = data["user_id"]
    payer_id = data["payer_account_id"]
    payee_id = data["payee_account_id"]
    card_number = data["card_number"]
    cvv = data["cvv"]
    amount = data["amount"]
    PIN = data["PIN"]
    payment_id = data['payment_id']
    
    # Ideally, the frontend/view passed this in 'data'. If not, we hope verify_card returns it.
    #payer_id = data.get("payer_account_id") 

    # Step 1: Verify card details and pin
    card_response = verify_card(user_id, card_number, cvv, PIN)
    
    # If verify_card returns the account ID, we ensure we have it
    card_data = card_response.get("data", {})
    
    if not card_data.get("validity", False):
        print(f"[⛔] Invalid card details")
        PaymentRequest.objects.filter(payer_account_id=payer_id, amount=amount, 
                                        status="PENDING").update(status="FAILED")
        return # 🛑 CRITICAL FIX: You MUST stop here if card is invalid!

    # 2. DEBIT PAYER (API CALL)
    # The API call actually moves the money in the Account Service
    debit_result = debit_account(user_id, payer_id, amount)
    
    if debit_result.get("status") != "success":
        print(f"[❌] Debit Failed: {debit_result}")
        PaymentRequest.objects.filter(payer_account_id=payer_id, amount=amount, 
                                    status="PENDING").update(status="FAILED")                                               
        return


    # 3. CREDIT PAYEE (API CALL)
    credit_result = credit_account(user_id, payee_id, amount)
    
    if credit_result.get("status") != "success":
        print(f"[❌] Credit Failed (Need Refund Logic): {credit_result}")
        PaymentRequest.objects.filter(payer_account_id=payer_id, amount=amount, 
                                    status="PENDING").update(status="FAILED_NEEDS_REFUND")
        # In a real app, you would queue a 'refund_payer' task here
        return

    # 4. SUCCESS - UPDATE DB & PUBLISH
    # We fetch these just to get User IDs for the event (Read Only)
    try:
        payer = PaymentAccount.objects.get(account_number=payer_id)
        payee = PaymentAccount.objects.get(account_number=payee_id)
    except PaymentAccount.DoesNotExist:
        print("[⚠️] Accounts not found locally, skipping event enrichment")
        return

    # Update only the Transaction Status locally
    try:
        payment = PaymentRequest.objects.select_for_update().get(id=payment_id)
        payment.status = "COMPLETED"
        payment.payer_account_id = payer_id # Ensure this is set
        payment.metadata = {'TYPE': 'USER CARD PAYMENT'}
        payment.processed_at = datetime.now()    
        payment.save()
        
    except:
        # If not found, Retry in 1 second.
        # This handles the race condition perfectly.
        print(f"[⏳] Payment record not found yet. Retrying...")
        raise self.retry(countdown=1, max_retries=5)
    

    # Publish Event
    event_data = {
        "event": "payment.card.charge",
        # Removed the empty string syntax error here
        "payer_user_id": payer.user_id,
        "payee_user_id": payee.user_id,
        "amount": amount,
        "reference": str(payment.id) if payment else "unknown",
        "currency": "NGN",
        "initiated_at_ts": data.get("initiated_at_ts")
    }
    
    print(event_data)
    publish_event(self, event_data, "payment.card.charge")
