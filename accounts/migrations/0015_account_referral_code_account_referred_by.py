# Generated by Django 5.0.6 on 2024-08-11 16:26

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0014_alter_useraddress_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='referral_code',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='account',
            name='referred_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='referrals', to=settings.AUTH_USER_MODEL),
        ),
    ]
