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
from django_chatbot.forms import FormHandler
from django_chatbot.handlers import DefaultHandler
from django_chatbot.models import (
    Bot,
    Chat,
    Form as FormKeeper,
    Message,
    Update)
from django_chatbot.services.dispatcher import load_handlers
from django_chatbot.telegram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup, )
from django_chatbot.tests import MockUser, TestCase as ChatbotTestCase


class FieldTestCase(TestCase):
    def setUp(self) -> None:
        self.update = Mock()
        self.cleaned_data = None
        self.form = Mock()

    def test_to_prompt_message__text(self):
        field = forms.Field(
            name='field',
            prompt="Input:",
            inline_keyboard=[
                [InlineKeyboardButton("Yes", callback_data="yes")],
                [InlineKeyboardButton("No", callback_data="No")]
            ],
        )

        message = field.get_prompt_message_params(Mock(), Mock(), Mock())

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
        field.clean("1", self.update, self.cleaned_data, self.form)

        self.assertEqual(field.value, "1")
        self.assertEqual(field.is_bound, False)
        self.assertEqual(field.is_valid, False)
        self.assertEqual(field.errors, [error])

    def test_clean__validators_invalid(self):
        first_error = ValidationError("First error", code="first_error")
        second_error = ValidationError("Second error", code="second_error")

        def first_validator(value):
            raise first_error

        def second_validator(value):
            raise second_error

        field = forms.Field(
            name="field",
            validators=[first_validator, second_validator],
        )

        field.clean("some value", Mock(), Mock(), Mock())

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

        field.clean("some value", Mock(), Mock(), Mock())

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

    def test_previous_and_next__linear(self):
        update = Mock()
        cleaned_data = {}
        field_1 = forms.Field("field_1")
        field_2 = forms.Field("field_2")
        field_3 = forms.Field("field_3")
        field_1.add_next(field_2)
        field_2.add_next(field_3)

        self.assertEqual(field_1.previous(), None)
        self.assertEqual(field_1.next(update, cleaned_data), field_2)
        self.assertEqual(field_2.previous(), field_1)
        self.assertEqual(field_2.next(update, cleaned_data), field_3)
        self.assertEqual(field_3.previous(), field_2)
        self.assertEqual(field_3.next(update, cleaned_data), None)

    def test_previous_and_next__tree(self):
        field_1 = forms.Field("field_1")
        field_2 = forms.Field("field_2")
        field_3 = forms.Field("field_3")
        field_4 = forms.Field("field_4")
        field_1.add_next(field_2, lambda v, u, c: v == 5)
        field_1.add_next(
            field_3,
            lambda v, u, c: c.get("answer") and c["answer"] == 42
        )
        field_1.add_next(field_4)

        field_1.value = 5
        update = Mock()
        cleaned_data = {}
        self.assertEqual(field_1.previous(), None)
        self.assertEqual(field_1.next(update, cleaned_data), field_2)
        self.assertEqual(field_2.previous(), field_1)
        self.assertEqual(field_2.next(update, cleaned_data), None)

        field_1.value = 1
        update = Mock()
        cleaned_data = {'answer': 42}
        self.assertEqual(field_1.previous(), None)
        self.assertEqual(field_1.next(update, cleaned_data), field_3)
        self.assertEqual(field_3.previous(), field_1)
        self.assertEqual(field_3.next(update, cleaned_data), None)

        field_1.value = 1
        update = Mock()
        cleaned_data = {}
        self.assertEqual(field_1.previous(), None)
        self.assertEqual(field_1.next(update, cleaned_data), field_4)
        self.assertEqual(field_4.previous(), field_1)
        self.assertEqual(field_4.next(update, cleaned_data), None)

    def test_previous_and_next__graph(self):
        field_1 = forms.Field("field_1")
        field_2 = forms.Field("field_2")
        field_3 = forms.Field("field_3")
        field_4 = forms.Field("field_4")
        forms.Field("field_5")

        field_1.add_next(field_2, lambda v, u, c: v == 5)
        field_1.add_next(field_3)

        field_2.add_next(field_4)

        field_3.add_next(field_4)

        field_4.add_next(field_1, lambda v, u, c: v == 'again')

        field_1.value = 5
        field_4.value = 'again'
        update = Mock()
        cleaned_data = {}
        self.assertEqual(field_1.next(update, cleaned_data), field_2)
        self.assertEqual(field_2.previous(), field_1)
        self.assertEqual(field_2.next(update, cleaned_data), field_4)
        self.assertEqual(field_4.previous(), field_2)
        self.assertEqual(field_4.next(update, cleaned_data), field_1)
        self.assertEqual(field_1.previous(), field_4)
        field_1.value = 6
        self.assertEqual(field_1.next(update, cleaned_data), field_3)
        self.assertEqual(field_3.previous(), field_1)
        self.assertEqual(field_3.next(update, cleaned_data), field_4)
        self.assertEqual(field_4.previous(), field_3)
        field_4.value = 'finish'
        self.assertEqual(field_4.next(update, cleaned_data), None)


