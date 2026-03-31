"""
Validates that a FormResponse's ``data`` dict conforms to the field
definitions declared in the associated FormSchema's ``schema``.

This module is used by both the web view (``_finalize``) and the
FormResponseSerializer to enforce data consistency.

The validator intentionally skips fields with conditions because conditional
visibility depends on runtime data — a field hidden by conditions is allowed
to be absent even if marked ``required``.  For the same reason, ``file`` and
``geolocation`` fields are treated leniently: file uploads are stored as
Attachment objects (not in ``data``), and geolocation values are captured
client-side.
"""
import datetime

from .schema_validator import VALID_FIELD_TYPES


# Field types whose values live outside ``data`` (attachments, client-side capture)
_SKIP_PRESENCE_CHECK_TYPES = {'file'}


def validate_response_data(data, schema):
    """
    Validate *data* (the response dict) against *schema* (the FormSchema's
    ``schema`` JSON).

    Returns a list of human-readable error strings (empty == valid).
    """
    errors = []

    if not isinstance(data, dict):
        return ['Response data must be a JSON object.']

    if not isinstance(schema, dict) or 'pages' not in schema:
        return ['Associated schema is invalid — cannot validate response data.']

    # Build a lookup of every field defined across all pages.
    field_defs = _collect_field_defs(schema)

    if not field_defs:
        # Schema has no fields — data should be empty.
        if data:
            errors.append('Schema defines no fields but response data is not empty.')
        return errors

    known_field_names = set(field_defs.keys())

    # 1. No unknown keys in data
    extra_keys = set(data.keys()) - known_field_names
    if extra_keys:
        errors.append(
            f'Unknown fields in response data: {", ".join(sorted(extra_keys))}.'
        )

    # 2. Required fields must be present (unless conditional or file/geolocation)
    for name, fdef in field_defs.items():
        if not fdef.get('required', False):
            continue
        if fdef.get('type') in _SKIP_PRESENCE_CHECK_TYPES:
            continue
        if fdef.get('conditions'):
            # Conditional fields may legitimately be absent.
            continue
        if name not in data or _is_empty(data[name]):
            errors.append(f'Required field "{name}" is missing or empty.')

    # 3. Value-type checks for present fields
    for name, value in data.items():
        if name not in field_defs:
            continue  # Already flagged as unknown above.
        fdef = field_defs[name]
        field_type = fdef.get('type', 'string')
        field_errors = _validate_value(name, value, fdef, field_type)
        errors.extend(field_errors)

    return errors


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _collect_field_defs(schema):
    """Return an {name: field_def} dict across all pages."""
    defs = {}
    for page in schema.get('pages', []):
        if not isinstance(page, dict):
            continue
        for fdef in page.get('fields', []):
            if not isinstance(fdef, dict):
                continue
            name = fdef.get('name')
            if name:
                defs[name] = fdef
    return defs


def _is_empty(value):
    """Check whether a value should be treated as empty."""
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    if isinstance(value, (list, dict)) and len(value) == 0:
        return True
    return False


def _validate_value(name, value, fdef, field_type):
    """Run type-appropriate checks on a single field value."""
    errors = []

    # Allow None / empty for non-required fields (they passed the required check above).
    if _is_empty(value) and not fdef.get('required', False):
        return errors

    if field_type == 'string':
        errors.extend(_validate_string(name, value, fdef))
    elif field_type in ('number', 'integer'):
        errors.extend(_validate_numeric(name, value, field_type, fdef))
    elif field_type == 'boolean':
        errors.extend(_validate_boolean(name, value))
    elif field_type == 'date':
        errors.extend(_validate_date(name, value, fdef))
    # file / geolocation — no type check on data (stored elsewhere or free-text).

    return errors


