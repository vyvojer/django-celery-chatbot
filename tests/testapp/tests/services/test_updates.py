from django.test import TestCase
from django.utils import timezone

from django_chatbot.models import Bot, Update, User, Chat, Message
from django_chatbot.services.updates import save_update


class UpdatesTestCase(TestCase):
    def setUp(self) -> None:
        self.bot = Bot.objects.create(name="bot1", token="token1")
        self.data = {
            'update_id': 708191904,
            'message': {'message_id': 5,
                        'from': {'id': 42,
                                 'is_bot': False,
                                 'first_name': 'Fedor',
                                 'last_name': 'Sumkin',
                                 'username': 'fedor',
                                 'language_code': 'en'},
                        'chat': {'id': 142,
                                 'first_name': 'Fedor',
                                 'last_name': 'Sumkin',
                                 'username': 'fedor',
                                 'type': 'private'},
                        'date': 1,
                        'text': '/start',
                        'entities': [
                            {'offset': 0,
                             'length': 6,
                             'type': 'bot_command'}]}}
        self.token_slug = "token2"

    def test_save_update__creates_user(self):
        save_update(bot=self.bot, update_data=self.data)

        user = User.objects.first()
        self.assertEqual(user.user_id, 42)
        self.assertEqual(user.is_bot, False)
        self.assertEqual(user.first_name, 'Fedor')
        self.assertEqual(user.last_name, 'Sumkin')
        self.assertEqual(user.username, 'fedor')
        self.assertEqual(user.language_code, 'en')

    def test_save_update__updates_existing_user(self):
        User.objects.create(
            user_id=42,
            is_bot=False,
            first_name='Frodo',
            last_name='Pytlik',
            username='frodo',
            language_code='cs',
        )

        save_update(bot=self.bot, update_data=self.data)

        users = User.objects.all()
        self.assertEqual(users.count(), 1)
        user = users.first()
        self.assertEqual(user.user_id, 42)
        self.assertEqual(user.is_bot, False)
        self.assertEqual(user.first_name, 'Fedor')
        self.assertEqual(user.last_name, 'Sumkin')
        self.assertEqual(user.username, 'fedor')
        self.assertEqual(user.language_code, 'en')

    def test_save_update__creates_chat(self):
        save_update(bot=self.bot, update_data=self.data)

        chat = Chat.objects.first()
        self.assertEqual(chat.chat_id, 142)
        self.assertEqual(chat.bot, self.bot)
        self.assertEqual(chat.first_name, 'Fedor')
        self.assertEqual(chat.last_name, 'Sumkin')
        self.assertEqual(chat.username, 'fedor')
        self.assertEqual(chat.type, 'private')

    def test_save_update__creates_message(self):
        save_update(bot=self.bot, update_data=self.data)

        user = User.objects.first()
        chat = Chat.objects.first()
        message = Message.objects.first()
        self.assertEqual(message.message_id, 5)
        self.assertEqual(message.text, '/start')
        self.assertEqual(message.chat, chat)
        self.assertEqual(message.from_user, user)
        self.assertEqual(
            message.date,
            timezone.datetime(1970, 1, 1, 0, 0, 1, tzinfo=timezone.utc)
        )

    def test_save_update__creates_update(self):
        update = save_update(bot=self.bot, update_data=self.data)

        User.objects.first()
        Chat.objects.first()
        message = Message.objects.first()
        self.assertEqual(Update.objects.first(), update)
        self.assertEqual(update.update_id, 708191904)
        self.assertEqual(update.bot, self.bot)
        self.assertEqual(update.original, self.data)
        self.assertEqual(update.message, message)
        self.assertEqual(update.message_type, Update.MESSAGE_TYPE_MESSAGE)
