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

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from django_chatbot import forms
from django_chatbot.models import (
    Bot,
    CallbackQuery,
    Chat,
    Message,
    Update,
    User)
from django_chatbot.services.forms import load_form
from django_chatbot.telegram.api import Api
from django_chatbot.telegram.types import (
    Chat as TelegramChat,
    InlineKeyboardButton,
    Message as TelegramMessage,
    User as TelegramUser,
)


class FieldTestCase(TestCase):
    def setUp(self) -> None:
        self.update = Mock()
        self.cleaned_data = None

    def test_get_prompt(self):
        field = forms.Field(name='field', prompt="Input:")

        field.update_prompt(self.update, self.cleaned_data)

        self.assertEqual(field.prompt, "Input:")

    def test_get_prompt__custom(self):
        class CustomField(forms.Field):
            def get_prompt(self, *args, **kwargs):
                return "Ok, input value:"

        field = CustomField(name='field', prompt="Input:")

        field.update_prompt(self.update, self.cleaned_data)

        self.assertEqual(field.prompt, "Ok, input value:")

    def test_get_inline_keyboard(self):
        field = forms.Field(
            name='field',
            prompt="Input:",
            inline_keyboard=[
                [InlineKeyboardButton("Yes", callback_data="yes")],
                [InlineKeyboardButton("No", callback_data="No")]
            ],
        )

        field.update_prompt(self.update, self.cleaned_data)

        self.assertEqual(field.inline_keyboard, [
            [InlineKeyboardButton("Yes", callback_data="yes")],
            [InlineKeyboardButton("No", callback_data="No")]
        ])

    def test_get_inline_keyboard__custom(self):
        class CustomField(forms.Field):
            def get_inline_keyboard(self, *args, **kwargs):
                return [[InlineKeyboardButton("No", callback_data="no")]]

        field = CustomField(name='field', prompt="Input:")

        field.update_prompt(self.update, self.cleaned_data)

        self.assertEqual(field.inline_keyboard, [
            [InlineKeyboardButton("No", callback_data="no")]
        ])

    def test_to_prompt_message__text(self):
        field = forms.Field(
            name='field',
            prompt="Input:",
            inline_keyboard=[
                [InlineKeyboardButton("Yes", callback_data="yes")],
                [InlineKeyboardButton("No", callback_data="No")]
            ],
        )

        message = field.to_send_message_params()

        self.assertEqual(
            message.reply_markup.inline_keyboard, [
                [InlineKeyboardButton("Yes", callback_data="yes")],
                [InlineKeyboardButton("No", callback_data="No")]
            ]
        )
        self.assertEqual(message.text, "Input:")

    def test_clean__invalid(self, ):
        error = ValidationError("Wrong input!")

        class CustomField(forms.Field):
            def validate(self, *args, **kwargs):
                raise error

        field = CustomField(name='field', prompt='Input value:')
        field.clean("1", self.update, self.cleaned_data)

        self.assertEqual(field.value, "1")
        self.assertEqual(field.is_bound, False)
        self.assertEqual(field.is_valid, False)
        self.assertEqual(field.errors, [error])

    def test_get_prompt__invalid(self, ):
        error = ValidationError("Wrong input!")

        class CustomField(forms.Field):
            pass

        field = CustomField(name='field', prompt='Input value:')
        field.errors = [error]

        prompt = field.get_prompt(self.update, self.cleaned_data)

        self.assertEqual(prompt, "Wrong input!\nInput value:")


class IntegerFieldTestCase(TestCase):
    def test_clean__valid(self):
        update = Mock()
        cleaned_data = {}
        field = forms.IntegerField(name="int_field")

        field.clean("42", update, cleaned_data)

        self.assertEqual(field.value, 42)
        self.assertEqual(field.is_bound, True)

    def test_to_python__invalid_value(self):
        field = forms.IntegerField(name="int_field")

        with self.assertRaises(ValidationError) as raised:
            field.to_python('4b')
        error = raised.exception
        self.assertEqual(error.code, 'invalid')


class SecondField(forms.IntegerField):
    def get_prompt(self, update, cleaned_data):
        first = cleaned_data['first_field']
        return f"First field was {first}. Now enter second field:"


