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


