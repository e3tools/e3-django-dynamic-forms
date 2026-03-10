import pytest
from django import forms

from e3_dynamic_forms.utils.json_form_parser import (
    parse_custom_jsonschema,
    build_dynamic_form_class,
    evaluate_conditions,
    ButtonField,
)


def _schema(*pages_fields):
    """Helper to build a schema dict from lists of field defs."""
    pages = []
    for i, fields in enumerate(pages_fields):
        pages.append({'title': f'Page {i+1}', 'fields': fields})
    return {'pages': pages}


class TestFieldTypes:
    def test_string_field(self):
        schema = _schema([{'name': 'q', 'type': 'string', 'label': 'Q'}])
        fields = parse_custom_jsonschema(schema)
        assert len(fields) == 1
        assert fields[0][0] == 'q'
        assert isinstance(fields[0][1], forms.CharField)

    def test_string_with_validators(self):
        schema = _schema([{'name': 'q', 'type': 'string', 'validators': {'min_length': 2, 'max_length': 10}}])
        fields = parse_custom_jsonschema(schema)
        field = fields[0][1]
        assert field.min_length == 2
        assert field.max_length == 10

    def test_number_field(self):
        schema = _schema([{'name': 'n', 'type': 'number', 'validators': {'min_value': 0, 'max_value': 100}}])
        fields = parse_custom_jsonschema(schema)
        field = fields[0][1]
        assert isinstance(field, forms.FloatField)
        assert field.min_value == 0.0
        assert field.max_value == 100.0

    def test_integer_field(self):
        schema = _schema([{'name': 'i', 'type': 'integer'}])
        fields = parse_custom_jsonschema(schema)
        assert isinstance(fields[0][1], forms.IntegerField)

    def test_boolean_field(self):
        schema = _schema([{'name': 'b', 'type': 'boolean'}])
        fields = parse_custom_jsonschema(schema)
        assert isinstance(fields[0][1], forms.BooleanField)

    def test_date_field(self):
        schema = _schema([{'name': 'd', 'type': 'date'}])
        fields = parse_custom_jsonschema(schema)
        assert isinstance(fields[0][1], forms.DateField)

    def test_file_field(self):
        schema = _schema([{'name': 'f', 'type': 'file'}])
        fields = parse_custom_jsonschema(schema)
        assert isinstance(fields[0][1], forms.FileField)

    def test_geolocation_field(self):
        schema = _schema([{'name': 'g', 'type': 'geolocation'}])
        fields = parse_custom_jsonschema(schema)
        assert isinstance(fields[0][1], ButtonField)

    def test_enum_choice_field(self):
        schema = _schema([{'name': 'c', 'type': 'string', 'enum': ['a', 'b', 'c']}])
        fields = parse_custom_jsonschema(schema)
        assert isinstance(fields[0][1], forms.ChoiceField)

    def test_multi_choice_field(self):
        schema = _schema([{'name': 'm', 'type': 'string', 'enum': ['x', 'y'], 'multi': True}])
        fields = parse_custom_jsonschema(schema)
        assert isinstance(fields[0][1], forms.MultipleChoiceField)


class TestOrdering:
    def test_fields_sorted_by_order(self):
        schema = _schema([
            {'name': 'b', 'type': 'string', 'order': 2},
            {'name': 'a', 'type': 'string', 'order': 1},
        ])
        fields = parse_custom_jsonschema(schema)
        assert fields[0][0] == 'a'
        assert fields[1][0] == 'b'


class TestRequired:
    def test_required_field(self):
        schema = _schema([{'name': 'q', 'type': 'string', 'required': True}])
        fields = parse_custom_jsonschema(schema)
        assert fields[0][1].required is True

    def test_not_required_field(self):
        schema = _schema([{'name': 'q', 'type': 'string', 'required': False}])
        fields = parse_custom_jsonschema(schema)
        assert fields[0][1].required is False


class TestLabels:
    def test_label_set(self):
        schema = _schema([{'name': 'q', 'type': 'string', 'label': 'My Question'}])
        fields = parse_custom_jsonschema(schema)
        assert fields[0][1].label == 'My Question'

    def test_label_defaults_to_name(self):
        schema = _schema([{'name': 'q', 'type': 'string'}])
        fields = parse_custom_jsonschema(schema)
        assert fields[0][1].label == 'q'


