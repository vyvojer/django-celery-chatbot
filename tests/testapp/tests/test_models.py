from django.test import TestCase

from django_chatbot.models import Message


class MessageTestCase(TestCase):

    def test__str(self):
        message = Message(text='text')
        self.assertEqual(str(message), 'text')