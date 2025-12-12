import os

from celery import Celery, bootsteps
from .settings import CELERY_BROKER_URL
from kombu import Exchange, Queue, Consumer

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'arhan_financial.settings')

app = Celery('Identity_service', broker=CELERY_BROKER_URL)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Exchanges
identity_exchange = Exchange("Identity_service", type="topic", durable=True)
payment_exchange = Exchange("payment", type="topic")
ledger_exchange = Exchange("ledger_service", type="topic")
account_exchange = Exchange("account_service", type="topic")

app.conf.task_queues = [
    #Inbound Events
    Queue('ledger.account.created', ledger_exchange, routing_key='account.created'),
    Queue('Identity_service.internal', durable=True),
    #Outbound Events
    Queue('Identity_service.customer.created', identity_exchange, routing_key='Identity_service.customer.created'),
    Queue('Identity_service.staff.created', identity_exchange, routing_key='Identity_service.staff.created'),
    Queue('Identity_service.user.details', identity_exchange, routing_key='Identity_service.user.details'),
    Queue('Identity_service.user.logged_in', identity_exchange, routing_key='Identity_service.user.logged_in'),
    Queue('Identity_service.loan.updated', identity_exchange, routing_key='Identity_service.loan.updated'),
]


app.conf.task_routes = {
    #Outbound publisher tasks
    'publish.Identity_service.*': {
        'queue': 'Identity_service.internal',
    },
    
    'publish.Identity_service.customer.created': {'queue': 'Identity_service.customer.created',
                                                  'routing_key': 'Identity_service.customer.created'},
    'publish.Identity_service.customer.created': {'queue': 'Identity_service.customer.created',
                                                  'routing_key': 'Identity_service.customer.created'},
    'publish.Identity_service.user.logged_in': {'queue': 'Identity_service.user.logged_in',
                                                'routing_key': 'Identity_service.user.logged_in'},

    
    #Inbound consumer tasks
    'consume.ledger.account.created': {'queue': 'Identity_service.incoming.ledger_events'},
}



# B. The "Catch-All" Event Queue
# Listens to "Identity_service.#" -> Everything starting with Identity_service.
event_router_queue = Queue(
    name='Identity_service.incoming.Identity_events', 
    exchange=identity_exchange, 
    routing_key='ledger.#', # <--- WILDCARD IS KEY HERE
    durable=True
)


class EventRouter(bootsteps.ConsumerStep):
    def get_consumers(self, channel):
        return [Consumer(channel,
                         queues=[event_router_queue],
                         callbacks=[self.route_message],
                         accept=['json'])]

    def route_message(self, body, message):
        routing_key = message.delivery_info['routing_key']
        print(f"[📥] Router received key: {routing_key}")
        
        # --- FIX STARTS HERE ---
        task_data = {}
        
        # Case A: Body is a Dictionary (Normal behavior)
        if isinstance(body, dict):
            task_data = body.get('data', {})
            
        # Case B: Body is a List (Handling the error)
        # This handles cases where data was sent as [arg1, arg2]
        elif isinstance(body, list):
            print(f" Received List instead of Dict: {body}")
            if len(body) > 0 and isinstance(body[0], dict):
                # Assume the first item is the data we want
                task_data = body[0]
            else:
                # Fallback: wrap the whole list so we don't lose data
                task_data = {'raw_list': body}
        # --- FIX ENDS HERE ---

        # THE DISPATCHER MAP
        event_map = {
            'ledger.account.created': 'consume.Identity_service.incoming.ledger_events',
        }

        if routing_key in event_map:
            task_name = event_map[routing_key]
            
            # Send to internal queue
            app.send_task(task_name, args=[task_data], queue='Identity_service.internal')
            print(f"   ↳ Routed to task: {task_name}")
        else:
            print(f"   No task mapped for {routing_key}. Ignoring.")

        # Always ack so the bad message doesn't crash the worker again
        message.ack()
        
app.steps['consumer'].add(EventRouter)

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')