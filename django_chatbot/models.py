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
from typing import Generator, List, Optional

from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.text import slugify

from django_chatbot import managers
from django_chatbot.conf import settings
from django_chatbot.querysets import BotQuerySet
from django_chatbot.telegram import types
from django_chatbot.telegram.api import Api, TelegramError

logger = logging.getLogger(__name__)


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
    webhook_enabled = models.BooleanField(default=False)
    _webhook_info = models.JSONField(blank=True, null=True)
    update_successful = models.BooleanField(default=True)
    test_mode = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = managers.BotManager.from_queryset(BotQuerySet)()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return self.name

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
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
        if not self.test_mode:
            api = Api(token=self.token)
        else:
            from django_chatbot.test.test_api import TestApi

            api = TestApi(token=self.token)
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
            self._webhook_info = webhook_info.to_dict(date_as_timestamp=True)
            if self.webhook_info.url:
                self.webhook_enabled = True
            else:
                self.webhook_enabled = False
            self.update_successful = True
            self.save()
            return self.webhook_info

    def set_webhook(
        self,
        domain: str = None,
        max_connections: int = None,
        allowed_updates: List[str] = None,
    ) -> bool:
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
            domain = settings.DJANGO_CHATBOT["WEBHOOK_DOMAIN"]
        url = domain + reverse(
            "django_chatbot:webhook", kwargs={"token_slug": self.token_slug}
        )
        if max_connections is None:
            max_connections = 40
        if allowed_updates is None:
            allowed_updates = [
                "messages",
            ]
        try:
            result = self.api.set_webhook(
                url=url,
                max_connections=max_connections,
                allowed_updates=allowed_updates,
            )
        except TelegramError as error:
            self.update_successful = False
            self.save()
            logger.error("Error setting webhook", extra={"bot": self, "error": error})
            raise error
        else:
            self.update_successful = True
            self.webhook_enabled = True
            self.save()
            logger.info("Webhook set successfully.", extra={"bot": self})
            return result

    def delete_webhook(
        self,
        drop_pending_updates: bool = False,
    ) -> bool:
        """Delete webhook on Telegram.

        This method calls telegram ``deleteWebhook`` method.
        https://core.telegram.org/bots/api#deletewebhook

        Args:
            drop_pending_updates: Pass True to drop all pending updates

        Returns:
            True if webhook was deleted successfully.

        Raises:
            TelegramError

        """
        try:
            result = self.api.delete_webhook(drop_pending_updates=drop_pending_updates)
        except TelegramError as error:
            self.update_successful = False
            self.save()
            logger.error("Error deleting webhook", extra={"bot": self, "error": error})
            raise error
        else:
            self.update_successful = True
            self.webhook_enabled = False
            self._webhook_info = None
            self.save()
            logger.info("Webhook deleted successfully.", extra={"bot": self})
            return result

    def get_updates(
        self,
        offset: int = None,
    ) -> Optional[Generator[types.Update, None, None]]:
        """Receive incoming updates.

        This method calls telegram ``getUpdates`` method.
        https://core.telegram.org/bots/api#getupdates

        Args:
            offset: Identifier of the first update to be returned. If None returns
                updates starting from the last known update.

        Returns:
            Generator of updates or None if webhook is enabled.

        Raises:
            TelegramError

        """
        if self.webhook_enabled:
            return None
        try:
            limit = settings.DJANGO_CHATBOT["GET_UPDATES_LIMIT"]
            if offset is None:
                latest_update = Update.objects.last_update(bot=self)
                offset = latest_update.update_id + 1 if latest_update else 0
            updates = self.api.get_updates(offset=offset, limit=limit)
        except TelegramError as error:
            logger.error(
                "Error during getting updates",
                extra={"bot": self, "offset": offset, "error": error},
            )
            raise error
        else:
            logger.debug(
                "Updates was received successfully.",
                extra={"bot": self, "offset": offset, "updates": updates},
            )
            for update in updates:
                yield update
            if updates and len(updates) == limit:
                latest_update = updates[-1]
                yield from self.get_updates(offset=latest_update.update_id + 1)

    def test_mode_on(self):
        self.test_mode = True
        self.save()


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

    objects = managers.UserManager()

    def __str__(self):
        if self.username:
            return f"{self.user_id} - {self.username}"
        else:
            return self.user_id

    def chat(self, bot: Bot):
        chat_ = Chat.objects.filter(chat_id=self.user_id, bot=bot).first()
        return chat_


