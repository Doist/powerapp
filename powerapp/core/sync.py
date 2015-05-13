# -*- coding: utf-8 -*-
from contextlib import contextmanager
from django.utils.timezone import now
import todoist
from copy import deepcopy
from logging import getLogger
from django.conf import settings
from django.dispatch import Signal
from powerapp.core.exceptions import return_or_raise

logger = getLogger(__name__)


sync_event = Signal(providing_args=['event_name', 'user', 'obj'])


class TodoistAPI(todoist.TodoistAPI):
    """
    A subclass of the standard Todoist API. The difference is that it
    automatically saves its state internally on every sync command, can
    be initialized from the User object and also emits sync events.

    Note that you probably don't want to subscribe to sync events directly.
    Instead, all services are subscribed and forwarded this event automatically
    """
    user_model = None

    @classmethod
    def create(cls, user_model):
        if user_model.api_state:
            obj = cls.deserialize(user_model.api_state)
        else:
            obj = cls(user_model.api_token)
        obj.api_endpoint = settings.API_ENDPOINT
        obj.user_model = user_model
        return obj

    def sync(self, commands=None, **kwargs):
        current_state = deepcopy(self.state)

        ret = super(TodoistAPI, self).sync(commands, **kwargs)
        return_or_raise(ret)

        if not self.user_model.id:
            self.user_model.id = self.user.get('id')
        self.user_model.email = self.user.get('email')
        self.user_model.api_state = self.serialize()
        self.user_model.api_last_sync = now()
        self.user_model.save()

        self.emit_sync_signals(current_state, ret)
        return ret

    def emit_sync_signals(self, api_state, result):
        """
        Process sync result and yield events, one by one
        """
        user = self.user_model
        _exists_cache = {}

        def exists(state_key, obj_id):
            if state_key not in _exists_cache:
                _exists_cache[state_key] = {obj['id'] for obj in
                                            api_state[state_key]}
            return obj_id in _exists_cache[state_key]

        result_event_map = [
            ('Items', 'task'),
            ('Notes', 'note'),
            ('Projects', 'project'),
        ]

        for result_key, event_type in result_event_map:
            for obj in result.get(result_key) or []:
                if obj['is_deleted']:
                    event_name = 'todoist_%s_deleted' % event_type
                elif exists(result_key, obj['id']):
                    event_name = 'todoist_%s_updated' % event_type
                else:
                    event_name = 'todoist_%s_added' % event_type

                logger.debug('Fire %s(%r, %r)' % (event_name, user.email,
                                                  obj['id']))
                resp = sync_event.send_robust(None, event_name=event_name,
                                              user=user, obj=obj)
                for item in resp:
                    logger.debug('-> %s', item)

    @contextmanager
    def autocommit(self):
        yield
        self.commit()