class TestForm(forms.Form):
    on_save_message = "Fields saved successfully."

    def get_fields(self):
        fields = [
            forms.IntegerField(
                name="first_field", prompt="Enter first field:"
            ),
            SecondField(
                name="second_field", prompt="Enter second field:"
            ),
        ]
        return fields

    def on_first_update(self, update, cleaned_data):
        self.cleaned_data['chat_id'] = update.message.chat.chat_id

    def on_complete(self, update, cleaned_data):
        pass


class InlineForm(forms.Form):
    def get_fields(self):
        fields = [
            forms.CharField(
                name='field',
                prompt="Yes?",
                inline_keyboard=[
                    [InlineKeyboardButton("Yes", callback_data="yes")],
                    [InlineKeyboardButton("No", callback_data="no")]
                ],
            )
        ]
        return fields

    def on_complete(self, update: Update, cleaned_data: dict):
        pass


class FormTestCase(TestCase):
    def setUp(self) -> None:
        self.bot = Bot.objects.create(
            name="bot",
            token="token",
        )
        self.chat = Chat.objects.create(
            bot=self.bot,
            chat_id=140,
            type='private',
        )

    @patch.object(Api, 'send_message')
    def test_update__user_initiates_form_input(self, mocked_send_message):
        """ Bot must send first field input"""

        mocked_send_message.return_value = TelegramMessage(
            message_id=2,
            date=timezone.datetime(2000, 1, 1, 2, tzinfo=timezone.utc),
            from_user=TelegramUser(id=1, is_bot=True),
            chat=TelegramChat(id=140, type="private"),
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

        form = TestForm()
        form.update(update)

        self.assertEqual(form.fields[0].value, None)
        self.assertEqual(form.fields[0].is_bound, False)
        self.assertEqual(form.fields[1].value, None)
        self.assertEqual(form.fields[1].is_bound, False)
        self.assertEqual(form.current_field, form.fields[0])
        self.assertEqual(form.cleaned_data, {'chat_id': 140})
        self.assertEqual(form.completed, False)
        out_messages = Message.objects.filter(direction=Message.DIRECTION_OUT)
        first_prompt = out_messages[0]
        self.assertEqual(first_prompt.chat, self.chat)
        self.assertEqual(first_prompt.direction, Message.DIRECTION_OUT)
        self.assertEqual(first_prompt.text, 'Enter first field:')
        deserialized = load_form(first_prompt)
        self.assertEqual(deserialized.current_field, deserialized.fields[0])

    @patch.object(Api, 'send_message')
    def test_update__first_input(self, mocked_send_message: Mock):
        first_prompt = Message.objects.create(
            message_id=2,
            direction=Message.DIRECTION_OUT,
            date=timezone.datetime(2000, 1, 1, 2, tzinfo=timezone.utc),
            chat=self.chat,
            text='Enter first field:',
            extra={'form': {}}
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
            chat=TelegramChat(id=140, type="private"),
            text='Enter second field:',
        )
        form = TestForm()
        first_field = forms.IntegerField(
            name="first_field", prompt="Enter first field:"
        )
        second_field = SecondField(
            name="second_field", prompt="Enter second field:"
        )
        form.fields = [first_field, second_field]
        form.current_field = first_field

        form.update(update)

        mocked_send_message.assert_called_with(
            chat_id=140,
            text='First field was 41. Now enter second field:',
            parse_mode=None
        )
        self.assertEqual(form.fields[0].value, 41)
        self.assertEqual(form.fields[0].is_bound, True)
        self.assertEqual(form.fields[1].value, None)
        self.assertEqual(form.fields[1].is_bound, False)
        self.assertEqual(form.completed, False)

        out_messages = Message.objects.filter(direction=Message.DIRECTION_OUT)
        first_prompt = out_messages[0]
        last_prompt = out_messages[1]
        deserialized = load_form(first_prompt)
        self.assertEqual(deserialized, form)
        self.assertEqual(last_prompt.chat, self.chat)
        self.assertEqual(last_prompt.direction, Message.DIRECTION_OUT)
        self.assertEqual(last_prompt.text, 'Enter second field:')
        self.assertEqual(
            last_prompt.extra,
            {
                'form_root_pk': first_prompt.pk
            }
        )

    @patch.object(Api, 'send_message')
    def test_update__first_input__invalid(self, mocked_send_message: Mock):
        first_prompt = Message.objects.create(
            message_id=2,
            direction=Message.DIRECTION_OUT,
            date=timezone.datetime(2000, 1, 1, 2, tzinfo=timezone.utc),
            chat=self.chat,
            text='Enter first field:',
            extra={'form': {}}
        )
        first_input = Message.objects.create(
            direction=Message.DIRECTION_IN,
            message_id=3,
            date=timezone.datetime(2000, 1, 1, 3, tzinfo=timezone.utc),
            chat=self.chat,
            text='4a',
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
            chat=TelegramChat(id=140, type="private"),
            text='Enter a whole number.\nEnter first field:',
        )
        form = TestForm()
        first_field = forms.IntegerField(
            name="first_field", prompt="Enter first field:"
        )
        second_field = SecondField(
            name="second_field", prompt="Enter second field:"
        )
        form.fields = [first_field, second_field]
        form.current_field = first_field

        form.update(update)

        self.assertEqual(form.fields[0].value, '4a')
        self.assertEqual(form.fields[0].is_bound, False)
        self.assertEqual(form.fields[0].is_valid, False)
        self.assertEqual(form.fields[1].value, None)
        self.assertEqual(form.fields[1].is_bound, False)
        self.assertEqual(form.current_field, form.fields[0])
        self.assertEqual(form.completed, False)

        mocked_send_message.assert_called_with(
            chat_id=140,
            text='Enter a whole number.\nEnter first field:',
            parse_mode=None
        )

        out_messages = Message.objects.filter(direction=Message.DIRECTION_OUT)
        first_prompt = out_messages[0]
        last_prompt = out_messages[1]
        self.assertEqual(last_prompt.chat, self.chat)
        self.assertEqual(last_prompt.direction, Message.DIRECTION_OUT)
        self.assertEqual(last_prompt.text,
                         'Enter a whole number.\nEnter first field:')
        self.assertEqual(
            last_prompt.extra,
            {
                'form_root_pk': first_prompt.pk
            }
        )

    @patch.object(TestForm, 'on_complete')
    def test_update__last_input(self, mocked_on_complete: Mock):
        first_prompt = Message.objects.create(
            message_id=2,
            direction=Message.DIRECTION_OUT,
            date=timezone.datetime(2000, 1, 1, 2, tzinfo=timezone.utc),
            chat=self.chat,
            text='Enter first field:',
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
        form = TestForm()
        first_field = forms.IntegerField(
            name="first_field", prompt="Enter first field:"
        )
        first_field.value = 41
        first_field.is_valid = True
        first_field.is_bound = True
        second_field = SecondField(
            name="second_field", prompt="Enter second field:"
        )
        form.fields = [first_field, second_field]
        form.current_field = second_field

        form.update(update)

        self.assertEqual(form.fields[0].value, 41)
        self.assertEqual(form.fields[0].is_valid, True)
        self.assertEqual(form.fields[1].value, 42)
        self.assertEqual(form.fields[1].is_valid, True)
        self.assertEqual(form.completed, True)

        first_prompt.refresh_from_db()
        deserialized = load_form(first_prompt)
        self.assertEqual(deserialized, form)
        mocked_on_complete.assert_called_with(update, form.cleaned_data)

    def test_update__callback_query(self):
        user = User.objects.create(user_id=40, is_bot=False)
        prompt = Message.objects.create(
            message_id=2,
            direction=Message.DIRECTION_OUT,
            date=timezone.datetime(2000, 1, 1, 2, tzinfo=timezone.utc),
            chat=self.chat,
            text='Yes?:',
            extra={'form': {}}
        )
        input = CallbackQuery.objects.create(
            callback_query_id="1",
            from_user=user,
            chat_instance="1",
            message=prompt,
            data="yes",
        )
        update = Update.objects.create(
            bot=self.bot,
            type=Update.TYPE_CALLBACK_QUERY,
            update_id=1,
            callback_query=input,
        )

        form = InlineForm()
        form.current_field = form.fields[0]

        form.update(update)

        self.assertEqual(form.fields[0].value, "yes")
        self.assertEqual(form.fields[0].is_bound, True)
        self.assertEqual(form.completed, True)
        self.assertEqual(form.cleaned_data, {'field': 'yes'})
        prompt.refresh_from_db()
        deserialized = load_form(prompt)
        self.assertEqual(deserialized, form)
