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

from django.test import TestCase
from django.utils import timezone

from django_chatbot.handlers import (
    CommandHandler,
    Handler
)
from django_chatbot.models import Bot, Chat, Message, Update
from django_chatbot.forms import Form


class HandlerTest(TestCase):
    def test_handle_update__set_handler_name_if_matches(self):
        bot = Bot.objects.create(name='bot', token='token')
        self.update = Update.objects.create(bot=bot, update_id=1)

        class TestHandler(Handler):
            def _match(self, update: Update) -> bool:
                return True

        handler = TestHandler(name="test")

        handler.handle_update(self.update)

        self.update.refresh_from_db()
        self.assertEqual(self.update.handler, "test")

    def test_form_match(self):
        class TestHandler(Handler):
            def _match(self, update: Update) -> bool:
                return False

        class TestForm(Form):
            def on_complete(self):
                pass

        handler = TestHandler(name="handler", form_class=TestForm)
        bot = Bot.objects.create(name='bot', token='token')
        chat = Chat.objects.create(bot=bot, chat_id=1, type="private")
        Message.objects.create(
            message_id=2,
            direction=Message.DIRECTION_OUT,
            date=timezone.datetime(2000, 1, 1, 2, tzinfo=timezone.utc),
            chat=chat,
            text='Enter first field:',
            extra={
                'form': {
                    'name': 'TestForm',
                    'fields': {},
                    'completed': False,
                }
            }
        )
        first_input = Message.objects.create(
            direction=Message.DIRECTION_IN,
            message_id=3,
            date=timezone.datetime(2000, 1, 1, 3, tzinfo=timezone.utc),
            chat=chat,
            text='41',
        )
        update = Update.objects.create(
            bot=bot,
            update_id=1,
            message=first_input,
        )

        self.assertTrue(handler._form_match(update))


class CommandHandlerTestCase(TestCase):
    def setUp(self) -> None:
        bot = Bot.objects.create(name='bot', token='token')
        chat = Chat.objects.create(bot=bot, chat_id=1, type="private")
        message = Message.objects.create(
            message_id=1,
            chat=chat,
            date=timezone.datetime(2000, 1, 1, tzinfo=timezone.utc),
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
        self.update = Update.objects.create(
            bot=bot,
            update_id=1,
            message=message,
        )

    def test_match(self):
        handler = CommandHandler(
            name="handler", command="/end"
        )
        self.assertEqual(handler.match(self.update), False)

        handler = CommandHandler(
            name="handler", command="/start"
        )
        self.assertEqual(handler.match(self.update), True)

        handler = CommandHandler(
            name="handler", command="/help"
        )
        self.assertEqual(handler.match(self.update), True)
