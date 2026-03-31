from rest_framework import serializers

from ..conf import get_attachment_model
from ..models import FormSchema, FormResponse
from ..utils.response_validator import validate_response_data
from ..utils.schema_validator import validate_schema


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

    def validate_schema(self, value):
        errors = validate_schema(value)
        if errors:
            raise serializers.ValidationError(errors)
        return value


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

    def validate_data(self, value):
        # Multipart uploads send ``data`` as a JSON string — parse it.
        if isinstance(value, str):
            import json
            try:
                value = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                raise serializers.ValidationError('Invalid JSON format.')
        if not isinstance(value, dict):
            raise serializers.ValidationError('Response data must be a JSON object.')
        return value

    def validate(self, attrs):
        schema_instance = attrs.get('schema')
        data = attrs.get('data')
        if schema_instance and data is not None:
            errors = validate_response_data(data, schema_instance.schema)
            if errors:
                raise serializers.ValidationError({'data': errors})
        return attrs

    def get_attachments(self, obj):
        Attachment = get_attachment_model()
        attachments = Attachment.objects.filter(response=obj)
        return AttachmentSerializer(attachments, many=True).data
