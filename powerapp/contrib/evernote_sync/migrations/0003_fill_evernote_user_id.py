# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, transaction


@transaction.atomic()
def fill_evernote_user_id(apps, schema_editor):
    EAC = apps.get_model("evernote_sync", "EvernoteAccountCache")
    for cache in EAC.objects.all():
        try:
            cache.evernote_user_id = cache.user_data.id
        except AttributeError:
            continue
        cache.save(update_fields=['evernote_user_id'])


def nop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('evernote_sync', '0002_evernoteaccountcache_evernote_user_id'),
    ]

    operations = [
        migrations.RunPython(fill_evernote_user_id, nop)
    ]
