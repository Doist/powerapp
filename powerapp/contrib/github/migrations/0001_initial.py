# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import picklefield.fields
from django.utils.timezone import utc
from django.conf import settings
import datetime


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GithubItemIssueMap',
            fields=[
                ('integration', models.OneToOneField(to='core.Integration', primary_key=True)),
                ('issue_id', models.IntegerField(db_index=True, auto_created=False)),
                ('task_id', models.IntegerField(db_index=True, auto_created=False)),
            ],
        )
    ]
