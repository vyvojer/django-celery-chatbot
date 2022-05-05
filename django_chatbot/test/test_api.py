# *****************************************************************************
#  MIT License
#
#  Copyright (c) 2022 Alexey Londkevich <londkevich@gmail.com>
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
from typing import List, Union

from django.utils import timezone

from django_chatbot.models import Message
from django_chatbot.telegram import types
from django_chatbot.telegram.api import Api


class TestApi(Api):
    def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = None,
        entities: List[types.MessageEntity] = None,
        disable_web_page_preview: bool = False,
        disable_notification: bool = False,
        reply_to_message_id: int = None,
        allow_sending_without_reply: bool = True,
        reply_markup: Union[
            types.ForceReply,
            types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup,
            types.ReplyKeyboardRemove,
        ] = None,
    ) -> types.Message:
        """Use this method to send text messages."""
        last_message = Message.objects.order_by("-message_id").first()
        user = types.User(id=1, is_bot=True, username="Bot")
        telegram_chat = types.Chat(id=chat_id, type="private")
        message = types.Message(
            message_id=last_message.message_id + 1,
            date=timezone.now(),
            chat=telegram_chat,
            from_user=user,
            text=text,
            entities=entities,
            reply_markup=reply_markup,
        )
        return message

    def edit_message_text(
        self,
        text: str,
        chat_id: Union[int, str] = None,
        message_id: int = None,
        inline_message_id: str = None,
        parse_mode: str = None,
        entities: List[types.MessageEntity] = None,
        disable_web_page_preview: bool = False,
        reply_markup: types.InlineKeyboardMarkup = None,
    ) -> types.Message:
        """Use this method to send text messages."""
        user = types.User(id=1, is_bot=True, username="Bot")
        telegram_chat = types.Chat(id=chat_id, type="private")
        message = types.Message(
            message_id=message_id,
            date=timezone.now(),
            chat=telegram_chat,
            from_user=user,
            text=text,
            entities=entities,
            reply_markup=reply_markup,
        )
        return message
