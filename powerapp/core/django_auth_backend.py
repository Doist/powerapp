from powerapp.core.models import User


class TodoistUserAuth(object):

    def authenticate(self, user):
        if isinstance(user, User) and user.api_token:
            return user
        else:
            return None

    def get_user(self, uid):
        try:
            return User.objects.get(id=uid)
        except User.DoesNotExist:
            return None
