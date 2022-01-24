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

"""This module contains classes for Telegram bot API"""
import json
import logging
from dataclasses import dataclass
from typing import List, Type, Union

import requests
from django.utils.timezone import datetime

from .types import (
    BotCommand,
    Chat,
    ChatInviteLink,
    ChatMember,
    ChatPermissions,
    File,
    ForceReply,
    GameHighScore,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InlineQueryResultAudio,
    InlineQueryResultCachedAudio,
    InlineQueryResultCachedDocument,
    InlineQueryResultCachedGif,
    InlineQueryResultCachedMpeg4Gif,
    InlineQueryResultCachedPhoto,
    InlineQueryResultCachedSticker,
    InlineQueryResultCachedVideo,
    InlineQueryResultCachedVoice,
    InlineQueryResultContact,
    InlineQueryResultDocument,
    InlineQueryResultGame,
    InlineQueryResultGif,
    InlineQueryResultLocation,
    InlineQueryResultMpeg4Gif,
    InlineQueryResultPhoto,
    InlineQueryResultVenue,
    InlineQueryResultVideo,
    InlineQueryResultVoice,
    InputFile,
    InputMediaAnimation,
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    LabeledPrice,
    MaskPosition,
    Message,
    MessageEntity,
    MessageId,
    PassportElementErrorDataField,
    PassportElementErrorFile,
    PassportElementErrorFiles,
    PassportElementErrorFrontSide,
    PassportElementErrorReverseSide,
    PassportElementErrorSelfie,
    PassportElementErrorTranslationFile,
    PassportElementErrorTranslationFiles,
    PassportElementErrorUnspecified,
    Poll,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    ShippingOption,
    StickerSet,
    TelegramType,
    Update,
    User,
    UserProfilePhotos,
    WebhookInfo,
)

log = logging.getLogger(__name__)

SERVER_URL = "https://api.telegram.org"


class TelegramError(Exception):
    """Telegram error

    Args:
        reason: The error description returned by Telegram.
        url: The Telegram API url.
        status_code: Status code of the response.
        response: The Telegram response.
        api_code: The error code returned by Telegram.
    Attributes:
        reason: The error description returned by Telegram.
        url: The Telegram API url.
        status_code: Status code of the response.
        response: The Telegram response.
        api_code: The error code returned by Telegram.
    """

    def __init__(
        self,
        reason: str,
        url: str = None,
        status_code: int = None,
        response: requests.Response = None,
        api_code=None,
    ):
        self.reason = reason
        self.url = url
        self.status_code = status_code
        self.response = response
        self.api_code = api_code
        super(TelegramError, self).__init__(reason)

    def __str__(self):
        return self.reason

    def to_dict(self) -> dict:
        return {
            "reason": self.reason,
            "url": self.url,
            "status_code": self.status_code,
            "response": self.response,
            "api_code": self.api_code,
        }


@dataclass
class _Binder:
    """Helper class for communicating with Telegram Bot API.

    The class sends requests to Telegram API and casts responses
    to django_chatbot types.

    Args:
        token: Bot token.
        method_name: Name of Telegram API method.
        params: Parameters of Telegram API methods.
        telegram_type: The 'TelegramType' to which the API response should be
            cast.
    """

    token: str
    method_name: str
    params: dict = None
    telegram_type: Type[TelegramType] = None

    def __post_init__(self):
        self.url = f"{SERVER_URL}/bot{self.token}/{self.method_name}"

    def bind(self):
        """Request to Telegram API and cast result to :class:`TelegramType`

        Returns:
            The casted to ``self.telegram_type`` API response.

        Raises:
            TelegramError: If there is telegram or requests error.
        """
        if self.params:
            params = {k: v for k, v in self.params.items() if v is not None}
            response = requests.post(url=self.url, data=params)
            log.debug(
                "Telegram params=%s response: url=%s, status_code=%s, json=%s",
                params,
                response.url,
                response.status_code,
                response.json(),
            )
        else:
            response = requests.get(url=self.url)
            log.debug(
                "Telegram request response: url=%s, status_code=%s, json=%s",
                response.url,
                response.status_code,
                response.json(),
            )
        result = self._parse_response(response, self.telegram_type)
        return result

    @staticmethod
    def _parse_response(response: requests.Response, telegram_type: Type[TelegramType]):
        """Parse response

        Args:
            response: requests response object.
            telegram_type: Type to which should be casted.

        Returns:
            The casted telegram API response

        Raises:
            TelegramError: If there was telegram or requests error.
        """
        if response.status_code == 200:
            response_result = response.json()
            result = _Binder._get_result(response_result, telegram_type)
            return result
        else:
            response_json = response.json()
            raise TelegramError(
                reason=response_json["description"],
                url=response.url,
                status_code=response.status_code,
                response=response_json,
                api_code=response_json["error_code"],
            )

    @staticmethod
    def _get_result(response_result: dict, telegram_type: Type[TelegramType]):
        """Extract result from response dictionary

        Args:
            response_result: telegram response dictionary
            telegram_type:

            telegram_type: Type to which should be casted.

        Returns:
            The casted telegram API response
        """
        if response_result["ok"]:
            result = response_result["result"]
            if telegram_type is None or not issubclass(telegram_type, TelegramType):
                return result
            else:
                return telegram_type.from_dict(source=result)


