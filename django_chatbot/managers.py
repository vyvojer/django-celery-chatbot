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
import logging
from typing import TYPE_CHECKING

from django.apps import apps
from django.db import models
from django.dispatch import Signal

logger = logging.getLogger(__name__)

telegram_instance = Signal()


if TYPE_CHECKING:
    from django_chatbot.models import Bot, CallbackQuery, Chat, Message, Update, User
    from django_chatbot.telegram import types


class BotManager(models.Manager):
    pass


class UserManager(models.Manager):
    def from_telegram(self, telegram_user: "types.User") -> "User":
        defaults = telegram_user.to_dict()
        defaults.pop("id")
        user, created = self.update_or_create(
            user_id=telegram_user.id, defaults=defaults
        )

        telegram_instance.send(sender=self.model, created=created, instance=user)

        return user


class ChatManager(models.Manager):
    def from_telegram(self, bot: "Bot", telegram_chat: "types.Chat") -> "Chat":
        """Create a model instance from a telegram type instance.

        Args:
            bot (Bot): The bot the chat belongs to.
            telegram_chat:

        Returns:
            model instance.
        """
        defaults = telegram_chat.to_dict()
        _update_defaults(telegram_chat, defaults, "photo")
        _update_defaults(telegram_chat, defaults, "permissions")
        _update_defaults(telegram_chat, defaults, "location")
        defaults.pop("id")
        chat, created = self.update_or_create(
            chat_id=telegram_chat.id, bot=bot, defaults=defaults
        )

        telegram_instance.send(sender=self.model, created=created, instance=chat)

        return chat


class FormManager(models.Manager):
    def get_form(self, update: "types.Update"):

        if message := update.message:
            try:
                previous = message.get_previous_by_date(chat_id=message.chat_id)
            except apps.get_model("django_chatbot", "Message").DoesNotExist:
                return None
            else:
                if previous.form and not previous.form.is_finished:
                    return previous.form
        elif callback_query := update.callback_query:
            if callback_query.form and not callback_query.form.is_finished:
                return callback_query.form
        return None


class MessageManager(models.Manager):
    def from_telegram(
        self, bot: "Bot", telegram_message: "types.Message", direction: str
    ) -> "Message":
        """Create a model instance from a telegram type instance.

        Args:
            bot: The bot the message belongs to.
            telegram_message: The telegram Message.
            direction: The message direction. Either Message.DIRECTION_IN or
                Either Message.DIRECTION_OUT for incoming/outgoing message.

        Returns:
            model instance.

        """
        defaults = telegram_message.to_dict()
        defaults["direction"] = direction
        _update_defaults(telegram_message, defaults, "entities")
        _update_defaults(telegram_message, defaults, "animation")
        _update_defaults(telegram_message, defaults, "audio")
        _update_defaults(telegram_message, defaults, "document")
        _update_defaults(telegram_message, defaults, "photo")
        _update_defaults(telegram_message, defaults, "sticker")
        _update_defaults(telegram_message, defaults, "video")
        _update_defaults(telegram_message, defaults, "video_note")
        _update_defaults(telegram_message, defaults, "voice")
        _update_defaults(telegram_message, defaults, "caption_entities")
        _update_defaults(telegram_message, defaults, "contact")
        _update_defaults(telegram_message, defaults, "dice")
        _update_defaults(telegram_message, defaults, "game")
        _update_defaults(telegram_message, defaults, "poll")
        _update_defaults(telegram_message, defaults, "venue")
        _update_defaults(telegram_message, defaults, "location")
        _update_defaults(telegram_message, defaults, "new_chat_photo")
        _update_defaults(telegram_message, defaults, "invoice")
        _update_defaults(telegram_message, defaults, "successful_payment")
        _update_defaults(telegram_message, defaults, "passport_data")
        _update_defaults(telegram_message, defaults, "proximity_alert_triggered")
        _update_defaults(telegram_message, defaults, "reply_markup")

        User = apps.get_model("django_chatbot", "User")
        Chat = apps.get_model("django_chatbot", "Chat")

        chat = Chat.objects.from_telegram(bot=bot, telegram_chat=telegram_message.chat)
        defaults["chat"] = chat
        if telegram_message.from_user:
            user = User.objects.from_telegram(telegram_message.from_user)
            defaults["from_user"] = user
        if telegram_message.reply_to_message:
            defaults["reply_to_message"] = self.get_message(
                telegram_message.reply_to_message
            )
        if telegram_message.left_chat_member:
            user = User.objects.from_telegram(telegram_message.left_chat_member)
            defaults["left_chat_member"] = user
        if telegram_message.new_chat_members:
            defaults.pop("new_chat_members")
        if telegram_message.sender_chat:
            sender_chat = Chat.objects.from_telegram(
                bot=bot, telegram_chat=telegram_message.sender_chat
            )
            defaults["sender_chat"] = sender_chat
        defaults.pop("message_id")
        message, created = self.update_or_create(
            message_id=telegram_message.message_id, defaults=defaults
        )

        telegram_instance.send(sender=self.model, created=created, instance=message)

        logger.debug(
            "Message record created/updated",
            extra={
                "message_id": telegram_message.message_id,
                "message_created": created,
                "defaults": defaults,
            },
        )
        if created and telegram_message.new_chat_members:
            members = [
                User.objects.from_telegram(telegram_user)
                for telegram_user in telegram_message.new_chat_members
            ]
            for member in members:
                message.new_chat_members.add(member)
        return message

    def get_message(self, telegram_message: "types.Message") -> "Message":
        Message = apps.get_model("django_chatbot", "Message")

        try:
            message = self.get(
                message_id=telegram_message.message_id,
                chat__chat_id=telegram_message.chat.id,
            )
        except Message.DoesNotExist:
            message = None
        return message


