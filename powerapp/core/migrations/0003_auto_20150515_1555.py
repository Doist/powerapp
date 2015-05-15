# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import picklefield.fields
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20150515_1533'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='api_last_sync',
            field=models.DateTimeField(default=datetime.datetime(2015, 5, 15, 15, 55, 35, 758892, tzinfo=utc), db_index=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='user',
            name='api_state',
            field=picklefield.fields.PickledObjectField(default='', editable=False),
            preserve_default=False,
        ),
    ]
