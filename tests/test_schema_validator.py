import pytest

from e3_dynamic_forms.utils.schema_validator import validate_schema


def _make_field(**overrides):
    """Helper to build a valid field definition with overrides."""
    base = {
        'name': 'test_field',
        'type': 'string',
        'label': 'Test Field',
        'required': False,
        'order': 0,
    }
    base.update(overrides)
    return base


def _make_schema(fields=None, pages=None):
    """Helper to build a valid schema."""
    if pages is not None:
        return {'pages': pages}
    if fields is None:
        fields = [_make_field()]
    return {'pages': [{'title': 'Page 1', 'fields': fields}]}


# ── Root-level validation ──────────────────────────────────────────────────


class TestRootValidation:
    def test_valid_minimal_schema(self):
        assert validate_schema(_make_schema()) == []

    def test_not_a_dict(self):
        assert validate_schema([]) != []
        assert validate_schema('string') != []

    def test_missing_pages(self):
        errors = validate_schema({})
        assert any('pages' in e for e in errors)

    def test_pages_not_a_list(self):
        errors = validate_schema({'pages': 'not a list'})
        assert len(errors) > 0

    def test_empty_pages(self):
        errors = validate_schema({'pages': []})
        assert any('at least one page' in e for e in errors)

    def test_extra_root_keys(self):
        schema = _make_schema()
        schema['unknown_key'] = 'value'
        errors = validate_schema(schema)
        assert any('Unknown root-level keys' in e for e in errors)


# ── Page validation ────────────────────────────────────────────────────────


class TestPageValidation:
    def test_page_not_a_dict(self):
        errors = validate_schema({'pages': ['not a dict']})
        assert len(errors) > 0

    def test_page_missing_title(self):
        errors = validate_schema({'pages': [{'fields': []}]})
        assert any('title' in e for e in errors)

    def test_page_empty_title(self):
        errors = validate_schema({'pages': [{'title': '', 'fields': []}]})
        assert any('title' in e for e in errors)

    def test_page_missing_fields(self):
        errors = validate_schema({'pages': [{'title': 'P1'}]})
        assert any('fields' in e for e in errors)

    def test_page_fields_not_a_list(self):
        errors = validate_schema({'pages': [{'title': 'P1', 'fields': 'bad'}]})
        assert len(errors) > 0

    def test_page_extra_keys(self):
        errors = validate_schema({'pages': [{'title': 'P1', 'fields': [], 'extra': 1}]})
        assert any('unknown keys' in e for e in errors)

    def test_valid_empty_fields_page(self):
        assert validate_schema({'pages': [{'title': 'P1', 'fields': []}]}) == []


# ── Field validation ───────────────────────────────────────────────────────


class TestFieldValidation:
    def test_valid_field(self):
        assert validate_schema(_make_schema()) == []

    def test_field_not_a_dict(self):
        errors = validate_schema(_make_schema(fields=['not a dict']))
        assert len(errors) > 0

    def test_missing_name(self):
        errors = validate_schema(_make_schema(fields=[_make_field(name='')]))
        assert any('name' in e for e in errors)

    def test_invalid_name_format(self):
        errors = validate_schema(_make_schema(fields=[_make_field(name='CamelCase')]))
        assert any('name' in e and 'lowercase' in e for e in errors)

    def test_name_starting_with_digit(self):
        errors = validate_schema(_make_schema(fields=[_make_field(name='1field')]))
        assert any('name' in e for e in errors)

    def test_valid_name_with_underscores(self):
        assert validate_schema(_make_schema(fields=[_make_field(name='my_field_2')])) == []

    def test_duplicate_field_names(self):
        fields = [_make_field(name='dup', label='A'), _make_field(name='dup', label='B')]
        errors = validate_schema(_make_schema(fields=fields))
        assert any('duplicate' in e for e in errors)

    def test_duplicate_across_pages(self):
        pages = [
            {'title': 'P1', 'fields': [_make_field(name='shared')]},
            {'title': 'P2', 'fields': [_make_field(name='shared')]},
        ]
        errors = validate_schema(_make_schema(pages=pages))
        assert any('duplicate' in e for e in errors)

    def test_missing_type(self):
        f = _make_field()
        del f['type']
        errors = validate_schema(_make_schema(fields=[f]))
        assert any('type' in e for e in errors)

    def test_invalid_type(self):
        errors = validate_schema(_make_schema(fields=[_make_field(type='textarea')]))
        assert any('invalid type' in e for e in errors)

    def test_all_valid_types(self):
        for t in ('string', 'number', 'integer', 'boolean', 'date', 'file', 'geolocation'):
            assert validate_schema(_make_schema(fields=[_make_field(type=t)])) == []

    def test_missing_label(self):
        f = _make_field()
        del f['label']
        errors = validate_schema(_make_schema(fields=[f]))
        assert any('label' in e for e in errors)

    def test_required_must_be_bool(self):
        errors = validate_schema(_make_schema(fields=[_make_field(required='yes')]))
        assert any('required' in e and 'boolean' in e for e in errors)

    def test_help_text_must_be_string(self):
        errors = validate_schema(_make_schema(fields=[_make_field(help_text=123)]))
        assert any('help_text' in e for e in errors)

    def test_order_must_be_int(self):
        errors = validate_schema(_make_schema(fields=[_make_field(order='first')]))
        assert any('order' in e for e in errors)

    def test_extra_field_keys(self):
        errors = validate_schema(_make_schema(fields=[_make_field(unknown_prop=True)]))
        assert any('unknown keys' in e for e in errors)


