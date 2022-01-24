from unittest.mock import Mock, patch

from django.test import TestCase

from django_chatbot import tasks


class DispatchTestCase(TestCase):
    @patch("django_chatbot.tasks.Dispatcher")
    def test_task(self, mocked_dispatcher: Mock):
        update_data = {"key": "value"}
        token_slug = "token"

        tasks.dispatch.s(update_data=update_data, token_slug=token_slug).apply()

        mocked_dispatcher.assert_called_with(token_slug=token_slug)
        mocked_dispatcher.return_value.dispatch.assert_called_with(
            update_data=update_data
        )
