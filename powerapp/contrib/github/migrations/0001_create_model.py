# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GithubDataMap',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('integration', models.ForeignKey(to='core.Integration')),
                ('github_data_id', models.IntegerField(db_index=True, auto_created=False)),
                ('github_data_type', models.TextField(auto_created=False)),
                ('github_data_url', models.TextField(auto_created=False)),
                ('todoist_task_id', models.IntegerField(db_index=True, auto_created=False))
            ],
        )
    ]