class TestConditions:
    def test_equals(self):
        assert evaluate_conditions(
            {'logic': 'AND', 'rules': [{'field': 'a', 'operator': 'equals', 'value': 'yes'}]},
            {'a': 'yes'}
        ) is True

    def test_not_equals(self):
        assert evaluate_conditions(
            {'logic': 'AND', 'rules': [{'field': 'a', 'operator': 'not_equals', 'value': 'yes'}]},
            {'a': 'no'}
        ) is True

    def test_contains(self):
        assert evaluate_conditions(
            {'logic': 'AND', 'rules': [{'field': 'a', 'operator': 'contains', 'value': 'ell'}]},
            {'a': 'hello'}
        ) is True

    def test_greater_than(self):
        assert evaluate_conditions(
            {'logic': 'AND', 'rules': [{'field': 'a', 'operator': 'greater_than', 'value': '5'}]},
            {'a': '10'}
        ) is True

    def test_less_than(self):
        assert evaluate_conditions(
            {'logic': 'AND', 'rules': [{'field': 'a', 'operator': 'less_than', 'value': '5'}]},
            {'a': '3'}
        ) is True

    def test_between(self):
        assert evaluate_conditions(
            {'logic': 'AND', 'rules': [{'field': 'a', 'operator': 'between', 'value': '1,10'}]},
            {'a': '5'}
        ) is True

    def test_between_outside(self):
        assert evaluate_conditions(
            {'logic': 'AND', 'rules': [{'field': 'a', 'operator': 'between', 'value': '1,10'}]},
            {'a': '15'}
        ) is False

    def test_and_logic(self):
        conditions = {
            'logic': 'AND',
            'rules': [
                {'field': 'a', 'operator': 'equals', 'value': 'yes'},
                {'field': 'b', 'operator': 'equals', 'value': 'no'},
            ]
        }
        assert evaluate_conditions(conditions, {'a': 'yes', 'b': 'no'}) is True
        assert evaluate_conditions(conditions, {'a': 'yes', 'b': 'yes'}) is False

    def test_or_logic(self):
        conditions = {
            'logic': 'OR',
            'rules': [
                {'field': 'a', 'operator': 'equals', 'value': 'yes'},
                {'field': 'b', 'operator': 'equals', 'value': 'yes'},
            ]
        }
        assert evaluate_conditions(conditions, {'a': 'yes', 'b': 'no'}) is True
        assert evaluate_conditions(conditions, {'a': 'no', 'b': 'no'}) is False

    def test_no_conditions_returns_true(self):
        assert evaluate_conditions(None, {}) is True
        assert evaluate_conditions({}, {}) is True

    def test_conditional_field_hidden(self):
        schema = _schema([
            {'name': 'trigger', 'type': 'string', 'order': 0},
            {'name': 'hidden', 'type': 'string', 'order': 1,
             'conditions': {'logic': 'AND', 'rules': [{'field': 'trigger', 'operator': 'equals', 'value': 'show'}]}},
        ])
        fields = parse_custom_jsonschema(schema, response_data={'trigger': 'hide'})
        assert len(fields) == 1
        assert fields[0][0] == 'trigger'

    def test_conditional_field_shown(self):
        schema = _schema([
            {'name': 'trigger', 'type': 'string', 'order': 0},
            {'name': 'shown', 'type': 'string', 'order': 1,
             'conditions': {'logic': 'AND', 'rules': [{'field': 'trigger', 'operator': 'equals', 'value': 'show'}]}},
        ])
        fields = parse_custom_jsonschema(schema, response_data={'trigger': 'show'})
        assert len(fields) == 2


class TestMultiPage:
    def test_page_0(self):
        schema = _schema(
            [{'name': 'q1', 'type': 'string'}],
            [{'name': 'q2', 'type': 'integer'}],
        )
        fields = parse_custom_jsonschema(schema, page_index=0)
        assert len(fields) == 1
        assert fields[0][0] == 'q1'

    def test_page_1(self):
        schema = _schema(
            [{'name': 'q1', 'type': 'string'}],
            [{'name': 'q2', 'type': 'integer'}],
        )
        fields = parse_custom_jsonschema(schema, page_index=1)
        assert len(fields) == 1
        assert fields[0][0] == 'q2'

    def test_invalid_page_index(self):
        schema = _schema([{'name': 'q1', 'type': 'string'}])
        assert parse_custom_jsonschema(schema, page_index=5) == []

    def test_empty_schema(self):
        assert parse_custom_jsonschema({}) == []


class TestBuildDynamicFormClass:
    def test_returns_form_class(self):
        schema = _schema([
            {'name': 'name', 'type': 'string', 'required': True},
            {'name': 'age', 'type': 'integer'},
        ])
        FormClass = build_dynamic_form_class(schema)
        assert issubclass(FormClass, forms.Form)
        form = FormClass(data={'name': 'Alice', 'age': '30'})
        assert form.is_valid()
        assert form.cleaned_data['name'] == 'Alice'
        assert form.cleaned_data['age'] == 30

    def test_validation_works(self):
        schema = _schema([
            {'name': 'n', 'type': 'integer', 'required': True, 'validators': {'min_value': 1, 'max_value': 10}},
        ])
        FormClass = build_dynamic_form_class(schema)
        form = FormClass(data={'n': '100'})
        assert not form.is_valid()
