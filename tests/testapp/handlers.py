from django_chatbot.handlers import CommandHandler, DefaultHandler
from testapp import callbacks

handlers = [
    CommandHandler(callback=callbacks.start, name="start", command="/start"),
    CommandHandler(callback=callbacks.start, name="help", command="/help"),
    DefaultHandler(callback=callbacks.default, name="default"),
]
