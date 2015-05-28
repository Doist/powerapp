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
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('bridge_name', models.CharField(max_length=512)),
                ('left_id', models.CharField(max_length=512, verbose_name='"Left system" item id', null=True)),
                ('right_id', models.CharField(max_length=512, verbose_name='"Right system" item id', null=True)),
                ('item_hash', models.CharField(max_length=64, verbose_name='Last seen hash of the item')),
                ('integration', models.ForeignKey(to='core.Integration')),
            ],
        ),
        migrations.AlterIndexTogether(
            name='itemmapping',
            index_together=set([('integration', 'bridge_name', 'left_id'), ('integration', 'bridge_name', 'right_id')]),
        ),
    ]
