from django.core.management import BaseCommand

from django_chatbot.models import Bot


class Command(BaseCommand):
    def handle(self, *args, **options):
        for bot in Bot.objects.all():
            result = bot.set_webhook()
            if result["ok"]:
                print(f"Webhook was successfully set for {bot.name}.")
            else:
                print(f"Setting webhook was failed for {bot.name}.")
                print(result["result"])
                continue
            result = bot.get_webhook_info()
            if result["ok"]:
                print(f"Webhook info was updated from telegram for {bot.name}.")
            else:
                print(f"Updating webhook info was failed for {bot.name}.")
                print(result["result"])
                continue