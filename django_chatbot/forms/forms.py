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
import copy

from .fields import Field


class Form:
    def __init__(self, repository):
        self.repository = repository
        self.fields = {}
        self.current_field = None
        self.previous_field = None
        self.context = {}
        self.is_finished = False
        self._prepare_fields()
        self.connect_fields()

    def _prepare_fields(self):
        """Prepare the form fields.
        Makes instance field variables of the class variables.
        """
        for attr in dir(self.__class__):
            if isinstance(class_field := getattr(self.__class__, attr), Field):
                field = copy.deepcopy(class_field)
                field.name = attr
                setattr(self, attr, field)
                self.fields[attr] = field

    def get_root_field(self) -> Field:
        """Return root field"""
        # Since python 3.6, dictionaries keep insertion order
        return [v for v in self.fields.values()][0]

    def connect_fields(self):
        fields = [v for v in self.fields.values()]
        for previous, current in zip(fields, fields[1:]):
            previous.add_next_field(current)

    def start(self):
        self.current_field = self.get_root_field()
        self.current_field.sent_prompt_message(form=self)
        self.repository.save_form(self)

    def input(self, value):
        self.current_field.input(value=value, form=self)

        if self.current_field.is_valid:
            if next_field := self.current_field.get_next_field(value=value, form=self):
                self.previous_field = self.current_field
                self.current_field = next_field
                self.current_field.sent_prompt_message(form=self)
            else:
                self.is_finished = True
                self.on_finish(self.repository.chat)
        self.repository.save_form(self)

    def on_finish(self, chat):
        pass
