"""
Validates that a JSON schema conforms to the structure expected by the
DynamicFormsDesigner JS builder and the json_form_parser module.

This module is used by both FormSchemaForm (Django form) and
FormSchemaSerializer (DRF serializer) to enforce structural consistency.
"""
import re

VALID_FIELD_TYPES = {'string', 'number', 'integer', 'boolean', 'date', 'file', 'geolocation'}

VALIDATORS_BY_TYPE = {
    'string': {'min_length', 'max_length'},
    'number': {'min_value', 'max_value'},
    'integer': {'min_value', 'max_value'},
    'date': {'min_value', 'max_value'},
    'boolean': set(),
    'file': set(),
    'geolocation': set(),
}

VALID_CONDITION_OPERATORS = {'equals', 'not_equals', 'contains', 'greater_than', 'less_than', 'between'}
VALID_CONDITION_LOGIC = {'AND', 'OR'}

FIELD_NAME_RE = re.compile(r'^[a-z][a-z0-9_]*$')


def validate_schema(data):
    """
    Validate a schema dict and return a list of error strings.
    Returns an empty list if the schema is valid.
    """
    errors = []

    if not isinstance(data, dict):
        return ['Schema must be a JSON object.']

    if 'pages' not in data:
        return ['Schema must contain a "pages" key.']

    # Only 'pages' is allowed at root level
    extra_root = set(data.keys()) - {'pages'}
    if extra_root:
        errors.append(f'Unknown root-level keys: {", ".join(sorted(extra_root))}.')

    pages = data['pages']
    if not isinstance(pages, list):
        return ['The "pages" key must be a list.']

    if len(pages) == 0:
        return ['Schema must contain at least one page.']

    all_field_names = set()

    for page_idx, page in enumerate(pages):
        page_label = f'Page {page_idx + 1}'
        errors.extend(_validate_page(page, page_label, all_field_names))

    return errors


def _validate_page(page, page_label, all_field_names):
    errors = []

    if not isinstance(page, dict):
        return [f'{page_label}: must be an object.']

    allowed_page_keys = {'title', 'fields'}
    extra = set(page.keys()) - allowed_page_keys
    if extra:
        errors.append(f'{page_label}: unknown keys: {", ".join(sorted(extra))}.')

    # title
    if 'title' not in page:
        errors.append(f'{page_label}: must have a "title".')
    elif not isinstance(page['title'], str) or not page['title'].strip():
        errors.append(f'{page_label}: "title" must be a non-empty string.')

    # fields
    if 'fields' not in page:
        errors.append(f'{page_label}: must contain "fields".')
        return errors

    fields = page['fields']
    if not isinstance(fields, list):
        errors.append(f'{page_label}: "fields" must be a list.')
        return errors

    for field_idx, field_def in enumerate(fields):
        field_label = f'{page_label}, Field {field_idx + 1}'
        errors.extend(_validate_field(field_def, field_label, all_field_names))

    return errors


def _validate_field(field_def, field_label, all_field_names):
    errors = []

    if not isinstance(field_def, dict):
        return [f'{field_label}: must be an object.']

    allowed_field_keys = {
        'name', 'type', 'label', 'required', 'help_text',
        'order', 'validators', 'enum', 'multi', 'conditions',
    }
    extra = set(field_def.keys()) - allowed_field_keys
    if extra:
        errors.append(f'{field_label}: unknown keys: {", ".join(sorted(extra))}.')

    # name (required)
    name = field_def.get('name')
    if not name or not isinstance(name, str):
        errors.append(f'{field_label}: "name" is required and must be a non-empty string.')
    elif not FIELD_NAME_RE.match(name):
        errors.append(
            f'{field_label}: "name" ("{name}") must be lowercase, start with a letter, '
            f'and contain only letters, digits, and underscores.'
        )
    else:
        if name in all_field_names:
            errors.append(f'{field_label}: duplicate field name "{name}".')
        all_field_names.add(name)

    # type (required)
    field_type = field_def.get('type')
    if not field_type or not isinstance(field_type, str):
        errors.append(f'{field_label}: "type" is required.')
    elif field_type not in VALID_FIELD_TYPES:
        errors.append(
            f'{field_label}: invalid type "{field_type}". '
            f'Must be one of: {", ".join(sorted(VALID_FIELD_TYPES))}.'
        )

    # label (required)
    label = field_def.get('label')
    if not label or not isinstance(label, str):
        errors.append(f'{field_label}: "label" is required and must be a non-empty string.')

    # required (must be bool if present)
    if 'required' in field_def and not isinstance(field_def['required'], bool):
        errors.append(f'{field_label}: "required" must be a boolean.')

    # help_text (must be string if present)
    if 'help_text' in field_def:
        if not isinstance(field_def['help_text'], str):
            errors.append(f'{field_label}: "help_text" must be a string.')

    # order (must be int if present)
    if 'order' in field_def:
        if not isinstance(field_def['order'], int):
            errors.append(f'{field_label}: "order" must be an integer.')

    # validators
    if 'validators' in field_def and field_type in VALID_FIELD_TYPES:
        errors.extend(_validate_validators(
            field_def['validators'], field_type, field_label,
        ))

    # enum / multi
    if 'enum' in field_def:
        errors.extend(_validate_enum(field_def, field_type, field_label))

    if 'multi' in field_def:
        if not isinstance(field_def['multi'], bool):
            errors.append(f'{field_label}: "multi" must be a boolean.')
        if 'enum' not in field_def:
            errors.append(f'{field_label}: "multi" requires "enum" to be set.')

    # conditions
    if 'conditions' in field_def:
        errors.extend(_validate_conditions(field_def['conditions'], field_label))

    return errors


