import logging

from django_chatbot.models import Update

log = logging.getLogger(__name__)


def default(update: Update):
    update.message.reply("I don't understand you", reply_to=True)
