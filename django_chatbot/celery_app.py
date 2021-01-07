from celery import Celery
from django.conf import settings

app = Celery('django_chatbot',
             broker=settings.CHATBOT_BROKER,
             backend=settings.CHATBOT_BACKEND,
             include='django_chatbot.tasks')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')
