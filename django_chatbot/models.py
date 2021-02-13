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

"""This module contains models representing some Telegram types"""

import logging
from typing import List, Optional

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.text import slugify

from django_chatbot.telegram.api import Api, TelegramError
from django_chatbot.telegram import types

log = logging.getLogger(__name__)


class Bot(models.Model):
    """Represent a bot

    Don't create or update a bot directly. It is better to add a bot to
    the ``settings``. To create a bot, firstly add the bot to the
    ``settings.DJANGO_CHATBOT["BOTS"]`` as a dictionary in format::

        {
            "NAME"': "@YourBot",
            "TOKEN": "1234:you_bot_token",
            "ROOT_HANDLERCONF": "your_app.handlers"
        }

    Where

    ``NAME`` - unique name (the good idea is to use the real bot name)

    ``TOKEN`` - bot token

    ``ROOT_HANDLERCONF`` - module that contains the ``handlers`` variable. The
        variable should be a list of ``Handler`` instances.

    Than run ``update_from_settings`` management command. The command creates
    or updates a ``Bot`` instance.

    """
    name = models.CharField(max_length=40, unique=True)
    token = models.CharField(max_length=50, unique=True)
    token_slug = models.SlugField(max_length=50, unique=True)
    root_handlerconf = models.CharField(max_length=100, default="")
    _me = models.JSONField(blank=True, null=True)
    _webhook_info = models.JSONField(blank=True, null=True)
    update_successful = models.BooleanField(default=True)
    me_update_datetime = models.DateTimeField(blank=True, null=True)
    webhook_update_datetime = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.token_slug = slugify(self.token)
        super().save(force_insert, force_update, using, update_fields)

    @property
    def me(self) -> Optional[types.User]:
        if self._me:
            return types.User.from_dict(self._me)

    @property
    def webhook_info(self) -> Optional[types.WebhookInfo]:
        if self._webhook_info:
            return types.WebhookInfo.from_dict(self._webhook_info)

    @cached_property
    def api(self):
        api = Api(token=self.token)
        return api

    def get_me(self) -> types.User:
        """Update the bot :attr:`me` from Telegram.

        Returns:
            information about the bot.

        Raises:
            TelegramError

        """
        try:
            me = self.api.get_me()
        except TelegramError as error:
            self.update_successful = False
            self.save()
            raise error
        else:
            self._me = me.to_dict()
            self.update_successful = True
            self.me_update_datetime = timezone.now()
            self.save()
            return self.me

    def get_webhook_info(self) -> types.WebhookInfo:
        """Update the bot :attr:`webhook_info` from Telegram.

        Returns:
            the bot WebhookInfo.

        Raises:
            TelegramError

        """
        try:
            webhook_info = self.api.get_webhook_info()
        except TelegramError as error:
            self.update_successful = False
            self.save()
            raise error
        else:
            self._webhook_info = webhook_info.to_dict()
            self.update_successful = True
            self.webhook_update_datetime = timezone.now()
            self.save()
            return self.webhook_info

    def set_webhook(self,
                    domain: str = None,
                    max_connections: int = None,
                    allowed_updates: List[str] = None) -> bool:
        """Set webhook on Telegram.

        This method calls telegram ``setWebhook`` method.
        https://core.telegram.org/bots/api#setwebhook

        Args:
            domain: The ``django_chatbot`` domain.
            max_connections: Maximum allowed number of simultaneous HTTPS
                connections to the webhook for update delivery.
            allowed_updates: A JSON-serialized list of the update types
                you want your bot to receive

        Returns:
            True if webhook was set successfully.

        Raises:
            TelegramError

        """
        if domain is None:
            domain = settings.DJANGO_CHATBOT['WEBHOOK_DOMAIN']
        url = domain + reverse(
            "django_chatbot:webhook",
            kwargs={'token_slug': self.token_slug}
        )
        if max_connections is None:
            max_connections = 40
        if allowed_updates is None:
            allowed_updates = ["messages", ]
        try:
            result = self.api.set_webhook(
                url=url,
                max_connections=max_connections,
                allowed_updates=allowed_updates
            )
            self.update_successful = True
            self.webhook_update_datetime = timezone.now()
            self.save()
        except TelegramError as error:
            self.update_successful = False
            self.save()
            raise error
        else:
            return result


class UserManager(models.Manager):
    def from_telegram(self, telegram_user: types.User):
        defaults = telegram_user.to_dict()
        defaults.pop('id')
        user, _ = self.update_or_create(
            user_id=telegram_user.id, defaults=defaults)
        return user


