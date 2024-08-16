# Generated by Django 5.0.6 on 2024-07-29 15:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carts', '0005_coupon'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='discount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
