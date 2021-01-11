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

import logging
from abc import ABC, abstractmethod
from typing import Callable, Optional, Type

from celery import group

from django_chatbot.models import Update
from django_chatbot.forms import Form

log = logging.getLogger(__name__)


class Handler(ABC):
    def __init__(self,
                 name: str,
                 callback: Optional[Callable[[Update], None]] = None,
                 async_callback=None,
                 form_class: Type[Form] = None):
        self.name = name
        self.callback = callback
        self.async_callback = async_callback
        self.form_class = form_class

    def match(self, update: Update) -> bool:
        if match := self._match(update):
            return match
        if self.form_class:
            match = self._form_match(update)
        return match

    def _form_match(self, update: Update) -> bool:
        match = False
        if form_root := update.message.get_form_root():
            if form_root.extra['form']['name'] == self.form_class.__name__:
                match = True
        return match

    @abstractmethod
    def _match(self, update: Update) -> bool:
        return False

    def handle_update(self, update: Update):
        update.handler = self.name
        update.save()
        if self.callback:
            log.debug("Before calling callback")
            self.callback(update)
        elif self.async_callback:
            group(self.async_callback.signature(update.id)).delay()
        elif self.form_class:
            self.form_class(update)


class DefaultHandler(Handler):
    def _match(self, update: Update) -> bool:
        return True


class CommandHandler(Handler):
    def __init__(self, *args, command, **kwargs):
        self.command = command
        super().__init__(*args, **kwargs)

    def _match(self, update: Update) -> bool:
        match = False
        message = update.message
        if message and message.entities:
            if [
                entity for entity in message.entities
                if entity.type == 'bot_command' and entity.text == self.command
            ]:
                match = True
        return match
