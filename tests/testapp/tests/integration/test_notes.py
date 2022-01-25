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

from testapp.models import Note

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
from django_chatbot.tests import TestCase


class CommandsTestCase(TestCase):
    bot_name = "notes"

    def setUp(self) -> None:
        self.note_1 = Note.objects.create(
            user=self.user.user, title="Title 1", text="Text 1"
        )
        self.note_2 = Note.objects.create(
            user=self.user.user, title="Title 2", text="Text 2"
        )
        self.note_1 = Note.objects.create(
            user=self.user.user, title="Title 3", text="Text 3"
        )

    def test_iterating_notes(self):
        response = self.client.send_message("/notes")
        self.assertContains(response, "Title 1")
        self.assertContains(response, "Text 1")
        self.assertContains(response, "Note 1 of 3")

        response = self.client.send_callback_query(data="next")
        self.assertContains(response, "Title 2")
        self.assertContains(response, "Text 2")
        self.assertContains(response, "Note 2 of 3")
