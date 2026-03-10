import json

from django import forms
from django.utils.translation import gettext_lazy as _

from ..models import FormSchema


class FormSchemaForm(forms.ModelForm):
    schema = forms.CharField(
        widget=forms.HiddenInput,
        required=True,
    )

    class Meta:
        model = FormSchema
        fields = ['name', 'description', 'schema', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_schema(self):
        raw = self.cleaned_data.get('schema', '')
        if not raw:
            raise forms.ValidationError(_('Schema is required.'))
        try:
            data = json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            raise forms.ValidationError(_('Invalid JSON format.'))

        if not isinstance(data, dict):
            raise forms.ValidationError(_('Schema must be a JSON object.'))
        if 'pages' not in data:
            raise forms.ValidationError(_('Schema must contain a "pages" key.'))
        if not isinstance(data['pages'], list):
            raise forms.ValidationError(_('"pages" must be a list.'))
        for i, page in enumerate(data['pages']):
            if not isinstance(page, dict):
                raise forms.ValidationError(_(f'Page {i + 1} must be an object.'))
            if 'fields' not in page:
                raise forms.ValidationError(_(f'Page {i + 1} must contain "fields".'))

        return data
