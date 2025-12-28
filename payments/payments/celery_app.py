import os

from celery import Celery, bootsteps
from .settings import CELERY_BROKER_URL
from kombu import Exchange, Queue, Consumer

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payments.settings')

app = Celery('tasks', broker=CELERY_BROKER_URL)

from celery import current_app

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Exchanges
account_exchange = Exchange("account_service", type="topic", durable=True)
payment_exchange = Exchange("payment", type="topic", durable=True)
ledger_exchange = Exchange("ledger_service", type="topic")
identity_exchange = Exchange("Identity_service", type="topic", durable=True)


#PRODUCERS & CONSUMERS
app.conf.task_queues = [
    

    # INBOUND EVENTS

    Queue("account_service.loan.updated",
          account_exchange,
          routing_key="account_service.loan.updated",
          durable=True
    ),

    Queue(
        name='Identity_service.customer.created',  # <--- Name A
        exchange=identity_exchange,
        routing_key='Identity_service.customer.created',            # <--- MUST match Producer's key exactly
        durable=True
    ),
    
    Queue(
        name='Identity_service.staff.created',  # <--- Name A
        exchange=identity_exchange,
        routing_key='Identity_service.staff.created',            # <--- MUST match Producer's key exactly
        durable=True
    ),
    
    Queue(
        name='Identity_service.user.logged_in',  # <--- Name A
        exchange=identity_exchange,
        routing_key='Identity_service.user.logged_in',            # <--- MUST match Producer's key exactly
        durable=True
    ),
    
    # OUTBOUND (for other services to listen to)
    Queue("payment.payment.completed", payment_exchange, 
          routing_key="payment.payment.completed", durable=True),
    
    Queue("payment.card.charge", payment_exchange, 
          routing_key="payment.card.charge", durable=True),
    
    Queue("payment.loan.updated", payment_exchange, 
          routing_key="payment.loan.updated", durable=True),
    
    Queue("payment.loan.repayment", payment_exchange, 
          routing_key="payment.loan.repayment", durable=True),
]

app.conf.task_routes = {
    # Outbound publisher tasks
    
    "publish.payment.payment.completed": {
        'queue': 'payment.internal',
        "routing_key": "payment.payment.completed"
    },
    "publish.payment.card.charge": {
        "queue": "payment.card.charge",
        "routing_key": "payment.card.charge"
    },
    "publish.payment.bank.transfer": {
        "queue": "payment.bank.transfer",
        "routing_key": "payment.bank.transfer"    
    },
    
    "publish.payment.loan.updated": {
        "queue": 'payment.loan.updated',
        "routing_key": "payment.loan.updated"
    },
    
    "publish.payment.loan.repayment": {
        "queue": 'payment.loan.repayment',
        "routing_key": "payment.loan.repayment"
    },

    # Consumers
    'consume.payment.*': {'queue': 'payment.internal'},
    

    # Inbound consumer tasks
#    "consume.payment.completed": {
#        "queue": "ledger.inbound.payment.completed",
#    },
    
#    "consume.payment.customer.created": {
##        "queue": "Identity_service.customer.created",
#        "routing_key": "Identity_service.customer.created"
#    },
    
#    "consume.payment.user.logged_in": {
#        "queue": "Identity_service.user.logged_in"
#    },
    
#    "consume.payment.loan.updated": {
#        "queue": "account_service.loan.updated",
#    },
    
}



# B. The "Catch-All" Event Queue
# Listens to "Identity_service.#" -> Everything starting with payment.
event_router_queue2 = Queue(
    name='payment.incoming.Identity_service_events', 
    exchange=identity_exchange, 
    routing_key='Identity_service.#', # <--- WILDCARD IS KEY HERE
    durable=True
)

# Listens to "account_service.#" -> Everything starting with payment.
event_router_queue3 = Queue(
    name='payment.incoming.account_service_events', 
    exchange=account_exchange, 
    routing_key='account_service.#', # <--- WILDCARD IS KEY HERE
    durable=True
)

class EventRouter(bootsteps.ConsumerStep):
    def get_consumers(self, channel):
        return [Consumer(channel,
                         queues=[event_router_queue2,
                                 event_router_queue3],
                         callbacks=[self.route_message],
                         accept=['json'])]


    def route_message(self, body, message):
        routing_key = message.delivery_info['routing_key']
        print(f"[📥] Router received key: {routing_key}")
        
        try:
            # --- IMPROVED EXTRACTION LOGIC ---
            task_data = {}
            
            # Case A: Standard Dictionary
            if isinstance(body, dict):
                task_data = body.get('data', body)
            
            # Case B: List (Handle the [[{data}]] structure)
            elif isinstance(body, list) and len(body) > 0:
                first_item = body[0]
                
                # Check for Double Nesting (List inside a List)
                if isinstance(first_item, list) and len(first_item) > 0:
                    real_payload = first_item[0] # Drill down to the inner dict
                    task_data = real_payload.get('data', real_payload)
                
                # Check for Single Nesting (List of Dicts)
                elif isinstance(first_item, dict):
                    task_data = first_item.get('data', first_item)
                
                else:
                    print(f"⚠️ Unexpected list content: {first_item}")
                    task_data = first_item # Fallback

            # --- ROUTING ---
            event_map = {
                'Identity_service.customer.created': 'consume.payment.customer.created',
                'Identity_service.staff.created': 'consume.payment.staff.created',
                'Identity_service.user.logged_in':   'consume.payment.user.logged_in',
                'account_service.BankAccount.created': 'consume.payment.BankAccount.created',
                'account_service.loan.updated': 'consume.payment.loan.updated',
            }

            if routing_key in event_map:
                task_name = event_map[routing_key]
                print(f"   ⟳ Routing to internal task: {task_name}")
                
                # Send to the specific internal queue
                # ✅ CORRECT
                current_app.send_task(task_name,
                                      args=[task_data],
                                      queue='payment.internal')
                print(f"   ↳ Sent successfully!")
            else:
                print(f"   ⛔ No task mapped for {routing_key}")

        except Exception as e:
            print(f"🔥 CRITICAL ERROR in EventRouter: {e}")
            import traceback
            traceback.print_exc()

        # Always ack to prevent the message from blocking the queue
        message.ack()
        
app.steps['consumer'].add(EventRouter)

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')