# Generated by Django 3.2.11 on 2022-01-23 13:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Bot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=40, unique=True)),
                ('token', models.CharField(max_length=50, unique=True)),
                ('token_slug', models.SlugField(unique=True)),
                ('root_handlerconf', models.CharField(default='', max_length=100)),
                ('_me', models.JSONField(blank=True, null=True)),
                ('_webhook_info', models.JSONField(blank=True, null=True)),
                ('update_successful', models.BooleanField(default=True)),
                ('me_update_datetime', models.DateTimeField(blank=True, null=True)),
                ('webhook_update_datetime', models.DateTimeField(blank=True, null=True)),
                ('test_mode', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='CallbackQuery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('callback_query_id', models.CharField(max_length=100)),
                ('chat_instance', models.CharField(max_length=100)),
                ('inline_message_id', models.CharField(blank=True, max_length=100)),
                ('data', models.CharField(blank=True, max_length=100)),
                ('game_short_name', models.CharField(blank=True, max_length=100)),
                ('bot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='django_chatbot.bot')),
            ],
            options={
                'ordering': ['callback_query_id'],
            },
        ),
        migrations.CreateModel(
            name='Chat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chat_id', models.BigIntegerField()),
                ('type', models.CharField(max_length=255)),
                ('title', models.CharField(blank=True, max_length=255)),
                ('username', models.CharField(blank=True, max_length=255)),
                ('first_name', models.CharField(blank=True, max_length=255)),
                ('last_name', models.CharField(blank=True, max_length=255)),
                ('_photo', models.JSONField(blank=True, null=True)),
                ('bio', models.CharField(blank=True, max_length=255)),
                ('description', models.TextField(blank=True)),
                ('invite_link', models.CharField(blank=True, max_length=255)),
                ('_permissions', models.JSONField(blank=True, null=True)),
                ('slow_mode_delay', models.IntegerField(blank=True, null=True)),
                ('sticker_set_name', models.CharField(blank=True, max_length=255)),
                ('can_set_sticker_set', models.BooleanField(default=False)),
                ('linked_chat_id', models.BigIntegerField(blank=True, null=True)),
                ('_location', models.JSONField(blank=True, null=True)),
                ('bot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='django_chatbot.bot')),
            ],
        ),
        migrations.CreateModel(
            name='Form',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_form', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('direction', models.CharField(choices=[('in', 'in'), ('out', 'out')], default='in', max_length=3)),
                ('message_id', models.BigIntegerField()),
                ('date', models.DateTimeField()),
                ('forward_from_message_id', models.BigIntegerField(blank=True, null=True)),
                ('forward_signature', models.CharField(blank=True, max_length=255)),
                ('forward_sender_name', models.CharField(blank=True, max_length=255)),
                ('forward_date', models.DateTimeField(blank=True, null=True)),
                ('edit_date', models.DateTimeField(blank=True, null=True)),
                ('media_group_id', models.CharField(blank=True, max_length=255)),
                ('author_signature', models.CharField(blank=True, max_length=255)),
                ('text', models.TextField(blank=True)),
                ('_entities', models.JSONField(blank=True, null=True)),
                ('_animation', models.JSONField(blank=True, null=True)),
                ('_audio', models.JSONField(blank=True, null=True)),
                ('_document', models.JSONField(blank=True, null=True)),
                ('_photo', models.JSONField(blank=True, null=True)),
                ('_sticker', models.JSONField(blank=True, null=True)),
                ('_video', models.JSONField(blank=True, null=True)),
                ('_video_note', models.JSONField(blank=True, null=True)),
                ('_voice', models.JSONField(blank=True, null=True)),
                ('caption', models.CharField(blank=True, max_length=1024)),
                ('_caption_entities', models.JSONField(blank=True, null=True)),
                ('_contact', models.JSONField(blank=True, null=True)),
                ('_dice', models.JSONField(blank=True, null=True)),
                ('_game', models.JSONField(blank=True, null=True)),
                ('_poll', models.JSONField(blank=True, null=True)),
                ('_venue', models.JSONField(blank=True, null=True)),
                ('_location', models.JSONField(blank=True, null=True)),
                ('new_chat_title', models.CharField(blank=True, max_length=255)),
                ('_new_chat_photo', models.CharField(blank=True, max_length=255)),
                ('delete_chat_photo', models.BooleanField(default=True)),
                ('group_chat_created', models.BooleanField(default=True)),
                ('supergroup_chat_created', models.BooleanField(default=True)),
                ('channel_chat_created', models.BooleanField(default=True)),
                ('migrate_to_chat_id', models.BigIntegerField(blank=True, null=True)),
                ('migrate_from_chat_id', models.BigIntegerField(blank=True, null=True)),
                ('_invoice', models.JSONField(blank=True, null=True)),
                ('_successful_payment', models.JSONField(blank=True, null=True)),
                ('connected_website', models.CharField(blank=True, max_length=255)),
                ('_passport_data', models.JSONField(blank=True, null=True)),
                ('_proximity_alert_triggered', models.JSONField(blank=True, null=True)),
                ('_reply_markup', models.JSONField(blank=True, null=True)),
                ('extra', models.JSONField(default=dict)),
                ('chat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='django_chatbot.chat')),
                ('form', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='django_chatbot.form')),
            ],
            options={
                'ordering': ['message_id', 'chat'],
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.BigIntegerField(db_index=True, unique=True)),
                ('is_bot', models.BooleanField(default=False)),
                ('first_name', models.CharField(blank=True, max_length=40)),
                ('last_name', models.CharField(blank=True, max_length=40)),
                ('username', models.CharField(blank=True, max_length=40)),
                ('language_code', models.CharField(blank=True, max_length=2)),
                ('can_join_groups', models.BooleanField(default=False)),
                ('can_read_all_group_messages', models.BooleanField(default=False)),
                ('supports_inline_queries', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Update',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('handler', models.CharField(blank=True, max_length=100)),
                ('update_id', models.BigIntegerField(db_index=True, unique=True)),
                ('type', models.CharField(choices=[('message', 'Message'), ('edited_message', 'Edited message'), ('channel_post', 'Channel post'), ('edited_channel_post', 'Edited channel post')], default='message', max_length=20)),
                ('bot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='django_chatbot.bot')),
                ('callback_query', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='django_chatbot.callbackquery')),
                ('message', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='updates', to='django_chatbot.message')),
            ],
            options={
                'ordering': ['message_id'],
            },
        ),
        migrations.AddField(
            model_name='message',
            name='forward_from',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='forwarded_messages', to='django_chatbot.user'),
        ),
        migrations.AddField(
            model_name='message',
            name='forward_from_chat',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='forwarded_messages', to='django_chatbot.chat'),
        ),
        migrations.AddField(
            model_name='message',
            name='from_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='messages', to='django_chatbot.user'),
        ),
        migrations.AddField(
            model_name='message',
            name='left_chat_member',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='messages_left_chat', to='django_chatbot.user'),
        ),
        migrations.AddField(
            model_name='message',
            name='new_chat_members',
            field=models.ManyToManyField(related_name='messages_new_chat', to='django_chatbot.User'),
        ),
        migrations.AddField(
            model_name='message',
            name='pinned_message',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pinned_to', to='django_chatbot.message'),
        ),
        migrations.AddField(
            model_name='message',
            name='reply_to_message',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reply_message', to='django_chatbot.message'),
        ),
        migrations.AddField(
            model_name='message',
            name='sender_chat',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='django_chatbot.chat'),
        ),
        migrations.AddField(
            model_name='message',
            name='via_bot',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bot_messages', to='django_chatbot.user'),
        ),
        migrations.AddField(
            model_name='chat',
            name='pinned_message',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pinned_to_chats', to='django_chatbot.message'),
        ),
        migrations.AddField(
            model_name='callbackquery',
            name='from_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='django_chatbot.user'),
        ),
        migrations.AddField(
            model_name='callbackquery',
            name='message',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='django_chatbot.message'),
        ),
        migrations.AlterUniqueTogether(
            name='message',
            unique_together={('message_id', 'chat')},
        ),
        migrations.AlterIndexTogether(
            name='message',
            index_together={('message_id', 'chat')},
        ),
        migrations.AddIndex(
            model_name='chat',
            index=models.Index(fields=['bot', 'chat_id'], name='django_chat_bot_id_f78e25_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='chat',
            unique_together={('bot', 'chat_id')},
        ),
    ]
