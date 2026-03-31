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

Schemas are validated on save — both via the web UI (Django form) and the REST API (DRF serializer). The same validation rules apply in both paths, enforced by `e3_dynamic_forms.utils.schema_validator.validate_schema`.

### Structure Overview

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

### Root

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `pages` | array | Yes | List of page objects. Must contain at least one page. No other root-level keys are allowed. |

### Page Object

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `title` | string | Yes | Non-empty page title displayed to the user. |
| `fields` | array | Yes | List of field objects (may be empty). |

### Field Object

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `name` | string | Yes | Unique field identifier. Must be lowercase snake_case (`^[a-z][a-z0-9_]*$`). Must be unique across **all** pages. |
| `type` | string | Yes | One of: `string`, `number`, `integer`, `boolean`, `date`, `file`, `geolocation`. |
| `label` | string | Yes | Non-empty display label. |
| `required` | boolean | No | Whether the field is required. Defaults to `false`. |
| `help_text` | string | No | Optional help text shown below the field. |
| `order` | integer | No | Sort order within the page. |
| `validators` | object | No | Type-specific validation rules (see table below). |
| `enum` | array | No | List of non-empty strings. Only valid for `type: "string"`. Renders a dropdown (or checkboxes if `multi` is set). |
| `multi` | boolean | No | Enable multiple selection. Requires `enum` to be set. |
| `conditions` | object | No | Conditional visibility rules (see below). |

No other keys are allowed on a field object.

### Supported Field Types and Validators

| Type | Description | Allowed Validators |
|------|-------------|--------------------|
| `string` | Text input (or choice field with `enum`) | `min_length`, `max_length` |
| `number` | Float input | `min_value`, `max_value` |
| `integer` | Integer input | `min_value`, `max_value` |
| `boolean` | Checkbox | — (no validators) |
| `date` | Date picker | `min_value`, `max_value` (accepts date strings or `"today"`) |
| `file` | File upload | — (no validators) |
| `geolocation` | GPS capture button | — (no validators) |

Validator values for `string`, `number`, and `integer` must be numeric (int, float, or numeric string). Using a validator key not listed for the field's type will cause a validation error.

### Enum and Multi-select

- Add `"enum": ["Option A", "Option B"]` to a `string` field to render it as a dropdown.
- Add `"multi": true` alongside `enum` to render checkboxes allowing multiple selections.
- `enum` is only valid on `string` fields and must be a non-empty list of non-empty strings.
- `multi` without `enum` is invalid.

### Conditions (Conditional Visibility)

Fields can be conditionally shown/hidden based on previously submitted data (useful in multi-page forms).

```json
{
    "conditions": {
        "logic": "AND",
        "rules": [
            {"field": "other_field", "operator": "equals", "value": "yes"}
        ]
    }
}
```

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `logic` | string | Yes | `"AND"` (all rules must pass) or `"OR"` (any rule must pass). |
| `rules` | array | Yes | Non-empty list of rule objects. |

**Rule object:**

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `field` | string | Yes | Name of the field to evaluate against. |
| `operator` | string | Yes | One of: `equals`, `not_equals`, `contains`, `greater_than`, `less_than`, `between`. |
| `value` | any | Yes | The value to compare against. For `between`, use the format `"min,max"`. |

### Schema Validation

Schema validation runs automatically when saving via:

- **Web UI** — `FormSchemaForm.clean_schema()` validates the JSON before saving.
- **REST API** — `FormSchemaSerializer.validate_schema()` validates the JSON on create/update.

Both use the same underlying validator (`e3_dynamic_forms.utils.schema_validator.validate_schema`). You can also call it directly:

```python
from e3_dynamic_forms.utils.schema_validator import validate_schema

errors = validate_schema(my_schema_dict)
if errors:
    print(errors)  # List of human-readable error strings
```

## Response Data Validation

When a form response is submitted, the `data` JSON is validated against the associated schema's field definitions. This validation runs in both the web UI (on final page submit) and the REST API (on create/update).

### What is validated

