import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    created_date = models.DateTimeField(_('created date'), auto_now_add=True)
    updated_date = models.DateTimeField(_('updated date'), auto_now=True)

    class Meta:
        abstract = True


class FormSchema(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('name'), max_length=255)
    description = models.TextField(_('description'), blank=True, default='')
    schema = models.JSONField(_('schema'), default=dict)
    version = models.PositiveIntegerField(_('version'), default=1)
    is_active = models.BooleanField(_('active'), default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_form_schemas',
        verbose_name=_('created by'),
    )

    class Meta:
        verbose_name = _('form schema')
        verbose_name_plural = _('form schemas')
        ordering = ['-created_date']

    def __str__(self):
        return f"{self.name} (v{self.version})"

    @property
    def page_count(self):
        pages = self.schema.get('pages', [])
        return len(pages) if pages else 1


class FormResponse(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schema = models.ForeignKey(
        FormSchema,
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name=_('schema'),
    )
    data = models.JSONField(_('data'), default=dict)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='form_responses',
        verbose_name=_('created by'),
    )

    class Meta:
        verbose_name = _('form response')
        verbose_name_plural = _('form responses')
        ordering = ['-created_date']

    def __str__(self):
        return f"Response to {self.schema.name} ({self.id})"


class AbstractAttachment(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    response = models.ForeignKey(
        'e3_dynamic_forms.FormResponse',
        on_delete=models.CASCADE,
        related_name='%(class)s_attachments',
        verbose_name=_('response'),
    )
    field_name = models.CharField(_('field name'), max_length=255)
    file = models.FileField(_('file'), upload_to='e3_dynamic_forms/attachments/%Y/%m/')

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.field_name}: {self.file.name}"


class Attachment(AbstractAttachment):
    class Meta(AbstractAttachment.Meta):
        verbose_name = _('attachment')
        verbose_name_plural = _('attachments')
        swappable = 'DYNAMIC_FORMS_ATTACHMENT_MODEL'
