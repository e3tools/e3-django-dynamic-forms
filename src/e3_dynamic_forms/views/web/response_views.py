from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, DetailView, TemplateView

from ...conf import app_settings, get_attachment_model
from ...models import FormSchema, FormResponse
from ...services import FormResponseProcessor, SessionStateBackend


class _BaseContextMixin:
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['base_template'] = app_settings.BASE_TEMPLATE
        return ctx


def get_response_list_view():
    Mixin = app_settings.get_mixin('STAFF_PERMISSION_MIXIN')

    class ResponseListView(Mixin, _BaseContextMixin, ListView):
        model = FormResponse
        template_name = 'e3_dynamic_forms/response_list.html'
        context_object_name = 'responses'
        paginate_by = 20

        def get_queryset(self):
            qs = super().get_queryset().select_related('schema', 'created_by')
            schema_pk = self.kwargs.get('schema_pk')
            if schema_pk:
                qs = qs.filter(schema_id=schema_pk)
            return qs

        def get_context_data(self, **kwargs):
            ctx = super().get_context_data(**kwargs)
            schema_pk = self.kwargs.get('schema_pk')
            if schema_pk:
                ctx['schema'] = get_object_or_404(FormSchema, pk=schema_pk)
            return ctx

    return ResponseListView


def get_response_detail_view():
    Mixin = app_settings.get_mixin('STAFF_PERMISSION_MIXIN')

    class ResponseDetailView(Mixin, _BaseContextMixin, DetailView):
        model = FormResponse
        template_name = 'e3_dynamic_forms/response_detail.html'
        context_object_name = 'response'

        def get_context_data(self, **kwargs):
            ctx = super().get_context_data(**kwargs)
            Attachment = get_attachment_model()
            ctx['attachments'] = Attachment.objects.filter(response=self.object)
            return ctx

    return ResponseDetailView


def get_response_create_view():
    Mixin = app_settings.get_mixin('FIELD_AGENT_PERMISSION_MIXIN')

    class ResponseCreateView(Mixin, _BaseContextMixin, TemplateView):
        template_name = 'e3_dynamic_forms/response_create.html'

        def dispatch(self, request, *args, **kwargs):
            self.schema_obj = get_object_or_404(FormSchema, pk=kwargs['pk'], is_active=True)
            self.processor = FormResponseProcessor(
                self.schema_obj, SessionStateBackend(request.session),
            )
            return super().dispatch(request, *args, **kwargs)

        def get_context_data(self, **kwargs):
            ctx = super().get_context_data(**kwargs)
            ctx['schema'] = self.schema_obj
            ctx['form'] = kwargs.get('form', self.processor.get_blank_form())
            ctx['current_page'] = self.processor.current_page
            ctx['total_pages'] = self.processor.total_pages
            ctx['is_last_page'] = self.processor.is_last_page
            return ctx

        def post(self, request, *args, **kwargs):
            result = self.processor.process_page(
                request.POST, request.FILES, user=request.user,
            )

            if not result.is_valid:
                return self.render_to_response(
                    self.get_context_data(form=result.form)
                )

            if result.is_complete:
                return HttpResponseRedirect(
                    reverse('e3_dynamic_forms:response_list',
                            kwargs={'schema_pk': self.schema_obj.pk})
                )

            return HttpResponseRedirect(
                reverse('e3_dynamic_forms:response_create',
                        kwargs={'pk': self.schema_obj.pk})
            )

    return ResponseCreateView