| Check | Description |
|-------|-------------|
| No unknown keys | Every key in `data` must correspond to a field `name` defined in the schema. |
| Required fields present | Fields marked `required: true` must be present and non-empty. |
| Type checking | Values are checked against their field type (see table below). |
| Enum enforcement | For fields with `enum`, submitted values must be from the allowed list. |
| Validator constraints | `min_length`/`max_length` for strings, `min_value`/`max_value` for numbers/integers/dates. |

### Type-specific value rules

| Field Type | Expected `data` value | Notes |
|------------|-----------------------|-------|
| `string` | `string` | Numeric strings accepted for coercion in `number`/`integer` fields, but `string` fields must be actual strings. |
| `string` + `enum` | `string` | Must match one of the `enum` options. |
| `string` + `enum` + `multi` | `list` of `string` | Each item must match an `enum` option. |
| `number` | `number` or numeric `string` | Strings like `"3.14"` are accepted. Booleans are rejected. |
| `integer` | `int` or integer `string` | Floats like `3.5` are rejected. Strings like `"25"` are accepted. |
| `boolean` | `boolean` | Strings like `"true"` are rejected — must be actual `true`/`false`. |
| `date` | `string` (YYYY-MM-DD) | Validated as ISO 8601 date. Min/max constraints support `"today"`. |
| `file` | — | Not expected in `data`. File uploads are stored as `Attachment` objects. |
| `geolocation` | `string` | Free-form text (typically `"lat,lng"`). No strict format enforced. |

### Special cases

- **Conditional fields**: Fields with `conditions` are exempt from the required-field check, since they may be hidden at runtime based on other responses.
- **File fields**: Skipped in the required-field check on `data` because file uploads are stored as `Attachment` records, not in the `data` JSON.
- **Multi-page forms**: All fields across all pages are validated together against the accumulated response data.

### Programmatic usage

```python
from e3_dynamic_forms.utils.response_validator import validate_response_data

errors = validate_response_data(
    data={'full_name': 'Alice', 'age': 30},
    schema=form_schema_instance.schema,
)
if errors:
    print(errors)  # List of human-readable error strings
```

## Form Response Processor

The package provides a reusable `FormResponseProcessor` service that handles the full multi-page form lifecycle: page tracking, data accumulation, validation, and response creation. The built-in views use this processor internally, and you can use it in your own custom views.

### Quick start

```python
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView
from e3_dynamic_forms.models import FormSchema
from e3_dynamic_forms.services import FormResponseProcessor, SessionStateBackend


class MySurveyView(LoginRequiredMixin, TemplateView):
    template_name = 'my_app/survey.html'

    def dispatch(self, request, *args, **kwargs):
        self.schema = get_object_or_404(FormSchema, pk=kwargs['pk'])
        self.processor = FormResponseProcessor(
            self.schema, SessionStateBackend(request.session),
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
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
            return self.render_to_response(self.get_context_data(form=result.form))

        if result.is_complete:
            return redirect('my_app:thank_you', response_id=result.response.pk)

        return redirect('my_app:survey', pk=self.schema.pk)
```

### API Reference

**`FormResponseProcessor(schema, state_backend)`**

| Property / Method | Returns | Description |
|-------------------|---------|-------------|
| `current_page` | `int` | Current 0-based page index. |
| `total_pages` | `int` | Total number of pages in the schema. |
| `is_last_page` | `bool` | Whether the current page is the final page. |
| `accumulated_data` | `dict` | Data collected from all completed pages so far. |
| `get_form_class(page_index=None)` | `type` | Build the dynamic Django Form class for a page (defaults to current). |
| `get_blank_form()` | `Form` | Unbound form instance for the current page. |
| `process_page(post_data, files, user=None)` | `PageResult` | Validate and process a submitted page. |
| `reset()` | `None` | Discard all accumulated state (e.g. user cancels). |

**`PageResult`** (dataclass returned by `process_page`):

| Field | Type | Description |
|-------|------|-------------|
| `is_valid` | `bool` | Whether validation passed. |
| `form` | `Form` or `None` | Bound form with errors (if invalid) or `None` (if complete). |
| `is_complete` | `bool` | `True` when the final page was submitted successfully. |
| `response` | `FormResponse` or `None` | The newly created response (only when `is_complete` is `True`). |
| `validation_errors` | `list[str]` | Accumulated-data validation errors (only on final-page failure). |

