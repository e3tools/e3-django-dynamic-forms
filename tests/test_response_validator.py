import pytest

from e3_dynamic_forms.utils.response_validator import validate_response_data


def _field(name, field_type='string', required=False, **kwargs):
    """Helper to build a valid field definition."""
    base = {'name': name, 'type': field_type, 'label': name.title(), 'required': required, 'order': 0}
    base.update(kwargs)
    return base


def _schema(*fields):
    """Wrap fields in a single-page schema."""
    return {'pages': [{'title': 'Page 1', 'fields': list(fields)}]}


# ── Basic validation ───────────────────────────────────────────────────────


class TestBasicValidation:
    def test_valid_response(self):
        schema = _schema(_field('name', required=True))
        assert validate_response_data({'name': 'Alice'}, schema) == []

    def test_data_must_be_dict(self):
        schema = _schema(_field('q1'))
        errors = validate_response_data('not a dict', schema)
        assert any('JSON object' in e for e in errors)

    def test_invalid_schema_returns_error(self):
        errors = validate_response_data({'q1': 'val'}, 'bad')
        assert any('schema is invalid' in e for e in errors)

    def test_empty_data_for_no_fields(self):
        schema = {'pages': [{'title': 'P1', 'fields': []}]}
        assert validate_response_data({}, schema) == []

    def test_non_empty_data_for_no_fields(self):
        schema = {'pages': [{'title': 'P1', 'fields': []}]}
        errors = validate_response_data({'extra': 'val'}, schema)
        assert any('no fields' in e for e in errors)


# ── Unknown keys ───────────────────────────────────────────────────────────


class TestUnknownKeys:
    def test_extra_keys_rejected(self):
        schema = _schema(_field('q1'))
        errors = validate_response_data({'q1': 'val', 'unknown': 'x'}, schema)
        assert any('Unknown fields' in e for e in errors)

    def test_known_keys_accepted(self):
        schema = _schema(_field('q1'), _field('q2'))
        assert validate_response_data({'q1': 'a', 'q2': 'b'}, schema) == []


# ── Required fields ────────────────────────────────────────────────────────


class TestRequiredFields:
    def test_missing_required_field(self):
        schema = _schema(_field('q1', required=True))
        errors = validate_response_data({}, schema)
        assert any('q1' in e and 'missing' in e for e in errors)

    def test_empty_string_required_field(self):
        schema = _schema(_field('q1', required=True))
        errors = validate_response_data({'q1': ''}, schema)
        assert any('q1' in e and 'missing' in e for e in errors)

    def test_none_required_field(self):
        schema = _schema(_field('q1', required=True))
        errors = validate_response_data({'q1': None}, schema)
        assert any('q1' in e and 'missing' in e for e in errors)

    def test_optional_field_can_be_absent(self):
        schema = _schema(_field('q1', required=False))
        assert validate_response_data({}, schema) == []

    def test_conditional_required_field_can_be_absent(self):
        """Required fields with conditions are allowed to be missing."""
        f = _field('q1', required=True, conditions={
            'logic': 'AND',
            'rules': [{'field': 'other', 'operator': 'equals', 'value': 'yes'}],
        })
        schema = _schema(f)
        assert validate_response_data({}, schema) == []

    def test_file_required_field_skipped(self):
        """File fields are stored as Attachments, not in data."""
        schema = _schema(_field('upload', field_type='file', required=True))
        assert validate_response_data({}, schema) == []


# ── String validation ──────────────────────────────────────────────────────


class TestStringValidation:
    def test_valid_string(self):
        schema = _schema(_field('q1'))
        assert validate_response_data({'q1': 'hello'}, schema) == []

    def test_wrong_type(self):
        schema = _schema(_field('q1'))
        errors = validate_response_data({'q1': 123}, schema)
        assert any('expected a string' in e for e in errors)

    def test_min_length(self):
        f = _field('q1', required=True, validators={'min_length': '3'})
        errors = validate_response_data({'q1': 'ab'}, _schema(f))
        assert any('shorter than minimum' in e for e in errors)

    def test_max_length(self):
        f = _field('q1', required=True, validators={'max_length': '5'})
        errors = validate_response_data({'q1': 'toolong'}, _schema(f))
        assert any('exceeds maximum' in e for e in errors)

    def test_within_length_bounds(self):
        f = _field('q1', validators={'min_length': '2', 'max_length': '10'})
        assert validate_response_data({'q1': 'hello'}, _schema(f)) == []


