from unittest.mock import Mock, call, patch

from django.test import TestCase, override_settings
from django.utils import timezone
from factories.factories import UpdateFactory

from django_chatbot.models import Bot, Chat, Message, User
from django_chatbot.telegram.api import Api, TelegramError
from django_chatbot.telegram.types import Chat as TelegramChat
from django_chatbot.telegram.types import InlineKeyboardButton, InlineKeyboardMarkup
from django_chatbot.telegram.types import Message as TelegramMessage
from django_chatbot.telegram.types import MessageEntity
from django_chatbot.telegram.types import Update as TelegramUpdate
from django_chatbot.telegram.types import User as TelegramUser
from django_chatbot.telegram.types import WebhookInfo


class BotTestCase(TestCase):
    def setUp(self) -> None:
        self.bot = Bot.objects.create(
            name="@TestBot",
            token="bot-token",
        )

    def test_token_slug(self):
        bot = Bot.objects.create(name="TestBot", token="123:xxx-yyyy")

        self.assertEqual(bot.token_slug, "123xxx-yyyy")

    def test_me(self):
        bot = Bot(
            _me={
                "id": 7,
                "is_bot": True,
                "first_name": "first_name",
                "username": "username",
            }
        )

        self.assertEqual(
            bot.me,
            TelegramUser(
                id=7,
                is_bot=True,
                first_name="first_name",
                username="username",
            ),
        )

    def test_webhook_info(self):
        bot = Bot(
            _webhook_info={
                "url": "https://example.com",
                "has_custom_certificate": False,
                "pending_update_count": 0,
            }
        )

        self.assertEqual(
            bot.webhook_info,
            WebhookInfo(
                url="https://example.com",
                has_custom_certificate=False,
                pending_update_count=0,
            ),
        )

    @patch("django_chatbot.models.Api")
    def test_get_me__successful(self, mocked_api):
        telegram_user = TelegramUser(
            id=7,
            is_bot=True,
            first_name="first_name",
            username="username",
        )
        mocked_api.return_value.get_me.return_value = telegram_user

        me = self.bot.get_me()

        mocked_api.assert_called_with(token="bot-token")
        self.assertEqual(me, telegram_user)
        self.bot.refresh_from_db()
        self.assertEqual(
            self.bot._me,
            {
                "id": 7,
                "is_bot": True,
                "first_name": "first_name",
                "username": "username",
            },
        )
        self.bot.refresh_from_db()
        self.assertEqual(self.bot.update_successful, True)

    @patch("django_chatbot.models.Api")
    def test_get_me__telegram_error(self, mocked_api):
        response = Mock()
        error = TelegramError(
            reason="Not found",
            url="url",
            status_code=404,
            response=response,
            api_code="404",
        )
        mocked_api.return_value.get_me.side_effect = [error]

        with self.assertRaises(TelegramError) as raised:
            self.bot.get_me()

        self.assertEqual(raised.exception, error)
        self.assertEqual(self.bot.update_successful, False)

    @patch("django_chatbot.models.Api")
    def test_get_webhook_info__successful(self, mocked_api):
        webhook_info = WebhookInfo(
            url="https://example.com",
            has_custom_certificate=False,
            pending_update_count=0,
        )
        mocked_api.return_value.get_webhook_info.return_value = webhook_info

        info = self.bot.get_webhook_info()

        mocked_api.assert_called_with(token="bot-token")
        self.assertEqual(info, webhook_info)
        self.bot.refresh_from_db()
        self.assertEqual(
            self.bot._webhook_info,
            {
                "url": "https://example.com",
                "has_custom_certificate": False,
                "pending_update_count": 0,
            },
        )
        self.bot.refresh_from_db()
        self.assertEqual(self.bot.update_successful, True)

    @patch("django_chatbot.models.Api")
    def test_get_webhook_info__telegram_error(self, mocked_api):
        error = TelegramError(
            reason="Not found",
            url="url",
            status_code=404,
            response=Mock(),
            api_code="404",
        )

        mocked_api.return_value.get_webhook_info.side_effect = [error]

        with self.assertRaises(TelegramError) as raised:
            self.bot.get_webhook_info()

        self.assertEqual(raised.exception, error)
        mocked_api.assert_called_with(token="bot-token")
        self.bot.refresh_from_db()
        self.assertEqual(self.bot.update_successful, False)

    @patch("django_chatbot.models.Api")
    def test_set_webhook__successful(self, mocked_api):
        mocked_api.return_value.set_webhook.return_value = True

        result = self.bot.set_webhook(
            domain="http://example.com",
            max_connections=42,
            allowed_updates=["message"],
        )

        mocked_api.assert_called_with(token="bot-token")
        mocked_api.return_value.set_webhook.assert_called_with(
            url="http://example.com/chatbot/webhook/bot-token/",
            max_connections=42,
            allowed_updates=["message"],
        )
        self.assertEqual(result, True)
        self.bot.refresh_from_db()
        self.assertEqual(self.bot.update_successful, True)
        self.assertEqual(self.bot.webhook_enabled, True)

    @patch("django_chatbot.models.Api")
    def test_set_webhook__telegram_error(self, mocked_api):
        self.bot.webhook_enabled = False
        self.bot.save()
        error = TelegramError(
            reason="Not found",
            url="url",
            status_code=404,
            response=Mock(),
            api_code="404",
        )
        mocked_api.return_value.set_webhook.side_effect = [error]

        with self.assertRaises(TelegramError) as raised:
            self.bot.set_webhook(
                domain="http://example.com",
                max_connections=42,
                allowed_updates=["message"],
            )

        mocked_api.assert_called_with(token="bot-token")
        mocked_api.return_value.set_webhook.assert_called_with(
            url="http://example.com/chatbot/webhook/bot-token/",
            max_connections=42,
            allowed_updates=["message"],
        )
        self.assertEqual(raised.exception, error)
        self.bot.refresh_from_db()
        self.assertEqual(self.bot.update_successful, False)
        self.assertEqual(self.bot.webhook_enabled, False)

    @patch("django_chatbot.models.Api")
    def test_delete_webhook__successfull(self, mocked_api):
        mocked_api.return_value.delete_webhook.return_value = True

        self.bot.webhook_enabled = True
        self.bot.save()

        result = self.bot.delete_webhook(
            drop_pending_updates=True,
        )

        mocked_api.assert_called_with(token="bot-token")
        mocked_api.return_value.delete_webhook.assert_called_with(
            drop_pending_updates=True,
        )
        self.assertEqual(result, True)
        self.bot.refresh_from_db()
        self.assertEqual(self.bot.update_successful, True)
        self.assertEqual(self.bot.webhook_enabled, False)

    @override_settings(DJANGO_CHATBOT={"GET_UPDATES_LIMIT": 2})
    @patch("django_chatbot.models.Api")
    def test_get_updates__successful(self, mocked_api):
        mocked_api.return_value.get_updates.side_effect = lambda offset, limit: {
            0: [
                TelegramUpdate(update_id=1),
                TelegramUpdate(update_id=2),
            ],
            3: [
                TelegramUpdate(update_id=3),
                TelegramUpdate(update_id=4),
            ],
            5: [
                TelegramUpdate(update_id=5),
                TelegramUpdate(update_id=6),
            ],
            7: [
                TelegramUpdate(update_id=7),
            ],
        }[offset]

        result = self.bot.get_updates()
        result = list(result)

        mocked_api.assert_called_with(token="bot-token")
        self.assertEqual(
            mocked_api.return_value.get_updates.mock_calls,
            [
                call(offset=0, limit=2),
                call(offset=3, limit=2),
                call(offset=5, limit=2),
                call(offset=7, limit=2),
            ],
        )
        self.assertEqual(
            result,
            [
                TelegramUpdate(update_id=1),
                TelegramUpdate(update_id=2),
                TelegramUpdate(update_id=3),
                TelegramUpdate(update_id=4),
                TelegramUpdate(update_id=5),
                TelegramUpdate(update_id=6),
                TelegramUpdate(update_id=7),
            ],
        )

    @override_settings(DJANGO_CHATBOT={"GET_UPDATES_LIMIT": 2})
    @patch("django_chatbot.models.Api")
    def test_get_updates__with_offset(self, mocked_api):
        UpdateFactory(bot=self.bot, update_id=2)
        mocked_api.return_value.get_updates.side_effect = lambda offset, limit: {
            0: [
                TelegramUpdate(update_id=1),
                TelegramUpdate(update_id=2),
            ],
            3: [
                TelegramUpdate(update_id=3),
                TelegramUpdate(update_id=4),
            ],
            5: [
                TelegramUpdate(update_id=5),
                TelegramUpdate(update_id=6),
            ],
            7: [
                TelegramUpdate(update_id=7),
            ],
        }[offset]

        result = self.bot.get_updates()
        result = list(result)

        mocked_api.assert_called_with(token="bot-token")
        self.assertEqual(
            mocked_api.return_value.get_updates.mock_calls,
            [
                call(offset=3, limit=2),
                call(offset=5, limit=2),
                call(offset=7, limit=2),
            ],
        )
        self.assertEqual(
            result,
            [
                TelegramUpdate(update_id=3),
                TelegramUpdate(update_id=4),
                TelegramUpdate(update_id=5),
                TelegramUpdate(update_id=6),
                TelegramUpdate(update_id=7),
            ],
        )


