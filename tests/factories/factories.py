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

import factory
from django.utils import timezone

NOW = timezone.now()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "django_chatbot.User"

    user_id = factory.Sequence(lambda n: n)
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    username = factory.Faker("user_name")


class BotFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "django_chatbot.Bot"
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"bot_{n}")
    token = factory.Sequence(lambda n: f"token_{n}")
    root_handlerconf = factory.LazyAttribute(lambda o: f"{o.name}.handler")
    webhook_enabled = factory.Faker("boolean")


class ChatFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "django_chatbot.Chat"
        django_get_or_create = ("chat_id",)

    bot = factory.SubFactory(BotFactory)
    chat_id = factory.Sequence(lambda n: n)
    type = factory.Iterator(["private", "group", "supergroup", "channel"])
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    username = factory.Faker("user_name")


class MessageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "django_chatbot.Message"
        django_get_or_create = ("chat", "message_id")

    direction = factory.Iterator(["in", "out"])
    chat = factory.SubFactory(ChatFactory)
    message_id = factory.Sequence(lambda n: n)
    date = factory.Sequence(lambda n: NOW + timezone.timedelta(minutes=n))
    text = factory.Faker("text")


class CallbackQueryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "django_chatbot.CallbackQuery"
        django_get_or_create = ("callback_query_id",)

    bot = factory.SubFactory(BotFactory)
    callback_query_id = factory.Sequence(lambda n: n)
    from_user = factory.SubFactory(UserFactory)
    chat_instance = factory.Faker("uuid4")
    message = factory.SubFactory(MessageFactory)
    data = factory.Faker("word")


class UpdateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "django_chatbot.Update"
        django_get_or_create = ("update_id",)

    bot = factory.SubFactory(BotFactory)
    type = "message"  # one of the "message", "edited_message", "channel_post",
    # "edited_channel_post", "callback_query"
    update_id = factory.Sequence(lambda n: n)

    @factory.lazy_attribute
    def message(self):
        if self.type in [
            "message",
            "edited_message",
            "channel_post",
            "edited_channel_post",
        ]:
            return factory.SubFactory(MessageFactory).get_factory().create()
        else:
            return None

    @factory.lazy_attribute
    def callback_query(self):
        if self.type == "callback_query":
            return factory.SubFactory(CallbackQueryFactory).get_factory().create()
        else:
            return None


class FormFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "django_chatbot.Form"

    module_name = factory.Sequence(lambda n: f"module_{n}")
    class_name = factory.Sequence(lambda n: f"class_{n}")
    current_field = factory.Sequence(lambda n: f"field_{n}")
    context = {}
    is_finished = False


class FieldFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "django_chatbot.Field"

    form = factory.SubFactory(FormFactory)
    name = factory.Sequence(lambda n: f"field_{n}")
    value = factory.Sequence(lambda n: f"value_{n}")
    is_valid = False
