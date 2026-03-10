import json
import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from e3_dynamic_forms.models import FormSchema, FormResponse

User = get_user_model()


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(username='staff', password='pass', is_staff=True)


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(username='regular', password='pass')


@pytest.fixture
def schema(db, staff_user):
    return FormSchema.objects.create(
        name='Survey',
        schema={
            'pages': [
                {
                    'title': 'Page 1',
                    'fields': [
                        {'name': 'q1', 'type': 'string', 'label': 'Question 1', 'required': True, 'order': 0},
                    ]
                }
            ]
        },
        created_by=staff_user,
    )


@pytest.fixture
def staff_client(staff_user):
    c = Client()
    c.login(username='staff', password='pass')
    return c


@pytest.fixture
def regular_client(regular_user):
    c = Client()
    c.login(username='regular', password='pass')
    return c


class TestSchemaViews:
    def test_list_requires_staff(self, db, regular_client):
        resp = regular_client.get('/dynamic-forms/schemas/')
        assert resp.status_code in (302, 403)

    def test_list_accessible_by_staff(self, schema, staff_client):
        resp = staff_client.get('/dynamic-forms/schemas/')
        assert resp.status_code == 200

    def test_create_schema(self, db, staff_client):
        schema_json = json.dumps({
            'pages': [{'title': 'P1', 'fields': [{'name': 'q1', 'type': 'string'}]}]
        })
        resp = staff_client.post('/dynamic-forms/schemas/create/', {
            'name': 'New Schema',
            'description': 'Test',
            'schema': schema_json,
            'is_active': True,
        })
        assert resp.status_code in (200, 302)
        assert FormSchema.objects.filter(name='New Schema').exists()

    def test_detail_view(self, schema, staff_client):
        resp = staff_client.get(f'/dynamic-forms/schemas/{schema.pk}/')
        assert resp.status_code == 200

    def test_edit_increments_version(self, schema, staff_client):
        schema_json = json.dumps(schema.schema)
        resp = staff_client.post(f'/dynamic-forms/schemas/{schema.pk}/edit/', {
            'name': schema.name,
            'description': '',
            'schema': schema_json,
            'is_active': True,
        })
        assert resp.status_code in (200, 302)
        schema.refresh_from_db()
        assert schema.version == 2

    def test_delete_view(self, schema, staff_client):
        resp = staff_client.post(f'/dynamic-forms/schemas/{schema.pk}/delete/')
        assert resp.status_code in (200, 302)
        assert not FormSchema.objects.filter(pk=schema.pk).exists()


class TestResponseViews:
    def test_create_response(self, schema, regular_client):
        resp = regular_client.post(f'/dynamic-forms/schemas/{schema.pk}/respond/', {
            'q1': 'My answer',
        })
        assert resp.status_code in (200, 302)
        assert FormResponse.objects.filter(schema=schema).exists()

    def test_response_list_requires_staff(self, schema, regular_client):
        resp = regular_client.get(f'/dynamic-forms/schemas/{schema.pk}/responses/')
        assert resp.status_code in (302, 403)

    def test_response_list_accessible_by_staff(self, schema, staff_client):
        resp = staff_client.get(f'/dynamic-forms/schemas/{schema.pk}/responses/')
        assert resp.status_code == 200
