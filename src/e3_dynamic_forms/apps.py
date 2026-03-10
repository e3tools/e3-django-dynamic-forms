from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DynamicFormsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'e3_dynamic_forms'
    verbose_name = _('Dynamic Forms')
