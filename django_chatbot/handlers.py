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

import logging
from abc import ABC, abstractmethod

from celery import group

from django_chatbot.models import Update

log = logging.getLogger(__name__)


class Handler(ABC):
    def __init__(self, callback=None, async_callback=None):
        self.callback = callback
        self.async_callback = async_callback

    @abstractmethod
    def check_update(self, update: Update) -> bool:
        return False

    def handle_update(self, update: Update):
        if self.callback:
            log.debug("Before calling callback")
            self.callback(update)
        elif self.async_callback:
            group(self.async_callback.signature(update.id)).delay()


class DefaultHandler(Handler):
    def check_update(self, update: Update) -> bool:
        return True
