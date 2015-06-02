# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import picklefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ItemMapping',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('bridge_name', models.CharField(max_length=512)),
                ('left_id', models.CharField(db_index=True, null=True, max_length=512, verbose_name='"Left system" item id')),
                ('left_hash', models.CharField(default='!', verbose_name='Last seen hash of the item', max_length=64)),
                ('left_extra', picklefield.fields.PickledObjectField(editable=False, default={}, verbose_name='Extra data of the "left side"')),
                ('right_id', models.CharField(db_index=True, null=True, max_length=512, verbose_name='"Right system" item id')),
                ('right_hash', models.CharField(default='!', verbose_name='Last seen hash of the item', max_length=64)),
                ('right_extra', picklefield.fields.PickledObjectField(editable=False, default={}, verbose_name='Extra data of the "right side"')),
                ('integration', models.ForeignKey(to='core.Integration')),
            ],
        ),
        migrations.AlterIndexTogether(
            name='itemmapping',
            index_together=set([('integration', 'bridge_name', 'left_id'), ('integration', 'bridge_name', 'right_id')]),
        ),
    ]