# ── Validators validation ──────────────────────────────────────────────────


class TestFieldValidators:
    def test_string_validators(self):
        f = _make_field(type='string', validators={'min_length': '2', 'max_length': '100'})
        assert validate_schema(_make_schema(fields=[f])) == []

    def test_number_validators(self):
        f = _make_field(type='number', validators={'min_value': '0', 'max_value': '100'})
        assert validate_schema(_make_schema(fields=[f])) == []

    def test_integer_validators(self):
        f = _make_field(type='integer', validators={'min_value': 0, 'max_value': 100})
        assert validate_schema(_make_schema(fields=[f])) == []

    def test_date_validators_with_today(self):
        f = _make_field(type='date', validators={'min_value': 'today'})
        assert validate_schema(_make_schema(fields=[f])) == []

    def test_date_validators_with_date_string(self):
        f = _make_field(type='date', validators={'min_value': '2025-01-01', 'max_value': '2025-12-31'})
        assert validate_schema(_make_schema(fields=[f])) == []

    def test_wrong_validators_for_type(self):
        f = _make_field(type='string', validators={'min_value': '0'})
        errors = validate_schema(_make_schema(fields=[f]))
        assert any('invalid validator keys' in e for e in errors)

    def test_boolean_no_validators_allowed(self):
        f = _make_field(type='boolean', validators={'min_length': '1'})
        errors = validate_schema(_make_schema(fields=[f]))
        assert any('invalid validator keys' in e for e in errors)

    def test_validators_must_be_dict(self):
        f = _make_field(validators='bad')
        errors = validate_schema(_make_schema(fields=[f]))
        assert any('validators' in e and 'object' in e for e in errors)

    def test_non_numeric_validator_value(self):
        f = _make_field(type='string', validators={'min_length': 'abc'})
        errors = validate_schema(_make_schema(fields=[f]))
        assert any('not numeric' in e for e in errors)


# ── Enum/multi validation ─────────────────────────────────────────────────


class TestEnumValidation:
    def test_valid_enum(self):
        f = _make_field(type='string', enum=['Option A', 'Option B'])
        assert validate_schema(_make_schema(fields=[f])) == []

    def test_enum_with_multi(self):
        f = _make_field(type='string', enum=['A', 'B'], multi=True)
        assert validate_schema(_make_schema(fields=[f])) == []

    def test_enum_not_allowed_on_non_string(self):
        f = _make_field(type='number', enum=['1', '2'])
        errors = validate_schema(_make_schema(fields=[f]))
        assert any('only valid for type "string"' in e for e in errors)

    def test_enum_must_be_list(self):
        f = _make_field(type='string', enum='not a list')
        errors = validate_schema(_make_schema(fields=[f]))
        assert any('enum' in e and 'list' in e for e in errors)

    def test_enum_empty(self):
        f = _make_field(type='string', enum=[])
        errors = validate_schema(_make_schema(fields=[f]))
        assert any('must not be empty' in e for e in errors)

    def test_enum_non_string_option(self):
        f = _make_field(type='string', enum=['valid', 123])
        errors = validate_schema(_make_schema(fields=[f]))
        assert any('enum option' in e for e in errors)

    def test_multi_without_enum(self):
        f = _make_field(multi=True)
        errors = validate_schema(_make_schema(fields=[f]))
        assert any('multi' in e and 'enum' in e for e in errors)

    def test_multi_must_be_bool(self):
        f = _make_field(type='string', enum=['A'], multi='yes')
        errors = validate_schema(_make_schema(fields=[f]))
        assert any('multi' in e and 'boolean' in e for e in errors)


# ── Conditions validation ──────────────────────────────────────────────────