class Chat(models.Model):
    """Persistent class for telegram ``Chat``"""

    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    chat_id = models.BigIntegerField()
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
        "Message",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="pinned_to_chats",
    )
    _permissions = models.JSONField(blank=True, null=True)
    slow_mode_delay = models.IntegerField(null=True, blank=True)
    sticker_set_name = models.CharField(max_length=255, blank=True)
    can_set_sticker_set = models.BooleanField(default=False)
    linked_chat_id = models.BigIntegerField(null=True, blank=True)
    _location = models.JSONField(blank=True, null=True)

    objects = managers.ChatManager()

    class Meta:
        unique_together = (("bot", "chat_id"),)
        indexes = [
            models.Index(fields=["bot", "chat_id"]),
        ]

    def __str__(self):
        if self.username:
            return f"{self.bot} - {self.chat_id} - {self.username}"
        else:
            return f"{self.bot} - {self.chat_id}"

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

    def reply(self, text: str, parse_mode: str = None, **kwargs):
        api = self.bot.api
        telegram_message = api.send_message(
            chat_id=self.chat_id, text=text, parse_mode=parse_mode, **kwargs
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


class Form(models.Model):
    module_name = models.CharField(max_length=255)
    class_name = models.CharField(max_length=255)
    current_field = models.CharField(max_length=255)
    context = models.JSONField(default=dict)
    is_finished = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    handler = models.CharField(max_length=255)

    objects = managers.FormManager()

    def __str__(self):
        return f"{self.module_name}.{self.class_name}"


class Field(models.Model):
    form = models.ForeignKey("django_chatbot.Form", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    value = models.TextField(blank=True, null=True)
    is_valid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"


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
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
    from_user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="messages",
    )
    sender_chat = models.ForeignKey(
        Chat, null=True, blank=True, on_delete=models.SET_NULL
    )
    forward_from = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="forwarded_messages",
    )
    forward_from_chat = models.ForeignKey(
        Chat,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="forwarded_messages",
    )
    forward_from_message_id = models.BigIntegerField(null=True, blank=True)
    forward_signature = models.CharField(max_length=255, blank=True)
    forward_sender_name = models.CharField(max_length=255, blank=True)
    forward_date = models.DateTimeField(null=True, blank=True)
    reply_to_message = models.OneToOneField(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reply_message",
    )
    via_bot = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="bot_messages",
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
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="pinned_to",
    )
    _invoice = models.JSONField(blank=True, null=True)
    _successful_payment = models.JSONField(blank=True, null=True)
    connected_website = models.CharField(max_length=255, blank=True)
    _passport_data = models.JSONField(blank=True, null=True)
    _proximity_alert_triggered = models.JSONField(blank=True, null=True)
    _reply_markup = models.JSONField(blank=True, null=True)
    extra = models.JSONField(default=dict)
    form = models.ForeignKey(Form, blank=True, null=True, on_delete=models.SET_NULL)

    objects = managers.MessageManager()

    class Meta:
        ordering = ["message_id", "chat"]
        unique_together = ["message_id", "chat"]
        index_together = ["message_id", "chat"]

    def __str__(self):
        return self.text[0:20]

    @cached_property
    def bot(self):
        return self.chat.bot

    @cached_property
    def entities(self):
        if not self._entities:
            return None
        entities = [types.MessageEntity.from_dict(e) for e in self._entities]  # noqa
        for entity in entities:
            entity.text = self.text[entity.offset : entity.offset + entity.length]
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
        entities = [
            types.MessageEntity.from_dict(e) for e in self._caption_entities
        ]  # noqa
        for entity in entities:
            entity.text = self.text[entity.offset : entity.offset + entity.length]
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
        return types.ProximityAlertTriggered.from_dict(self._proximity_alert_triggered)

    @cached_property
    def reply_markup(self) -> types.InlineKeyboardMarkup:
        return types.InlineKeyboardMarkup.from_dict(self._reply_markup)

    def reply(self, text: str, parse_mode: str = None, reply: bool = False, **kwargs):
        chat = self.chat
        if reply:
            kwargs.update({"reply_to_message_id": self.message_id})
        message = chat.reply(
            text=text,
            parse_mode=parse_mode,
            **kwargs,
        )
        return message

    def edit(
        self,
        text: str,
        parse_mode: str = None,
        entities: List[types.MessageEntity] = None,
        disable_web_page_preview: bool = None,
        reply_markup: types.InlineKeyboardMarkup = None,
    ):

        api = self.bot.api
        telegram_message = api.edit_message_text(
            text=text,
            chat_id=self.chat.chat_id,
            message_id=self.message_id,
            parse_mode=parse_mode,
            entities=entities,
            disable_web_page_preview=disable_web_page_preview,
            reply_markup=reply_markup,
        )

        message = Message.objects.from_telegram(
            bot=self.bot,
            telegram_message=telegram_message,
            direction=Message.DIRECTION_OUT,
        )
        return message

    def set_form(self, form: Form):
        self.form = form
        self.save()

    def edit_reply_markup(self, reply_markup: types.InlineKeyboardMarkup):
        api = self.bot.api
        telegram_message = api.edit_message_reply_markup(
            chat_id=self.chat.chat_id,
            message_id=self.message_id,
            reply_markup=reply_markup,
        )

        message = Message.objects.from_telegram(
            bot=self.bot,
            telegram_message=telegram_message,
            direction=Message.DIRECTION_OUT,
        )
        return message


