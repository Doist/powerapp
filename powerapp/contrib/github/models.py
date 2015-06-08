# -*- coding: utf-8 -*-
from django.db import models


class GithubDataMap(models.Model):
    id = models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)
    integration = models.ForeignKey(to='core.Integration')
    github_data_id = models.IntegerField(db_index=True, auto_created=False)
    github_data_type = models.TextField(auto_created=False)
    github_data_url = models.TextField(auto_created=False)
    todoist_task_id = models.IntegerField(db_index=True, auto_created=False)
