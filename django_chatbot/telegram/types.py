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
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, List, Optional

import dacite
from django.utils import timezone


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
        source = TelegramType.convert_date(
            source, TelegramType.timestamp_to_datetime
        )
        source = TelegramType.convert_froms(source)
        o = dacite.from_dict(cls, source)
        return o

    @staticmethod
    def convert_date(source: dict, convertor: Callable[[Any], Any]):
        converted = {}
        for k, v in source.items():
            if isinstance(v, dict):
                v = TelegramType.convert_date(v, convertor)
            if k == 'date' or k == 'edit_date':
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
            if k == 'from':
                converted['from_user'] = v
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
            self,
            dict_factory=lambda l: {k: v for k, v in l if v is not None}
        )
        if date_as_timestamp:
            dikt = TelegramType.convert_date(
                dikt, TelegramType.datetime_to_timestamp
            )
        return dikt


@dataclass(eq=True)
class User(TelegramType):
    """This object represents a Telegram user or bot.

    https://core.telegram.org/bots/api#user
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
class WebhookInfo(TelegramType):
    url: str
    has_custom_certificate: bool
    pending_update_count: int
    ip_address: str = None
    last_error_date: int = None
    last_error_message: str = None
    max_connections: int = None
    allowed_updates: List[str] = None


@dataclass(eq=True)
class ChatPhoto(TelegramType):
    """This object represents a chat photo.

    https://core.telegram.org/bots/api#chatphoto
    """
    small_file_id: str
    small_file_unique_id: str
    big_file_id: str
    big_file_unique_id: str


@dataclass(eq=True)
class ChatPermissions(TelegramType):
    """
    Describes actions that a non-administrator user is allowed to take in
    a chat.

    https://core.telegram.org/bots/api#chatpermissions
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
class Location(TelegramType):
    """This object represents a point on the map.

    https://core.telegram.org/bots/api#location
    """
    longitude: float
    latitude: float
    horizontal_accuracy: float = None
    live_period: int = None
    heading: int = None
    proximity_alert_radius: int = None


@dataclass(eq=True)
class ChatLocation(TelegramType):
    """Represents a location to which a chat is connected.

    https://core.telegram.org/bots/api#chatlocation
    """
    location: Location
    address: str


@dataclass(eq=True)
class Chat(TelegramType):
    """This object represents a chat.

    https://core.telegram.org/bots/api#chat
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
    sticker_set_name: str = None
    can_set_sticker_set: bool = None
    linked_chat_id: int = None
    location: ChatLocation = None


@dataclass(eq=True)
class MessageEntity(TelegramType):
    """This object represents one special entity in a text message.

    For example, hashtags, usernames, URLs, etc.
    https://core.telegram.org/bots/api#messageentity
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
    """This object represents one size of a photo or a file/sticker thumbnail.

    https://core.telegram.org/bots/api#photosize
    """
    file_id: str
    file_unique_id: str
    width: int
    height: int
    file_size: int = None


@dataclass(eq=True)
class Animation(TelegramType):
    """This object represents an animation file

    https://core.telegram.org/bots/api#animation
    """
    file_id: str
    file_unique_id: str
    width: int
    height: int
    duration: int
    thumb: PhotoSize = None
    file_name: str = None
    mime_type: str = None
    file_size: int = None


@dataclass(eq=True)
class Audio(TelegramType):
    """This object represents an audio file.

    https://core.telegram.org/bots/api#audio
    """
    file_id: str
    file_unique_id: str
    duration: int
    performer: str = None
    title: str = None
    file_name: str = None
    mime_type: str = None
    file_size: int = None
    thumb: PhotoSize = None


@dataclass(eq=True)
class Document(TelegramType):
    """This object represents a general file.

    https://core.telegram.org/bots/api#document
    """
    file_id: str
    file_unique_id: str
    thumb: PhotoSize = None
    file_name: str = None
    mime_type: str = None
    file_size: int = None