class TestConditionsValidation:
    def test_valid_conditions(self):
        f = _make_field(conditions={
            'logic': 'AND',
            'rules': [{'field': 'other', 'operator': 'equals', 'value': 'yes'}],
        })
        assert validate_schema(_make_schema(fields=[f])) == []

    def test_conditions_or_logic(self):
        f = _make_field(conditions={
            'logic': 'OR',
            'rules': [{'field': 'other', 'operator': 'not_equals', 'value': 'no'}],
        })
        assert validate_schema(_make_schema(fields=[f])) == []

    def test_conditions_not_a_dict(self):
        f = _make_field(conditions='bad')
        errors = validate_schema(_make_schema(fields=[f]))
        assert any('conditions' in e and 'object' in e for e in errors)

    def test_conditions_missing_logic(self):
        f = _make_field(conditions={'rules': [{'field': 'x', 'operator': 'equals', 'value': '1'}]})
        errors = validate_schema(_make_schema(fields=[f]))
        assert any('logic' in e for e in errors)

    def test_conditions_invalid_logic(self):
        f = _make_field(conditions={
            'logic': 'XOR',
            'rules': [{'field': 'x', 'operator': 'equals', 'value': '1'}],
        })
        errors = validate_schema(_make_schema(fields=[f]))
        assert any('logic' in e for e in errors)

    def test_conditions_missing_rules(self):
        f = _make_field(conditions={'logic': 'AND'})
        errors = validate_schema(_make_schema(fields=[f]))
        assert any('rules' in e for e in errors)

    def test_conditions_empty_rules(self):
        f = _make_field(conditions={'logic': 'AND', 'rules': []})
        errors = validate_schema(_make_schema(fields=[f]))
        assert any('must not be empty' in e for e in errors)

    def test_conditions_extra_keys(self):
        f = _make_field(conditions={'logic': 'AND', 'rules': [], 'extra': 1})
        errors = validate_schema(_make_schema(fields=[f]))
        assert any('unknown keys' in e for e in errors)

    def test_rule_missing_field(self):
        f = _make_field(conditions={
            'logic': 'AND',
            'rules': [{'operator': 'equals', 'value': '1'}],
        })
        errors = validate_schema(_make_schema(fields=[f]))
        assert any('"field"' in e for e in errors)

    def test_rule_missing_operator(self):
        f = _make_field(conditions={
            'logic': 'AND',
            'rules': [{'field': 'x', 'value': '1'}],
        })
        errors = validate_schema(_make_schema(fields=[f]))
        assert any('operator' in e for e in errors)

    def test_rule_invalid_operator(self):
        f = _make_field(conditions={
            'logic': 'AND',
            'rules': [{'field': 'x', 'operator': 'starts_with', 'value': '1'}],
        })
        errors = validate_schema(_make_schema(fields=[f]))
        assert any('invalid operator' in e for e in errors)

    def test_rule_missing_value(self):
        f = _make_field(conditions={
            'logic': 'AND',
            'rules': [{'field': 'x', 'operator': 'equals'}],
        })
        errors = validate_schema(_make_schema(fields=[f]))
        assert any('"value"' in e for e in errors)

    def test_all_valid_operators(self):
        for op in ('equals', 'not_equals', 'contains', 'greater_than', 'less_than', 'between'):
            f = _make_field(conditions={
                'logic': 'AND',
                'rules': [{'field': 'other', 'operator': op, 'value': '1'}],
            })
            assert validate_schema(_make_schema(fields=[f])) == [], f'Failed for operator: {op}'

    def test_rule_extra_keys(self):
        f = _make_field(conditions={
            'logic': 'AND',
            'rules': [{'field': 'x', 'operator': 'equals', 'value': '1', 'extra': True}],
        })
        errors = validate_schema(_make_schema(fields=[f]))
        assert any('unknown keys' in e for e in errors)


# ── Multi-page complex schema ─────────────────────────────────────────────


class TestComplexSchema:
    def test_full_valid_schema(self):
        schema = {
            'pages': [
                {
                    'title': 'Personal Info',
                    'fields': [
                        {
                            'name': 'full_name',
                            'type': 'string',
                            'label': 'Full Name',
                            'required': True,
                            'order': 0,
                            'validators': {'min_length': '2', 'max_length': '100'},
                        },
                        {
                            'name': 'age',
                            'type': 'integer',
                            'label': 'Age',
                            'required': True,
                            'order': 1,
                            'validators': {'min_value': '0', 'max_value': '150'},
                        },
                        {
                            'name': 'country',
                            'type': 'string',
                            'label': 'Country',
                            'required': True,
                            'order': 2,
                            'enum': ['USA', 'Canada', 'Mexico'],
                        },
                    ],
                },
                {
                    'title': 'Survey',
                    'fields': [
                        {
                            'name': 'satisfaction',
                            'type': 'string',
                            'label': 'Satisfaction',
                            'required': False,
                            'order': 0,
                            'enum': ['Low', 'Medium', 'High'],
                            'conditions': {
                                'logic': 'AND',
                                'rules': [
                                    {'field': 'age', 'operator': 'greater_than', 'value': '18'},
                                ],
                            },
                        },
                        {
                            'name': 'photo',
                            'type': 'file',
                            'label': 'Upload Photo',
                            'required': False,
                            'order': 1,
                        },
                        {
                            'name': 'location',
                            'type': 'geolocation',
                            'label': 'Your Location',
                            'required': False,
                            'order': 2,
                        },
                    ],
                },
            ],
        }
        assert validate_schema(schema) == []