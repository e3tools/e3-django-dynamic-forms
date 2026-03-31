from rest_framework import viewsets, permissions
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.permissions import IsAuthenticated

from ..conf import get_attachment_model
from ..models import FormSchema, FormResponse
from .serializers import (
    FormSchemaSerializer,
    FormSchemaListSerializer,
    FormResponseSerializer,
)


class IsStaffPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and (request.user.is_staff or request.user.is_superuser)


class FormSchemaViewSet(viewsets.ModelViewSet):
    queryset = FormSchema.objects.all()
    permission_classes = [IsStaffPermission]

    def get_serializer_class(self):
        if self.action == 'list':
            return FormSchemaListSerializer
        return FormSchemaSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class FormResponseViewSet(viewsets.ModelViewSet):
    queryset = FormResponse.objects.select_related('schema').all()
    parser_classes = [MultiPartParser, JSONParser]

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        return [IsStaffPermission()]

    def get_serializer_class(self):
        return FormResponseSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        schema_id = self.request.query_params.get('schema')
        if schema_id:
            qs = qs.filter(schema_id=schema_id)
        return qs

    def perform_create(self, serializer):
        response = serializer.save(created_by=self.request.user)

        # Create Attachment objects for any uploaded files.
        Attachment = get_attachment_model()
        for field_name, file_obj in self.request.FILES.items():
            Attachment.objects.create(
                response=response,
                field_name=field_name,
                file=file_obj,
            )