def _validate_string(name, value, fdef):
    errors = []
    enum = fdef.get('enum')
    multi = fdef.get('multi', False)

    if multi and enum:
        # Value should be a list of valid options.
        if not isinstance(value, list):
            errors.append(f'Field "{name}": expected a list for multi-select, got {type(value).__name__}.')
            return errors
        invalid = [v for v in value if v not in enum]
        if invalid:
            errors.append(f'Field "{name}": invalid options: {", ".join(str(v) for v in invalid)}.')
        return errors

    if enum:
        if not isinstance(value, str):
            errors.append(f'Field "{name}": expected a string, got {type(value).__name__}.')
            return errors
        if value and value not in enum:
            errors.append(f'Field "{name}": value "{value}" is not one of the allowed options.')
        return errors

    if not isinstance(value, str):
        errors.append(f'Field "{name}": expected a string, got {type(value).__name__}.')
        return errors

    validators = fdef.get('validators', {})
    if 'min_length' in validators:
        try:
            min_len = int(validators['min_length'])
            if len(value) < min_len:
                errors.append(f'Field "{name}": value is shorter than minimum length {min_len}.')
        except (ValueError, TypeError):
            pass
    if 'max_length' in validators:
        try:
            max_len = int(validators['max_length'])
            if len(value) > max_len:
                errors.append(f'Field "{name}": value exceeds maximum length {max_len}.')
        except (ValueError, TypeError):
            pass

    return errors


def _validate_numeric(name, value, field_type, fdef):
    errors = []

    # After form processing values may arrive as strings — try to coerce.
    numeric_value = value
    if isinstance(value, str):
        try:
            numeric_value = int(value) if field_type == 'integer' else float(value)
        except (ValueError, TypeError):
            errors.append(f'Field "{name}": expected a {field_type}, got non-numeric string "{value}".')
            return errors
    elif isinstance(value, bool):
        # bool is a subclass of int in Python — reject explicitly.
        errors.append(f'Field "{name}": expected a {field_type}, got boolean.')
        return errors
    elif not isinstance(value, (int, float)):
        errors.append(f'Field "{name}": expected a {field_type}, got {type(value).__name__}.')
        return errors

    if field_type == 'integer' and isinstance(numeric_value, float) and not numeric_value.is_integer():
        errors.append(f'Field "{name}": expected an integer, got a float.')
        return errors

    validators = fdef.get('validators', {})
    if 'min_value' in validators:
        try:
            min_val = float(validators['min_value'])
            if float(numeric_value) < min_val:
                errors.append(f'Field "{name}": value {numeric_value} is less than minimum {validators["min_value"]}.')
        except (ValueError, TypeError):
            pass
    if 'max_value' in validators:
        try:
            max_val = float(validators['max_value'])
            if float(numeric_value) > max_val:
                errors.append(f'Field "{name}": value {numeric_value} is greater than maximum {validators["max_value"]}.')
        except (ValueError, TypeError):
            pass

    return errors


def _validate_boolean(name, value):
    if not isinstance(value, bool):
        return [f'Field "{name}": expected a boolean, got {type(value).__name__}.']
    return []


def _validate_date(name, value, fdef):
    errors = []
    if not isinstance(value, str):
        errors.append(f'Field "{name}": expected a date string (YYYY-MM-DD), got {type(value).__name__}.')
        return errors

    try:
        parsed = datetime.date.fromisoformat(value)
    except (ValueError, TypeError):
        errors.append(f'Field "{name}": "{value}" is not a valid date (expected YYYY-MM-DD).')
        return errors

    validators = fdef.get('validators', {})
    today = datetime.date.today()

    if 'min_value' in validators:
        min_str = validators['min_value']
        try:
            min_date = today if min_str == 'today' else datetime.date.fromisoformat(min_str)
            if parsed < min_date:
                errors.append(f'Field "{name}": date {value} is before minimum {min_date.isoformat()}.')
        except (ValueError, TypeError):
            pass

    if 'max_value' in validators:
        max_str = validators['max_value']
        try:
            max_date = today if max_str == 'today' else datetime.date.fromisoformat(max_str)
            if parsed > max_date:
                errors.append(f'Field "{name}": date {value} is after maximum {max_date.isoformat()}.')
        except (ValueError, TypeError):
            pass

    return errors
