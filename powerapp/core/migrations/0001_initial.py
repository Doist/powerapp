# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import picklefield.fields
from django.conf import settings
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(verbose_name='password', max_length=128)),
                ('last_login', models.DateTimeField(null=True, blank=True, verbose_name='last login')),
                ('id', models.IntegerField(serialize=False, primary_key=True)),
                ('email', models.CharField(db_index=True, max_length=255)),
                ('api_token', models.CharField(db_index=True, max_length=255)),
                ('api_state', picklefield.fields.PickledObjectField(editable=False)),
                ('api_last_sync', models.DateTimeField(default=datetime.datetime(2000, 1, 1, 0, 0, tzinfo=utc), db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='Integration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=1024)),
                ('settings', picklefield.fields.PickledObjectField(editable=False, default={})),
                ('stateless', models.BooleanField(default=True)),
                ('api_state', picklefield.fields.PickledObjectField(editable=False)),
                ('api_last_sync', models.DateTimeField(default=datetime.datetime(2000, 1, 1, 0, 0, tzinfo=utc))),
                ('api_next_sync', models.DateTimeField(default=datetime.datetime(2000, 1, 1, 0, 0, tzinfo=utc))),
            ],
        ),
        migrations.CreateModel(
            name='OAuthToken',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('client', models.CharField(verbose_name='OAuth client name', max_length=128)),
                ('access_token', models.CharField(verbose_name='OAuth access token', max_length=1024)),
                ('refresh_token', models.CharField(null=True, max_length=1024, verbose_name='OAuth refresh token')),
                ('token_type', models.CharField(default='Bearer', verbose_name='Token type', max_length=64)),
                ('access_token_expires', models.DateTimeField(default=None, null=True, verbose_name='Access token expiration date')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PeriodicTask',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=1024)),
                ('next_run', models.DateTimeField(db_index=True)),
                ('integration', models.ForeignKey(to='core.Integration')),
            ],
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('label', models.CharField(max_length=256, serialize=False, verbose_name='Service label', primary_key=True)),
                ('name', models.CharField(verbose_name='Service name', max_length=256)),
                ('path', models.CharField(verbose_name='Service path', max_length=1024)),
            ],
        ),
        migrations.AddField(
            model_name='integration',
            name='service',
            field=models.ForeignKey(to='core.Service', max_length=1024),
        ),
        migrations.AddField(
            model_name='integration',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='periodictask',
            unique_together=set([('integration', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='oauthtoken',
            unique_together=set([('user', 'client')]),
        ),
        migrations.AlterIndexTogether(
            name='integration',
            index_together=set([('user', 'service'), ('stateless', 'api_next_sync')]),
        ),
    ]
