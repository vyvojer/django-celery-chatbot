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

import importlib
from functools import lru_cache
from typing import Dict, List

from django_chatbot.models import Bot
from django_chatbot.services.updates import save_update
from django_chatbot.handlers import Handler


@lru_cache()
def load_handlers() -> Dict[str, List[Handler]]:
    handlers = {}
    for bot in Bot.objects.all():
        handlers[bot.token_slug] = _load_bot_handlers(bot.root_handlerconf)
    return handlers


def _load_bot_handlers(name: str) -> List[Handler]:
    module = importlib.import_module(name)
    return module.handlers


class Dispatcher:
    def __init__(self, update_data: dict, token_slug: str):
        self.bot = Bot.objects.get(token_slug=token_slug)
        self.update = save_update(bot=self.bot, update_data=update_data)
        self.handlers = load_handlers()

    def dispatch(self):
        for handler in self.handlers[self.bot.token_slug]:
            if handler.check_update(update=self.update):
                handler.handle_update(update=self.update)
                break
