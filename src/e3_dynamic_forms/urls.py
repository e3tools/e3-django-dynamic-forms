from django.urls import include, path

from .views.web.schema_views import (
    get_schema_list_view,
    get_schema_create_view,
    get_schema_edit_view,
    get_schema_detail_view,
    get_schema_delete_view,
)
from .views.web.response_views import (
    get_response_list_view,
    get_response_detail_view,
    get_response_create_view,
)

app_name = 'e3_dynamic_forms'

urlpatterns = [
    path('schemas/', get_schema_list_view().as_view(), name='schema_list'),
    path('schemas/create/', get_schema_create_view().as_view(), name='schema_create'),
    path('schemas/<uuid:pk>/edit/', get_schema_edit_view().as_view(), name='schema_edit'),
    path('schemas/<uuid:pk>/', get_schema_detail_view().as_view(), name='schema_detail'),
    path('schemas/<uuid:pk>/delete/', get_schema_delete_view().as_view(), name='schema_delete'),
    path('schemas/<uuid:schema_pk>/responses/', get_response_list_view().as_view(), name='response_list'),
    path('responses/<uuid:pk>/', get_response_detail_view().as_view(), name='response_detail'),
    path('schemas/<uuid:pk>/respond/', get_response_create_view().as_view(), name='response_create'),
    path('api/', include('e3_dynamic_forms.api.urls')),
]
