from django.db.models.signals import post_save
from django.dispatch import receiver
from Identity_service.models import *
from django.contrib.auth.signals import user_logged_in
from Identity_service.tasks import *



@receiver(post_save, sender=user)
def customer_created_handler(sender, instance, created, **kwargs):
    if created:
        user_data = {
            "event": "Identity_service.customer.created",
            "id": str(instance.id),
            "email": instance.email,
            "full_name": str(instance.first_name) + " "
                + str(instance.last_name),
            "created_at": instance.date_joined.isoformat(),
        }
        publish_customer_created.delay(user_data)
        
@receiver(post_save, sender=user)
def staff_created_handler(sender, instance, created, **kwargs):
    if created:
        user_data = {
            "event": "Identity_service.staff.created",
            "user_id": str(instance.id),
            "email": instance.email,
            "full_name": str(instance.first_name) + " "
                + str(instance.last_name),
            "created_at": instance.date_joined.isoformat(),
        }
        publish_staff_created.delay(user_data)
        

@receiver(user_logged_in, sender=user)
def handle_user_login(sender, request, user, **kwargs):

    user_data = {
        "event": "Identu.user.logged_in",
        "user_id": str(user.id),
        "email": user.email,
        # Assuming firstname/lastname are attributes on your User model
        "full_name": f"{user.firstname} {user.lastname}",
    }
    
    # Asynchronously publish the event
    publish_user_loggedIn.delay(user_data)
      