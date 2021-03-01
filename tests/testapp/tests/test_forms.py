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
    Form as FormKeeper,
    Message,
    Update,
    User)
from django_chatbot.telegram.api import Api
from django_chatbot.telegram.types import (
    Chat as TelegramChat,
    InlineKeyboardButton,
    Message as TelegramMessage,
    User as TelegramUser,
)
from django_chatbot.forms import FormHandler


class FieldTestCase(TestCase):
    def setUp(self) -> None:
        self.update = Mock()
        self.cleaned_data = None

    def test_to_prompt_message__text(self):
        field = forms.Field(
            name='field',
            prompt="Input:",
            inline_keyboard=[
                [InlineKeyboardButton("Yes", callback_data="yes")],
                [InlineKeyboardButton("No", callback_data="No")]
            ],
        )

        message = field.get_prompt_message_params(Mock(), Mock())

        self.assertEqual(
            message.reply_markup.inline_keyboard, [
                [InlineKeyboardButton("Yes", callback_data="yes")],
                [InlineKeyboardButton("No", callback_data="No")]
            ]
        )
        self.assertEqual(message.text, "Input:")

    def test_clean__validate_invalid(self):
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

    def test_clean__validators_invalid(self):
        first_error = ValidationError("First error", code="first_error")
        second_error = ValidationError("Second error", code="second_error")

        def first_validator(value):
            raise first_error

        def second_validatator(value):
            raise second_error

        field = forms.Field(
            name="field",
            validators=[first_validator, second_validatator],
        )

        field.clean("some value", Mock(), Mock())

        self.assertEqual(field.value, "some value")
        self.assertEqual(field.is_bound, False)
        self.assertEqual(field.is_valid, False)
        self.assertEqual(field.errors[0].code, "first_error")
        self.assertEqual(field.errors[1].code, "second_error")
        self.assertEqual(field.errors[0].message, "First error")
        self.assertEqual(field.errors[1].message, "Second error")

    def test_clean__use_custom_error_messages(self):
        first_error = ValidationError("First error", code="first_error")
        second_error = ValidationError("Second error", code="second_error")

        def first_validator(value):
            raise first_error

        def second_validatator(value):
            raise second_error

        field = forms.Field(
            name="field",
            validators=[first_validator, second_validatator],
            custom_error_messages={
                'second_error': "Custom error message!"
            }
        )

        field.clean("some value", Mock(), Mock())

        self.assertEqual(field.errors[0].message, "First error")
        self.assertEqual(field.errors[1].message, "Custom error message!")

    def test_get_error_text(self, ):
        error_1 = ValidationError("Wrong input!", code="wrong")
        error_2 = ValidationError("Bad input!", code="bad")
        error_3 = ValidationError(["Another error"])

        field = forms.Field(name='field', prompt='Input value:')
        field.errors = [error_1, error_2, error_3]

        error_text = field.get_error_text()

        self.assertEqual(
            error_text,
            "Wrong input!\nBad input!\nAnother error")


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

    def test_max_value__valid_value(self):
        update = Mock()
        cleaned_data = {}
        field = forms.IntegerField(name="int_field", max_value=10)

        field.clean('10', update, cleaned_data)

        self.assertEqual(field.value, 10)
        self.assertEqual(field.is_bound, True)

    def test_max_value__invalid_value(self):
        update = Mock()
        cleaned_data = {}
        field = forms.IntegerField(name="int_field", max_value=10)

        field.clean('11', update, cleaned_data)

        self.assertEqual(field.value, 11)
        self.assertEqual(field.is_bound, False)
        self.assertEqual(field.errors[0].code, 'max_value')

    def test_min_value__valid_value(self):
        update = Mock()
        cleaned_data = {}
        field = forms.IntegerField(name="int_field", min_value=0)

        field.clean('10', update, cleaned_data)

        self.assertEqual(field.value, 10)
        self.assertEqual(field.is_bound, True)

    def test_min_value__invalid_value(self):
        update = Mock()
        cleaned_data = {}
        field = forms.IntegerField(name="int_field", min_value=0)

        field.clean('-1', update, cleaned_data)

        self.assertEqual(field.value, -1)
        self.assertEqual(field.is_bound, False)
        self.assertEqual(field.errors[0].code, 'min_value')