def _validate_validators(validators, field_type, field_label):
    errors = []

    if not isinstance(validators, dict):
        errors.append(f'{field_label}: "validators" must be an object.')
        return errors

    allowed = VALIDATORS_BY_TYPE.get(field_type, set())
    extra = set(validators.keys()) - allowed
    if extra:
        errors.append(
            f'{field_label}: invalid validator keys for type "{field_type}": '
            f'{", ".join(sorted(extra))}.'
        )

    # Validate that numeric validator values are actually numeric (or "today" for date)
    for key, value in validators.items():
        if key not in allowed:
            continue
        if field_type == 'date':
            if not isinstance(value, str):
                errors.append(f'{field_label}: validator "{key}" must be a string (date or "today").')
        elif field_type in ('number', 'integer', 'string'):
            if not isinstance(value, (int, float, str)):
                errors.append(f'{field_label}: validator "{key}" must be a numeric value or numeric string.')
            elif isinstance(value, str):
                try:
                    float(value)
                except ValueError:
                    errors.append(f'{field_label}: validator "{key}" value "{value}" is not numeric.')

    return errors


def _validate_enum(field_def, field_type, field_label):
    errors = []
    enum = field_def['enum']

    if field_type != 'string':
        errors.append(f'{field_label}: "enum" is only valid for type "string".')
        return errors

    if not isinstance(enum, list):
        errors.append(f'{field_label}: "enum" must be a list.')
        return errors

    if len(enum) == 0:
        errors.append(f'{field_label}: "enum" must not be empty.')
        return errors

    for i, option in enumerate(enum):
        if not isinstance(option, str) or not option.strip():
            errors.append(f'{field_label}: enum option {i + 1} must be a non-empty string.')

    return errors


def _validate_conditions(conditions, field_label):
    errors = []

    if not isinstance(conditions, dict):
        errors.append(f'{field_label}: "conditions" must be an object.')
        return errors

    allowed_keys = {'logic', 'rules'}
    extra = set(conditions.keys()) - allowed_keys
    if extra:
        errors.append(f'{field_label}: "conditions" has unknown keys: {", ".join(sorted(extra))}.')

    # logic
    logic = conditions.get('logic')
    if not logic or not isinstance(logic, str):
        errors.append(f'{field_label}: conditions "logic" is required and must be a string.')
    elif logic.upper() not in VALID_CONDITION_LOGIC:
        errors.append(f'{field_label}: conditions "logic" must be "AND" or "OR".')

    # rules
    rules = conditions.get('rules')
    if rules is None:
        errors.append(f'{field_label}: conditions must contain "rules".')
        return errors

    if not isinstance(rules, list):
        errors.append(f'{field_label}: conditions "rules" must be a list.')
        return errors

    if len(rules) == 0:
        errors.append(f'{field_label}: conditions "rules" must not be empty.')
        return errors

    for rule_idx, rule in enumerate(rules):
        rule_label = f'{field_label}, Rule {rule_idx + 1}'
        errors.extend(_validate_condition_rule(rule, rule_label))

    return errors


def _validate_condition_rule(rule, rule_label):
    errors = []

    if not isinstance(rule, dict):
        return [f'{rule_label}: must be an object.']

    allowed_keys = {'field', 'operator', 'value'}
    extra = set(rule.keys()) - allowed_keys
    if extra:
        errors.append(f'{rule_label}: unknown keys: {", ".join(sorted(extra))}.')

    # field
    field = rule.get('field')
    if not field or not isinstance(field, str):
        errors.append(f'{rule_label}: "field" is required and must be a non-empty string.')

    # operator
    operator = rule.get('operator')
    if not operator or not isinstance(operator, str):
        errors.append(f'{rule_label}: "operator" is required.')
    elif operator not in VALID_CONDITION_OPERATORS:
        errors.append(
            f'{rule_label}: invalid operator "{operator}". '
            f'Must be one of: {", ".join(sorted(VALID_CONDITION_OPERATORS))}.'
        )

    # value (required, can be any type but must be present)
    if 'value' not in rule:
        errors.append(f'{rule_label}: "value" is required.')

    return errors