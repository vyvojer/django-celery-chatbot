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
from unittest import TestCase

from django_chatbot import forms


class FakeRepository:
    def __init__(self):
        self.data = []
        self._current_id = 1
        self.chat = "chat"

    def sent_message(self, message, inline_keyboard=None):
        self.data.append(
            {
                "id": self._current_id,
                "message": message,
                "inline_keyboard": inline_keyboard,
            }
        )
        self._current_id += 1

    def edit_message(self, message, inline_keyboard=None):
        self.data[-1] = {
            "id": self.data[-1]["id"],
            "message": message,
            "inline_keyboard": inline_keyboard,
        }

    def save_form(self, form):
        pass


class FormTest(TestCase):
    def test_form_gives_names_to_fields(self):
        class Form(forms.Form):
            first = forms.Field("first prompt")
            second = forms.Field("second prompt")

        form = Form(repository=FakeRepository())

        self.assertEqual(form.first.name, "first")
        self.assertEqual(form.second.name, "second")

    def test_get_root_returns_the_first_field(self):
        class Form(forms.Form):
            first = forms.Field("first prompt")
            second = forms.Field("second prompt")

        form = Form(repository=FakeRepository())
        root = form.get_root_field()

        self.assertEqual(root, form.first)

    def test_connect_fields_connects_them_one_by_one(self):
        class Form(forms.Form):
            first = forms.Field("first prompt")
            second = forms.Field("second prompt")
            third = forms.Field("third prompt")

        form = Form(repository=FakeRepository())
        root_field = form.get_root_field()

        self.assertEqual(root_field, form.first)

        self.assertEqual(form.first.get_next_field(None, None), form.second)
        self.assertEqual(form.second.get_next_field(None, None), form.third)
        self.assertEqual(form.third.get_next_field(None, None), None)


class SimpleFormFlowTest(TestCase):
    def setUp(self) -> None:
        class Form(forms.Form):
            first = forms.Field("first prompt")
            second = forms.Field("second prompt")

            def on_finish(self, chat):
                self.repository.sent_message("Finished")

        self.repository = FakeRepository()
        self.form = Form(repository=self.repository)

    def test_all_fields_is_unbound_before_start(self):
        self.assertFalse(self.form.first.is_bound)
        self.assertFalse(self.form.second.is_bound)

    # start

    def test_all_fields_is_unbound_after_start(self):
        self.form.start()
        self.assertFalse(self.form.first.is_bound)
        self.assertFalse(self.form.second.is_bound)

    def test_form_is_not_finished_after_start(self):
        self.form.start()
        self.assertFalse(self.form.is_finished)

    def test_there_is_the_first_prompt_after_start(self):
        self.form.start()
        self.assertEqual(
            self.repository.data,
            [
                {"id": 1, "message": "first prompt", "inline_keyboard": None},
            ],
        )

    # first input

    def test_first_has_value_after_first_input(self):
        self.form.start()
        self.form.input("first value")
        self.assertEqual(self.form.first.value, "first value")
        self.assertFalse(self.form.second.is_bound)

    def test_form_is_not_finished_after_first_input(self):
        self.form.start()
        self.assertFalse(self.form.is_finished)

    def test_there_is_the_second_prompt_after_first_input(self):
        self.form.start()
        self.form.input("first value")
        self.assertEqual(
            self.repository.data,
            [
                {"id": 1, "message": "first prompt", "inline_keyboard": None},
                {"id": 2, "message": "second prompt", "inline_keyboard": None},
            ],
        )

    # second input

    def test_first_and_second_have_value_after_second_input(self):
        self.form.start()
        self.form.input("first value")
        self.form.input("second value")
        self.assertEqual(self.form.first.value, "first value")
        self.assertEqual(self.form.second.value, "second value")

    def test_form_is_finished_after_second_input(self):
        self.form.start()
        self.form.input("first value")
        self.form.input("second value")
        self.assertTrue(self.form.is_finished)

    def test_there_is_the_finish_message_after_second_input(self):
        self.form.start()
        self.form.input("first value")
        self.form.input("second value")
        self.assertEqual(
            self.repository.data,
            [
                {"id": 1, "message": "first prompt", "inline_keyboard": None},
                {"id": 2, "message": "second prompt", "inline_keyboard": None},
                {"id": 3, "message": "Finished", "inline_keyboard": None},
            ],
        )


class FormWithInlineKeyboardFieldFlowTest(TestCase):
    def setUp(self) -> None:
        class Form(forms.Form):
            first = forms.Field("first prompt", inline_keyboard="first keyboard")

        self.repository = FakeRepository()
        self.form = Form(repository=self.repository)

    def test_all_fields_is_unbound_before_start(self):
        self.assertFalse(self.form.first.is_bound)

    # start

    def test_all_fields_is_unbound_after_start(self):
        self.form.start()
        self.assertFalse(self.form.first.is_bound)

    def test_there_is_the_first_prompt_after_start(self):
        self.form.start()
        self.assertEqual(
            self.repository.data,
            [
                {
                    "id": 1,
                    "message": "first prompt",
                    "inline_keyboard": "first keyboard",
                },
            ],
        )

    # first input

    def test_first_has_value_after_first_input(self):
        self.form.start()
        self.form.input("first value")
        self.assertEqual(self.form.first.value, "first value")


