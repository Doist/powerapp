# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('evernote_sync', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='evernoteaccountcache',
            name='evernote_user_id',
            field=models.PositiveIntegerField(null=True, db_index=True),
        ),
    ]
