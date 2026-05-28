# Changelog

## 0.3.1 - 2026-05-28

### Fixed
- Fixed `AttributeError: 'SettingsReference' object has no attribute '_meta'` caused by Django's swappable mechanism returning `SettingsReference` objects instead of plain strings for ForeignKey targets.
- Swappable model settings (`DYNAMIC_FORMS_SCHEMA_MODEL`, `DYNAMIC_FORMS_RESPONSE_MODEL`, `DYNAMIC_FORMS_ATTACHMENT_MODEL`) now have defaults set at app load time, matching the `settings.AUTH_USER_MODEL` pattern.
- Migrations now declare proper `swappable_dependency` for custom swappable settings.

## 0.3.0 - 2026-05-28

### Added
- Swappable form response model via `DYNAMIC_FORMS_RESPONSE_MODEL` setting.
- `AbstractFormResponse` base class for custom response models.
- `get_form_response_model()` helper in `e3_dynamic_forms.conf`.

### Changed
- `FormResponse.schema` related_name changed from `responses` to `%(class)s_responses` to prevent clashes when subclassing `AbstractFormResponse`.
- `FormResponse.created_by` related_name changed from `form_responses` to `%(class)s_form_responses`.
- `AbstractAttachment.response` FK now points to the swappable `DYNAMIC_FORMS_RESPONSE_MODEL` setting instead of hardcoded `FormResponse`.

### Migration notes
- Run `python manage.py migrate` to apply migration `0003_make_formresponse_swappable`.
- If you use `schema.responses` in your code, update it to `schema.formresponse_responses`.
- If you use `user.form_responses` in your code, update it to `user.formresponse_form_responses`.

## 0.2.0 - 2026-05-25

### Added
- Swappable form schema model via `DYNAMIC_FORMS_SCHEMA_MODEL` setting.
- `AbstractFormSchema` base class for custom schema models.
- `get_form_schema_model()` helper in `e3_dynamic_forms.conf`.
- `get_form_schema_form_class()` factory for the schema ModelForm.

### Changed
- `FormSchema.created_by` related_name changed from `created_form_schemas` to `%(class)s_created_schemas` to prevent clashes when subclassing `AbstractFormSchema`.

### Migration notes
- Run `python manage.py migrate` to apply migration `0002_make_formschema_swappable`.
- If you use `user.created_form_schemas` in your code, update it to `user.formschema_created_schemas`.

## 0.1.3 - 2026-03-10

### Changed
- Renamed package from `dynamic_forms` to `e3_dynamic_forms`.

## 0.1.2 - 2026-03-04

### Added
- Initial public release.
- JSON-based dynamic form engine with multi-page support.
- Conditional field visibility with AND/OR logic.
- REST API for form schemas and responses.
- Swappable attachment model.
- Geolocation field support.
- Built-in web views with permission mixins.
