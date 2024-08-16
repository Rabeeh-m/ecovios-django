# Generated by Django 5.0.6 on 2024-07-21 11:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0002_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='order_note',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='order',
            name='order_number',
            field=models.CharField(default=' ', max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='order_total',
            field=models.FloatField(default='0.0'),
            preserve_default=False,
        ),
    ]
