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

from django.contrib import admin
from .models import Bot, Chat, Message, Update, User


@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "update_successful",
        "me_update_datetime",
        "webhook_update_datetime",
    ]


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = [
        "bot",
        "chat_id",
        "type",
        "username"
    ]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = [
        "direction",
        "message_id",
        "date",
        "chat",
        "trancated_text",
    ]

    def trancated_text(self, obj):
        return obj.text[:20]


@admin.register(Update)
class UpdateAdmin(admin.ModelAdmin):
    list_display = [
        "bot",
        "update_id",
        "message_type",
    ]


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        "user_id",
        "username",
    ]