class IntegerFieldTestCase(TestCase):
    def test_clean__valid(self):
        update = Mock()
        form = Mock()
        cleaned_data = {}
        field = forms.IntegerField(name="int_field")

        field.clean("42", update, cleaned_data, form)

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
        form = Mock()
        cleaned_data = {}
        field = forms.IntegerField(name="int_field", max_value=10)

        field.clean('10', update, cleaned_data, form)

        self.assertEqual(field.value, 10)
        self.assertEqual(field.is_bound, True)

    def test_max_value__invalid_value(self):
        update = Mock()
        form = Mock()
        cleaned_data = {}
        field = forms.IntegerField(name="int_field", max_value=10)

        field.clean('11', update, cleaned_data, form)

        self.assertEqual(field.value, 11)
        self.assertEqual(field.is_bound, False)
        self.assertEqual(field.errors[0].code, 'max_value')

    def test_min_value__valid_value(self):
        update = Mock()
        form = Mock()
        cleaned_data = {}
        field = forms.IntegerField(name="int_field", min_value=0)

        field.clean('10', update, cleaned_data, form)

        self.assertEqual(field.value, 10)
        self.assertEqual(field.is_bound, True)

    def test_min_value__invalid_value(self):
        update = Mock()
        form = Mock()
        cleaned_data = {}
        field = forms.IntegerField(name="int_field", min_value=0)

        field.clean('-1', update, cleaned_data, form)

        self.assertEqual(field.value, -1)
        self.assertEqual(field.is_bound, False)
        self.assertEqual(field.errors[0].code, 'min_value')


class CharFieldTestCase(TestCase):
    def test_max_length__valid_value(self):
        update = Mock()
        form = Mock()
        cleaned_data = {}
        field = forms.CharField(name="field", max_length=3)

        field.clean('123', update, cleaned_data, form)

        self.assertEqual(field.value, '123')
        self.assertEqual(field.is_bound, True)
        self.assertEqual(field.is_valid, True)

    def test_max_length__invalid_value(self):
        update = Mock()
        form = Mock()
        cleaned_data = {}
        field = forms.CharField(name="field", max_length=3)

        field.clean('1234', update, cleaned_data, form)

        self.assertEqual(field.value, '1234')
        self.assertEqual(field.is_bound, False)
        self.assertEqual(field.is_valid, False)

    def test_min_length__valid_value(self):
        update = Mock()
        form = Mock()
        cleaned_data = {}
        field = forms.CharField(name="field", min_length=3)

        field.clean('123', update, cleaned_data, form)

        self.assertEqual(field.value, '123')
        self.assertEqual(field.is_bound, True)
        self.assertEqual(field.is_valid, True)

    def test_min_length__invalid_value(self):
        update = Mock()
        form = Mock()
        cleaned_data = {}
        field = forms.CharField(name="field", min_length=3)

        field.clean('12', update, cleaned_data, form)

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
    first_field = forms.IntegerField(prompt="Enter first field:")
    second_field = SecondField(prompt="Enter second field:")

    def on_init(self, update, cleaned_data):
        self.cleaned_data['chat_id'] = update.message.chat.chat_id


