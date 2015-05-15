# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import picklefield.fields
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='api_last_sync',
        ),
        migrations.RemoveField(
            model_name='user',
            name='api_next_sync',
        ),
        migrations.RemoveField(
            model_name='user',
            name='api_state',
        ),
        migrations.AddField(
            model_name='integration',
            name='api_last_sync',
            field=models.DateTimeField(db_index=True, default=datetime.datetime(2015, 5, 15, 15, 32, 52, 729980, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='integration',
            name='api_next_sync',
            field=models.DateTimeField(db_index=True, default=datetime.datetime(2015, 5, 15, 15, 33, 2, 693771, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='integration',
            name='api_state',
            field=picklefield.fields.PickledObjectField(default='', editable=False),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='integration',
            name='service',
            field=models.ForeignKey(to='core.Service', max_length=1024),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.CharField(db_index=True, max_length=255),
        ),
    ]
