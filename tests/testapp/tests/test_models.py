from unittest.mock import patch, Mock

from django.test import TestCase
from django.utils import timezone

from django_chatbot.models import Bot, Message, Chat, User
from django_chatbot.telegram.api import TelegramError, Api
from django_chatbot.telegram.types import (
    Chat as TelegramChat,
    Message as TelegramMessage,
    User as TelegramUser,
    MessageEntity,
    WebhookInfo,
)


class BotTestCase(TestCase):
    def setUp(self) -> None:
        self.bot = Bot.objects.create(
            name="@TestBot",
            token="bot-token",
        )

    def test_token_slug(self):
        bot = Bot.objects.create(
            name="TestBot",
            token="123:xxx-yyyy"
        )

        self.assertEqual(bot.token_slug, "123xxx-yyyy")

    @patch("django_chatbot.models.Api")
    @patch("django_chatbot.models.timezone.now")
    def test_get_me__successfull(self, mocked_now, mocked_api):
        now = timezone.datetime(2000, 1, 1, tzinfo=timezone.utc)
        mocked_now.return_value = now
        mocked_api.return_value.get_me.return_value = TelegramUser(
            id=7,
            is_bot=True,
            first_name="first_name",
            username="username",
        )

        me = self.bot.get_me()

        mocked_api.assert_called_with(token="bot-token")
        self.assertEqual(
            me,
            {
                'ok': True,
                'result': {
                    'id': 7,
                    'is_bot': True,
                    'first_name': 'first_name',
                    'username': 'username'
                },
            }
        )
        self.bot.refresh_from_db()
        self.assertEqual(
            self.bot.me,
            {
                'id': 7,
                'is_bot': True,
                'first_name': 'first_name',
                'username': 'username'
            }
        )
        self.bot.refresh_from_db()
        self.assertEqual(self.bot.update_successful, True)
        self.assertEqual(self.bot.me_update_datetime, now)

    @patch("django_chatbot.models.Api")
    @patch("django_chatbot.models.timezone.now")
    def test_get_me__telegram_error(self, mocked_now, mocked_api):
        now = timezone.datetime(2000, 1, 1, tzinfo=timezone.utc)
        mocked_now.return_value = now
        mocked_api.return_value.get_me.side_effect = [
            TelegramError(
                reason="Not found",
                url="url",
                status_code="404",
                response="response",
                api_code="404"
            )
        ]

        me = self.bot.get_me()

        mocked_api.assert_called_with(token="bot-token")
        self.assertEqual(
            me,
            {
                'ok': False,
                'result': {
                    "reason": "Not found",
                    "url": "url",
                    "status_code": "404",
                    "response": "response",
                    "api_code": "404"
                },
            }
        )
        self.bot.refresh_from_db()
        self.assertEqual(self.bot.update_successful, False)
        self.assertEqual(self.bot.me_update_datetime, None)

    @patch("django_chatbot.models.Api")
    @patch("django_chatbot.models.timezone.now")
    def test_get_webhook_info__successfull(self, mocked_now, mocked_api):
        now = timezone.datetime(2000, 1, 1, tzinfo=timezone.utc)
        mocked_now.return_value = now
        mocked_api.return_value.get_webhook_info.return_value = WebhookInfo(
            url="https://example.com",
            has_custom_certificate=False,
            pending_update_count=0
        )

        info = self.bot.get_webhook_info()

        mocked_api.assert_called_with(token="bot-token")
        self.assertEqual(
            info,
            {
                'ok': True,
                'result': {
                    'url': 'https://example.com',
                    'has_custom_certificate': False,
                    'pending_update_count': 0
                },
            }
        )
        self.bot.refresh_from_db()
        self.assertEqual(
            self.bot.webhook_info,
            {
                'url': 'https://example.com',
                'has_custom_certificate': False,
                'pending_update_count': 0
            }
        )
        self.bot.refresh_from_db()
        self.assertEqual(self.bot.update_successful, True)
        self.assertEqual(self.bot.webhook_update_datetime, now)

    @patch("django_chatbot.models.Api")
    @patch("django_chatbot.models.timezone.now")
    def test_get_webhook_info__telegram_error(self, mocked_now, mocked_api):
        now = timezone.datetime(2000, 1, 1, tzinfo=timezone.utc)
        mocked_now.return_value = now
        mocked_api.return_value.get_webhook_info.side_effect = [
            TelegramError(
                reason="Not found",
                url="url",
                status_code="404",
                response="response",
                api_code="404"
            )
        ]

        info = self.bot.get_webhook_info()

        mocked_api.assert_called_with(token="bot-token")
        self.assertEqual(
            info,
            {
                'ok': False,
                'result': {
                    "reason": "Not found",
                    "url": "url",
                    "status_code": "404",
                    "response": "response",
                    "api_code": "404"
                },
            }
        )
        self.bot.refresh_from_db()
        self.assertEqual(self.bot.update_successful, False)
        self.assertEqual(self.bot.me_update_datetime, None)

    @patch("django_chatbot.models.Api")
    @patch("django_chatbot.models.timezone.now")
    def test_set_webhook__successfull(self, mocked_now, mocked_api):
        now = timezone.datetime(2000, 1, 1, tzinfo=timezone.utc)
        mocked_now.return_value = now
        mocked_api.return_value.set_webhook.return_value = True

        result = self.bot.set_webhook(
            domain='http://example.com',
            max_connections=42,
            allowed_updates=["message"],
        )

        mocked_api.assert_called_with(token="bot-token")
        mocked_api.return_value.set_webhook.assert_called_with(
            url='http://example.com/chatbot/webhook/bot-token/',
            max_connections=42,
            allowed_updates=["message"],
        )
        self.assertEqual(result, {"ok": True})
        self.bot.refresh_from_db()
        self.assertEqual(self.bot.update_successful, True)
        self.assertEqual(self.bot.webhook_update_datetime, now)

    @patch("django_chatbot.models.Api")
    @patch("django_chatbot.models.timezone.now")
    def test_set_webhook__telegram_error(self, mocked_now, mocked_api):
        now = timezone.datetime(2000, 1, 1, tzinfo=timezone.utc)
        mocked_now.return_value = now
        mocked_api.return_value.set_webhook.side_effect = [
            TelegramError(
                reason="Not found",
                url="url",
                status_code="404",
                response="response",
                api_code="404"
            )
        ]

        result = self.bot.set_webhook(
            domain='http://example.com',
            max_connections=42,
            allowed_updates=["message"],
        )

        mocked_api.assert_called_with(token="bot-token")
        mocked_api.return_value.set_webhook.assert_called_with(
            url='http://example.com/chatbot/webhook/bot-token/',
            max_connections=42,
            allowed_updates=["message"],
        )
        self.assertEqual(result, {
            "ok": False,
            'result': {
                "reason": "Not found",
                "url": "url",
                "status_code": "404",
                "response": "response",
                "api_code": "404"
            },
        })
        self.bot.refresh_from_db()
        self.assertEqual(self.bot.update_successful, False)
        self.assertEqual(self.bot.webhook_update_datetime, None)


