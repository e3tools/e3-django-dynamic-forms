import json
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

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
        name='API Schema',
        schema={'pages': [{'title': 'P1', 'fields': [{'name': 'q1', 'type': 'string'}]}]},
        created_by=staff_user,
    )


@pytest.fixture
def staff_api(staff_user):
    c = APIClient()
    c.force_authenticate(user=staff_user)
    return c


@pytest.fixture
def regular_api(regular_user):
    c = APIClient()
    c.force_authenticate(user=regular_user)
    return c


class TestFormSchemaAPI:
    def test_list_requires_staff(self, db, regular_api):
        resp = regular_api.get('/dynamic-forms/api/form-schemas/')
        assert resp.status_code == 403

    def test_list_as_staff(self, schema, staff_api):
        resp = staff_api.get('/dynamic-forms/api/form-schemas/')
        assert resp.status_code == 200
        assert len(resp.data) >= 1

    def test_create(self, db, staff_api):
        resp = staff_api.post('/dynamic-forms/api/form-schemas/', {
            'name': 'API Created',
            'schema': {'pages': [{'title': 'P1', 'fields': []}]},
        }, format='json')
        assert resp.status_code == 201
        assert FormSchema.objects.filter(name='API Created').exists()

    def test_retrieve(self, schema, staff_api):
        resp = staff_api.get(f'/dynamic-forms/api/form-schemas/{schema.pk}/')
        assert resp.status_code == 200
        assert resp.data['name'] == 'API Schema'


class TestFormResponseAPI:
    def test_create_as_authenticated(self, schema, regular_api):
        resp = regular_api.post('/dynamic-forms/api/form-responses/', {
            'schema': str(schema.pk),
            'data': {'q1': 'answer'},
        }, format='json')
        assert resp.status_code == 201

    def test_list_requires_staff(self, db, regular_api):
        resp = regular_api.get('/dynamic-forms/api/form-responses/')
        assert resp.status_code == 403

    def test_list_as_staff(self, schema, staff_api):
        FormResponse.objects.create(schema=schema, data={'q1': 'val'})
        resp = staff_api.get('/dynamic-forms/api/form-responses/')
        assert resp.status_code == 200
        assert len(resp.data) >= 1

    def test_filter_by_schema(self, schema, staff_api):
        FormResponse.objects.create(schema=schema, data={'q1': 'val'})
        resp = staff_api.get(f'/dynamic-forms/api/form-responses/?schema={schema.pk}')
        assert resp.status_code == 200
        assert len(resp.data) >= 1
