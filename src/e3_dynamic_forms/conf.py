from django.conf import settings
from django.utils.module_loading import import_string


DEFAULTS = {
    'FIELD_AGENT_CHECK': 'e3_dynamic_forms.defaults.is_field_agent',
    'USER_ADMIN_UNIT': 'e3_dynamic_forms.defaults.get_user_admin_unit',
    'ADMIN_UNIT_MODEL': None,
    'STAFF_PERMISSION_MIXIN': 'e3_dynamic_forms.permissions.IsStaffMemberMixin',
    'FIELD_AGENT_PERMISSION_MIXIN': 'e3_dynamic_forms.permissions.IsFieldAgentUserMixin',
    'BASE_TEMPLATE': 'e3_dynamic_forms/base.html',
}


class DynamicFormsSettings:
    def __init__(self):
        self._user_settings = None

    @property
    def user_settings(self):
        if self._user_settings is None:
            self._user_settings = getattr(settings, 'DYNAMIC_FORMS', {})
        return self._user_settings

    def __getattr__(self, name):
        if name.startswith('_') or name == 'user_settings':
            raise AttributeError(name)
        if name not in DEFAULTS:
            raise AttributeError(f"Invalid setting: {name}")
        return self.user_settings.get(name, DEFAULTS[name])

    def get_callable(self, name):
        dotted_path = getattr(self, name)
        if dotted_path is None:
            return None
        return import_string(dotted_path)

    def get_model(self, name):
        from django.apps import apps
        model_path = getattr(self, name)
        if model_path is None:
            return None
        return apps.get_model(model_path)

    def get_mixin(self, name):
        dotted_path = getattr(self, name)
        if dotted_path is None:
            return None
        return import_string(dotted_path)

    def reload(self):
        self._user_settings = None


def get_attachment_model():
    from django.apps import apps
    model_label = getattr(settings, 'DYNAMIC_FORMS_ATTACHMENT_MODEL', 'e3_dynamic_forms.Attachment')
    return apps.get_model(model_label)


app_settings = DynamicFormsSettings()