@dataclass(eq=True)
class Video(TelegramType):
    """This object represents a video file.

    https://core.telegram.org/bots/api#video
    """
    file_id: str
    file_unique_id: str
    width: int
    height: int
    duration: int
    thumb: PhotoSize = None
    file_name: str = None
    mime_type: str = None
    file_size: int = None


@dataclass(eq=True)
class VideoNote(TelegramType):
    """This object represents a video message

    https://core.telegram.org/bots/api#videonote
    """
    file_unique_id: str
    length: int
    duration: int
    thumb: PhotoSize = None
    file_size: int = None


@dataclass(eq=True)
class Voice(TelegramType):
    """This object represents a voice note.

    https://core.telegram.org/bots/api#voice
    """
    file_id: str
    file_unique_id: str
    duration: int
    mime_type: str = None
    file_size: int = None


@dataclass(eq=True)
class Contact(TelegramType):
    """This object represents a phone contact.

    https://core.telegram.org/bots/api#contact
    """
    phone_number: str
    first_name: str
    last_name: str = None
    user_id: int = None
    vcard: str = None


@dataclass(eq=True)
class Dice(TelegramType):
    """This object represents an animated emoji that displays a random value.

    https://core.telegram.org/bots/api#dice
    """
    emoji: str
    value: int


@dataclass(eq=True)
class PollOption(TelegramType):
    """This object contains information about one answer option in a poll.

    https://core.telegram.org/bots/api#polloption
    """
    text: str
    voter_count: int


@dataclass(eq=True)
class PollAnswer(TelegramType):
    """This object represents an answer of a user in a non-anonymous poll.

    https://core.telegram.org/bots/api#pollanswer
    """
    poll_id: str
    user: User
    option_ids: List[int]


@dataclass(eq=True)
class Poll(TelegramType):
    """This object contains information about a poll.

    https://core.telegram.org/bots/api#poll
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
    close_date: int = None


@dataclass(eq=True)
class Venue(TelegramType):
    """This object represents a venue.

    https://core.telegram.org/bots/api#venue
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
    This object represents the content of a service message, sent whenever
    a user in the chat triggers a proximity alert set by another user.

    https://core.telegram.org/bots/api#proximityalerttriggered
    """
    traveler: User
    watcher: User
    distance: int


@dataclass(eq=True)
class MaskPosition(TelegramType):
    """
    This object describes the position on faces where
    a mask should be placed by default.

    https://core.telegram.org/bots/api#maskposition
    """
    point: str
    x_shift: float
    y_shift: float
    scale: float


@dataclass(eq=True)
class Sticker(TelegramType):
    """This object represents a sticker.

    https://core.telegram.org/bots/api#sticker
    """
    file_id: str
    file_unique_id: str
    width: int
    height: int
    is_animated: bool
    thumb: PhotoSize = None
    emoji: str = None
    set_name: str = None
    mask_position: MaskPosition = None
    file_size: int = None


@dataclass(eq=True)
class Game(TelegramType):
    """This object represents a game.

    https://core.telegram.org/bots/api#game
    """
    title: str
    description: str
    photo: List[PhotoSize]
    file_id: str
    file_unique_id: str
    width: int
    height: int
    is_animated: bool
    text: str = None
    text_entities: List[MessageEntity] = None
    animation: Animation = None
    thumb: PhotoSize = None
    emoji: str = None
    set_name: str = None
    mask_position: MaskPosition = None
    file_size: int = None


@dataclass(eq=True)
class Invoice(TelegramType):
    """This object contains basic information about an invoice.

    https://core.telegram.org/bots/api#invoice
    """
    title: str
    description: str
    start_parameter: str
    currency: str
    total_amount: int


@dataclass(eq=True)
class ShippingAddress(TelegramType):
    """This object represents a shipping address.

    https://core.telegram.org/bots/api#shippingaddress
    """
    country_code: str
    state: str
    city: str
    street_line1: str
    street_line2: str
    post_code: str


@dataclass(eq=True)
class OrderInfo(TelegramType):
    """This object represents information about an order.

    https://core.telegram.org/bots/api#orderinfo
    """
    name: str = None
    phone_number: str = None
    email: str = None
    shipping_address: ShippingAddress = None


@dataclass(eq=True)
class SuccessfulPayment(TelegramType):
    """This object contains basic information about a successful payment.

    https://core.telegram.org/bots/api#successfulpayment
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
    """This object contains information about an incoming shipping query.

    https://core.telegram.org/bots/api#shippingquery
    """
    id: str
    from_user: User
    invoice_payload: str
    shipping_address: ShippingAddress


