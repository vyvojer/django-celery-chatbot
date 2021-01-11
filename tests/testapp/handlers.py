from django_chatbot.handlers import CommandHandler, DefaultHandler
from testapp import callbacks
from testapp.forms import NoteForm

handlers = [
    CommandHandler(name="start", command="/start", callback=callbacks.start),
    CommandHandler(name="help", command="/help", callback=callbacks.start),
    CommandHandler(name="show_notes", command="/show_notes",
                   callback=callbacks.start),
    CommandHandler(name="add_note", command="/add_note", form_class=NoteForm),
    CommandHandler(name="count", command="/count", callback=callbacks.count),
    DefaultHandler(name="default", callback=callbacks.default),
]
