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

# *****************************************************************************
#  MIT License
#
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense,
#  and/or sell copies of the Software, and to permit persons to whom
#  the Software is furnished to do so, subject to the following conditions:
#
#
from django_chatbot.handlers import CommandHandler, DefaultHandler
from testapp import callbacks
from testapp.forms import AddNote, DeleteNoteForm, NotesForm

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
    CommandHandler(name="notes", command="/notes", form_class=NotesForm),
    DefaultHandler(name="default", callback=callbacks.default),
]