handlers = []

class CustomHandlerTestCase(ChatbotTestCase):
    handler_form = None

    def setUp(self) -> None:
        super().setUp()
        self.patcher = patch(
            "testapp.tests.test_forms.handlers",
            [DefaultHandler('default', form_class=self.handler_form)],
        )
        self.patcher.start()
        load_handlers.cache_clear()
        self.bot = Bot.objects.create(
            name='bot', token='token',
            root_handlerconf='testapp.tests.test_forms'
        )
        self.mock_user = MockUser(self.bot)

    def tearDown(self) -> None:
        super().tearDown()
        self.patcher.stop()
        load_handlers.cache_clear()


class FormFlowTestCase(CustomHandlerTestCase):
    class Form(forms.Form):
        field_1 = forms.IntegerField(prompt='Enter field_1:')
        field_2 = forms.IntegerField(prompt='Enter field_2:')

        def on_init(self, update, cleaned_data):
            self.cleaned_data['chat_id'] = update.message.chat.chat_id

        def on_complete(self, update: Update, cleaned_data: dict):
            update.telegram_object.reply('Thank you!')

        def on_cancel(self, update: Update, cleaned_data: dict):
            update.telegram_object.reply("It is sad")

    handler_form = Form

    def test_init_form(self):
        self.mock_user.send_message(message_text='Hey, form')
        form = self.mock_user.form()
        self.assertEqual(form.current_field.name, 'field_1')
        self.assertEqual(
            form.cleaned_data,
            {'chat_id': self.mock_user.chat.chat_id})
        self.assertEqual(self.mock_user.messages()[0].text, 'Enter field_1:')
        self.assertEqual(self.mock_user.messages()[1].text, 'Hey, form')

    def test_first_input(self):
        self.mock_user.send_message(message_text='Hey, form')
        self.mock_user.send_message(message_text='10')
        form = self.mock_user.form()
        self.assertEqual(form.current_field.name, 'field_2')
        self.assertEqual(
            form.cleaned_data,
            {
                'chat_id': self.mock_user.chat.chat_id,
                'field_1': 10,
            }
        )
        self.assertEqual(self.mock_user.messages()[0].text, 'Enter field_2:')
        self.assertEqual(self.mock_user.messages()[1].text, '10')
        self.assertEqual(self.mock_user.messages()[2].text, 'Enter field_1:')
        self.assertEqual(self.mock_user.messages()[3].text, 'Hey, form')

    def test_previous_on_second_field(self):
        self.mock_user.send_message(message_text='Hey, form')
        self.mock_user.send_message(message_text='10')
        self.mock_user.send_message(message_text='/previous')
        form = self.mock_user.form()
        self.assertEqual(form.current_field.name, 'field_1')
        self.assertEqual(
            form.cleaned_data,
            {
                'chat_id': self.mock_user.chat.chat_id,
            }
        )
        self.assertEqual(self.mock_user.messages()[0].text, 'Enter field_1:')
        self.assertEqual(self.mock_user.messages()[1].text, '/previous')
        self.assertEqual(self.mock_user.messages()[2].text, 'Enter field_2:')
        self.assertEqual(self.mock_user.messages()[3].text, '10')
        self.assertEqual(self.mock_user.messages()[4].text, 'Enter field_1:')
        self.assertEqual(self.mock_user.messages()[5].text, 'Hey, form')

    def test_complete_form(self):
        self.mock_user.send_message(message_text='Hey, form')
        self.mock_user.send_message(message_text='10')
        self.mock_user.send_message(message_text='20')

        self.assertEqual(self.mock_user.form(), None)
        completed_form = FormKeeper.objects.first().form
        self.assertEqual(
            completed_form.cleaned_data,
            {
                'chat_id': self.mock_user.chat.chat_id,
                'field_1': 10,
                'field_2': 20,
            }
        )
        self.assertEqual(completed_form.completed, True)
        self.assertEqual(self.mock_user.messages()[0].text, 'Thank you!')
        self.assertEqual(self.mock_user.messages()[1].text, '20')
        self.assertEqual(self.mock_user.messages()[2].text, 'Enter field_2:')
        self.assertEqual(self.mock_user.messages()[3].text, '10')
        self.assertEqual(self.mock_user.messages()[4].text, 'Enter field_1:')
        self.assertEqual(self.mock_user.messages()[5].text, 'Hey, form')

    def test_cancel_form(self):
        self.mock_user.send_message(message_text='Hey, form')
        self.mock_user.send_message(message_text='10')
        self.mock_user.send_message(message_text='/cancel')

        self.assertEqual(self.mock_user.form(), None)
        completed_form = FormKeeper.objects.first().form
        self.assertEqual(
            completed_form.cleaned_data,
            {
                'chat_id': self.mock_user.chat.chat_id,
                'field_1': 10,
            }
        )
        self.assertEqual(completed_form.completed, False)
        self.assertEqual(self.mock_user.messages()[0].text, 'It is sad')
        self.assertEqual(self.mock_user.messages()[1].text, '/cancel')
        self.assertEqual(self.mock_user.messages()[2].text, 'Enter field_2:')
        self.assertEqual(self.mock_user.messages()[3].text, '10')
        self.assertEqual(self.mock_user.messages()[4].text, 'Enter field_1:')
        self.assertEqual(self.mock_user.messages()[5].text, 'Hey, form')


