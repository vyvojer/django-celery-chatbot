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
from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone

from django_chatbot.models import Bot, CallbackQuery, Chat, Message, Update, User
from django_chatbot.telegram import types
from django_chatbot.tests.tests import (
    ClientResponse,
    ClientUser,
    START_USER_ID,
    TestCase as ChatbotTestCase,
)
from factories.factories import BotFactory, ChatFactory, UpdateFactory


@patch("django_chatbot.tests.tests.Dispatcher")
class ClientUserTestCase(TestCase):
    def setUp(self) -> None:
        self.bot = Bot.objects.create(
            name="bot",
            token="token",
        )
        self.another_bot = Bot.objects.create(
            name="another_bot",
            token="another_token",
        )

    @patch.object(ClientUser, "_next_user_id")
    def test_init(self, mocked_next_user_id: Mock, mocked_dispatcher: Mock):
        mocked_next_user_id.return_value = 100
        test_user = ClientUser(bot=self.bot)

        self.assertEqual(test_user.user_id, 100)
        self.assertEqual(test_user.username, "test_user_100")
        self.assertEqual(test_user.bot, self.bot)
        user = User.objects.first()
        self.assertEqual(test_user.user, user)
        self.assertEqual(test_user.user.user_id, test_user.user_id)
        self.assertEqual(test_user.user.username, test_user.username)
        self.assertEqual(test_user.user.first_name, test_user.username)
        self.assertEqual(test_user.user.last_name, test_user.username)

    def test_next_update_id(self, mocked_dispatcher: Mock):
        """update_id must be unique"""
        now = timezone.now()
        mock_user = ClientUser(bot=self.bot)
        another_chat = Chat.objects.create(
            bot=self.another_bot,
            chat_id=18,
            type="private",
        )
        now = timezone.now()
        message_1 = Message.objects.create(
            message_id=7, chat=mock_user.chat, date=now, text="message_1"
        )
        message_2_2 = Message.objects.create(
            message_id=8, chat=mock_user.chat, date=now, text="message_2_2"
        )
        message_2_1 = Message.objects.create(
            message_id=9, chat=another_chat, date=now, text="message_2_1"
        )
        Update.objects.create(update_id=7, bot=self.bot, message=message_1)
        Update.objects.create(update_id=9, bot=self.bot, message=message_2_2)
        Update.objects.create(update_id=8, bot=self.bot, message=message_2_1)

        self.assertEqual(mock_user._next_update_id(), 10)

    def test_next_message_id(self, mocked_dispatcher: Mock):
        """chat_id + message_id must be unique"""
        mock_user = ClientUser(bot=self.bot)
        another_chat = Chat.objects.create(
            bot=self.another_bot,
            chat_id=18,
            type="private",
        )
        now = timezone.now()
        Message.objects.create(
            message_id=7, chat=mock_user.chat, date=now, text="message_1"
        )
        Message.objects.create(
            message_id=8, chat=mock_user.chat, date=now, text="message_2_2"
        )
        Message.objects.create(
            message_id=9, chat=another_chat, date=now, text="message_2_1"
        )

        self.assertEqual(mock_user._next_message_id(), 9)

    def test_next_callback_query(self, mocked_dispatcher: Mock):
        mock_user = ClientUser(bot=self.bot)
        now = timezone.now()
        message_1 = Message.objects.create(
            message_id=7, chat=mock_user.chat, date=now, text="message_1"
        )
        message_2 = Message.objects.create(
            message_id=8, chat=mock_user.chat, date=now, text="message_2"
        )
        CallbackQuery.objects.create(
            callback_query_id="22",
            bot=self.bot,
            from_user=mock_user.user,
            message=message_1,
        )
        CallbackQuery.objects.create(
            callback_query_id="23",
            bot=self.bot,
            from_user=mock_user.user,
            message=message_2,
        )
        self.assertEqual(mock_user._next_callback_query_id(), "24")

    def test_callback_queries(self, mocked_dispatcher: Mock):
        mock_user = ClientUser(bot=self.bot)
        another_user = ClientUser(bot=self.bot)
        now = timezone.now()
        message_1 = Message.objects.create(
            message_id=7, chat=mock_user.chat, date=now, text="message_1"
        )
        message_2 = Message.objects.create(
            message_id=8, chat=mock_user.chat, date=now, text="message_2"
        )
        message_3 = Message.objects.create(
            message_id=8, chat=another_user.chat, date=now, text="message_2"
        )
        callback_query_1 = CallbackQuery.objects.create(
            callback_query_id="22",
            bot=self.bot,
            from_user=mock_user.user,
            message=message_1,
        )
        callback_query_2 = CallbackQuery.objects.create(
            callback_query_id="23",
            bot=self.bot,
            from_user=mock_user.user,
            message=message_2,
        )
        CallbackQuery.objects.create(
            callback_query_id="24",
            bot=self.bot,
            from_user=another_user.user,
            message=message_3,
        )

        self.assertQuerysetEqual(
            mock_user.callback_queries(),
            [callback_query_2, callback_query_1],
            transform=lambda x: x,
        )

    @patch("django_chatbot.tests.tests.timezone.now")
    @patch.object(ClientUser, "_next_message_id")
    @patch.object(ClientUser, "_next_update_id")
    def test_send_message(
        self,
        mocked_next_update_id: Mock,
        mocked_next_message_id: Mock,
        mocked_now: Mock,
        mocked_dispatcher: Mock,
    ):
        now = timezone.datetime(2000, 1, 1, tzinfo=timezone.utc)
        mocked_now.return_value = now
        mocked_next_message_id.return_value = 42
        mocked_next_update_id.return_value = 142
        test_user = ClientUser(bot=self.bot, username="u")

        test_user.send_message("Help")

        user = types.User(
            id=START_USER_ID, is_bot=False, username="u", first_name="u", last_name="u"
        )
        chat = types.Chat(
            id=START_USER_ID,
            type="private",
            username="u",
            first_name="u",
            last_name="u",
        )
        message = types.Message(
            message_id=42, date=now, chat=chat, from_user=user, text="Help"
        )
        update = types.Update(update_id=142, message=message)
        update_data = update.to_dict(date_as_timestamp=True)
        mocked_dispatcher.return_value.dispatch.assert_called_with(
            update_data=update_data
        )

    @patch("django_chatbot.tests.tests.timezone.now")
    @patch.object(ClientUser, "_next_message_id")
    @patch.object(ClientUser, "_next_update_id")
    def test_send_message__with_commands(
        self,
        mocked_next_update_id: Mock,
        mocked_next_message_id: Mock,
        mocked_now: Mock,
        mocked_dispatcher: Mock,
    ):
        now = timezone.datetime(2000, 1, 1, tzinfo=timezone.utc)
        mocked_now.return_value = now
        mocked_next_message_id.return_value = 42
        mocked_next_update_id.return_value = 142
        test_user = ClientUser(bot=self.bot, username="u")

        test_user.send_message("/start /help")

        user = types.User(
            id=START_USER_ID, is_bot=False, username="u", first_name="u", last_name="u"
        )
        chat = types.Chat(
            id=START_USER_ID,
            type="private",
            username="u",
            first_name="u",
            last_name="u",
        )
        message = types.Message(
            message_id=42,
            date=now,
            chat=chat,
            from_user=user,
            text="/start /help",
            entities=[
                types.MessageEntity(type="bot_command", offset=0, length=6),
                types.MessageEntity(type="bot_command", offset=7, length=5),
            ],
        )
        update = types.Update(update_id=142, message=message)
        update_data = update.to_dict(date_as_timestamp=True)
        test_user.dispatcher.dispatch.assert_called_with(update_data=update_data)

    def test_extract_entities(self, mocked_dispatcher: Mock):
        entities = ClientUser._extract_entities(text="/start /help")

        expected_entities = [
            {"offset": 0, "length": 6, "type": "bot_command"},
            {"offset": 7, "length": 5, "type": "bot_command"},
        ]
        self.assertEqual(expected_entities, entities)

    @patch("django_chatbot.tests.tests.timezone.now")
    @patch.object(ClientUser, "_next_message_id")
    @patch.object(ClientUser, "_next_update_id")
    def test_send_callback_query(
        self,
        mocked_next_update_id: Mock,
        mocked_next_message_id: Mock,
        mocked_now: Mock,
        mocked_dispatcher: Mock,
    ):
        now = timezone.datetime(2000, 1, 1, tzinfo=timezone.utc)
        mocked_now.return_value = now
        mocked_next_message_id.return_value = 42
        mocked_next_update_id.return_value = 142
        test_user = ClientUser(self.bot, username="u")
        message = Message.objects.create(
            chat=test_user.chat,
            date=timezone.now(),
            message_id=test_user._next_message_id(),
            text="Yes of No?",
            _reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton("Yes", callback_data="yes")],
                    [types.InlineKeyboardButton("No", callback_data="no")],
                ]
            ).to_dict(),
        )

        test_user.send_callback_query(data="yes", markup_message=message)

        user = types.User(
            id=START_USER_ID, is_bot=False, username="u", first_name="u", last_name="u"
        )
        chat = types.Chat(
            id=START_USER_ID,
            type="private",
            username="u",
            first_name="u",
            last_name="u",
        )
        message = types.Message(
            message_id=message.message_id,
            date=message.date,
            chat=chat,
        )
        callback_query = types.CallbackQuery(
            id="1", from_user=user, chat_instance="1", message=message, data="yes"
        )

        update = types.Update(update_id=142, callback_query=callback_query)
        update_data = update.to_dict(date_as_timestamp=True)
        test_user.dispatcher.dispatch.assert_called_with(update_data=update_data)

    @patch("django_chatbot.tests.tests.timezone.now")
    @patch.object(ClientUser, "_next_message_id")
    @patch.object(ClientUser, "_next_update_id")
    def test_send_callback_query_default_message(
        self,
        mocked_next_update_id: Mock,
        mocked_next_message_id: Mock,
        mocked_now: Mock,
        mocked_dispatcher: Mock,
    ):
        now = timezone.datetime(2000, 1, 1, tzinfo=timezone.utc)
        mocked_now.return_value = now
        mocked_next_message_id.return_value = 42
        mocked_next_update_id.return_value = 142
        test_user = ClientUser(self.bot, username="u")
        message = Message.objects.create(
            chat=test_user.chat,
            date=timezone.now(),
            message_id=test_user._next_message_id(),
            text="Yes of No?",
            _reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton("Yes", callback_data="yes")],
                    [types.InlineKeyboardButton("No", callback_data="no")],
                ]
            ).to_dict(),
        )

        test_user.send_callback_query(data="yes")

        user = types.User(
            id=START_USER_ID, is_bot=False, username="u", first_name="u", last_name="u"
        )
        chat = types.Chat(
            id=START_USER_ID,
            type="private",
            username="u",
            first_name="u",
            last_name="u",
        )
        message = types.Message(
            message_id=message.message_id,
            date=message.date,
            chat=chat,
        )
        callback_query = types.CallbackQuery(
            id="1", from_user=user, chat_instance="1", message=message, data="yes"
        )

        update = types.Update(update_id=142, callback_query=callback_query)
        update_data = update.to_dict(date_as_timestamp=True)
        test_user.dispatcher.dispatch.assert_called_with(update_data=update_data)


