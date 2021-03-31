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

from __future__ import annotations
import logging
from abc import ABC
import dataclasses
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional

from django.core.exceptions import ValidationError
from django.core.validators import (
    MaxLengthValidator,
    MaxValueValidator,
    MinLengthValidator,
    MinValueValidator
)
from django.utils.translation import gettext as _

from django_chatbot.models import Form as FormKeeper, Update
from django_chatbot.telegram.api import SendMessageParams
from django_chatbot.telegram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
)

log = logging.getLogger(__name__)


@dataclass(eq=True)
class ConditionalField:
    field: Field
    condition: Callable = dataclasses.field(repr=False, default=None)

    def __post_init__(self):
        if self.condition is None:
            self.condition = lambda value, update, cleaned_data: True
        ConditionalField.condition = staticmethod(self.condition)

    def match(self, value: Any, update: Update, cleaned_data: dict):
        return self.condition(value, update, cleaned_data)


@dataclass(eq=True)
class Field:
    name: str = None
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
    next_fields: List[ConditionalField] = field(default_factory=list)
    _previous_field: Field = None

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

    def clear(self):
        self.value = None
        self.is_bound = False
        self.is_valid = False

    def on_valid(self, update: Update, cleaned_data: dict):
        pass

    def add_next(self,
                 field: Field,
                 condition: Callable = None):
        if condition is None:
            self.next_fields.append(ConditionalField(field))
        else:
            self.next_fields.append(ConditionalField(field, condition))

    def previous(self):
        return self._previous_field

    def next(self, update: Update, cleaned_data: dict):
        next_field = None
        for conditional_field in self.next_fields:
            if conditional_field.match(self.value, update, cleaned_data):
                next_field = conditional_field.field
                break
        if next_field:
            next_field._previous_field = self
        return next_field


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


@dataclass(eq=True)
class FormHandler:
    callback: Callable
    command: str = None

    def handle(self, form, update: Update):
        self.callback(form, update=update)

    def match(self, update: Update) -> bool:
        match = False
        if (message := update.message) and message.entities and self.command:
            if [
                entity for entity in message.entities
                if entity.type == 'bot_command' and entity.text == self.command
            ]:
                match = True
        return match


@dataclass()
class Form(ABC):
    """Base class for validation and saving multi-message user input.

    You should override this class.

    Attributes:
        form_keeper_id: pk of Message, where serialized form is keeping.
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
    form_keeper: Optional[FormKeeper] = field(init=False, default=None)
    completed: bool = field(init=False, default=False)
    current_field: Field = field(init=False, default=None)
    cleaned_data: dict = field(init=False, default_factory=dict)
    handlers: List[FormHandler] = field(init=False, default_factory=list)

    def __post_init__(self):
        self.handlers = [
            FormHandler(callback=self.back_to_previous, command='/previous'),
            FormHandler(callback=self.cancel, command='/cancel'),
        ]

    def __getstate__(self):
        """Exclude some fields from serializing"""
        state = self.__dict__.copy()
        if 'form_keeper' in state:
            del state['form_keeper']
        return state

    def __setstate__(self, state):
        state['form_keepr'] = None
        self.__dict__.update(state)

    def get_root_field(self) -> Field:
        fields = []
        for name, attr in self.__class__.__dict__.items():
            if isinstance(attr, Field):
                attr.name = name
                fields.append(attr)
        try:
            root = previous = fields[0]
        except IndexError:
            raise ValueError(
                "There is no root field. Add fields to form or override get_root_fields")  # noqa
        for current in fields[1:]:
            previous.add_next(current)
            previous = current
        return root

    def _send_prompt(self,
                     update: Update):
        """Send field input prompt to user

        Args:
            update:
            root_message:

        Returns:

        """
        chat = update.telegram_object.chat
        prompt_message = chat.reply(
            **self.current_field.get_prompt_message_params(
                update, self.cleaned_data
            ).to_dict()
        )
        if self.form_keeper is None:
            self.form_keeper = FormKeeper.objects.create()
        prompt_message.form = self.form_keeper
        prompt_message.save()
        self._save()

    def _save(self):
        self.form_keeper.form = self
        self.form_keeper.save()

    def _init_form(self, update: Update):
        self.current_field = self.get_root_field()
        self.on_init(update, self.cleaned_data)
        self._send_prompt(update)

    def _handle_user_input(self, update: Update):
        t_object = update.telegram_object
        self.current_field.clean(t_object.text, update, self.cleaned_data)
        if self.current_field.is_valid:
            self.cleaned_data[
                self.current_field.name] = self.current_field.value
            if next_field := self.current_field.next(
                    update, self.cleaned_data):
                self.current_field = next_field
                self._send_prompt(update)
            else:
                self.completed = True
                self.on_complete(update, self.cleaned_data)
                self._save()
        else:
            self._send_prompt(update)

    def _handle_user_command(self, update: Update) -> Optional[FormHandler]:
        for handler in self.handlers:
            if handler.match(update):
                return handler

    def update(self, update: Update) -> None:
        """Update and save form with the user update.

        Args:
            update: The telegram update with an user input.

        Returns:

        """
        if self.form_keeper is None:
            self._init_form(update)
        elif handler := self._handle_user_command(update):
            handler.handle(self, update)
        else:
            self._handle_user_input(update)

    def on_init(self, update: Update, cleaned_data: dict):
        """This method is called on form init after getting first update.

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

    def on_cancel(self, update: Update, cleaned_data: dict):
        """This method is called on form cancelation.

        Override this method if you want to handle cancelation, for example
        send message

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

    # Command/button handlers

    @staticmethod
    def back_to_previous(form: Form, update):
        if previous := form.current_field.previous():
            form.current_field = previous
            previous.clear()
            del form.cleaned_data[previous.name]
        form._send_prompt(update)

    @staticmethod
    def cancel(form: Form, update):
        form.on_cancel(update, form.cleaned_data)
