# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import picklefield.fields
from django.conf import settings
from django.utils.timezone import utc
import datetime


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0006_remove_integration_next_sync'),
    ]

    operations = [
        migrations.CreateModel(
            name='EvernoteNotebookCache',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('last_update_count', models.IntegerField(default=0)),
                ('last_update_time', models.DateTimeField(default=datetime.datetime(2000, 1, 1, 0, 0, tzinfo=utc))),
                ('notebooks', picklefield.fields.PickledObjectField(editable=False, null=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='EvernoteSyncState',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('last_update_count', models.IntegerField(default=0)),
                ('last_sync_time', models.BigIntegerField(default=0)),
                ('integration', models.OneToOneField(to='core.Integration')),
            ],
        ),
    ]
