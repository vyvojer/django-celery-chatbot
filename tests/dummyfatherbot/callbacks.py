# *****************************************************************************
#  MIT License
#
#  Copyright (c) 2022 Alexey Londkevich <londkevich@gmail.com>
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
from django_chatbot.models import Update


def default(update: Update):
    update.telegram_object.chat.reply("I don't understand you :( /help")


def help(update: Update):
    update.telegram_object.chat.reply(
        """
    I can help you to find a doctor.
    You can ask me:
    - "Find me a doctor"
    - "Find me a doctor in Moscow"
    - "Find me a doctor in Moscow, Moscow"
    - "Find me a doctor in Moscow, Moscow, Russia"
    - "Find me a doctor in Moscow, Moscow, Russia, Moscow"
    Command list:
    - /help - show this help
    - /start - start conversation
    """
    )
