"""
Pluggable state backends for multi-page form progression.

The ``StateBackend`` ABC defines the interface.  The package ships with
``SessionStateBackend`` (Django sessions); consumers can implement their
own (cache, database, signed cookies, etc.).
"""
import abc
import json


class StateBackend(abc.ABC):
    """Abstract interface for storing multi-page form state between requests."""

    @abc.abstractmethod
    def get_current_page(self, schema_id):
        """Return the current 0-based page index."""

    @abc.abstractmethod
    def set_current_page(self, schema_id, page_index):
        """Store the current page index."""

    @abc.abstractmethod
    def get_accumulated_data(self, schema_id):
        """Return the accumulated response data dict."""

    @abc.abstractmethod
    def set_accumulated_data(self, schema_id, data):
        """Store the accumulated response data dict."""

    @abc.abstractmethod
    def clear(self, schema_id):
        """Remove all stored state for the given schema."""


class SessionStateBackend(StateBackend):
    """Default implementation backed by Django's request.session."""

    def __init__(self, session):
        self._session = session

    def _key(self, schema_id, suffix):
        return f'df_{schema_id}_{suffix}'

    def get_current_page(self, schema_id):
        return self._session.get(self._key(schema_id, 'current_page'), 0)

    def set_current_page(self, schema_id, page_index):
        self._session[self._key(schema_id, 'current_page')] = page_index

    def get_accumulated_data(self, schema_id):
        raw = self._session.get(self._key(schema_id, 'accumulated_data'), '{}')
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                return {}
        return raw

    def set_accumulated_data(self, schema_id, data):
        self._session[self._key(schema_id, 'accumulated_data')] = json.dumps(
            data, default=str,
        )

    def clear(self, schema_id):
        self._session.pop(self._key(schema_id, 'current_page'), None)
        self._session.pop(self._key(schema_id, 'accumulated_data'), None)
