from rest_framework.routers import DefaultRouter

from .views import FormSchemaViewSet, FormResponseViewSet

router = DefaultRouter()
router.register('form-schemas', FormSchemaViewSet, basename='form-schema')
router.register('form-responses', FormResponseViewSet, basename='form-response')

urlpatterns = router.urls
