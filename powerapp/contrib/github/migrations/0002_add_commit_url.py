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
        ('github', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='GithubItemIssueMap',
            name='issue_url',
            field=models.TextField(auto_created=False)
        )
    ]