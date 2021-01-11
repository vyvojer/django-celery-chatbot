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

from django.utils.translation import gettext_lazy as _

from django_chatbot.models import Update

log = logging.getLogger(__name__)


class Field:
    default_error_messages = {
        'required': _('This value is required.'),
    }

    def __init__(self,
                 name: str,
                 required: bool = True,
                 label: str = None,
                 validators: list = None,
                 value=None):
        self.name = name
        self.required = required
        self.label = label
        self.validators = validators
        self.value = value
        if value is None:
            self.bound = False
            self.valid = False
        else:
            self.bound = True
            self.valid = True

    def __str__(self):
        return f"Field(name={self.name}, value={self.value}, bound={self.bound}, valid={self.valid})"  # noqa

    def to_python(self, value):
        return value

    def validate(self, value):
        if value == '' and self.required:
            pass

    def clean(self, value):
        self.validate(value)
        value = self.to_python(value)
        self.bound = True
        self.valid = True
        self.value = value


class CharField(Field):
    pass


class IntegerField(Field):
    def to_python(self, value):
        return int(value)


class Form(ABC):
    fields = None

    def __init__(self, update: Update):
        self.message = update.message
        self._root_message = self.message.get_form_root()
        self._init_fields()
        self._current_field = self._get_next_not_bound()
        self.completed = False
        self._handle_update()

    def _init_fields(self):
        if self._root_message:
            for field in self.fields:
                if value := self._root_message.get_form_fields().get(
                        field.name):
                    field.value = value
                    field.bound = True
                field.valid = True

    def _get_next_not_bound(self):
        not_bound = [f for f in self.fields if not f.bound]
        if not_bound:
            return not_bound[0]

    def _handle_update(self):
        if self._root_message:
            self._current_field.clean(self.message.text)
            log.debug("Handle field %s text=%s",
                      self._current_field, self.message.text)
            next_not_bound = self._get_next_not_bound()
            if not next_not_bound:
                self.completed = True
            self._root_message.update_form(
                fields={f.name: f.value for f in self.fields if f.bound},
                completed=self.completed
            )
            if self.completed:
                self.on_complete()
            else:
                prompt_message = self.message.reply(text=next_not_bound.label)
                prompt_message.set_form_root(form_root=self._root_message)
        else:
            prompt_message = self.message.reply(text=self.fields[0].label)
            prompt_message.init_form(form_class=self.__class__)

    @abstractmethod
    def on_complete(self):
        pass

    def get_field(self, field_name: str) -> Field:
        fields = [f for f in self.fields if f.name == field_name]
        if fields:
            return fields[0]
