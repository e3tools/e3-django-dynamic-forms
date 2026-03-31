"""
Framework-agnostic orchestrator for multi-page form response collection.

Usage::

    from e3_dynamic_forms.services import FormResponseProcessor, SessionStateBackend

    processor = FormResponseProcessor(schema, SessionStateBackend(request.session))
    result = processor.process_page(request.POST, request.FILES, user=request.user)

    if result.is_complete:
        redirect(...)          # result.response holds the new FormResponse
    elif not result.is_valid:
        re_render(result.form) # form with validation errors
    else:
        redirect_to_next_page()
"""
from dataclasses import dataclass, field
from typing import List, Optional

from ..conf import get_attachment_model
from ..models import FormResponse, FormSchema
from ..utils.json_form_parser import build_dynamic_form_class
from ..utils.response_validator import validate_response_data
from .state_backend import StateBackend


@dataclass
class PageResult:
    """Result of processing a single page submission."""

    is_valid: bool
    """Whether the page (and, on the last page, accumulated data) passed validation."""

    form: object
    """The bound Django Form instance. ``None`` only when ``is_complete`` is ``True``."""

    is_complete: bool = False
    """``True`` when the final page was submitted successfully."""

    response: Optional[FormResponse] = None
    """The newly created ``FormResponse``. Set only when ``is_complete`` is ``True``."""

    validation_errors: List[str] = field(default_factory=list)
    """Accumulated-data validation errors (non-empty only on final-page failure)."""


class FormResponseProcessor:
    """
    Orchestrates multi-page form response collection.

    All persistent state goes through the injected ``StateBackend``, so the
    processor itself is stateless with respect to HTTP.
    """

    def __init__(self, schema: FormSchema, state_backend: StateBackend):
        self.schema = schema
        self.state = state_backend

    # -- read-only properties ------------------------------------------------

    @property
    def schema_id(self) -> str:
        return str(self.schema.pk)

    @property
    def current_page(self) -> int:
        return self.state.get_current_page(self.schema_id)

    @property
    def total_pages(self) -> int:
        return self.schema.page_count

    @property
    def is_last_page(self) -> bool:
        return self.current_page >= self.total_pages - 1

    @property
    def accumulated_data(self) -> dict:
        return self.state.get_accumulated_data(self.schema_id)

    # -- form helpers --------------------------------------------------------

    def get_form_class(self, page_index=None, accumulated_data=None):
        """Build the dynamic Django Form class for the given (or current) page."""
        if page_index is None:
            page_index = self.current_page
        if accumulated_data is None:
            accumulated_data = self.accumulated_data
        return build_dynamic_form_class(
            self.schema.schema,
            page_index=page_index,
            response_data=accumulated_data,
        )

    def get_blank_form(self):
        """Return an unbound form instance for the current page."""
        FormClass = self.get_form_class()
        return FormClass()

    # -- main entry point ----------------------------------------------------

    def process_page(self, post_data, files, user=None) -> PageResult:
        """
        Validate and process a submitted page.

        Args:
            post_data: ``request.POST`` (QueryDict or plain dict).
            files: ``request.FILES`` (MultiValueDict or plain dict).
            user: The submitting user (or ``None`` for anonymous).

        Returns:
            A ``PageResult`` describing the outcome.
        """
        page_index = self.current_page
        accumulated_data = self.accumulated_data
        FormClass = self.get_form_class(page_index, accumulated_data)
        form = FormClass(post_data, files)

        if not form.is_valid():
            return PageResult(is_valid=False, form=form)

        # Merge non-file cleaned data into accumulated data.
        for key, value in form.cleaned_data.items():
            if hasattr(value, 'read'):
                continue
            accumulated_data[key] = value
        self.state.set_accumulated_data(self.schema_id, accumulated_data)

        if self.is_last_page:
            return self._finalize(post_data, files, accumulated_data, user)

        # Advance to next page.
        self.state.set_current_page(self.schema_id, page_index + 1)
        return PageResult(is_valid=True, form=form, is_complete=False)

    # -- reset ---------------------------------------------------------------

    def reset(self):
        """Discard all accumulated state (e.g. user cancels the form)."""
        self.state.clear(self.schema_id)

    # -- internals -----------------------------------------------------------

    def _finalize(self, post_data, files, accumulated_data, user) -> PageResult:
        """Validate accumulated data, create response and attachments."""
        validation_errors = validate_response_data(
            accumulated_data, self.schema.schema,
        )

        if validation_errors:
            FormClass = self.get_form_class()
            form = FormClass(post_data, files)
            for error in validation_errors:
                form.add_error(None, error)
            return PageResult(
                is_valid=False,
                form=form,
                validation_errors=validation_errors,
            )

        response = FormResponse.objects.create(
            schema=self.schema,
            data=accumulated_data,
            created_by=user if user and getattr(user, 'is_authenticated', False) else None,
        )

        Attachment = get_attachment_model()
        for field_name, file_obj in files.items():
            Attachment.objects.create(
                response=response,
                field_name=field_name,
                file=file_obj,
            )

        self.state.clear(self.schema_id)

        return PageResult(
            is_valid=True,
            form=None,
            is_complete=True,
            response=response,
        )
