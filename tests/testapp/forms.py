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

from django.core.exceptions import ValidationError

from django_chatbot.forms import CharField, Form, IntegerField
from django_chatbot.models import Update
from django_chatbot.telegram.types import InlineKeyboardButton

from .models import Note

log = logging.getLogger(__name__)


class AddNote(Form):
    class ConfirmSaveField(CharField):
        def get_prompt(self, update: Update, cleaned_data: dict):
            prompt = f""" Save note?
        {cleaned_data['title']}
        {cleaned_data['text']}
        """
            return prompt

    def get_fields(self):
        fields = [
            CharField(name="title", prompt="Input title:"),
            CharField(name="text", prompt="Input text:"),
            self.ConfirmSaveField(name="confirm", inline_keyboard=[
                [InlineKeyboardButton("Yes", callback_data="yes"),
                 InlineKeyboardButton("No", callback_data="cancel")]])
        ]
        return fields

    def on_complete(self, update, cleaned_data):
        telegram_object = update.telegram_object
        user = telegram_object.from_user
        chat = telegram_object.chat
        if cleaned_data['confirm'] == 'cancel':
            chat.reply("Note has not been added.")
        else:
            title = cleaned_data["title"]
            text = cleaned_data["text"]
            Note.objects.create(user=user, title=title, text=text)
            chat.reply("Success! Note was added.")


class ConfirmDeleteField(CharField):
    def get_prompt(self, update: Update, cleaned_data: dict):
        note = Note.objects.get(id=cleaned_data['note_id'])
        prompt = f"""Delete note?
        {note.title}
        {note.text}
        """
        return prompt


class IdToDeleteField(IntegerField):
    def get_prompt(self, update: Update, cleaned_data: dict):
        user = update.telegram_object.from_user
        ids = [n.id for n in Note.objects.filter(user=user)]
        ids = ", ".join(str(id) for id in ids)
        self.prompt = f"Enter not Id, one of \n{ids}:"
        return super().get_prompt(update, cleaned_data)

    def validate(self, value, update: Update, cleaned_data: dict):
        user = update.telegram_object.from_user
        ids = [n.id for n in Note.objects.filter(user=user)]
        if value not in ids:
            ids = ", ".join(str(id) for id in ids)
            raise ValidationError(f"Id must be one of: {ids}")


class DeleteNoteForm(Form):
    def get_fields(self):
        fields = [
            IdToDeleteField(name='note_id', prompt="Input note ID"),
            ConfirmDeleteField(name="confirm", inline_keyboard=[
                [InlineKeyboardButton("Yes", callback_data="yes"),
                 InlineKeyboardButton("No", callback_data="cancel")]])
        ]
        return fields

    def on_complete(self, update, cleaned_data):
        telegram_object = update.telegram_object
        chat = telegram_object.chat
        if cleaned_data['confirm'] == 'cancel':
            chat.reply("Note has not been deleted.")
        else:
            Note.objects.get(id=cleaned_data['note_id']).delete()
            chat.reply("Success! Note was deleted.")
