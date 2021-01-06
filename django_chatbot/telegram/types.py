import copy
from dataclasses import dataclass, field
from typing import List, Optional, Union

from django.utils import timezone


class TelegramType:
    @classmethod
    def from_dict(cls, source: dict):
        copied = copy.deepcopy(source)
        o = TelegramType._cast_result(cls=cls, source=copied)
        return o

    @staticmethod
    def _from_timestamp(timestamp: int) -> timezone.datetime:
        dt = timezone.datetime.fromtimestamp(timestamp)
        dt = timezone.make_aware(dt, timezone=timezone.utc)
        return dt

    @staticmethod
    def _convert_date(source: dict) -> dict:
        if 'date' in source:
            source['date'] = TelegramType._from_timestamp(source['date'])
        return source

    @staticmethod
    def _rename_from(source: dict) -> dict:
        if 'from' in source:
            source['from_user'] = source.pop('from')
        return source

    @staticmethod
    def _convert_dict(source: dict) -> dict:
        TelegramType._rename_from(source)
        TelegramType._convert_date(source)
        return source

    @staticmethod
    def _get_telegram_type(
            some_type: Union[type, str]):
        if isinstance(some_type, type):
            if issubclass(some_type, TelegramType):
                return some_type
        elif isinstance(some_type, str):
            try:
                some_type = globals()[some_type]
            except KeyError:
                return None
            else:
                if issubclass(some_type, TelegramType):
                    return some_type

    @staticmethod
    def _cast_result(cls, source: dict):
        TelegramType._convert_dict(source)
        for param, value in source.items():
            param_type = cls.__annotations__[param]
            telegram_type = TelegramType._get_telegram_type(param_type)
            if isinstance(value, list):
                member_class = param_type.__args__[0]
                telegram_type = TelegramType._get_telegram_type(member_class)
                if telegram_type:
                    source[param] = [
                        TelegramType._cast_result(
                            cls=telegram_type, source=member
                        )
                        for member in value
                    ]
            elif telegram_type:
                source[param] = TelegramType._cast_result(
                    cls=telegram_type, source=value
                )
        o = cls(**source)
        return o

    def to_dict(self):
        d = {}
        for key, value in self.__dict__.items():
            if not key.startswith("_") and value is not None:
                if issubclass(type(value), TelegramType):
                    d[key] = value.to_dict()
                elif isinstance(value, list):
                    l = []
                    for member in value:
                        if issubclass(type(member), TelegramType):
                            l.append(member.to_dict())
                        else:
                            l.append(member)
                    d[key] = l
                else:
                    d[key] = value
        return d


@dataclass(eq=True)
class User(TelegramType):
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
    small_file_id: str
    small_file_unique_id: str
    big_file_id: str
    big_file_unique_id: str


@dataclass(eq=True)
class ChatPermissions(TelegramType):
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
    longitude: float
    latitude: float
    horizontal_accuracy: float = None
    live_period: int = None
    heading: int = None
    proximity_alert_radius: int = None


@dataclass(eq=True)
class ChatLocation(TelegramType):
    location: Location
    address: str


@dataclass(eq=True)
class Chat(TelegramType):
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
    pinned_message: 'Message' = None
    permissions: ChatPermissions = None
    slow_mode_delay: int = None
    sticker_set_name: str = None
    can_set_sticker_set: bool = None
    linked_chat_id: int = None
    location: ChatLocation = None


@dataclass(eq=True)
class MessageEntity(TelegramType):
    type: str
    offset: int
    length: int
    url: str = None
    user: User = None
    language: str = None
    text: str = None


@dataclass(eq=True)
class PhotoSize(TelegramType):
    file_id: str
    file_unique_id: str
    width: int
    height: int
    file_size: int = None


@dataclass(eq=True)
class Animation(TelegramType):
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
    file_id: str
    file_unique_id: str
    thumb: PhotoSize = None
    file_name: str = None
    mime_type: str = None
    file_size: int = None


@dataclass(eq=True)
class Video(TelegramType):
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
    file_unique_id: str
    length: int
    duration: int
    thumb: PhotoSize = None
    file_size: int = None


@dataclass(eq=True)
class Voice(TelegramType):
    file_id: str
    file_unique_id: str
    duration: int
    mime_type: str = None
    file_size: int = None


@dataclass(eq=True)
class Contact(TelegramType):
    phone_number: str
    first_name: str
    last_name: str = None
    user_id: int = None
    vcard: str = None


@dataclass(eq=True)
class Dice(TelegramType):
    emoji: str
    value: int


@dataclass(eq=True)
class PollOption(TelegramType):
    text: str
    voter_count: int


@dataclass(eq=True)
class PollAnswer(TelegramType):
    poll_id: str
    user: User
    option_ids: List[int]


