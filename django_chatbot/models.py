import logging
from typing import List

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
    name = models.CharField(max_length=40, unique=True)
    token = models.CharField(max_length=50, unique=True)
    token_slug = models.SlugField(max_length=50, unique=True)
    root_handlerconf = models.CharField(max_length=100, default="")
    me = models.JSONField(blank=True, null=True)
    webhook_info = models.JSONField(blank=True, null=True)
    update_successful = models.BooleanField(default=True)
    me_update_datetime = models.DateTimeField(blank=True, null=True)
    webhook_update_datetime = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.token_slug = slugify(self.token)
        super().save(force_insert, force_update, using, update_fields)

    @cached_property
    def api(self):
        api = Api(token=self.token)
        return api

    def get_me(self):
        try:
            me = self.api.get_me()
        except TelegramError as error:
            self.update_successful = False
            self.save()
            return {
                "ok": False,
                "result": error.to_dict()
            }
        else:
            self.me = me.to_dict()
            self.update_successful = True
            self.me_update_datetime = timezone.now()
            self.save()
            return {
                "ok": True,
                "result": self.me
            }

    def get_webhook_info(self):
        try:
            webhook_info = self.api.get_webhook_info()
        except TelegramError as error:
            self.update_successful = False
            self.save()
            return {
                "ok": False,
                "result": error.to_dict()
            }
        else:
            self.webhook_info = webhook_info.to_dict()
            self.update_successful = True
            self.webhook_update_datetime = timezone.now()
            self.save()
            return {
                "ok": True,
                "result": self.webhook_info
            }

    def set_webhook(self,
                    domain: str = None,
                    max_connections: int = None,
                    allowed_updates: List[str] = None):
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
            return {
                "ok": False,
                "result": error.to_dict()
            }
        else:
            return {"ok": result}


class UserManager(models.Manager):
    def from_telegram(self, telegram_user: types.User):
        defaults = telegram_user.to_dict()
        defaults.pop('id')
        user, _ = self.update_or_create(
            user_id=telegram_user.id, defaults=defaults)
        return user


class User(models.Model):
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


class Update(models.Model):
    MESSAGE_TYPE_NONE = "none"
    MESSAGE_TYPE_MESSAGE = "message"
    MESSAGE_TYPE_EDITED_MESSAGE = "edited_message"
    MESSAGE_TYPE_CHANNEL_POST = "channel_post"
    MESSAGE_TYPE_EDITED_CHANNEL_POST = "edited_channel_post"
    MESSAGE_CHOICES = (
        (MESSAGE_TYPE_NONE, "-"),
        (MESSAGE_TYPE_MESSAGE, "Message"),
        (MESSAGE_TYPE_EDITED_MESSAGE, "Edited message"),
        (MESSAGE_TYPE_CHANNEL_POST, "Channel post"),
        (MESSAGE_TYPE_EDITED_CHANNEL_POST, "Edited channel post"),
    )

    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    update_id = models.BigIntegerField(unique=True, db_index=True)
    message_type = models.CharField(
        max_length=20, choices=MESSAGE_CHOICES, default=MESSAGE_TYPE_NONE
    )
    message = models.OneToOneField(
        'Message', null=True, blank=True, on_delete=models.SET_NULL,
        related_name="update"
    )
    original = models.JSONField(blank=True, null=True)


class Chat(models.Model):
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    chat_id = models.BigIntegerField(unique=True, db_index=True)
    type = models.CharField(max_length=255)
    title = models.CharField(max_length=255, blank=True)
    username = models.CharField(max_length=255, blank=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    photo = models.JSONField(blank=True, null=True)
    bio = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    invite_link = models.CharField(max_length=255, blank=True)
    pinned_message = models.ForeignKey(
        'Message', null=True, blank=True, on_delete=models.SET_NULL,
        related_name="pinned_to_chats"
    )
    permissions = models.JSONField(blank=True, null=True)
    slow_mode_delay = models.IntegerField(null=True, blank=True)
    sticker_set_name = models.CharField(max_length=255, blank=True)
    can_set_sticker_set = models.BooleanField(default=False)
    linked_chat_id = models.BigIntegerField(null=True, blank=True)
    location = models.JSONField(blank=True, null=True)

    def __str__(self):
        if self.username:
            return f"{self.chat_id} - {self.username}"
        else:
            return self.chat_id

    def reply(self,
              text: str,
              parse_mode: str = None,
              **kwargs):
        api = self.bot.api
        # TODO: add error handling
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
            telegram_message=telegram_message,
            direction=Message.DIRECTION_OUT,
            chat=self,
            user=user,
        )
        return message


class MessageManager(models.Manager):
    def from_telegram(self,
                      telegram_message: types.Message,
                      direction: str,
                      chat: Chat,
                      user: User = None):
        defaults = telegram_message.to_dict()
        defaults['direction'] = direction
        if telegram_message.entities:
            defaults['_entities'] = defaults['entities']
            defaults.pop('entities')
        defaults['chat'] = chat
        if user:
            defaults['from_user'] = user
        if telegram_message.reply_to_message:
            defaults['reply_to_message'] = self.get_message(
                telegram_message.reply_to_message
            )
        defaults.pop('message_id')
        message, _ = self.update_or_create(
            message_id=telegram_message.message_id,
            defaults=defaults
        )
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
    # TODO    animation: Animation = None
    # TODO    audio: Audio = None
    # TODO    document: Document = None
    # TODO     photo: List[PhotoSize] = None
    # TODO    sticker: Sticker = None
    # TODO    video: Video = None
    # TODO    video_note: VideoNote = None
    # TODO    voice: Voice = None
    caption = models.CharField(max_length=1024, blank=True)
    # TODO    caption_entities: List[MessageEntity] = None
    # TODO    contact: Contact = None
    # TODO    dice: Dice = None
    # TODO    game: Game = None
    # TODO    poll: Poll = None
    # TODO    venue: Venue = None
    location = models.JSONField(blank=True, null=True)
    # TODO    new_chat_members: List[User] = None
    left_chat_member = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL
    )
    new_chat_title = models.CharField(max_length=255, blank=True)
    # TODO    new_chat_photo: List[PhotoSize] = None
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
    # TODO    invoice: Invoice = None
    # TODO    successful_payment: SuccessfulPayment = None
    connected_website = models.CharField(max_length=255, blank=True)

    # TODO    passport_data: PassportData = None
    # TODO    proximity_alert_triggered: ProximityAlertTriggered = None
    # TODO    reply_markup: InlineKeyboardMarkup = None

    objects = MessageManager()

    class Meta:
        ordering = ["date"]
        unique_together = ["message_id", "chat"]
        index_together = ["message_id", "chat"]

    def __str__(self):
        return self.text[0:20]

    @cached_property
    def entities(self):
        entities = [types.MessageEntity.from_dict(e) for e in self._entities]
        for entity in entities:
            entity.text = self.text[
                          entity.offset: entity.offset + entity.length
                          ]
        return entities

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
