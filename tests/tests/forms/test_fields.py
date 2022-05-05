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
from unittest.mock import Mock

from django_chatbot.forms.fields import Field


class FieldTest(TestCase):
    def test_assign_value(self):
        field = Field("Input value")
        field.input("value", Mock())
        self.assertEqual(field.value, "value")

    def test_add_next_field_without_condition(self):
        """Test that default condition is added to every next field"""
        field = Field("Field 1")
        next_field_2a = Field("Field 2a")
        next_field_2b = Field("Field 2b")
        field.add_next_field(next_field_2a)
        field.add_next_field(next_field_2b)
        self.assertEqual(field._next_fields[0][0], next_field_2a)
        self.assertEqual(field._next_fields[1][0], next_field_2b)

        # The default condition is always returns True
        self.assertTrue(field._next_fields[0][1]())
        self.assertTrue(field._next_fields[1][1]())

    def test_add_next_fields_without_condition(self):
        "Field can be added with and without condition"
        field = Field("Field 1")
        condition_2a = lambda *args, **kwargs: False
        next_field_2a = Field("Field 2a")
        next_field_2b = Field("Field 2b")
        field.add_next_fields((next_field_2a, condition_2a), next_field_2b)
        self.assertEqual(field._next_fields[0][0], next_field_2a)
        self.assertEqual(field._next_fields[1][0], next_field_2b)

        # The default condition is always returns True
        self.assertFalse(field._next_fields[0][1]())
        self.assertTrue(field._next_fields[1][1]())

    def test_get_next_field_returns_first_next_field_if_no_condition(self):
        value = "value"
        form = Mock()

        field = Field("Field 1")
        next_field_2a = Field("Field 2a")
        next_field_2b = Field("Field 2b")
        field.add_next_fields(next_field_2a, next_field_2b)
        self.assertEqual(field.get_next_field(value, form), next_field_2a)

    def test_get_next_field_returns_first_next_field_with_condition(self):
        value = "value"
        form = Mock()

        field = Field("Field 1")
        next_field_2a = Field("Field 2a")
        next_field_2b = Field("Field 2b")
        field.add_next_fields(next_field_2a, next_field_2b)
        self.assertEqual(field.get_next_field(value, form), next_field_2a)