class ClientResponseTest(TestCase):
    def setUp(self):
        self.bot = BotFactory()
        self.chat = ChatFactory(bot=self.bot)

    def test_changed(self):
        update_1 = UpdateFactory(bot=self.bot)
        update_2 = UpdateFactory(bot=self.bot)

        changed_before = [
            {"model": "Update", "instance": update_1, "created": True},
        ]
        changed_after = [
            {"model": "Update", "instance": update_1, "created": True},
            {"model": "Update", "instance": update_2, "created": True},
        ]

        client_response = ClientResponse(self.bot, changed_before, changed_after)

        self.assertEqual(
            client_response.changed,
            [
                {"model": "Update", "instance": update_2, "created": True},
            ],
        )

    def test_text(self):
        update = UpdateFactory(bot=self.bot, message__text="text")

        changed_before = []
        changed_after = [
            {"model": "Update", "instance": update, "created": True},
            {"model": "Message", "instance": update.message, "created": True},
        ]

        client_response = ClientResponse(self.bot, changed_before, changed_after)

        self.assertEqual(client_response.text, "text")


class TestCaseTest(ChatbotTestCase):
    def test_changed_is_emtpy_when_no_changes(self):
        self.assertEqual(self.client._changed, [])

    def test_changed_add_new_telegram_object(self):
        update = UpdateFactory()
        message = update.message

        self.assertIn(
            {"model": "Message", "instance": message, "created": True},
            self.client._changed,
        )
        self.assertIn(
            {"model": "Update", "instance": update, "created": True},
            self.client._changed,
        )
