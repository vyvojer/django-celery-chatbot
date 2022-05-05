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
import importlib

from django_chatbot import models
from django_chatbot.telegram.types import InlineKeyboardMarkup


class FormRepository:
    def __init__(self, update, form_class=None, form_model=None, handler=None):
        """

        Args:
            update (Update): update object
            form_class (type): form class
            form_model (django_chatbot.models.Form):
            handler (django_chatbot.handlers.Handler): the form handler
        """
        self.update = update
        self.input_telegram_object = update.telegram_object
        self.chat = self.input_telegram_object.chat
        self.prompt_message = None
        self.form_model = form_model
        self.handler = handler

        if form_model:
            self.is_started = True
            self.form = self._load_form(form_model)
        elif form_class:
            self.is_started = False
            self.form = form_class(repository=self)

    def handle_update(self):
        if self.is_started:
            self.form.input(self.input_telegram_object.text)
        else:
            self.form.start()

    def sent_message(self, message, inline_keyboard=None):
        kwargs = {}
        if inline_keyboard:
            reply_markup = InlineKeyboardMarkup(inline_keyboard)
            kwargs["reply_markup"] = reply_markup
        self.prompt_message = self.chat.reply(message, **kwargs)

    def edit_message(self, message, inline_keyboard=None):
        kwargs = {}
        if inline_keyboard:
            reply_markup = InlineKeyboardMarkup(inline_keyboard)
            kwargs["reply_markup"] = reply_markup
        self.prompt_message = self.input_telegram_object.edit(message, **kwargs)

    def save_form(self, form):
        if self.form_model:
            form_model = self.form_model
            form_model.current_field = (
                form.current_field.name if form.current_field else None
            )
            form_model.context = form.context
            form_model.is_finished = form.is_finished
            form_model.save()
        else:
            form_model = models.Form.objects.create(
                module_name=form.__module__,
                class_name=form.__class__.__name__,
                current_field=form.current_field.name if form.current_field else None,
                context=form.context,
                is_finished=form.is_finished,
                handler=self.handler.name,
            )

        for field in form.fields.values():
            self._save_field(field, form_model)

        self.update.set_handler(form_model.handler)
        self.input_telegram_object.set_form(form_model)
        if self.prompt_message:
            self.prompt_message.set_form(form_model)

        return form_model

    @staticmethod
    def _save_field(field, form_model):
        models.Field.objects.update_or_create(
            form=form_model,
            name=field.name,
            defaults={
                "value": field.value,
                "is_valid": field.is_valid,
            },
        )

    def _load_form(self, form_model):
        module = importlib.import_module(form_model.module_name)
        klass = getattr(module, form_model.class_name)
        form = klass(repository=self)
        form.context = form_model.context
        form.is_finished = form_model.is_finished
        form.current_field = (
            getattr(form, form_model.current_field)
            if form_model.current_field
            else None
        )

        for field_model in models.Field.objects.filter(form=form_model):
            self._load_field(form, field_model)

        return form

    @staticmethod
    def _load_field(form, field_model):
        field = getattr(form, field_model.name)
        field.value = field_model.value
        field.is_valid = field_model.is_valid
