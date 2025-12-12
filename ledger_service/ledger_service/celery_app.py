import os

from celery import Celery, bootsteps
from .settings import CELERY_BROKER_URL
from kombu import Exchange, Queue, Consumer

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ledger_service.settings')

app = Celery('ledger', broker=CELERY_BROKER_URL)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

from celery import current_app

# Exchanges
account_exchange = Exchange("account_service", type="topic", durable=True)
payment_exchange = Exchange("payment", type="topic")
ledger_exchange = Exchange("ledger", type="topic", durable=True)
identity_exchange = Exchange("Identity_service", type="topic", durable=True)

#PRODUCERS & CONSUMERS
app.conf.task_queues = [

    # INBOUND EVENTS
    Queue("payment.payment.completed", payment_exchange, routing_key="payment.payment.completed"),

    Queue("payment.loan.updated", payment_exchange, routing_key="payment.loan.updated"),

    Queue("payment.loan.repayment", payment_exchange, routing_key="payment.loan.repayment"),

    
    #Queue("account_service.acccount.created", account_exchange, routing_key="account_service.account.created"),

    Queue(
        name='Identity_service.customer.created',  # <--- Name A
        exchange=identity_exchange,
        routing_key='Identity_service.customer.created',            # <--- MUST match Producer's key exactly
        durable=True
    ),
    Queue(
        name='Identity_service.user.logged_in',  # <--- Name A
        exchange=identity_exchange,
        routing_key='Identity_service.user.logged_in',            # <--- MUST match Producer's key exactly
        durable=True
    ),
    
    Queue(
        name='account_service.SavingsAccount.created',  # <--- Name A
        exchange=account_exchange,
        routing_key='account_service.SavingsAccount.created',            # <--- MUST match Producer's key exactly
        durable=True
    ),
    Queue(
        name='account_service.currentAccount.created',  # <--- Name A
        exchange=account_exchange,
        routing_key='account_service.currentAccount.created',            # <--- MUST match Producer's key exactly
        durable=True
    ),
    
    # OUTBOUND (for other services to listen to)
    Queue("ledger.transaction.created", ledger_exchange, routing_key="ledger.transaction.created"),

    Queue("ledger.entry.created", ledger_exchange, routing_key="ledger.entry.created"),

    Queue("ledger.account.created", ledger_exchange, routing_key="ledger.account.created"),
]

app.conf.task_routes = {
    # Outbound publisher tasks
    
    "publish.ledger.transaction.created": {
        "queue": "ledger.transaction.created",
        "routing_key": "ledger.transaction.created"
    },
    "publish.ledger.entry.created": {
        "queue": "ledger.entry.created",
        "routing_key": "ledger.entry.created"
    },
    "publish.ledger.account.created": {
        "queue": "ledger.account.created",
        "routing_key": "ledger.account.created"
    },


    # Inbound consumer tasks
    'consume.ledger.*': {'queue': 'ledger.internal'},
    
 #   "consume.ledger.customer.created": {
  #      "queue": "Identity_service.customer.created"},
    
 #   "consume.ledger.payment.completed": {
#        "queue": "payment.payment.completed"},
    
#    "consume.ledger.loan.updated": {
#        "queue": "ledger.loan.updated"},
    
#    "consume.ledger.user.logged_in": {
#        "queue": "Identity_service.user.logged_in"},
    
    
}



# B. The "Catch-All" Event Queue
# Listens to "Identity_service.#" -> Everything starting with Identity_service.
event_router_queue1 = Queue(
    name='ledger.incoming.Identity_events', 
    exchange=identity_exchange, 
    routing_key='Identity_service.#', # <--- WILDCARD IS KEY HERE
    durable=True
)

# Listens to "account_service.#" -> Everything starting with account_service.
event_router_queue2 = Queue(
    name='ledger.incoming.account_service_events', 
    exchange=account_exchange, 
    routing_key='account_service.#', # <--- WILDCARD IS KEY HERE
    durable=True
)

# Listens to "payment.#" -> Everything starting with payment.
event_router_queue3 = Queue(
    name='ledger.incoming.payment_events', 
    exchange=payment_exchange, 
    routing_key='payment.#', # <--- WILDCARD IS KEY HERE
    durable=True
)


class EventRouter(bootsteps.ConsumerStep):
    def get_consumers(self, channel):
        return [Consumer(channel,
                         queues=[event_router_queue1, event_router_queue2,
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
                'Identity_service.customer.created': 'consume.ledger.customer.created',
                'Identity_service.user.logged_in':   'consume.ledger.user.logged_in',
                'account_service.SavingsAccount.created': 'consume.ledger.SavingsAccount.created',
                'account_service.currentAccount.created': 'consume.ledger.CurrentAccount.created',
                'payment.payment.completed': 'consume.ledger.payment.completed',
                'payment.card.charge': 'consume.ledger.card.charge',
                'payment.loan.updated': 'consume.ledger.loan.updated',
                'payment.loan.repayment': 'consume.ledger.loan.repayment',
            }

            if routing_key in event_map:
                task_name = event_map[routing_key]
                print(f"   ⟳ Routing to internal task: {task_name}")
                
                # Send to the specific internal queue
                # ✅ CORRECT
                current_app.send_task(task_name, args=[task_data], queue='ledger.internal')
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