class InlineTestCase(CustomHandlerTestCase):
    class Form(forms.Form):
        apple_field = forms.Field(
            prompt="An apple?",
            inline_keyboard=[
                [InlineKeyboardButton("Yes", callback_data="yes")],
                [InlineKeyboardButton("No", callback_data="no")]
            ],
        )
        orange_field = forms.Field(
            prompt="An orange?",
            inline_keyboard=[
                [InlineKeyboardButton("Yes", callback_data="yes")],
                [InlineKeyboardButton("No", callback_data="no")]
            ],
        )

    handler_form = Form

    def test_init_form(self):
        self.mock_user.send_message("hey, form")

        self.assertEqual(self.mock_user.messages()[0].text, 'An apple?')
        self.assertEqual(
            self.mock_user.messages()[0].reply_markup,
            InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("Yes", callback_data="yes")],
                [InlineKeyboardButton("No", callback_data="no")]
            ]
            )
        )
        self.assertEqual(self.mock_user.messages()[1].text, 'hey, form')
        form = self.mock_user.form()
        self.assertEqual(form.completed, False)
        self.assertEqual(form.cleaned_data, {})

    def test_apple_field(self):
        self.mock_user.send_message("hey, form")
        self.mock_user.send_callback_query(data='yes')

        self.assertEqual(self.mock_user.messages()[0].text, 'An orange?')
        self.assertEqual(
            self.mock_user.messages()[0].reply_markup,
            InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("Yes", callback_data="yes")],
                [InlineKeyboardButton("No", callback_data="no")]
            ]
            )
        )
        self.assertEqual(self.mock_user.messages()[1].text, 'An apple?')
        self.assertEqual(self.mock_user.callback_queries()[0].data, 'yes')
        form = self.mock_user.form()
        self.assertEqual(form.completed, False)
        self.assertEqual(form.cleaned_data, {'apple_field': 'yes'})

    def test_orange_field(self):
        self.mock_user.send_message("hey, form")
        self.mock_user.send_callback_query(data='yes')
        self.mock_user.send_callback_query(data='no')

        self.assertEqual(self.mock_user.messages()[0].text, 'An orange?')
        self.assertEqual(self.mock_user.messages()[1].text, 'An apple?')
        self.assertEqual(self.mock_user.callback_queries()[0].data, 'no')
        self.assertEqual(self.mock_user.callback_queries()[1].data, 'yes')

        form = self.mock_user.form()
        self.assertEqual(form.completed, True)
        self.assertEqual(
            form.cleaned_data,
            {
                'apple_field': 'yes',
                'orange_field': 'no',
            }
        )


