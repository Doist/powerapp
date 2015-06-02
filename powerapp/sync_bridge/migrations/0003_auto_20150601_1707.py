# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import picklefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('sync_bridge', '0002_auto_20150530_2252'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemmapping',
            name='left_extra',
            field=picklefield.fields.PickledObjectField(verbose_name='Extra data of the "left side"', default={}, editable=False),
        ),
        migrations.AddField(
            model_name='itemmapping',
            name='right_extra',
            field=picklefield.fields.PickledObjectField(verbose_name='Extra data of the "right side"', default={}, editable=False),
        ),
    ]
