from django.contrib import admin

# Register your models here.
from dummyfatherbot.models import FakeBot


@admin.register(FakeBot)
class FakeBotAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "username")
