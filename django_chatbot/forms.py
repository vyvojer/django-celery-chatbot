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
from dataclasses import dataclass, field
from typing import Any, List

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from django_chatbot.models import Chat, Update
from django_chatbot.services.forms import (get_form_root, save_form,
                                           set_form_root)
from django_chatbot.telegram.api import SendMessageParams
from django_chatbot.telegram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
)

log = logging.getLogger(__name__)


@dataclass(eq=True)
class Field:
    name: str
    required: bool = True
    prompt: str = None
    inline_keyboard: List[List[InlineKeyboardButton]] = None
    validators: list = field(default_factory=list, repr=False)
    error_messages: dict = field(default_factory=dict, repr=False)
    value: Any = field(default=None, init=False)
    is_bound: bool = field(default=False, init=False)
    is_valid: bool = field(default=False, init=False)
    default_error_messages: dict = field(
        default_factory=dict, init=False, repr=False)
    errors: list = field(default_factory=list, init=False)

    def __post_init__(self):
        self.default_error_messages.update(self.error_messages)
        self.error_messages = self.default_error_messages

    def update_prompt(self, update: Update, cleaned_data: dict):
        self.prompt = self.get_prompt(update, cleaned_data)
        self.inline_keyboard = self.get_inline_keyboard(update, cleaned_data)

    def get_prompt(self, update: Update, cleaned_data: dict):
        if self.errors:
            errors = self.errors[0].message
            self.prompt = f"{errors}\n{self.prompt}"
        return self.prompt

    def get_inline_keyboard(self, update: Update, cleaned_data: dict):
        return self.inline_keyboard

    def to_send_message_params(self):
        text = self.prompt
        if self.inline_keyboard:
            reply_markup = InlineKeyboardMarkup(
                inline_keyboard=self.inline_keyboard
            )
        else:
            reply_markup = None
        send_message_params = SendMessageParams(
            text=text,
            reply_markup=reply_markup,
        )
        return send_message_params

    def to_python(self, value):
        return value

    def validate(self, value, update: Update, cleaned_data: dict):
        pass

    def clean(self, value, update: Update, cleaned_data: dict):
        self.errors = []
        self.value = value
        try:
            value = self.to_python(value)
            self.value = value
            self.validate(value, update, cleaned_data)
        except ValidationError as error:
            self.errors.append(error)
        else:
            self.is_bound = True
            self.is_valid = True


class CharField(Field):
    pass


class IntegerField(Field):
    def __post_init__(self):
        self.default_error_messages = {
            'invalid': _('Enter a whole number.'),
        }
        super().__post_init__()

    def to_python(self, value):
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(
                self.error_messages['invalid'], code='invalid'
            )
        return int(value)


@dataclass()
class Form(ABC):
    completed: bool = field(init=False, default=False)
    current_field: Field = field(init=False, default=None)
    cleaned_data: dict = field(init=False, default=None)
    fields: List[Field] = field(init=False, default=None)

    def __post_init__(self):
        if self.cleaned_data is None:
            self.cleaned_data = {}
        self.fields = self.get_fields()

    @abstractmethod
    def get_fields(self) -> List[Field]:
        pass

    def _send_prompt(self, chat: Chat):
        message = chat.reply(
            **self.current_field.to_send_message_params().to_dict()
        )
        return message

    def _next_field(self):
        next_index = self.fields.index(self.current_field) + 1
        if next_index < len(self.fields):
            return self.fields[next_index]

    def update(self, update: Update):
        telegram_object = update.telegram_object
        if self.current_field is None:
            self.current_field = self.fields[0]
            self.current_field.update_prompt(update, self.cleaned_data)
            self.on_first_update(update, self.cleaned_data)
            prompt_message = self._send_prompt(telegram_object.chat)
            save_form(prompt_message, self)
        else:
            self.current_field.clean(
                telegram_object.text, update, self.cleaned_data
            )
            root_message = get_form_root(telegram_object)
            if self.current_field.is_valid:
                self.cleaned_data[
                    self.current_field.name] = self.current_field.value
                if next_field := self._next_field():
                    self.current_field = next_field
                    self.current_field.update_prompt(update, self.cleaned_data)
                    prompt_message = self._send_prompt(telegram_object.chat)
                    set_form_root(prompt_message, root_message)
                else:
                    self.completed = True
                    self.on_complete(update, self.cleaned_data)
            else:
                self.current_field.update_prompt(update, self.cleaned_data)
                prompt_message = self._send_prompt(telegram_object.chat)
                set_form_root(prompt_message, root_message)
            save_form(root_message, self)

    def on_first_update(self, update: Update, cleaned_data: dict):
        pass

    @abstractmethod
    def on_complete(self, update: Update, cleaned_data: dict):
        pass
