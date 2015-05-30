# -*- coding: utf-8 -*-
import datetime
from django.conf import settings
from django.db import models
from django.utils.timezone import make_aware, now
from picklefield.fields import PickledObjectField


class EvernoteNotebookCache(models.Model):
    """
    Notebook cache, common for all integrations of the same user
    """
    UPDATE_THRESHOLD = datetime.timedelta(seconds=30) if settings.DEBUG else datetime.timedelta(minutes=15)
    MILLENIUM = make_aware(datetime.datetime(2000, 1, 1))

    user = models.OneToOneField('core.User')
    last_update_count = models.IntegerField(default=0)
    last_update_time = models.DateTimeField(default=MILLENIUM)
    notebooks = PickledObjectField(null=True)

    def refresh(self):
        """
        Refresh the evernote cache if required
        """
        from .utils import get_evernote_client
        if self.last_update_time > now() - self.UPDATE_THRESHOLD:
            # no need to update yet
            return

        # let's see if there are some updates
        client = get_evernote_client(self.user)

        note_store = client.get_note_store()
        update_count = note_store.getSyncState().updateCount
        if update_count <= self.last_update_count:
            # no updates yet
            self.last_update_time = now()
            self.save()
            return

        # it's time for update
        self.notebooks = note_store.listNotebooks()
        self.last_update_time = now()
        self.last_update_count = update_count
        self.save()



class EvernoteSyncState(models.Model):
    """
    Evernote sync state
    """
    integration = models.OneToOneField('core.Integration')
    last_update_count = models.IntegerField(default=0)
    last_sync_time = models.BigIntegerField(default=0)

    def get_last_sync(self):
        return datetime.datetime.fromtimestamp(self.last_sync_time / 1000)

    def __str__(self):
        return '%s (%s)' % (self.last_update_count,
                            self.get_last_sync().strftime('%Y-%m-%d %T'))
