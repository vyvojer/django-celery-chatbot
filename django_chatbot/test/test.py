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

import logging
import re
from functools import cached_property
from typing import Optional

from django.db.models import QuerySet
from django.db.models.signals import post_save
from django.forms import Form
from django.test import TransactionTestCase
from django.utils import timezone

from django_chatbot.conf import settings
from django_chatbot.models import (
    Bot,
    CallbackQuery,
    Chat,
    Message,
    Update,
    User,
    telegram_instance,
)
from django_chatbot.services.dispatcher import Dispatcher
from django_chatbot.telegram import types

START_USER_ID = 1000

logger = logging.getLogger(__name__)


class MockUserError(Exception):
    pass


class ClientUser:
    def __init__(self, bot: Bot, username: str = None):
        self.bot = bot
        self.user_id = self._next_user_id()
        if username is None:
            username = f"test_user_{self.user_id}"
        self.username = username
        self.user = User.objects.create(
            user_id=self.user_id,
            is_bot=False,
            username=username,
            first_name=username,
            last_name=username,
        )
        self.chat = Chat.objects.create(
            bot=self.bot,
            chat_id=self.user_id,
            type="private",
            username=username,
            first_name=username,
            last_name=username,
        )
        self.dispatcher = Dispatcher(bot.token_slug)

    def _next_user_id(self) -> int:
        users = User.objects.all().order_by("user_id")
        last = users.last()
        if last:
            return last.user_id + 1
        else:
            return START_USER_ID

    def messages(self) -> QuerySet[Message]:
        """Return `Message` query set related to the user"""
        messages = Message.objects.filter(chat=self.chat).order_by("-message_id")
        return messages

    def updates(self) -> QuerySet[Update]:
        """Return `Update` query set related to the user"""
        updates = Update.objects.filter(message__chat=self.chat).order_by("-update_id")
        return updates

    def callback_queries(self) -> QuerySet[CallbackQuery]:
        """Return `Update` query set related to the user"""
        callback_queries = CallbackQuery.objects.filter(from_user=self.user).order_by(
            "-callback_query_id"
        )
        return callback_queries

    def form(self) -> Optional[Form]:
        if last := self.chat.messages.last():
            if form_model := last.form:
                return form_model.form

    def _next_message_id(self) -> int:
        messages = Message.objects.filter(chat__chat_id=self.user_id).order_by(
            "message_id"
        )
        last = messages.last()
        if last:
            return last.message_id + 1
        else:
            return 1

    def _next_callback_query_id(self) -> str:
        callbacks = CallbackQuery.objects.all()
        last = callbacks.last()
        if last:
            return str(int(last.callback_query_id) + 1)
        else:
            return "1"

    def _next_update_id(self) -> int:
        last = Update.objects.all().order_by("update_id").last()
        if last:
            return last.update_id + 1
        else:
            return 1

    def _telegram_user(self):
        user = types.User(
            id=self.user_id,
            is_bot=False,
            username=self.username,
            first_name=self.username,
            last_name=self.username,
        )
        return user

    def _telegram_chat(self):
        user = types.Chat(
            id=self.user_id,
            type="private",
            username=self.username,
            first_name=self.username,
            last_name=self.username,
        )
        return user

    @staticmethod
    def _extract_entities(text: str):
        pattern = re.compile(r"/\w+")
        entities = []
        for match in re.finditer(pattern, text):
            offset, end = match.span()
            length = end - offset
            entities.append({"offset": offset, "length": length, "type": "bot_command"})
        if entities:
            return entities

    def send_message(self, message_text: str):
        """Simulate sending message to bot by the user."""
        message = types.Message(
            message_id=self._next_message_id(),
            date=timezone.now(),
            chat=self._telegram_chat(),
            from_user=self._telegram_user(),
            text=message_text,
            entities=self._extract_entities(message_text),
        )
        update = types.Update(
            update_id=self._next_update_id(),
            message=message,
        )
        self.dispatcher.dispatch(update_data=update.to_dict(date_as_timestamp=True))

    def send_callback_query(self, data: str, markup_message: Message = None):
        if markup_message is None:
            last = self.messages().first()
            if last is None or last.reply_markup is None:
                raise ValueError("No ReplyMarkup to response")
            else:
                markup_message = last
        callback_query = types.CallbackQuery(
            id=self._next_callback_query_id(),
            from_user=self._telegram_user(),
            chat_instance=self._next_callback_query_id(),
            message=types.Message(
                message_id=markup_message.message_id,
                chat=self._telegram_chat(),
                date=markup_message.date,
            ),
            data=data,
        )
        update = types.Update(
            update_id=self._next_update_id(),
            callback_query=callback_query,
        )
        self.dispatcher.dispatch(update_data=update.to_dict(date_as_timestamp=True))