class CharFieldTestCase(TestCase):
    def test_max_length__valid_value(self):
        update = Mock()
        cleaned_data = {}
        field = forms.CharField(name="field", max_length=3)

        field.clean('123', update, cleaned_data)

        self.assertEqual(field.value, '123')
        self.assertEqual(field.is_bound, True)
        self.assertEqual(field.is_valid, True)

    def test_max_length__invalid_value(self):
        update = Mock()
        cleaned_data = {}
        field = forms.CharField(name="field", max_length=3)

        field.clean('1234', update, cleaned_data)

        self.assertEqual(field.value, '1234')
        self.assertEqual(field.is_bound, False)
        self.assertEqual(field.is_valid, False)

    def test_min_length__valid_value(self):
        update = Mock()
        cleaned_data = {}
        field = forms.CharField(name="field", min_length=3)

        field.clean('123', update, cleaned_data)

        self.assertEqual(field.value, '123')
        self.assertEqual(field.is_bound, True)
        self.assertEqual(field.is_valid, True)

    def test_min_length__invalid_value(self):
        update = Mock()
        cleaned_data = {}
        field = forms.CharField(name="field", min_length=3)

        field.clean('12', update, cleaned_data)

        self.assertEqual(field.value, '12')
        self.assertEqual(field.is_bound, False)
        self.assertEqual(field.is_valid, False)


