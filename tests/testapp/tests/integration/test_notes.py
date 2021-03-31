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
from django_chatbot.tests import TestCase, MockUser
from django_chatbot.models import Bot
from testapp.models import Note


class CommandsTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.bot = Bot.objects.create(
            name='bot', token='token',
            root_handlerconf='testapp.handlers'
        )
        self.test_user = MockUser(bot=self.bot)
        self.note_1 = Note.objects.create(
            user=self.test_user.user, title="Title 1", text="Text 1"
        )
        self.note_2 = Note.objects.create(
            user=self.test_user.user, title="Title 2", text="Text 2"
        )
        self.note_1 = Note.objects.create(
            user=self.test_user.user, title="Title 3", text="Text 3"
        )

    def test_iterating_notes(self):
        self.test_user.send_message('/notes')
        bot_message = self.test_user.messages()[0]
        self.assertIn("Title 1", bot_message.text)
        self.assertIn("Text 1", bot_message.text)
        self.assertIn("Note 1 of 3", bot_message.text)

        self.test_user.send_callback_query(data="next")
        bot_message = self.test_user.messages()[0]
        self.assertIn("Title 2", bot_message.text)
        self.assertIn("Text 2", bot_message.text)
        self.assertIn("Note 2 of 3", bot_message.text)