# ── Enum validation ────────────────────────────────────────────────────────


class TestEnumValidation:
    def test_valid_enum_value(self):
        f = _field('color', enum=['red', 'blue', 'green'])
        assert validate_response_data({'color': 'red'}, _schema(f)) == []

    def test_invalid_enum_value(self):
        f = _field('color', enum=['red', 'blue'])
        errors = validate_response_data({'color': 'yellow'}, _schema(f))
        assert any('not one of the allowed' in e for e in errors)

    def test_empty_enum_value_optional(self):
        f = _field('color', enum=['red', 'blue'])
        assert validate_response_data({'color': ''}, _schema(f)) == []

    def test_multi_select_valid(self):
        f = _field('colors', enum=['red', 'blue', 'green'], multi=True)
        assert validate_response_data({'colors': ['red', 'blue']}, _schema(f)) == []

    def test_multi_select_invalid_option(self):
        f = _field('colors', enum=['red', 'blue'], multi=True)
        errors = validate_response_data({'colors': ['red', 'yellow']}, _schema(f))
        assert any('invalid options' in e for e in errors)

    def test_multi_select_wrong_type(self):
        f = _field('colors', enum=['red', 'blue'], multi=True)
        errors = validate_response_data({'colors': 'red'}, _schema(f))
        assert any('expected a list' in e for e in errors)


# ── Number validation ──────────────────────────────────────────────────────


class TestNumberValidation:
    def test_valid_number(self):
        schema = _schema(_field('score', field_type='number'))
        assert validate_response_data({'score': 3.14}, schema) == []

    def test_string_numeric_coercion(self):
        schema = _schema(_field('score', field_type='number'))
        assert validate_response_data({'score': '3.14'}, schema) == []

    def test_non_numeric_string(self):
        schema = _schema(_field('score', field_type='number'))
        errors = validate_response_data({'score': 'abc'}, schema)
        assert any('non-numeric' in e for e in errors)

    def test_boolean_rejected(self):
        schema = _schema(_field('score', field_type='number'))
        errors = validate_response_data({'score': True}, schema)
        assert any('boolean' in e for e in errors)

    def test_min_value(self):
        f = _field('score', field_type='number', required=True, validators={'min_value': '0'})
        errors = validate_response_data({'score': -1}, _schema(f))
        assert any('less than minimum' in e for e in errors)

    def test_max_value(self):
        f = _field('score', field_type='number', required=True, validators={'max_value': '100'})
        errors = validate_response_data({'score': 101}, _schema(f))
        assert any('greater than maximum' in e for e in errors)


# ── Integer validation ─────────────────────────────────────────────────────


class TestIntegerValidation:
    def test_valid_integer(self):
        schema = _schema(_field('age', field_type='integer'))
        assert validate_response_data({'age': 25}, schema) == []

    def test_string_integer_coercion(self):
        schema = _schema(_field('age', field_type='integer'))
        assert validate_response_data({'age': '25'}, schema) == []

    def test_float_rejected_for_integer(self):
        schema = _schema(_field('age', field_type='integer'))
        errors = validate_response_data({'age': 3.5}, schema)
        assert any('expected an integer' in e for e in errors)

    def test_integer_min_max(self):
        f = _field('age', field_type='integer', required=True, validators={'min_value': '0', 'max_value': '150'})
        assert validate_response_data({'age': 25}, _schema(f)) == []

        errors = validate_response_data({'age': -1}, _schema(f))
        assert any('less than minimum' in e for e in errors)


# ── Boolean validation ─────────────────────────────────────────────────────


class TestBooleanValidation:
    def test_valid_boolean(self):
        schema = _schema(_field('agree', field_type='boolean'))
        assert validate_response_data({'agree': True}, schema) == []
        assert validate_response_data({'agree': False}, schema) == []

    def test_non_boolean_rejected(self):
        schema = _schema(_field('agree', field_type='boolean'))
        errors = validate_response_data({'agree': 'yes'}, schema)
        assert any('expected a boolean' in e for e in errors)


# ── Date validation ────────────────────────────────────────────────────────


