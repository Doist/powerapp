# -*- coding: utf-8 -*-
import time
from django.db import transaction
from powerapp.core.models import Integration


@transaction.atomic
def schedule_with_rate_limit(integration_id, last_op_settings_key,
                             task, timeout=60):
    """
    Schedule an idempotent task (such as "sync with the upstream") to Celery,
    and make sure the task isn't executed more often than once in "timeout"
    seconds.

    The logic is following:

    - If for the last time we executed the task more than `timeout`
      seconds ago, we schedule it to start right now and keep current time
      in the `last_op_settings_key`

    - If we executed the task quite recently (less than `timeout` ago), but
      still in the past, we schedule the next task to be started in a minute
      after the last launch.

    - If the task is scheduled for the future (the value in
      `last_op_settings_key` more than current time), skip scheduling a new task

    Misc considerations:

    - `task` has to be a "half-baked Celery task object" (so called
       "signature"), made with Celery API like ``task_func.s(params)`` or
       a task object

    - Return the time (always in future) on which the task is scheduled, or
      None, if integration is not found

    - The task doesn't have to be executed more that `timeout` seconds. We
      enforce this by setting up the time_limit and soft_time_limit (timeout - 10s).
      If worker wants to react on soft time limit, it has to catch the
      SoftTimeLimitExceeded exception
    """
    try:
        integration = Integration.objects.get(id=integration_id)
    except Integration.DoesNotExist:
        return

    last_op = integration.settings.get(last_op_settings_key)
    now = int(time.time())

    apply_async_kwargs = {'time_limit': timeout,
                          'soft_time_limit': timeout if timeout < 20 else timeout - 10}

    if not last_op or last_op < now - timeout:
        integration.update_settings(**{last_op_settings_key: now})
        task.apply_async(**apply_async_kwargs)
        return now

    if last_op < now:
        next_schedule = last_op + timeout
        countdown = next_schedule - now
        integration.update_settings(**{last_op_settings_key: next_schedule})
        task.apply_async(countdown=countdown, **apply_async_kwargs)
        return next_schedule

    # otherwise last op is in future, just return the value
    return last_op
