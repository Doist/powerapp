# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import picklefield.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(null=True, blank=True, verbose_name='last login')),
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('email', models.CharField(max_length=255, db_index=True, unique=True)),
                ('api_state', picklefield.fields.PickledObjectField(editable=False)),
                ('api_token', models.CharField(max_length=255, db_index=True)),
                ('api_last_sync', models.DateTimeField(db_index=True)),
                ('api_next_sync', models.DateTimeField(db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='AccessToken',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('client', models.CharField(max_length=128, verbose_name='OAuth client name')),
                ('scope', models.CharField(max_length=1024, verbose_name='OAuth scope')),
                ('token', models.CharField(max_length=1024, verbose_name='OAuth token value')),
                ('time', models.DateTimeField(auto_now_add=True, verbose_name='Time token added')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Integration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(max_length=1024)),
                ('next_sync', models.IntegerField(db_index=True, default=0)),
                ('settings', picklefield.fields.PickledObjectField(default={}, editable=False)),
            ],
        ),
        migrations.CreateModel(
            name='PeriodicTask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(max_length=1024)),
                ('next_run', models.DateTimeField(db_index=True)),
                ('integration', models.ForeignKey(to='core.Integration')),
            ],
        ),
        migrations.CreateModel(
            name='RefreshToken',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('client', models.CharField(max_length=128, verbose_name='OAuth client name')),
                ('scope', models.CharField(max_length=1024, verbose_name='OAuth scope')),
                ('token', models.CharField(max_length=1024, verbose_name='OAuth token value')),
                ('time', models.DateTimeField(auto_now_add=True, verbose_name='Time token added')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('label', models.CharField(max_length=256, primary_key=True, verbose_name='Service label', serialize=False)),
                ('name', models.CharField(max_length=256, verbose_name='Service name')),
                ('path', models.CharField(max_length=1024, verbose_name='Service path')),
            ],
        ),
        migrations.AddField(
            model_name='integration',
            name='service',
            field=models.ForeignKey(max_length=1024, to='core.Service'),
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
        migrations.AlterIndexTogether(
            name='integration',
            index_together=set([('user', 'service')]),
        ),
    ]
