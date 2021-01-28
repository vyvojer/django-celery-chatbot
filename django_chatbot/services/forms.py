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
import json
from typing import Optional, Union

import jsonpickle

from django_chatbot.models import CallbackQuery, Message


def _get_message_form_root(message: Message) -> Optional[Message]:
    if message.direction == Message.DIRECTION_OUT:
        return None
    try:
        previous = message.get_previous_by_date(
            chat_id=message.chat_id, direction=Message.DIRECTION_OUT
        )
    except Message.DoesNotExist:
        return None
    if previous.extra.get('form') is not None:
        return previous
    if pk := previous.extra.get('form_root_pk'):
        root = Message.objects.get(pk=pk)
        return root


def _get_callback_query_form_root(
        callback_query: CallbackQuery
) -> Optional[Message]:
    message = callback_query.message
    if message.extra.get('form') is not None:
        return message
    if pk := message.extra.get('form_root_pk'):
        root = Message.objects.get(pk=pk)
        return root


def get_form_root(
        telegram_object: Union[CallbackQuery, Message]) -> Optional[Message]:
    if isinstance(telegram_object, Message):
        return _get_message_form_root(telegram_object)
    elif isinstance(telegram_object, CallbackQuery):
        return _get_callback_query_form_root(telegram_object)


def set_form_root(message: Message, form_root: Message):
    message.extra.update(
        {'form_root_pk': form_root.pk}
    )
    message.save()


def save_form(root_message: Message, form):
    root_message.extra['form'] = jsonpickle.encode(form)
    root_message.save()


def load_form(root_message: Message):
    if 'form' in root_message.extra:
        form = jsonpickle.decode(
            root_message.extra['form']
        )
        return form


def _save_form(root_message: Message, form):
    root_message.extra['form'] = json.loads(
        jsonpickle.encode(form)
    )
    root_message.save()


def _load_form(root_message: Message):
    if 'form' in root_message.extra:
        form = jsonpickle.decode(
            json.dumps(root_message.extra['form'])
        )
        return form


def get_form(update):
    if root_message := get_form_root(update.telegram_object):
        return load_form(root_message)