class User(models.Model):
    """Persistent class for telegram ``User``"""
    user_id = models.BigIntegerField(unique=True, db_index=True)
    is_bot = models.BooleanField(default=False)
    first_name = models.CharField(max_length=40, blank=True)
    last_name = models.CharField(max_length=40, blank=True)
    username = models.CharField(max_length=40, blank=True)
    language_code = models.CharField(max_length=2, blank=True)
    can_join_groups = models.BooleanField(default=False)
    can_read_all_group_messages = models.BooleanField(default=False)
    supports_inline_queries = models.BooleanField(default=False)

    objects = UserManager()

    def __str__(self):
        if self.username:
            return f"{self.user_id} - {self.username}"
        else:
            return self.user_id


class ChatManager(models.Manager):
    def from_telegram(self,
                      bot: Bot,
                      telegram_chat: types.Chat):
        """Create a model instance from a telegram type instance.

        Args:
            bot: The bot the chat belongs to.
            telegram_chat:

        Returns:
            model instance.
        """
        defaults = telegram_chat.to_dict()
        defaults['bot'] = bot
        _update_defaults(telegram_chat, defaults, 'photo')
        _update_defaults(telegram_chat, defaults, 'permissions')
        _update_defaults(telegram_chat, defaults, 'location')
        defaults.pop('id')
        chat, _ = self.update_or_create(
            chat_id=telegram_chat.id,
            defaults=defaults
        )
        return chat


