from unittest.mock import call, patch, Mock

from django.test import TestCase

from django_chatbot.services.dispatcher import (
    Dispatcher,
    _load_bot_handlers,
    load_handlers,
)
from django_chatbot.models import Bot

handlers = [
    "handler1",
    "handler2",
]


class LoadBotHandlersTestCase(TestCase):
    def setUp(self) -> None:
        handler1 = Mock()
        handler2 = Mock()
        self.handlers = [
            handler1,
            handler2,
        ]

    def test_load_bot_handlers(self):
        bot_handlers = _load_bot_handlers(
            "testapp.tests.services.test_dispatcher"
        )

        self.assertEqual(bot_handlers, handlers)


class LoadHandlersTestCase(TestCase):
    @patch("django_chatbot.services.dispatcher._load_bot_handlers")
    def test_load_handlers(self, mocked_load_bot_handlers: Mock):
        Bot.objects.create(
            name="bot1",
            token="token1",
            root_handlerconf="module1"
        )
        Bot.objects.create(
            name="bot2",
            token="token2",
            root_handlerconf="module2"
        )
        mocked_load_bot_handlers.side_effect = [
            ["handler1_1", "handler1_2"],
            ["handler2_1", "handler2_2"],
        ]

        handlers = load_handlers()

        self.assertEqual(
            handlers,
            {
                "token1": ["handler1_1", "handler1_2"],
                "token2": ["handler2_1", "handler2_2"],
            }
        )
        self.assertEqual(
            mocked_load_bot_handlers.mock_calls,
            [
                call("module1"),
                call("module2"),
            ]
        )


@patch("django_chatbot.services.dispatcher.load_handlers")
class DispatcherTestCase(TestCase):
    def setUp(self) -> None:
        Bot.objects.create(name="bot1", token="token1")
        self.bot = Bot.objects.create(name="bot2", token="token2")
        Bot.objects.create(name="bot3", token="token3")
        self.update_data = {'key': 'value'}

        self.token_slug = "token2"

    @patch("django_chatbot.services.dispatcher.save_update")
    def test_init__set_attributes(
            self,
            mocked_save_update: Mock,
            mocked_load_handlers: Mock,
    ):
        update = Mock()
        mocked_save_update.return_value = update

        dispatcher = Dispatcher(self.update_data, self.token_slug)

        self.assertEqual(dispatcher.bot, self.bot)
        self.assertEqual(dispatcher.update, update)
        mocked_save_update.assert_called_with(
            bot=self.bot, update_data=self.update_data
        )

    @patch("django_chatbot.services.dispatcher.save_update")
    def test_dispatch(
            self,
            mocked_save_update: Mock,
            mocked_load_handlers: Mock,
    ):
        update = Mock()
        mocked_save_update.return_value = update
        handler_1 = Mock(**{'check_update.return_value': False})
        handler_2 = Mock(**{'check_update.return_value': True})
        handler_3 = Mock(**{'check_update.return_value': True})
        mocked_load_handlers.return_value = {
            'token1': [handler_3],
            'token2': [handler_1, handler_2, handler_3],
        }
        dispatcher = Dispatcher(update_data={}, token_slug='token2')

        dispatcher.dispatch()

        handler_1.check_update.assert_called_with(update=update)
        handler_2.check_update.assert_called_with(update=update)
        handler_3.check_update.assert_not_called()
        handler_1.handle_update.assert_not_called()
        handler_2.handle_update.assert_called_with(update=update)
        handler_3.handle_update.assert_not_called()
