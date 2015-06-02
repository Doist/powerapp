# -*- coding: utf-8 -*-
from django.conf import settings


def settings_values(request):
    """
    The context processor which populates template variables with some
    values from settings
    """
    return {'google_site_verification': settings.GOOGLE_SITE_VERIFICATION}