class UserTestCase(TestCase):
    def setUp(self) -> None:
        self.bot = Bot.objects.create(name="bot", token="token")
        self.another_bot = Bot.objects.create(name="another_bot", token="another_token")
        self.user = User.objects.create(
            user_id=1,
            is_bot=False,
        )
        self.bot_user = User.objects.create(
            user_id=100,
            is_bot=True,
        )

    def test_chat(self):
        chat = Chat.objects.create(bot=self.bot, chat_id=1, type="private")
        Message.objects.create(
            message_id=1,
            date=timezone.datetime(2000, 1, 1, tzinfo=timezone.utc),
            chat=chat,
            from_user=self.user,
        )
        Message.objects.create(
            message_id=2,
            date=timezone.datetime(2000, 1, 1, 1, tzinfo=timezone.utc),
            chat=chat,
            from_user=self.bot_user,
        )
        Message.objects.create(
            message_id=3,
            date=timezone.datetime(2000, 1, 1, 2, tzinfo=timezone.utc),
            chat=chat,
            from_user=self.user,
        )
        another_chat = Chat.objects.create(
            bot=self.another_bot, chat_id=1, type="private"
        )

        self.assertEqual(self.user.chat(self.bot), chat)
        self.assertEqual(self.user.chat(self.another_bot), another_chat)


