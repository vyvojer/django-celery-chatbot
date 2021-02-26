from django_chatbot.handlers import CommandHandler, DefaultHandler
from testapp import callbacks
from testapp.forms import AddNote, DeleteNoteForm

handlers = [
    CommandHandler(
        name="start",
        command="/start",
        callback=callbacks.start,
        suppress_form=True,
    ),
    CommandHandler(
        name="help",
        command="/help",
        callback=callbacks.start,
        suppress_form=True,
    ),
    CommandHandler(
        name="cancel current input",
        command="/cancel",
        callback=callbacks.start,
        suppress_form=True,
    ),
    CommandHandler(name="count", command="/count", callback=callbacks.count),
    CommandHandler(name="add", command="/add", form_class=AddNote),
    CommandHandler(
        name="delete", command="/delete", form_class=DeleteNoteForm
    ),
    DefaultHandler(name="default", callback=callbacks.default),
]