class Client:
    def __init__(self, user: ClientUser):
        self.user = user
        self._bot = user.bot
        self._api = user.bot.api
        self._changed = []

    def send_message(self, message_text: str) -> ClientResponse:
        changed_before = self._changed.copy()
        self.user.send_message(message_text)
        return ClientResponse(
            bot=self._bot, changed_before=changed_before, changed_after=self._changed
        )

    def send_callback_query(
        self, data: str, markup_message: Message = None
    ) -> ClientResponse:
        changed_before = self._changed.copy()
        self.user.send_callback_query(data, markup_message)
        return ClientResponse(
            bot=self._bot, changed_before=changed_before, changed_after=self._changed
        )

    def messages(self):
        return self.user.messages()


class ClientResponse:
    UPDATE = "update"
    NEW = "new"

    def __init__(self, bot: Bot, changed_before: list, changed_after: list):
        self.bot = bot
        self.changed = changed_after[len(changed_before) :]
        self.is_successful = len(self.changed) > 0

    def __bool__(self):
        return self.is_successful

    def _get_instances(self, instance_type: str):
        instances = [
            c["instance"]
            for c in filter(
                lambda c: c["model"] == instance_type,
                self.changed,
            )
        ]
        return instances

    @cached_property
    def messages(self):
        return self._get_instances("Message")

    @cached_property
    def callback_queries(self):
        return self._get_instances("CallbackQuery")

    @cached_property
    def updates(self):
        return self._get_instances("Update")

    @cached_property
    def message(self):
        """Return the last updated/created message."""
        return self.messages[-1] if self.messages else None

    @cached_property
    def callback_query(self):
        """Return the last updated/created callback query."""
        return self.callback_queries[-1] if self.callback_queries else None

    @cached_property
    def update(self):
        """Return the last updated/created update."""
        return self.updates[-1] if self.updates else None

    @cached_property
    def inline_keyboard(self):
        if hasattr(self.message, "reply_markup"):
            return self.message.reply_markup.inline_keyboard

    @cached_property
    def inline_keyboard_labels(self):
        labels = []
        if hasattr(self.message, "reply_markup"):
            for row in self.message.reply_markup.inline_keyboard:
                for button in row:
                    labels.append(button.text)
        return labels

    @property
    def operation(self):
        """
        Return the last operation that was performed.

        Possible values are:
        - ClientResponse.UPDATE
        - ClientResponse.NEW
        """
        try:
            last_created = [
                c["created"]
                for c in filter(
                    lambda c: c["model"] == "Message",
                    self.changed,
                )
            ][-1]
        except IndexError:
            return None
        else:
            return ClientResponse.NEW if last_created else ClientResponse.UPDATE

    @cached_property
    def text(self):
        if self.message:
            return self.message.text
        if self.callback_query:
            return self.callback_query.data

    def __contains__(self, item):
        return item in self.text

    def __str__(self):
        if self.text is not None:
            return f"Response text: {self.text}"
        else:
            return "Response is unsuccessful"


class TestCase(TransactionTestCase):
    reset_sequences = True
    bot_name = None

    def get_bot(self) -> Bot:
        if self.bot_name is not None:
            try:
                bot_settings = next(
                    bot_settings
                    for bot_settings in settings.DJANGO_CHATBOT["BOTS"]
                    if bot_settings.get("TEST_NAME") == self.bot_name
                )
            except StopIteration:
                raise ValueError(
                    f"Bot with test name {self.bot_name} not found in settings.DJANGO_CHATBOT['BOTS']"  # noqa
                )
        else:
            bot_settings = settings.DJANGO_CHATBOT["BOTS"][0]
        bot = Bot.objects.create(
            name=bot_settings["NAME"],
            token=bot_settings["TOKEN"],
            root_handlerconf=bot_settings["ROOT_HANDLERCONF"],
            test_mode=True,
        )
        return bot

    def _pre_setup(self):
        super()._pre_setup()
        self.bot = self.get_bot()
        self.bot.test_mode_on()
        self.user = ClientUser(bot=self.bot)
        self.client = Client(self.user)

        def on_changed(sender, instance, created, **kwargs):
            if sender in [Update, Message, CallbackQuery]:
                changes = {
                    "created": created,
                    "instance": instance,
                    "model": sender.__name__,
                }
                self.client._changed.append(changes)

        telegram_instance.connect(on_changed, weak=False)

    def _post_teardown(self):
        post_save.disconnect(dispatch_uid="django_chatbot_test_case")
        super()._post_teardown()

    def assertContains(self, response, text, msg=""):
        return self.assertTrue(
            text in response.text, msg + f"Couldn't find '{text}' in `{response.text}`"
        )
