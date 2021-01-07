#  MIT License
#
#  Copyright (c) 2020 Alexey Londkevich
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

import logging
from dataclasses import dataclass
from typing import List, Type

import requests

from .types import (
    MessageEntity,
    TelegramType,
    User,
    WebhookInfo, Message,
)

log = logging.getLogger(__name__)

SERVER_URL = "https://api.telegram.org"


class TelegramError(Exception):
    """Telegram exception"""

    def __init__(self,
                 reason,
                 url=None,
                 status_code=None,
                 response=None,
                 api_code=None):
        self.reason = reason
        self.url = url
        self.status_code = status_code
        self.response = response
        self.api_code = api_code
        super(TelegramError, self).__init__(reason)

    def __str__(self):
        return self.reason

    def to_dict(self):
        return {
            'reason': self.reason,
            'url': self.url,
            'status_code': self.status_code,
            'response': self.response,
            'api_code': self.api_code,
        }


@dataclass
class _Binder:
    token: str
    method_name: str
    params: dict = None
    telegram_type: Type[TelegramType] = None

    def __post_init__(self):
        self.url = f"{SERVER_URL}/bot{self.token}/{self.method_name}"

    def bind(self):
        if self.params:
            params = {k: v for k, v in self.params.items() if v is not None}
            response = requests.post(url=self.url, data=params)
        else:
            response = requests.get(url=self.url)
        result = self._parse_response(response, self.telegram_type)
        return result

    @staticmethod
    def _parse_response(response: requests.Response,
                        telegram_type: Type[TelegramType]):
        log.debug(
            "Telegram response: url=%s, status_code=%s, json=%s",
            response.url, response.status_code, response.json()
        )
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
        if response_result["ok"]:
            result = response_result["result"]
            if telegram_type is None:
                return result
            else:
                return telegram_type.from_dict(source=result)


class Api:
    def __init__(self, token):
        self.token = token

    def _bind(self,
              method_name: str,
              params: dict = None,
              telegram_type: Type[TelegramType] = None):
        binder = _Binder(
            token=self.token, method_name=method_name,
            params=params, telegram_type=telegram_type
        )
        return binder.bind()

    def get_me(self) -> User:
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
        params = locals()
        params.pop('self')
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
                     ) -> Message:
        params = locals()
        if entities is not None:
            params['entities'] = [me.to_dict() for me in entities]
        params.pop('self')
        return self._bind(
            method_name="sendMessage",
            params=params,
            telegram_type=Message
        )
