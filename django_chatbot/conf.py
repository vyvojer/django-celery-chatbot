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
from collections.abc import MutableMapping

from django.conf import settings as user_settings


class ChatbotSettingsError(Exception):
    pass


DEFAULTS = {
    "DEFAULT_TEST_CLIENT_BOT_NAME": None,
    "BROKER_URL": getattr(user_settings, "CELERY_BROKER_URL", None),
    "BOTS": [],
    "LOAD_HANDLERS_CACHE_SIZE": None,
}


class DjangoChatbotSettings(MutableMapping):
    def __getitem__(self, key):
        if key in user_settings.DJANGO_CHATBOT:
            return user_settings.DJANGO_CHATBOT[key]
        elif key in DEFAULTS:
            return DEFAULTS[key]
        else:
            raise ChatbotSettingsError(f"Chatbot setting '{key}' not found.")

    def __setitem__(self, key, value):
        pass

    def __delitem__(self, key):
        pass

    def __iter__(self):
        pass

    def __len__(self):
        pass


class Settings:
    @property
    def DJANGO_CHATBOT(self):
        try:
            getattr(user_settings, "DJANGO_CHATBOT")
        except AttributeError:
            raise ChatbotSettingsError("DJANGO_CHATBOT settings not found")
        return DjangoChatbotSettings()


settings = Settings()