class FormHandlerTestCase(TestCase):
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

    def test_match_command_valid(self):
        last_input = Message.objects.create(
            direction=Message.DIRECTION_IN,
            message_id=5,
            date=timezone.datetime(2000, 1, 1, 5, tzinfo=timezone.utc),
            chat=self.chat,
            text='/previous',
            _entities=[{"type": "bot_command", "length": 9, "offset": 0}],
        )
        update = Update.objects.create(
            bot=self.bot,
            update_id=1,
            message=last_input,
        )
        handler = FormHandler(callback=Mock(), command="/previous")

        self.assertEqual(handler.match(update), True)

    def test_command_invalid(self):
        last_input = Message.objects.create(
            direction=Message.DIRECTION_IN,
            message_id=5,
            date=timezone.datetime(2000, 1, 1, 5, tzinfo=timezone.utc),
            chat=self.chat,
            text='/previous',
            _entities=[{"type": "bot_command", "length": 9, "offset": 0}],
        )
        update = Update.objects.create(
            bot=self.bot,
            update_id=1,
            message=last_input,
        )
        handler = FormHandler(callback=Mock(), command="/cancel")

        self.assertEqual(handler.match(update), False)


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

    def on_init(self, update, cleaned_data):
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
        prompt = Message.objects.get(direction=Message.DIRECTION_OUT)
        self.assertEqual(prompt.chat, self.chat)
        self.assertEqual(prompt.direction, Message.DIRECTION_OUT)
        self.assertEqual(prompt.text, 'Enter first field:')
        form_keeper = FormKeeper.objects.first()
        self.assertEqual(prompt.form, form_keeper)
        self.assertEqual(
            form_keeper.form.current_field,
            form_keeper.form.fields[0])

    @patch.object(Api, 'send_message')
    def test_update__first_input(self, mocked_send_message: Mock):
        form = TestForm()
        first_field = forms.IntegerField(
            name="first_field", prompt="Enter first field:"
        )
        second_field = SecondField(
            name="second_field", prompt="Enter second field:"
        )
        form.fields = [first_field, second_field]
        form.current_field = first_field
        form_keeper = FormKeeper.objects.create(form=form)
        form.form_keeper = form_keeper

        Message.objects.create(
            message_id=2,
            direction=Message.DIRECTION_OUT,
            date=timezone.datetime(2000, 1, 1, 2, tzinfo=timezone.utc),
            chat=self.chat,
            text='Enter first field:',
            form=form_keeper,
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
        last_prompt = out_messages[1]
        form_keeper.refresh_from_db()
        self.assertEqual(form_keeper.form, form)
        self.assertEqual(last_prompt.chat, self.chat)
        self.assertEqual(last_prompt.direction, Message.DIRECTION_OUT)
        self.assertEqual(last_prompt.text, 'Enter second field:')
        self.assertEqual(last_prompt.form, form_keeper)

    @patch.object(Api, 'send_message')
    def test_update__first_input__invalid(self, mocked_send_message: Mock):
        form = TestForm()
        first_field = forms.IntegerField(
            name="first_field", prompt="Enter first field:"
        )
        second_field = SecondField(
            name="second_field", prompt="Enter second field:"
        )
        form.fields = [first_field, second_field]
        form.current_field = first_field
        form_keeper = FormKeeper.objects.create(form=form)
        form.form_keeper = form_keeper

        Message.objects.create(
            message_id=2,
            direction=Message.DIRECTION_OUT,
            date=timezone.datetime(2000, 1, 1, 2, tzinfo=timezone.utc),
            chat=self.chat,
            text='Enter first field:',
            form=form_keeper,
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
            text='Enter a whole number.\n\nEnter first field:',
            parse_mode=None
        )

        out_messages = Message.objects.filter(direction=Message.DIRECTION_OUT)
        last_prompt = out_messages[1]
        self.assertEqual(last_prompt.chat, self.chat)
        self.assertEqual(last_prompt.direction, Message.DIRECTION_OUT)
        self.assertEqual(last_prompt.text,
                         'Enter a whole number.\nEnter first field:')
        self.assertEqual(last_prompt.form, form_keeper)

    @patch.object(TestForm, 'on_complete')
    def test_update__last_input(self, mocked_on_complete: Mock):
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
        form.cleaned_data = {'first_field': 41}
        form_keeper = FormKeeper.objects.create(form=form)
        form.form_keeper = form_keeper

        first_prompt = Message.objects.create(
            message_id=2,
            direction=Message.DIRECTION_OUT,
            date=timezone.datetime(2000, 1, 1, 2, tzinfo=timezone.utc),
            chat=self.chat,
            text='Enter first field:',
            form=form_keeper,
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

        form.update(update)

        self.assertEqual(form.fields[0].value, 41)
        self.assertEqual(form.fields[0].is_valid, True)
        self.assertEqual(form.fields[1].value, 42)
        self.assertEqual(form.fields[1].is_valid, True)
        self.assertEqual(form.completed, True)

        form_keeper.refresh_from_db()
        self.assertEqual(form_keeper.form, form)
        mocked_on_complete.assert_called_with(update, form.cleaned_data)

    @patch.object(Api, 'send_message')
    def test_update__last_input__previous_command(
            self, mocked_send_message: Mock
    ):
        """Previous command must return to previous (first) field input"""
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
        form.cleaned_data = {'first_field': 41}
        form_keeper = FormKeeper.objects.create(form=form)
        form.form_keeper = form_keeper

        first_prompt = Message.objects.create(
            message_id=2,
            direction=Message.DIRECTION_OUT,
            date=timezone.datetime(2000, 1, 1, 2, tzinfo=timezone.utc),
            chat=self.chat,
            text='Enter first field:',
            form=form_keeper,
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
            text='/previous',
            _entities=[{"type": "bot_command", "length": 9, "offset": 0}],
        )
        update = Update.objects.create(
            bot=self.bot,
            update_id=1,
            message=last_input,
        )
        mocked_send_message.return_value = TelegramMessage(
            message_id=2,
            date=timezone.datetime(2000, 1, 1, 2, tzinfo=timezone.utc),
            from_user=TelegramUser(id=1, is_bot=True),
            chat=TelegramChat(id=140, type="private"),
            text='Enter first field:',
        )

        form.update(update)

        self.assertEqual(form.fields[0].value, None)
        self.assertEqual(form.fields[0].is_bound, False)
        self.assertEqual(form.fields[1].value, None)
        self.assertEqual(form.fields[1].is_bound, False)
        self.assertEqual(form.current_field, form.fields[0])
        self.assertEqual(form.completed, False)

        first_prompt.refresh_from_db()
        self.assertEqual(first_prompt.chat, self.chat)
        self.assertEqual(first_prompt.direction, Message.DIRECTION_OUT)
        self.assertEqual(first_prompt.text, 'Enter first field:')
        form_keeper.refresh_from_db()
        self.assertEqual(
            form_keeper.form.current_field, form_keeper.form.fields[0]
        )

    def test_update__callback_query(self):
        user = User.objects.create(user_id=40, is_bot=False)
        form = InlineForm()
        form.current_field = form.fields[0]
        form_keeper = FormKeeper.objects.create(form=form)
        form.form_keeper = form_keeper
        prompt = Message.objects.create(
            message_id=2,
            direction=Message.DIRECTION_OUT,
            date=timezone.datetime(2000, 1, 1, 2, tzinfo=timezone.utc),
            chat=self.chat,
            text='Yes?:',
            form=form_keeper,
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

        form.update(update)

        self.assertEqual(form.fields[0].value, "yes")
        self.assertEqual(form.fields[0].is_bound, True)
        self.assertEqual(form.completed, True)
        self.assertEqual(form.cleaned_data, {'field': 'yes'})
        prompt.refresh_from_db()
        form_keeper.refresh_from_db()
        self.assertEqual(form_keeper.form, form)