class TestDateValidation:
    def test_valid_date(self):
        schema = _schema(_field('dob', field_type='date'))
        assert validate_response_data({'dob': '2000-01-15'}, schema) == []

    def test_invalid_date_format(self):
        schema = _schema(_field('dob', field_type='date'))
        errors = validate_response_data({'dob': 'January 15'}, schema)
        assert any('not a valid date' in e for e in errors)

    def test_non_string_date(self):
        schema = _schema(_field('dob', field_type='date'))
        errors = validate_response_data({'dob': 20000115}, schema)
        assert any('expected a date string' in e for e in errors)

    def test_date_before_min(self):
        f = _field('dob', field_type='date', required=True, validators={'min_value': '2020-01-01'})
        errors = validate_response_data({'dob': '2019-12-31'}, _schema(f))
        assert any('before minimum' in e for e in errors)

    def test_date_after_max(self):
        f = _field('dob', field_type='date', required=True, validators={'max_value': '2025-12-31'})
        errors = validate_response_data({'dob': '2026-01-01'}, _schema(f))
        assert any('after maximum' in e for e in errors)

    def test_date_within_range(self):
        f = _field('dob', field_type='date', validators={
            'min_value': '2020-01-01', 'max_value': '2025-12-31',
        })
        assert validate_response_data({'dob': '2023-06-15'}, _schema(f)) == []


# ── Multi-page schemas ─────────────────────────────────────────────────────


class TestMultiPage:
    def test_fields_across_pages_validated(self):
        schema = {
            'pages': [
                {'title': 'P1', 'fields': [_field('q1', required=True)]},
                {'title': 'P2', 'fields': [_field('q2', required=True)]},
            ]
        }
        errors = validate_response_data({'q1': 'a'}, schema)
        assert any('q2' in e and 'missing' in e for e in errors)

    def test_all_pages_valid(self):
        schema = {
            'pages': [
                {'title': 'P1', 'fields': [_field('q1', required=True)]},
                {'title': 'P2', 'fields': [_field('q2', required=True)]},
            ]
        }
        assert validate_response_data({'q1': 'a', 'q2': 'b'}, schema) == []


# ── Geolocation fields ────────────────────────────────────────────────────


class TestGeolocationField:
    def test_geolocation_accepts_string(self):
        schema = _schema(_field('loc', field_type='geolocation'))
        assert validate_response_data({'loc': '12.345,-67.890'}, schema) == []

    def test_geolocation_optional_can_be_absent(self):
        schema = _schema(_field('loc', field_type='geolocation'))
        assert validate_response_data({}, schema) == []


# ── Full integration-style test ────────────────────────────────────────────


class TestFullSchema:
    def test_realistic_response(self):
        schema = {
            'pages': [
                {
                    'title': 'Personal Info',
                    'fields': [
                        _field('full_name', required=True, validators={'min_length': '2', 'max_length': '100'}),
                        _field('age', field_type='integer', required=True, validators={'min_value': '0', 'max_value': '150'}),
                        _field('country', required=True, enum=['USA', 'Canada', 'Mexico']),
                    ],
                },
                {
                    'title': 'Survey',
                    'fields': [
                        _field('satisfaction', enum=['Low', 'Medium', 'High'], conditions={
                            'logic': 'AND',
                            'rules': [{'field': 'age', 'operator': 'greater_than', 'value': '18'}],
                        }),
                        _field('birth_date', field_type='date'),
                        _field('photo', field_type='file'),
                        _field('location', field_type='geolocation'),
                    ],
                },
            ],
        }
        data = {
            'full_name': 'Alice Smith',
            'age': 30,
            'country': 'Canada',
            'satisfaction': 'High',
            'birth_date': '1994-05-20',
            'location': '45.421,-75.697',
        }
        assert validate_response_data(data, schema) == []

    def test_realistic_response_with_errors(self):
        schema = {
            'pages': [
                {
                    'title': 'Personal Info',
                    'fields': [
                        _field('full_name', required=True, validators={'min_length': '2'}),
                        _field('age', field_type='integer', required=True, validators={'min_value': '0'}),
                    ],
                },
            ],
        }
        data = {
            'full_name': 'A',       # too short
            'age': -5,              # below min
            'unknown_field': 'x',   # not in schema
        }
        errors = validate_response_data(data, schema)
        assert any('shorter than minimum' in e for e in errors)
        assert any('less than minimum' in e for e in errors)
        assert any('Unknown fields' in e for e in errors)
