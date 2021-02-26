# *****************************************************************************
#  MIT License
#
#  Copyright (c) 2020 Alexey Londkevich <londkevich@gmail.com>
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense,
#  and/or sell copies of the Software, and to permit persons to whom
#  the Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included
#  in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#  ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
#  THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# *****************************************************************************

"""This module contains update handlers"""

import logging
from abc import ABC, abstractmethod
from typing import Callable, Optional, Type

from celery import group

from django_chatbot.forms import Form
from django_chatbot.models import Update

log = logging.getLogger(__name__)


class Handler(ABC):
    """The base class for all update handlers

    Args:
        name: The handler name.
        callback: The callback function for the handler.
        async_callback: The Celery task for the handler.
        form_class: Form class to be used for the handler.
        suppress_form:

    """
    def __init__(self,
                 name: str,
                 callback: Optional[Callable[[Update], None]] = None,
                 async_callback=None,
                 form_class: Type[Form] = None,
                 suppress_form: bool = False):
        self.name = name
        self.callback = callback
        self.async_callback = async_callback
        self.form_class = form_class
        self.form = None
        self.suppress_form = suppress_form

    @abstractmethod
    def match(self, update: Update) -> bool:
        """
        This method is called to determine if the handler matches the update.
        It should always be overridden.

        Args:
            update: The update.

        Returns:
            True if the handler matches the update, False otherwise.
        """
        return False

    def handle_update(self, update: Update):
        """
        Call callback/async_callback/form

        Should be called only if the handler matches the update.
        """
        update.handler = self.name
        update.save()
        if self.callback:
            self.callback(update)
        elif self.async_callback:
            group(self.async_callback.signature(update.id)).delay()
        elif self.form_class:
            if self.form:
                form = self.form
            else:
                form = self.form_class()
            form.update(update)


class DefaultHandler(Handler):
    """This handler matches any update. Use it as the default handler.

    Args:
        name: The handler name.
        callback: The callback function for the handler.
        async_callback: The Celery task for the handler.
        form_class: Form class to be used for the handler.

    """
    def match(self, update: Update) -> bool:
        return True


class CommandHandler(Handler):
    """Handler class to handle a Telegram command.

    Args:
        name: The handler name.
        callback: The callback function for the handler.
        async_callback: The Celery task for the handler.
        form_class: Form class to be used for the handler.
        command: The telegram command to handle.

    """
    def __init__(self, *args, command, **kwargs):
        self.command = command
        super().__init__(*args, **kwargs)

    def match(self, update: Update) -> bool:
        match = False
        message = update.message
        if message and message.entities:
            if [
                entity for entity in message.entities
                if entity.type == 'bot_command' and entity.text == self.command
            ]:
                match = True
        return match
