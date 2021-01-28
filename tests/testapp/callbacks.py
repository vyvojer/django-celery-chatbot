import logging

from django_chatbot.models import Update
from testapp.models import Note

log = logging.getLogger(__name__)


def default(update: Update):
    update.message.reply("I don't understand you :( /help")


def start(update: Update):
    update.message.reply("""
Command list:
/help - help
/add - add note
/delete - delete note
/count - count notes    
""") # noqa


def count(update: Update):
    user = update.message.from_user
    note_count = Note.objects.filter(user=user).count()
    update.message.reply(f"Note(s) count: {note_count}")