class Chat(models.Model):
    """Persistent class for telegram ``Chat``"""
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    chat_id = models.BigIntegerField(unique=True, db_index=True)
    type = models.CharField(max_length=255)
    title = models.CharField(max_length=255, blank=True)
    username = models.CharField(max_length=255, blank=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    _photo = models.JSONField(blank=True, null=True)
    bio = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    invite_link = models.CharField(max_length=255, blank=True)
    pinned_message = models.ForeignKey(
        'Message', null=True, blank=True, on_delete=models.SET_NULL,
        related_name="pinned_to_chats"
    )
    _permissions = models.JSONField(blank=True, null=True)
    slow_mode_delay = models.IntegerField(null=True, blank=True)
    sticker_set_name = models.CharField(max_length=255, blank=True)
    can_set_sticker_set = models.BooleanField(default=False)
    linked_chat_id = models.BigIntegerField(null=True, blank=True)
    _location = models.JSONField(blank=True, null=True)

    objects = ChatManager()

    def __str__(self):
        if self.username:
            return f"{self.chat_id} - {self.username}"
        else:
            return self.chat_id

    @cached_property
    def photo(self) -> Optional[types.ChatPhoto]:
        if self._photo:
            return types.ChatPhoto.from_dict(self._photo)  # noqa

    @cached_property
    def permissions(self) -> Optional[types.ChatPermissions]:
        if self._permissions:
            return types.ChatPermissions.from_dict(self._permissions)  # noqa

    @cached_property
    def location(self) -> Optional[types.ChatLocation]:
        if self._location:
            return types.ChatLocation.from_dict(self._location)  # noqa

    def reply(self,
              text: str,
              parse_mode: str = None,
              **kwargs):
        api = self.bot.api
        telegram_message = api.send_message(
            chat_id=self.chat_id,
            text=text,
            parse_mode=parse_mode,
            **kwargs
        )
        user = telegram_message.from_user
        if user is not None:
            user = User.objects.from_telegram(telegram_user=user)

        message = Message.objects.from_telegram(
            bot=self.bot,
            telegram_message=telegram_message,
            direction=Message.DIRECTION_OUT,
        )
        return message


class MessageManager(models.Manager):
    def from_telegram(self,
                      bot: Bot,
                      telegram_message: types.Message,
                      direction: str):
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
        defaults['direction'] = direction
        _update_defaults(telegram_message, defaults, 'entities')
        _update_defaults(telegram_message, defaults, 'animation')
        _update_defaults(telegram_message, defaults, 'audio')
        _update_defaults(telegram_message, defaults, 'document')
        _update_defaults(telegram_message, defaults, 'photo')
        _update_defaults(telegram_message, defaults, 'sticker')
        _update_defaults(telegram_message, defaults, 'video')
        _update_defaults(telegram_message, defaults, 'video_note')
        _update_defaults(telegram_message, defaults, 'voice')
        _update_defaults(telegram_message, defaults, 'caption_entities')
        _update_defaults(telegram_message, defaults, 'contact')
        _update_defaults(telegram_message, defaults, 'dice')
        _update_defaults(telegram_message, defaults, 'game')
        _update_defaults(telegram_message, defaults, 'poll')
        _update_defaults(telegram_message, defaults, 'venue')
        _update_defaults(telegram_message, defaults, 'location')
        _update_defaults(telegram_message, defaults, 'new_chat_photo')
        _update_defaults(telegram_message, defaults, 'invoice')
        _update_defaults(telegram_message, defaults, 'successful_payment')
        _update_defaults(telegram_message, defaults, 'passport_data')
        _update_defaults(
            telegram_message, defaults, 'proximity_alert_triggered'
        )
        _update_defaults(telegram_message, defaults, 'reply_markup')

        chat = Chat.objects.from_telegram(
            bot=bot, telegram_chat=telegram_message.chat
        )
        defaults['chat'] = chat
        if telegram_message.from_user:
            user = User.objects.from_telegram(telegram_message.from_user)
            defaults['from_user'] = user
        if telegram_message.reply_to_message:
            defaults['reply_to_message'] = self.get_message(
                telegram_message.reply_to_message
            )
        if telegram_message.left_chat_member:
            user = User.objects.from_telegram(
                telegram_message.left_chat_member
            )
            defaults['left_chat_member'] = user
        if telegram_message.new_chat_members:
            defaults.pop('new_chat_members')
        defaults.pop('message_id')
        message, created = self.update_or_create(
            message_id=telegram_message.message_id,
            defaults=defaults
        )
        if created and telegram_message.new_chat_members:
            members = [
                User.objects.from_telegram(telegram_user) for telegram_user
                in telegram_message.new_chat_members
            ]
            for member in members:
                message.new_chat_members.add(member)
        return message

    def get_message(self, telegram_message: types.Message):
        try:
            message = self.get(
                message_id=telegram_message.message_id,
                chat__chat_id=telegram_message.chat.id,
            )
        except Message.DoesNotExist:
            message = None
        return message


class Message(models.Model):
    """Persistent class for telegram ``Message``"""
    DIRECTION_IN = "in"
    DIRECTION_OUT = "out"
    DIRECTION_CHOICES = (
        (DIRECTION_IN, DIRECTION_IN),
        (DIRECTION_OUT, DIRECTION_OUT),
    )

    direction = models.CharField(
        max_length=3, choices=DIRECTION_CHOICES, default=DIRECTION_IN
    )
    message_id = models.BigIntegerField()
    date = models.DateTimeField()
    chat = models.ForeignKey(
        Chat, on_delete=models.CASCADE, related_name="messages"
    )
    from_user = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='messages'
    )
    sender_chat = models.ForeignKey(
        Chat, null=True, blank=True, on_delete=models.SET_NULL
    )
    forward_from = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="forwarded_messages"
    )
    forward_from_chat = models.ForeignKey(
        Chat, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="forwarded_messages"
    )
    forward_from_message_id = models.BigIntegerField(null=True, blank=True)
    forward_signature = models.CharField(max_length=255, blank=True)
    forward_sender_name = models.CharField(max_length=255, blank=True)
    forward_date = models.DateTimeField(null=True, blank=True)
    reply_to_message = models.OneToOneField(
        'self', null=True, blank=True, on_delete=models.SET_NULL,
        related_name="reply_message"
    )
    via_bot = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="bot_messages"
    )
    edit_date = models.DateTimeField(null=True, blank=True)
    media_group_id = models.CharField(max_length=255, blank=True)
    author_signature = models.CharField(max_length=255, blank=True)
    text = models.TextField(blank=True)
    _entities = models.JSONField(blank=True, null=True)
    _animation = models.JSONField(blank=True, null=True)
    _audio = models.JSONField(blank=True, null=True)
    _document = models.JSONField(blank=True, null=True)
    _photo = models.JSONField(blank=True, null=True)
    _sticker = models.JSONField(blank=True, null=True)
    _video = models.JSONField(blank=True, null=True)
    _video_note = models.JSONField(blank=True, null=True)
    _voice = models.JSONField(blank=True, null=True)
    caption = models.CharField(max_length=1024, blank=True)
    _caption_entities = models.JSONField(blank=True, null=True)
    _contact = models.JSONField(blank=True, null=True)
    _dice = models.JSONField(blank=True, null=True)
    _game = models.JSONField(blank=True, null=True)
    _poll = models.JSONField(blank=True, null=True)
    _venue = models.JSONField(blank=True, null=True)
    _location = models.JSONField(blank=True, null=True)
    new_chat_members = models.ManyToManyField(
        User,
        related_name="messages_new_chat",
    )
    left_chat_member = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="messages_left_chat",
    )
    new_chat_title = models.CharField(max_length=255, blank=True)
    _new_chat_photo = models.CharField(max_length=255, blank=True)
    delete_chat_photo = models.BooleanField(default=True)
    group_chat_created = models.BooleanField(default=True)
    supergroup_chat_created = models.BooleanField(default=True)
    channel_chat_created = models.BooleanField(default=True)
    migrate_to_chat_id = models.BigIntegerField(null=True, blank=True)
    migrate_from_chat_id = models.BigIntegerField(null=True, blank=True)
    pinned_message = models.OneToOneField(
        'self', null=True, blank=True, on_delete=models.SET_NULL,
        related_name="pinned_to"
    )
    _invoice = models.JSONField(blank=True, null=True)
    _successful_payment = models.JSONField(blank=True, null=True)
    connected_website = models.CharField(max_length=255, blank=True)
    _passport_data = models.JSONField(blank=True, null=True)
    _proximity_alert_triggered = models.JSONField(blank=True, null=True)
    _reply_markup = models.JSONField(blank=True, null=True)
    extra = models.JSONField(default=dict)

    objects = MessageManager()

    class Meta:
        ordering = ["date"]
        unique_together = ["message_id", "chat"]
        index_together = ["message_id", "chat"]

    def __str__(self):
        return self.text[0:20]

    @cached_property
    def entities(self):
        if not self._entities:
            return None
        entities = [types.MessageEntity.from_dict(e) for e in
                    self._entities]  # noqa
        for entity in entities:
            entity.text = self.text[
                          entity.offset: entity.offset + entity.length
                          ]
        return entities

    @cached_property
    def animation(self) -> types.Animation:
        return types.Animation.from_dict(self._animation)

    @cached_property
    def audio(self) -> types.Audio:
        return types.Audio.from_dict(self._audio)

    @cached_property
    def document(self) -> types.Document:
        return types.Document.from_dict(self._document)

    @cached_property
    def photo(self) -> List[types.PhotoSize]:
        return [types.PhotoSize.from_dict(p) for p in self._photo]

    @cached_property
    def sticker(self) -> types.Sticker:
        return types.Sticker.from_dict(self._sticker)

    @cached_property
    def video(self) -> types.Video:
        return types.Video.from_dict(self._video)

    @cached_property
    def video_note(self) -> types.VideoNote:
        return types.VideoNote.from_dict(self._video_note)

    @cached_property
    def voice(self) -> types.Voice:
        return types.Voice.from_dict(self._voice)

    @cached_property
    def caption_entities(self):
        if not self._caption_entities:
            return None
        entities = [types.MessageEntity.from_dict(e) for e in
                    self._caption_entities]  # noqa
        for entity in entities:
            entity.text = self.text[
                          entity.offset: entity.offset + entity.length
                          ]
        return entities

    @cached_property
    def contact(self) -> types.Contact:
        return types.Contact.from_dict(self._contact)

    @cached_property
    def dice(self) -> types.Dice:
        return types.Dice.from_dict(self._dice)

    @cached_property
    def game(self) -> types.Game:
        return types.Game.from_dict(self._game)

    @cached_property
    def poll(self) -> types.Poll:
        return types.Poll.from_dict(self._poll)

    @cached_property
    def venue(self) -> types.Venue:
        return types.Venue.from_dict(self._venue)

    @cached_property
    def location(self) -> types.Location:
        return types.Location.from_dict(self._location)

    @cached_property
    def new_chat_photo(self) -> List[types.PhotoSize]:
        return [types.PhotoSize.from_dict(p) for p in self._new_chat_photo]

    @cached_property
    def invoice(self) -> types.Invoice:
        return types.Invoice.from_dict(self._invoice)

    @cached_property
    def successful_payment(self) -> types.SuccessfulPayment:
        return types.SuccessfulPayment.from_dict(self._successful_payment)

    @cached_property
    def passport_data(self) -> types.PassportData:
        return types.PassportData.from_dict(self._passport_data)

    @cached_property
    def proximity_alert_triggered(self) -> types.ProximityAlertTriggered:
        return types.ProximityAlertTriggered.from_dict(
            self._proximity_alert_triggered
        )

    @cached_property
    def reply_markup(self) -> types.InlineKeyboardMarkup:
        return types.InlineKeyboardMarkup.from_dict(self._reply_markup)

    def reply(self,
              text: str,
              parse_mode: str = None,
              reply: bool = False,
              **kwargs):
        chat = self.chat
        if reply:
            kwargs.update(
                {"reply_to_message_id": self.message_id}
            )
        message = chat.reply(
            text=text,
            parse_mode=parse_mode,
            **kwargs,
        )
        return message


