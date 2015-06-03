# -*- coding: utf-8 -*-
from django.db import models


class GithubItemIssueMap(models.Model):
    integration = models.OneToOneField(to='core.Integration', primary_key=True)
    issue_id = models.IntegerField(db_index=True, auto_created=False)
    task_id = models.IntegerField(db_index=True, auto_created=False)
