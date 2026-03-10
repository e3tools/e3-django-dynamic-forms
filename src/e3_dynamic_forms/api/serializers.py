from rest_framework import serializers

from ..conf import get_attachment_model
from ..models import FormSchema, FormResponse


class FormSchemaSerializer(serializers.ModelSerializer):
    page_count = serializers.ReadOnlyField()

    class Meta:
        model = FormSchema
        fields = [
            'id', 'name', 'description', 'schema', 'version',
            'is_active', 'created_by', 'created_date', 'updated_date',
            'page_count',
        ]
        read_only_fields = ['id', 'version', 'created_date', 'updated_date', 'created_by']


class FormSchemaListSerializer(serializers.ModelSerializer):
    page_count = serializers.ReadOnlyField()

    class Meta:
        model = FormSchema
        fields = ['id', 'name', 'version', 'is_active', 'page_count']


class AttachmentSerializer(serializers.ModelSerializer):
    file = serializers.FileField(read_only=True)

    class Meta:
        fields = ['id', 'field_name', 'file', 'created_date']
        read_only_fields = ['id', 'created_date']

    def __init__(self, *args, **kwargs):
        self.Meta.model = get_attachment_model()
        super().__init__(*args, **kwargs)


class FormResponseSerializer(serializers.ModelSerializer):
    attachments = serializers.SerializerMethodField()

    class Meta:
        model = FormResponse
        fields = [
            'id', 'schema', 'data', 'created_by',
            'created_date', 'updated_date', 'attachments',
        ]
        read_only_fields = ['id', 'created_date', 'updated_date', 'created_by']

    def get_attachments(self, obj):
        Attachment = get_attachment_model()
        attachments = Attachment.objects.filter(response=obj)
        return AttachmentSerializer(attachments, many=True).data