class CallbackQuery(models.Model):
    """Persistent class for telegram ``CallbackQuery``"""

    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    callback_query_id = models.CharField(max_length=100)
    from_user = models.ForeignKey(User, on_delete=models.CASCADE)
    chat_instance = models.CharField(max_length=100)
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, null=True, blank=True
    )
    inline_message_id = models.CharField(max_length=100, blank=True)
    data = models.CharField(max_length=100, blank=True)
    game_short_name = models.CharField(max_length=100, blank=True)

    objects = managers.CallbackQueryManager()

    class Meta:
        ordering = ["callback_query_id"]

    @property
    def chat(self):
        return self.message.chat

    @property
    def text(self):
        return self.data

    def edit(
        self,
        text: str,
        parse_mode: str = None,
        entities: List[types.MessageEntity] = None,
        disable_web_page_preview: bool = None,
        reply_markup: types.InlineKeyboardMarkup = None,
    ):
        """Edit according message."""
        self.message.edit(
            text=text,
            parse_mode=parse_mode,
            entities=entities,
            disable_web_page_preview=disable_web_page_preview,
            reply_markup=reply_markup,
        )

    @property
    def form(self):
        return self.message.form

    def set_form(self, form: Form):
        self.message.form = form
        self.message.save()


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
        (TYPE_CALLBACK_QUERY, "Callback query"),
    )

    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    handler = models.CharField(max_length=100, blank=True)
    update_id = models.BigIntegerField(unique=True, db_index=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_MESSAGE)
    message = models.OneToOneField(
        Message, null=True, blank=True, on_delete=models.CASCADE, related_name="updates"
    )
    callback_query = models.OneToOneField(
        CallbackQuery,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    objects = managers.UpdateManager()

    class Meta:
        ordering = ["update_id"]

    def __str__(self):
        return f"{self.update_id}"

    @property
    def telegram_object(self):
        if self.type in [
            self.TYPE_MESSAGE,
            self.TYPE_EDITED_MESSAGE,
            self.TYPE_CHANNEL_POST,
            self.TYPE_EDITED_CHANNEL_POST,
        ]:
            return self.message
        elif self.type == self.TYPE_CALLBACK_QUERY:
            return self.callback_query

    def set_handler(self, handler: str):
        """Set the handler for this update."""
        self.handler = handler
        self.save()


def _update_defaults(telegram_object: object, defaults: dict, attr: str):
    """Add underscore a JSON field name."""

    if getattr(telegram_object, attr):
        defaults[f"_{attr}"] = defaults[attr]
        defaults.pop(attr)


class PeriodicTask(models.Model):
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    enabled = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["bot", "name"],
                condition=Q(user__isnull=True),
                name="unique_periodic_task_name",
            ),
        ]