class CallbackQueryManager(models.Manager):
    def from_telegram(
        self, bot: "Bot", telegram_callback_query: "types.CallbackQuery"
    ) -> "CallbackQuery":
        """Create a model instance from a telegram type instance.

        Args:
            bot: The bot the callback query belongs to.
            telegram_callback_query: The telegram CallbackQuery.

        Returns:
            model instance.

        """
        User = apps.get_model("django_chatbot", "User")

        Message = apps.get_model("django_chatbot", "Message")
        defaults = telegram_callback_query.to_dict()
        defaults.pop("id")
        user = User.objects.from_telegram(telegram_callback_query.from_user)
        defaults["from_user"] = user
        defaults["bot"] = bot
        if telegram_callback_query.message:
            message = Message.objects.from_telegram(
                bot=bot,
                telegram_message=telegram_callback_query.message,
                direction=Message.DIRECTION_OUT,
            )
            defaults["message"] = message
        callback_query, created = self.update_or_create(
            callback_query_id=telegram_callback_query.id, defaults=defaults
        )

        telegram_instance.send(
            sender=self.model, created=created, instance=callback_query
        )

        return callback_query


class UpdateManager(models.Manager):
    @staticmethod
    def _message_type(telegram_update: "types.Update") -> str:
        Update = apps.get_model("django_chatbot", "Update")
        if telegram_update.message:
            return Update.TYPE_MESSAGE
        elif telegram_update.edited_message:
            return Update.TYPE_EDITED_MESSAGE
        elif telegram_update.channel_post:
            return Update.TYPE_CHANNEL_POST
        elif telegram_update.edited_channel_post:
            return Update.TYPE_EDITED_CHANNEL_POST
        elif telegram_update.callback_query:
            return Update.TYPE_CALLBACK_QUERY

    def from_telegram(self, bot: "Bot", telegram_update: "types.Update") -> "Update":
        """Create a model instance from a telegram type instance.

        Args:
            bot: The bot the chat belongs to.
            telegram_update: Telegram Update.

        Returns:
            model instance.

        """
        defaults = telegram_update.to_dict()
        defaults.pop("update_id")
        defaults["bot"] = bot
        telegram_message = None
        Message = apps.get_model("django_chatbot", "Message")
        CallbackQuery = apps.get_model("django_chatbot", "CallbackQuery")

        if telegram_update.message:
            telegram_message = telegram_update.message
        if telegram_update.edited_message:
            telegram_message = telegram_update.edited_message
            defaults.pop("edited_message")
        if telegram_update.channel_post:
            telegram_message = telegram_update.channel_post
            defaults.pop("channel_post")
        if telegram_update.edited_channel_post:
            telegram_message = telegram_update.edited_channel_post
            defaults.pop("edited_channel_post")
        if telegram_message is not None:
            defaults["message"] = Message.objects.from_telegram(
                bot, telegram_message, direction=Message.DIRECTION_IN
            )
        if telegram_callback_query := telegram_update.callback_query:
            defaults["callback_query"] = CallbackQuery.objects.from_telegram(
                bot, telegram_callback_query
            )
        defaults["type"] = self._message_type(telegram_update)
        update, created = self.update_or_create(
            update_id=telegram_update.update_id, defaults=defaults
        )

        telegram_instance.send(sender=self.model, created=created, instance=update)

        return update

    def last_update(self, bot: "Bot") -> "Update":
        return self.get_queryset().filter(bot=bot).last()


def _update_defaults(telegram_object: object, defaults: dict, attr: str):
    """Add underscore a JSON field name."""

    if getattr(telegram_object, attr):
        defaults[f"_{attr}"] = defaults[attr]
        defaults.pop(attr)
