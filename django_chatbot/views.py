import json
import logging

from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt

from django_chatbot.tasks import dispatch

log = logging.getLogger(__name__)


@csrf_exempt
def webhook(request: HttpRequest, token_slug):
    update_data = json.loads(request.body)
    dispatch.delay(update_data=update_data, token_slug=token_slug)
    log.debug("Request %s slug_token %s", update_data, token_slug)
    return JsonResponse({"ok": "POST request processed"})
