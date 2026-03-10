import django
from django.conf import settings


def pytest_configure():
    import os
    import sys
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(base_dir, 'src'))

    settings.DJANGO_SETTINGS_MODULE = 'tests.test_app.settings'
    if not settings.configured:
        settings.configure(
            SECRET_KEY='test-secret-key',
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'django.contrib.sessions',
                'django.contrib.messages',
                'django.contrib.admin',
                'rest_framework',
                'e3_dynamic_forms',
                'tests.test_app',
            ],
            ROOT_URLCONF='tests.test_app.urls',
            DEFAULT_AUTO_FIELD='django.db.models.BigAutoField',
            DYNAMIC_FORMS_ATTACHMENT_MODEL='e3_dynamic_forms.Attachment',
            TEMPLATES=[{
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [],
                'APP_DIRS': True,
                'OPTIONS': {
                    'context_processors': [
                        'django.template.context_processors.request',
                        'django.contrib.auth.context_processors.auth',
                        'django.contrib.messages.context_processors.messages',
                    ],
                },
            }],
            MIDDLEWARE=[
                'django.contrib.sessions.middleware.SessionMiddleware',
                'django.contrib.auth.middleware.AuthenticationMiddleware',
                'django.contrib.messages.middleware.MessageMiddleware',
            ],
            USE_TZ=True,
        )
    django.setup()
