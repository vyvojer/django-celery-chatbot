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