class ChatTestCase(TestCase):
    def setUp(self) -> None:
        bot = Bot.objects.create(
            name="bot",
            token="token",
        )
        self.chat = Chat.objects.create(
            bot=bot,
            chat_id=42,
            type="private",
        )

    @patch.object(Api, "send_message")
    def test_reply(self, mocked_send_message: Mock):
        mocked_send_message.return_value = TelegramMessage.from_dict(
            {
                "message_id": 42,
                "from": {
                    "id": 142,
                    "is_bot": True,
                    "first_name": "bot_name",
                    "username": "bot_user_name",
                },
                "chat": {"id": 42, "type": "private"},
                "date": 1,
                "text": "text",
            }
        )

        self.chat.reply(text="Reply")

        mocked_send_message.assert_called_with(
            chat_id=self.chat.chat_id,
            text="Reply",
            parse_mode=None,
        )

        user = User.objects.first()
        message = Message.objects.first()

        self.assertEqual(message.chat, self.chat)
        self.assertEqual(message.from_user, user)


class MessageTestCase(TestCase):
    def test_entities(self):
        message = Message(
            text="/start /help",
            _entities=[
                {"offset": 0, "length": 6, "type": "bot_command"},
                {"offset": 7, "length": 5, "type": "bot_command"},
            ],
        )

        entities = message.entities

        self.assertEqual(
            entities,
            [
                MessageEntity(
                    type="bot_command",
                    text="/start",
                    offset=0,
                    length=6,
                ),
                MessageEntity(
                    type="bot_command",
                    text="/help",
                    offset=7,
                    length=5,
                ),
            ],
        )

    @patch.object(Api, "send_message")
    def test_reply(self, mocked_send_message: Mock):
        bot = Bot.objects.create(
            name="bot",
            token="token",
        )
        chat = Chat.objects.create(
            bot=bot,
            chat_id=142,
            type="private",
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
            chat=TelegramChat(id=142, type="private"),
            text="Reply",
            reply_to_message=TelegramMessage(
                message_id=42,
                chat=TelegramChat(id=142, type="private"),
                date=timezone.datetime(2000, 1, 1, tzinfo=timezone.utc),
            ),
        )

        incoming_message.reply(
            text="Reply",
            reply=True,
        )

        mocked_send_message.assert_called_with(
            chat_id=chat.chat_id,
            text="Reply",
            parse_mode=None,
            reply_to_message_id=42,
        )

        user = User.objects.first()
        message = Message.objects.last()

        self.assertEqual(message.direction, Message.DIRECTION_OUT)
        self.assertEqual(message.message_id, 43)
        self.assertEqual(
            message.date, timezone.datetime(1999, 12, 31, tzinfo=timezone.utc)
        )
        self.assertEqual(message.chat, chat)
        self.assertEqual(message.from_user, user)
        self.assertEqual(message.reply_to_message, incoming_message)
        self.assertEqual(incoming_message.reply_message, message)

    @patch.object(Api, "edit_message_text")
    def test_edit(self, mocked_edit_message_text: Mock):
        old_text = "old text"
        new_text = "new text"
        old_markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton("Yes", callback_data="yes"),
                    InlineKeyboardButton("No", callback_data="no"),
                ]
            ]
        )
        new_markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton("Yes and yes", callback_data="yes"),
                ]
            ]
        )
        bot = Bot.objects.create(
            name="bot",
            token="token",
        )
        chat = Chat.objects.create(
            bot=bot,
            chat_id=142,
            type="private",
        )
        message = Message.objects.create(
            message_id=42,
            date=timezone.datetime(1999, 12, 31, tzinfo=timezone.utc),
            chat=chat,
            text=old_text,
            _reply_markup=old_markup.to_dict(),
        )
        mocked_edit_message_text.return_value = TelegramMessage(
            message_id=42,
            date=timezone.datetime(1999, 12, 31, tzinfo=timezone.utc),
            chat=TelegramChat(id=142, type="private"),
            text=new_text,
            reply_markup=new_markup,
        )

        returned = message.edit(
            text=new_text,
            reply_markup=new_markup,
        )
        mocked_edit_message_text.assert_called_with(
            text=new_text,
            chat_id=chat.chat_id,
            message_id=message.message_id,
            parse_mode=None,
            entities=None,
            disable_web_page_preview=None,
            reply_markup=new_markup,
        )

        message.refresh_from_db()

        self.assertEqual(message.reply_markup, new_markup)
        self.assertEqual(message.text, new_text)
        self.assertEqual(message, returned)

    @patch.object(Api, "edit_message_reply_markup")
    def test_edit_reply_markup(self, mocked_edit_message_reply_markup: Mock):
        old_markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton("Yes", callback_data="yes"),
                    InlineKeyboardButton("No", callback_data="no"),
                ]
            ]
        )
        new_markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton("Yes and yes", callback_data="yes"),
                ]
            ]
        )
        bot = Bot.objects.create(
            name="bot",
            token="token",
        )
        chat = Chat.objects.create(
            bot=bot,
            chat_id=142,
            type="private",
        )
        message = Message.objects.create(
            message_id=42,
            date=timezone.datetime(1999, 12, 31, tzinfo=timezone.utc),
            chat=chat,
            _reply_markup=old_markup.to_dict(),
        )
        mocked_edit_message_reply_markup.return_value = TelegramMessage(
            message_id=42,
            date=timezone.datetime(1999, 12, 31, tzinfo=timezone.utc),
            chat=TelegramChat(id=142, type="private"),
            reply_markup=new_markup,
        )

        returned = message.edit_reply_markup(
            reply_markup=new_markup,
        )

        mocked_edit_message_reply_markup.assert_called_with(
            chat_id=chat.chat_id, message_id=message.message_id, reply_markup=new_markup
        )

        message.refresh_from_db()

        self.assertEqual(message.reply_markup, new_markup)
        self.assertEqual(message, returned)
