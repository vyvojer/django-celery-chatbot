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

from django_chatbot.handlers import DefaultHandler
from django_chatbot.models import Bot, Chat, Message, Update, User
from django_chatbot.telegram import types
from django_chatbot.tests import (
    START_USER_ID,
    MockUser,
    TestCase as ChatbotTestCase)


@patch("django_chatbot.tests.Dispatcher")
class MockUserTestCase(TestCase):

    def setUp(self) -> None:
        self.bot = Bot.objects.create(
            name='bot',
            token='token',
        )
        self.another_bot = Bot.objects.create(
            name='another_bot',
            token='another_token',
        )

    @patch.object(MockUser, "_next_user_id")
    def test_init(self, mocked_next_user_id: Mock, mocked_dispatcher: Mock):
        mocked_next_user_id.return_value = 100
        test_user = MockUser(bot=self.bot)

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
        mock_user = MockUser(bot=self.bot)
        another_chat = Chat.objects.create(
            bot=self.another_bot, chat_id=18, type='private',
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
        Update.objects.create(
            update_id=7, bot=self.bot, message=message_1
        )
        Update.objects.create(
            update_id=9, bot=self.bot, message=message_2_2
        )
        Update.objects.create(
            update_id=8, bot=self.bot, message=message_2_1
        )

        self.assertEqual(mock_user._next_update_id(), 10)

    def test_next_message_id(self, mocked_dispatcher: Mock):
        """chat_id + message_id must be unique"""
        mock_user = MockUser(bot=self.bot)
        another_chat = Chat.objects.create(
            bot=self.another_bot, chat_id=18, type='private',
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

    @patch("django_chatbot.tests.timezone.now")
    @patch.object(MockUser, '_next_message_id')
    @patch.object(MockUser, '_next_update_id')
    def test_send_message(self,
                          mocked_next_update_id: Mock,
                          mocked_next_message_id: Mock,
                          mocked_now: Mock,
                          mocked_dispatcher: Mock):
        now = timezone.datetime(2000, 1, 1, tzinfo=timezone.utc)
        mocked_now.return_value = now
        mocked_next_message_id.return_value = 42
        mocked_next_update_id.return_value = 142
        test_user = MockUser(bot=self.bot, username='u')

        test_user.send_message("Help")

        user = types.User(
            id=START_USER_ID, is_bot=False,
            username='u', first_name='u', last_name='u'
        )
        chat = types.Chat(
            id=START_USER_ID, type='private',
            username='u', first_name='u', last_name='u'
        )
        message = types.Message(
            message_id=42, date=now, chat=chat, from_user=user, text='Help'
        )
        update = types.Update(update_id=142, message=message)
        update_data = update.to_dict(date_as_timestamp=True)
        mocked_dispatcher.return_value.dispatch.assert_called_with(
            update_data=update_data
        )

    @patch("django_chatbot.tests.timezone.now")
    @patch.object(MockUser, '_next_message_id')
    @patch.object(MockUser, '_next_update_id')
    def test_send_message__with_commands(self,
                                         mocked_next_update_id: Mock,
                                         mocked_next_message_id: Mock,
                                         mocked_now: Mock,
                                         mocked_dispatcher: Mock):
        now = timezone.datetime(2000, 1, 1, tzinfo=timezone.utc)
        mocked_now.return_value = now
        mocked_next_message_id.return_value = 42
        mocked_next_update_id.return_value = 142
        test_user = MockUser(bot=self.bot, username='u')

        test_user.send_message("/start /help")

        user = types.User(
            id=START_USER_ID, is_bot=False,
            username='u', first_name='u', last_name='u'
        )
        chat = types.Chat(
            id=START_USER_ID, type='private',
            username='u', first_name='u', last_name='u'
        )
        message = types.Message(
            message_id=42, date=now, chat=chat, from_user=user,
            text='/start /help',
            entities=[
                types.MessageEntity(
                    type='bot_command', offset=0, length=6
                ),
                types.MessageEntity(
                    type='bot_command', offset=7, length=5
                ),
            ]
        )
        update = types.Update(update_id=142, message=message)
        update_data = update.to_dict(date_as_timestamp=True)
        test_user.dispatcher.dispatch.assert_called_with(
            update_data=update_data
        )

    def test_extract_entities(self, mocked_dispatcher: Mock):
        entities = MockUser._extract_entities(text='/start /help')

        expected_entities = [
            {
                'offset': 0,
                'length': 6,
                'type': 'bot_command'
            },
            {
                'offset': 7,
                'length': 5,
                'type': 'bot_command'
            },
        ]
        self.assertEqual(expected_entities, entities)


class TestCaseTestCase(ChatbotTestCase):
    def setUp(self) -> None:
        super().setUp()

        def callback(update: Update):
            update.message.reply(text='answer')

        self.handler = DefaultHandler("default", callback=callback)
        now = timezone.datetime(2001, 1, 1, tzinfo=timezone.utc)
        bot = Bot.objects.create(name="Bot", token="token")
        user = User.objects.create(user_id=2, is_bot=False, username='User')
        self.chat = Chat.objects.create(
            chat_id='2', type="private", bot=bot, username='User'
        )
        message = Message.objects.create(
            direction=Message.DIRECTION_IN,
            message_id="1",
            date=now,
            text="Help",
            chat=self.chat,
            from_user=user,
        )
        self.update = Update.objects.create(
            update_id="1",
            bot=bot,
            message=message,
        )

    @patch("django_chatbot.telegram.api.requests")
    def test_requests_get_will_not_invoked(self, mocked_requests):
        """Api.send_message must be monkey patched"""

        self.handler.handle_update(self.update)

        mocked_requests.get.assert_not_called()
        mocked_requests.post.assert_not_called()

    def test_patched_send_message__return_right_message(self):
        self.handler.handle_update(self.update)

        self.assertEqual(Message.objects.count(), 2)
        answer = Message.objects.get(direction=Message.DIRECTION_OUT)
        bot_user = answer.from_user

        self.assertEqual(bot_user.user_id, 1)
        self.assertEqual(answer.from_user, bot_user)
        self.assertEqual(answer.chat, self.chat)
        self.assertEqual(answer.text, "answer")
