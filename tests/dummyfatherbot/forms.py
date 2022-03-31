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
from dummyfatherbot.models import FakeBot

from django_chatbot import forms
from django_chatbot.telegram.types import InlineKeyboardButton


class NewBotForm(forms.Form):
    name = forms.Field(
        "Alright, a new bot. How are we going to call it? Please choose a name for your bot."  # noqa
    )
    username = forms.Field(
        "Good. Now let's choose a username for your bot. It must end in `bot`. Like this, for example: TetrisBot or tetris_bot."  # noqa
    )

    def on_finish(self, chat):
        bot = FakeBot.objects.create(name=self.name.value, username=self.username.value)
        chat.reply(f"Bot is created. @{bot.username}")


class ManiMenuField(forms.Field):
    def get_inline_keyboard(self, form):
        bots = FakeBot.objects.all()
        rows = [bots[i : i + 2] for i in range(0, len(bots), 2)]
        keyboard = []
        for row in rows:
            keyboard.append(
                [
                    InlineKeyboardButton(f"@{bot.username}", callback_data=bot.username)
                    for bot in row
                ]
            )
        return keyboard


class BotActionsField(forms.Field):
    inline_keyboard = [
        [
            InlineKeyboardButton("Edit Bot", callback_data="edit_bot"),
            InlineKeyboardButton("Delete Bot", callback_data="delete_bot"),
        ],
        [
            InlineKeyboardButton("Back to Bots List", callback_data="back_to_list"),
        ],
    ]

    def get_prompt_message(self, form):
        return f"What do you want to do with @{form.bot.value}?"


class MyBotsForm(forms.Form):
    bot = ManiMenuField("Choose a bot from the list below:")
    bot_actions = BotActionsField()

    def connect_fields(self):
        self.bot.add_next_field(
            self.bot_actions, prompt_type=forms.PromptType.UPDATE_MESSAGE
        )
        self.bot_actions.add_next_field(
            self.bot, prompt_type=forms.PromptType.UPDATE_MESSAGE
        )
