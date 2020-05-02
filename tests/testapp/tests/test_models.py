from django.test import TestCase

from django_chatbot.models import Message, Phrase, SimplePattern


class MessageTestCase(TestCase):

    def test__str(self):
        message = Message(text='text')
        self.assertEqual(str(message), 'text')


class SimplePatternTestCase(TestCase):
    def setUp(self) -> None:
        self.hello_phrase = Phrase.objects.create(phrase="hello")
        self.hi_phrase = Phrase.objects.create(phrase="hi")
        self.my_friend_phrase = Phrase.objects.create(phrase="my friend")
        self.bye_phrase = Phrase.objects.create(phrase="bye")
        self.goodbye_phrase = Phrase.objects.create(phrase="goodbye")

    def test_match_any(self):
        pattern = SimplePattern.objects.create(condition=SimplePattern.ANY)
        pattern.phrases.add(self.hello_phrase, self.hi_phrase)

        self.assertTrue(pattern.match("Hi all"))
        self.assertTrue(pattern.match("Hello"))
        self.assertFalse(pattern.match("Bye"))

    def test_match_all(self):
        pattern = SimplePattern.objects.create(condition=SimplePattern.ALL)
        pattern.phrases.add(self.hi_phrase, self.my_friend_phrase)

        self.assertTrue(pattern.match("Hi my friend"))
        self.assertFalse(pattern.match("Hi all"))
        self.assertFalse(pattern.match("My friend Dario"))
