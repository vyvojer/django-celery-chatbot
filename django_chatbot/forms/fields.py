# *****************************************************************************
#  MIT License
#
#  Copyright (c) 2022 Alexey Londkevich <londkevich@gmail.com>
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

from enum import Enum
from typing import Callable, Literal


class PromptType(Enum):
    NEW_MESSAGE = "new_message"
    UPDATE_MESSAGE = "update_message"


class Field:
    def __init__(
        self,
        prompt_message=None,
        field_type=None,
        error_message=None,
        inline_keyboard=None,
        validators=None,
    ):
        """

        Args:
            prompt_message (str): prompt message
            error_message (str, optional): Defaults to None.
            validators(list, optional): Defaults to None.
            field_type (FieldType, optional): Defaults to FieldType.UPDATE.
            callback (Callable, optional): Defaults to None.
            error_callback (Callable, optional): Defaults to None.
            condition (Callable, optional): Defaults to None.
        """
        if prompt_message or not hasattr(self, "prompt_message"):
            self.prompt_message = prompt_message
        if error_message or not hasattr(self, "error_message"):
            self.error_message = error_message
        if inline_keyboard or not hasattr(self, "inline_keyboard"):
            self.inline_keyboard = inline_keyboard
        if validators or not hasattr(self, "validators"):
            self.validators = validators
        if field_type or not hasattr(self, "field_type"):
            self.field_type = field_type

        self.is_valid = False
        self.value = None
        self.name = self.__class__.__name__
        self.prompt_type = PromptType.NEW_MESSAGE
        self._next_fields = []  # list of tuple (field, condition, prompt_type)

    def input(self, value, form):
        """

        Args:
            value (str): input value, sent by user
            form (Form): form to which field belongs
        """
        self.value = value
        self.is_valid = True

    def get_prompt_message(self, form):
        return self.prompt_message

    def sent_prompt_message(self, form):
        if self.prompt_type == PromptType.NEW_MESSAGE:
            form.repository.sent_message(
                self.get_prompt_message(form),
                inline_keyboard=self.get_inline_keyboard(form),
            )
        else:
            form.repository.edit_message(
                self.get_prompt_message(form),
                inline_keyboard=self.get_inline_keyboard(form),
            )

    def sent_error_message(self, form):
        form.repository.sent_message(
            self.get_error_message(form), inline_keyboard=self.get_inline_keyboard(form)
        )

    def get_error_message(self, form):
        return self.error_message

    def get_inline_keyboard(self, form):
        return self.inline_keyboard

    @property
    def is_bound(self):
        return self.value is not None

    def on_valid(self, form):
        """
        This method is called when field is valid.
        Override this method to do something when field is valid.

        Args:
            form (Form): form to which field belongs
        """
        pass

    def on_invalid(self, form):
        """
        This method is called when field is invalid.
        Override this method to do something when field is invalid.

        Args:
            form (Form): form to which field belongs
        """
        pass

    def add_next_field(
        self,
        field: Field,
        condition: Callable = None,
        prompt_type: Literal[
            PromptType.NEW_MESSAGE, PromptType.UPDATE_MESSAGE
        ] = PromptType.NEW_MESSAGE,
    ):
        """Add next field to form

        Args:
            field(Field): field to add
            condition(Callable, optional): function to check if field should be added.
                The function that takes the current field value and form
                and return boolean.
                The function should return True if field should be next field.
            prompt_type(PromptType, optional): If prompt_type is UPDATE_MESSAGE
                then the message will be updated instead of new message
                (on-the-fly update).
                Defaults to PromptType.NEW_MESSAGE.
        """
        if condition is None:
            condition = lambda *args, **kwargs: True
        self._next_fields.append((field, condition, prompt_type))

    def add_next_fields(self, *fields):
        """Add next fields to form

        Args:
            fields(Union[Field, Tuple[Field, Callable]): fields to add
        """
        for field in fields:
            if isinstance(field, tuple):
                self.add_next_field(*field)
            else:
                self.add_next_field(field)

    def get_next_field(self, value, form):
        if len(self._next_fields) == 0:
            return None
        else:
            for field, condition, prompt_type in self._next_fields:
                if condition(value, form):
                    if field is None:
                        return None
                    field.prompt_type = prompt_type
                    return field
            return None

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name
