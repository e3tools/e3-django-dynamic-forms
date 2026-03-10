"""
Core module: converts a JSON schema into Django form fields.

Schema format:
{
    "pages": [
        {
            "title": "Page 1",
            "fields": [
                {
                    "name": "field_name",
                    "type": "string",
                    "label": "Field Label",
                    "required": true,
                    "help_text": "...",
                    "order": 1,
                    "validators": {"min_length": 2, "max_length": 100},
                    "enum": ["opt1", "opt2"],     # for choice fields
                    "multi": true,                 # for multiple choice
                    "conditions": {
                        "logic": "AND",           # or "OR"
                        "rules": [
                            {"field": "other_field", "operator": "equals", "value": "yes"}
                        ]
                    }
                }
            ]
        }
    ]
}
"""
import datetime

from django import forms
from django.utils.translation import gettext_lazy as _


# ---------------------------------------------------------------------------
# Custom widget & field for geolocation
# ---------------------------------------------------------------------------

class ButtonWidget(forms.Widget):
    template_name = 'e3_dynamic_forms/widgets/geolocation_button.html'

    def __init__(self, attrs=None):
        default_attrs = {'class': 'geolocation-field'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['value'] = value or ''
        return context


class ButtonField(forms.CharField):
    widget = ButtonWidget

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('required', False)
        super().__init__(*args, **kwargs)


# ---------------------------------------------------------------------------
# Condition evaluator
# ---------------------------------------------------------------------------

def evaluate_conditions(conditions, response_data):
    """
    Evaluate conditional visibility rules against existing response data.

    Returns True if the field should be visible.
    If no conditions are provided, returns True (always visible).
    """
    if not conditions or not conditions.get('rules'):
        return True

    if response_data is None:
        response_data = {}

    rules = conditions.get('rules', [])
    logic = conditions.get('logic', 'AND').upper()

    results = []
    for rule in rules:
        field = rule.get('field', '')
        operator = rule.get('operator', 'equals')
        expected = rule.get('value', '')
        actual = response_data.get(field, '')

        result = _evaluate_single_rule(operator, actual, expected)
        results.append(result)

    if not results:
        return True

    if logic == 'OR':
        return any(results)
    return all(results)


def _evaluate_single_rule(operator, actual, expected):
    """Evaluate a single condition rule."""
    actual_str = str(actual) if actual is not None else ''
    expected_str = str(expected) if expected is not None else ''

    if operator == 'equals':
        return actual_str == expected_str
    elif operator == 'not_equals':
        return actual_str != expected_str
    elif operator == 'contains':
        return expected_str in actual_str
    elif operator == 'greater_than':
        try:
            return float(actual_str) > float(expected_str)
        except (ValueError, TypeError):
            return False
    elif operator == 'less_than':
        try:
            return float(actual_str) < float(expected_str)
        except (ValueError, TypeError):
            return False
    elif operator == 'between':
        try:
            parts = expected_str.split(',')
            if len(parts) != 2:
                return False
            low, high = float(parts[0].strip()), float(parts[1].strip())
            val = float(actual_str)
            return low <= val <= high
        except (ValueError, TypeError):
            return False
    return False


# ---------------------------------------------------------------------------
# Field builders
# ---------------------------------------------------------------------------

def _build_string_field(field_def):
    """Build CharField or ChoiceField depending on enum/multi."""
    validators_def = field_def.get('validators', {})
    enum = field_def.get('enum')
    multi = field_def.get('multi', False)

    if enum:
        choices = [('', _('-- Select --'))] + [(v, v) for v in enum]
        if multi:
            choices = [(v, v) for v in enum]
            return forms.MultipleChoiceField(
                choices=choices,
                widget=forms.CheckboxSelectMultiple,
                required=field_def.get('required', False),
            )
        return forms.ChoiceField(
            choices=choices,
            required=field_def.get('required', False),
        )

    kwargs = {}
    if 'min_length' in validators_def:
        kwargs['min_length'] = int(validators_def['min_length'])
    if 'max_length' in validators_def:
        kwargs['max_length'] = int(validators_def['max_length'])
    return forms.CharField(
        required=field_def.get('required', False),
        widget=forms.TextInput,
        **kwargs,
    )


def _build_number_field(field_def):
    validators_def = field_def.get('validators', {})
    kwargs = {}
    if 'min_value' in validators_def:
        kwargs['min_value'] = float(validators_def['min_value'])
    if 'max_value' in validators_def:
        kwargs['max_value'] = float(validators_def['max_value'])
    return forms.FloatField(
        required=field_def.get('required', False),
        **kwargs,
    )


def _build_integer_field(field_def):
    validators_def = field_def.get('validators', {})
    kwargs = {}
    if 'min_value' in validators_def:
        kwargs['min_value'] = int(validators_def['min_value'])
    if 'max_value' in validators_def:
        kwargs['max_value'] = int(validators_def['max_value'])
    return forms.IntegerField(
        required=field_def.get('required', False),
        **kwargs,
    )


def _build_boolean_field(field_def):
    return forms.BooleanField(
        required=False,  # BooleanField required=True means must be checked
    )


def _build_date_field(field_def):
    validators_def = field_def.get('validators', {})
    kwargs = {}
    if 'min_value' in validators_def:
        min_val = validators_def['min_value']
        if min_val == 'today':
            kwargs['validators'] = kwargs.get('validators', [])
        else:
            pass  # handled via widget attrs
    if 'max_value' in validators_def:
        max_val = validators_def['max_value']
        if max_val == 'today':
            pass

    widget_attrs = {'type': 'date'}
    if 'min_value' in validators_def:
        min_val = validators_def['min_value']
        if min_val == 'today':
            widget_attrs['min'] = datetime.date.today().isoformat()
        else:
            widget_attrs['min'] = str(min_val)
    if 'max_value' in validators_def:
        max_val = validators_def['max_value']
        if max_val == 'today':
            widget_attrs['max'] = datetime.date.today().isoformat()
        else:
            widget_attrs['max'] = str(max_val)

    return forms.DateField(
        required=field_def.get('required', False),
        widget=forms.DateInput(attrs=widget_attrs),
    )


def _build_file_field(field_def):
    return forms.FileField(
        required=field_def.get('required', False),
    )


def _build_geolocation_field(field_def):
    return ButtonField(
        required=field_def.get('required', False),
    )


FIELD_BUILDERS = {
    'string': _build_string_field,
    'number': _build_number_field,
    'integer': _build_integer_field,
    'boolean': _build_boolean_field,
    'date': _build_date_field,
    'file': _build_file_field,
    'geolocation': _build_geolocation_field,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_custom_jsonschema(schema, page_index=0, response_data=None):
    """
    Parse a JSON schema and return a list of (field_name, django_field) tuples
    for the given page index.

    Args:
        schema: The full JSON schema dict.
        page_index: Which page to render (0-based).
        response_data: Previously submitted data (for conditional evaluation).

    Returns:
        List of (name, Field) tuples in order.
    """
    pages = schema.get('pages', [])
    if not pages:
        return []

    if page_index < 0 or page_index >= len(pages):
        return []

    page = pages[page_index]
    fields_def = page.get('fields', [])

    # Sort by order if present
    fields_def = sorted(fields_def, key=lambda f: f.get('order', 0))

    result = []
    for field_def in fields_def:
        name = field_def.get('name', '')
        if not name:
            continue

        # Evaluate conditions
        conditions = field_def.get('conditions')
        if conditions and not evaluate_conditions(conditions, response_data):
            continue

        field_type = field_def.get('type', 'string')
        builder = FIELD_BUILDERS.get(field_type, _build_string_field)
        field = builder(field_def)

        # Apply common attributes
        label = field_def.get('label', name)
        field.label = label

        help_text = field_def.get('help_text', '')
        if help_text:
            field.help_text = help_text

        result.append((name, field))

    return result


def build_dynamic_form_class(schema, page_index=0, response_data=None):
    """
    Build and return a Django Form class from a JSON schema for a specific page.

    Args:
        schema: The full JSON schema dict.
        page_index: Which page to render (0-based).
        response_data: Previously submitted data (for conditional evaluation).

    Returns:
        A dynamically created Form class.
    """
    fields = parse_custom_jsonschema(schema, page_index, response_data)
    field_dict = dict(fields)
    return type('DynamicForm', (forms.Form,), field_dict)
