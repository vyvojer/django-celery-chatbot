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
from unittest.mock import Mock, patch

from django.test import TestCase
from factories.factories import FieldFactory, FormFactory, MessageFactory, UpdateFactory

from django_chatbot import models
from django_chatbot.forms import Field, Form, FormRepository


class FormForTest(Form):
    field1 = Field("first_prompt")
    field2 = Field("second_prompt")
    field3 = Field("third_prompt")


class RepositorySaveFormTest(TestCase):
    def setUp(self) -> None:
        self.handler = Mock()
        self.handler.name = "test_handler"

    def test_save_form(self):
        update = UpdateFactory()
        prompt_message = MessageFactory()
        handler = Mock()
        handler.name = "handler"
        repository = FormRepository(update, handler=self.handler)
        repository.prompt_message = prompt_message

        form = FormForTest(repository=self)

        form.field1.value = "first_value"
        form.field1.is_valid = True
        form.field2.value = "second_value"
        form.field2.is_valid = False

        form.current_field = form.field2
        form.context = {"context_key": "context_value"}

        form_model = repository.save_form(form)

        self.assertEqual(models.Form.objects.count(), 1)
        self.assertEqual(form_model, models.Form.objects.first())
        self.assertEqual(models.Field.objects.count(), 3)
        field1_model = models.Field.objects.get(name="field1")
        field2_model = models.Field.objects.get(name="field2")

        self.assertEqual(field1_model.form, form_model)
        self.assertEqual(field1_model.value, "first_value")
        self.assertEqual(field1_model.is_valid, True)
        self.assertEqual(field2_model.value, "second_value")
        self.assertEqual(field2_model.is_valid, False)

        self.assertEqual(form_model.context, {"context_key": "context_value"})
        self.assertEqual(form_model.current_field, "field2")
        self.assertEqual(form_model.is_finished, False)
        self.assertEqual(form_model.module_name, "tests.forms.test_repository")
        self.assertEqual(form_model.class_name, "FormForTest")
        self.assertEqual(form_model.handler, self.handler.name)

        self.assertEqual(update.telegram_object.form, form_model)
        self.assertEqual(prompt_message.form, form_model)
        self.assertEqual(update.handler, self.handler.name)

    def test_save_form_doesnt_create_new_model_if_model_exists(self):
        """
        If form already exists in database, it should not create new model
        """
        update = UpdateFactory()
        prompt_message = MessageFactory()
        repository = FormRepository(update, handler=self.handler)
        repository.prompt_message = prompt_message

        form = FormForTest(repository=self)

        form.field1.value = "first_value"
        form.field1.is_valid = True
        form.field2.value = "second_value"
        form.field2.is_valid = False

        form.current_field = form.field2
        form.context = {"context_key": "context_value"}

        form_model = repository.save_form(form)

        self.assertEqual(models.Form.objects.count(), 1)
        self.assertEqual(form_model, models.Form.objects.first())
        self.assertEqual(models.Field.objects.count(), 3)
        field1_model = models.Field.objects.get(name="field1")
        field2_model = models.Field.objects.get(name="field2")

        self.assertEqual(field1_model.form, form_model)
        self.assertEqual(field1_model.value, "first_value")
        self.assertEqual(field1_model.is_valid, True)
        self.assertEqual(field2_model.value, "second_value")
        self.assertEqual(field2_model.is_valid, False)

        repository.form_model = form_model
        form.field1.value = "new_first_value"
        form_model = repository.save_form(form)

        self.assertEqual(models.Form.objects.count(), 1)
        self.assertEqual(form_model, models.Form.objects.first())
        self.assertEqual(models.Field.objects.count(), 3)

        field1_model = models.Field.objects.get(name="field1")

        self.assertEqual(field1_model.form, form_model)
        self.assertEqual(field1_model.value, "new_first_value")


class RepositoryLoadFormTest(TestCase):
    def test_load_form(self):
        form_model = FormFactory(
            module_name="tests.forms.test_repository",
            class_name="FormForTest",
            current_field="field2",
            context={"context_key": "context_value"},
            is_finished=False,
        )
        FieldFactory(
            form=form_model,
            name="field1",
            value="first_value",
            is_valid=True,
        )
        FieldFactory(
            form=form_model,
            name="field2",
            value="second_value",
            is_valid=False,
        )

        repository = FormRepository(update=Mock())

        form = repository._load_form(form_model)

        self.assertEqual(isinstance(form, FormForTest), True)
        self.assertEqual(form.context, {"context_key": "context_value"})
        self.assertEqual(form.is_finished, False)
        self.assertEqual(form.field1.value, "first_value")
        self.assertEqual(form.field1.is_valid, True)
        self.assertEqual(form.field2.value, "second_value")
        self.assertEqual(form.field2.is_valid, False)


class RepositoryInitTest(TestCase):
    @patch("django_chatbot.forms.forms.Form.start")
    def test_form_created_from_form_class(self, mocked_form_start):
        form_class = FormForTest

        repository = FormRepository(update=Mock(), form_class=form_class)

        self.assertEqual(isinstance(repository.form, FormForTest), True)
