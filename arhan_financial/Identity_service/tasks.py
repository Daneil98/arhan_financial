from celery import shared_task
from .models import *
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from kombu import Exchange, Queue
from django.contrib.auth import authenticate, login



headers = {
        'Content-Type': 'application/json',
    }

# Define exchanges for outbound events
from celery import current_app

# Define exchanges for outbound events
identity_exchange = Exchange("Identity_service", type="topic", durable=True)


def _publish_event(task_self, event_data, routing_key):
    """Internal helper to encapsulate the publishing logic and error handling."""
    
    # Using 'account_exchange' defined above
    exchange = identity_exchange
    
    try:
        with current_app.connection() as conn:
            producer = conn.Producer(serializer='json')
            producer.publish(
                event_data,
                exchange=identity_exchange,
                routing_key=routing_key,
                retry=True,
                retry_policy={'max_retries': 5, 'interval_start': 0, 'interval_step': 2}
            )
        print(f"Published event: {routing_key} -> {event_data}")
    except Exception as exc:
        # Retry the task if publishing fails (e.g., broker down)
        raise task_self.retry(exc=exc, countdown=60)
        



@shared_task(name="publish.Identity_service.customer.created", bind=True)
def publish_customer_created(self, data):  #GOOD
    """
    Publishes 'Identity_service.customer.created' event to RabbitMQ.
    """
    event_data = {
        "event": "Identity_service.customer.created",
        "data": data
    }
    _publish_event(self, event_data, routing_key="Identity_service.customer.created")
    print(f"Published event: Identity_service.customer.created -> {event_data}")
    

@shared_task(name="publish.Identity_service.staff.created", bind=True)
def publish_staff_created(self, user_data):
    
    #Publishes 'Identity_service.staff.created' event to RabbitMQ.
    
    event_data = {
        "event": "Identity_service.staff.created",
        "data": user_data
    }
    _publish_event(self, event_data, routing_key="Identity_service.staff.created")  
    print(f"Published event: Identity_service.staff.created -> {event_data}")
    
    
 
@shared_task(name="publish.Identity_service.user.logged_in", bind=True)
def publish_user_loggedIn(self, user_data):
    
    #Publishes 'Identity_service.user.logged_in' event to RabbitMQ.
    event_data = {
        "event": "Identity_service.user.logged_in",
        "data": user_data
    }
    _publish_event(self, event_data, routing_key="Identity_service.user.logged_in")
    print(f"Published event: Identity_service.user.logged_in -> {event_data}")    


@shared_task(name="publish.Identity_service.user.logged_out", bind=True)
def publish_user_loggedOut(self, user_data):
    
    #Publishes 'Identity_service.user.logged_out' event to RabbitMQ.
    
    event_data = {
        "event": "Identity_service.user.logged_out",
        "data": user_data
    }
    _publish_event(self, event_data, routing_key="Identity_service.user.logged_out")
    print(f"Published event: Identity_service.user.logged_out -> {user_data}")       
    

@shared_task(name="publish.Identity_service.user.details")
def publish_user_details(self, user_data):
    event_data = {
        "event": "Identity_service.user.details",
        "data": user_data
    }
    _publish_event(self, event_data, routing_key="Identity_service.user.details")
    print(f"Published event: Identity_service.user.details -> {user_data}")

