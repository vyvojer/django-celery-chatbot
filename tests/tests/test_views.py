from unittest.mock import Mock, patch

from django.test import TestCase
from django.urls import reverse


class WebhookTestCase(TestCase):
    @patch("django_chatbot.views.dispatch")
    def test_return_ok(self, mocked_dispatch: Mock):
        data = {"key": "value"}
        token_slug = "token_slug"
        response = self.client.post(
            reverse("django_chatbot:webhook", kwargs={"token_slug": token_slug}),
            data=data,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        mocked_dispatch.delay.assert_called_with(
            update_data=data, token_slug=token_slug
        )
