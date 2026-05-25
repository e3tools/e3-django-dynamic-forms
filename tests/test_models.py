import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings

from e3_dynamic_forms.conf import get_form_schema_model
from e3_dynamic_forms.models import AbstractFormSchema, FormSchema, FormResponse, Attachment

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username='testuser', password='testpass')


@pytest.fixture
def schema(db, user):
    return FormSchema.objects.create(
        name='Test Schema',
        description='A test schema',
        schema={'pages': [{'title': 'Page 1', 'fields': [{'name': 'q1', 'type': 'string'}]}]},
        created_by=user,
    )


@pytest.fixture
def two_page_schema(db, user):
    return FormSchema.objects.create(
        name='Two Page Schema',
        schema={
            'pages': [
                {'title': 'Page 1', 'fields': [{'name': 'q1', 'type': 'string'}]},
                {'title': 'Page 2', 'fields': [{'name': 'q2', 'type': 'integer'}]},
            ]
        },
        created_by=user,
    )


@pytest.fixture
def response(db, schema, user):
    return FormResponse.objects.create(
        schema=schema,
        data={'q1': 'answer'},
        created_by=user,
    )


class TestFormSchema:
    def test_str(self, schema):
        assert str(schema) == 'Test Schema (v1)'

    def test_page_count_single(self, schema):
        assert schema.page_count == 1

    def test_page_count_multi(self, two_page_schema):
        assert two_page_schema.page_count == 2

    def test_page_count_empty(self, db, user):
        s = FormSchema.objects.create(name='Empty', schema={}, created_by=user)
        assert s.page_count == 1

    def test_default_version(self, schema):
        assert schema.version == 1

    def test_is_active_default(self, schema):
        assert schema.is_active is True


class TestFormResponse:
    def test_str(self, response):
        assert 'Response to Test Schema' in str(response)

    def test_fk_relation(self, response, schema):
        assert response.schema == schema
        assert schema.responses.count() == 1


class TestAttachment:
    def test_str(self, response):
        att = Attachment(response=response, field_name='my_file')
        att.file.name = 'test.pdf'
        assert 'my_file' in str(att)


class TestSwappableFormSchema:
    def test_abstract_form_schema_is_abstract(self):
        assert AbstractFormSchema._meta.abstract is True

    def test_form_schema_swappable_meta(self):
        assert FormSchema._meta.swappable == 'DYNAMIC_FORMS_SCHEMA_MODEL'

    def test_form_schema_not_swapped_by_default(self):
        assert FormSchema._meta.swapped is None

    def test_get_form_schema_model_returns_default(self):
        assert get_form_schema_model() is FormSchema

    @override_settings(DYNAMIC_FORMS_SCHEMA_MODEL='test_app.CustomFormSchema')
    def test_get_form_schema_model_returns_custom(self):
        from tests.test_app.models import CustomFormSchema
        assert get_form_schema_model() is CustomFormSchema

    def test_custom_schema_inherits_str(self, db, user):
        from tests.test_app.models import CustomFormSchema
        s = CustomFormSchema.objects.create(
            name='Custom', schema={'pages': [{'title': 'P1', 'fields': []}]},
            department='Engineering', created_by=user,
        )
        assert str(s) == 'Custom (v1)'

    def test_custom_schema_inherits_page_count(self, db, user):
        from tests.test_app.models import CustomFormSchema
        s = CustomFormSchema.objects.create(
            name='Custom',
            schema={
                'pages': [
                    {'title': 'P1', 'fields': []},
                    {'title': 'P2', 'fields': []},
                ]
            },
            department='Engineering', created_by=user,
        )
        assert s.page_count == 2

    def test_custom_schema_has_extra_field(self, db, user):
        from tests.test_app.models import CustomFormSchema
        s = CustomFormSchema.objects.create(
            name='Custom', schema={}, department='Finance', created_by=user,
        )
        assert s.department == 'Finance'

    def test_custom_schema_has_timestamps(self, db, user):
        from tests.test_app.models import CustomFormSchema
        s = CustomFormSchema.objects.create(
            name='Custom', schema={}, created_by=user,
        )
        assert s.created_date is not None
        assert s.updated_date is not None
