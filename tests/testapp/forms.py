# *****************************************************************************
#  MIT License
#
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense,
#  and/or sell copies of the Software, and to permit persons to whom
#  the Software is furnished to do so, subject to the following conditions:
#
#
from __future__ import annotations

import logging
from dataclasses import dataclass

from django.core.exceptions import ValidationError
from testapp.models import Note

from django_chatbot.forms import CharField, Field, Form, IntegerField
from django_chatbot.models import Update
from django_chatbot.telegram.types import InlineKeyboardButton

log = logging.getLogger(__name__)


class AddNote(Form):
    class ConfirmSaveField(CharField):
        def get_prompt(self, update: Update, cleaned_data: dict, form: Form):
            prompt = f""" Save note?
        {cleaned_data['title']}
        {cleaned_data['text']}
        """
            return prompt

    title = CharField(prompt="Input title:", min_length=5, max_length=15)
    text = CharField(prompt="Input text:", min_length=10, max_length=100)
    confirm = ConfirmSaveField(
        inline_keyboard=[
            [
                InlineKeyboardButton("Yes", callback_data="yes"),
                InlineKeyboardButton("No", callback_data="cancel"),
            ]
        ]
    )

    def on_complete(self, update, cleaned_data):
        telegram_object = update.telegram_object
        user = telegram_object.from_user
        chat = telegram_object.chat
        if cleaned_data["confirm"] == "cancel":
            chat.reply("Note has not been added.")
        else:
            title = cleaned_data["title"]
            text = cleaned_data["text"]
            Note.objects.create(user=user, title=title, text=text)
            chat.reply("Success! Note was added.")


class ConfirmDeleteField(CharField):
    def get_prompt(self, update: Update, cleaned_data: dict, form: Form):
        note = Note.objects.get(id=cleaned_data["note_id"])
        prompt = f"""Delete note?
        {note.title}
        {note.text}
        """
        return prompt


class IdToDeleteField(IntegerField):
    def get_prompt(self, update: Update, cleaned_data: dict, form: Form):
        user = update.telegram_object.from_user
        ids = [n.id for n in Note.objects.filter(user=user)]
        ids = ", ".join(str(id) for id in ids)
        self.prompt = f"Enter not Id, one of \n{ids}:"
        return super().get_prompt(update, cleaned_data, form)

    def validate(self, value, update: Update, cleaned_data: dict, form: Form):
        user = update.telegram_object.from_user
        ids = [n.id for n in Note.objects.filter(user=user)]
        if value not in ids:
            ids = ", ".join(str(id) for id in ids)
            raise ValidationError(f"Id must be one of: {ids}")


class DeleteNoteForm(Form):
    note_id = IdToDeleteField(
        prompt="Input note ID",
        min_value=0,
    )
    confirm = ConfirmDeleteField(
        inline_keyboard=[
            [
                InlineKeyboardButton("Yes", callback_data="yes"),
                InlineKeyboardButton("No", callback_data="cancel"),
            ]
        ]
    )

    def on_complete(self, update, cleaned_data):
        telegram_object = update.telegram_object
        chat = telegram_object.get_chat
        if cleaned_data["confirm"] == "cancel":
            chat.reply("Note has not been deleted.")
        else:
            Note.objects.get(id=cleaned_data["note_id"]).delete()
            chat.reply("Success! Note was deleted.")


@dataclass
class NotesField(Field):
    def __post_init__(self):
        self.name = "notes"
        self.inline_keyboard = [
            [
                InlineKeyboardButton("<", callback_data="previous"),
                InlineKeyboardButton(">", callback_data="next"),
            ]
        ]

    def get_prompt(self, update: Update, cleaned_data: dict, form: NotesForm):
        user_id = cleaned_data["user_id"]
        notes = Note.objects.filter(user_id=user_id)
        if cleaned_data["note_id"] is None:
            note_idx = 0
        else:
            note_idx = self._get_note_index(notes, cleaned_data["note_id"])
        if value := cleaned_data.get("notes"):
            if value == "previous":
                note_idx -= 1
            elif value == "next":
                note_idx += 1
        note = notes[note_idx]
        cleaned_data["note_id"] = note.id

        return self._prompt_from_note(note, note_idx + 1, notes.count())

    @staticmethod
    def _prompt_from_note(note: Note, number, count):
        prompt = f"""
Note {number} of {count}
Title: {note.title}
Text: {note.text}
"""
        return prompt

    @staticmethod
    def _get_note_index(notes, note_id):
        return list(notes.values_list("id", flat=True)).index(note_id)


@dataclass
class NotesForm(Form):
    def get_root_field(self) -> Field:
        notes_field = NotesField()
        notes_field.add_next(
            notes_field, lambda value, update, data: value in ["previous", "next"]
        )
        return notes_field

    def on_init(self, update: Update, cleaned_data: dict):
        user_id = update.telegram_object.from_user
        cleaned_data["user_id"] = user_id
        cleaned_data["note_id"] = None