@dataclass(eq=True)
class Poll(TelegramType):
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
    location: Location
    title: str
    address: str
    foursquare_id: str = None
    foursquare_type: str = None
    google_place_id: str = None
    google_place_type: str = None


@dataclass(eq=True)
class ProximityAlertTriggered(TelegramType):
    traveler: User
    watcher: User
    distance: int


@dataclass(eq=True)
class MaskPosition(TelegramType):
    point: str
    x_shift: float
    y_shift: float
    scale: float


@dataclass(eq=True)
class Sticker(TelegramType):
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
    title: str
    description: str
    start_parameter: str
    currency: str
    total_amount: int


@dataclass(eq=True)
class ShippingAddress(TelegramType):
    country_code: str
    state: str
    city: str
    street_line1: str
    street_line2: str
    post_code: str


@dataclass(eq=True)
class OrderInfo(TelegramType):
    name: str = None
    phone_number: str = None
    email: str = None
    shipping_address: ShippingAddress = None


@dataclass(eq=True)
class SuccessfulPayment(TelegramType):
    currency: str
    total_amount: int
    invoice_payload: str
    telegram_payment_charge_id: str
    provider_payment_charge_id: str
    shipping_option_id: str = None
    order_info: OrderInfo = None


@dataclass(eq=True)
class ShippingQuery(TelegramType):
    id: str
    from_user: User
    invoice_payload: str
    shipping_address: ShippingAddress


@dataclass(eq=True)
class PreCheckoutQuery(TelegramType):
    id: str
    from_user: User
    currency: str
    total_amount: int
    invoice_payload: str
    shipping_option_id: str = None
    order_info: OrderInfo = None


@dataclass(eq=True)
class PassportFile(TelegramType):
    file_id: str
    file_unique_id: str
    file_size: int
    file_date: int


@dataclass(eq=True)
class EncryptedPassportElement(TelegramType):
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
    data: str
    hash: str
    secret: str


@dataclass(eq=True)
class PassportData(TelegramType):
    data: List[EncryptedPassportElement]
    credentials: EncryptedCredentials


@dataclass(eq=True)
class LoginUrl(TelegramType):
    url: str
    forward_text: str = None
    bot_username: str = None


@dataclass(eq=True)
class CallbackGame(TelegramType):
    user_id: int
    score: int
    force: bool = None
    disable_edit_message: bool = None
    chat_id: int = None
    message_id: int = None
    inline_message_id: str = None


@dataclass(eq=True)
class InlineQuery(TelegramType):
    id: str
    from_user: User
    query: str
    offset: str
    location: Location = None


@dataclass(eq=True)
class ChosenInlineResult(TelegramType):
    result_id: str
    from_user: User
    query: str
    location: Location = None
    inline_message_id: str = None


@dataclass(eq=True)
class InlineKeyboardButton(TelegramType):
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
    inline_keyboard: List[InlineKeyboardButton]


@dataclass(eq=True)
class Message(TelegramType):
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
    reply_to_message: 'Message' = None
    via_bot: User = None
    edit_date: int = None
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
    pinned_message: 'Message' = None
    invoice: Invoice = None
    successful_payment: SuccessfulPayment = None
    connected_website: str = None
    passport_data: PassportData = None
    proximity_alert_triggered: ProximityAlertTriggered = None
    reply_markup: InlineKeyboardMarkup = None

    @classmethod
    def from_dict(cls, source: dict):
        source['from_user'] = source.pop('from')
        return super().from_dict(source)


@dataclass(eq=True)
class CallbackQuery(TelegramType):
    id: str
    from_user: User
    chat_instance: str
    message: Message = None
    inline_message_id: str = None
    data: str = None
    game_short_name: str = None


@dataclass(eq=True)
class Update(TelegramType):
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
        """
        :class:`telegram.types.User`: The user that sent this update, no matter what kind of update this
            is. Will be :obj:`None` for :attr:`channel_post` and :attr:`poll`.

        """
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
        """
        :class:`telegram.Message`: The message included in this update, no matter what kind of
            update this is. Will be :obj:`None` for :attr:`inline_query`,
            :attr:`chosen_inline_result`, :attr:`callback_query` from inline messages,
            :attr:`shipping_query`, :attr:`pre_checkout_query`, :attr:`poll` and
            :attr:`poll_answer`.

        """
        if self._effective_message:
            return self._effective_message

        if self.message:
            self._effective_message = self.message
        elif self.edited_message:
            self._effective_message = self.edited_message
        elif self.callback_query:
            self._effective_message = self.callback_query.message
        elif self.channel_post:
            self._effective_message = self.channel_post
        elif self.edited_channel_post:
            self._effective_message = self.edited_channel_post
        return self._effective_message