class OnTheFlyInlineTestCase(CustomHandlerTestCase):
    class Form(forms.Form):
        apple_field = forms.Field(
            prompt="An apple?",
            inline_keyboard=[
                [InlineKeyboardButton("Yes", callback_data="yes")],
                [InlineKeyboardButton("No", callback_data="no")]
            ],
        )
        orange_field = forms.Field(
            prompt="An orange?",
            inline_keyboard=[
                [InlineKeyboardButton("Yes", callback_data="yes")],
                [InlineKeyboardButton("No", callback_data="no")]
            ],
            field_to_change=apple_field
        )

    handler_form = Form

    def test_init_form(self):
        self.mock_user.send_message("hey, form")

        self.assertEqual(self.mock_user.messages()[0].text, 'An apple?')
        self.assertEqual(
            self.mock_user.messages()[0].reply_markup,
            InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("Yes", callback_data="yes")],
                [InlineKeyboardButton("No", callback_data="no")]
            ]
            )
        )
        self.assertEqual(self.mock_user.messages()[1].text, 'hey, form')

    def test_apple_field(self):
        """ New message must not be added. Message must be updated """
        self.mock_user.send_message("hey, form")
        self.mock_user.send_callback_query(data='yes')

        self.assertEqual(self.mock_user.messages()[0].text, 'An orange?')
        # New message must not be added. Message must be updated
        self.assertEqual(self.mock_user.messages().count(), 2)
        self.assertEqual(
            self.mock_user.messages()[0].reply_markup,
            InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("Yes", callback_data="yes")],
                [InlineKeyboardButton("No", callback_data="no")]
            ]
            )
        )
        self.assertEqual(self.mock_user.callback_queries()[0].data, 'yes')
        form = self.mock_user.form()
        self.assertEqual(form.completed, False)
        self.assertEqual(form.cleaned_data, {'apple_field': 'yes'})


class OnTheFlyInlineLoopTestCase(CustomHandlerTestCase):
    class Form(forms.Form):
        def get_root_field(self):
            field = forms.Field(
                name="field",
                prompt="An apple?",
                inline_keyboard=[
                    [InlineKeyboardButton("Yes", callback_data="yes")],
                    [InlineKeyboardButton("No", callback_data="no")]
                ],
            )
            field.add_next(field)
            return field

    handler_form = Form

    def test_init_form(self):
        self.mock_user.send_message("hey, form")

        self.assertEqual(self.mock_user.messages()[0].text, 'An apple?')
        self.assertEqual(
            self.mock_user.messages()[0].reply_markup,
            InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("Yes", callback_data="yes")],
                [InlineKeyboardButton("No", callback_data="no")]
            ]
            )
        )
        self.assertEqual(self.mock_user.messages()[1].text, 'hey, form')

    def test_field_is_looped(self):
        """ New message must not be added. Message must be updated """
        self.mock_user.send_message("hey, form")
        self.mock_user.send_callback_query(data='yes')

        self.assertEqual(self.mock_user.messages()[0].text, 'An apple?')
        # New message must not be added. Message must be updated
        self.assertEqual(self.mock_user.messages().count(), 2)
        self.assertEqual(
            self.mock_user.messages()[0].reply_markup,
            InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("Yes", callback_data="yes")],
                [InlineKeyboardButton("No", callback_data="no")]
            ]
            )
        )
        self.assertEqual(self.mock_user.callback_queries()[0].data, 'yes')
        form = self.mock_user.form()
        self.assertEqual(form.completed, False)
        self.assertEqual(form.cleaned_data, {'field': 'yes'})

        self.mock_user.send_callback_query(data='no')

        self.assertEqual(self.mock_user.messages()[0].text, 'An apple?')
        # New message must not be added. Message must be updated
        self.assertEqual(self.mock_user.messages().count(), 2)
        self.assertEqual(
            self.mock_user.messages()[0].reply_markup,
            InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("Yes", callback_data="yes")],
                [InlineKeyboardButton("No", callback_data="no")]
            ]
            )
        )
        self.assertEqual(self.mock_user.callback_queries()[0].data, 'no')
        form = self.mock_user.form()
        self.assertEqual(form.completed, False)
        self.assertEqual(form.cleaned_data, {'field': 'no'})
