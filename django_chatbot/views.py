#  MIT License
#
#  Copyright (c) 2020 Alexey Londkevich
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

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