class UserManagerTestCase(TestCase):
    def test_from_telegram__creates(self):
        telegram_user = TelegramUser(
            id=42,
            is_bot=False,
            first_name="first_name",
            last_name="last_name",
            username="username",
            language_code="en",
            can_join_groups=True,
            can_read_all_group_messages=True,
            supports_inline_queries=True,
        )

        User.objects.from_telegram(telegram_user)

        user = User.objects.first()
        self.assertEqual(user.user_id, 42)
        self.assertEqual(user.is_bot, False)
        self.assertEqual(user.first_name, "first_name")
        self.assertEqual(user.last_name, "last_name")
        self.assertEqual(user.username, "username")

    def test_from_telegram__existing(self):
        telegram_user = TelegramUser(
            id=42,
            is_bot=False,
            first_name="first_name",
            last_name="last_name",
            username="username",
            language_code="en",
            can_join_groups=True,
            can_read_all_group_messages=True,
            supports_inline_queries=True,
        )
        User.objects.create(
            user_id=42,
            first_name="old_first_name",
            last_name="old_last_name",
            username="username",
            language_code="en",
        )

        User.objects.from_telegram(telegram_user)

        self.assertEqual(User.objects.count(), 1)
        user = User.objects.first()
        self.assertEqual(user.user_id, 42)
        self.assertEqual(user.is_bot, False)
        self.assertEqual(user.first_name, "first_name")
        self.assertEqual(user.last_name, "last_name")
        self.assertEqual(user.username, "username")


class ChatTestCase(TestCase):
    def setUp(self) -> None:
        bot = Bot.objects.create(
            name="bot",
            token="token",
        )
        self.chat = Chat.objects.create(
            bot=bot,
            chat_id=42,
            type='private',
        )

    @patch.object(Api, 'send_message')
    def test_reply(self, mocked_send_message: Mock):
        mocked_send_message.return_value = TelegramMessage.from_dict({
            'message_id': 42,
            'from': {'id': 142,
                     'is_bot': True,
                     'first_name': 'bot_name',
                     'username': 'bot_user_name'},
            'chat': {'id': 1042,
                     'first_name': 'Fedor',
                     'last_name': 'Sumkin',
                     'username': 'fedor',
                     'type': 'private'},
            'date': 1,
            'text': 'text'})

        self.chat.reply(
            text="Reply"
        )

        mocked_send_message.assert_called_with(
            chat_id=self.chat.chat_id,
            text="Reply",
            parse_mode=None,
        )

        user = User.objects.first()
        message = Message.objects.first()

        self.assertEqual(message.chat, self.chat)
        self.assertEqual(message.from_user, user)


