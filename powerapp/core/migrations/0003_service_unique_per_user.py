# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_service_enabled_flag'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='unique_per_user',
            field=models.BooleanField(verbose_name='True - user can add only one integration', default=True),
        ),
    ]