class CallbackQueryManager(models.Manager):
    def from_telegram(self,
                      bot: Bot,
                      telegram_callback_query: types.CallbackQuery):
        """Create a model instance from a telegram type instance.

        Args:
            bot: The bot the callback query belongs to.
            telegram_callback_query: The telegram CallbackQuery.

        Returns:
            model instance.

        """
        defaults = telegram_callback_query.to_dict()
        defaults.pop('id')
        user = User.objects.from_telegram(telegram_callback_query.from_user)
        defaults['from_user'] = user
        if telegram_callback_query.message:
            message = Message.objects.from_telegram(
                bot=bot,
                telegram_message=telegram_callback_query.message,
                direction=Message.DIRECTION_IN,
            )
            defaults['message'] = message
        update, _ = self.update_or_create(
            callback_query_id=telegram_callback_query.id,
            defaults=defaults
        )
        return update


class CallbackQuery(models.Model):
    """Persistent class for telegram ``CallbackQuery``"""
    callback_query_id = models.CharField(max_length=100)
    from_user = models.ForeignKey(User, on_delete=models.CASCADE)
    chat_instance = models.CharField(max_length=100)
    message = models.ForeignKey(
        Message, on_delete=models.SET_NULL, null=True, blank=True
    )
    inline_message_id = models.CharField(max_length=100, blank=True)
    data = models.CharField(max_length=100, blank=True)
    game_short_name = models.CharField(max_length=100, blank=True)

    objects = CallbackQueryManager()

    @property
    def chat(self):
        return self.message.chat

    @property
    def text(self):
        return self.data


