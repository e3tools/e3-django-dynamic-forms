from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView

from ...conf import app_settings
from ...forms.schema_form import FormSchemaForm
from ...models import FormSchema


def _get_mixin():
    """Get the configured staff permission mixin."""
    return app_settings.get_mixin('STAFF_PERMISSION_MIXIN')


class _BaseContextMixin:
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['base_template'] = app_settings.BASE_TEMPLATE
        return ctx


def get_schema_list_view():
    Mixin = _get_mixin()

    class SchemaListView(Mixin, _BaseContextMixin, ListView):
        model = FormSchema
        template_name = 'e3_dynamic_forms/schema_list.html'
        context_object_name = 'schemas'
        paginate_by = 20

    return SchemaListView


def get_schema_create_view():
    Mixin = _get_mixin()

    class SchemaCreateView(Mixin, _BaseContextMixin, CreateView):
        model = FormSchema
        form_class = FormSchemaForm
        template_name = 'e3_dynamic_forms/schema_create.html'
        success_url = reverse_lazy('e3_dynamic_forms:schema_list')

        def form_valid(self, form):
            form.instance.created_by = self.request.user
            return super().form_valid(form)

    return SchemaCreateView


def get_schema_edit_view():
    Mixin = _get_mixin()

    class SchemaEditView(Mixin, _BaseContextMixin, UpdateView):
        model = FormSchema
        form_class = FormSchemaForm
        template_name = 'e3_dynamic_forms/schema_edit.html'
        success_url = reverse_lazy('e3_dynamic_forms:schema_list')

        def form_valid(self, form):
            form.instance.version += 1
            return super().form_valid(form)

    return SchemaEditView


def get_schema_detail_view():
    Mixin = _get_mixin()

    class SchemaDetailView(Mixin, _BaseContextMixin, DetailView):
        model = FormSchema
        template_name = 'e3_dynamic_forms/schema_detail.html'
        context_object_name = 'schema'

        def get_context_data(self, **kwargs):
            ctx = super().get_context_data(**kwargs)
            ctx['recent_responses'] = self.object.responses.order_by('-created_date')[:10]
            return ctx

    return SchemaDetailView


def get_schema_delete_view():
    Mixin = _get_mixin()

    class SchemaDeleteView(Mixin, _BaseContextMixin, DeleteView):
        model = FormSchema
        template_name = 'e3_dynamic_forms/schema_delete.html'
        success_url = reverse_lazy('e3_dynamic_forms:schema_list')
        context_object_name = 'schema'

    return SchemaDeleteView
