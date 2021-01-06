from django_chatbot.handlers import DefaultHandler
from testapp import callbacks
handlers = [
    DefaultHandler(callback=callbacks.default)
]