class UpdateManager(models.Manager):
    @staticmethod
    def _message_type(telegram_update: types.Update) -> str:
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

    def from_telegram(self,
                      bot: Bot,
                      telegram_update: types.Update):
        """Create a model instance from a telegram type instance.

        Args:
            bot: The bot the chat belongs to.
            telegram_update: Telegram Update.

        Returns:
            model instance.

        """
        defaults = telegram_update.to_dict()
        defaults.pop('update_id')
        defaults['bot'] = bot
        if telegram_message := telegram_update.effective_message:
            defaults['message'] = Message.objects.from_telegram(
                bot, telegram_message, direction=Message.DIRECTION_IN
            )
        if telegram_callback_query := telegram_update.callback_query:
            defaults['callback_query'] = CallbackQuery.objects.from_telegram(
                bot, telegram_callback_query
            )
        defaults['type'] = self._message_type(telegram_update)
        update, _ = self.update_or_create(
            update_id=telegram_update.update_id,
            defaults=defaults
        )
        return update


class Update(models.Model):
    """Persistent class for telegram ``Update``"""
    TYPE_MESSAGE = "message"
    TYPE_EDITED_MESSAGE = "edited_message"
    TYPE_CHANNEL_POST = "channel_post"
    TYPE_EDITED_CHANNEL_POST = "edited_channel_post"
    TYPE_CALLBACK_QUERY = "callback_query"
    TYPE_CHOICES = (
        (TYPE_MESSAGE, "Message"),
        (TYPE_EDITED_MESSAGE, "Edited message"),
        (TYPE_CHANNEL_POST, "Channel post"),
        (TYPE_EDITED_CHANNEL_POST, "Edited channel post"),
    )

    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    handler = models.CharField(max_length=100, blank=True)
    update_id = models.BigIntegerField(unique=True, db_index=True)
    type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default=TYPE_MESSAGE
    )
    message = models.OneToOneField(
        Message, null=True, blank=True, on_delete=models.CASCADE,
        related_name="update"
    )
    callback_query = models.OneToOneField(
        CallbackQuery, null=True, blank=True, on_delete=models.CASCADE,
    )

    objects = UpdateManager()

    def __str__(self):
        return f"{self.update_id}"

    @property
    def telegram_object(self):
        if self.type in [
            self.TYPE_MESSAGE, self.TYPE_EDITED_MESSAGE,
            self.TYPE_CHANNEL_POST, self.TYPE_EDITED_CHANNEL_POST
        ]:
            return self.message
        elif self.type == self.TYPE_CALLBACK_QUERY:
            return self.callback_query


def _update_defaults(telegram_object: object, defaults: dict, attr: str):
    """Add underscore a JSON field name."""

    if getattr(telegram_object, attr):
        defaults[f"_{attr}"] = defaults[attr]
        defaults.pop(attr)
