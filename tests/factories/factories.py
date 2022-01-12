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


class BotFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "django_chatbot.Bot"
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"bot_{n}")
    token = factory.Sequence(lambda n: f"token_{n}")
    root_handlerconf = factory.LazyAttribute(lambda o: f"{o.name}.handler")


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


class UpdateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "django_chatbot.Update"
        django_get_or_create = ("update_id",)

    bot = factory.SubFactory(BotFactory)
    type = factory.Iterator(
        ["message", "edited_message", "channel_post", "edited_channel_post"]
    )
    update_id = factory.Sequence(lambda n: n)
    message = factory.SubFactory(MessageFactory)
