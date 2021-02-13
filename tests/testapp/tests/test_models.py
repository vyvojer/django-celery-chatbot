from unittest.mock import patch, Mock

from django.test import TestCase
from django.utils import timezone

from django_chatbot.models import (
    Bot,
    CallbackQuery,
    Message,
    Chat,
    Update,
    User, _update_defaults
)
from django_chatbot.telegram.api import TelegramError, Api
from django_chatbot.telegram.types import (
    Animation,
    CallbackQuery as TelegramCallbackQuery,
    Chat as TelegramChat,
    ChatLocation,
    ChatPermissions,
    ChatPhoto,
    InlineKeyboardButton,
    Location,
    Message as TelegramMessage,
    Update as TelegramUpdate,
    User as TelegramUser,
    InlineKeyboardMarkup,
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

    def test_me(self):
        bot = Bot(
            _me={
                'id': 7,
                'is_bot': True,
                'first_name': 'first_name',
                'username': 'username'
            }
        )

        self.assertEqual(
            bot.me,
            TelegramUser(
                id=7,
                is_bot=True,
                first_name='first_name',
                username='username',
            )
        )

    def test_webhook_info(self):
        bot = Bot(
            _webhook_info={
                'url': 'https://example.com',
                'has_custom_certificate': False,
                'pending_update_count': 0
            }
        )

        self.assertEqual(
            bot.webhook_info,
            WebhookInfo(
                url='https://example.com',
                has_custom_certificate=False,
                pending_update_count=0
            )
        )

    @patch("django_chatbot.models.Api")
    @patch("django_chatbot.models.timezone.now")
    def test_get_me__successfull(self, mocked_now, mocked_api):
        now = timezone.datetime(2000, 1, 1, tzinfo=timezone.utc)
        mocked_now.return_value = now
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
        response = Mock()
        error = TelegramError(
            reason="Not found",
            url="url",
            status_code=404,
            response=response,
            api_code="404"
        )
        mocked_api.return_value.get_me.side_effect = [error]

        with self.assertRaises(TelegramError) as raised:
            self.bot.get_me()

        self.assertEqual(raised.exception, error)
        self.assertEqual(self.bot.update_successful, False)
        self.assertEqual(self.bot.me_update_datetime, None)

    @patch("django_chatbot.models.Api")
    @patch("django_chatbot.models.timezone.now")
    def test_get_webhook_info__successfull(self, mocked_now, mocked_api):
        now = timezone.datetime(2000, 1, 1, tzinfo=timezone.utc)
        mocked_now.return_value = now
        webhook_info = WebhookInfo(
            url="https://example.com",
            has_custom_certificate=False,
            pending_update_count=0
        )
        mocked_api.return_value.get_webhook_info.return_value = webhook_info

        info = self.bot.get_webhook_info()

        mocked_api.assert_called_with(token="bot-token")
        self.assertEqual(info, webhook_info)
        self.bot.refresh_from_db()
        self.assertEqual(
            self.bot._webhook_info,
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
        error = TelegramError(
            reason="Not found",
            url="url",
            status_code=404,
            response=Mock(),
            api_code="404"
        )

        mocked_api.return_value.get_webhook_info.side_effect = [error]

        with self.assertRaises(TelegramError) as raised:
            self.bot.get_webhook_info()

        self.assertEqual(raised.exception, error)
        mocked_api.assert_called_with(token="bot-token")
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
        self.assertEqual(result, True)
        self.bot.refresh_from_db()
        self.assertEqual(self.bot.update_successful, True)
        self.assertEqual(self.bot.webhook_update_datetime, now)

    @patch("django_chatbot.models.Api")
    @patch("django_chatbot.models.timezone.now")
    def test_set_webhook__telegram_error(self, mocked_now, mocked_api):
        now = timezone.datetime(2000, 1, 1, tzinfo=timezone.utc)
        mocked_now.return_value = now
        error = TelegramError(
            reason="Not found",
            url="url",
            status_code=404,
            response=Mock(),
            api_code="404"
        )
        mocked_api.return_value.set_webhook.side_effect = [error]

        with self.assertRaises(TelegramError) as raised:
            self.bot.set_webhook(
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
        self.assertEqual(raised.exception, error)
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


class UpdateManagerTestCase(TestCase):
    def setUp(self) -> None:
        self.bot = Bot.objects.create(
            name="bot", token="token",
        )

    def test_from_telegram__message(self):
        telegram_update = TelegramUpdate(
            update_id=40,
            message=TelegramMessage(
                message_id=41,
                chat=TelegramChat(id=42, type='private'),
                date=timezone.datetime(2000, 1, 1, tzinfo=timezone.utc),
            )
        )

        Update.objects.from_telegram(
            telegram_update=telegram_update,
            bot=self.bot,
        )

        update = Update.objects.first()
        chat = Chat.objects.first()
        message = Message.objects.first()
        self.assertEqual(update.update_id, telegram_update.update_id)
        self.assertEqual(update.message, message)
        self.assertEqual(message.chat, chat)

    def test_from_telegram__callback_query(self):
        telegram_update = TelegramUpdate(
            update_id=10000,
            callback_query=TelegramCallbackQuery(
                id="4382bfdwdsb323b2d9",
                data="Data from button callback",
                inline_message_id="1234csdbsk4839",
                chat_instance="42a",
                from_user=TelegramUser(
                    id=1111111,
                    is_bot=False,
                    username="Testusername",
                    first_name="Test Firstname",
                    last_name="Test Lastname",
                )
            )
        )

        Update.objects.from_telegram(
            bot=self.bot,
            telegram_update=telegram_update,
        )

        update = Update.objects.first()
        self.assertEqual(update.update_id, telegram_update.update_id)


class ChatManagerTestCase(TestCase):
    def setUp(self) -> None:
        self.bot = Bot.objects.create(
            name="bot",
            token="token",
        )

    def test_from_telegram(self):
        photo = ChatPhoto(
            small_file_id='small_file_id',
            small_file_unique_id='small_file_unique_id',
            big_file_id='big_file_id',
            big_file_unique_id='big_file_unique_id',
        )
        permissions = ChatPermissions(can_send_messages=True)
        location = ChatLocation(
            location=Location(longitude=10.5, latitude=62.8),
            address='address',
        )
        telegram_chat = TelegramChat(
            id=1,
            type='private',
            title='title',
            username='username',
            first_name='first_name',
            last_name='last_name',
            photo=photo,
            bio='bio',
            description='description',
            invite_link='invite_link',
            permissions=permissions,
            slow_mode_delay=1,
            sticker_set_name='sticker_set_name',
            can_set_sticker_set=True,
            linked_chat_id=1,
            location=location,
        )

        Chat.objects.from_telegram(
            telegram_chat=telegram_chat, bot=self.bot
        )

        chat = Chat.objects.first()

        self.assertEqual(chat.chat_id, telegram_chat.id)
        self.assertEqual(chat.type, telegram_chat.type)
        self.assertEqual(chat.username, telegram_chat.username)
        self.assertEqual(chat.first_name, telegram_chat.first_name)
        self.assertEqual(chat.last_name, telegram_chat.last_name)
        self.assertEqual(chat.photo, telegram_chat.photo)
        self.assertEqual(chat.bio, telegram_chat.bio)
        self.assertEqual(chat.description, telegram_chat.description)
        self.assertEqual(chat.invite_link, telegram_chat.invite_link)
        self.assertEqual(chat.permissions, telegram_chat.permissions)
        self.assertEqual(chat.slow_mode_delay, telegram_chat.slow_mode_delay)
        self.assertEqual(chat.sticker_set_name, telegram_chat.sticker_set_name)
        self.assertEqual(chat.can_set_sticker_set,
                         telegram_chat.can_set_sticker_set)
        self.assertEqual(chat.linked_chat_id, telegram_chat.linked_chat_id)
        self.assertEqual(chat.location, telegram_chat.location)


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
            'chat': {'id': 42,
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

    def test_from_telegram(self):
        animation = Animation(
            file_id="1",
            file_unique_id="1",
            width=1,
            height=1,
            duration=1,
        )
        reply_markup = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="button")]]
        )
        telegram_message = TelegramMessage(
            message_id=42,
            date=timezone.datetime(2000, 1, 1, tzinfo=timezone.utc),
            chat=TelegramChat(id=42, type="private"),
            from_user=TelegramUser(id=40, is_bot=False),
            animation=animation,
            reply_markup=reply_markup,
            left_chat_member=TelegramUser(id=41, is_bot=False),
            new_chat_members=[
                TelegramUser(id=42, is_bot=False),
                TelegramUser(id=43, is_bot=False),
            ]
        )
        direction = Message.DIRECTION_OUT

        Message.objects.from_telegram(
            bot=self.bot,
            telegram_message=telegram_message,
            direction=direction
        )

        chat = Chat.objects.first()
        self.assertEqual(chat.chat_id, 42)
        self.assertEqual(chat.type, "private")
        user = User.objects.get(user_id=40)
        self.assertEqual(user.is_bot, False)
        message = Message.objects.first()
        self.assertEqual(message.direction, Message.DIRECTION_OUT)
        self.assertEqual(message.message_id, 42)
        self.assertEqual(message.chat, chat)
        self.assertEqual(message.from_user, user)
        self.assertEqual(message.animation, animation)
        self.assertEqual(message.reply_markup, reply_markup)
        self.assertEqual(message.left_chat_member.user_id, 41)
        new_chat_member_1 = User.objects.get(user_id=42)
        new_chat_member_2 = User.objects.get(user_id=43)
        self.assertIn(new_chat_member_1, message.new_chat_members.all())
        self.assertIn(new_chat_member_2, message.new_chat_members.all())

    def test_get_message(self):
        chat = Chat.objects.create(
            bot=self.bot, chat_id=42, type="private"
        )
        wanted = Message.objects.create(
            message_id=42,
            date=timezone.datetime(2000, 1, 1, tzinfo=timezone.utc),
            chat=chat
        )

        found = Message.objects.get_message(
            telegram_message=TelegramMessage(
                message_id=wanted.message_id,
                date=timezone.datetime(1999, 12, 31, tzinfo=timezone.utc),
                chat=TelegramChat(id=chat.chat_id, type="private"),
            )
        )

        self.assertEqual(found, wanted)

    def test_get_message__wrong_chat_id(self):
        chat = Chat.objects.create(
            bot=self.bot, chat_id=42, type="private"
        )
        wanted = Message.objects.create(
            message_id=42,
            date=timezone.datetime(2000, 1, 1, tzinfo=timezone.utc),
            chat=chat
        )

        found = Message.objects.get_message(
            telegram_message=TelegramMessage(
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
            chat=TelegramChat(id=142, type="private"),
            text='Reply',
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
        message = Message.objects.first()

        self.assertEqual(message.direction, Message.DIRECTION_OUT)
        self.assertEqual(message.message_id, 43)
        self.assertEqual(message.date,
                         timezone.datetime(1999, 12, 31, tzinfo=timezone.utc))
        self.assertEqual(message.chat, chat)
        self.assertEqual(message.from_user, user)
        self.assertEqual(message.reply_to_message, incoming_message)
        self.assertEqual(incoming_message.reply_message, message)


class CallbackQueryManagerTestCase(TestCase):
    def setUp(self) -> None:
        self.bot = Bot.objects.create(name="name", token="token")

    def test_from_telegram(self):
        telegram_callback_query = TelegramCallbackQuery(
            id="4382bfdwdsb323b2d9",
            data="Data from button callback",
            chat_instance="42a",
            from_user=TelegramUser(
                id=1111111,
                is_bot=False,
                username="Testusername",
                first_name="Test Firstname",
                last_name="Test Lastname",
            ),
            message=TelegramMessage(
                message_id=42,
                date=timezone.datetime(2000, 1, 1, tzinfo=timezone.utc),
                chat=TelegramChat(id=42, type="private"),
                from_user=TelegramUser(id=40, is_bot=False),
            )
        )

        CallbackQuery.objects.from_telegram(
            bot=self.bot,
            telegram_callback_query=telegram_callback_query,
        )

        callback_query = CallbackQuery.objects.first()
        user = User.objects.get(user_id=1111111)
        message = Message.objects.first()
        self.assertEqual(
            callback_query.callback_query_id,
            telegram_callback_query.id)
        self.assertEqual(callback_query.from_user, user)
        self.assertEqual(callback_query.message, message)
        self.assertEqual(callback_query.chat.chat_id, 42)
        self.assertEqual(callback_query.text, "Data from button callback")


class UpdateDefaultsTestCase(TestCase):
    class Something:
        some_attr = None

    def test_atr_not_none(self):
        something = self.Something()
        something.some_attr = "something"
        defaults = {'some_attr': "something"}

        _update_defaults(
            something,
            defaults,
            "some_attr",
        )

        self.assertEqual(defaults, {'_some_attr': "something"})
