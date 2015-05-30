# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sync_bridge', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='itemmapping',
            name='left_id',
            field=models.CharField(db_index=True, verbose_name='"Left system" item id', null=True, max_length=512),
        ),
        migrations.AlterField(
            model_name='itemmapping',
            name='right_id',
            field=models.CharField(db_index=True, verbose_name='"Right system" item id', null=True, max_length=512),
        ),
    ]
