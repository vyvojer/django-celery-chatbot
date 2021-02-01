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

"""This module contains classes for Telegram bot API"""
import json
import logging
from dataclasses import dataclass
from typing import List, Type, Union

import requests

from .types import (
    ForceReply, InlineKeyboardMarkup, MessageEntity,
    ReplyKeyboardMarkup, ReplyKeyboardRemove, TelegramType,
    User,
    WebhookInfo, Message,
)

log = logging.getLogger(__name__)

SERVER_URL = "https://api.telegram.org"


class TelegramError(Exception):
    """Telegram error

    Args:
        reason: The error description returned by Telegram.
        url: The Telegram API url.
        status_code: Status code of the response.
        response: The Telegram response.
        api_code: The error code returned by Telegram.
    Attributes:
        reason: The error description returned by Telegram.
        url: The Telegram API url.
        status_code: Status code of the response.
        response: The Telegram response.
        api_code: The error code returned by Telegram.
    """

    def __init__(self,
                 reason: str,
                 url: str = None,
                 status_code: int = None,
                 response: requests.Response = None,
                 api_code=None):
        self.reason = reason
        self.url = url
        self.status_code = status_code
        self.response = response
        self.api_code = api_code
        super(TelegramError, self).__init__(reason)

    def __str__(self):
        return self.reason

    def to_dict(self) -> dict:
        return {
            'reason': self.reason,
            'url': self.url,
            'status_code': self.status_code,
            'response': self.response,
            'api_code': self.api_code,
        }


@dataclass
class _Binder:
    """Helper class for communicating with Telegram Bot API.

    The class sends requests to Telegram API and casts responses
    to django_chatbot types.

    Args:
        token: Bot token.
        method_name: Name of Telegram API method.
        params: Parameters of Telegram API methods.
        telegram_type: The 'TelegramType' to which the API response should be
            cast.
    """
    token: str
    method_name: str
    params: dict = None
    telegram_type: Type[TelegramType] = None

    def __post_init__(self):
        self.url = f"{SERVER_URL}/bot{self.token}/{self.method_name}"

    def bind(self):
        """Request to Telegram API and cast result to :class:`TelegramType`

        Returns:
            The casted to ``self.telegram_type`` API response.

        Raises:
            TelegramError: If there is telegram or requests error.
        """
        if self.params:
            params = {k: v for k, v in self.params.items() if v is not None}
            response = requests.post(url=self.url, data=params)
            log.debug(
                "Telegram params=%s response: url=%s, status_code=%s, json=%s",
                params, response.url, response.status_code, response.json()
            )
        else:
            response = requests.get(url=self.url)
            log.debug(
                "Telegram request response: url=%s, status_code=%s, json=%s",
                response.url, response.status_code, response.json()
            )
        result = self._parse_response(response, self.telegram_type)
        return result

    @staticmethod
    def _parse_response(response: requests.Response,
                        telegram_type: Type[TelegramType]):
        """Parse response

        Args:
            response: requests response object.
            telegram_type: Type to which should be casted.

        Returns:
            The casted telegram API response

        Raises:
            TelegramError: If there was telegram or requests error.
        """
        if response.status_code == 200:
            response_result = response.json()
            result = _Binder._get_result(response_result, telegram_type)
            return result
        else:
            response_json = response.json()
            raise TelegramError(
                reason=response_json["description"],
                url=response.url,
                status_code=response.status_code,
                response=response_json,
                api_code=response_json["error_code"]
            )

    @staticmethod
    def _get_result(response_result: dict,
                    telegram_type: Type[TelegramType]):
        """Extract result from response dictionary

        Args:
            response_result: telegram response dictionary
            telegram_type:

            telegram_type: Type to which should be casted.

        Returns:
            The casted telegram API response
        """
        if response_result["ok"]:
            result = response_result["result"]
            if telegram_type is None:
                return result
            else:
                return telegram_type.from_dict(source=result)


