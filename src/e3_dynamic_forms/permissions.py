from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .conf import app_settings


class IsStaffMemberMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Allows access only to staff members or superusers."""

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


class IsFieldAgentUserMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Allows access to field agent users as determined by the configured check."""

    def test_func(self):
        check_fn = app_settings.get_callable('FIELD_AGENT_CHECK')
        if check_fn:
            return check_fn(self.request.user)
        return self.request.user.is_authenticated
