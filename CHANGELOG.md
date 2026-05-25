# Changelog

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
