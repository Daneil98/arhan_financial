from .celery_app import app as celery_app
__all__ = ('celery_app',)

# In your settings.py or near the top of your custom code:
import uuid
from sqlite3 import register_adapter

# This ensures Python tells SQLite to treat UUID objects as TEXT/CHAR
def adapt_uuid(val):
    return str(val)

register_adapter(uuid.UUID, adapt_uuid)