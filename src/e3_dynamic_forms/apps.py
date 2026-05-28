from django.apps import AppConfig
from django.conf import settings
from django.utils.translation import gettext_lazy as _

_SWAPPABLE_DEFAULTS = {
    'DYNAMIC_FORMS_SCHEMA_MODEL': 'e3_dynamic_forms.FormSchema',
    'DYNAMIC_FORMS_RESPONSE_MODEL': 'e3_dynamic_forms.FormResponse',
    'DYNAMIC_FORMS_ATTACHMENT_MODEL': 'e3_dynamic_forms.Attachment',
}

for _key, _default in _SWAPPABLE_DEFAULTS.items():
    if not hasattr(settings, _key):
        setattr(settings, _key, _default)


class DynamicFormsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'e3_dynamic_forms'
    verbose_name = _('Dynamic Forms')
