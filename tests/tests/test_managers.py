from django.test import TestCase
from django.utils import timezone
from factories.factories import BotFactory, UpdateFactory

from django_chatbot.models import (
    Bot,
    CallbackQuery,
    Chat,
    Form,
    Message,
    Update,
    User,
    _update_defaults,
)
from django_chatbot.telegram.types import Animation
from django_chatbot.telegram.types import CallbackQuery as TelegramCallbackQuery
from django_chatbot.telegram.types import Chat as TelegramChat
from django_chatbot.telegram.types import (
    ChatLocation,
    ChatPermissions,
    ChatPhoto,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Location,
)
from django_chatbot.telegram.types import Message as TelegramMessage
from django_chatbot.telegram.types import Update as TelegramUpdate
from django_chatbot.telegram.types import User as TelegramUser


class BotManagerTestCase(TestCase):
    def test_with_pulling_updates(self):
        BotFactory(webhook_enabled=True)
        bot_2 = BotFactory(webhook_enabled=False)
        bot_3 = BotFactory(webhook_enabled=False)
        BotFactory(webhook_enabled=True)

        bots = Bot.objects.with_pulling_updates()

        self.assertQuerysetEqual(
            bots,
            [
                bot_2,
                bot_3,
            ],
            transform=lambda x: x,
            ordered=False,
        )


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
            name="bot",
            token="token",
        )

    def test_from_telegram__message(self):
        telegram_update = TelegramUpdate(
            update_id=40,
            message=TelegramMessage(
                message_id=41,
                chat=TelegramChat(id=42, type="private"),
                date=timezone.datetime(2000, 1, 1, tzinfo=timezone.utc),
            ),
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

    def test_from_telegram__channel_post(self):
        telegram_update = TelegramUpdate(
            update_id=40,
            channel_post=TelegramMessage(
                message_id=41,
                chat=TelegramChat(id=-42, type="channel", title="the_channel"),
                date=timezone.datetime(2000, 1, 1, tzinfo=timezone.utc),
                sender_chat=TelegramChat(id=-42, type="channel", title="the_channel"),
                text="post",
            ),
        )
        Update.objects.from_telegram(
            bot=self.bot,
            telegram_update=telegram_update,
        )

        update = Update.objects.first()
        self.assertEqual(update.update_id, telegram_update.update_id)
        self.assertEqual(update.type, Update.TYPE_CHANNEL_POST)

    def test_from_telegram__edited_channel_post(self):
        telegram_update = TelegramUpdate(
            update_id=40,
            edited_channel_post=TelegramMessage(
                message_id=41,
                chat=TelegramChat(id=-42, type="channel", title="the_channel"),
                date=timezone.datetime(2000, 1, 1, tzinfo=timezone.utc),
                sender_chat=TelegramChat(id=-42, type="channel", title="the_channel"),
                text="post",
            ),
        )
        Update.objects.from_telegram(
            bot=self.bot,
            telegram_update=telegram_update,
        )

        update = Update.objects.first()
        self.assertEqual(update.update_id, telegram_update.update_id)
        self.assertEqual(update.type, Update.TYPE_EDITED_CHANNEL_POST)

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
                ),
            ),
        )

        Update.objects.from_telegram(
            bot=self.bot,
            telegram_update=telegram_update,
        )

        update = Update.objects.first()
        self.assertEqual(update.update_id, telegram_update.update_id)

    def test_last_update(self):
        another_bot = BotFactory()
        UpdateFactory(bot=self.bot)
        UpdateFactory(bot=self.bot)
        UpdateFactory(bot=another_bot)
        update_4 = UpdateFactory(bot=self.bot)
        update_5 = UpdateFactory(bot=another_bot)

        last_update = Update.objects.last_update(bot=self.bot)
        self.assertEqual(last_update, update_4)
        last_update = Update.objects.last_update(bot=another_bot)
        self.assertEqual(last_update, update_5)


