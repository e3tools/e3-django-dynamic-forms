import pytest
from django.contrib.auth import get_user_model

from e3_dynamic_forms.models import FormSchema, FormResponse, Attachment

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
