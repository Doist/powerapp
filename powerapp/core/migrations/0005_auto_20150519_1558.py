# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.timezone import utc
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_auto_20150519_1210'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='api_last_sync',
            field=models.DateTimeField(default=datetime.datetime(2000, 1, 1, 0, 0, tzinfo=utc), db_index=True),
        ),
    ]
