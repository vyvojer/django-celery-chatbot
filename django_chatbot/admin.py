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
