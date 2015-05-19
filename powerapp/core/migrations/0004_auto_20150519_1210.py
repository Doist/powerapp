# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20150515_1555'),
    ]

    operations = [
        migrations.AddField(
            model_name='integration',
            name='stateless',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='integration',
            name='api_last_sync',
            field=models.DateTimeField(default=datetime.datetime(2000, 1, 1, 0, 0, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='integration',
            name='api_next_sync',
            field=models.DateTimeField(default=datetime.datetime(2000, 1, 1, 0, 0, tzinfo=utc)),
        ),
        migrations.AlterIndexTogether(
            name='integration',
            index_together=set([('user', 'service'), ('stateless', 'api_next_sync')]),
        ),
    ]