class Api:
    """Telegram API client

    Args:
        token: Bot token

    Attributes:
        token: Bot token

    """

    def __init__(self, token: str):
        self.token = token

    def _bind(
        self,
        method_name: str,
        params: dict = None,
        telegram_type: Type[TelegramType] = None,
    ):
        """Make request to API and return casted response.

        Args:
            method_name: Name of Telegram API method.
            params: Parameters of Telegram API methods.
            telegram_type: The 'TelegramType' to which the API response
                should be casted.

        Returns:
            Casted response.

        Raises:
            TelegramError: If there was telegram or requests error.
        """
        binder = _Binder(
            token=self.token,
            method_name=method_name,
            params=params,
            telegram_type=telegram_type,
        )
        return binder.bind()

    def get_updates(
        self,
        offset: int = None,
        limit: int = None,
        timeout: int = None,
        allowed_updates: List[str] = None,
    ) -> Update:
        """
        Use this method to receive incoming updates using long polling (wiki).
        An Array of Update objects is returned.

        https://core.telegram.org/bots/api/#getupdates

        Args:
            offset: Identifier of the first update to be returned. Must be
                greater by one than the highest among the identifiers of
                previously received updates. By default, updates starting with
                the earliest unconfirmed update are returned. An update is
                considered confirmed as soon as getUpdates is called with an
                offset higher than its update_id. The negative offset can be
                specified to retrieve updates starting from -offset update from
                the end of the updates queue. All previous updates will
                forgotten.
            limit: Limits the number of updates to be retrieved. Values
                between 1-100 are accepted. Defaults to 100.
            timeout: Timeout in seconds for long polling. Defaults to 0,
                i.e. usual short polling. Should be positive, short polling
                should be used for testing purposes only.
            allowed_updates: A JSON-serialized list of the update types you
                want your bot to receive. For example, specify [“message”,
                “edited_channel_post”, “callback_query”] to only receive
                updates of these types. See Update for a complete list of
                available update types. Specify an empty list to receive all
                update types except chat_member (default). If not specified,
                the previous setting will be used.Please note that this
                parameter doesn't affect updates created before the call to the
                getUpdates, so unwanted updates may be received for a short
                period of time.

        Returns:
            Update
        """

        params = {
            "offset": offset,
            "limit": limit,
            "timeout": timeout,
            "allowed_updates": allowed_updates,
        }
        return self._bind(method_name="getUpdates", params=params, telegram_type=Update)

    def set_webhook(
        self,
        url: str,
        certificate: InputFile = None,
        ip_address: str = None,
        max_connections: int = None,
        allowed_updates: List[str] = None,
        drop_pending_updates: bool = None,
    ) -> bool:
        """
        Use this method to specify a url and receive incoming updates via an
        outgoing webhook. Whenever there is an update for the bot, we will send
        an HTTPS POST request to the specified url, containing a
        JSON-serialized Update. In case of an unsuccessful request, we will
        give up after a reasonable amount of attempts. Returns True on success.

        If you'd like to make sure that the Webhook request comes from
        Telegram, we recommend using a secret path in the URL, e.g.
        https://www.example.com/<token>. Since nobody else knows your bot's
        token, you can be pretty sure it's us.

        https://core.telegram.org/bots/api/#setwebhook

        Args:
            url: HTTPS url to send updates to. Use an empty string to remove
                webhook integration
            certificate: Upload your public key certificate so that the root
                certificate in use can be checked. See our self-signed guide
                for details.
            ip_address: The fixed IP address which will be used to send
                webhook requests instead of the IP address resolved through DNS
            max_connections: Maximum allowed number of simultaneous HTTPS
                connections to the webhook for update delivery, 1-100. Defaults
                to 40. Use lower values to limit the load on your bot's server,
                and higher values to increase your bot's throughput.
            allowed_updates: A JSON-serialized list of the update types you
                want your bot to receive. For example, specify [“message”,
                “edited_channel_post”, “callback_query”] to only receive
                updates of these types. See Update for a complete list of
                available update types. Specify an empty list to receive all
                update types except chat_member (default). If not specified,
                the previous setting will be used.Please note that this
                parameter doesn't affect updates created before the call to the
                setWebhook, so unwanted updates may be received for a short
                period of time.
            drop_pending_updates: Pass True to drop all pending updates

        Returns:
            bool
        """
        if certificate is not None:
            certificate = certificate.to_dict()

        params = {
            "url": url,
            "certificate": certificate,
            "ip_address": ip_address,
            "max_connections": max_connections,
            "allowed_updates": allowed_updates,
            "drop_pending_updates": drop_pending_updates,
        }
        return self._bind(method_name="setWebhook", params=params, telegram_type=bool)

    def delete_webhook(self, drop_pending_updates: bool = None) -> bool:
        """
        Use this method to remove webhook integration if you decide to switch
        back to getUpdates. Returns True on success.

        https://core.telegram.org/bots/api/#deletewebhook

        Args:
            drop_pending_updates: Pass True to drop all pending updates

        Returns:
            bool
        """

        params = {
            "drop_pending_updates": drop_pending_updates,
        }
        return self._bind(
            method_name="deleteWebhook", params=params, telegram_type=bool
        )

    def get_webhook_info(
        self,
    ) -> WebhookInfo:
        """
        Use this method to get current webhook status. Requires no parameters.
        On success, returns a WebhookInfo object. If the bot is using
        getUpdates, will return an object with the url field empty.

        https://core.telegram.org/bots/api/#getwebhookinfo


        Returns:
            WebhookInfo
        """
        return self._bind(method_name="getWebhookInfo", telegram_type=WebhookInfo)

    def get_me(
        self,
    ) -> User:
        """
        A simple method for testing your bot's auth token. Requires no
        parameters. Returns basic information about the bot in form of a User
        object.

        https://core.telegram.org/bots/api/#getme


        Returns:
            User
        """
        return self._bind(method_name="getMe", telegram_type=User)

    def log_out(
        self,
    ) -> bool:
        """
        Use this method to log out from the cloud Bot API server before
        launching the bot locally. You must log out the bot before running it
        locally, otherwise there is no guarantee that the bot will receive
        updates. After a successful call, you can immediately log in on a local
        server, but will not be able to log in back to the cloud Bot API server
        for 10 minutes. Returns True on success. Requires no parameters.

        https://core.telegram.org/bots/api/#logout


        Returns:
            bool
        """
        return self._bind(method_name="logOut", telegram_type=bool)

    def close(
        self,
    ) -> bool:
        """
        Use this method to close the bot instance before moving it from one
        local server to another. You need to delete the webhook before calling
        this method to ensure that the bot isn't launched again after server
        restart. The method will return error 429 in the first 10 minutes after
        the bot is launched. Returns True on success. Requires no parameters.

        https://core.telegram.org/bots/api/#close


        Returns:
            bool
        """
        return self._bind(method_name="close", telegram_type=bool)

    def send_message(
        self,
        chat_id: Union[int, str],
        text: str,
        parse_mode: str = None,
        entities: List[MessageEntity] = None,
        disable_web_page_preview: bool = None,
        disable_notification: bool = None,
        reply_to_message_id: int = None,
        allow_sending_without_reply: bool = None,
        reply_markup: Union[
            InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply
        ] = None,
    ) -> Message:
        """
        Use this method to send text messages. On success, the sent Message is
        returned.

        https://core.telegram.org/bots/api/#sendmessage

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)
            text: Text of the message to be sent, 1-4096 characters after
                entities parsing
            parse_mode: Mode for parsing entities in the message text. See
                formatting options for more details.
            entities: List of special entities that appear in message text,
                which can be specified instead of parse_mode
            disable_web_page_preview: Disables link previews for links in
                this message
            disable_notification: Sends the message silently. Users will
                receive a notification with no sound.
            reply_to_message_id: If the message is a reply, ID of the
                original message
            allow_sending_without_reply: Pass True, if the message should be
                sent even if the specified replied-to message is not found
            reply_markup: Additional interface options. A JSON-serialized
                object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from
                the user.

        Returns:
            Message
        """
        if entities is not None:
            entities = [e.to_dict() for e in entities]
        if reply_markup is not None:
            reply_markup = json.dumps(reply_markup.to_dict())

        params = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "entities": entities,
            "disable_web_page_preview": disable_web_page_preview,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "allow_sending_without_reply": allow_sending_without_reply,
            "reply_markup": reply_markup,
        }
        return self._bind(
            method_name="sendMessage", params=params, telegram_type=Message
        )

    def forward_message(
        self,
        chat_id: Union[int, str],
        from_chat_id: Union[int, str],
        message_id: int,
        disable_notification: bool = None,
    ) -> Message:
        """
        Use this method to forward messages of any kind. On success, the sent
        Message is returned.

        https://core.telegram.org/bots/api/#forwardmessage

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)
            from_chat_id: Unique identifier for the chat where the original
                message was sent (or channel username in the format
                @channelusername)
            message_id: Message identifier in the chat specified in
                from_chat_id
            disable_notification: Sends the message silently. Users will
                receive a notification with no sound.

        Returns:
            Message
        """

        params = {
            "chat_id": chat_id,
            "from_chat_id": from_chat_id,
            "message_id": message_id,
            "disable_notification": disable_notification,
        }
        return self._bind(
            method_name="forwardMessage", params=params, telegram_type=Message
        )

    def copy_message(
        self,
        chat_id: Union[int, str],
        from_chat_id: Union[int, str],
        message_id: int,
        caption: str = None,
        parse_mode: str = None,
        caption_entities: List[MessageEntity] = None,
        disable_notification: bool = None,
        reply_to_message_id: int = None,
        allow_sending_without_reply: bool = None,
        reply_markup: Union[
            InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply
        ] = None,
    ) -> MessageId:
        """
        Use this method to copy messages of any kind. The method is analogous
        to the method forwardMessage, but the copied message doesn't have a
        link to the original message. Returns the MessageId of the sent message
        on success.

        https://core.telegram.org/bots/api/#copymessage

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)
            from_chat_id: Unique identifier for the chat where the original
                message was sent (or channel username in the format
                @channelusername)
            message_id: Message identifier in the chat specified in
                from_chat_id
            caption: New caption for media, 0-1024 characters after entities
                parsing. If not specified, the original caption is kept
            parse_mode: Mode for parsing entities in the new caption. See
                formatting options for more details.
            caption_entities: List of special entities that appear in the
                new caption, which can be specified instead of parse_mode
            disable_notification: Sends the message silently. Users will
                receive a notification with no sound.
            reply_to_message_id: If the message is a reply, ID of the
                original message
            allow_sending_without_reply: Pass True, if the message should be
                sent even if the specified replied-to message is not found
            reply_markup: Additional interface options. A JSON-serialized
                object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from
                the user.

        Returns:
            MessageId
        """
        if caption_entities is not None:
            caption_entities = [c.to_dict() for c in caption_entities]
        if reply_markup is not None:
            reply_markup = reply_markup.to_dict()

        params = {
            "chat_id": chat_id,
            "from_chat_id": from_chat_id,
            "message_id": message_id,
            "caption": caption,
            "parse_mode": parse_mode,
            "caption_entities": caption_entities,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "allow_sending_without_reply": allow_sending_without_reply,
            "reply_markup": reply_markup,
        }
        return self._bind(
            method_name="copyMessage", params=params, telegram_type=MessageId
        )

    def send_photo(
        self,
        chat_id: Union[int, str],
        photo: Union[InputFile, str],
        caption: str = None,
        parse_mode: str = None,
        caption_entities: List[MessageEntity] = None,
        disable_notification: bool = None,
        reply_to_message_id: int = None,
        allow_sending_without_reply: bool = None,
        reply_markup: Union[
            InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply
        ] = None,
    ) -> Message:
        """
        Use this method to send photos. On success, the sent Message is
        returned.

        https://core.telegram.org/bots/api/#sendphoto

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)
            photo: Photo to send. Pass a file_id as String to send a photo
                that exists on the Telegram servers (recommended), pass an HTTP
                URL as a String for Telegram to get a photo from the Internet,
                or upload a new photo using multipart/form-data. The photo must
                be at most 10 MB in size. The photo's width and height must not
                exceed 10000 in total. Width and height ratio must be at most
                20. More info on Sending Files »
            caption: Photo caption (may also be used when resending photos
                by file_id), 0-1024 characters after entities parsing
            parse_mode: Mode for parsing entities in the photo caption. See
                formatting options for more details.
            caption_entities: List of special entities that appear in the
                caption, which can be specified instead of parse_mode
            disable_notification: Sends the message silently. Users will
                receive a notification with no sound.
            reply_to_message_id: If the message is a reply, ID of the
                original message
            allow_sending_without_reply: Pass True, if the message should be
                sent even if the specified replied-to message is not found
            reply_markup: Additional interface options. A JSON-serialized
                object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from
                the user.

        Returns:
            Message
        """
        if photo is not None and hasattr(photo, "to_dict"):
            photo = photo.to_dict()
        if caption_entities is not None:
            caption_entities = [c.to_dict() for c in caption_entities]
        if reply_markup is not None:
            reply_markup = reply_markup.to_dict()

        params = {
            "chat_id": chat_id,
            "photo": photo,
            "caption": caption,
            "parse_mode": parse_mode,
            "caption_entities": caption_entities,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "allow_sending_without_reply": allow_sending_without_reply,
            "reply_markup": reply_markup,
        }
        return self._bind(method_name="sendPhoto", params=params, telegram_type=Message)

    def send_audio(
        self,
        chat_id: Union[int, str],
        audio: Union[InputFile, str],
        caption: str = None,
        parse_mode: str = None,
        caption_entities: List[MessageEntity] = None,
        duration: int = None,
        performer: str = None,
        title: str = None,
        thumb: Union[InputFile, str] = None,
        disable_notification: bool = None,
        reply_to_message_id: int = None,
        allow_sending_without_reply: bool = None,
        reply_markup: Union[
            InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply
        ] = None,
    ) -> Message:
        """
        Use this method to send audio files, if you want Telegram clients to
        display them in the music player. Your audio must be in the .MP3 or
        .M4A format. On success, the sent Message is returned. Bots can
        currently send audio files of up to 50 MB in size, this limit may be
        changed in the future.

        For sending voice messages, use the sendVoice method instead.

        https://core.telegram.org/bots/api/#sendaudio

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)
            audio: Audio file to send. Pass a file_id as String to send an
                audio file that exists on the Telegram servers (recommended),
                pass an HTTP URL as a String for Telegram to get an audio file
                from the Internet, or upload a new one using
                multipart/form-data. More info on Sending Files »
            caption: Audio caption, 0-1024 characters after entities parsing
            parse_mode: Mode for parsing entities in the audio caption. See
                formatting options for more details.
            caption_entities: List of special entities that appear in the
                caption, which can be specified instead of parse_mode
            duration: Duration of the audio in seconds
            performer: Performer
            title: Track name
            thumb: Thumbnail of the file sent; can be ignored if thumbnail
                generation for the file is supported server-side. The thumbnail
                should be in JPEG format and less than 200 kB in size. A
                thumbnail's width and height should not exceed 320. Ignored if
                the file is not uploaded using multipart/form-data. Thumbnails
                can't be reused and can be only uploaded as a new file, so you
                can pass “attach://<file_attach_name>” if the thumbnail was
                uploaded using multipart/form-data under <file_attach_name>.
                More info on Sending Files »
            disable_notification: Sends the message silently. Users will
                receive a notification with no sound.
            reply_to_message_id: If the message is a reply, ID of the
                original message
            allow_sending_without_reply: Pass True, if the message should be
                sent even if the specified replied-to message is not found
            reply_markup: Additional interface options. A JSON-serialized
                object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from
                the user.

        Returns:
            Message
        """
        if audio is not None and hasattr(audio, "to_dict"):
            audio = audio.to_dict()
        if caption_entities is not None:
            caption_entities = [c.to_dict() for c in caption_entities]
        if thumb is not None and hasattr(thumb, "to_dict"):
            thumb = thumb.to_dict()
        if reply_markup is not None:
            reply_markup = reply_markup.to_dict()

        params = {
            "chat_id": chat_id,
            "audio": audio,
            "caption": caption,
            "parse_mode": parse_mode,
            "caption_entities": caption_entities,
            "duration": duration,
            "performer": performer,
            "title": title,
            "thumb": thumb,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "allow_sending_without_reply": allow_sending_without_reply,
            "reply_markup": reply_markup,
        }
        return self._bind(method_name="sendAudio", params=params, telegram_type=Message)

    def send_document(
        self,
        chat_id: Union[int, str],
        document: Union[InputFile, str],
        thumb: Union[InputFile, str] = None,
        caption: str = None,
        parse_mode: str = None,
        caption_entities: List[MessageEntity] = None,
        disable_content_type_detection: bool = None,
        disable_notification: bool = None,
        reply_to_message_id: int = None,
        allow_sending_without_reply: bool = None,
        reply_markup: Union[
            InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply
        ] = None,
    ) -> Message:
        """
        Use this method to send general files. On success, the sent Message is
        returned. Bots can currently send files of any type of up to 50 MB in
        size, this limit may be changed in the future.

        https://core.telegram.org/bots/api/#senddocument

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)
            document: File to send. Pass a file_id as String to send a file
                that exists on the Telegram servers (recommended), pass an HTTP
                URL as a String for Telegram to get a file from the Internet,
                or upload a new one using multipart/form-data. More info on
                Sending Files »
            thumb: Thumbnail of the file sent; can be ignored if thumbnail
                generation for the file is supported server-side. The thumbnail
                should be in JPEG format and less than 200 kB in size. A
                thumbnail's width and height should not exceed 320. Ignored if
                the file is not uploaded using multipart/form-data. Thumbnails
                can't be reused and can be only uploaded as a new file, so you
                can pass “attach://<file_attach_name>” if the thumbnail was
                uploaded using multipart/form-data under <file_attach_name>.
                More info on Sending Files »
            caption: Document caption (may also be used when resending
                documents by file_id), 0-1024 characters after entities parsing
            parse_mode: Mode for parsing entities in the document caption.
                See formatting options for more details.
            caption_entities: List of special entities that appear in the
                caption, which can be specified instead of parse_mode
            disable_content_type_detection: Disables automatic server-side
                content type detection for files uploaded using
                multipart/form-data
            disable_notification: Sends the message silently. Users will
                receive a notification with no sound.
            reply_to_message_id: If the message is a reply, ID of the
                original message
            allow_sending_without_reply: Pass True, if the message should be
                sent even if the specified replied-to message is not found
            reply_markup: Additional interface options. A JSON-serialized
                object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from
                the user.

        Returns:
            Message
        """
        if document is not None and hasattr(document, "to_dict"):
            document = document.to_dict()
        if thumb is not None and hasattr(thumb, "to_dict"):
            thumb = thumb.to_dict()
        if caption_entities is not None:
            caption_entities = [c.to_dict() for c in caption_entities]
        if reply_markup is not None:
            reply_markup = reply_markup.to_dict()

        params = {
            "chat_id": chat_id,
            "document": document,
            "thumb": thumb,
            "caption": caption,
            "parse_mode": parse_mode,
            "caption_entities": caption_entities,
            "disable_content_type_detection": disable_content_type_detection,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "allow_sending_without_reply": allow_sending_without_reply,
            "reply_markup": reply_markup,
        }
        return self._bind(
            method_name="sendDocument", params=params, telegram_type=Message
        )

    def send_video(
        self,
        chat_id: Union[int, str],
        video: Union[InputFile, str],
        duration: int = None,
        width: int = None,
        height: int = None,
        thumb: Union[InputFile, str] = None,
        caption: str = None,
        parse_mode: str = None,
        caption_entities: List[MessageEntity] = None,
        supports_streaming: bool = None,
        disable_notification: bool = None,
        reply_to_message_id: int = None,
        allow_sending_without_reply: bool = None,
        reply_markup: Union[
            InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply
        ] = None,
    ) -> Message:
        """
        Use this method to send video files, Telegram clients support mp4
        videos (other formats may be sent as Document). On success, the sent
        Message is returned. Bots can currently send video files of up to 50 MB
        in size, this limit may be changed in the future.

        https://core.telegram.org/bots/api/#sendvideo

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)
            video: Video to send. Pass a file_id as String to send a video
                that exists on the Telegram servers (recommended), pass an HTTP
                URL as a String for Telegram to get a video from the Internet,
                or upload a new video using multipart/form-data. More info on
                Sending Files »
            duration: Duration of sent video in seconds
            width: Video width
            height: Video height
            thumb: Thumbnail of the file sent; can be ignored if thumbnail
                generation for the file is supported server-side. The thumbnail
                should be in JPEG format and less than 200 kB in size. A
                thumbnail's width and height should not exceed 320. Ignored if
                the file is not uploaded using multipart/form-data. Thumbnails
                can't be reused and can be only uploaded as a new file, so you
                can pass “attach://<file_attach_name>” if the thumbnail was
                uploaded using multipart/form-data under <file_attach_name>.
                More info on Sending Files »
            caption: Video caption (may also be used when resending videos
                by file_id), 0-1024 characters after entities parsing
            parse_mode: Mode for parsing entities in the video caption. See
                formatting options for more details.
            caption_entities: List of special entities that appear in the
                caption, which can be specified instead of parse_mode
            supports_streaming: Pass True, if the uploaded video is suitable
                for streaming
            disable_notification: Sends the message silently. Users will
                receive a notification with no sound.
            reply_to_message_id: If the message is a reply, ID of the
                original message
            allow_sending_without_reply: Pass True, if the message should be
                sent even if the specified replied-to message is not found
            reply_markup: Additional interface options. A JSON-serialized
                object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from
                the user.

        Returns:
            Message
        """
        if video is not None and hasattr(video, "to_dict"):
            video = video.to_dict()
        if thumb is not None and hasattr(thumb, "to_dict"):
            thumb = thumb.to_dict()
        if caption_entities is not None:
            caption_entities = [c.to_dict() for c in caption_entities]
        if reply_markup is not None:
            reply_markup = reply_markup.to_dict()

        params = {
            "chat_id": chat_id,
            "video": video,
            "duration": duration,
            "width": width,
            "height": height,
            "thumb": thumb,
            "caption": caption,
            "parse_mode": parse_mode,
            "caption_entities": caption_entities,
            "supports_streaming": supports_streaming,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "allow_sending_without_reply": allow_sending_without_reply,
            "reply_markup": reply_markup,
        }
        return self._bind(method_name="sendVideo", params=params, telegram_type=Message)

    def send_animation(
        self,
        chat_id: Union[int, str],
        animation: Union[InputFile, str],
        duration: int = None,
        width: int = None,
        height: int = None,
        thumb: Union[InputFile, str] = None,
        caption: str = None,
        parse_mode: str = None,
        caption_entities: List[MessageEntity] = None,
        disable_notification: bool = None,
        reply_to_message_id: int = None,
        allow_sending_without_reply: bool = None,
        reply_markup: Union[
            InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply
        ] = None,
    ) -> Message:
        """
        Use this method to send animation files (GIF or H.264/MPEG-4 AVC video
        without sound). On success, the sent Message is returned. Bots can
        currently send animation files of up to 50 MB in size, this limit may
        be changed in the future.

        https://core.telegram.org/bots/api/#sendanimation

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)
            animation: Animation to send. Pass a file_id as String to send
                an animation that exists on the Telegram servers (recommended),
                pass an HTTP URL as a String for Telegram to get an animation
                from the Internet, or upload a new animation using
                multipart/form-data. More info on Sending Files »
            duration: Duration of sent animation in seconds
            width: Animation width
            height: Animation height
            thumb: Thumbnail of the file sent; can be ignored if thumbnail
                generation for the file is supported server-side. The thumbnail
                should be in JPEG format and less than 200 kB in size. A
                thumbnail's width and height should not exceed 320. Ignored if
                the file is not uploaded using multipart/form-data. Thumbnails
                can't be reused and can be only uploaded as a new file, so you
                can pass “attach://<file_attach_name>” if the thumbnail was
                uploaded using multipart/form-data under <file_attach_name>.
                More info on Sending Files »
            caption: Animation caption (may also be used when resending
                animation by file_id), 0-1024 characters after entities parsing
            parse_mode: Mode for parsing entities in the animation caption.
                See formatting options for more details.
            caption_entities: List of special entities that appear in the
                caption, which can be specified instead of parse_mode
            disable_notification: Sends the message silently. Users will
                receive a notification with no sound.
            reply_to_message_id: If the message is a reply, ID of the
                original message
            allow_sending_without_reply: Pass True, if the message should be
                sent even if the specified replied-to message is not found
            reply_markup: Additional interface options. A JSON-serialized
                object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from
                the user.

        Returns:
            Message
        """
        if animation is not None and hasattr(animation, "to_dict"):
            animation = animation.to_dict()
        if thumb is not None and hasattr(thumb, "to_dict"):
            thumb = thumb.to_dict()
        if caption_entities is not None:
            caption_entities = [c.to_dict() for c in caption_entities]
        if reply_markup is not None:
            reply_markup = reply_markup.to_dict()

        params = {
            "chat_id": chat_id,
            "animation": animation,
            "duration": duration,
            "width": width,
            "height": height,
            "thumb": thumb,
            "caption": caption,
            "parse_mode": parse_mode,
            "caption_entities": caption_entities,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "allow_sending_without_reply": allow_sending_without_reply,
            "reply_markup": reply_markup,
        }
        return self._bind(
            method_name="sendAnimation", params=params, telegram_type=Message
        )

    def send_voice(
        self,
        chat_id: Union[int, str],
        voice: Union[InputFile, str],
        caption: str = None,
        parse_mode: str = None,
        caption_entities: List[MessageEntity] = None,
        duration: int = None,
        disable_notification: bool = None,
        reply_to_message_id: int = None,
        allow_sending_without_reply: bool = None,
        reply_markup: Union[
            InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply
        ] = None,
    ) -> Message:
        """
        Use this method to send audio files, if you want Telegram clients to
        display the file as a playable voice message. For this to work, your
        audio must be in an .OGG file encoded with OPUS (other formats may be
        sent as Audio or Document). On success, the sent Message is returned.
        Bots can currently send voice messages of up to 50 MB in size, this
        limit may be changed in the future.

        https://core.telegram.org/bots/api/#sendvoice

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)
            voice: Audio file to send. Pass a file_id as String to send a
                file that exists on the Telegram servers (recommended), pass an
                HTTP URL as a String for Telegram to get a file from the
                Internet, or upload a new one using multipart/form-data. More
                info on Sending Files »
            caption: Voice message caption, 0-1024 characters after entities
                parsing
            parse_mode: Mode for parsing entities in the voice message
                caption. See formatting options for more details.
            caption_entities: List of special entities that appear in the
                caption, which can be specified instead of parse_mode
            duration: Duration of the voice message in seconds
            disable_notification: Sends the message silently. Users will
                receive a notification with no sound.
            reply_to_message_id: If the message is a reply, ID of the
                original message
            allow_sending_without_reply: Pass True, if the message should be
                sent even if the specified replied-to message is not found
            reply_markup: Additional interface options. A JSON-serialized
                object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from
                the user.

        Returns:
            Message
        """
        if voice is not None and hasattr(voice, "to_dict"):
            voice = voice.to_dict()
        if caption_entities is not None:
            caption_entities = [c.to_dict() for c in caption_entities]
        if reply_markup is not None:
            reply_markup = reply_markup.to_dict()

        params = {
            "chat_id": chat_id,
            "voice": voice,
            "caption": caption,
            "parse_mode": parse_mode,
            "caption_entities": caption_entities,
            "duration": duration,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "allow_sending_without_reply": allow_sending_without_reply,
            "reply_markup": reply_markup,
        }
        return self._bind(method_name="sendVoice", params=params, telegram_type=Message)

    def send_video_note(
        self,
        chat_id: Union[int, str],
        video_note: Union[InputFile, str],
        duration: int = None,
        length: int = None,
        thumb: Union[InputFile, str] = None,
        disable_notification: bool = None,
        reply_to_message_id: int = None,
        allow_sending_without_reply: bool = None,
        reply_markup: Union[
            InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply
        ] = None,
    ) -> Message:
        """
        As of v.4.0, Telegram clients support rounded square mp4 videos of up
        to 1 minute long. Use this method to send video messages. On success,
        the sent Message is returned.

        https://core.telegram.org/bots/api/#sendvideonote

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)
            video_note: Video note to send. Pass a file_id as String to send
                a video note that exists on the Telegram servers (recommended)
                or upload a new video using multipart/form-data. More info on
                Sending Files ». Sending video notes by a URL is currently
                unsupported
            duration: Duration of sent video in seconds
            length: Video width and height, i.e. diameter of the video
                message
            thumb: Thumbnail of the file sent; can be ignored if thumbnail
                generation for the file is supported server-side. The thumbnail
                should be in JPEG format and less than 200 kB in size. A
                thumbnail's width and height should not exceed 320. Ignored if
                the file is not uploaded using multipart/form-data. Thumbnails
                can't be reused and can be only uploaded as a new file, so you
                can pass “attach://<file_attach_name>” if the thumbnail was
                uploaded using multipart/form-data under <file_attach_name>.
                More info on Sending Files »
            disable_notification: Sends the message silently. Users will
                receive a notification with no sound.
            reply_to_message_id: If the message is a reply, ID of the
                original message
            allow_sending_without_reply: Pass True, if the message should be
                sent even if the specified replied-to message is not found
            reply_markup: Additional interface options. A JSON-serialized
                object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from
                the user.

        Returns:
            Message
        """
        if video_note is not None and hasattr(video_note, "to_dict"):
            video_note = video_note.to_dict()
        if thumb is not None and hasattr(thumb, "to_dict"):
            thumb = thumb.to_dict()
        if reply_markup is not None:
            reply_markup = reply_markup.to_dict()

        params = {
            "chat_id": chat_id,
            "video_note": video_note,
            "duration": duration,
            "length": length,
            "thumb": thumb,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "allow_sending_without_reply": allow_sending_without_reply,
            "reply_markup": reply_markup,
        }
        return self._bind(
            method_name="sendVideoNote", params=params, telegram_type=Message
        )

    def send_media_group(
        self,
        chat_id: Union[int, str],
        media: List[
            Union[InputMediaAudio, InputMediaDocument, InputMediaPhoto, InputMediaVideo]
        ],
        disable_notification: bool = None,
        reply_to_message_id: int = None,
        allow_sending_without_reply: bool = None,
    ) -> List[Message]:
        """
        Use this method to send a group of photos, videos, documents or audios
        as an album. Documents and audio files can be only grouped in an album
        with messages of the same type. On success, an array of Messages that
        were sent is returned.

        https://core.telegram.org/bots/api/#sendmediagroup

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)
            media: A JSON-serialized array describing messages to be sent,
                must include 2-10 items
            disable_notification: Sends messages silently. Users will
                receive a notification with no sound.
            reply_to_message_id: If the messages are a reply, ID of the
                original message
            allow_sending_without_reply: Pass True, if the message should be
                sent even if the specified replied-to message is not found

        Returns:
            List[Message]
        """
        if media is not None:
            media = [m.to_dict() for m in media]

        params = {
            "chat_id": chat_id,
            "media": media,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "allow_sending_without_reply": allow_sending_without_reply,
        }
        return self._bind(
            method_name="sendMediaGroup", params=params, telegram_type=List[Message]
        )

    def send_location(
        self,
        chat_id: Union[int, str],
        latitude: float,
        longitude: float,
        horizontal_accuracy: float = None,
        live_period: int = None,
        heading: int = None,
        proximity_alert_radius: int = None,
        disable_notification: bool = None,
        reply_to_message_id: int = None,
        allow_sending_without_reply: bool = None,
        reply_markup: Union[
            InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply
        ] = None,
    ) -> Message:
        """
        Use this method to send point on the map. On success, the sent Message
        is returned.

        https://core.telegram.org/bots/api/#sendlocation

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)
            latitude: Latitude of the location
            longitude: Longitude of the location
            horizontal_accuracy: The radius of uncertainty for the location,
                measured in meters; 0-1500
            live_period: Period in seconds for which the location will be
                updated (see Live Locations, should be between 60 and 86400.
            heading: For live locations, a direction in which the user is
                moving, in degrees. Must be between 1 and 360 if specified.
            proximity_alert_radius: For live locations, a maximum distance
                for proximity alerts about approaching another chat member, in
                meters. Must be between 1 and 100000 if specified.
            disable_notification: Sends the message silently. Users will
                receive a notification with no sound.
            reply_to_message_id: If the message is a reply, ID of the
                original message
            allow_sending_without_reply: Pass True, if the message should be
                sent even if the specified replied-to message is not found
            reply_markup: Additional interface options. A JSON-serialized
                object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from
                the user.

        Returns:
            Message
        """
        if reply_markup is not None:
            reply_markup = reply_markup.to_dict()

        params = {
            "chat_id": chat_id,
            "latitude": latitude,
            "longitude": longitude,
            "horizontal_accuracy": horizontal_accuracy,
            "live_period": live_period,
            "heading": heading,
            "proximity_alert_radius": proximity_alert_radius,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "allow_sending_without_reply": allow_sending_without_reply,
            "reply_markup": reply_markup,
        }
        return self._bind(
            method_name="sendLocation", params=params, telegram_type=Message
        )

    def edit_message_live_location(
        self,
        latitude: float,
        longitude: float,
        chat_id: Union[int, str] = None,
        message_id: int = None,
        inline_message_id: str = None,
        horizontal_accuracy: float = None,
        heading: int = None,
        proximity_alert_radius: int = None,
        reply_markup: InlineKeyboardMarkup = None,
    ) -> Message:
        """
        Use this method to edit live location messages. A location can be
        edited until its live_period expires or editing is explicitly disabled
        by a call to stopMessageLiveLocation. On success, if the edited message
        is not an inline message, the edited Message is returned, otherwise
        True is returned.

        https://core.telegram.org/bots/api/#editmessagelivelocation

        Args:
            latitude: Latitude of new location
            longitude: Longitude of new location
            chat_id: Required if inline_message_id is not specified. Unique
                identifier for the target chat or username of the target
                channel (in the format @channelusername)
            message_id: Required if inline_message_id is not specified.
                Identifier of the message to edit
            inline_message_id: Required if chat_id and message_id are not
                specified. Identifier of the inline message
            horizontal_accuracy: The radius of uncertainty for the location,
                measured in meters; 0-1500
            heading: Direction in which the user is moving, in degrees. Must
                be between 1 and 360 if specified.
            proximity_alert_radius: Maximum distance for proximity alerts
                about approaching another chat member, in meters. Must be
                between 1 and 100000 if specified.
            reply_markup: A JSON-serialized object for a new inline
                keyboard.

        Returns:
            Message
        """
        if reply_markup is not None:
            reply_markup = reply_markup.to_dict()

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "chat_id": chat_id,
            "message_id": message_id,
            "inline_message_id": inline_message_id,
            "horizontal_accuracy": horizontal_accuracy,
            "heading": heading,
            "proximity_alert_radius": proximity_alert_radius,
            "reply_markup": reply_markup,
        }
        return self._bind(
            method_name="editMessageLiveLocation", params=params, telegram_type=Message
        )

    def stop_message_live_location(
        self,
        chat_id: Union[int, str] = None,
        message_id: int = None,
        inline_message_id: str = None,
        reply_markup: InlineKeyboardMarkup = None,
    ) -> Message:
        """
        Use this method to stop updating a live location message before
        live_period expires. On success, if the message was sent by the bot,
        the sent Message is returned, otherwise True is returned.

        https://core.telegram.org/bots/api/#stopmessagelivelocation

        Args:
            chat_id: Required if inline_message_id is not specified. Unique
                identifier for the target chat or username of the target
                channel (in the format @channelusername)
            message_id: Required if inline_message_id is not specified.
                Identifier of the message with live location to stop
            inline_message_id: Required if chat_id and message_id are not
                specified. Identifier of the inline message
            reply_markup: A JSON-serialized object for a new inline
                keyboard.

        Returns:
            Message
        """
        if reply_markup is not None:
            reply_markup = reply_markup.to_dict()

        params = {
            "chat_id": chat_id,
            "message_id": message_id,
            "inline_message_id": inline_message_id,
            "reply_markup": reply_markup,
        }
        return self._bind(
            method_name="stopMessageLiveLocation", params=params, telegram_type=Message
        )

    def send_venue(
        self,
        chat_id: Union[int, str],
        latitude: float,
        longitude: float,
        title: str,
        address: str,
        foursquare_id: str = None,
        foursquare_type: str = None,
        google_place_id: str = None,
        google_place_type: str = None,
        disable_notification: bool = None,
        reply_to_message_id: int = None,
        allow_sending_without_reply: bool = None,
        reply_markup: Union[
            InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply
        ] = None,
    ) -> Message:
        """
        Use this method to send information about a venue. On success, the sent
        Message is returned.

        https://core.telegram.org/bots/api/#sendvenue

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)
            latitude: Latitude of the venue
            longitude: Longitude of the venue
            title: Name of the venue
            address: Address of the venue
            foursquare_id: Foursquare identifier of the venue
            foursquare_type: Foursquare type of the venue, if known. (For
                example, “arts_entertainment/default”,
                “arts_entertainment/aquarium” or “food/icecream”.)
            google_place_id: Google Places identifier of the venue
            google_place_type: Google Places type of the venue. (See
                supported types.)
            disable_notification: Sends the message silently. Users will
                receive a notification with no sound.
            reply_to_message_id: If the message is a reply, ID of the
                original message
            allow_sending_without_reply: Pass True, if the message should be
                sent even if the specified replied-to message is not found
            reply_markup: Additional interface options. A JSON-serialized
                object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from
                the user.

        Returns:
            Message
        """
        if reply_markup is not None:
            reply_markup = reply_markup.to_dict()

        params = {
            "chat_id": chat_id,
            "latitude": latitude,
            "longitude": longitude,
            "title": title,
            "address": address,
            "foursquare_id": foursquare_id,
            "foursquare_type": foursquare_type,
            "google_place_id": google_place_id,
            "google_place_type": google_place_type,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "allow_sending_without_reply": allow_sending_without_reply,
            "reply_markup": reply_markup,
        }
        return self._bind(method_name="sendVenue", params=params, telegram_type=Message)

    def send_contact(
        self,
        chat_id: Union[int, str],
        phone_number: str,
        first_name: str,
        last_name: str = None,
        vcard: str = None,
        disable_notification: bool = None,
        reply_to_message_id: int = None,
        allow_sending_without_reply: bool = None,
        reply_markup: Union[
            InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply
        ] = None,
    ) -> Message:
        """
        Use this method to send phone contacts. On success, the sent Message is
        returned.

        https://core.telegram.org/bots/api/#sendcontact

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)
            phone_number: Contact's phone number
            first_name: Contact's first name
            last_name: Contact's last name
            vcard: Additional data about the contact in the form of a vCard,
                0-2048 bytes
            disable_notification: Sends the message silently. Users will
                receive a notification with no sound.
            reply_to_message_id: If the message is a reply, ID of the
                original message
            allow_sending_without_reply: Pass True, if the message should be
                sent even if the specified replied-to message is not found
            reply_markup: Additional interface options. A JSON-serialized
                object for an inline keyboard, custom reply keyboard,
                instructions to remove keyboard or to force a reply from the
                user.

        Returns:
            Message
        """
        if reply_markup is not None:
            reply_markup = reply_markup.to_dict()

        params = {
            "chat_id": chat_id,
            "phone_number": phone_number,
            "first_name": first_name,
            "last_name": last_name,
            "vcard": vcard,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "allow_sending_without_reply": allow_sending_without_reply,
            "reply_markup": reply_markup,
        }
        return self._bind(
            method_name="sendContact", params=params, telegram_type=Message
        )

    def send_poll(
        self,
        chat_id: Union[int, str],
        question: str,
        options: List[str],
        is_anonymous: bool = None,
        type: str = None,
        allows_multiple_answers: bool = None,
        correct_option_id: int = None,
        explanation: str = None,
        explanation_parse_mode: str = None,
        explanation_entities: List[MessageEntity] = None,
        open_period: int = None,
        close_date: datetime = None,
        is_closed: bool = None,
        disable_notification: bool = None,
        reply_to_message_id: int = None,
        allow_sending_without_reply: bool = None,
        reply_markup: Union[
            InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply
        ] = None,
    ) -> Message:
        """
        Use this method to send a native poll. On success, the sent Message is
        returned.

        https://core.telegram.org/bots/api/#sendpoll

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)
            question: Poll question, 1-300 characters
            options: A JSON-serialized list of answer options, 2-10 strings
                1-100 characters each
            is_anonymous: True, if the poll needs to be anonymous, defaults
                to True
            type: Poll type, “quiz” or “regular”, defaults to “regular”
            allows_multiple_answers: True, if the poll allows multiple
                answers, ignored for polls in quiz mode, defaults to False
            correct_option_id: 0-based identifier of the correct answer
                option, required for polls in quiz mode
            explanation: Text that is shown when a user chooses an incorrect
                answer or taps on the lamp icon in a quiz-style poll, 0-200
                characters with at most 2 line feeds after entities parsing
            explanation_parse_mode: Mode for parsing entities in the
                explanation. See formatting options for more details.
            explanation_entities: List of special entities that appear in
                the poll explanation, which can be specified instead of
                parse_mode
            open_period: Amount of time in seconds the poll will be active
                after creation, 5-600. Can't be used together with close_date.
            close_date: Point in time (Unix timestamp) when the poll will be
                automatically closed. Must be at least 5 and no more than 600
                seconds in the future. Can't be used together with open_period.
            is_closed: Pass True, if the poll needs to be immediately
                closed. This can be useful for poll preview.
            disable_notification: Sends the message silently. Users will
                receive a notification with no sound.
            reply_to_message_id: If the message is a reply, ID of the
                original message
            allow_sending_without_reply: Pass True, if the message should be
                sent even if the specified replied-to message is not found
            reply_markup: Additional interface options. A JSON-serialized
                object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from
                the user.

        Returns:
            Message
        """
        if explanation_entities is not None:
            explanation_entities = [e.to_dict() for e in explanation_entities]
        if reply_markup is not None:
            reply_markup = reply_markup.to_dict()

        params = {
            "chat_id": chat_id,
            "question": question,
            "options": options,
            "is_anonymous": is_anonymous,
            "type": type,
            "allows_multiple_answers": allows_multiple_answers,
            "correct_option_id": correct_option_id,
            "explanation": explanation,
            "explanation_parse_mode": explanation_parse_mode,
            "explanation_entities": explanation_entities,
            "open_period": open_period,
            "close_date": close_date,
            "is_closed": is_closed,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "allow_sending_without_reply": allow_sending_without_reply,
            "reply_markup": reply_markup,
        }
        return self._bind(method_name="sendPoll", params=params, telegram_type=Message)

    def send_dice(
        self,
        chat_id: Union[int, str],
        emoji: str = None,
        disable_notification: bool = None,
        reply_to_message_id: int = None,
        allow_sending_without_reply: bool = None,
        reply_markup: Union[
            InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply
        ] = None,
    ) -> Message:
        """
        Use this method to send an animated emoji that will display a random
        value. On success, the sent Message is returned.

        https://core.telegram.org/bots/api/#senddice

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)
            emoji: Emoji on which the dice throw animation is based.
                Currently, must be one of “”, “”, “”, “”, “”, or “”. Dice can
                have values 1-6 for “”, “” and “”, values 1-5 for “” and “”,
                and values 1-64 for “”. Defaults to “”
            disable_notification: Sends the message silently. Users will
                receive a notification with no sound.
            reply_to_message_id: If the message is a reply, ID of the
                original message
            allow_sending_without_reply: Pass True, if the message should be
                sent even if the specified replied-to message is not found
            reply_markup: Additional interface options. A JSON-serialized
                object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from
                the user.

        Returns:
            Message
        """
        if reply_markup is not None:
            reply_markup = reply_markup.to_dict()

        params = {
            "chat_id": chat_id,
            "emoji": emoji,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "allow_sending_without_reply": allow_sending_without_reply,
            "reply_markup": reply_markup,
        }
        return self._bind(method_name="sendDice", params=params, telegram_type=Message)

    def send_chat_action(self, chat_id: Union[int, str], action: str) -> bool:
        """
        Use this method when you need to tell the user that something is
        happening on the bot's side. The status is set for 5 seconds or less
        (when a message arrives from your bot, Telegram clients clear its
        typing status). Returns True on success.

        Example: The ImageBot needs some time to process a request and upload
        the image. Instead of sending a text message along the lines of
        “Retrieving image, please wait…”, the bot may use sendChatAction with
        action = upload_photo. The user will see a “sending photo” status for
        the bot.

        We only recommend using this method when a response from the bot will
        take a noticeable amount of time to arrive.

        https://core.telegram.org/bots/api/#sendchataction

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)
            action: Type of action to broadcast. Choose one, depending on
                what the user is about to receive: typing for text messages,
                upload_photo for photos, record_video or upload_video for
                videos, record_voice or upload_voice for voice notes,
                upload_document for general files, find_location for location
                data, record_video_note or upload_video_note for video notes.

        Returns:
            bool
        """

        params = {
            "chat_id": chat_id,
            "action": action,
        }
        return self._bind(
            method_name="sendChatAction", params=params, telegram_type=bool
        )

    def get_user_profile_photos(
        self, user_id: int, offset: int = None, limit: int = None
    ) -> UserProfilePhotos:
        """
        Use this method to get a list of profile pictures for a user. Returns a
        UserProfilePhotos object.

        https://core.telegram.org/bots/api/#getuserprofilephotos

        Args:
            user_id: Unique identifier of the target user
            offset: Sequential number of the first photo to be returned. By
                default, all photos are returned.
            limit: Limits the number of photos to be retrieved. Values
                between 1-100 are accepted. Defaults to 100.

        Returns:
            UserProfilePhotos
        """

        params = {
            "user_id": user_id,
            "offset": offset,
            "limit": limit,
        }
        return self._bind(
            method_name="getUserProfilePhotos",
            params=params,
            telegram_type=UserProfilePhotos,
        )

    def get_file(self, file_id: str) -> File:
        """
        Use this method to get basic info about a file and prepare it for
        downloading. For the moment, bots can download files of up to 20MB in
        size. On success, a File object is returned. The file can then be
        downloaded via the link
        https://api.telegram.org/file/bot<token>/<file_path>, where <file_path>
        is taken from the response. It is guaranteed that the link will be
        valid for at least 1 hour. When the link expires, a new one can be
        requested by calling getFile again.

        https://core.telegram.org/bots/api/#getfile

        Args:
            file_id: File identifier to get info about

        Returns:
            File
        """

        params = {
            "file_id": file_id,
        }
        return self._bind(method_name="getFile", params=params, telegram_type=File)

    def kick_chat_member(
        self,
        chat_id: Union[int, str],
        user_id: int,
        until_date: datetime = None,
        revoke_messages: bool = None,
    ) -> bool:
        """
        Use this method to kick a user from a group, a supergroup or a channel.
        In the case of supergroups and channels, the user will not be able to
        return to the chat on their own using invite links, etc., unless
        unbanned first. The bot must be an administrator in the chat for this
        to work and must have the appropriate admin rights. Returns True on
        success.

        https://core.telegram.org/bots/api/#kickchatmember

        Args:
            chat_id: Unique identifier for the target group or username of
                the target supergroup or channel (in the format
                @channelusername)
            user_id: Unique identifier of the target user
            until_date: Date when the user will be unbanned, unix time. If
                user is banned for more than 366 days or less than 30 seconds
                from the current time they are considered to be banned forever.
                Applied for supergroups and channels only.
            revoke_messages: Pass True to delete all messages from the chat
                for the user that is being removed. If False, the user will be
                able to see messages in the group that were sent before the
                user was removed. Always True for supergroups and channels.

        Returns:
            bool
        """

        params = {
            "chat_id": chat_id,
            "user_id": user_id,
            "until_date": until_date,
            "revoke_messages": revoke_messages,
        }
        return self._bind(
            method_name="kickChatMember", params=params, telegram_type=bool
        )

    def unban_chat_member(
        self, chat_id: Union[int, str], user_id: int, only_if_banned: bool = None
    ) -> bool:
        """
        Use this method to unban a previously kicked user in a supergroup or
        channel. The user will not return to the group or channel
        automatically, but will be able to join via link, etc. The bot must be
        an administrator for this to work. By default, this method guarantees
        that after the call the user is not a member of the chat, but will be
        able to join it. So if the user is a member of the chat they will also
        be removed from the chat. If you don't want this, use the parameter
        only_if_banned. Returns True on success.

        https://core.telegram.org/bots/api/#unbanchatmember

        Args:
            chat_id: Unique identifier for the target group or username of
                the target supergroup or channel (in the format @username)
            user_id: Unique identifier of the target user
            only_if_banned: Do nothing if the user is not banned

        Returns:
            bool
        """

        params = {
            "chat_id": chat_id,
            "user_id": user_id,
            "only_if_banned": only_if_banned,
        }
        return self._bind(
            method_name="unbanChatMember", params=params, telegram_type=bool
        )

    def restrict_chat_member(
        self,
        chat_id: Union[int, str],
        user_id: int,
        permissions: ChatPermissions,
        until_date: datetime = None,
    ) -> bool:
        """
        Use this method to restrict a user in a supergroup. The bot must be an
        administrator in the supergroup for this to work and must have the
        appropriate admin rights. Pass True for all permissions to lift
        restrictions from a user. Returns True on success.

        https://core.telegram.org/bots/api/#restrictchatmember

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target supergroup (in the format @supergroupusername)
            user_id: Unique identifier of the target user
            permissions: A JSON-serialized object for new user permissions
            until_date: Date when restrictions will be lifted for the user,
                unix time. If user is restricted for more than 366 days or less
                than 30 seconds from the current time, they are considered to
                be restricted forever

        Returns:
            bool
        """
        if permissions is not None:
            permissions = permissions.to_dict()

        params = {
            "chat_id": chat_id,
            "user_id": user_id,
            "permissions": permissions,
            "until_date": until_date,
        }
        return self._bind(
            method_name="restrictChatMember", params=params, telegram_type=bool
        )

    def promote_chat_member(
        self,
        chat_id: Union[int, str],
        user_id: int,
        is_anonymous: bool = None,
        can_manage_chat: bool = None,
        can_post_messages: bool = None,
        can_edit_messages: bool = None,
        can_delete_messages: bool = None,
        can_manage_voice_chats: bool = None,
        can_restrict_members: bool = None,
        can_promote_members: bool = None,
        can_change_info: bool = None,
        can_invite_users: bool = None,
        can_pin_messages: bool = None,
    ) -> bool:
        """
        Use this method to promote or demote a user in a supergroup or a
        channel. The bot must be an administrator in the chat for this to work
        and must have the appropriate admin rights. Pass False for all boolean
        parameters to demote a user. Returns True on success.

        https://core.telegram.org/bots/api/#promotechatmember

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)
            user_id: Unique identifier of the target user
            is_anonymous: Pass True, if the administrator's presence in the
                chat is hidden
            can_manage_chat: Pass True, if the administrator can access the
                chat event log, chat statistics, message statistics in
                channels, see channel members, see anonymous administrators in
                supergroups and ignore slow mode. Implied by any other
                administrator privilege
            can_post_messages: Pass True, if the administrator can create
                channel posts, channels only
            can_edit_messages: Pass True, if the administrator can edit
                messages of other users and can pin messages, channels only
            can_delete_messages: Pass True, if the administrator can delete
                messages of other users
            can_manage_voice_chats: Pass True, if the administrator can
                manage voice chats
            can_restrict_members: Pass True, if the administrator can
                restrict, ban or unban chat members
            can_promote_members: Pass True, if the administrator can add new
                administrators with a subset of their own privileges or demote
                administrators that he has promoted, directly or indirectly
                (promoted by administrators that were appointed by him)
            can_change_info: Pass True, if the administrator can change chat
                title, photo and other settings
            can_invite_users: Pass True, if the administrator can invite new
                users to the chat
            can_pin_messages: Pass True, if the administrator can pin
                messages, supergroups only

        Returns:
            bool
        """

        params = {
            "chat_id": chat_id,
            "user_id": user_id,
            "is_anonymous": is_anonymous,
            "can_manage_chat": can_manage_chat,
            "can_post_messages": can_post_messages,
            "can_edit_messages": can_edit_messages,
            "can_delete_messages": can_delete_messages,
            "can_manage_voice_chats": can_manage_voice_chats,
            "can_restrict_members": can_restrict_members,
            "can_promote_members": can_promote_members,
            "can_change_info": can_change_info,
            "can_invite_users": can_invite_users,
            "can_pin_messages": can_pin_messages,
        }
        return self._bind(
            method_name="promoteChatMember", params=params, telegram_type=bool
        )

    def set_chat_administrator_custom_title(
        self, chat_id: Union[int, str], user_id: int, custom_title: str
    ) -> bool:
        """
        Use this method to set a custom title for an administrator in a
        supergroup promoted by the bot. Returns True on success.

        https://core.telegram.org/bots/api/#setchatadministratorcustomtitle

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target supergroup (in the format @supergroupusername)
            user_id: Unique identifier of the target user
            custom_title: New custom title for the administrator; 0-16
                characters, emoji are not allowed

        Returns:
            bool
        """

        params = {
            "chat_id": chat_id,
            "user_id": user_id,
            "custom_title": custom_title,
        }
        return self._bind(
            method_name="setChatAdministratorCustomTitle",
            params=params,
            telegram_type=bool,
        )

    def set_chat_permissions(
        self, chat_id: Union[int, str], permissions: ChatPermissions
    ) -> bool:
        """
        Use this method to set default chat permissions for all members. The
        bot must be an administrator in the group or a supergroup for this to
        work and must have the can_restrict_members admin rights. Returns True
        on success.

        https://core.telegram.org/bots/api/#setchatpermissions

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target supergroup (in the format @supergroupusername)
            permissions: New default chat permissions

        Returns:
            bool
        """
        if permissions is not None:
            permissions = permissions.to_dict()

        params = {
            "chat_id": chat_id,
            "permissions": permissions,
        }
        return self._bind(
            method_name="setChatPermissions", params=params, telegram_type=bool
        )

    def export_chat_invite_link(self, chat_id: Union[int, str]) -> str:
        """
        Use this method to generate a new primary invite link for a chat; any
        previously generated primary link is revoked. The bot must be an
        administrator in the chat for this to work and must have the
        appropriate admin rights. Returns the new invite link as String on
        success.

        https://core.telegram.org/bots/api/#exportchatinvitelink

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)

        Returns:
            str
        """

        params = {
            "chat_id": chat_id,
        }
        return self._bind(
            method_name="exportChatInviteLink", params=params, telegram_type=str
        )

    def create_chat_invite_link(
        self,
        chat_id: Union[int, str],
        expire_date: datetime = None,
        member_limit: int = None,
    ) -> ChatInviteLink:
        """
        Use this method to create an additional invite link for a chat. The bot
        must be an administrator in the chat for this to work and must have the
        appropriate admin rights. The link can be revoked using the method
        revokeChatInviteLink. Returns the new invite link as ChatInviteLink
        object.

        https://core.telegram.org/bots/api/#createchatinvitelink

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)
            expire_date: Point in time (Unix timestamp) when the link will
                expire
            member_limit: Maximum number of users that can be members of the
                chat simultaneously after joining the chat via this invite
                link; 1-99999

        Returns:
            ChatInviteLink
        """

        params = {
            "chat_id": chat_id,
            "expire_date": expire_date,
            "member_limit": member_limit,
        }
        return self._bind(
            method_name="createChatInviteLink",
            params=params,
            telegram_type=ChatInviteLink,
        )

    def edit_chat_invite_link(
        self,
        chat_id: Union[int, str],
        invite_link: str,
        expire_date: datetime = None,
        member_limit: int = None,
    ) -> ChatInviteLink:
        """
        Use this method to edit a non-primary invite link created by the bot.
        The bot must be an administrator in the chat for this to work and must
        have the appropriate admin rights. Returns the edited invite link as a
        ChatInviteLink object.

        https://core.telegram.org/bots/api/#editchatinvitelink

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)
            invite_link: The invite link to edit
            expire_date: Point in time (Unix timestamp) when the link will
                expire
            member_limit: Maximum number of users that can be members of the
                chat simultaneously after joining the chat via this invite
                link; 1-99999

        Returns:
            ChatInviteLink
        """

        params = {
            "chat_id": chat_id,
            "invite_link": invite_link,
            "expire_date": expire_date,
            "member_limit": member_limit,
        }
        return self._bind(
            method_name="editChatInviteLink",
            params=params,
            telegram_type=ChatInviteLink,
        )

    def revoke_chat_invite_link(
        self, chat_id: Union[int, str], invite_link: str
    ) -> ChatInviteLink:
        """
        Use this method to revoke an invite link created by the bot. If the
        primary link is revoked, a new link is automatically generated. The bot
        must be an administrator in the chat for this to work and must have the
        appropriate admin rights. Returns the revoked invite link as
        ChatInviteLink object.

        https://core.telegram.org/bots/api/#revokechatinvitelink

        Args:
            chat_id: Unique identifier of the target chat or username of the
                target channel (in the format @channelusername)
            invite_link: The invite link to revoke

        Returns:
            ChatInviteLink
        """

        params = {
            "chat_id": chat_id,
            "invite_link": invite_link,
        }
        return self._bind(
            method_name="revokeChatInviteLink",
            params=params,
            telegram_type=ChatInviteLink,
        )

    def set_chat_photo(self, chat_id: Union[int, str], photo: InputFile) -> bool:
        """
        Use this method to set a new profile photo for the chat. Photos can't
        be changed for private chats. The bot must be an administrator in the
        chat for this to work and must have the appropriate admin rights.
        Returns True on success.

        https://core.telegram.org/bots/api/#setchatphoto

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)
            photo: New chat photo, uploaded using multipart/form-data

        Returns:
            bool
        """
        if photo is not None:
            photo = photo.to_dict()

        params = {
            "chat_id": chat_id,
            "photo": photo,
        }
        return self._bind(method_name="setChatPhoto", params=params, telegram_type=bool)

    def delete_chat_photo(self, chat_id: Union[int, str]) -> bool:
        """
        Use this method to delete a chat photo. Photos can't be changed for
        private chats. The bot must be an administrator in the chat for this to
        work and must have the appropriate admin rights. Returns True on
        success.

        https://core.telegram.org/bots/api/#deletechatphoto

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)

        Returns:
            bool
        """

        params = {
            "chat_id": chat_id,
        }
        return self._bind(
            method_name="deleteChatPhoto", params=params, telegram_type=bool
        )

    def set_chat_title(self, chat_id: Union[int, str], title: str) -> bool:
        """
        Use this method to change the title of a chat. Titles can't be changed
        for private chats. The bot must be an administrator in the chat for
        this to work and must have the appropriate admin rights. Returns True
        on success.

        https://core.telegram.org/bots/api/#setchattitle

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)
            title: New chat title, 1-255 characters

        Returns:
            bool
        """

        params = {
            "chat_id": chat_id,
            "title": title,
        }
        return self._bind(method_name="setChatTitle", params=params, telegram_type=bool)

    def set_chat_description(
        self, chat_id: Union[int, str], description: str = None
    ) -> bool:
        """
        Use this method to change the description of a group, a supergroup or a
        channel. The bot must be an administrator in the chat for this to work
        and must have the appropriate admin rights. Returns True on success.

        https://core.telegram.org/bots/api/#setchatdescription

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)
            description: New chat description, 0-255 characters

        Returns:
            bool
        """

        params = {
            "chat_id": chat_id,
            "description": description,
        }
        return self._bind(
            method_name="setChatDescription", params=params, telegram_type=bool
        )

    def pin_chat_message(
        self,
        chat_id: Union[int, str],
        message_id: int,
        disable_notification: bool = None,
    ) -> bool:
        """
        Use this method to add a message to the list of pinned messages in a
        chat. If the chat is not a private chat, the bot must be an
        administrator in the chat for this to work and must have the
        'can_pin_messages' admin right in a supergroup or 'can_edit_messages'
        admin right in a channel. Returns True on success.

        https://core.telegram.org/bots/api/#pinchatmessage

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)
            message_id: Identifier of a message to pin
            disable_notification: Pass True, if it is not necessary to send
                a notification to all chat members about the new pinned
                message. Notifications are always disabled in channels and
                private chats.

        Returns:
            bool
        """

        params = {
            "chat_id": chat_id,
            "message_id": message_id,
            "disable_notification": disable_notification,
        }
        return self._bind(
            method_name="pinChatMessage", params=params, telegram_type=bool
        )

    def unpin_chat_message(
        self, chat_id: Union[int, str], message_id: int = None
    ) -> bool:
        """
        Use this method to remove a message from the list of pinned messages in
        a chat. If the chat is not a private chat, the bot must be an
        administrator in the chat for this to work and must have the
        'can_pin_messages' admin right in a supergroup or 'can_edit_messages'
        admin right in a channel. Returns True on success.

        https://core.telegram.org/bots/api/#unpinchatmessage

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)
            message_id: Identifier of a message to unpin. If not specified,
                the most recent pinned message (by sending date) will be
                unpinned.

        Returns:
            bool
        """

        params = {
            "chat_id": chat_id,
            "message_id": message_id,
        }
        return self._bind(
            method_name="unpinChatMessage", params=params, telegram_type=bool
        )

    def unpin_all_chat_messages(self, chat_id: Union[int, str]) -> bool:
        """
        Use this method to clear the list of pinned messages in a chat. If the
        chat is not a private chat, the bot must be an administrator in the
        chat for this to work and must have the 'can_pin_messages' admin right
        in a supergroup or 'can_edit_messages' admin right in a channel.
        Returns True on success.

        https://core.telegram.org/bots/api/#unpinallchatmessages

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)

        Returns:
            bool
        """

        params = {
            "chat_id": chat_id,
        }
        return self._bind(
            method_name="unpinAllChatMessages", params=params, telegram_type=bool
        )

    def leave_chat(self, chat_id: Union[int, str]) -> bool:
        """
        Use this method for your bot to leave a group, supergroup or channel.
        Returns True on success.

        https://core.telegram.org/bots/api/#leavechat

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target supergroup or channel (in the format
                @channelusername)

        Returns:
            bool
        """

        params = {
            "chat_id": chat_id,
        }
        return self._bind(method_name="leaveChat", params=params, telegram_type=bool)

    def get_chat(self, chat_id: Union[int, str]) -> Chat:
        """
        Use this method to get up to date information about the chat (current
        name of the user for one-on-one conversations, current username of a
        user, group or channel, etc.). Returns a Chat object on success.

        https://core.telegram.org/bots/api/#getchat

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target supergroup or channel (in the format
                @channelusername)

        Returns:
            Chat
        """

        params = {
            "chat_id": chat_id,
        }
        return self._bind(method_name="getChat", params=params, telegram_type=Chat)

    def get_chat_administrators(self, chat_id: Union[int, str]) -> ChatMember:
        """
        Use this method to get a list of administrators in a chat. On success,
        returns an Array of ChatMember objects that contains information about
        all chat administrators except other bots. If the chat is a group or a
        supergroup and no administrators were appointed, only the creator will
        be returned.

        https://core.telegram.org/bots/api/#getchatadministrators

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target supergroup or channel (in the format
                @channelusername)

        Returns:
            ChatMember
        """

        params = {
            "chat_id": chat_id,
        }
        return self._bind(
            method_name="getChatAdministrators", params=params, telegram_type=ChatMember
        )

    def get_chat_members_count(self, chat_id: Union[int, str]) -> int:
        """
        Use this method to get the number of members in a chat. Returns Int on
        success.

        https://core.telegram.org/bots/api/#getchatmemberscount

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target supergroup or channel (in the format
                @channelusername)

        Returns:
            int
        """

        params = {
            "chat_id": chat_id,
        }
        return self._bind(
            method_name="getChatMembersCount", params=params, telegram_type=int
        )

    def get_chat_member(self, chat_id: Union[int, str], user_id: int) -> ChatMember:
        """
        Use this method to get information about a member of a chat. Returns a
        ChatMember object on success.

        https://core.telegram.org/bots/api/#getchatmember

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target supergroup or channel (in the format
                @channelusername)
            user_id: Unique identifier of the target user

        Returns:
            ChatMember
        """

        params = {
            "chat_id": chat_id,
            "user_id": user_id,
        }
        return self._bind(
            method_name="getChatMember", params=params, telegram_type=ChatMember
        )

    def set_chat_sticker_set(
        self, chat_id: Union[int, str], sticker_set_name: str
    ) -> bool:
        """
        Use this method to set a new group sticker set for a supergroup. The
        bot must be an administrator in the chat for this to work and must have
        the appropriate admin rights. Use the field can_set_sticker_set
        optionally returned in getChat requests to check if the bot can use
        this method. Returns True on success.

        https://core.telegram.org/bots/api/#setchatstickerset

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target supergroup (in the format @supergroupusername)
            sticker_set_name: Name of the sticker set to be set as the group
                sticker set

        Returns:
            bool
        """

        params = {
            "chat_id": chat_id,
            "sticker_set_name": sticker_set_name,
        }
        return self._bind(
            method_name="setChatStickerSet", params=params, telegram_type=bool
        )

    def delete_chat_sticker_set(self, chat_id: Union[int, str]) -> bool:
        """
        Use this method to delete a group sticker set from a supergroup. The
        bot must be an administrator in the chat for this to work and must have
        the appropriate admin rights. Use the field can_set_sticker_set
        optionally returned in getChat requests to check if the bot can use
        this method. Returns True on success.

        https://core.telegram.org/bots/api/#deletechatstickerset

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target supergroup (in the format @supergroupusername)

        Returns:
            bool
        """

        params = {
            "chat_id": chat_id,
        }
        return self._bind(
            method_name="deleteChatStickerSet", params=params, telegram_type=bool
        )

    def answer_callback_query(
        self,
        callback_query_id: str,
        text: str = None,
        show_alert: bool = None,
        url: str = None,
        cache_time: int = None,
    ) -> bool:
        """
        Use this method to send answers to callback queries sent from inline
        keyboards. The answer will be displayed to the user as a notification
        at the top of the chat screen or as an alert. On success, True is
        returned.

        Alternatively, the user can be redirected to the specified Game URL.
        For this option to work, you must first create a game for your bot via
        @Botfather and accept the terms. Otherwise, you may use links like
        t.me/your_bot?start=XXXX that open your bot with a parameter.

        https://core.telegram.org/bots/api/#answercallbackquery

        Args:
            callback_query_id: Unique identifier for the query to be
                answered
            text: Text of the notification. If not specified, nothing will
                be shown to the user, 0-200 characters
            show_alert: If true, an alert will be shown by the client
                instead of a notification at the top of the chat screen.
                Defaults to false.
            url: URL that will be opened by the user's client. If you have
                created a Game and accepted the conditions via @Botfather,
                specify the URL that opens your game — note that this will only
                work if the query comes from a callback_game button.Otherwise,
                you may use links like t.me/your_bot?start=XXXX that open your
                bot with a parameter.
            cache_time: The maximum amount of time in seconds that the
                result of the callback query may be cached client-side.
                Telegram apps will support caching starting in version 3.14.
                Defaults to 0.

        Returns:
            bool
        """

        params = {
            "callback_query_id": callback_query_id,
            "text": text,
            "show_alert": show_alert,
            "url": url,
            "cache_time": cache_time,
        }
        return self._bind(
            method_name="answerCallbackQuery", params=params, telegram_type=bool
        )

    def set_my_commands(self, commands: List[BotCommand]) -> bool:
        """
        Use this method to change the list of the bot's commands. Returns True
        on success.

        https://core.telegram.org/bots/api/#setmycommands

        Args:
            commands: A JSON-serialized list of bot commands to be set as
                the list of the bot's commands. At most 100 commands can be
                specified.

        Returns:
            bool
        """
        if commands is not None:
            commands = [c.to_dict() for c in commands]

        params = {
            "commands": commands,
        }
        return self._bind(
            method_name="setMyCommands", params=params, telegram_type=bool
        )

    def get_my_commands(
        self,
    ) -> BotCommand:
        """
        Use this method to get the current list of the bot's commands. Requires
        no parameters. Returns Array of BotCommand on success.

        https://core.telegram.org/bots/api/#getmycommands


        Returns:
            BotCommand
        """
        return self._bind(method_name="getMyCommands", telegram_type=BotCommand)

    def edit_message_text(
        self,
        text: str,
        chat_id: Union[int, str] = None,
        message_id: int = None,
        inline_message_id: str = None,
        parse_mode: str = None,
        entities: List[MessageEntity] = None,
        disable_web_page_preview: bool = None,
        reply_markup: InlineKeyboardMarkup = None,
    ) -> Message:
        """
        Use this method to edit text and game messages. On success, if the
        edited message is not an inline message, the edited Message is
        returned, otherwise True is returned.

        https://core.telegram.org/bots/api/#editmessagetext

        Args:
            text: New text of the message, 1-4096 characters after entities
                parsing
            chat_id: Required if inline_message_id is not specified. Unique
                identifier for the target chat or username of the target
                channel (in the format @channelusername)
            message_id: Required if inline_message_id is not specified.
                Identifier of the message to edit
            inline_message_id: Required if chat_id and message_id are not
                specified. Identifier of the inline message
            parse_mode: Mode for parsing entities in the message text. See
                formatting options for more details.
            entities: List of special entities that appear in message text,
                which can be specified instead of parse_mode
            disable_web_page_preview: Disables link previews for links in
                this message
            reply_markup: A JSON-serialized object for an inline keyboard.

        Returns:
            Message
        """
        if entities is not None:
            entities = [e.to_dict() for e in entities]
        if reply_markup is not None:
            reply_markup = json.dumps(reply_markup.to_dict())

        params = {
            "text": text,
            "chat_id": chat_id,
            "message_id": message_id,
            "inline_message_id": inline_message_id,
            "parse_mode": parse_mode,
            "entities": entities,
            "disable_web_page_preview": disable_web_page_preview,
            "reply_markup": reply_markup,
        }
        return self._bind(
            method_name="editMessageText", params=params, telegram_type=Message
        )

    def edit_message_caption(
        self,
        chat_id: Union[int, str] = None,
        message_id: int = None,
        inline_message_id: str = None,
        caption: str = None,
        parse_mode: str = None,
        caption_entities: List[MessageEntity] = None,
        reply_markup: InlineKeyboardMarkup = None,
    ) -> Message:
        """
        Use this method to edit captions of messages. On success, if the edited
        message is not an inline message, the edited Message is returned,
        otherwise True is returned.

        https://core.telegram.org/bots/api/#editmessagecaption

        Args:
            chat_id: Required if inline_message_id is not specified. Unique
                identifier for the target chat or username of the target
                channel (in the format @channelusername)
            message_id: Required if inline_message_id is not specified.
                Identifier of the message to edit
            inline_message_id: Required if chat_id and message_id are not
                specified. Identifier of the inline message
            caption: New caption of the message, 0-1024 characters after
                entities parsing
            parse_mode: Mode for parsing entities in the message caption.
                See formatting options for more details.
            caption_entities: List of special entities that appear in the
                caption, which can be specified instead of parse_mode
            reply_markup: A JSON-serialized object for an inline keyboard.

        Returns:
            Message
        """
        if caption_entities is not None:
            caption_entities = [c.to_dict() for c in caption_entities]
        if reply_markup is not None:
            reply_markup = reply_markup.to_dict()

        params = {
            "chat_id": chat_id,
            "message_id": message_id,
            "inline_message_id": inline_message_id,
            "caption": caption,
            "parse_mode": parse_mode,
            "caption_entities": caption_entities,
            "reply_markup": reply_markup,
        }
        return self._bind(
            method_name="editMessageCaption", params=params, telegram_type=Message
        )

    def edit_message_media(
        self,
        media: Union[
            InputMediaAnimation,
            InputMediaDocument,
            InputMediaAudio,
            InputMediaPhoto,
            InputMediaVideo,
        ],
        chat_id: Union[int, str] = None,
        message_id: int = None,
        inline_message_id: str = None,
        reply_markup: InlineKeyboardMarkup = None,
    ) -> Message:
        """
        Use this method to edit animation, audio, document, photo, or video
        messages. If a message is part of a message album, then it can be
        edited only to an audio for audio albums, only to a document for
        document albums and to a photo or a video otherwise. When an inline
        message is edited, a new file can't be uploaded. Use a previously
        uploaded file via its file_id or specify a URL. On success, if the
        edited message was sent by the bot, the edited Message is returned,
        otherwise True is returned.

        https://core.telegram.org/bots/api/#editmessagemedia

        Args:
            media: A JSON-serialized object for a new media content of the
                message
            chat_id: Required if inline_message_id is not specified. Unique
                identifier for the target chat or username of the target
                channel (in the format @channelusername)
            message_id: Required if inline_message_id is not specified.
                Identifier of the message to edit
            inline_message_id: Required if chat_id and message_id are not
                specified. Identifier of the inline message
            reply_markup: A JSON-serialized object for a new inline
                keyboard.

        Returns:
            Message
        """
        if media is not None:
            media = media.to_dict()
        if reply_markup is not None:
            reply_markup = reply_markup.to_dict()

        params = {
            "media": media,
            "chat_id": chat_id,
            "message_id": message_id,
            "inline_message_id": inline_message_id,
            "reply_markup": reply_markup,
        }
        return self._bind(
            method_name="editMessageMedia", params=params, telegram_type=Message
        )

    def edit_message_reply_markup(
        self,
        chat_id: Union[int, str] = None,
        message_id: int = None,
        inline_message_id: str = None,
        reply_markup: InlineKeyboardMarkup = None,
    ) -> Message:
        """
        Use this method to edit only the reply markup of messages. On success,
        if the edited message is not an inline message, the edited Message is
        returned, otherwise True is returned.

        https://core.telegram.org/bots/api/#editmessagereplymarkup

        Args:
            chat_id: Required if inline_message_id is not specified. Unique
                identifier for the target chat or username of the target
                channel (in the format @channelusername)
            message_id: Required if inline_message_id is not specified.
                Identifier of the message to edit
            inline_message_id: Required if chat_id and message_id are not
                specified. Identifier of the inline message
            reply_markup: A JSON-serialized object for an inline keyboard.

        Returns:
            Message
        """
        if reply_markup is not None:
            reply_markup = reply_markup.to_dict()

        params = {
            "chat_id": chat_id,
            "message_id": message_id,
            "inline_message_id": inline_message_id,
            "reply_markup": reply_markup,
        }
        return self._bind(
            method_name="editMessageReplyMarkup", params=params, telegram_type=Message
        )

    def stop_poll(
        self,
        chat_id: Union[int, str],
        message_id: int,
        reply_markup: InlineKeyboardMarkup = None,
    ) -> Poll:
        """
        Use this method to stop a poll which was sent by the bot. On success,
        the stopped Poll with the final results is returned.

        https://core.telegram.org/bots/api/#stoppoll

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)
            message_id: Identifier of the original message with the poll
            reply_markup: A JSON-serialized object for a new message inline
                keyboard.

        Returns:
            Poll
        """
        if reply_markup is not None:
            reply_markup = reply_markup.to_dict()

        params = {
            "chat_id": chat_id,
            "message_id": message_id,
            "reply_markup": reply_markup,
        }
        return self._bind(method_name="stopPoll", params=params, telegram_type=Poll)

    def delete_message(self, chat_id: Union[int, str], message_id: int) -> bool:
        """
        Use this method to delete a message, including service messages, with
        the following limitations:- A message can only be deleted if it was
        sent less than 48 hours ago.- A dice message in a private chat can only
        be deleted if it was sent more than 24 hours ago.- Bots can delete
        outgoing messages in private chats, groups, and supergroups.- Bots can
        delete incoming messages in private chats.- Bots granted
        can_post_messages permissions can delete outgoing messages in
        channels.- If the bot is an administrator of a group, it can delete any
        message there.- If the bot has can_delete_messages permission in a
        supergroup or a channel, it can delete any message there.Returns True
        on success.

        https://core.telegram.org/bots/api/#deletemessage

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)
            message_id: Identifier of the message to delete

        Returns:
            bool
        """

        params = {
            "chat_id": chat_id,
            "message_id": message_id,
        }
        return self._bind(
            method_name="deleteMessage", params=params, telegram_type=bool
        )

    def send_sticker(
        self,
        chat_id: Union[int, str],
        sticker: Union[InputFile, str],
        disable_notification: bool = None,
        reply_to_message_id: int = None,
        allow_sending_without_reply: bool = None,
        reply_markup: Union[
            InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply
        ] = None,
    ) -> Message:
        """
        Use this method to send static .WEBP or animated .TGS stickers. On
        success, the sent Message is returned.

        https://core.telegram.org/bots/api/#sendsticker

        Args:
            chat_id: Unique identifier for the target chat or username of
                the target channel (in the format @channelusername)
            sticker: Sticker to send. Pass a file_id as String to send a
                file that exists on the Telegram servers (recommended), pass an
                HTTP URL as a String for Telegram to get a .WEBP file from the
                Internet, or upload a new one using multipart/form-data. More
                info on Sending Files »
            disable_notification: Sends the message silently. Users will
                receive a notification with no sound.
            reply_to_message_id: If the message is a reply, ID of the
                original message
            allow_sending_without_reply: Pass True, if the message should be
                sent even if the specified replied-to message is not found
            reply_markup: Additional interface options. A JSON-serialized
                object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from
                the user.

        Returns:
            Message
        """
        if sticker is not None and hasattr(sticker, "to_dict"):
            sticker = sticker.to_dict()
        if reply_markup is not None:
            reply_markup = reply_markup.to_dict()

        params = {
            "chat_id": chat_id,
            "sticker": sticker,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "allow_sending_without_reply": allow_sending_without_reply,
            "reply_markup": reply_markup,
        }
        return self._bind(
            method_name="sendSticker", params=params, telegram_type=Message
        )

    def get_sticker_set(self, name: str) -> StickerSet:
        """
        Use this method to get a sticker set. On success, a StickerSet object
        is returned.

        https://core.telegram.org/bots/api/#getstickerset

        Args:
            name: Name of the sticker set

        Returns:
            StickerSet
        """

        params = {
            "name": name,
        }
        return self._bind(
            method_name="getStickerSet", params=params, telegram_type=StickerSet
        )

    def upload_sticker_file(self, user_id: int, png_sticker: InputFile) -> File:
        """
        Use this method to upload a .PNG file with a sticker for later use in
        createNewStickerSet and addStickerToSet methods (can be used multiple
        times). Returns the uploaded File on success.

        https://core.telegram.org/bots/api/#uploadstickerfile

        Args:
            user_id: User identifier of sticker file owner
            png_sticker: PNG image with the sticker, must be up to 512
                kilobytes in size, dimensions must not exceed 512px, and either
                width or height must be exactly 512px. More info on Sending
                Files »

        Returns:
            File
        """
        if png_sticker is not None:
            png_sticker = png_sticker.to_dict()

        params = {
            "user_id": user_id,
            "png_sticker": png_sticker,
        }
        return self._bind(
            method_name="uploadStickerFile", params=params, telegram_type=File
        )

    def create_new_sticker_set(
        self,
        user_id: int,
        name: str,
        title: str,
        emojis: str,
        png_sticker: Union[InputFile, str] = None,
        tgs_sticker: InputFile = None,
        contains_masks: bool = None,
        mask_position: MaskPosition = None,
    ) -> bool:
        """
        Use this method to create a new sticker set owned by a user. The bot
        will be able to edit the sticker set thus created. You must use exactly
        one of the fields png_sticker or tgs_sticker. Returns True on success.

        https://core.telegram.org/bots/api/#createnewstickerset

        Args:
            user_id: User identifier of created sticker set owner
            name: Short name of sticker set, to be used in t.me/addstickers/
                URLs (e.g., animals). Can contain only english letters, digits
                and underscores. Must begin with a letter, can't contain
                consecutive underscores and must end in “_by_<bot username>”.
                <bot_username> is case insensitive. 1-64 characters.
            title: Sticker set title, 1-64 characters
            emojis: One or more emoji corresponding to the sticker
            png_sticker: PNG image with the sticker, must be up to 512
                kilobytes in size, dimensions must not exceed 512px, and either
                width or height must be exactly 512px. Pass a file_id as a
                String to send a file that already exists on the Telegram
                servers, pass an HTTP URL as a String for Telegram to get a
                file from the Internet, or upload a new one using
                multipart/form-data. More info on Sending Files »
            tgs_sticker: TGS animation with the sticker, uploaded using
                multipart/form-data. See
                https://core.telegram.org/animated_stickers#technical-requirements
                for technical requirements
            contains_masks: Pass True, if a set of mask stickers should be
                created
            mask_position: A JSON-serialized object for position where the
                mask should be placed on faces

        Returns:
            bool
        """
        if png_sticker is not None and hasattr(png_sticker, "to_dict"):
            png_sticker = png_sticker.to_dict()
        if tgs_sticker is not None:
            tgs_sticker = tgs_sticker.to_dict()
        if mask_position is not None:
            mask_position = mask_position.to_dict()

        params = {
            "user_id": user_id,
            "name": name,
            "title": title,
            "emojis": emojis,
            "png_sticker": png_sticker,
            "tgs_sticker": tgs_sticker,
            "contains_masks": contains_masks,
            "mask_position": mask_position,
        }
        return self._bind(
            method_name="createNewStickerSet", params=params, telegram_type=bool
        )

    def add_sticker_to_set(
        self,
        user_id: int,
        name: str,
        emojis: str,
        png_sticker: Union[InputFile, str] = None,
        tgs_sticker: InputFile = None,
        mask_position: MaskPosition = None,
    ) -> bool:
        """
        Use this method to add a new sticker to a set created by the bot. You
        must use exactly one of the fields png_sticker or tgs_sticker. Animated
        stickers can be added to animated sticker sets and only to them.
        Animated sticker sets can have up to 50 stickers. Static sticker sets
        can have up to 120 stickers. Returns True on success.

        https://core.telegram.org/bots/api/#addstickertoset

        Args:
            user_id: User identifier of sticker set owner
            name: Sticker set name
            emojis: One or more emoji corresponding to the sticker
            png_sticker: PNG image with the sticker, must be up to 512
                kilobytes in size, dimensions must not exceed 512px, and either
                width or height must be exactly 512px. Pass a file_id as a
                String to send a file that already exists on the Telegram
                servers, pass an HTTP URL as a String for Telegram to get a
                file from the Internet, or upload a new one using
                multipart/form-data. More info on Sending Files »
            tgs_sticker: TGS animation with the sticker, uploaded using
                multipart/form-data. See
                https://core.telegram.org/animated_stickers#technical-requirements
                for technical requirements
            mask_position: A JSON-serialized object for position where the
                mask should be placed on faces

        Returns:
            bool
        """
        if png_sticker is not None and hasattr(png_sticker, "to_dict"):
            png_sticker = png_sticker.to_dict()
        if tgs_sticker is not None:
            tgs_sticker = tgs_sticker.to_dict()
        if mask_position is not None:
            mask_position = mask_position.to_dict()

        params = {
            "user_id": user_id,
            "name": name,
            "emojis": emojis,
            "png_sticker": png_sticker,
            "tgs_sticker": tgs_sticker,
            "mask_position": mask_position,
        }
        return self._bind(
            method_name="addStickerToSet", params=params, telegram_type=bool
        )

    def set_sticker_position_in_set(self, sticker: str, position: int) -> bool:
        """
        Use this method to move a sticker in a set created by the bot to a
        specific position. Returns True on success.

        https://core.telegram.org/bots/api/#setstickerpositioninset

        Args:
            sticker: File identifier of the sticker
            position: New sticker position in the set, zero-based

        Returns:
            bool
        """

        params = {
            "sticker": sticker,
            "position": position,
        }
        return self._bind(
            method_name="setStickerPositionInSet", params=params, telegram_type=bool
        )

    def delete_sticker_from_set(self, sticker: str) -> bool:
        """
        Use this method to delete a sticker from a set created by the bot.
        Returns True on success.

        https://core.telegram.org/bots/api/#deletestickerfromset

        Args:
            sticker: File identifier of the sticker

        Returns:
            bool
        """

        params = {
            "sticker": sticker,
        }
        return self._bind(
            method_name="deleteStickerFromSet", params=params, telegram_type=bool
        )

    def set_sticker_set_thumb(
        self, name: str, user_id: int, thumb: Union[InputFile, str] = None
    ) -> bool:
        """
        Use this method to set the thumbnail of a sticker set. Animated
        thumbnails can be set for animated sticker sets only. Returns True on
        success.

        https://core.telegram.org/bots/api/#setstickersetthumb

        Args:
            name: Sticker set name
            user_id: User identifier of the sticker set owner
            thumb: A PNG image with the thumbnail, must be up to 128
                kilobytes in size and have width and height exactly 100px, or a
                TGS animation with the thumbnail up to 32 kilobytes in size;
                see
                https://core.telegram.org/animated_stickers#technical-requirements
                for animated sticker technical requirements. Pass a file_id as
                a String to send a file that already exists on the Telegram
                servers, pass an HTTP URL as a String for Telegram to get a
                file from the Internet, or upload a new one using
                multipart/form-data. More info on Sending Files ». Animated
                sticker set thumbnail can't be uploaded via HTTP URL.

        Returns:
            bool
        """
        if thumb is not None and hasattr(thumb, "to_dict"):
            thumb = thumb.to_dict()

        params = {
            "name": name,
            "user_id": user_id,
            "thumb": thumb,
        }
        return self._bind(
            method_name="setStickerSetThumb", params=params, telegram_type=bool
        )

    def answer_inline_query(
        self,
        inline_query_id: str,
        results: List[
            Union[
                InlineQueryResultCachedAudio,
                InlineQueryResultCachedDocument,
                InlineQueryResultCachedGif,
                InlineQueryResultCachedMpeg4Gif,
                InlineQueryResultCachedPhoto,
                InlineQueryResultCachedSticker,
                InlineQueryResultCachedVideo,
                InlineQueryResultCachedVoice,
                InlineQueryResultArticle,
                InlineQueryResultAudio,
                InlineQueryResultContact,
                InlineQueryResultGame,
                InlineQueryResultDocument,
                InlineQueryResultGif,
                InlineQueryResultLocation,
                InlineQueryResultMpeg4Gif,
                InlineQueryResultPhoto,
                InlineQueryResultVenue,
                InlineQueryResultVideo,
                InlineQueryResultVoice,
            ]
        ],
        cache_time: int = None,
        is_personal: bool = None,
        next_offset: str = None,
        switch_pm_text: str = None,
        switch_pm_parameter: str = None,
    ) -> bool:
        """
        Use this method to send answers to an inline query. On success, True is
        returned.No more than 50 results per query are allowed.

        https://core.telegram.org/bots/api/#answerinlinequery

        Args:
            inline_query_id: Unique identifier for the answered query
            results: A JSON-serialized array of results for the inline query
            cache_time: The maximum amount of time in seconds that the
                result of the inline query may be cached on the server.
                Defaults to 300.
            is_personal: Pass True, if results may be cached on the server
                side only for the user that sent the query. By default, results
                may be returned to any user who sends the same query
            next_offset: Pass the offset that a client should send in the
                next query with the same text to receive more results. Pass an
                empty string if there are no more results or if you don't
                support pagination. Offset length can't exceed 64 bytes.
            switch_pm_text: If passed, clients will display a button with
                specified text that switches the user to a private chat with
                the bot and sends the bot a start message with the parameter
                switch_pm_parameter
            switch_pm_parameter: Deep-linking parameter for the /start
                message sent to the bot when user presses the switch button.
                1-64 characters, only A-Z, a-z, 0-9, _ and - are
                allowed.Example: An inline bot that sends YouTube videos can
                ask the user to connect the bot to their YouTube account to
                adapt search results accordingly. To do this, it displays a
                'Connect your YouTube account' button above the results, or
                even before showing any. The user presses the button, switches
                to a private chat with the bot and, in doing so, passes a start
                parameter that instructs the bot to return an oauth link. Once
                done, the bot can offer a switch_inline button so that the user
                can easily return to the chat where they wanted to use the
                bot's inline capabilities.

        Returns:
            bool
        """
        if results is not None:
            results = [r.to_dict() for r in results]

        params = {
            "inline_query_id": inline_query_id,
            "results": results,
            "cache_time": cache_time,
            "is_personal": is_personal,
            "next_offset": next_offset,
            "switch_pm_text": switch_pm_text,
            "switch_pm_parameter": switch_pm_parameter,
        }
        return self._bind(
            method_name="answerInlineQuery", params=params, telegram_type=bool
        )

    def send_invoice(
        self,
        chat_id: int,
        title: str,
        description: str,
        payload: str,
        provider_token: str,
        start_parameter: str,
        currency: str,
        prices: List[LabeledPrice],
        provider_data: str = None,
        photo_url: str = None,
        photo_size: int = None,
        photo_width: int = None,
        photo_height: int = None,
        need_name: bool = None,
        need_phone_number: bool = None,
        need_email: bool = None,
        need_shipping_address: bool = None,
        send_phone_number_to_provider: bool = None,
        send_email_to_provider: bool = None,
        is_flexible: bool = None,
        disable_notification: bool = None,
        reply_to_message_id: int = None,
        allow_sending_without_reply: bool = None,
        reply_markup: InlineKeyboardMarkup = None,
    ) -> Message:
        """
        Use this method to send invoices. On success, the sent Message is
        returned.

        https://core.telegram.org/bots/api/#sendinvoice

        Args:
            chat_id: Unique identifier for the target private chat
            title: Product name, 1-32 characters
            description: Product description, 1-255 characters
            payload: Bot-defined invoice payload, 1-128 bytes. This will not
                be displayed to the user, use for your internal processes.
            provider_token: Payments provider token, obtained via Botfather
            start_parameter: Unique deep-linking parameter that can be used
                to generate this invoice when used as a start parameter
            currency: Three-letter ISO 4217 currency code, see more on
                currencies
            prices: Price breakdown, a JSON-serialized list of components
                (e.g. product price, tax, discount, delivery cost, delivery
                tax, bonus, etc.)
            provider_data: A JSON-serialized data about the invoice, which
                will be shared with the payment provider. A detailed
                description of required fields should be provided by the
                payment provider.
            photo_url: URL of the product photo for the invoice. Can be a
                photo of the goods or a marketing image for a service. People
                like it better when they see what they are paying for.
            photo_size: Photo size
            photo_width: Photo width
            photo_height: Photo height
            need_name: Pass True, if you require the user's full name to
                complete the order
            need_phone_number: Pass True, if you require the user's phone
                number to complete the order
            need_email: Pass True, if you require the user's email address
                to complete the order
            need_shipping_address: Pass True, if you require the user's
                shipping address to complete the order
            send_phone_number_to_provider: Pass True, if user's phone number
                should be sent to provider
            send_email_to_provider: Pass True, if user's email address
                should be sent to provider
            is_flexible: Pass True, if the final price depends on the
                shipping method
            disable_notification: Sends the message silently. Users will
                receive a notification with no sound.
            reply_to_message_id: If the message is a reply, ID of the
                original message
            allow_sending_without_reply: Pass True, if the message should be
                sent even if the specified replied-to message is not found
            reply_markup: A JSON-serialized object for an inline keyboard.
                If empty, one 'Pay total price' button will be shown. If not
                empty, the first button must be a Pay button.

        Returns:
            Message
        """
        if prices is not None:
            prices = [p.to_dict() for p in prices]
        if reply_markup is not None:
            reply_markup = reply_markup.to_dict()

        params = {
            "chat_id": chat_id,
            "title": title,
            "description": description,
            "payload": payload,
            "provider_token": provider_token,
            "start_parameter": start_parameter,
            "currency": currency,
            "prices": prices,
            "provider_data": provider_data,
            "photo_url": photo_url,
            "photo_size": photo_size,
            "photo_width": photo_width,
            "photo_height": photo_height,
            "need_name": need_name,
            "need_phone_number": need_phone_number,
            "need_email": need_email,
            "need_shipping_address": need_shipping_address,
            "send_phone_number_to_provider": send_phone_number_to_provider,
            "send_email_to_provider": send_email_to_provider,
            "is_flexible": is_flexible,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "allow_sending_without_reply": allow_sending_without_reply,
            "reply_markup": reply_markup,
        }
        return self._bind(
            method_name="sendInvoice", params=params, telegram_type=Message
        )

    def answer_shipping_query(
        self,
        shipping_query_id: str,
        ok: bool,
        shipping_options: List[ShippingOption] = None,
        error_message: str = None,
    ) -> bool:
        """
        If you sent an invoice requesting a shipping address and the parameter
        is_flexible was specified, the Bot API will send an Update with a
        shipping_query field to the bot. Use this method to reply to shipping
        queries. On success, True is returned.

        https://core.telegram.org/bots/api/#answershippingquery

        Args:
            shipping_query_id: Unique identifier for the query to be
                answered
            ok: Specify True if delivery to the specified address is
                possible and False if there are any problems (for example, if
                delivery to the specified address is not possible)
            shipping_options: Required if ok is True. A JSON-serialized
                array of available shipping options.
            error_message: Required if ok is False. Error message in human
                readable form that explains why it is impossible to complete
                the order (e.g. "Sorry, delivery to your desired address is
                unavailable'). Telegram will display this message to the user.

        Returns:
            bool
        """
        if shipping_options is not None:
            shipping_options = [s.to_dict() for s in shipping_options]

        params = {
            "shipping_query_id": shipping_query_id,
            "ok": ok,
            "shipping_options": shipping_options,
            "error_message": error_message,
        }
        return self._bind(
            method_name="answerShippingQuery", params=params, telegram_type=bool
        )

    def answer_pre_checkout_query(
        self, pre_checkout_query_id: str, ok: bool, error_message: str = None
    ) -> bool:
        """
        Once the user has confirmed their payment and shipping details, the Bot
        API sends the final confirmation in the form of an Update with the
        field pre_checkout_query. Use this method to respond to such
        pre-checkout queries. On success, True is returned. Note: The Bot API
        must receive an answer within 10 seconds after the pre-checkout query
        was sent.

        https://core.telegram.org/bots/api/#answerprecheckoutquery

        Args:
            pre_checkout_query_id: Unique identifier for the query to be
                answered
            ok: Specify True if everything is alright (goods are available,
                etc.) and the bot is ready to proceed with the order. Use False
                if there are any problems.
            error_message: Required if ok is False. Error message in human
                readable form that explains the reason for failure to proceed
                with the checkout (e.g. "Sorry, somebody just bought the last
                of our amazing black T-shirts while you were busy filling out
                your payment details. Please choose a different color or
                garment!"). Telegram will display this message to the user.

        Returns:
            bool
        """

        params = {
            "pre_checkout_query_id": pre_checkout_query_id,
            "ok": ok,
            "error_message": error_message,
        }
        return self._bind(
            method_name="answerPreCheckoutQuery", params=params, telegram_type=bool
        )

    def set_passport_data_errors(
        self,
        user_id: int,
        errors: List[
            Union[
                PassportElementErrorDataField,
                PassportElementErrorFrontSide,
                PassportElementErrorReverseSide,
                PassportElementErrorSelfie,
                PassportElementErrorFile,
                PassportElementErrorFiles,
                PassportElementErrorTranslationFile,
                PassportElementErrorTranslationFiles,
                PassportElementErrorUnspecified,
            ]
        ],
    ) -> bool:
        """
        Informs a user that some of the Telegram Passport elements they
        provided contains errors. The user will not be able to re-submit their
        Passport to you until the errors are fixed (the contents of the field
        for which you returned the error must change). Returns True on success.

        Use this if the data submitted by the user doesn't satisfy the
        standards your service requires for any reason. For example, if a
        birthday date seems invalid, a submitted document is blurry, a scan
        shows evidence of tampering, etc. Supply some details in the error
        message to make sure the user knows how to correct the issues.

        https://core.telegram.org/bots/api/#setpassportdataerrors

        Args:
            user_id: User identifier
            errors: A JSON-serialized array describing the errors

        Returns:
            bool
        """
        if errors is not None:
            errors = [e.to_dict() for e in errors]

        params = {
            "user_id": user_id,
            "errors": errors,
        }
        return self._bind(
            method_name="setPassportDataErrors", params=params, telegram_type=bool
        )

    def send_game(
        self,
        chat_id: int,
        game_short_name: str,
        disable_notification: bool = None,
        reply_to_message_id: int = None,
        allow_sending_without_reply: bool = None,
        reply_markup: InlineKeyboardMarkup = None,
    ) -> Message:
        """
        Use this method to send a game. On success, the sent Message is
        returned.

        https://core.telegram.org/bots/api/#sendgame

        Args:
            chat_id: Unique identifier for the target chat
            game_short_name: Short name of the game, serves as the unique
                identifier for the game. Set up your games via Botfather.
            disable_notification: Sends the message silently. Users will
                receive a notification with no sound.
            reply_to_message_id: If the message is a reply, ID of the
                original message
            allow_sending_without_reply: Pass True, if the message should be
                sent even if the specified replied-to message is not found
            reply_markup: A JSON-serialized object for an inline keyboard.
                If empty, one 'Play game_title' button will be shown. If not
                empty, the first button must launch the game.

        Returns:
            Message
        """
        if reply_markup is not None:
            reply_markup = reply_markup.to_dict()

        params = {
            "chat_id": chat_id,
            "game_short_name": game_short_name,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "allow_sending_without_reply": allow_sending_without_reply,
            "reply_markup": reply_markup,
        }
        return self._bind(method_name="sendGame", params=params, telegram_type=Message)

    def set_game_score(
        self,
        user_id: int,
        score: int,
        force: bool = None,
        disable_edit_message: bool = None,
        chat_id: int = None,
        message_id: int = None,
        inline_message_id: str = None,
    ) -> Message:
        """
        Use this method to set the score of the specified user in a game. On
        success, if the message was sent by the bot, returns the edited
        Message, otherwise returns True. Returns an error, if the new score is
        not greater than the user's current score in the chat and force is
        False.

        https://core.telegram.org/bots/api/#setgamescore

        Args:
            user_id: User identifier
            score: New score, must be non-negative
            force: Pass True, if the high score is allowed to decrease. This
                can be useful when fixing mistakes or banning cheaters
            disable_edit_message: Pass True, if the game message should not
                be automatically edited to include the current scoreboard
            chat_id: Required if inline_message_id is not specified. Unique
                identifier for the target chat
            message_id: Required if inline_message_id is not specified.
                Identifier of the sent message
            inline_message_id: Required if chat_id and message_id are not
                specified. Identifier of the inline message

        Returns:
            Message
        """

        params = {
            "user_id": user_id,
            "score": score,
            "force": force,
            "disable_edit_message": disable_edit_message,
            "chat_id": chat_id,
            "message_id": message_id,
            "inline_message_id": inline_message_id,
        }
        return self._bind(
            method_name="setGameScore", params=params, telegram_type=Message
        )

    def get_game_high_scores(
        self,
        user_id: int,
        chat_id: int = None,
        message_id: int = None,
        inline_message_id: str = None,
    ) -> List[GameHighScore]:
        """
        Use this method to get data for high score tables. Will return the
        score of the specified user and several of their neighbors in a game.
        On success, returns an Array of GameHighScore objects.

        This method will currently return scores for the target user, plus two
        of their closest neighbors on each side. Will also return the top three
        users if the user and his neighbors are not among them. Please note
        that this behavior is subject to change.

        https://core.telegram.org/bots/api/#getgamehighscores

        Args:
            user_id: Target user id
            chat_id: Required if inline_message_id is not specified. Unique
                identifier for the target chat
            message_id: Required if inline_message_id is not specified.
                Identifier of the sent message
            inline_message_id: Required if chat_id and message_id are not
                specified. Identifier of the inline message

        Returns:
            List[GameHighScore]
        """

        params = {
            "user_id": user_id,
            "chat_id": chat_id,
            "message_id": message_id,
            "inline_message_id": inline_message_id,
        }
        return self._bind(
            method_name="getGameHighScores",
            params=params,
            telegram_type=List[GameHighScore],
        )


@dataclass(eq=True)
class SendMessageParams:
    """Encapsulate send_message parameters"""

    text: str
    parse_mode: str = None
    entities: List[MessageEntity] = None
    disable_web_page_preview: bool = None
    disable_notification: bool = None
    allow_sending_without_reply: bool = None
    reply_markup: Union[
        InlineKeyboardMarkup,
        ReplyKeyboardMarkup,
        ReplyKeyboardRemove,
        ForceReply,
    ] = None

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}
