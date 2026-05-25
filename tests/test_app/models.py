from django.db import models

from e3_dynamic_forms.models import AbstractFormSchema


class CustomFormSchema(AbstractFormSchema):
    """Test model to verify AbstractFormSchema can be subclassed."""
    department = models.CharField(max_length=255, default='')

    class Meta(AbstractFormSchema.Meta):
        pass
