# Create your tests here.
from dummyfatherbot.models import FakeBot

from django_chatbot.telegram.types import InlineKeyboardButton
from django_chatbot.test import TestCase


class TestNewBot(TestCase):
    bot_name = "dummy_father"

    def test_newbot(self):
        response = self.client.send_message("/newbot")
        self.assertContains(
            response,
            "Alright, a new bot. How are we going to call it? Please choose a name for your bot.",  # noqa
        )
        response = self.client.send_message("bot_1")
        self.assertContains(
            response,
            "Good. Now let's choose a username for your bot. It must end in `bot`. Like this, for example: TetrisBot or tetris_bot.",  # noqa
        )
        response = self.client.send_message("username_1_bot")
        self.assertContains(response, "Bot is created.")

        bot_1 = FakeBot.objects.get(name="bot_1")
        self.assertEqual(bot_1.name, "bot_1")
        self.assertEqual(bot_1.username, "username_1_bot")


class TestMyBots(TestCase):
    bot_name = "dummy_father"
    reset_sequences = True

    def setUp(self) -> None:
        self.bot_1 = FakeBot.objects.create(name="bot_1", username="username_1_bot")
        self.bot_2 = FakeBot.objects.create(name="bot_2", username="username_2_bot")
        self.bot_3 = FakeBot.objects.create(name="bot_3", username="username_3_bot")

    def test_my_bots(self):
        response = self.client.send_message("/mybots")
        self.assertTrue(response.is_successful)
        self.assertEqual(response.operation, response.NEW)
        self.assertContains(response, "Choose a bot from the list below:")

        self.assertEqual(
            response.inline_keyboard,
            [
                [
                    InlineKeyboardButton(
                        "@username_1_bot", callback_data="username_1_bot"
                    ),
                    InlineKeyboardButton(
                        "@username_2_bot", callback_data="username_2_bot"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "@username_3_bot", callback_data="username_3_bot"
                    ),
                ],
            ],
        )

        main_menu_message = response.message
        response = self.client.send_callback_query("username_1_bot")
        self.assertTrue(response.is_successful)
        self.assertEqual(response.message.form.current_field, "bot_actions")
        self.assertEqual(response.operation, response.UPDATE)
        self.assertEqual(response.message, main_menu_message)
        self.assertContains(response, "What do you want to do with @username_1_bot?")
        self.assertIn("Edit Bot", response.inline_keyboard_labels)
        self.assertIn("Delete Bot", response.inline_keyboard_labels)

        response = self.client.send_message("/mybots")
        self.assertTrue(response.is_successful)
        self.assertEqual(response.operation, response.NEW)
        self.assertContains(response, "Choose a bot from the list below:")
