from unittest import skip
from unittest.mock import patch, Mock


from django.core.management import call_command
from django.test import TestCase, override_settings

from django_chatbot.models import Bot

class UpdateFromSettings(TestCase):
    chatbot_settings = {
        'WEBHOOK_SITE': "https://example1.com",
        'BOTS': [
            {
                'NAME': "@Bot1",
                'TOKEN': "bot-1-token",
                'ROOT_HANDLERCONF': "testapp.handlers"
            },
            {
                'NAME': "@Bot2",
                'TOKEN': "bot-2-token",
                'ROOT_HANDLERCONF': "testapp.handlers",
            },
        ]
    }

    @override_settings(DJANGO_CHATBOT=chatbot_settings)
    def test_command__create_bots(self):
        call_command("update_from_settings")

        bots = Bot.objects.all()
        self.assertEqual(bots.count(), 2)
        self.assertEqual(bots[0].name, "@Bot1")
        self.assertEqual(bots[0].token, "bot-1-token")
        self.assertEqual(bots[0].root_handlerconf, "testapp.handlers")
        self.assertEqual(bots[1].name, "@Bot2")
        self.assertEqual(bots[1].token, "bot-2-token")
        self.assertEqual(bots[1].root_handlerconf, "testapp.handlers")

    @override_settings(DJANGO_CHATBOT=chatbot_settings)
    def test_command__update_bots(self):
        bot1 = Bot.objects.create(
            name="@Bot1", token="bot-1-old-token", root_handlerconf="old.conf"
        )
        bot2 = Bot.objects.create(
            name="@Bot2", token="bot-2-old-token", root_handlerconf="old.conf"
        )

        call_command("update_from_settings")

        bots = Bot.objects.all()
        self.assertEqual(bots.count(), 2)
        self.assertEqual(bots[0].name, "@Bot1")
        self.assertEqual(bots[0].token, "bot-1-token")
        self.assertEqual(bots[0].root_handlerconf, "testapp.handlers")
        self.assertEqual(bots[1].name, "@Bot2")
        self.assertEqual(bots[1].token, "bot-2-token")
        self.assertEqual(bots[1].root_handlerconf, "testapp.handlers")



