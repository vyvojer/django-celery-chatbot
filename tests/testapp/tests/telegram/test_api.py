from dataclasses import dataclass
from typing import List
from unittest import TestCase
from unittest.mock import Mock, patch

from django_chatbot.telegram.api import _Binder, TelegramError
from django_chatbot.telegram.types import TelegramType


class BinderTestCase(TestCase):
    @patch("django_chatbot.telegram.api.requests.get")
    def test_bind__without_params_invokes_get(self, mocked_get: Mock):
        mocked_get.return_value.status_code = 200
        mocked_get.return_value.json.return_value = {
            "ok": True, "result": None
        }
        binder = _Binder(token="test_token", method_name="method_name")

        binder.bind()

        mocked_get.assert_called_with(
            url="https://api.telegram.org/bottest_token/method_name")

    @patch("django_chatbot.telegram.api.requests.post")
    def test_bind__with_params_invokes_post(self, mocked_post: Mock):
        mocked_post.return_value.status_code = 200
        mocked_post.return_value.json.return_value = {
            "ok": True, "result": None
        }
        params = {"a": 1, "b": 2}
        binder = _Binder(
            token="test_token", method_name="method_name", params=params)

        binder.bind()

        mocked_post.assert_called_with(
            url="https://api.telegram.org/bottest_token/method_name",
            data=params,
        )

    @patch("django_chatbot.telegram.api.requests.post")
    def test_bind__with_params_ignores_none_params(self, mocked_post: Mock):
        mocked_post.return_value.status_code = 200
        mocked_post.return_value.json.return_value = {
            "ok": True, "result": None
        }
        params = {"a": 1, "b": None, "c": 2}
        binder = _Binder(
            token="test_token",
            method_name="method_name",
            params=params)

        binder.bind()

        mocked_post.assert_called_with(
            url="https://api.telegram.org/bottest_token/method_name",
            data={"a": 1, "c": 2},
        )

    @patch("django_chatbot.telegram.api.requests.get")
    def test_bind__without_return_type_returns_dict(self, mocked_get: Mock):
        mocked_get.return_value.status_code = 200
        mocked_get.return_value.json.return_value = {
            "ok": True,
            "result": {"answer": 42}
        }
        binder = _Binder(token="test_token", method_name="method_name")

        result = binder.bind()

        self.assertEqual(result, {"answer": 42})

    @patch("django_chatbot.telegram.api.requests.get")
    def test_bind__with_return_type_returns_filled_object_of_type(
            self, mocked_get: Mock
    ):
        mocked_get.return_value.status_code = 200
        mocked_get.return_value.json.return_value = {
            "ok": True,
            "result": {
                "parent_p1": 1,
                "parent_p2": {
                    "child_p1": [
                        {"grandchild_p1": 5, "grandchild_p2": ["a", "b"]},
                        {"grandchild_p1": 6, "grandchild_p2": ["c", "d"]},
                        {"grandchild_p1": 7, "grandchild_p2": ["e", "f"]},
                    ],
                    "child_p2": 2,
                }
            }
        }

        @dataclass(eq=True)
        class GrandChild(TelegramType):
            grandchild_p1: int
            grandchild_p2: List[str]

        @dataclass(eq=True)
        class Child(TelegramType):
            child_p1: List[GrandChild]
            child_p2: int

        @dataclass(eq=True)
        class Parent(TelegramType):
            parent_p1: int
            parent_p2: Child

        binder = _Binder(
            token="test_token",
            method_name="method_name",
            telegram_type=Parent
        )

        result = binder.bind()

        self.assertTrue(isinstance(result, Parent))
        self.assertEqual(
            result,
            Parent(
                parent_p1=1,
                parent_p2=Child(
                    child_p1=[
                        GrandChild(5, ["a", "b"]),
                        GrandChild(6, ["c", "d"]),
                        GrandChild(7, ["e", "f"]),
                    ],
                    child_p2=2,
                )
            )
        )

    @patch("django_chatbot.telegram.api.requests.get")
    def test_bind__telegram_not_ok(self, mocked_get: Mock):
        mocked_get.return_value.status_code = 401
        mocked_get.return_value.json.return_value = {
            "ok": False,
            "error_code": 401,
            "description": "Unauthorized",
        }
        binder = _Binder(token="test_token", method_name="method_name")

        with self.assertRaises(TelegramError) as context:
            binder.bind()

        self.assertEqual(context.exception.reason, "Unauthorized")
