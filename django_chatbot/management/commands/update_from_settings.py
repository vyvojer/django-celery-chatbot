from django.conf import settings
from django.core.management import BaseCommand

from django_chatbot.models import Bot


class Command(BaseCommand):
    def handle(self, *args, **options):
        for bot_settings in settings.DJANGO_CHATBOT['BOTS']:
            name = bot_settings['NAME']
            token = bot_settings['TOKEN']
            root_handlerconf = bot_settings['ROOT_HANDLERCONF']
            bot, created = Bot.objects.update_or_create(
                name=name,
                defaults={'token': token, 'root_handlerconf': root_handlerconf}
            )
            if created:
                print(f'Bot "{name}" has been added')
            else:
                print(f'Bot "{name}" has been updated')
