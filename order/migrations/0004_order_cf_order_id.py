# Generated by Django 4.1.4 on 2023-03-09 19:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("order", "0003_order_cart"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="cf_order_id",
            field=models.CharField(blank=True, max_length=40, null=True),
        ),
    ]