@dataclass(eq=True)
class PreCheckoutQuery(TelegramType):
    """This object contains information about an incoming pre-checkout query.

    https://core.telegram.org/bots/api#precheckoutquery
    """
    id: str
    from_user: User
    currency: str
    total_amount: int
    invoice_payload: str
    shipping_option_id: str = None
    order_info: OrderInfo = None


@dataclass(eq=True)
class PassportFile(TelegramType):
    """This object represents a file uploaded to Telegram Passport.

    https://core.telegram.org/bots/api#passportfile
    """
    file_id: str
    file_unique_id: str
    file_size: int
    file_date: int


@dataclass(eq=True)
class EncryptedPassportElement(TelegramType):
    """
    Contains information about documents or other Telegram Passport elements
    shared with the bot by the user.

    https://core.telegram.org/bots/api#encryptedpassportelement
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
    EncryptedPassportElement.

    https://core.telegram.org/bots/api#encryptedcredentials
    """
    data: str
    hash: str
    secret: str


@dataclass(eq=True)
class PassportData(TelegramType):
    """
    Contains information about Telegram Passport data shared with
    the bot by the user.

    https://core.telegram.org/bots/api#passportdata
    """
    data: List[EncryptedPassportElement]
    credentials: EncryptedCredentials


@dataclass(eq=True)
class LoginUrl(TelegramType):
    """
    This object represents a parameter of the inline keyboard button
    used to automatically authorize a user.

    https://core.telegram.org/bots/api#loginurl
    """
    url: str
    forward_text: str = None
    bot_username: str = None


@dataclass(eq=True)
class CallbackGame(TelegramType):
    """A placeholder, currently holds no information.

    https://core.telegram.org/bots/api#callbackgame
    """
    user_id: int
    score: int
    force: bool = None
    disable_edit_message: bool = None
    chat_id: int = None
    message_id: int = None
    inline_message_id: str = None


@dataclass(eq=True)
class InlineQuery(TelegramType):
    """This object represents an incoming inline query.

    https://core.telegram.org/bots/api#inlinequery
    """
    id: str
    from_user: User
    query: str
    offset: str
    location: Location = None


@dataclass(eq=True)
class ChosenInlineResult(TelegramType):
    """
    Represents a result of an inline query that was chosen by the user
    and sent to their chat partner.

    https://core.telegram.org/bots/api#choseninlineresult
    """
    result_id: str
    from_user: User
    query: str
    location: Location = None
    inline_message_id: str = None


@dataclass(eq=True)
class KeyboardButtonPollType(TelegramType):
    """
    This object represents type of a poll, which is allowed to be created
    and sent when the corresponding button is pressed.

    https://core.telegram.org/bots/api#keyboardbuttonpolltype
    """
    type: str = None


@dataclass(eq=True)
class KeyboardButton(TelegramType):
    """This object represents one button of the reply keyboard.

    https://core.telegram.org/bots/api#keyboardbutton
    """
    text: str
    request_contact: bool = None
    request_location: bool = None
    request_poll: KeyboardButtonPollType = None


@dataclass(eq=True)
class ReplyKeyboardMarkup(TelegramType):
    """This object represents a custom keyboard with reply options.

    https://core.telegram.org/bots/api#replykeyboardmarkup
    """
    keyboard: List[List[KeyboardButton]]
    resize_keyboard: bool = None
    one_time_keyboard: bool = None
    selective: bool = None


