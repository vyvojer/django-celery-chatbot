from django_chatbot.models import Bot, Chat, Update, User, Message
from django_chatbot.telegram.types import Update as TelegramUpdate


def save_update(bot: Bot, update_data: dict):
    user = _handle_user(update_data)
    chat = _handle_chat(bot, update_data)
    message = _handle_message(update_data, chat=chat, user=user)
    update = _handle_update(bot, update_data, message=message)
    return update


def _handle_user(update_data: dict) -> User:
    telegram_update = TelegramUpdate.from_dict(update_data)
    telegram_user = telegram_update.effective_user
    defaults = telegram_user.to_dict()
    defaults.pop('id')
    user, _ = User.objects.update_or_create(
        user_id=telegram_user.id,
        defaults=defaults,
    )
    return user


def _handle_chat(bot: Bot, update_data: dict) -> Chat:
    telegram_update = TelegramUpdate.from_dict(update_data)
    telegram_chat = telegram_update.effective_message.chat
    defaults = telegram_chat.to_dict()
    defaults.pop('id')
    defaults["bot"] = bot
    chat, _ = Chat.objects.update_or_create(
        chat_id=telegram_chat.id,
        defaults=defaults,
    )
    return chat


def _handle_message(update_data: dict,
                    chat: Chat,
                    user: User = None) -> Message:
    telegram_update = TelegramUpdate.from_dict(update_data)
    telegram_message = telegram_update.effective_message
    defaults = telegram_message.to_dict()
    if telegram_message.entities:
        defaults['_entities'] = defaults['entities']
        defaults.pop('entities')
    defaults['chat'] = chat
    if telegram_message.from_user:
        defaults['from_user'] = user
    defaults.pop('message_id')
    message, _ = Message.objects.update_or_create(
        message_id=telegram_message.message_id,
        defaults=defaults,
    )
    return message


def _handle_update(bot: Bot, update_data: dict, message: Message) -> Update:
    telegram_update = TelegramUpdate.from_dict(update_data)
    defaults = telegram_update.to_dict()
    defaults['message'] = message
    defaults['message_type'] = message_type(telegram_update)
    defaults['bot'] = bot
    defaults['original'] = update_data
    defaults.pop('update_id')
    update, _ = Update.objects.update_or_create(
        update_id=telegram_update.update_id,
        defaults=defaults,
    )
    return update


def message_type(telegram_update: TelegramUpdate) -> str:
    if telegram_update.message:
        return Update.MESSAGE_TYPE_MESSAGE
    elif telegram_update.edited_message:
        return Update.MESSAGE_TYPE_EDITED_MESSAGE
    elif telegram_update.channel_post:
        return Update.MESSAGE_TYPE_CHANNEL_POST
    elif telegram_update.edited_channel_post:
        return Update.MESSAGE_TYPE_EDITED_CHANNEL_POST
