# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='integration',
            name='service_enabled',
            field=models.BooleanField(editable=False, default=True),
        ),
        migrations.AddField(
            model_name='service',
            name='enabled',
            field=models.BooleanField(verbose_name='Service enabled', default=True),
        ),
        migrations.AlterIndexTogether(
            name='integration',
            index_together=set([('service_enabled', 'user', 'service'), ('service_enabled', 'stateless', 'api_next_sync')]),
        ),
    ]
