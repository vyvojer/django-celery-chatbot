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
from django.core.validators import (
    MaxLengthValidator,
    MaxValueValidator,
    MinLengthValidator,
    MinValueValidator
)
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
    default_validators: list = field(
        default_factory=list, repr=False, init=False
    )
    validators: list = field(default_factory=list, repr=False)
    custom_error_messages: dict = field(default_factory=dict, repr=False)
    errors: list = field(default_factory=list, init=False)
    value: Any = field(default=None, init=False)
    is_bound: bool = field(default=False, init=False)
    is_valid: bool = field(default=False, init=False)

    def __post_init__(self):
        self.validators += self.default_validators

    def get_prompt(self, update: Update, cleaned_data: dict):
        return self.prompt

    def get_text(self, prompt: str, error_text: str):
        if error_text:
            return f"{error_text}\n\n{prompt}"
        else:
            return prompt

    def get_error_text(self):
        return "\n".join(self.get_error_messages())

    def get_error_messages(self):
        error_messages = []
        for error in self.errors:
            error_messages.append([message for message in error][0])
        return error_messages

    def get_inline_keyboard(self, update: Update, cleaned_data: dict):
        return self.inline_keyboard

    def get_prompt_message_params(self,
                                  update: Update,
                                  cleaned_data: dict):
        prompt = self.get_prompt(update, cleaned_data)
        error_text = self.get_error_text()
        inline_keyboard = self.get_inline_keyboard(update, cleaned_data)
        text = self.get_text(prompt, error_text)
        if inline_keyboard:
            reply_markup = InlineKeyboardMarkup(
                inline_keyboard=inline_keyboard
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

    def _run_validators(self, value):
        errors = []
        for validator in self.validators:
            try:
                validator(value)
            except ValidationError as e:
                errors.extend(e.error_list)
        if errors:
            raise ValidationError(errors)

    def validate(self, value, update: Update, cleaned_data: dict):
        pass

    def clean(self, value, update: Update, cleaned_data: dict):
        self.errors = []
        self.value = value
        try:
            value = self.to_python(value)
            self.value = value
            self._run_validators(value)
            self.validate(value, update, cleaned_data)
        except ValidationError as error:
            self.errors.extend(error.error_list)
            self._update_error_messages()
        else:
            self.is_bound = True
            self.is_valid = True

    def _update_error_messages(self):
        for error in [error for error in self.errors if error.code]:
            if message := self.custom_error_messages.get(error.code):
                error.message = message


@dataclass()
class CharField(Field):
    min_length: int = None
    max_length: int = None

    def __post_init__(self):
        if self.min_length is not None:
            self.default_validators.append(
                MinLengthValidator(limit_value=self.min_length)
            )
        if self.max_length is not None:
            self.default_validators.append(
                MaxLengthValidator(limit_value=self.max_length)
            )
        super().__post_init__()


@dataclass
class IntegerField(Field):
    min_value: int = None
    max_value: int = None

    def __post_init__(self):
        if self.min_value is not None:
            self.default_validators.append(
                MinValueValidator(limit_value=self.min_value)
            )
        if self.max_value is not None:
            self.default_validators.append(
                MaxValueValidator(limit_value=self.max_value)
            )
        super().__post_init__()

    def to_python(self, value):
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(
                _('Enter a whole number.'), code='invalid',
            )
        return int(value)


@dataclass()
class Form(ABC):
    """Base class for validation and saving multi-message user input.

    You should override this class.

    Attributes:
        completed: True if form is completed (All fields are validated
            and saved.)
        current_field: The reference to the currently handled field.
        cleaned_data: The dictionary that contains the saved data in
            the format::
            {
                "field_1_name": "field_1_value",
                ...
                "field_n_name": "field_n_value",
            }
        fields: The list of `Field` belonging to form

    """
    completed: bool = field(init=False, default=False)
    current_field: Field = field(init=False, default=None)
    cleaned_data: dict = field(init=False, default_factory=dict)
    fields: List[Field] = field(init=False, default=None)

    def __post_init__(self):
        self.fields = self.get_fields()

    @abstractmethod
    def get_fields(self) -> List[Field]:
        """Should return list of ``Field`` belonging to the form."""
        pass

    def _send_prompt(self, chat: Chat, update: Update, cleaned_data: dict):
        message = chat.reply(
            **self.current_field.get_prompt_message_params(
                update, cleaned_data
            ).to_dict()
        )
        return message

    def _next_field(self):
        next_index = self.fields.index(self.current_field) + 1
        if next_index < len(self.fields):
            return self.fields[next_index]

    def update(self, update: Update):
        """Update and save form with the user update.

        Args:
            update: The telegram update with an user input.

        Returns:

        """
        telegram_object = update.telegram_object
        if self.current_field is None:
            self.current_field = self.fields[0]
            self.on_first_update(update, self.cleaned_data)
            prompt_message = self._send_prompt(
                telegram_object.chat, update, self.cleaned_data
            )
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
                    prompt_message = self._send_prompt(
                        telegram_object.chat, update, self.cleaned_data
                    )
                    set_form_root(prompt_message, root_message)
                else:
                    self.completed = True
                    self.on_complete(update, self.cleaned_data)
            else:
                prompt_message = self._send_prompt(
                    telegram_object.chat, update, self.cleaned_data
                )
                set_form_root(prompt_message, root_message)
            save_form(root_message, self)

    def on_first_update(self, update: Update, cleaned_data: dict):
        """This method is called on first update.

        Override this method if you want to save some information from
            the update (for example, a model pk). Use the dictionary
            :attr:`cleaned_data` as a place to keep that information.

        Args:
            update: The telegram update with an user input.
            cleaned_data: The dictionary that contains the saved data in
                the format
                {
                    "field_1_name": "field_1_value",
                    ...
                    "field_n_name": "field_n_value",
                }

        """
        pass

    @abstractmethod
    def on_complete(self, update: Update, cleaned_data: dict):
        """This method is called on form completion.

        You should override this method to process user input.

        Args:
            update: The last user input. You can use it to get telegram User,
                for example.
            cleaned_data: The dictionary that contains the saved data in
                the format
                {
                    "field_1_name": "field_1_value",
                    ...
                    "field_n_name": "field_n_value",
                }

        """
        pass
