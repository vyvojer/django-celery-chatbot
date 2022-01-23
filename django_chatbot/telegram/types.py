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

"""Contains telegram types"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable, List, Union

import dacite
from django.utils import timezone
from django.utils.timezone import datetime


class TelegramType:
    """Base class for telegram types"""

    @classmethod
    def from_dict(cls, source: dict):
        """Create TelegramType from response dict

        Args:
            source: Telegram response dictionary

        Returns:
            TelegramType

        """
        source = TelegramType.convert_date(source, TelegramType.timestamp_to_datetime)
        source = TelegramType.convert_froms(source)
        o = dacite.from_dict(cls, source)
        return o

    @staticmethod
    def convert_date(source: dict, convertor: Callable[[Any], Any]):
        converted = {}
        for k, v in source.items():
            if isinstance(v, dict):
                v = TelegramType.convert_date(v, convertor)
            if k == "date" or k.endswith("_date"):
                converted[k] = convertor(v)
            else:
                converted[k] = v
        return converted

    @staticmethod
    def convert_froms(source: dict):
        converted = {}
        for k, v in source.items():
            if isinstance(v, dict):
                v = TelegramType.convert_froms(v)
            if k == "from":
                converted["from_user"] = v
            else:
                converted[k] = v
        return converted

    @staticmethod
    def timestamp_to_datetime(timestamp: int) -> timezone.datetime:
        """Convert timestamp to datetime"""
        dt = timezone.datetime.fromtimestamp(timestamp)
        dt = timezone.make_aware(dt, timezone=timezone.utc)
        return dt

    @staticmethod
    def datetime_to_timestamp(datetime: timezone.datetime) -> float:
        """Convert datetime to timestamp"""
        return datetime.timestamp()

    def to_dict(self, date_as_timestamp=False):
        dikt = asdict(
            self, dict_factory=lambda l: {k: v for k, v in l if v is not None}
        )
        if date_as_timestamp:
            dikt = TelegramType.convert_date(dikt, TelegramType.datetime_to_timestamp)
        return dikt


@dataclass(eq=True)
class Update(TelegramType):
    """
    This object represents an incoming update.At most one of the optional
    parameters can be present in any given update.

    https://core.telegram.org/bots/api/#update

    Attributes:
        update_id: The update's unique identifier. Update identifiers start
            from a certain positive number and increase sequentially. This ID
            becomes especially handy if you're using Webhooks, since it allows
            you to ignore repeated updates or to restore the correct update
            sequence, should they get out of order. If there are no new
            updates for at least a week, then identifier of the next update
            will be chosen randomly instead of sequentially.
        message: Optional. New incoming message of any kind — text, photo,
            sticker, etc.
        edited_message: Optional. New version of a message that is known to
            the bot and was edited
        channel_post: Optional. New incoming channel post of any kind —
            text, photo, sticker, etc.
        edited_channel_post: Optional. New version of a channel post that
            is known to the bot and was edited
        inline_query: Optional. New incoming inline query
        chosen_inline_result: Optional. The result of an inline query that
            was chosen by a user and sent to their chat partner. Please see
            our documentation on the feedback collecting for details on how to
            enable these updates for your bot.
        callback_query: Optional. New incoming callback query
        shipping_query: Optional. New incoming shipping query. Only for
            invoices with flexible price
        pre_checkout_query: Optional. New incoming pre-checkout query.
            Contains full information about checkout
        poll: Optional. New poll state. Bots receive only updates about
            stopped polls and polls, which are sent by the bot
        poll_answer: Optional. A user changed their answer in a
            non-anonymous poll. Bots receive new votes only in polls that were
            sent by the bot itself.
        my_chat_member: Optional. The bot's chat member status was updated
            in a chat. For private chats, this update is received only when
            the bot is blocked or unblocked by the user.
        chat_member: Optional. A chat member's status was updated in a
            chat. The bot must be an administrator in the chat and must
            explicitly specify “chat_member” in the list of allowed_updates to
            receive these updates.

    """

    update_id: int
    message: Message = None
    edited_message: Message = None
    channel_post: Message = None
    edited_channel_post: Message = None
    inline_query: InlineQuery = None
    chosen_inline_result: ChosenInlineResult = None
    callback_query: CallbackQuery = None
    shipping_query: ShippingQuery = None
    pre_checkout_query: PreCheckoutQuery = None
    poll: Poll = None
    poll_answer: PollAnswer = None
    my_chat_member: ChatMemberUpdated = None
    chat_member: ChatMemberUpdated = None


@dataclass(eq=True)
class WebhookInfo(TelegramType):
    """
    Contains information about the current status of a webhook.

    https://core.telegram.org/bots/api/#webhookinfo

    Attributes:
        url: Webhook URL, may be empty if webhook is not set up
        has_custom_certificate: True, if a custom certificate was provided
            for webhook certificate checks
        pending_update_count: Number of updates awaiting delivery
        ip_address: Optional. Currently used webhook IP address
        last_error_date: Optional. Unix time for the most recent error that
            happened when trying to deliver an update via webhook
        last_error_message: Optional. Error message in human-readable
            format for the most recent error that happened when trying to
            deliver an update via webhook
        max_connections: Optional. Maximum allowed number of simultaneous
            HTTPS connections to the webhook for update delivery
        allowed_updates: Optional. A list of update types the bot is
            subscribed to. Defaults to all update types except chat_member

    """

    url: str
    has_custom_certificate: bool
    pending_update_count: int
    ip_address: str = None
    last_error_date: datetime = None
    last_error_message: str = None
    max_connections: int = None
    allowed_updates: List[str] = None


@dataclass(eq=True)
class User(TelegramType):
    """
    This object represents a Telegram user or bot.

    https://core.telegram.org/bots/api/#user

    Attributes:
        id: Unique identifier for this user or bot. This number may have
            more than 32 significant bits and some programming languages may
            have difficulty/silent defects in interpreting it. But it has at
            most 52 significant bits, so a 64-bit integer or double-precision
            float type are safe for storing this identifier.
        is_bot: True, if this user is a bot
        first_name: User's or bot's first name
        last_name: Optional. User's or bot's last name
        username: Optional. User's or bot's username
        language_code: Optional. IETF language tag of the user's language
        can_join_groups: Optional. True, if the bot can be invited to
            groups. Returned only in getMe.
        can_read_all_group_messages: Optional. True, if privacy mode is
            disabled for the bot. Returned only in getMe.
        supports_inline_queries: Optional. True, if the bot supports inline
            queries. Returned only in getMe.

    """

    id: int
    is_bot: bool
    first_name: str = None
    last_name: str = None
    username: str = None
    language_code: str = None
    can_join_groups: bool = None
    can_read_all_group_messages: bool = None
    supports_inline_queries: bool = None


@dataclass(eq=True)
class Chat(TelegramType):
    """
    This object represents a chat.

    https://core.telegram.org/bots/api/#chat

    Attributes:
        id: Unique identifier for this chat. This number may have more than
            32 significant bits and some programming languages may have
            difficulty/silent defects in interpreting it. But it has at most
            52 significant bits, so a signed 64-bit integer or
            double-precision float type are safe for storing this identifier.
        type: Type of chat, can be either “private”, “group”, “supergroup”
            or “channel”
        title: Optional. Title, for supergroups, channels and group chats
        username: Optional. Username, for private chats, supergroups and
            channels if available
        first_name: Optional. First name of the other party in a private
            chat
        last_name: Optional. Last name of the other party in a private chat
        photo: Optional. Chat photo. Returned only in getChat.
        bio: Optional. Bio of the other party in a private chat. Returned
            only in getChat.
        description: Optional. Description, for groups, supergroups and
            channel chats. Returned only in getChat.
        invite_link: Optional. Primary invite link, for groups, supergroups
            and channel chats. Returned only in getChat.
        pinned_message: Optional. The most recent pinned message (by
            sending date). Returned only in getChat.
        permissions: Optional. Default chat member permissions, for groups
            and supergroups. Returned only in getChat.
        slow_mode_delay: Optional. For supergroups, the minimum allowed
            delay between consecutive messages sent by each unpriviledged
            user. Returned only in getChat.
        message_auto_delete_time: Optional. The time after which all
            messages sent to the chat will be automatically deleted; in
            seconds. Returned only in getChat.
        sticker_set_name: Optional. For supergroups, name of group sticker
            set. Returned only in getChat.
        can_set_sticker_set: Optional. True, if the bot can change the
            group sticker set. Returned only in getChat.
        linked_chat_id: Optional. Unique identifier for the linked chat,
            i.e. the discussion group identifier for a channel and vice versa;
            for supergroups and channel chats. This identifier may be greater
            than 32 bits and some programming languages may have
            difficulty/silent defects in interpreting it. But it is smaller
            than 52 bits, so a signed 64 bit integer or double-precision float
            type are safe for storing this identifier. Returned only in
            getChat.
        location: Optional. For supergroups, the location to which the
            supergroup is connected. Returned only in getChat.

    """

    id: int
    type: str
    title: str = None
    username: str = None
    first_name: str = None
    last_name: str = None
    photo: ChatPhoto = None
    bio: str = None
    description: str = None
    invite_link: str = None
    pinned_message: Message = None
    permissions: ChatPermissions = None
    slow_mode_delay: int = None
    message_auto_delete_time: int = None
    sticker_set_name: str = None
    can_set_sticker_set: bool = None
    linked_chat_id: int = None
    location: ChatLocation = None


@dataclass(eq=True)
class Message(TelegramType):
    """
    This object represents a message.

    https://core.telegram.org/bots/api/#message

    Attributes:
        message_id: Unique message identifier inside this chat
        date: Date the message was sent in Unix time
        chat: Conversation the message belongs to
        from_user: Optional. Sender, empty for messages sent to channels
        sender_chat: Optional. Sender of the message, sent on behalf of a
            chat. The channel itself for channel messages. The supergroup
            itself for messages from anonymous group administrators. The
            linked channel for messages automatically forwarded to the
            discussion group
        forward_from: Optional. For forwarded messages, sender of the
            original message
        forward_from_chat: Optional. For messages forwarded from channels
            or from anonymous administrators, information about the original
            sender chat
        forward_from_message_id: Optional. For messages forwarded from
            channels, identifier of the original message in the channel
        forward_signature: Optional. For messages forwarded from channels,
            signature of the post author if present
        forward_sender_name: Optional. Sender's name for messages forwarded
            from users who disallow adding a link to their account in
            forwarded messages
        forward_date: Optional. For forwarded messages, date the original
            message was sent in Unix time
        reply_to_message: Optional. For replies, the original message. Note
            that the Message object in this field will not contain further
            reply_to_message fields even if it itself is a reply.
        via_bot: Optional. Bot through which the message was sent
        edit_date: Optional. Date the message was last edited in Unix time
        media_group_id: Optional. The unique identifier of a media message
            group this message belongs to
        author_signature: Optional. Signature of the post author for
            messages in channels, or the custom title of an anonymous group
            administrator
        text: Optional. For text messages, the actual UTF-8 text of the
            message, 0-4096 characters
        entities: Optional. For text messages, special entities like
            usernames, URLs, bot commands, etc. that appear in the text
        animation: Optional. Message is an animation, information about the
            animation. For backward compatibility, when this field is set, the
            document field will also be set
        audio: Optional. Message is an audio file, information about the
            file
        document: Optional. Message is a general file, information about
            the file
        photo: Optional. Message is a photo, available sizes of the photo
        sticker: Optional. Message is a sticker, information about the
            sticker
        video: Optional. Message is a video, information about the video
        video_note: Optional. Message is a video note, information about
            the video message
        voice: Optional. Message is a voice message, information about the
            file
        caption: Optional. Caption for the animation, audio, document,
            photo, video or voice, 0-1024 characters
        caption_entities: Optional. For messages with a caption, special
            entities like usernames, URLs, bot commands, etc. that appear in
            the caption
        contact: Optional. Message is a shared contact, information about
            the contact
        dice: Optional. Message is a dice with random value
        game: Optional. Message is a game, information about the game. More
            about games »
        poll: Optional. Message is a native poll, information about the
            poll
        venue: Optional. Message is a venue, information about the venue.
            For backward compatibility, when this field is set, the location
            field will also be set
        location: Optional. Message is a shared location, information about
            the location
        new_chat_members: Optional. New members that were added to the
            group or supergroup and information about them (the bot itself may
            be one of these members)
        left_chat_member: Optional. A member was removed from the group,
            information about them (this member may be the bot itself)
        new_chat_title: Optional. A chat title was changed to this value
        new_chat_photo: Optional. A chat photo was change to this value
        delete_chat_photo: Optional. Service message: the chat photo was
            deleted
        group_chat_created: Optional. Service message: the group has been
            created
        supergroup_chat_created: Optional. Service message: the supergroup
            has been created. This field can't be received in a message coming
            through updates, because bot can't be a member of a supergroup
            when it is created. It can only be found in reply_to_message if
            someone replies to a very first message in a directly created
            supergroup.
        channel_chat_created: Optional. Service message: the channel has
            been created. This field can't be received in a message coming
            through updates, because bot can't be a member of a channel when
            it is created. It can only be found in reply_to_message if someone
            replies to a very first message in a channel.
        message_auto_delete_timer_changed: Optional. Service message:
            auto-delete timer settings changed in the chat
        migrate_to_chat_id: Optional. The group has been migrated to a
            supergroup with the specified identifier. This number may have
            more than 32 significant bits and some programming languages may
            have difficulty/silent defects in interpreting it. But it has at
            most 52 significant bits, so a signed 64-bit integer or
            double-precision float type are safe for storing this identifier.
        migrate_from_chat_id: Optional. The supergroup has been migrated
            from a group with the specified identifier. This number may have
            more than 32 significant bits and some programming languages may
            have difficulty/silent defects in interpreting it. But it has at
            most 52 significant bits, so a signed 64-bit integer or
            double-precision float type are safe for storing this identifier.
        pinned_message: Optional. Specified message was pinned. Note that
            the Message object in this field will not contain further
            reply_to_message fields even if it is itself a reply.
        invoice: Optional. Message is an invoice for a payment, information
            about the invoice. More about payments »
        successful_payment: Optional. Message is a service message about a
            successful payment, information about the payment. More about
            payments »
        connected_website: Optional. The domain name of the website on
            which the user has logged in. More about Telegram Login »
        passport_data: Optional. Telegram Passport data
        proximity_alert_triggered: Optional. Service message. A user in the
            chat triggered another user's proximity alert while sharing Live
            Location.
        voice_chat_started: Optional. Service message: voice chat started
        voice_chat_ended: Optional. Service message: voice chat ended
        voice_chat_participants_invited: Optional. Service message: new
            participants invited to a voice chat
        reply_markup: Optional. Inline keyboard attached to the message.
            login_url buttons are represented as ordinary url buttons.

    """

    message_id: int
    date: datetime
    chat: Chat
    from_user: User = None
    sender_chat: Chat = None
    forward_from: User = None
    forward_from_chat: Chat = None
    forward_from_message_id: int = None
    forward_signature: str = None
    forward_sender_name: str = None
    forward_date: datetime = None
    reply_to_message: Message = None
    via_bot: User = None
    edit_date: datetime = None
    media_group_id: str = None
    author_signature: str = None
    text: str = None
    entities: List[MessageEntity] = None
    animation: Animation = None
    audio: Audio = None
    document: Document = None
    photo: List[PhotoSize] = None
    sticker: Sticker = None
    video: Video = None
    video_note: VideoNote = None
    voice: Voice = None
    caption: str = None
    caption_entities: List[MessageEntity] = None
    contact: Contact = None
    dice: Dice = None
    game: Game = None
    poll: Poll = None
    venue: Venue = None
    location: Location = None
    new_chat_members: List[User] = None
    left_chat_member: User = None
    new_chat_title: str = None
    new_chat_photo: List[PhotoSize] = None
    delete_chat_photo: bool = True
    group_chat_created: bool = True
    supergroup_chat_created: bool = True
    channel_chat_created: bool = True
    message_auto_delete_timer_changed: MessageAutoDeleteTimerChanged = None
    migrate_to_chat_id: int = None
    migrate_from_chat_id: int = None
    pinned_message: Message = None
    invoice: Invoice = None
    successful_payment: SuccessfulPayment = None
    connected_website: str = None
    passport_data: PassportData = None
    proximity_alert_triggered: ProximityAlertTriggered = None
    voice_chat_started: VoiceChatStarted = None
    voice_chat_ended: VoiceChatEnded = None
    voice_chat_participants_invited: VoiceChatParticipantsInvited = None
    reply_markup: InlineKeyboardMarkup = None


@dataclass(eq=True)
class MessageId(TelegramType):
    """
    This object represents a unique message identifier.

    https://core.telegram.org/bots/api/#messageid

    Attributes:
        message_id: Unique message identifier

    """

    message_id: int


@dataclass(eq=True)
class MessageEntity(TelegramType):
    """
    This object represents one special entity in a text message. For example,
    hashtags, usernames, URLs, etc.

    https://core.telegram.org/bots/api/#messageentity

    Attributes:
        type: Type of the entity. Can be “mention” (@username), “hashtag”
            (#hashtag), “cashtag” ($USD), “bot_command” (/start@jobs_bot),
            “url” (https://telegram.org), “email” (do-not-reply@telegram.org),
            “phone_number” (+1-212-555-0123), “bold” (bold text), “italic”
            (italic text), “underline” (underlined text), “strikethrough”
            (strikethrough text), “code” (monowidth string), “pre” (monowidth
            block), “text_link” (for clickable text URLs), “text_mention” (for
            users without usernames)
        offset: Offset in UTF-16 code units to the start of the entity
        length: Length of the entity in UTF-16 code units
        url: Optional. For “text_link” only, url that will be opened after
            user taps on the text
        user: Optional. For “text_mention” only, the mentioned user
        language: Optional. For “pre” only, the programming language of the
            entity text

    """

    type: str
    offset: int
    length: int
    url: str = None
    user: User = None
    language: str = None
    text: str = None


@dataclass(eq=True)
class PhotoSize(TelegramType):
    """
    This object represents one size of a photo or a file / sticker thumbnail.

    https://core.telegram.org/bots/api/#photosize

    Attributes:
        file_id: Identifier for this file, which can be used to download or
            reuse the file
        file_unique_id: Unique identifier for this file, which is supposed
            to be the same over time and for different bots. Can't be used to
            download or reuse the file.
        width: Photo width
        height: Photo height
        file_size: Optional. File size

    """

    file_id: str
    file_unique_id: str
    width: int
    height: int
    file_size: int = None


@dataclass(eq=True)
class Animation(TelegramType):
    """
    This object represents an animation file (GIF or H.264/MPEG-4 AVC video
    without sound).

    https://core.telegram.org/bots/api/#animation

    Attributes:
        file_id: Identifier for this file, which can be used to download or
            reuse the file
        file_unique_id: Unique identifier for this file, which is supposed
            to be the same over time and for different bots. Can't be used to
            download or reuse the file.
        width: Video width as defined by sender
        height: Video height as defined by sender
        duration: Duration of the video in seconds as defined by sender
        thumb: Optional. Animation thumbnail as defined by sender
        file_name: Optional. Original animation filename as defined by
            sender
        mime_type: Optional. MIME type of the file as defined by sender
        file_size: Optional. File size

    """

    file_id: str
    file_unique_id: str
    width: int
    height: int
    duration: int
    thumb: Union[str, InputFile] = None
    file_name: str = None
    mime_type: str = None
    file_size: int = None


@dataclass(eq=True)
class Audio(TelegramType):
    """
    This object represents an audio file to be treated as music by the
    Telegram clients.

    https://core.telegram.org/bots/api/#audio

    Attributes:
        file_id: Identifier for this file, which can be used to download or
            reuse the file
        file_unique_id: Unique identifier for this file, which is supposed
            to be the same over time and for different bots. Can't be used to
            download or reuse the file.
        duration: Duration of the audio in seconds as defined by sender
        performer: Optional. Performer of the audio as defined by sender or
            by audio tags
        title: Optional. Title of the audio as defined by sender or by
            audio tags
        file_name: Optional. Original filename as defined by sender
        mime_type: Optional. MIME type of the file as defined by sender
        file_size: Optional. File size
        thumb: Optional. Thumbnail of the album cover to which the music
            file belongs

    """

    file_id: str
    file_unique_id: str
    duration: int
    performer: str = None
    title: str = None
    file_name: str = None
    mime_type: str = None
    file_size: int = None
    thumb: Union[str, InputFile] = None


@dataclass(eq=True)
class Document(TelegramType):
    """
    This object represents a general file (as opposed to photos, voice
    messages and audio files).

    https://core.telegram.org/bots/api/#document

    Attributes:
        file_id: Identifier for this file, which can be used to download or
            reuse the file
        file_unique_id: Unique identifier for this file, which is supposed
            to be the same over time and for different bots. Can't be used to
            download or reuse the file.
        thumb: Optional. Document thumbnail as defined by sender
        file_name: Optional. Original filename as defined by sender
        mime_type: Optional. MIME type of the file as defined by sender
        file_size: Optional. File size

    """

    file_id: str
    file_unique_id: str
    thumb: Union[str, InputFile] = None
    file_name: str = None
    mime_type: str = None
    file_size: int = None


@dataclass(eq=True)
class Video(TelegramType):
    """
    This object represents a video file.

    https://core.telegram.org/bots/api/#video

    Attributes:
        file_id: Identifier for this file, which can be used to download or
            reuse the file
        file_unique_id: Unique identifier for this file, which is supposed
            to be the same over time and for different bots. Can't be used to
            download or reuse the file.
        width: Video width as defined by sender
        height: Video height as defined by sender
        duration: Duration of the video in seconds as defined by sender
        thumb: Optional. Video thumbnail
        file_name: Optional. Original filename as defined by sender
        mime_type: Optional. Mime type of a file as defined by sender
        file_size: Optional. File size

    """

    file_id: str
    file_unique_id: str
    width: int
    height: int
    duration: int
    thumb: Union[str, InputFile] = None
    file_name: str = None
    mime_type: str = None
    file_size: int = None


@dataclass(eq=True)
class VideoNote(TelegramType):
    """
    This object represents a video message (available in Telegram apps as of
    v.4.0).

    https://core.telegram.org/bots/api/#videonote

    Attributes:
        file_id: Identifier for this file, which can be used to download or
            reuse the file
        file_unique_id: Unique identifier for this file, which is supposed
            to be the same over time and for different bots. Can't be used to
            download or reuse the file.
        length: Video width and height (diameter of the video message) as
            defined by sender
        duration: Duration of the video in seconds as defined by sender
        thumb: Optional. Video thumbnail
        file_size: Optional. File size

    """

    file_id: str
    file_unique_id: str
    length: int
    duration: int
    thumb: Union[str, InputFile] = None
    file_size: int = None


@dataclass(eq=True)
class Voice(TelegramType):
    """
    This object represents a voice note.

    https://core.telegram.org/bots/api/#voice

    Attributes:
        file_id: Identifier for this file, which can be used to download or
            reuse the file
        file_unique_id: Unique identifier for this file, which is supposed
            to be the same over time and for different bots. Can't be used to
            download or reuse the file.
        duration: Duration of the audio in seconds as defined by sender
        mime_type: Optional. MIME type of the file as defined by sender
        file_size: Optional. File size

    """

    file_id: str
    file_unique_id: str
    duration: int
    mime_type: str = None
    file_size: int = None


@dataclass(eq=True)
class Contact(TelegramType):
    """
    This object represents a phone contact.

    https://core.telegram.org/bots/api/#contact

    Attributes:
        phone_number: Contact's phone number
        first_name: Contact's first name
        last_name: Optional. Contact's last name
        user_id: Optional. Contact's user identifier in Telegram. This
            number may have more than 32 significant bits and some programming
            languages may have difficulty/silent defects in interpreting it.
            But it has at most 52 significant bits, so a 64-bit integer or
            double-precision float type are safe for storing this identifier.
        vcard: Optional. Additional data about the contact in the form of a
            vCard

    """

    phone_number: str
    first_name: str
    last_name: str = None
    user_id: int = None
    vcard: str = None


@dataclass(eq=True)
class Dice(TelegramType):
    """
    This object represents an animated emoji that displays a random value.

    https://core.telegram.org/bots/api/#dice

    Attributes:
        emoji: Emoji on which the dice throw animation is based
        value: Value of the dice, 1-6 for “”, “” and “” base emoji, 1-5 for
            “” and “” base emoji, 1-64 for “” base emoji

    """

    emoji: str
    value: int


@dataclass(eq=True)
class PollOption(TelegramType):
    """
    This object contains information about one answer option in a poll.

    https://core.telegram.org/bots/api/#polloption

    Attributes:
        text: Option text, 1-100 characters
        voter_count: Number of users that voted for this option

    """

    text: str
    voter_count: int


@dataclass(eq=True)
class PollAnswer(TelegramType):
    """
    This object represents an answer of a user in a non-anonymous poll.

    https://core.telegram.org/bots/api/#pollanswer

    Attributes:
        poll_id: Unique poll identifier
        user: The user, who changed the answer to the poll
        option_ids: 0-based identifiers of answer options, chosen by the
            user. May be empty if the user retracted their vote.

    """

    poll_id: str
    user: User
    option_ids: List[int]


@dataclass(eq=True)
class Poll(TelegramType):
    """
    This object contains information about a poll.

    https://core.telegram.org/bots/api/#poll

    Attributes:
        id: Unique poll identifier
        question: Poll question, 1-300 characters
        options: List of poll options
        total_voter_count: Total number of users that voted in the poll
        is_closed: True, if the poll is closed
        is_anonymous: True, if the poll is anonymous
        type: Poll type, currently can be “regular” or “quiz”
        allows_multiple_answers: True, if the poll allows multiple answers
        correct_option_id: Optional. 0-based identifier of the correct
            answer option. Available only for polls in the quiz mode, which
            are closed, or was sent (not forwarded) by the bot or to the
            private chat with the bot.
        explanation: Optional. Text that is shown when a user chooses an
            incorrect answer or taps on the lamp icon in a quiz-style poll,
            0-200 characters
        explanation_entities: Optional. Special entities like usernames,
            URLs, bot commands, etc. that appear in the explanation
        open_period: Optional. Amount of time in seconds the poll will be
            active after creation
        close_date: Optional. Point in time (Unix timestamp) when the poll
            will be automatically closed

    """

    id: str
    question: str
    options: List[PollOption]
    total_voter_count: int
    is_closed: bool
    is_anonymous: bool
    type: str
    allows_multiple_answers: bool
    correct_option_id: int = None
    explanation: str = None
    explanation_entities: List[MessageEntity] = None
    open_period: int = None
    close_date: datetime = None


@dataclass(eq=True)
class Location(TelegramType):
    """
    This object represents a point on the map.

    https://core.telegram.org/bots/api/#location

    Attributes:
        longitude: Longitude as defined by sender
        latitude: Latitude as defined by sender
        horizontal_accuracy: Optional. The radius of uncertainty for the
            location, measured in meters; 0-1500
        live_period: Optional. Time relative to the message sending date,
            during which the location can be updated, in seconds. For active
            live locations only.
        heading: Optional. The direction in which user is moving, in
            degrees; 1-360. For active live locations only.
        proximity_alert_radius: Optional. Maximum distance for proximity
            alerts about approaching another chat member, in meters. For sent
            live locations only.

    """

    longitude: float
    latitude: float
    horizontal_accuracy: float = None
    live_period: int = None
    heading: int = None
    proximity_alert_radius: int = None


@dataclass(eq=True)
class Venue(TelegramType):
    """
    This object represents a venue.

    https://core.telegram.org/bots/api/#venue

    Attributes:
        location: Venue location. Can't be a live location
        title: Name of the venue
        address: Address of the venue
        foursquare_id: Optional. Foursquare identifier of the venue
        foursquare_type: Optional. Foursquare type of the venue. (For
            example, “arts_entertainment/default”,
            “arts_entertainment/aquarium” or “food/icecream”.)
        google_place_id: Optional. Google Places identifier of the venue
        google_place_type: Optional. Google Places type of the venue. (See
            supported types.)

    """

    location: Location
    title: str
    address: str
    foursquare_id: str = None
    foursquare_type: str = None
    google_place_id: str = None
    google_place_type: str = None


@dataclass(eq=True)
class ProximityAlertTriggered(TelegramType):
    """
    This object represents the content of a service message, sent whenever a
    user in the chat triggers a proximity alert set by another user.

    https://core.telegram.org/bots/api/#proximityalerttriggered

    Attributes:
        traveler: User that triggered the alert
        watcher: User that set the alert
        distance: The distance between the users

    """

    traveler: User
    watcher: User
    distance: int


@dataclass(eq=True)
class MessageAutoDeleteTimerChanged(TelegramType):
    """
    This object represents a service message about a change in auto-delete
    timer settings.

    https://core.telegram.org/bots/api/#messageautodeletetimerchanged

    Attributes:
        message_auto_delete_time: New auto-delete time for messages in the
            chat

    """

    message_auto_delete_time: int


@dataclass(eq=True)
class VoiceChatStarted(TelegramType):
    """
    This object represents a service message about a voice chat started in the
    chat. Currently holds no information.

    https://core.telegram.org/bots/api/#voicechatstarted


    """

    pass


@dataclass(eq=True)
class VoiceChatEnded(TelegramType):
    """
    This object represents a service message about a voice chat ended in the
    chat.

    https://core.telegram.org/bots/api/#voicechatended

    Attributes:
        duration: Voice chat duration; in seconds

    """

    duration: int


@dataclass(eq=True)
class VoiceChatParticipantsInvited(TelegramType):
    """
    This object represents a service message about new members invited to a
    voice chat.

    https://core.telegram.org/bots/api/#voicechatparticipantsinvited

    Attributes:
        users: Optional. New members that were invited to the voice chat

    """

    users: List[User] = None


@dataclass(eq=True)
class UserProfilePhotos(TelegramType):
    """
    This object represent a user's profile pictures.

    https://core.telegram.org/bots/api/#userprofilephotos

    Attributes:
        total_count: Total number of profile pictures the target user has
        photos: Requested profile pictures (in up to 4 sizes each)

    """

    total_count: int
    photos: List[List[PhotoSize]]


@dataclass(eq=True)
class File(TelegramType):
    """
    This object represents a file ready to be downloaded. The file can be
    downloaded via the link
    https://api.telegram.org/file/bot<token>/<file_path>. It is guaranteed
    that the link will be valid for at least 1 hour. When the link expires, a
    new one can be requested by calling getFile.

    Maximum file size to download is 20 MB

    https://core.telegram.org/bots/api/#file

    Attributes:
        file_id: Identifier for this file, which can be used to download or
            reuse the file
        file_unique_id: Unique identifier for this file, which is supposed
            to be the same over time and for different bots. Can't be used to
            download or reuse the file.
        file_size: Optional. File size, if known
        file_path: Optional. File path. Use
            https://api.telegram.org/file/bot<token>/<file_path> to get the
            file.

    """

    file_id: str
    file_unique_id: str
    file_size: int = None
    file_path: str = None


@dataclass(eq=True)
class ReplyKeyboardMarkup(TelegramType):
    """
    This object represents a custom keyboard with reply options (see
    Introduction to bots for details and examples).

    https://core.telegram.org/bots/api/#replykeyboardmarkup

    Attributes:
        keyboard: Array of button rows, each represented by an Array of
            KeyboardButton objects
        resize_keyboard: Optional. Requests clients to resize the keyboard
            vertically for optimal fit (e.g., make the keyboard smaller if
            there are just two rows of buttons). Defaults to false, in which
            case the custom keyboard is always of the same height as the app's
            standard keyboard.
        one_time_keyboard: Optional. Requests clients to hide the keyboard
            as soon as it's been used. The keyboard will still be available,
            but clients will automatically display the usual letter-keyboard
            in the chat – the user can press a special button in the input
            field to see the custom keyboard again. Defaults to false.
        selective: Optional. Use this parameter if you want to show the
            keyboard to specific users only. Targets: 1) users that are
            @mentioned in the text of the Message object; 2) if the bot's
            message is a reply (has reply_to_message_id), sender of the
            original message.Example: A user requests to change the bot's
            language, bot replies to the request with a keyboard to select the
            new language. Other users in the group don't see the keyboard.

    """

    keyboard: List[List[KeyboardButton]]
    resize_keyboard: bool = None
    one_time_keyboard: bool = None
    selective: bool = None


@dataclass(eq=True)
class KeyboardButton(TelegramType):
    """
    This object represents one button of the reply keyboard. For simple text
    buttons String can be used instead of this object to specify text of the
    button. Optional fields request_contact, request_location, and
    request_poll are mutually exclusive.

    https://core.telegram.org/bots/api/#keyboardbutton

    Attributes:
        text: Text of the button. If none of the optional fields are used,
            it will be sent as a message when the button is pressed
        request_contact: Optional. If True, the user's phone number will be
            sent as a contact when the button is pressed. Available in private
            chats only
        request_location: Optional. If True, the user's current location
            will be sent when the button is pressed. Available in private
            chats only
        request_poll: Optional. If specified, the user will be asked to
            create a poll and send it to the bot when the button is pressed.
            Available in private chats only

    """

    text: str
    request_contact: bool = None
    request_location: bool = None
    request_poll: KeyboardButtonPollType = None


@dataclass(eq=True)
class KeyboardButtonPollType(TelegramType):
    """
    This object represents type of a poll, which is allowed to be created and
    sent when the corresponding button is pressed.

    https://core.telegram.org/bots/api/#keyboardbuttonpolltype

    Attributes:
        type: Optional. If quiz is passed, the user will be allowed to
            create only polls in the quiz mode. If regular is passed, only
            regular polls will be allowed. Otherwise, the user will be allowed
            to create a poll of any type.

    """

    type: str = None


@dataclass(eq=True)
class ReplyKeyboardRemove(TelegramType):
    """
    Upon receiving a message with this object, Telegram clients will remove
    the current custom keyboard and display the default letter-keyboard. By
    default, custom keyboards are displayed until a new keyboard is sent by a
    bot. An exception is made for one-time keyboards that are hidden
    immediately after the user presses a button (see ReplyKeyboardMarkup).

    https://core.telegram.org/bots/api/#replykeyboardremove

    Attributes:
        remove_keyboard: Requests clients to remove the custom keyboard
            (user will not be able to summon this keyboard; if you want to
            hide the keyboard from sight but keep it accessible, use
            one_time_keyboard in ReplyKeyboardMarkup)
        selective: Optional. Use this parameter if you want to remove the
            keyboard for specific users only. Targets: 1) users that are
            @mentioned in the text of the Message object; 2) if the bot's
            message is a reply (has reply_to_message_id), sender of the
            original message.Example: A user votes in a poll, bot returns
            confirmation message in reply to the vote and removes the keyboard
            for that user, while still showing the keyboard with poll options
            to users who haven't voted yet.

    """

    remove_keyboard: bool
    selective: bool = None


@dataclass(eq=True)
class InlineKeyboardMarkup(TelegramType):
    """
    This object represents an inline keyboard that appears right next to the
    message it belongs to.

    https://core.telegram.org/bots/api/#inlinekeyboardmarkup

    Attributes:
        inline_keyboard: Array of button rows, each represented by an Array
            of InlineKeyboardButton objects

    """

    inline_keyboard: List[List[InlineKeyboardButton]]


@dataclass(eq=True)
class InlineKeyboardButton(TelegramType):
    """
    This object represents one button of an inline keyboard. You must use
    exactly one of the optional fields.

    https://core.telegram.org/bots/api/#inlinekeyboardbutton

    Attributes:
        text: Label text on the button
        url: Optional. HTTP or tg:// url to be opened when button is
            pressed
        login_url: Optional. An HTTP URL used to automatically authorize
            the user. Can be used as a replacement for the Telegram Login
            Widget.
        callback_data: Optional. Data to be sent in a callback query to the
            bot when button is pressed, 1-64 bytes
        switch_inline_query: Optional. If set, pressing the button will
            prompt the user to select one of their chats, open that chat and
            insert the bot's username and the specified inline query in the
            input field. Can be empty, in which case just the bot's username
            will be inserted.Note: This offers an easy way for users to start
            using your bot in inline mode when they are currently in a private
            chat with it. Especially useful when combined with switch_pm…
            actions – in this case the user will be automatically returned to
            the chat they switched from, skipping the chat selection screen.
        switch_inline_query_current_chat: Optional. If set, pressing the
            button will insert the bot's username and the specified inline
            query in the current chat's input field. Can be empty, in which
            case only the bot's username will be inserted.This offers a quick
            way for the user to open your bot in inline mode in the same chat
            – good for selecting something from multiple options.
        callback_game: Optional. Description of the game that will be
            launched when the user presses the button.NOTE: This type of
            button must always be the first button in the first row.
        pay: Optional. Specify True, to send a Pay button.NOTE: This type
            of button must always be the first button in the first row.

    """

    text: str
    url: str = None
    login_url: LoginUrl = None
    callback_data: str = None
    switch_inline_query: str = None
    switch_inline_query_current_chat: str = None
    callback_game: CallbackGame = None
    pay: bool = None


@dataclass(eq=True)
class LoginUrl(TelegramType):
    """
    This object represents a parameter of the inline keyboard button used to
    automatically authorize a user. Serves as a great replacement for the
    Telegram Login Widget when the user is coming from Telegram. All the user
    needs to do is tap/click a button and confirm that they want to log in:

    https://core.telegram.org/bots/api/#loginurl

    Attributes:
        url: An HTTP URL to be opened with user authorization data added to
            the query string when the button is pressed. If the user refuses
            to provide authorization data, the original URL without
            information about the user will be opened. The data added is the
            same as described in Receiving authorization data.NOTE: You must
            always check the hash of the received data to verify the
            authentication and the integrity of the data as described in
            Checking authorization.
        forward_text: Optional. New text of the button in forwarded
            messages.
        bot_username: Optional. Username of a bot, which will be used for
            user authorization. See Setting up a bot for more details. If not
            specified, the current bot's username will be assumed. The url's
            domain must be the same as the domain linked with the bot. See
            Linking your domain to the bot for more details.
        request_write_access: Optional. Pass True to request the permission
            for your bot to send messages to the user.

    """

    url: str
    forward_text: str = None
    bot_username: str = None
    request_write_access: bool = None


@dataclass(eq=True)
class CallbackQuery(TelegramType):
    """
    This object represents an incoming callback query from a callback button
    in an inline keyboard. If the button that originated the query was
    attached to a message sent by the bot, the field message will be present.
    If the button was attached to a message sent via the bot (in inline mode),
    the field inline_message_id will be present. Exactly one of the fields
    data or game_short_name will be present.

    https://core.telegram.org/bots/api/#callbackquery

    Attributes:
        id: Unique identifier for this query
        from_user: Sender
        chat_instance: Global identifier, uniquely corresponding to the
            chat to which the message with the callback button was sent.
            Useful for high scores in games.
        message: Optional. Message with the callback button that originated
            the query. Note that message content and message date will not be
            available if the message is too old
        inline_message_id: Optional. Identifier of the message sent via the
            bot in inline mode, that originated the query.
        data: Optional. Data associated with the callback button. Be aware
            that a bad client can send arbitrary data in this field.
        game_short_name: Optional. Short name of a Game to be returned,
            serves as the unique identifier for the game

    """

    id: str
    from_user: User
    chat_instance: str
    message: Message = None
    inline_message_id: str = None
    data: str = None
    game_short_name: str = None


@dataclass(eq=True)
class ForceReply(TelegramType):
    """
    Upon receiving a message with this object, Telegram clients will display a
    reply interface to the user (act as if the user has selected the bot's
    message and tapped 'Reply'). This can be extremely useful if you want to
    create user-friendly step-by-step interfaces without having to sacrifice
    privacy mode.

    https://core.telegram.org/bots/api/#forcereply

    Attributes:
        force_reply: Shows reply interface to the user, as if they manually
            selected the bot's message and tapped 'Reply'
        selective: Optional. Use this parameter if you want to force reply
            from specific users only. Targets: 1) users that are @mentioned in
            the text of the Message object; 2) if the bot's message is a reply
            (has reply_to_message_id), sender of the original message.

    """

    force_reply: bool
    selective: bool = None


@dataclass(eq=True)
class ChatPhoto(TelegramType):
    """
    This object represents a chat photo.

    https://core.telegram.org/bots/api/#chatphoto

    Attributes:
        small_file_id: File identifier of small (160x160) chat photo. This
            file_id can be used only for photo download and only for as long
            as the photo is not changed.
        small_file_unique_id: Unique file identifier of small (160x160)
            chat photo, which is supposed to be the same over time and for
            different bots. Can't be used to download or reuse the file.
        big_file_id: File identifier of big (640x640) chat photo. This
            file_id can be used only for photo download and only for as long
            as the photo is not changed.
        big_file_unique_id: Unique file identifier of big (640x640) chat
            photo, which is supposed to be the same over time and for
            different bots. Can't be used to download or reuse the file.

    """

    small_file_id: str
    small_file_unique_id: str
    big_file_id: str
    big_file_unique_id: str


@dataclass(eq=True)
class ChatInviteLink(TelegramType):
    """
    Represents an invite link for a chat.

    https://core.telegram.org/bots/api/#chatinvitelink

    Attributes:
        invite_link: The invite link. If the link was created by another
            chat administrator, then the second part of the link will be
            replaced with “…”.
        creator: Creator of the link
        is_primary: True, if the link is primary
        is_revoked: True, if the link is revoked
        expire_date: Optional. Point in time (Unix timestamp) when the link
            will expire or has been expired
        member_limit: Optional. Maximum number of users that can be members
            of the chat simultaneously after joining the chat via this invite
            link; 1-99999

    """

    invite_link: str
    creator: User
    is_primary: bool
    is_revoked: bool
    expire_date: datetime = None
    member_limit: int = None


@dataclass(eq=True)
class ChatMember(TelegramType):
    """
    This object contains information about one member of a chat.

    https://core.telegram.org/bots/api/#chatmember

    Attributes:
        user: Information about the user
        status: The member's status in the chat. Can be “creator”,
            “administrator”, “member”, “restricted”, “left” or “kicked”
        custom_title: Optional. Owner and administrators only. Custom title
            for this user
        is_anonymous: Optional. Owner and administrators only. True, if the
            user's presence in the chat is hidden
        can_be_edited: Optional. Administrators only. True, if the bot is
            allowed to edit administrator privileges of that user
        can_manage_chat: Optional. Administrators only. True, if the
            administrator can access the chat event log, chat statistics,
            message statistics in channels, see channel members, see anonymous
            administrators in supergroups and ignore slow mode. Implied by any
            other administrator privilege
        can_post_messages: Optional. Administrators only. True, if the
            administrator can post in the channel; channels only
        can_edit_messages: Optional. Administrators only. True, if the
            administrator can edit messages of other users and can pin
            messages; channels only
        can_delete_messages: Optional. Administrators only. True, if the
            administrator can delete messages of other users
        can_manage_voice_chats: Optional. Administrators only. True, if the
            administrator can manage voice chats
        can_restrict_members: Optional. Administrators only. True, if the
            administrator can restrict, ban or unban chat members
        can_promote_members: Optional. Administrators only. True, if the
            administrator can add new administrators with a subset of their
            own privileges or demote administrators that he has promoted,
            directly or indirectly (promoted by administrators that were
            appointed by the user)
        can_change_info: Optional. Administrators and restricted only.
            True, if the user is allowed to change the chat title, photo and
            other settings
        can_invite_users: Optional. Administrators and restricted only.
            True, if the user is allowed to invite new users to the chat
        can_pin_messages: Optional. Administrators and restricted only.
            True, if the user is allowed to pin messages; groups and
            supergroups only
        is_member: Optional. Restricted only. True, if the user is a member
            of the chat at the moment of the request
        can_send_messages: Optional. Restricted only. True, if the user is
            allowed to send text messages, contacts, locations and venues
        can_send_media_messages: Optional. Restricted only. True, if the
            user is allowed to send audios, documents, photos, videos, video
            notes and voice notes
        can_send_polls: Optional. Restricted only. True, if the user is
            allowed to send polls
        can_send_other_messages: Optional. Restricted only. True, if the
            user is allowed to send animations, games, stickers and use inline
            bots
        can_add_web_page_previews: Optional. Restricted only. True, if the
            user is allowed to add web page previews to their messages
        until_date: Optional. Restricted and kicked only. Date when
            restrictions will be lifted for this user; unix time

    """

    user: User
    status: str
    custom_title: str = None
    is_anonymous: bool = None
    can_be_edited: bool = None
    can_manage_chat: bool = None
    can_post_messages: bool = None
    can_edit_messages: bool = None
    can_delete_messages: bool = None
    can_manage_voice_chats: bool = None
    can_restrict_members: bool = None
    can_promote_members: bool = None
    can_change_info: bool = None
    can_invite_users: bool = None
    can_pin_messages: bool = None
    is_member: bool = None
    can_send_messages: bool = None
    can_send_media_messages: bool = None
    can_send_polls: bool = None
    can_send_other_messages: bool = None
    can_add_web_page_previews: bool = None
    until_date: datetime = None


@dataclass(eq=True)
class ChatMemberUpdated(TelegramType):
    """
    This object represents changes in the status of a chat member.

    https://core.telegram.org/bots/api/#chatmemberupdated

    Attributes:
        chat: Chat the user belongs to
        from_user: Performer of the action, which resulted in the change
        date: Date the change was done in Unix time
        old_chat_member: Previous information about the chat member
        new_chat_member: New information about the chat member
        invite_link: Optional. Chat invite link, which was used by the user
            to join the chat; for joining by invite link events only.

    """

    chat: Chat
    from_user: User
    date: datetime
    old_chat_member: ChatMember
    new_chat_member: ChatMember
    invite_link: ChatInviteLink = None


@dataclass(eq=True)
class ChatPermissions(TelegramType):
    """
    Describes actions that a non-administrator user is allowed to take in a
    chat.

    https://core.telegram.org/bots/api/#chatpermissions

    Attributes:
        can_send_messages: Optional. True, if the user is allowed to send
            text messages, contacts, locations and venues
        can_send_media_messages: Optional. True, if the user is allowed to
            send audios, documents, photos, videos, video notes and voice
            notes, implies can_send_messages
        can_send_polls: Optional. True, if the user is allowed to send
            polls, implies can_send_messages
        can_send_other_messages: Optional. True, if the user is allowed to
            send animations, games, stickers and use inline bots, implies
            can_send_media_messages
        can_add_web_page_previews: Optional. True, if the user is allowed
            to add web page previews to their messages, implies
            can_send_media_messages
        can_change_info: Optional. True, if the user is allowed to change
            the chat title, photo and other settings. Ignored in public
            supergroups
        can_invite_users: Optional. True, if the user is allowed to invite
            new users to the chat
        can_pin_messages: Optional. True, if the user is allowed to pin
            messages. Ignored in public supergroups

    """

    can_send_messages: bool = None
    can_send_media_messages: bool = None
    can_send_polls: bool = None
    can_send_other_messages: bool = None
    can_add_web_page_previews: bool = None
    can_change_info: bool = None
    can_invite_users: bool = None
    can_pin_messages: bool = None


@dataclass(eq=True)
class ChatLocation(TelegramType):
    """
    Represents a location to which a chat is connected.

    https://core.telegram.org/bots/api/#chatlocation

    Attributes:
        location: The location to which the supergroup is connected. Can't
            be a live location.
        address: Location address; 1-64 characters, as defined by the chat
            owner

    """

    location: Location
    address: str


@dataclass(eq=True)
class BotCommand(TelegramType):
    """
    This object represents a bot command.

    https://core.telegram.org/bots/api/#botcommand

    Attributes:
        command: Text of the command, 1-32 characters. Can contain only
            lowercase English letters, digits and underscores.
        description: Description of the command, 3-256 characters.

    """

    command: str
    description: str


@dataclass(eq=True)
class ResponseParameters(TelegramType):
    """
    Contains information about why a request was unsuccessful.

    https://core.telegram.org/bots/api/#responseparameters

    Attributes:
        migrate_to_chat_id: Optional. The group has been migrated to a
            supergroup with the specified identifier. This number may have
            more than 32 significant bits and some programming languages may
            have difficulty/silent defects in interpreting it. But it has at
            most 52 significant bits, so a signed 64-bit integer or
            double-precision float type are safe for storing this identifier.
        retry_after: Optional. In case of exceeding flood control, the
            number of seconds left to wait before the request can be repeated

    """

    migrate_to_chat_id: int = None
    retry_after: int = None


@dataclass(eq=True)
class InputMediaPhoto(TelegramType):
    """
    Represents a photo to be sent.

    https://core.telegram.org/bots/api/#inputmediaphoto

    Attributes:
        type: Type of the result, must be photo
        media: File to send. Pass a file_id to send a file that exists on
            the Telegram servers (recommended), pass an HTTP URL for Telegram
            to get a file from the Internet, or pass
            “attach://<file_attach_name>” to upload a new one using
            multipart/form-data under <file_attach_name> name. More info on
            Sending Files »
        caption: Optional. Caption of the photo to be sent, 0-1024
            characters after entities parsing
        parse_mode: Optional. Mode for parsing entities in the photo
            caption. See formatting options for more details.
        caption_entities: Optional. List of special entities that appear in
            the caption, which can be specified instead of parse_mode

    """

    type: str
    media: str
    caption: str = None
    parse_mode: str = None
    caption_entities: List[MessageEntity] = None


@dataclass(eq=True)
class InputMediaVideo(TelegramType):
    """
    Represents a video to be sent.

    https://core.telegram.org/bots/api/#inputmediavideo

    Attributes:
        type: Type of the result, must be video
        media: File to send. Pass a file_id to send a file that exists on
            the Telegram servers (recommended), pass an HTTP URL for Telegram
            to get a file from the Internet, or pass
            “attach://<file_attach_name>” to upload a new one using
            multipart/form-data under <file_attach_name> name. More info on
            Sending Files »
        thumb: Optional. Thumbnail of the file sent; can be ignored if
            thumbnail generation for the file is supported server-side. The
            thumbnail should be in JPEG format and less than 200 kB in size. A
            thumbnail's width and height should not exceed 320. Ignored if the
            file is not uploaded using multipart/form-data. Thumbnails can't
            be reused and can be only uploaded as a new file, so you can pass
            “attach://<file_attach_name>” if the thumbnail was uploaded using
            multipart/form-data under <file_attach_name>. More info on Sending
            Files »
        caption: Optional. Caption of the video to be sent, 0-1024
            characters after entities parsing
        parse_mode: Optional. Mode for parsing entities in the video
            caption. See formatting options for more details.
        caption_entities: Optional. List of special entities that appear in
            the caption, which can be specified instead of parse_mode
        width: Optional. Video width
        height: Optional. Video height
        duration: Optional. Video duration
        supports_streaming: Optional. Pass True, if the uploaded video is
            suitable for streaming

    """

    type: str
    media: str
    thumb: Union[str, InputFile] = None
    caption: str = None
    parse_mode: str = None
    caption_entities: List[MessageEntity] = None
    width: int = None
    height: int = None
    duration: int = None
    supports_streaming: bool = None


@dataclass(eq=True)
class InputMediaAnimation(TelegramType):
    """
    Represents an animation file (GIF or H.264/MPEG-4 AVC video without sound)
    to be sent.

    https://core.telegram.org/bots/api/#inputmediaanimation

    Attributes:
        type: Type of the result, must be animation
        media: File to send. Pass a file_id to send a file that exists on
            the Telegram servers (recommended), pass an HTTP URL for Telegram
            to get a file from the Internet, or pass
            “attach://<file_attach_name>” to upload a new one using
            multipart/form-data under <file_attach_name> name. More info on
            Sending Files »
        thumb: Optional. Thumbnail of the file sent; can be ignored if
            thumbnail generation for the file is supported server-side. The
            thumbnail should be in JPEG format and less than 200 kB in size. A
            thumbnail's width and height should not exceed 320. Ignored if the
            file is not uploaded using multipart/form-data. Thumbnails can't
            be reused and can be only uploaded as a new file, so you can pass
            “attach://<file_attach_name>” if the thumbnail was uploaded using
            multipart/form-data under <file_attach_name>. More info on Sending
            Files »
        caption: Optional. Caption of the animation to be sent, 0-1024
            characters after entities parsing
        parse_mode: Optional. Mode for parsing entities in the animation
            caption. See formatting options for more details.
        caption_entities: Optional. List of special entities that appear in
            the caption, which can be specified instead of parse_mode
        width: Optional. Animation width
        height: Optional. Animation height
        duration: Optional. Animation duration

    """

    type: str
    media: str
    thumb: Union[str, InputFile] = None
    caption: str = None
    parse_mode: str = None
    caption_entities: List[MessageEntity] = None
    width: int = None
    height: int = None
    duration: int = None


@dataclass(eq=True)
class InputMediaAudio(TelegramType):
    """
    Represents an audio file to be treated as music to be sent.

    https://core.telegram.org/bots/api/#inputmediaaudio

    Attributes:
        type: Type of the result, must be audio
        media: File to send. Pass a file_id to send a file that exists on
            the Telegram servers (recommended), pass an HTTP URL for Telegram
            to get a file from the Internet, or pass
            “attach://<file_attach_name>” to upload a new one using
            multipart/form-data under <file_attach_name> name. More info on
            Sending Files »
        thumb: Optional. Thumbnail of the file sent; can be ignored if
            thumbnail generation for the file is supported server-side. The
            thumbnail should be in JPEG format and less than 200 kB in size. A
            thumbnail's width and height should not exceed 320. Ignored if the
            file is not uploaded using multipart/form-data. Thumbnails can't
            be reused and can be only uploaded as a new file, so you can pass
            “attach://<file_attach_name>” if the thumbnail was uploaded using
            multipart/form-data under <file_attach_name>. More info on Sending
            Files »
        caption: Optional. Caption of the audio to be sent, 0-1024
            characters after entities parsing
        parse_mode: Optional. Mode for parsing entities in the audio
            caption. See formatting options for more details.
        caption_entities: Optional. List of special entities that appear in
            the caption, which can be specified instead of parse_mode
        duration: Optional. Duration of the audio in seconds
        performer: Optional. Performer of the audio
        title: Optional. Title of the audio

    """

    type: str
    media: str
    thumb: Union[str, InputFile] = None
    caption: str = None
    parse_mode: str = None
    caption_entities: List[MessageEntity] = None
    duration: int = None
    performer: str = None
    title: str = None


@dataclass(eq=True)
class InputMediaDocument(TelegramType):
    """
    Represents a general file to be sent.

    https://core.telegram.org/bots/api/#inputmediadocument

    Attributes:
        type: Type of the result, must be document
        media: File to send. Pass a file_id to send a file that exists on
            the Telegram servers (recommended), pass an HTTP URL for Telegram
            to get a file from the Internet, or pass
            “attach://<file_attach_name>” to upload a new one using
            multipart/form-data under <file_attach_name> name. More info on
            Sending Files »
        thumb: Optional. Thumbnail of the file sent; can be ignored if
            thumbnail generation for the file is supported server-side. The
            thumbnail should be in JPEG format and less than 200 kB in size. A
            thumbnail's width and height should not exceed 320. Ignored if the
            file is not uploaded using multipart/form-data. Thumbnails can't
            be reused and can be only uploaded as a new file, so you can pass
            “attach://<file_attach_name>” if the thumbnail was uploaded using
            multipart/form-data under <file_attach_name>. More info on Sending
            Files »
        caption: Optional. Caption of the document to be sent, 0-1024
            characters after entities parsing
        parse_mode: Optional. Mode for parsing entities in the document
            caption. See formatting options for more details.
        caption_entities: Optional. List of special entities that appear in
            the caption, which can be specified instead of parse_mode
        disable_content_type_detection: Optional. Disables automatic
            server-side content type detection for files uploaded using
            multipart/form-data. Always true, if the document is sent as part
            of an album.

    """

    type: str
    media: str
    thumb: Union[str, InputFile] = None
    caption: str = None
    parse_mode: str = None
    caption_entities: List[MessageEntity] = None
    disable_content_type_detection: bool = None


@dataclass(eq=True)
class InputFile(TelegramType):
    """
    This object represents the contents of a file to be uploaded. Must be
    posted using multipart/form-data in the usual way that files are uploaded
    via the browser.

    https://core.telegram.org/bots/api/#inputfile


    """

    pass


@dataclass(eq=True)
class Sticker(TelegramType):
    """
    This object represents a sticker.

    https://core.telegram.org/bots/api/#sticker

    Attributes:
        file_id: Identifier for this file, which can be used to download or
            reuse the file
        file_unique_id: Unique identifier for this file, which is supposed
            to be the same over time and for different bots. Can't be used to
            download or reuse the file.
        width: Sticker width
        height: Sticker height
        is_animated: True, if the sticker is animated
        thumb: Optional. Sticker thumbnail in the .WEBP or .JPG format
        emoji: Optional. Emoji associated with the sticker
        set_name: Optional. Name of the sticker set to which the sticker
            belongs
        mask_position: Optional. For mask stickers, the position where the
            mask should be placed
        file_size: Optional. File size

    """

    file_id: str
    file_unique_id: str
    width: int
    height: int
    is_animated: bool
    thumb: Union[str, InputFile] = None
    emoji: str = None
    set_name: str = None
    mask_position: MaskPosition = None
    file_size: int = None


@dataclass(eq=True)
class StickerSet(TelegramType):
    """
    This object represents a sticker set.

    https://core.telegram.org/bots/api/#stickerset

    Attributes:
        name: Sticker set name
        title: Sticker set title
        is_animated: True, if the sticker set contains animated stickers
        contains_masks: True, if the sticker set contains masks
        stickers: List of all set stickers
        thumb: Optional. Sticker set thumbnail in the .WEBP or .TGS format

    """

    name: str
    title: str
    is_animated: bool
    contains_masks: bool
    stickers: List[Sticker]
    thumb: Union[str, InputFile] = None


@dataclass(eq=True)
class MaskPosition(TelegramType):
    """
    This object describes the position on faces where a mask should be placed
    by default.

    https://core.telegram.org/bots/api/#maskposition

    Attributes:
        point: The part of the face relative to which the mask should be
            placed. One of “forehead”, “eyes”, “mouth”, or “chin”.
        x_shift: Shift by X-axis measured in widths of the mask scaled to
            the face size, from left to right. For example, choosing -1.0 will
            place mask just to the left of the default mask position.
        y_shift: Shift by Y-axis measured in heights of the mask scaled to
            the face size, from top to bottom. For example, 1.0 will place the
            mask just below the default mask position.
        scale: Mask scaling coefficient. For example, 2.0 means double
            size.

    """

    point: str
    x_shift: float
    y_shift: float
    scale: float


@dataclass(eq=True)
class InlineQuery(TelegramType):
    """
    This object represents an incoming inline query. When the user sends an
    empty query, your bot could return some default or trending results.

    https://core.telegram.org/bots/api/#inlinequery

    Attributes:
        id: Unique identifier for this query
        from_user: Sender
        query: Text of the query (up to 256 characters)
        offset: Offset of the results to be returned, can be controlled by
            the bot
        location: Optional. Sender location, only for bots that request
            user location

    """

    id: str
    from_user: User
    query: str
    offset: str
    location: Location = None


@dataclass(eq=True)
class InlineQueryResultArticle(TelegramType):
    """
    Represents a link to an article or web page.

    https://core.telegram.org/bots/api/#inlinequeryresultarticle

    Attributes:
        type: Type of the result, must be article
        id: Unique identifier for this result, 1-64 Bytes
        title: Title of the result
        input_message_content: Content of the message to be sent
        reply_markup: Optional. Inline keyboard attached to the message
        url: Optional. URL of the result
        hide_url: Optional. Pass True, if you don't want the URL to be
            shown in the message
        description: Optional. Short description of the result
        thumb_url: Optional. Url of the thumbnail for the result
        thumb_width: Optional. Thumbnail width
        thumb_height: Optional. Thumbnail height

    """

    type: str
    id: str
    title: str
    input_message_content: Union[
        InputTextMessageContent,
        InputLocationMessageContent,
        InputVenueMessageContent,
        InputContactMessageContent,
    ]
    reply_markup: InlineKeyboardMarkup = None
    url: str = None
    hide_url: bool = None
    description: str = None
    thumb_url: str = None
    thumb_width: int = None
    thumb_height: int = None


@dataclass(eq=True)
class InlineQueryResultPhoto(TelegramType):
    """
    Represents a link to a photo. By default, this photo will be sent by the
    user with optional caption. Alternatively, you can use
    input_message_content to send a message with the specified content instead
    of the photo.

    https://core.telegram.org/bots/api/#inlinequeryresultphoto

    Attributes:
        type: Type of the result, must be photo
        id: Unique identifier for this result, 1-64 bytes
        photo_url: A valid URL of the photo. Photo must be in jpeg format.
            Photo size must not exceed 5MB
        thumb_url: URL of the thumbnail for the photo
        photo_width: Optional. Width of the photo
        photo_height: Optional. Height of the photo
        title: Optional. Title for the result
        description: Optional. Short description of the result
        caption: Optional. Caption of the photo to be sent, 0-1024
            characters after entities parsing
        parse_mode: Optional. Mode for parsing entities in the photo
            caption. See formatting options for more details.
        caption_entities: Optional. List of special entities that appear in
            the caption, which can be specified instead of parse_mode
        reply_markup: Optional. Inline keyboard attached to the message
        input_message_content: Optional. Content of the message to be sent
            instead of the photo

    """

    type: str
    id: str
    photo_url: str
    thumb_url: str
    photo_width: int = None
    photo_height: int = None
    title: str = None
    description: str = None
    caption: str = None
    parse_mode: str = None
    caption_entities: List[MessageEntity] = None
    reply_markup: InlineKeyboardMarkup = None
    input_message_content: Union[
        InputTextMessageContent,
        InputLocationMessageContent,
        InputVenueMessageContent,
        InputContactMessageContent,
    ] = None


@dataclass(eq=True)
class InlineQueryResultGif(TelegramType):
    """
    Represents a link to an animated GIF file. By default, this animated GIF
    file will be sent by the user with optional caption. Alternatively, you
    can use input_message_content to send a message with the specified content
    instead of the animation.

    https://core.telegram.org/bots/api/#inlinequeryresultgif

    Attributes:
        type: Type of the result, must be gif
        id: Unique identifier for this result, 1-64 bytes
        gif_url: A valid URL for the GIF file. File size must not exceed
            1MB
        thumb_url: URL of the static (JPEG or GIF) or animated (MPEG4)
            thumbnail for the result
        gif_width: Optional. Width of the GIF
        gif_height: Optional. Height of the GIF
        gif_duration: Optional. Duration of the GIF
        thumb_mime_type: Optional. MIME type of the thumbnail, must be one
            of “image/jpeg”, “image/gif”, or “video/mp4”. Defaults to
            “image/jpeg”
        title: Optional. Title for the result
        caption: Optional. Caption of the GIF file to be sent, 0-1024
            characters after entities parsing
        parse_mode: Optional. Mode for parsing entities in the caption. See
            formatting options for more details.
        caption_entities: Optional. List of special entities that appear in
            the caption, which can be specified instead of parse_mode
        reply_markup: Optional. Inline keyboard attached to the message
        input_message_content: Optional. Content of the message to be sent
            instead of the GIF animation

    """

    type: str
    id: str
    gif_url: str
    thumb_url: str
    gif_width: int = None
    gif_height: int = None
    gif_duration: int = None
    thumb_mime_type: str = None
    title: str = None
    caption: str = None
    parse_mode: str = None
    caption_entities: List[MessageEntity] = None
    reply_markup: InlineKeyboardMarkup = None
    input_message_content: Union[
        InputTextMessageContent,
        InputLocationMessageContent,
        InputVenueMessageContent,
        InputContactMessageContent,
    ] = None


@dataclass(eq=True)
class InlineQueryResultMpeg4Gif(TelegramType):
    """
    Represents a link to a video animation (H.264/MPEG-4 AVC video without
    sound). By default, this animated MPEG-4 file will be sent by the user
    with optional caption. Alternatively, you can use input_message_content to
    send a message with the specified content instead of the animation.

    https://core.telegram.org/bots/api/#inlinequeryresultmpeg4gif

    Attributes:
        type: Type of the result, must be mpeg4_gif
        id: Unique identifier for this result, 1-64 bytes
        mpeg4_url: A valid URL for the MP4 file. File size must not exceed
            1MB
        thumb_url: URL of the static (JPEG or GIF) or animated (MPEG4)
            thumbnail for the result
        mpeg4_width: Optional. Video width
        mpeg4_height: Optional. Video height
        mpeg4_duration: Optional. Video duration
        thumb_mime_type: Optional. MIME type of the thumbnail, must be one
            of “image/jpeg”, “image/gif”, or “video/mp4”. Defaults to
            “image/jpeg”
        title: Optional. Title for the result
        caption: Optional. Caption of the MPEG-4 file to be sent, 0-1024
            characters after entities parsing
        parse_mode: Optional. Mode for parsing entities in the caption. See
            formatting options for more details.
        caption_entities: Optional. List of special entities that appear in
            the caption, which can be specified instead of parse_mode
        reply_markup: Optional. Inline keyboard attached to the message
        input_message_content: Optional. Content of the message to be sent
            instead of the video animation

    """

    type: str
    id: str
    mpeg4_url: str
    thumb_url: str
    mpeg4_width: int = None
    mpeg4_height: int = None
    mpeg4_duration: int = None
    thumb_mime_type: str = None
    title: str = None
    caption: str = None
    parse_mode: str = None
    caption_entities: List[MessageEntity] = None
    reply_markup: InlineKeyboardMarkup = None
    input_message_content: Union[
        InputTextMessageContent,
        InputLocationMessageContent,
        InputVenueMessageContent,
        InputContactMessageContent,
    ] = None


@dataclass(eq=True)
class InlineQueryResultVideo(TelegramType):
    """
    Represents a link to a page containing an embedded video player or a video
    file. By default, this video file will be sent by the user with an
    optional caption. Alternatively, you can use input_message_content to send
    a message with the specified content instead of the video.

    If an InlineQueryResultVideo message contains an embedded video (e.g.,
    YouTube), you must replace its content using input_message_content.

    https://core.telegram.org/bots/api/#inlinequeryresultvideo

    Attributes:
        type: Type of the result, must be video
        id: Unique identifier for this result, 1-64 bytes
        video_url: A valid URL for the embedded video player or video file
        mime_type: Mime type of the content of video url, “text/html” or
            “video/mp4”
        thumb_url: URL of the thumbnail (jpeg only) for the video
        title: Title for the result
        caption: Optional. Caption of the video to be sent, 0-1024
            characters after entities parsing
        parse_mode: Optional. Mode for parsing entities in the video
            caption. See formatting options for more details.
        caption_entities: Optional. List of special entities that appear in
            the caption, which can be specified instead of parse_mode
        video_width: Optional. Video width
        video_height: Optional. Video height
        video_duration: Optional. Video duration in seconds
        description: Optional. Short description of the result
        reply_markup: Optional. Inline keyboard attached to the message
        input_message_content: Optional. Content of the message to be sent
            instead of the video. This field is required if
            InlineQueryResultVideo is used to send an HTML-page as a result
            (e.g., a YouTube video).

    """

    type: str
    id: str
    video_url: str
    mime_type: str
    thumb_url: str
    title: str
    caption: str = None
    parse_mode: str = None
    caption_entities: List[MessageEntity] = None
    video_width: int = None
    video_height: int = None
    video_duration: int = None
    description: str = None
    reply_markup: InlineKeyboardMarkup = None
    input_message_content: Union[
        InputTextMessageContent,
        InputLocationMessageContent,
        InputVenueMessageContent,
        InputContactMessageContent,
    ] = None


@dataclass(eq=True)
class InlineQueryResultAudio(TelegramType):
    """
    Represents a link to an MP3 audio file. By default, this audio file will
    be sent by the user. Alternatively, you can use input_message_content to
    send a message with the specified content instead of the audio.

    https://core.telegram.org/bots/api/#inlinequeryresultaudio

    Attributes:
        type: Type of the result, must be audio
        id: Unique identifier for this result, 1-64 bytes
        audio_url: A valid URL for the audio file
        title: Title
        caption: Optional. Caption, 0-1024 characters after entities
            parsing
        parse_mode: Optional. Mode for parsing entities in the audio
            caption. See formatting options for more details.
        caption_entities: Optional. List of special entities that appear in
            the caption, which can be specified instead of parse_mode
        performer: Optional. Performer
        audio_duration: Optional. Audio duration in seconds
        reply_markup: Optional. Inline keyboard attached to the message
        input_message_content: Optional. Content of the message to be sent
            instead of the audio

    """

    type: str
    id: str
    audio_url: str
    title: str
    caption: str = None
    parse_mode: str = None
    caption_entities: List[MessageEntity] = None
    performer: str = None
    audio_duration: int = None
    reply_markup: InlineKeyboardMarkup = None
    input_message_content: Union[
        InputTextMessageContent,
        InputLocationMessageContent,
        InputVenueMessageContent,
        InputContactMessageContent,
    ] = None


@dataclass(eq=True)
class InlineQueryResultVoice(TelegramType):
    """
    Represents a link to a voice recording in an .OGG container encoded with
    OPUS. By default, this voice recording will be sent by the user.
    Alternatively, you can use input_message_content to send a message with
    the specified content instead of the the voice message.

    https://core.telegram.org/bots/api/#inlinequeryresultvoice

    Attributes:
        type: Type of the result, must be voice
        id: Unique identifier for this result, 1-64 bytes
        voice_url: A valid URL for the voice recording
        title: Recording title
        caption: Optional. Caption, 0-1024 characters after entities
            parsing
        parse_mode: Optional. Mode for parsing entities in the voice
            message caption. See formatting options for more details.
        caption_entities: Optional. List of special entities that appear in
            the caption, which can be specified instead of parse_mode
        voice_duration: Optional. Recording duration in seconds
        reply_markup: Optional. Inline keyboard attached to the message
        input_message_content: Optional. Content of the message to be sent
            instead of the voice recording

    """

    type: str
    id: str
    voice_url: str
    title: str
    caption: str = None
    parse_mode: str = None
    caption_entities: List[MessageEntity] = None
    voice_duration: int = None
    reply_markup: InlineKeyboardMarkup = None
    input_message_content: Union[
        InputTextMessageContent,
        InputLocationMessageContent,
        InputVenueMessageContent,
        InputContactMessageContent,
    ] = None


@dataclass(eq=True)
class InlineQueryResultDocument(TelegramType):
    """
    Represents a link to a file. By default, this file will be sent by the
    user with an optional caption. Alternatively, you can use
    input_message_content to send a message with the specified content instead
    of the file. Currently, only .PDF and .ZIP files can be sent using this
    method.

    https://core.telegram.org/bots/api/#inlinequeryresultdocument

    Attributes:
        type: Type of the result, must be document
        id: Unique identifier for this result, 1-64 bytes
        title: Title for the result
        document_url: A valid URL for the file
        mime_type: Mime type of the content of the file, either
            “application/pdf” or “application/zip”
        caption: Optional. Caption of the document to be sent, 0-1024
            characters after entities parsing
        parse_mode: Optional. Mode for parsing entities in the document
            caption. See formatting options for more details.
        caption_entities: Optional. List of special entities that appear in
            the caption, which can be specified instead of parse_mode
        description: Optional. Short description of the result
        reply_markup: Optional. Inline keyboard attached to the message
        input_message_content: Optional. Content of the message to be sent
            instead of the file
        thumb_url: Optional. URL of the thumbnail (jpeg only) for the file
        thumb_width: Optional. Thumbnail width
        thumb_height: Optional. Thumbnail height

    """

    type: str
    id: str
    title: str
    document_url: str
    mime_type: str
    caption: str = None
    parse_mode: str = None
    caption_entities: List[MessageEntity] = None
    description: str = None
    reply_markup: InlineKeyboardMarkup = None
    input_message_content: Union[
        InputTextMessageContent,
        InputLocationMessageContent,
        InputVenueMessageContent,
        InputContactMessageContent,
    ] = None
    thumb_url: str = None
    thumb_width: int = None
    thumb_height: int = None


@dataclass(eq=True)
class InlineQueryResultLocation(TelegramType):
    """
    Represents a location on a map. By default, the location will be sent by
    the user. Alternatively, you can use input_message_content to send a
    message with the specified content instead of the location.

    https://core.telegram.org/bots/api/#inlinequeryresultlocation

    Attributes:
        type: Type of the result, must be location
        id: Unique identifier for this result, 1-64 Bytes
        latitude: Location latitude in degrees
        longitude: Location longitude in degrees
        title: Location title
        horizontal_accuracy: Optional. The radius of uncertainty for the
            location, measured in meters; 0-1500
        live_period: Optional. Period in seconds for which the location can
            be updated, should be between 60 and 86400.
        heading: Optional. For live locations, a direction in which the
            user is moving, in degrees. Must be between 1 and 360 if
            specified.
        proximity_alert_radius: Optional. For live locations, a maximum
            distance for proximity alerts about approaching another chat
            member, in meters. Must be between 1 and 100000 if specified.
        reply_markup: Optional. Inline keyboard attached to the message
        input_message_content: Optional. Content of the message to be sent
            instead of the location
        thumb_url: Optional. Url of the thumbnail for the result
        thumb_width: Optional. Thumbnail width
        thumb_height: Optional. Thumbnail height

    """

    type: str
    id: str
    latitude: float
    longitude: float
    title: str
    horizontal_accuracy: float = None
    live_period: int = None
    heading: int = None
    proximity_alert_radius: int = None
    reply_markup: InlineKeyboardMarkup = None
    input_message_content: Union[
        InputTextMessageContent,
        InputLocationMessageContent,
        InputVenueMessageContent,
        InputContactMessageContent,
    ] = None
    thumb_url: str = None
    thumb_width: int = None
    thumb_height: int = None


@dataclass(eq=True)
class InlineQueryResultVenue(TelegramType):
    """
    Represents a venue. By default, the venue will be sent by the user.
    Alternatively, you can use input_message_content to send a message with
    the specified content instead of the venue.

    https://core.telegram.org/bots/api/#inlinequeryresultvenue

    Attributes:
        type: Type of the result, must be venue
        id: Unique identifier for this result, 1-64 Bytes
        latitude: Latitude of the venue location in degrees
        longitude: Longitude of the venue location in degrees
        title: Title of the venue
        address: Address of the venue
        foursquare_id: Optional. Foursquare identifier of the venue if
            known
        foursquare_type: Optional. Foursquare type of the venue, if known.
            (For example, “arts_entertainment/default”,
            “arts_entertainment/aquarium” or “food/icecream”.)
        google_place_id: Optional. Google Places identifier of the venue
        google_place_type: Optional. Google Places type of the venue. (See
            supported types.)
        reply_markup: Optional. Inline keyboard attached to the message
        input_message_content: Optional. Content of the message to be sent
            instead of the venue
        thumb_url: Optional. Url of the thumbnail for the result
        thumb_width: Optional. Thumbnail width
        thumb_height: Optional. Thumbnail height

    """

    type: str
    id: str
    latitude: float
    longitude: float
    title: str
    address: str
    foursquare_id: str = None
    foursquare_type: str = None
    google_place_id: str = None
    google_place_type: str = None
    reply_markup: InlineKeyboardMarkup = None
    input_message_content: Union[
        InputTextMessageContent,
        InputLocationMessageContent,
        InputVenueMessageContent,
        InputContactMessageContent,
    ] = None
    thumb_url: str = None
    thumb_width: int = None
    thumb_height: int = None


@dataclass(eq=True)
class InlineQueryResultContact(TelegramType):
    """
    Represents a contact with a phone number. By default, this contact will be
    sent by the user. Alternatively, you can use input_message_content to send
    a message with the specified content instead of the contact.

    https://core.telegram.org/bots/api/#inlinequeryresultcontact

    Attributes:
        type: Type of the result, must be contact
        id: Unique identifier for this result, 1-64 Bytes
        phone_number: Contact's phone number
        first_name: Contact's first name
        last_name: Optional. Contact's last name
        vcard: Optional. Additional data about the contact in the form of a
            vCard, 0-2048 bytes
        reply_markup: Optional. Inline keyboard attached to the message
        input_message_content: Optional. Content of the message to be sent
            instead of the contact
        thumb_url: Optional. Url of the thumbnail for the result
        thumb_width: Optional. Thumbnail width
        thumb_height: Optional. Thumbnail height

    """

    type: str
    id: str
    phone_number: str
    first_name: str
    last_name: str = None
    vcard: str = None
    reply_markup: InlineKeyboardMarkup = None
    input_message_content: Union[
        InputTextMessageContent,
        InputLocationMessageContent,
        InputVenueMessageContent,
        InputContactMessageContent,
    ] = None
    thumb_url: str = None
    thumb_width: int = None
    thumb_height: int = None


@dataclass(eq=True)
class InlineQueryResultGame(TelegramType):
    """
    Represents a Game.

    https://core.telegram.org/bots/api/#inlinequeryresultgame

    Attributes:
        type: Type of the result, must be game
        id: Unique identifier for this result, 1-64 bytes
        game_short_name: Short name of the game
        reply_markup: Optional. Inline keyboard attached to the message

    """

    type: str
    id: str
    game_short_name: str
    reply_markup: InlineKeyboardMarkup = None


@dataclass(eq=True)
class InlineQueryResultCachedPhoto(TelegramType):
    """
    Represents a link to a photo stored on the Telegram servers. By default,
    this photo will be sent by the user with an optional caption.
    Alternatively, you can use input_message_content to send a message with
    the specified content instead of the photo.

    https://core.telegram.org/bots/api/#inlinequeryresultcachedphoto

    Attributes:
        type: Type of the result, must be photo
        id: Unique identifier for this result, 1-64 bytes
        photo_file_id: A valid file identifier of the photo
        title: Optional. Title for the result
        description: Optional. Short description of the result
        caption: Optional. Caption of the photo to be sent, 0-1024
            characters after entities parsing
        parse_mode: Optional. Mode for parsing entities in the photo
            caption. See formatting options for more details.
        caption_entities: Optional. List of special entities that appear in
            the caption, which can be specified instead of parse_mode
        reply_markup: Optional. Inline keyboard attached to the message
        input_message_content: Optional. Content of the message to be sent
            instead of the photo

    """

    type: str
    id: str
    photo_file_id: str
    title: str = None
    description: str = None
    caption: str = None
    parse_mode: str = None
    caption_entities: List[MessageEntity] = None
    reply_markup: InlineKeyboardMarkup = None
    input_message_content: Union[
        InputTextMessageContent,
        InputLocationMessageContent,
        InputVenueMessageContent,
        InputContactMessageContent,
    ] = None


@dataclass(eq=True)
class InlineQueryResultCachedGif(TelegramType):
    """
    Represents a link to an animated GIF file stored on the Telegram servers.
    By default, this animated GIF file will be sent by the user with an
    optional caption. Alternatively, you can use input_message_content to send
    a message with specified content instead of the animation.

    https://core.telegram.org/bots/api/#inlinequeryresultcachedgif

    Attributes:
        type: Type of the result, must be gif
        id: Unique identifier for this result, 1-64 bytes
        gif_file_id: A valid file identifier for the GIF file
        title: Optional. Title for the result
        caption: Optional. Caption of the GIF file to be sent, 0-1024
            characters after entities parsing
        parse_mode: Optional. Mode for parsing entities in the caption. See
            formatting options for more details.
        caption_entities: Optional. List of special entities that appear in
            the caption, which can be specified instead of parse_mode
        reply_markup: Optional. Inline keyboard attached to the message
        input_message_content: Optional. Content of the message to be sent
            instead of the GIF animation

    """

    type: str
    id: str
    gif_file_id: str
    title: str = None
    caption: str = None
    parse_mode: str = None
    caption_entities: List[MessageEntity] = None
    reply_markup: InlineKeyboardMarkup = None
    input_message_content: Union[
        InputTextMessageContent,
        InputLocationMessageContent,
        InputVenueMessageContent,
        InputContactMessageContent,
    ] = None


@dataclass(eq=True)
class InlineQueryResultCachedMpeg4Gif(TelegramType):
    """
    Represents a link to a video animation (H.264/MPEG-4 AVC video without
    sound) stored on the Telegram servers. By default, this animated MPEG-4
    file will be sent by the user with an optional caption. Alternatively, you
    can use input_message_content to send a message with the specified content
    instead of the animation.

    https://core.telegram.org/bots/api/#inlinequeryresultcachedmpeg4gif

    Attributes:
        type: Type of the result, must be mpeg4_gif
        id: Unique identifier for this result, 1-64 bytes
        mpeg4_file_id: A valid file identifier for the MP4 file
        title: Optional. Title for the result
        caption: Optional. Caption of the MPEG-4 file to be sent, 0-1024
            characters after entities parsing
        parse_mode: Optional. Mode for parsing entities in the caption. See
            formatting options for more details.
        caption_entities: Optional. List of special entities that appear in
            the caption, which can be specified instead of parse_mode
        reply_markup: Optional. Inline keyboard attached to the message
        input_message_content: Optional. Content of the message to be sent
            instead of the video animation

    """

    type: str
    id: str
    mpeg4_file_id: str
    title: str = None
    caption: str = None
    parse_mode: str = None
    caption_entities: List[MessageEntity] = None
    reply_markup: InlineKeyboardMarkup = None
    input_message_content: Union[
        InputTextMessageContent,
        InputLocationMessageContent,
        InputVenueMessageContent,
        InputContactMessageContent,
    ] = None


@dataclass(eq=True)
class InlineQueryResultCachedSticker(TelegramType):
    """
    Represents a link to a sticker stored on the Telegram servers. By default,
    this sticker will be sent by the user. Alternatively, you can use
    input_message_content to send a message with the specified content instead
    of the sticker.

    https://core.telegram.org/bots/api/#inlinequeryresultcachedsticker

    Attributes:
        type: Type of the result, must be sticker
        id: Unique identifier for this result, 1-64 bytes
        sticker_file_id: A valid file identifier of the sticker
        reply_markup: Optional. Inline keyboard attached to the message
        input_message_content: Optional. Content of the message to be sent
            instead of the sticker

    """

    type: str
    id: str
    sticker_file_id: str
    reply_markup: InlineKeyboardMarkup = None
    input_message_content: Union[
        InputTextMessageContent,
        InputLocationMessageContent,
        InputVenueMessageContent,
        InputContactMessageContent,
    ] = None


@dataclass(eq=True)
class InlineQueryResultCachedDocument(TelegramType):
    """
    Represents a link to a file stored on the Telegram servers. By default,
    this file will be sent by the user with an optional caption.
    Alternatively, you can use input_message_content to send a message with
    the specified content instead of the file.

    https://core.telegram.org/bots/api/#inlinequeryresultcacheddocument

    Attributes:
        type: Type of the result, must be document
        id: Unique identifier for this result, 1-64 bytes
        title: Title for the result
        document_file_id: A valid file identifier for the file
        description: Optional. Short description of the result
        caption: Optional. Caption of the document to be sent, 0-1024
            characters after entities parsing
        parse_mode: Optional. Mode for parsing entities in the document
            caption. See formatting options for more details.
        caption_entities: Optional. List of special entities that appear in
            the caption, which can be specified instead of parse_mode
        reply_markup: Optional. Inline keyboard attached to the message
        input_message_content: Optional. Content of the message to be sent
            instead of the file

    """

    type: str
    id: str
    title: str
    document_file_id: str
    description: str = None
    caption: str = None
    parse_mode: str = None
    caption_entities: List[MessageEntity] = None
    reply_markup: InlineKeyboardMarkup = None
    input_message_content: Union[
        InputTextMessageContent,
        InputLocationMessageContent,
        InputVenueMessageContent,
        InputContactMessageContent,
    ] = None


@dataclass(eq=True)
class InlineQueryResultCachedVideo(TelegramType):
    """
    Represents a link to a video file stored on the Telegram servers. By
    default, this video file will be sent by the user with an optional
    caption. Alternatively, you can use input_message_content to send a
    message with the specified content instead of the video.

    https://core.telegram.org/bots/api/#inlinequeryresultcachedvideo

    Attributes:
        type: Type of the result, must be video
        id: Unique identifier for this result, 1-64 bytes
        video_file_id: A valid file identifier for the video file
        title: Title for the result
        description: Optional. Short description of the result
        caption: Optional. Caption of the video to be sent, 0-1024
            characters after entities parsing
        parse_mode: Optional. Mode for parsing entities in the video
            caption. See formatting options for more details.
        caption_entities: Optional. List of special entities that appear in
            the caption, which can be specified instead of parse_mode
        reply_markup: Optional. Inline keyboard attached to the message
        input_message_content: Optional. Content of the message to be sent
            instead of the video

    """

    type: str
    id: str
    video_file_id: str
    title: str
    description: str = None
    caption: str = None
    parse_mode: str = None
    caption_entities: List[MessageEntity] = None
    reply_markup: InlineKeyboardMarkup = None
    input_message_content: Union[
        InputTextMessageContent,
        InputLocationMessageContent,
        InputVenueMessageContent,
        InputContactMessageContent,
    ] = None


@dataclass(eq=True)
class InlineQueryResultCachedVoice(TelegramType):
    """
    Represents a link to a voice message stored on the Telegram servers. By
    default, this voice message will be sent by the user. Alternatively, you
    can use input_message_content to send a message with the specified content
    instead of the voice message.

    https://core.telegram.org/bots/api/#inlinequeryresultcachedvoice

    Attributes:
        type: Type of the result, must be voice
        id: Unique identifier for this result, 1-64 bytes
        voice_file_id: A valid file identifier for the voice message
        title: Voice message title
        caption: Optional. Caption, 0-1024 characters after entities
            parsing
        parse_mode: Optional. Mode for parsing entities in the voice
            message caption. See formatting options for more details.
        caption_entities: Optional. List of special entities that appear in
            the caption, which can be specified instead of parse_mode
        reply_markup: Optional. Inline keyboard attached to the message
        input_message_content: Optional. Content of the message to be sent
            instead of the voice message

    """

    type: str
    id: str
    voice_file_id: str
    title: str
    caption: str = None
    parse_mode: str = None
    caption_entities: List[MessageEntity] = None
    reply_markup: InlineKeyboardMarkup = None
    input_message_content: Union[
        InputTextMessageContent,
        InputLocationMessageContent,
        InputVenueMessageContent,
        InputContactMessageContent,
    ] = None


@dataclass(eq=True)
class InlineQueryResultCachedAudio(TelegramType):
    """
    Represents a link to an MP3 audio file stored on the Telegram servers. By
    default, this audio file will be sent by the user. Alternatively, you can
    use input_message_content to send a message with the specified content
    instead of the audio.

    https://core.telegram.org/bots/api/#inlinequeryresultcachedaudio

    Attributes:
        type: Type of the result, must be audio
        id: Unique identifier for this result, 1-64 bytes
        audio_file_id: A valid file identifier for the audio file
        caption: Optional. Caption, 0-1024 characters after entities
            parsing
        parse_mode: Optional. Mode for parsing entities in the audio
            caption. See formatting options for more details.
        caption_entities: Optional. List of special entities that appear in
            the caption, which can be specified instead of parse_mode
        reply_markup: Optional. Inline keyboard attached to the message
        input_message_content: Optional. Content of the message to be sent
            instead of the audio

    """

    type: str
    id: str
    audio_file_id: str
    caption: str = None
    parse_mode: str = None
    caption_entities: List[MessageEntity] = None
    reply_markup: InlineKeyboardMarkup = None
    input_message_content: Union[
        InputTextMessageContent,
        InputLocationMessageContent,
        InputVenueMessageContent,
        InputContactMessageContent,
    ] = None


@dataclass(eq=True)
class InputTextMessageContent(TelegramType):
    """
    Represents the content of a text message to be sent as the result of an
    inline query.

    https://core.telegram.org/bots/api/#inputtextmessagecontent

    Attributes:
        message_text: Text of the message to be sent, 1-4096 characters
        parse_mode: Optional. Mode for parsing entities in the message
            text. See formatting options for more details.
        entities: Optional. List of special entities that appear in message
            text, which can be specified instead of parse_mode
        disable_web_page_preview: Optional. Disables link previews for
            links in the sent message

    """

    message_text: str
    parse_mode: str = None
    entities: List[MessageEntity] = None
    disable_web_page_preview: bool = None


@dataclass(eq=True)
class InputLocationMessageContent(TelegramType):
    """
    Represents the content of a location message to be sent as the result of
    an inline query.

    https://core.telegram.org/bots/api/#inputlocationmessagecontent

    Attributes:
        latitude: Latitude of the location in degrees
        longitude: Longitude of the location in degrees
        horizontal_accuracy: Optional. The radius of uncertainty for the
            location, measured in meters; 0-1500
        live_period: Optional. Period in seconds for which the location can
            be updated, should be between 60 and 86400.
        heading: Optional. For live locations, a direction in which the
            user is moving, in degrees. Must be between 1 and 360 if
            specified.
        proximity_alert_radius: Optional. For live locations, a maximum
            distance for proximity alerts about approaching another chat
            member, in meters. Must be between 1 and 100000 if specified.

    """

    latitude: float
    longitude: float
    horizontal_accuracy: float = None
    live_period: int = None
    heading: int = None
    proximity_alert_radius: int = None


@dataclass(eq=True)
class InputVenueMessageContent(TelegramType):
    """
    Represents the content of a venue message to be sent as the result of an
    inline query.

    https://core.telegram.org/bots/api/#inputvenuemessagecontent

    Attributes:
        latitude: Latitude of the venue in degrees
        longitude: Longitude of the venue in degrees
        title: Name of the venue
        address: Address of the venue
        foursquare_id: Optional. Foursquare identifier of the venue, if
            known
        foursquare_type: Optional. Foursquare type of the venue, if known.
            (For example, “arts_entertainment/default”,
            “arts_entertainment/aquarium” or “food/icecream”.)
        google_place_id: Optional. Google Places identifier of the venue
        google_place_type: Optional. Google Places type of the venue. (See
            supported types.)

    """

    latitude: float
    longitude: float
    title: str
    address: str
    foursquare_id: str = None
    foursquare_type: str = None
    google_place_id: str = None
    google_place_type: str = None


@dataclass(eq=True)
class InputContactMessageContent(TelegramType):
    """
    Represents the content of a contact message to be sent as the result of an
    inline query.

    https://core.telegram.org/bots/api/#inputcontactmessagecontent

    Attributes:
        phone_number: Contact's phone number
        first_name: Contact's first name
        last_name: Optional. Contact's last name
        vcard: Optional. Additional data about the contact in the form of a
            vCard, 0-2048 bytes

    """

    phone_number: str
    first_name: str
    last_name: str = None
    vcard: str = None


@dataclass(eq=True)
class ChosenInlineResult(TelegramType):
    """
    Represents a result of an inline query that was chosen by the user and
    sent to their chat partner.

    https://core.telegram.org/bots/api/#choseninlineresult

    Attributes:
        result_id: The unique identifier for the result that was chosen
        from_user: The user that chose the result
        query: The query that was used to obtain the result
        location: Optional. Sender location, only for bots that require
            user location
        inline_message_id: Optional. Identifier of the sent inline message.
            Available only if there is an inline keyboard attached to the
            message. Will be also received in callback queries and can be used
            to edit the message.

    """

    result_id: str
    from_user: User
    query: str
    location: Location = None
    inline_message_id: str = None


@dataclass(eq=True)
class LabeledPrice(TelegramType):
    """
    This object represents a portion of the price for goods or services.

    https://core.telegram.org/bots/api/#labeledprice

    Attributes:
        label: Portion label
        amount: Price of the product in the smallest units of the currency
            (integer, not float/double). For example, for a price of US$ 1.45
            pass amount = 145. See the exp parameter in currencies.json, it
            shows the number of digits past the decimal point for each
            currency (2 for the majority of currencies).

    """

    label: str
    amount: int


@dataclass(eq=True)
class Invoice(TelegramType):
    """
    This object contains basic information about an invoice.

    https://core.telegram.org/bots/api/#invoice

    Attributes:
        title: Product name
        description: Product description
        start_parameter: Unique bot deep-linking parameter that can be used
            to generate this invoice
        currency: Three-letter ISO 4217 currency code
        total_amount: Total price in the smallest units of the currency
            (integer, not float/double). For example, for a price of US$ 1.45
            pass amount = 145. See the exp parameter in currencies.json, it
            shows the number of digits past the decimal point for each
            currency (2 for the majority of currencies).

    """

    title: str
    description: str
    start_parameter: str
    currency: str
    total_amount: int


@dataclass(eq=True)
class ShippingAddress(TelegramType):
    """
    This object represents a shipping address.

    https://core.telegram.org/bots/api/#shippingaddress

    Attributes:
        country_code: ISO 3166-1 alpha-2 country code
        state: State, if applicable
        city: City
        street_line1: First line for the address
        street_line2: Second line for the address
        post_code: Address post code

    """

    country_code: str
    state: str
    city: str
    street_line1: str
    street_line2: str
    post_code: str


@dataclass(eq=True)
class OrderInfo(TelegramType):
    """
    This object represents information about an order.

    https://core.telegram.org/bots/api/#orderinfo

    Attributes:
        name: Optional. User name
        phone_number: Optional. User's phone number
        email: Optional. User email
        shipping_address: Optional. User shipping address

    """

    name: str = None
    phone_number: str = None
    email: str = None
    shipping_address: ShippingAddress = None


@dataclass(eq=True)
class ShippingOption(TelegramType):
    """
    This object represents one shipping option.

    https://core.telegram.org/bots/api/#shippingoption

    Attributes:
        id: Shipping option identifier
        title: Option title
        prices: List of price portions

    """

    id: str
    title: str
    prices: List[LabeledPrice]


@dataclass(eq=True)
class SuccessfulPayment(TelegramType):
    """
    This object contains basic information about a successful payment.

    https://core.telegram.org/bots/api/#successfulpayment

    Attributes:
        currency: Three-letter ISO 4217 currency code
        total_amount: Total price in the smallest units of the currency
            (integer, not float/double). For example, for a price of US$ 1.45
            pass amount = 145. See the exp parameter in currencies.json, it
            shows the number of digits past the decimal point for each
            currency (2 for the majority of currencies).
        invoice_payload: Bot specified invoice payload
        telegram_payment_charge_id: Telegram payment identifier
        provider_payment_charge_id: Provider payment identifier
        shipping_option_id: Optional. Identifier of the shipping option
            chosen by the user
        order_info: Optional. Order info provided by the user

    """

    currency: str
    total_amount: int
    invoice_payload: str
    telegram_payment_charge_id: str
    provider_payment_charge_id: str
    shipping_option_id: str = None
    order_info: OrderInfo = None


@dataclass(eq=True)
class ShippingQuery(TelegramType):
    """
    This object contains information about an incoming shipping query.

    https://core.telegram.org/bots/api/#shippingquery

    Attributes:
        id: Unique query identifier
        from_user: User who sent the query
        invoice_payload: Bot specified invoice payload
        shipping_address: User specified shipping address

    """

    id: str
    from_user: User
    invoice_payload: str
    shipping_address: ShippingAddress


@dataclass(eq=True)
class PreCheckoutQuery(TelegramType):
    """
    This object contains information about an incoming pre-checkout query.

    https://core.telegram.org/bots/api/#precheckoutquery

    Attributes:
        id: Unique query identifier
        from_user: User who sent the query
        currency: Three-letter ISO 4217 currency code
        total_amount: Total price in the smallest units of the currency
            (integer, not float/double). For example, for a price of US$ 1.45
            pass amount = 145. See the exp parameter in currencies.json, it
            shows the number of digits past the decimal point for each
            currency (2 for the majority of currencies).
        invoice_payload: Bot specified invoice payload
        shipping_option_id: Optional. Identifier of the shipping option
            chosen by the user
        order_info: Optional. Order info provided by the user

    """

    id: str
    from_user: User
    currency: str
    total_amount: int
    invoice_payload: str
    shipping_option_id: str = None
    order_info: OrderInfo = None


@dataclass(eq=True)
class PassportData(TelegramType):
    """
    Contains information about Telegram Passport data shared with the bot by
    the user.

    https://core.telegram.org/bots/api/#passportdata

    Attributes:
        data: Array with information about documents and other Telegram
            Passport elements that was shared with the bot
        credentials: Encrypted credentials required to decrypt the data

    """

    data: List[EncryptedPassportElement]
    credentials: EncryptedCredentials


@dataclass(eq=True)
class PassportFile(TelegramType):
    """
    This object represents a file uploaded to Telegram Passport. Currently all
    Telegram Passport files are in JPEG format when decrypted and don't exceed
    10MB.

    https://core.telegram.org/bots/api/#passportfile

    Attributes:
        file_id: Identifier for this file, which can be used to download or
            reuse the file
        file_unique_id: Unique identifier for this file, which is supposed
            to be the same over time and for different bots. Can't be used to
            download or reuse the file.
        file_size: File size
        file_date: Unix time when the file was uploaded

    """

    file_id: str
    file_unique_id: str
    file_size: int
    file_date: datetime


@dataclass(eq=True)
class EncryptedPassportElement(TelegramType):
    """
    Contains information about documents or other Telegram Passport elements
    shared with the bot by the user.

    https://core.telegram.org/bots/api/#encryptedpassportelement

    Attributes:
        type: Element type. One of “personal_details”, “passport”,
            “driver_license”, “identity_card”, “internal_passport”, “address”,
            “utility_bill”, “bank_statement”, “rental_agreement”,
            “passport_registration”, “temporary_registration”, “phone_number”,
            “email”.
        hash: Base64-encoded element hash for using in
            PassportElementErrorUnspecified
        data: Optional. Base64-encoded encrypted Telegram Passport element
            data provided by the user, available for “personal_details”,
            “passport”, “driver_license”, “identity_card”, “internal_passport”
            and “address” types. Can be decrypted and verified using the
            accompanying EncryptedCredentials.
        phone_number: Optional. User's verified phone number, available
            only for “phone_number” type
        email: Optional. User's verified email address, available only for
            “email” type
        files: Optional. Array of encrypted files with documents provided
            by the user, available for “utility_bill”, “bank_statement”,
            “rental_agreement”, “passport_registration” and
            “temporary_registration” types. Files can be decrypted and
            verified using the accompanying EncryptedCredentials.
        front_side: Optional. Encrypted file with the front side of the
            document, provided by the user. Available for “passport”,
            “driver_license”, “identity_card” and “internal_passport”. The
            file can be decrypted and verified using the accompanying
            EncryptedCredentials.
        reverse_side: Optional. Encrypted file with the reverse side of the
            document, provided by the user. Available for “driver_license” and
            “identity_card”. The file can be decrypted and verified using the
            accompanying EncryptedCredentials.
        selfie: Optional. Encrypted file with the selfie of the user
            holding a document, provided by the user; available for
            “passport”, “driver_license”, “identity_card” and
            “internal_passport”. The file can be decrypted and verified using
            the accompanying EncryptedCredentials.
        translation: Optional. Array of encrypted files with translated
            versions of documents provided by the user. Available if requested
            for “passport”, “driver_license”, “identity_card”,
            “internal_passport”, “utility_bill”, “bank_statement”,
            “rental_agreement”, “passport_registration” and
            “temporary_registration” types. Files can be decrypted and
            verified using the accompanying EncryptedCredentials.

    """

    type: str
    hash: str
    data: str = None
    phone_number: str = None
    email: str = None
    files: List[PassportFile] = None
    front_side: PassportFile = None
    reverse_side: PassportFile = None
    selfie: PassportFile = None
    translation: List[PassportFile] = None


@dataclass(eq=True)
class EncryptedCredentials(TelegramType):
    """
    Contains data required for decrypting and authenticating
    EncryptedPassportElement. See the Telegram Passport Documentation for a
    complete description of the data decryption and authentication processes.

    https://core.telegram.org/bots/api/#encryptedcredentials

    Attributes:
        data: Base64-encoded encrypted JSON-serialized data with unique
            user's payload, data hashes and secrets required for
            EncryptedPassportElement decryption and authentication
        hash: Base64-encoded data hash for data authentication
        secret: Base64-encoded secret, encrypted with the bot's public RSA
            key, required for data decryption

    """

    data: str
    hash: str
    secret: str


@dataclass(eq=True)
class PassportElementErrorDataField(TelegramType):
    """
    Represents an issue in one of the data fields that was provided by the
    user. The error is considered resolved when the field's value changes.

    https://core.telegram.org/bots/api/#passportelementerrordatafield

    Attributes:
        source: Error source, must be data
        type: The section of the user's Telegram Passport which has the
            error, one of “personal_details”, “passport”, “driver_license”,
            “identity_card”, “internal_passport”, “address”
        field_name: Name of the data field which has the error
        data_hash: Base64-encoded data hash
        message: Error message

    """

    source: str
    type: str
    field_name: str
    data_hash: str
    message: str


@dataclass(eq=True)
class PassportElementErrorFrontSide(TelegramType):
    """
    Represents an issue with the front side of a document. The error is
    considered resolved when the file with the front side of the document
    changes.

    https://core.telegram.org/bots/api/#passportelementerrorfrontside

    Attributes:
        source: Error source, must be front_side
        type: The section of the user's Telegram Passport which has the
            issue, one of “passport”, “driver_license”, “identity_card”,
            “internal_passport”
        file_hash: Base64-encoded hash of the file with the front side of
            the document
        message: Error message

    """

    source: str
    type: str
    file_hash: str
    message: str


@dataclass(eq=True)
class PassportElementErrorReverseSide(TelegramType):
    """
    Represents an issue with the reverse side of a document. The error is
    considered resolved when the file with reverse side of the document
    changes.

    https://core.telegram.org/bots/api/#passportelementerrorreverseside

    Attributes:
        source: Error source, must be reverse_side
        type: The section of the user's Telegram Passport which has the
            issue, one of “driver_license”, “identity_card”
        file_hash: Base64-encoded hash of the file with the reverse side of
            the document
        message: Error message

    """

    source: str
    type: str
    file_hash: str
    message: str


@dataclass(eq=True)
class PassportElementErrorSelfie(TelegramType):
    """
    Represents an issue with the selfie with a document. The error is
    considered resolved when the file with the selfie changes.

    https://core.telegram.org/bots/api/#passportelementerrorselfie

    Attributes:
        source: Error source, must be selfie
        type: The section of the user's Telegram Passport which has the
            issue, one of “passport”, “driver_license”, “identity_card”,
            “internal_passport”
        file_hash: Base64-encoded hash of the file with the selfie
        message: Error message

    """

    source: str
    type: str
    file_hash: str
    message: str


@dataclass(eq=True)
class PassportElementErrorFile(TelegramType):
    """
    Represents an issue with a document scan. The error is considered resolved
    when the file with the document scan changes.

    https://core.telegram.org/bots/api/#passportelementerrorfile

    Attributes:
        source: Error source, must be file
        type: The section of the user's Telegram Passport which has the
            issue, one of “utility_bill”, “bank_statement”,
            “rental_agreement”, “passport_registration”,
            “temporary_registration”
        file_hash: Base64-encoded file hash
        message: Error message

    """

    source: str
    type: str
    file_hash: str
    message: str


@dataclass(eq=True)
class PassportElementErrorFiles(TelegramType):
    """
    Represents an issue with a list of scans. The error is considered resolved
    when the list of files containing the scans changes.

    https://core.telegram.org/bots/api/#passportelementerrorfiles

    Attributes:
        source: Error source, must be files
        type: The section of the user's Telegram Passport which has the
            issue, one of “utility_bill”, “bank_statement”,
            “rental_agreement”, “passport_registration”,
            “temporary_registration”
        file_hashes: List of base64-encoded file hashes
        message: Error message

    """

    source: str
    type: str
    file_hashes: List[str]
    message: str


@dataclass(eq=True)
class PassportElementErrorTranslationFile(TelegramType):
    """
    Represents an issue with one of the files that constitute the translation
    of a document. The error is considered resolved when the file changes.

    https://core.telegram.org/bots/api/#passportelementerrortranslationfile

    Attributes:
        source: Error source, must be translation_file
        type: Type of element of the user's Telegram Passport which has the
            issue, one of “passport”, “driver_license”, “identity_card”,
            “internal_passport”, “utility_bill”, “bank_statement”,
            “rental_agreement”, “passport_registration”,
            “temporary_registration”
        file_hash: Base64-encoded file hash
        message: Error message

    """

    source: str
    type: str
    file_hash: str
    message: str


@dataclass(eq=True)
class PassportElementErrorTranslationFiles(TelegramType):
    """
    Represents an issue with the translated version of a document. The error
    is considered resolved when a file with the document translation change.

    https://core.telegram.org/bots/api/#passportelementerrortranslationfiles

    Attributes:
        source: Error source, must be translation_files
        type: Type of element of the user's Telegram Passport which has the
            issue, one of “passport”, “driver_license”, “identity_card”,
            “internal_passport”, “utility_bill”, “bank_statement”,
            “rental_agreement”, “passport_registration”,
            “temporary_registration”
        file_hashes: List of base64-encoded file hashes
        message: Error message

    """

    source: str
    type: str
    file_hashes: List[str]
    message: str


@dataclass(eq=True)
class PassportElementErrorUnspecified(TelegramType):
    """
    Represents an issue in an unspecified place. The error is considered
    resolved when new data is added.

    https://core.telegram.org/bots/api/#passportelementerrorunspecified

    Attributes:
        source: Error source, must be unspecified
        type: Type of element of the user's Telegram Passport which has the
            issue
        element_hash: Base64-encoded element hash
        message: Error message

    """

    source: str
    type: str
    element_hash: str
    message: str


@dataclass(eq=True)
class Game(TelegramType):
    """
    This object represents a game. Use BotFather to create and edit games,
    their short names will act as unique identifiers.

    https://core.telegram.org/bots/api/#game

    Attributes:
        title: Title of the game
        description: Description of the game
        photo: Photo that will be displayed in the game message in chats.
        text: Optional. Brief description of the game or high scores
            included in the game message. Can be automatically edited to
            include current high scores for the game when the bot calls
            setGameScore, or manually edited using editMessageText. 0-4096
            characters.
        text_entities: Optional. Special entities that appear in text, such
            as usernames, URLs, bot commands, etc.
        animation: Optional. Animation that will be displayed in the game
            message in chats. Upload via BotFather

    """

    title: str
    description: str
    photo: List[PhotoSize]
    text: str = None
    text_entities: List[MessageEntity] = None
    animation: Animation = None


@dataclass(eq=True)
class CallbackGame(TelegramType):
    """
    A placeholder, currently holds no information. Use BotFather to set up
    your game.

    https://core.telegram.org/bots/api/#callbackgame


    """

    pass


@dataclass(eq=True)
class GameHighScore(TelegramType):
    """
    This object represents one row of the high scores table for a game.

    https://core.telegram.org/bots/api/#gamehighscore

    Attributes:
        position: Position in high score table for the game
        user: User
        score: Score

    """

    position: int
    user: User
    score: int
