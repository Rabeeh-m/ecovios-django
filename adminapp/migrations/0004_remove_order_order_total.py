# Generated by Django 5.0.6 on 2024-07-21 11:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0003_order_order_note_order_order_number_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='order_total',
        ),
    ]
