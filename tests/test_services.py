import pytest
from django.contrib.auth import get_user_model

from e3_dynamic_forms.models import FormSchema, FormResponse, Attachment
from e3_dynamic_forms.services import (
    FormResponseProcessor,
    PageResult,
    SessionStateBackend,
    StateBackend,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _valid_schema(pages=None):
    """Return a valid schema dict."""
    if pages is None:
        pages = [
            {
                'title': 'Page 1',
                'fields': [
                    {'name': 'q1', 'type': 'string', 'label': 'Question 1', 'required': True, 'order': 0},
                ],
            },
        ]
    return {'pages': pages}


def _two_page_schema():
    return _valid_schema(pages=[
        {
            'title': 'Page 1',
            'fields': [
                {'name': 'name', 'type': 'string', 'label': 'Name', 'required': True, 'order': 0},
            ],
        },
        {
            'title': 'Page 2',
            'fields': [
                {'name': 'age', 'type': 'integer', 'label': 'Age', 'required': True, 'order': 0},
            ],
        },
    ])


class DictStateBackend(StateBackend):
    """In-memory state backend for tests (no Django session needed)."""

    def __init__(self):
        self._pages = {}
        self._data = {}

    def get_current_page(self, schema_id):
        return self._pages.get(schema_id, 0)

    def set_current_page(self, schema_id, page_index):
        self._pages[schema_id] = page_index

    def get_accumulated_data(self, schema_id):
        return dict(self._data.get(schema_id, {}))

    def set_accumulated_data(self, schema_id, data):
        self._data[schema_id] = dict(data)

    def clear(self, schema_id):
        self._pages.pop(schema_id, None)
        self._data.pop(schema_id, None)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user(db):
    return User.objects.create_user(username='testuser', password='testpass')


@pytest.fixture
def schema_obj(db, user):
    return FormSchema.objects.create(
        name='Test', schema=_valid_schema(), created_by=user,
    )


@pytest.fixture
def two_page_schema_obj(db, user):
    return FormSchema.objects.create(
        name='Two Page', schema=_two_page_schema(), created_by=user,
    )


@pytest.fixture
def backend():
    return DictStateBackend()


# ---------------------------------------------------------------------------
# SessionStateBackend tests
# ---------------------------------------------------------------------------

class TestSessionStateBackend:
    def test_initial_state(self):
        session = {}
        backend = SessionStateBackend(session)
        assert backend.get_current_page('abc') == 0
        assert backend.get_accumulated_data('abc') == {}

    def test_set_and_get_page(self):
        session = {}
        backend = SessionStateBackend(session)
        backend.set_current_page('abc', 2)
        assert backend.get_current_page('abc') == 2

    def test_set_and_get_data(self):
        session = {}
        backend = SessionStateBackend(session)
        backend.set_accumulated_data('abc', {'q1': 'hello'})
        assert backend.get_accumulated_data('abc') == {'q1': 'hello'}

    def test_clear(self):
        session = {}
        backend = SessionStateBackend(session)
        backend.set_current_page('abc', 3)
        backend.set_accumulated_data('abc', {'q1': 'hello'})
        backend.clear('abc')
        assert backend.get_current_page('abc') == 0
        assert backend.get_accumulated_data('abc') == {}

    def test_isolation_between_schemas(self):
        session = {}
        backend = SessionStateBackend(session)
        backend.set_current_page('s1', 1)
        backend.set_current_page('s2', 5)
        assert backend.get_current_page('s1') == 1
        assert backend.get_current_page('s2') == 5


# ---------------------------------------------------------------------------
# FormResponseProcessor — properties
# ---------------------------------------------------------------------------

class TestProcessorProperties:
    def test_current_page_initial(self, schema_obj, backend):
        proc = FormResponseProcessor(schema_obj, backend)
        assert proc.current_page == 0

    def test_total_pages(self, two_page_schema_obj, backend):
        proc = FormResponseProcessor(two_page_schema_obj, backend)
        assert proc.total_pages == 2

    def test_is_last_page_single(self, schema_obj, backend):
        proc = FormResponseProcessor(schema_obj, backend)
        assert proc.is_last_page is True

    def test_is_last_page_multi(self, two_page_schema_obj, backend):
        proc = FormResponseProcessor(two_page_schema_obj, backend)
        assert proc.is_last_page is False

    def test_accumulated_data_initial(self, schema_obj, backend):
        proc = FormResponseProcessor(schema_obj, backend)
        assert proc.accumulated_data == {}


# ---------------------------------------------------------------------------
# FormResponseProcessor — get_blank_form / get_form_class
# ---------------------------------------------------------------------------

class TestProcessorFormBuilding:
    def test_get_blank_form(self, schema_obj, backend):
        proc = FormResponseProcessor(schema_obj, backend)
        form = proc.get_blank_form()
        assert 'q1' in form.fields

    def test_get_form_class_for_page(self, two_page_schema_obj, backend):
        proc = FormResponseProcessor(two_page_schema_obj, backend)
        FormClass = proc.get_form_class(page_index=1)
        form = FormClass()
        assert 'age' in form.fields
        assert 'name' not in form.fields


# ---------------------------------------------------------------------------
# FormResponseProcessor — single-page flow
# ---------------------------------------------------------------------------

class TestSinglePageFlow:
    def test_valid_submission(self, schema_obj, backend, user):
        proc = FormResponseProcessor(schema_obj, backend)
        result = proc.process_page({'q1': 'answer'}, {}, user=user)

        assert result.is_valid is True
        assert result.is_complete is True
        assert result.response is not None
        assert result.response.data == {'q1': 'answer'}
        assert result.response.schema == schema_obj
        assert result.response.created_by == user

    def test_invalid_submission(self, schema_obj, backend):
        proc = FormResponseProcessor(schema_obj, backend)
        # q1 is required but missing
        result = proc.process_page({}, {})

        assert result.is_valid is False
        assert result.is_complete is False
        assert result.response is None
        assert result.form is not None
        assert result.form.errors

    def test_state_cleared_after_completion(self, schema_obj, backend, user):
        proc = FormResponseProcessor(schema_obj, backend)
        proc.process_page({'q1': 'answer'}, {}, user=user)

        assert backend.get_current_page(proc.schema_id) == 0
        assert backend.get_accumulated_data(proc.schema_id) == {}


# ---------------------------------------------------------------------------
# FormResponseProcessor — multi-page flow
# ---------------------------------------------------------------------------

class TestMultiPageFlow:
    def test_page_one_advances(self, two_page_schema_obj, backend):
        proc = FormResponseProcessor(two_page_schema_obj, backend)
        result = proc.process_page({'name': 'Alice'}, {})

        assert result.is_valid is True
        assert result.is_complete is False
        assert proc.current_page == 1

    def test_full_two_page_flow(self, two_page_schema_obj, backend, user):
        proc = FormResponseProcessor(two_page_schema_obj, backend)

        # Page 1
        result1 = proc.process_page({'name': 'Alice'}, {})
        assert result1.is_valid is True
        assert result1.is_complete is False

        # Page 2
        result2 = proc.process_page({'age': '30'}, {}, user=user)
        assert result2.is_valid is True
        assert result2.is_complete is True
        assert result2.response.data == {'name': 'Alice', 'age': 30}

    def test_accumulated_data_persists(self, two_page_schema_obj, backend):
        proc = FormResponseProcessor(two_page_schema_obj, backend)
        proc.process_page({'name': 'Alice'}, {})

        assert proc.accumulated_data == {'name': 'Alice'}

    def test_invalid_page_does_not_advance(self, two_page_schema_obj, backend):
        proc = FormResponseProcessor(two_page_schema_obj, backend)
        result = proc.process_page({}, {})  # name is required

        assert result.is_valid is False
        assert proc.current_page == 0


# ---------------------------------------------------------------------------
# FormResponseProcessor — reset
# ---------------------------------------------------------------------------

class TestProcessorReset:
    def test_reset_clears_state(self, two_page_schema_obj, backend):
        proc = FormResponseProcessor(two_page_schema_obj, backend)
        proc.process_page({'name': 'Alice'}, {})
        assert proc.current_page == 1

        proc.reset()
        assert proc.current_page == 0
        assert proc.accumulated_data == {}


# ---------------------------------------------------------------------------
# FormResponseProcessor — response validation errors
# ---------------------------------------------------------------------------

class TestFinalValidation:
    def test_response_with_unknown_fields_fails(self, db, user):
        """Manually inject bad data to trigger accumulated-data validation."""
        schema = FormSchema.objects.create(
            name='Strict',
            schema=_valid_schema(),
            created_by=user,
        )
        backend = DictStateBackend()
        # Pre-populate accumulated data with an unknown field
        backend.set_accumulated_data(str(schema.pk), {'q1': 'val', 'unknown': 'x'})
        # Set to last page so _finalize runs
        backend.set_current_page(str(schema.pk), 0)

        proc = FormResponseProcessor(schema, backend)
        # Submit valid page data — but accumulated data has extra key
        result = proc.process_page({'q1': 'answer'}, {}, user=user)

        # The accumulated data now has q1=answer AND unknown=x
        # _finalize should catch the unknown field
        assert result.is_valid is False
        assert len(result.validation_errors) > 0
        assert any('unknown' in e.lower() for e in result.validation_errors)


# ---------------------------------------------------------------------------
# FormResponseProcessor — anonymous user
# ---------------------------------------------------------------------------

class TestAnonymousUser:
    def test_none_user(self, schema_obj, backend):
        proc = FormResponseProcessor(schema_obj, backend)
        result = proc.process_page({'q1': 'answer'}, {}, user=None)

        assert result.is_complete is True
        assert result.response.created_by is None


# ---------------------------------------------------------------------------
# PageResult dataclass
# ---------------------------------------------------------------------------

class TestPageResult:
    def test_defaults(self):
        r = PageResult(is_valid=True, form=None)
        assert r.is_complete is False
        assert r.response is None
        assert r.validation_errors == []