class MessageManagerTestCase(TestCase):
    def setUp(self) -> None:
        self.bot = Bot.objects.create(name="bot", token="token")
        self.chat = Chat.objects.create(
            bot=self.bot, chat_id=42, type="private"
        )

    def test_from_telegram(self):
        user = User.objects.create(user_id=42)
        telegram_message = TelegramMessage(
            message_id=42,
            date=timezone.datetime(2000, 1, 1, tzinfo=timezone.utc),
            chat=Chat(id=42, type="private"),
            from_user=TelegramUser(id=42, is_bot=False)
        )
        direction = Message.DIRECTION_OUT

        Message.objects.from_telegram(
            telegram_message, direction, self.chat, user
        )

        message = Message.objects.first()
        self.assertEqual(message.direction, Message.DIRECTION_OUT)
        self.assertEqual(message.message_id, 42)
        self.assertEqual(message.chat, self.chat)
        self.assertEqual(message.from_user, user)

    def test_get_message(self):
        wanted = Message.objects.create(
            message_id=42,
            date=timezone.datetime(2000, 1, 1, tzinfo=timezone.utc),
            chat=self.chat
        )

        found = Message.objects.get_message(
            telegram_message = TelegramMessage(
                message_id=wanted.message_id,
                date=timezone.datetime(1999, 12, 31, tzinfo=timezone.utc),
                chat=TelegramChat(id=self.chat.chat_id, type="private"),
            )
        )

        self.assertEqual(found, wanted)

    def test_get_message__wrong_chat_id(self):
        wanted = Message.objects.create(
            message_id=42,
            date=timezone.datetime(2000, 1, 1, tzinfo=timezone.utc),
            chat=self.chat
        )

        found = Message.objects.get_message(
            telegram_message = TelegramMessage(
                message_id=wanted.message_id,
                date=timezone.datetime(1999, 12, 31, tzinfo=timezone.utc),
                chat=TelegramChat(id=999, type="private"),
            )
        )

        self.assertEqual(found, None)





class MessageTestCase(TestCase):
    def test_entities(self):
        message = Message(
            text='/start /help',
            _entities=[
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
        )

        entities = message.entities

        self.assertEqual(
            entities,
            [
                MessageEntity(
                    type='bot_command',
                    text='/start',
                    offset=0,
                    length=6,
                ),
                MessageEntity(
                    type='bot_command',
                    text='/help',
                    offset=7,
                    length=5,
                ),
            ]
        )

    @patch.object(Api, 'send_message')
    def test_reply(self, mocked_send_message: Mock):
        bot = Bot.objects.create(
            name="bot",
            token="token",
        )
        chat = Chat.objects.create(
            bot=bot,
            chat_id=142,
            type='private',
        )
        incoming_message = Message.objects.create(
            message_id=42,
            date=timezone.datetime(2000, 1, 1, tzinfo=timezone.utc),
            chat=chat,
        )

        mocked_send_message.return_value = TelegramMessage(
            message_id=43,
            date=timezone.datetime(1999, 12, 31, tzinfo=timezone.utc),
            from_user=TelegramUser(id=1, is_bot=True),
            chat=TelegramChat(id=1, type="private"),
            text='Reply',
            reply_to_message=TelegramMessage(
                message_id=42,
                chat=TelegramChat(id=142, type="private"),
                date=timezone.datetime(2000, 1, 1, tzinfo=timezone.utc),
            ),
        )

        incoming_message.reply(
            text="Reply"
        )

        mocked_send_message.assert_called_with(
            chat_id=chat.chat_id,
            text="Reply",
            parse_mode=None,
            reply_to_message_id=42,

        )

        user = User.objects.first()
        message = Message.objects.first()

        self.assertEqual(message.direction, Message.DIRECTION_OUT)
        self.assertEqual(message.message_id, 43)
        self.assertEqual(message.date, timezone.datetime(1999, 12, 31, tzinfo=timezone.utc))
        self.assertEqual(message.chat, chat)
        self.assertEqual(message.from_user, user)
        self.assertEqual(message.reply_to_message, incoming_message)
        self.assertEqual(incoming_message.reply_message, message)
