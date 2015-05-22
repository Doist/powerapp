# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_remove_integration_next_sync'),
    ]

    operations = [
        migrations.CreateModel(
            name='LocalItem',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('hub_name', models.CharField(max_length=512)),
                ('queue_name', models.CharField(max_length=512)),
                ('local_id', models.CharField(max_length=512)),
                ('integration', models.ForeignKey(to='core.Integration')),
            ],
        ),
        migrations.CreateModel(
            name='MetaItem',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('hub_name', models.CharField(max_length=512)),
                ('item_hash', models.CharField(max_length=64)),
                ('integration', models.ForeignKey(to='core.Integration')),
            ],
        ),
        migrations.AddField(
            model_name='localitem',
            name='meta_item',
            field=models.ForeignKey(to='sync_hub.MetaItem'),
        ),
        migrations.AlterIndexTogether(
            name='metaitem',
            index_together=set([('integration', 'hub_name')]),
        ),
    ]
