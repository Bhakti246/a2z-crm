from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='connectedaccount',
            name='encrypted_access_token',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='connectedaccount',
            name='encrypted_refresh_token',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='connectedaccount',
            name='token_last_checked_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='WebhookEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(db_index=True, default='meta', max_length=50)),
                ('event_type', models.CharField(db_index=True, max_length=100)),
                ('external_id', models.CharField(db_index=True, max_length=255)),
                ('payload', models.JSONField(default=dict)),
                ('status', models.CharField(choices=[('received', 'Received'), ('processing', 'Processing'), ('processed', 'Processed'), ('failed', 'Failed'), ('dead_letter', 'Dead Letter')], db_index=True, default='received', max_length=20)),
                ('attempts', models.PositiveIntegerField(default=0)),
                ('last_error', models.TextField(blank=True, null=True)),
                ('received_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Webhook Event',
                'verbose_name_plural': 'Webhook Events',
                'ordering': ['-received_at'],
                'unique_together': {('provider', 'event_type', 'external_id')},
            },
        ),
        migrations.CreateModel(
            name='MetaConversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform', models.CharField(choices=[('facebook', 'Facebook'), ('instagram', 'Instagram')], default='instagram', max_length=30)),
                ('conversation_id', models.CharField(db_index=True, max_length=255, unique=True)),
                ('sender_id', models.CharField(db_index=True, max_length=255)),
                ('recipient_id', models.CharField(db_index=True, max_length=255)),
                ('status', models.CharField(db_index=True, default='open', max_length=20)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('last_message_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('connected_account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='meta_conversations', to='crm.connectedaccount')),
                ('lead', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='meta_conversations', to='crm.lead')),
            ],
            options={
                'verbose_name': 'Meta Conversation',
                'verbose_name_plural': 'Meta Conversations',
                'ordering': ['-last_message_at', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='MetaMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message_id', models.CharField(db_index=True, max_length=255, unique=True)),
                ('sender_id', models.CharField(db_index=True, max_length=255)),
                ('recipient_id', models.CharField(db_index=True, max_length=255)),
                ('direction', models.CharField(choices=[('inbound', 'Inbound'), ('outbound', 'Outbound')], default='inbound', max_length=20)),
                ('text', models.TextField(blank=True, null=True)),
                ('event_type', models.CharField(default='message', max_length=100)),
                ('raw_data', models.JSONField(blank=True, default=dict)),
                ('sent_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='crm.metaconversation')),
            ],
            options={
                'verbose_name': 'Meta Message',
                'verbose_name_plural': 'Meta Messages',
                'ordering': ['-sent_at', '-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='webhookevent',
            index=models.Index(fields=['provider', 'status'], name='crm_wh_provider_status'),
        ),
        migrations.AddIndex(
            model_name='webhookevent',
            index=models.Index(fields=['event_type', 'external_id'], name='crm_wh_event_external'),
        ),
    ]
