from django.contrib import admin

from .conf import get_attachment_model
from .models import FormSchema, FormResponse


@admin.register(FormSchema)
class FormSchemaAdmin(admin.ModelAdmin):
    list_display = ('name', 'version', 'is_active', 'created_by', 'created_date')
    list_filter = ('is_active', 'created_date')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'created_date', 'updated_date')


@admin.register(FormResponse)
class FormResponseAdmin(admin.ModelAdmin):
    list_display = ('id', 'schema', 'created_by', 'created_date')
    list_filter = ('schema', 'created_date')
    search_fields = ('schema__name',)
    readonly_fields = ('id', 'created_date', 'updated_date')


Attachment = get_attachment_model()

try:
    @admin.register(Attachment)
    class AttachmentAdmin(admin.ModelAdmin):
        list_display = ('id', 'response', 'field_name', 'file', 'created_date')
        list_filter = ('created_date',)
        search_fields = ('field_name',)
        readonly_fields = ('id', 'created_date', 'updated_date')
except admin.sites.AlreadyRegistered:
    pass