@dataclass(eq=True)
class ReplyKeyboardRemove(TelegramType):
    """
    Upon receiving a message with this object, Telegram clients will remove
    the current custom keyboard and display the default letter-keyboard.

    https://core.telegram.org/bots/api#replykeyboardremove
    """
    remove_keyboard: bool
    selective: bool = None


@dataclass(eq=True)
class InlineKeyboardButton(TelegramType):
    """
    This object represents one button of an inline keyboard.

    https://core.telegram.org/bots/api#inlinekeyboardbutton
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
class InlineKeyboardMarkup(TelegramType):
    """
    This object represents an inline keyboard that appears right next
    to the message it belongs to.

    https://core.telegram.org/bots/api#inlinekeyboardmarkup
    """
    inline_keyboard: List[List[InlineKeyboardButton]]


@dataclass(eq=True)
class ForceReply(TelegramType):
    """
    Upon receiving a message with this object,
    Telegram clients will display a reply interface to the user

    https://core.telegram.org/bots/api#forcereply
    """
    force_reply: bool = True
    selective: bool = None


@dataclass(eq=True)
class Message(TelegramType):
    """This object represents a message.

    https://core.telegram.org/bots/api#message
    """
    message_id: int
    date: timezone.datetime
    chat: Chat
    from_user: User = None
    sender_chat: Chat = None
    forward_from: User = None
    forward_from_chat: Chat = None
    forward_from_message_id: int = None
    forward_signature: str = None
    forward_sender_name: str = None
    forward_date: int = None
    reply_to_message: Message = None
    via_bot: User = None
    edit_date: timezone.datetime = None
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
    migrate_to_chat_id: int = None
    migrate_from_chat_id: int = None
    pinned_message: Message = None
    invoice: Invoice = None
    successful_payment: SuccessfulPayment = None
    connected_website: str = None
    passport_data: PassportData = None
    proximity_alert_triggered: ProximityAlertTriggered = None
    reply_markup: InlineKeyboardMarkup = None


@dataclass(eq=True)
class CallbackQuery(TelegramType):
    """
    This object represents an incoming callback query from
    a callback button in an inline keyboard.

    https://core.telegram.org/bots/api#callbackquery
    """
    id: str
    from_user: User
    chat_instance: str
    message: Message = None
    inline_message_id: str = None
    data: str = None
    game_short_name: str = None


@dataclass(eq=True)
class Update(TelegramType):
    """
    This object represents an incoming update.

    https://core.telegram.org/bots/api#update
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

    _effective_user: User = field(init=None, default=None)
    _effective_message: Message = field(init=None, default=None)

    @property
    def effective_user(self) -> Optional[User]:
        if self._effective_user:
            return self._effective_user

        if self.message:
            self._effective_user = self.message.from_user
        elif self.edited_message:
            self._effective_user = self.edited_message.from_user
        elif self.inline_query:
            self._effective_user = self.inline_query.from_user
        elif self.chosen_inline_result:
            self._effective_user = self.chosen_inline_result.from_user
        elif self.callback_query:
            self._effective_user = self.callback_query.from_user
        elif self.shipping_query:
            self._effective_user = self.shipping_query.from_user
        elif self.pre_checkout_query:
            self._effective_user = self.pre_checkout_query.from_user
        elif self.poll_answer:
            self._effective_user = self.poll_answer.user

        return self._effective_user

    @property
    def effective_message(self) -> Optional[Message]:
        if self._effective_message:
            return self._effective_message

        if self.message:
            self._effective_message = self.message
        elif self.edited_message:
            self._effective_message = self.edited_message
        elif self.channel_post:
            self._effective_message = self.channel_post
        elif self.edited_channel_post:
            self._effective_message = self.edited_channel_post
        return self._effective_message
