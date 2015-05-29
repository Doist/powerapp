# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_remove_integration_next_sync'),
    ]

    operations = [
        migrations.CreateModel(
            name='ItemMapping',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('bridge_name', models.CharField(max_length=512)),
                ('left_id', models.CharField(verbose_name='"Left system" item id', null=True, max_length=512)),
                ('left_hash', models.CharField(default='!', verbose_name='Last seen hash of the item', max_length=64)),
                ('right_id', models.CharField(verbose_name='"Right system" item id', null=True, max_length=512)),
                ('right_hash', models.CharField(default='!', verbose_name='Last seen hash of the item', max_length=64)),
                ('integration', models.ForeignKey(to='core.Integration')),
            ],
        ),
        migrations.AlterIndexTogether(
            name='itemmapping',
            index_together=set([('integration', 'bridge_name', 'right_id'), ('integration', 'bridge_name', 'left_id')]),
        ),
    ]
