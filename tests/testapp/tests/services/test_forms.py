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
from typing import List
from unittest.mock import Mock, patch

import jsonpickle
from django.test import TestCase
from django.utils import timezone

from django_chatbot.forms import Form
from django_chatbot.models import Bot, CallbackQuery, Chat, Message, Update, \
    User
from django_chatbot.services import forms
from django_chatbot.forms import Field


class GetRootFormMessage(TestCase):
    def test_get_form_root__root_message(self):
        bot = Bot.objects.create(name='bot', token='token')
        chat = Chat.objects.create(bot=bot, chat_id=1, type='private')
        root_message = Message.objects.create(
            direction=Message.DIRECTION_OUT,
            message_id=1,
            chat=chat,
            date=timezone.datetime(2000, 1, 1, tzinfo=timezone.utc),
            extra={'form': {}},
            text="Question 1"
        )

        answer = Message.objects.create(
            direction=Message.DIRECTION_IN,
            message_id=2,
            chat=chat,
            date=timezone.datetime(2000, 1, 1, 1, tzinfo=timezone.utc),
            reply_to_message=root_message,
            text="Answer 1"
        )

        root = forms.get_form_root(answer)
        self.assertEqual(root, root_message)

    def test_get_form_root__not_root_message(self):
        bot = Bot.objects.create(name='bot', token='token')
        chat = Chat.objects.create(bot=bot, chat_id=1, type='private')
        root_prompt = Message.objects.create(
            direction=Message.DIRECTION_OUT,
            message_id=1,
            chat=chat,
            date=timezone.datetime(2000, 1, 1, tzinfo=timezone.utc),
            extra={'form': {}},
            text="Question 1"
        )
        Message.objects.create(
            direction=Message.DIRECTION_IN,
            message_id=2,
            chat=chat,
            date=timezone.datetime(2000, 1, 1, 1, tzinfo=timezone.utc),
            reply_to_message=root_prompt,
            text="Answer 1"
        )
        prompt_2 = Message.objects.create(
            direction=Message.DIRECTION_OUT,
            message_id=3,
            chat=chat,
            date=timezone.datetime(2000, 1, 1, 2, tzinfo=timezone.utc),
            extra={'form_root_pk': root_prompt.pk},
            text="Question 2"
        )
        input_2 = Message.objects.create(
            direction=Message.DIRECTION_IN,
            message_id=4,
            chat=chat,
            date=timezone.datetime(2000, 1, 1, 3, tzinfo=timezone.utc),
            reply_to_message=prompt_2,
            text="Answer 1"
        )

        root = forms.get_form_root(input_2)
        self.assertEqual(root, root_prompt)

    def test_get_form_root__root_prompt(self):
        bot = Bot.objects.create(name='bot', token='token')
        chat = Chat.objects.create(bot=bot, chat_id=1, type='private')
        user = User.objects.create(user_id=1, is_bot=False)
        root_message = Message.objects.create(
            direction=Message.DIRECTION_OUT,
            message_id=1,
            chat=chat,
            date=timezone.datetime(2000, 1, 1, tzinfo=timezone.utc),
            extra={'form': {}},
            text="Question 1"
        )

        callback_query = CallbackQuery.objects.create(
            callback_query_id="1",
            from_user=user,
            chat_instance="1",
            message=root_message
        )

        root = forms.get_form_root(callback_query)
        self.assertEqual(root, root_message)

    def test_get_form_root__not_root_prompt(self):
        bot = Bot.objects.create(name='bot', token='token')
        chat = Chat.objects.create(bot=bot, chat_id=1, type='private')
        user = User.objects.create(user_id=1, is_bot=False)
        root_prompt = Message.objects.create(
            direction=Message.DIRECTION_OUT,
            message_id=1,
            chat=chat,
            date=timezone.datetime(2000, 1, 1, tzinfo=timezone.utc),
            extra={'form': {}},
            text="Question 1"
        )
        Message.objects.create(
            direction=Message.DIRECTION_IN,
            message_id=2,
            chat=chat,
            date=timezone.datetime(2000, 1, 1, 1, tzinfo=timezone.utc),
            reply_to_message=root_prompt,
            text="Answer 1"
        )
        prompt_2 = Message.objects.create(
            direction=Message.DIRECTION_OUT,
            message_id=3,
            chat=chat,
            date=timezone.datetime(2000, 1, 1, 2, tzinfo=timezone.utc),
            extra={'form_root_pk': root_prompt.pk},
            text="Question 2"
        )
        callback_query = CallbackQuery.objects.create(
            callback_query_id="1",
            from_user=user,
            chat_instance="1",
            message=prompt_2
        )
        root = forms.get_form_root(callback_query)
        self.assertEqual(root, root_prompt)


class SetFormRootTestCase(TestCase):
    def test_set_root(self):
        bot = Bot.objects.create(name='bot', token='token')
        chat = Chat.objects.create(bot=bot, chat_id=1, type='private')
        message1 = Message.objects.create(
            message_id=1,
            chat=chat,
            date=timezone.datetime(2000, 1, 1, tzinfo=timezone.utc),
        )
        message2 = Message.objects.create(
            message_id=2,
            chat=chat,
            date=timezone.datetime(2000, 1, 1, tzinfo=timezone.utc),
        )

        forms.set_form_root(message=message2, form_root=message1)

        message2.refresh_from_db()
        self.assertEqual(message2.extra, {'form_root_pk': message1.pk})


class MyForm(Form):
    def get_fields(self) -> List[Field]:
        return []

    def on_complete(self, update, cleaned_data):
        pass


class SaveFormTestCase(TestCase):
    def test_save_form(self):
        bot = Bot.objects.create(name='bot', token='token')
        chat = Chat.objects.create(bot=bot, chat_id=1, type='private')
        root_message = Message.objects.create(
            message_id=1,
            chat=chat,
            date=timezone.datetime(2000, 1, 1, tzinfo=timezone.utc),
        )
        form = MyForm()

        forms.save_form(root_message=root_message, form=form)

        root_message.refresh_from_db()
        self.assertEqual(jsonpickle.decode(root_message.extra['form']), form)


class LoadFormTestCase(TestCase):
    def test_save_form(self):
        bot = Bot.objects.create(name='bot', token='token')
        chat = Chat.objects.create(bot=bot, chat_id=1, type='private')
        form = MyForm()
        root_message = Message.objects.create(
            message_id=1,
            chat=chat,
            date=timezone.datetime(2000, 1, 1, tzinfo=timezone.utc),
            extra={
                'form': jsonpickle.encode(form),
            }
        )

        thawed = forms.load_form(root_message=root_message)

        self.assertEqual(thawed, form)


class GetFormTestCase(TestCase):
    @patch("django_chatbot.services.forms.get_form_root")
    @patch("django_chatbot.services.forms.load_form")
    def test_get_form(self,
                      mocked_load_form: Mock,
                      mocked_get_form_root: Mock):
        message = Mock()
        update = Mock(spec=Update, telegram_object=message)
        root_message = Mock()
        form = Mock()
        mocked_get_form_root.return_value = root_message
        mocked_load_form.return_value = form

        expected_form = forms.get_form(update)

        self.assertEqual(expected_form, form)
        mocked_get_form_root.assert_called_with(message)
        mocked_load_form.assert_called_with(root_message)
