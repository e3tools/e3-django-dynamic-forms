# e3-django-dynamic-forms

A dynamic JSON-based form engine for Django. Staff design form schemas via a visual web UI, those schemas render server-side as Django forms, and responses are stored as JSON.

## Installation

```bash
pip install e3-django-dynamic-forms
```

## Quick Setup

1. Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    'rest_framework',
    'e3_dynamic_forms',
]
```

2. Include URLs:

```python
urlpatterns = [
    path('dynamic-forms/', include('e3_dynamic_forms.urls')),
]
```

3. Run migrations:

```bash
python manage.py migrate
```

4. Visit `/dynamic-forms/schemas/` to start designing forms.

## Templates

The package ships with a built-in base template (`e3_dynamic_forms/base.html`) so it works out of the box — no need to provide your own `base.html`.

To use your project's base template instead, set `BASE_TEMPLATE` in your settings:

```python
DYNAMIC_FORMS = {
    'BASE_TEMPLATE': 'my_project/base.html',
}
```

The only requirement is that your base template defines a `{% block content %}` block, which is where all dynamic form pages render their content.

## Settings

All settings go in a `DYNAMIC_FORMS` dict in your Django settings:

```python
DYNAMIC_FORMS = {
    'BASE_TEMPLATE': 'e3_dynamic_forms/base.html',       # Template to extend (default: built-in)
    'FIELD_AGENT_CHECK': 'myapp.utils.is_agent',      # Custom field agent check
    'USER_ADMIN_UNIT': 'myapp.utils.get_admin_unit',   # Custom admin unit getter
    'ADMIN_UNIT_MODEL': 'myapp.AdminUnit',             # Admin unit model (optional)
    'STAFF_PERMISSION_MIXIN': 'e3_dynamic_forms.permissions.IsStaffMemberMixin',
    'FIELD_AGENT_PERMISSION_MIXIN': 'e3_dynamic_forms.permissions.IsFieldAgentUserMixin',
}
```

### Swappable Attachment Model

Like `AUTH_USER_MODEL`, you can swap the attachment model:

```python
# settings.py
DYNAMIC_FORMS_ATTACHMENT_MODEL = 'myapp.MyAttachment'
```

```python
# myapp/models.py
from e3_dynamic_forms.models import AbstractAttachment

class MyAttachment(AbstractAttachment):
    extra_field = models.CharField(max_length=255)

    class Meta(AbstractAttachment.Meta):
        swappable = 'DYNAMIC_FORMS_ATTACHMENT_MODEL'
```

## JSON Schema Format

```json
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
                    "help_text": "Help text",
                    "order": 0,
                    "validators": {"min_length": 2, "max_length": 100},
                    "enum": ["opt1", "opt2"],
                    "multi": false,
                    "conditions": {
                        "logic": "AND",
                        "rules": [
                            {"field": "other_field", "operator": "equals", "value": "yes"}
                        ]
                    }
                }
            ]
        }
    ]
}
```

### Supported Field Types

| Type | Description | Validators |
|------|-------------|------------|
| `string` | Text input | `min_length`, `max_length` |
| `number` | Float input | `min_value`, `max_value` |
| `integer` | Integer input | `min_value`, `max_value` |
| `boolean` | Checkbox | — |
| `date` | Date picker | `min_value`, `max_value` (supports `"today"`) |
| `file` | File upload | — |
| `geolocation` | GPS capture button | — |

Add `"enum": [...]` to `string` for dropdown, plus `"multi": true` for checkboxes.

### Condition Operators

`equals`, `not_equals`, `contains`, `greater_than`, `less_than`, `between` (format: `"min,max"`)

## API Endpoints

- `GET/POST /dynamic-forms/api/form-schemas/` — List/create schemas (staff only)
- `GET/PUT/DELETE /dynamic-forms/api/form-schemas/<uuid>/` — Schema detail (staff only)
- `GET/POST /dynamic-forms/api/form-responses/` — List (staff) / create (authenticated)
- `GET /dynamic-forms/api/form-responses/<uuid>/` — Response detail (staff only)
- Filter responses: `?schema=<uuid>`

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```
