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

""" This module contains class dispatching incoming Telegram updates"""

import importlib
import logging
from typing import Dict, Iterable, List

from django_chatbot.handlers import Handler
from django_chatbot.models import Bot, Form, Update
from django_chatbot.telegram.types import Update as TelegramUpdate

log = logging.getLogger(__name__)


def load_handlers() -> Dict[str, List[Handler]]:
    """Load registered handlers for all bots

    Returns:
        dictionary like
        {'first_bot_token':[Handler_1, Handler_2 ... ]

    """
    handlers = {}
    for bot in Bot.objects.all():
        handlers[bot.token_slug] = _load_bot_handlers(bot.root_handlerconf)
        log.info(
            "Handlers %s for bot %s has been loaded",
            bot.root_handlerconf,
            bot.name,
        )
    return handlers


def _load_bot_handlers(module_name: str) -> List[Handler]:
    """Return handler for a bot.

    django_chatbot loads the module and looks for the variable `handlers`.
    This should be a list of `Handler` instances.

    Args:
        module_name: Full module name where to search handlers.

    Returns:
        list of `Handler`

    """
    module = importlib.import_module(module_name)
    return module.handlers  # noqa


class Dispatcher:
    """This class dispatches incoming Telegram updates.

    Dispatcher iterates all registered handlers until the handler matches
    the update. Then Dispatcher calls the handler `handle_update` method.

    Note: To register handlers for a bot, add some module that contains
        the `handlers` variable. This should be a list of `Handler` instances.
        Then add the module name to bot 'ROOT_HANDLERCONF' setting.

    Args:
        update_data: The incoming update dictionary.
        token_slug: The bot token slug.

    Attributes:
        bot (Bot): The bot model.
        update (Update): The update object.
        handlers: List of handler registered to this bot.

    """

    def __init__(self, token_slug: str):
        self.bot = Bot.objects.get(token_slug=token_slug)
        self.handlers = load_handlers()[self.bot.token_slug]

    def dispatch(self, update_data: dict):
        """Dispatch incoming Telegram updates"""
        update = Update.objects.from_telegram(
            bot=self.bot, telegram_update=TelegramUpdate.from_dict(update_data)
        )
        if form_keeper := Form.objects.get_form(update):
            if not self._check_handlers(
                update=update, handlers=[h for h in self.handlers if h.suppress_form]
            ):
                form_keeper.form.update(update=update)
        else:
            self._check_handlers(update, self.handlers)

    @staticmethod
    def _check_handlers(update: Update, handlers: Iterable[Handler]) -> bool:
        """Check if one of the handlers match the update

        Args:
            update: The update to check.
            handlers: The handlers to check.

        Returns:
            True if one of the handlers match the update.

        """
        for handler in handlers:
            if handler.match(update=update):
                handler.handle_update(update=update)
                return True
        return False