class FormWithOnTheFlyUpdateTest(TestCase):
    def setUp(self) -> None:
        class Form(forms.Form):
            first = forms.Field("first prompt", inline_keyboard="first keyboard")
            second = forms.Field(
                "second prompt",
                inline_keyboard="second keyboard",
            )

            def connect_fields(self):
                self.first.add_next_field(
                    self.second, prompt_type=forms.PromptType.UPDATE_MESSAGE
                )
                self.second.add_next_fields(
                    (
                        self.first,
                        lambda v, f: v == "to_first",
                        forms.PromptType.UPDATE_MESSAGE,
                    ),
                    None,
                )

        self.repository = FakeRepository()
        self.form = Form(repository=self.repository)

    def test_all_fields_is_unbound_before_start(self):
        self.assertFalse(self.form.first.is_bound)

    # start

    def test_all_fields_is_unbound_after_start(self):
        self.form.start()
        self.assertFalse(self.form.first.is_bound)

    def test_there_is_the_first_prompt_after_start(self):
        self.form.start()
        self.assertEqual(
            self.repository.data,
            [
                {
                    "id": 1,
                    "message": "first prompt",
                    "inline_keyboard": "first keyboard",
                },
            ],
        )

    # first input

    def first_input(self):
        self.form.start()
        self.form.input("first value")

    def test_first_field_has_value_after_first_input(self):
        self.first_input()
        self.assertEqual(self.form.first.value, "first value")
        self.assertEqual(self.form.second.value, None)

    def test_form_is_not_finished_after_first_input(self):
        self.first_input()
        self.assertFalse(self.form.is_finished)

    def test_first_message_is_updated_by_second_prompt(self):
        self.first_input()
        self.assertEqual(
            self.repository.data,
            [
                {
                    "id": 1,
                    "message": "second prompt",
                    "inline_keyboard": "second keyboard",
                },
            ],
        )

    # second input returns to first field

    def second_input(self):
        self.form.start()
        self.form.input("first value")
        self.form.input("to_first")  # second input has "returning" to first field value

    def test_second_field_has_value_after_second_input(self):
        self.second_input()
        self.assertEqual(self.form.first.value, "first value")
        self.assertEqual(self.form.second.value, "to_first")

    def test_form_is_not_yet_finished_after_second_returning_input(self):
        self.second_input()
        self.assertFalse(self.form.is_finished)

    def test_there_is_first_prompt_again(self):
        self.second_input()
        self.assertEqual(
            self.repository.data,
            [
                {
                    "id": 1,
                    "message": "first prompt",
                    "inline_keyboard": "first keyboard",
                },
            ],
        )

    def test_all_fields_have_value_after_second_input(self):
        self.second_input()
        self.assertEqual(self.form.first.value, "first value")
        self.assertEqual(self.form.second.value, "to_first")

    # third input

    def third_input(self):
        self.form.start()
        self.form.input("first value")
        self.form.input("to_first")  # second input has "returning" to first field value
        self.form.input("first value again")

    def test_third_field_has_value_after_third_input(self):
        self.third_input()
        self.assertEqual(self.form.first.value, "first value again")
        self.assertEqual(self.form.second.value, "to_first")

    def test_form_is_not_finished_after_third_input(self):
        self.third_input()
        self.assertFalse(self.form.is_finished)

    def test_third_message_is_updated_by_second_prompt(self):
        self.third_input()
        self.assertEqual(
            self.repository.data,
            [
                {
                    "id": 1,
                    "message": "second prompt",
                    "inline_keyboard": "second keyboard",
                },
            ],
        )

    # fourth input finishes the form

    def fourth_input(self):
        self.form.start()
        self.form.input("first value")
        self.form.input("to_first")  # second input has "returning" to first field value
        self.form.input("first value again")
        self.form.input("finish")

    def test_fourth_field_has_value_after_fourth_input(self):
        self.fourth_input()
        self.assertEqual(self.form.first.value, "first value again")
        self.assertEqual(self.form.second.value, "finish")

    def test_form_is_finished_after_fourth_input(self):
        self.fourth_input()
        self.assertTrue(self.form.is_finished)

    def test_there_is_no_prompt_after_fourth_input(self):
        self.fourth_input()
        self.assertEqual(
            self.repository.data,
            [
                {
                    "id": 1,
                    "message": "second prompt",
                    "inline_keyboard": "second keyboard",
                },
            ],
        )
