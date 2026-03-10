import json

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, DetailView, TemplateView

from ...conf import app_settings, get_attachment_model
from ...models import FormSchema, FormResponse
from ...utils.json_form_parser import build_dynamic_form_class


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
            return super().dispatch(request, *args, **kwargs)

        def _session_key(self, suffix):
            return f'df_{self.schema_obj.pk}_{suffix}'

        def _get_accumulated_data(self):
            raw = self.request.session.get(self._session_key('accumulated_data'), '{}')
            if isinstance(raw, str):
                try:
                    return json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    return {}
            return raw

        def _get_current_page(self):
            return self.request.session.get(self._session_key('current_page'), 0)

        def _get_form_class(self, page_index, accumulated_data):
            return build_dynamic_form_class(
                self.schema_obj.schema,
                page_index=page_index,
                response_data=accumulated_data,
            )

        def get_context_data(self, **kwargs):
            ctx = super().get_context_data(**kwargs)
            page_index = self._get_current_page()
            accumulated_data = self._get_accumulated_data()
            FormClass = self._get_form_class(page_index, accumulated_data)

            ctx['schema'] = self.schema_obj
            ctx['form'] = kwargs.get('form', FormClass())
            ctx['current_page'] = page_index
            ctx['total_pages'] = self.schema_obj.page_count
            ctx['is_last_page'] = page_index >= self.schema_obj.page_count - 1
            return ctx

        def post(self, request, *args, **kwargs):
            page_index = self._get_current_page()
            accumulated_data = self._get_accumulated_data()
            FormClass = self._get_form_class(page_index, accumulated_data)
            form = FormClass(request.POST, request.FILES)

            if not form.is_valid():
                return self.render_to_response(self.get_context_data(form=form))

            # Merge page data
            for key, value in form.cleaned_data.items():
                if hasattr(value, 'read'):
                    # Skip files in accumulated data — handle on final submit
                    continue
                accumulated_data[key] = value
            self.request.session[self._session_key('accumulated_data')] = json.dumps(
                accumulated_data, default=str
            )

            is_last_page = page_index >= self.schema_obj.page_count - 1

            if is_last_page:
                return self._finalize(request, form, accumulated_data)

            # Advance to next page
            self.request.session[self._session_key('current_page')] = page_index + 1
            return HttpResponseRedirect(
                reverse('e3_dynamic_forms:response_create', kwargs={'pk': self.schema_obj.pk})
            )

        def _finalize(self, request, form, accumulated_data):
            response = FormResponse.objects.create(
                schema=self.schema_obj,
                data=accumulated_data,
                created_by=request.user if request.user.is_authenticated else None,
            )

            # Handle file attachments
            Attachment = get_attachment_model()
            for field_name, file_obj in request.FILES.items():
                Attachment.objects.create(
                    response=response,
                    field_name=field_name,
                    file=file_obj,
                )

            # Clean up session
            self.request.session.pop(self._session_key('current_page'), None)
            self.request.session.pop(self._session_key('accumulated_data'), None)

            return HttpResponseRedirect(
                reverse('e3_dynamic_forms:response_list', kwargs={'schema_pk': self.schema_obj.pk})
            )

    return ResponseCreateView
