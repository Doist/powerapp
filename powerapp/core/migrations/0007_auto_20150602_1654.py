# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_remove_integration_next_sync'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='refreshtoken',
            name='user',
        ),
        migrations.AddField(
            model_name='oauthtoken',
            name='access_token',
            field=models.CharField(default='', max_length=1024, verbose_name='OAuth access token'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='oauthtoken',
            name='access_token_expires',
            field=models.DateTimeField(default=None, null=True, verbose_name='Access token expiration date'),
        ),
        migrations.AddField(
            model_name='oauthtoken',
            name='refresh_token',
            field=models.CharField(max_length=1024, null=True, verbose_name='OAuth refresh token'),
        ),
        migrations.AddField(
            model_name='oauthtoken',
            name='token_type',
            field=models.CharField(default='Bearer', max_length=64, verbose_name='Token type'),
        ),
        migrations.AlterUniqueTogether(
            name='oauthtoken',
            unique_together=set([('user', 'client')]),
        ),
        migrations.DeleteModel(
            name='RefreshToken',
        ),
        migrations.RemoveField(
            model_name='oauthtoken',
            name='scope',
        ),
        migrations.RemoveField(
            model_name='oauthtoken',
            name='time',
        ),
        migrations.RemoveField(
            model_name='oauthtoken',
            name='token',
        ),
    ]
