# Generated by Django 5.0.6 on 2024-07-30 07:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('carts', '0010_appliedcoupon'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='coupon',
            name='used_by',
        ),
        migrations.RemoveField(
            model_name='cart',
            name='coupon',
        ),
        migrations.RemoveField(
            model_name='cart',
            name='discount',
        ),
        migrations.DeleteModel(
            name='AppliedCoupon',
        ),
        migrations.DeleteModel(
            name='Coupon',
        ),
    ]
