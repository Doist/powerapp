import os

def configure_app(settings_module='powerapp.settings'):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)
