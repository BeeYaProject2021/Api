# Generated by Django 3.2.3 on 2021-08-11 08:13

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catch', '0006_auto_20210811_1528'),
    ]

    operations = [
        migrations.AlterField(
            model_name='train',
            name='start_date',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
    ]