### State backends

The processor delegates state storage to a `StateBackend`. The package ships with `SessionStateBackend` (Django sessions). You can implement your own for different storage strategies:

```python
from e3_dynamic_forms.services import StateBackend


class CacheStateBackend(StateBackend):
    """Example: store form state in Django's cache framework."""

    def __init__(self, cache_key_prefix, timeout=3600):
        self._prefix = cache_key_prefix
        self._timeout = timeout

    def get_current_page(self, schema_id):
        from django.core.cache import cache
        return cache.get(f'{self._prefix}_{schema_id}_page', 0)

    def set_current_page(self, schema_id, page_index):
        from django.core.cache import cache
        cache.set(f'{self._prefix}_{schema_id}_page', page_index, self._timeout)

    def get_accumulated_data(self, schema_id):
        from django.core.cache import cache
        return cache.get(f'{self._prefix}_{schema_id}_data', {})

    def set_accumulated_data(self, schema_id, data):
        from django.core.cache import cache
        cache.set(f'{self._prefix}_{schema_id}_data', data, self._timeout)

    def clear(self, schema_id):
        from django.core.cache import cache
        cache.delete(f'{self._prefix}_{schema_id}_page')
        cache.delete(f'{self._prefix}_{schema_id}_data')
```

## API Endpoints

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| `GET` | `/dynamic-forms/api/form-schemas/` | Staff | List all schemas |
| `POST` | `/dynamic-forms/api/form-schemas/` | Staff | Create a schema |
| `GET` | `/dynamic-forms/api/form-schemas/<uuid>/` | Staff | Retrieve a schema |
| `PUT/PATCH` | `/dynamic-forms/api/form-schemas/<uuid>/` | Staff | Update a schema |
| `DELETE` | `/dynamic-forms/api/form-schemas/<uuid>/` | Staff | Delete a schema |
| `GET` | `/dynamic-forms/api/form-responses/` | Staff | List responses (filter: `?schema=<uuid>`) |
| `POST` | `/dynamic-forms/api/form-responses/` | Authenticated | Submit a response |
| `GET` | `/dynamic-forms/api/form-responses/<uuid>/` | Staff | Retrieve a response |

### Creating responses via the API

The API accepts a single-shot submission — all field data in one request (no multi-page state). Both JSON and multipart requests are supported.

**JSON request** (no file uploads):

```bash
curl -X POST /dynamic-forms/api/form-responses/ \
  -H "Content-Type: application/json" \
  -d '{
    "schema": "<schema-uuid>",
    "data": {
      "full_name": "Alice Smith",
      "age": 30,
      "country": "Canada"
    }
  }'
```

**Multipart request** (with file uploads):

```bash
curl -X POST /dynamic-forms/api/form-responses/ \
  -F "schema=<schema-uuid>" \
  -F 'data={"full_name": "Alice Smith", "age": 30}' \
  -F "photo=@/path/to/photo.jpg"
```

When using `multipart/form-data`, the `data` field must be a JSON-encoded string. File fields are sent as standard multipart file uploads — the field name in the upload must match the field `name` in the schema.

**Response format:**

```json
{
  "id": "uuid",
  "schema": "schema-uuid",
  "data": {"full_name": "Alice Smith", "age": 30},
  "created_by": 1,
  "created_date": "2025-01-15T10:30:00Z",
  "updated_date": "2025-01-15T10:30:00Z",
  "attachments": [
    {
      "id": "uuid",
      "field_name": "photo",
      "file": "/media/e3_dynamic_forms/attachments/2025/01/photo.jpg",
      "created_date": "2025-01-15T10:30:00Z"
    }
  ]
}
```

### What gets validated on the API

The same validation that runs on the web UI also runs on the API:

- Response `data` is validated against the schema's field definitions (unknown keys, required fields, type checking, enum enforcement, validator constraints)
- File uploads are stored as `Attachment` objects linked to the response
- The `created_by` field is automatically set to the authenticated user

See [Response Data Validation](#response-data-validation) for the full validation rules.

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```