class ChatManagerTestCase(TestCase):
    def setUp(self) -> None:
        self.bot = Bot.objects.create(
            name="bot",
            token="token",
        )

    def test_from_telegram(self):
        photo = ChatPhoto(
            small_file_id="small_file_id",
            small_file_unique_id="small_file_unique_id",
            big_file_id="big_file_id",
            big_file_unique_id="big_file_unique_id",
        )
        permissions = ChatPermissions(can_send_messages=True)
        location = ChatLocation(
            location=Location(longitude=10.5, latitude=62.8),
            address="address",
        )
        telegram_chat = TelegramChat(
            id=1,
            type="private",
            title="title",
            username="username",
            first_name="first_name",
            last_name="last_name",
            photo=photo,
            bio="bio",
            description="description",
            invite_link="invite_link",
            permissions=permissions,
            slow_mode_delay=1,
            sticker_set_name="sticker_set_name",
            can_set_sticker_set=True,
            linked_chat_id=1,
            location=location,
        )

        Chat.objects.from_telegram(telegram_chat=telegram_chat, bot=self.bot)

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
        self.assertEqual(chat.can_set_sticker_set, telegram_chat.can_set_sticker_set)
        self.assertEqual(chat.linked_chat_id, telegram_chat.linked_chat_id)
        self.assertEqual(chat.location, telegram_chat.location)


class FormManagerTestCase(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(user_id=1, is_bot=False)
        self.bot = Bot.objects.create(name="bot", token="token")
        self.chat = Chat.objects.create(bot=self.bot, chat_id=1, type="private")
        self.form = Form.objects.create()
        self.root_message = Message.objects.create(
            direction=Message.DIRECTION_OUT,
            message_id=1,
            chat=self.chat,
            date=timezone.datetime(2000, 1, 1, tzinfo=timezone.utc),
            text="Question 1",
            form=self.form,
        )

    def test_get_form_for_message(self):
        answer = Message.objects.create(
            direction=Message.DIRECTION_IN,
            message_id=2,
            chat=self.chat,
            date=timezone.datetime(2000, 1, 1, 1, tzinfo=timezone.utc),
            text="Answer 1",
        )
        update = Update.objects.create(
            bot=self.bot,
            message=answer,
            update_id="1",
        )

        form = Form.objects.get_form(update=update)
        self.assertEqual(form, self.form)

    def test_get_form_for_callback_query(self):
        callback_query = CallbackQuery.objects.create(
            bot=self.bot,
            callback_query_id="1",
            from_user=self.user,
            chat_instance="1",
            message=self.root_message,
        )
        update = Update.objects.create(
            bot=self.bot,
            callback_query=callback_query,
            update_id="1",
        )

        form = Form.objects.get_form(update=update)
        self.assertEqual(form, self.form)


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
            ],
        )
        direction = Message.DIRECTION_OUT

        Message.objects.from_telegram(
            bot=self.bot, telegram_message=telegram_message, direction=direction
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
        chat = Chat.objects.create(bot=self.bot, chat_id=42, type="private")
        wanted = Message.objects.create(
            message_id=42,
            date=timezone.datetime(2000, 1, 1, tzinfo=timezone.utc),
            chat=chat,
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
        chat = Chat.objects.create(bot=self.bot, chat_id=42, type="private")
        wanted = Message.objects.create(
            message_id=42,
            date=timezone.datetime(2000, 1, 1, tzinfo=timezone.utc),
            chat=chat,
        )

        found = Message.objects.get_message(
            telegram_message=TelegramMessage(
                message_id=wanted.message_id,
                date=timezone.datetime(1999, 12, 31, tzinfo=timezone.utc),
                chat=TelegramChat(id=999, type="private"),
            )
        )

        self.assertEqual(found, None)


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
            ),
        )

        CallbackQuery.objects.from_telegram(
            bot=self.bot,
            telegram_callback_query=telegram_callback_query,
        )

        callback_query = CallbackQuery.objects.first()
        user = User.objects.get(user_id=1111111)
        message = Message.objects.first()
        self.assertEqual(callback_query.callback_query_id, telegram_callback_query.id)
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
        defaults = {"some_attr": "something"}

        _update_defaults(
            something,
            defaults,
            "some_attr",
        )

        self.assertEqual(defaults, {"_some_attr": "something"})
