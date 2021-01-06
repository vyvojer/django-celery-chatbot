from django.urls import path

from . import views

app_name = 'django_chatbot'

urlpatterns = [
    path("webhook/<slug:token_slug>/", views.webhook, name="webhook")
]
