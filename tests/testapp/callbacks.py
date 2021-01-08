import logging

from django_chatbot.models import Update

log = logging.getLogger(__name__)


def default(update: Update):
    update.message.reply("I don't understand you", reply=True)


def start(update: Update):
    update.message.reply("""
    Command list:
    /add_note - add text note
    /count - return note count
    /show_note number - show note
    """)
