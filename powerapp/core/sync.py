# -*- coding: utf-8 -*-
from contextlib import contextmanager
from django.utils.timezone import now
import todoist
from copy import deepcopy
from logging import getLogger
from django.conf import settings
from powerapp.core.exceptions import return_or_raise


logger = getLogger(__name__)


class TodoistAPI(todoist.TodoistAPI):

    @contextmanager
    def autocommit(self):
        yield
        self.commit()

    @classmethod
    def create(cls, integration):
        if integration.app_config.stateless:
            return StatelessTodoistAPI.create(integration)
        else:
            return StatefulTodoistAPI.create(integration)


class UserTodoistAPI(TodoistAPI):
    """
    A Todoist API object attached to a user.

    Keeps track of user's data, but doesn't emit any events. Used mostly to
    display form elements and user data
    """
    user_obj = None

    @classmethod
    def create(cls, user_obj):
        """
        Initiate API from the integration

        :param powerapp.core.models.Integration integration: the integration object
        """
        if user_obj.api_state:
            obj = cls.deserialize(user_obj.api_state)
        else:
            obj = cls(user_obj.api_token)
        obj.api_endpoint = settings.API_ENDPOINT
        obj.user_obj = user_obj
        return obj

    def sync(self, commands=None, **kwargs):
        new_state = super(UserTodoistAPI, self).sync(commands, **kwargs)
        return_or_raise(new_state)

        self.user_obj.api_state = self.serialize()
        self.user_obj.api_last_sync = now()
        self.user_obj.save(update_fields=['api_state', 'api_last_sync'])

        return new_state


class StatelessTodoistAPI(TodoistAPI):
    """
    A "stateless" subclass of the standard Todoist API
    """
    integration = None

    @classmethod
    def create(cls, integration):
        obj = cls(integration.user.api_token)
        obj.patch_managers()
        obj.api_endpoint = settings.API_ENDPOINT
        obj.integration = integration
        return obj

    def sync(self, commands, **kwargs):
        """
        Make a sync request, but never ask for server data,
        don't emit any signals, and don't update the sync state
        """
        kwargs.pop('resource_types', None)
        return super(StatelessTodoistAPI, self).sync(commands, **kwargs)

    def patch_managers(self):
        """
        Replace sync manager methods with stubs raising RuntimeError, because
        stateless API is not allowed to have a local copy of remote data
        """
        def stub(*arg, **kwargs):
            raise RuntimeError("You cannot call this method "
                               "from a stateless API client")

        methods = ['all', 'get_by_id', 'sync']
        for obj in self.__dict__.values():
            for method_name in methods:
                if hasattr(obj, method_name):
                    setattr(obj, method_name, stub)


class StatefulTodoistAPI(TodoistAPI):
    """
    A "stateful" subclass of the standard Todoist API. The difference is that
    it automatically saves its state internally on every sync command, can
    be initialized from the Integration object and also emits sync events.
    """
    integration = None

    @classmethod
    def create(cls, integration):
        """
        Initiate API from the integration

        :param powerapp.core.models.Integration integration: the integration object
        """
        if integration.api_state:
            obj = cls.deserialize(integration.api_state)
        else:
            obj = cls(integration.user.api_token)
        obj.api_endpoint = settings.API_ENDPOINT
        obj.integration = integration
        return obj

    def sync(self, commands=None, **kwargs):
        current_state = deepcopy(self.state)
        new_state = super(StatefulTodoistAPI, self).sync(commands, **kwargs)
        return_or_raise(new_state)

        self.integration.api_state = self.serialize()
        self.integration.api_last_sync = now()
        self.integration.save(update_fields=['api_state', 'api_last_sync'])

        self.emit_sync_signals(current_state, new_state)
        return new_state

    def emit_sync_signals(self, api_state, result):
        """
        Process sync result and yield events, one by one
        """
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

                signal_obj = self.integration.app_config.signals[event_name]
                signal_obj.fire()
