# -*- coding: utf-8 -*-
import datetime
from django.db import models
from django.utils.timezone import make_aware
from picklefield.fields import PickledObjectField


class EvernoteCache(models.Model):

    # Woohoo! Millenium!
    MILLENIUM = make_aware(datetime.datetime(2000, 1, 1))

    user = models.OneToOneField('core.User')
    last_update_time = models.DateTimeField(default=MILLENIUM)
    last_update_count = models.IntegerField(default=0)
    notebooks = PickledObjectField(null=True)
