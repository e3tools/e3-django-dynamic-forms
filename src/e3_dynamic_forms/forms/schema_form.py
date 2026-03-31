import json

from django import forms
from django.utils.translation import gettext_lazy as _

from ..models import FormSchema
from ..utils.schema_validator import validate_schema


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

        errors = validate_schema(data)
        if errors:
            raise forms.ValidationError([_(e) for e in errors])

        return data