class Api:
    """Telegram API client

    Args:
        token: Bot token

    Attributes:
        token: Bot token

    """
    def __init__(self, token: str):
        self.token = token

    def _bind(self,
              method_name: str,
              params: dict = None,
              telegram_type: Type[TelegramType] = None):
        """Make request to API and return casted response.

        Args:
            method_name: Name of Telegram API method.
            params: Parameters of Telegram API methods.
            telegram_type: The 'TelegramType' to which the API response
                should be casted.

        Returns:
            Casted response.

        Raises:
            TelegramError: If there was telegram or requests error.
        """
        binder = _Binder(
            token=self.token, method_name=method_name,
            params=params, telegram_type=telegram_type
        )
        return binder.bind()

    def get_me(self) -> User:
        """Return basic information about the bot in form of a ``User`` object.

        https://core.telegram.org/bots/api#getme

        Returns:
            `User` object.
        """
        return self._bind(
            method_name="getMe",
            telegram_type=User,
        )

    def get_webhook_info(self) -> WebhookInfo:
        return self._bind(
            method_name="getWebhookInfo",
            telegram_type=WebhookInfo,
        )

    def set_webhook(self,
                    url: str,
                    max_connections: int = None,
                    allowed_updates: List[str] = None) -> bool:
        """Use this method to specify a webhook.

        https://core.telegram.org/bots/api#setwebhook



        Args:
            url:
            max_connections:
            allowed_updates:

        Returns:
            True on success
        """
        params = {
            'url': url,
            'max_connections': max_connections,
            'allowed_updates': allowed_updates,
        }
        return self._bind(
            method_name="setWebhook",
            params=params,
        )

    def send_message(self,
                     chat_id: int,
                     text: str,
                     parse_mode: str = None,
                     entities: List[MessageEntity] = None,
                     disable_web_page_preview: bool = False,
                     disable_notification: bool = False,
                     reply_to_message_id: int = None,
                     allow_sending_without_reply: bool = True,
                     reply_markup: Union[
                         ForceReply,
                         InlineKeyboardMarkup,
                         ReplyKeyboardMarkup,
                         ReplyKeyboardRemove,
                     ] = None
                     ) -> Message:
        """Use this method to send text messages.

        https://core.telegram.org/bots/api#sendmessage

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername).
            text: Text of the message to be sent, 1-4096 characters
                after entities parsing.
            parse_mode: Mode for parsing entities in the message text.
                One of `MarkdownV2`, `HTML`, `Markdown`.
            entities: List of special entities that appear in message text,
                which can be specified instead of parse_mode.
            disable_web_page_preview: Disables link previews for links
                in this message.
            disable_notification: Sends the message silently.
                Users will receive a notification with no sound.
            reply_to_message_id: If the message is a reply,
                ID of the original message.
            allow_sending_without_reply: Pass True, if the message
                should be sent even if the specified replied-to message
                is not found.
            reply_markup: Additional interface options. A JSON-serialized
                object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force
                a reply from the user.

        Returns:
            On success, the sent `Message` is returned.
        """
        if entities:
            entities = [e.to_dict() for e in entities]
        if reply_markup:
            reply_markup = json.dumps(reply_markup.to_dict())
        params = {
            'chat_id': chat_id,
            'text': text,
            'entities': entities,
            'parse_mode': parse_mode,
            'disable_web_page_preview': disable_web_page_preview,
            'disable_notification': disable_notification,
            'reply_to_message_id': reply_to_message_id,
            'allow_sending_without_reply': allow_sending_without_reply,
            'reply_markup': reply_markup,
        }
        return self._bind(
            method_name="sendMessage",
            params=params,
            telegram_type=Message
        )


@dataclass(eq=True)
class SendMessageParams:
    """ Encapsulate send_message parameters"""
    text: str
    parse_mode: str = None
    entities: List[MessageEntity] = None
    disable_web_page_preview: bool = None
    disable_notification: bool = None
    allow_sending_without_reply: bool = None
    reply_markup: Union[
        InlineKeyboardMarkup, ReplyKeyboardMarkup,
        ReplyKeyboardRemove, ForceReply,
    ] = None

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}
