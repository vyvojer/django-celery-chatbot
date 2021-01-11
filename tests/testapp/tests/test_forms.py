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

from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone

from django_chatbot import forms
from django_chatbot.models import Bot, Chat, Message, Update
from django_chatbot.telegram.api import Api
from django_chatbot.telegram.types import (
    Chat as TelegramChat,
    Message as TelegramMessage,
    User as TelegramUser,
)


class IntegerFieldTestCase(TestCase):
    def test_clean__valid(self):
        field = forms.IntegerField(name="int_field")

        field.clean("42")

        self.assertEqual(field.value, 42)
        self.assertEqual(field.bound, True)


class TestForm(forms.Form):
    on_save_message = "Fields saved successfully."
    fields = [
        forms.IntegerField(
            name="first_field", label="Enter first field:"
        ),
        forms.IntegerField(
            name="second_field", label="Enter second field:"
        ),
    ]

    def on_complete(self):
        pass


class FormTestCase(TestCase):
    def setUp(self) -> None:
        self.bot = Bot.objects.create(
            name="bot",
            token="token",
        )
        self.chat = Chat.objects.create(
            bot=self.bot,
            chat_id=1,
            type='private',
        )

    @patch.object(Api, 'send_message')
    def test_form__user_initiates_form_input(self, mocked_send_message):
        """ Bot must send first field input"""

        mocked_send_message.return_value = TelegramMessage(
            message_id=2,
            date=timezone.datetime(2000, 1, 1, 2, tzinfo=timezone.utc),
            from_user=TelegramUser(id=1, is_bot=True),
            chat=TelegramChat(id=1, type="private"),
            text='Enter first field:',
        )
        request_message = Message.objects.create(
            direction=Message.DIRECTION_IN,
            message_id=1,
            date=timezone.datetime(2000, 1, 1, 1, tzinfo=timezone.utc),
            chat=self.chat,
            text='I want to input data',
        )
        update = Update.objects.create(
            bot=self.bot,
            update_id=1,
            message=request_message,
        )

        form = TestForm(update=update)

        self.assertEqual(form.fields[0].value, None)
        self.assertEqual(form.fields[0].bound, False)
        self.assertEqual(form.fields[1].value, None)
        self.assertEqual(form.fields[1].bound, False)
        self.assertEqual(form.completed, False)
        out_messages = Message.objects.filter(direction=Message.DIRECTION_OUT)
        first_prompt = out_messages[0]
        self.assertEqual(first_prompt.chat, self.chat)
        self.assertEqual(first_prompt.direction, Message.DIRECTION_OUT)
        self.assertEqual(first_prompt.text, 'Enter first field:')
        self.assertEqual(
            first_prompt.extra['form'],
            {
                'name': "TestForm",
                'fields': {},
                'completed': False,
            }
        )

    @patch.object(Api, 'send_message')
    def test_init__first_input(self, mocked_send_message):
        first_prompt = Message.objects.create(
            message_id=2,
            direction=Message.DIRECTION_OUT,
            date=timezone.datetime(2000, 1, 1, 2, tzinfo=timezone.utc),
            chat=self.chat,
            text='Enter first field:',
            extra={
                'form': {
                    'fields': {},
                    'completed': False,
                }
            }
        )
        first_input = Message.objects.create(
            direction=Message.DIRECTION_IN,
            message_id=3,
            date=timezone.datetime(2000, 1, 1, 3, tzinfo=timezone.utc),
            chat=self.chat,
            text='41',
        )
        update = Update.objects.create(
            bot=self.bot,
            update_id=1,
            message=first_input,
        )
        mocked_send_message.return_value = TelegramMessage(
            message_id=4,
            date=timezone.datetime(2000, 1, 1, 4, tzinfo=timezone.utc),
            from_user=TelegramUser(id=1, is_bot=True),
            chat=TelegramChat(id=1, type="private"),
            text='Enter second field:',
        )

        form = TestForm(update)

        self.assertEqual(form.fields[0].value, 41)
        self.assertEqual(form.fields[0].bound, True)
        self.assertEqual(form.fields[1].value, None)
        self.assertEqual(form.fields[1].bound, False)
        self.assertEqual(form.completed, False)

        out_messages = Message.objects.filter(direction=Message.DIRECTION_OUT)
        first_prompt = out_messages[0]
        last_prompt = out_messages[1]
        self.assertEqual(
            first_prompt.extra['form'],
            {
                'fields': {
                    'first_field': 41,
                },
                'completed': False,
            }
        )
        self.assertEqual(last_prompt.chat, self.chat)
        self.assertEqual(last_prompt.direction, Message.DIRECTION_OUT)
        self.assertEqual(last_prompt.text, 'Enter second field:')
        self.assertEqual(
            last_prompt.extra,
            {
                'form_root_pk': first_prompt.pk
            }
        )

    @patch.object(TestForm, 'on_complete')
    def test_init__last_input(self, mocked_on_complete: Mock):
        first_prompt = Message.objects.create(
            message_id=2,
            direction=Message.DIRECTION_OUT,
            date=timezone.datetime(2000, 1, 1, 2, tzinfo=timezone.utc),
            chat=self.chat,
            text='Enter first field:',
            extra={
                'form': {
                    'fields': {
                        'first_field': 41,
                    },
                    'completed': False,
                }
            }
        )
        Message.objects.create(
            message_id=4,
            direction=Message.DIRECTION_OUT,
            date=timezone.datetime(2000, 1, 1, 4, tzinfo=timezone.utc),
            chat=self.chat,
            text='Enter second field:',
            extra={'form_root_pk': first_prompt.pk}
        )
        last_input = Message.objects.create(
            direction=Message.DIRECTION_IN,
            message_id=5,
            date=timezone.datetime(2000, 1, 1, 5, tzinfo=timezone.utc),
            chat=self.chat,
            text='42',
        )
        update = Update.objects.create(
            bot=self.bot,
            update_id=1,
            message=last_input,
        )

        form = TestForm(update)

        self.assertEqual(form.fields[0].value, 41)
        self.assertEqual(form.fields[0].valid, True)
        self.assertEqual(form.fields[1].value, 42)
        self.assertEqual(form.fields[1].valid, True)
        self.assertEqual(form.completed, True)

        first_prompt.refresh_from_db()
        self.assertEqual(
            first_prompt.extra['form'],
            {
                'fields': {
                    'first_field': 41,
                    'second_field': 42,
                },
                'completed': True,
            }
        )
        mocked_on_complete.assert_called_with()
